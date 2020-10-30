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
from rest_framework import views
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

class Permission_MappingProject_Whitelist(permissions.BasePermission):
    """
    Global permission check rights to use the whitelist functionality.
    """
    def has_permission(self, request, view):
        if 'mapping | audit whitelist' in request.user.groups.values_list('name', flat=True):
            return True

class SnomedFailbackImport(viewsets.ViewSet):
    permission_classes = [Permission_MappingProject_Whitelist]

    """
    Will import SNOMED concepts in ECL query: '<<pk'
    """

    def retrieve(self, request, pk=None):
        conceptid = str(pk)
        import_snomed_async(conceptid)

        return Response(f"Started import [{str(pk)}]")