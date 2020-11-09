from django.shortcuts import render

# Create your views here.

# howdy/views.py
from django.shortcuts import render, redirect
from django.views.generic import TemplateView
from django.conf import settings
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from django.template.defaultfilters import linebreaksbr
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin, UserPassesTestMixin
from urllib.request import urlopen, Request
import urllib.parse
from django.contrib.postgres.search import SearchQuery, SearchVector, SearchRank
from django.db.models import Q
from django.db.models.functions import Trunc, TruncMonth, TruncYear, TruncDay
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Max
import json
# from .forms import *
from .models import *
from mapping.models import *
from datetime import datetime, timedelta
from django.utils import timezone
import pytz
from .tasks import *
import time
import environ

from rest_framework import viewsets
from .serializers import *
from rest_framework import views
from rest_framework.response import Response
from rest_framework import permissions

from snowstorm_client import Snowstorm

# Import environment variables
env = environ.Env(DEBUG=(bool, False))
# reading .env file
environ.Env.read_env(env.str('ENV_PATH', '.env'))

class Permission_TermspaceProgressReport(permissions.BasePermission):
    """
    Global permission check rights to use the RC Audit functionality.
    """
    def has_permission(self, request, view):
        if 'termspace | termspace progress' in request.user.groups.values_list('name', flat=True):
            return True

# Search termspace comments
class searchTermspaceComments(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]
    def retrieve(self, request, pk=None):
        term = str(pk)
        print(request)
        # Get results for searchterm        
        query = None ## Query to search for every search term
        terms = term.split(' ')
        print('Searching for:',term)
        for term in terms:
            or_query = None ## Query to search for a given term in each field
            for field_name in ['comment', 'assignee', 'folder', 'concept']:
                q = Q(**{"%s__icontains" % field_name: term})
                if or_query is None:
                    or_query = q
                else:
                    or_query = or_query | q
            if query is None:
                query = or_query
            else:
                query = query & or_query

        comments_found = TermspaceComments.objects.filter(query)
        print(query)
        results = []
        if comments_found.count() == 0:
            print('Geen resultaten')
        for comment in comments_found:
            results.append({
                'id' : comment.concept,
                'time' : comment.time,
                'author' : comment.assignee,
                'folder' : comment.folder,
                'status' : comment.status,
                'comment' : comment.comment,
                'fsn' : comment.fsn,
            })

        sep = " "
        context = {
            'searchterm' : sep.join(terms),
            'num_results' : len(results),
            'results': results,
        }
        return Response(context)

class searchMappingComments(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]
    def retrieve(self, request, pk=None):
        term = str(pk)
        print(request)
        # Get results for searchterm        
        query = None ## Query to search for every search term
        terms = term.split(' ')
        print('Searching for:',term)
        for term in terms:
            or_query = None ## Query to search for a given term in each field
            for field_name in ['comment_body', 'comment_task__id']:
                q = Q(**{"%s__icontains" % field_name: term})
                if or_query is None:
                    or_query = q
                else:
                    or_query = or_query | q
            if query is None:
                query = or_query
            else:
                query = query & or_query

        comments_found = MappingComment.objects.filter(query).order_by('comment_created')
        print(query)
        results = []
        if comments_found.count() == 0:
            print('Geen resultaten')
        for comment in comments_found:
            results.append({
                'comment_id' : comment.id,
                'task_id' : comment.comment_task.id,
                'status' : comment.comment_task.status.status_title,
                'project' : comment.comment_task.project_id.title,
                'project_id' : comment.comment_task.project_id.id,
                'codesystem' : comment.comment_task.source_component.codesystem_id.codesystem_title,
                'component_id' : comment.comment_task.source_component.component_id,
                'component_title' : comment.comment_task.source_component.component_title,
                'user' : comment.comment_user.username,
                'comment' : comment.comment_body,
                'time' : comment.comment_created,
            })

        sep = " "
        context = {
            'searchterm' : sep.join(terms),
            'num_results' : len(results),
            'results': results,
        }
        return Response(context)

