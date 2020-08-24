# Create your tasks here
from __future__ import absolute_import, unicode_literals
from celery import shared_task
from .models import *
import time, json
from urllib.request import urlopen, Request
import urllib.parse
import environ

# Import environment variables
env = environ.Env(DEBUG=(bool, False))
# reading .env file
environ.Env.read_env(env.str('ENV_PATH', '.env'))

# @shared_task
# def load_termspace_comments():
#     token = None