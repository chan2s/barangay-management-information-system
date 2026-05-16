from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db.models import Q, Count
from staff_module.models import Staff, AuditLog
from staff_module.decorators import role_required
from staff_module.models import ActivityLog, SystemSetting
from django.core import serializers
from django.db import connection
import csv
import json
from django.utils import timezone
from django.http import JsonResponse, HttpResponse, HttpResponseForbidden
from django.conf import settings
from Blotter_Module.models import Blotter
from certificates.models import CertificateRequest
from staff_module.models import Announcement, Appointment, ActivityLog, SystemSetting
from accounts.forms import ResidentForm
from accounts.models import Resident, ResidentExportRequest
from accounts.resident_exports import (
    AGE_GROUP_CHOICES,
    SEX_FILTER_CHOICES,
    apply_age_group,
    apply_resident_category,
    filtered_residents_from_request,
    normalize_export_filters,
)
from accounts.services import user_account_exists
from staff_module.audit import log_activity

@login_required
@role_required(['admin'])
def admin_dashboard(request):
    """Admin dashboard"""
    residents = Resident.objects.filter(is_deleted=False)
    today = timezone.localdate()
    total_users = User.objects.count()
    total_staff = Staff.objects.count()
    total_admins = Staff.objects.filter(role='admin').count()
    total_kapitan = Staff.objects.filter(role='kapitan').count()
    total_residents = residents.count()
    total_households = residents.exclude(household_number='').values('household_number').distinct().count()
    senior_count = sum(1 for resident in residents if resident.age >= 60)
    minor_count = sum(1 for resident in residents if resident.age < 18)
    voter_age_count = sum(1 for resident in residents if resident.age >= 18)
    male_count = residents.filter(sex='male').count()
    female_count = residents.filter(sex='female').count()
    
    recent_logs = AuditLog.objects.all()[:10]
    recent_users = User.objects.all().order_by('-date_joined')[:10]
    recent_activity = ActivityLog.objects.all()[:10]
    
    context = {
        'total_users': total_users,
        'total_staff': total_staff,
        'total_admins': total_admins,
        'total_kapitan': total_kapitan,
        'total_residents': total_residents,
        'total_households': total_households,
        'senior_count': senior_count,
        'minor_count': minor_count,
        'voter_age_count': voter_age_count,
        'male_count': male_count,
        'female_count': female_count,
        'recent_logs': recent_logs,
        'recent_users': recent_users,
        'recent_activity': recent_activity,
        'staff': request.user.staff_profile if hasattr(request.user, 'staff_profile') else None,
        'user': request.user,
    }
    return render(request, 'admin_panel/dashboard.html', context)

@login_required
@role_required(['admin'])
def user_list(request):
    """List all users"""
    users = User.objects.all().order_by('-date_joined')
    
    search_query = request.GET.get('search', '')
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query)
        )
    
    paginator = Paginator(users, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'users': page_obj,
        'search_query': search_query,
        'staff': request.user.staff_profile if hasattr(request.user, 'staff_profile') else None,
    }
    return render(request, 'admin_panel/user_list.html', context)

@login_required
@role_required(['admin'])
def user_create(request):
    """Create a new user with staff role"""
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        role = request.POST.get('role', 'staff')
        if role not in ['admin', 'staff', 'kapitan']:
            role = 'staff'
        position = request.POST.get('position', '')
        contact_number = request.POST.get('contact_number', '')
        
        # Validation
        errors = []
        if User.objects.filter(username__iexact=username).exists():
            errors.append('Username already exists')
        if User.objects.filter(email__iexact=email).exists():
            errors.append('Email already registered')
        if password != confirm_password:
            errors.append('Passwords do not match')
        try:
            validate_password(password)
        except ValidationError as exc:
            errors.extend(exc.messages)
        
        if errors:
            for error in errors:
                messages.error(request, error)
        else:
            # Create user
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )
            
            if role != 'user':
                Staff.objects.create(
                    user=user,
                    role=role,
                    position=position,
                    contact_number=contact_number
                )
            
            log_activity(request, 'create', 'user', f'Created user {username} with role {role}')
            messages.success(request, f'User {username} created successfully!')
            return redirect('admin_panel:user_list')
    
    context = {
        'role_choices': Staff.ROLE_CHOICES,
        'staff': request.user.staff_profile if hasattr(request.user, 'staff_profile') else None,
    }
    return render(request, 'admin_panel/user_create.html', context)


