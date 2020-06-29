# Create your tasks here
from __future__ import absolute_import, unicode_literals
from celery import shared_task
import time, json
from celery.task.schedules import crontab
from celery.result import AsyncResult
from celery.decorators import periodic_task
from celery.utils.log import get_task_logger
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
        valid_rules = {}

        # Set all relevant ECL queries to 'running'
        eclqueries = MappingEclPart.objects.filter(task=task)
        for query in eclqueries:
            query.export_finished = False
            query.save()
        
        # Loop through queries to find individual rules, put in list
        for query in queries:  
            print("Found query",query.id)
            if query.finished == False:
                queries_unfinished = True
            if query.finished:
                print("Query is finished, let's go")
                # Add all results to a list for easy viewing
                try:
                    for key, result in query.result.get('concepts').items():
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
                except:
                    print("Retrieve mappings: No results")




        ## Create new rules
        for concept in all_results:
            print(f"Handling rule for concept {concept.get('id')}")
            print("Correlation",concept.get('correlation'))
            component = MappingCodesystemComponent.objects.get(component_id=concept.get('id'))
            existing = MappingRule.objects.filter(
                project_id = task.project_id,
                source_component = component,
                target_component = task.source_component,
                mapcorrelation = concept.get('correlation'),
            )
            if existing.count() == 0:
                print("Start get_or_create")
                rule, created = MappingRule.objects.get_or_create(
                    project_id = task.project_id,
                    source_component = component,
                    target_component = task.source_component,
                    mapcorrelation = concept.get('correlation'),
                )
                print("Regel in DB", rule)
                print("Created?", created)
                print("\n\n\n")
            else:
                print(f"Already {existing.count()} rules in database - skip creating another")

        # Cleanup - Remove rules that should not be there
        ## Get all rules for this task
        rules = MappingRule.objects.filter(
            project_id = task.project_id,
            target_component = task.source_component,
        )
        for rule in rules:
            if valid_rules.get(rule.target_component.component_id):
                if rule.mapcorrelation == valid_rules.get(rule.target_component.component_id).get('correlation'):
                    # Corret; can stay
                    True
                else:
                    # Make it gone
                    rule.delete()

        # Set all relevant ECL queries to 'done'
        eclqueries = MappingEclPart.objects.filter(task=task)
        for query in eclqueries:
            query.export_finished = True
            query.save()
    else:
        # No queries - remove all relevant mapping rules
        rules = MappingRule.objects.filter(
            project_id = task.project_id,
            target_component = task.source_component,
        ).delete()
        celery = "No queries, no celery"

    return True