# Snomed component endpoint
class componentApi(viewsets.ViewSet):
    permission_classes = [permissions.AllowAny]
    def list(self, request):
        # clinicalFinding = MappingCodesystemComponent.objects.get(component_id='404684003')
        # clinicalFinding_list = json.loads(clinicalFinding.descendants)
        # snomed = MappingCodesystem.objects.get(id=1)
        # query = MappingCodesystemComponent.objects.filter(codesystem_id=snomed, component_id__in=clinicalFinding_list)

        snomed = MappingCodesystem.objects.get(id=1)
        query = MappingCodesystemComponent.objects.filter(codesystem_id=snomed)
        results = MappingComponentSerializer(query, many=True).data
        return Response(results)
    def retrieve(self, request, pk=None):
        snomed = MappingCodesystem.objects.get(id=1)
        query = MappingCodesystemComponent.objects.filter(codesystem_id=snomed, component_id=pk)
        results = MappingComponentSerializer(query, many=True).data
        return Response(results)
    def create(self, request):
        return Response({
            'error' : 'Not allowed'
        })
        # MethodNotAllowed(method, detail=None, code=None)

# SNOMED Ancestor list
class cached_results(viewsets.ViewSet):
    permission_classes = [permissions.AllowAny]
    def list(self, request):
        cached = cachedResults.objects.all()
        output = []
        for cache in cached:
            output.append({
                'id' : cache.id,
                'title' : cache.title,
                'finished' : cache.finished,
            })
        return Response(output)

    def retrieve(self, request, pk=None):
        try:
            obj = cachedResults.objects.get(id=pk)
            
            data = {
                'id' : obj.id,
                'time' : obj.time,
                'title' : obj.title,
                'finished' : obj.finished,
                'data' : obj.data,
            }
            return Response(data)
        except Exception as e:
            return Response(e)
    def create(self, request):
        return Response({
            'error' : 'Not allowed'
        })
        # MethodNotAllowed(method, detail=None, code=None)

# ECL query results
class eclQueryApi(viewsets.ViewSet):
    permission_classes = [permissions.AllowAny]
    def list(self, request):
        query = EclQueryResults.objects.filter()
        results = EclQueryResultsSerializer(query, many=True).data
        return Response(results)
    def retrieve(self, request, pk=None):
        query = EclQueryResults.objects.filter(component_id=pk)
        results = EclQueryResultsSerializer(query, many=True).data
        return Response(results)
    def create(self, request):
        snowstorm = Snowstorm(
            # baseUrl="https://snowstorm.test-nictiz.nl",
            baseUrl="https://snowstorm.ihtsdotools.org/snowstorm/snomed-ct",
            debug=True,
            preferredLanguage="nl",
            defaultBranchPath="MAIN/SNOMEDCT-NL",
        )
        payload = request.data
        title = payload.get('title')
        ecl_query = payload.get('query')

        print("ECL query received: POST: {}\n Title {}\nQuery:{}".format(payload, title, ecl_query))
        
        # Get or create based on 2 criteria (fsn & codesystem)
        obj, created = EclQueryResults.objects.get_or_create(
            component_id=str(time.time()).replace(".",""),
            component_title=title,
        )
        # Add data not used for matching
        current_user = User.objects.get(id=request.user.id)
        extra = {
            'Query' : str(ecl_query),
            'UserID': current_user.id,
            'User'  : current_user.username,
        }
        obj.component_extra_dict = extra
        # obj.parents     = json.dumps(list(snowstorm.findConcepts(ecl='>!'+ecl_query)))
        # obj.children    = json.dumps(list(snowstorm.findConcepts(ecl='<!'+ecl_query)))
        obj.descendants = json.dumps(list(snowstorm.findConcepts(ecl=ecl_query)))
        # obj.ancestors   = json.dumps(list(snowstorm.findConcepts(ecl='>>'+ecl_query)))
        obj.save()

        query = EclQueryResults.objects.filter(component_id=obj.component_id)
        results = EclQueryResultsSerializer(query, many=True).data
        return Response(results)
        # MethodNotAllowed(method, detail=None, code=None)

