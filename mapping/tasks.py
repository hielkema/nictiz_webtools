# Create your tasks here
from __future__ import absolute_import, unicode_literals
from celery import shared_task
import time, json
from celery.task.schedules import crontab
from celery.result import AsyncResult
from celery.decorators import periodic_task
from celery.utils.log import get_task_logger
import xmltodict
from .forms import *
from .models import *
import urllib.request
from pandas import read_excel, read_csv

# Get latest snowstorm client. Set master or develop
# branch = "develop"
# url = 'https://raw.githubusercontent.com/mertenssander/python_snowstorm_client/' + \
#     branch+'/snowstorm_client.py'
# urllib.request.urlretrieve(url, 'snowstorm_client.py')
from snowstorm_client import Snowstorm

logger = get_task_logger(__name__)

@shared_task
def import_snomed_async(focus=None):
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
        codesystem_obj = MappingCodesystem.objects.get(id='1')
        obj, created = MappingCodesystemComponent.objects.get_or_create(
            codesystem_id_id=codesystem_obj.id,
            component_id=conceptid,
        )
        print("CREATED **** ",codesystem_obj, conceptid)
        # Add data not used for matching
        obj.component_title = str(concept['fsn']['term'])
        extra = {
            'Preferred term' : str(concept['pt']['term']),
        }
        obj.component_extra_dict = json.dumps(extra)
        # Save
        obj.save()

@shared_task
def import_labcodeset_async():
    with open('/webserver/mapping/resources/labcodeset/labconcepts-20190520-100827775.xml') as fd:
        doc = xmltodict.parse(fd.read())

        # Lijst voor alle materialen maken
        all_materials = []
        for material in doc['publication']['materials']['material']:
            try:
                # print(material.get('@id'), material.get('@code'), material.get('@displayName'))
                all_materials.append({
                    'id' : material.get('@id'),
                    'code' : material.get('@code'),
                    'displayName' : material.get('@displayName'),
                })
            except:
                print('Fout in maken materialenlijst')

        # Verwerken loincConcepts
        i=0 # Teller voor debug
        for component in doc['publication']['lab_concepts']['lab_concept']:
            print("loincConcept: ", i, component['loincConcept']['@loinc_num'])
            # Materialen van huidig concept in lijst zetten
            material_list = []
            try:
                # Materiaal is: component['materials']['material']['@ref']
                material_list.append(component['materials']['material']['@ref'])
            except:
                try:
                    for material in component['materials']['material']:
                        # Materiaal is: material['@ref']
                        material_list.append(material['@ref'])
                except:
                    material_list.append('Materiaal error')
            logger.info(material_list)
            # Materiaal -> snomed
            material_list_snomed = []
            for material in material_list:
                print("LOINC material code", material)
                filterr = filter(lambda x : x['id'] == material, all_materials)
                for item in filterr:
                    # print("FILTERED ITEM: ", item)
                    material_list_snomed.append({
                        'Materiaal ID' : item.get('id'),
                        'SCTID' : item.get('code'),
                        'FSN' : item.get('displayName'),
                    })

            # Concept -> database
            codesystem = MappingCodesystem.objects.get(id='3') # codesystem 3 = labcodeset
            # Data used for matching:
            obj, created = MappingCodesystemComponent.objects.get_or_create(
                codesystem_id=codesystem,
                component_id=component['loincConcept']['@loinc_num'],
            )
            # Additional data:
            try:
                loinc_component = component['loincConcept']['translation']['component']
                loinc_property  = component['loincConcept']['translation']['property']
                loinc_timing    = component['loincConcept']['translation']['timing']
                loinc_system    = component['loincConcept']['translation']['system']
                loinc_scale     = component['loincConcept']['translation']['scale']
                loinc_class     = component['loincConcept']['translation']['class']
                loinc_orderObs  = component.get('loincConcept',{}).get('orderObs')
            except:
                loinc_component = component.get('loincConcept',{}).get('component')
                loinc_property  = component.get('loincConcept',{}).get('property')
                loinc_timing    = component.get('loincConcept',{}).get('timing')
                loinc_system    = component.get('loincConcept',{}).get('system')
                loinc_scale     = component.get('loincConcept',{}).get('scale')
                loinc_class     = component.get('loincConcept',{}).get('class')
                loinc_orderObs  = component.get('loincConcept',{}).get('orderObs')

            term_en = component['loincConcept']['longName']
            term_nl = component['loincConcept'].get('translation',{}).get('longName','Geen vertaling')
            obj.component_title     = term_en
            obj.component_extra_dict   = json.dumps({
                'Nederlands'            : term_nl,
                'Component'             : loinc_component,
                'Kenmerk'               : loinc_property,
                'Timing'                : loinc_timing,
                'Systeem'               : loinc_system,
                'Schaal'                : loinc_scale,
                'Klasse'                : loinc_class,
                'Aanvraag/Resultaat'    : loinc_orderObs,
                'Materialen'            : material_list_snomed,
            })
            obj.save()

            material_list = []
            # i+=1
            # if i>10:
            #     break

