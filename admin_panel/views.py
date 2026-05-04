from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from staff_module.models import Staff
from Blotter_Module.models import Blotter
from certificates.models import CertificateRequest

@login_required
def admin_dashboard(request):
    """Admin dashboard with system overview"""
    # Check if user is admin (superuser or staff with admin role)
    if not request.user.is_superuser and not (hasattr(request.user, 'staff_profile') and request.user.staff_profile.role == 'admin'):
        messages.error(request, 'Access denied. Admin only area.')
        return redirect('dashboard')
    
    # Statistics
    total_users = User.objects.count()
    total_staff = Staff.objects.count()
    total_residents = User.objects.filter(is_staff=False, is_superuser=False).count()
    total_blotters = Blotter.objects.count()
    total_certificates = CertificateRequest.objects.count()
    
    # Recent users
    recent_users = User.objects.all().order_by('-date_joined')[:10]
    
    # Recent blotters
    recent_blotters = Blotter.objects.all().order_by('-created_at')[:10]
    
    context = {
        'total_users': total_users,
        'total_staff': total_staff,
        'total_residents': total_residents,
        'total_blotters': total_blotters,
        'total_certificates': total_certificates,
        'recent_users': recent_users,
        'recent_blotters': recent_blotters,
        'staff': request.user.staff_profile if hasattr(request.user, 'staff_profile') else None,
        'user': request.user,
    }
    return render(request, 'admin_panel/dashboard.html', context)

@login_required
def user_list(request):
    """List all users with search and filters"""
    if not request.user.is_superuser:
        messages.error(request, 'Access denied. Superuser only.')
        return redirect('admin_dashboard')
    
    users = User.objects.all().order_by('-date_joined')
    
    # Search
    search_query = request.GET.get('search', '')
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query)
        )
    
    # Filter by role
    role_filter = request.GET.get('role', '')
    if role_filter == 'staff':
        users = users.filter(is_staff=True)
    elif role_filter == 'superuser':
        users = users.filter(is_superuser=True)
    elif role_filter == 'resident':
        users = users.filter(is_staff=False, is_superuser=False)
    
    paginator = Paginator(users, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'users': page_obj,
        'search_query': search_query,
        'role_filter': role_filter,
        'total_users': users.count(),
        'staff': request.user.staff_profile if hasattr(request.user, 'staff_profile') else None,
        'user': request.user,
    }
    return render(request, 'admin_panel/user_list.html', context)

@login_required
def user_create(request):
    """Create a new user account"""
    if not request.user.is_superuser:
        messages.error(request, 'Access denied. Superuser only.')
        return redirect('admin_dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        is_staff = request.POST.get('is_staff') == 'on'
        is_superuser = request.POST.get('is_superuser') == 'on'
        
        # Validation
        errors = []
        if User.objects.filter(username=username).exists():
            errors.append('Username already exists')
        if User.objects.filter(email=email).exists():
            errors.append('Email already registered')
        if password != confirm_password:
            errors.append('Passwords do not match')
        if len(password) < 6:
            errors.append('Password must be at least 6 characters')
        
        if errors:
            for error in errors:
                messages.error(request, error)
        else:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                is_staff=is_staff,
                is_superuser=is_superuser
            )
            messages.success(request, f'User {username} created successfully!')
            return redirect('admin_panel:user_list')
    
    context = {
        'staff': request.user.staff_profile if hasattr(request.user, 'staff_profile') else None,
        'user': request.user,
    }
    return render(request, 'admin_panel/user_create.html', context)

@login_required
def user_edit(request, user_id):
    """Edit a user account"""
    if not request.user.is_superuser:
        messages.error(request, 'Access denied. Superuser only.')
        return redirect('admin_dashboard')
    
    edit_user = get_object_or_404(User, id=user_id)
    
    # Prevent admin from editing their own role incorrectly
    is_self = edit_user.id == request.user.id
    
    if request.method == 'POST':
        edit_user.first_name = request.POST.get('first_name', '')
        edit_user.last_name = request.POST.get('last_name', '')
        edit_user.email = request.POST.get('email', '')
        
        if not is_self:
            edit_user.is_staff = request.POST.get('is_staff') == 'on'
            edit_user.is_superuser = request.POST.get('is_superuser') == 'on'
        
        password = request.POST.get('password', '')
        if password:
            if len(password) >= 6:
                edit_user.set_password(password)
                messages.success(request, 'Password updated successfully!')
            else:
                messages.error(request, 'Password must be at least 6 characters')
        
        edit_user.save()
        messages.success(request, f'User {edit_user.username} updated successfully!')
        return redirect('admin_panel:user_list')
    
    context = {
        'edit_user': edit_user,
        'is_self': is_self,
        'staff': request.user.staff_profile if hasattr(request.user, 'staff_profile') else None,
        'user': request.user,
    }
    return render(request, 'admin_panel/user_edit.html', context)

@login_required
def user_delete(request, user_id):
    """Delete a user account"""
    if not request.user.is_superuser:
        messages.error(request, 'Access denied. Superuser only.')
        return redirect('admin_dashboard')
    
    delete_user = get_object_or_404(User, id=user_id)
    
    # Prevent self-deletion
    if delete_user.id == request.user.id:
        messages.error(request, 'You cannot delete your own account!')
        return redirect('admin_panel:user_list')
    
    if request.method == 'POST':
        username = delete_user.username
        delete_user.delete()
        messages.success(request, f'User {username} has been deleted successfully!')
        return redirect('admin_panel:user_list')
    
    context = {
        'delete_user': delete_user,
        'staff': request.user.staff_profile if hasattr(request.user, 'staff_profile') else None,
        'user': request.user,
    }
    return render(request, 'admin_panel/user_delete.html', context)

@login_required
def system_settings(request):
    """System settings page"""
    if not request.user.is_superuser:
        messages.error(request, 'Access denied. Superuser only.')
        return redirect('admin_dashboard')
    
    context = {
        'staff': request.user.staff_profile if hasattr(request.user, 'staff_profile') else None,
        'user': request.user,
    }
    return render(request, 'admin_panel/system_settings.html', context)