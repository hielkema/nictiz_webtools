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
from pandas import read_excel
import sys, os
import pprint
import environ
import time
import random
import json
import urllib.request
# Get latest snowstorm client once on startup. Set master or develop
branch = "develop"
url = 'https://raw.githubusercontent.com/mertenssander/python_snowstorm_client/' + \
    branch+'/snowstorm_client.py'
# urllib.request.urlretrieve(url, 'snowstorm_client.py')
from snowstorm_client import Snowstorm
from ..tasks import *
from ..forms import *
from ..models import *

class api_EventList_get(UserPassesTestMixin,TemplateView):
    '''
    Returns all comments and events for the current task in a list
    Only allowed with change task status rights.
    '''
    def handle_no_permission(self):
        return redirect('login')
    def test_func(self):
        # return self.request.user.has_perm('Build_Tree.make_taskRecord')
        return self.request.user.groups.filter(name='mapping | view tasks').exists()

    def get(self, request, **kwargs):
        # Create dictionary for events (ie. should look for all actions and comments, combine them into a dict)
        events_list = []
        comments = MappingComment.objects.filter(comment_task=kwargs.get('task')).order_by('-comment_created') 
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
        events = MappingEventLog.objects.filter(task_id=kwargs.get('task')).order_by('-event_time') 
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
        context = {
            'eventList': events_list,
        }
        # Return JSON
        return JsonResponse(context,safe=False)

class api_StatusChange_post(UserPassesTestMixin,TemplateView):
    '''
    Receives requests to change status of a task
    Only allowed with change task status rights.
    '''
    def handle_no_permission(self):
        return redirect('login')
    def test_func(self):
        # return self.request.user.has_perm('Build_Tree.make_taskRecord')
        return self.request.user.groups.filter(name='mapping | change task status').exists()

    def post(self, request, **kwargs):
        try:
            payload = request.POST
            # print(payload.get('task'), payload.get('newTaskStatus'))
            task = MappingTask.objects.get(id=payload.get('task'))
            current_user = User.objects.get(id=request.user.id)
            new_status = MappingTaskStatus.objects.get(id=payload.get('newStatus'))
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

            context = {
                'result': "success",
                'new' : str(task),
            }
            # Return JSON
            return JsonResponse(context,safe=False)
        except Exception as e:
            print(type(e), e, kwargs)

class api_PostComment_post(UserPassesTestMixin,TemplateView):
    '''
    Receives requests to place a new comment
    Only allowed with place comments rights.
    '''
    def handle_no_permission(self):
        return redirect('login')
    def test_func(self):
        # return self.request.user.has_perm('Build_Tree.make_taskRecord')
        return self.request.user.groups.filter(name='mapping | place comments').exists()

    def post(self, request, **kwargs):
        try:
            payload = request.POST
            # print(payload.get('task'), payload.get('comment'))
            task = MappingTask.objects.get(id=payload.get('task'))
            user = User.objects.get(id=request.user.id)

            comment = MappingComment.objects.create(
                comment_title   = '',
                comment_task    = task,
                comment_body    = payload.get('comment'),
                comment_user    = user,
            )
            comment.save()

            context = {
                'result': "success",
            }
            # Return JSON
            return JsonResponse(context,safe=False)
        except Exception as e:
            print(type(e), e, kwargs)

class api_DelComment_post(UserPassesTestMixin,TemplateView):
    '''
    Receives requests to place a new comment
    Only allowed with place comments rights.
    '''
    def handle_no_permission(self):
        return redirect('login')
    def test_func(self):
        # return self.request.user.has_perm('Build_Tree.make_taskRecord')
        return self.request.user.groups.filter(name='mapping | place comments').exists()

    def post(self, request, **kwargs):
        try:
            payload = request.POST
            # print(payload.get('task'), payload.get('comment'))
            current_user = User.objects.get(id=request.user.id)
            comment = MappingComment.objects.get(id=payload.get('comment'), comment_user=current_user)
            comment.delete()

            context = {
                'result': "success",
            }
            # Return JSON
            return JsonResponse(context,safe=False)
        except Exception as e:
            print(type(e), e, kwargs)

