from django.shortcuts import render
import random, json
from django.views.generic import TemplateView
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from django.urls import reverse
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from .models import *
from mapping.models import *
from django.middleware.csrf import get_token

# Create your views here.
class api_ApiTest_get(TemplateView):
    '''
    Returns all comments and events for the current task in a list
    Only allowed with change task status rights.
    '''

    def get(self, request, **kwargs):
        context = {
            'test' : 'Testtekst'
        }
        names = ['Lorem','Ipsum','Dolor','Sid','Amed']
        admitted = [True, False]

        context = {
            'id': random.randrange(100000,10000000,4),
            'surname': random.choice(names)+random.choice(names),
            'admitted': random.choice(admitted),
        }

        context = get_token(request)

        # Return JSON
        return JsonResponse(context,safe=False)

###### Patients
class api_patient_get(TemplateView):
    '''
    Returns patients
    '''
    def get(self, request, **kwargs):
        patients = Patient.objects.all()
        print('\nPatient data requested')
        if kwargs.get('id'):
            patients = patients.filter(id=kwargs.get('id'))
            print('Patient data filter: ID=',kwargs.get('id'))

        patient_list = []
        for patient in patients:
            patient_list.append({
                'id': patient.id,
                'name':{
                    'first':patient.firstname,
                    'last':patient.surname,
                    'initials':patient.initials,
                },
                'dob':patient.dob,
                'gender':patient.gender,
                'address':{
                    'street':patient.address_street,
                    'city':patient.address_city,
                    'country':patient.address_country
                },
                'bsn': patient.bsn,
            })

        context = patient_list

        # Return JSON
        return JsonResponse(context,safe=False)

class api_decursus(TemplateView):
    def post(self, request, **kwargs):
        payload = json.loads(request.body.decode("utf-8"))
        print('\nReceived decursus data: ', payload)
        print('Action: ',payload.get('action'))

        currentUser = User.objects.get(id=request.user.id)
        currentPatient = Patient.objects.get(id=payload.get('patientId'))

        print('Start handling action')

        if payload.get('action') == 'new':
            print('Request: add new decursus')
            decursus = Decursus.objects.create(
                 user = currentUser,
                 patient = currentPatient,
             )
            decursus.save()
            context = {
                'patientid': payload.get('patientId'),
                'decursusid' : decursus.id
            }
        elif payload.get('action') == 'patch':
            print('Request: edit decursus')
            data = payload.get('decursus')
            decursus = Decursus.objects.get(
                 id = data.get('id')
             )
            decursus.anamnese = data.get('anamnese')
            decursus.save()
            context = {
                'patientid': payload.get('patientId'),
                'decursusid' : decursus.id
            }
        elif payload.get('action') == 'delete':
            print('Request: delete decursus ',payload.get('decursusId'))
            decursus = Decursus.objects.get(
                 id = payload.get('decursusId')
             )
            decursus.delete()
            context = {
                'patientid': payload.get('patientId')
            }
        else:
            print('No valid action received')
            context = {
                'patientid': payload.get('patientId')
            }

        
        print('Response: ', context)
        return JsonResponse(context,safe=False)

    def get(self, request, **kwargs):
        print('\nReceived request for decursus data for patientid: ', kwargs.get('patientid'))
        
        current_patient = Patient.objects.get(id = kwargs.get('patientid'))
        decursus_query = Decursus.objects.filter(patient = current_patient).order_by('-edited')

        if kwargs.get('decursusId'):
            decursus_query = decursus_query.filter(id=kwargs.get('decursusId'))

        decursus_list = []
        for decursus in decursus_query:
            problems = ZibProbleem.objects.filter(Decursus_id=decursus.id)
            problem_list = []
            for problem in problems:
                problem_list.append({
                    'id':problem.id,
                    'type':problem.ProbleemType,
                    'naam':problem.ProbleemNaam.component_title,
                    'begin':problem.ProbleemBeginDatum,
                    'eind':problem.ProbleemEindDatum,
                    'status':problem.ProbleemStatus,
                    'verificatie':problem.VerificatieStatus,
                })

            decursus_list.append({
                'id': decursus.id,
                'patientid': decursus.patient.id,
                'user': decursus.user.username,
                'anamnese':decursus.anamnese,
                'problems':problem_list,
                'created':decursus.created,
                'edited':decursus.edited,
            })
        
        if kwargs.get('decursusId'):
            context = decursus_list[0]
        else:
            context = decursus_list

        return JsonResponse(context,safe=False)

class api_problem(TemplateView):
    def post(self, request, **kwargs):
        payload = json.loads(request.body.decode("utf-8"))
        print('\nReceived problem data: ', payload)

        currentUser = User.objects.get(id=request.user.id)
        currentPatient = Patient.objects.get(id=payload.get('patientId'))
        probleem = payload.get('problem')
        decursus = Decursus.objects.get(id=probleem.get('decursusId'))

        problem_component = MappingCodesystemComponent.objects.get(component_id=probleem.get('naam'))

        obj = ZibProbleem.objects.create(
            user = currentUser,
            patient = currentPatient,

            ProbleemType = probleem.get('type'),
            ProbleemNaam = problem_component,
            ProbleemBeginDatum = probleem.get('begin'),
            ProbleemEindDatum = probleem.get('eind'),
            ProbleemStatus = probleem.get('status'),
            VerificatieStatus = probleem.get('verificatie'),

            Decursus = decursus,
            comments = ''
        )
        obj.save()

        context = {
            'patientid' : currentPatient.id,
            'created' : str(obj),
        }
        # Should return patientid:id
        return JsonResponse(context,safe=False)