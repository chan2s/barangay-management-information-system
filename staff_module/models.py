from django.db import models
from django.db.models import ProtectedError
from django.contrib.auth.models import User
from django.utils.timezone import now
import re
from django.core.validators import FileExtensionValidator
from django.utils import timezone

class Staff(models.Model):
    ROLE_CHOICES = [
        ('admin', 'Administrator'),
        ('staff', 'Staff'),
        ('kapitan', 'Punong Barangay / Kapitan'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='staff_profile')
    role = models.CharField(max_length=50, choices=ROLE_CHOICES, default='staff')
    employee_id = models.CharField(max_length=20, unique=True, blank=True)
    position = models.CharField(max_length=100, blank=True)
    contact_number = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    date_hired = models.DateField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    def save(self, *args, **kwargs):
        if not self.employee_id:
            year = now().year
            last_staff = Staff.objects.filter(employee_id__startswith=f'STAFF-{year}').order_by('-employee_id').first()
            if last_staff and last_staff.employee_id:
                import re
                match = re.search(r'STAFF-\d+-(\d+)', last_staff.employee_id)
                if match:
                    last_num = int(match.group(1))
                    new_num = last_num + 1
                else:
                    new_num = 1
            else:
                new_num = 1
            self.employee_id = f'STAFF-{year}-{new_num:04d}'
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} - {self.get_role_display()}"
    
    def has_permission(self, permission):
        """Check if user has specific permission based on role"""
        if self.user.is_superuser:
            return True
        
        # Define role permissions
        role_permissions = {
            'kapitan': ['approve_certificate', 'view_reports', 'view_analytics', 'approve_blotter'],
            'admin': ['manage_users', 'view_reports', 'approve_certificate', 'manage_staff', 'manage_residents', 'approve_exports'],
            'staff': ['view_blotters', 'process_certificate', 'schedule_hearing'],
        }
        
        return permission in role_permissions.get(self.role, [])

