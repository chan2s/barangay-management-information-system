from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from staff_module.models import Staff  # Import Staff model

def login_view(request):
    context = {
        'hide_navbar': True,
        'hide_footer': True,
        'hide_dashboard_styles': True,  # Use auth-specific styles only
    }
    
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            
            # Check if user is superuser (admin)
            if user.is_superuser:
                return redirect('admin_panel:dashboard')
            
            # Check if user has a staff profile
            try:
                if hasattr(user, 'staff_profile') and user.staff_profile:
                    # Check if role is kapitan
                    if user.staff_profile.role == 'kapitan':
                        return redirect('kapitan_portal:dashboard')
                    elif user.staff_profile.role == 'admin':
                        return redirect('admin_panel:dashboard')
                    else:
                        return redirect('staff_module:staff_dashboard')
                else:
                    # Regular user (non-staff) - redirect to public dashboard
                    return redirect('dashboard')
            except Staff.DoesNotExist:
                return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password')
            return render(request, 'login.html', context)
    
    return render(request, 'login.html', context)

def signup_view(request):
    context = {
        'hide_navbar': True,
        'hide_footer': True,
        'hide_dashboard_styles': True,  # Use auth-specific styles only
    }
    
    if request.method == "POST":
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        # Check if username already exists
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already taken')
            return render(request, 'signup.html', context)
        
        # Check if email already exists
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered')
            return render(request, 'signup.html', context)
        
        # Create user (regular user, not staff)
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

def logout_view(request):
    logout(request)
    return redirect('login')