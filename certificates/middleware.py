import logging

from django.conf import settings

from .models import VisitorLog
from .visitor_utils import get_client_ip, send_new_visitor_admin_email

logger = logging.getLogger(__name__)


class VisitorTrackingMiddleware:
    SESSION_KEY = 'visitor_alert_sent'

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        self.track_visit(request)
        return self.get_response(request)

    def track_visit(self, request):
        if not self.should_track(request):
            return

        try:
            visitor_log = VisitorLog.objects.create(
                ip_address=get_client_ip(request),
                user_agent=(request.META.get('HTTP_USER_AGENT') or '')[:2000],
                visited_path=request.get_full_path()[:2048],
            )
        except Exception:
            logger.exception('Visitor tracking failed for path %s.', request.path)
            return

        if not request.session.get(self.SESSION_KEY):
            request.session[self.SESSION_KEY] = True
            send_new_visitor_admin_email(visitor_log)

    def should_track(self, request):
        user = getattr(request, 'user', None)
        if user and user.is_authenticated:
            return False
        if request.method not in ('GET', 'HEAD'):
            return False

        path = request.path or '/'
        static_url = '/' + settings.STATIC_URL.lstrip('/')
        excluded_prefixes = [
            '/admin',
            static_url,
            settings.STATIC_URL,
            settings.MEDIA_URL,
            '/favicon.ico',
        ]

        return not any(path.startswith(prefix) for prefix in excluded_prefixes if prefix)
