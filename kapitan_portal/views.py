from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q, Count
from django.core.paginator import Paginator
from Blotter_Module.models import Blotter, Schedule
from certificates.models import CertificateRequest
from staff_module.models import Staff, AuditLog, Appointment  # Add Appointment import
from staff_module.decorators import role_required
from certificates.notification_utils import send_claim_notification, send_rejection_notification

@login_required(login_url='login')
def kapitan_dashboard(request):
    """Kapitan Dashboard - shows hearing schedules, appointments, and pending approvals"""
    try:
        staff_profile = request.user.staff_profile
        
        # Verify user is Kapitan
        if staff_profile.role != 'kapitan':
            messages.error(request, 'Access denied. Kapitan only area.')
            return redirect('staff_module:staff_dashboard')
        
        # Hearing statistics
        total_hearings = Schedule.objects.count()
        pending_hearings = Schedule.objects.filter(is_completed=False, hearing_date__gt=timezone.now()).count()
        completed_hearings = Schedule.objects.filter(is_completed=True).count()
        
        # Today's hearings
        today_hearings = Schedule.objects.filter(
            hearing_date__date=timezone.now().date(),
            is_completed=False
        ).select_related('blotter')
        
        # Upcoming hearings
        upcoming_hearings = Schedule.objects.filter(
            hearing_date__gt=timezone.now(),
            is_completed=False
        ).select_related('blotter').order_by('hearing_date')[:10]
        
        # Past hearings
        past_hearings = Schedule.objects.filter(
            hearing_date__lt=timezone.now(),
            is_completed=True
        ).select_related('blotter').order_by('-hearing_date')[:10]
        
        # ===== FIXED: Appointment statistics for Kapitan =====
        # Show ALL pending appointments (both blotter_hearing AND kapitan types)
        pending_appointments = Appointment.objects.filter(
            status='pending'  # Removed appointment_type filter to show all pending appointments
        ).order_by('appointment_date')[:10]
        
        pending_appointments_count = Appointment.objects.filter(
            status='pending'  # Removed appointment_type filter
        ).count()
        
        # Upcoming appointments (approved) - show all types
        upcoming_appointments = Appointment.objects.filter(
            status='approved',
            appointment_date__gte=timezone.now()
        ).order_by('appointment_date')[:10]
        
        # Certificate statistics
        total_certificates = CertificateRequest.objects.count()
        pending_certificates = CertificateRequest.objects.filter(status='for_approval').count()
        approved_certificates = CertificateRequest.objects.filter(status='approved').count()
        released_certificates = CertificateRequest.objects.filter(status='released').count()
        pending_cert_requests = CertificateRequest.objects.filter(status='for_approval').order_by('-date_submitted')[:10]
    
        # Pending certificate requests awaiting Kapitan approval
        pending_cert_requests = CertificateRequest.objects.filter(status='for_approval').order_by('-date_submitted')[:10]
        
        context = {
            'staff': staff_profile,
            'user': request.user,
            # Hearing data
            'total_hearings': total_hearings,
            'pending_hearings': pending_hearings,
            'completed_hearings': completed_hearings,
            'today_hearings': today_hearings,
            'upcoming_hearings': upcoming_hearings,
            'past_hearings': past_hearings,
            # Appointment data - FIXED
            'pending_appointments': pending_appointments,
            'pending_appointments_count': pending_appointments_count,
            'upcoming_appointments': upcoming_appointments,
            # Certificate data
            'total_certificates': total_certificates,
            'pending_certificates': pending_certificates,
            'approved_certificates': approved_certificates,
            'released_certificates': released_certificates,
            'pending_cert_requests': pending_cert_requests,
        }
        return render(request, 'kapitan_portal/dashboard.html', context)
        
    except Staff.DoesNotExist:
        messages.error(request, 'Access denied. Staff only area.')
        return redirect('dashboard')

# ====================== APPOINTMENT MANAGEMENT (NEW) ======================

