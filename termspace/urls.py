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
router.register(r'snomed_json_tree', SnomedJSONTree, basename="snomed_json_tree")
# router.register(r'test_post_endpoint', ShareView, basename="testpoint_post")

# urlpatterns = router.urls

# urlpatterns = [
#     #url(r'medicatie/', views.get_name, name='medicatie'),
#     url('', include(router.urls)),
#     url(r'api/search_comments/(?P<term>.+?)/', views.api_SearchcommentsPageView.as_view(), name='search_api'),
#     url(r'search_comments/', views.SearchcommentsPageView.as_view(), name='search'),
# ]

urlpatterns = [ 
    # path('search_comments/(?P<term>.+?)/', SearchComments.as_view(), name="test"),
    path('', include(router.urls)),
]