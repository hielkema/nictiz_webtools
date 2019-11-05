# Create your tasks here
from __future__ import absolute_import, unicode_literals
from celery import shared_task, current_task
from .build_tree import *
from .models import *
import time
from celery.task.schedules import crontab
from celery.result import AsyncResult
from celery.decorators import periodic_task

@shared_task
def build_tree_async(sctid=None, username=None):
    # Taak in database plaatsen
    task = taskRecord.objects.create(
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
    output = html_tree(sctid)
    # print ("[{}] ******* {} / {} *******".format(task_id, output[0], output[1]))

    stop = time.time()

    # DB updaten met resultaten
    taskUpdate = taskRecord.objects.get(id=task.id)
    taskUpdate.conceptFSN = output[1]
    taskUpdate.execution_time = round(stop - start, 1)
    taskUpdate.filename = output[0]
    taskUpdate.output_available = True
    taskUpdate.finished = True
    taskUpdate.save()

    pass
    # Aan te passen zodat de bestandsnaam teruggegeven wordt aan het bestand?
    # Anders hier na voltooien e-mail sturen aan gebruiker, en overzicht met bestanden per gebruiker maken.


# Cleanup van bestanden na x tijd
@periodic_task(run_every=(crontab(minute='*/1')), name="some_task", ignore_result=False)
def some_task():
    # TODO - Toevoegen opruimtaak. Dan ook boolean output_available op False zetten.
    print("\n\n*************** test **************\n\n")