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
from urllib.parse import quote, quote_plus
from pandas import read_excel, read_csv
import environ
import sys, os
import requests

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

    max_tries = 10
    sleep_time = 10
    tries = 0

    # Fetch query object
    currentQuery = MappingEclPart.objects.get(id = record_id)
    # Empty results and set it to active
    currentQuery.result  = {}
    currentQuery.finished = False
    currentQuery.error = None
    currentQuery.failed = False
    currentQuery.save()


    # Enter loop
    queryCount = 0
    while True:
        tries += 1
        print(f"[Delegate SharedTask UpdateECL1Task] Task owned by: {str(currentQuery.task.user)}")
        try:

            counter = 0
            url = "https://snowstorm.test-nictiz.nl/MAIN/SNOMEDCT-NL/concepts?activeFilter=true&limit=10000&ecl={}".format(
                quote_plus(query.strip())
            )
            print(url)
            response = requests.get(url, params = {'Accept-Language': "nl"})
            
            # Start of status code 200 section
            if response.status_code == 200:
                print("200 result")
                items = json.loads(response.text)
                results = {}
                total_results = items['total']
                print(f"Looking for a total of {total_results}")
                # Update query count
                queryCount += 1

                # Loop while the cacheTemp is smaller than the total results
                while counter < total_results:
                    print(f"Loop {queryCount}")
                    # If no results, break while loop - Probably redundant
                    if items['total'] == 0:
                        break

                    # For all results, add to cache
                    for value in items['items']:
                        results.update({value['conceptId']: value})
                        counter += 1

                    # If there are more results than currently present in cacheTemp, run another query
                    if counter < total_results:
                        # Request results
                        url = "https://snowstorm.test-nictiz.nl/MAIN/SNOMEDCT-NL/concepts?activeFilter=true&limit=10000&searchAfter={}&ecl={}".format(
                            quote_plus(items.get('searchAfter')), 
                            quote_plus(query).strip(),
                        )
                        print(url)
                        response = requests.get(url, params = {'Accept-Language': "nl"})
                        items = json.loads(response.text)
                        # Update query count
                        queryCount += 1
                    
                    print(f"End of loop {queryCount} - we have {len(results)} now.")

                print("Writing out results to db")
                currentQuery.result = {
                    'concepts': results,
                    'numResults': len(results),
                }
                currentQuery.finished = True
                currentQuery.error = None
                currentQuery.failed = False
                currentQuery.save()
                print("Breaking loop")
                break
            # End of status code 200 section
            # Handle 400 errors: Syntax correct, other mistakes were made
            elif response.status_code == 400:
                print("400 error")
                body = json.loads(response.text)
                print(body)
                currentQuery.finished = True
                currentQuery.error = f"{body.get('error')}: {body.get('message')}"
                currentQuery.failed = True
                currentQuery.save()
                break

            # Handle 500 errors: Query syntax error
            elif response.status_code == 500:
                print("500 error")
                body = json.loads(response.text)
                print(body)
                currentQuery.finished = True
                currentQuery.error = f"{body.get('error')}: {body.get('message')}"
                currentQuery.failed = True
                currentQuery.save()
                break
            
            # Other errors: retry
            else:
                if tries > max_tries:
                    print(f"Error in UpdateECL1Task ({record_id}). Response code: {response.status_code}. Response body: {response.text}. Try [{tries}/{max_tries}]. Giving up - big error.")

                    currentQuery.finished = True
                    currentQuery.error = f"Na {tries} pogingen opgegeven. Status code: {response.status_code}. Response body: {response.text}."
                    currentQuery.failed = True
                    currentQuery.save()

                    break
                else:
                    print(f"Error in UpdateECL1Task ({record_id}). Response code: {response.status_code}. Response body: {response.text}. Try [{tries}/{max_tries}]. Sleeping {sleep_time*tries} and retrying.")
                    time.sleep(sleep_time*tries)
                    continue
        except Exception as e:
            print(f"Other breaking error in UpdateECL1Task ({record_id}):",e)
            currentQuery.finished = True
            currentQuery.error = f"Na {tries} pogingen opgegeven: {e}"
            currentQuery.failed = True
            currentQuery.save()
            break

        
    print("Done")
    return str(currentQuery)

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
    df = read_excel('/webserver/mapping/resources/apache/extractie_20171120.xlsx')
    # Vervang lege cellen door False
    df=df.fillna(value=False)
    for index, row in df.iterrows():
        codesystem = MappingCodesystem.objects.get(id='10') #10 = apache
        obj, created = MappingCodesystemComponent.objects.get_or_create(
            codesystem_id=codesystem,
            component_id=row['id'],
        )
        # Add data not used for matching

        #### Add sticky audit hit if concept was already in database and title changed
        if (obj.component_title != None) and (obj.component_title != '') and (obj.component_title != row['description']):
            print(f"{obj.component_title} in database != {row['description']} - sticky audit hit maken")
            # Find tasks using this component
            tasks = MappingTask.objects.filter(source_component = obj)
            for task in tasks:
                audit, created_audit = MappingTaskAudit.objects.get_or_create(
                        task=task,
                        audit_type="IMPORT",
                        sticky=True,
                        hit_reason=f"Let op: de bronterm/FSN is gewijzigd bij een update van het codestelsel. [{obj.component_title} => {row['description']}] Controleer of de betekenis nog gelijk is.",
                    )
        else:
            print(f"{obj.component_title} in database == {row['description']} - geen hits")

        obj.component_title     = row['description']

        ##### Legacy map not available for current extraction
        # legacy_map = ''
        # for item in df[df['id'] == row['id']].values:
        #     legacy_map += f"{item[2]} |{item[3]}|\n"

        extra = {
            # 'Legacy map' : legacy_map,
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
    ##### Version wordt gebruikt voor de bestandsnaam EN versie in de database! #####
    version = "36"
    df = read_csv(
        f'/webserver/mapping/resources/nhg/NHG-Tabel-45-Diagnostische-bepalingen-versie-{version}-bepaling.txt',
        sep='\t',
        header = 1,
        )
    i=0
    # Vervang lege cellen door False
    df=df.fillna(value=False)

    # Select codesystem
    codesystem = MappingCodesystem.objects.get(id='4')
    # Update codesystem version
    codesystem.codesystem_version = str(version)
    codesystem.save()
    
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
            'Memo' : row[1],
            'Sleutelcode' : f"{row[1]} {row[2]} {row[3]}",
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
    rc = MappingReleaseCandidate.objects.select_related(
        'codesystem',
        'target_codesystem',
    ).get(id = rc_id)
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


        # tasks = MappingTask.objects.filter(
        #         source_component__codesystem_id__id = rc.codesystem.id,
        #     ).order_by('source_component__component_id')

        # try:
        #     tasks = tasks | MappingTask.objects.filter(
        #                 source_component__codesystem_id__id = rc.target_codesystem.id,
        #             ).order_by('source_component__component_id')
        # except:
        #     tasks = tasks
            
        # Only include tasks included in the RC spec
        project_list = rc.export_project.values_list('id')
        print("Only include project ID's: ",project_list)
        tasks = MappingTask.objects.all().filter(project_id__id__in = project_list).select_related(
            'project_id',
            'source_component',
            'source_component__codesystem_id',
            'source_codesystem',
            'target_codesystem',
            'user',
            'status',
        )

        print('Found',tasks.count(),'tasks.')
        
        debug_list = []
        valid_rules = []
        # Loop through tasks
        for task in tasks:
            if (task.status != task.project_id.status_complete) and (rc.import_all == False):
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

            elif (task.status == task.project_id.status_complete) or (rc.import_all == True):
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
                                    'value' : target.get('id'),
                                    # 'display' : target.get('title'), ## TODO - remove for production
                                })

                            # Translate the map correlation
                            equivalence = single_rule.mapcorrelation
                            for code, readable in correlation_options:
                                try:
                                    equivalence = equivalence.replace(code, readable)
                                except:
                                    continue
                            
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

                # Add the group to the group list, if there are elements in it
                if len(elements) > 0:
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
            try:
                status = status.replace(code, readable)
            except:
                continue

        contact = [{
            "telecom": [
                {
                    "system": "url",
                    "value": rc.metadata_contact,
                }
            ]
        }]

        output = {
            'url' : rc.metadata_url,
            'resourceType' : 'ConceptMap',
            'id' : rc.metadata_id,
            'name' : rc.title,
            'description' : rc.metadata_description,
            'version' : rc.metadata_version,
            'status' : status,
            # 'DEBUG_export_all' : rc.export_all,
            'experimental' : rc.metadata_experimental,
            'date' : rc.metadata_date,
            'publisher' : rc.metadata_publisher,
            'contact' : contact,
            'copyright' : rc.metadata_copyright,
            # 'sourceUri' : rc.metadata_sourceUri,

            # 'DEBUG_projects' : list(projects),
            'group' : groups,
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