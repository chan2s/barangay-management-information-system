from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from datetime import datetime
from .models import CertificateRequest
from staff_module.audit import log_activity
from staff_module.decorators import role_required
import uuid


def request_form(request):
    """Display certificate request form"""
    return render(request, 'certificates/request_form.html')


def submit_request(request):
    """Process certificate request submission and show confirmation"""
    if request.method == 'POST':
        
        print("FILES RECEIVED:", request.FILES)
        print("POST DATA:", request.POST)

        # Map certificate type
        cert_type_map = {
            'Barangay Clearance': 'clearance',
            'Certificate of Indigency': 'indigency',
            'Certificate of Residency': 'residency',
            'Barangay ID': 'id',
        }

        request_type = request.POST.get('requestType')
        cert_type = cert_type_map.get(request_type, 'clearance')

        # Get purpose based on certificate type
        purpose_value = ''
        if request_type == 'Barangay Clearance':
            purpose_value = request.POST.get('purpose_clearance', '')
        elif request_type == 'Certificate of Indigency':
            purpose_value = request.POST.get('purpose_indigency', '')
        elif request_type == 'Certificate of Residency':
            purpose_value = request.POST.get('purpose_residency', '')
        elif request_type == 'Barangay ID':
            purpose_value = request.POST.get('purpose', '')

        # Get common form values
        full_name_value = request.POST.get('fullName', '')
        address_value = request.POST.get('address', '')
        contact_number_value = request.POST.get('contactNumber', '')
        email_value = request.POST.get('email', '')
        dob_value = request.POST.get('dob', '')
        age_value = request.POST.get('age', '')
        civil_status_value = request.POST.get('civilStatus', '')
        gender_value = request.POST.get('gender', '')
        purok_value = request.POST.get('purok', '')

        # For Barangay ID - get all specific fields
        birthplace_value = request.POST.get('birthplace', '')
        weight_value = request.POST.get('weight', '')
        height_value = request.POST.get('height', '')
        emergency_name_value = request.POST.get('emergency_name', '')
        emergency_address_value = request.POST.get('emergency_address', '')
        emergency_contact_value = request.POST.get('emergency_contact', '')
        emergency_relationship_value = request.POST.get('emergency_relationship', '')

        # Handle file uploads
        valid_id_file = request.FILES.get('valid_id')
        proof_residency_file = request.FILES.get('proof_residency')
        photo_file = request.FILES.get('photo')
        
        # Create certificate request
        certificate = CertificateRequest(
            request_type=cert_type,
            full_name=full_name_value,
            address=address_value,
            contact_number=contact_number_value,
            email=email_value,
            date_of_birth=dob_value if dob_value else None,
            age=age_value if age_value else None,
            civil_status=civil_status_value,
            gender=gender_value,
            purpose=purpose_value,
            purok=purok_value,
            birthplace=birthplace_value,
            weight=weight_value,
            height=height_value,
            emergency_name=emergency_name_value,
            emergency_address=emergency_address_value,
            emergency_contact=emergency_contact_value,
            emergency_relationship=emergency_relationship_value,
            valid_id=valid_id_file,
            proof_residency=proof_residency_file,
            photo=photo_file,
            status='pending'
        )

        certificate.save()

        context = {
            'tracking_id': certificate.request_id,
            'request_type': request_type,
            'full_name': full_name_value,
            'status': 'pending',
            'submitted_date': datetime.now().strftime('%B %d, %Y at %I:%M %p'),
            'valid_id': valid_id_file is not None,
            'proof_residency': proof_residency_file is not None,
            'photo': photo_file is not None,
        }
        
        return render(request, 'certificates/confirmation.html', context)

    return redirect('certificates:request_form')


# ====================== STAFF MANAGEMENT VIEWS ======================

@login_required
def request_list(request):
    """Staff view: List all certificate requests"""
    certificate_requests = CertificateRequest.objects.all().order_by('-date_submitted')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        certificate_requests = certificate_requests.filter(
            Q(request_id__icontains=search_query) |
            Q(full_name__icontains=search_query)
        )
    
    # Filter by status
    status_filter = request.GET.get('status', '')
    if status_filter:
        certificate_requests = certificate_requests.filter(status=status_filter)
    
    # Filter by certificate type
    type_filter = request.GET.get('type', '')
    if type_filter:
        certificate_requests = certificate_requests.filter(request_type=type_filter)
    
    # Pagination
    paginator = Paginator(certificate_requests, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'requests': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
        'type_filter': type_filter,
        'total_count': certificate_requests.count(),
        'status_choices': CertificateRequest.STATUS_CHOICES,
        'type_choices': CertificateRequest.CERTIFICATE_TYPES,
    }
    return render(request, 'certificates/request_list.html', context)


