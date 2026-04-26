from django.db import models
from django.contrib.auth.models import User
from django.utils.timezone import now
import re
# ====================== BLOTTER MODEL ======================
class Blotter(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    ]

    INCIDENT_CHOICES = [
        ('physical_injury', 'Physical Injury'),
        ('threat', 'Threat/Intimidation'),
        ('property_damage', 'Property Damage'),
        ('domestic', 'Domestic Violence'),
        ('others', 'Others'),
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

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    def save(self, *args, **kwargs):
        """Generate blotter_number if not already set"""
        if not self.blotter_number:
            # Get current year
            from django.utils.timezone import now
            year = now().year
            
            # Get the last blotter number for this year
            last_blotter = Blotter.objects.filter(
                blotter_number__startswith=f'BL-{year}-'
            ).order_by('-blotter_number').first()
            
            if last_blotter and last_blotter.blotter_number:
                # Extract the sequence number
                match = re.search(r'BL-\d+-(\d+)', last_blotter.blotter_number)
                if match:
                    last_num = int(match.group(1))
                    new_num = last_num + 1
                else:
                    new_num = 1
            else:
                new_num = 1
            
            # Format: BL-2025-001
            self.blotter_number = f'BL-{year}-{new_num:04d}'
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Blotter #{self.blotter_number or 'NEW'} - {self.complainant_name}"

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "Blotters"


# ====================== SCHEDULE MODEL ======================
class Schedule(models.Model):
    blotter = models.ForeignKey('Blotter', on_delete=models.CASCADE, related_name='schedules')
    hearing_date = models.DateTimeField()
    notes = models.TextField(blank=True, null=True)
    is_completed = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(          # ← Add this
        'auth.User', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )

    def __str__(self):
        return f"Hearing for Blotter #{self.blotter.blotter_number} on {self.hearing_date.strftime('%Y-%m-%d')}"

    class Meta:
        ordering = ['hearing_date']


# ====================== AUDIT LOG MODEL ======================
class BlotterAuditLog(models.Model):
    blotter = models.ForeignKey('Blotter', on_delete=models.CASCADE, related_name='audit_logs')
    action = models.CharField(max_length=100)
    old_value = models.TextField(blank=True, null=True)
    new_value = models.TextField(blank=True, null=True)
    performed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.action} - Blotter #{self.blotter.blotter_number}"


# ====================== NOTIFICATION MODEL ======================
class Notification(models.Model):
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification to {self.recipient}"