class api_TaskList_get(UserPassesTestMixin,TemplateView):
    '''
    Delivers task lists
    Only allowed with view tasks rights.
    '''
    def handle_no_permission(self):
        return redirect('login')
    def test_func(self):
        # return self.request.user.has_perm('Build_Tree.make_taskRecord')
        return self.request.user.groups.filter(name='mapping | view tasks').exists()

    def get(self, request, **kwargs):
        # Get data
        project = MappingProject.objects.get(id=kwargs.get('project_id'))
        data = MappingTask.objects.filter(project_id=project).order_by('id')
    
        tasks = []
        for task in data:
            tasks.append({
                'id'    :   task.id,
                'user' : {
                    'id' : task.user.id,
                    'name' : task.user.username,
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
        
        context = {
            'taskList': tasks,
        }
        # Return JSON
        return JsonResponse(context,safe=False)

class api_Permissions_get(UserPassesTestMixin,TemplateView):
    '''
    Delivers a list of permissions for the current user
    Only allowed with access rights.
    '''
    def handle_no_permission(self):
        return redirect('login')
    def test_func(self):
        # return self.request.user.has_perm('Build_Tree.make_taskRecord')
        return self.request.user.groups.filter(name='mapping | access').exists()

    def get(self, request, **kwargs):
        # Get data
        # Lookup edit rights for mapping      
        db_permissions = request.user.groups.values_list('name', flat=True)
        permissions = []
        for perm in db_permissions:
            permissions.append(perm)
        
        # Return JSON
        return JsonResponse(permissions,safe=False)

class api_User_get(UserPassesTestMixin,TemplateView):
    '''
    Generates a list of registered users
    Only allowed with access rights.
    '''
    def handle_no_permission(self):
        return redirect('login')
    def test_func(self):
        # return self.request.user.has_perm('Build_Tree.make_taskRecord')
        return self.request.user.groups.filter(name='mapping | access').exists()

    def get(self, request, **kwargs):
        # Get data
        # Lookup edit rights for mapping      
        users = User.objects.filter()
        user_list = []
        for user in users:
            user_list.append({
                'id' : user.id,
                'username' : user.username,
            })
        
        # Return JSON
        return JsonResponse(user_list,safe=False)

class api_Mapping_post(UserPassesTestMixin,TemplateView):
    '''
    Receives requests to change the current mapping
    Only allowed with edit mapping rights.
    '''
    def handle_no_permission(self):
        return redirect('login')
    def test_func(self):
        # return self.request.user.has_perm('Build_Tree.make_taskRecord')
        return self.request.user.groups.filter(name='mapping | edit mapping').exists()
    def post(self, request, **kwargs):

        payload = request.POST
        task = MappingTask.objects.get(id=payload.get('task'))

        maprules = json.loads(payload.get('mapping'))
        for value in maprules:
            # print(json.dumps(value, indent=4, sort_keys=True))
            
            try:
                if task.project_id.project_type == "1": # One to many
                    try:
                        target_component = MappingCodesystemComponent.objects.get(id=value['target']['new']['id'])
                    except:
                        target_component = MappingCodesystemComponent.objects.get(id=value['target']['id'])
                    source_component = MappingCodesystemComponent.objects.get(id=task.source_component.id)
                elif task.project_id.project_type == "2": # Many to one
                    try:
                        source_component = MappingCodesystemComponent.objects.get(id=value['target']['new']['id'])
                    except:
                        source_component = MappingCodesystemComponent.objects.get(id=value['target']['id'])
                    target_component = MappingCodesystemComponent.objects.get(id=task.source_component.id)
                elif task.project_id.project_type == "4": # ECL to one
                    try:
                        source_component = MappingCodesystemComponent.objects.get(id=value['target']['new']['id'])
                    except:
                        source_component = MappingCodesystemComponent.objects.get(id=value['target']['id'])
                    target_component = MappingCodesystemComponent.objects.get(id=task.source_component.id)
                else:
                    print("No support for this project type in api_Mapping_post POST method [3]")
            except Exception as e:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                error = 'Exc type: {} \n TB: {}'.format(exc_type, exc_tb.tb_lineno)
                print(error)
            
            if value.get('delete') == True:
                print('Get ready to delete')
                mapping_rule = MappingRule.objects.get(id=value.get('id'))
                mapping_rule.delete()
            elif value.get('id') != 'extra':
                print("Aanpassen mapping")
                mapping_rule = MappingRule.objects.get(id=value.get('id'))
                mapping_rule.source_component   = source_component
                mapping_rule.target_component   = target_component
                mapping_rule.mapgroup           = value.get('group')
                mapping_rule.mappriority        = value.get('priority')
                mapping_rule.mapcorrelation     = value.get('correlation')
                mapping_rule.mapadvice          = value.get('advice')
                mapping_rule.maprule            = value.get('rule')
                mapping_rule.save()
            elif value.get('id') == 'extra' and  value.get('target').get('new'):
                print("Nieuwe mapping toevoegen")
                mapping_rule = MappingRule.objects.create(
                    project_id         = task.project_id,
                    source_component   = source_component,
                    target_component   = target_component,
                    mapgroup           = value.get('group'),
                    mappriority        = value.get('priority'),
                    mapcorrelation     = value.get('correlation'),
                    mapadvice          = value.get('advice'),
                    maprule            = value.get('rule'),
                )
                mapping_rule.save()

        context = {
            'result': "success",
        }
        # Start audit on current item
        audit_async.delay('multiple_mapping', task.project_id.id, task.id)
        # Return JSON
        return JsonResponse(context,safe=False)

class api_UserChange_post(UserPassesTestMixin,TemplateView):
    '''
    Receives requests to change the task's current user
    Only allowed with change task status rights.
    '''
    def handle_no_permission(self):
        return redirect('login')
    def test_func(self):
        # return self.request.user.has_perm('Build_Tree.make_taskRecord')
        return self.request.user.groups.filter(name='mapping | change task status').exists()

    def post(self, request, **kwargs):
        try:
            payload = request.POST
            # print(payload.get('task'), payload.get('newUser'))
            task = MappingTask.objects.get(id=payload.get('task'))
            newuser = User.objects.get(id=payload.get('newUser'))
            source_user = User.objects.get(id=task.user.id)
            target_user = User.objects.get(id=payload.get('newUser'))
            current_user = User.objects.get(id=request.user.id)
            task.user = newuser
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
            # print(str(mappingrules))
            event = MappingEventLog.objects.create(
                    task=task,
                    action='user_change',
                    action_user=current_user,
                    action_description='Gebruiker:',
                    old_data='',
                    new_data=str(mappingrules),
                    old=str(source_user),
                    new=str(target_user),
                    user_source=source_user,
                    user_target=target_user,
                )
            event.save()

            context = {
                'result': "success",
                'new' : str(task),
            }
            # Return JSON
            return JsonResponse(context,safe=False)
        except Exception as e:
            print(type(e), e, kwargs)

class api_TaskId_get(UserPassesTestMixin,TemplateView):
    '''
    Generates information about a single task
    Only allowed with view tasks rights.
    '''
    def handle_no_permission(self):
        return redirect('login')
    def test_func(self):
        # return self.request.user.has_perm('Build_Tree.make_taskRecord')
        return self.request.user.groups.filter(name='mapping | view tasks').exists()

    def get(self, request, **kwargs):
        # Get task data by ID
        try:
            task = MappingTask.objects.get(id=kwargs.get('task'))
            project = MappingProject.objects.get(id=task.project_id.id)
            statuses = MappingTaskStatus.objects.filter(project_id=project).order_by('status_id')
            # print(statuses)
            task = ({
                    'id'    :   task.id,
                    'component' : {
                        'title' :   task.source_component.component_title,
                        'codesystem' : {
                            'id' : task.source_component.codesystem_id.id,
                            'title' : task.source_component.codesystem_id.codesystem_title,
                            'version' : task.source_component.codesystem_id.codesystem_version,
                        },
                        'extra_1' : {
                            'label' : task.source_component.codesystem_id.codesystem_extra_1,
                            'value' : task.source_component.component_extra_1,
                        },
                        'extra_2' : {
                            'label' : task.source_component.codesystem_id.codesystem_extra_2,
                            'value' : task.source_component.component_extra_2,
                        },
                        'extra_3' : {
                            'label' : task.source_component.codesystem_id.codesystem_extra_3,
                            'value' : task.source_component.component_extra_3,
                        },
                        'extra_4' : {
                            'label' : task.source_component.codesystem_id.codesystem_extra_4,
                            'value' : task.source_component.component_extra_4,
                        },
                        'extra_5' : {
                            'label' : task.source_component.codesystem_id.codesystem_extra_5,
                            'value' : task.source_component.component_extra_5,
                        },
                        'extra_6' : {
                            'label' : task.source_component.codesystem_id.codesystem_extra_6,
                            'value' : task.source_component.component_extra_6,
                        },
                        'extra_7' : {
                            'label' : task.source_component.codesystem_id.codesystem_extra_7,
                            'value' : task.source_component.component_extra_7,
                        }
                    },
                    'status' : {
                        'id' : task.status.id,
                        'status_id' : task.status.status_id,
                        'title' : task.status.status_title,
                    },
                    'user' : {
                        'id' : task.user.id,
                        'name' : task.user.username,
                    },
                })
            status_list = []
            for status in statuses:
                status_list.append({
                    'id' : status.id,
                    'status_id' : status.status_id,
                    'title' : status.status_title,
                })
        # If task does not exist, return empty
        except Exception as e:
            print(type(e), e)
            print("Kwargs: ",kwargs)
            task = []
        
        context = {
            'task': task,
            'status_list': status_list,
        }
        # Return JSON
        return JsonResponse(context,safe=False)

class api_Mapping_get(UserPassesTestMixin,TemplateView):
    '''
    Delivers the current mapping for a task
    Only allowed with view tasks rights.
    '''
    def handle_no_permission(self):
        return redirect('login')
    def test_func(self):
        # return self.request.user.has_perm('Build_Tree.make_taskRecord')
        return self.request.user.groups.filter(name='mapping | view tasks').exists()

    def get(self, request, **kwargs):
        # Get data
        # Lookup mappings for current task     
        payload = request.POST

        task = MappingTask.objects.get(id=kwargs.get('task'))
        mappings = MappingRule.objects.filter(project_id=task.project_id, source_component=task.source_component).order_by('mappriority')
        mapping_list = []
        for mapping in mappings:
            mapcorrelation = mapping.mapcorrelation
            # if mapcorrelation == "447559001": mapcorrelation = "Broad to narrow"
            # if mapcorrelation == "447557004": mapcorrelation = "Exact match"
            # if mapcorrelation == "447558009": mapcorrelation = "Narrow to broad"
            # if mapcorrelation == "447560006": mapcorrelation = "Partial overlap"
            # if mapcorrelation == "447556008": mapcorrelation = "Not mappable"
            # if mapcorrelation == "447561005": mapcorrelation = "Not specified"
            mapping_list.append({
                'id' : mapping.id,
                'source' : {
                    'id': mapping.source_component.id,
                    'component_id': mapping.source_component.component_id,
                    'component_title': mapping.source_component.component_title,
                },
                'target' : {
                    'id': mapping.target_component.id,
                    'component_id': mapping.target_component.component_id,
                    'component_title': mapping.target_component.component_title,
                    'codesystem': {
                        'title' : mapping.target_component.codesystem_id.codesystem_title,
                        'version' : mapping.target_component.codesystem_id.codesystem_version,
                        'id' : mapping.target_component.codesystem_id.id,
                    }
                },
                'group' : mapping.mapgroup,
                'priority' : mapping.mappriority,
                'correlation' : mapping.mapcorrelation,
                'advice' : mapping.mapadvice,
                'rule' : mapping.maprule,
                'delete' : False,
            })

        # Append extra empty mapping
        mapping_list.append({
                'id' : 'extra',
                'source' : {
                    'id': task.source_component.id,
                    'component_id': task.source_component.component_id,
                    'component_title': task.source_component.component_title,
                },
                'target' : {
                    'id': None,
                    'component_id': None,
                    'component_title': None,
                    'codesystem': {
                        'title' : None,
                        'version' : None,
                        'id' : None,
                    }
                },
                'group' : None,
                'priority' : None,
                'correlation' : '447557004',
                'advice' : None,
                'rule' : None,
                'delete' : False,
            })
        
        project_data = {
            'type' : task.project_id.project_type,
            'group' : task.project_id.use_mapgroup,
            'priority' : task.project_id.use_mappriority,
            'correlation' : task.project_id.use_mapcorrelation,
            'rule' : task.project_id.use_maprule,
            'correlation_options' : {
                '447559001' : 'Broad to narrow',
                '447557004' : 'Exact match',
                '447558009' : 'Narrow to broad',
                '447560006' : 'Partial overlap',
                '447556008' : 'Not mappable',
                '447561005' : 'Not specified',
            }
        }

        context = {
            'mappings' : mapping_list,
            'project' : project_data,
        }
        # Return JSON
        return JsonResponse(context,safe=False)

class vue_MappingIndex(UserPassesTestMixin,TemplateView):
    '''
    View for choosing a project to work on.
    Only accessible with view tasks rights.
    '''
    def handle_no_permission(self):
        return redirect('login')
    def test_func(self):
        # return self.request.user.has_perm('Build_Tree.make_taskRecord')
        return self.request.user.groups.filter(name='mapping | access').exists()

    def get(self, request, **kwargs):
        # TODO - Check if active projects exist, otherwise -> error.
        project_list = MappingProject.objects.filter(active=True)
        return render(request, 'mapping/v2/index.html', {
            'page_title': 'Mapping project',
            'project_list': project_list,
        })

class vue_ProjectIndex(UserPassesTestMixin,TemplateView):
    '''
    Extremely convoluted view to allow a single-page overview of the current project.
    Also shows progress through time if the AjaxProgressRecordPageView is called at regular intervals.
    Only accessible with view tasks permissions.
    '''
    def handle_no_permission(self):
        return redirect('login')
    def test_func(self):
        # return self.request.user.has_perm('Build_Tree.make_taskRecord')
        return self.request.user.groups.filter(name='mapping | access').exists()

    def get(self, request, **kwargs):
        # TODO - Check if project and task exist, otherwise -> redirect to project or homepage.

        # Taken per status
        try:
            current_user = User.objects.get(id=request.user.id)
            project_list = MappingProject.objects.filter(active=True)
            current_project = MappingProject.objects.get(id=kwargs.get('project'), active=True)
            tasks = MappingTask.objects.filter(user=current_user, project_id_id=current_project.id).exclude(status=current_project.status_complete).order_by('id')
            
            status_list = MappingTaskStatus.objects.filter(project_id=kwargs.get('project')).order_by('status_id')#.exclude(id=current_project.status_complete.id)
            tasks_per_status_labels = []
            tasks_per_status_values = []
            user_list = User.objects.filter()
            tasks_per_user_labels = []
            tasks_per_user_values = []
            for user in user_list:
                num_tasks = MappingTask.objects.filter(project_id_id=current_project.id, user=user).exclude(status=current_project.status_complete).count()
                if num_tasks > 0:
                    num_tasks = MappingTask.objects.filter(project_id_id=current_project.id, user=user).exclude(status=current_project.status_complete).count()
                    tasks_per_user_labels.append(user.username)
                    tasks_per_user_values.append(num_tasks)
            for status in status_list:            
                num_tasks = MappingTask.objects.filter(project_id_id=current_project.id, status_id=status).count()
                tasks_per_status_labels.append(status.status_title)
                tasks_per_status_values.append(num_tasks)
        except:
            tasks_per_status_labels = []
            tasks_per_status_values = []
            tasks_per_user_labels = []
            tasks_per_user_values = []
            print("Error in 'taken per status'")
        
        # Taken per status huidige gebruiker
        try:
            tasks_current_user_status_labels = []
            tasks_current_user_status_values = []

            for status in status_list:
                tasks_current_user_status_labels.append(status.status_title)
            current_user = User.objects.get(id=request.user.id)
            num_tasks = MappingTask.objects.filter(project_id_id=current_project.id, user=current_user).count()
            if num_tasks > 0:
                person_label = []
                person_value = []
                for status in status_list:
                    num_tasks = MappingTask.objects.filter(project_id_id=current_project.id, status_id=status, user=current_user).count()
                    person_value.append(num_tasks)
                
                r = 255 * random.random()
                g = 255 * random.random()
                b = 255 * random.random()
                background_color = 'rgba({}, {}, {}, 0.2)'.format(r,g,b)
                border_color = 'rgba({}, {}, {}, 0.5)'.format(r,g,b)
                dataset = {
                    'label' : user.username,
                    'backgroundColor' : background_color,
                    'borderColor' : background_color,
                    'hoverBackgroundColor' : border_color,
                    'data': person_value
                }
                tasks_current_user_status_values.append(dataset)
                tasks_current_user_status_values = person_value
                
        except:
            tasks_current_user_status_labels = []
            tasks_current_user_status_values = []
            print("Error in 'taken per status'")


        # Taken per status per gebruiker
        try:
            tasks_user_status_labels = []
            tasks_user_status_values = []

            for status in status_list:
                tasks_user_status_labels.append(status.status_title)
            for user in user_list:
                num_tasks = MappingTask.objects.filter(project_id_id=current_project.id, user=user).count()
                if num_tasks > 0:
                    person_label = []
                    person_value = []
                    for status in status_list:
                        num_tasks = MappingTask.objects.filter(project_id_id=current_project.id, status_id=status, user=user).count()
                        person_value.append(num_tasks)
                    
                    r = 255 * random.random()
                    g = 255 * random.random()
                    b = 255 * random.random()
                    background_color = 'rgba({}, {}, {}, 0.2)'.format(r,g,b)
                    border_color = 'rgba({}, {}, {}, 0.5)'.format(r,g,b)
                    dataset = {
                        'label' : user.username,
                        'backgroundColor' : background_color,
                        'borderColor' : background_color,
                        'hoverBackgroundColor' : border_color,
                        'data': person_value
                    }
                    tasks_user_status_values.append(dataset)
        except:
            tasks_user_status_labels = []
            tasks_user_status_values = []
            print("Error in 'taken per status'")

        # Statusverdeling door de tijd
        history = MappingProgressRecord.objects.filter(project=current_project, name="TasksPerStatus")
        time_labels = {}
        time_time = []
        for point in history:
            values = json.loads(point.values)
            for (index, value) in enumerate(values):
                # print(value['status'], value['num_tasks'])
                if value['status'] not in time_labels:
                    time_labels.update({value['status'] : []})
                time_labels[value['status']].append(value['num_tasks'])
            time_time.append(point.time.strftime("%Y-%m-%d %H:%M:%S"))
        time_dataset = []
        for index, value in time_labels.items():
            r = 255 * random.random()
            g = 255 * random.random()
            b = 255 * random.random()
            background_color = 'rgba({}, {}, {}, 0.2)'.format(r,g,b)
            border_color = 'rgba({}, {}, {}, 0.5)'.format(r,g,b)

            time_dataset.append({
                'label' : index,
                'data' : value,
                'fill' : 'false',
                'backgroundColor' : background_color,
                'borderColor' : background_color,
                'hoverBackgroundColor' : border_color,
                
            })

        print("current_user", current_user)
        print("project_list", project_list)
        print("current_project", current_project)
        print("TASKS", tasks)

        current_user = User.objects.get(id=request.user.id)
        project_list = MappingProject.objects.filter(active=True)
        current_project = MappingProject.objects.get(id=kwargs.get('project'), active=True)
        tasks = MappingTask.objects.filter(user=current_user, project_id_id=current_project.id).exclude(status=current_project.status_complete).order_by('id')
        total_num_tasks = len(tasks)
        if tasks.count() == 0:    
            tasks = MappingTask.objects.filter(project_id_id=current_project.id).exclude(status=current_project.status_complete).order_by('id')
            total_num_tasks = 0
                
        # print(task_list) # DEBUG
        
        # Lookup edit rights for mapping      
        db_permissions = request.user.groups.values_list('name', flat=True)
        permissions = []
        for perm in db_permissions:
            permissions.append(perm)
        print("Permissions: ", current_user.username, " -> ",permissions)


        # Render page
        return render(request, 'mapping/v2/project_index.html', {
            'page_title': 'Mapping project',
            'current_project' :  current_project,
            'project_list': project_list,
            'first_task': tasks[0],
            'tasks_total' : total_num_tasks,
            'tasks_per_status_values' : tasks_per_status_values,
            'tasks_per_status_labels' : tasks_per_status_labels,
            'tasks_per_user_values' : tasks_per_user_values,
            'tasks_per_user_labels' : tasks_per_user_labels,
            'tasks_user_status_values' : tasks_user_status_values,
            'tasks_user_status_labels' : tasks_user_status_labels,
            'tasks_current_user_status_labels' : tasks_current_user_status_labels,
            'tasks_current_user_status_values' : tasks_current_user_status_values,
            'time_dataset' : time_dataset,
            'time_time' : time_time,
            'permissions' : permissions,
        })

        # return HttpResponseRedirect(reverse('homepage:index'))

class vue_TaskEditor(UserPassesTestMixin,TemplateView):
    '''
    View for choosing a project to work on.
    Only accessible with view tasks rights.
    '''
    def handle_no_permission(self):
        return redirect('login')
    def test_func(self):
        # return self.request.user.has_perm('Build_Tree.make_taskRecord')
        return self.request.user.groups.filter(name='mapping | view tasks').exists()

    def get(self, request, **kwargs):
        # TODO - Check if active projects exist, otherwise -> error.
        project = MappingProject.objects.get(id=kwargs.get('project'))
        user = User.objects.get(id=request.user.id)
        try:
            task = MappingTask.objects.get(id=kwargs.get('task'))
            task = task.id
        except Exception as e:
            print(type(e),e)
            print("Kwargs: ",kwargs)
            task = 0
        return render(request, 'mapping/v2/1-n/task_editor.html', {
            'page_title': 'Mapping project',
            'current_project': project,
            'current_task' : task,
        })

class api_GeneralData_get(UserPassesTestMixin,TemplateView):
    '''
    Class used for delivering general data required for rendering the page
    Only accessible with view tasks rights.
    '''
    def handle_no_permission(self):
        return redirect('login')
    def test_func(self):
        # User has no reason being here if he has no mapping rights
        return self.request.user.groups.filter(name='mapping | view tasks').exists()
    
    def get(self, request, **kwargs):
        # TODO - Check if project and task exist, otherwise -> redirect to project or homepage.
        
        user = User.objects.get(id=request.user.id)

        # Return Json response
        return JsonResponse({'current_user': {
            'id' : user.id,
            'name' : user.username,
        }})

class api_TargetSearch_get(UserPassesTestMixin,TemplateView):
    '''
    Class used for delivering search results when looking for a component to map to.
    Only accessible with edit mapping rights.
    '''
    def handle_no_permission(self):
        return redirect('login')
    def test_func(self):
        # User has no reason being here if he has no mapping rights
        return self.request.user.groups.filter(name='mapping | edit mapping').exists()
    
    def get(self, request, **kwargs):
        # TODO - Check if project and task exist, otherwise -> redirect to project or homepage.
        search_query = str(request.GET.get('term'))
        print(search_query)

        # Prepare results for vue-select request
        items =[]

        # Start with the best matches: single word postgres match
        snomedComponents = MappingCodesystemComponent.objects.filter(
            Q(component_id__icontains=search_query) |
            Q(component_title__icontains=search_query)
        )
        for component in snomedComponents:
            items.append({
                'id': component.id,
                'component_id': component.component_id,
                'component_title': component.component_title,
                'codesystem': {
                    'title' : component.codesystem_id.codesystem_title,
                    'version' : component.codesystem_id.codesystem_version,
                    'id' : component.codesystem_id.id,
                }
            })
        # In addition, full text search if needed
        if len(items) == 0:
            snomedComponents = MappingCodesystemComponent.objects.annotate(search=SearchVector('component_title','component_id',),).filter(search=search_query)        
            for component in snomedComponents:
                items.append({
                    'target' : {
                        'id': component.id,
                        'component_id': component.component_id,
                        'component_title': component.component_title,
                        'codesystem': {
                            'title' : component.codesystem_id.codesystem_title,
                            'version' : component.codesystem_id.codesystem_version,
                            'id' : component.codesystem_id.id,
                        }
                    },
                })


        # Return Json response
        return JsonResponse({'items':items[:100]})

class api_GetAudit_get(UserPassesTestMixin,TemplateView):
    '''
    View for requesting audit hits for current task
    '''
    def handle_no_permission(self):
        return redirect('login')
    def test_func(self):
        # return self.request.user.has_perm('Build_Tree.make_taskRecord')
        return self.request.user.groups.filter(name='mapping | view tasks').exists()

    def get(self, request, **kwargs):
        try:
            task = MappingTask.objects.get(id=kwargs.get('task'))
            audits = MappingTaskAudit.objects.filter(task=task)
            whitelist = audits.filter(ignore=True)
            active = audits.filter(ignore=False)
            # whitelist_num = whitelist.count()

            audit_list = []
            whitelist = []
            for audit in active:
                created = audit.first_hit_time.strftime('%B %d %Y')
                audit_list.append({
                    'id' : audit.id,
                    'type' : audit.audit_type,
                    'reason' : audit.hit_reason,
                    'comment' : audit.comment,
                    'timestamp' : audit.first_hit_time,
                    'created' : created,
                })
            for audit in whitelist:
                created = audit.first_hit_time.strftime('%B %d %Y')
                whitelist.append({
                    'id' : audit.id,
                    'type' : audit.audit_type,
                    'reason' : audit.hit_reason,
                    'comment' : audit.comment,
                    'timestamp' : audit.first_hit_time,
                    'created' : created,
                })
            # Return Json response
            return JsonResponse({
                'hit' : audit_list,
                'whitelist' : whitelist,
            })
        except Exception as e:
            print(e)

class api_WhitelistAudit_post(UserPassesTestMixin,TemplateView):
    '''
    View for whitelisting audit hits for current task
    '''
    def handle_no_permission(self):
        return redirect('login')
    def test_func(self):
        # return self.request.user.has_perm('Build_Tree.make_taskRecord')
        return self.request.user.groups.filter(name='mapping | view tasks').exists()

    def post(self, request, **kwargs):
        try:
            payload = request.POST

            audit = MappingTaskAudit.objects.get(id=payload.get('auditId'))
            current_user = User.objects.get(id=request.user.id)
            audit.ignore = True
            audit.ignore_user = current_user
            audit.save()
            # Return Json response
            return JsonResponse({
                'hit' : str(audit),
                'whitelist' : 'Whitelist success',
            })
        except Exception as e:
            print(e)