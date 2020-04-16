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

class Tasklist(viewsets.ViewSet):
    permission_classes = [Permission_MappingProject_Access]

    def retrieve(self, request, pk=None):
        # List all projects
        # TODO filter on which projects the user has access to
         # Get data
        project = MappingProject.objects.get(id=pk)
        data = MappingTask.objects.filter(project_id=project).order_by('id')
    
        task_list = []
        for task in data:
            try:
                user_id = task.user.id
                user_name = task.user.username
            except:
                user_id = 'Niet toegewezen'
                user_name = 'Niet toegewezen'
            task_list.append({
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

        return Response(task_list)

class TaskDetails(viewsets.ViewSet):
    permission_classes = [Permission_MappingProject_Access]

    def retrieve(self, request, pk=None):
        # List all projects
        # TODO filter on which projects the user has access to
         # Get data
        task = MappingTask.objects.get(id=pk)

        try:
            user_id = task.user.id
            user_name = task.user.username
        except:
            user_id = 'Niet toegewezen'
            user_name = 'Niet toegewezen'
        output = {
            'id'    :   task.id,
            'user' : {
                'id' : user_id,
                'name' : user_name,
            },
            'project' : {
                'id' : task.project_id.id,
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
            'status'  :   {
                'id' : task.status.id,
                'title' : task.status.status_title,
                'description' : task.status.status_description,
            },
        }

        return Response(output)

class EventsAndComments(viewsets.ViewSet):
    permission_classes = [Permission_MappingProject_Access]

    def retrieve(self, request, pk=None):
        # List all events
        # TODO filter on which projects the user has access to
         # Get data
    
        events_list = []
        comments = MappingComment.objects.filter(comment_task=pk).order_by('-comment_created') 
        for item in comments:
            created = item.comment_created.strftime('%B %d %Y')
            events_list.append({
                'id' : item.id,
                'text' : item.comment_body,
                'type' : 'comment',
                'user' : {
                    'id' : item.comment_user.id,
                    'name' : item.comment_user.username,
                },
                'action_user' : {
                    'id' : item.comment_user.id,
                    'name' : item.comment_user.username,
                },
                'created' : created,
                'timestamp' : item.comment_created,
            })
        events = MappingEventLog.objects.filter(task_id=pk).order_by('-event_time') 
        for item in events:
            data =  json.dumps(item.new_data, sort_keys=True, indent=4)
            created = item.event_time.strftime('%B %d %Y')
            
            try:
                # Make it break if user not set
                item.action_user.username
                action_user = item.action_user
            except:
                action_user = item.user_source
            events_list.append({
                'id' : item.id,
                'text' : action_user.username + ': ' + item.old + ' -> ' + item.new,
                'data' : data,
                'action_user' : {
                    'id' : action_user.id,
                    'name' : action_user.username,
                },
                'type' : item.action,
                'user' : {
                    'id' : item.user_source.id,
                    'name' : item.user_source.username,
                },
                'created' : created,
                'timestamp' : item.event_time,
            })
                 
        # Sort event_list on date
        events_list.sort(key=lambda item:item['timestamp'], reverse=True)
        

        return Response(events_list)