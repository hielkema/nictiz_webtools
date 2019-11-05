from django import forms

class SearchForm(forms.Form):
    searchterm = forms.CharField(label='SCTID', max_length=100)