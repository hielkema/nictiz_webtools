# howdy/urls.py
from django.conf.urls import url
from django.urls import include, path
from rest_framework.routers import SimpleRouter
# from . import views
from .views import *

app_name = 'qa_service'

router = SimpleRouter()
router.register(r'perform', test_api, basename="Test_API")


urlpatterns = [ 
    path('', include(router.urls)),
]