class SnomedJSONTree(viewsets.ViewSet):
    permission_classes = [permissions.AllowAny]
    def retrieve(self, request, pk=None):
        # def list_children(focus):
        #     component = MappingCodesystemComponent.objects.get(component_id=focus)
            
        #     _children = []
        #     if component.children != None:
        #         for child in list(json.loads(component.children)):
        #             _children.append(list_children(child))
           
        #     output = {
        #         'id' : focus,
        #         'name' : component.component_id+' - '+component.component_title,
        #         'component_id' : component.component_id,
        #         'children' : _children
        #     }
            
        #     return(output)

        # print('Get tree for',str(pk))
        # children_list = [list_children(pk)]

        payload = pk.split('**')
        conceptid = payload[0]
        refset = payload[1]
        print(conceptid, refset)

        finished_tasks = SnomedTree.objects.filter(title = str(pk), finished = True)
        if finished_tasks.count() > 0:
            tree = finished_tasks.last()
            return Response({
                'message' : 'loaded',
                'data': tree.data
            })
        else:
            tree = SnomedTree.objects.filter(title = str(pk))
            if tree.count() == 0:
                if MappingCodesystemComponent.objects.filter(component_id = conceptid).count() == 1:
                    current_user = User.objects.get(id=request.user.id)
                    obj = SnomedTree.objects.create(
                        user = current_user,
                        title = str(pk),
                    )

                    
                    generate_snomed_tree.delay({
                        'db_id' : obj.id,
                        'conceptid' : conceptid,
                        'refset' : refset,
                    })

                    return Response({
                        'message': 'dispatched',
                        'data': {},
                    })
                else:
                    return Response({
                        'message': 'error: nonexistant SCTID',
                        'data': {},
                    })
            else:
                return Response({
                        'message': 'running',
                        'data': {},
                    })

class Mapping_Progressreport_perStatus(viewsets.ViewSet):
    permission_classes = [permissions.AllowAny]
    def retrieve(self, request, pk=None):
        output = []


        print('Received request for progress report')
        if str(request.GET.get('secret')) != str(env('mapping_api_secret')):
            print('Incorrect or absent secret')
            return Response('error')
        else:
            progressReports = MappingProgressRecord.objects.filter(project_id=pk, name='TasksPerStatus').last()
            status_list =[]
            statuses = json.loads(progressReports.values)
            for item in statuses:
                status_list.append(item)

            output.append({
                'Project' : progressReports.project.title,
                'Time' : progressReports.time,
                'Progress' : status_list,
            })
            # Return Json response
            return Response(output)

