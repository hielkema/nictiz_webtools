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

# Import environment variables
env = environ.Env(DEBUG=(bool, False))
# reading .env file
environ.Env.read_env(env.str('ENV_PATH', '.env'))

logger = get_task_logger(__name__)

@shared_task
def nhg_loinc_order_vs_observation(taskid):
    logger.info("Spawned nhg_loinc_order_vs_observation for TASK "+str(taskid))
    task = MappingTask.objects.get(id=taskid)
    mappings = MappingRule.objects.filter(project_id = task.project_id, source_component = task.source_component)

    # For each mapping rule associated with the selected task:
    for mapping in mappings:
        # If the mapping is between Labcodeset and NHG Diagnostisch bepalingen:
        if ((mapping.source_component.codesystem_id.codesystem_title == "NHG Diagnostische bepalingen") and (mapping.target_component.codesystem_id.codesystem_title == "Labcodeset")) or ((mapping.target_component.codesystem_id.codesystem_title == "NHG Diagnostische bepalingen") and (mapping.source_component.codesystem_id.codesystem_title == "Labcodeset")):
            # Source AUB
            if mapping.source_component.component_extra_dict.get('Aanvraag/Uitslag/Beide'):
                source = mapping.source_component.component_extra_dict.get('Aanvraag/Uitslag/Beide')
            else:
                source = mapping.source_component.component_extra_dict.get('Aanvraag/Resultaat')
            # Target AUB
            if mapping.target_component.component_extra_dict.get('Aanvraag/Uitslag/Beide'):
                target = mapping.target_component.component_extra_dict.get('Aanvraag/Uitslag/Beide')
            else:
                target = mapping.target_component.component_extra_dict.get('Aanvraag/Resultaat')

            hit = False
            if (source == "A" and target == "Observation") or (target == "A" and source == "Observation"):
                hit = True
            if (source == "U" and target == "Order") or (target == "U" and source == "Order"):
                hit = True

            # NHG beide -> Labcodeset observation
            if (source == "B" and target == "Observation"):
                hit = True

            if hit:
                logger.info("That's a problem. Mismatch.")
                obj, created = MappingTaskAudit.objects.get_or_create(
                                task=task,
                                audit_type="nhg_loinc_order_vs_observation",
                                hit_reason='Mismatch order/aanvraag',
                            )