from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register(Project)
admin.site.register(Status)
admin.site.register(Task)
# admin.site.register(Question)
admin.site.register(Answer)