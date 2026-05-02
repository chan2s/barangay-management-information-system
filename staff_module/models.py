from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class Staff(models.Model):
    ROLE_CHOICES = [
        ('admin', 'Administrator'),
        ('barangay_official', 'Barangay Official'),
        ('secretary', 'Secretary'),
        ('treasurer', 'Treasurer'),
        ('staff', 'Staff'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='staff_profile')
    role = models.CharField(max_length=50, choices=ROLE_CHOICES, default='staff')
    employee_id = models.CharField(max_length=20, unique=True, blank=True)
    position = models.CharField(max_length=100, blank=True)
    contact_number = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    date_hired = models.DateField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} - {self.get_role_display()}"
    
    def save(self, *args, **kwargs):
        if not self.employee_id:
            import datetime
            year = datetime.datetime.now().year
            last_staff = Staff.objects.filter(employee_id__startswith=f'STAFF-{year}').order_by('-employee_id').first()
            if last_staff and last_staff.employee_id:
                last_num = int(last_staff.employee_id.split('-')[-1])
                new_num = last_num + 1
            else:
                new_num = 1
            self.employee_id = f'STAFF-{year}-{new_num:04d}'
        super().save(*args, **kwargs)

@receiver(post_save, sender=User)
def create_staff_profile(sender, instance, created, **kwargs):
    if created:
        Staff.objects.get_or_create(user=instance)  # Use get_or_create instead

@receiver(post_save, sender=User)
def save_staff_profile(sender, instance, **kwargs):
    try:
        instance.staff_profile.save()
    except Staff.DoesNotExist:
        # Create profile if it doesn't exist
        Staff.objects.create(user=instance)