@login_required
@role_required(['kapitan', 'admin'])
def appointment_list(request):
    """Kapitan view: List all appointments"""
    try:
        staff_profile = request.user.staff_profile
        if staff_profile.role != 'kapitan' and not request.user.is_superuser:
            messages.error(request, 'Access denied. Kapitan only area.')
            return redirect('staff_module:staff_dashboard')
        
        appointments = Appointment.objects.all().order_by('-appointment_date')
        
        # Get pending count for the badge
        pending_count = Appointment.objects.filter(status='pending').count()
        
        # Filter by status
        status_filter = request.GET.get('status', '')
        if status_filter:
            appointments = appointments.filter(status=status_filter)
        
        # Filter by type (optional)
        type_filter = request.GET.get('type', '')
        if type_filter:
            appointments = appointments.filter(appointment_type=type_filter)
        
        # Search
        search_query = request.GET.get('search', '')
        if search_query:
            appointments = appointments.filter(
                Q(reference_number__icontains=search_query) |
                Q(resident_name__icontains=search_query) |
                Q(blotter__blotter_number__icontains=search_query)
            )
        
        paginator = Paginator(appointments, 20)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        context = {
            'appointments': page_obj,
            'search_query': search_query,
            'status_filter': status_filter,
            'type_filter': type_filter,
            'pending_count': pending_count,  # Add this line
            'staff': staff_profile,
            'user': request.user,
        }
        return render(request, 'kapitan_portal/appointment_list.html', context)
        
    except Staff.DoesNotExist:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')


@login_required
@role_required(['kapitan', 'admin'])
def appointment_detail(request, appt_id):
    """Kapitan view: View appointment details"""
    try:
        staff_profile = request.user.staff_profile
        if staff_profile.role != 'kapitan' and not request.user.is_superuser:
            messages.error(request, 'Access denied. Kapitan only area.')
            return redirect('staff_module:staff_dashboard')
        
        appointment = get_object_or_404(Appointment, id=appt_id)
        
        context = {
            'appointment': appointment,
            'staff': staff_profile,
            'user': request.user,
        }
        return render(request, 'kapitan_portal/appointment_detail.html', context)
        
    except Staff.DoesNotExist:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')


@login_required
@role_required(['kapitan', 'admin'])
def appointment_approve(request, appt_id):
    """Kapitan approves an appointment"""
    try:
        staff_profile = request.user.staff_profile
        if staff_profile.role != 'kapitan' and not request.user.is_superuser:
            messages.error(request, 'Access denied. Kapitan only area.')
            return redirect('staff_module:staff_dashboard')
        
        appointment = get_object_or_404(Appointment, id=appt_id)
        
        if appointment.status != 'pending':
            messages.error(request, 'This appointment is not pending approval.')
            return redirect('kapitan_portal:appointment_list')
        
        if request.method == 'POST':
            appointment.status = 'approved'
            appointment.approved_by = request.user
            appointment.approved_at = timezone.now()
            appointment.notes = request.POST.get('notes', appointment.notes or '')
            appointment.save()
            
            # If this is a blotter hearing, update the blotter schedule
            if appointment.appointment_type == 'blotter_hearing' and appointment.blotter:
                # Update the schedule with approved status
                schedule = appointment.blotter.schedules.filter(hearing_date=appointment.appointment_date).first()
                if schedule:
                    schedule.notes = f"Approved by Kapitan. {schedule.notes or ''}"
                    schedule.save()
            
            messages.success(request, f'Appointment {appointment.reference_number} has been approved.')
            return redirect('kapitan_portal:appointment_list')
        
        context = {
            'appointment': appointment,
            'staff': staff_profile,
            'user': request.user,
        }
        return render(request, 'kapitan_portal/appointment_approve.html', context)
        
    except Staff.DoesNotExist:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')


