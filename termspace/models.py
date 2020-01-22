from django.db import models
from django.utils import timezone

class TermspaceComments(models.Model):
    task_id = models.CharField(max_length=300)
    concept = models.CharField(max_length=300)
    fsn = models.CharField(max_length=600)
    assignee = models.CharField(max_length=300)
    status = models.CharField(max_length=300)
    folder = models.CharField(max_length=600)
    time = models.CharField(max_length=300)
    comment = models.TextField()