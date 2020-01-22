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