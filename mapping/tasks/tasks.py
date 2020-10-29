# Create your tasks here
from __future__ import absolute_import, unicode_literals
from celery import shared_task
from celery.execute import send_task    
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
import sys, os

# Import environment variables
env = environ.Env(DEBUG=(bool, False))
# reading .env file
environ.Env.read_env(env.str('ENV_PATH', '.env'))

# Get latest snowstorm client. Set master or develop
# branch = "develop"
# url = 'https://raw.githubusercontent.com/mertenssander/python_snowstorm_client/' + \
#     branch+'/snowstorm_client.py'
# urllib.request.urlretrieve(url, 'snowstorm_client.py')
from snowstorm_client import Snowstorm


from celery.task.control import  inspect
i = inspect()

# from nictiz_webtools.mapping.tasks.nhg_labcodeset import nhg_loinc_order_vs_observation

logger = get_task_logger(__name__)

@shared_task
def UpdateECL1Task(record_id, query):
    currentQuery = MappingEclPart.objects.get(id = record_id)
    currentQuery.result = {}
    currentQuery.finished = False
    currentQuery.error = None
    currentQuery.failed = False
    currentQuery.save()
    try:
        snowstorm = Snowstorm(
            baseUrl="https://snowstorm.test-nictiz.nl",
            debug=False,
            preferredLanguage="nl",
            defaultBranchPath="MAIN/SNOMEDCT-NL",
        )
        result = snowstorm.findConcepts(ecl=query.strip())

        try:
            num_results = len(result)
        except Exception as e:
            num_results = 0
            print("Error in UpdateECL1Task:",e)

        currentQuery.result = {
            'concepts': result,
            'numResults': num_results,
        }
        currentQuery.finished = True
        currentQuery.error = None
        currentQuery.failed = False
        currentQuery.save()
        return str(currentQuery)
    except Exception as e:
        currentQuery.result = {
            'concepts': {},
            'numResults': 0,
        }
        currentQuery.finished = True
        currentQuery.failed = True
        currentQuery.error = f"Fout in Snowstorm connectie. Waarschijnlijk is de ECL query niet juist. Error: {str(e)}"
        currentQuery.save()
        return {
            'query' : str(currentQuery),
            'error' : str(e),
        }

# @shared_task
# def check_snomed_active(concept = None):
#     snowstorm = Snowstorm(
#         baseUrl="https://snowstorm.test-nictiz.nl",
#         debug=False,
#         preferredLanguage="nl",
#         defaultBranchPath="MAIN/SNOMEDCT-NL",
#     )
#     result = snowstorm.getConceptById(id=concept)
#     obj = MappingCodesystemComponent.objects.get(component_id = concept)
#     extra_dict = obj.component_extra_dict
#     extra_dict.update({'Actief':result.get('active')})
#     obj.component_extra_dict = extra_dict
#     obj.save()
#     print(extra_dict)
#     print(obj.component_extra_dict)
    
# @shared_task
# def import_snomed_async(focus=None):
#     snowstorm = Snowstorm(
#         baseUrl="https://snowstorm.test-nictiz.nl",
#         debug=False,
#         preferredLanguage="nl",
#         defaultBranchPath="MAIN/SNOMEDCT-NL",
#     )
#     result = snowstorm.findConcepts(ecl="<<"+focus)
#     print('Found {} concepts'.format(len(result)))

#     # Set snomed concepts in the database as inactive, if they are not retrieved through ECL (this means they are not active and will not be updated)
#     ##### ALERT - can't be done this way! Not all concepts are descendants of this focus concept. Should be a separately scheduled task that checks the entire library.
#     # snomed = MappingCodesystem.objects.get(id='1')
#     # concepts = MappingCodesystemComponent.objects.filter(codesystem_id=snomed)
#     # concepts = concepts.exclude(component_id__in = list(result.keys()))
#     # concepts.update(component_extra_dict = {
#     #     'Actief':'False',
#     # })
#     # print(f"Set {concepts.count()} as inactive - were not in ECL query from focus concept {focus}.")

#     # Spawn task for each concept
#     for conceptid, concept in result.items():
#         payload = {
#             'conceptid' : conceptid,
#             'concept'   : concept,
#         }
#         update_snomedConcept_async.delay(payload)

# @shared_task
# def update_snomedConcept_async(payload=None):
#     snowstorm = Snowstorm(
#         baseUrl="https://snowstorm.test-nictiz.nl",
#         debug=False,
#         preferredLanguage="nl",
#         defaultBranchPath="MAIN/SNOMEDCT-NL",
#     )
    
#     concept = payload.get('concept')
#     conceptid = payload.get('conceptid')

#     # Get or create based on 2 criteria (fsn & codesystem)
#     codesystem_obj = MappingCodesystem.objects.get(id='1')
#     obj, created = MappingCodesystemComponent.objects.get_or_create(
#         codesystem_id_id=codesystem_obj.id,
#         component_id=conceptid,
#     )
#     print("HANDLED **** Codesystem [{}] / Concept {}".format(codesystem_obj, conceptid))
#     # Add data not used for matching
#     #### Add sticky audit hit if concept was already in database and title changed
#     # term_en = concept['fsn']['term']
#     # if (obj.component_title != None) and (obj.component_title != term_en):
#     #     print(f"{obj.component_title} in database != {term_en} - audit hit maken")

#     #     # Find rules using this component (both from and to)
#     #     hit_rules = MappingRule.objects.filter(source_component = obj)
#     #     for hit_rule in hit_rules: 
#     #         # Find tasks using any of the involved components
#     #         ## From
#     #         tasks = MappingTask.objects.filter(source_component = hit_rule.source_component, project_id__project_type = '1')
#     #         print(f"Audit-tagging [from] {tasks.count()} tasks.")
#     #         for task in tasks:
#     #                 print(f"Audit hit maken voor taak {str(task)}")
#     #                 audit, created_audit = MappingTaskAudit.objects.get_or_create(
#     #                         task=task,
#     #                         audit_type="IMPORT",
#     #                         sticky=True,
#     #                         hit_reason=f"Let op: een FSN is gewijzigd bij een update van het codestelsel. Betreft component {obj.codesystem_id.codesystem_title} {obj.component_id} - {term_en} [was {obj.component_title}]",
#     #                     )
#     #         ## To
#     #         tasks = MappingTask.objects.filter(source_component = hit_rule.target_component, project_id__project_type = '4')
#     #         print(f"Audit-tagging [to] {tasks.count()} tasks.")
#     #         for task in tasks:
#     #                 print(f"Audit hit maken voor taak {str(task)}")
#     #                 audit, created_audit = MappingTaskAudit.objects.get_or_create(
#     #                         task=task,
#     #                         audit_type="IMPORT",
#     #                         sticky=True,
#     #                         hit_reason=f"Let op: een FSN is gewijzigd bij een update van het codestelsel. Betreft component {obj.codesystem_id.codesystem_title} {obj.component_id} - {term_en} [was {obj.component_title}]",
#     #                     )
#     # else:
#     #     print(f"{obj.component_title} in database == {term_en} - geen hits")
#     try:
#         obj.component_title = str(concept['fsn']['term'])
#         extra = {
#             'Preferred term' : str(concept['pt']['term']),
#             'Actief'         : str(concept['active']),
#             'Effective time' : str(concept['effectiveTime']),
#             'Definition status'  : str(concept['definitionStatus']),
#         }

