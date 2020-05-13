from django.db import models
from django.utils import timezone

class template(models.Model):
    title = models.CharField(max_length=300)
    description = models.TextField(default=None)
    attributes = models.ManyToManyField("attribute", default=None, blank=True)
    root_concept = models.OneToOneField("attributeValue", default=None, blank=True, null=True, related_name="rootAttribute", on_delete=models.PROTECT)
    def __str__(self):
        return self.title

class attribute(models.Model):
    fsn = models.CharField(max_length=300)
    sctid = models.CharField(max_length=300)
    attribute_values = models.ManyToManyField("attributeValue", default=None, blank=True)

    def __str__(self):
        return self.fsn

class attributeValue(models.Model):
    fsn = models.CharField(max_length=300)
    sctid = models.CharField(max_length=300)

    def __str__(self):
        return self.fsn