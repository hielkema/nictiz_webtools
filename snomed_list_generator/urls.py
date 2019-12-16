# build_tree/urls.py
from django.conf.urls import url

from . import views

app_name = 'snomed_list'

urlpatterns = [
    url(r'download/(?P<downloadfile>\w+)', views.DownloadFile.as_view(), name='download'),
    url(r'index/', views.createTaskPageView.as_view(), name='index'),
    url(r'create_task/', views.ajaxCreateTask.as_view(), name='create_task'),
    url(r'get_tasks/', views.showTaskPageView.as_view(), name='get_tasks'),
    url(r'', views.createTaskPageView.as_view()),
]