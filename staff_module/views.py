from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.utils import timezone
from django.http import JsonResponse
from .models import Staff
from Blotter_Module.models import Blotter, Schedule, Evidence, BlotterAuditLog, Notification
from Blotter_Module.forms import ScheduleForm, EvidenceForm, CommentForm, BlotterStatusForm
from django.contrib.auth.models import User
from django.template.loader import get_template


# ====================== STAFF DASHBOARD ======================
@login_required(login_url='login')
def staff_dashboard(request):
    """Staff dashboard with statistics"""
    try:
        staff_profile = request.user.staff_profile
        
        # Get statistics from blotter module
        total_blotters = Blotter.objects.count()
        pending = Blotter.objects.filter(status='pending').count()
        scheduled = Schedule.objects.filter(is_completed=False).count()
        resolved = Blotter.objects.filter(status='resolved').count()
        unsettled = Blotter.objects.filter(status='in_progress').count()
        
        # NEW: Pending approvals count for staff review
        pending_approvals_count = Blotter.objects.filter(is_approved=False, status='pending').count()
        
        # Today's hearings
        today_hearings = Schedule.objects.filter(
            hearing_date__date=timezone.now().date(),
            is_completed=False
        ).select_related('blotter')[:5]
        
        # Recent blotters
        recent_blotters = Blotter.objects.all().order_by('-created_at')[:10]
        
        context = {
            'staff': staff_profile,
            'user': request.user,
            'total_blotters': total_blotters,
            'pending': pending,
            'scheduled': scheduled,
            'resolved': resolved,
            'unsettled': unsettled,
            'pending_approvals_count': pending_approvals_count,  # NEW
            'today_hearings': today_hearings,
            'recent_blotters': recent_blotters,
        }
        return render(request, 'staff_module/dashboard.html', context)
    except Staff.DoesNotExist:
        messages.error(request, 'Access denied. Staff only area.')
        return redirect('dashboard')
@login_required(login_url='login')
def pending_approvals(request):
    """View all blotters pending staff approval"""
    try:
        staff_profile = request.user.staff_profile
        
        pending_blotters = Blotter.objects.filter(is_approved=False, status='pending').order_by('-created_at')
        
        # Search functionality
        search_query = request.GET.get('search', '')
        if search_query:
            pending_blotters = pending_blotters.filter(
                Q(blotter_number__icontains=search_query) |
                Q(complainant_name__icontains=search_query) |
                Q(respondent_name__icontains=search_query)
            )
        
        paginator = Paginator(pending_blotters, 20)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        context = {
            'staff': staff_profile,
            'blotters': page_obj,
            'search_query': search_query,
            'total_pending': pending_blotters.count(),
            'user': request.user,
        }
        return render(request, 'staff_module/pending_approvals.html', context)
    except Staff.DoesNotExist:
        messages.error(request, 'Access denied. Staff only area.')
        return redirect('dashboard')

