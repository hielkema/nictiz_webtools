from django import forms
from .models import *
# from django_select2.forms import HeavySelect2Widget

class MappingForm(forms.Form):
    id = forms.CharField(widget=forms.HiddenInput(), label='id', max_length=100)
    source_component = forms.CharField(widget=forms.HiddenInput(), label='source_component', max_length=100)
    target_component = forms.CharField(widget=forms.HiddenInput(), label='target_component', max_length=100)

    mapgroup = forms.IntegerField(label='mapgroup', required=False, widget=forms.NumberInput(attrs={'class':'form-control'}))
    mappriority = forms.IntegerField(label='mappriority', required=False, widget=forms.NumberInput(attrs={'class':'form-control'}))
    correlation_options = [
        # (code, readable)
        ('447557004', 'Exact match'),
        ('447559001', 'Broad to narrow'),
        ('447558009', 'Narrow to broad'),
        ('447560006', 'Partial overlap'),
        ('447556008', 'Not mappable'),
        ('447561005', 'Not specified'),
    ]
    mapcorrelation = forms.CharField(label='mapcorrelation', widget=forms.Select(choices=correlation_options, attrs={'class':'form-control'}), required=False)        
    mapcorrelation_type = forms.CharField(label='mapcorrelation_type', widget=forms.Select(attrs={'class':'form-control'}), required=False)
    mapadvice = forms.CharField(label='mapadvice', required=False, widget=forms.TextInput(attrs={'class':'form-control'}))
    maprule = forms.CharField(label='maprule', required=False, widget=forms.TextInput(attrs={'class':'form-control'}))

    target_component_ident = forms.CharField(label='target_component_term', max_length=100)
    target_component_codesystem = forms.CharField(label='target_component_term', max_length=100)
    target_component_term = forms.CharField(label='target_component_term', max_length=100)
    active = forms.BooleanField(label='active', required=False, widget=forms.HiddenInput()) #widget=forms.CheckboxInput())

class MappingFormEclQuery(forms.Form):
    source_component = forms.CharField(widget=forms.HiddenInput(), label='source_component', max_length=100)
    source_component_ident = forms.CharField(label='source_component_ident', required=False, max_length=100)
    source_component_term = forms.CharField(label='source_component_term', required=False, max_length=100)

class SnomedUpdateForm(forms.Form):
    codesystem = forms.CharField(label='codesystem', max_length=100)
    focus_concept = forms.CharField(label='snomed_focus', max_length=100)

class NHGUpdateForm(forms.Form):
    codesystem = forms.CharField(label='codesystem', max_length=100)

class TaskCreateForm(forms.Form):
    project = forms.CharField(label='project', max_length=100)
    codesystem = forms.CharField(label='codesystem', max_length=100)
    comment = forms.CharField(label='comment', required=False, widget=forms.Textarea(attrs={"rows":3, "cols":42}))
    tasks = forms.CharField(label='tasks', required=False, widget=forms.Textarea(attrs={"rows":3, "cols":42}))

class PostCommentForm(forms.Form):
    project_id          = forms.CharField(widget=forms.HiddenInput(), label='project_id', max_length=100)
    task_id             = forms.CharField(widget=forms.HiddenInput(), label='task_id', max_length=100)
    # comment_title       = forms.CharField(label='Titel', max_length=50)
    comment_body        = forms.CharField(label='Body', max_length=500, widget=forms.Textarea(attrs={"rows":3, "cols":42, "class":'form-control'}))
 
class TaskManagerForm(forms.Form):
    checkbox           = forms.BooleanField(label='checkbox', required=False)
    task_id            = forms.CharField(widget=forms.HiddenInput(), label='task_id', max_length=100, required=False)
    source_component   = forms.CharField(label='source_component', max_length=500, required=False)
    target_component   = forms.CharField(label='target_component', max_length=500, required=False)
    status             = forms.CharField(label='status', max_length=500, required=False)
    user               = forms.CharField(label='user', max_length=500, required=False)

class EclQueryForm(forms.Form):
    query = forms.CharField(widget=forms.TextInput(attrs={'class':'form-control'}))

class EclQueryBuilderForm(forms.Form):
    query_id    = forms.IntegerField(widget=forms.HiddenInput(), label='query_id')
    type_options = [
        # (code, readable)
        ('2', 'Descendants and self'),
        ('1', 'Descendants'),
        ('3', 'Custom'),
    ]
    query_type = forms.CharField(label='Query Type', widget=forms.Select(choices=type_options, attrs={'class':'form-control'}), required=False)
    function_options = [
        # (code, readable)
        ('2', 'ADD'),
        ('1', 'MINUS'),
    ]
    query_function = forms.CharField(label='Query function', widget=forms.Select(choices=function_options, attrs={'class':'form-control'}), required=False)  
    query = forms.CharField(widget=forms.Textarea(attrs={"rows":2, "cols":42, "class":'form-control'}))