@login_required
@role_required(['kapitan', 'admin'])
def appointment_reject(request, appt_id):
    """Kapitan rejects an appointment"""
    try:
        staff_profile = request.user.staff_profile
        if staff_profile.role != 'kapitan' and not request.user.is_superuser:
            messages.error(request, 'Access denied. Kapitan only area.')
            return redirect('staff_module:staff_dashboard')
        
        appointment = get_object_or_404(Appointment, id=appt_id)
        
        if appointment.status != 'pending':
            messages.error(request, 'This appointment is not pending approval.')
            return redirect('kapitan_portal:appointment_list')
        
        if request.method == 'POST':
            rejection_reason = request.POST.get('rejection_reason', '')
            appointment.status = 'rejected'  # Change from 'cancelled' to 'rejected'
            appointment.notes = f"Rejected: {rejection_reason}"
            appointment.save()
            
            messages.warning(request, f'Appointment {appointment.reference_number} has been rejected.')
            return redirect('kapitan_portal:appointment_list')
        
        context = {
            'appointment': appointment,
            'staff': staff_profile,
            'user': request.user,
        }
        return render(request, 'kapitan_portal/appointment_reject.html', context)
        
    except Staff.DoesNotExist:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')

@login_required
@role_required(['kapitan', 'admin'])
def for_approval_appointments(request):
    """Kapitan view: List appointments pending approval"""
    try:
        staff_profile = request.user.staff_profile
        if staff_profile.role != 'kapitan' and not request.user.is_superuser:
            messages.error(request, 'Access denied. Kapitan only area.')
            return redirect('staff_module:staff_dashboard')
        
        # FIX: Include BOTH blotter_hearing AND kapitan appointment types
        pending_appointments = Appointment.objects.filter(
            status='pending'
        ).order_by('appointment_date')  # Remove the appointment_type filter
        
        # Search functionality
        search_query = request.GET.get('search', '')
        if search_query:
            pending_appointments = pending_appointments.filter(
                Q(reference_number__icontains=search_query) |
                Q(resident_name__icontains=search_query) |
                Q(blotter__blotter_number__icontains=search_query)
            )
        
        paginator = Paginator(pending_appointments, 20)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        context = {
            'appointments': page_obj,
            'search_query': search_query,
            'total_count': pending_appointments.count(),
            'staff': staff_profile,
            'user': request.user,
        }
        return render(request, 'kapitan_portal/for_approval_appointments.html', context)
        
    except Staff.DoesNotExist:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')


# ====================== EXISTING HEARING VIEWS ======================

@login_required
def hearing_detail(request, hearing_id):
    """View details of a specific hearing appointment"""
    try:
        staff_profile = request.user.staff_profile
        if staff_profile.role != 'kapitan':
            messages.error(request, 'Access denied.')
            return redirect('staff_module:staff_dashboard')
        
        hearing = get_object_or_404(Schedule, id=hearing_id)
        
        context = {
            'hearing': hearing,
            'blotter': hearing.blotter,
            'staff': staff_profile,
            'user': request.user,
        }
        return render(request, 'kapitan_portal/hearing_detail.html', context)
        
    except Staff.DoesNotExist:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')


@login_required
def certificate_list(request):
    """Kapitan view: View certificate requests that need Kapitan approval"""
    try:
        staff_profile = request.user.staff_profile
        if staff_profile.role != 'kapitan':
            messages.error(request, 'Access denied.')
            return redirect('staff_module:staff_dashboard')
        
        # Only show certificates that are 'for_approval' (sent by staff for Kapitan approval)
        certificates = CertificateRequest.objects.filter(status='for_approval').order_by('-date_submitted')
        
        # Search
        search_query = request.GET.get('search', '')
        if search_query:
            certificates = certificates.filter(
                Q(request_id__icontains=search_query) |
                Q(full_name__icontains=search_query)
            )
        
        paginator = Paginator(certificates, 20)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        context = {
            'certificates': page_obj,
            'search_query': search_query,
            'staff': staff_profile,
            'user': request.user,
        }
        return render(request, 'kapitan_portal/certificate_list.html', context)
        
    except Staff.DoesNotExist:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')


@login_required
def certificate_detail(request, cert_id):
    """View certificate details for Kapitan approval"""
    try:
        staff_profile = request.user.staff_profile
        if staff_profile.role != 'kapitan':
            messages.error(request, 'Access denied.')
            return redirect('staff_module:staff_dashboard')
        
        certificate = get_object_or_404(CertificateRequest, id=cert_id)
        
        context = {
            'certificate': certificate,
            'staff': staff_profile,
            'user': request.user,
        }
        return render(request, 'kapitan_portal/certificate_detail.html', context)
        
    except Staff.DoesNotExist:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')


