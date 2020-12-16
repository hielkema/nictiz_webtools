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
def test_recursive_ecl_exclusion(taskid):
    logger.info("Spawned snomed_daily_build_active for TASK "+str(taskid))

    task = MappingTask.objects.select_related(
            'source_component',
            'project_id'
        ).get(id=taskid)
    exclusions = MappingEclPartExclusion.objects.get(task=task)

    for exclusion in exclusions.components:
        # exclusion is a source component for a task in the current codesystem
        # Now; look for the task with this source component
        try:
            other_task = MappingTask.objects.select_related(
                    'source_component'
                ).get(
                    project_id = task.project_id,
                    source_component__component_id = exclusion,
                )

            # Then retrieve the exclusions for that task
            other_exclusions = MappingEclPartExclusion.objects.get(task=other_task)
            if task.source_component.component_id in other_exclusions.components:
                # print(f"{str(task.source_component.component_id)} excludes {exclusion}. {exclusion} excludes {other_exclusions.components}")
                # print(f"ALARM - Wederzijdse exclusie {task.source_component.component_id} en {other_task.source_component.component_id}")
                logger.info("That's a problem. Mismatch.")
                obj, created = MappingTaskAudit.objects.get_or_create(
                        task=task,
                        audit_type="ecl_recursive_exclusion",
                        hit_reason=f"Wederzijdse exclusie {task.source_component.component_id} en {other_task.source_component.component_id}",
                    )
                logger.info(str(obj))
        except Exception as e:
            logger.info("Error in QA [test_recursive_ecl_exclusion]: "+str(e))
    