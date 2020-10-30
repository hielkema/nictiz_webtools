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
def runAllEclQueriesInProject(projectid):
    project = MappingProject.objects.get(id=projectid)
    logger.info(f"[runAllEclQueriesInProject] Started full-project run for project {project.title}")
    tasks = MappingTask.objects.filter(project_id=project)
    for task in tasks:
        # Get all ECL queries for the task
        queries = MappingEclPart.objects.filter(task=task)
        for query in queries:
            send_task('mapping.tasks.tasks.UpdateECL1Task', [], {'record_id':query.id, 'query': query.query})            
    logger.info("[runAllEclQueriesInProject] Finished")

    return True