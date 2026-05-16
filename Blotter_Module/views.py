from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from .forms import PublicBlotterForm, ScheduleForm, EvidenceForm, CommentForm, BlotterStatusForm, EmailVerificationForm, VerifyOTPForm
from .models import Blotter, Schedule, Evidence, BlotterAuditLog, Notification, BlotterComment
import random
import datetime
from django.core.mail import send_mail
from django.conf import settings
import json

# ====================== HELPER FUNCTIONS ======================
def get_client_ip(request):
    """Get client IP address"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def send_verification_email(email, otp_code):
    """Send OTP verification email"""
    subject = 'Barangay Poblacion - Verify Your Email Address'
    message = f"""
Republic of the Philippines
Barangay Poblacion, Santa Catalina, Negros Oriental

EMAIL VERIFICATION

Your OTP (One-Time Password) code is: {otp_code}

This code will expire in 10 minutes.

If you did not request this verification, please ignore this email.

This is an automated message. Please do not reply.
"""
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email], fail_silently=False)

# ====================== EMAIL VERIFICATION VIEWS ======================
def blotter_verify_email(request):
    """Step 1: Enter email for verification"""
    if 'email_verified' in request.session:
        del request.session['email_verified']
    
    if request.method == 'POST':
        form = EmailVerificationForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            request.session['pending_complaint_email'] = email
            otp_code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
            request.session['email_otp'] = otp_code
            request.session['otp_created_at'] = datetime.datetime.now().isoformat()
            
            try:
                # Send email using configured settings
                subject = '🔐 BIMS - Email Verification Code'
                message = f"""
═══════════════════════════════════════════════════════════
              BARANGAY SANTA CATALINA - BIMS
                    EMAIL VERIFICATION
═══════════════════════════════════════════════════════════

Dear Resident,

Your verification code for the Barangay Integrated Management System (BIMS) is:

                    🔐 {otp_code} 🔐

This code will expire in 10 minutes.

If you did not request this verification, please ignore this email.

For concerns, please contact the Barangay Hall.