@login_required
@role_required(['kapitan', 'admin'])
def certificate_approve(request, cert_id):
    """Kapitan approves a certificate request"""
    try:
        staff_profile = request.user.staff_profile
        if staff_profile.role != 'kapitan' and not request.user.is_superuser:
            messages.error(request, 'Access denied. Kapitan only area.')
            return redirect('staff_module:staff_dashboard')
        
        certificate = get_object_or_404(CertificateRequest, id=cert_id)
        
        if certificate.status != 'for_approval':
            messages.error(request, 'This request is not pending approval.')
            return redirect('kapitan_portal:for_approval_list')
        
        if request.method == 'POST':
            certificate.status = 'approved'
            certificate.date_approved = timezone.now()
            certificate.approved_by = request.user.username
            certificate.remarks = request.POST.get('remarks', '')
            certificate.save()
            
            messages.success(request, f'Certificate {certificate.request_id} has been approved.')
            return redirect('kapitan_portal:for_approval_list')
        
        context = {
            'certificate': certificate,
            'staff': staff_profile,
            'user': request.user,
        }
        return render(request, 'kapitan_portal/approve_certificate.html', context)
        
    except Staff.DoesNotExist:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')


@login_required
@role_required(['kapitan', 'admin'])
def certificate_reject(request, cert_id):
    """Kapitan rejects a certificate request"""
    try:
        staff_profile = request.user.staff_profile
        if staff_profile.role != 'kapitan' and not request.user.is_superuser:
            messages.error(request, 'Access denied. Kapitan only area.')
            return redirect('staff_module:staff_dashboard')
        
        certificate = get_object_or_404(CertificateRequest, id=cert_id)
        
        if certificate.status != 'for_approval':
            messages.error(request, f'Cannot reject request with status: {certificate.get_status_display()}')
            return redirect('kapitan_portal:certificate_list')
        
        if request.method == 'POST':
            rejection_reason = request.POST.get('rejection_reason', '')
            certificate.status = 'rejected'
            certificate.rejection_reason = rejection_reason
            certificate.remarks = rejection_reason
            certificate.save()
            
            messages.warning(request, f'Certificate {certificate.request_id} has been rejected.')
            return redirect('kapitan_portal:certificate_list')
        
        context = {
            'certificate': certificate,
            'staff': staff_profile,
            'user': request.user,
        }
        return render(request, 'kapitan_portal/certificate_reject.html', context)
        
    except Staff.DoesNotExist:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')


@login_required
def hearing_list(request):
    """View all hearings for Kapitan"""
    try:
        staff_profile = request.user.staff_profile
        if staff_profile.role != 'kapitan':
            messages.error(request, 'Access denied.')
            return redirect('staff_module:staff_dashboard')
        
        hearings = Schedule.objects.all().select_related('blotter').order_by('-hearing_date')
        
        # Filter by status
        status_filter = request.GET.get('status', '')
        if status_filter:
            hearings = hearings.filter(outcome=status_filter)
        
        # Search
        search_query = request.GET.get('search', '')
        if search_query:
            hearings = hearings.filter(
                Q(blotter__blotter_number__icontains=search_query) |
                Q(blotter__complainant_name__icontains=search_query) |
                Q(blotter__respondent_name__icontains=search_query)
            )
        
        paginator = Paginator(hearings, 20)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        context = {
            'hearings': page_obj,
            'search_query': search_query,
            'status_filter': status_filter,
            'staff': staff_profile,
            'user': request.user,
        }
        return render(request, 'kapitan_portal/hearing_list.html', context)
        
    except Staff.DoesNotExist:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')


