from django import forms
from .models import Blotter

class PublicBlotterForm(forms.ModelForm):
    class Meta:
        model = Blotter
        fields = [
            'complainant_name',
            'complainant_address',
            'complainant_phone',
            'complainant_email',
            'respondent_name',
            'respondent_address',
            'respondent_contact',
            'incident_type',
            'incident_date',
            'incident_location',
            'incident_description',
        ]
        widgets = {
            'incident_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'incident_description': forms.Textarea(attrs={'rows': 5, 'class': 'form-control'}),
            'complainant_address': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'respondent_address': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }