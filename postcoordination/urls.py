# howdy/urls.py
from django.conf.urls import url
from django.urls import include, path
from rest_framework.routers import SimpleRouter
# from . import views
from .views import *

app_name = 'postco'

router = SimpleRouter()
# router.register(r'termspace_comments', termspaceComments, basename="termspace_comments")
router.register(r'templates', PostcoTemplates, basename="postco templates")
router.register(r'attributes', PostcoAttributes, basename="postco templates attr-values")
router.register(r'expression', PostcoExpression, basename="postco templates expression")
# router.register(r'attributevalues', PostcoAttributeValues, basename="postco templates attr-values")

urlpatterns = [ 
    path('', include(router.urls)), 
]