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
from mapping.models import *
from .models import *
import time
import environ

from rest_framework import viewsets
from .serializers import *
from rest_framework import views
from rest_framework.response import Response
from rest_framework.permissions import *

from snowstorm_client import Snowstorm

from django.db.models.functions import Cast

# Import environment variables
env = environ.Env(DEBUG=(bool, False))
# reading .env file
environ.Env.read_env(env.str('ENV_PATH', '.env'))

class PostcoTemplates(viewsets.ViewSet):
    permission_classes = [AllowAny]
    def retrieve(self, request, pk=None):
        output = TemplateSerializer(template.objects.get(id=pk)).data

        return Response(output)
    def list(self, request):
        output = TemplateSerializer(template.objects.all(), many=True).data

        return Response(output)

class PostcoAttributes(viewsets.ViewSet):
    permission_classes = [AllowAny]
    def retrieve(self, request, pk=None):

        output = AttributeSerializer(attribute.objects.get(id=pk)).data

        return Response(output)

class PostcoExpression(viewsets.ViewSet):
    permission_classes = [AllowAny]
    def create(self, request):
        data = request.data
        print(data)
        print("\n ------------")

        string =    f"=== {data.get('rootConcept').get('sctid')} |{data.get('rootConcept').get('fsn')} : \n"
        string +=   "{\n"
        
        for attribute in data.get('postcoComponents'):
            string +=   f"{attribute['attribute']['sctid']} |{attribute['attribute']['fsn']}| = {attribute['value'].get('sctid')} |{attribute['value'].get('fsn')}|,\n"

        string +=   "}"

        print("STRING:\n",string)

        output=string
        return Response(output)