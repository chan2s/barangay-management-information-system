from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone

def send_claim_notification(certificate):
    """
    Send email notification to resident when certificate is ready for claiming
    Only sends if email is provided
    """
    notifications_sent = False
    
    # Check if email is provided
    if certificate.email and certificate.email.strip():
        try:
            # Set claim deadline (7 days from approval if not set)
            if not certificate.claim_deadline:
                certificate.claim_deadline = timezone.now() + timezone.timedelta(days=7)
                certificate.save()
            
            subject = f'Certificate Ready for Claim - {certificate.request_id}'
            
            # Map certificate type to display name
            type_map = {
                'clearance': 'Barangay Clearance',
                'indigency': 'Certificate of Indigency', 
                'residency': 'Certificate of Residency',
                'id': 'Barangay ID',
            }
            cert_type_display = type_map.get(certificate.request_type, 'Certificate')
            
            message = f"""
Republic of the Philippines
Barangay Poblacion, Santa Catalina, Negros Oriental

═══════════════════════════════════════════════════════════
              CERTIFICATE READY FOR CLAIM
═══════════════════════════════════════════════════════════

Dear {certificate.full_name},

Your certificate request has been APPROVED and is now ready for claiming.

📄 CERTIFICATE DETAILS:
   Reference Number: {certificate.request_id}
   Certificate Type: {cert_type_display}
   Date Approved: {certificate.date_approved.strftime('%B %d, %Y') if certificate.date_approved else 'N/A'}

📅 CLAIM INFORMATION:
   Claim By Date: {certificate.claim_deadline.strftime('%B %d, %Y')}
   Time: 8:00 AM - 5:00 PM (Monday to Friday)
   Location: Barangay Poblacion Hall, Burgos St., Poblacion, Santa Catalina, Negros Oriental

📋 WHAT TO BRING:
   • Valid Government ID (any valid ID)
   • This reference number: {certificate.request_id}
   • Payment fee (if applicable - ₱50 for Clearance/Residency, ₱100 for Barangay ID, Free for Indigency)

⚠️ IMPORTANT REMINDERS:
   1. Please claim your certificate within 7 days from today
   2. If you cannot claim personally, you may send an authorized representative with:
      - Signed authorization letter
      - Your valid ID (original or photocopy)
      - Representative's valid ID
   3. Keep this reference number for claiming
   4. Certificate will be considered forfeited if not claimed after 30 days

For inquiries, please contact:
   📞 Barangay Hall: (032) 123-4567
   📱 Mobile: 09123456789
   ✉️ Email: brgy.poblacion@bims.gov.ph

Thank you for using the Barangay Integrated Management System (BIMS).

Sincerely,
Barangay Poblacion Administration

═══════════════════════════════════════════════════════════
This is an automated message. Please do not reply.
"""
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [certificate.email],
                fail_silently=False,
            )
            notifications_sent = True
            print(f"✅ Email notification sent to {certificate.email} for certificate {certificate.request_id}")
        except Exception as e:
            print(f"❌ Failed to send email to {certificate.email}: {str(e)}")
    else:
        print(f"⚠️ No email provided for certificate {certificate.request_id}. Skipping notification.")
    
    return notifications_sent


def send_rejection_notification(certificate):
    """
    Send rejection notification email
    """
    if certificate.email and certificate.email.strip():
        try:
            type_map = {
                'clearance': 'Barangay Clearance',
                'indigency': 'Certificate of Indigency',
                'residency': 'Certificate of Residency',
                'id': 'Barangay ID',
            }
            cert_type_display = type_map.get(certificate.request_type, 'Certificate')
            
            subject = f'Certificate Request Update - {certificate.request_id}'
            message = f"""
Republic of the Philippines
Barangay Poblacion, Santa Catalina, Negros Oriental

═══════════════════════════════════════════════════════════
              CERTIFICATE REQUEST UPDATE
═══════════════════════════════════════════════════════════

Dear {certificate.full_name},

We regret to inform you that your certificate request has been reviewed and cannot be approved at this time.

📄 Reference Number: {certificate.request_id}
📅 Date Submitted: {certificate.date_submitted.strftime('%B %d, %Y')}
📄 Certificate Type: {cert_type_display}

❌ STATUS: Not Approved

Reason: {certificate.rejection_reason or certificate.remarks or 'Please contact the Barangay Hall for more information.'}

📋 WHAT TO DO NEXT:
   1. Please visit the Barangay Hall to clarify the requirements
   2. Bring any additional documents needed
   3. You may re-submit your request once requirements are complete

For inquiries, please contact:
   📞 Barangay Hall: (032) 123-4567
   📱 Mobile: 09123456789
   ✉️ Email: brgy.poblacion@bims.gov.ph

We apologize for any inconvenience.

Sincerely,
Barangay Poblacion Administration

═══════════════════════════════════════════════════════════
This is an automated message. Please do not reply.
"""
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [certificate.email],
                fail_silently=False,
            )
            print(f"✅ Rejection notification sent to {certificate.email} for certificate {certificate.request_id}")
            return True
        except Exception as e:
            print(f"❌ Failed to send rejection email: {str(e)}")
            return False
    return False