@shared_task
def add_mappings_ecl_1_task(task=None, query=False, preview=False):
    if query != False:
        if preview == True:
            print('Preview run task add_mappings_ecl_1_task')
            snowstorm = Snowstorm(baseUrl="https://snowstorm.test-nictiz.nl", defaultBranchPath="MAIN/SNOMEDCT-NL", debug=True)
            results = snowstorm.findConcepts(ecl=query)
            return results
        else:
            print('Production run task add_mappings_ecl_1_task')
            # Delete existing rules
            task = MappingTask.objects.get(id=task)
            rules = MappingRule.objects.filter(target_component=task.source_component, project_id=task.project_id)
            print(rules)
            rules.delete()
            snowstorm = Snowstorm(baseUrl="https://snowstorm.test-nictiz.nl", defaultBranchPath="MAIN/SNOMEDCT-NL", debug=True)
            results = snowstorm.findConcepts(ecl=query)
            for result in results.values():
                # Snomed is hardcoded id 1. TODO - make this flexible
                source = MappingCodesystemComponent.objects.get(
                    component_id = result.get('conceptId'),
                    codesystem_id = "1",
                )
                obj, created = MappingRule.objects.get_or_create(
                    project_id=task.project_id,
                    source_component=source,
                    target_component=task.source_component,
                    active=True,
                )
                print("Created SNOMED mapping {source} to {target}".format(
                    source=source,
                    target=task.source_component,
                ))
            return results
    else:
        print("Query false -> delete en stop")
        # Delete existing rules
        task = MappingTask.objects.get(id=task)
        rules = MappingRule.objects.filter(target_component=task.source_component, project_id=task.project_id)
        rules.delete()
        return({})

@shared_task
def import_nhgverrichtingen_task():
    df = read_excel('/webserver/mapping/resources/nhg/Ingrepentabel_v3.xls')
    # Vervang lege cellen door False
    df=df.fillna(value=False)
    for index, row in df.iterrows():
        codesystem = MappingCodesystem.objects.get(id='2')
        obj, created = MappingCodesystemComponent.objects.get_or_create(
            codesystem_id=codesystem,
            component_id=row[0],
        )
        # Add data not used for matching
        obj.component_title     = row[1]
        obj.component_extra_1   = row[2]
        obj.component_extra_2   = row[3]
        obj.component_extra_3   = row[4]
        obj.component_extra_4   = row[5]
        obj.component_extra_5   = row[6]
        obj.component_extra_6   = row[7]
        obj.component_extra_7   = row[8]

        extra = {
            'Rubriek' : row[2],
            'Subrubriek' : row[3],
            'Tractus' : row[4],
            'CMSV-code' : row[5],
            'VO' : row[6],
            'VM' : row[7],
            'VV' : row[8],
        }
        obj.component_extra_dict = json.dumps(extra)
        # Save
        obj.save()

