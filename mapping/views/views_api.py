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

class api_UpdateCodesystems_post(UserPassesTestMixin,TemplateView):
    '''
    Receives requests reload the labcodeset through async task
    Only allowed with admin codesystem rights.
    '''
    def handle_no_permission(self):
        return redirect('login')
    def test_func(self):
        # return self.request.user.has_perm('Build_Tree.make_taskRecord')
        return self.request.user.groups.filter(name='mapping | admin codesystems').exists()

    def post(self, request, **kwargs):
        try:
            print('Labcode', json.loads(request.POST.get('codesystem[labcode]')))
            if json.loads(request.POST.get('codesystem[labcode]')):
                import_labcodeset_async.delay()
                # Import pre-existent mappings as a comment
                try:
                    df = read_excel('/webserver/mapping/resources/labcodeset/init_mapping_NHG45-LOINC.xlsx')
                    # Vervang lege cellen door False
                    df=df.fillna(value=False)
                    codesystem = MappingCodesystem.objects.get(id='4') # NHG tabel 45
                    user = User.objects.get(username='hielkema')
                    for index, row in df.iterrows():
                        bepalingnr = row['bepalingsnr']
                        notitie = row['Notitie']
                        loinc_id = row['LOINC-id']
                        loinc_name = row['LOINC-naam']
                        component = MappingCodesystemComponent.objects.get(codesystem_id=codesystem, component_id=bepalingnr)
                        try:
                            if loinc_id != 'UNMAPPED':
                                task = MappingTask.objects.get(source_component=component)
                                comment = "Voorstel import: [{notitie}] LOINC-ID {loinc_id} - {loinc_name}".format(notitie=notitie, loinc_id=loinc_id, loinc_name=loinc_name)
                                MappingComment.objects.get_or_create(
                                    comment_title = 'NHG-LOINC mapping (Hielkema)',
                                    comment_task = task,
                                    comment_body = comment,
                                    comment_user = user,
                                )
                        except:
                            print('Geen taak voor dit concept')
                            print(bepalingnr, notitie, loinc_id, loinc_name)
                except:
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    error = 'Exc type: {} \n TB: {}'.format(exc_type, exc_tb.tb_lineno)
                    print(error)

            print('Snomed', json.loads(request.POST.get('codesystem[snomed]')))
            if json.loads(request.POST.get('codesystem[snomed]')): # codesystem 1 = snomed
                import_snomed_async.delay('373873005') # farmaceutisch/biologisch product (product)
                import_snomed_async.delay('260787004') # fysiek object (fysiek object)
                import_snomed_async.delay('78621006') # fysieke kracht (fysieke kracht)
                import_snomed_async.delay('272379006') # gebeurtenis (gebeurtenis)
                import_snomed_async.delay('419891008') # gegevensobject (gegevensobject)
                import_snomed_async.delay('404684003') # klinische bevinding (bevinding)
                import_snomed_async.delay('362981000') # kwalificatiewaarde (kwalificatiewaarde)
                import_snomed_async.delay('123037004') # lichaamsstructuur (lichaamsstructuur)
                import_snomed_async.delay('123038009') # monster (monster)
                import_snomed_async.delay('410607006') # organisme (organisme)
                import_snomed_async.delay('243796009') # situatie met expliciete context (situatie)
                import_snomed_async.delay('48176007') # sociale context (sociaal concept)
                import_snomed_async.delay('105590001') # substantie (substantie)
                import_snomed_async.delay('71388002') #  verrichting (verrichting)
                import_snomed_async.delay('363787002') #   waarneembare entiteit (waarneembare entiteit)

            print('nhgVerr', json.loads(request.POST.get('codesystem[nhgverr]')))
            if json.loads(request.POST.get('codesystem[nhgverr]')):
                import_nhgverrichtingen_task.delay()
                
            print('nhgBep', json.loads(request.POST.get('codesystem[nhgbep]')))
            if json.loads(request.POST.get('codesystem[nhgbep]')):
                import_nhgbepalingen_task.delay()
            
            print('nhgICPC', json.loads(request.POST.get('codesystem[icpc]')))
            if json.loads(request.POST.get('codesystem[icpc]')):
                import_icpc_task.delay()

            context = {
                'result': "success",
            }
            # Return JSON
            return JsonResponse(context,safe=False)
        except Exception as e:
            print(type(e), e, kwargs)
    def get(self, request, **kwargs):        
        return render(request, 'mapping/v2/import_codesystems.html', {
            'page_title': 'Mapping project',
        })

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

