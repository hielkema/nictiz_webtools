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

class Projects(viewsets.ViewSet):
    permission_classes = [Permission_MappingProject_Access]

    def list(self, request):
        # List all projects
        # TODO filter on which projects the user has access to
        current_user = User.objects.get(id=request.user.id)
        projects = MappingProject.objects.filter(active=True).filter(access__username=current_user)
    
        project_list = []
        for project in projects:
            # if project.access.filter(username=current_user).exists():
            # Get task count for current user
            tasks = MappingTask.objects.filter(user=current_user, project_id=project).exclude(status=project.status_complete).exclude(status=project.status_rejected)
            project_list.append({
                'id' : project.id,
                'active' : project.active,
                'title' : project.title,
                'source' : project.source_codesystem.codesystem_title,
                'target' : project.target_codesystem.codesystem_title,
                'open_tasks' : tasks.count(),
            })
        return Response(project_list)
    def retrieve(self, request, pk=None):
        # Details on the selected project
        # TODO filter on which projects the user has access to
        current_user = User.objects.get(id=request.user.id)
        project = MappingProject.objects.get(active=True, id=pk, access__username=current_user)

        tasks = MappingTask.objects.filter(project_id=project)

        tasks_per_status =[]
        status_list = tasks.distinct('status').values_list('status__status_title', flat=True)
        for status in status_list:
            tasks_per_status.append({
                'status_title' : status,
                'count_total' : tasks.filter(status__status_title = status).count(),
                'count_user' : tasks.filter(status__status_title = status, user = current_user).count(),
            })

        project_data = {
            'id' : project.id,
            'active' : project.active,
            'title' : project.title,
            'source' : project.source_codesystem.codesystem_title,
            'target' : project.target_codesystem.codesystem_title,
            'tags' : project.tags,

            'open_tasks' : tasks.exclude(status=project.status_complete).exclude(status=project.status_rejected).count(),
            'open_tasks_user' : tasks.filter(user=current_user).exclude(status=project.status_complete).exclude(status=project.status_rejected).count(),
            'tasks_per_status' : tasks_per_status,

            'type' : project.project_type,
            'group' : project.use_mapgroup,
            'priority' : project.use_mappriority,
            'correlation' : project.use_mapcorrelation,
            'rule' : project.use_maprule,
            'advice' : project.use_mapadvice,
            'rulebinding' : project.use_rulebinding,
            'correlation_options' : [
                {'text' : 'Broad to narrow',    'value' : '447559001'},
                {'text' : 'Exact match',        'value' : '447557004'},
                {'text' : 'Narrow to broad',    'value' : '447558009'},
                {'text' : 'Partial overlap',    'value' : '447560006'},
                {'text' : 'Not mappable',       'value' : '447556008'},
                {'text' : 'Not specified',      'value' : '447561005'},
            ],
        }

        return Response(project_data)