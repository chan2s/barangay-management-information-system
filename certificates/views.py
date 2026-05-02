from django.shortcuts import render, redirect
from django.contrib import messages
from datetime import datetime
from .models import CertificateRequest
import uuid


def request_form(request):
    """Display certificate request form"""
    return render(request, 'certificates/request_form.html')


def submit_request(request):
    """Process certificate request submission and generate certificate"""
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

        # Get form values (removed dob, civil_status, gender)
        full_name_value = request.POST.get('fullName', '')
        address_value = request.POST.get('address', '')

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

        # Create certificate request (removed dob, civil_status, gender)
        certificate = CertificateRequest(
            request_type=cert_type,
            full_name=full_name_value,
            address=address_value,
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

        current_date = datetime.now().strftime('%dth day of %B, %Y')

        # Prepare context for template (removed dob, age, civil_status, gender)
        context = {
            'tracking_id': certificate.request_id,
            'request_type': request_type,
            'full_name': full_name_value,
            'address': address_value,
            'purpose': purpose_value,
            'purok': purok_value,
            'current_date': current_date,
            'birthplace': birthplace_value,
            'weight': weight_value,
            'height': height_value,
            'emergency_name': emergency_name_value,
            'emergency_address': emergency_address_value,
            'emergency_contact': emergency_contact_value,
            'emergency_relationship': emergency_relationship_value,
        }

        # Render appropriate certificate
        if request_type == 'Barangay Clearance':
            return render(request, 'certificates/barangay_clearance.html', context)
        elif request_type == 'Certificate of Indigency':
            return render(request, 'certificates/certificate_indigency.html', context)
        elif request_type == 'Certificate of Residency':
            return render(request, 'certificates/certificate_residency.html', context)
        elif request_type == 'Barangay ID':
            return render(request, 'certificates/barangay_id.html', context)

    return redirect('certificates:request_form')