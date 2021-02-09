# Step 1: Add this file to __init__.py
# Step 2: Add your functions below.
# Step 3: Don't forget to fire the task somewhere if that is the intended use of this file.


# Create your tasks here
from __future__ import absolute_import, unicode_literals
from celery import shared_task
import time, json
from celery.task.schedules import crontab
from celery.result import AsyncResult
from celery.decorators import periodic_task
from celery.utils.log import get_task_logger
import xmltodict
from ..models import *
import urllib.request
import environ

# Import environment variables
env = environ.Env(DEBUG=(bool, False))
# reading .env file
environ.Env.read_env(env.str('ENV_PATH', '.env'))

logger = get_task_logger(__name__)

# Example task
# @shared_task
# def function_title(kwarg):
#       logger.info("Doing something with "+str(kwarg))
#       output = "Success!"
#       return output