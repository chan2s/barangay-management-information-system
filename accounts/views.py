from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from staff_module.models import Staff, AuditLog
from staff_module.models import Announcement
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
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            
            # Log login
            AuditLog.objects.create(
                user=user,
                user_role=user.staff_profile.role if hasattr(user, 'staff_profile') else 'public',
                action='login',
                module='auth',
                description=f'User {username} logged in',
                ip_address=get_client_ip(request)
            )
            
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
            messages.error(request, 'Invalid username or password')
            return render(request, 'login.html', context)
    
    return render(request, 'login.html', context)

def logout_view(request):
    if request.user.is_authenticated:
        AuditLog.objects.create(
            user=request.user,
            user_role=request.user.staff_profile.role if hasattr(request.user, 'staff_profile') else 'public',
            action='logout',
            module='auth',
            description=f'User {request.user.username} logged out',
            ip_address=get_client_ip(request)
        )
    logout(request)
    return redirect('login')

def signup_view(request):
    context = {
        'hide_navbar': True,
        'hide_footer': True,
        'hide_dashboard_styles': True,
    }
    
    if request.method == "POST":
        username = request.POST.get('username')
        email = request.POST.get('email')
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
        models.Q(expires_at__isnull=True) | models.Q(expires_at__gt=timezone.now())
    ).order_by('-priority', '-created_at')[:10]
    
    return announcements