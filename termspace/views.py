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

# Snomed component endpoint
class componentApi(viewsets.ViewSet):
    permission_classes = [AllowAny]
    def list(self, request):
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
                        output.append({
                            'id' : component.component_id,
                            'codesystem' : component.codesystem_id.codesystem_title,
                            # 'extra' : extra,
                            'group' : extra.get('Groep'),
                            'AUB' : aub,
                            'actief' : extra.get('Actief?'),
                            'title' : component.component_title,
                            'aantal taken' : tasks.count(),
                            'project' : task.project_id.title,
                            'status' : task.status.status_title,
                        })
                else:
                    output.append({
                            'id' : component.component_id,
                            'codesystem' : component.codesystem_id.codesystem_title,
                            # 'extra' : extra,
                            'group' : extra.get('Groep'),
                            'AUB' : aub,
                            'actief' : extra.get('Actief?'),
                            'title' : component.component_title,
                            'aantal taken' : tasks.count(),
                            'project' : None,
                            'status' : None,
                        })

            # Return Json response
            return Response(output)

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