from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register(MappingProject)
admin.site.register(MappingCodesystemComponent)
admin.site.register(MappingCodesystem)
admin.site.register(MappingTask)
admin.site.register(MappingTaskStatus)
admin.site.register(MappingRule)
admin.site.register(MappingEclQuery)
admin.site.register(MappingComment)
admin.site.register(MappingEventLog)
admin.site.register(MappingTaskAudit)
admin.site.register(MappingProgressRecord)
admin.site.register(MappingReleaseCandidate)
admin.site.register(MappingReleaseCandidateRules)
admin.site.register(MappingReleaseCandidateFHIRConceptMap)
admin.site.register(MappingEclPart)