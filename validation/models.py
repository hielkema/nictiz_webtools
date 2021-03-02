from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.core.serializers.json import DjangoJSONEncoder

class Project(models.Model):
    created         = models.DateTimeField(default=timezone.now)
    title           = models.CharField(max_length=300, default=None, null=True, blank=True)
    type            = models.CharField(max_length=300, default=None, null=True, blank=True)
    access          = models.ManyToManyField(User, related_name="validation_access_user", default=None, blank=True)
    finished_status = models.ForeignKey('Status', related_name="status_finished", on_delete=models.PROTECT, blank=True, null=True, default=None)
    new_status      = models.ForeignKey('Status', related_name="status_new_tasks", on_delete=models.PROTECT, blank=True, null=True, default=None)
    
    def __str__(self):
        return str(self.id) + " " + self.title

class Status(models.Model):
    project     = models.ForeignKey('Project', related_name="status_project_validation", on_delete=models.PROTECT, blank=True, null=True, default=None)
    title       = models.CharField(max_length=300, default=None, null=True, blank=True)
    next        = models.ForeignKey('Status', related_name="status_next", on_delete=models.PROTECT, blank=True, null=True, default=None)
    previous    = models.ForeignKey('Status', related_name="status_previous", on_delete=models.PROTECT, blank=True, null=True, default=None)
    
    def __str__(self):
        return str(self.id) + " " + self.title

class Task(models.Model):
    created     = models.DateTimeField(default=timezone.now)
    project     = models.ForeignKey('Project', related_name="task_project_validation", on_delete=models.PROTECT, blank=True, null=True, default=None)
    data        = models.JSONField(encoder=DjangoJSONEncoder, default=dict, blank=True, null=True)
    # status      = models.ForeignKey('Status', related_name="status_current", on_delete=models.PROTECT, blank=True, null=True, default=None)
    access      = models.ManyToManyField(User, related_name="validation_task_users", default=None, blank=True)
    # user        = models.ForeignKey(User, related_name="status_current", on_delete=models.PROTECT, blank=True, null=True, default=None)
    
# class Question(models.Model):
#     created     = models.DateTimeField(default=timezone.now)
#     task        = models.ForeignKey('Task', on_delete=models.PROTECT, blank=True, null=True, default=None)
#     data        = models.JSONField(encoder=DjangoJSONEncoder, default=dict, blank=True, null=True)
    
class Answer(models.Model):
    created     = models.DateTimeField(default=timezone.now)
    # question    = models.ForeignKey('Question', on_delete=models.PROTECT, blank=True, null=True, default=None)
    task        = models.ForeignKey('Task', on_delete=models.PROTECT, blank=True, null=True, default=None)
    user        = models.ForeignKey(User, related_name="answer_user", on_delete=models.PROTECT, blank=True, null=True, default=None)
    data        = models.JSONField(encoder=DjangoJSONEncoder, default=dict, blank=True, null=True)