class api_hashtag_post(UserPassesTestMixin,TemplateView):
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
            print(payload)
            task = MappingTask.objects.get(id=payload.get('task'))
            current_user = User.objects.get(id=request.user.id)
            MappingComment.objects.create(
                comment_title='hashtag',
                comment_task=task,
                comment_body='#'+payload.get('tag'),
                comment_user=current_user
            )

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
        users = User.objects.filter().order_by('username')
        user_list = []
        tasks = MappingTask.objects.all()
        # For each user
        for user in users:
            # Check if they have access, or have any tasks to their name. If so, add to list.
            if tasks.filter(user=user).exists() or user.groups.filter(name='mapping | access').exists():
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
            try:
                extra_dict = json.loads(task.source_component.component_extra_dict)
            except:
                extra_dict = ''
            task = ({
                    'id'    :   task.id,
                    'component' : {
                        'title' :   task.source_component.component_title,
                        'codesystem' : {
                            'id' : task.source_component.codesystem_id.id,
                            'title' : task.source_component.codesystem_id.codesystem_title,
                            'version' : task.source_component.codesystem_id.codesystem_version,
                        },
                        'extra' : extra_dict,
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
            context = {
                'task': task,
                'status_list': status_list,
            }
        # If task does not exist, return empty
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            error = 'Exc type: {} \n TB: {}'.format(exc_type, exc_tb.tb_lineno)
            print(error)
            task = []
            context = {
                'task': '',
                'status' : 'Mislukt - geen ID?',
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
        if task.project_id.project_type == "1":
            mappings = MappingRule.objects.filter(project_id=task.project_id, source_component=task.source_component)
        if task.project_id.project_type == "2":
            mappings = MappingRule.objects.filter(project_id=task.project_id, source_component=task.source_component)
        elif task.project_id.project_type == "4":
            mappings = MappingRule.objects.filter(project_id=task.project_id, target_component=task.source_component)
        mappings = mappings.order_by('mapgroup', 'mappriority')
        mapping_list = []
        for mapping in mappings:
            mapcorrelation = mapping.mapcorrelation
            # if mapcorrelation == "447559001": mapcorrelation = "Broad to narrow"
            # if mapcorrelation == "447557004": mapcorrelation = "Exact match"
            # if mapcorrelation == "447558009": mapcorrelation = "Narrow to broad"
            # if mapcorrelation == "447560006": mapcorrelation = "Partial overlap"
            # if mapcorrelation == "447556008": mapcorrelation = "Not mappable"
            # if mapcorrelation == "447561005": mapcorrelation = "Not specified"
            try:
                extra = json.loads(mapping.target_component.component_extra_dict)
            except:
                extra = ""
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
                    'extra' : extra,
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
        if task.project_id.project_type == "1" or task.project_id.project_type == "2" :
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
            'advice' : task.project_id.use_mapadvice,
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

class api_ReverseMapping_get(UserPassesTestMixin,TemplateView):
    '''
    Delivers the reverse mapping for a task
    Only allowed with view tasks rights.
    '''
    def handle_no_permission(self):
        return redirect('login')
    def test_func(self):
        # return self.request.user.has_perm('Build_Tree.make_taskRecord')
        return self.request.user.groups.filter(name='mapping | view tasks').exists()

    def get(self, request, **kwargs):
        # Get reverse mappings for relevant project types
        current_task = MappingTask.objects.get(id=kwargs.get('task')) 
        reverse_mappings = MappingRule.objects.filter(source_component=current_task.source_component)
        
        reverse_list = []
        for reverse in reverse_mappings:
            reverse_list.append({
                'codesystem' : {
                    'id' : reverse.target_component.codesystem_id.id,
                    'title' : reverse.target_component.codesystem_id.codesystem_title,
                    'version' : reverse.target_component.codesystem_id.codesystem_version,
                },
                'id' : reverse.target_component.component_id,
                'title' : reverse.target_component.component_title,
            })

        return JsonResponse({
            'reversemappings' : reverse_list,
        })

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
            tasks = MappingTask.objects.filter(user=current_user, project_id_id=current_project.id).exclude(status=current_project.status_complete).exclude(status=current_project.status_rejected).order_by('id')
            
            status_list = MappingTaskStatus.objects.filter(project_id=kwargs.get('project')).order_by('status_id')#.exclude(id=current_project.status_complete.id)
            tasks_per_status_labels = []
            tasks_per_status_values = []
            user_list = User.objects.filter()
            tasks_per_user_labels = []
            tasks_per_user_values = []
            for user in user_list:
                num_tasks = MappingTask.objects.filter(project_id_id=current_project.id, user=user).exclude(status=current_project.status_complete).exclude(status=current_project.status_rejected).count()
                if num_tasks > 0:
                    num_tasks = MappingTask.objects.filter(project_id_id=current_project.id, user=user).exclude(status=current_project.status_complete).exclude(status=current_project.status_rejected).count()
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
        tasks = MappingTask.objects.filter(user=current_user, project_id_id=current_project.id).exclude(status=current_project.status_complete).exclude(status=current_project.status_rejected).order_by('id')
        total_num_tasks = len(tasks)
        if tasks.count() == 0:    
            tasks = MappingTask.objects.filter(project_id_id=current_project.id).exclude(status=current_project.status_complete).exclude(status=current_project.status_rejected).order_by('id')
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

class api_EclQuery_get(UserPassesTestMixin,TemplateView):
    '''
    Class used to handle creating an ECL query bound to a (target) component.
    Only accessible with edit mapping rights.
    '''
    def handle_no_permission(self):
        return redirect('login')
    def test_func(self):
        return self.request.user.groups.filter(name='mapping | view tasks').exists()
    
    def get(self, request, **kwargs):

        task_id = int(kwargs.get('task'))
        task = MappingTask.objects.get(id=task_id)
        try:
            current_user = User.objects.get(id=request.user.id)
            
            # Generate query list for view
            querys = MappingEclQuery.objects.filter(target_component=task.source_component).order_by('query_function')
            query_list = []
            for query in querys:
                query_list.append({
                    'query_id' : query.id,
                    'query' : query.query,
                    'query_function' : query.query_function,
                    'query_type' : query.query_type,
                    'DELETE' : False,
                })
            query_list.append({
                'query_id' : False,
                'query' : '',
                'query_function' : '2',
                'query_type' : '2',
                'DELETE' : False,
            })

            # Generate ECL query
            query_add_list = []
            query_min_list = []

            min_querys = querys.filter(query_function="1")
            add_querys = querys.filter(query_function="2")
            for query in min_querys:
                if query.query_type == "1":
                    modifier = "<"
                elif query.query_type == "2":
                    modifier = "<<"
                elif query.query_type == "3":
                    modifier = ""
                query_min_list.append(
                    "({modif}{query})".format(modif=modifier, query=query.query)
                )
            for query in add_querys:
                if query.query_type == "1":
                    modifier = "<"
                elif query.query_type == "2":
                    modifier = "<<"
                elif query.query_type == "3":
                    modifier = ""
                query_add_list.append(
                    "({modif}{query})".format(modif=modifier, query=query.query)
                )
            add_querys_sep = " or "
            min_querys_sep = " or "
            if len(query_add_list) > 0 and len(query_min_list) > 0:
                generated_query = "({add}) MINUS ({minus})".format(
                    add = add_querys_sep.join(query_add_list),
                    minus = min_querys_sep.join(query_min_list),
                )
            elif len(query_add_list) > 0 and len(query_min_list) == 0:
                generated_query = "({add})".format(
                    add = add_querys_sep.join(query_add_list),
                )
            else:
                generated_query = False
                results = []

            return JsonResponse({
                'generated_query' : generated_query,
                'queries' : query_list,
            })
        except:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            error = 'Exc type: {} \n TB: {}'.format(exc_type, exc_tb.tb_lineno)
            print(error)

            return JsonResponse({
                'result' : 'error',
            })

class api_EclQuery_put(UserPassesTestMixin,TemplateView):
    '''
    Class used to handle creating an ECL query bound to a (target) component.
    Only accessible with edit mapping rights.
    '''
    def handle_no_permission(self):
        return redirect('login')
    def test_func(self):
        return self.request.user.groups.filter(name='mapping | edit mapping').exists()
    def post(self, request, **kwargs):
        payload = request.POST
        print(payload)
        task_id = int(payload.get('task'))
        try:
            task = MappingTask.objects.get(id=int(task_id),)
            # Handle search form and present results
            mapping_queries = json.loads(payload.get('mappingQueries'))
            
            for query in mapping_queries:
                print(query)
                if query.get('query_id') and query.get('DELETE'):
                    obj = MappingEclQuery.objects.get(id = query.get('query_id')).delete()
                elif query.get('query_id'):
                    print("Query id gevonden, aanpassen")
                    # Aanpassen
                    obj = MappingEclQuery.objects.get(id = query.get('query_id'))
                    obj.query_type = query.get('query_type')
                    obj.query_function = query.get('query_function')
                    obj.query = query.get('query')
                    obj.save()
                elif query.get('query') != '':
                    # New query
                    print("Saving new query to DB")
                    created = MappingEclQuery.objects.create(
                        project_id=task.project_id,
                        target_component=task.source_component,
                        query=query.get('query'),
                        query_type=query.get('query_type'),
                        query_function=query.get('query_function'),
                    )
                    created.save()
                else:
                    print("Query niet verwerkt (query leeg?)")
                print("ECL query saved in DB")

            # Generate ECL query
            querys = MappingEclQuery.objects.filter(target_component=task.source_component).order_by('id')
            query_add_list = []
            query_min_list = []

            min_querys = querys.filter(query_function="1")
            add_querys = querys.filter(query_function="2")
            for query in min_querys:
                if query.query_type == "1":
                    modifier = "<"
                elif query.query_type == "2":
                    modifier = "<<"
                elif query.query_type == "3":
                    modifier = ""
                query_min_list.append(
                    "({modif}{query})".format(modif=modifier, query=query.query)
                )
            for query in add_querys:
                if query.query_type == "1":
                    modifier = "<"
                elif query.query_type == "2":
                    modifier = "<<"
                elif query.query_type == "3":
                    modifier = ""
                query_add_list.append(
                    "({modif}{query})".format(modif=modifier, query=query.query)
                )
            add_querys_sep = " or "
            min_querys_sep = " or "
            if len(query_add_list) > 0 and len(query_min_list) > 0:
                generated_query = "({add}) MINUS ({minus})".format(
                    add = add_querys_sep.join(query_add_list),
                    minus = min_querys_sep.join(query_min_list),
                )
            elif len(query_add_list) > 0 and len(query_min_list) == 0:
                generated_query = "({add})".format(
                    add = add_querys_sep.join(query_add_list),
                )
            else:
                generated_query = False
                results = []
            
            # Check if there are running celery tasks for this task, cancel them if there are before starting a new task
            if payload.get('preview') == 'true':
                print("preview")
                celery_task = add_mappings_ecl_1_task.delay(task=task.id, query=generated_query, preview=True)
                celery_task_id = celery_task.id
                print("TASK STARTED WITH ID ******", celery_task_id)
            
            else:
                print("production run")
                i = inspect()
                active = i.active('mapping.tasks.add_mappings_ecl_1_task')
                try:
                    for async_task in active:
                        info = i.active(async_task)
                        for celery_task in info.get(async_task):
                            celery_task_details = json.loads(celery_task.get('kwargs').replace("\'", "\""))
                            if celery_task_details.get('task') == task.id:
                                print("Task already running! ID is {}. Revoking task.".format(
                                    celery_task.get('id'),
                                ))
                                revoke(celery_task.get('id'), terminate=True)
                    celery_task = add_mappings_ecl_1_task.delay(task=task.id, query=generated_query, preview=False)
                    celery_task_id = celery_task.id
                    print("TASK STARTED WITH ID ******", celery_task_id)
                except:
                    print("No active tasks or celery unreachable.")
            
            
            return JsonResponse({
                'result' : 'success',
                'mappings' : celery_task.get(),
                'celery' : celery_task_id,
            })
        except:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            error = 'Exc type: {} \n TB: {}'.format(exc_type, exc_obj, exc_tb.tb_lineno)
            print(error)

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
        # Handle 1-N mapping tasks
        if project.project_type == '1':
            user = User.objects.get(id=request.user.id)
            try:
                task = MappingTask.objects.get(id=kwargs.get('task'))
                task = task.id
            except Exception as e:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                error = 'Exc type: {} \n TB: {}'.format(exc_type, exc_tb.tb_lineno)
                print(error)
                task = 0
            return render(request, 'mapping/v2/1-n/task_editor.html', {
                'page_title': 'Mapping project',
                'current_project': project,
                'current_task' : task,
            })
        # Handle ECL-1 mapping tasks
        elif project.project_type == '4':
            user = User.objects.get(id=request.user.id)
            try:
                task = MappingTask.objects.get(id=kwargs.get('task'))
                task = task.id
            except Exception as e:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                error = 'Exc type: {} \n TB: {}'.format(exc_type, exc_tb.tb_lineno)
                print(error)
                task = 0
            return render(request, 'mapping/v2/ecl-1/task_editor.html', {
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
        project = MappingProject.objects.get(id=kwargs.get('project'))
        statuses = MappingTaskStatus.objects.filter(project_id=project).order_by('status_id')
        status_list = []
        for status in statuses:
            status_list.append({
                'id' : status.id,
                'status_id' : status.status_id,
                'title' : status.status_title,
            })

        # Return Json response
        return JsonResponse({
            'current_user': {
                'id' : user.id,
                'name' : user.username,
            },
            'status_list' : status_list,
        })

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
                'extra' : component.component_extra_dict,
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
                        'extra' : component.component_extra_dict,
                        'codesystem': {
                            'title' : component.codesystem_id.codesystem_title,
                            'version' : component.codesystem_id.codesystem_version,
                            'id' : component.codesystem_id.id,
                        }
                    },
                })


        # Return Json response
        return JsonResponse({'items':items[:20]})

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