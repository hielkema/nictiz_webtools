from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.contrib.postgres.fields import JSONField
from django.core.serializers.json import DjangoJSONEncoder

class MappingProject(models.Model):
    title = models.CharField(max_length=300)
    active = models.BooleanField(default=True)
    created = models.DateTimeField(default=timezone.now)
    status_complete = models.ForeignKey('MappingTaskStatus', related_name="status_complete", on_delete=models.PROTECT, blank=True, null=True, default=None)
    status_rejected = models.ForeignKey('MappingTaskStatus', related_name="status_rejected", on_delete=models.PROTECT, blank=True, null=True, default=None)

    project_types_options = [
        # (code, readable)
        ('1', 'One to Many'),
        ('2', 'Many to One'),
        ('3', 'Many to Many'),
        ('4', 'Snomed ECL to one'),
    ]
    project_type  = models.CharField(max_length=50, choices=project_types_options, default=None, blank=True, null=True)

    source_codesystem = models.ForeignKey('MappingCodesystem', on_delete=models.PROTECT, related_name = 'project_source', default=None, blank=True, null=True)
    target_codesystem = models.ForeignKey('MappingCodesystem', on_delete=models.PROTECT, related_name = 'project_target', default=None, blank=True, null=True)

    use_mapgroup = models.BooleanField(blank=True, null=True, default=False)
    use_mappriority = models.BooleanField(blank=True, null=True, default=False)
    use_mapcorrelation = models.BooleanField(blank=True, null=True, default=False)
    use_mapadvice = models.BooleanField(blank=True, null=True, default=False)
    use_maprule = models.BooleanField(blank=True, null=True, default=False)
    use_rulebinding = models.BooleanField(blank=True, null=True, default=False)

    def __str__(self):
        return str(self.id) + " " + self.title

class MappingCodesystem(models.Model):
    codesystem_title    = models.CharField(max_length=50)
    codesystem_version  = models.CharField(max_length=50)
    codesystem_fhir_uri = models.CharField(max_length=500, default=None, null=True, blank=True)
    component_fhir_uri = models.CharField(max_length=500, default=None, null=True, blank=True)
    component_created   = models.DateTimeField(default=timezone.now)
    codesystem_extra_1  = models.CharField(max_length=500, default=None, null=True, blank=True)
    codesystem_extra_2  = models.CharField(max_length=500, default=None, null=True, blank=True)
    codesystem_extra_3  = models.CharField(max_length=500, default=None, null=True, blank=True)
    codesystem_extra_4  = models.CharField(max_length=500, default=None, null=True, blank=True)
    codesystem_extra_5  = models.CharField(max_length=500, default=None, null=True, blank=True)
    codesystem_extra_6  = models.CharField(max_length=500, default=None, null=True, blank=True)
    codesystem_extra_7  = models.CharField(max_length=500, default=None, null=True, blank=True)

    def __str__(self):
        return str(self.id) + " " + self.codesystem_title + " " + self.codesystem_version


class MappingComment(models.Model):
    comment_title       = models.CharField(max_length=50)
    comment_task        = models.ForeignKey('MappingTask', on_delete=models.PROTECT)
    comment_body        = models.TextField(max_length=500)
    # comment_user        = models.ForeignKey(User, on_delete=models.CASCADE)
    comment_user        = models.ForeignKey(User, on_delete=models.PROTECT)
    comment_created     = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return str(self.id) + " " + str(self.comment_task.id) + " " + self.comment_user.username