#         obj.descriptions = snowstorm.getDescriptions(id=str(conceptid)).get('categorized',{})

#         obj.parents     = json.dumps(list(snowstorm.getParents(id=conceptid)))
#         obj.children    = json.dumps(list(snowstorm.getChildren(id=conceptid)))
#         obj.descendants = json.dumps(list(snowstorm.findConcepts(ecl='<<'+conceptid)))
#         obj.ancestors   = json.dumps(list(snowstorm.findConcepts(ecl='>>'+conceptid)))

#         obj.component_extra_dict = extra
#         # Save
#         obj.save()

#         return str(obj)
#     except Exception as e:
#         print(f"[Error in shared task update_snomedConcept_async]: {str(e)}")
#         return(e)

@shared_task
def import_snomed_snowstorm(payload=None):
    def concept_data(concept):
        return {
            'id' : str(concept['conceptId']),
            'fsn' : str(concept['fsn']['term']),
            'pt'  : str(concept['pt']['term']),
            'active' : str(concept['active']),
            'effectiveTime' : str(concept['effectiveTime']),
            'definitionStatus' : str(concept['definitionStatus']),
        }

    def retrieve_concepts():
        search_after = ''
        output = []
        while True:
            url = f"https://snowstorm.test-nictiz.nl/browser/MAIN%2FSNOMEDCT-NL/concepts?searchAfter={search_after}&number=0&size=10000"
            req = urllib.request.Request(url)
            req.add_header('Accept-Language', 'nl')
            response = urllib.request.urlopen(req).read()
            result = json.loads(response.decode('utf-8'))

            search_after = result['searchAfter']
            total = result['total']
            # total = 5
            
            concept_list = [concept_data(concept) for concept in result['items']]
            
            output.extend(concept_list)
            print(f"Retrieved {len(result['items'])} - {len(output)}/{total} - {round((len(output)/total*100),0)}%")
            if len(output) >= total: break
        return output

    print(f"Starting [@shared_task: import_snomed_snowstorm]")

    concepts = retrieve_concepts()

    print(f"[@shared_task: import_snomed_snowstorm] Finished retrieving concepts. Moving on to database update.")

    updated_concepts = 0
    created_concepts = 0
    codesystem_obj = MappingCodesystem.objects.get(id='1')
    for concept in concepts:
        try:
            # Get or create based on 2 criteria (fsn & codesystem)
            obj, created = MappingCodesystemComponent.objects.get_or_create(
                codesystem_id_id=codesystem_obj.id,
                component_id=concept['id'],
            )
            obj.component_title = str(concept['fsn'])
            extra = {
                'Preferred term'    : str(concept['pt']),
                'Actief'            : str(concept['active']),
                'Effective time'    : str(concept['effectiveTime']),
                'Definition status' : str(concept['definitionStatus']),
            }
            obj.component_extra_dict = extra
            if created:
                created_concepts += 1
            else:
                updated_concepts += 1
            obj.save()
        except Exception as e:
            print(f"Error in [@shared_task: import_snomed_snowstorm]: {e}")

    print(f"[@shared_task: import_snomed_snowstorm] Finished updating database for FSN/metadata. Now firing task to update hierarchical info (parents/ancestors/children/descendants)")
    add_hierarchy_snomed.delay()
    return {
        'updated' : updated_concepts,
        'created' : created_concepts,
    }

@shared_task
def add_hierarchy_snomed():
    snowstorm = Snowstorm(
        baseUrl="https://snowstorm.test-nictiz.nl",
        debug=False,
        preferredLanguage="nl",
        defaultBranchPath="MAIN/SNOMEDCT-NL",
    )
    components = MappingCodesystemComponent.objects.filter(
        codesystem_id_id = '1'
    )
    for component in components:
        conceptid = component.component_id
        # component.descriptions = snowstorm.getDescriptions(id=str(conceptid)).get('categorized',{})
        component.parents     = json.dumps(list(snowstorm.getParents(id=conceptid)))
        component.children    = json.dumps(list(snowstorm.getChildren(id=conceptid)))
        component.descendants = json.dumps(list(snowstorm.findConcepts(ecl='<<'+conceptid)))
        component.ancestors   = json.dumps(list(snowstorm.findConcepts(ecl='>>'+conceptid)))
        component.save()
    print(f"[@shared_task: add_hierarchy_snomed] Finished updating SNOMED hierarchical data.")
    

