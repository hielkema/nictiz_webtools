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
from rest_framework import views, status
from rest_framework.response import Response
from rest_framework import permissions

from ..tasks import *
from ..forms import *
from ..models import *

from snowstorm_client import Snowstorm

class Permission_MappingProject_Access(permissions.BasePermission):
    """
    Global permission check rights to use the RC Audit functionality.
    """
    def has_permission(self, request, view):
        if 'mapping | access' in request.user.groups.values_list('name', flat=True):
            return True

class Permission_MappingProject_ChangeMappings(permissions.BasePermission):
    """
    Global permission check rights to change mappings.
    """
    def has_permission(self, request, view):
        if 'mapping | edit mapping' in request.user.groups.values_list('name', flat=True):
            return True

class MappingTargetSearch(viewsets.ViewSet):
    permission_classes = [Permission_MappingProject_Access]

    def create(self, request):
        query = request.data.get('query').strip()
        print(request.user.username,": mappings/MappingTargetSearch : Searching for",query)

        output =[]

        # Start with the best matches: single word postgres match
        snomedComponents = MappingCodesystemComponent.objects.filter(
            Q(component_id__icontains=query) |
            Q(component_title__icontains=query)
        ).select_related(
            'codesystem_id',
        )
        for result in snomedComponents:
            try:
                if (result.component_extra_dict.get('Actief',False) == "True") or (result.component_extra_dict.get('Actief',False) == True) :
                    active = 'Ja'
                else:
                    active = 'Nee'
            except:
                active = 'Onbekend'
            output.append({
                'text' : f"{result.codesystem_id.codesystem_title} {result.component_id} - {result.component_title} [Actief: {active}]",
                'value': result.component_id,
                'component': {'id':result.id, 'title':result.component_title},
                'codesystem': {'title': result.codesystem_id.codesystem_title, 'version': result.codesystem_id.codesystem_version},
                'extra': result.component_extra_dict,
            })
        # In addition, full text search if needed
        if len(output) == 0:
            snomedComponents = MappingCodesystemComponent.objects.annotate(search=SearchVector('component_title','component_id',),).filter(search=query)        
            for result in snomedComponents:
                output.append({
                    'text' : result.component_title,
                    'value': result.component_id,
                    'component': {'id':result.id, 'title':result.component_title},
                    'codesystem': {'title': result.codesystem_id.codesystem_title, 'version': result.codesystem_id.codesystem_version},
                    'extra': result.component_extra_dict,
                })
        output = sorted(output, key=lambda item: len(item.get("text")), reverse=False)
        return Response(output[:20])

class RuleSearchByComponent(viewsets.ViewSet):
    permission_classes = [Permission_MappingProject_Access]

    def create(self, request):
        query = request.data.get('query')
        print(request.user.username,": mappings/RuleSearchByComponent : Searching for",query)

        component = MappingCodesystemComponent.objects.get(id=query)
        
        output=[]

        target = MappingRule.objects.filter(target_component = component)
        for rule in target:
            tasks = MappingTask.objects.filter(source_component = rule.source_component)
            for task in tasks:
                output.append({
                    'task_id' : task.id,
                    'project' : task.project_id.title,
                    'project_id' : task.project_id.id,
                    'rule_id' : rule.id,
                    'source_id' : rule.source_component.component_id,
                    'source_title' : rule.source_component.component_title,
                    'target_id' : rule.target_component.component_id,
                    'target_title' : rule.target_component.component_title,
                })

        source = MappingRule.objects.filter(source_component = component)
        for rule in source:
            tasks = MappingTask.objects.filter(source_component = rule.source_component)
            for task in tasks:
                output.append({
                    'task_id' : task.id,
                    'project' : task.project_id.title,
                    'project_id' : task.project_id.id,
                    'rule_id' : rule.id,
                    'source_id' : rule.source_component.component_id,
                    'source_title' : rule.source_component.component_title,
                    'target_id' : rule.target_component.component_id,
                    'target_title' : rule.target_component.component_title,
                })

        return Response(output)

