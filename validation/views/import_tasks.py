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
class import_tasks(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]
    def retrieve(self, request, pk=None):

        # Select correct project
        project = Project.objects.get(title = 'Validatie patiëntvriendelijke beschrijvingen AMC')
        print(project)

        # Get data from .tsv file
        df = pd.read_csv('./validation/resources/importdata.tsv', sep='\t', encoding = "ISO-8859-1")
        
        output = []
        for index, row in df.iterrows():
            # sortIndex sctId	dtId	preferredTerm	text
            data = {
                'sortIndex'     : int(row[0]),
                'sctId'         : int(row[1]),
                'dtId'          : int(row[2]),
                'preferredTerm' : str(row[3]),
                'text'          : str(row[4]),
            }
            output.append(data)
            obj, created = Task.objects.get_or_create(
                project = project,
                data = data,

            )
            if created:
                obj.status = project.new_status
                obj.save()
            data.update({
                'created' : created,
            })
        
        context = output

        return Response(context)