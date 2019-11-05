from django.db import models
from django.utils import timezone

class MedicationLookup(models.Model):
    username = models.CharField(max_length=30)
    timestamp = models.DateTimeField(default=timezone.now)
    searchterm = models.CharField(max_length=30, default="onbekend")
    execution_time = models.CharField(max_length=30)

    def __str__(self):
        return self.searchterm