# TODO - opruimen code. Nog veel residu van de standalone module.
# V0.1 decentralized module

from __future__ import division
import requests, time, sys, pandas, datetime, os
from .snowstorm_client import Snowstorm


def html_tree(concept):
    global concepten, children, descendants, alternative, maps, loopnummer, start, stop, filename

    # Start tijdregistratie
    start = time.time()

    # Server IP
    server_ip = 'termservice.test-nictiz.nl'
    # Server port
    server_port = '8080'


    # TODO - opruimen ongebruikte modifiers
    # Functie modifiers. Voor meest uitgebreide cache allen behalve include_children_noDT op True zetten
    # Meenemen van kinderen als alle kinderen van het huidige concept niet in de DT staan? True/False
    include_children_noDT = True # nog niet functioneel
    # Concept tonen als deze niet in de DT staat? Irrelevant als crosscheck_markup uit staat: =dan altijd True. True/False
    include_if_noDT = True # nog niet functioneel
    # Markup t.a.v. crosscheck? / <mark> indien in DT? True/False
    crosscheck_markup = False
    # Cache run? -> maximaal opvragen
    cache_execute = False

    # start loopteller
    loopnummer = 0

    # open placeholders
    checkDescendants = False

    # dictionaries tbv caching
    concepten = {}
    children = {}
    descendants = {}
    alternative = {}
    maps = {}


    # timestamp voor bestand
    ts = time.time()
    ts = str.split(str(ts),".")
    # Save the resulting html file
    w = get_concept(concept)
    try:
        nlFSN = w['nl']['PTN']
    except:
        nlFSN = w['en']['FSN']
    filename = "[{}] - {}.html".format(concept, ts[0])

    # Maken container voor schrijven van .html
    writeFolder = "/webserver/static_files/tree/"
        
    print("Output richting: "+ writeFolder + filename)
    f = open(writeFolder + filename,"w+")

    # Header in bestand schrijven
    with open(os.path.dirname(os.path.abspath(__file__))+"/resources/header.html","r") as header:
        f.write(header.read())

    # Header in bestand schrijven

    # Crossreference lijst inladen (CrossReferenceItems)
    cri = pandas.read_csv(os.path.dirname(os.path.abspath(__file__))+"/resources/crossreference.csv", sep="\t")
    # Alle kolommen converteren naar strings tbv zoekfunctie
    cri = cri.applymap(str)

    def lookupDT(searchterm, searchcolumn, returncolumn):
        try:
            query = cri.loc[cri[searchcolumn] == searchterm][returncolumn].values
            query = query[0]
            return query
        except:
            return 'Error lookupDT'


    def crossCheck(concept):
        found = cri[cri['SCTID'].str.match(str(concept))]
        aantal = found.count()
        if aantal['SCTID'] > 0:
            return True
        else:
            return False

    def crossCheckDescendants(concept):
        global descendants
        if concept not in descendants.keys():
            # Alleen stated descendants = http://localhost:8080/MAIN/concepts?statedEcl=<125589001
            #http://localhost:8081/MAIN/concepts?ecl=<{}&limit=10000
            r = requests.get('http://{}:{}/MAIN/concepts/{}/descendants?stated=false&offset=0&limit=10000'.format(server_ip, server_port, concept))
            descendant_local = r.json()
            descendant_local = descendant_local['items']
            descendants.update({concept : descendant_local})
            print("descendants [{}] toegevoegd aan cache".format(concept))
        else:
            descendant_local = descendants[concept]
            print("cache winst descendants [{}]".format(concept))
        #if descendant_local['total'] > 9999:
        #    sys.exit("Meer dan 10.000 resultaten bij descendant-check - afgebroken")
        aanwezig = False
        for index in descendant_local:
            if crossCheck(index['conceptId']):
                aanwezig = True
        if aanwezig == True:
            return True
        else:
            return False


    def children_array(concept):
        global loopnummer, start, cache_execute, checkDescendants

        children = get_children(concept)

        # als kinderen aanwezig, door met script
        if children:
            f.write("<ul>")
            for index, value in enumerate(children):
                crosscheckdescendants = crossCheckDescendants(value['conceptId'])
                current = {}
                current = get_concept(value['conceptId'])
                try:
                    nlpatient = current['nl']['patient']
                except:
                    # nlpatient = "[Geen NL patiententerm]"
                    nlpatient = " "
                try:
                    nl_term = current['nl']['FSN']
                except:
                    nl_term = ""

                # get_concept(value['conceptId'])
                if include_children_noDT and get_children(current['conceptId']):
                    f.write("<li><span id=nest class=caret>")
                elif not include_children_noDT and crosscheckdescendants:
                    f.write("<li><span id=nest class=caret>")
                elif not include_children_noDT and not crosscheckdescendants:
                    f.write("<li>")
                else:
                    f.write("<li>")

                if crosscheck_markup and include_if_noDT:
                    crosscheck = crossCheck(current['conceptId'])
                    if crosscheck:
                        f.write("\n <mark>{} / {} - DT [{}: {}]</mark>".format(current['en']['FSN'], nl_term, lookupDT(current['conceptId'], 'SCTID', 'DT-id'), lookupDT(current['conceptId'], 'SCTID', 'Referentieterm')))
                    elif not crosscheck:
                        f.write("\n {} --- <mark><a href=\"https://nl-prod-main.termspace.com/app.html?project=Netherlands%20Dutch%20Translation&mode=authoring&concept={}\" target=_blank>{}</a></mark>".format(value['pt']['term'], value['conceptId'], nl_term))
                elif crosscheck_markup and not include_if_noDT:
                    crosscheck = crossCheck(value['conceptId'])
                    if crosscheck:
                        f.write("\n [{} / {}] - DT [{}: {}]".format(current['en']['FSN'], nl_term, lookupDT(current['conceptId'], 'SCTID', 'DT-id'), lookupDT(current['conceptId'], 'SCTID', 'Referentieterm')))
                    elif not crosscheck:
                        #f.write("\n [concept niet in DT - overslaan]")
                        f.write("")
                else:
                    try:
                        synoniemen = current['nl']['SYNONYM']
                        synoniemen_nl = []
                        for values in synoniemen.values():
                            synoniemen_nl.append(values)
                        synoniemen_nl = '<br>'.join(synoniemen_nl)
                    except:
                        synoniemen_nl = "Geen synoniemen"
                    try:
                        synoniemen = current['en']['SYNONYM']
                        synoniemen_en = []
                        for values in synoniemen.values():
                            synoniemen_en.append(values)
                        synoniemen_en = '<br>'.join(synoniemen_en)
                    except:
                        synoniemen_en = "Geen synoniemen"

                    try:
                        tooltip_nl = "<b>NEDERLANDS</b><hr><b>SCTID:</b> {} <br> <b>FSN:</b> {} <br><b>PTN:</b> {} <br><b>Synoniemen:</b><br> {}".format(value['conceptId'], current['nl']['FSN'], current['nl']['PTN'], synoniemen_nl)
                    except:
                        tooltip_nl = False
                    try:
                        tooltip_en = "<b>ENGELS</b><hr><b>SCTID:</b> {} <br> <b>FSN:</b> {} <br><b>PTN:</b> {} <br><b>Synoniemen:</b><br> {}".format(value['conceptId'], current['en']['FSN'], current['en']['PTN'], synoniemen_en)
                    except:
                        tooltip_en = False

                    f.write("[{}] <div class=tooltip><font class=english>{}</font> | <font class=dutch>{} <span class=tooltiptext_nl>{}</span><span class=tooltiptext_en>{}</span></div></font> <a href=\"https://nl-prod-main.termspace.com/app.html?project=Netherlands%20Dutch%20Translation&mode=authoring&concept={}\" target=_blank>Termspace</a>".format(current['conceptId'], current['en']['FSN'], nl_term, tooltip_nl, tooltip_en, current['conceptId']))

                if include_children_noDT and get_children(current['conceptId']):
                    f.write("</span><ul id=nest class=nested>")
                elif not include_children_noDT and crosscheckdescendants:
                    f.write("</span><ul id=nest class=nested>")
                elif not include_children_noDT and not crosscheckdescendants:
                    f.write(" <i><small>[kinderen verborgen; 0 in DT]</small></i></li>")
                else:
                    f.write("</li>")

                interim = time.time()
                loopnummer+=1
                print("#{} - {}min [{} / {}]".format(loopnummer, round((interim-start)//60), value['pt']['term'], nl_term))
                if include_children_noDT:
                    children_array(current['conceptId'])
                elif not include_children_noDT and crosscheckdescendants:
                    children_array(current['conceptId'])

                if include_children_noDT and get_children(current['conceptId']):
                    f.write("</ul></li>")
                elif not include_children_noDT and crosscheckdescendants:
                    f.write("</ul></li>")
                elif not include_children_noDT and not crosscheckdescendants:
                    f.write("</li>")
                else:
                    f.write("</li>")
            f.write('</ul>')
        #elif not children:
            #f.write("geen kinderen voor dit concept")


    # Opgeroepen root concept tonen en lijst openen
    w = get_concept(concept)
    try:
        nlFSN = w['nl']['PTN']
    except:
        nlFSN = w['en']['FSN']

    print("Lijst met kinderen voor concept [{}]: {}. NL: {}".format(concept, w['en']['FSN'], nlFSN))
    f.write("Lijst met kinderen voor concept [{}]: {}. NL: {}".format(concept, w['en']['FSN'], nlFSN))


    children_array(concept)

    # Lijst sluiten
    f.write("</ul>")

    # Footer in bestand schrijven
    with open(os.path.dirname(os.path.abspath(__file__))+"/resources/footer.html","r") as footer:
        f.write(footer.read())

    # Print variabele f naar bestand
    f.close()


    #stop tijdregistratie
    stop = time.time()
    # Printen totale duur van script
    print("Script executie heeft {} seconden geduurd. Bestandsnaam: {}".format(round(stop-start,1), filename))

    return [filename, w['en']['FSN']]

if __name__ == "__main__":
    print(html_tree("36653000"))