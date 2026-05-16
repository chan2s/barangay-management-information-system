from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse


def csrf_failure(request, reason=''):
    login_url = reverse('login')
    message = 'Your session or security token expired. Please sign in again and retry.'

    if (
        request.headers.get('x-requested-with') == 'XMLHttpRequest'
        or 'application/json' in request.headers.get('accept', '')
    ):
        return JsonResponse({'detail': message, 'login_url': login_url}, status=403)

    messages.warning(request, message)
    return redirect(f'{login_url}?next={request.get_full_path()}')
