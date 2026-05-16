from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.html import strip_tags

from .models import Resident
from .services import find_possible_resident_duplicates, fingerprint_sensitive_value


STREET_CHOICES = [
    ('Poblacion Proper', 'Poblacion Proper'),
    ('Municipal Hall Area', 'Municipal Hall Area'),
    ('Public Market Area', 'Public Market Area'),
    ('Church Area', 'Church Area'),
    ('National Road', 'National Road'),
    ('School Area', 'School Area'),
    ('Barangay Hall Area', 'Barangay Hall Area'),
]


class ResidentForm(forms.ModelForm):
    national_id = forms.CharField(required=False, max_length=80, help_text='Stored as a protected fingerprint only.')
    privacy_notice = forms.BooleanField(
        required=True,
        label='I confirm that the resident was shown the privacy notice and gave consent.',
    )

    class Meta:
        model = Resident
        fields = [
            'full_name',
            'middle_name',
            'suffix',
            'birthdate',
            'sex',
            'civil_status',
            'street_name',
            'purok',
            'address',
            'contact_number',
            'email',
            'resident_id',
            'national_id',
            'profile_photo',
            'household_number',
            'occupation',
            'is_solo_parent',
            'is_indigent',
            'voter_status',
            'privacy_notice',
        ]
        widgets = {
            'birthdate': forms.DateInput(attrs={'type': 'date'}),
            'address': forms.Textarea(attrs={'rows': 3}),
            'street_name': forms.Select(choices=[('', 'Select street or area')] + STREET_CHOICES),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk and self.instance.privacy_consent:
            self.fields['privacy_notice'].initial = True

    def clean_full_name(self):
        return ' '.join(strip_tags(self.cleaned_data['full_name']).split())

    def clean_email(self):
        return (self.cleaned_data.get('email') or '').strip().lower()

    def clean_contact_number(self):
        return (self.cleaned_data.get('contact_number') or '').strip()

    def clean_address(self):
        value = ' '.join(strip_tags(self.cleaned_data.get('address') or '').split())
        if value and not all(part.lower() in value.lower() for part in ['poblacion', 'santa catalina', 'negros oriental']):
            raise ValidationError('Address must be in Poblacion, Santa Catalina, Negros Oriental.')
        return value

    def clean(self):
        cleaned_data = super().clean()
        if self.errors:
            return cleaned_data

        national_id = cleaned_data.get('national_id')
        if national_id:
            cleaned_data['national_id_hash'] = fingerprint_sensitive_value(national_id)

        duplicates = find_possible_resident_duplicates(
            cleaned_data,
            exclude_pk=self.instance.pk if self.instance else None,
        )
        if duplicates.exists():
            names = ', '.join(str(item) for item in duplicates[:3])
            raise ValidationError(f'Possible duplicate resident detected. Matching record(s): {names}')

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        national_id = self.cleaned_data.get('national_id')
        if national_id:
            clean_id = ''.join(ch for ch in national_id if ch.isalnum())
            instance.national_id_hash = fingerprint_sensitive_value(clean_id)
            instance.national_id_last4 = clean_id[-4:]
        if self.cleaned_data.get('privacy_notice') and not instance.consented_at:
            instance.privacy_consent = True
            instance.consented_at = timezone.now()
        instance.barangay = 'Poblacion'
        instance.municipality = 'Santa Catalina'
        instance.province = 'Negros Oriental'
        if commit:
            instance.save()
        return instance
