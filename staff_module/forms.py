from django import forms
from .models import Announcement
from .models import Appointment

class AnnouncementForm(forms.ModelForm):
    class Meta:
        model = Announcement
        fields = ['title', 'content', 'priority', 'image', 'scheduled_date', 'expires_at']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Announcement Title'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 6, 'placeholder': 'Write your announcement here...'}),
            'priority': forms.Select(attrs={'class': 'form-control'}),
            'scheduled_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'expires_at': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
        }
        
class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ['appointment_type', 'resident_name', 'resident_address', 'resident_contact', 'resident_email', 
                  'purpose', 'appointment_date', 'duration_minutes', 'priority', 'hearing_type', 'location', 'notes']
        widgets = {
            'appointment_type': forms.Select(attrs={'class': 'form-control', 'id': 'appointment_type'}),
            'resident_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full Name'}),
            'resident_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Complete Address'}),
            'resident_contact': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '09123456789'}),
            'resident_email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'email@example.com'}),
            'purpose': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Purpose of appointment/hearing...'}),
            'appointment_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'duration_minutes': forms.NumberInput(attrs={'class': 'form-control', 'min': 15, 'max': 120}),
            'priority': forms.Select(attrs={'class': 'form-control'}),
            'hearing_type': forms.Select(attrs={'class': 'form-control', 'id': 'hearing_type'}, choices=[
                ('', 'Select hearing type'),
                ('initial_mediation', 'Initial Mediation (Lupon Meeting)'),
                ('conciliation', 'Conciliation Conference'),
                ('follow_up', 'Follow-up Mediation'),
                ('settlement_meeting', 'Settlement Meeting'),
                ('arbitration', 'Arbitration'),
            ]),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Barangay Poblacion Session Hall'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Additional notes...'}),
        }
class AppointmentStatusForm(forms.Form):
    status = forms.ChoiceField(choices=Appointment.STATUS_CHOICES, widget=forms.Select(attrs={'class': 'form-control'}))
    notes = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2}), required=False)