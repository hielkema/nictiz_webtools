# howdy/urls.py
from django.conf.urls import url
from django.urls import include, path
from rest_framework.routers import SimpleRouter
# from . import views
from .views import *

app_name = 'validation'

router = SimpleRouter()
router.register(r'pk_testing', pk_test, basename="Test_PK")
router.register(r'import', import_tasks, basename="Import all tasks")


urlpatterns = [ 
    path('', include(router.urls)),
]