class MappingCodesystemComponent(models.Model):
    # codesystem_id       = models.CharField(max_length=50)
    codesystem_id       = models.ForeignKey('MappingCodesystem', on_delete=models.PROTECT)
    component_id        = models.CharField(max_length=50)
    component_title     = models.CharField(max_length=500)
    component_created   = models.DateTimeField(default=timezone.now)
    descriptions        = JSONField(default=None, null=True, blank=True)
    component_extra_dict = JSONField(default=None, null=True, blank=True)
    parents             = models.TextField(default=None, null=True, blank=True)
    children            = models.TextField(default=None, null=True, blank=True)
    descendants         = models.TextField(default=None, null=True, blank=True)
    ancestors           = models.TextField(default=None, null=True, blank=True)
    component_extra_5  = models.CharField(max_length=500, default=None, null=True, blank=True)
    component_extra_6  = models.CharField(max_length=500, default=None, null=True, blank=True)
    component_extra_7  = models.CharField(max_length=500, default=None, null=True, blank=True)


    def __str__(self):
        return str(self.id) + " " + self.component_title


class MappingTask(models.Model):
    project_id = models.ForeignKey('MappingProject', on_delete=models.PROTECT)
    source_component = models.ForeignKey('MappingCodesystemComponent', on_delete=models.PROTECT) # Uniek ID in codesystem = MappingCodesystemComponent:id
    source_codesystem = models.ForeignKey('MappingCodesystem', on_delete=models.PROTECT, related_name = 'source_codesystem_task', default=None, null=True, blank=True) # Uniek ID van codesystem waar vandaan in deze taak gemapt moet worden
    target_codesystem = models.ForeignKey('MappingCodesystem', on_delete=models.PROTECT, related_name = 'target_codesystem_task', default=None, null=True, blank=True) # Uniek ID van codesystem waar naartoe in deze taak gemapt moet worden
    user = models.ForeignKey(User, on_delete=models.PROTECT, default=None, null=True, blank=True) # ID van gebruiker
    status = models.ForeignKey('MappingTaskStatus', on_delete=models.PROTECT, default=None, null=True, blank=True) # ID van status
    task_created   = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return '{}: {} * source component {}'.format(
            self.id,
            self.project_id,
            self.source_component,
            )


class MappingTaskStatus(models.Model):
    project_id = models.ForeignKey('MappingProject', on_delete=models.PROTECT)
    status_title = models.CharField(max_length=50) # Uniek ID in codesystem = MappingCodesystemComponent:id
    status_id = models.IntegerField() # Uniek ID van codesystem waar vandaan in deze taak gemapt moet worden
    status_description = models.CharField(max_length=50) # Uniek ID van codesystem waar naartoe in deze taak gemapt moet worden
    status_next = models.CharField(max_length=50) # ID van gebruiker

    def __str__(self):
        return str(self.id) + " Status ID: " + str(self.status_id) + " @ project " + str(self.project_id) + ": " + self.status_title


class MappingRule(models.Model):
    id = models.BigAutoField(primary_key=True)
    project_id = models.ForeignKey('MappingProject', on_delete=models.PROTECT)
    source_component = models.ForeignKey('MappingCodesystemComponent', on_delete=models.PROTECT, related_name = 'source_component_rule') # Component ID in source codesystem = MappingCodesystems:component_id
    target_component = models.ForeignKey('MappingCodesystemComponent', on_delete=models.PROTECT, related_name = 'target_component_rule') # Uniek ID van codesystem waar naartoe in deze taak gemapt moet worden
    
    mapgroup        = models.IntegerField(default=None, blank=True, null=True)
    mappriority     = models.IntegerField(default=None, blank=True, null=True)
    correlation_options = [
        # (code, readable)
        ('447559001', 'Broad to narrow'),
        ('447557004', 'Exact match'),
        ('447558009', 'Narrow to broad'),
        ('447560006', 'Partial overlap'),
        ('447556008', 'Not mappable'),
        ('447561005', 'Not specified'),
    ]
    mapcorrelation  = models.CharField(max_length=50, choices=correlation_options, default=None, blank=True, null=True)
    mapadvice       = models.CharField(max_length=500, default=None, blank=True, null=True)
    maprule         = models.CharField(max_length=500, default=None, blank=True, null=True)
    mapspecifies    = models.ManyToManyField("MappingRule")

    active = models.BooleanField(max_length=50, null=True) # Actief of deprecated rule

    # def __str__(self):
    #     return str(self.id), str(self.project_id.title), str(self.source_component.component_title)