@shared_task
def import_labcodeset_async():
    # Import pre-existent mappings as a comment
    try:
        df = read_excel('/webserver/mapping/resources/labcodeset/init_mapping_NHG45-LOINC.xlsx')
        # Vervang lege cellen door False
        df=df.fillna(value=False)
        codesystem = MappingCodesystem.objects.get(id='4') # NHG tabel 45
        user = User.objects.get(username='mertens')
        for index, row in df.iterrows():
            bepalingnr = row['bepalingsnr']
            notitie = row['Notitie']
            loinc_id = row['LOINC-id']
            loinc_name = row['LOINC-naam']
            component = MappingCodesystemComponent.objects.get(codesystem_id=codesystem, component_id=bepalingnr)
            try:
                if loinc_id != 'UNMAPPED':
                    task = MappingTask.objects.get(source_component=component)
                    comment = "Automatisch geïmporteerde legacy mapping: [{notitie}] LOINC-ID {loinc_id} - {loinc_name}".format(notitie=notitie, loinc_id=loinc_id, loinc_name=loinc_name)
                    MappingComment.objects.get_or_create(
                        comment_title = 'NHG-LOINC mapping (Legacy import)',
                        comment_task = task,
                        comment_body = comment,
                        comment_user = user,
                    )
            except:
                print('Geen taak voor dit concept')
                print(bepalingnr, notitie, loinc_id, loinc_name)
    except:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        error = 'Exc type: {} \n TB: {}'.format(exc_type, exc_tb.tb_lineno)
        print(error)

    # Import codesystem
    with open('/webserver/mapping/resources/labcodeset/labconcepts-20201022-165920601.xml') as fd:
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
            # logger.info(material_list)
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

            #### Add sticky audit hit if concept was already in database and title changed
            # if (obj.component_title != None) and (obj.component_title != term_en):
            #     print(f"{obj.component_title} in database != {term_en} - audit hit maken")

            #     # Find rules using this component (both from and to)
            #     hit_rules = MappingRule.objects.filter(source_component = obj)
            #     for hit_rule in hit_rules: 
            #         # Find tasks using any of the involved components
            #         ## From
            #         tasks = MappingTask.objects.filter(source_component = hit_rule.source_component, project_id__project_type = '1')
            #         print(f"Audit-tagging [from] {tasks.count()} tasks.")
            #         for task in tasks:
            #                 print(f"Audit hit maken voor taak {str(task)}")
            #                 audit, created_audit = MappingTaskAudit.objects.get_or_create(
            #                         task=task,
            #                         audit_type="IMPORT",
            #                         sticky=True,
            #                         hit_reason=f"Let op: een FSN is gewijzigd bij een update van het codestelsel. Betreft component {obj.codesystem_id.codesystem_title} {obj.component_id} - {term_en} [was {obj.component_title}]",
            #                     )
            #         ## To
            #         tasks = MappingTask.objects.filter(source_component = hit_rule.target_component, project_id__project_type = '4')
            #         print(f"Audit-tagging [to] {tasks.count()} tasks.")
            #         for task in tasks:
            #                 print(f"Audit hit maken voor taak {str(task)}")
            #                 audit, created_audit = MappingTaskAudit.objects.get_or_create(
            #                         task=task,
            #                         audit_type="IMPORT",
            #                         sticky=True,
            #                         hit_reason=f"Let op: een FSN is gewijzigd bij een update van het codestelsel. Betreft component {obj.codesystem_id.codesystem_title} {obj.component_id} - {term_en} [was {obj.component_title}]",
            #                     )
            # else:
            #     print(f"{obj.component_title} in database == {term_en} - geen hits")

            component_active = 'True'
            try:
                if component['@status'] != "active": component_active = 'False'
            except:
                print("Fout bij bepalen of lab_concept actief is - import als actief")


            obj.component_title     = term_en
            obj.component_extra_dict   = {
                'Nederlands'            : term_nl,
                'Component'             : loinc_component,
                'Kenmerk'               : loinc_property,
                'Timing'                : loinc_timing,
                'Systeem'               : loinc_system,
                'Schaal'                : loinc_scale,
                'Klasse'                : loinc_class,
                'Aanvraag/Resultaat'    : loinc_orderObs,
                'Materialen'            : material_list_snomed,
                'Actief'                : component_active,
            }
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

        #### Add sticky audit hit if concept was already in database and title changed
        if (obj.component_title != None) and (obj.component_title != row[1]):
            print(f"{obj.component_title} in database != {row[1]} - audit hit maken")
            # Find tasks using this component
            tasks = MappingTask.objects.filter(source_component = obj)
            for task in tasks:
                audit, created_audit = MappingTaskAudit.objects.get_or_create(
                        task=task,
                        audit_type="IMPORT",
                        sticky=True,
                        hit_reason=f"Let op: de bronterm/FSN is gewijzigd bij een update van het codestelsel. Controleer of de betekenis nog gelijk is.",
                    )
        else:
            print(f"{obj.component_title} in database == {row[1]} - geen hits")

        obj.component_title     = row[1]

        extra = {
            'Rubriek' : row[2],
            'Subrubriek' : row[3],
            'Tractus' : row[4],
            'CMSV-code' : row[5],
            'VO' : row[6],
            'VM' : row[7],
            'VV' : row[8],
            'Actief' : 'True', # Deze tabel heeft geen aanduiding voor actief/inactief - hardcoded actief.
        }
        obj.component_extra_dict = extra
        # Save
        obj.save()

@shared_task
def import_apache_async():
    df = read_excel('/webserver/mapping/resources/apache/20171120_apache-snomed_eerstetab_Basislijst.xlsx')
    # Vervang lege cellen door False
    df=df.fillna(value=False)
    for index, row in df.iterrows():
        codesystem = MappingCodesystem.objects.get(id='10') #10 = apache
        obj, created = MappingCodesystemComponent.objects.get_or_create(
            codesystem_id=codesystem,
            component_id=row['ID'],
        )
        # Add data not used for matching

        #### Add sticky audit hit if concept was already in database and title changed
        if (obj.component_title != None) and (obj.component_title != row['APACHE IV TERM']):
            print(f"{obj.component_title} in database != {row['APACHE IV TERM']} - sticky audit hit maken")
            # Find tasks using this component
            tasks = MappingTask.objects.filter(source_component = obj)
            for task in tasks:
                audit, created_audit = MappingTaskAudit.objects.get_or_create(
                        task=task,
                        audit_type="IMPORT",
                        sticky=True,
                        hit_reason=f"Let op: de bronterm/FSN is gewijzigd bij een update van het codestelsel. Controleer of de betekenis nog gelijk is.",
                    )
        else:
            print(f"{obj.component_title} in database == {row['APACHE IV TERM']} - geen hits")

        obj.component_title     = row['APACHE IV TERM']

        legacy_map = ''
        for item in df[df['ID'] == row['ID']].values:
            legacy_map += f"{item[2]} |{item[3]}|\n"

        extra = {
            'Legacy map' : legacy_map,
            'Actief' : 'True', # Deze tabel heeft geen aanduiding voor actief/inactief - hardcoded actief.
        }
        obj.component_extra_dict = extra
        # Save
        obj.save()

@shared_task
def import_omaha_task():
    df = read_excel('/webserver/mapping/resources/omaha/omaha.xlsx')
    # Vervang lege cellen door False
    df=df.fillna(value=False)

    for index, row in df.iterrows():
        codesystem = MappingCodesystem.objects.get(id='8')
        obj, created = MappingCodesystemComponent.objects.get_or_create(
            codesystem_id=codesystem,
            component_id=row[0],
        )
        # Add data not used for matching

        #### Add sticky audit hit if concept was already in database and title changed
        if (obj.component_title != None) and (obj.component_title != row[1]):
            print(f"{obj.component_title} in database != {row[1]} - audit hit maken")
            # Find tasks using this component
            tasks = MappingTask.objects.filter(source_component = obj)
            for task in tasks:
                audit, created_audit = MappingTaskAudit.objects.get_or_create(
                        task=task,
                        audit_type="IMPORT",
                        sticky=True,
                        hit_reason=f"Let op: de bronterm/FSN is gewijzigd bij een update van het codestelsel. Controleer of de betekenis nog gelijk is.",
                    )
        else:
            print(f"{obj.component_title} in database == {row[1]} - geen hits")

        obj.component_title     = row[1]

        extra = {
            'Actief' : 'True', # Deze tabel heeft geen aanduiding voor actief/inactief - hardcoded actief.
        }
        obj.component_extra_dict = extra
        # Save
        obj.save()