@login_required
@role_required(['admin', 'staff'])
def resident_list(request):
    base_residents = Resident.objects.filter(is_deleted=False)
    residents = base_residents
    search_query = request.GET.get('search', '').strip()
    purok_filter = request.GET.get('purok', '').strip()
    category_filter = request.GET.get('category', '').strip()
    age_group_filter = request.GET.get('age_group', '').strip()
    sex_filter = request.GET.get('sex', '').strip()
    if search_query:
        residents = residents.filter(
            Q(full_name__icontains=search_query)
            | Q(resident_id__icontains=search_query)
            | Q(contact_number__icontains=search_query)
            | Q(email__icontains=search_query)
            | Q(household_number__icontains=search_query)
        )
    if purok_filter:
        residents = residents.filter(purok=purok_filter)
    if sex_filter:
        residents = residents.filter(sex=sex_filter)
    residents = apply_age_group(residents, age_group_filter)
    residents = apply_resident_category(residents, category_filter)

    paginator = Paginator(residents, 20)
    page_obj = paginator.get_page(request.GET.get('page'))
    can_review_exports = user_has_role(request.user, ['admin'])
    has_filters = any([search_query, purok_filter, category_filter, age_group_filter, sex_filter])
    pending_export_count = ResidentExportRequest.objects.filter(status='pending').count() if can_review_exports else 0
    approved_export_count = ResidentExportRequest.objects.filter(status='approved').count() if can_review_exports else 0
    return render(request, 'admin_panel/resident_list.html', {
        'residents': page_obj,
        'search_query': search_query,
        'purok_filter': purok_filter,
        'category_filter': category_filter,
        'age_group_filter': age_group_filter,
        'sex_filter': sex_filter,
        'purok_choices': Resident.PUROK_CHOICES,
        'category_choices': ResidentExportRequest.CATEGORY_CHOICES,
        'age_group_choices': AGE_GROUP_CHOICES,
        'sex_choices': SEX_FILTER_CHOICES,
        'total_count': residents.count(),
        'total_residents': base_residents.count(),
        'has_filters': has_filters,
        'pending_export_count': pending_export_count,
        'approved_export_count': approved_export_count,
        'can_manage': user_has_role(request.user, ['admin', 'staff']),
        'can_delete': user_has_role(request.user, ['admin']),
        'pending_exports': ResidentExportRequest.objects.select_related('requested_by').filter(status='pending')[:10] if can_review_exports else [],
        'approved_exports': ResidentExportRequest.objects.select_related('requested_by', 'approved_by').filter(status='approved')[:10] if can_review_exports else [],
    })


@login_required
@role_required(['admin', 'staff'])
def resident_create(request):
    if request.method == 'POST':
        form = ResidentForm(request.POST, request.FILES)
        if form.is_valid():
            email = form.cleaned_data.get('email')
            resident_id = form.cleaned_data.get('resident_id')
            if user_account_exists(email=email, username=resident_id):
                form.add_error(None, 'A user account already exists with this resident ID or email.')
            else:
                resident = form.save()
                log_activity(request, 'create', 'residents', f'Resident record created: {resident.resident_id} - {resident.full_name}', str(resident))
                messages.success(request, 'Resident record saved successfully.')
                return redirect('admin_panel:resident_list')
    else:
        form = ResidentForm()
    return render(request, 'admin_panel/resident_form.html', {'form': form, 'mode': 'Create'})


@login_required
@role_required(['admin', 'staff'])
def resident_edit(request, resident_id):
    resident = get_object_or_404(Resident, id=resident_id, is_deleted=False)
    if request.method == 'POST':
        form = ResidentForm(request.POST, request.FILES, instance=resident)
        if form.is_valid():
            resident = form.save()
            log_activity(request, 'update', 'residents', f'Resident record updated: {resident.resident_id} - {resident.full_name}', str(resident))
            messages.success(request, 'Resident record updated successfully.')
            return redirect('admin_panel:resident_list')
    else:
        form = ResidentForm(instance=resident)
    return render(request, 'admin_panel/resident_form.html', {'form': form, 'mode': 'Edit', 'resident': resident})


