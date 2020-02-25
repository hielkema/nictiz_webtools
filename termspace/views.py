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
import json
from .forms import *
from .models import *
import time
import environ

from rest_framework import viewsets
from .serializers import *
from rest_framework import views
from rest_framework.response import Response
from rest_framework.permissions import *

from snowstorm_client import Snowstorm

# Import environment variables
env = environ.Env(DEBUG=(bool, False))
# reading .env file
environ.Env.read_env(env.str('ENV_PATH', '.env'))

# Search termspace comments
class searchTermspaceComments(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
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
    permission_classes = [IsAuthenticated]
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
    permission_classes = [AllowAny]
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

# ECL query results
class eclQueryApi(viewsets.ViewSet):
    permission_classes = [AllowAny]
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
    permission_classes = [AllowAny]
    def retrieve(self, request, pk=None):
        def list_children(focus):
            component = MappingCodesystemComponent.objects.get(component_id=focus)
            
            _children = []
            if component.children != None:
                for child in list(json.loads(component.children)):
                    _children.append(list_children(child))
           
            output = {
                'id' : focus,
                'name' : component.component_title,
                'children' : _children
            }
            
            return(output)

        print('Get tree for',str(pk))
        children_list = list_children(pk)

        return Response(children_list)

class Mapping_Progressreport_perStatus(viewsets.ViewSet):
    permission_classes = [AllowAny]
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
    permission_classes = [AllowAny]
    def retrieve(self, request, pk=None):
        output = []

        codesystem  = MappingCodesystem.objects.get(id=pk)
        components  = MappingCodesystemComponent.objects.filter(codesystem_id=codesystem)
        projects    = MappingProject.objects.all()

        print('Received request for codesystem',codesystem.codesystem_title)
        if str(request.GET.get('secret')) != str(env('mapping_api_secret')):
            print('Incorrect or absent secret')
            return Response('error')
        else:
            for component in components:
                tasks = MappingTask.objects.filter(source_component = component)
                extra = json.loads(component.component_extra_dict)
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

                        output.append({
                            'id' : component.component_id,
                            'codesystem' : component.codesystem_id.codesystem_title,
                            # 'extra' : extra,
                            'group' : extra.get('Groep'),
                            'AUB' : aub,
                            'actief' : extra.get('Actief'),
                            'soort' : extra.get('Soort'),
                            'title' : component.component_title,
                            'aantal taken' : tasks.count(),
                            'project' : task.project_id.title,
                            'source or target' : task_type,
                            'status' : task.status.status_title,
                        })
                else:
                    output.append({
                            'id' : component.component_id,
                            'codesystem' : component.codesystem_id.codesystem_title,
                            # 'extra' : extra,
                            'group' : extra.get('Groep'),
                            'AUB' : aub,
                            'actief' : extra.get('Actief'),
                            'soort' : extra.get('Soort'),
                            'title' : component.component_title,
                            'aantal taken' : tasks.count(),
                            'project' : None,
                            'source or target' : None,
                            'status' : None,
                        })

            # Return Json response
            return Response(output)

class Mapping_Progressreport_overTime(viewsets.ViewSet):
    permission_classes = [AllowAny]
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

            records = MappingProgressRecord.objects.filter(name="TasksPerStatus")
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
    """
    Draft for exporting FHIR ConceptMap.
    Currently only valid for project NHG diagnostische bepalingen -> labcodeset [3]
    -> /termspace/mapping_json/3/
    Will currently only export the first 100 mapping rules
    """
    permission_classes = [AllowAny]
    def list(self, request, pk=None):
        conceptmap = []
        # Return Json response
        return Response({
            "codesystems" : conceptmap
        })
    def retrieve(self, request, pk=None):
        project = MappingProject.objects.get(id=pk)
        elements = []
        error = []
        correlation_options = [
            # [code, readable]
            ['447559001', 'Broad to narrow'],
            ['447557004', 'Exact match'],
            ['447558009', 'Narrow to broad'],
            ['447560006', 'Partial overlap'],
            ['447556008', 'Not mappable'],
            ['447561005', 'Not specified'],
        ]
        # JSON export for project NHG diagn -> labcodeset + SNOMED
        if project.id == 3:
            message = "NHG diagnostische bepalingen -> labcodeset + SNOMED"

            # Find mapping tasks
            tasks = MappingTask.objects.filter(project_id = project)
            # Filter rejected tasks
            tasks = tasks.exclude(status = project.status_rejected)

            for task in tasks[:100]:
                targets = []
                product_list = []
                # Find mapping rules for current task
                rules = MappingRule.objects.filter(source_component = task.source_component)

                # Find Snomed material
                products = rules.filter(target_component__codesystem_id = 1)
                if products.count() > 1:
                    error.append({
                        "type" : "Multiple materials. Add priorities / correlation to products or accept as both?",
                        "task" : task.id,
                    })

                for single_product in products:
                    product_list.append({
                        "property" : "http://snomed.info/id/"+single_product.target_component.component_id+"/",
                        "system" : single_product.target_component.codesystem_id.codesystem_title, # TODO - add FHIR URI to model instead
                        "code" : single_product.target_component.component_id,
                        "display" : single_product.target_component.component_title,
                    })

                # Append target
                for rule in rules:
                    equivalence = rule.mapcorrelation
                    for code, readable in correlation_options:
                        equivalence = equivalence.replace(code, readable)
                    targets.append({
                        "code" : rule.target_component.component_id,
                        "display" : rule.target_component.component_title,
                        "equivalence" : equivalence,
                        "comment" : rule.mapadvice,
                        "product" : product_list,
                    })

                # Append element
                elements.append({
                    # "[DEBUG]task.id" : task.id,
                    # "[DEBUG]task.status" : task.status.status_title,
                    "code" : task.source_component.component_id,
                    "display" : task.source_component.component_title,
                    "target" : targets,
                })

            return Response({
                "[DEBUG] errors" : error,
                "[DEBUG] project" : project.title,
                "[DEBUG] message" : message,

                "resourceType" : "ConceptMap",
                "url" : "TODO",
                
                "id" : "nhg-tabel-45-to-labcodeset",
                "name" : "NHG Tabel 45 naar Nederlandse Labcodeset",
                "description" : "TODO",
                
                "version" : "draft",
                "status" : "draft",
                "experimental" : True,

                "date" : "TODO",
                "publisher" : "Nictiz",
                "contact" : {
                    "telecom" : [
                        {
                            "system" : "url",
                            "name" : "https://www.nictiz.nl",
                        }
                    ]
                },
                "copyright" : "Nictiz - NHG - NVMM - NVKC",
                "sourceCanonical" : "https://referentiemodel.nhg.org/tabellen/nhg-tabel-45-diagnostische-bepalingen", # NHG diagn bep
                "targetCanonical" : "http://loinc.org",
                "group" : {
                    "source" : "https://referentiemodel.nhg.org/tabellen/nhg-tabel-45-diagnostische-bepalingen", # NHG diagn bep
                    "sourceVersion" : "TODO", # NHG versie
                    "target" : "http://loinc.org",
                    "targetVersion" : "TODO", # LOINC versie
                    "element" : elements,
                    "unmapped" : [] # TODO
                }
            })
        else:
            message = "Geen exportregels bekend voor dit project"


# Full modelviewset
# class componentApi(viewsets.ReadOnlyModelViewSet):
#     queryset = MappingCodesystemComponent.objects.all()
#     serializer_class = MappingComponentSerializer

# LIST endpoint
# class testEndPoint(viewsets.ViewSet):
#     def list(self, request):
#         yourdata= [{"id": 1 ,"likes": 10, "comments": 0}, {"id": 2,"likes": 4, "comments": 23}]
#         results = testEndPointSerializer(yourdata, many=True).data
#         return Response(results)
#     def retrieve(self, request, pk=None):
#         yourdata = pk
#         # results = testEndPointSerializer(yourdata, many=True).data
#         return Response(yourdata)
#     def create(self, request):
#         return Response('succes')

# CUSTOM endpoint
# class TestCustomView(views.APIView):
#     permission_classes = []
#     def post(self, request, *args, **kwargs):
#         email = request.data.get('email', None)
#         url = request.data.get('url', None)
#         if email and url:
#             return Response({"success": True, "email":email,"url":url})
#         else:
#             return Response({"success": False})
#     def get(self, request):
#         yourdata= [{"id": 1 ,"likes": 10, "comments": 0}, {"id": 2,"likes": 4, "comments": 23}]
#         results = testEndPointSerializer(yourdata, many=True).data
#         return Response(results)