@shared_task
def import_palgathesaurus_task():
    df = read_excel('/webserver/mapping/resources/palga/Thesaurus_20200401.xls')
    # Vervang lege cellen door False
    df=df.fillna(value=False)
    # Selecteer alleen rijen met voorkeursterm
    df = df[df['DESTACE'] == 'V']
    df = df[df['DESNOMEDCT'] != 'nvt']

    # Set alle bestaande concepten in het codestelsel Palga als inactief
    palga = MappingCodesystem.objects.get(id='7')
    snomed = MappingCodesystem.objects.get(id='1')
    concepts = MappingCodesystemComponent.objects.filter(codesystem_id=palga)
    concepts.update(component_extra_dict = {
        'Actief':False,
    })

    for index, row in df.iterrows():
        obj, created = MappingCodesystemComponent.objects.get_or_create(
            codesystem_id=palga,
            component_id=row[1],
        )
        # Add data not used for matching
        obj.component_title     = row[0]

        extra = {
            'DEADVOM' : row[3],
            'DEPROT' : row[5],
            'DERETR' : row[6],
            'DENKR' : row[7],
            'Actief' : 'True', # Deze tabel heeft geen aanduiding voor actief/inactief - hardcoded actief.
        }
        obj.component_extra_dict = extra
        # Save
        obj.save()

        try:
            # Bestaande mapping rules doorvoeren
            
            # Bestaande mappings verwijderen
            existing_mappings = MappingRule.objects.filter(source_component = obj)
            existing_mappings.delete()
        except Exception as e:
            print(e)
            print('Nog geen taak voor '+str(row[0]))

        try:
            task = MappingTask.objects.get(source_component = obj)
            target = MappingCodesystemComponent.objects.get(codesystem_id = snomed, component_id = row[4])
            rule, createdRule = MappingRule.objects.get_or_create(
                project_id = task.project_id,
                source_component = obj,
                target_component = target,
                active = True,
            )
            # Als dit gelukt is, taak op klaar voor publicatie zetten.
            task.status = task.project_id.status_complete
            task.save()
        except Exception as e:
            print(e)
            print('Geen hit op',row[4])

    # Commentaren uit todo bestand inladen
    df = read_excel('/webserver/mapping/resources/palga/PALGA_TODO.xlsx')
    # Vervang lege cellen door False
    df = df.fillna(value=False)
    for index, row in df.iterrows():
        # Find concept
        component = MappingCodesystemComponent.objects.get(
            codesystem_id=palga,
            component_id=row[1],
        )
        # Find task for the concept
        task = MappingTask.objects.get(source_component = component)

        # Maak commentaar indien nog niet aanwezig
        comments = []
        if row[9] != False: comments.append("Commentaar import [Nictiz 1]: "+str(row[9])) # Nictiz
        if row[10] != False: comments.append("Commentaar import [Palga 1]: "+str(row[10])) # Palga
        if row[11] != False: comments.append("Commentaar import [Nictiz 2]: "+str(row[11])) # Nictiz
        if row[12] != False: comments.append("Commentaar import [Palga 2]: "+str(row[12])) # Palga

        for comment in comments:
            obj,created = MappingComment.objects.get_or_create(
                comment_task = task,
                comment_title = 'Import uit TODO bestand',
                comment_body = comment,
                comment_user = User.objects.get(username='mertens')
            )

@shared_task
def import_diagnosethesaurus_task():
    thesaurusConcept    = read_csv('/webserver/mapping/resources/dhd/20200316_145538_versie4.1_ThesaurusConcept.csv')
    thesaurusTerm       = read_csv('/webserver/mapping/resources/dhd/20200316_145538_versie4.1_ThesaurusTerm.csv')
    thesaurusConcept    = thesaurusConcept.fillna(value=False)
    thesaurusTerm       = thesaurusTerm.fillna(value=False)


    # Build dictionary of concepts
    concepts = {}
    for index, row in thesaurusConcept.iterrows():
        conceptid = row.get('ConceptID')
        terms = []
        # Add descriptions in a custom format
        for no, term in thesaurusTerm[thesaurusTerm['ConceptID'] == row.get('ConceptID')].iterrows():
            actief = False
            if term['Einddatum'] == 20991231: actief = True
            terms.append({
                'type' : term['TypeTerm'],
                'term' : term['Omschrijving'],
                'actief' : actief,
            })
        # Check if concept is active
        actief = False
        if row.get('Einddatum') == 20991231: actief = True
        # Add concept to dict of concepts
        concepts.update({
            conceptid : {
                'conceptid' : str(conceptid),
                'descriptions': terms,
                'actief' : actief,
                'snomedid' : str(row.get('SnomedID','')).split('.')[0],
            }
        })

    # Loop through the dictionary of concepts and add to database
    for key, concept in concepts.items():
        codesystem = MappingCodesystem.objects.get(id='6')
        obj, created = MappingCodesystemComponent.objects.get_or_create(
            codesystem_id=codesystem,
            component_id=concept.get('conceptid'),
        )
        descriptions = concept.get('descriptions',{})
        try:
            title = list(filter(lambda x : x['type'] == 'voorkeursterm', descriptions))[0].get('term','[Geen titel]')
        except:
            title = "[Geen titel]"

        #### Add sticky audit hit if concept was already in database and title changed
        if (obj.component_title != None) and (obj.component_title != title):
            print(f"{obj.component_title} in database != {title} - audit hit maken")
            # Find tasks using this component
            tasks = MappingTask.objects.filter(source_component = obj)
            for task in tasks:
                audit, created_audit = MappingTaskAudit.objects.get_or_create(
                        task=task,
                        audit_type="IMPORT",
                        sticky=True,
                        hit_reason=f"Let op: de bronterm/FSN is gewijzigd bij een update van het codestelsel. Controleer of de betekenis nog gelijk is.",
                    )
        else:
            print(f"{obj.component_title} in database == {title} - geen hits")

        obj.component_title = title
        obj.descriptions = descriptions
        extra = {
            'Actief' : concept.get('actief'),
            'snomed_mapping' : concept.get('snomedid', False),
        }
        obj.component_extra_dict = extra
        obj.save()

