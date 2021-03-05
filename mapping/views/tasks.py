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

class Permission_CreateMappingTasks(permissions.BasePermission):
    """
    Global permission check rights to use the taskmanager.
    """
    def has_permission(self, request, view):
        if 'mapping | create tasks' in request.user.groups.values_list('name', flat=True):
            return True

class CreateTasks(viewsets.ViewSet):
    permission_classes = [Permission_CreateMappingTasks]

    def create(self, request):
        print(f"[tasks/CreateTasks create] requested by {request.user} - data: {str(request.data)[:500]}")

        # Create new tasks
        current_user = User.objects.get(id=request.user.id)
        payload = request.data
        
        # Check for permissions in chosen project
        project = MappingProject.objects.filter(id=payload.get('projectid'), access__username=current_user)
        # Continue if project exists and user has access
        if project.exists():
            project = project.first()
            


            codesystem = MappingCodesystem.objects.get(id=int(payload.get('codesystem')))

            print("Taken worden aangemaakt in project {} / codesystem {}".format(project, codesystem))


            print("Gaat om project {} / codesystem {}".format(project.title, codesystem.codesystem_title))
            # user = User.objects.get(id=request.user.id) # Taken maken we nu altijd zonder gebruiker

            status = MappingTaskStatus.objects.get(project_id = project, id = payload.get('status'))
   
            projects = MappingProject.objects.all()
            project_list = []
            for projectIter in projects:
                project_list.append((projectIter.id, projectIter.title))

            tasks_list = payload.get('tasks').splitlines()
            handled = []
            for component in tasks_list:
                print("\nAttempting to find component ",component)
                error   = False
                created = False
                present = False
                component_id = None
                component_title = None
                try:
                    component_obj = MappingCodesystemComponent.objects.get(component_id=component, codesystem_id=codesystem)
                    print("Component found: ", component_obj)

                    obj = MappingTask.objects.filter(
                        project_id=project,
                        source_component=component_obj,
                    )
                    if obj.count() > 0:
                        present = True
                        obj = obj.first()
                    else:
                        present = False
                        obj = MappingTask.objects.create(
                            project_id=project, # Wel matchen op project - anders kan het zijn dat je geen taak voor een mapping naar een ander stels kan maken - denk palga & NHG parallel.
                            source_component=component_obj,
                        )
                        # Add data not used for matching
                        # obj.source_component = component_obj.id
                        print(component_obj)
                        obj.source_codesystem = component_obj.codesystem_id
                        obj.target_codesystem = component_obj.codesystem_id # Voor nu gelijk aan bron.
                        # TODO target nog aanpassen naar optie in formulier, om een doel-codesystem af te dwingen.
                        obj.status = status
                        if payload.get('user'):
                            obj.user = User.objects.get(id=payload.get('user'))
                        else:
                            obj.user = User.objects.get(id=request.user.id)

                        # Save
                        obj.save()
                        created = True

                        # Add comment
                        print("Comment: ",payload.get('comments'))
                        if payload.get('comments'):
                            print("Adding comment")
                            user = User.objects.get(id=request.user.id)
                            comment = MappingComment.objects.get_or_create(
                                        comment_title = 'task created',
                                        comment_task = obj,
                                        comment_body = '[Commentaar bij aanmaken taak]\n'+payload.get('comments'),
                                        comment_user = user,
                                    )

                    
                    component_id = component_obj.id
                    component_title = component_obj.component_title
                    handled.append({
                        'taskid'    : obj.id,
                        'user'      : obj.user.username,
                        'status'    : obj.status.status_title,
                        'reqid'     : component,
                        'present'   : present,
                        'created'   : created,
                        'error'     : error,
                        'project'   : project.title,
                        'component_id'      : component_id,
                        'component_title'   : component_title,
                    })
                except Exception as e:
                    print("Component not found, or error: ", e)
                    error = str(e)

                    handled.append({
                        'reqid'     : component,
                        'created'   : False,
                        'error'     : error,
                    })

            return Response({
                'response' : 'OK: Toegang => '+str(project),
                'request' : payload,
                'result' : handled,
            })
        else:
            return Response('Error: Geen toegang')

