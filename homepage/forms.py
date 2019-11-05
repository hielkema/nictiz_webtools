from django import forms

class MedicinSearchForm(forms.Form):
    searchterm = forms.CharField(label='Zoekterm', max_length=100)