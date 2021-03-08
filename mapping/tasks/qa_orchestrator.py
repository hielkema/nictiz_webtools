# Step 1: Add this file to __init__.py
# Step 2: Add your functions below.
# Step 3: Don't forget to fire the task somewhere if that is the intended use of this file.


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
from ..models import *
import urllib.request
import environ

# Import environment variables
env = environ.Env(DEBUG=(bool, False))
# reading .env file
environ.Env.read_env(env.str('ENV_PATH', '.env'))

logger = get_task_logger(__name__)

@shared_task
def audit_async(audit_type=None, project=None, task_id=None):
    project = MappingProject.objects.get(id=project)
    if task_id == None:
        tasks = MappingTask.objects.select_related(
            'project_id',
            'source_component',
            'source_component__codesystem_id',
            'source_codesystem',
            'target_codesystem',
            'user',
            'status',
        ).filter(project_id=project)
    else:
        tasks = MappingTask.objects.select_related(
            'project_id',
            'source_component',
            'source_component__codesystem_id',
            'source_codesystem',
            'target_codesystem',
            'user',
            'status',
        ).filter(project_id=project, id=task_id).order_by('id')

    ###### Slowly moving to separate audit QA scripts.
    logger.info(f'Orchestrator is spawning QA processes for {tasks.count()} task(s) in project {project.id} - {project.title}')
    
    # Spawn QA for labcodeset<->NHG tasks
    for task in tasks:
        logger.info("Handling taskID "+str(task.id))
        # Delete all old audit hits for this task if not whitelisted
        delete = MappingTaskAudit.objects.filter(task=task, ignore=False, sticky=False).delete()

        # logger.info('Checking task: {0}'.format(task.id))
        send_task('mapping.tasks.qa_check_rule_attributes.check_rule_attributes', [], {'taskid':task.id})
        
        # logger.info('Spawning QA scripts for Labcodeset)
        send_task('mapping.tasks.qa_labcodeset.labcodeset_order_as_source', [], {'taskid':task.id})

        # logger.info('Spawning QA scripts for NHG<->Labcodeset')
        send_task('mapping.tasks.qa_nhg_labcodeset.nhg_loinc_order_vs_observation', [], {'taskid':task.id})
        
        if task.project_id.project_type == '4':
            # logger.info('Spawning QA scripts for ECL-1 queries')
            if task_id == None:
                print(f"Skipping [mapping.tasks.qa_ecl_vs_rules.ecl_vs_rules] - only run this in project mode")
                send_task('mapping.tasks.qa_ecl_vs_rules.ecl_vs_rules', [], {'taskid':task.id})
            send_task('mapping.tasks.qa_ecl_duplicates.check_duplicate_rules', [], {'taskid':task.id})
            send_task('mapping.tasks.qa_recursive_exclusions.test_recursive_ecl_exclusion', [], {'taskid':task.id})
        
        # logger.info('Spawning general QA scripts for SNOMED')
        # Snowstorm daily build SNOWSTORM does not like DDOS - only run on individual tasks, not on entire projects.
        if tasks.count() == 1:
            send_task('mapping.tasks.qa_snomed.snomed_daily_build_active', [], {'taskid':task.id})