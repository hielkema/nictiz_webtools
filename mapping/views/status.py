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
import pprint
import environ
import time
import random
import json
import urllib.request
import re
import natsort

from ..serializers import *
from rest_framework import views, viewsets, status, permissions
from rest_framework.response import Response

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

class MappingStatuses(viewsets.ViewSet):
    permission_classes = [Permission_MappingProject_Access]

    def retrieve(self, request, pk=None):
        current_user = User.objects.get(id=request.user.id)
        project = MappingProject.objects.get(id=pk, access__username=current_user)
        status_list = MappingTaskStatus.objects.filter(project_id = project).order_by('status_id')
        output=[]
        for status in status_list:
            output.append({
                'project' : status.project_id.id,
                'title' : status.status_title,
                'text' : status.status_title,
                'status_id' : status.status_id,
                'value' : status.id,
                'id' : status.id,
                'description' : status.status_description,
                'next' : status.status_next,
            })

        return Response(output)

    def create(self, request):
        task = MappingTask.objects.get(id=request.data.get('task'))
        current_user = User.objects.get(id=request.user.id)
        if ('mapping | change task status' in request.user.groups.values_list('name', flat=True)) and MappingProject.objects.filter(id=task.project_id.id, access__username=current_user).exists():
            current_user = User.objects.get(id=request.user.id)
            new_status = MappingTaskStatus.objects.get(id=request.data.get('status'))
            old_status = task.status.status_title
            old_task = str(task)
            task.status = new_status
            task.save()

            # Save snapshot to database
            source_component = MappingCodesystemComponent.objects.get(id=task.source_component.id)
            mappingquery = MappingRule.objects.filter(source_component_id=source_component.id)
            mappingrules = {}
            for rule in mappingquery:
                mappingrules.update({rule.id : {
                    'Project ID' : rule.project_id.id,
                    'Project' : rule.project_id.title,
                    'Target component ID' : rule.target_component.component_id,
                    'Target component Term' : rule.target_component.component_title,
                    'Mapgroup' : rule.mapgroup,
                    'Mappriority' : rule.mappriority,
                    'Mapcorrelation' : rule.mapcorrelation,
                    'Mapadvice' : rule.mapadvice,
                    'Maprule' : rule.maprule,
                    'Active' : rule.active,
                }})

            event = MappingEventLog.objects.create(
                task=task,
                action='status_change',
                action_user=current_user,
                action_description='Status:',
                old_data='',
                new_data=str(mappingrules),
                old=old_status,
                new=task.status.status_title,
                user_source=current_user,
            )
            event.save()
            audit_async.delay('multiple_mapping', task.project_id.id, task.id)

            return Response([])
        else:
            return Response('Geen toegang',status=status.HTTP_401_UNAUTHORIZED)