class MappingDialog(viewsets.ViewSet):
    permission_classes = [Permission_MappingProject_Access]

    def retrieve(self, request, pk=None):
        print("Retrieving mappingrule",pk)
        if pk != 'extra':
            mapping = MappingRule.objects.get(id = pk)
            output = {
                'id' : mapping.id,
                'codesystem': {
                    'title': mapping.target_component.codesystem_id.codesystem_title, 
                    'version': mapping.target_component.codesystem_id.codesystem_version
                },
                'component' : {
                    'id' : mapping.target_component.component_id,
                    'title' : mapping.target_component.component_title,
                    'extra' : mapping.target_component.component_extra_dict,
                }
            }
        else:
            output = {
                'id' : 'extra',
                'codesystem': {
                    'title': None, 
                    'version': None,
                },
                'component' : {
                    'id' : None,
                    'title' : 'Nieuwe mapping',
                    'extra' : None,
                }
            }
        return Response(output)

    def create(self, request):
        if 'mapping | edit mapping' in request.user.groups.values_list('name', flat=True):
            print(f"[MappingDialog/create] @ {request.user.username}")
            print(f"Data: {request.data}")
  
            if request.data.get('new'):
                print("Target is bekend - uitvoeren")
                task = MappingTask.objects.get(id=request.data.get('task'))
                current_user = User.objects.get(id=request.user.id)
                if MappingProject.objects.get(id=task.project_id.id, access__username=current_user):
                    try:
                        if task.project_id.project_type == "1": # One to many
                            source_component = MappingCodesystemComponent.objects.get(id=task.source_component.id)
                            target_component = MappingCodesystemComponent.objects.get(id=request.data.get('new').get('component').get('id'))                
                            print('Project type 1')
                        elif task.project_id.project_type == "2": # Many to one
                            source_component = MappingCodesystemComponent.objects.get(id=request.data.get('new').get('component').get('id'))
                            target_component = MappingCodesystemComponent.objects.get(id=task.source_component.id)
                            print('Project type 2')
                        elif task.project_id.project_type == "4": # ECL to one
                            source_component = MappingCodesystemComponent.objects.get(id=request.data.get('new').get('component').get('id'))
                            target_component = MappingCodesystemComponent.objects.get(id=task.source_component.id)
                            print('Project type 4')
                        else:
                            print("No support for this project type in MappingDialog POST method [type 3?]")
                    except Exception as e:
                        exc_type, exc_obj, exc_tb = sys.exc_info()
                        error = 'Exc [MappingDialog/create] error type: {} \n TB: {}'.format(exc_type, exc_tb.tb_lineno)
                        print(error)

                    print('Mapping:', request.data.get('mapping'),'\n\n')
                    if request.data.get('mapping').get('id') == 'extra':
                        print('ID=extra -> Zou een nieuwe mapping moeten worden.')
                        print('Task',request.data.get('task'))
                        print('Creating new mapping to component',request.data.get('new').get('component').get('id'))
                        new_target = MappingCodesystemComponent.objects.get(id=request.data.get('new').get('component').get('id'))
                        mapping = MappingRule.objects.create(
                            project_id = task.project_id,
                            source_component = task.source_component,
                            target_component = new_target,
                            active = True,
                        )
                        mapping.save()
                    else:
                        print('Betreft bestaande mapping.')
                        print('Replacing mapping',request.data.get('mapping',{}).get('id'))
                        print(f"New target: {request.data.get('new')}")
                        print(f"Target is ingesteld - wordt aangepast")
                        mapping = MappingRule.objects.get(id = request.data.get('mapping').get('id'))
                        new_target = MappingCodesystemComponent.objects.get(id=request.data.get('new').get('component').get('id'))
                        mapping.target_component = new_target
                        mapping.save()
                        print(f"Mapping object: {str(mapping)}")

                    print("Start audit")
                    audit_async.delay('multiple_mapping', task.project_id.id, task.id)

                return Response(str(mapping))
            else:
                print("Target is niet bekend - geen actie ondernomen")
                return Response(None)
        else:
            return Response('Geen toegang', status=status.HTTP_401_UNAUTHORIZED)

class MappingExclusions(viewsets.ViewSet):
    permission_classes = [Permission_MappingProject_ChangeMappings]
    def create(self, request):
        print(f"[MappingExclusions/create] @ {request.user.username} - {request.data}")
        try:
            if 'mapping | edit mapping' in request.user.groups.values_list('name', flat=True):
                print(f"[MappingExclusions/create] @ {request.user.username} => Go")
                task = MappingTask.objects.get(id=request.data.get('payload').get('id'))
                obj, created = MappingEclPartExclusion.objects.get_or_create(task = task)
                obj.components = list(request.data.get('payload').get('exclusions',{}).get('string').split('\n'))
                obj.save()
                print(obj, created)
            else:
                print(f"[MappingExclusions/create] @ {request.user.username} => No permission")
        except Exception as e:
            print(f"[MappingExclusions/create] @ {request.user.username} => error ({e})")
            
        return Response(True)

