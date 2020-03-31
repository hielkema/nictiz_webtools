from django.conf.urls import url
from django.urls import include, path
from rest_framework.routers import SimpleRouter

from . import views

app_name = 'mapping'

# Define DRF URL router
router_1_0 = SimpleRouter()
router_1_0.register(r'export_rc_rules', views.exportReleaseCandidateRules, basename="export_rc_rules")
router_1_0.register(r'rc_export_fhir_json', views.RCFHIRConceptMap, basename="RC FHIR ConceptMap")
router_1_0.register(r'fhir_conceptmap_list', views.RCFHIRConceptMapList, basename="RC_FHIR_ConceptMap_List")
router_1_0.register(r'export_rcs', views.ReleaseCandidates, basename="export_rcs")
router_1_0.register(r'rc_rule_review', views.RCRuleReview, basename="rc_rule_review")

router_1_0.register(r'tasks', views.MappingTasks, basename="Mapping_Tasks")
router_1_0.register(r'change_tasks', views.ChangeMappingTasks, basename="Change_Mapping_Tasks")

router_1_0.register(r'progress', views.progressReturnAll, basename="progress_reports_Return_All")

urlpatterns = [
    # DRF router
    path(r'api/1.0/', include(router_1_0.urls)),

    # API based views
    url(r'api/componentsearch/', views.api_TargetSearch_get.as_view(), name='targetsearch'),
    
    url(r'api/task/get/project/(?P<project_id>\w+)', views.api_TaskList_get.as_view(), name='api_task_get'),
    url(r'api/task/get/(?P<task>\w+)', views.api_TaskId_get.as_view(), name='api_task_get'),

    url(r'api/comment/del/', views.api_DelComment_post.as_view(), name='delcomment'),
    url(r'api/comment/put/', views.api_PostComment_post.as_view(), name='postcomment'),

    url(r'api/user/get/', views.api_User_get.as_view(), name='users'),
    
    url(r'api/eclquery/get/(?P<task>\w+)', views.api_EclQuery_get.as_view(), name='eclquery'),
    url(r'api/eclquery/put/', views.api_EclQuery_put.as_view(), name='eclquery'),
    
    url(r'api/reverse_mapping/get/(?P<task>\w+)', views.api_ReverseMapping_get.as_view(), name='reversemapping'),
    
    url(r'api/mapping/get/(?P<task>\w+)', views.api_Mapping_get.as_view(), name='mapping'),
    url(r'api/mapping/put/', views.api_Mapping_post.as_view(), name='mapping'),
    
    url(r'api/general/get/(?P<project>\w+)', views.api_GeneralData_get.as_view(), name='general_data'),
    
    url(r'api/hashtag/post/', views.api_hashtag_post.as_view(), name='api_hashtag_post'),

    url(r'api/audit/get/(?P<task>\w+)', views.api_GetAudit_get.as_view(), name='get_audit'),
    url(r'api/audit/post/', views.api_WhitelistAudit_post.as_view(), name='whitelist_audit'),

    url(r'api/permissions/get/', views.api_Permissions_get.as_view(), name='permissions'),
    
    url(r'api/taskuser/put/', views.api_UserChange_post.as_view(), name='change_status'),
    
    url(r'api/status/put/', views.api_StatusChange_post.as_view(), name='change_status'),
    
    url(r'api/events/get/task/(?P<task>\w+)', views.api_EventList_get.as_view(), name='events'),

    url(r'api/updatecodesystems/put/', views.api_UpdateCodesystems_post.as_view(), name='updatecodesystems'),
    url(r'updatecodesystems/', views.api_UpdateCodesystems_post.as_view(), name='updatecodesystems'),

    # V2 static views
    url(r'project/(?P<project>\w+)/task/(?P<task>\w+)', views.vue_TaskEditor.as_view(), name='task_editor'),
    url(r'project/(?P<project>\w+)/task/', views.vue_TaskEditor.as_view(), name='task_editor'),
    url(r'project/(?P<project>\w+)', views.vue_ProjectIndex.as_view(), name='project_index'),

    # V1 static views
    url(r'project/?project_id=(?P<project>\w+)', views.ProjectIndexPageView.as_view(), name='project_index'),
    url(r'taskmanager/(?P<project>\w+)', views.TaskManagerPageView.as_view(), name='taskmanager_project'),
    url(r'taskmanager', views.TaskManagerPageView.as_view(), name='taskmanager'),

    url(r'ajaxprogressreport/(?P<secret>\w+)', views.AjaxProgressRecordPageView.as_view(), name='ajaxprogressreport'),
    url(r'audit/(?P<project>\w+)/(?P<audit_type>\w+)', views.AuditPageView.as_view(), name='audit'),

    url(r'task_create', views.TaskCreatePageView.as_view(), name='task_create'),

    url(r'', views.vue_MappingIndex.as_view(), name='index'),
]