# build_tree/urls.py
from django.conf.urls import url

from . import views

app_name = 'build_tree_excel'

urlpatterns = [
    url(r'download/(?P<downloadfile>\w+)', views.DownloadFile.as_view(), name='download'),
    url(r'index/', views.BuildTreeView.as_view(), name='index'),
    url(r'', views.BuildTreeView.as_view()),
]