import pandas, json, requests, re, pickle, xlwt, xlrd, time, datetime, sys, os
from xlutils.copy import copy
from xlrd import open_workbook
from xlwt import easyxf

def med_lookup(zoekterm):
    directory = os.path.dirname(os.path.abspath(__file__))
    #start tijdregistratie
    start = time.time()

    bst020t = pandas.read_csv(directory+"/resources/gstandaard/bst020t.csv", sep=";")
    bst020t = bst020t.applymap(str)

    bst711t = pandas.read_csv(directory+"/resources/gstandaard/bst711t.csv", sep=";")
    bst711t = bst711t.applymap(str)

    #bst750t = pandas.read_csv(directory+"/resources/gstandaard/bst750t.csv", sep=";")
    #bst750t = bst750t.applymap(str)

    bst801t = pandas.read_csv(directory+"/resources/gstandaard/bst801t.csv", sep=";")
    bst801t = bst801t.applymap(str)

    #bst902t = pandas.read_csv(directory+"/resources/gstandaard/bst902t.csv", sep=";", encoding = "ISO-8859-1")
    #bst902t = bst902t.applymap(str)

    print("Data:")

    #tijdVoorBestandsnaam = str(start)
    #tijdVoorBestandsnaam = tijdVoorBestandsnaam.split(".")
    #bestandsnaam = directory+"/resources/gstandaard/Zoekterm {} - {}.txt".format(zoekterm, tijdVoorBestandsnaam[0])
    #l = open(bestandsnaam,"w+")

    # Zoek naar matches in ATOMSE (engelse ATC naam)
    atcnamen = bst801t[bst801t['atomse'].str.contains(zoekterm, case=False)]
    atcnamen = atcnamen.values
    outputDict = {}
    output = ""
    for index in atcnamen:
        gpnaam = bst711t.loc[bst711t['atcode'] == index[2]]['gpnmnr']
        etiketnamen={}
        # Loop voor alle GST naamnummers geassocieerd met de ATC code
        for index2 in gpnaam:
            naam = bst020t.loc[bst020t['nmnr'] == index2]
            #farmaceutische_vorm_code = bst711t.loc[bst711t['gpkode'] == value]['gpktvr'].values
            etiketnamen.update(naam['nmnaam'])
        if not etiketnamen:
            etiketnamen = {1:"Geen match in G-standaard"}
        print("[DEBUG]\nATC EN: {}\nATC NL: {}\nGST: {}\n".format(index[4], index[3], etiketnamen))

        #l.write(("ATC EN: {}\nATC NL: {}\nGST:\n- {}\n--------------------------\n".format(index[4], index[3], etiketnamen)))
        #output = ("{}ATC EN: {}\nATC NL: {}\nGST:\n- {}\n--------------------------\n".format(output, index[4], index[3], etiketnamen))
        updatewaarde = {
                            len(outputDict)+1 :
                            {
                                "ATC Engels":index[4],
                                "ATC Nederlands":index[3],
                                "G-standaard":etiketnamen
                            },
                        }
        outputDict.update(updatewaarde)
    return(outputDict)
    #l.close()