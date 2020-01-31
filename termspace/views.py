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