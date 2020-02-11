# build_tree/urls.py
from django.conf.urls import url

from . import views

app_name = 'build_tree_excel'

urlpatterns = [
    url(r'qa/download/(?P<downloadfile>\w+)', views.TermspaceQaDownload.as_view(), name='qa_download'),
    url(r'qa/', views.TermspaceQaOverview.as_view(), name='qa_index'),
    url(r'download/(?P<downloadfile>\w+)', views.DownloadFile.as_view(), name='download'),
    url(r'index/', views.BuildTreeView.as_view(), name='index'),
    url(r'', views.BuildTreeView.as_view()),
]