def track_request(request):
    """Public view: Track certificate request status"""
    reference_number = None
    certificate_request = None
    
    if request.method == 'POST':
        reference_number = request.POST.get('reference_number', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        
        if reference_number:
            # First try to find by reference number only
            try:
                certificate_request = CertificateRequest.objects.get(request_id=reference_number)
                messages.success(request, f'Request found!')
            except CertificateRequest.DoesNotExist:
                # If not found and last name provided, try with both
                if last_name:
                    try:
                        certificate_request = CertificateRequest.objects.get(
                            request_id=reference_number,
                            full_name__icontains=last_name
                        )
                        messages.success(request, f'Request found!')
                    except CertificateRequest.DoesNotExist:
                        messages.error(request, f'No certificate request found with that reference number and name.')
                else:
                    messages.error(request, f'No certificate request found with reference number: {reference_number}')
    
    context = {
        'reference_number': reference_number,
        'request': certificate_request,
    }
    return render(request, 'certificates/track_request.html', context)


@login_required
def view_request(request, request_id):
    """Staff view: View single certificate request details"""
    cert_request = get_object_or_404(CertificateRequest, id=request_id)
    
    type_display = dict(CertificateRequest.CERTIFICATE_TYPES).get(cert_request.request_type, '')
    
    context = {
        'cert_request': cert_request,
        'type_display': type_display,
    }
    return render(request, 'certificates/view_request.html', context)


@login_required
def process_request(request, request_id):
    """Staff view: Process a certificate request (move to for_approval)"""
    cert_request = get_object_or_404(CertificateRequest, id=request_id)
    
    if request.method == 'POST':
        # Only allow processing from pending status
        if cert_request.status != 'pending':
            messages.error(request, f'Cannot process request with status: {cert_request.get_status_display()}')
            return redirect('certificates:view_request', request_id=cert_request.id)
        
        cert_request.status = 'for_approval'
        cert_request.date_processed = timezone.now()
        cert_request.processed_by = request.user.username
        cert_request.remarks = request.POST.get('remarks', '')
        cert_request.save()
        
        messages.success(request, f'Certificate request {cert_request.request_id} has been sent for Kapitan approval.')
        return redirect('certificates:request_list')
    
    context = {
        'request': cert_request,
        'type_display': dict(CertificateRequest.CERTIFICATE_TYPES).get(cert_request.request_type, ''),
    }
    return render(request, 'certificates/process_request.html', context)


@login_required
def release_request(request, request_id):
    """Staff view: Release certificate after Kapitan approval"""
    cert_request = get_object_or_404(CertificateRequest, id=request_id)
    
    if request.method == 'POST':
        # Only allow release from approved status
        if cert_request.status != 'approved':
            messages.error(request, f'Cannot release certificate with status: {cert_request.get_status_display()}. Only approved certificates can be released.')
            return redirect('certificates:view_request', request_id=cert_request.id)
        
        cert_request.status = 'released'
        cert_request.date_released = timezone.now()
        cert_request.remarks = request.POST.get('remarks', '')
        cert_request.save()
        
        messages.success(request, f'Certificate {cert_request.request_id} has been marked as released.')
        return redirect('certificates:request_list')
    
    context = {
        'request': cert_request,
        'type_display': dict(CertificateRequest.CERTIFICATE_TYPES).get(cert_request.request_type, ''),
    }
    return render(request, 'certificates/release_request.html', context)


# ====================== KAPITAN APPROVAL VIEWS ======================

@login_required
@role_required(['kapitan', 'admin'])
def for_approval_list(request):
    """Kapitan view: List requests pending approval"""
    certificate_requests = CertificateRequest.objects.filter(status='for_approval').order_by('-date_submitted')
    
    context = {
        'requests': certificate_requests,
        'total_count': certificate_requests.count(),
    }
    return render(request, 'kapitan_portal/for_approval_list.html', context)


@login_required
@role_required(['kapitan', 'admin'])
def kapitan_approve_request(request, request_id):
    """Kapitan view: Approve a certificate request"""
    cert_request = get_object_or_404(CertificateRequest, id=request_id)
    
    # Only allow approval from for_approval status
    if cert_request.status != 'for_approval':
        messages.error(request, f'Cannot approve request with status: {cert_request.get_status_display()}. Only requests sent for approval can be approved.')
        return redirect('kapitan_portal:for_approval_list')
    
    if request.method == 'POST':
        cert_request.status = 'approved'
        cert_request.date_approved = timezone.now()
        cert_request.approved_by = request.user.username
        cert_request.remarks = request.POST.get('remarks', '')
        cert_request.save()
        
        messages.success(request, f'Certificate request {cert_request.request_id} has been approved.')
        return redirect('kapitan_portal:for_approval_list')
    
    context = {
        'request': cert_request,
        'type_display': dict(CertificateRequest.CERTIFICATE_TYPES).get(cert_request.request_type, ''),
    }
    return render(request, 'kapitan_portal/approve_request.html', context)


@login_required
@role_required(['kapitan', 'admin'])
def kapitan_reject_request(request, request_id):
    """Kapitan view: Reject a certificate request"""
    cert_request = get_object_or_404(CertificateRequest, id=request_id)
    
    # Only allow rejection from for_approval status
    if cert_request.status != 'for_approval':
        messages.error(request, f'Cannot reject request with status: {cert_request.get_status_display()}')
        return redirect('kapitan_portal:for_approval_list')
    
    if request.method == 'POST':
        rejection_reason = request.POST.get('rejection_reason', '')
        cert_request.status = 'rejected'
        cert_request.rejection_reason = rejection_reason
        cert_request.remarks = rejection_reason
        cert_request.save()
        
        messages.warning(request, f'Certificate request {cert_request.request_id} has been rejected.')
        return redirect('kapitan_portal:for_approval_list')
    
    context = {
        'request': cert_request,
        'type_display': dict(CertificateRequest.CERTIFICATE_TYPES).get(cert_request.request_type, ''),
    }
    return render(request, 'kapitan_portal/reject_request.html', context)


@login_required
def generate_certificate(request, request_id):
    """Staff view: Generate certificate PDF (only for approved certificates)"""
    cert_request = get_object_or_404(CertificateRequest, id=request_id)
    
    if cert_request.status != 'approved':
        messages.error(request, 'Only approved certificates can be generated.')
        return redirect('certificates:view_request', request_id=cert_request.id)
    
    # Map display type
    type_map = {
        'clearance': 'Barangay Clearance',
        'indigency': 'Certificate of Indigency',
        'residency': 'Certificate of Residency',
        'id': 'Barangay ID',
    }
    request_type_display = type_map.get(cert_request.request_type, 'Barangay Clearance')
    log_activity(request, 'certificate_generate', 'certificate', f'Generated {request_type_display} for request {cert_request.request_id}')
    
    context = {
        'tracking_id': cert_request.request_id,
        'request_type': request_type_display,
        'full_name': cert_request.full_name,
        'address': cert_request.address,
        'purpose': cert_request.purpose,
        'purok': cert_request.purok,
        'current_date': timezone.now().strftime('%dth day of %B, %Y'),
        'birthplace': cert_request.birthplace,
        'weight': cert_request.weight,
        'height': cert_request.height,
        'emergency_name': cert_request.emergency_name,
        'emergency_address': cert_request.emergency_address,
        'emergency_contact': cert_request.emergency_contact,
        'emergency_relationship': cert_request.emergency_relationship,
        # ADD THESE LINES for Barangay ID
        'gender': cert_request.gender,
        'civil_status': cert_request.civil_status,
        'dob': cert_request.date_of_birth.strftime('%B %d, %Y') if cert_request.date_of_birth else '',
        'photo_url': cert_request.photo.url if cert_request.photo else None,
    }
    
    # Render appropriate certificate
    if cert_request.request_type == 'clearance':
        return render(request, 'certificates/barangay_clearance.html', context)
    elif cert_request.request_type == 'indigency':
        return render(request, 'certificates/certificate_indigency.html', context)
    elif cert_request.request_type == 'residency':
        return render(request, 'certificates/certificate_residency.html', context)
    elif cert_request.request_type == 'id':
        return render(request, 'certificates/barangay_id.html', context)
    
    return redirect('certificates:request_list')


@login_required
def generate_clearance(request, request_id):
    cert_request = get_object_or_404(CertificateRequest, id=request_id)
    log_activity(request, 'certificate_generate', 'certificate', f'Generated Barangay Clearance for request {cert_request.request_id}')
    context = {
        'tracking_id': cert_request.request_id,
        'full_name': cert_request.full_name,
        'age': cert_request.age,
        'purpose': cert_request.purpose,
        'current_date': timezone.now().strftime('%dth day of %B, %Y'),
    }
    return render(request, 'certificates/barangay_clearance.html', context)


@login_required
def generate_residency(request, request_id):
    cert_request = get_object_or_404(CertificateRequest, id=request_id)
    log_activity(request, 'certificate_generate', 'certificate', f'Generated Certificate of Residency for request {cert_request.request_id}')
    context = {
        'tracking_id': cert_request.request_id,
        'full_name': cert_request.full_name,
        'age': cert_request.age,
        'civil_status': cert_request.civil_status,
        'purok': cert_request.purok,
        'purpose': cert_request.purpose,
        'current_date': timezone.now().strftime('%dth day of %B, %Y'),
    }
    return render(request, 'certificates/certificate_residency.html', context)


@login_required
def generate_indigency(request, request_id):
    cert_request = get_object_or_404(CertificateRequest, id=request_id)
    log_activity(request, 'certificate_generate', 'certificate', f'Generated Certificate of Indigency for request {cert_request.request_id}')
    context = {
        'tracking_id': cert_request.request_id,
        'full_name': cert_request.full_name,
        'purpose': cert_request.purpose,
        'current_date': timezone.now().strftime('%dth day of %B, %Y'),
    }
    return render(request, 'certificates/certificate_indigency.html', context)


@login_required
def generate_barangay_id(request, request_id):
    """Generate Barangay ID certificate"""
    from django.utils import timezone
    
    # DEBUG PRINT - This will show in your terminal
    print(f"========== DEBUG generate_barangay_id ==========")
    print(f"Received request_id parameter: '{request_id}'")
    
    # Try to get by id (database primary key)
    try:
        cert_request = CertificateRequest.objects.get(id=request_id)
        print(f"Found by ID (primary key): {cert_request.request_id}")
    except (ValueError, CertificateRequest.DoesNotExist):
        # If not found by id, try by request_id string
        try:
            cert_request = CertificateRequest.objects.get(request_id=request_id)
            print(f"Found by request_id: {cert_request.request_id}")
        except CertificateRequest.DoesNotExist:
            print(f"ERROR: Certificate not found with id or request_id: {request_id}")
            messages.error(request, 'Certificate request not found.')
            return redirect('certificates:request_list')

    log_activity(request, 'certificate_generate', 'certificate', f'Generated Barangay ID for request {cert_request.request_id}')
    
    print(f"Certificate: {cert_request.request_id}")
    print(f"Gender from DB: '{cert_request.gender}'")
    print(f"Civil Status from DB: '{cert_request.civil_status}'")
    print(f"Date of Birth from DB: {cert_request.date_of_birth}")
    print(f"Request Type: {cert_request.request_type}")
    print(f"=================================================")
    
    # Check if it's a Barangay ID request
    if cert_request.request_type != 'id':
        messages.error(request, 'This is not a Barangay ID request.')
        return redirect('certificates:request_list')
    
    context = {
        'tracking_id': cert_request.request_id,
        'full_name': cert_request.full_name,
        'purok': cert_request.purok,
        'weight': cert_request.weight,
        'height': cert_request.height,
        'gender': cert_request.gender,
        'civil_status': cert_request.civil_status,
        'dob': cert_request.date_of_birth.strftime('%B %d, %Y') if cert_request.date_of_birth else '',
        'birthplace': cert_request.birthplace or 'Sta. Catalina, Negros Oriental',
        'emergency_name': cert_request.emergency_name,
        'emergency_address': cert_request.emergency_address,
        'emergency_contact': cert_request.emergency_contact,
        'emergency_relationship': cert_request.emergency_relationship,
        'current_date': timezone.now().strftime('%B %d, %Y'),
        'photo_url': cert_request.photo.url if cert_request.photo else None,
    }
    
    # DEBUG: Print the context being sent
    print(f"Context being sent to template:")
    print(f"  gender: '{context['gender']}'")
    print(f"  civil_status: '{context['civil_status']}'")
    print(f"  dob: '{context['dob']}'")
    print(f"=================================================")
    
    return render(request, 'certificates/barangay_id.html', context)
