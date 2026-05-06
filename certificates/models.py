from django.db import models
from datetime import datetime
import uuid


class CertificateRequest(models.Model):
    CERTIFICATE_TYPES = [
        ('clearance', 'Barangay Clearance'),
        ('indigency', 'Certificate of Indigency'),
        ('residency', 'Certificate of Residency'),
        ('id', 'Barangay ID'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('for_approval', 'For Kapitan Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('released', 'Released'),
        ('cancelled', 'Cancelled'),
    ]

    CIVIL_STATUS_CHOICES = [
        ('single', 'Single'),
        ('married', 'Married'),
        ('widowed', 'Widowed'),
        ('divorced', 'Divorced'),
        ('separated', 'Separated'),
    ]

    # Basic Information
    request_id = models.CharField(max_length=20, unique=True, blank=True)
    request_type = models.CharField(max_length=20, choices=CERTIFICATE_TYPES)
    full_name = models.CharField(max_length=200)
    address = models.TextField()
    contact_number = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    age = models.IntegerField(null=True, blank=True)
    civil_status = models.CharField(max_length=20, choices=CIVIL_STATUS_CHOICES, blank=True)
    gender = models.CharField(max_length=10, blank=True)
    purpose = models.TextField(blank=True)
    claim_deadline = models.DateTimeField(null=True, blank=True)

    # Certificate Specific Fields
    purok = models.CharField(max_length=100, blank=True)

    # File Upload Fields - ADD THESE
    valid_id = models.FileField(upload_to='valid_ids/%Y/%m/%d/', blank=True, null=True)
    proof_residency = models.FileField(upload_to='proof_residency/%Y/%m/%d/', blank=True, null=True)
    photo = models.FileField(upload_to='photos/%Y/%m/%d/', blank=True, null=True)

    # Health Certification Specific Fields
    birthplace = models.CharField(max_length=200, blank=True)
    parents = models.CharField(max_length=200, blank=True)
    date_first_seen = models.DateField(null=True, blank=True)
    sex = models.CharField(max_length=10, blank=True)

    # Barangay ID Back Side Fields
    weight = models.CharField(max_length=20, blank=True, null=True)
    height = models.CharField(max_length=20, blank=True, null=True)
    emergency_name = models.CharField(max_length=200, blank=True, null=True)
    emergency_address = models.TextField(blank=True, null=True)
    emergency_contact = models.CharField(max_length=20, blank=True, null=True)
    emergency_relationship = models.CharField(max_length=50, blank=True, null=True)

    # Status and Tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    date_submitted = models.DateTimeField(auto_now_add=True)
    date_processed = models.DateTimeField(null=True, blank=True)
    date_approved = models.DateTimeField(null=True, blank=True)
    date_released = models.DateTimeField(null=True, blank=True)

    # Additional Info
    remarks = models.TextField(blank=True)
    processed_by = models.CharField(max_length=100, blank=True)
    approved_by = models.CharField(max_length=100, blank=True)
    rejection_reason = models.TextField(blank=True)

    class Meta:
        ordering = ['-date_submitted']
        verbose_name = 'Certificate Request'
        verbose_name_plural = 'Certificate Requests'

    def save(self, *args, **kwargs):
        if not self.request_id:
            self.request_id = f"REQ-{uuid.uuid4().hex[:4].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.request_id} - {self.full_name}"