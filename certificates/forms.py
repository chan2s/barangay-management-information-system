from django import forms
from django.core.exceptions import ValidationError
from .models import CertificateRequest, CertificateTemplate
from .services import sanitize_certificate_html
import re

class CertificateRequestForm(forms.ModelForm):
    confirm_email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Confirm Email Address'})
    )
    
    class Meta:
        model = CertificateRequest
        fields = [
            'request_type', 'full_name', 'address', 'date_of_birth', 'civil_status',
            'gender', 'purpose', 'purok', 'birthplace', 'weight', 'height',
            'emergency_name', 'emergency_address', 'emergency_contact', 'emergency_relationship'
        ]
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'purpose': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'State the purpose of this request'}),
            'address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Complete address'}),
            'full_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full name as appears on ID'}),
            'civil_status': forms.Select(attrs={'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-control'}),
            'purok': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Purok 1, Sitio Example'}),
            'birthplace': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Place of birth'}),
            'weight': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Weight in kg'}),
            'height': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Height (e.g., 5\'4")'}),
            'emergency_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full name'}),
            'emergency_address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Complete address'}),
            'emergency_contact': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Contact number'}),
            'emergency_relationship': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Relationship'}),
        }
    
    def clean_contact_number(self):
        contact = self.cleaned_data.get('contact_number', '')
        if contact and not re.match(r'^(09|\+639)\d{9}$', contact.replace(' ', '').replace('-', '')):
            raise ValidationError('Enter a valid Philippine mobile number (e.g., 09123456789)')
        return contact
    
    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email', '')
        confirm_email = cleaned_data.get('confirm_email', '')
        
        if email and confirm_email and email != confirm_email:
            self.add_error('confirm_email', 'Email addresses do not match')
        
        return cleaned_data


class TrackRequestForm(forms.Form):
    reference_number = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your reference number (e.g., REQ-XXXX)'
        })
    )
    last_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your last name'
        })
    )


class CertificateTemplateForm(forms.ModelForm):
    class Meta:
        model = CertificateTemplate
        fields = [
            'template_name', 'template_type', 'document_html',
            'logo', 'seal', 'signature', 'is_active'
        ]
        widgets = {
            'template_name': forms.TextInput(attrs={'class': 'form-control'}),
            'template_type': forms.Select(attrs={'class': 'form-control'}, choices=CertificateRequest.CERTIFICATE_TYPES),
            'document_html': forms.Textarea(attrs={'class': 'document-source', 'rows': 4}),
            'logo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'seal': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'signature': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_template_type(self):
        template_type = self.cleaned_data['template_type']
        valid_types = [value for value, _label in CertificateRequest.CERTIFICATE_TYPES]
        if template_type not in valid_types:
            raise ValidationError('Select a valid certificate type.')
        return template_type

    def clean_document_html(self):
        return sanitize_certificate_html(self.cleaned_data.get('document_html', ''))
