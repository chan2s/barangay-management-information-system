from django.db import models
from django.contrib.auth.models import User
from django.utils.timezone import now
import re
from django.core.validators import FileExtensionValidator

# ====================== BLOTTER MODEL ======================
class Blotter(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
        ('unsettled', 'Unsettled'),
        ('dismissed', 'Dismissed'),
    ]

    INCIDENT_CHOICES = [
        ('physical_injury', 'Physical Injury'),
        ('threat', 'Threat/Intimidation'),
        ('property_damage', 'Property Damage'),
        ('domestic', 'Domestic Violence'),
        ('theft', 'Theft/Robbery'),
        ('harassment', 'Harassment'),
        ('land_dispute', 'Land Dispute'),
        ('others', 'Others'),
    ]

    VERIFICATION_METHOD_CHOICES = [
        ('email', 'Email Verification'),
        ('id_card', 'Valid ID Verification'),
    ]

    ID_VERIFICATION_STATUS_CHOICES = [
        ('pending', 'Pending Verification'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected'),
    ]

    # Identification
    blotter_number = models.CharField(max_length=50, unique=True, editable=False, blank=True)

    # Complainant
    complainant_name = models.CharField(max_length=255)
    complainant_address = models.TextField(blank=True, null=True)
    complainant_phone = models.CharField(max_length=20, blank=True, null=True)
    complainant_email = models.EmailField(blank=True, null=True)

    # Respondent
    respondent_name = models.CharField(max_length=255, blank=True, null=True)
    respondent_address = models.TextField(blank=True, null=True)
    respondent_contact = models.CharField(max_length=20, blank=True, null=True)

    # Incident
    incident_type = models.CharField(max_length=50, choices=INCIDENT_CHOICES, default='others')
    incident_date = models.DateField(default=now)
    incident_location = models.TextField()
    incident_description = models.TextField()

    # Hearing and Resolution
    hearing_date = models.DateTimeField(null=True, blank=True)
    hearing_notes = models.TextField(blank=True, null=True)
    resolution_notes = models.TextField(blank=True, null=True)
    initial_action = models.TextField(blank=True, null=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Tracking
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_blotters')
    assigned_officer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_blotters')

    # Verification Fields
    purpose = models.CharField(max_length=50, blank=True, null=True)
    verification_method = models.CharField(max_length=20, choices=VERIFICATION_METHOD_CHOICES, blank=True, null=True)
    verification_status = models.CharField(max_length=30, default='pending_verification')
    verified_contact = models.CharField(max_length=100, blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    
    # ID Verification Fields
    valid_id_file = models.FileField(
        upload_to='valid_ids/%Y/%m/%d/',
        blank=True, 
        null=True,
        validators=[FileExtensionValidator(['jpg', 'jpeg', 'png', 'pdf'])]
    )
    valid_id_type = models.CharField(max_length=50, blank=True, null=True)
    id_verification_status = models.CharField(max_length=20, choices=ID_VERIFICATION_STATUS_CHOICES, default='pending')
    id_verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_ids')
    id_verified_at = models.DateTimeField(blank=True, null=True)
    id_rejection_reason = models.TextField(blank=True, null=True)
    
    # Staff Review Fields
    staff_notes = models.TextField(blank=True, null=True)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_blotters')
    reviewed_at = models.DateTimeField(blank=True, null=True)
    rejection_reason = models.TextField(blank=True, null=True)

    # ==================== NEW APPROVAL FIELDS ====================
    is_approved = models.BooleanField(default=False)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_blotters')
    approved_at = models.DateTimeField(blank=True, null=True)
    review_notes = models.TextField(blank=True, null=True)
    duplicate_of = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='duplicates')

    def save(self, *args, **kwargs):
        """Generate blotter_number if not already set"""
        if not self.blotter_number:
            from django.utils.timezone import now
            year = now().year
            
            last_blotter = Blotter.objects.filter(
                blotter_number__startswith=f'BL-{year}-'
            ).order_by('-blotter_number').first()
            
            if last_blotter and last_blotter.blotter_number:
                import re
                match = re.search(r'BL-\d+-(\d+)', last_blotter.blotter_number)
                if match:
                    last_num = int(match.group(1))
                    new_num = last_num + 1
                else:
                    new_num = 1
            else:
                new_num = 1
            
            self.blotter_number = f'BL-{year}-{new_num:04d}'
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Blotter #{self.blotter_number or 'NEW'} - {self.complainant_name}"

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "Blotters"


# ====================== SCHEDULE MODEL ======================
class Schedule(models.Model):
    HEARING_TYPES = [
        ('initial', 'Initial Hearing'),
        ('follow_up', 'Follow-up Hearing'),
        ('conciliation', 'Conciliation'),
        ('final', 'Final Hearing'),
    ]
    
    OUTCOME_CHOICES = [
        ('pending', 'Pending'),
        ('adjourned', 'Adjourned'),
        ('settled', 'Settled'),
        ('rescheduled', 'Rescheduled'),
        ('completed', 'Completed'),
    ]
    ATTENDANCE_CHOICES = [
        ('pending', 'Select Attendance'),
        ('both_present', 'Both Parties Present'),
        ('complainant_only', 'Complainant Only'),
        ('respondent_only', 'Respondent Only'),
        ('both_absent', 'Both Absent'),
    ]
    blotter = models.ForeignKey('Blotter', on_delete=models.CASCADE, related_name='schedules')
    hearing_type = models.CharField(max_length=20, choices=HEARING_TYPES, default='initial')
    hearing_date = models.DateTimeField()
    location = models.CharField(max_length=200, default='Barangay Hall')
    notes = models.TextField(blank=True, null=True)
    outcome = models.CharField(max_length=20, choices=OUTCOME_CHOICES, default='pending')
    outcome_notes = models.TextField(blank=True, null=True)
    is_completed = models.BooleanField(default=False)
    is_rescheduled = models.BooleanField(default=False)
    rescheduled_reason = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"Hearing for Blotter #{self.blotter.blotter_number} on {self.hearing_date.strftime('%Y-%m-%d')}"

    class Meta:
        ordering = ['hearing_date']


# ====================== EVIDENCE MODEL ======================
class Evidence(models.Model):
    EVIDENCE_TYPES = [
        ('photo', 'Photo'),
        ('document', 'Document'),
        ('video', 'Video'),
        ('audio', 'Audio'),
        ('other', 'Other'),
    ]
    
    blotter = models.ForeignKey('Blotter', on_delete=models.CASCADE, related_name='evidences')
    title = models.CharField(max_length=200)
    evidence_type = models.CharField(max_length=20, choices=EVIDENCE_TYPES, default='document')
    file = models.FileField(
        upload_to='evidence/%Y/%m/%d/',
        validators=[FileExtensionValidator(['pdf', 'jpg', 'jpeg', 'png', 'mp4', 'mp3', 'doc', 'docx'])]
    )
    description = models.TextField(blank=True, null=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.title


# ====================== AUDIT LOG MODEL ======================
class BlotterAuditLog(models.Model):
    ACTION_CHOICES = [
        ('create', 'Create'),
        ('update', 'Update'),
        ('status_change', 'Status Change'),
        ('schedule', 'Schedule'),
        ('upload_evidence', 'Upload Evidence'),
        ('approve', 'Approve'),
        ('reject', 'Reject'),
        ('mark_duplicate', 'Mark as Duplicate'),
    ]
    
    blotter = models.ForeignKey('Blotter', on_delete=models.CASCADE, related_name='audit_logs')
    action = models.CharField(max_length=100, choices=ACTION_CHOICES)
    old_value = models.TextField(blank=True, null=True)
    new_value = models.TextField(blank=True, null=True)
    performed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.action} - Blotter #{self.blotter.blotter_number}"


# ====================== NOTIFICATION MODEL ======================
class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('new', 'New Blotter'),
        ('hearing', 'Hearing Scheduled'),
        ('reminder', 'Hearing Reminder'),
        ('status', 'Status Update'),
        ('resolved', 'Case Resolved'),
        ('approved', 'Blotter Approved'),
        ('rejected', 'Blotter Rejected'),
    ]
    
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    blotter = models.ForeignKey('Blotter', on_delete=models.CASCADE, null=True, blank=True, related_name='notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, default='new')
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification to {self.recipient.username}"


# ====================== COMMENT MODEL ======================
class BlotterComment(models.Model):
    blotter = models.ForeignKey('Blotter', on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    comment = models.TextField()
    is_internal = models.BooleanField(default=False)  # Internal staff notes
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"Comment on {self.blotter.blotter_number}"