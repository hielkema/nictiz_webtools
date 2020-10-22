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
def check_duplicate_rules(taskid):
    # Check the mappings for each task, and check if any duplicate mapping rules exist.
    task = MappingTask.objects.get(id=taskid)
    # only run if task is ECL-1
    if task.project_id.project_type == '4':
        logger.info(f"[ECL check_duplicate_rules] Task {task.id} check started")
        target = task.source_component
        
        # Find all rules in this project pointing to the target of this task.
        # Amounts to all rules in the 'REGELS' tab.
        rules = MappingRule.objects.filter(
            project_id = task.project_id,
            target_component = target,
        ).select_related(
            'project_id',
            'source_component',
        )

        # Now, for each rule, check if the source_component has bro's.
        for rule in rules:
            # Get rules with the same source_component in this project.
            related_rules = MappingRule.objects.filter(
                project_id = rule.project_id,
                source_component = rule.source_component,
            ).select_related(
                'project_id',
                'source_component',
            )

            # This should be 0-1 rule. If more: error.
            if related_rules.count() > 1:
                # Find the tasks for each of these rules.
                _tasks = MappingTask.objects.filter(
                    project_id = task.project_id,
                    source_component = rule.target_component
                )
                tasks_with_errors = []
                for _task in _tasks:
                    tasks_with_errors.append(_task)

                for task_with_error in tasks_with_errors:
                    # QA hit
                    logger.info(f"[ECL check_duplicate_rules] Duplicate found.")
                    task_ids    = list(_tasks.values_list('id', flat=True))
                    # rule_list   = list(related_rules.values_list('target_component__component_id', 'target_component__component_title'))
                    # rule_list_items = [f"{item[0]} {item[1]}" for item in rule_list]
                    rule_list   = list(related_rules.values_list('target_component__component_id'))
                    rule_list_items = [f"{item[0]}" for item in rule_list]
                    rule_list_flat = ', '.join(rule_list_items)

                    obj, created = MappingTaskAudit.objects.get_or_create(
                        task=task_with_error,
                        audit_type="ECL - duplicate mapping rule",
                        hit_reason=f"Dezelfde SNOMED code [{rule.source_component.component_id}] wordt gebruikt in mappings bij taken [{task_ids}]. Regels: {rule_list_flat}",
                    )


    else:
        logger.info(f"[ECL check_duplicate_rules] Task {task.id} is not an ECL-1 task. No check.")