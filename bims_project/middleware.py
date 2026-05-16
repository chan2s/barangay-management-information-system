from django.conf import settings
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse


class SessionExpiredMiddleware:
    """Return a predictable response when authenticated-only requests lose session state."""

    PUBLIC_PREFIXES = (
        '/accounts/login/',
        '/accounts/signup/',
        '/blotter/',
        '/certificates/',
        '/media/',
        '/static/',
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        protected_post = request.method == 'POST' and not self._is_public_path(request.path)
        if protected_post and not request.user.is_authenticated:
            login_url = reverse(settings.LOGIN_URL)
            if self._is_ajax(request):
                return JsonResponse(
                    {
                        'detail': 'Your session has expired. Please sign in again.',
                        'login_url': login_url,
                    },
                    status=401,
                )
            messages.warning(request, 'Your session has expired. Please sign in again.')
            return redirect(f'{login_url}?next={request.get_full_path()}')

        return self.get_response(request)

    def _is_public_path(self, path):
        return any(path.startswith(prefix) for prefix in self.PUBLIC_PREFIXES)

    def _is_ajax(self, request):
        return (
            request.headers.get('x-requested-with') == 'XMLHttpRequest'
            or 'application/json' in request.headers.get('accept', '')
        )