class Tasklist(viewsets.ViewSet):
    permission_classes = [Permission_MappingProject_Access]

    def retrieve(self, request, pk=None):
        print(f"[tasks/Tasklist retrieve] requested by {request.user} - {pk}")

        # List all tasks
        # TODO filter on which projects the user has access to
         # Get data
        current_user = User.objects.get(id=request.user.id)
        project = MappingProject.objects.get(id=pk, access__username=current_user)
        data = MappingTask.objects.select_related('status','user','source_component','source_component__codesystem_id').filter(project_id=project).order_by('id')

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
                'category' : task.category,
            })

        sort_alphab = [3,13]
        if project.id in sort_alphab:
            task_list = natsort.natsorted(task_list, key=lambda k: k['component']['title'])
        else:
            task_list = natsort.natsorted(task_list, key=lambda k: k['component']['id'])


        return Response(task_list)

class TaskDetails(viewsets.ViewSet):
    permission_classes = [Permission_MappingProject_Access]

    def retrieve(self, request, pk=None):
        print(f"[tasks/TaskDetails retrieve] requested by {request.user} - {pk}")

        # Get data
        task = MappingTask.objects.select_related('project_id','user','source_component','source_component__codesystem_id','status').get(id=pk)
        current_user = User.objects.get(id=request.user.id)
        if MappingProject.objects.get(id=task.project_id.id, access__username=current_user):

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
                    'pk' : task.source_component.id,
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

            if task.project_id.project_type == '4':
                try:
                    obj = MappingEclPartExclusion.objects.get(task = task)
                    component_list = MappingCodesystemComponent.objects.filter(codesystem_id = obj.task.source_component.codesystem_id, component_id__in=obj.components)

                    component_list_output = []
                    for component in component_list.order_by('component_id'):
                        component_list_output.append(f"{component.codesystem_id.codesystem_title} {component.component_id} - {component.component_title}")

                    output.update({
                        'exclusions' : {
                            'string' : "\n".join(obj.components),
                            'recognized' : '\n'.join(component_list_output),
                        }
                    })
                except:
                    output.update({
                        'exclusions' : {
                            'string' : ''
                        }
                    })

                

            return Response(output)

class RelatedTasks(viewsets.ViewSet):
    """ Takes component ID as PK, returns all tasks with the same component as source_component """

    permission_classes = [Permission_MappingProject_Access]

    def retrieve(self, request, pk=None):
        print(f"[tasks/RelatedTasks retrieve] requested by {request.user} - {pk}")

        # Get data
        task = MappingTask.objects.get(id=int(pk))
        component = MappingCodesystemComponent.objects.get(id = task.source_component.id)

        # Fetch mapping rules that use the current source as source
        rules = MappingRule.objects.filter(
            target_component = component
        )
        # Create a list of component ids from the targets of these rules
        target_list = list(rules.distinct().values_list('source_component__id', flat=True))
        # print(target_list)


        # Collect relevant tasks
        tasks = MappingTask.objects.filter(
            source_component = component
        ) | MappingTask.objects.filter(
            source_component__id__in = target_list
        )
        # print(tasks.values_list('id'))

        # Loop tasks and comments
        output = []
        for task in tasks:

            comments = MappingComment.objects.filter(
                comment_task = task,
            ).select_related()

            comment_list = []
            for comment in comments:
                comment_list.append({
                    'title': comment.comment_title,
                    'body' : comment.comment_body,
                    'user' : comment.comment_user.username,
                    'created' : comment.comment_created.strftime('%B %d %Y'),
                })

            output.append({
                'id' : task.id,
                'source_component' : {
                    'component_id' : task.source_component.component_id,
                    'component_title' : task.source_component.component_title,
                },
                'project' : {
                    'id' : task.project_id.id,
                    'title' : task.project_id.title,
                },
                'status' : {
                    'title' : task.status.status_title,
                },
                'user' : {
                    'username' : task.user.username,
                },
                'comments' : comment_list,
            })

        return Response(output)

class EventsAndComments(viewsets.ViewSet):
    permission_classes = [Permission_MappingProject_Access]

    def retrieve(self, request, pk=None):
        print(f"[tasks/EventsAndComments retrieve] requested by {request.user} - {pk}")

        # List all events
        # TODO filter on which projects the user has access to
         # Get data
    
        events_list = []
        current_user = User.objects.get(id=request.user.id)
        task = MappingTask.objects.get(id=pk)
        if MappingProject.objects.get(id=task.project_id.id, access__username=current_user):
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
                created = item.event_time.strftime('%B %d %Y')
                try:
                    snapshot = json.loads(item.new_data)
                except:
                    snapshot = "FALLBACK: "+item.new_data

                try:
                    # Make it break if user not set
                    item.action_user.username
                    action_user = item.action_user
                except:
                    action_user = item.user_source
                events_list.append({
                    'id' : item.id,
                    'text' : action_user.username + ': ' + item.old + ' -> ' + item.new,
                    'data' : snapshot,
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