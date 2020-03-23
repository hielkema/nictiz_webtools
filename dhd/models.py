from django.db import models
from django.utils import timezone

class TermspaceComments(models.Model):
    task_id = models.CharField(max_length=300, default=None, null=True, blank=True)
    concept = models.CharField(max_length=300, default=None, null=True, blank=True)
    fsn = models.CharField(max_length=600, default=None, null=True, blank=True)
    assignee = models.CharField(max_length=300, default=None, null=True, blank=True)
    status = models.CharField(max_length=300, default=None, null=True, blank=True)
    folder = models.CharField(max_length=600, default=None, null=True, blank=True)
    time = models.CharField(max_length=300, default=None, null=True, blank=True)
    comment = models.TextField()

class EclQueryResults(models.Model):
    component_id        = models.CharField(max_length=50)
    component_title     = models.CharField(max_length=500)
    component_created   = models.DateTimeField(default=timezone.now)
    component_extra_dict = models.TextField(default=None, null=True, blank=True)
    parents             = models.TextField(default=None, null=True, blank=True)
    children            = models.TextField(default=None, null=True, blank=True)
    descendants         = models.TextField(default=None, null=True, blank=True)
    ancestors           = models.TextField(default=None, null=True, blank=True)