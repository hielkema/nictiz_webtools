from django import forms

class SearchForm(forms.Form):
    searchterm = forms.CharField(label='SCTID', max_length=100)

class QaForm(forms.Form):
    concepts = forms.CharField(label='Concepts', widget=forms.Textarea(attrs={"rows":3, "cols":42}))