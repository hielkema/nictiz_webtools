from django.shortcuts import render, redirect
from django.views.generic import TemplateView
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from django.template.defaultfilters import linebreaksbr
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin, UserPassesTestMixin
from django.contrib.postgres.search import SearchQuery, SearchVector, SearchRank
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import User
from django.forms import formset_factory
from django.urls import reverse
from django.db.models import Q
from datetime import datetime
from celery.task.control import inspect, revoke
from pandas import read_excel, read_csv
import xmltodict
import sys, os
import environ
import time
import random
import json
import urllib.request
import re
import natsort

from rest_framework import viewsets
from ..serializers import *
from rest_framework import views
from rest_framework.response import Response
from rest_framework import permissions

from ..tasks import *
from ..forms import *
from ..models import *

class Permission_MappingProject_Access(permissions.BasePermission):
    """
    Global permission check rights to use the RC Audit functionality.
    """
    def has_permission(self, request, view):
        if 'mapping | access' in request.user.groups.values_list('name', flat=True):
            return True

class MappingUsers(viewsets.ViewSet):
    permission_classes = [Permission_MappingProject_Access]

    def retrieve(self, request, pk=None):
        current_user = User.objects.get(id=request.user.id)
        project = MappingProject.objects.get(id=pk, access__username=current_user)
        users = User.objects.all().order_by('username').prefetch_related(
            'groups'
        )
        tasks = MappingTask.objects.all()
        output = []
        # For each user
        for user in users:
            # Check if they have access, or have any tasks to their name. If so, add to list.
            if tasks.filter(user=user).exists() or user.groups.filter(name='mapping | access').exists():
                output.append({
                    'value' : user.id,
                    'text' : user.username,
                })     

        return Response(output)
    def create(self, request):
        task = MappingTask.objects.get(id=request.data.get('task'))
        current_user = User.objects.get(id=request.user.id)
        if MappingProject.objects.filter(id=task.project_id.id, access__username=current_user).exists():

            newuser = User.objects.get(id=request.data.get('user'))
            if task.user == None:    
                source_user = User.objects.get(id=1)
            else:
                source_user = User.objects.get(id=task.user.id)
            target_user = User.objects.get(id=request.data.get('user'))
            current_user = User.objects.get(id=request.user.id)
            task.user = newuser
            task.save()

            # Save snapshot to database
            source_component = MappingCodesystemComponent.objects.get(id=task.source_component.id)
            mappingquery = MappingRule.objects.filter(source_component_id=source_component.id)
            mappingrules = []
            for rule in mappingquery:
                bindings = []
                for binding in rule.mapspecifies.all():
                    bindings.append(binding.id)
                mappingrules.append({
                    'Rule ID' : rule.id,
                    'Project ID' : rule.project_id.id,
                    'Project' : rule.project_id.title,
                    'Target codesystem' : rule.target_component.codesystem_id.codesystem_title,
                    'Target component ID' : rule.target_component.component_id,
                    'Target component Term' : rule.target_component.component_title,
                    'Mapgroup' : rule.mapgroup,
                    'Mappriority' : rule.mappriority,
                    'Mapcorrelation' : rule.mapcorrelation,
                    'Mapadvice' : rule.mapadvice,
                    'Maprule' : rule.maprule,
                    'Active' : rule.active,
                    'Bindings' : bindings,
                })            
            # print(str(mappingrules))
            event = MappingEventLog.objects.create(
                    task=task,
                    action='user_change',
                    action_user=current_user,
                    action_description='Gebruiker:',
                    old_data='',
                    new_data=json.dumps(mappingrules),
                    old=str(source_user),
                    new=str(target_user),
                    user_source=source_user,
                    user_target=target_user,
                )
            event.save()
            print(str(task))
            audit_async.delay('multiple_mapping', task.project_id.id, task.id)

            return Response([])
        else:
            return Response('Geen toegang',status=status.HTTP_401_UNAUTHORIZED)