from django.shortcuts import render

# Create your views here.

# howdy/views.py
from django.shortcuts import render, redirect
from django.views.generic import TemplateView
from django.conf import settings
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from django.template.defaultfilters import linebreaksbr
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin, UserPassesTestMixin
from urllib.request import urlopen, Request
import urllib.parse
from django.contrib.postgres.search import SearchQuery, SearchVector, SearchRank
from django.db.models import Q
from django.db.models.functions import Trunc, TruncMonth, TruncYear, TruncDay
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Max
import json
from ..forms import * 
from ..models import *
from mapping.models import *
from datetime import datetime, timedelta
from django.utils import timezone
import pytz
from ..tasks import *
import time
import environ
import pandas as pd

from rest_framework import viewsets
from ..serializers import *
from rest_framework import views
from rest_framework.response import Response
from rest_framework import permissions

from snowstorm_client import Snowstorm

# Import environment variables
env = environ.Env(DEBUG=(bool, False))
# reading .env file
environ.Env.read_env(env.str('ENV_PATH', '.env'))

class Permission_Validation_access(permissions.BasePermission):
    """
    Global permission check - rights to the translation validation module
    """
    def has_permission(self, request, view):
        if 'validation | access' in request.user.groups.values_list('name', flat=True):
            return True

# Provide statistics on remaining and finished tasks
class total_number_of_tasks(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]
    def list(self, request, pk=None):
        
        current_user = request.user
        all_tasks = Task.objects.all()
        tasks = all_tasks.filter(access = current_user)

        context = {
            'open' : {
                'count' : tasks.count(),
            },
            'total' : {
                'count' : all_tasks.count(),
            },
            'user' : str(current_user)
        }

        return Response(context)


# Send the next task
class next_task(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]
    def list(self, request, pk=None):
        
        current_user = request.user
        
        tasks = Task.objects.filter(access = current_user)
        tasks.order_by('data__sortIndex')

        if tasks.count() > 0:
            task = tasks.first()
            output = {
                    'id' : task.id,
                    'data' : task.data,
                }
        else:
            output = False

        return Response(output)
    

# Add users to tasks
class create_tasks(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]
    def create(self, request):
        current_user = request.user
        payload = request.data.get('payload')

        selected_user = User.objects.get(id = payload.get('user'))

        for task in payload.get('tasks').splitlines():
            print(f"Handling {task}")
            try:
                db_task = Task.objects.get(data__sortIndex = int(task))
                print(f"Found task {str(db_task)}")

                if payload.get('action') == "add":
                    print(f"Add user with ID {payload.get('user')} ({selected_user}) to task.")
                    db_task.access.add(selected_user)
                    db_task.save()
                elif payload.get('action') == "remove":
                    print(f"Remove user with ID {payload.get('user')} ({selected_user}) from task.")
                    db_task.access.remove(selected_user)
                    db_task.save()
                else:
                    print("Request did not contain any action. None taken.")

                print(f"Resulting users with access to task: {db_task.access.values('username')}")

            except Exception as e:
                print(task, "==>", e)

            print(f"Finished handling task {task}\n")

        output = ''




        return Response(output)
    