# ====================== BLOTTER MANAGEMENT ======================
@login_required(login_url='login')
def staff_blotter_list(request):
    """View all blotters with advanced filters"""
    try:
        staff_profile = request.user.staff_profile
        blotters = Blotter.objects.all().order_by('-created_at')
        
        # Search
        search_query = request.GET.get('search', '')
        if search_query:
            blotters = blotters.filter(
                Q(blotter_number__icontains=search_query) |
                Q(complainant_name__icontains=search_query) |
                Q(respondent_name__icontains=search_query) |
                Q(complainant_phone__icontains=search_query)
            )
        
        # Status filter
        status_filter = request.GET.get('status', '')
        if status_filter:
            blotters = blotters.filter(status=status_filter)
        
        # Incident type filter
        incident_type_filter = request.GET.get('incident_type', '')
        if incident_type_filter:
            blotters = blotters.filter(incident_type=incident_type_filter)
        
        # Date range filter
        date_from = request.GET.get('date_from', '')
        date_to = request.GET.get('date_to', '')
        if date_from:
            blotters = blotters.filter(created_at__date__gte=date_from)
        if date_to:
            blotters = blotters.filter(created_at__date__lte=date_to)
        
        # Verification method filter
        verification_filter = request.GET.get('verification_method', '')
        if verification_filter:
            blotters = blotters.filter(verification_method=verification_filter)
        
        # Sorting
        sort_by = request.GET.get('sort', '-created_at')
        allowed_sorts = ['created_at', '-created_at', 'blotter_number', '-blotter_number', 'status', '-status', 'incident_date', '-incident_date']
        if sort_by in allowed_sorts:
            blotters = blotters.order_by(sort_by)
        else:
            blotters = blotters.order_by('-created_at')
        
        # Pagination
        paginator = Paginator(blotters, 20)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        context = {
            'staff': staff_profile,
            'blotters': page_obj,
            'search_query': search_query,
            'status_filter': status_filter,
            'incident_type_filter': incident_type_filter,
            'date_from': date_from,
            'date_to': date_to,
            'verification_filter': verification_filter,
            'sort_by': sort_by,
            'status_choices': Blotter.STATUS_CHOICES,
            'incident_choices': Blotter.INCIDENT_CHOICES,
            'total_count': blotters.count(),
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
        schedules = blotter.schedules.all()
        evidences = blotter.evidences.all()
        
        context = {
            'staff': staff_profile,
            'blotter': blotter,
            'schedules': schedules,
            'evidences': evidences,
            'user': request.user,
        }
        return render(request, 'staff_module/blotter_detail.html', context)
    except Staff.DoesNotExist:
        messages.error(request, 'Access denied. Staff only area.')
        return redirect('dashboard')


@login_required(login_url='login')
def staff_schedule_hearing(request, blotter_id):
    """Schedule a hearing for a blotter"""
    try:
        staff_profile = request.user.staff_profile
        blotter = get_object_or_404(Blotter, id=blotter_id)

        if request.method == 'POST':
            hearing_type = request.POST.get('hearing_type')
            hearing_date = request.POST.get('hearing_date')
            location = request.POST.get('location')
            notes = request.POST.get('notes', '')

            Schedule.objects.create(
                blotter=blotter,
                hearing_type=hearing_type,
                hearing_date=hearing_date,
                location=location,
                notes=notes,
                created_by=request.user,
                outcome='pending'
            )

            blotter.status = 'scheduled'
            blotter.hearing_date = hearing_date
            blotter.save()

            messages.success(request, f'Hearing scheduled successfully for {blotter.blotter_number}!')
            return redirect('staff_module:staff_blotter_detail', blotter_id=blotter.id)
        else:
            form = ScheduleForm()

        context = {
            'staff': staff_profile,
            'blotter': blotter,
            'form': form,
            'user': request.user,
        }
        return render(request, 'staff_module/schedule_hearing.html', context)
    except Staff.DoesNotExist:
        messages.error(request, 'Access denied. Staff only area.')
        return redirect('dashboard')


@login_required(login_url='login')
def staff_update_status(request, blotter_id):
    """Update blotter status"""
    try:
        staff_profile = request.user.staff_profile
        blotter = get_object_or_404(Blotter, id=blotter_id)
        old_status = blotter.status
        
        if request.method == 'POST':
            new_status = request.POST.get('status')
            reason = request.POST.get('reason', '')
            
            blotter.status = new_status
            if new_status == 'resolved':
                blotter.resolution_notes = reason
            blotter.save()
            
            messages.success(request, f'Status updated to {new_status}')
            return redirect('staff_module:staff_blotter_detail', blotter_id=blotter.id)
        
        context = {
            'staff': staff_profile,
            'blotter': blotter,
            'status_choices': Blotter.STATUS_CHOICES,
            'user': request.user,
        }
        return render(request, 'staff_module/update_status.html', context)
    except Staff.DoesNotExist:
        messages.error(request, 'Access denied. Staff only area.')
        return redirect('dashboard')


@login_required(login_url='login')
def staff_upload_evidence(request, blotter_id):
    """Upload evidence for a blotter"""
    try:
        staff_profile = request.user.staff_profile
        blotter = get_object_or_404(Blotter, id=blotter_id)
        
        if request.method == 'POST':
            form = EvidenceForm(request.POST, request.FILES)
            if form.is_valid():
                evidence = form.save(commit=False)
                evidence.blotter = blotter
                evidence.uploaded_by = request.user
                evidence.save()
                
                messages.success(request, 'Evidence uploaded successfully!')
                return redirect('staff_module:staff_blotter_detail', blotter_id=blotter.id)
        else:
            form = EvidenceForm()
        
        context = {
            'staff': staff_profile,
            'blotter': blotter,
            'form': form,
            'user': request.user,
        }
        return render(request, 'staff_module/upload_evidence.html', context)
    except Staff.DoesNotExist:
        messages.error(request, 'Access denied. Staff only area.')
        return redirect('dashboard')


# ====================== STAFF MANAGEMENT (ADMIN ONLY) ======================
@login_required(login_url='login')
def staff_list(request):
    """View all staff members (admin only)"""
    try:
        if request.user.staff_profile.role != 'admin':
            messages.error(request, 'Admin access required')
            return redirect('staff_module:staff_dashboard')
        
        staff_members = Staff.objects.all().select_related('user')
        
        context = {
            'staff_members': staff_members,
            'staff': request.user.staff_profile,
            'user': request.user,
        }
        return render(request, 'staff_module/staff_list.html', context)
    except Staff.DoesNotExist:
        messages.error(request, 'Access denied. Staff only area.')
        return redirect('dashboard')


@login_required(login_url='login')
def staff_create(request):
    """Create new staff member (admin only)"""
    try:
        if request.user.staff_profile.role != 'admin':
            messages.error(request, 'Admin access required')
            return redirect('staff_module:staff_dashboard')
        
        if request.method == 'POST':
            username = request.POST.get('username')
            email = request.POST.get('email')
            password = request.POST.get('password')
            role = request.POST.get('role')
            position = request.POST.get('position')
            contact_number = request.POST.get('contact_number')
            first_name = request.POST.get('first_name', '')
            last_name = request.POST.get('last_name', '')
            
            # Check if username exists
            if User.objects.filter(username=username).exists():
                messages.error(request, 'Username already exists')
                return redirect('staff_module:staff_create')
            
            # Create user
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )
            
            # Update staff profile (created by signal)
            user.staff_profile.role = role
            user.staff_profile.position = position
            user.staff_profile.contact_number = contact_number
            user.staff_profile.save()
            
            messages.success(request, f'Staff {username} created successfully!')
            return redirect('staff_module:staff_list')
        
        context = {
            'staff': request.user.staff_profile,
            'user': request.user,
            'role_choices': Staff.ROLE_CHOICES,
        }
        return render(request, 'staff_module/staff_create.html', context)
    except Staff.DoesNotExist:
        messages.error(request, 'Access denied. Staff only area.')
        return redirect('dashboard')