class MappingTargets(viewsets.ViewSet):
    permission_classes = [Permission_MappingProject_Access]

    def create(self, request):
        print(f"[MappingTargets/create] @ {request.user.username}")

        try:
            if 'mapping | edit mapping' in request.user.groups.values_list('name', flat=True):
                print(str(request.data)[:100],"........")
                task = MappingTask.objects.get(id=request.data.get('task'))
                current_user = User.objects.get(id=request.user.id)

                if MappingProject.objects.get(id=task.project_id.id, access__username=current_user) and task.user == current_user:
                    # Handle 1-Many mapping targets
                    if task.project_id.project_type == '1':
                        print('\n\n----------------------------------\n')
                        for target in request.data.get('targets'):
                            print("ID",             target.get('target').get('id'))     
                            print("NIEUW",          target.get('target').get('new'))     
                            print("component_id",   target.get('target').get('component_id'))     
                            print("component_title",target.get('target').get('component_title'))
                            print("rule",           target.get('rule'))
                            print("correlation",    target.get('correlation'))
                            print("advice",         target.get('advice'))
                            print("group",          target.get('group'))
                            print("priority",       target.get('priority'))
                            print("dependency",     target.get('dependency'))
                            print("DELETE",         target.get('delete'))
                            print("")

                            if target.get('delete') == True:
                                print('Get ready to delete')
                                mapping_rule = MappingRule.objects.get(id=target.get('id'))
                                print(mapping_rule)
                                mapping_rule.delete()
                                print(mapping_rule)
                            elif target.get('id') != 'extra':
                                print("Aanpassen mapping", target.get('id'))
                                mapping_rule = MappingRule.objects.get(id=target.get('id'))

                                mapping_rule.mapgroup           = target.get('group')
                                mapping_rule.mappriority        = target.get('priority')
                                mapping_rule.mapcorrelation     = target.get('correlation')
                                mapping_rule.mapadvice          = target.get('advice')
                                mapping_rule.maprule            = target.get('rule')

                                # Handle specifies/dependency/rule binding
                                if target.get('dependency'):
                                    for dependency in target.get('dependency'):
                                        print("Handling",dependency) # TODO debug
                                        # If binding should be true:
                                        # First check if the relationship exists in DB, otherwise create it.
                                        if dependency.get('binding'):
                                            # Check if binding does not exists in DB
                                            print('Binding should be present')
                                            if not mapping_rule.mapspecifies.filter(id=dependency.get('rule_id')).exists():
                                                print("Binding (many to many) not present in DB - creating")
                                                addrule = MappingRule.objects.get(id=dependency.get('rule_id'))
                                                print('Adding relationship to rule', addrule)
                                                mapping_rule.mapspecifies.add(addrule)
                                                # Sanity check: success?
                                                if mapping_rule.mapspecifies.filter(id=dependency.get('rule_id')).exists():
                                                    print("Created")
                                                else:
                                                    print("Failed")
                                            else:
                                                print('Binding already present')
                                        # If binding should not exist:
                                        # Check if present, if so: remove
                                        else:
                                            print('Binding should not be present')
                                            # Check if binding exists in DB
                                            if mapping_rule.mapspecifies.filter(id=dependency.get('rule_id')).exists():
                                                print("Binding (many to many) present in DB but should not be - removing")
                                                remrule = MappingRule.objects.get(id=dependency.get('rule_id'))
                                                mapping_rule.mapspecifies.remove(remrule)
                                                # Sanity check: success?
                                                if mapping_rule.mapspecifies.filter(id=dependency.get('rule_id')).exists():
                                                    print("Still present")
                                                else:
                                                    print("Succesfully removed")
                                            else:
                                                print('Binding was already absent')
                                    print("Done handling dependency for",dependency)
                                mapping_rule.save()

                        audit_async.delay('multiple_mapping', task.project_id.id, task.id)
                        return Response([])
                    # Handle ECL-1 mapping targets
                    elif task.project_id.project_type == '4':
                        print("MappingTargets/create - Handling ECL-1 mapping targets for task",task.id)
                        
                        queries = request.data.get('targets').get('queries')
                        for query in queries:
                            print("Handling query",str(query)[:100],".........")
                            if query.get('delete') == True:
                                print('delete query ',query.get('id'))
                                current_query = MappingEclPart.objects.get(id = query.get('id'))
                                current_query.delete()
                            else:                           
                                if query.get('id') == 'extra' and query.get('description') and query.get('query') and query.get('correlation'):
                                    print(f"Creating new query with description {query.get('description')} and query {query.get('query')}")
                                    currentQuery = MappingEclPart.objects.create(
                                        task = task,
                                        description = query.get('description'),
                                        query = query.get('query'),
                                        mapcorrelation = query.get('correlation'),
                                    )
                                    UpdateECL1Task.delay(currentQuery.id, query.get('query'))
                                elif query.get('id') != 'extra' and query.get('description') and query.get('query') and query.get('correlation'):
                                    print(f"Editing existing query {query.get('id')}")
                                    currentQuery = MappingEclPart.objects.get(id = query.get('id'))
                                    currentQuery.description = query.get('description')
                                    currentQuery.query = query.get('query')
                                    currentQuery.mapcorrelation = query.get('correlation')
                                    currentQuery.save()
                                    print(f"---\nUsed the following data for update:\nQuery: {query.get('query')}\nDescription: {query.get('description')}\nCorrelation: {query.get('correlation')}\n")
                                    queryInDatabase = MappingEclPart.objects.get(id = query.get('id'))
                                    print(f"Update resulted in:\nQuery {queryInDatabase.id}: {queryInDatabase.query}\nDescription: {queryInDatabase.description}\nCorrelation: {queryInDatabase.mapcorrelation}\n---")
                                    print("---")
                                    print(f"Handled {str(queryInDatabase)}")
                                    UpdateECL1Task.delay(currentQuery.id, query.get('query'))
                                else:
                                    print("Empty query?")

                            
                        return Response({
                            'message': 'ECL-1 targets',
                        })
                # Error - no access due to project or task requirements
                else:
                    return Response('Geen toegang. Niet jouw taak? Geen toegang tot het project?')
            # Error - no acces due to no rights
            else:
                return Response('Geen toegang tot -edit mapping-')
        except Exception as e:
            print("\n\nException caught")
            print("Request by",str(request.user))
            print(e)
            print("\n\n")


    def retrieve(self, request, pk=None):
        task = MappingTask.objects.get(id=pk)
        current_user = User.objects.get(id=request.user.id)
        
        if MappingProject.objects.get(id=task.project_id.id, access__username=current_user):
            # Handle 1-N mapping targets
            if task.project_id.project_type == '1':
                if task.project_id.project_type == "1":
                    mappings = MappingRule.objects.filter(project_id=task.project_id, source_component=task.source_component)
                elif task.project_id.project_type == "2":
                    mappings = MappingRule.objects.filter(project_id=task.project_id, source_component=task.source_component)
                mappings = mappings.order_by('mapgroup', 'mappriority')
                mapping_list = []
                dependency_list = []
                for mapping in mappings:
                    mapcorrelation = mapping.mapcorrelation
                    # if mapcorrelation == "447559001": mapcorrelation = "Broad to narrow"
                    # if mapcorrelation == "447557004": mapcorrelation = "Exact match"
                    # if mapcorrelation == "447558009": mapcorrelation = "Narrow to broad"
                    # if mapcorrelation == "447560006": mapcorrelation = "Partial overlap"
                    # if mapcorrelation == "447556008": mapcorrelation = "Not mappable"
                    # if mapcorrelation == "447561005": mapcorrelation = "Not specified"
                    try:
                        extra = mapping.target_component.component_extra_dict
                    except:
                        extra = ""
                    
                    # Add dependencies to list
                    # For each mapping rule in this task, add an item with true/false
                    for maprule in mappings:
                        if mapping.mapspecifies.filter(id = maprule.id).exists():
                            binding = True
                        else:
                            binding = False
                        if maprule is not mapping:
                            dependency_list.append({
                                'rule_id'   : maprule.id,
                                'source'    : maprule.target_component.component_title,
                                'binding'   : binding,
                            })

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
                            },
                            'new' : {},
                        },
                        'group' : mapping.mapgroup,
                        'priority' : mapping.mappriority,
                        'correlation' : mapping.mapcorrelation,
                        'advice' : mapping.mapadvice,
                        'rule' : mapping.maprule,
                        'dependency' : dependency_list,
                        'delete' : False,
                    })
                    dependency_list = []
                if task.project_id.project_type == "1" or task.project_id.project_type == "2" :
                    # Append extra empty mapping
                    dependency_list = []
                    for maprule in mappings:
                        dependency_list.append({
                            'rule_id'   : maprule.id,
                            'source'    : maprule.target_component.component_title,
                            'binding'   : False,
                        })
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
                            'dependency' : dependency_list,
                            'delete' : False,
                        })
                    dependency_list = []
                return Response(mapping_list)

            # Handle ECL-1 mapping targets
            elif task.project_id.project_type == '4':
                ### Get all definitive mappings
                mappings = MappingRule.objects.filter(
                    project_id=task.project_id, 
                    target_component=task.source_component).select_related(
                        'source_component',
                        'target_component',
                    )
                mappings = mappings.order_by('mapgroup', 'mappriority')
                mapping_list = []
                dependency_list = []
                try:
                    extra = mapping.target_component.component_extra_dict
                except:
                    extra = ""
                for mapping in mappings:
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
                            },
                        },
                        'correlation' : mapping.mapcorrelation,
                    })
                

                # Retrieve results from components that should be excluded
                exclude_componentIDs = []
                excluded_componentIDs = []
                try:
                    obj = MappingEclPartExclusion.objects.get(task = task)
                    components = MappingCodesystemComponent.objects.filter(
                            codesystem_id = obj.task.source_component.codesystem_id,
                            component_id__in=list(obj.components)
                        )
                    # print(f"Will exclude ECL results from {str(components)}")
                    # Loop components
                    for component in components:
                        # print(f"Handling exclusion of {str(component)}")
                        # For each, retrieve their tasks, in this same project
                        exclude_tasks = MappingTask.objects.filter(project_id = task.project_id, source_component=component)
                        # print(f"Found tasks: {str(exclude_tasks)}")
                        for exclude_task in exclude_tasks:
                            # print(f"Handling exclude_task {str(exclude_task)}")
                            queries = MappingEclPart.objects.filter(task=exclude_task)
                            for query in queries:
                                # print(f"Found query result for {exclude_task.source_component.component_title}: [{str(query.result)}] \n{list(query.result.get('concepts'))}")
                                for key, value in query.result.get('concepts').items():
                                    exclude_componentIDs.append(key)
                        
                        # print(f"Next component - list is now: {exclude_componentIDs}\n\n")
                    print(f"Full exclude list: {exclude_componentIDs}")
                except Exception as e:
                    True

                # Get all ECL Queries - including cached snowstorm response
                all_results = list()
                query_list = list()
                queries = MappingEclPart.objects.filter(task=task).select_related(
                    'task'
                ).order_by('id')
                queries_unfinished = False
                mapping_list_unfinished = False
                i=0
                for query in queries:
                    i+=1
                    if query.finished == False:
                        queries_unfinished = True
                    if query.export_finished == False:
                        mapping_list_unfinished = True
                    query_list.append({
                        'id' : query.id,
                        'description' : query.description,
                        'query' : query.query,
                        'finished' : query.finished,
                        'error' : query.error,
                        'failed' : query.failed,
                        'result' : query.result,
                        'correlation' : query.mapcorrelation,
                    })
                    # Add all results to a list for easy viewing
                    try:
                        for key, result in query.result.get('concepts').items():
                            if key not in exclude_componentIDs:
                                # print(result)   
                                _query = result
                                _query.update({
                                    'queryId' : query.id,
                                    'query' : query.query,
                                    'description' : query.description,
                                    'correlation' : query.mapcorrelation,
                                })
                                all_results.append(_query) 
                            else:
                                excluded_componentIDs.append(result)
                    except:
                        print("Retrieve mappings: No results")
                query_list.append({
                    'id' : 'extra',
                    'description' : '',
                    'query' : '',
                    'finished' : False,
                    'error' : False,
                    'failed' : False,
                    'result' : '',
                    'correlation' : '447561005',
                })

                return Response({
                    'queries': query_list, # List of ECL queries
                    'queries_unfinished' : queries_unfinished, # True if any queries have not returned from Snowstorm
                    'allResults' : all_results, # Results of all ECL queries combined in 1 list

                    'exclusion_list' : exclude_componentIDs,
                    'excluded' : excluded_componentIDs,

                    'mappings' : mapping_list,
                    'mappings_unfinished' : mapping_list_unfinished,
                })