@shared_task
def import_nhgbepalingen_task():
    df = read_csv(
        '/webserver/mapping/resources/nhg/NHG-Tabel 45 Diagnostische bepalingen - versie 31 - bepaling.txt',
        sep='\t',
        header = 1,
        )
    i=0
    # Vervang lege cellen door False
    df=df.fillna(value=False)

    # Verwerk dataset -> database
    for index, row in df.iterrows():
        i+=1
        # if i > 5: break

        # Transformeren materiaal -> Snomed koppeling
        if row[2] == 'B': voorstel_materiaal = '119297000 bloed (monster)'
        if row[2] == 'BA': voorstel_materiaal = '122552005 arterieel bloed (monster)'
        if row[2] == 'BC': voorstel_materiaal = '122554006 capillair bloed (monster)'
        if row[2] == 'BD': voorstel_materiaal = '119297000 bloed (monster)'
        if row[2] == 'BP': voorstel_materiaal = '119361006 plasma (monster)'
        if row[2] == 'BQ': voorstel_materiaal = '119297000 bloed (monster)'
        if row[2] == 'BS': voorstel_materiaal = '119364003 serum (monster)'
        if row[2] == 'DA': voorstel_materiaal = '258664003 plakbandpreparaat (monster)'
        if row[2] == 'DF': voorstel_materiaal = '119339001 feces (monster)'
        if row[2] == 'DN': voorstel_materiaal = '309185002 monster uit cavitas oris (monster)'
        if row[2] == 'DO': voorstel_materiaal = '447955000 Specimen from rectum (specimen)'
        if row[2] == 'DS': voorstel_materiaal = '119342007 speeksel (monster)'
        if row[2] == 'DU': voorstel_materiaal = '119379005 Specimen from stomach (specimen)'
        if row[2] == 'FS': voorstel_materiaal = '309128003 oogvocht (monster)'
        if row[2] == 'NL': voorstel_materiaal = '258450006 liquor cerebrospinalis (monster)'
        if row[2] == 'O': voorstel_materiaal = '123038009 monster (monster)'
        if row[2] == 'OH': voorstel_materiaal = '123038009 monster (monster)'
        if row[2] == 'OO': voorstel_materiaal = '123038009 monster (monster)'
        if row[2] == 'OQ': voorstel_materiaal = '123038009 monster (monster)'
        if row[2] == 'OV': voorstel_materiaal = '123038009 monster (monster)'
        if row[2] == 'RB': voorstel_materiaal = '119389009 monster uit keelholte (monster)'
        if row[2] == 'RK': voorstel_materiaal = '258529004 Throat swab (specimen)'
        if row[2] == 'RM': voorstel_materiaal = '447154002 Specimen from nose (specimen)'
        if row[2] == 'RN': voorstel_materiaal = '168141000 vloeistof uit neus (monster)'
        if row[2] == 'RP': voorstel_materiaal = '418564007 pleuravocht (monster)'
        if row[2] == 'RS': voorstel_materiaal = '119334006 Sputum specimen (specimen)'
        if row[2] == 'RU': voorstel_materiaal = '119336008 uitgeademde lucht (monster)'
        if row[2] == 'SA': voorstel_materiaal = '608969007 Specimen from skin (specimen)'
        if row[2] == 'SE': voorstel_materiaal = '122568004 Exudate specimen from wound (specimen)'
        if row[2] == 'SH': voorstel_materiaal = '119326000 haar (monster)'
        if row[2] == 'SN': voorstel_materiaal = '119327009 Nail specimen (specimen)'
        if row[2] == 'SP': voorstel_materiaal = '119323008 Pus specimen (specimen)'
        if row[2] == 'SS': voorstel_materiaal = '446952006 schraapsel van huid (monster)'
        if row[2] == 'SZ': voorstel_materiaal = '122569007 zweet (monster)'
        if row[2] == 'U': voorstel_materiaal = '122575003 urine (monster)'
        if row[2] == 'UC': voorstel_materiaal = '46121000146104 Urinary system calculus sample (specimen)'
        if row[2] == 'UD': voorstel_materiaal = '122575003 urine (monster)'
        if row[2] == 'UE': voorstel_materiaal = '276833005 24 hour urine sample (specimen)'
        if row[2] == 'UM': voorstel_materiaal = '258574006 midstream-urine (monster)'
        if row[2] == 'US': voorstel_materiaal = '122567009 urinesediment (monster)'
        if row[2] == 'UU': voorstel_materiaal = '119393003 monster uit urethra (monster)'
        if row[2] == 'WA': voorstel_materiaal = '119373006 vruchtwater (monster)'
        if row[2] == 'WB': voorstel_materiaal = '122556008 navelstrengbloed (monster)'
        if row[2] == 'XA': voorstel_materiaal = '309053003 Female genital sample (specimen)'
        if row[2] == 'XC': voorstel_materiaal = '119395005 monster uit cervix uteri (monster)'
        if row[2] == 'XP': voorstel_materiaal = '276446009 Cervical smear sample (specimen)'
        if row[2] == 'XV': voorstel_materiaal = '258577004 fluor vaginalis (monster)'
        if row[2] == 'XP': voorstel_materiaal = '119397002 Specimen from penis (specimen)'
        if row[2] == 'YX': voorstel_materiaal = '119347001 Seminal fluid specimen (specimen)'
        if not voorstel_materiaal: voorstel_materiaal = "Geen materiaalcode"
        codesystem = MappingCodesystem.objects.get(id='4')
        obj, created = MappingCodesystemComponent.objects.get_or_create(
            codesystem_id=codesystem,
            component_id=row[0],
        )
        obj.component_title = row[4]
        if str(row[12])[-1:] == "V": 
            vervallen = "Bepaling is vervallen"
        else:
            vervallen = "Bepaling is actief"
        extra = {
            'Omschrijving' : row[4],
            'Bepaling nummer' : row[0],
            'Aanvraag/Uitslag/Beide' : row[6],
            'Materiaal NHG' : row[2],
            'Materiaal voorstel Snomed' : voorstel_materiaal,
            'Vraagtype' : row[14],
            'Eenheid' : row[16],
            'Versie mutatie' : row[12],
            'Actief?' : vervallen,
        }
        # Clear material for next loop
        voorstel_materiaal = ''
        # print(extra)
        obj.component_extra_dict = json.dumps(extra)
        obj.save()

