from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.core.exceptions import PermissionDenied

def role_required(allowed_roles=[]):
    """
    Decorator to check if user has required role
    Usage: @role_required(['admin', 'kapitan'])
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            
            # Superuser has access to everything
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            
            # Check if user has staff profile with allowed role
            if hasattr(request.user, 'staff_profile'):
                user_role = request.user.staff_profile.role
                if user_role in allowed_roles:
                    return view_func(request, *args, **kwargs)
            
            messages.error(request, 'Access denied. Insufficient permissions.')
            return redirect('dashboard')
        return wrapper
    return decorator

def permission_required(permission):
    """
    Decorator to check if user has specific permission
    Usage: @permission_required('approve_certificate')
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            
            if hasattr(request.user, 'staff_profile'):
                if request.user.staff_profile.has_permission(permission):
                    return view_func(request, *args, **kwargs)
            
            messages.error(request, 'Access denied. You don\'t have permission for this action.')
            return redirect('dashboard')
        return wrapper
    return decorator