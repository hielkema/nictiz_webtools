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
import xmltodict
from ..models import *
import urllib.request
import environ

# Import environment variables
env = environ.Env(DEBUG=(bool, False))
# reading .env file
environ.Env.read_env(env.str('ENV_PATH', '.env'))

logger = get_task_logger(__name__)

# Example task
@shared_task
def check_rule_attributes(taskid):
    logger.info("Spawned check_rule_attributes for TASK "+str(taskid))
    hit = False
    task = MappingTask.objects.select_related(
        'project_id',
        'source_component',
        'source_component__codesystem_id',
        'source_codesystem',
        'target_codesystem',
        'user',
        'status',
    ).get(id=taskid)
    
    # Only do something if the project is of the N-1 type. No use checking this for ECL-1.
    # Create exclusion lists for targets such as specimen in project NHG diagnostische bepalingen -> LOINC+Snomed
    specimen_exclusion_list = json.loads(MappingCodesystemComponent.objects.get(component_id='123038009').descendants)


    # Functions needed for audit
    def checkConsecutive(l): 
        try:
            return sorted(l) == list(range(min(l), max(l)+1)) 
        except:
            return False
    # Sanity check
    logger.info('Starting multiple mapping audit')
    logger.info('Auditing project: #{0} {1}'.format(task.project_id.id, task.project_id.title))

    # Print task identification, sanity check
    # logger.info('Checking task for: {0}'.format(task.source_component.component_title))

    # Checks for the entire task
    # If source component contains active/deprecated designation ->
    extra_dict = task.source_component.component_extra_dict
    if extra_dict.get('Actief',False):
        # If source code is deprecated ->
        if extra_dict.get('Actief') == "False":
            obj, created = MappingTaskAudit.objects.get_or_create(
                        task=task,
                        audit_type="Deprecated source",
                        hit_reason='Item in bron-codesystem is vervallen',
                    )


    # Get all mapping rules for the current task
    rules = MappingRule.objects.filter(project_id=task.project_id, source_component=task.source_component).order_by('mappriority')
    # logger.info('Number of rules: {0}'.format(rules.count()))
    # Create list for holding all used map priorities
    mapping_priorities = []
    mapping_groups = []
    mapping_targets = []
    mapping_target_idents = []
    mapping_prio_per_group = {}
    # Loop through individual rules
    for rule in rules:
        # Append priority to list for analysis
        mapping_priorities.append(rule.mappriority)
        if rule.mapgroup == None:
            mapgroup = 1
        else:
            mapgroup = rule.mapgroup
        mapping_groups.append(mapgroup)
        mapping_targets.append(rule.target_component)
        mapping_target_idents.append(rule.target_component.component_id)

        if not mapping_prio_per_group.get(rule.mapgroup,False):
            mapping_prio_per_group.update({
                rule.mapgroup: [rule.mappriority]
            })
        else:
            mapping_prio_per_group[rule.mapgroup].append(rule.mappriority)

        # logger.info('Rule: {0}'.format(rule))



        # Audits valid for all rules
        if rule.mappriority == '' or rule.mappriority == None:
            if rule.project_id.use_mappriority:
                obj, created = MappingTaskAudit.objects.get_or_create(
                            task=task,
                            audit_type="Priority error",
                            hit_reason='Regel heeft geen prioriteit',
                        )
        if rule.mapadvice == '':
            if rule.project_id.use_mapadvice:
                obj, created = MappingTaskAudit.objects.get_or_create(
                            task=task,
                            audit_type="Mapadvice error",
                            hit_reason='Regel heeft geen mapadvice',
                        )
        if rule.source_component == rule.target_component:
            obj, created = MappingTaskAudit.objects.get_or_create(
                        task=task,
                        audit_type="Maps to self",
                        hit_reason='Regel mapt naar zichzelf',
                    )

        # If Target component contains active/deprecated designation ->
        extra_dict = rule.target_component.component_extra_dict
        if extra_dict.get('Actief',{}):
            # If source code is deprecated ->
            if extra_dict.get('Actief') == "False":
                obj, created = MappingTaskAudit.objects.get_or_create(
                            task=task,
                            audit_type="Deprecated target",
                            hit_reason='Item in target-codesystem is vervallen',
                        )

    # For project 3 (NHG diag -> LOINC/SNOMED):
    if (task.project_id.id == 3) and rules.count() > 0:
        # Check if one of the targets is <<specimen
        check = False
        for target in mapping_targets:
            if target.component_id in specimen_exclusion_list:
                check = True
        if check == False:
            obj, created = MappingTaskAudit.objects.get_or_create(
                            task=task,
                            audit_type="Missing target",
                            hit_reason='Mapt niet naar <<specimen',
                        )
        # Check if one of the targets is a LOINC item
        check = False
        for target in mapping_targets:
            if target.codesystem_id.id == 3:
                check = True
        if check == False:
            obj, created = MappingTaskAudit.objects.get_or_create(
                            task=task,
                            audit_type="Missing target",
                            hit_reason='Mapt niet naar labcodeset',
                        )

    # Look for rules with the same target component
    for target in mapping_targets:
        other_rules = MappingRule.objects.filter(target_component=target).order_by('id')
        if other_rules.count() > 0:
            other_tasks_same_target = []
            for other_rule in other_rules:
                other_tasks = MappingTask.objects.filter(source_component=other_rule.source_component)
                for other_task in other_tasks:
                    other_tasks_same_target.append(f"{other_task.source_component.component_id} - {other_task.source_component.component_title}")

            for other_rule in other_rules:
                # Separate rule for project 3 (NHG Diagn-LOINC/SNOMED)    
                if (rule.project_id.id == 3) and (other_rule.target_component.component_id in specimen_exclusion_list):
                    # logger.info('Project 3 -> negeer <<specimen voor dubbele mappings')
                    True
                # Separate rule for project 3 (NHG Diagn-LOINC/SNOMED)    
                elif (rule.project_id.id == 13) and (other_rule.target_component.component_id in specimen_exclusion_list):
                    # logger.info('Project 13 -> negeer <<specimen voor dubbele mappings')
                    True
                elif (rule.project_id.id == 4) and (other_rule.target_component.component_id in json.loads(MappingCodesystemComponent.objects.get(component_id='182353008').descendants)):
                    # logger.info('Project 7 -> negeer <<zijde voor dubbele mappings')
                    True
                elif (rule.project_id.id == 7) and (other_rule.target_component.component_id in json.loads(MappingCodesystemComponent.objects.get(component_id='118718002').descendants)):
                    # logger.info('Project 7 -> negeer <<procedure op huid voor dubbele mappings')
                    True
                else:
                    if (other_rule.source_component != task.source_component) and (task.source_component.codesystem_id == other_rule.source_component.codesystem_id):
                        obj, created = MappingTaskAudit.objects.get_or_create(
                            task=task,
                            audit_type="Target used in multiple tasks",
                            hit_reason='Meerdere taken {} gebruiken hetzelfde target: component #{} - {}'.format(other_tasks_same_target, other_rule.target_component.component_id, other_rule.target_component.component_title)
                        )
                    
    # Specific rules for single or multiple mappings
    if rules.count() == 1:
        # logger.info('Mappriority 1?: {0}'.format(rules[0].mappriority))
        if rules[0].mappriority != 1 and rules[0].project_id.use_mappriority:
            obj, created = MappingTaskAudit.objects.get_or_create(
                    task=task,
                    audit_type="Priority error",
                    hit_reason='Taak heeft 1 mapping rule: prioriteit is niet 1'
                )
        if rules[0].mapadvice != 'Altijd' and rules[0].project_id.use_mapadvice:
            obj, created = MappingTaskAudit.objects.get_or_create(
                    task=task,
                    audit_type="Advice error",
                    hit_reason='Taak heeft 1 mapping rule: map advice is niet Altijd'
                )
    elif rules.count() > 1:
        # Check for order in groups
        # logger.info('Mapping groups: {0}'.format(mapping_groups))
        groups_ex_duplicates = list(dict.fromkeys(mapping_groups))
        # logger.info('Mapping groups no duplicates: {0}'.format(groups_ex_duplicates))
        # logger.info('Consecutive groups?: {0} -> {1}'.format(groups_ex_duplicates, checkConsecutive(groups_ex_duplicates)))
        if not checkConsecutive(groups_ex_duplicates):
            obj, created = MappingTaskAudit.objects.get_or_create(
                    task=task,
                    audit_type="Priority error",
                    hit_reason='Taak heeft meerdere mapping groups: geen opeenvolgende prioriteit'
                )

        # print("PRIO PER GROUP",mapping_prio_per_group)

        # Rest in loop door prio's uitvoeren?
        for key in mapping_prio_per_group.items():
            # logger.info('Checking group {}'.format(str(key[0])))
            priority_list = key[1]
            # logger.info('Consecutive priorities?: {0} -> {1}'.format(priority_list, checkConsecutive(priority_list)))
            if not checkConsecutive(priority_list):
                obj, created = MappingTaskAudit.objects.get_or_create(
                        task=task,
                        audit_type="Priority error",
                        hit_reason='Groep heeft meerdere mapping rules: geen opeenvolgende prioriteit'
                    )
            try:
                if sorted(priority_list)[0] != 1:
                    obj, created = MappingTaskAudit.objects.get_or_create(
                            task=task,
                            audit_type="Priority error",
                            hit_reason='Groep heeft meerdere mapping rules: geen mapprioriteit 1'
                        )
            except:
                obj, created = MappingTaskAudit.objects.get_or_create(
                            task=task,
                            audit_type="Priority error",
                            hit_reason='Probleem met controleren prioriteiten: meerdere regels zonder prioriteit?'
                        )
            # if rules.last().mapadvice != 'Anders':
            #     obj, created = MappingTaskAudit.objects.get_or_create(
            #             task=task,
            #             audit_type=audit_type,
            #             hit_reason='Taak heeft meerdere mapping rules: laatste prioriteit is niet gelijk aan Anders'
            #         )
    else:
        # logger.info('No rules for current task')
        True