class Mapping_Progressreport_perProject(viewsets.ViewSet):
    permission_classes = [permissions.AllowAny]
    def retrieve(self, request, pk=None):
        output = []

        print('Received request for progress report per project')
        if str(request.GET.get('secret')) != str(env('mapping_api_secret')):
            print('Incorrect or absent secret')
            return Response('error')
        else:
            codesystem  = MappingCodesystem.objects.get(id=pk)
            components  = MappingCodesystemComponent.objects.filter(codesystem_id=codesystem).select_related(
                'codesystem_id'
            )
            # projects    = MappingProject.objects.all()

            print('Received request for codesystem',codesystem.codesystem_title)
            if str(request.GET.get('secret')) != str(env('mapping_api_secret')):
                print('Incorrect or absent secret')
                return Response('error')
            else:
                for component in components:
                    tasks = MappingTask.objects.filter(source_component = component).select_related(
                        'project_id',
                        'status',
                        'user',
                    )
                    extra = component.component_extra_dict
                    aub = extra.get('Aanvraag/Uitslag/Beide')
                    if aub == 'A': aub="Aanvraag"
                    if aub == 'B': aub="Aanvraag en uitslag"
                    if aub == 'U': aub="Uitslag"

                    if tasks.exists():
                        for task in tasks:
                            if task.project_id.project_type == "1": task_type = 'Source'
                            if task.project_id.project_type == "2": task_type = 'Target'
                            if task.project_id.project_type == "3": task_type = '?'
                            if task.project_id.project_type == "4": task_type = 'Target'

                            try:
                                user = task.user.username
                            except:
                                user = None

                            output.append({
                                'id' : component.component_id,
                                'codesystem' : component.codesystem_id.codesystem_title,
                                'extra' : extra,
                                'group' : extra.get('Groep'),
                                'AUB' : aub,
                                'actief' : extra.get('Actief'),
                                'soort' : extra.get('Soort'),
                                'title' : component.component_title,
                                'aantal taken' : tasks.count(),
                                'project' : task.project_id.title,
                                'source or target' : task_type,
                                'category' : task.category,
                                'status' : task.status.status_title,
                                'user' : user,
                            })
                    else:
                        output.append({
                                'id' : component.component_id,
                                'codesystem' : component.codesystem_id.codesystem_title,
                                'extra' : extra,
                                'group' : extra.get('Groep'),
                                'AUB' : aub,
                                'actief' : extra.get('Actief'),
                                'soort' : extra.get('Soort'),
                                'title' : component.component_title,
                                'aantal taken' : tasks.count(),
                                'project' : None,
                                'source or target' : None,
                                'category' : None,
                                'status' : None,
                                'user' : None,
                            })

                # Return Json response
                return Response(output)

class Mapping_Progressreport_overTime(viewsets.ViewSet):
    permission_classes = [permissions.AllowAny]
    def list(self, request, pk=None):
        output = []

        completed_tasks = 0
        all_tasks = 0

        print('Received request for progress report over time')
        if str(request.GET.get('secret')) != str(env('mapping_api_secret')):
            print('Incorrect or absent secret')
            return Response('error')
        else:
            projects = MappingProject.objects.all()
            tasks = MappingTask.objects.all()
            daily_report = {}

            ### INFO - select or exclude projects to include in output here
            records = MappingProgressRecord.objects.filter(name="TasksPerStatus").exclude(project__id = 6)
            for record in records:
                project = MappingProject.objects.get(id=record.project.id)
                date = record.time
                date = date.strftime("%Y-%m-%d")

                if not daily_report.get(str(date), False):
                    daily_report[str(date)] = {
                        "complete" : 0,
                        "Nieuw" : 0,
                        "NHG review" : 0,
                        "total" : 0,
                    }

                for item in json.loads(record.values):
                    if item.get('status') != str(project.status_rejected.status_title):
                        daily_report[str(date)]['total'] += item.get('num_tasks')
                    if item.get('status') == "Nieuw":
                        daily_report[str(date)]['Nieuw'] += item.get('num_tasks')
                    if item.get('status') == "NHG review":
                        daily_report[str(date)]['NHG review'] += item.get('num_tasks')
                    if item.get('status') == project.status_complete.status_title:
                        daily_report[str(date)]['complete'] += item.get('num_tasks')
                        completed_tasks += item.get('num_tasks')

                    # for key, value in item.items():
                    #     print("*",key, value)
                    #     if key == "NHG review":
                    #         print(value)
                    #         daily_report[str(date)]['NHG review'] += value
                    #     if key != str(project.status_rejected.status_title):
                    #         if key == "num_tasks":
                    #             daily_report[str(date)]['total'] += value
                    #         if key == project.status_complete.status_title:
                    #             daily_report[str(date)]['complete'] += value


            # Return Json response
            return Response({
                "reports":daily_report,
                "completed":completed_tasks,
            })

