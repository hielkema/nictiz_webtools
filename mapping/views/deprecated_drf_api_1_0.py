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
from ..forms import *
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
    Global permission check rights to use the RC Audit functionality.
    """
    def has_permission(self, request, view):
        if 'mapping | view tasks' in request.user.groups.values_list('name', flat=True):
            return True

# Tasklis
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
                    'extra' : json.loads(task.source_component.component_extra_dict),
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
                'component_actief' : json.loads(task.source_component.component_extra_dict).get('Actief','?'),
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

# List of cached FHIR conceptmaps
class RCFHIRConceptMapList(viewsets.ViewSet):
    """
    Provides a list of cached FHIR conceptmaps.
    List = all
    Retrieve = filtered on RC foreign key id.
    """
    permission_classes = [Permission_MappingRcAudit]
    def list(self, request):
        output = []
        cache = MappingReleaseCandidateFHIRConceptMap.objects.all()
        for fhirmap in cache:
            output.append({
                'id' : fhirmap.id,
                'title' : fhirmap.title,
                'rc_id' : fhirmap.rc.id,
                'codesystem' : str(fhirmap.codesystem),
                'deprecated' : str(fhirmap.deprecated),
                'created' : str(fhirmap.created),
                'status' : fhirmap.data.get('status'),
            })
        return Response(output)
    def retrieve(self, request, pk=None):
        output = []
        cache = MappingReleaseCandidateFHIRConceptMap.objects.filter(rc__id=pk)
        for fhirmap in cache:
            output.append({
                'id' : fhirmap.id,
                'title' : fhirmap.title,
                'rc_id' : fhirmap.rc.id,
                'codesystem' : str(fhirmap.codesystem),
                'deprecated' : str(fhirmap.deprecated),
                'created' : str(fhirmap.created),
                'status' : fhirmap.data.get('status'),
            })
        return Response(output)

# FHIR conceptmap export from RC
class RCFHIRConceptMap(viewsets.ViewSet):
    """
    Export and retrieve cached release candidates FHIR JSON object to/from database.
    For retrieve, use PK
    For create, use rc_id, action='save', title, rc_notes (releasenotes)
    """
    permission_classes = [Permission_MappingRcAudit]
    def create(self, request):
        payload = request.data
        print(payload)
        # Start celery task voor creating
        GenerateFHIRConceptMap.delay(
            rc_id=payload.get('rc_id'),
            action='save',
            payload=payload
        )
        return Response(
            {'message' : 'Cache creation started'}, 
            status=status.HTTP_201_CREATED
            )

    def retrieve(self, request, pk=None):
        payload = request.data
        # Start celery task
        task = GenerateFHIRConceptMap(
            rc_id=pk,
            action='output',
            payload=payload
        )
        return Response(task)

    def list(self, request):
        cached = MappingReleaseCandidateFHIRConceptMap.objects.all().order_by('-created')
        rc_list = []
        for conceptmap in cached:
            rc_list.append({
                'id' : conceptmap.id,
                'rc_id' : conceptmap.rc.id,
                'type' : conceptmap.data.get('resourceType'),
                'experimental' : conceptmap.data.get('experimental'),
                'deprecated' : conceptmap.deprecated,
                'title' : conceptmap.title,
                'release_notes' : conceptmap.release_notes,
                'codesystem' : str(conceptmap.codesystem),
                'created' : str(conceptmap.created),
            })
        return Response(rc_list)

# Handle Rule review
class RCRuleReview(viewsets.ViewSet):
    """
    Veto and fiat functionality for RC audit view
    """
    permission_classes = [Permission_MappingRcAudit]
    def create(self, request, pk=None):
        payload = request.data
        component_id = str(payload.get('component_id'))
        rc_id = str(payload.get('rc_id'))
        action = str(payload.get('action'))

        print('Checking RC {}.'.format(rc_id))
        rc = MappingReleaseCandidate.objects.get(id=rc_id)
        print('Found RC',rc,'.')

        print("Printing first few rules")
        test_rules = MappingRule.objects.all()[:10]
        for rule in test_rules:
            print(rule, rule.source_component.component_id)

        # Identify rules in RC DB
        rules = MappingReleaseCandidateRules.objects.filter(
            static_source_component_ident = component_id,
            export_rc = rc,
        )
        print('Found {} rules for concept {} in RC {}.'.format(rules.count(), component_id, rc_id))
        for rule in rules:
            user = User.objects.get(id=request.user.id)
            if action == 'fiat':
                rule.accepted.add(user)
            elif action == 'veto':
                rule.rejected.add(user)
            rule.save()
            print('Accepted bindings for:')
            print(rule, rule.accepted.all(), rc_id, component_id, action)
            print('Rejected bindings for:')
            print(rule, rule.rejected.all(), rc_id, component_id, action)

        return Response('output')

# Handle RC lists
class ReleaseCandidates(viewsets.ViewSet):
    """
    
    """
    permission_classes = [Permission_MappingRcAudit]
    def list(self, request, pk=None):
        rc_list = MappingReleaseCandidate.objects.all().order_by('-created')
        output = []
        status_options = [
            # (code, readable)
            ['0', 'Testing'],
            ['1', 'Experimental'],
            ['2', 'Acceptance'],
            ['3', 'Production'],
        ]
        for rc in rc_list:
            status = rc.status
            for code, readable in status_options:
                status = status.replace(code, readable)
            output.append({
                'id' : rc.id,
                'title' : rc.title,
                'status' : status,
                'finished' : rc.finished,
                'created' : rc.created,
                'text' : rc.title + ' [' + str(rc.created) + ']',
            })
        return Response(output)

# Export releasecandidate rules
class exportReleaseCandidateRules(viewsets.ViewSet):
    """
    Exporteert regels vanuit de productiedatabase naar de RC database
    Stuur een POST request met het volgende format:
    {
        'rc_id' : int, # Release candidate ID in database
        'selection' : str # 'codesystem' or 'component'
        ['id'] : int, # component identifier, requiered in the case of selection == component
        ['codesystem'] : int, # required in the case of selection == component
    }
    Of een GET met een RC ID voor een lijst met rules in die RC
    """
    permission_classes = [Permission_MappingRcAudit]
    def create(self, request, pk=None):
        payload = request.data
        selection = str(payload.get('selection',None))
        rc_id = int(payload.get('rc_id',0))
        codesystem = int(payload.get('codesystem',0))
        id = int(payload.get('id',0))

        # TODO - move to celery task
        if selection == 'codesystem':
            exportCodesystemToRCRules.delay(rc_id=rc_id, user_id=request.user.id)
        elif selection == "component" and codesystem:
            def component_dump(codesystem=None, component_id=None):
                component = MappingCodesystemComponent.objects.get(component_id = component_id, codesystem_id=codesystem)
                output = {
                    'identifier'    : component.component_id,
                    'title'         : component.component_title,
                    'extra'         : json.loads(component.component_extra_dict),
                    'created'       : str(component.component_created),
                    'codesystem'    : {
                        'id'        : component.codesystem_id.id,
                        'name'      : component.codesystem_id.codesystem_title,
                        'version'   : component.codesystem_id.codesystem_version,
                        'fhir_uri'  : component.codesystem_id.codesystem_fhir_uri,
                    }
                }
                return output
            # Get all tasks for requested component - based on the identifier of the source component
            tasks = MappingTask.objects.filter(source_component__component_id = id)
            rc = MappingReleaseCandidate.objects.get(id = rc_id)
            print("Received update request for RC {rc} for component {component}. Found {numtasks} tasks.".format(rc=rc, component=id, codesystem=codesystem, numtasks=tasks.count()))
            if not tasks.count() == 1:
                print("Error: did not find exactly 1 task with the given attributes.")
            else:
                # Select the task
                task = tasks.first()
                # Find all rules in development using this source component
                rules = MappingRule.objects.filter(source_component=task.source_component)
                # Provide useful entertainment.
                print("Nice. Found exactly one task. This task has {numrules} rules associated in the development database. Continue.".format(numrules = rules.count()))
                
                # Find all rules in the RC database with these characteristics and delete them.
                rc_rules = MappingReleaseCandidateRules.objects.filter(
                    export_task = task,
                    export_rc = rc,
                    )
                rc_rules_count = rc_rules.count()
                rc_rules.delete()
                print("Found {numrules} rules in the RC database. Deleting these.".format(numrules=rc_rules_count))
                
                # Only continue if the task does not have status - rejected, otherwise skip re-adding the rules.
                if task.status == task.project_id.status_rejected:
                    print("Stop adding rules derived from now rejected task: {}".format(task.id))
                else:
                    # Loop through the rules in development, and update RC database with data from the development database
                    for rule in rules:
                        # Handle bindings / specifications / products
                        mapspecifies = []
                        for binding in rule.mapspecifies.all():
                            mapspecifies.append({
                                'id' : binding.target_component.component_id,
                                'title' : binding.target_component.component_title,
                            })
                        # Create the actual rule in the RC database
                        rc_rule = MappingReleaseCandidateRules.objects.create(
                                export_rc = rc,
                                export_user = User.objects.get(id=request.user.id),
                                export_task = task,
                                export_rule = rule,
                                task_status = task.status.status_title,
                                task_user = task.user.username,
                                source_component = rule.source_component,
                                static_source_component_ident = rule.source_component.component_id,
                                static_source_component = json.dumps(component_dump(codesystem = rule.source_component.codesystem_id.id, component_id = rule.source_component.component_id)),
                                target_component = rule.target_component,
                                static_target_component_ident = rule.target_component.component_id,
                                static_target_component = json.dumps(component_dump(codesystem = rule.target_component.codesystem_id.id, component_id = rule.target_component.component_id)),
                                mapgroup = rule.mapgroup,
                                mappriority = rule.mappriority,
                                mapcorrelation = rule.mapcorrelation,
                                mapadvice = rule.mapadvice,
                                maprule = rule.maprule,
                                mapspecifies = json.dumps(mapspecifies),
                            )
                        rc_rule.save()
                        print("Added {rule}".format(rule=rc_rule))
                rc_rules = MappingReleaseCandidateRules.objects.filter(
                    export_task = task,
                    export_rc = rc,
                    )
                print("There are now {numrules} rules in the RC database.".format(numrules=rc_rules.count()))

        return Response({
            'message' : 'Taak ontvangen',
            'selection' : selection,
            'id' : id,
        })
    def retrieve(self, request, pk=None):
        task_list = []
        id = int(pk)
        # Get RC
        rc = MappingReleaseCandidate.objects.get(id = id)
        print('Exporting RC',rc)
        # Total number of components in codesystem linked to RC
        source_codesystem = MappingCodesystemComponent.objects.filter(codesystem_id = rc.codesystem)
        # Identify all unique tasks in order to group the rules for export
        rules = MappingReleaseCandidateRules.objects.filter(export_rc = rc)
        print('Exporting',rules.count(),'rules')
        source_components = rules.order_by('static_source_component_ident').values_list('static_source_component_ident',flat=True).distinct()
        print('Found',len(source_components),'distinct source components / =tasks')
        
        # Loop through the unique source components to group all rules using this source
        for component in source_components:
            component_id = component
            # print('Handling component',component_id)
            # Get all rules using this component as source
            rule_list = []
            filtered_rule_list = []
            rejected = False
            rejected_list = []
            fiat_me = False
            veto_me = False
            accepted = None
            accepted_list = []
            ignore_list = []
            for rule in rules.filter(static_source_component_ident = component_id).order_by('mapgroup', 'mappriority'):
                mapspecifies = json.loads(rule.mapspecifies)
                # Add ID's used as binding target to ignore list: don't show twice
                for value in mapspecifies:
                    # print('Added',value.get('id'),'to ignore list')
                    ignore_list.append(value.get('id'))
                # If no specifies are mentioned; false to hide rule in table
                if len(mapspecifies) == 0:
                    mapspecifies = False
                
                correlation_options = [
                    # (code, readable)
                    ('447559001', 'Broad to narrow'),
                    ('447557004', 'Exact match'),
                    ('447558009', 'Narrow to broad'),
                    ('447560006', 'Partial overlap'),
                    ('447556008', 'Not mappable'),
                    ('447561005', 'Not specified'),
                ]
                correlation = rule.mapcorrelation
                for code, readable in correlation_options:
                    correlation = correlation.replace(code, readable)
                
                rule_list.append({
                    'from_project' : rule.export_rule.project_id.id,
                    'rule_id' : rule.export_rule.id,

                    'task_status'   : rule.task_status,
                    'task_user'     : rule.task_user,

                    'codesystem' : rule.target_component.codesystem_id.codesystem_title,
                    'target' : json.loads(rule.static_target_component),

                    'mapgroup'      : rule.mapgroup,
                    'mappriority'   : rule.mappriority,
                    'mapcorrelation': correlation,
                    'mapadvice'     : rule.mapadvice,
                    'maprule'       : rule.maprule,
                    'mapspecifies'  : mapspecifies,

                })
                # TODO - not validated yet 
                if rule.rejected.count() > 0:
                    rejected = True
                    for user in rule.rejected.values_list('username', flat=True):
                        rejected_list.append(user)
                    if request.user.username in rejected_list:
                        veto_me = True
                if rule.accepted.count() > 0:
                    accepted = True
                    for user in rule.accepted.values_list('username', flat=True):
                        accepted_list.append(user)
                    if request.user.username in accepted_list:
                        fiat_me = True
            
            # Filter -> ID not in rejected list
            for single_rule in rule_list:
                # print('IGNORE HANDLING',single_rule.get('target').get('identifier'))
                # print(ignore_list)
                if single_rule.get('target').get('identifier') in ignore_list:
                    # print('IGNORED',single_rule.get('target').get('identifier'),': rule binding in place')
                    True
                else:
                    # print("ADDED")
                    filtered_rule_list.append(single_rule)
            
            static_source_component = json.loads(rule.static_source_component)
            task_list.append({
                'status' : rule.task_status,
                'source' : static_source_component,
                'project' : rule.export_rule.project_id.title,
                'group' : static_source_component.get('extra',{}).get('Groep',''),
                'rules' : filtered_rule_list,
                'accepted_list' : set(accepted_list),
                'num_accepted' : len(set(accepted_list)),
                'accepted_me' : fiat_me,
                'rejected_list' : set(rejected_list),
                'num_rejected' : len(set(rejected_list)),
                'rejected_me' : veto_me,
                'accepted' : accepted,
                'rejected' : rejected,
            })

        status_options = [
            # (code, readable)
            ['0', 'Testing'],
            ['1', 'Experimental'],
            ['2', 'Acceptance'],
            ['3', 'Production'],
        ]
        status = rc.status
        for code, readable in status_options:
            status = status.replace(code, readable)

        return Response({
            'message' : 'Lijst met alle items voor RC',
            'rc' : {
                'id' : rc.id,
                'title' : rc.title,
                'status' : status,
                'created' : rc.created,
                'finished' : rc.finished,
                'stats' : {
                    'total_tasks'   : source_components.count(),
                    'tasks_in_rc'   : len(task_list),
                    'num_accepted'  : len(list(filter(lambda x: x['accepted'] == True, task_list))),
                    'num_rejected'  : len(list(filter(lambda x: x['rejected'] == True, task_list))),
                    'total_components' : source_codesystem.count(),
                    'perc_in_rc'    :  round(source_components.count() / source_codesystem.count() * 100),
                },
                'text' : rc.title + ' [' + str(rc.created) + ']',
            },
            'rules' : task_list,
        })