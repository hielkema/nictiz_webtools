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
        payload = request.data
        
        if payload.get('tasks'):
            tasks = MappingTask.objects.filter(id__in = payload.get('tasks'))
            
            if payload.get('action').get('changeUser') and payload.get('value').get('changeUser'):
                new_user = User.objects.get(id=payload.get('value').get('changeUser'))
                tasks.update(user = new_user)
                print('Gebruiker wijzigen voor ',tasks.count(),'naar',str(new_user))

            if payload.get('action').get('changeStatus') and payload.get('value').get('changeStatus'):
                new_status = MappingTaskStatus.objects.get(id=payload.get('value').get('changeStatus'))
                tasks.update(status = new_status)
                print('Status wijzigen voor ',tasks.count(),'naar',str(new_status))

            if payload.get('action').get('changeProject') and payload.get('value').get('changeProject'):
                new_project = MappingProject.objects.get(id=payload.get('value').get('changeProject'))
                tasks.update(project_id = new_project)
                print('Project wijzigen voor ',tasks.count(),'naar',str(new_project))

            if payload.get('action').get('changeCategory') and payload.get('value').get('changeCategory'):
                new_category = str(payload.get('value').get('changeCategory'))
                tasks.update(category = new_category)
                print('Categorie wijzigen voor',tasks.count(),'naar', new_category)

            output = payload
        else:
            output = payload

        return Response(
            output
        )

# Tasklist
class MappingTasks(viewsets.ViewSet):
    permission_classes = [Permission_MappingTasks]

    # NOTE - Dit  kan niet meer met de huidige hoeveelheid taken. Moet per project.
    # NOTE - Volgende stap is een loop voor het ophalen van taken in batches.
    # def list(self, request):
    #     # Get data
    #     data = MappingTask.objects.filter().order_by('id')
        
    #     tasks = []
    #     for task in data:
    #         try:
    #             user_id = task.user.id
    #             user_name = task.user.username
    #         except:
    #             user_id = 'Niet toegewezen'
    #             user_name = 'Niet toegewezen'
    #         tasks.append({
    #             'id'    :   task.id,
    #             'user' : {
    #                 'id' : user_id,
    #                 'name' : user_name,
    #             },
    #             'component' : {
    #                 'id'  :   task.source_component.component_id,
    #                 'title' :   task.source_component.component_title,
    #                 'extra' : task.source_component.component_extra_dict,
    #                 'codesystem' : {
    #                     'id' : task.source_component.codesystem_id.id,
    #                     'version' : task.source_component.codesystem_id.codesystem_version,
    #                     'title' : task.source_component.codesystem_id.codesystem_title,
    #                 }
    #             },
    #             'status'  :   {
    #                 'id' : task.status.id,
    #                 'title' : task.status.status_title
    #             },
    #             # Exports used in filtering in task manager - can't be nested
    #             'username' : user_name,
    #             'project' : task.project_id.title,
    #             'codesystem' : task.source_component.codesystem_id.codesystem_title,
    #             'status_title' : task.status.status_title,
    #             'component_actief' : task.source_component.component_extra_dict.get('Actief','?'),
    #         })

        # # Return JSON
        # return Response(tasks)

    def retrieve(self, request, pk=None):
        # Get data
        project = MappingProject.objects.get(id=pk)
        data = MappingTask.objects.filter(project_id=project).order_by('id').select_related(
            'user', 'source_component', 'status', 'project_id', 'source_component__codesystem_id',
        )
    
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
                'component_id'  :   task.source_component.component_id,
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
                    },
                    'extra' : task.source_component.component_extra_dict,
                },
                'component_extra' : task.source_component.component_extra_dict,
                'status'  :   {
                    'id' : task.status.id,
                    'title' : task.status.status_title
                },
                'category' : task.category,
                # Exports used in filtering in task manager - can't be nested
                'username' : user_name,
                'project' : task.project_id.title,
                'codesystem' : task.source_component.codesystem_id.codesystem_title,
                'status_title' : task.status.status_title,
                'component_actief' : task.source_component.component_extra_dict.get('Actief','?'),
            })

        # Return JSON
        return Response(tasks)