import logging

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.core.validators import validate_ipv46_address
from django.utils import timezone

logger = logging.getLogger(__name__)


def get_client_ip(request):
    forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR', '')
    if forwarded_for:
        ip_address = forwarded_for.split(',')[0].strip()
    else:
        ip_address = request.META.get('REMOTE_ADDR')

    try:
        validate_ipv46_address(ip_address)
    except (TypeError, ValidationError):
        return None
    return ip_address


def get_admin_email_recipients():
    recipients = [email for _name, email in getattr(settings, 'ADMINS', []) if email]
    extra_recipients = getattr(settings, 'VISITOR_ALERT_EMAILS', [])
    recipients.extend(extra_recipients)
    if not recipients and getattr(settings, 'EMAIL_HOST_USER', ''):
        recipients.append(settings.EMAIL_HOST_USER)
    return list(dict.fromkeys(recipients))


def send_new_visitor_admin_email(visitor_log):
    recipients = get_admin_email_recipients()
    if not recipients:
        logger.warning('Visitor alert skipped: no admin email recipients configured.')
        return False

    timestamp = timezone.localtime(visitor_log.timestamp).strftime('%B %d, %Y %I:%M %p %Z')
    subject = 'BIMS New Unregistered Visitor Detected'
    message = (
        'A new unregistered visitor session was detected in BIMS.\n\n'
        f'IP address: {visitor_log.ip_address or "Unknown"}\n'
        f'Visited page: {visitor_log.visited_path}\n'
        f'User agent: {visitor_log.user_agent or "Unknown"}\n'
        f'Timestamp: {timestamp}\n'
    )

    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            recipients,
            fail_silently=False,
        )
        return True
    except Exception:
        logger.exception('Failed to send visitor alert email for log id=%s.', visitor_log.pk)
        return False