class jsonMappingExport(viewsets.ViewSet):

    #### TODO : Alle concepten van een codesystem loopen. Output voor ieder element per project bepalen?
    # dan kan een hele NHG tabel in 1x geëxporteerd worden, anders moet je per project eigen regels bepalen.

    """
    Draft for exporting FHIR ConceptMap.
    Currently only valid for codesystem NHG Diagnostische Bepalingen [4]
    -> /termspace/mapping_json/4/
    Will currently only export the first 10 mapping rules from each project with an export format
    """
    permission_classes = [permissions.IsAuthenticated]
    def list(self, request, pk=None):
        conceptmap = []
        # Return Json response
        return Response({
            "codesystems" : conceptmap
        })
    def retrieve(self, request, pk=None):
        #### Export metadata - TODO move to model?
        if int(pk) == 4: # NHG diagn -> labcodeset
            metadata = {
                'id' : "nhg-tabel-45-to-labcodeset",
                'name' : "NHG Tabel 45 naar Nederlandse Labcodeset",
                'description' : "FHIR ConceptMap NHG -> Labcodeset + SNOMED",
                'date' : str(time.time()),
                'copyright' : "Nictiz - NHG - NVMM - NVKC",
            }
        else:
            metadata = {}

        codesystem = MappingCodesystem.objects.get(id=pk)
        elements = []
        error = []
        groups = []
        correlation_options = [
            # [code, readable]
            ['447559001', 'Broad to narrow'],
            ['447557004', 'Exact match'],
            ['447558009', 'Narrow to broad'],
            ['447560006', 'Partial overlap'],
            ['447556008', 'Not mappable'],
            ['447561005', 'Not specified'],
        ]

        # Find mapping tasks
        tasks = MappingTask.objects.filter(source_component__codesystem_id = codesystem)
        # Find projects
        projects = MappingProject.objects.all()
        # Loop through all projects
        for project in projects:
            # Find all tasks in the current project
            tasks_in_project = tasks.filter(project_id__id = project.id)
            # Filter out rejected tasks
            # TODO - Eventually this should be changed to only including completed tasks
            tasks_in_project = tasks_in_project.exclude(status = project.status_rejected)

            #### FHIR ConceptMap rules for NHG tabel 45 Diagnostische Bepalingen
            if project.id == 3:
                #### START project TBL 45 -> LOINC
                for task in tasks_in_project:
                    targets = []
                    product_list = []
                    ##### Find mapping rules using the source component of the task as source, part of this project
                    rules = MappingRule.objects.filter(source_component = task.source_component, project_id = project)

                    ##### Loop through rules, excluding rules pointing to Snomed
                    for rule in rules.exclude(target_component__codesystem_id = 1):
                        # Replace Snomed equivalence code with readable text
                        equivalence = rule.mapcorrelation
                        for code, readable in correlation_options:
                            equivalence = equivalence.replace(code, readable)

                        # Add mapspecifies targets to product list (known as rule binding in GUI)
                        product_list = []
                        for product in rule.mapspecifies.all():
                            product_list.append({
                                "property" : "http://snomed.info/id/"+product.target_component.component_id+"/",
                                "system" : product.target_component.codesystem_id.codesystem_fhir_uri,
                                "code" : product.target_component.component_id,
                                "display" : product.target_component.component_title,
                            })

                        # Append mapping target to target list
                        targets.append({
                            "code" : rule.target_component.component_id,
                            "display" : rule.target_component.component_title,
                            "equivalence" : equivalence,
                            "comment" : rule.mapadvice,
                            "product" : product_list,
                        })

                    # Append element to element list
                    elements.append({
                        "DEBUG.task.id" : task.id,
                        "DEBUG.task.status" : task.status.status_title,
                        "code" : task.source_component.component_id,
                        "display" : task.source_component.component_title,
                        "target" : targets,
                    })
                # Add all elements from current project to one group
                source = MappingCodesystem.objects.get(id=4) # NHG
                target = MappingCodesystem.objects.get(id=3) # labcodeset
                groups.append({
                    "DEBUG.project.title" : project.title,
                    "source" : source.codesystem_fhir_uri,
                    "sourceVersion" : source.codesystem_version,
                    "target" : target.codesystem_fhir_uri,
                    "targetVersion" : target.codesystem_version,
                    "element" : elements,
                    "unmapped" : [] # TODO
                })
                ##### END project TBL 45 -> LOINC

        #### START output for all groups
        return Response({
            "DEBUG.errors" : error,

            "resourceType" : "ConceptMap",
            "url" : "https://termservice.test-nictiz.nl/termspace/mapping_json/"+pk+"/",
            
            "id" : metadata.get('id'),
            "name" : metadata.get('name'),
            "description" : metadata.get('description'),
            
            "version" : "developmentPath",
            "status" : "developmentPath",
            "experimental" : True,

            "date" : metadata.get('date'),
            "publisher" : "Nictiz",
            "contact" : {
                "telecom" : [
                    {
                        "system" : "url",
                        "name" : "https://www.nictiz.nl",
                    }
                ]
            },
            "copyright" : metadata.get('copyright'),
            "sourceCanonical" : codesystem.codesystem_fhir_uri,

            "group" : groups,
        })

