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
    task = MappingTask.objects.select_related(
        'source_component',
        'source_component__codesystem_id',
        'project_id',
    ).get(id=taskid)
    # only run if task is ECL-1
    if task.project_id.project_type == '4':
        logger.info(f"[ECL vs RULES] Task {task.id} check started")


        # Find component ID's from ECL queries that should not be there
        exclude_componentIDs = []
        excluded_componentIDs = []
        try:
            obj = MappingEclPartExclusion.objects.get(task = task)
            components = MappingCodesystemComponent.objects.select_related(
                'task',
                'task__source_component'
            ).filter(
                    codesystem_id = obj.task.source_component.codesystem_id,
                    component_id__in=list(obj.components)
                )
            print(f"Will exclude ECL results from {str(components)}")
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
                        for key, value in exclusion_query.result.get('concepts').items():
                            exclude_componentIDs.append(key)
                
                # print(f"Next component - list is now: {exclude_componentIDs}\n\n")
            # print(f"Full exclude list: {exclude_componentIDs}")
        except Exception as e:
            True


        queries = MappingEclPart.objects.filter(task=task)
        valid_concept_ids = {}
        # For each ECL query, check of the corresponding rules are present
        for query in queries:
            # Only handle if query is finished
            if query.export_finished:
                for conceptid, concept in query.result.get('concepts').items():
                    if conceptid not in exclude_componentIDs:
                        # logger.info(f"[ECL vs RULES] Task {task.id} / Rule for {conceptid} is not excluded by MappingEclPartExclusion")
                        #Check if a rule with this conceptid and correlation exists
                        rules = MappingRule.objects.select_related(
                            'source_component'
                        ).filter(
                            source_component__component_id = conceptid,
                            mapcorrelation = query.mapcorrelation,
                        )
                        if rules.count() > 0:
                            # logger.info(f"[ECL vs RULES] Task {task.id} / Rule for {conceptid} present")
                            True
                        else:
                            # logger.info(f"[ECL vs RULES] Task {task.id} / Rule for {conceptid} not present - HIT")
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
                        # logger.info(f"[ECL vs RULES] Task {task.id} / Rule for {conceptid} IS excluded by MappingEclPartExclusion")
                        True
            else:
                # logger.info(f"[ECL vs RULES] Task {task.id} not all rules finished - no check")
                True
                obj, created = MappingTaskAudit.objects.get_or_create(
                        task=task,
                        audit_type="Audit while active export",
                        hit_reason='De audit draaide terwijl er nog een export liep. Resultaat niet betrouwbaar.',
                    )

        # Check if there are any additional rules present that should not be there according to the ECL results.
        logger.info(f"[ECL vs RULES] Task {task.id} checking if the present rules SHOULD be there")
        rules = MappingRule.objects.select_related(
            'source_component',
            'target_component'
        ).filter(
            project_id = task.project_id,
            target_component = task.source_component,
        )
        for rule in rules:
            valid = valid_concept_ids.get(str(rule.source_component.component_id), False)
            if valid:
                if rule.source_component.component_id == valid.get('id') and rule.mapcorrelation == valid.get('correlation'):
                    # logger.info(f"[ECL vs RULES] Task {task.id} rule en correlation correct")
                    True
                else:
                    logger.info(f"[ECL vs RULES] Task {task.id} rule en correlation incorrect - HIT")
                    obj, created = MappingTaskAudit.objects.get_or_create(
                                task=task,
                                audit_type="Mismatch ECL vs rules",
                                hit_reason='Er is een regel aanwezig die er niet hoort - type 1',
                            )
            else:
                # ConceptID should not be there at all
                logger.info(f"[ECL vs RULES] Task {task.id} / Rule not present - HIT")
                obj, created = MappingTaskAudit.objects.get_or_create(
                        task=task,
                        audit_type="Mismatch ECL vs rules",
                        hit_reason='Er is een regel aanwezig die er niet hoort / regels komen in 2 ECL queries voor met andere correlatie - type 2',
                    )


    else:
        logger.info(f"[ECL vs RULES] Task {task.id} is not an ECL-1 task. No check.")