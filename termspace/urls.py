# howdy/urls.py
from django.conf.urls import url
from django.urls import include, path
from rest_framework.routers import SimpleRouter
# from . import views
from .views import *

app_name = 'termspace'

router = SimpleRouter()
# router.register(r'termspace_comments', termspaceComments, basename="termspace_comments")
router.register(r'search_comments', searchTermspaceComments, basename="termspace_comments")
router.register(r'component_api', componentApi, basename="component_api")
router.register(r'ecl_api', eclQueryApi, basename="ecl_query_api")
router.register(r'cached_results', cached_results, basename="cached_results")

router.register(r'snomed_json_tree', SnomedJSONTree, basename="snomed_json_tree")

router.register(r'mapping_json', jsonMappingExport, basename="mapping_export_json")
router.register(r'mapping_comments', searchMappingComments, basename="mapping_comments")
router.register(r'mapping_progress', Mapping_Progressreport_perProject, basename="mapping_progress")
router.register(r'mapping_progress_per_status', Mapping_Progressreport_perStatus, basename="mapping_progress")
router.register(r'mapping_progress_over_time', Mapping_Progressreport_overTime, basename="mapping_progress_over_time")

router.register(r'fetch_termspace_tasksupply', fetch_termspace_tasksupply, basename="fetch_termspace_tasksupply")
router.register(r'fetch_termspace_tasksupply_v2', fetch_termspace_tasksupply_v2, basename="fetch_termspace_tasksupply_v2")
router.register(r'fetch_termspace_user_tasksupply', fetch_termspace_user_tasksupply, basename="fetch_termspace_user_tasksupply")

urlpatterns = [ 
    path('', include(router.urls)),
]