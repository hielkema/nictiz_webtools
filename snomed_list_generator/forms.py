from django import forms

class SearchForm(forms.Form):
    query = forms.CharField(label='Query', widget=forms.Textarea(attrs={"rows":2, "cols":42, "class":'form-control'}))
    type_options = [
        # (code, readable)
        ('1', 'Excel download'),
        ('2', 'HTML download'),
        ('3', 'HTML weergave'),
    ]
    list_type = forms.CharField(label='Soort lijst', widget=forms.Select(choices=type_options, attrs={'class':'form-control'}), required=False)