from django.db import models
from django.utils import timezone
from django.contrib.postgres.fields import JSONField
from django.core.serializers.json import DjangoJSONEncoder

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

class TermspaceMeta(models.Model):
    username = models.CharField(max_length=300, default=None, null=True, blank=True)
    token = models.CharField(max_length=300, default=None, null=True, blank=True)

class TermspaceTask(models.Model):
    task_id     = models.CharField(max_length=300, default=None, null=True, blank=True)
    data        = JSONField(default=None, null=True, blank=True)

class TermspaceUserReport(models.Model):
    time   = models.DateTimeField(default=timezone.now)
    username = models.CharField(max_length=50, default=None, null=True, blank=True)
    status = models.CharField(max_length=50, default=None, null=True, blank=True)
    count = models.IntegerField(default=None, null=True, blank=True)
    def __str__(self):
        return str(self.id) + ': ' + str(self.time) + ' ' + str(self.username) + ' ' + str(self.status) + '\t[' + str(self.count) + ']'

class TermspaceProgressReport(models.Model):
    time   = models.DateTimeField(default=timezone.now)
    description = models.TextField(default=None, null=True, blank=True)
    tag = models.CharField(max_length=50, default=None, null=True, blank=True)
    title = models.CharField(max_length=50, default=None, null=True, blank=True)
    count = models.IntegerField(default=None, null=True, blank=True)
    def __str__(self):
        return str(self.id) + ': ' + str(self.time) + ' ' + str(self.title) + '\t[' + str(self.count) + ']'