class MappingEclQuery(models.Model):
    project_id          = models.ForeignKey('MappingProject', on_delete=models.PROTECT)
    target_component    = models.ForeignKey('MappingCodesystemComponent', on_delete=models.PROTECT) # Uniek ID van codesystem waar naartoe in deze taak gemapt moet worden
    query               = models.TextField(default=None, blank=True, null=True)
    
    type_options = [
        # (code, readable)
        ('1', 'Children'),
        ('2', 'Descendants and self'),
        ('3', 'Custom'),
    ]
    query_type  = models.CharField(max_length=50, choices=type_options, default=None, blank=True, null=True)

    function_options = [
        # (code, readable)
        ('1', 'MINUS'),
        ('2', 'ADD'),
        ('3', 'Custom'),
    ]
    query_function  = models.CharField(max_length=50, choices=function_options, default=None, blank=True, null=True)

class MappingEventLog(models.Model):
    task = models.ForeignKey('MappingTask', on_delete=models.PROTECT)
    action_options = [
        ('status_change', 'Status wijzigen'),
        ('user_change', 'Toegewezen aan gebruiker'),
    ]
    action = models.CharField(max_length=500, choices=action_options) # Beschrijving van actie (status_update)
    action_description = models.CharField(max_length=500) # Leesbare beschrijving van actie (Status gewijzigd)
    action_user = models.ForeignKey(User, on_delete=models.PROTECT, related_name = 'event_action_user', default=None, blank=True, null=True) # Huidige gebruiker
    old_data = models.TextField() # Oude situatie - payload
    new_data = models.TextField() # Nieuwe situatie - payload
    old = models.TextField() # Oude situatie - leesbaar
    new = models.TextField() # Nieuwe situatie - leesbaar
    user_source = models.ForeignKey(User, on_delete=models.PROTECT, related_name = 'user_event_source') # Huidige gebruiker
    user_target = models.ForeignKey(User, on_delete=models.PROTECT, related_name = 'user_event_target', default=None, blank=True, null=True) # Gebruiker waaraan gerefereerd wordt, niet verplicht
    event_time   = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return str(self.id) + " Task ID: " + str(self.task.id) + " Actie: " + str(self.action_description)

class MappingProgressRecord(models.Model):
    name = models.TextField()
    project = models.ForeignKey('MappingProject', on_delete=models.PROTECT)
    labels = models.TextField()
    values = models.TextField()
    time = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return str(self.id) + " " + str(self.project) +" " + self.name

class MappingTaskAudit(models.Model):
    audit_type = models.TextField()
    task = models.ForeignKey("MappingTask", on_delete=models.PROTECT)
    hit_reason = models.TextField(default=None, blank=True, null=True)
    comment = models.TextField(default=None, blank=True, null=True)
    ignore = models.BooleanField(default=False)
    ignore_user = models.ForeignKey(User, default=None, blank=True, null=True, on_delete=models.PROTECT)
    first_hit_time  = models.DateTimeField(default=timezone.now)

class MappingReleaseCandidate(models.Model):
    title = models.TextField(default=None, blank=True, null=True)

    metadata_id = models.TextField(default=None, blank=True, null=True)
    metadata_url = models.TextField(default=None, blank=True, null=True)
    metadata_description = models.TextField(default=None, blank=True, null=True)
    metadata_version = models.TextField(default=None, blank=True, null=True)
    metadata_experimental = models.BooleanField(default=True)
    metadata_date = models.TextField(default=None, blank=True, null=True)
    metadata_publisher = models.TextField(default=None, blank=True, null=True)
    metadata_contact = models.TextField(default=None, blank=True, null=True)
    metadata_copyright = models.TextField(default=None, blank=True, null=True)
    metadata_sourceCanonical = models.TextField(default=None, blank=True, null=True)

    codesystem = models.ForeignKey('MappingCodesystem', on_delete=models.PROTECT, related_name = 'source_codesystem', default=None, blank=True, null=True)
    finished = models.BooleanField(default=False)
    # Perhaps status should be coming from the status DB table - text for now
    status_options = [
        # (code, readable)
        ('0', 'Testing'),
        ('1', 'Experimental'),
        ('2', 'Acceptance'),
        ('3', 'Production'),
    ]
    status = models.CharField(default=None, max_length=50, blank=True, null=True, choices=status_options)
    created = models.DateTimeField(default=timezone.now)