@shared_task
def import_nhgbepalingen_task():
    df = read_csv(
        '/webserver/mapping/resources/nhg/NHG-Tabel 45 Diagnostische bepalingen - versie 32 - bepaling.txt',
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
        # Start clean
        voorstel_materiaal = ''
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
        if not voorstel_materiaal: voorstel_materiaal = "Geen voorstel gevonden"

        codesystem = MappingCodesystem.objects.get(id='4')
        obj, created = MappingCodesystemComponent.objects.get_or_create(
            codesystem_id=codesystem,
            component_id=row[0],
        )

        obj.component_title = row[4]
        
        # Check status van NHG term
        if str(row[12])[-1:] == "V": 
            actief_component = "False"
        else:
            actief_component = "True"

        # Check soort van NHG term
        if str(row[13]) == "L":
            soort = "Laboratorium bepaling"
        elif str(row[13]) == "D":
            soort = "Diagnostische bepaling, algemeen"
        elif str(row[13]) == "P":
            soort = "Protocol specifieke diagnostische bepaling"
        else:
            soort = str(row[13])

        # Check groep van NHG term
        if   str(row[9]) == "AA": groep = "Anamnese"
        elif str(row[9]) == "AL": groep = "Allergologie"
        elif str(row[9]) == "AU": groep = "Auscultatie"
        elif str(row[9]) == "AL": groep = "Allergologie"
        elif str(row[9]) == "BA": groep = "Bacteriologie"
        elif str(row[9]) == "BM": groep = "Biometrie"
        elif str(row[9]) == "BO": groep = "Beeldvormend onderzoek"
        elif str(row[9]) == "BV": groep = "Bevolkingsonderzoek"
        elif str(row[9]) == "CO": groep = "Comorbiditeit"
        elif str(row[9]) == "CY": groep = "Cytologie"
        elif str(row[9]) == "DD": groep = "DNA diagnostiek"
        elif str(row[9]) == "FA": groep = "Familieanamnese"
        elif str(row[9]) == "FO": groep = "Functieonderzoek"
        elif str(row[9]) == "FT": groep = "Farmacologie/toxicologie"
        elif str(row[9]) == "HA": groep = "Eigen praktijk huisarts"
        elif str(row[9]) == "HE": groep = "Hematologie"
        elif str(row[9]) == "IM": groep = "Immunologie/serologie"
        elif str(row[9]) == "IN": groep = "Inspectie"
        elif str(row[9]) == "KC": groep = "Klinische chemie"
        elif str(row[9]) == "LO": groep = "Lichamelijk onderzoek"
        elif str(row[9]) == "PA": groep = "Pathologie"
        elif str(row[9]) == "PP": groep = "Palpatie"
        elif str(row[9]) == "PS": groep = "Parasitologie"
        elif str(row[9]) == "SG": groep = "Socio-grafische gegevens"
        elif str(row[9]) == "ST": groep = "Stollingslab"
        elif str(row[9]) == "TH": groep = "Therapie"
        elif str(row[9]) == "VG": groep = "Voorgeschiedenis"
        elif str(row[9]) == "VI": groep = "Virologie"
        elif str(row[9]) == "XX": groep = "Overig"
        elif str(row[9]) == "ZE": groep = "Patiënt zelf"
        elif str(row[9]) == "ZP": groep = "Zorgproces"
        else: groep = "Onbekend"
        groep = str(row[9]+' - '+groep)

        extra = {
            'Omschrijving' : row[4],
            'Bepaling nummer' : row[0],
            'Aanvraag/Uitslag/Beide' : row[6],
            'Soort' : soort,
            'Groep' : groep,
            'Selectie' : row[10],
            'Materiaal NHG' : row[2],
            'Materiaal voorstel Snomed' : voorstel_materiaal,
            'Vraagtype' : row[14],
            'Eenheid' : row[16],
            'Versie mutatie' : row[12],
            'Actief' : actief_component,
        }
        # print(extra)
        obj.component_extra_dict = extra
        obj.save()

@shared_task
def import_icpc_task():
    df = read_csv(
        '/webserver/mapping/resources/nhg/NHG-ICPC.txt',
        sep='\t',
        header = 1,
        )
    i=0
    # Vervang lege cellen door False
    df=df.fillna(value=False)

    # Verwerk dataset -> database
    for index, row in df.iterrows():
        codesystem = MappingCodesystem.objects.get(id='5')
        obj, created = MappingCodesystemComponent.objects.get_or_create(
            codesystem_id=codesystem,
            component_id=str(row['ICPC Code']),
        )
        
        #### Sticky audit hit if concept was already in database and title changed
        if (obj.component_title != None) and (obj.component_title != row['ICPC Titel']):
            print(f"{obj.component_title} in database != {row['ICPC Titel']} - audit hit maken")
            # Find tasks using this component
            tasks = MappingTask.objects.filter(source_component = obj)
            for task in tasks:
                audit, created_audit = MappingTaskAudit.objects.get_or_create(
                        task=task,
                        audit_type="IMPORT",
                        sticky=True,
                        hit_reason=f"Let op: de bronterm/FSN is gewijzigd bij een update van het codestelsel. Controleer of de betekenis nog gelijk is.",
                    )
        else:
            print(f"{obj.component_title} in database == {row['ICPC Titel']} - geen hits")

        obj.component_title = row['ICPC Titel']

        actief_concept = 'True'
        if row['Versie vervallen'] != False: actief_concept = 'False'

        extra = {
            'ICPC code' : row['ICPC Code'],
            'NHG ID'    : row['ID'],
            'Actief'    : actief_concept,
        }
        # print(extra)
        obj.component_extra_dict = extra
        obj.save()

@shared_task
def import_gstandaardDiagnoses_task():
    df = read_excel(
        '/webserver/mapping/resources/gstandaard/diagnosenLijst_20200824.xlsx',
        )
    i=0
    # Vervang lege cellen door lege string
    df=df.fillna(value='')

    # Verwerk dataset -> database
    for index, row in df.iterrows():
        codesystem = MappingCodesystem.objects.get(id='9')
        obj, created = MappingCodesystemComponent.objects.get_or_create(
            codesystem_id=codesystem,
            component_id=str(row['Parameternummer']),
        )
        
        # #### Sticky audit hit if concept was already in database and title changed
        # if (obj.component_title != None) and (obj.component_title != row['ICPC Titel']):
        #     print(f"{obj.component_title} in database != {row['ICPC Titel']} - audit hit maken")
        #     # Find tasks using this component
        #     tasks = MappingTask.objects.filter(source_component = obj)
        #     for task in tasks:
        #         audit, created_audit = MappingTaskAudit.objects.get_or_create(
        #                 task=task,
        #                 audit_type="IMPORT",
        #                 sticky=True,
        #                 hit_reason=f"Let op: de bronterm/FSN is gewijzigd bij een update van het codestelsel. Controleer of de betekenis nog gelijk is.",
        #             )
        # else:
        #     print(f"{obj.component_title} in database == {row['ICPC Titel']} - geen hits")

        obj.component_title = row['diagnose']

        actief_concept = 'True'

        extra = {
            'Opmerking' : row['opmerking'],
            'Actief' : actief_concept,
        }
        # print(extra)
        obj.component_extra_dict = extra
        obj.save()

@shared_task
def audit_async(audit_type=None, project=None, task_id=None):
    project = MappingProject.objects.get(id=project)
    if task_id == None:
        tasks = MappingTask.objects.filter(project_id=project)
    else:
        tasks = MappingTask.objects.filter(project_id=project, id=task_id).order_by('id')

    # Delete existing audit hits for tasks (unless whitelisted)
    for task in tasks:
            # Print task identification, sanity check
            # logger.info('Deleting hits for: TASK {0} - {1}'.format(task.source_component.component_title, task.id))

            # Delete all old audit hits for this task if not whitelisted
            delete = MappingTaskAudit.objects.filter(task=task, ignore=False, sticky=False).delete()
            # logger.info(delete)

    ###### Slowly moving to separate audit QA scripts.
    logger.info('Spawning QA processes')
    logger.info('Auditing project: #{0} {1}'.format(project.id, project.title))
    
    # Spawn QA for labcodeset<->NHG tasks
    for task in tasks:
        # logger.info('Checking task: {0}'.format(task.id))
        
        # logger.info('Spawning QA scripts for NHG<->LOINC')
        send_task('mapping.tasks.qa_nhg_labcodeset.nhg_loinc_order_vs_observation', [], {'taskid':task.id})
        
        if task.project_id.project_type == '4':
            # logger.info('Spawning QA scripts for ECL-1 queries')
            send_task('mapping.tasks.qa_ecl_vs_rules.ecl_vs_rules', [], {'taskid':task.id})
            send_task('mapping.tasks.qa_ecl_duplicates.check_duplicate_rules', [], {'taskid':task.id})
        
        # logger.info('Spawning general QA scripts for SNOMED')
        # Snowstorm daily build SNOWSTORM does not like DDOS - only run on individual tasks, not on entire projects.
        if tasks.count() == 1:
            send_task('mapping.tasks.qa_snomed.snomed_daily_build_active', [], {'taskid':task.id})

    # Also run legacy rules, in addition to rules split in multiple task files?
    legacy = True

    ###### Older code, still functional. Needs to be distributed over other QA scripts in the future.
    if audit_type == "multiple_mapping" and legacy:
        # Create exclusion lists for targets such as specimen in project NHG diagnostische bepalingen -> LOINC+Snomed
        # snowstorm = Snowstorm(baseUrl="https://snowstorm.test-nictiz.nl", defaultBranchPath="MAIN/SNOMEDCT-NL", debug=True)
        # results = snowstorm.findConcepts(ecl='<<123038009')
        # specimen_exclusion_list = []
        # for concept in results:
        #     specimen_exclusion_list.append(str(concept))
        # Now using the local exclusion list built in the concept
        specimen_exclusion_list = json.loads(MappingCodesystemComponent.objects.get(component_id='123038009').descendants)


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
            rules = MappingRule.objects.filter(project_id=project, source_component=task.source_component).order_by('mappriority')
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


# Create RC shadow copy of codesystem
@shared_task
def exportCodesystemToRCRules(rc_id, user_id):
    def component_dump(codesystem=None, component_id=None):
        component = MappingCodesystemComponent.objects.get(component_id = component_id, codesystem_id=codesystem)
        output = {
            'identifier'    : component.component_id,
            'title'         : component.component_title,
            'extra'         : component.component_extra_dict,
            'created'       : str(component.component_created),
            'codesystem'    : {
                'id'        : component.codesystem_id.id,
                'name'      : component.codesystem_id.codesystem_title,
                'version'   : component.codesystem_id.codesystem_version,
                'fhir_uri'  : component.codesystem_id.codesystem_fhir_uri,
            }
        }
        return output

    # Select RC
    rc = MappingReleaseCandidate.objects.get(id = rc_id)
    if rc.status != 3: # 3=production
        rc.finished = False
        rc.save()
        # Get all tasks in requested codesystem - based on the codesystem of the source component
        # if rc.target_codesystem != None:
        #     print("Target filter applied")
        #     tasks = MappingTask.objects.filter(
        #             source_component__codesystem_id__id = rc.codesystem.id,
        #             target_codesystem = rc.target_codesystem,
        #         ).order_by('source_component__component_id')
        #     tasks = tasks | MappingTask.objects.filter(
        #             source_component__codesystem_id__id = rc.codesystem.id,
        #             target_codesystem = rc.target_codesystem,
        #         ).order_by('source_component__component_id')
        # else:
            # print("Target filter NOT applied")
        tasks = MappingTask.objects.filter(
                source_component__codesystem_id__id = rc.codesystem.id,
            ).order_by('source_component__component_id')

        try:
            tasks = tasks | MappingTask.objects.filter(
                        source_component__codesystem_id__id = rc.target_codesystem.id,
                    ).order_by('source_component__component_id')
        except:
            tasks = tasks

        print('Found',tasks.count(),'tasks.')
        
        debug_list = []
        valid_rules = []
        # Loop through tasks
        for task in tasks:
            if task.status != task.project_id.status_complete:
                print(f"Ignored a task [{task.project_id.id} / {str(task.id)} / {task.source_component.component_id}] with a status [{task.status.id} {task.status.status_title}] other than completed [{task.project_id.status_complete.id} {task.project_id.status_complete.status_title}] - should probably be removed from the dev database, Ok ok ill do this now... Task ID: {str(task.id)}")
                debug_list.append(f"Ignored a task [{task.project_id.id} / {str(task.id)} / {task.source_component.component_id}] with a status [{task.status.id} {task.status.status_title}] other than completed [{task.project_id.status_complete.id} {task.project_id.status_complete.status_title}] - should probably be removed from the dev database, Ok ok ill do this now... Task ID: {str(task.id)}")
                # Remove all rules in the RC database originating from this task, since it is rejected.
                if task.project_id.project_type == '1':
                    # In type 1 - source_component is used as SOURCE for all related rules
                    rc_rules = MappingReleaseCandidateRules.objects.filter(
                            static_source_component_ident = task.source_component.component_id,
                            export_task = task,
                            export_rc = rc,
                    )
                elif task.project_id.project_type == '4':
                    # In type 4 - source_component is used as a TARGET for all related rules
                    rc_rules = MappingReleaseCandidateRules.objects.filter(
                            static_target_component_ident = task.source_component.component_id,
                            export_task = task,
                            export_rc = rc,
                    )
                
                rc_rules.delete()

            else:
                print(f"Handle task {task.id}")
                if task.project_id.project_type == '1':
                    # In type 1 - source_component is used as SOURCE for all related rules
                    rules = MappingRule.objects.filter(
                            project_id = task.project_id,
                            source_component = task.source_component,
                        )
                elif task.project_id.project_type == '4':
                    # In type 4 - source_component is used as a TARGET for all related rules
                    rules = MappingRule.objects.filter(
                            project_id = task.project_id,
                            target_component = task.source_component,
                        )
                # Filter on target codesystem if enabled
                if rc.target_codesystem != None:
                    rules = rules.filter(
                        target_component__codesystem_id = rc.target_codesystem
                    )
                
                ## First: check if any of the rules for this task have changes
                ## if so: delete all existing rules in RC and replace them all
                for rule in rules:
                    print(f"Handle rule {rule.id} of task {task.id}")
                    # Handle bindings / specifications / products
                    mapspecifies = []
                    for binding in rule.mapspecifies.all():
                        mapspecifies.append({
                            'id' : binding.target_component.component_id,
                            'title' : binding.target_component.component_title,
                        })

                    # Get all RC rules, filtered on this rule and RC
                    rc_rule = MappingReleaseCandidateRules.objects.filter(
                        export_rule = rule,
                        export_rc = rc,
                        # rc_rule.export_user = User.objects.get(id=user_id)
                        export_task = task,
                        task_status = task.status.status_title,
                        # task_user = task.user.username
                        source_component = rule.source_component,
                        static_source_component_ident = rule.source_component.component_id,
                        # static_source_component = component_dump(codesystem = rule.source_component.codesystem_id.id, component_id = rule.source_component.component_id),
                        target_component = rule.target_component,
                        static_target_component_ident = rule.target_component.component_id,
                        # static_target_component = component_dump(codesystem = rule.target_component.codesystem_id.id, component_id = rule.target_component.component_id),
                        mapgroup = rule.mapgroup,
                        mappriority = rule.mappriority,
                        mapcorrelation = rule.mapcorrelation,
                        mapadvice = rule.mapadvice,
                        maprule = rule.maprule,
                        mapspecifies = mapspecifies,
                    )
                    # Check if rules with this criterium exist without changes (ignoring veto/fiat), if so: let it be and go to the next rule
                    if rc_rule.count() == 1:
                        print(f"Pre-existing rule - skip")
                        rc_rule = rc_rule.first()
                        debug_list.append('Found a pre-existing exported rule [dev {}/{} = rc {}] that is equal to dev path - skipping'.format(task.source_component.component_id, rule.id, rc_rule.id))
                    else:
                        rc_rule_todelete = MappingReleaseCandidateRules.objects.filter(
                            source_component = task.source_component,
                            export_rc = rc,
                        )
                        if rc_rule_todelete.count() > 0:
                            print(f"Rule with changes - delete everything in rc in prep for copying")
                            debug_list.append('Found rule(s) with changes for component {} - deleting all RC rules for this task.'.format(task.source_component.component_id))
                            rc_rule_todelete.delete()
                ### End check for changes
                
                ## Now copy the new rules where needed
                for rule in rules:
                    print(f"Copy rule {rule.id} for task {task.id}")
                    # Handle bindings / specifications / products
                    mapspecifies = []
                    for binding in rule.mapspecifies.all():
                        mapspecifies.append({
                            'id' : binding.target_component.component_id,
                            'title' : binding.target_component.component_title,
                        })

                    # Get all RC rules, filtered on this rule and RC
                    rc_rule = MappingReleaseCandidateRules.objects.filter(
                        export_rule = rule,
                        export_rc = rc,
                        # rc_rule.export_user = User.objects.get(id=user_id)
                        export_task = task,
                        task_status = task.status.status_title,
                        # task_user = task.user.username
                        source_component = rule.source_component,
                        static_source_component_ident = rule.source_component.component_id,
                        # static_source_component = component_dump(codesystem = rule.source_component.codesystem_id.id, component_id = rule.source_component.component_id),
                        target_component = rule.target_component,
                        static_target_component_ident = rule.target_component.component_id,
                        # static_target_component = component_dump(codesystem = rule.target_component.codesystem_id.id, component_id = rule.target_component.component_id),
                        mapgroup = rule.mapgroup,
                        mappriority = rule.mappriority,
                        mapcorrelation = rule.mapcorrelation,
                        mapadvice = rule.mapadvice,
                        maprule = rule.maprule,
                        mapspecifies = mapspecifies,
                    )
                    # Check if rules with this criterium exist, if so: let it be and go to the next rule in order to avoid duplicates
                    if rc_rule.count() == 1:
                        rc_rule = rc_rule.first()
                        print('Found a pre-existing exported rule [dev {}/{} = rc {}] that is equal to dev path - skipping'.format(task.source_component.component_id, rule.id, rc_rule.id))
                        debug_list.append('Found a pre-existing exported rule [dev {}/{} = rc {}] that is equal to dev path - skipping'.format(task.source_component.component_id, rule.id, rc_rule.id))

                    elif rc_rule.count() > 1:
                        debug_list.append(rc_rule.all())
                        print("Multiple RC rules exists for a single dev rule. PASS.")
                        debug_list.append("Multiple RC rules exists for a single dev rule. PASS.")
                        pass
                    # If not, make a new one
                    else:
                        print(f"Add rule {rule.id} to database.")
                        rc_rule = MappingReleaseCandidateRules.objects.create(
                            export_rule = rule,
                            export_rc = rc,
                            # Add essential data to shadow copy in RC
                            export_user = User.objects.get(id=user_id),
                            export_task = task,
                            task_status = task.status.status_title,
                            task_user = task.user.username,
                            source_component = rule.source_component,
                            static_source_component_ident = rule.source_component.component_id,
                            static_source_component = component_dump(codesystem = rule.source_component.codesystem_id.id, component_id = rule.source_component.component_id),
                            target_component = rule.target_component,
                            static_target_component_ident = rule.target_component.component_id,
                            static_target_component = component_dump(codesystem = rule.target_component.codesystem_id.id, component_id = rule.target_component.component_id),
                            mapgroup = rule.mapgroup,
                            mappriority = rule.mappriority,
                            mapcorrelation = rule.mapcorrelation,
                            mapadvice = rule.mapadvice,
                            maprule = rule.maprule,
                            mapspecifies = mapspecifies,
                        )
                        # rc_rule.save()
                    valid_rules.append(rule)

        # Clean up - leave no rules behind that should not be there
        invalid_rules = MappingReleaseCandidateRules.objects.filter(
            export_rc = rc,
        ).exclude(
            export_rule__in = valid_rules,
        )
        print(f"Found {invalid_rules.count()} invalid rules - deleting")
        invalid_rules.delete()

        rc.finished = True
        logger.info('Finished')
        for item in debug_list:
            print(item,'\n')
        rc.save()
        return str('Import klaar')
    else:
        return str('Import niet toegestaan - productie RC')

# Generate FHIR ConceptMap
@shared_task
def GenerateFHIRConceptMap(rc_id=None, action=None, payload=None):
    # Option to return as JSON object, or save to database
    # Database queries
    pk = rc_id
    if action == 'output':
        output = MappingReleaseCandidateFHIRConceptMap.objects.get(id=rc_id)
        return output.data
    elif action == 'save':
        rc = MappingReleaseCandidate.objects.get(id=int(pk))
        rules = MappingReleaseCandidateRules.objects.filter(export_rc = rc)
        project_ids = rules.values_list('export_task__project_id',flat=True).distinct()

        # Setup
        elements = []
        projects = []
        error = []
        groups = []
        correlation_options = [
            # [code, readable]
            # ['447559001', 'Broad to narrow'],
            # ['447557004', 'Exact match'],
            # ['447558009', 'Narrow to broad'],
            # ['447560006', 'Partial overlap'],
            # ['447556008', 'Not mappable'],
            # ['447561005', 'Not specified'],
            # Suitable for FHIR spec
            ['447559001', 'narrower'],
            ['447557004', 'equal'],
            ['447558009', 'wider'],
            ['447560006', 'inexact'],
            ['447556008', 'unmatched'],
            ['447561005', 'unmatched'],
        ]

        # Loop through elements in this RC, per project
        for project_id in project_ids:
            elements = []
            project = MappingProject.objects.get(id=project_id)
            projects.append(str(project))
            # Export rules, can be unique per project
            # if project_id == 3:
            if project_id:
                # Get all unique source components
                tasks = rules.filter(export_task__project_id = project).values_list('static_source_component_ident',flat=True).order_by('static_source_component_ident').distinct()
                # Loop through unique source components
                for task in tasks:
                    targets = []
                    product_list = []
                    # Get all rules using the source component of the loop as source
                    rules_for_task = MappingReleaseCandidateRules.objects.filter(static_source_component_ident = task, export_task__project_id = project)
                    
                    # Put all the identifiers of products in a list for later use
                    for single_rule in rules_for_task:
                        for target in single_rule.mapspecifies:
                            product_list.append(target.get('id'))
                    # Now loop through while ignoring id's used as product
                    for single_rule in rules_for_task:
                        target_component = single_rule.static_target_component

                        # Skip if identifier in the list of used products
                        if (target_component.get('identifier') not in product_list):
                            # Put all the products in a list
                            products = []
                            for target in single_rule.mapspecifies:
                                # Lookup data for the target
                                target_data = MappingCodesystemComponent.objects.get(component_id = target.get('id'))
                                # Property can be added to designate the product as sample/laterality/etc
                                # WARNING - hardcoded decision making
                                # ?? 'property' : target_data.codesystem_id.component_fhir_uri.replace('[[component_id]]', target.get('id')),
                                # LOGIC: if descendant of A/B/C, add property value X/Y/Z
                                fhir_url_prefix = MappingCodesystem.objects.get(id = 1).component_fhir_uri
                                if target.get('id') in MappingCodesystemComponent.objects.get(component_id = '123038009').descendants:
                                    property_value = fhir_url_prefix.replace('[[component_id]]', '276731003') # 276731003 = SNOMED: Material (attribute) - <<UNAPPROVED ATTRIBUTE
                                elif target.get('id') in MappingCodesystemComponent.objects.get(component_id = '182353008').descendants:
                                    property_value = fhir_url_prefix.replace('[[component_id]]', '272741003') # 272741003 = SNOMED: lateraliteit (attribuut)
                                elif target.get('id') in MappingCodesystemComponent.objects.get(component_id = '252569009').descendants: # Descendants of 252569009 Test for allergens (procedure)
                                    property_value = fhir_url_prefix.replace('[[component_id]]', '408730004') # 408730004 = context van verrichting (attribuut)
                                else:
                                    property_value = fhir_url_prefix.replace('[[component_id]]', '263491009') # 263491009 = Context (attribute) - <<UNAPPROVED ATTRIBUTE
                                products.append({
                                    'property' : property_value,
                                    'system' : target_data.codesystem_id.codesystem_fhir_uri,
                                    'code' : target.get('id'),
                                    # 'display' : target.get('title'), ## TODO - remove for production
                                })

                            # Translate the map correlation
                            equivalence = single_rule.mapcorrelation
                            for code, readable in correlation_options:
                                equivalence = equivalence.replace(code, readable)
                            
                            # Create output dict
                            output = {
                                'code' : target_component.get('identifier'),
                                'equivalence' : equivalence,
                                # 'display' : target_component.get('title'), ## TODO - remove for production
                            }
                            if single_rule.mapadvice != None:
                                output.update({'comment' : single_rule.mapadvice,})
                            # Add products to output if they exist
                            if len(products) > 0:
                                output['product'] = products
                            
                            # Append result for this rule
                            targets.append(output)

                    # Add this source component with all targets and products to the element list
                    ## WARNING - export_all=True will disregard veto/fiat!
                    if rc.export_all == False:
                        # # Only if it has approves and no rejects
                        accepted_count = single_rule.accepted.count()
                        rejected_count = single_rule.rejected.count()
                        if (accepted_count > 0) and (rejected_count == 0):
                            source_component = single_rule.static_source_component
                            output = {
                                # 'DEBUG_numrules' : rules_for_task.count(),
                                # 'DEBUG_productlist' : product_list,
                                'code' : source_component.get('identifier'),
                                # 'display' : source_component.get('title'), ## TODO - remove for production
                                'target' : targets,
                            }
                            elements.append(output)
                    else:
                        # Alternative: export all rules, regardless of veto / approve. Responsibility for checking veto lies with exporter.
                        source_component = single_rule.static_source_component
                        output = {
                            # 'DEBUG_numrules' : rules_for_task.count(),
                            # 'DEBUG_productlist' : product_list,
                            'code' : source_component.get('identifier'),
                            # 'display' : source_component.get('title'), ## TODO - remove for production
                            'target' : targets,
                        }
                        elements.append(output)

                # Add the group to the group list
                groups.append({
                    # 'DEBUG_projecttitle' : project.title,
                    'source' : project.source_codesystem.codesystem_fhir_uri,
                    'sourceVersion' : project.source_codesystem.codesystem_version,
                    'target' : project.target_codesystem.codesystem_fhir_uri,
                    'targetVersion': project.target_codesystem.codesystem_version,
                    'element' : elements,
                })

        status_options = [
                # (code, readable)
                ('0', 'draft'),
                ('1', 'active'),
                ('2', 'retired'),
                ('3', 'unknown'),
            ]
        status = rc.status
        for code, readable in status_options:
            status = status.replace(code, readable)

        contact = {
            "telecom": [
                {
                    "system": "url",
                    "name": rc.metadata_contact,
                }
            ]
        }

        output = {
            'resourceType' : 'ConceptMap',
            'id' : rc.metadata_id,
            'name' : rc.title,
            'description' : rc.metadata_description,
            'version' : rc.metadata_version,
            'status' : status,
            'DEBUG_export_all' : rc.export_all,
            'experimental' : rc.metadata_experimental,
            'date' : rc.metadata_date,
            'publisher' : rc.metadata_publisher,
            'contact' : contact,
            'copyright' : rc.metadata_copyright,
            'sourceCanonical' : rc.metadata_sourceCanonical,

            # 'DEBUG_projects' : list(projects),
            'groups' : groups,
        }


        
        obj = MappingReleaseCandidateFHIRConceptMap.objects.create(
            title = payload.get('title'),
            rc = rc,
            release_notes = payload.get('rc_notes'),
            codesystem = rc.codesystem,
            deprecated=True,
            data = output,
        )
        return obj.id
        
# Dump progress per day to database
@shared_task
def mappingProgressDump():
    # Taken per status
    project_list = MappingProject.objects.filter(active=True)
    tasks_per_user_dict = []
    tasks_per_status_dict = []

    for project in project_list:        
        try:
            project_list = MappingProject.objects.filter(active=True)
            current_project = MappingProject.objects.get(id=project.id, active=True)
            
            status_list = MappingTaskStatus.objects.filter(project_id=project.id).order_by('status_id')#.exclude(id=current_project.status_complete.id)
            tasks_per_status_labels = []
            tasks_per_status_values = []
            tasks_per_status_dict = []
            user_list = User.objects.filter()
            tasks_per_user_labels = []
            tasks_per_user_values = []
            tasks_per_user_dict = []
            for user in user_list:
                num_tasks = MappingTask.objects.filter(project_id_id=current_project.id, user=user).exclude(status=current_project.status_complete).exclude(status=current_project.status_rejected).count()
                if num_tasks > 0:
                    num_tasks = MappingTask.objects.filter(project_id_id=current_project.id, user=user).exclude(status=current_project.status_complete).exclude(status=current_project.status_rejected).count()
                    tasks_per_user_labels.append(user.username)
                    tasks_per_user_values.append(num_tasks)
                    tasks_per_user_dict.append({
                    'user' : user.username,
                    'num_tasks' : num_tasks,
                    })
            for status in status_list:
                num_tasks = MappingTask.objects.filter(project_id_id=current_project.id, status_id=status).exclude(status=current_project.status_rejected).count()
                tasks_per_status_labels.append(status.status_title)
                tasks_per_status_values.append(num_tasks)
                tasks_per_status_dict.append({
                    'status' : status.status_title,
                    'num_tasks' : num_tasks,
                    })
        except:
            tasks_per_status_labels = []
            tasks_per_status_values = []
            tasks_per_user_labels = []
            tasks_per_user_values = []
        
        # print(tasks_per_user_dict)
        # print(tasks_per_status_dict)
        try:
            MappingProgressRecord.objects.create(
                name = 'TasksPerStatus',
                project = project,
                labels = '',
                values = json.dumps(tasks_per_status_dict)
            )
        except Exception as e:
            print(e)
        try:
            MappingProgressRecord.objects.create(
                name = 'TasksPerUser',
                project = project,
                labels = '',
                values = json.dumps(tasks_per_user_dict)
            )
        except Exception as e:
            print(e)

    return {
        'project' : project.id,
        'results' : tasks_per_status_dict,
    }