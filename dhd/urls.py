# howdy/urls.py
from django.conf.urls import url
from django.urls import include, path
from rest_framework.routers import SimpleRouter
# from . import views
from .views import *

app_name = 'dhd'

router = SimpleRouter()
# router.register(r'termspace_comments', termspaceComments, basename="termspace_comments")
router.register(r'search', searchChipsoft, basename="search")
router.register(r'children', searchChipsoftChildren, basename="children")
router.register(r'parents', searchChipsoftParents, basename="parents")
router.register(r'concept', searchChipsoftConcept, basename="concept")

router.register(r'postcodemo_templates', searchChipsoftConcept, basename="postco templates")
router.register(r'postcodemo_attributevalues', searchChipsoftConcept, basename="postco templates attr-values")


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