class MappingEclToRules(viewsets.ViewSet):
    permission_classes = [Permission_MappingProject_ChangeMappings]

    def retrieve(self, request, pk=None):
        print(request.user,"Creating mapping rules for ECL queries associated with task",pk)
        
        celery = createRulesFromEcl.delay(
            taskid = pk,
        )
        return Response(str(celery))

class MappingReverse(viewsets.ViewSet):
    permission_classes = [Permission_MappingProject_Access]
    def retrieve(self, request, pk=None):
        task = MappingTask.objects.select_related(
            'project_id',
        ).get(id = pk)
        component = MappingCodesystemComponent.objects.get(id = task.source_component.id)
        if task.project_id.project_type == "1":
            reverse_mappings = MappingRule.objects.filter(target_component = component)

            reverse = []
            for mapping in reverse_mappings:
                # reverse.append(f"{mapping.target_component.codesystem_id.codesystem_title} #{mapping.target_component.component_id} - {mapping.target_component.component_title}")
                reverse.append({
                    'id' : mapping.target_component.component_id,
                    'title' : mapping.target_component.component_title,
                    'codesystem' : {
                        'title': mapping.target_component.codesystem_id.codesystem_title,
                    },
                    'correlation' : mapping.mapcorrelation,
                })

        elif task.project_id.project_type == "4":
            reverse_mappings = MappingRule.objects.filter(source_component = component)

            reverse = []
            for mapping in reverse_mappings:
                # reverse.append(f"{mapping.target_component.codesystem_id.codesystem_title} #{mapping.target_component.component_id} - {mapping.target_component.component_title}")
                reverse.append({
                    'id' : mapping.target_component.component_id,
                    'title' : mapping.target_component.component_title,
                    'codesystem' : {
                        'title': mapping.target_component.codesystem_id.codesystem_title,
                    },
                    'correlation' : mapping.mapcorrelation,
                })

        # output = " /".join(reverse)
        return Response(reverse)
        

