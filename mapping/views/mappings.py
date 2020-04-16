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
from rest_framework import views, status
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

class Permission_MappingProject_ChangeMappings(permissions.BasePermission):
    """
    Global permission check rights to change mappings.
    """
    def has_permission(self, request, view):
        if 'mapping | edit mapping' in request.user.groups.values_list('name', flat=True):
            return True

class MappingTargetSearch(viewsets.ViewSet):
    permission_classes = [Permission_MappingProject_ChangeMappings]

    def create(self, request):
        query = request.data.get('query').strip()
        print(request.user.username,": mappings/MappingTargetSearch : Searching for",query)

        output =[]

        # Start with the best matches: single word postgres match
        snomedComponents = MappingCodesystemComponent.objects.filter(
            Q(component_id__icontains=query) |
            Q(component_title__icontains=query)
        )
        for result in snomedComponents:
            output.append({
                'text' : f"{result.codesystem_id.codesystem_title} {result.component_id} - {result.component_title}",
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
            task = MappingTask.objects.get(id=request.data.get('task'))
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
                error = 'Exc MappingDialog/create type: {} \n TB: {}'.format(exc_type, exc_tb.tb_lineno)
                print(error)

            print('\n\n','Raw request data',request.data,'\n\n')

            print('Mapping:', request.data.get('mapping'),'\n\n')
            if request.data.get('mapping').get('id') == 'extra':
                print('Zou een nieuwe mapping moeten worden.')
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
                print('New target:', request.data.get('new'),'\n\n')
                print('User',request.user.username,': Replacing mapping',request.data.get('mapping').get('id'),'with',request.data.get('new').get('component').get('id'))
                mapping = MappingRule.objects.get(id = request.data.get('mapping').get('id'))
                new_target = MappingCodesystemComponent.objects.get(id=request.data.get('new').get('component').get('id'))
                mapping.target_component = new_target
                mapping.save()

            audit_async.delay('multiple_mapping', task.project_id.id, task.id)

            return Response(str(mapping))
        else:
            return Response('Geen toegang', status=status.HTTP_401_UNAUTHORIZED)

class MappingTargets(viewsets.ViewSet):
    permission_classes = [Permission_MappingProject_ChangeMappings]

    def create(self, request):
        task = MappingTask.objects.get(id=request.data.get('task'))
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

    def retrieve(self, request, pk=None):
        # List all events
        # TODO filter on which projects the user has access to

        task = MappingTask.objects.get(id=pk)

        if task.project_id.project_type == "1":
            mappings = MappingRule.objects.filter(project_id=task.project_id, source_component=task.source_component)
        if task.project_id.project_type == "2":
            mappings = MappingRule.objects.filter(project_id=task.project_id, source_component=task.source_component)
        elif task.project_id.project_type == "4":
            mappings = MappingRule.objects.filter(project_id=task.project_id, target_component=task.source_component)
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