@login_required(login_url='login')
def staff_edit(request, staff_id):
    """Edit staff member (admin only)"""
    try:
        if request.user.staff_profile.role != 'admin':
            messages.error(request, 'Admin access required')
            return redirect('staff_module:staff_dashboard')
        
        staff = get_object_or_404(Staff, id=staff_id)
        
        if request.method == 'POST':
            staff.role = request.POST.get('role')
            staff.position = request.POST.get('position')
            staff.contact_number = request.POST.get('contact_number')
            staff.address = request.POST.get('address', '')
            staff.is_active = request.POST.get('is_active') == 'on'
            staff.save()
            
            # Update user info
            staff.user.first_name = request.POST.get('first_name', '')
            staff.user.last_name = request.POST.get('last_name', '')
            staff.user.email = request.POST.get('email', '')
            staff.user.save()
            
            messages.success(request, f'Staff {staff.user.username} updated successfully!')
            return redirect('staff_module:staff_list')
        
        context = {
            'staff': staff,
            'user_staff': request.user.staff_profile,
            'user': request.user,
            'role_choices': Staff.ROLE_CHOICES,
        }
        return render(request, 'staff_module/staff_edit.html', context)
    except Staff.DoesNotExist:
        messages.error(request, 'Access denied. Staff only area.')
        return redirect('dashboard')


