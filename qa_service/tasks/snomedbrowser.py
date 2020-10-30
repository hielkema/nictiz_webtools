import time

from ..serializers import *

from urllib.request import urlopen, Request

from celery import shared_task
from celery.execute import send_task

from bs4 import BeautifulSoup
import pymsteams

@shared_task
def checkFSN(concept_list = []):

    ### Format: ###
    # concept_list = [
    #         {'id':'18213006', 'fsn': 'elektriciteit (fysische kracht)'},
    #         {'id':'18213006', 'fsn': 'elektricity (fout)'},
    #     ]
    ###############

    foutmeldingen = []

    def request_fsn(conceptid):
        url = f"https://terminologie.nictiz.nl/terminology/snomed/viewConcept/{conceptid}"
        req = Request(url)
        req.add_header('Accept-Language', 'nl')
        response = urlopen(req).read()
        parsed_html = BeautifulSoup(response, features="html.parser")

        return parsed_html.body.find('span', attrs={'style':'font-size:110%;font-weight:bold;'}).text

    try:
        for item in concept_list:
            browser_waarde = request_fsn(item['id'])
            if item['fsn'] == browser_waarde:
                True
            else:
                foutmeldingen.append({
                    'id' : item['id'],
                    'fsn_desired' : item['fsn'],
                    'fsn_true' : browser_waarde,
                })

        output = {
            'snomedbrowser.checkFSN' : {
                'Percentage fouten' : int(len(foutmeldingen)/len(concept_list)*100),
                'Foutmeldingen' : foutmeldingen,
            }
        }
    except Exception as e:
        output = {
            'snomedbrowser.checkFSN' : {
                'Percentage fouten' : 100,
                'Foutmeldingen' : f'Functie heeft een fout gemeld: {e}',
            }
        }

    return output

@shared_task
def checkPTFriendly(concept_list = []):

    ### Format: ###
    # concept_list = [
    #         {'id':'18213006', 'fsn': 'elektriciteit (fysische kracht)'},
    #         {'id':'18213006', 'fsn': 'elektricity (fout)'},
    #     ]
    ###############

    foutmeldingen = []

    def request_ptfriendly_pt(conceptid):
        url = f"https://terminologie.nictiz.nl/terminology/snomed/viewConcept/{conceptid}"
        req = Request(url)
        req.add_header('Accept-Language', 'nl')
        response = urlopen(req).read()
        parsed_html = BeautifulSoup(response, features="html.parser")

        result = parsed_html.body.find('img', attrs={'src':'/terminology/resources/images/languageRefsets/15551000146102.png'}).parent.parent.parent
        result = result.find('div', attrs={'title':'Preferred term'}).text
        return result
    try:
        for item in concept_list:
            browser_waarde = request_ptfriendly_pt(item['id'])
            if item['pt'] == browser_waarde:
                True
            else:
                foutmeldingen.append({
                    'id' : item['id'],
                    'pt_desired' : item['pt'],
                    'pt_true' : browser_waarde,
                })

        output = {
            'snomedbrowser.checkPTFriendly' : {
                'Percentage fouten' : int(len(foutmeldingen)/len(concept_list)*100),
                'Foutmeldingen' : foutmeldingen,
            }
        }
    except Exception as e:
        output = {
            'snomedbrowser.checkFSN' : {
                'Percentage fouten' : 100,
                'Foutmeldingen' : f'Functie heeft een fout gemeld: {e}',
            }
        }

    return output