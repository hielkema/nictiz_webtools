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
        data = template.objects.get(id=pk)
        output = {
            'id' : data.id,
            'title' : data.title,
            'description' : data.description,
        }

        return Response(output)

class PostcoAttributes(viewsets.ViewSet):
    permission_classes = [AllowAny]
    def retrieve(self, request, pk=None):
        data = template.objects.get(id=pk)
        output = []
        for attribute in data.attributes.all():
            output.append({
                'id': attribute.id,
                'sctid': attribute.sctid,
                'fsn' : attribute.fsn,
            })
        
        return Response(output)

class PostcoAttributeValues(viewsets.ViewSet):
    permission_classes = [AllowAny]
    def retrieve(self, request, pk=None):
        output = []
        data = attribute.objects.get(id=pk)
        for value in data.attribute_values.all():
            output.append({
                'id': value.id,
                'sctid': value.sctid,
                'fsn' : value.fsn,
            })

        return Response(output)