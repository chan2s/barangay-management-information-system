from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required  # ✅ FIX: added import
from django.contrib.auth.models import User
from django.contrib import messages
from django.conf import settings
from django.core.cache import cache
from django.db.models import Q  # ✅ FIX: was missing, caused NameError in get_public_announcements
from staff_module.models import Staff, AuditLog
from staff_module.models import Announcement
from staff_module.audit import log_activity
from django.utils import timezone

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def login_view(request):
    context = {
        'hide_navbar': True,
        'hide_footer': True,
        'hide_dashboard_styles': True,
    }
    
    if request.method == "POST":
        username = (request.POST.get('username') or '').strip()
        password = request.POST.get('password')
        ip_address = get_client_ip(request)
        rate_key = f'login-attempts:{ip_address}:{username.lower()}'
        attempts = cache.get(rate_key, 0)

        if attempts >= 5:
            log_activity(request, 'login_failed', 'auth', f'Locked login attempt for {username}')
            messages.error(request, 'Too many failed login attempts. Please try again in 15 minutes.')
            return render(request, 'login.html', context)
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            request.session.set_expiry(settings.SESSION_COOKIE_AGE)
            cache.delete(rate_key)
            
            # Log login
            AuditLog.objects.create(
                user=user,
                user_role=user.staff_profile.role if hasattr(user, 'staff_profile') else 'public',
                action='login',
                module='auth',
                description=f'User {username} logged in',
                ip_address=ip_address
            )
            log_activity(request, 'login', 'auth', f'User {username} logged in')
            
            # Role-based redirect
            if user.is_superuser:
                return redirect('admin_panel:dashboard')
            
            if hasattr(user, 'staff_profile'):
                role = user.staff_profile.role
                if role == 'kapitan':
                    return redirect('kapitan_portal:dashboard')
                elif role == 'admin':
                    return redirect('admin_panel:dashboard')
                else:
                    return redirect('staff_module:staff_dashboard')
            else:
                return redirect('dashboard')
        else:
            cache.set(rate_key, attempts + 1, 15 * 60)
            log_activity(request, 'login_failed', 'auth', f'Failed login attempt for {username}')
            messages.error(request, 'Invalid username or password')
            return render(request, 'login.html', context)
    
    return render(request, 'login.html', context)

def logout_view(request):
    # ✅ FIX: only log out on POST — base.html logout is now a POST form
    if request.method == 'POST':
        if request.user.is_authenticated:
            AuditLog.objects.create(
                user=request.user,
                user_role=request.user.staff_profile.role if hasattr(request.user, 'staff_profile') else 'public',
                action='logout',
                module='auth',
                description=f'User {request.user.username} logged out',
                ip_address=get_client_ip(request)
            )
            log_activity(request, 'logout', 'auth', f'User {request.user.username} logged out')
        logout(request)
    return redirect('login')

def signup_view(request):
    context = {
        'hide_navbar': True,
        'hide_footer': True,
        'hide_dashboard_styles': True,
    }
    
    if request.method == "POST":
        username = (request.POST.get('username') or '').strip()
        email = (request.POST.get('email') or '').strip().lower()
        password = request.POST.get('password')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already taken')
            return render(request, 'signup.html', context)
        
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered')
            return render(request, 'signup.html', context)
        
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )
        user.save()
        
        messages.success(request, 'Account created successfully! Please login.')
        return redirect('login')
    
    return render(request, 'signup.html', context)

# ✅ FIX: @login_required added — unauthenticated users are redirected to login
@login_required(login_url='login')
def dashboard(request):
    """Regular user dashboard (public)"""
    return render(request, 'dashboard.html')


def get_public_announcements(request):
    """API or context processor for public announcements"""
    # Get active announcements that are not expired
    announcements = Announcement.objects.filter(
        is_active=True,
        scheduled_date__lte=timezone.now()
    ).filter(
        # ✅ FIX: was models.Q which caused NameError — now uses Q imported from django.db.models
        Q(expires_at__isnull=True) | Q(expires_at__gt=timezone.now())
    ).order_by('-priority', '-created_at')[:10]
    
    return announcements
