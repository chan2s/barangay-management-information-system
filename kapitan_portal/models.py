from django.db import models
from django.contrib.auth.models import User
from Blotter_Module.models import Blotter, Schedule
from django.utils import timezone

class KapitanNote(models.Model):
    """Notes and announcements from Kapitan"""
    title = models.CharField(max_length=200)
    content = models.TextField()
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.title

class MeetingAgenda(models.Model):
    """Agenda items for blotter hearings"""
    hearing = models.ForeignKey(Schedule, on_delete=models.CASCADE, related_name='agendas')
    agenda_item = models.TextField()
    notes = models.TextField(blank=True)
    order = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return f"Agenda for {self.hearing}"

class MeetingMinute(models.Model):
    """Minutes of the meeting/hearing"""
    hearing = models.OneToOneField(Schedule, on_delete=models.CASCADE, related_name='minutes')
    summary = models.TextField()
    decisions = models.TextField(blank=True)
    follow_up_actions = models.TextField(blank=True)
    recorded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    recorded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Minutes for {self.hearing}"