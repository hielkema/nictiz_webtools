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
def ecl_vs_rules(taskid):
    # Check the ECL result of every ecl_part attached to a task, and check if all rules are present in the mapping rule database.
    task = MappingTask.objects.get(id=taskid)
    # only run if task is ECL-1
    if task.project_id.project_type == '4':
        logger.info(f"[ECL vs RULES] Task {task.id} check started")
        queries = MappingEclPart.objects.filter(task=task)
        valid_concept_ids = {}
        # For each ECL query, check of the corresponding rules are present
        for query in queries:
            # Only handle if query is finished
            if query.export_finished:
                for conceptid, concept in query.result.get('concepts').items():
                    #Check if a rule with this conceptid and correlation exists
                    rules = MappingRule.objects.filter(
                        source_component__component_id = conceptid,
                        mapcorrelation = query.mapcorrelation,
                    )
                    if rules.count() > 0:
                        logger.info(f"[ECL vs RULES] Task {task.id} / Rule for {conceptid} present")
                    else:
                        logger.info(f"[ECL vs RULES] Task {task.id} / Rule for {conceptid} not present - HIT")
                        obj, created = MappingTaskAudit.objects.get_or_create(
                                task=task,
                                audit_type="Mismatch ECL vs rules",
                                hit_reason='Resultaat van ECL query komt niet overeen met mapping rules in database',
                            )
                    valid_concept_ids.update({
                        conceptid : {
                            'id' : conceptid,
                            'correlation' : query.mapcorrelation,
                        }
                    })
            else:
                logger.info(f"[ECL vs RULES] Task {task.id} not all rules finished - no check")

        # Check if there are any additional rules present that should not be there according to the ECL results.
        logger.info(f"[ECL vs RULES] Task {task.id} checking if the present rules SHOULD be there")
        rules = MappingRule.objects.filter(
            project_id = task.project_id,
            target_component = task.source_component,
        ).select_related('target_component', 'source_component')
        for rule in rules:
            valid = valid_concept_ids.get(str(rule.source_component.component_id), False)
            if valid:
                if rule.source_component.component_id == valid.get('id') and rule.mapcorrelation == valid.get('correlation'):
                    logger.info(f"[ECL vs RULES] Task {task.id} rule en correlation correct")
                else:
                    logger.info(f"[ECL vs RULES] Task {task.id} rule en correlation incorrect - HIT")
                    obj, created = MappingTaskAudit.objects.get_or_create(
                                task=task,
                                audit_type="Mismatch ECL vs rules",
                                hit_reason='Er is een regel aanwezig die er niet hoort - type 1',
                            )
            else:
                # ConceptID should not be there at all
                logger.info(f"[ECL vs RULES] Task {task.id} / Rule for {conceptid} not present - HIT")
                obj, created = MappingTaskAudit.objects.get_or_create(
                        task=task,
                        audit_type="Mismatch ECL vs rules",
                        hit_reason='Er is een regel aanwezig die er niet hoort / regels komen in 2 ECL queries voor met andere correlatie - type 2',
                    )


    else:
        logger.info(f"[ECL vs RULES] Task {task.id} is not an ECL-1 task. No check.")