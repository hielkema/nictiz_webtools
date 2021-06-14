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

# List of cached FHIR conceptmaps
class RCFHIRConceptMapList(viewsets.ViewSet):
    """
    Provides a list of cached FHIR conceptmaps.
    List = all
    Retrieve = filtered on RC foreign key id.
    """
    permission_classes = [Permission_MappingRcAudit]
    def list(self, request):
        print(f"[release_candidate/RCFHIRConceptMapList list] requested by {request.user}")
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
        print(f"[release_candidate/RCFHIRConceptMapList retrieve] requested by {request.user} - {pk}")
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
    permission_classes = [permissions.AllowAny]
    def create(self, request):
        print(f"[release_candidate/RCFHIRConceptMap create] requested by {request.user} - data: {str(request.data)[:500]}")
        payload = request.data
        print(payload)
        # Check permissions
        current_user = User.objects.get(id=request.user.id)
        rc = MappingReleaseCandidate.objects.get(id=payload.get('rc_id'), access__username=current_user)
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
        print(f"[release_candidate/RCFHIRConceptMap retrieve] requested by {request.user} - {pk}")
        payload = request.data
        # Start celery task
        task = GenerateFHIRConceptMap(
            rc_id=pk,
            action='output',
            payload=payload
        )
        return Response(task)

    def list(self, request):
        print(f"[release_candidate/RCFHIRConceptMap list] requested by {request.user}")
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
        print(f"[release_candidate/RCRuleReview create] requested by {request.user} - data: {str(request.data)[:500]}")

        payload = request.data
        component_id = str(payload.get('component_id'))
        rc_id = str(payload.get('rc_id'))
        action = str(payload.get('action'))

        print('Checking RC {}.'.format(rc_id))
        current_user = User.objects.get(id=request.user.id)
        rc = MappingReleaseCandidate.objects.get(id=rc_id, access__username=current_user)
        print('Found RC',rc,'.')

        # Only allow review on non-production RC's
        if rc.status != '3':
            # Identify rules in RC DB
            rules = MappingReleaseCandidateRules.objects.filter(
                static_source_component_ident = component_id,
                export_rc = rc,
            )
            print('Found {} rules for concept {} in RC {}.'.format(rules.count(), component_id, rc_id))
            for rule in rules:
                print(f"Handling rule {str(rule)} - {action}")
                try:
                    if action == 'fiat':
                        print("Add fiat")
                        # Add fiat
                        
                        print(f"Accepted1: {str(rule.accepted)}")
                        print(f"Rejected1: {str(rule.rejected)}")

                        _accepted = rule.accepted
                        if _accepted == None:
                            print("accepted = None")
                            _accepted = [request.user.id]
                        elif len(_accepted) == 0:
                            print("accepted = 0")
                            _accepted = [request.user.id]
                        else:
                            print("accepted = iets")
                            print(f"Accepted1.1: {list(_accepted)}")
                            _accepted.append(request.user.id)

                            rule.save()
                            print(f"Accepted1.2: {str(_accepted)}")
                        rule.accepted = list(set(_accepted))

                        # Remove veto
                        _rejected = rule.rejected
                        if _rejected == None:
                            _rejected = []
                        elif len(_rejected) == 0:
                            _rejected = []
                        else:
                            _rejected.remove(request.user.id)
                        rule.rejected = _rejected

                        print(f"Accepted2: {str(rule.accepted)}")
                        print(f"Rejected2: {str(rule.rejected)}")
                        rule.save()

                    elif action == 'veto':
                        print("Add veto")
                        if rule.rejected == None:
                            rule.rejected = [request.user.id]
                        elif len(rule.rejected) == 0:
                            rule.rejected = [request.user.id]
                        else:
                            rule.rejected = rule.rejected.append(request.user.id)

                        # Remove fiat
                        if rule.accepted == None:
                            rule.accepted = []
                        elif len(rule.accepted) == 0:
                            rule.accepted = []
                        else:
                            rule.accepted = rule.accepted.remove(request.user.id)
                        rule.save()
                except Exception as e:
                    print(e)

        return Response('output')

