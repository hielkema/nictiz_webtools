from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User

## Patients
class Patient(models.Model):
    firstname       = models.CharField(max_length=100)
    surname         = models.CharField(max_length=100)
    initials        = models.CharField(max_length=100)
    dob             = models.CharField(max_length=500, default=None, null=True, blank=True)
    gender_options  = [
        # (code, readable)
        ('0', 'Onbekend'),
        ('1', 'Man'),
        ('2', 'Vrouw'),
    ]
    gender          = models.CharField(max_length=2, choices=gender_options, default=0)
    address_street  = models.CharField(max_length=500, default=None, null=True, blank=True)
    address_city    = models.CharField(max_length=500, default=None, null=True, blank=True)
    address_country = models.CharField(max_length=500, default=None, null=True, blank=True)
    bsn             = models.IntegerField(default=None, null=True, blank=True)
    created         = models.DateTimeField(default=timezone.now)
    edited          = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return str(self.id) + " " + self.surname + " " + self.gender

class Decursus(models.Model):
    patient     = models.ForeignKey('Patient', on_delete=models.PROTECT)
    user        = models.ForeignKey(User, on_delete=models.PROTECT)
    anamnese    = models.TextField(default=None, null=True, blank=True)
    created     = models.DateTimeField(default=timezone.now)
    edited      = models.DateTimeField(default=timezone.now)

class ZibProbleem(models.Model):
    patient     = models.ForeignKey('Patient', on_delete=models.PROTECT)
    user        = models.ForeignKey(User, on_delete=models.PROTECT)
    created     = models.DateTimeField(default=timezone.now)
    edited      = models.DateTimeField(default=timezone.now)
    
    ProbleemType        = models.TextField(default=None, null=True, blank=True)
    ProbleemNaam        = models.ForeignKey('mapping.MappingCodesystemComponent', on_delete=models.PROTECT)
    ProbleemBeginDatum  = models.TextField(default=None, null=True, blank=True)
    ProbleemEindDatum   = models.TextField(default=None, null=True, blank=True)
    ProbleemStatus      = models.TextField(default=None, null=True, blank=True)
    VerificatieStatus   = models.TextField(default=None, null=True, blank=True)
    Decursus            = models.ForeignKey('Decursus', on_delete=models.PROTECT)
    comments            = models.TextField(default=None, null=True, blank=True)
    