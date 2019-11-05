# VERSION 0.4
# No caching to files

# import
import json, requests, re, time, sys, pandas, pprint, pickle

# Server IP
server_ip = 'https://snowstorm.test-nictiz.nl'
# # Server port
# server_port = '8080'
# Server port - ElasticSearch
server_es_port = '9200'
# Cache map
cache_folder = '/Users/sander/GitHub/nictiz/snowstorm_cache/'

# Cache variabele concepten
concepten = {}
children = {}
alternative = {}
maps = {}

def get_concept(concept):
# ====== GET_CONCEPT ======
# output[compleet] = complete JSON uit API call
# output[conceptId] = conceptId van aangeroepen concept
# output[nl/en/nlpatient][FSN/PTN/SYNONYM[0,1,etc]]
# NB: errorhandling voor missende termen moet buiten deze functie gebouwd worden

    global concepten
    output = {}
    output['nl'] = {}
    output['nlpatient'] = {}
    output['en'] = {}
    if concept not in concepten.keys():
        try:
            r = requests.get('{}/browser/MAIN%2FSNOMEDCT-NL/concepts/{}'.format(server_ip, concept))
            concepten_local = r.json()
            concepten.update({concept : concepten_local})
            print("Concepten cache update")
        except:
            print("Concept bestaat niet, exit ({}:{}/browser/MAIN%2FSNOMEDCT-NL/concepts/{})".format(server_ip, server_port, concept))
            exit(56)
    else:
        concepten_local = concepten[concept]
        print("cache winst concept[{}]".format(concept))

    output['conceptId'] = concepten_local['conceptId']
    output['compleet'] = concepten_local
    for value in concepten_local['descriptions']:
    # Patiententerm FSN PTN en synoniemen opzoeken - eigen try omdat de acceptability check een break geeft indien niet aanwezig
        try:
            if value['active'] and value['type'] == "FSN" and value['acceptabilityMap']['15551000146102']:
                output['nlpatient']['FSN'] = value['term']
            if value['active'] and value['type'] == "SYNONYM" and value['acceptabilityMap']['15551000146102'] == "PREFERRED":
                output['nlpatient']['PTN'] = value['term']
            if value['active'] and value['type'] == "SYNONYM" and value['acceptabilityMap']['15551000146102'] == "ACCEPTABLE":
                if "SYNONYM" in output['nlpatient']:
                    output['nlpatient']["SYNONYM"][max(output['nlpatient'][value['type']], key=int) + 1] = value['term']
                else:
                    output['nlpatient']["SYNONYM"] = {0 : value['term']}
        except:
            error = True

    # PTN NL/EN opzoeken
        # Nederlandse PTN definieren - eigen try omdat de acceptability check een break geeft indien niet aanwezig
        try:
            if value['lang'] == "nl" and value['type'] == "SYNONYM" and value['active'] and value['acceptabilityMap']['31000146106'] == "PREFERRED":
                output['nl']['PTN'] = value['term']
        except:
            error = True
        # Engels PTN - eigen try omdat de acceptability check een break geeft indien niet aanwezig
        try:
            if value['lang'] == "en" and value['type'] == "SYNONYM" and value['active']:
                output['en']['PTN'] = value['term']
        except:
            error = True

    # Synoniemen NL/EN in nested dictionary zetten voor NL en EN
        try:
            # NL
            if value['type'] == "FSN" and value['lang'] == "nl" and value['active']:
                output['nl'][value['type']] = value['term']
            elif value['type'] == "SYNONYM" and value['lang'] == "nl" and value['active']:
                if value['type'] in output['nl']:
                    output['nl'][value['type']][max(output['nl'][value['type']], key=int)+1] = value['term']
                else:
                    output['nl'][value['type']] = {0 : value['term']}
            # EN
            elif value['type'] == "FSN" and value['lang'] == "en" and value['active']:
                output['en'][value['type']] = value['term']
            elif value['type'] == "SYNONYM" and value['lang'] == "en" and value['active']:
                if value['type'] in output['nl']:
                    output['en'][value['type']][max(output['en'][value['type']], key=int)+1] = value['term']
                else:
                    output['en'][value['type']] = {0 : value['term']}
            else:
                error = True
        except:
            error = True
    return output

def search_term(searchterm, eclterm=False):
# ====== Search Term ======
    output = {}
    output['nl'] = {}
    output['nlpatient'] = {}
    output['en'] = {}
    try:
        if eclterm:
            r = requests.get('{}/MAIN%2FSNOMEDCT-NL/concepts?activeFilter=true&term={}&ecl={}&offset=0&limit=10000'.format(server_ip, searchterm, eclterm))
        else:
            r = requests.get(
                '{}/MAIN%2FSNOMEDCT-NL/concepts?activeFilter=true&term={}&offset=0&limit=10000'.format(server_ip,
                                                                                                          searchterm))
        resultaten = r.json()
        resultaten = resultaten['items'][0]
    except:
        resultaten = False
    return resultaten