@login_required
@role_required(['kapitan', 'admin'])
def for_approval_list(request):
    """Kapitan view: List certificate requests pending approval"""
    try:
        staff_profile = request.user.staff_profile
        if staff_profile.role != 'kapitan' and not request.user.is_superuser:
            messages.error(request, 'Access denied. Kapitan only area.')
            return redirect('staff_module:staff_dashboard')
        
        pending_requests = CertificateRequest.objects.filter(status='for_approval').order_by('-date_submitted')
        
        # Search functionality
        search_query = request.GET.get('search', '')
        if search_query:
            pending_requests = pending_requests.filter(
                Q(request_id__icontains=search_query) |
                Q(full_name__icontains=search_query)
            )
        
        paginator = Paginator(pending_requests, 20)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        context = {
            'requests': page_obj,
            'search_query': search_query,
            'total_count': pending_requests.count(),
            'staff': staff_profile,
            'user': request.user,
        }
        return render(request, 'kapitan_portal/for_approval_list.html', context)
        
    except Staff.DoesNotExist:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    

@login_required
@role_required(['kapitan', 'admin'])
def certificate_approve(request, cert_id):
    """Kapitan approves a certificate request and sends email notification"""
    try:
        staff_profile = request.user.staff_profile
        if staff_profile.role != 'kapitan' and not request.user.is_superuser:
            messages.error(request, 'Access denied. Kapitan only area.')
            return redirect('staff_module:staff_dashboard')
        
        certificate = get_object_or_404(CertificateRequest, id=cert_id)
        
        if certificate.status != 'for_approval':
            messages.error(request, 'This request is not pending approval.')
            return redirect('kapitan_portal:for_approval_list')
        
        if request.method == 'POST':
            certificate.status = 'approved'
            certificate.date_approved = timezone.now()
            certificate.approved_by = request.user.username
            certificate.remarks = request.POST.get('remarks', '')
            
            # Set claim deadline (7 days from approval)
            certificate.claim_deadline = timezone.now() + timezone.timedelta(days=7)
            certificate.save()
            
            # Send email notification to resident
            email_sent = send_claim_notification(certificate)
            
            # Show appropriate message
            if email_sent:
                messages.success(request, f'Certificate {certificate.request_id} has been approved. Notification sent to {certificate.email}')
            else:
                if certificate.email:
                    messages.warning(request, f'Certificate {certificate.request_id} approved but failed to send email notification.')
                else:
                    messages.warning(request, f'Certificate {certificate.request_id} approved. No email provided for notification.')
            
            return redirect('kapitan_portal:certificate_list')
        
        context = {
            'certificate': certificate,
            'staff': staff_profile,
            'user': request.user,
        }
        return render(request, 'kapitan_portal/approve_certificate.html', context)
        
    except Staff.DoesNotExist:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')


@login_required
@role_required(['kapitan', 'admin'])
def certificate_reject(request, cert_id):
    """Kapitan rejects a certificate request and sends email notification"""
    try:
        staff_profile = request.user.staff_profile
        if staff_profile.role != 'kapitan' and not request.user.is_superuser:
            messages.error(request, 'Access denied. Kapitan only area.')
            return redirect('staff_module:staff_dashboard')
        
        certificate = get_object_or_404(CertificateRequest, id=cert_id)
        
        if certificate.status != 'for_approval':
            messages.error(request, f'Cannot reject request with status: {certificate.get_status_display()}')
            return redirect('kapitan_portal:certificate_list')
        
        if request.method == 'POST':
            rejection_reason = request.POST.get('rejection_reason', '')
            certificate.status = 'rejected'
            certificate.rejection_reason = rejection_reason
            certificate.remarks = rejection_reason
            certificate.save()
            
            # Send rejection email notification
            send_rejection_notification(certificate)
            
            if certificate.email:
                messages.warning(request, f'Certificate {certificate.request_id} has been rejected. Notification sent to {certificate.email}')
            else:
                messages.warning(request, f'Certificate {certificate.request_id} rejected. No email provided for notification.')
            
            return redirect('kapitan_portal:certificate_list')
        
        context = {
            'certificate': certificate,
            'staff': staff_profile,
            'user': request.user,
        }
        return render(request, 'kapitan_portal/certificate_reject.html', context)
        
    except Staff.DoesNotExist:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')