# Handle RC lists
class ReleaseCandidates(viewsets.ViewSet):
    """
    
    """
    permission_classes = [Permission_MappingRcAudit]
    def list(self, request, pk=None):
        print(f"[release_candidate/ReleaseCandidates list] requested by {request.user}")

        current_user = User.objects.get(id=request.user.id)
        rc_list = MappingReleaseCandidate.objects.filter(access__username=current_user).order_by('-created')
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
        print(f"[release_candidate/exportReleaseCandidateRules create] requested by {request.user} - data: {str(request.data)[:500]}")
        
        try:

            payload = request.data
            selection = str(payload.get('selection',None))
            rc_id = int(payload.get('rc_id',0))
            codesystem = int(payload.get('codesystem',0))
            id = int(payload.get('id',0))

            current_user = User.objects.get(id=request.user.id)
            rc = MappingReleaseCandidate.objects.get(id = rc_id, access__username=current_user)
            if rc:
                if selection == 'codesystem':
                    if ('mapping | audit mass pull changes' in request.user.groups.values_list('name', flat=True)) and (rc.status != '3'):
                        exportCodesystemToRCRules.delay(rc_id=rc_id, user_id=request.user.id)
                    else:
                        return Response({
                            'message' : 'Geen toegang. Geen permissies voor audit mass pull, of de status van de RC is \'productie\'.'
                        }, status=status.HTTP_401_UNAUTHORIZED)
                elif (selection == "component") and codesystem and (rc.status != '3'):
                    print('gogogo')
                    def component_dump(codesystem=None, component_id=None):
                        component = MappingCodesystemComponent.objects.get(component_id = component_id, codesystem_id=codesystem)
                        output = {
                            'identifier'    : component.component_id,
                            'title'         : component.component_title,
                            'extra'         : component.component_extra_dict,
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
                                        static_source_component = component_dump(codesystem = rule.source_component.codesystem_id.id, component_id = rule.source_component.component_id),
                                        target_component = rule.target_component,
                                        static_target_component_ident = rule.target_component.component_id,
                                        static_target_component = component_dump(codesystem = rule.target_component.codesystem_id.id, component_id = rule.target_component.component_id),
                                        mapgroup = rule.mapgroup,
                                        mappriority = rule.mappriority,
                                        mapcorrelation = rule.mapcorrelation,
                                        mapadvice = rule.mapadvice,
                                        maprule = rule.maprule,
                                        mapspecifies = mapspecifies,
                                    )
                                rc_rule.save()
                                print("Added {rule}".format(rule=rc_rule))
                        rc_rules = MappingReleaseCandidateRules.objects.filter(
                            export_task = task,
                            export_rc = rc,
                            )
                        print("There are now {numrules} rules in the RC database.".format(numrules=rc_rules.count()))

                return Response({
                    'message' : 'Taak ontvangen. De taak wordt alleen uitgevoerd als de RC niet als status \'productie\' heeft.',
                    'selection' : selection,
                    'id' : id,
                })
        except Exception as e:
            print(f"[release_candidate/exportReleaseCandidateRules create] Error: {e}")
            
    def retrieve(self, request, pk=None):
        print(f"[release_candidate/exportReleaseCandidateRules retrieve] requested by {request.user} - {pk}")
        try:
            task_list = []
            id = int(pk)
            # Get RC
            current_user = User.objects.get(id=request.user.id)
            rc = MappingReleaseCandidate.objects.get(id = id, access__username=current_user)
            print('Exporting RC',rc)
            # Total number of components in codesystem linked to RC
            source_codesystem = MappingCodesystemComponent.objects.select_related(
                'codesystem_id'
            ).filter(codesystem_id = rc.codesystem)
            # Identify all unique tasks in order to group the rules for export
            all_rules = MappingReleaseCandidateRules.objects.select_related(
                'export_rc', 
                'export_user', 
                'export_task', 
                'export_task__source_component', 
                'export_task__source_codesystem', 
                'export_rule',
                'export_rule__project_id', 
                'source_component', 
                'source_component__codesystem_id', 
                'target_component',
                'target_component__codesystem_id',
                ).filter(export_rc = rc)
            print('Exporting',all_rules.count(),'rules')
            source_components = all_rules.order_by('static_source_component_ident').values_list('static_source_component_ident',flat=True).distinct()
            print('Found',len(source_components),'distinct source components / =tasks')
            
            # Fetch all rule-related data
            rules = all_rules.order_by('mapgroup', 'mappriority').values(
                'export_rc', 
                'export_user__id', 
                'export_task__category', 
                'export_task__source_component', 
                'export_task__source_codesystem', 
                'export_rule',
                'export_rule__project_id', 
                'source_component', 
                'source_component__codesystem_id', 
                'target_component',
                'target_component__codesystem_id',
                'static_source_component', 
                'static_source_component_ident', 
                'mapspecifies',
                'mapcorrelation',
                'export_rule__id',
                'export_rule__project_id__title',
                'export_rule__project_id__id',
                'export_task__id',
                'task_user',
                'task_status',
                'target_component__codesystem_id__codesystem_title',
                'static_target_component',
                'mapgroup',
                'mappriority',
                'mapadvice',
                'maprule',
                'accepted',
                'rejected',
            )


            # Fetch all users and groups
            userdata = User.objects.all().values('id', 'username', 'groups__name')

            # Fetch all audit hits (ignore == False)
            all_audit_hits = MappingTaskAudit.objects.filter(ignore = False).values(
                'id',
                'audit_type',
                'task__id',
                'hit_reason',
                'comment',
                'ignore',
                'sticky',
                'ignore_user',
                'first_hit_time',
            )

            # print(source_components)
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

            # .filter(static_source_component_ident = component_id)
                # print(f"[[***]] -> {component_id}")
                _rules = list(filter(lambda x: (x['static_source_component_ident'] == component_id), rules))
                for rule in _rules:
                    # print(rule)
                    mapspecifies = rule.get('mapspecifies')
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
                    correlation = rule.get('mapcorrelation')
                    for code, readable in correlation_options:
                        try:
                            correlation = correlation.replace(code, readable)
                        except:
                            continue
                    
                    # Handle foreign keys that could have been removed
                    try:
                        from_project = rule.get('export_rule__project_id__id')
                    except:
                        from_project = '[deleted]'
                    try:
                        rule_id = rule.get('export_rule__id')
                    except:
                        rule_id = '[deleted]'

                    try:
                        export_task_id = rule.get('export_task__id')
                    except:
                        export_task_id = '[deleted]'

                    try:
                        export_task_category = rule.get('export_task__category')
                    except:
                        export_task_category = '[deleted]'


                    rule_list.append({
                        'from_project' : from_project,
                        'rule_id' : rule_id,

                        'task_status'   : rule.get('task_status'),
                        'task_user'     : rule.get('task_user'),

                        'codesystem'    : rule.get('target_component__codesystem_id__codesystem_title'),
                        'target'        : rule.get('static_target_component'),

                        'mapgroup'      : rule.get('mapgroup'),
                        'mappriority'   : rule.get('mappriority'),
                        'mapcorrelation': correlation,
                        'mapadvice'     : rule.get('mapadvice'),
                        'maprule'       : rule.get('maprule'),
                        'mapspecifies'  : mapspecifies,

                    })
                    # TODO - not validated yet 
                    accepted_nvmm   = False
                    accepted_nvkc   = False
                    accepted_nictiz = False
                    accepted_nhg    = False
                    accepted_palga  = False
                    if (rule.get('accepted') != None) and (len(rule.get('accepted')) > 0):
                        # Fetch user groups
                        accepted_groups = list(filter(lambda x: (x['id'] in rule.get('accepted')), userdata))
                        accepted_groups = set([x['groups__name'] for x in accepted_groups])
                        if 'groepen | nictiz' in accepted_groups:
                            accepted_nictiz = True
                        if 'groepen | palga' in accepted_groups:
                            accepted_palga = True
                        if 'groepen | nhg' in accepted_groups:
                            accepted_nhg = True
                        if 'groepen | nvmm' in accepted_groups:
                            accepted_nvmm = True
                        if 'groepen | nvkc' in accepted_groups:
                            accepted_nvkc = True

                    if (rule.get('rejected') != None) and (len(rule.get('rejected')) > 0):
                        rejected = True
                        for userid in rule.get('rejected'):
                            _userdata = list(filter(lambda x: (x['id'] == userid), userdata))[0]
                            rejected_list.append(_userdata['username'])
                        if request.user.id in rule.get('rejected'):
                            veto_me = True
                    if (rule.get('accepted') != None) and (len(rule.get('accepted')) > 0):
                        accepted = True
                        for userid in rule.get('accepted'):
                            _userdata = list(filter(lambda x: (x['id'] == userid), userdata))[0]
                            accepted_list.append(_userdata['username'])
                        if request.user.id in rule.get('accepted'):
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
                

                # Handle foreign key info that might be deleted in dev path
                try:
                    project_title = rule.get('export_rule__project_id__title')
                    project_id = rule.get('export_rule__project_id__id')
                except:
                    project_title = '[unknown]'
                    project_id = '[unknown]'
                static_source_component = rule.get('static_source_component')

                # Add audit hits
                audit_hits = list(filter(lambda x: (x['task__id'] == rule.get('export_task__id')), all_audit_hits))
                audits = []
                audits_present = False
                for audit in audit_hits:
                    audits.append({
                        'id':audit.get('id'),
                        'type':audit.get('audit_type'),
                        'reason':audit.get('hit_reason'),
                        'ignore':audit.get('ignore'),
                        'sticky':audit.get('sticky'),
                        'timestamp':audit.get('first_hit_time'),
                    })
                    audits_present = True

                task_list.append({
                    'status' : rule.get('task_status'),
                    'source' : static_source_component,
                    'source_title' : static_source_component.get('title',None),
                    'task_id': export_task_id,
                    'task_category' : export_task_category,
                    'project' : project_title,
                    'project_id' : project_id,

                    # Extra data for filtering
                    'group' : static_source_component.get('extra',{}).get('Groep',None),
                    'class' : static_source_component.get('extra',{}).get('Klasse',None),

                    'rules' : filtered_rule_list,

                    'audit' : audits,
                    'audit_present' : audits_present,

                    'accepted_list' : ", ".join(set(accepted_list)),
                    'num_accepted' : len(set(accepted_list)),
                    'accepted_me' : fiat_me,
                    'rejected_list' : ", ".join(set(rejected_list)),
                    'num_rejected' : len(set(rejected_list)),
                    'rejected_me' : veto_me,
                    'accepted' : accepted,
                    'rejected' : rejected,

                    'accepted_nvmm'     : accepted_nvmm,
                    'accepted_nvkc'     : accepted_nvkc,
                    'accepted_nictiz'   : accepted_nictiz,
                    'accepted_nhg'      : accepted_nhg,
                    'accepted_palga'    : accepted_palga,
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
                try:
                    status = status.replace(code, readable)
                except:
                    continue

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
        except Exception as e:
            print("[release_candidate/exportReleaseCandidateRules retrieve] ERROR: ", e)


class exportReleaseCandidateRulesV2(viewsets.ViewSet):
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
            
    def retrieve(self, request, pk=None):
        print(f"[release_candidate/exportReleaseCandidateRulesV2 retrieve] requested by {request.user} - {pk}")
        
        task_list = []
        id = int(pk)
        # Get RC
        current_user = User.objects.get(id=request.user.id)
        rc = MappingReleaseCandidate.objects.select_related(
            'codesystem'
        ).get(id = id, access__username=current_user)
        
        ## DEBUG RULE - REMOVE FOR PRODUCTION
        print('Exporting RC',rc)
        
        # Total number of components in codesystem linked to RC
        source_codesystem = MappingCodesystemComponent.objects.select_related(
            'codesystem_id'
        ).filter(codesystem_id = rc.codesystem)
        
        # Fetch users and their groups


        # Fetch all rules from the database
        db_rules = MappingReleaseCandidateRules.objects.filter(export_rc = rc).select_related(
            'export_rc', 
            'export_user', 
            'export_task',
            'export_task__source_component', 
            'export_task__source_codesystem', 
            'export_rule',
            'export_rule__project_id', 
            'source_component', 
            'source_component__codesystem_id', 
            'target_component',
            'target_component__codesystem_id',
            ).prefetch_related(
                # 'accepted',
                # 'accepted__groups',
                # 'rejected',
                # 'rejected__groups',
            )
        
        ## DEBUG RULE - REMOVE FOR PRODUCTION
        print('Exporting',db_rules.count(),'rules')
        
        # rules = list(db_rules.values())
        rules = db_rules
        db_rules_list = db_rules.values(
            'id',
            'static_source_component_ident',
            'mapspecifies',
            'mapcorrelation',
            'mappriority',
            'mapadvice',
            'mapgroup',
            'maprule',
            'export_rc',
            'export_date',
            'export_user',
            'export_task',
            'export_rule',
            'task_status',
            'task_user',
            'source_component',
            'static_source_component_ident',
            'static_source_component',
            'target_component',
            'static_target_component_ident',
            'static_target_component',
            'accepted', 
            # 'accepted__groups', 
            'rejected',
            # 'rejected__groups',
            )
        # Get unique source component ID's
        source_components = list()
        for rule in rules:
            source_components.append(rule.static_source_component_ident)
        source_components = sorted(set(source_components))

        task_list = list()

        # Loop over all unique source component_id's - we assume each unique component is a task
        for source_component_ident in source_components[:25]:
            ## DEBUG RULE - REMOVE FOR PRODUCTION
            print("Handling",source_component_ident)

            rule_list = []
            filtered_rule_list = []
            rejected = False
            rejected_list = []
            fiat_me = False
            veto_me = False
            accepted = None
            accepted_list = []
            ignore_list = []

            # Get all items from the rules dictionary where 'source_component' is the same
            _rules = list(filter(lambda x: x['static_source_component_ident'] == source_component_ident, db_rules_list))
            print(_rules)
            for _rule in _rules: 
                ## DEBUG RULE - REMOVE FOR PRODUCTION
                print("Rule:",_rule['export_rule'])
                
                # Add ID's used as binding target to ignore list: don't show twice
                mapspecifies = _rule['mapspecifies']
                for value in mapspecifies:
                    # print('Added',value.get('id'),'to ignore list')
                    ignore_list.append(value.get('id'))
                # If no specifies are mentioned; false to hide rule in table
                if len(mapspecifies) == 0:
                    mapspecifies = False

                # Translate correlation options
                correlation_options = [
                    # (code, readable)
                    ('447559001', 'Broad to narrow'),
                    ('447557004', 'Exact match'),
                    ('447558009', 'Narrow to broad'),
                    ('447560006', 'Partial overlap'),
                    ('447556008', 'Not mappable'),
                    ('447561005', 'Not specified'),
                ]
                correlation = _rule['mapcorrelation']
                for code, readable in correlation_options:
                    mapcorrelation = _rule['mapcorrelation'].replace(code, readable)

                # Handle foreign keys that could have been removed in dev path
                try:
                    rule_id = _rule['export_rule']
                except:
                    rule_id = '[deleted]'

                try:
                    export_task_id = _rule['export_task']
                except:
                    export_task_id = '[deleted]'


                # TO BE FIXED - results in many extra queries due to many-many relationships
                # current_rule = db_rules.get(id=_rule['id'])
                current_rule = list(filter(lambda x: x['id'] == _rule['id'], db_rules_list))[0]
                accepted_nvmm   = False
                accepted_nvkc   = False
                accepted_nictiz = False
                accepted_nhg    = False
                accepted_palga  = False

                print("CURRENT_RULE: ", current_rule)

                # if (type(current_rule['accepted']) == list) and (len(current_rule['accepted']) > 0):
                #     print("ACCEPTED: ", current_rule['accepted'])
                    
                #     if 'groepen | nictiz' in current_rule.accepted.values_list('groups__name', flat=True):
                #         accepted_nictiz = True
                #     if 'groepen | palga' in current_rule.accepted.values_list('groups__name', flat=True):
                #         accepted_palga = True
                #     if 'groepen | nhg' in current_rule.accepted.values_list('groups__name', flat=True):
                #         accepted_nhg = True
                #     if 'groepen | nvmm' in current_rule.accepted.values_list('groups__name', flat=True):
                #         accepted_nvmm = True
                #     if 'groepen | nvkc' in current_rule.accepted.values_list('groups__name', flat=True):
                #         accepted_nvkc = True
                #     if current_rule.accepted.count() > 0:
                #         accepted = True
                #         for user in current_rule.accepted.values_list('username', flat=True):
                #             accepted_list.append(user)
                #         if request.user.username in accepted_list:
                #             fiat_me = True
                # if current_rule.rejected.count() > 0:
                #     rejected = True
                #     for user in current_rule.rejected.values_list('username', flat=True):
                #         rejected_list.append(user)
                #     if request.user.username in rejected_list:
                #         veto_me = True
                



                rule_list.append({
                    'rule_id'       : rule_id,
                    'task_id'       : export_task_id,

                    'task_status'   : _rule['task_status'],
                    'task_user'     : _rule['task_user'],

                    'codesystem'    : _rule['static_target_component']['codesystem']['name'],
                    'target'        : _rule['static_target_component'],

                    'mapgroup'      : _rule['mapgroup'],
                    'mappriority'   : _rule['mappriority'],
                    'mapcorrelation': correlation,
                    'mapadvice'     : _rule['mapadvice'],
                    'maprule'       : _rule['maprule'],
                    'mapspecifies'  : mapspecifies,

                    'rejected_me' : veto_me,
                    'accepted' : accepted,
                    'rejected' : rejected,

                    # 'accepted_nvmm'     : accepted_nvmm,
                    # 'accepted_nvkc'     : accepted_nvkc,
                    # 'accepted_nictiz'   : accepted_nictiz,
                    # 'accepted_nhg'      : accepted_nhg,
                    # 'accepted_palga'    : accepted_palga,

                    'raw' : _rule,
                })

                # Filter -> ID not in rejected list
                for single_rule in rule_list:
                    if single_rule.get('target').get('identifier') in ignore_list:
                        True
                    else:
                        filtered_rule_list.append(single_rule)

            task_list.append({
                'source' : source_component_ident,
                'targets' : filtered_rule_list,
            })
            


        # Task list for export
        # task_list = source_components

        return Response({
            'message' : 'Lijst met alle items voor RC',
            # 'stats' : {
            #     'num_tasks': num_tasks,
            # },
            'rules' : task_list,
        })