class MappingReleaseCandidateFHIRConceptMap(models.Model):
    title = models.TextField(default=None, blank=True, null=True)
    release_notes = models.TextField(default=None, blank=True, null=True)

    rc = models.ForeignKey('MappingReleaseCandidate', on_delete=models.PROTECT, default=None, blank=True, null=True)
    
    codesystem = models.ForeignKey('MappingCodesystem', on_delete=models.PROTECT, related_name = 'source_codesystem_for_rc', default=None, blank=True, null=True)
    created = models.DateTimeField(default=timezone.now)

    deprecated = models.BooleanField(default=False)

    data = JSONField(encoder=DjangoJSONEncoder)

class MappingReleaseCandidateRules(models.Model):
    # Contains the individual rules to be included in the MappingReleaseCandidate
    export_rc   = models.ForeignKey("MappingReleaseCandidate", on_delete=models.PROTECT, default=None, null=True, blank=True)
    # Export data
    export_date = models.DateTimeField(default=timezone.now)
    export_user = models.ForeignKey(User, on_delete=models.PROTECT, default=None, null=True, blank=True)
    # Foreign key bound task used for export
    export_task = models.ForeignKey('MappingTask', on_delete=models.PROTECT, default=None, blank=True, null=True)
    # Foreign key bound rule used for export
    export_rule = models.ForeignKey('MappingRule', on_delete=models.PROTECT, default=None, blank=True, null=True)
    # Denormalized task data
    task_status = models.TextField(default=None, blank=True, null=True)
    task_user = models.TextField(default=None, blank=True, null=True)
    # Denormalized source component
    source_component = models.ForeignKey('MappingCodesystemComponent', on_delete=models.PROTECT, related_name = 'source_component', default=None, blank=True, null=True)
    static_source_component_ident = models.CharField(max_length=50, default=None, blank=True, null=True)
    static_source_component = models.TextField(default=None, blank=True, null=True)
    # Denormalized target component
    target_component = models.ForeignKey('MappingCodesystemComponent', on_delete=models.PROTECT, related_name = 'target_component', default=None, blank=True, null=True)
    static_target_component_ident = models.CharField(max_length=50, default=None, blank=True, null=True)
    static_target_component = models.TextField(default=None, blank=True, null=True)
    # Denormalized rule components
    mapgroup        = models.IntegerField(default=None, blank=True, null=True)
    mappriority     = models.IntegerField(default=None, blank=True, null=True)
    correlation_options = [
        # (code, readable)
        ('447559001', 'Broad to narrow'),
        ('447557004', 'Exact match'),
        ('447558009', 'Narrow to broad'),
        ('447560006', 'Partial overlap'),
        ('447556008', 'Not mappable'),
        ('447561005', 'Not specified'),
    ]
    mapcorrelation  = models.CharField(max_length=50, choices=correlation_options, default=None, blank=True, null=True)
    mapadvice       = models.CharField(max_length=500, default=None, blank=True, null=True)
    maprule         = models.CharField(max_length=500, default=None, blank=True, null=True)
    # Denormalized rule bindings
    mapspecifies    = models.TextField(default=None, blank=True, null=True)
    # Log accepted
    accepted = models.ManyToManyField(User, related_name="accepted_users", default=None, blank=True)
    # Log rejected
    rejected = models.ManyToManyField(User, related_name="rejected_users", default=None, blank=True)

    def __str__(self):
        return str(self.export_task)