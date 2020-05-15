from django.db import models
from django.utils import timezone

class template(models.Model):
    title = models.CharField(max_length=300)
    description = models.TextField(default=None)
    root_concept = models.OneToOneField("rootConcept", default=None, blank=True, null=True, related_name="rootAttribute", on_delete=models.PROTECT)
    attributes = models.ManyToManyField("attributeSet", related_name="AttributeSets", default=None, blank=True)
    
    def __str__(self):
        return self.title

class rootConcept(models.Model):
    fsn = models.CharField(max_length=300)
    sctid = models.CharField(max_length=300)

    def __str__(self):
        return self.fsn
class attributeSet(models.Model):
    template = models.OneToOneField("template", default=None, blank=True, null=True, related_name="Template", on_delete=models.PROTECT)
    description = models.TextField(default=None)
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