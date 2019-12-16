# Create your tasks here
from __future__ import absolute_import, unicode_literals
from celery import shared_task, current_task
from .modules.build_tree_excel import *
from .modules.build_tree_html import *
from .models import *
import time
from celery.task.schedules import crontab
from celery.result import AsyncResult
from celery.decorators import periodic_task

@shared_task
def snomed_list_generator_excel_v01(sctid=None, username=None):
    # Taak in database plaatsen
    task = snomedListGeneratorLog.objects.create(
        task="Excel tree",
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
    output = excel_tree(str(sctid))

    stop = time.time()

    # DB updaten met resultaten
    taskUpdate = snomedListGeneratorLog.objects.get(id=task.id)
    taskUpdate.conceptFSN = output[1]
    taskUpdate.execution_time = round(stop - start, 1)
    taskUpdate.filename = output[0]
    taskUpdate.output_available = True
    taskUpdate.finished = True
    taskUpdate.save()

    pass

@shared_task
def snomed_list_generator_html_v01(sctid=None, username=None):
    # Taak in database plaatsen
    task = snomedListGeneratorLog.objects.create(
        task="HTML tree",
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

    stop = time.time()

    # DB updaten met resultaten
    taskUpdate = snomedListGeneratorLog.objects.get(id=task.id)
    taskUpdate.conceptFSN = output[1]
    taskUpdate.execution_time = round(stop - start, 1)
    taskUpdate.filename = output[0]
    taskUpdate.output_available = True
    taskUpdate.finished = True
    taskUpdate.save()

    pass