Thank you,
Barangay Santa Catalina Administration
═══════════════════════════════════════════════════════════
This is an automated message. Please do not reply.
"""
                from_email = settings.EMAIL_HOST_USER
                recipient_list = [email]
                
                email_sent = send_mail(
                    subject,
                    message,
                    from_email,
                    recipient_list,
                    fail_silently=False,
                )
                
                if email_sent:
                    messages.success(request, f'✅ Verification code sent to {email}')
                    return redirect('blotter:verify_otp')
                else:
                    messages.error(request, 'Failed to send email. Please try again.')
                    
            except Exception as e:
                print(f"Email error details: {str(e)}")
                messages.error(request, f'Failed to send verification email. Error: {str(e)[:100]}')
        else:
            messages.error(request, 'Please enter a valid email address.')
    else:
        form = EmailVerificationForm()
    
    return render(request, 'verify_email.html', {'form': form})

def verify_otp(request):
    """Step 2: Verify OTP code"""
    if not request.session.get('pending_complaint_email'):
        messages.error(request, 'Please start the verification process again.')
        return redirect('blotter:choose_verification')
    
    if request.method == 'POST':
        form = VerifyOTPForm(request.POST)
        if form.is_valid():
            entered_otp = form.cleaned_data['otp_code']
            stored_otp = request.session.get('email_otp')
            
            # Check OTP expiry (10 minutes)
            otp_created = request.session.get('otp_created_at')
            if otp_created:
                created_time = datetime.datetime.fromisoformat(otp_created)
                if datetime.datetime.now() - created_time > datetime.timedelta(minutes=10):
                    messages.error(request, 'OTP has expired. Please request a new code.')
                    return redirect('blotter:blotter_verify_email')
            
            if entered_otp == stored_otp:
                request.session['email_verified'] = True
                request.session['verification_method'] = 'email'
                messages.success(request, '✅ Email verified successfully! You can now file your blotter.')
                return redirect('blotter:file_blotter')
            else:
                messages.error(request, '❌ Invalid OTP code. Please try again.')
        else:
            messages.error(request, 'Please enter a valid 6-digit code.')
    else:
        form = VerifyOTPForm()
    
    # Get email for display (masked)
    email = request.session.get('pending_complaint_email', '')
    masked_email = ''
    if email:
        parts = email.split('@')
        if len(parts) == 2:
            masked_email = parts[0][:3] + '***@' + parts[1]
    
    return render(request, 'verify_otp.html', {'form': form, 'masked_email': masked_email})

# ====================== CHOOSE VERIFICATION ======================
def choose_verification(request):
    """Step 0: Let user choose verification method"""
    for key in ('email_verified', 'verification_method', 'pending_complaint_email', 'email_otp', 'otp_created_at'):
        request.session.pop(key, None)
    
    if request.method == 'POST':
        method = request.POST.get('verification_method')
        if method == 'email':
            return redirect('blotter:blotter_verify_email')
        elif method == 'id_card':
            request.session['verification_method'] = 'id_card'
            request.session['email_verified'] = False
            return redirect('blotter:file_blotter')
    
    return render(request, 'choose_verification.html')

# ====================== PUBLIC VIEWS ======================
def file_blotter(request):
    """Step 3: Show blotter form after email verification or allow ID upload"""
    
    id_verification_mode = request.session.get('verification_method') == 'id_card'
    
    if not id_verification_mode and not request.session.get('email_verified'):
        return redirect('blotter:choose_verification')
    
    if request.method == 'POST':
        form = PublicBlotterForm(request.POST, request.FILES)
        if form.is_valid():
            blotter = form.save(commit=False)
            
            if id_verification_mode:
                blotter.verification_method = 'id_card'
                blotter.verification_status = 'pending_id_verification'
                blotter.verified_contact = form.cleaned_data.get('complainant_phone') or form.cleaned_data.get('complainant_email')
                blotter.valid_id_file = request.FILES.get('valid_id')
                blotter.valid_id_type = form.cleaned_data.get('id_type')
                blotter.id_verification_status = 'pending'
            else:
                blotter.verification_method = 'email'
                blotter.verification_status = 'pending_review'
                blotter.verified_contact = form.cleaned_data.get('complainant_email')
            
            blotter.is_approved = False
            blotter.purpose = form.cleaned_data.get('purpose')
            blotter.status = 'pending'
            blotter.ip_address = get_client_ip(request)
            blotter.save()
            
            # ===== HANDLE EVIDENCE UPLOADS =====
            evidence_files = request.FILES.getlist('evidence')
            for file in evidence_files:
                if file:
                    # Determine file type
                    ext = file.name.split('.')[-1].lower()
                    if ext in ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp']:
                        file_type = 'image'
                    elif ext in ['pdf', 'doc', 'docx', 'txt']:
                        file_type = 'document'
                    elif ext in ['mp4', 'avi', 'mov', 'mkv']:
                        file_type = 'video'
                    else:
                        file_type = 'other'
                    
                    Evidence.objects.create(
                        blotter=blotter,
                        title=f"Evidence - {file.name[:50]}",
                        file=file,
                        file_type=file_type,
                        uploaded_by=request.user if request.user.is_authenticated else None
                    )
            
            BlotterAuditLog.objects.create(
                blotter=blotter,
                action='create',
                new_value=f'Blotter created - Awaiting staff approval. Verification: {blotter.verification_method}',
                performed_by=request.user if request.user.is_authenticated else None
            )
            
            for key in ('email_verified', 'verification_method', 'pending_complaint_email', 'email_otp', 'otp_created_at'):
                request.session.pop(key, None)
            
            messages.success(request, f'Your blotter has been submitted! Your blotter number is: {blotter.blotter_number}')
            
            return render(request, 'blotter_success.html', {'blotter': blotter})
        else:
            print("Form errors:", form.errors)
            messages.error(request, 'Please correct the errors below.')
    else:
        initial_data = {}
        if id_verification_mode:
            pass
        else:
            if request.session.get('pending_complaint_email'):
                initial_data['complainant_email'] = request.session.get('pending_complaint_email')
                initial_data['confirm_email'] = request.session.get('pending_complaint_email')
        
        form = PublicBlotterForm(initial=initial_data)
    
    return render(request, 'file_blotter.html', {'form': form})

def track_blotter(request):
    """Public tracking - ONLY shows APPROVED blotters"""
    blotter = None
    searched_number = ''
    
    if request.method == 'POST':
        blotter_number = request.POST.get('blotter_number', '').strip()
        searched_number = blotter_number
        
        if blotter_number:
            try:
                # IMPORTANT: Only show blotters that are approved by staff
                blotter = Blotter.objects.get(blotter_number=blotter_number, is_approved=True)
                messages.success(request, f"✅ Blotter found!")
            except Blotter.DoesNotExist:
                messages.error(request, f"❌ No approved blotter found with number: {blotter_number}")
    
    return render(request, 'track_blotter.html', {
        'blotter': blotter,
        'searched_number': searched_number
    })

def blotter_success(request):
    return render(request, 'blotter_success.html')

def blotter_stats_api(request):
    """API endpoint to get blotter statistics"""
    try:
        total = Blotter.objects.filter(is_approved=True).count()
        pending = Blotter.objects.filter(status='pending', is_approved=True).count()
        resolved = Blotter.objects.filter(status='resolved', is_approved=True).count()
        scheduled_today = Schedule.objects.filter(
            hearing_date__date=timezone.now().date(),
            is_completed=False
        ).count()
        
        monthly_data = []
        for i in range(6):
            month = timezone.now().date().replace(day=1) - timezone.timedelta(days=30*i)
            count = Blotter.objects.filter(
                created_at__year=month.year,
                created_at__month=month.month,
                is_approved=True
            ).count()
            monthly_data.append({
                'month': month.strftime('%B'),
                'count': count
            })
        
        data = {
            'total': total,
            'pending': pending,
            'resolved': resolved,
            'scheduled_today': scheduled_today,
            'monthly': monthly_data,
        }
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ====================== STAFF/ADMIN VIEWS ======================
@login_required
def staff_dashboard(request):
    """Staff dashboard with statistics"""
    total_blotters = Blotter.objects.count()
    pending = Blotter.objects.filter(status='pending').count()
    scheduled = Schedule.objects.filter(is_completed=False).count()
    resolved = Blotter.objects.filter(status='resolved').count()
    unsettled = Blotter.objects.filter(status='in_progress').count()
    
    # Pending approvals count (blotters not yet approved)
    pending_approvals_count = Blotter.objects.filter(is_approved=False).count()
    
    today_hearings = Schedule.objects.filter(
        hearing_date__date=timezone.now().date(),
        is_completed=False
    ).select_related('blotter')[:5]
    
    recent_blotters = Blotter.objects.all()[:10]
    
    notifications = Notification.objects.filter(
        recipient=request.user,
        is_read=False
    )[:10]
    
    status_distribution = Blotter.objects.values('status').annotate(count=Count('status'))
    
    context = {
        'total_blotters': total_blotters,
        'pending': pending,
        'scheduled': scheduled,
        'resolved': resolved,
        'unsettled': unsettled,
        'pending_approvals_count': pending_approvals_count,
        'today_hearings': today_hearings,
        'recent_blotters': recent_blotters,
        'notifications': notifications,
        'status_distribution': list(status_distribution),
    }
    
    return render(request, 'blotter_module/staff/dashboard.html', context)

@login_required
def blotter_list(request):
    """List all blotters with filters"""
    blotters = Blotter.objects.all()
    
    search_query = request.GET.get('search', '')
    if search_query:
        blotters = blotters.filter(
            Q(blotter_number__icontains=search_query) |
            Q(complainant_name__icontains=search_query) |
            Q(respondent_name__icontains=search_query)
        )
    
    status_filter = request.GET.get('status', '')
    if status_filter:
        blotters = blotters.filter(status=status_filter)
    
    paginator = Paginator(blotters, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'blotters': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
        'status_choices': Blotter.STATUS_CHOICES,
    }
    
    return render(request, 'blotter_module/staff/blotter_list.html', context)

@login_required
def blotter_detail(request, blotter_id):
    """View blotter details"""
    blotter = get_object_or_404(Blotter, id=blotter_id)
    schedules = blotter.schedules.all()
    evidences = blotter.evidences.all()
    comments = blotter.comments.all()
    audit_logs = blotter.audit_logs.all()[:20]
    
    context = {
        'blotter': blotter,
        'schedules': schedules,
        'evidences': evidences,
        'comments': comments,
        'audit_logs': audit_logs,
    }
    
    return render(request, 'blotter_module/staff/blotter_detail.html', context)

@login_required
def blotter_update_status(request, blotter_id):
    """Update blotter status"""
    blotter = get_object_or_404(Blotter, id=blotter_id)
    old_status = blotter.status
    
    if request.method == 'POST':
        form = BlotterStatusForm(request.POST)
        if form.is_valid():
            new_status = form.cleaned_data['status']
            reason = form.cleaned_data['reason']
            
            blotter.status = new_status
            if new_status == 'resolved':
                blotter.resolution_notes = reason
            blotter.save()
            
            BlotterAuditLog.objects.create(
                blotter=blotter,
                action='status_change',
                old_value=old_status,
                new_value=new_status,
                performed_by=request.user
            )
            
            Notification.objects.create(
                recipient=request.user,
                blotter=blotter,
                notification_type='status',
                message=f'Blotter {blotter.blotter_number} status changed from {old_status} to {new_status}'
            )
            
            messages.success(request, f'Status updated to {new_status}')
            return redirect('blotter_detail', blotter_id=blotter.id)
    else:
        form = BlotterStatusForm(initial={'status': blotter.status})
    
    context = {
        'blotter': blotter,
        'form': form,
        'status_choices': Blotter.STATUS_CHOICES,
    }
    
    return render(request, 'blotter_module/staff/update_status.html', context)

@login_required
def schedule_hearing(request, blotter_id):
    """Schedule a hearing for a blotter"""
    blotter = get_object_or_404(Blotter, id=blotter_id)
    
    if request.method == 'POST':
        form = ScheduleForm(request.POST)
        if form.is_valid():
            schedule = form.save(commit=False)
            schedule.blotter = blotter
            schedule.created_by = request.user
            schedule.save()
            
            blotter.status = 'scheduled'
            blotter.hearing_date = schedule.hearing_date
            blotter.save()
            
            BlotterAuditLog.objects.create(
                blotter=blotter,
                action='schedule',
                new_value=f'Hearing scheduled on {schedule.hearing_date}',
                performed_by=request.user
            )
            
            Notification.objects.create(
                recipient=request.user,
                blotter=blotter,
                notification_type='hearing',
                message=f'Hearing scheduled for {blotter.blotter_number} on {schedule.hearing_date.strftime("%Y-%m-%d %H:%M")}'
            )
            
            messages.success(request, 'Hearing scheduled successfully!')
            return redirect('blotter_detail', blotter_id=blotter.id)
    else:
        form = ScheduleForm()
    
    context = {
        'blotter': blotter,
        'form': form,
    }
    
    return render(request, 'blotter_module/staff/schedule_hearing.html', context)

@login_required
def upload_evidence(request, blotter_id):
    """Upload evidence for a blotter"""
    blotter = get_object_or_404(Blotter, id=blotter_id)
    
    if request.method == 'POST':
        form = EvidenceForm(request.POST, request.FILES)
        if form.is_valid():
            evidence = form.save(commit=False)
            evidence.blotter = blotter
            evidence.uploaded_by = request.user
            evidence.save()
            
            BlotterAuditLog.objects.create(
                blotter=blotter,
                action='upload_evidence',
                new_value=f'Evidence uploaded: {evidence.title}',
                performed_by=request.user
            )
            
            messages.success(request, 'Evidence uploaded successfully!')
            return redirect('blotter_detail', blotter_id=blotter.id)
    else:
        form = EvidenceForm()
    
    context = {
        'blotter': blotter,
        'form': form,
    }
    
    return render(request, 'blotter_module/staff/upload_evidence.html', context)

@login_required
def add_comment(request, blotter_id):
    """Add comment to blotter"""
    blotter = get_object_or_404(Blotter, id=blotter_id)
    
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.blotter = blotter
            comment.user = request.user
            comment.save()
            
            messages.success(request, 'Comment added!')
            return redirect('blotter_detail', blotter_id=blotter.id)
    
    return redirect('blotter_detail', blotter_id=blotter.id)

@login_required
def download_pdf(request, blotter_id):
    """Generate HTML printable version"""
    blotter = get_object_or_404(Blotter, id=blotter_id)
    
    context = {
        'blotter': blotter,
        'today': timezone.now(),
    }
    
    return render(request, 'blotter_module/staff/blotter_print.html', context)

@login_required
def mark_notification_read(request, notification_id):
    """Mark a notification as read"""
    notification = get_object_or_404(Notification, id=notification_id, recipient=request.user)
    notification.is_read = True
    notification.save()
    return JsonResponse({'status': 'success'})

# Staff ID Verification Views
@login_required
def pending_id_verifications(request):
    """View all blotters pending ID verification"""
    if request.user.staff_profile.role != 'admin':
        messages.error(request, 'Admin access required')
        return redirect('staff_dashboard')
    
    pending_blotters = Blotter.objects.filter(id_verification_status='pending')
    
    context = {
        'pending_blotters': pending_blotters,
    }
    
    return render(request, 'blotter_module/staff/pending_id_verifications.html', context)

@login_required
def verify_id(request, blotter_id):
    """Verify a complainant's ID"""
    if request.user.staff_profile.role != 'admin':
        messages.error(request, 'Admin access required')
        return redirect('staff_dashboard')
    
    blotter = get_object_or_404(Blotter, id=blotter_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'approve':
            blotter.id_verification_status = 'verified'
            blotter.verification_status = 'pending_review'
            blotter.id_verified_by = request.user
            blotter.id_verified_at = timezone.now()
            messages.success(request, f'ID for {blotter.complainant_name} has been verified.')
        elif action == 'reject':
            blotter.id_verification_status = 'rejected'
            blotter.id_rejection_reason = request.POST.get('rejection_reason', '')
            messages.warning(request, f'ID for {blotter.complainant_name} has been rejected.')
        
        blotter.save()
        return redirect('pending_id_verifications')
    
    context = {
        'blotter': blotter,
    }
    
    return render(request, 'blotter_module/staff/verify_id.html', context)

# ====================== STAFF APPROVAL VIEWS ======================
@login_required
def pending_approvals(request):
    """View all blotters pending staff approval"""
    if not hasattr(request.user, 'staff_profile'):
        messages.error(request, 'Access denied. Staff only area.')
        return redirect('dashboard')
    
    # Show ONLY blotters that are NOT approved yet
    pending_blotters = Blotter.objects.filter(is_approved=False).order_by('-created_at')
    
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
        'blotters': page_obj,
        'search_query': search_query,
        'total_pending': pending_blotters.count(),
    }
    return render(request, 'blotter_module/staff/pending_approvals.html', context)

