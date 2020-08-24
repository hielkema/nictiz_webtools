from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register(TermspaceComments)
admin.site.register(TermspaceMeta)
admin.site.register(TermspaceTask)
admin.site.register(TermspaceProgressReport)
admin.site.register(TermspaceUserReport)
admin.site.register(SnomedTree)