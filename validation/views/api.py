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
class export_answers(viewsets.ViewSet):
    permission_classes = [permissions.AllowAny]
    def list(self, request):
  
        answers = Answer.objects.all()

        output = []

        # Add one row with column names for use with power query
        output.append({
            'date' : 'Datum',
            'task' : 'Taak ID (tool intern)',
            'participantId'     : 'ParticipantId',
            'sortIndex'         : 'SortIndex',
            'SctConceptId'      : 'SctConceptId',
            'CannotValidate'    : 'CannotValidate',
            'WhyNotValidate'    : 'WhyNotValidate',
            'ContainsErrors'    : 'ContainsErrors',
            'Errors'            : 'Errors',
            'Completeness'      : 'Completeness',
            'Relevance'         : 'Relevance',
            'Clarity'           : 'Clarity',
            'IsAcceptable'      : 'IsAcceptable',
            'NotAcceptableNotes': 'NotAcceptableNotes',
            'Suggestion'        : 'Suggestion',
            })


        for answer in answers:
            task = answer.task.data

            # Modify cannot_validate to correct format
            cannot_validate = 0
            if answer.data.get('cannot_validate',False): cannot_validate = 1


            # Add answer to output list
            output.append({
                'date' : answer.created,
                'task' : answer.task.id,
                'participantId' : answer.user.username,
                'sortIndex'  : task.get('sortIndex'),
                'SctConceptId'  : task.get('sctId'),
                'CannotValidate'    : cannot_validate,
                'WhyNotValidate'    : answer.data.get('why_no_validate',None),
                'ContainsErrors'    : answer.data.get('errors',None),
                'Errors'            : answer.data.get('what_errors',None),
                'Completeness'      : answer.data.get('complete',None),
                'Relevance'         : answer.data.get('relevance',None),
                'Clarity'           : answer.data.get('clarity',None),
                'IsAcceptable'      : answer.data.get('acceptable',None),
                'NotAcceptableNotes': answer.data.get('feedback_notes',None),
                'Suggestion'        : answer.data.get('feedback_suggestion',None),
            })

        context = output

        return Response(context)


class export_tasks(viewsets.ViewSet):
    permission_classes = [permissions.AllowAny]
    def list(self, request):
  
        output = []

        # Add one row with column names for use with power query
        output.append({
                'user' : 'Gebruiker',
                'task' : 'Taak ID (tool intern)',
                'sortIndex' : 'SortIndex',
             })

        users = User.objects.all()

        for user in users:
            tasks = Task.objects.filter(access = user)

            if tasks.count() > 0:
                # Add task to output list
                for task in tasks:
                    output.append({
                        'task' : task.id,
                        'sortIndex' : task.data.get('sortIndex'),
                        'user' : user.username,
                    })

        context = output

        return Response(context)