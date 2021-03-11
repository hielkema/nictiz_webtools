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
    task = MappingTask.objects.select_related(
                'project_id',
                'source_component',
                ).get(id=taskid)

    # Put the results of all ECL queries for the task in 1 list
    all_results = list()
    queries = MappingEclPart.objects.filter(task=task).select_related(
        'task'
    ).order_by('id')
    
    if queries:
        try:
            error = False
            output = True
            print(f"Creating rules for task {taskid} from project {task.project_id}")


            # Delete any existing conflicting rules
            rules = MappingRule.objects.filter(
                project_id          = task.project_id,
                target_component    = task.source_component,
            ).delete()


            # Put the results of all ECL queries for the task in 1 list
            queries = MappingEclPart.objects.filter(task=task).select_related(
                'task'
            ).order_by('id')

            # Set queries to in progress
            queries.export_finished = False

            # Find component ID's that should be excluded
            exclude_componentIDs = []
            excluded_componentIDs = []
            try:
                obj = MappingEclPartExclusion.objects.get(task = task)
                components = MappingCodesystemComponent.objects.filter(
                        codesystem_id = obj.task.source_component.codesystem_id,
                        component_id__in=list(obj.components)
                    )
                # Loop components
                for component in components:
                    # For each, retrieve their tasks, in this same project
                    exclude_tasks = MappingTask.objects.filter(project_id = task.project_id, source_component=component)
                    for exclude_task in exclude_tasks:
                        exclusion_queries = MappingEclPart.objects.filter(task=exclude_task)
                        for exclusion_query in exclusion_queries:
                            try:
                                for key, value in exclusion_query.result.get('concepts').items():
                                    exclude_componentIDs.append(key)
                            except Exception as e:
                                print(f"[Task createRulesFromEcl] ## Issue tijdens uitlezen resultaten: {e}")
                                error = e

            except Exception as e:
                print(f"[Task createRulesFromEcl] ## Unhandled exception reverse mappings: {e}")
                error = e


            # For each ECL query:
            all_queries = queries.values()
            print("Start export for queries")
            i=0
            rules_to_create = list()
            for query in all_queries:
                if query['finished'] == True:
                    try:
                        i+=1
                        print(f"Handling query {i}")
                        # Collect all SNOMED concepts we need
                        snomed_ids = query['result']['concepts'].keys()
                        snomed_concepts = list(MappingCodesystemComponent.objects.filter(component_id__in = snomed_ids).values(
                            'id',
                            'component_id'
                        ))

                        target_component_id = task.source_component_id
                        for snomed_concept in snomed_concepts:
                            if snomed_concept['component_id'] not in exclude_componentIDs:

                                rules_to_create.append(MappingRule(
                                    project_id_id = task.project_id_id,
                                    source_component_id = snomed_concept['id'],
                                    target_component_id = target_component_id,
                                    mapgroup = 1,
                                    mappriority = 1,
                                    mapcorrelation = query['mapcorrelation'],
                                    active = True
                                ))
                            else:
                                exclude_componentIDs.append(snomed_concept['component_id'])

                        print(f"Finished handling query {i}")
                    except Exception as e:
                        print(f"[Task createRulesFromEcl] Error creating bulk task list for query #{i}: {str(e)}")
                        output = False
                        error = e
                else:
                    print("Trying to export unfinished query, skipping.")
                
            # Bulk create these rules
            print(f"Bulk create all {len(rules_to_create)} rules.")
            MappingRule.objects.bulk_create(rules_to_create, batch_size=5000)
            print("Finished creating rules.")

            rules = MappingRule.objects.filter(
                project_id          = task.project_id,
                target_component    = task.source_component,
            )
            print(f"Double check: {len(rules)} rules created.")

        except Exception as e:
            print("[Task createRulesFromEcl] Unhandled exception",str(e))
            error = e
            output = False
        
        for query in queries:
            query.export_finished = True
            query.failed = False
            query.error = None
            query.save()
        if output == False:
            print("Er is iets niet in orde met deze export.")
            for query in queries:
                query.failed = True
                query.error = f"Tijdens het aanmaken van de regels is voor deze queries iets mis gegaan. Zie server logs voor details. Hint (indien beschikbaar): {error}"
                query.save()

    else:
        # No queries - remove all relevant mapping rules
        rules = MappingRule.objects.filter(
            project_id = task.project_id,
            target_component = task.source_component,
        ).delete()
        celery = "No queries, no celery"

    return True