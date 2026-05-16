from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Resident(models.Model):
    SEX_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    ]
    CIVIL_STATUS_CHOICES = [
        ('single', 'Single'),
        ('married', 'Married'),
        ('widowed', 'Widowed'),
        ('separated', 'Separated'),
    ]
    VOTER_STATUS_CHOICES = [
        ('registered', 'Registered'),
        ('not_registered', 'Not Registered'),
        ('unknown', 'Unknown'),
    ]
    PUROK_CHOICES = [(f'purok_{i}', f'Purok {i}') for i in range(1, 8)]

    full_name = models.CharField(max_length=255)
    middle_name = models.CharField(max_length=100, blank=True)
    suffix = models.CharField(max_length=30, blank=True)
    birthdate = models.DateField()
    sex = models.CharField(max_length=20, choices=SEX_CHOICES)
    civil_status = models.CharField(max_length=20, choices=CIVIL_STATUS_CHOICES)
    address = models.TextField()
    street_name = models.CharField(max_length=255, blank=True)
    purok = models.CharField(max_length=20, choices=PUROK_CHOICES, blank=True)
    barangay = models.CharField(max_length=100, default='Poblacion')
    municipality = models.CharField(max_length=100, default='Santa Catalina')
    province = models.CharField(max_length=100, default='Negros Oriental')
    contact_number = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    resident_id = models.CharField(max_length=50, unique=True)
    national_id_hash = models.CharField(max_length=128, blank=True, db_index=True)
    national_id_last4 = models.CharField(max_length=4, blank=True)
    profile_photo = models.ImageField(upload_to='residents/%Y/%m/%d/', blank=True, null=True)
    household_number = models.CharField(max_length=50, blank=True)
    occupation = models.CharField(max_length=120, blank=True)
    is_solo_parent = models.BooleanField(default=False)
    is_indigent = models.BooleanField(default=False)
    voter_status = models.CharField(max_length=20, choices=VOTER_STATUS_CHOICES, default='unknown')
    privacy_consent = models.BooleanField(default=False)
    consented_at = models.DateTimeField(null=True, blank=True)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='deleted_residents')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def age(self):
        today = timezone.localdate()
        years = today.year - self.birthdate.year
        if (today.month, today.day) < (self.birthdate.month, self.birthdate.day):
            years -= 1
        return years

    def __str__(self):
        return f'{self.full_name} ({self.resident_id})'

    class Meta:
        ordering = ['full_name']
        indexes = [
            models.Index(fields=['full_name', 'birthdate']),
            models.Index(fields=['contact_number']),
            models.Index(fields=['email']),
            models.Index(fields=['household_number']),
            models.Index(fields=['is_deleted']),
        ]


class ResidentExportRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    CATEGORY_CHOICES = [
        ('filtered', 'Filtered residents'),
        ('senior', 'Senior citizens'),
        ('youth', 'Youth residents'),
        ('solo_parent', 'Solo parents'),
        ('voter_age', 'Voter-age residents'),
        ('indigent', 'Indigent residents'),
    ]

    requested_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='resident_export_requests')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_resident_exports')
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default='filtered')
    filters = models.JSONField(default=dict, blank=True)
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    requested_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-requested_at']

    def __str__(self):
        return f'{self.get_category_display()} export by {self.requested_by} ({self.status})'

    @property
    def filter_summary(self):
        from .resident_exports import describe_export_request

        return describe_export_request(self)
