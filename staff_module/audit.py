from staff_module.models import ActivityLog


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0]
    return request.META.get('REMOTE_ADDR')


def get_role(user):
    if not user or not user.is_authenticated:
        return 'anonymous'
    if user.is_superuser:
        return 'admin'
    if hasattr(user, 'staff_profile'):
        return user.staff_profile.role
    return 'public'


def log_activity(request, action, module, description, affected_resident=''):
    user = request.user if getattr(request, 'user', None) and request.user.is_authenticated else None
    return ActivityLog.objects.create(
        user=user,
        username=user.username if user else '',
        user_role=get_role(user),
        action=action,
        module=module,
        description=description,
        affected_resident=affected_resident or '',
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', '')[:1000],
    )