class fetch_termspace_tasksupply(viewsets.ViewSet):
    """
    Fetches terms from termspace.
    """
    permission_classes = [Permission_TermspaceProgressReport]
    def list(self, request, pk=None):
        # Get list of unique titles
        titles = TermspaceProgressReport.objects.all().values_list('title', flat=True)
        for title in titles:
            # Selects last time_stamp for each day
            last_entries = (TermspaceProgressReport.objects
                .filter(title = title)
                .annotate(tx_day=TruncDay('time'))
                .values('tx_day')
                .annotate(last_entry=Max('time'))
                .values_list('last_entry', flat=True))
            # Add queries, also filter on last 20 days
            last_month = datetime.today() - timedelta(days=20)
            try:
                query = query | TermspaceProgressReport.objects.filter(
                    time__in=last_entries,
                ).filter(time__gte=last_month)
            except:
                query = TermspaceProgressReport.objects.filter(
                    time__in=last_entries,
                ).filter(time__gte=last_month)
        # Return entire queryset
        output = []

        for day in query.annotate(tx_day=TruncDay('time')).distinct('tx_day'):
            # print(day.tx_day)
            
            day_query = query.filter(time__day=day.time.day, time__month=day.time.month, time__year=day.time.year)

            # Create dict to add to the list of days
            _output = {'date' : day.tx_day.strftime('%Y-%m-%d')}
            # For each unique title, query the database and add the relevant count
            for title in query.distinct('title'):
                try:
                    _query = day_query.get(title=title.title).count
                except ObjectDoesNotExist:
                    _query = None
                _output.update({ title.tag :  _query})

            output.append(_output)

        # Get legends to show on site        
        legend = []
        for item in query.distinct('description'):
            legend.append({
                'tag' : item.tag,
                'title' : item.title,
                'description' : item.description,
            })

        return Response({
            'progress' : output,
            'legend' : legend,
        })

    def create(self, request, pk=None):
        output = []
        
        return Response(output)