class MappingListLookup(viewsets.ViewSet):
    permission_classes = [Permission_MappingProject_Access]

    def create(self, request):
        query = request.data.get('list')
        print(request.user.username,": mappings/RuleSearchByComponent : Searching for",query)

        list_source = []
        handled = []
        for ident in query.splitlines():
            print("get component",ident)

            # try:
            components = MappingCodesystemComponent.objects.filter(component_id = str(ident))
            
            for component in components:
                # Identify rules using this component as either target or source
                _rules = MappingRule.objects.filter(source_component = component)
                _rules = _rules | MappingRule.objects.filter(target_component = component)

                # Loop over all source components in the above rules
                for _rule in _rules:

                    # Find tasks using this component as source
                    tasks = MappingTask.objects.filter(source_component = _rule.source_component, project_id__project_type = '1')
                    for task in tasks:
                        if task.id not in handled:
                            rules = MappingRule.objects.filter(source_component = task.source_component).order_by('mapgroup', 'mappriority')
                            rule_list = []
                            for rule in rules:
                                mapcorrelation = rule.mapcorrelation
                                if mapcorrelation == "447559001": mapcorrelation = "Broad to narrow"
                                if mapcorrelation == "447557004": mapcorrelation = "Exact match"
                                if mapcorrelation == "447558009": mapcorrelation = "Narrow to broad"
                                if mapcorrelation == "447560006": mapcorrelation = "Partial overlap"
                                if mapcorrelation == "447556008": mapcorrelation = "Not mappable"
                                if mapcorrelation == "447561005": mapcorrelation = "Not specified"
                                rule_list.append({
                                    'codesystem' : rule.target_component.codesystem_id.codesystem_title,
                                    'id' : rule.target_component.component_id,
                                    'title' : rule.target_component.component_title,
                                    'group' : rule.mapgroup,
                                    'priority' : rule.mappriority,
                                    'correlation' : mapcorrelation,
                                    'advice' : rule.mapadvice,
                                })
                            list_source.append({
                                'project' : task.project_id.title,
                                'status' : task.status.status_title,
                                'task' : task.id,
                                'source' : {
                                    'codesystem' : task.source_component.codesystem_id.codesystem_title,
                                    'id' : task.source_component.component_id,
                                    'title' : task.source_component.component_title,
                                },
                                'targets' : rule_list,
                            })
                        handled.append(task.id)

        return Response(list_source)