@login_required
def approve_blotter(request, blotter_id):
    """Approve a blotter complaint"""
    if not hasattr(request.user, 'staff_profile'):
        messages.error(request, 'Access denied. Staff only area.')
        return redirect('dashboard')
    
    blotter = get_object_or_404(Blotter, id=blotter_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'approve':
            blotter.is_approved = True
            blotter.approved_by = request.user
            blotter.approved_at = timezone.now()
            blotter.verification_status = 'approved'
            messages.success(request, f'Blotter {blotter.blotter_number} has been approved.')
            
            # Send notification to complainant email if available
            if blotter.complainant_email:
                try:
                    send_mail(
                        f'Blotter Approved - {blotter.blotter_number}',
                        f"""
Republic of the Philippines
Barangay Poblacion, Santa Catalina, Negros Oriental

BLOTTER APPROVED

Dear {blotter.complainant_name},

Your blotter complaint has been approved by the Barangay.

Blotter Number: {blotter.blotter_number}
Date Approved: {timezone.now().strftime('%Y-%m-%d %H:%M')}

You can now track your blotter using the tracking system.

Thank you for your cooperation.

This is an automated message.
                        """,
                        settings.DEFAULT_FROM_EMAIL,
                        [blotter.complainant_email],
                        fail_silently=True,
                    )
                except:
                    pass
            
        elif action == 'reject':
            rejection_reason = request.POST.get('rejection_reason', '')
            blotter.is_approved = False
            blotter.verification_status = 'rejected'
            blotter.status = 'dismissed'
            blotter.rejection_reason = rejection_reason
            messages.warning(request, f'Blotter {blotter.blotter_number} has been rejected.')
            
            # Send rejection notification
            if blotter.complainant_email:
                try:
                    send_mail(
                        f'Blotter Update - {blotter.blotter_number}',
                        f"""
Republic of the Philippines
Barangay Poblacion, Santa Catalina, Negros Oriental

BLOTTER STATUS UPDATE

Dear {blotter.complainant_name},

Your blotter complaint has been reviewed.

Blotter Number: {blotter.blotter_number}
Status: Rejected
Reason: {rejection_reason}

Please contact the Barangay Hall for further assistance.

This is an automated message.
                        """,
                        settings.DEFAULT_FROM_EMAIL,
                        [blotter.complainant_email],
                        fail_silently=True,
                    )
                except:
                    pass
        
        blotter.reviewed_by = request.user
        blotter.reviewed_at = timezone.now()
        blotter.save()
        
        BlotterAuditLog.objects.create(
            blotter=blotter,
            action=action,
            new_value=f'Blotter {action}d by {request.user.username}',
            performed_by=request.user
        )
        
        return redirect('blotter:pending_approvals')
    
    # Find potential duplicates for staff reference
    potential_duplicates = Blotter.objects.filter(
        Q(complainant_name__icontains=blotter.complainant_name) |
        Q(respondent_name__icontains=blotter.respondent_name),
        is_approved=True
    ).exclude(id=blotter.id)[:5]
    
    context = {
        'blotter': blotter,
        'potential_duplicates': potential_duplicates,
    }
    return render(request, 'blotter_module/staff/approve_blotter.html', context)