# Add AuditLog model at the end of the file
class AuditLog(models.Model):
    ACTION_CHOICES = [
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('approve', 'Approve'),
        ('reject', 'Reject'),
        ('view', 'View'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    user_role = models.CharField(max_length=50, blank=True)
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    module = models.CharField(max_length=100)
    description = models.TextField()
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.user} - {self.action} - {self.timestamp}"


class Announcement(models.Model):
    PRIORITY_CHOICES = [
        ('normal', 'Normal'),
        ('important', 'Important'),
        ('urgent', 'Urgent'),
    ]
    
    title = models.CharField(max_length=200)
    content = models.TextField()
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='normal')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='announcements')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    scheduled_date = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    # For image attachments
    image = models.ImageField(upload_to='announcements/', null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
    
    def is_expired(self):
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False
    
    def get_priority_color(self):
        colors = {
            'normal': '#6c757d',
            'important': '#ffc107',
            'urgent': '#dc3545'
        }
        return colors.get(self.priority, '#6c757d')
    
    def get_priority_icon(self):
        icons = {
            'normal': 'fa-info-circle',
            'important': 'fa-exclamation-circle',
            'urgent': 'fa-bell'
        }
        return icons.get(self.priority, 'fa-info-circle')
    

class Appointment(models.Model):
    APPOINTMENT_TYPES = [
        ('kapitan', 'Kapitan Appointment'),
        ('blotter_hearing', 'Blotter Hearing'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('completed', 'Completed'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
        ('rescheduled', 'Rescheduled'),
    ]
    
    PRIORITY_CHOICES = [
        ('normal', 'Normal'),
        ('important', 'Important'),
        ('urgent', 'Urgent'),
    ]
    
    # Type of appointment
    appointment_type = models.CharField(max_length=20, choices=APPOINTMENT_TYPES, default='kapitan')
    
    # For blotter hearings - link to blotter
    blotter = models.ForeignKey('Blotter_Module.Blotter', on_delete=models.CASCADE, null=True, blank=True, related_name='appointments')
    
    # Resident Information
    resident_name = models.CharField(max_length=200)
    resident_address = models.TextField()
    resident_contact = models.CharField(max_length=20)
    resident_email = models.EmailField(blank=True, null=True)
    
    # Appointment Details
    purpose = models.TextField()
    appointment_date = models.DateTimeField()
    duration_minutes = models.IntegerField(default=30)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='normal')
    
    # For blotter hearings
    hearing_type = models.CharField(max_length=50, blank=True, null=True)  # initial_mediation, conciliation, etc.
    location = models.CharField(max_length=255, blank=True, null=True)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    notes = models.TextField(blank=True, null=True)
    
    # Staff Handling
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_appointments')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_appointments')
    approved_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Reference number
    reference_number = models.CharField(max_length=20, unique=True, blank=True)
    
    class Meta:
        ordering = ['appointment_date']
    
    def save(self, *args, **kwargs):
        if not self.reference_number:
            import random
            import string
            prefix = 'HEAR' if self.appointment_type == 'blotter_hearing' else 'APT'
            self.reference_number = f"{prefix}-{random.randint(10000, 99999)}"
        super().save(*args, **kwargs)
    
    def __str__(self):
        type_label = "Hearing" if self.appointment_type == 'blotter_hearing' else "Appointment"
        return f"{self.reference_number} - {self.resident_name} ({self.appointment_date.strftime('%Y-%m-%d %H:%M')})"
    
    def get_priority_color(self):
        colors = {
            'normal': '#6c757d',
            'important': '#ffc107',
            'urgent': '#dc3545'
        }
        return colors.get(self.priority, '#6c757d')
    
    def get_status_color(self):
        colors = {
            'pending': '#ffc107',
            'approved': '#28a745',
            'completed': '#17a2b8',
            'cancelled': '#dc3545',
            'rescheduled': '#fd7e14'
        }
        return colors.get(self.status, '#6c757d')


class ActivityLog(models.Model):
    ACTION_CHOICES = [
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('login_failed', 'Failed Login'),
        ('export_attempt', 'Export Attempt'),
        ('export_approve', 'Export Approve'),
        ('export_reject', 'Export Reject'),
        ('certificate_generate', 'Certificate Generate'),
        ('approve', 'Approve'),
        ('reject', 'Reject'),
        ('view', 'View'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='activities')
    username = models.CharField(max_length=150, blank=True)
    user_role = models.CharField(max_length=50, blank=True)
    action = models.CharField(max_length=30, choices=ACTION_CHOICES)
    module = models.CharField(max_length=100)
    description = models.TextField()
    affected_resident = models.CharField(max_length=255, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name_plural = 'Activity Logs'
    
    def __str__(self):
        return f"{self.user} - {self.action} - {self.timestamp}"

    def save(self, *args, **kwargs):
        if self.pk:
            raise ProtectedError('Audit logs cannot be edited.', [self])
        if self.user and not self.username:
            self.username = self.user.username
        if self.user and not self.user_role:
            if self.user.is_superuser:
                self.user_role = 'admin'
            elif hasattr(self.user, 'staff_profile'):
                self.user_role = self.user.staff_profile.role
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ProtectedError('Audit logs cannot be deleted.', [self])
    

class SystemSetting(models.Model):
    """System configuration settings"""
    # General Settings
    barangay_name = models.CharField(max_length=200, default='Barangay Poblacion')
    barangay_address = models.TextField(default='Poblacion, Santa Catalina, Negros Oriental')
    contact_number = models.CharField(max_length=20, default='(032) 123-4567')
    email = models.EmailField(default='brgy.poblacion@bims.gov.ph')
    office_hours = models.CharField(max_length=500, default='Monday to Friday: 8:00 AM - 5:00 PM')
    
    # Notification Settings
    email_notifications = models.BooleanField(default=True)
    claim_deadline_days = models.IntegerField(default=7)
    
    # Security Settings
    session_timeout = models.IntegerField(default=30)
    min_password_length = models.IntegerField(default=8)
    max_login_attempts = models.IntegerField(default=5)
    
    # Maintenance
    last_backup = models.DateTimeField(null=True, blank=True)
    
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    def __str__(self):
        return "System Settings"
    
    class Meta:
        verbose_name_plural = "System Settings"
