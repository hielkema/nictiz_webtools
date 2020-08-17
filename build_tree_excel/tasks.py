# Create your tasks here
from __future__ import absolute_import, unicode_literals
from celery import shared_task, current_task
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
import environ

from .build_tree import *

import csv, multiprocessing, pandas, sys, os
from openpyxl import Workbook
from os import listdir
import glob

from urllib.request import urlopen, Request
import urllib.parse

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

logger = get_task_logger(__name__)

@shared_task
def termspace_audit(worklist=None):
    termspace_token = 'ysycphe72ghbbawjdbolpu'
    url = 'https://nl-prod-main.termspace.com/api/users/login'
    payload = {
        'username' : env('termspace_user2'),
        'password' : env('termspace_pass2'),
        }
    data = urllib.parse.urlencode(payload)
    data = data.encode('ascii')
    req = urllib.request.Request(url, data)
    with urllib.request.urlopen(req) as response:
        result = json.loads(response.read())

    termspace_token = result.get('token',False)

    def get_tasks_per_concept(conceptid):
        def load_tasks(start=0, limit=100, conceptid=conceptid, published='false'):
            # Per user
            url = "https://nl-prod-main.termspace.com/api/workflow/nl-edition/workflow/instances/112?projectId=57be297bc9fbcde30c573aa0&access_token={token}&name={conceptid}&excludePublished=false&workList=asd&viewPublished={published}&limit={limit}&skip={start}&dontUseWorklist=true".format(token=termspace_token, conceptid=conceptid, limit=limit, start=start, published=published)
            req = Request(url)
            response = urlopen(req).read()
            response = json.loads(response)
            return response
            
        print('Start ophalen takenlijst voor ',conceptid)
        tasks = []
        start = 0
        limit = 30000
        while True:
            result = load_tasks(start=start, limit=limit, conceptid=conceptid, published='false')
            if result:
                for item in result:
                    tasks.append(item)
                start += limit
                if len(result) == 0: break
            else:
                break

        start = 0
        limit = 30000
        while True: 
            result = load_tasks(start=start, limit=limit, conceptid=conceptid, published='true')
            if result:
                for item in result:
                    tasks.append(item)
                start += limit
                if len(result) == 0: break
            else:
                break
        return tasks

    headers       = [
        'Concept ID',
        'FSN',
        'Assignee',
        'Author',
        'Workflowstate',
        'Worklist',
        'Folder',
        'ProjectID',
        'Path'
        ]
    workbook_name = str(time.time()).split(".")[0]+'_termspace_export.xlsx'
    wb = Workbook()
    page = wb.active
    page.title = 'Taken in termspace'
    page.append(headers)

    for concept in worklist.splitlines():
        taskdata = get_tasks_per_concept(concept)
        print("---------------")
        print(taskdata)
        for task in taskdata:
            output_row = [
                str(task.get('terminologyComponent',{}).get('id',"Geen")),
                str(task.get('terminologyComponent',{}).get('name',"Geen")),
                str(task.get('assignee')),
                str(task.get('authorId')),
                str(task.get('workflowState')),
                str(task.get('workList')),
                str(task.get('folder')),
                str(task.get('projectId')),
                str(task.get('path',{}).get('name',"Geen")),
            ]
            page.append(output_row)
    wb.save(filename = "/webserver/static_files/termspace_qa/"+workbook_name)
            

@shared_task
def build_flat_tree_async(sctid=None, username=None):
    # Taak in database plaatsen
    task = taskRecordBuildFlat.objects.create(
        task="Build tree",
        username=username,
        searchterm=sctid,
        conceptFSN=sctid,
        execution_time=0,
        output_available=False,
        filename="NULL",
        celery_task_id=current_task.request.id,
    )
    task.save()

    start = time.time()
    output = html_tree(str(sctid))
    #print ("[{}] ******* {} / {} *******".format(task_id, output[0], output[1]))

    stop = time.time()

    # DB updaten met resultaten
    taskUpdate = taskRecordBuildFlat.objects.get(id=task.id)
    taskUpdate.conceptFSN = output[1]
    taskUpdate.execution_time = round(stop - start, 1)
    taskUpdate.filename = output[0]
    taskUpdate.output_available = True
    taskUpdate.finished = True
    taskUpdate.save()

    pass
    # Aan te passen zodat de bestandsnaam teruggegeven wordt aan het bestand?
    # Anders hier na voltooien e-mail sturen aan gebruiker, en overzicht met bestanden per gebruiker maken.