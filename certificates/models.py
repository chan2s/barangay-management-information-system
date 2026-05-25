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


class CertificateTemplate(models.Model):
    template_name = models.CharField(max_length=200)
    template_type = models.CharField(max_length=50, db_index=True)

    header_html = models.TextField(blank=True, default='')
    body_html = models.TextField(blank=True, default='')
    footer_html = models.TextField(blank=True, default='')
    document_html = models.TextField(blank=True, default='')

    logo = models.ImageField(blank=True, null=True, upload_to='certificate_assets/%Y/%m/logos/')
    seal = models.ImageField(blank=True, null=True, upload_to='certificate_assets/%Y/%m/seals/')
    signature = models.ImageField(blank=True, null=True, upload_to='certificate_assets/%Y/%m/signatures/')

    is_active = models.BooleanField(default=True, db_index=True)

    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    created_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, related_name='created_certificate_templates')
    updated_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, related_name='updated_certificate_templates')

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['template_type', 'is_deleted', 'is_active']),
        ]
        ordering = ['-created_at']
        verbose_name = 'Certificate Template'
        verbose_name_plural = 'Certificate Templates'

    def __str__(self):
        status = 'Active' if self.is_active else 'Inactive'
        return f"{self.template_name} ({self.template_type}) - {status}"


class CertificateTemplateVersion(models.Model):
    template = models.ForeignKey(CertificateTemplate, on_delete=models.CASCADE, related_name='versions')

    version_number = models.PositiveIntegerField(db_index=True)
    change_notes = models.CharField(max_length=500, blank=True, default='')

    snapshot_header_html = models.TextField(blank=True, default='')
    snapshot_body_html = models.TextField(blank=True, default='')
    snapshot_footer_html = models.TextField(blank=True, default='')
    snapshot_document_html = models.TextField(blank=True, default='')

    snapshot_logo = models.ImageField(blank=True, null=True, upload_to='certificate_assets/%Y/%m/version_logos/')
    snapshot_seal = models.ImageField(blank=True, null=True, upload_to='certificate_assets/%Y/%m/version_seals/')
    snapshot_signature = models.ImageField(blank=True, null=True, upload_to='certificate_assets/%Y/%m/version_signatures/')

    changed_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, related_name='certificate_template_versions')
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = [('template', 'version_number')]
        verbose_name = 'Certificate Template Version'
        verbose_name_plural = 'Certificate Template Versions'

    def __str__(self):
        return f"{self.template_id} v{self.version_number}"


class CertificateTemplatePermission(models.Model):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('staff', 'Staff'),
        ('kapitan', 'Kapitan'),
    ]

    template = models.ForeignKey(CertificateTemplate, on_delete=models.CASCADE, related_name='permissions')

    role = models.CharField(max_length=20, blank=True, choices=ROLE_CHOICES)
    staff_user = models.ForeignKey('auth.User', on_delete=models.CASCADE, null=True, blank=True, related_name='certificate_template_permissions')

    class Meta:
        unique_together = [('template', 'role', 'staff_user')]
        verbose_name = 'Certificate Template Permission'
        verbose_name_plural = 'Certificate Template Permissions'

    def __str__(self):
        who = self.staff_user.username if self.staff_user_id else '—'
        return f"Perm {who} {self.role} for template {self.template_id}"
