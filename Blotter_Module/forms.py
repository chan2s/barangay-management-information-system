from django import forms
from django.core.validators import MinLengthValidator, RegexValidator
from django.core.exceptions import ValidationError
from .models import Blotter, Schedule, Evidence, BlotterComment
import re

class PublicBlotterForm(forms.ModelForm):
    # Purpose field
    purpose = forms.ChoiceField(
        choices=[
            ('', 'Select purpose of report'),
            ('mediation', 'Request for Mediation'),
            ('complaint', 'Formal Complaint'),
            ('intervention', 'Request for Barangay Intervention'),
            # ('assistance', 'Request for Assistance'),
            ('report', 'Incident Report'),
        ],
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=True,
        label="Purpose of Report"
    )
    
    # Email confirmation field
    confirm_email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Confirm Email Address'}),
        label="Confirm Email"
    )
    
    # ID Verification Fields
    valid_id = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*,.pdf'}),
        label="Upload Valid ID"
    )
    
    id_type = forms.ChoiceField(
        choices=[
            ('', 'Select ID type'),
            ('passport', 'Passport'),
            ('drivers_license', "Driver's License"),
            # ('postal_id', 'Postal ID'),
            # ('umid', 'UMID'),
            ('philhealth', 'PhilHealth ID'),
            ('pagibig', 'Pag-IBIG ID'),
            ('national_id', 'National ID (PhilSys)'),
            ('barangay_id', 'Barangay ID'),
            ('voters_id', "Voter's ID"),
            ('others', 'Others'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Type of ID"
    )
    
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
            'incident_description': forms.Textarea(attrs={'rows': 6, 'class': 'form-control', 'placeholder': 'Provide a detailed account of what happened (minimum 20 characters)...'}),
            'complainant_address': forms.Textarea(attrs={'rows': 2, 'class': 'form-control', 'placeholder': 'Complete address'}),
            'respondent_address': forms.Textarea(attrs={'rows': 2, 'class': 'form-control', 'placeholder': 'Address of respondent'}),
            'complainant_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full name'}),
            'complainant_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 09123456789'}),
            'complainant_email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'youremail@example.com'}),
            'respondent_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full name of respondent'}),
            'respondent_contact': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'If known'}),
            'incident_location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Specific location/address'}),
        }
    
    def clean_complainant_phone(self):
        phone = self.cleaned_data.get('complainant_phone', '')
        if phone:
            if not re.match(r'^(09|\+639)\d{9}$', phone.replace(' ', '').replace('-', '')):
                raise ValidationError('Enter a valid Philippine mobile number (e.g., 09123456789 or +639123456789)')
        return phone
    
    def clean_complainant_email(self):
        email = self.cleaned_data.get('complainant_email', '')
        if email:
            disposable_domains = ['tempmail.com', '10minutemail.com', 'guerrillamail.com', 'mailinator.com', 'temp-mail.org']
            domain = email.split('@')[-1].lower()
            if domain in disposable_domains:
                raise ValidationError('Please use a permanent email address. Temporary/disposable emails are not allowed.')
        return email
    
    def clean(self):
        cleaned_data = super().clean()
        phone = cleaned_data.get('complainant_phone', '')
        email = cleaned_data.get('complainant_email', '')
        confirm_email = cleaned_data.get('confirm_email', '')
        valid_id = cleaned_data.get('valid_id', '')
        id_type = cleaned_data.get('id_type', '')
        incident_description = cleaned_data.get('incident_description', '')
        
        # Require at least one contact method
        if not phone and not email:
            raise ValidationError('Please provide at least a phone number OR email address for contact purposes.')
        
        # Email confirmation (if email is provided)
        if email and confirm_email and email != confirm_email:
            self.add_error('confirm_email', 'Email addresses do not match.')
        
        # ID validation (only if ID is provided - will be checked in view)
        if valid_id and not id_type:
            self.add_error('id_type', 'Please select the type of ID you are uploading.')
        
        # Minimum description length (anti-spam)
        if incident_description and len(incident_description.strip()) < 20:
            self.add_error('incident_description', 'Please provide a more detailed description (minimum 20 characters).')
        
        # Validate incident date is not in future
        incident_date = cleaned_data.get('incident_date')
        if incident_date:
            from django.utils import timezone
            if incident_date > timezone.now().date():
                self.add_error('incident_date', 'Incident date cannot be in the future.')
        
        return cleaned_data

# Email verification forms
class EmailVerificationForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter your email address'})
    )

class VerifyOTPForm(forms.Form):
    otp_code = forms.CharField(
        max_length=6,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter 6-digit code'})
    )

class ScheduleForm(forms.ModelForm):
    class Meta:
        model = Schedule
        fields = ['hearing_type', 'hearing_date', 'location', 'notes', 'hearing_type']
        widgets = {
            'hearing_date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'hearing_type': forms.Select(attrs={'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }

from .models import Evidence

class EvidenceForm(forms.ModelForm):
    class Meta:
        model = Evidence
        fields = ['title', 'description', 'file', 'file_type']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Evidence title'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Description of evidence...'}),
            'file': forms.FileInput(attrs={'class': 'form-control'}),
            'file_type': forms.Select(attrs={'class': 'form-control'}),
        }

class CommentForm(forms.ModelForm):
    class Meta:
        model = BlotterComment
        fields = ['comment', 'is_internal']
        widgets = {
            'comment': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'Write your comment here...'}),
            'is_internal': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class BlotterStatusForm(forms.Form):
    status = forms.ChoiceField(choices=Blotter.STATUS_CHOICES, widget=forms.Select(attrs={'class': 'form-control'}))
    reason = forms.CharField(widget=forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}), required=False)