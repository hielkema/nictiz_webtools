# howdy/urls.py
from django.conf.urls import url

from . import views

app_name = 'termspace'
urlpatterns = [
    #url(r'medicatie/', views.get_name, name='medicatie'),
    url(r'search_comments/', views.SearchcommentsPageView.as_view(), name='search'),
]