@login_required
@role_required(['admin'])
def resident_delete(request, resident_id):
    resident = get_object_or_404(Resident, id=resident_id, is_deleted=False)
    if request.method == 'POST':
        resident.is_deleted = True
        resident.deleted_at = timezone.now()
        resident.deleted_by = request.user
        resident.save(update_fields=['is_deleted', 'deleted_at', 'deleted_by', 'updated_at'])
        log_activity(request, 'delete', 'residents', f'Resident soft-deleted: {resident.resident_id} - {resident.full_name}', str(resident))
        messages.success(request, 'Resident record archived. Permanent deletion is disabled for audit protection.')
    return redirect('admin_panel:resident_list')


@login_required
@role_required(['admin', 'staff'])
def resident_export_request(request):
    if request.method != 'POST':
        return redirect('admin_panel:resident_list')
    category, filters = normalize_export_filters(request.POST, allow_search=True, allow_category=True)
    reason = request.POST.get('reason', '').strip()
    if not reason:
        messages.error(request, 'Export reason is required.')
        return redirect('admin_panel:resident_list')
    export_request = ResidentExportRequest.objects.create(
        requested_by=request.user,
        category=category,
        filters=filters,
        reason=reason,
    )
    log_activity(request, 'export_attempt', 'residents', f'Resident export requested: {export_request.filter_summary} - {reason}')
    messages.success(request, 'Export request submitted for Admin approval.')
    return redirect('admin_panel:resident_list')


@login_required
@role_required(['admin'])
def resident_export_review(request, request_id):
    export_request = get_object_or_404(ResidentExportRequest, id=request_id, status='pending')
    if request.method == 'POST':
        action = request.POST.get('action')
        export_request.approved_by = request.user
        export_request.reviewed_at = timezone.now()
        if action == 'approve':
            export_request.status = 'approved'
            export_request.save()
            log_activity(request, 'export_approve', 'residents', f'Approved resident export request #{export_request.id}')
            messages.success(request, 'Export request approved. Admin can now generate and download the CSV.')
        elif action == 'reject':
            export_request.status = 'rejected'
            export_request.save()
            log_activity(request, 'export_reject', 'residents', f'Rejected resident export request #{export_request.id}')
            messages.warning(request, 'Export request rejected.')
        else:
            messages.error(request, 'Invalid export review action.')
    return redirect('admin_panel:resident_list')


@login_required
@role_required(['admin'])
def resident_export_download(request, request_id):
    export_request = get_object_or_404(ResidentExportRequest, id=request_id, status='approved')
    residents = filtered_residents_from_request(export_request)
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="resident_export_{export_request.id}.csv"'
    writer = csv.writer(response)
    writer.writerow(['Resident ID', 'Full Name', 'Birthdate', 'Age', 'Sex', 'Purok', 'Address', 'Household', 'Voter Status'])
    for resident in residents[:1000]:
        writer.writerow([
            resident.resident_id,
            resident.full_name,
            resident.birthdate,
            resident.age,
            resident.get_sex_display(),
            resident.get_purok_display() if resident.purok else '',
            resident.address,
            resident.household_number,
            resident.get_voter_status_display(),
        ])
    log_activity(request, 'export_attempt', 'residents', f'Downloaded approved resident export #{export_request.id}')
    return response

