# Create your tasks here
from __future__ import absolute_import, unicode_literals
from celery import shared_task
import time
from celery.task.schedules import crontab
from celery.result import AsyncResult
from celery.decorators import periodic_task
from celery.utils.log import get_task_logger
from .forms import *
from .models import *
import urllib.request
# Get latest snowstorm client. Set master or develop
# branch = "develop"
# url = 'https://raw.githubusercontent.com/mertenssander/python_snowstorm_client/' + \
#     branch+'/snowstorm_client.py'
# urllib.request.urlretrieve(url, 'snowstorm_client.py')
from snowstorm_client import Snowstorm

logger = get_task_logger(__name__)

@shared_task
def import_snomed_async(focus=None, codesystem=None):
    snowstorm = Snowstorm(
        baseUrl="https://snowstorm.test-nictiz.nl",
        debug=True,
        preferredLanguage="nl",
        defaultBranchPath="MAIN/SNOMEDCT-NL",
    )
    result = snowstorm.findConcepts(ecl="<<"+focus)
    print(result)

    for conceptid, concept in result.items():
        # Get or create based on 2 criteria (fsn & codesystem)
        codesystem_obj = MappingCodesystem.objects.get(id=codesystem)
        obj, created = MappingCodesystemComponent.objects.get_or_create(
            codesystem_id_id=codesystem_obj.id,
            component_id=conceptid,
        )
        print("CREATED **** ",codesystem, conceptid)
        # Add data not used for matching
        obj.component_title = str(concept['fsn']['term'])
        obj.component_extra_1 = str(concept['pt']['term'])

        # Save
        obj.save()

@shared_task
def audit_async(audit_type=None, project=None, task_id=None):
    project = MappingProject.objects.get(id=project)
    tasks = MappingTask.objects.filter(project_id=project)
    if audit_type == "multiple_mapping":
        # Functions needed for audit
        def checkConsecutive(l): 
            return sorted(l) == list(range(min(l), max(l)+1)) 
        # Sanity check
        logger.info('Starting multiple mapping audit')
        logger.info('Auditing project: #{0} {1}'.format(project.id, project.title))
        # Loop through all tasks
        for task in tasks:
            # Print task identification, sanity check
            logger.info('Checking task for: {0}'.format(task.source_component.component_title))

            # Delete all old audit hits for this task if not whitelisted
            MappingTaskAudit.objects.filter(task=task, ignore=False).delete()

            # Get all mapping rules for the current task
            rules = MappingRule.objects.filter(project_id=project, source_component=task.source_component)
            logger.info('Number of rules: {0}'.format(rules.count()))
            # Create list for holding all used map priorities
            mapping_priorities = []
            mapping_targets = []
            # Loop through individual rules
            for rule in rules:
                # Append priority to list for analysis
                mapping_priorities.append(rule.mappriority)
                mapping_targets.append(rule.target_component)
                logger.info('Rule: {0}'.format(rule))
            # Look for rules with the same target component
            for target in mapping_targets:
                other_rules = MappingRule.objects.filter(target_component=target)
                if other_rules.count() > 0:
                    for other_rule in other_rules:
                        if other_rule.source_component != task.source_component:
                            obj, created = MappingTaskAudit.objects.get_or_create(
                                task=task,
                                audit_type=audit_type,
                                hit_reason='Andere taak gebruikt hetzelfde target: component #{} - {}'.format(other_rule.target_component.component_id, other_rule.target_component.component_title)
                            )
            # Specific rules for single or multiple mappings
            if rules.count() == 1:
                logger.info('Mappriority 1?: {0}'.format(rules[0].mappriority))
                if rules[0].mappriority != 1:
                    obj, created = MappingTaskAudit.objects.get_or_create(
                            task=task,
                            audit_type=audit_type,
                            hit_reason='Taak heeft 1 mapping rule: prioriteit is niet 1'
                        )
                if rules[0].mapadvice != 'Altijd':
                    obj, created = MappingTaskAudit.objects.get_or_create(
                            task=task,
                            audit_type=audit_type,
                            hit_reason='Taak heeft 1 mapping rule: map advice is niet Altijd'
                        )
            elif rules.count() > 1:
                logger.info('Consecutive priorities?: {0} -> {1}'.format(mapping_priorities, checkConsecutive(mapping_priorities)))
                if not checkConsecutive(mapping_priorities):
                    obj, created = MappingTaskAudit.objects.get_or_create(
                            task=task,
                            audit_type=audit_type,
                            hit_reason='Taak heeft meerdere mapping rules: geen opeenvolgende prioriteit'
                        )
                if sorted(mapping_priorities)[0] != 1:
                    obj, created = MappingTaskAudit.objects.get_or_create(
                            task=task,
                            audit_type=audit_type,
                            hit_reason='Taak heeft meerdere mapping rules: geen mapprioriteit 1'
                        )
                if sorted(mapping_priorities)[-1] != 'Anders':
                    obj, created = MappingTaskAudit.objects.get_or_create(
                            task=task,
                            audit_type=audit_type,
                            hit_reason='Taak heeft meerdere mapping rules: laatste prioriteit is niet gelijk aan Anders'
                        )
            else:
                logger.info('No rules for current task')
            