class fetch_termspace_user_tasksupply(viewsets.ViewSet):
    """
    Fetches tasks from termspace, per user.
    """
    permission_classes = [Permission_TermspaceProgressReport]
    def retrieve(self, request, pk=None):
        print(f"[fetch_termspace_user_tasksupply] Starting view fetch_termspace_user_tasksupply with pk={pk}")
        output = []
        categories = []
        last_month = timezone.now() - timedelta(days=30)
        reports = TermspaceUserReport.objects.filter(time__gte=last_month)
        print(f"[fetch_termspace_user_tasksupply] Found {reports.count()} reports.")

        if pk == 'all':
            statuses = reports.distinct('status').values_list('status', flat=True)
        else:
            statuses = [str(pk)]
        
        users = reports.distinct('username').values_list('username', flat=True)

        for user in users:
            print(f"[fetch_termspace_user_tasksupply] Handling reports for {user}.")
            # User loop - now go over every status and get totals per day
            for status in statuses:
                user_output = []
                try:
                    for day in (reports
                            .annotate(tx_day=TruncDay('time'))
                            .values('tx_day')
                            .order_by('tx_day')
                            .annotate(last_entry=Max('time'))).values_list('tx_day', flat=True):
                        # print('Unique day:',day)
                        
                        # Selects last time_stamp for each day
                        last_entries = (TermspaceUserReport.objects
                            .filter(username = user, status=status)
                            .annotate(tx_day=TruncDay('time'))
                            .order_by('tx_day')
                            .values('tx_day')
                            .annotate(last_entry=Max('time'))
                            .values_list('last_entry', flat=True))
                        query = TermspaceUserReport.objects.filter(
                            time__in=last_entries,
                        )
                        # print('Looking up: ', status, user)
                        _query = query.filter(status = str(status), username = user, time__day=day.day, time__month=day.month, time__year=day.year)
                        if _query.count() > 0:
                            if _query.last().time.strftime('%d-%m-%Y') not in categories:
                                categories.append(_query.last().time.strftime('%d-%m-%Y'))
                            if _query.count() == 0:
                                user_output.append(0)
                            else:
                                user_output.append(_query.last().count)
                        else:
                            user_output.append(0)
                        # days.append(day.strftime('%d-%m-%Y'))
                except Exception as e:
                    print(f"[fetch_termspace_user_tasksupply] Error handling {user} / {status}. Error: {e}.")
                output.append({
                    'name' : user + ' ' + str(status),
                    'data' : user_output,
                })
            
        print(f"Response: {len(categories)} days / {len(output)} users.")
        return Response({
            'progress' : {
                    'categories' : categories,
                    'series':output,
                }
        })
class fetch_termspace_tasksupply_v2(viewsets.ViewSet):
    """
    Fetches terms from termspace.
    """
    permission_classes = [Permission_TermspaceProgressReport]

    def list(self, request, pk=None):
        # limit search to last x days
        last_month = datetime.today() - timedelta(days=30)
        # Get categories - list of days
        days = TermspaceProgressReport.objects.all().annotate(tx_day=TruncDay('time')).distinct('tx_day').values_list('tx_day', flat=True).filter(time__gte=last_month)
        titles = TermspaceProgressReport.objects.all().distinct('title').values_list('title', flat=True).filter(time__gte=last_month)
        for title in titles:
            # Selects last time_stamp for each day
            last_entries = (TermspaceProgressReport.objects
                .filter(time__gte=last_month)
                .filter(title = title)
                .annotate(tx_day=TruncDay('time'))
                .values('tx_day')
                .annotate(last_entry=Max('time'))
                .values_list('last_entry', flat=True))
            # Add queries
            try:
                query = query | TermspaceProgressReport.objects.filter(
                    time__in=last_entries,
                ).filter(time__gte=last_month)
            except:
                query = TermspaceProgressReport.objects.filter(
                    time__in=last_entries,
                ).filter(time__gte=last_month)
        
        categories = []
        series = []
        # for day in days:
        #     # List all unique days
        #     categories.append(day.strftime('%d-%m-%Y'))
        # Loop over all unique titles
        for title in titles:
            _data = []
            # For each day
            for day in days:
                # Get the last query with this title for the day
                day_query = query.filter(time__day=day.day, time__month=day.month, time__year=day.year)
                day_query = day_query.filter(title = title)
                if day_query.count() == 1:
                    _data.append(day_query.last().count)
                    if day_query.last().time.strftime('%d-%m-%Y') not in categories:
                        categories.append(day.strftime('%d-%m-%Y'))
                else:
                    _data.append(None)
                
            series.append({
                'name': title,
                'data' : _data,
                })
        return Response({
            'progress' : {
                'categories' : categories,
                'series' : series,
            },
            'legend' : [],
        })
    def create(self, request, pk=None):
        dump_termspace_progress()
        return Response('started')