@login_required
@role_required(['admin'])
def user_edit(request, user_id):
    """Edit user and assign staff role"""
    edit_user = get_object_or_404(User, id=user_id)
    staff_profile = Staff.objects.filter(user=edit_user).first()
    
    if request.method == 'POST':
        edit_user.first_name = request.POST.get('first_name', '')
        edit_user.last_name = request.POST.get('last_name', '')
        edit_user.email = request.POST.get('email', '')
        edit_user.is_staff = request.POST.get('is_staff') == 'on'
        edit_user.save()
        
        # Create or update staff profile
        role = request.POST.get('role', 'staff')
        if role not in ['admin', 'staff', 'kapitan']:
            role = 'staff'
        if staff_profile:
            staff_profile.role = role
            staff_profile.position = request.POST.get('position', '')
            staff_profile.contact_number = request.POST.get('contact_number', '')
            staff_profile.save()
        else:
            Staff.objects.create(
                user=edit_user,
                role=role,
                position=request.POST.get('position', ''),
                contact_number=request.POST.get('contact_number', '')
            )
        
        # Change password if provided
        password = request.POST.get('password', '')
        if password:
            if len(password) >= 6:
                edit_user.set_password(password)
                edit_user.save()
                messages.success(request, 'Password updated successfully!')
            else:
                messages.error(request, 'Password must be at least 6 characters')
        
        messages.success(request, f'User {edit_user.username} updated successfully!')
        return redirect('admin_panel:user_list')
    
    context = {
        'edit_user': edit_user,
        'staff_profile': staff_profile,
        'role_choices': Staff.ROLE_CHOICES,
        'staff': request.user.staff_profile if hasattr(request.user, 'staff_profile') else None,
    }
    return render(request, 'admin_panel/user_edit.html', context)

@login_required
@role_required(['admin'])
def user_delete(request, user_id):
    """Delete a user account"""
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
    }
    return render(request, 'admin_panel/user_delete.html', context)

@login_required
@role_required(['admin'])
def system_settings(request):
    """System settings page"""
    context = {
        'staff': request.user.staff_profile if hasattr(request.user, 'staff_profile') else None,
    }
    return render(request, 'admin_panel/system_settings.html', context)

@login_required
@role_required(['admin'])
def audit_logs(request):
    """View system audit logs"""
    logs = AuditLog.objects.all().order_by('-timestamp')
    
    # Filter by action
    action_filter = request.GET.get('action', '')
    if action_filter:
        logs = logs.filter(action=action_filter)
    
    paginator = Paginator(logs, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'logs': page_obj,
        'action_filter': action_filter,
        'action_choices': AuditLog.ACTION_CHOICES,
        'staff': request.user.staff_profile if hasattr(request.user, 'staff_profile') else None,
    }
    return render(request, 'admin_panel/audit_logs.html', context)


@login_required
@role_required(['admin'])
def system_settings(request):
    """System settings page"""
    # Get or create settings
    settings_obj, created = SystemSetting.objects.get_or_create(id=1)
    
    if request.method == 'POST':
        settings_obj.barangay_name = request.POST.get('barangay_name', 'Barangay Poblacion')
        settings_obj.barangay_address = request.POST.get('barangay_address', 'Poblacion, Santa Catalina, Negros Oriental')
        settings_obj.contact_number = request.POST.get('contact_number', '(032) 123-4567')
        settings_obj.email = request.POST.get('email', 'brgy.poblacion@bims.gov.ph')
        settings_obj.office_hours = request.POST.get('office_hours', 'Monday to Friday: 8:00 AM - 5:00 PM')
        settings_obj.email_notifications = request.POST.get('email_notifications') == 'on'
        settings_obj.claim_deadline_days = int(request.POST.get('claim_deadline_days', 7))
        settings_obj.session_timeout = int(request.POST.get('session_timeout', 30))
        settings_obj.min_password_length = int(request.POST.get('min_password_length', 8))
        settings_obj.max_login_attempts = int(request.POST.get('max_login_attempts', 5))
        settings_obj.save()
        
        # Log activity
        log_activity(request, 'update', 'system_settings', 'System settings updated')
        
        messages.success(request, 'System settings saved successfully!')
        return redirect('admin_panel:system_settings')
    
    context = {
        'settings': settings_obj,
    }
    return render(request, 'admin_panel/system_settings.html', context)


