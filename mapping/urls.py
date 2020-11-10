from django.conf.urls import url
from django.urls import include, path
from rest_framework.routers import SimpleRouter

from . import views

app_name = 'mapping'

# Define DRF URL router
router_1_0 = SimpleRouter()
router_1_0.register(r'export_rc_rules', views.exportReleaseCandidateRules, basename="export_rc_rules")
router_1_0.register(r'export_rc_rules_v2', views.exportReleaseCandidateRulesV2, basename="export_rc_rules")
router_1_0.register(r'rc_export_fhir_json', views.RCFHIRConceptMap, basename="RC FHIR ConceptMap")
router_1_0.register(r'fhir_conceptmap_list', views.RCFHIRConceptMapList, basename="RC_FHIR_ConceptMap_List")
router_1_0.register(r'export_rcs', views.ReleaseCandidates, basename="export_rcs")
router_1_0.register(r'rc_rule_review', views.RCRuleReview, basename="rc_rule_review")

router_1_0.register(r'tasks_manager', views.MappingTasks, basename="Mapping_Tasks")
router_1_0.register(r'change_tasks', views.ChangeMappingTasks, basename="Change_Mapping_Tasks")
router_1_0.register(r'create_tasks', views.CreateTasks, basename="Create_Mapping_Tasks")

router_1_0.register(r'progress', views.progressReturnAll, basename="progress_reports_Return_All")

router_1_0.register(r'audits', views.MappingAudits, basename="Audits")
router_1_0.register(r'audits_per_project', views.MappingAuditsPerProject, basename="Audits per project")
router_1_0.register(r'audit_whitelist', views.MappingAuditWhitelist, basename="Audits whitelist")
router_1_0.register(r'audit_remove_whitelist', views.MappingAuditRemoveWhitelist, basename="Audits remove whitelist")
router_1_0.register(r'audit_remove', views.MappingAuditRemove, basename="Audits remove")
router_1_0.register(r'audit_trigger', views.MappingTriggerAudit, basename="Audits trigger")
router_1_0.register(r'audit_project_trigger', views.MappingTriggerProjectAudit, basename="Audits trigger")
router_1_0.register(r'audit_status', views.MappingAuditStatus, basename="Audits status")

router_1_0.register(r'snomed_failback_import', views.SnomedFailbackImport, basename="Import SNOMED - backup system")

router_1_0.register(r'codesystems', views.Codesystems, basename="Mapping Codesystems")
router_1_0.register(r'projects', views.Projects, basename="Mapping Projects")
router_1_0.register(r'tasklist', views.Tasklist, basename="Mapping tasks")
router_1_0.register(r'taskdetails', views.TaskDetails, basename="Mapping tasks")
router_1_0.register(r'events_and_comments', views.EventsAndComments, basename="Mapping events and comments")
router_1_0.register(r'mappings', views.MappingTargets, basename="Mappings")
router_1_0.register(r'mappings_ecl_to_rules', views.MappingEclToRules, basename="Mapping ECL To Rules")
router_1_0.register(r'mapping_exclusions', views.MappingExclusions, basename="Mapping exclusions")
router_1_0.register(r'mapping_reverse_exclusions', views.ReverseMappingExclusions, basename="Mapping reverse exclusions")
router_1_0.register(r'remove_rules', views.MappingRemoveRules, basename="Remove rules for task")
router_1_0.register(r'mapping_add_from_reverse', views.MappingTargetFromReverse, basename="Add a rule from a reverse mapping")
router_1_0.register(r'mapping_add_remote_exclusion', views.AddRemoteExclusion, basename="Add a remote exclusion")

router_1_0.register(r'reverse', views.MappingReverse, basename="Reverse mappings")
router_1_0.register(r'mapping_dialog', views.MappingDialog, basename="Mappings")
router_1_0.register(r'componentsearch', views.MappingTargetSearch, basename="Component search endpoint")
router_1_0.register(r'search_by_component', views.RuleSearchByComponent, basename="Search by mapping rule components")
router_1_0.register(r'statuses', views.MappingStatuses, basename="Mapping statuses for selected project")
router_1_0.register(r'users', views.MappingUsers, basename="Mapping users for selected project")
router_1_0.register(r'comments', views.MappingPostComment, basename="Mapping comments for selected task")

router_1_0.register(r'list_lookup', views.MappingListLookup, basename="Retrieve mapping rules from list of components")
router_1_0.register(r'rules_by_codesystem', views.MappingRulesInvolvingCodesystem, basename="Retrieve components used in rules by codesystem")

urlpatterns = [
    # DRF router
    path(r'api/1.0/', include(router_1_0.urls)),

    # The last remnants of the old static interface
    url(r'updatecodesystems/', views.api_UpdateCodesystems_post.as_view(), name='updatecodesystems'),
    url(r'', views.vue_MappingIndex.as_view(), name='index'),
]