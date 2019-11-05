# Create your tasks here
from __future__ import absolute_import, unicode_literals
from celery import shared_task
import time
from celery.task.schedules import crontab
from celery.result import AsyncResult
from celery.decorators import periodic_task
from .forms import *
from .models import *
import urllib.request
# Get latest snowstorm client. Set master or develop
# branch = "develop"
# url = 'https://raw.githubusercontent.com/mertenssander/python_snowstorm_client/' + \
#     branch+'/snowstorm_client.py'
# urllib.request.urlretrieve(url, 'snowstorm_client.py')
from snowstorm_client import Snowstorm

@shared_task
def import_snomed_async(focus=None, codesystem=None):
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
        codesystem_obj = MappingCodesystem.objects.get(id=codesystem)
        obj, created = MappingCodesystemComponent.objects.get_or_create(
            codesystem_id_id=codesystem_obj.id,
            component_id=conceptid,
        )
        print("CREATED **** ",codesystem, conceptid)
        # Add data not used for matching
        obj.component_title = str(concept['fsn']['term'])
        obj.component_extra_1 = str(concept['pt']['term'])

        # Save
        obj.save()

# @shared_task
# def send_post_signup_email(user_pk=None):
#     print("Post signup ... user_pk={}".format(user_pk))
#     med_lookup(user_pk)
#     pass