from django.shortcuts import render, redirect
from django.views.generic import TemplateView
from django.conf import settings
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from django.template.defaultfilters import linebreaksbr
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import User, Group, Permission
from urllib.request import urlopen, Request
import urllib.parse
from django.contrib.postgres.search import SearchQuery, SearchVector, SearchRank
from django.utils import timezone
from django.db.models import Q
import json
from ..models import *
import time
import environ

from rest_framework import viewsets
from ..tasks import *
from ..serializers import *
from rest_framework import status, views, permissions
from rest_framework.response import Response

class Permission_MappingRcAudit(permissions.BasePermission):
    """
    Global permission check rights to use the RC Audit functionality.
    """
    def has_permission(self, request, view):
        if 'mapping | rc_audit' in request.user.groups.values_list('name', flat=True):
            return True
class Permission_MappingTasks(permissions.BasePermission):
    """
    Global permission check rights to use the taskmanager.
    """
    def has_permission(self, request, view):
        if 'mapping | taskmanager' in request.user.groups.values_list('name', flat=True):
            return True

# Change tasks
class ChangeMappingTasks(viewsets.ViewSet):
    permission_classes = [Permission_MappingTasks]

    def create(self, request):
        return Response({
            'request' : request.data,
        })

# Tasklist
class MappingTasks(viewsets.ViewSet):
    permission_classes = [Permission_MappingTasks]

    def list(self, request):
        # Get data
        data = MappingTask.objects.filter().order_by('id')
        
        tasks = []
        for task in data:
            try:
                user_id = task.user.id
                user_name = task.user.username
            except:
                user_id = 'Niet toegewezen'
                user_name = 'Niet toegewezen'
            tasks.append({
                'id'    :   task.id,
                'user' : {
                    'id' : user_id,
                    'name' : user_name,
                },
                'component' : {
                    'id'  :   task.source_component.component_id,
                    'title' :   task.source_component.component_title,
                    'extra' : task.source_component.component_extra_dict,
                    'codesystem' : {
                        'id' : task.source_component.codesystem_id.id,
                        'version' : task.source_component.codesystem_id.codesystem_version,
                        'title' : task.source_component.codesystem_id.codesystem_title,
                    }
                },
                'status'  :   {
                    'id' : task.status.id,
                    'title' : task.status.status_title
                },
                # Exports used in filtering in task manager - can't be nested
                'username' : user_name,
                'project' : task.project_id.title,
                'codesystem' : task.source_component.codesystem_id.codesystem_title,
                'status_title' : task.status.status_title,
                'component_actief' : task.source_component.component_extra_dict.get('Actief','?'),
            })

        # Return JSON
        return Response(tasks)
    def retrieve(self, request, pk=None):
        # Get data
        project = MappingProject.objects.get(id=pk)
        data = MappingTask.objects.filter(project_id=project).order_by('id')
    
        tasks = []
        for task in data:
            try:
                user_id = task.user.id
                user_name = task.user.username
            except:
                user_id = 'Niet toegewezen'
                user_name = 'Niet toegewezen'
            tasks.append({
                'id'    :   task.id,
                'user' : {
                    'id' : user_id,
                    'name' : user_name,
                },
                'component' : {
                    'id'  :   task.source_component.component_id,
                    'title' :   task.source_component.component_title,
                    'codesystem' : {
                        'id' : task.source_component.codesystem_id.id,
                        'version' : task.source_component.codesystem_id.codesystem_version,
                        'title' : task.source_component.codesystem_id.codesystem_title,
                    }
                },
                'status'  :   {
                    'id' : task.status.id,
                    'title' : task.status.status_title
                },
            })

        # Return JSON
        return Response(tasks)