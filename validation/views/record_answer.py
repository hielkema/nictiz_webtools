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

# Search termspace comments
class receive_form(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]
    def create(self, request):
  
        data = request.data.get('payload')
        print(f"Received form from {str(request.user)} => {data}")

        current_user = User.objects.get(id = request.user.id)
        print(f"Task ID = {request.data.get('payload').get('taskId')}")
        task = Task.objects.get(id = request.data.get('payload').get('taskId'))

        # Some logic
        if data.get('errors') == 0:
            data['what_errors'] = ''
        if data.get('cannot_validate') == 0:
            data['why_no_validate'] = ''
        elif data.get('cannot_validate') == 1:
            data['errors'] = None
            data['what_errors'] = None
            data['clarity'] = None
            data['relevance'] = None
            data['acceptable'] = None
            data['complete'] = None
            data['feedback'] = None

        obj = Answer.objects.create(
            task = task,
            user = current_user,
            data = data,
        )

        task.access.remove(current_user)

        context = {
            'received' : request.data.get('payload'),
            'obj' : str(obj),
        }

        return Response(context)