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
from operator import itemgetter

from rest_framework import viewsets
from ..serializers import *
from rest_framework import views
from rest_framework.response import Response
from rest_framework.permissions import *

from ..tasks import *
from ..forms import *
from ..models import *

class api_UpdateCodesystems_post(UserPassesTestMixin,TemplateView):
    '''
    Receives requests reload the labcodeset through async task
    Only allowed with admin codesystem rights.
    '''
    def handle_no_permission(self):
        return redirect('login')
    def test_func(self):
        # return self.request.user.has_perm('Build_Tree.make_taskRecord')
        return self.request.user.groups.filter(name='mapping | admin codesystems').exists()

    def post(self, request, **kwargs):
        try:
            print('Diagnosethesaurus', json.loads(request.POST.get('codesystem[diagnosethesaurus]')))
            if json.loads(request.POST.get('codesystem[diagnosethesaurus]')):
                import_diagnosethesaurus_task.delay()
            
            print('Labcode', json.loads(request.POST.get('codesystem[labcode]')))
            if json.loads(request.POST.get('codesystem[labcode]')):
                import_labcodeset_async.delay()

            print('Apache', json.loads(request.POST.get('codesystem[apache]')))
            if json.loads(request.POST.get('codesystem[apache]')):
                import_apache_async.delay()

            print('G-Standaard Diagnoses', json.loads(request.POST.get('codesystem[gstandaardDiagnoses]')))
            if json.loads(request.POST.get('codesystem[gstandaardDiagnoses]')):
                import_gstandaardDiagnoses_task.delay()

            print('Snomed', json.loads(request.POST.get('codesystem[snomed]')))
            if json.loads(request.POST.get('codesystem[snomed]')): # codesystem 1 = snomed
                # import_snomed_async.delay('373873005') # farmaceutisch/biologisch product (product)
                # import_snomed_async.delay('260787004') # fysiek object (fysiek object)
                # import_snomed_async.delay('78621006') # fysieke kracht (fysieke kracht)
                # import_snomed_async.delay('272379006') # gebeurtenis (gebeurtenis)
                # import_snomed_async.delay('419891008') # gegevensobject (gegevensobject)
                # import_snomed_async.delay('404684003') # klinische bevinding (bevinding)
                # import_snomed_async.delay('362981000') # kwalificatiewaarde (kwalificatiewaarde)
                # import_snomed_async.delay('123037004') # lichaamsstructuur (lichaamsstructuur)
                # import_snomed_async.delay('123038009') # monster (monster)
                # import_snomed_async.delay('410607006') # organisme (organisme)
                # import_snomed_async.delay('243796009') # situatie met expliciete context (situatie)
                # import_snomed_async.delay('48176007') # sociale context (sociaal concept)
                # import_snomed_async.delay('105590001') # substantie (substantie)
                # import_snomed_async.delay('71388002') #  verrichting (verrichting)
                # import_snomed_async.delay('363787002') # waarneembare entiteit (waarneembare entiteit)

                # # Now check all SNOMED concepts in the database for status active/inactive.
                # concepts = MappingCodesystemComponent.objects.filter(codesystem_id__id = '1').values_list('component_id', flat = True)
                # for concept in list(concepts):
                #     check_snomed_active.delay(concept=concept)
                
                import_snomed_snowstorm.delay()

            print('nhgVerr', json.loads(request.POST.get('codesystem[nhgverr]')))
            if json.loads(request.POST.get('codesystem[nhgverr]')):
                import_nhgverrichtingen_task.delay()
                
            print('nhgBep', json.loads(request.POST.get('codesystem[nhgbep]')))
            if json.loads(request.POST.get('codesystem[nhgbep]')):
                import_nhgbepalingen_task.delay()
            
            print('nhgICPC', json.loads(request.POST.get('codesystem[icpc]')))
            if json.loads(request.POST.get('codesystem[icpc]')):
                import_icpc_task.delay()

            print('Palga', json.loads(request.POST.get('codesystem[palga]')))
            if json.loads(request.POST.get('codesystem[palga]')):
                print("Let's go")
                import_palgathesaurus_task.delay()

            print('Omaha', json.loads(request.POST.get('codesystem[omaha]')))
            if json.loads(request.POST.get('codesystem[omaha]')):
                print("Importeren Omaha")
                import_omaha_task.delay()

            context = {
                'result': "success",
            }
            # Return JSON
            return JsonResponse(context,safe=False)
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            error = 'Exc type: {} \n TB: {}'.format(exc_type, exc_tb.tb_lineno)
            print(type(e), e, kwargs, error)
    def get(self, request, **kwargs):        
        return render(request, 'mapping/v2/import_codesystems.html', {
            'page_title': 'Mapping project',
        })



class vue_MappingIndex(UserPassesTestMixin,TemplateView):
    '''
    View for choosing a project to work on.
    Only accessible with view tasks rights.
    '''
    def handle_no_permission(self):
        return redirect('login')
    def test_func(self):
        # return self.request.user.has_perm('Build_Tree.make_taskRecord')
        return self.request.user.groups.filter(name='mapping | access').exists()

    def get(self, request, **kwargs):
        # TODO - Check if active projects exist, otherwise -> error.
        # TODO - Check if active projects exist, otherwise -> error.
        current_user = User.objects.get(id=request.user.id)
        project_list = MappingProject.objects.filter(active=True).filter(access__username=current_user).order_by('id')
        project_dict = []
        for project in project_list:
            tasks = MappingTask.objects.filter(project_id=project)
            project_dict.append({
                'id' : project.id,
                'title' : project.title,
                'num_tasks': tasks.exclude(status=project.status_rejected).count(),
                'num_open_tasks': tasks.exclude(status=project.status_complete).exclude(status=project.status_rejected).count(),
                'num_open_tasks_user': tasks.filter(user=current_user).exclude(status=project.status_complete).exclude(status=project.status_rejected).count(),
            })
        return render(request, 'mapping/v2/index.html', {
            'page_title': 'Mapping project',
            'project_list': project_dict,
        })