# Create your tasks here
from __future__ import absolute_import, unicode_literals
from celery import shared_task
from .med_lookup import *
import time


@shared_task
def send_post_signup_email(user_pk=None):
    print("Post signup ... user_pk={}".format(user_pk))
    med_lookup(user_pk)
    pass