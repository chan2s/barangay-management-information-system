from staff_module.models import Announcement
from django.utils import timezone
from django.db.models import Q

def announcements_context(request):
    """Make active announcements available to all templates"""
    try:
        now = timezone.now()
        
        announcements = Announcement.objects.filter(
            is_active=True
        ).filter(
            Q(scheduled_date__isnull=True) | Q(scheduled_date__lte=now)
        ).filter(
            Q(expires_at__isnull=True) | Q(expires_at__gt=now)
        ).order_by('-priority', '-created_at')[:6]
        
        return {
            'announcements': announcements,
            'has_announcements': announcements.exists(),
        }
    except Exception:
        return {
            'announcements': [],
            'has_announcements': False,
        }
