# howdy/urls.py
from django.conf.urls import url

from . import views

app_name = 'epd'
urlpatterns = [
    #url(r'medicatie/', views.get_name, name='medicatie'),
    url(r'test', views.api_ApiTest_get.as_view(), name='test'),

    url(r'decursus/(?P<patientid>\w+)/(?P<decursusId>\w+)', views.api_decursus.as_view(), name='decursus-detail'),
    url(r'decursus/(?P<patientid>\w+)', views.api_decursus.as_view(), name='decursus-list'),
    url(r'decursus', views.api_decursus.as_view(), name='decursus'),

    url(r'problem', views.api_problem.as_view(), name='problem'),

    url(r'patient/(?P<id>\w+)', views.api_patient_get.as_view(), name='patient-detail'),
    url(r'patient', views.api_patient_get.as_view(), name='patient-list'),
]