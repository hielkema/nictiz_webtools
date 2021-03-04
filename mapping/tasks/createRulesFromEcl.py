# Create your tasks here
from __future__ import absolute_import, unicode_literals
from celery import shared_task
import time, json
from celery.task.schedules import crontab
from celery.result import AsyncResult
from celery.decorators import periodic_task
from celery.utils.log import get_task_logger
from celery.execute import send_task
import xmltodict
from ..forms import *
from ..models import *
import urllib.request
from pandas import read_excel, read_csv
import environ
from snowstorm_client import Snowstorm

# Import environment variables
env = environ.Env(DEBUG=(bool, False))
# reading .env file
environ.Env.read_env(env.str('ENV_PATH', '.env'))

logger = get_task_logger(__name__)

@shared_task
def createRulesFromEcl(taskid):
    print("Task createRulesFromEcl received by celery")
    task = MappingTask.objects.get(id=taskid)

    # Put the results of all ECL queries for the task in 1 list
    all_results = list()
    queries = MappingEclPart.objects.filter(task=task).select_related(
        'task'
    ).order_by('id')
    
    if queries:
        # Create list of rules that should be present
        # Using a dictionary means that every component can only be present in 1 rule - last one in the loop below wins.
        # This is on purpose; duplicate rules cannot exist.
        valid_rules = {}

        # Set all relevant ECL queries to 'running'
        eclqueries = MappingEclPart.objects.filter(task=task)
        for query in eclqueries:
            query.export_finished = False
            query.save()
        
        # Find component ID's that should be excluded
        exclude_componentIDs = []
        excluded_componentIDs = []
        try:
            obj = MappingEclPartExclusion.objects.get(task = task)
            components = MappingCodesystemComponent.objects.filter(
                    codesystem_id = obj.task.source_component.codesystem_id,
                    component_id__in=list(obj.components)
                )
            # print(f"Will exclude ECL results from {str(components)}")
            # Loop components
            for component in components:
                # print(f"Handling exclusion of {str(component)}")
                # For each, retrieve their tasks, in this same project
                exclude_tasks = MappingTask.objects.filter(project_id = task.project_id, source_component=component)
                # print(f"Found tasks: {str(exclude_tasks)}")
                for exclude_task in exclude_tasks:
                    # print(f"Handling exclude_task {str(exclude_task)}")
                    exclusion_queries = MappingEclPart.objects.filter(task=exclude_task)
                    for exclusion_query in exclusion_queries:
                        # print(f"Found query result for {exclude_task.source_component.component_title}: [{str(exclusion_query.result)}] \n{list(exclusion_query.result.get('concepts'))}")
                        try:
                            for key, value in exclusion_query.result.get('concepts').items():
                                exclude_componentIDs.append(key)
                        except Exception as e:
                            print(f"[Task createRulesFromEcl] ## Issue tijdens uitlezen resultaten: {e}")

                # print(f"Next component - list is now: {exclude_componentIDs}\n\n")
            # print(f"Full exclude list: {exclude_componentIDs}")
        except Exception as e:
            print(f"[Task createRulesFromEcl] ## Unhandled exception reverse mappings: {e}")


        # Loop through queries to find individual rules, put in list
        for query in queries:  
            print("[@shared task - createRulesFromEcl] Found query",query.id)
            if query.finished == False:
                queries_unfinished = True
            if query.finished:
                print("[@shared task - createRulesFromEcl] Query is finished, let's go")
                # Add all results to a list for easy viewing
                try:
                    for key, result in query.result.get('concepts').items():
                        if key not in exclude_componentIDs:
                            # print(result)   
                            _query = result
                            _query.update({
                                # 'queryId' : query.id,
                                'query' : query.query,
                                # 'description' : query.description,
                                'correlation' : query.mapcorrelation,
                            })
                            # Append to all_results for creation
                            all_results.append(_query)
                            
                            # Append to valid_rules for validation after
                            valid_rules.update({
                                result.get('id') : {
                                    'correlation' : query.mapcorrelation,
                                }
                            })
                            # print(f"{key} mag aangemaakt worden!")
                        else:
                            # print(f"{key} mag NIET aangemaakt worden!")
                            True
                except:
                    print(f"[@shared task - createRulesFromEcl] Retrieve mappings: No results in query {query.id}")


        ## Create new rules
        ##### OLD METHOD - check before adding
        #region
        # for concept in all_results:
        #     try:
        #         # print(f"Handling rule for concept {concept.get('id')}")
        #         # print("Concept",concept.get('id'))
        #         # print("Correlation",concept.get('correlation'))

        #         # If concepts from the ECL query are not present, import them and try again.
        #         try:
        #             component = MappingCodesystemComponent.objects.get(component_id=concept.get('id'))
        #         except:
        #             print(f"[@shared task - createRulesFromEcl] Error while selecting SNOMED Concept {concept.get('id')} from database! Going to retrieve it, and all descendants to be sure.\nError: [{str(e)}]")
        #             task = import_snomed_async(str(concept.get('id')))
        #             while task.result != 'SUCCESS':
        #                 print("Waiting for data to be retrieved.....")
        #                 time.sleep(1)
        #             try:
        #                 print("Trying again")
        #                 component = MappingCodesystemComponent.objects.get(component_id=concept.get('id'))
        #             except Exception as e:
        #                 print(f"[@shared task - createRulesFromEcl] REPEATED Error while selecting SNOMED Concept {concept.get('id')} from database! Going to retrieve it, and all descendants to be sure.")
        #                 print(f"Giving up. Error [{str(e)}]")

        #         existing = MappingRule.objects.filter(
        #             project_id = task.project_id,
        #             source_component = component,
        #             target_component = task.source_component,
        #             mapcorrelation = concept.get('correlation'),
        #         )
        #         if existing.count() == 0:
        #             # print("Start get_or_create")
        #             rule, created = MappingRule.objects.get_or_create(
        #                 project_id = task.project_id,
        #                 source_component = component,
        #                 target_component = task.source_component,
        #                 mapcorrelation = concept.get('correlation'),
        #             )
        #             # print("Regel in DB", rule)
        #             # print("Created?", created)
        #             print("\n\n\n")
        #         else:
        #             # print(f"Already {existing.count()} rules in database - skip creating another")
        #             True
        #     except Exception as e:
        #         print(f"[Exception in shared task createRulesFromEcl] - intended to handle {concept.get('id')} - Error: [{str(e)}]")
        #endregion

        # NEW METHOD - delete, then add all as bulk
        #region
        # Delete existing rules for this task
        print("[@shared task - createRulesFromEcl] Delete old rules related to this project and component")
        rules = MappingRule.objects.filter(
            project_id = task.project_id,
            target_component = task.source_component,
        ).delete()
        
        # Prefetch all components before generating worklist
        components = MappingCodesystemComponent.objects.filter(component_id__in=[x['id'] for x in all_results])
        component_list = components.values()

        # Create list for bulk creation
        print("[@shared task - createRulesFromEcl] Create list for bulk creation")
        to_create = []
        for concept in all_results:
            try:
                _component = list(filter(lambda x: x['component_id'] == concept.get('id'), component_list))[0]
                to_create.append(MappingRule(
                    project_id = task.project_id,
                    source_component__id = _component['id'],
                    target_component = task.source_component,
                    mapcorrelation = concept.get('correlation'),
                ))
            except Exception as e:
                print(f"[Exception in shared task createRulesFromEcl] - intended to handle {concept.get('id')} - Error: [{str(e)}]")

        print(f"[@shared task - createRulesFromEcl] Adding {len(to_create)} to db in bulk")
        msg = MappingRule.objects.bulk_create(to_create)
        #endregion



        # Cleanup - Remove rules that should not be there
        # print(f"Valid rules:\n {valid_rules}")
        print("Doing some cleanup")
        ## Get all rules for this task
        rules = MappingRule.objects.filter(
            project_id = task.project_id,
            target_component = task.source_component,
        ).select_related(
            'source_component'
        )
        for rule in rules:
            # print(f"Checking {str(rule)}")
            if valid_rules.get(rule.source_component.component_id):
                if rule.mapcorrelation == valid_rules.get(rule.source_component.component_id).get('correlation'):
                    # Correct ID and correlation; can stay
                    True
                else:
                    # Correct ID, wrong correlation; Make it gone
                    rule.delete()
            else:
                # Not present in valid_rules at all - delete
                rule.delete()


        # Set all relevant ECL queries to 'done'
        eclqueries = MappingEclPart.objects.filter(task=task)
        for query in eclqueries:
            query.export_finished = True
            query.save()
        send_task('mapping.tasks.qa_ecl_vs_rules.ecl_vs_rules', [], {'taskid':task.id})
    else:
        # No queries - remove all relevant mapping rules
        rules = MappingRule.objects.filter(
            project_id = task.project_id,
            target_component = task.source_component,
        ).delete()
        celery = "No queries, no celery"

    return True