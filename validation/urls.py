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
router.register(r'task_count', total_number_of_tasks, basename="Count all tasks")
router.register(r'send_form', receive_form, basename="Handle post requests")
router.register(r'next_task', next_task, basename="Send user the next task")
router.register(r'create_tasks', create_tasks, basename="Add users to tasks")

router.register(r'all_users', all_users, basename="Send all users")
router.register(r'user_stats', user_stats, basename="Stats for all users")


router.register(r'export_answers', export_answers, basename="Provide all answer data for export")


urlpatterns = [ 
    path('', include(router.urls)),
]