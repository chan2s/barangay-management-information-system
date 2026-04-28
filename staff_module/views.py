from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from .models import Staff
from Blotter_Module.models import Blotter

@login_required(login_url='login')
def staff_dashboard(request):
    """Staff dashboard - only accessible by staff members"""
    try:
        staff_profile = request.user.staff_profile
        context = {
            'staff': staff_profile,
            'user': request.user,
        }
        return render(request, 'staff_module/dashboard.html', context)
    except Staff.DoesNotExist:
        messages.error(request, 'Access denied. Staff only area.')
        return redirect('dashboard')

@login_required(login_url='login')
def staff_blotter_list(request):
    """View all blotters (for staff)"""
    try:
        staff_profile = request.user.staff_profile
        blotters = Blotter.objects.all().order_by('-created_at')
        context = {
            'staff': staff_profile,
            'blotters': blotters,
            'user': request.user,
        }
        return render(request, 'staff_module/blotter_list.html', context)
    except Staff.DoesNotExist:
        messages.error(request, 'Access denied. Staff only area.')
        return redirect('dashboard')

@login_required(login_url='login')
def staff_blotter_detail(request, blotter_id):
    """View blotter details"""
    try:
        staff_profile = request.user.staff_profile
        blotter = get_object_or_404(Blotter, id=blotter_id)
        context = {
            'staff': staff_profile,
            'blotter': blotter,
            'user': request.user,
        }
        return render(request, 'staff_module/blotter_detail.html', context)
    except Staff.DoesNotExist:
        messages.error(request, 'Access denied. Staff only area.')
        return redirect('dashboard')

@login_required(login_url='login')
def staff_list(request):
    """View all staff members (admin only)"""
    if request.user.staff_profile.role != 'admin':
        messages.error(request, 'Admin access required')
        return redirect('staff_dashboard')
    
    staff_members = Staff.objects.all().select_related('user')
    return render(request, 'staff_module/staff_list.html', {'staff_members': staff_members})

@login_required(login_url='login')
def staff_create(request):
    """Create new staff member (admin only)"""
    if request.user.staff_profile.role != 'admin':
        messages.error(request, 'Admin access required')
        return redirect('staff_dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        role = request.POST.get('role')
        position = request.POST.get('position')
        contact_number = request.POST.get('contact_number')
        
        # Create user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )
        
        # Update staff profile
        user.staff_profile.role = role
        user.staff_profile.position = position
        user.staff_profile.contact_number = contact_number
        user.staff_profile.save()
        
        messages.success(request, f'Staff {username} created successfully!')
        return redirect('staff_list')
    
    return render(request, 'staff_module/staff_create.html')

@login_required(login_url='login')
def staff_edit(request, staff_id):
    """Edit staff member (admin only)"""
    if request.user.staff_profile.role != 'admin':
        messages.error(request, 'Admin access required')
        return redirect('staff_dashboard')
    
    staff = get_object_or_404(Staff, id=staff_id)
    
    if request.method == 'POST':
        staff.role = request.POST.get('role')
        staff.position = request.POST.get('position')
        staff.contact_number = request.POST.get('contact_number')
        staff.address = request.POST.get('address')
        staff.is_active = request.POST.get('is_active') == 'on'
        staff.save()
        
        messages.success(request, f'Staff {staff.user.username} updated successfully!')
        return redirect('staff_list')
    
    return render(request, 'staff_module/staff_edit.html', {'staff': staff})