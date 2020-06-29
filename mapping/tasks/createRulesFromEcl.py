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
def createRulesFromEcl(taskid, ecl_results):
    print("Task createRulesFromEcl received by celery")
    task = MappingTask.objects.get(id=taskid)

    # Set all relevant ECL queries to 'running'
    eclqueries = MappingEclPart.objects.filter(task=task)
    for query in eclqueries:
        query.export_finished = False
        query.save()

    ## Remove existing rules for this concept
    MappingRule.objects.filter(
        project_id = task.project_id,
        target_component = task.source_component,
    ).delete()

    ## Create new rules
    for concept in ecl_results:
        print("Concept",concept.get('id'))
        print("Correlation",concept.get('correlation'))
        component = MappingCodesystemComponent.objects.get(component_id=concept.get('id'))
        rule, created = MappingRule.objects.update_or_create(
            project_id = task.project_id,
            source_component = component,
            target_component = task.source_component,
            mapcorrelation = concept.get('correlation'),
        )
        print("Regel in DB", rule)
        print("Created?", created)
        print("\n\n\n")

    # Set all relevant ECL queries to 'running'
    eclqueries = MappingEclPart.objects.filter(task=task)
    for query in eclqueries:
        query.export_finished = True
        query.save()

    return True