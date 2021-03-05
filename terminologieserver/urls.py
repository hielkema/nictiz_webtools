# howdy/urls.py
from django.conf.urls import url
from django.urls import include, path
from rest_framework.routers import SimpleRouter
# from . import views
from . import views

app_name = 'nts'

router = SimpleRouter(trailing_slash=False)
router.register(r'AuditEvent', views.ingestAuditEvent, basename="Test_API")
router.register(r'AuditEvent/', views.ingestAuditEvent, basename="Test_API")


urlpatterns = [ 
    path('', include(router.urls)),
]