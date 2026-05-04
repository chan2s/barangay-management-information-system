from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from datetime import datetime
from .models import CertificateRequest
import uuid



def request_form(request):
    """Display certificate request form"""
    return render(request, 'certificates/request_form.html')


def submit_request(request):
    """Process certificate request submission and show confirmation"""
    if request.method == 'POST':

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

        # Get form values
        full_name_value = request.POST.get('fullName', '')
        address_value = request.POST.get('address', '')
        contact_number_value = request.POST.get('contactNumber', '')
        email_value = request.POST.get('email', '')

        # Date of Birth and Age
        dob_value = request.POST.get('dob', '')
        age_value = request.POST.get('age', '')
        civil_status_value = request.POST.get('civilStatus', '')
        gender_value = request.POST.get('gender', '')

        # For Barangay ID - use specific field names
        barangay_purok = request.POST.get('barangay_purok', '')
        barangay_birthplace = request.POST.get('barangay_birthplace', '')

        # For other certificates - use general fields
        general_purok = request.POST.get('purok', '')
        general_birthplace = request.POST.get('birthplace', '')

        # Choose which values to use based on certificate type
        if request_type == 'Barangay ID':
            purok_value = barangay_purok
            birthplace_value = barangay_birthplace
        else:
            purok_value = general_purok
            birthplace_value = general_birthplace

        # Other fields
        weight_value = request.POST.get('weight', '')
        height_value = request.POST.get('height', '')
        emergency_name_value = request.POST.get('emergency_name', '')
        emergency_address_value = request.POST.get('emergency_address', '')
        emergency_contact_value = request.POST.get('emergency_contact', '')
        emergency_relationship_value = request.POST.get('emergency_relationship', '')

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
            status='pending'
        )

        certificate.save()

        # Show confirmation page with tracking number
        context = {
            'tracking_id': certificate.request_id,
            'request_type': request_type,
            'full_name': full_name_value,
            'status': 'pending',
            'submitted_date': datetime.now().strftime('%B %d, %Y at %I:%M %p'),
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
    
    # Get display type
    type_display = dict(CertificateRequest.CERTIFICATE_TYPES).get(cert_request.request_type, '')
    
    context = {
        'request': cert_request,
        'type_display': type_display,
    }
    return render(request, 'certificates/view_request.html', context)


@login_required
def approve_request(request, request_id):
    """Staff view: Approve a certificate request"""
    cert_request = get_object_or_404(CertificateRequest, id=request_id)
    
    if request.method == 'POST':
        cert_request.status = 'processing'
        cert_request.date_processed = timezone.now()
        cert_request.processed_by = request.user.username
        cert_request.remarks = request.POST.get('remarks', '')
        cert_request.save()
        
        messages.success(request, f'Certificate request {cert_request.request_id} has been approved.')
        return redirect('certificates:request_list')
    
    context = {
        'request': cert_request,
        'type_display': dict(CertificateRequest.CERTIFICATE_TYPES).get(cert_request.request_type, ''),
    }
    return render(request, 'certificates/approve_request.html', context)


@login_required
def reject_request(request, request_id):
    """Staff view: Reject a certificate request"""
    cert_request = get_object_or_404(CertificateRequest, id=request_id)
    
    if request.method == 'POST':
        rejection_reason = request.POST.get('rejection_reason', '')
        cert_request.status = 'cancelled'
        cert_request.remarks = rejection_reason
        cert_request.save()
        
        messages.warning(request, f'Certificate request {cert_request.request_id} has been rejected.')
        return redirect('certificates:request_list')
    
    context = {
        'request': cert_request,
        'type_display': dict(CertificateRequest.CERTIFICATE_TYPES).get(cert_request.request_type, ''),
    }
    return render(request, 'certificates/reject_request.html', context)

@login_required
def generate_certificate(request, request_id):
    """Staff view: Generate certificate PDF"""
    cert_request = get_object_or_404(CertificateRequest, id=request_id)
    
    if cert_request.status != 'processing':
        messages.error(request, 'Only approved requests can generate certificates.')
        return redirect('certificates:request_list')
    
    # Map display type
    type_map = {
        'clearance': 'Barangay Clearance',
        'indigency': 'Certificate of Indigency',
        'residency': 'Certificate of Residency',
        'id': 'Barangay ID',
    }
    request_type_display = type_map.get(cert_request.request_type, 'Barangay Clearance')
    
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
def regenerate_certificate(request, request_id):
    """Staff view: Regenerate certificate (for printing)"""
    cert_request = get_object_or_404(CertificateRequest, id=request_id)
    
    if cert_request.status != 'approved':
        messages.error(request, 'Only approved requests can be regenerated.')
        return redirect('certificates:request_list')
    
    current_date = datetime.now().strftime('%dth day of %B, %Y')
    
    # Map display type
    type_map = {
        'clearance': 'Barangay Clearance',
        'indigency': 'Certificate of Indigency',
        'residency': 'Certificate of Residency',
        'id': 'Barangay ID',
    }
    request_type_display = type_map.get(cert_request.request_type, 'Barangay Clearance')
    
    context = {
        'tracking_id': cert_request.request_id,
        'request_type': request_type_display,
        'full_name': cert_request.full_name,
        'address': cert_request.address,
        'purpose': cert_request.purpose,
        'purok': cert_request.purok,
        'current_date': current_date,
        'birthplace': cert_request.birthplace,
        'weight': cert_request.weight,
        'height': cert_request.height,
        'emergency_name': cert_request.emergency_name,
        'emergency_address': cert_request.emergency_address,
        'emergency_contact': cert_request.emergency_contact,
        'emergency_relationship': cert_request.emergency_relationship,
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
def mark_as_released(request, request_id):
    """Staff view: Mark certificate as released/claimed"""
    cert_request = get_object_or_404(CertificateRequest, id=request_id)
    
    if request.method == 'POST':
        cert_request.status = 'released'
        cert_request.date_released = timezone.now()
        cert_request.save()
        
        messages.success(request, f'Certificate {cert_request.request_id} has been marked as released.')
        return redirect('certificates:request_list')
    
    context = {
        'request': cert_request,
        'type_display': dict(CertificateRequest.CERTIFICATE_TYPES).get(cert_request.request_type, ''),
    }
    return render(request, 'certificates/mark_released.html', context)

@login_required
def generate_clearance(request, request_id):
    cert_request = get_object_or_404(CertificateRequest, id=request_id)
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
    context = {
        'tracking_id': cert_request.request_id,
        'full_name': cert_request.full_name,
        'purpose': cert_request.purpose,
        'current_date': timezone.now().strftime('%dth day of %B, %Y'),
    }
    return render(request, 'certificates/certificate_indigency.html', context)

@login_required
def generate_barangay_id(request, request_id):
    cert_request = get_object_or_404(CertificateRequest, id=request_id)
    context = {
        'tracking_id': cert_request.request_id,
        'full_name': cert_request.full_name,
        'purok': cert_request.purok,
        'weight': cert_request.weight,
        'height': cert_request.height,
        'gender': cert_request.gender,
        'civil_status': cert_request.civil_status,
        'dob': cert_request.date_of_birth.strftime('%B %d, %Y') if cert_request.date_of_birth else '',
        'birthplace': cert_request.birthplace,
        'emergency_name': cert_request.emergency_name,
        'emergency_address': cert_request.emergency_address,
        'emergency_contact': cert_request.emergency_contact,
        'emergency_relationship': cert_request.emergency_relationship,
        'current_date': timezone.now().strftime('%B %d, %Y'),
    }
    return render(request, 'certificates/barangay_id.html', context)