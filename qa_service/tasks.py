# Create your tasks here
from __future__ import absolute_import, unicode_literals
from celery import shared_task
from .models import *
from mapping.models import *
import time, json
from urllib.request import urlopen, Request
import urllib.parse
import environ
from snowstorm_client import Snowstorm

# Import environment variables
env = environ.Env(DEBUG=(bool, False))
# reading .env file
environ.Env.read_env(env.str('ENV_PATH', '.env'))