@login_required
@role_required(['admin'])
def audit_log(request):
    """View system audit logs"""
    logs = ActivityLog.objects.select_related('user').all()
    
    # Filters
    user_filter = request.GET.get('user', '')
    if user_filter:
        logs = logs.filter(user__username__icontains=user_filter)
    
    action_filter = request.GET.get('action', '')
    if action_filter:
        logs = logs.filter(action=action_filter)
    module_filter = request.GET.get('module', '')
    if module_filter:
        logs = logs.filter(module__icontains=module_filter)
    
    date_from = request.GET.get('date_from', '')
    if date_from:
        logs = logs.filter(timestamp__date__gte=date_from)
    
    date_to = request.GET.get('date_to', '')
    if date_to:
        logs = logs.filter(timestamp__date__lte=date_to)
    
    # Pagination
    paginator = Paginator(logs, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'logs': page_obj,
        'user_filter': user_filter,
        'action_filter': action_filter,
        'module_filter': module_filter,
        'date_from': date_from,
        'date_to': date_to,
    }
    return render(request, 'admin_panel/audit_log.html', context)


@login_required
@role_required(['admin'])
def backup_database(request):
    """Download database backup"""
    try:
        # Get database settings
        db_settings = settings.DATABASES['default']
        
        # Create backup filename
        filename = f"bims_backup_{timezone.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        # Get all data from key models
        data = {
            'users': serializers.serialize('json', User.objects.all()),
            'staff': serializers.serialize('json', Staff.objects.all()),
            'blotters': serializers.serialize('json', Blotter.objects.all()),
            'certificates': serializers.serialize('json', CertificateRequest.objects.all()),
            'announcements': serializers.serialize('json', Announcement.objects.all()),
            'appointments': serializers.serialize('json', Appointment.objects.all()),
        }
        
        response = HttpResponse(json.dumps(data, indent=2), content_type='application/json')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        # Log activity
        log_activity(request, 'create', 'backup', f'Database backup created: {filename}')
        
        messages.success(request, f'Backup created successfully!')
        return response
        
    except Exception as e:
        messages.error(request, f'Backup failed: {str(e)}')
        return redirect('admin_panel:system_settings')


@login_required
@role_required(['admin'])
def system_health(request):
    """Check system health status"""
    health_status = {
        'database': 'healthy',
        'storage': 'healthy',
        'email': 'healthy' if settings.EMAIL_HOST_USER else 'not_configured',
        'last_backup': None,
    }
    
    # Check database connection
    try:
        connection.ensure_connection()
        health_status['database'] = 'healthy'
    except:
        health_status['database'] = 'unhealthy'
    
    # Check storage
    try:
        import shutil
        usage = shutil.disk_usage('/')
        free_percent = (usage.free / usage.total) * 100
        if free_percent < 10:
            health_status['storage'] = 'critical'
        elif free_percent < 20:
            health_status['storage'] = 'warning'
        else:
            health_status['storage'] = 'healthy'
    except:
        health_status['storage'] = 'unknown'
    
    return JsonResponse(health_status)


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


@login_required
@role_required(['admin'])
def export_audit_log(request):
    """Export audit logs to CSV"""
    logs = ActivityLog.objects.select_related('user').all()
    
    # Apply filters
    user_filter = request.GET.get('user', '')
    if user_filter:
        logs = logs.filter(user__username__icontains=user_filter)
    
    action_filter = request.GET.get('action', '')
    if action_filter:
        logs = logs.filter(action=action_filter)
    
    date_from = request.GET.get('date_from', '')
    if date_from:
        logs = logs.filter(timestamp__date__gte=date_from)
    
    date_to = request.GET.get('date_to', '')
    if date_to:
        logs = logs.filter(timestamp__date__lte=date_to)
    
    log_activity(request, 'export_attempt', 'audit_log', 'Audit log export downloaded')
    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="audit_log_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Timestamp', 'Username', 'Role', 'Action', 'Module', 'Affected Resident', 'Description', 'IP Address', 'Browser/Device'])
    
    for log in logs:
        writer.writerow([
            log.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            log.username or (log.user.username if log.user else 'System'),
            log.user_role,
            log.action,
            log.module,
            log.affected_resident,
            log.description,
            log.ip_address or '',
            log.user_agent or '',
        ])
    
    return response


def user_has_role(user, roles):
    if user.is_superuser:
        return 'admin' in roles
    return hasattr(user, 'staff_profile') and user.staff_profile.role in roles