@shared_task
def audit_async(audit_type=None, project=None, task_id=None):
    project = MappingProject.objects.get(id=project)
    if task_id == None:
        tasks = MappingTask.objects.filter(project_id=project)
    else:
        tasks = MappingTask.objects.filter(project_id=project, id=task_id)
        
    # Create exclusion lists for targets such as specimen in project NHG diagnostische bepalingen -> LOINC+Snomed
    snowstorm = Snowstorm(baseUrl="https://snowstorm.test-nictiz.nl", defaultBranchPath="MAIN/SNOMEDCT-NL", debug=True)
    results = snowstorm.findConcepts(ecl='<<123038009')
    specimen_exclusion_list = []
    for concept in results:
        specimen_exclusion_list.append(str(concept))

    if audit_type == "multiple_mapping":
        # Functions needed for audit
        def checkConsecutive(l): 
            try:
                return sorted(l) == list(range(min(l), max(l)+1)) 
            except:
                return False
        # Sanity check
        logger.info('Starting multiple mapping audit')
        logger.info('Auditing project: #{0} {1}'.format(project.id, project.title))
        # Loop through all tasks
        for task in tasks:
            # Print task identification, sanity check
            logger.info('Checking task for: {0}'.format(task.source_component.component_title))

            # Delete all old audit hits for this task if not whitelisted
            delete = MappingTaskAudit.objects.filter(task=task, ignore=False).delete()
            logger.info(delete)

            # Get all mapping rules for the current task
            rules = MappingRule.objects.filter(project_id=project, source_component=task.source_component).order_by('mappriority')
            logger.info('Number of rules: {0}'.format(rules.count()))
            # Create list for holding all used map priorities
            mapping_priorities = []
            mapping_targets = []
            mapping_target_idents = []
            # Loop through individual rules
            for rule in rules:
                # Append priority to list for analysis
                mapping_priorities.append(rule.mappriority)
                mapping_targets.append(rule.target_component)
                mapping_target_idents.append(rule.target_component.component_id)
                logger.info('Rule: {0}'.format(rule))



                # Audits valid for all rules
                if rule.mappriority == '' or rule.mappriority == None:
                    obj, created = MappingTaskAudit.objects.get_or_create(
                                task=task,
                                audit_type=audit_type,
                                hit_reason='Regel heeft geen prioriteit',
                            )
                if rule.mapadvice == '':
                    obj, created = MappingTaskAudit.objects.get_or_create(
                                task=task,
                                audit_type=audit_type,
                                hit_reason='Regel heeft geen mapadvice',
                            )
                if rule.source_component == rule.target_component:
                    obj, created = MappingTaskAudit.objects.get_or_create(
                                task=task,
                                audit_type=audit_type,
                                hit_reason='Regel mapt naar zichzelf',
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
                                    audit_type=audit_type,
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
                                    audit_type=audit_type,
                                    hit_reason='Mapt niet naar labcodeset',
                                )

            # Look for rules with the same target component
            for target in mapping_targets:
                other_rules = MappingRule.objects.filter(target_component=target)
                if other_rules.count() > 0:
                    other_tasks_same_target = []
                    for other_rule in other_rules:
                        other_tasks = MappingTask.objects.filter(source_component=other_rule.source_component)
                        for other_task in other_tasks:
                            other_tasks_same_target.append(other_task.id)

                    for other_rule in other_rules:
                        # Separate rule for project 3 (NHG Diagn-LOINC/SNOMED)    
                        if (rule.project_id.id == 3) and (other_rule.target_component.component_id in specimen_exclusion_list):
                            logger.info('Project 3 -> negeer <<specimen voor dubbele mappings')
                        else:
                            if other_rule.source_component != task.source_component:
                                obj, created = MappingTaskAudit.objects.get_or_create(
                                    task=task,
                                    audit_type=audit_type,
                                    hit_reason='Meerdere taken {} gebruiken hetzelfde target: component #{} - {}'.format(other_tasks_same_target, other_rule.target_component.component_id, other_rule.target_component.component_title)
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
                try:
                    if sorted(mapping_priorities)[0] != 1:
                        obj, created = MappingTaskAudit.objects.get_or_create(
                                task=task,
                                audit_type=audit_type,
                                hit_reason='Taak heeft meerdere mapping rules: geen mapprioriteit 1'
                            )
                except:
                    obj, created = MappingTaskAudit.objects.get_or_create(
                                task=task,
                                audit_type=audit_type,
                                hit_reason='Probleem met controleren prioriteiten: meerdere regels zonder prioriteit?'
                            )
                if rules.last().mapadvice != 'Anders':
                    obj, created = MappingTaskAudit.objects.get_or_create(
                            task=task,
                            audit_type=audit_type,
                            hit_reason='Taak heeft meerdere mapping rules: laatste prioriteit is niet gelijk aan Anders'
                        )
            else:
                logger.info('No rules for current task')
            