@login_required(login_url='login')
def staff_delete(request, staff_id):
    """Delete staff member (admin only)"""
    try:
        if request.user.staff_profile.role != 'admin':
            messages.error(request, 'Admin access required')
            return redirect('staff_module:staff_dashboard')
        
        staff = get_object_or_404(Staff, id=staff_id)
        
        # Prevent deleting yourself
        if staff.user.id == request.user.id:
            messages.error(request, 'You cannot delete your own account!')
            return redirect('staff_module:staff_list')
        
        if request.method == 'POST':
            username = staff.user.username
            staff.user.delete()  # Staff profile will be deleted due to CASCADE
            messages.success(request, f'Staff {username} has been deleted successfully!')
            return redirect('staff_module:staff_list')
        
        context = {
            'staff': staff,
            'user_staff': request.user.staff_profile,
            'user': request.user,
        }
        return render(request, 'staff_module/staff_confirm_delete.html', context)
    except Staff.DoesNotExist:
        messages.error(request, 'Access denied. Staff only area.')
        return redirect('dashboard')



@login_required(login_url='login')
def staff_generate_summon(request, blotter_id):
    """Generate summon letter for respondent"""
    try:
        staff_profile = request.user.staff_profile
        blotter = get_object_or_404(Blotter, id=blotter_id)
        
        # Check if hearing is scheduled
        latest_schedule = blotter.schedules.filter(is_completed=False).order_by('-hearing_date').first()
        
        if not latest_schedule:
            messages.error(request, f'Cannot generate summon letter. Please schedule a hearing first for Blotter #{blotter.blotter_number}.')
            return redirect('staff_module:staff_blotter_detail', blotter_id=blotter.id)
        
        # Use the schedule date instead of blotter.hearing_date
        hearing_date = latest_schedule.hearing_date
        
        context = {
            'blotter': blotter,
            'staff': staff_profile,
            'today': timezone.now(),
            'hearing_date': hearing_date,
            'schedule': latest_schedule,
        }
        
        return render(request, 'staff_module/summon_letter.html', context)
        
    except Staff.DoesNotExist:
        messages.error(request, 'Access denied. Staff only area.')
        return redirect('dashboard')


@login_required(login_url='login')
def staff_schedule_hearing(request, blotter_id):
    """Schedule a hearing for a blotter"""
    try:
        staff_profile = request.user.staff_profile
        blotter = get_object_or_404(Blotter, id=blotter_id)
        
        if request.method == 'POST':
            hearing_type = request.POST.get('hearing_type')
            hearing_date = request.POST.get('hearing_date')
            location = request.POST.get('location')
            notes = request.POST.get('notes', '')
            
            # Create schedule
            schedule = Schedule.objects.create(
                blotter=blotter,
                hearing_type=hearing_type,
                hearing_date=hearing_date,
                location=location,
                notes=notes,
                created_by=request.user,
                outcome='pending'
            )
            
            # Update blotter status and hearing_date
            blotter.status = 'scheduled'
            blotter.hearing_date = hearing_date
            blotter.save()
            
            messages.success(request, f'Hearing scheduled successfully for {blotter.blotter_number}!')
            return redirect('staff_module:staff_blotter_detail', blotter_id=blotter.id)
        else:
            form = ScheduleForm()
        
        context = {
            'staff': staff_profile,
            'blotter': blotter,
            'form': form,
            'user': request.user,
        }
        return render(request, 'staff_module/schedule_hearing.html', context)
    except Staff.DoesNotExist:
        messages.error(request, 'Access denied. Staff only area.')
        return redirect('dashboard')