def get_children(concept):
    global children
    if concept not in children.keys():
        # Alleen stated descendants = localhost:8080/MAIN%2FSNOMEDCT-NL/concepts?statedEcl=<125589001
        r = requests.get('{}/browser/MAIN%2FSNOMEDCT-NL/concepts/{}/children?form=inferred'.format(server_ip, concept))
        children_local = r.json()
        children.update({concept : children_local})
        print("children [{}] toegevoegd aan cache".format(concept))
    else:
        children_local = children[concept]
    if children_local:
        return children_local
    else:
        return []

def get_alternative(concept):
    # 900000000000527005 = refset SameAs
    # items[additionalFields][targetComponentId] = ID van alternatief
    # output = get_concept[ID van alternatief]
    alternative_list = {}
    global alternative
    if concept not in alternative.keys():
        # try:
            #r = requests.get('{}:{}/MAIN%2FSNOMEDCT-NL/members?referenceSet=900000000000527005&referencedComponentId={}&active=true&offset=0&limit=5000'.format(server_ip, server_port, concept))
        r = requests.get('{}/MAIN%2FSNOMEDCT-NL/members?referencedComponentId={}&active=true&offset=0&limit=5000'.format(server_ip, concept))
        concepten_local_query = r.json()
        concepten_local = concepten_local_query['items']

        # Door alternative maps lopen
        for value in concepten_local:
            #print(value)
            try:
                # 74739000
                # 900000000000527005 SAME AS
                # 900000000000529008 SIMILAR TO
                # 900000000000523009 POSSIBLY EQUIVALENT
                if value['refsetId'] in alternative_list:
                    alternative_list[value['refsetId']][max(alternative_list[value['refsetId']], key=int)+1] = value['additionalFields']['targetComponentId']
                else:
                    alternative_list[value['refsetId']] = {0 : value['additionalFields']['targetComponentId']}
            except:
                error = 1

        alternative.update({concept: alternative_list})
    else:
        concepten_local = alternative[concept]
        print("cache winst alternatief [{}] -> {}".format(concept, alternative[concept]))
    if alternative[concept]:
        #print("alternatief gevonden",alternative)
        output = alternative[concept]
    else:
        output = "Geen alternatief"
        print("Geen alternatief")
    return output


def get_map(concept):
    global maps
    limit = 5000
    if concept not in maps.keys():
        try:
            headers = {
                'Content-Type': 'application/json',
            }
            data = ' { "index" : { "max_result_window": {} } } '.format('1000000')
            url = '{}:{}/_settings'.format(server_ip,server_es_port)
            response = requests.put(url, headers=headers, data=data)
        except:
            print("Kon max resultaten elasticsearch niet verhogen")

        r = requests.get('{}/MAIN%2FSNOMEDCT-NL/members?referenceSet={}&offset=0&limit={}'.format(server_ip, concept, limit))
        maps_local = r.json()
        conceptList = {}
        try:
            while maps_local:
                r = requests.get('{}/MAIN%2FSNOMEDCT-NL/members?referenceSet={}&offset={}&limit={}'.format(server_ip, concept,len(conceptList),limit))
                print("offset: {} limit: {}".format(len(conceptList), limit))
                maps_local = r.json()
                for value in maps_local['items']:
                    conceptList[len(conceptList)+ 1] = value
                print("lengte: ",len(conceptList))
                #dataprint.pprint(conceptList)
        except:
            error = 1
        print("Aan einde loop lengte: {}".format(len(conceptList)))
        print("map [{}] toegevoegd aan cache".format(concept))
        maps.update({concept: conceptList})
    else:
        maps_local = maps[concept]

    if maps_local:
        return maps_local
    else:
        return False


if __name__ == "__main__":
    concept = '36653000'
    data = get_concept(concept)
    dataprint = pprint.PrettyPrinter(indent=4)
    # dataprint.pprint(data)
    print("=== Concept client ===")
    print("NL:")
    dataprint.pprint(data['nl'])
    print("Patient:")
    dataprint.pprint(data['nlpatient'])
    print("EN:")
    dataprint.pprint(data['en'])

    print("\n Search:")
    dataprint.pprint(search_term("Bowen disease of skin"))

    print("\n Map: geen test")

    concept = '74739000'
    data = get_alternative(concept)
    print("\n Alternatief:")
    dataprint.pprint(data)