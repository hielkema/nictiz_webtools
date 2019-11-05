from django.db import models
from django.utils import timezone

class taskRecord(models.Model):
    username = models.CharField(max_length=30)
    timestamp = models.DateTimeField(default=timezone.now)
    task = models.CharField(max_length=30, default="onbekend")
    searchterm = models.CharField(max_length=30, default="onbekend")
    conceptFSN = models.CharField(max_length=500, default="onbekend")
    execution_time = models.DecimalField(max_digits=50, decimal_places=2)
    output_available = models.BooleanField(default=True)
    filename = models.CharField(max_length=500, default="onbekend")
    celery_task_id = models.CharField(max_length=120, default="onbekend")
    finished = models.BooleanField(default=False)

    def __str__(self):
        return str(self.id)+" "+self.username+" - "+self.conceptFSN