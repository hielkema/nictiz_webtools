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

class MappingTriggerAudit(viewsets.ViewSet):
    permission_classes = [Permission_MappingProject_Access]

    def retrieve(self, request, pk=None):
        print(f"[audits/MappingTriggerAudit retrieve] requested by {request.user} - {pk}")
        try:
            task = MappingTask.objects.get(id=pk)
            send_task('mapping.tasks.qa_orchestrator.audit_async', ['multiple_mapping', task.project_id.id, task.id], {})
            return Response(True)
        except Exception as e:
            print(e)
            return Response(e)    

class MappingTriggerProjectAudit(viewsets.ViewSet):
    permission_classes = [Permission_MappingProject_Access]

    def retrieve(self, request, pk=None):
        print(f"[audits/MappingTriggerProjectAudit retrieve] requested by {request.user} - {pk}")
        try:
            project = MappingProject.objects.get(id=pk)
            send_task('mapping.tasks.qa_orchestrator.audit_async', ['multiple_mapping', project.id, None], {})

            return Response(True)
        except Exception as e:
            return Response(e)  

class MappingAudits(viewsets.ViewSet):
    permission_classes = [Permission_MappingProject_Access]

    def retrieve(self, request, pk=None):
        print(f"[audits/MappingAudits retrieve] requested by {request.user} - {pk}")
        task = MappingTask.objects.get(id=pk)
        audit_hits = MappingTaskAudit.objects.filter(task=task).select_related(
            'task',
            'task__status',
            'task__user',
            'task__project_id',
        )

        audits = []
        for audit in audit_hits:
            audits.append({
                'id':audit.id,
                'type':audit.audit_type,
                'reason':audit.hit_reason,
                'ignore':audit.ignore,
                'timestamp':audit.first_hit_time,
            })
        return Response(audits)
    def create(self, request):
        print(f"[audits/MappingAudits create (veto audit view)] requested by {request.user} - data: {str(request.data)[:500]}")
        payload = request.data
        taskid = str(payload.get('task_id'))
        task = MappingTask.objects.get(id=taskid)

        audit, created_audit = MappingTaskAudit.objects.get_or_create(
                        task=task,
                        audit_type="AUDIT_VETO",
                        sticky=True,
                        hit_reason=f"Deze taak heeft in de audit view een veto ontvangen. Zie commentaar voor meer informatie.",
                    )
        return Response(True)

class MappingAuditWhitelist(viewsets.ViewSet):
    permission_classes = [Permission_MappingProject_Whitelist]

    def retrieve(self, request, pk=None):
        print(f"[audits/MappingAuditWhitelist  - {pk}")
        audit_hit = MappingTaskAudit.objects.get(id=pk)
        audit_hit.ignore = True
        audit_hit.save()
        
        return Response(str(audit_hit))

class MappingAuditRemoveWhitelist(viewsets.ViewSet):
    permission_classes = [Permission_MappingProject_Whitelist]

    def retrieve(self, request, pk=None):
        print(f"[audits/MappingAuditRemoveWhitelist retrieve] requested by {request.user} - {pk}")
        audit_hit = MappingTaskAudit.objects.get(id=pk)
        audit_hit.ignore = False
        audit_hit.save()
        
        return Response(str(audit_hit))

class MappingAuditRemove(viewsets.ViewSet):
    permission_classes = [Permission_MappingProject_Whitelist]

    def retrieve(self, request, pk=None):
        print(f"[audits/MappingAuditRemove retrieve] requested by {request.user} - {pk}")
        audit_hit = MappingTaskAudit.objects.get(id=pk)
        audit_hit.delete()
        
        return Response(f'{pk} deleted')

class MappingAuditsPerProject(viewsets.ViewSet):
    permission_classes = [Permission_MappingProject_Access]

    def retrieve(self, request, pk=None):
        print(f"[audits/MappingAuditsPerProject retrieve] requested by {request.user} - {pk}")
        project = MappingProject.objects.get(id=pk)
        audit_hits = MappingTaskAudit.objects.filter(task__project_id=project).select_related(
            'task',
            'task__status',
            'task__user',
            'task__project_id',
        )

        audits = []
        for audit in audit_hits:
            audits.append({
                'id':audit.id,
                'task':audit.task.id,
                'status':audit.task.status.status_title,
                'user':audit.task.user.username,
                'project':audit.task.project_id.id,
                'type':audit.audit_type,
                'reason':audit.hit_reason,
                'ignore':audit.ignore,
                'sticky':audit.sticky,
                'timestamp':audit.first_hit_time,
            })
        return Response(audits)

class MappingAuditStatus(viewsets.ViewSet):
    permission_classes = [Permission_MappingProject_Whitelist]

    def retrieve(self, request, pk=None):
        print(f"[audits/MappingAuditStatus retrieve] requested by {request.user} - {pk}")
        i = inspect()
        active = i.active()
        info = []
        if not active:
            pk = 'error - celery down?'
        else:
            for worker, tasks in list(active.items()):
                if tasks:
                    taskstr = '; '.join("%s(*%s, **%s)" % (t['name'], t['args'], t['kwargs'])
                            for t in tasks)
                else:
                    taskstr = 'None'
                info.append((worker + ' active', taskstr))
            for worker, tasks in list(i.scheduled().items()):
                info.append((worker + ' scheduled', len(tasks)))

            

        # Should return:
        # - audit running for project true/false
        # - audit running for current task true/false

        return Response(f'{pk} checked {info}')
    
    def list(self, request):
        print(f"[audits/MappingAuditStatus list] requested by {request.user}")
        i = inspect()
        active = i.active()
        info = []
        if not active:
            pk = 'error - celery down?'
        else:
            processes = []
            for worker, tasks in list(active.items()):
                print(f"[audits/MappingAuditStatus list] worker: {worker} => {tasks}")
                for task in tasks:
                    if task.get('type').split(".")[0] == 'mapping':
                        processes.append(task)

        return Response({
            'active' : (len(processes) > 0),
            'list' : processes
        })