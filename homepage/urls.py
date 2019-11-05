# howdy/urls.py
from django.conf.urls import url

from . import views

app_name = 'homepage'
urlpatterns = [
    #url(r'medicatie/', views.get_name, name='medicatie'),
    url(r'', views.HomePageView.as_view(), name='index'),
]