@login_required(login_url='login')
def staff_update_hearing_status(request, hearing_id):
    """Update hearing/mediation session status"""
    try:
        staff_profile = request.user.staff_profile
        hearing = get_object_or_404(Schedule, id=hearing_id)
        blotter = hearing.blotter
        
        if request.method == 'POST':
            attendance = request.POST.get('attendance')
            outcome = request.POST.get('outcome')
            outcome_notes = request.POST.get('outcome_notes', '')
            
            # Update hearing record
            hearing.attendance = attendance
            hearing.outcome = outcome
            hearing.outcome_notes = outcome_notes
            hearing.is_completed = outcome in ['completed', 'settled', 'unsettled']
            hearing.save()
            
            # Update blotter status based on hearing outcome
            if outcome == 'settled':
                blotter.status = 'resolved'
                blotter.resolution_notes = outcome_notes
            elif outcome == 'unsettled':
                blotter.status = 'unsettled'
            elif outcome == 'failed_complainant' or outcome == 'failed_respondent':
                blotter.status = 'dismissed'
            else:
                blotter.status = 'in_progress'
            
            blotter.save()
            
            # Create audit log
            BlotterAuditLog.objects.create(
                blotter=blotter,
                action='status_change',
                old_value=hearing.get_outcome_display(),
                new_value=outcome,
                performed_by=request.user
            )
            
            messages.success(request, f'Hearing status updated successfully!')
            return redirect('staff_module:staff_blotter_detail', blotter_id=blotter.id)
        
        context = {
            'staff': staff_profile,
            'hearing': hearing,
            'blotter': blotter,
            'user': request.user,
            'attendance_choices': Schedule.ATTENDANCE_CHOICES,
            'outcome_choices': Schedule.OUTCOME_CHOICES,
        }
        return render(request, 'staff_module/update_hearing_status.html', context)
        
    except Staff.DoesNotExist:
        messages.error(request, 'Access denied. Staff only area.')
        return redirect('dashboard')

@login_required(login_url='login')
def staff_pending_approvals(request):
    """View all blotters pending staff approval"""
    try:
        staff_profile = request.user.staff_profile

        pending_blotters = Blotter.objects.filter(is_approved=False).order_by('-created_at')

        search_query = request.GET.get('search', '').strip()
        if search_query:
            pending_blotters = pending_blotters.filter(
                Q(blotter_number__icontains=search_query) |
                Q(complainant_name__icontains=search_query) |
                Q(respondent_name__icontains=search_query)
            )

        total_pending = pending_blotters.count()  # count BEFORE pagination

        paginator = Paginator(pending_blotters, 20)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        context = {
            'staff': staff_profile,
            'blotters': page_obj,
            'search_query': search_query,
            'total_pending': total_pending,
            'user': request.user,
        }
        return render(request, 'staff_module/pending_approvals.html', context)
    except Staff.DoesNotExist:
        messages.error(request, 'Access denied. Staff only area.')
        return redirect('dashboard')

@login_required(login_url='login')
def staff_approve_blotter(request, blotter_id):
    """Approve a blotter complaint"""
    try:
        staff_profile = request.user.staff_profile
        blotter = get_object_or_404(Blotter, id=blotter_id)
        
        if request.method == 'POST':
            action = request.POST.get('action')
            
            if action == 'approve':
                blotter.is_approved = True
                blotter.approved_by = request.user
                blotter.approved_at = timezone.now()
                blotter.verification_status = 'approved'
                messages.success(request, f'Blotter {blotter.blotter_number} has been approved.')
                
            elif action == 'reject':
                rejection_reason = request.POST.get('rejection_reason', '')
                blotter.is_approved = False
                blotter.rejection_reason = rejection_reason
                blotter.status = 'dismissed'
                messages.warning(request, f'Blotter {blotter.blotter_number} has been rejected.')
            
            blotter.reviewed_by = request.user
            blotter.reviewed_at = timezone.now()
            blotter.save()
            
            return redirect('staff_module:staff_pending_approvals')
        
        context = {
            'staff': staff_profile,
            'blotter': blotter,
            'user': request.user,
        }
        return render(request, 'staff_module/approve_blotter.html', context)
    except Staff.DoesNotExist:
        messages.error(request, 'Access denied. Staff only area.')
        return redirect('dashboard')