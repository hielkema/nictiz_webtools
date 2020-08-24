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

class MappingPostComment(viewsets.ViewSet):
    permission_classes = [Permission_MappingProject_Access]

    def create(self, request):
        if 'mapping | place comments' in request.user.groups.values_list('name', flat=True):
            print("Commentaar:",request.user, request.data.get('task'), request.data.get('comment'))
            current_user = User.objects.get(id=request.user.id)
            task = MappingTask.objects.get(id=request.data.get('task'))
            if MappingProject.objects.filter(id=task.project_id.id, access__username=current_user).exists():

                comment = MappingComment.objects.create(
                    comment_title   = '',
                    comment_task    = task,
                    comment_body    = request.data.get('comment'),
                    comment_user    = current_user,
                )
                comment.save()
                return Response(str(comment))
        else:
            return Response('Geen toegang', status=status.HTTP_401_UNAUTHORIZED)

    def delete(self, request, pk=None):
        print("Commentaar:",request.user)
        current_user = User.objects.get(id=request.user.id)
        comment = MappingComment.objects.get(id=pk, comment_user=current_user)
        current_user = User.objects.get(id=request.user.id)
        if MappingProject.objects.filter(id=comment.comment_task.project_id.id, access__username=current_user).exists():
            if current_user == request.user:
                comment.delete()
                return Response('succes')
            else:
                return Response('fail: not your comment?')
        else:
            return Response('Geen toegang', status=status.HTTP_401_UNAUTHORIZED)

    def retrieve(self, request, pk=None):
        comment = MappingComment.objects.get(id=pk)
        current_user = User.objects.get(id=request.user.id)
        if MappingProject.objects.filter(id=comment.comment_task.project_id.id, access__username=current_user).exists():
            output = {
                'comment_title'   : '',
                'comment_task'    : str(comment.comment_task),
                'comment_body'    : comment.comment_body,
                'comment_user'    : comment.comment_user.username,
            }
            return Response(output)
        else:
            return Response('Geen toegang', status=status.HTTP_401_UNAUTHORIZED)