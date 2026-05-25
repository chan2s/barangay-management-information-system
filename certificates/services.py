from django.template import Context, Template
from django.utils import timezone
from django.utils.safestring import mark_safe
import re

from .models import CertificateRequest, CertificateTemplate


CERTIFICATE_TEMPLATE_FILES = {
    'clearance': 'certificates/barangay_clearance.html',
    'indigency': 'certificates/certificate_indigency.html',
    'residency': 'certificates/certificate_residency.html',
    'id': 'certificates/barangay_id.html',
}


DEFAULT_HEADER_HTML = """
<div class="certificate-header">
    {% if seal_url %}<img src="{{ seal_url }}" alt="Barangay Seal" class="seal">{% endif %}
    <div>
        <div>Republic of the Philippines</div>
        <div>Province of Negros Oriental</div>
        <strong>Municipality of Santa Catalina</strong>
        <h2>Barangay Poblacion</h2>
        <div>Office of the Punong Barangay</div>
    </div>
    {% if logo_url %}<img src="{{ logo_url }}" alt="Municipality Seal" class="seal">{% endif %}
</div>
"""

DEFAULT_BODY_HTML = {
    'clearance': """
<h1>Barangay Clearance</h1>
<p><strong>TO WHOM IT MAY CONCERN:</strong></p>
<p>This is to certify that <strong>{{ full_name }}</strong>, {{ age|default:"____" }} years of age, Filipino, and a resident of {{ address }} is known to this office as a person of good moral character and standing in the community.</p>
<p>This certification is issued upon request for <strong>{{ purpose|default:"________________" }}</strong>.</p>
<p>Issued this <strong>{{ current_date }}</strong> at Barangay Poblacion, Santa Catalina, Negros Oriental.</p>
""",
    'indigency': """
<h1>Certificate of Indigency</h1>
<p><strong>TO WHOM IT MAY CONCERN:</strong></p>
<p>This is to certify that <strong>{{ full_name }}</strong> is a resident of {{ address }}.</p>
<p>This certification is issued upon request for <strong>{{ purpose|default:"________________" }}</strong>.</p>
<p>Issued this <strong>{{ current_date }}</strong> at Barangay Poblacion, Santa Catalina, Negros Oriental.</p>
""",
    'residency': """
<h1>Certificate of Residency</h1>
<p><strong>TO WHOM IT MAY CONCERN:</strong></p>
<p>This is to certify that <strong>{{ full_name }}</strong>, {{ age|default:"____" }} years of age, {{ civil_status|default:"" }}, is a bona fide resident of {{ address }}.</p>
<p>This certification is issued upon request for <strong>{{ purpose|default:"________________" }}</strong>.</p>
<p>Given this <strong>{{ current_date }}</strong> at Barangay Poblacion, Santa Catalina, Negros Oriental.</p>
""",
    'id': """
<h1>Barangay ID Preview</h1>
<p><strong>ID No.:</strong> {{ tracking_id }}</p>
<p><strong>Name:</strong> {{ full_name }}</p>
<p><strong>Address:</strong> {{ address }}</p>
<p><strong>Birth Date:</strong> {{ dob|default:"________" }}</p>
<p><strong>Emergency Contact:</strong> {{ emergency_name|default:"________" }} - {{ emergency_contact|default:"________" }}</p>
""",
}

DEFAULT_FOOTER_HTML = """
<div class="signature-block">
    {% if signature_url %}<img src="{{ signature_url }}" alt="Authorized Signature" class="signature">{% endif %}
    <div class="signature-line"></div>
    <strong>{{ approved_by|default:"HON. WELMAR TA-ALA" }}</strong>
    <span>Punong Barangay</span>
</div>
<div class="certificate-footer">Tracking ID: <strong>{{ tracking_id }}</strong></div>
"""

ALLOWED_PLACEHOLDERS = {
    'tracking_id', 'request_type', 'full_name', 'address', 'age', 'purpose', 'purok',
    'current_date', 'birthplace', 'weight', 'height', 'gender', 'civil_status', 'dob',
    'emergency_name', 'emergency_address', 'emergency_contact', 'emergency_relationship',
    'approved_by', 'photo_url', 'logo_url', 'seal_url', 'signature_url',
}


def certificate_context(cert_request):
    return {
        'certificate': cert_request,
        'tracking_id': cert_request.request_id,
        'request_type': cert_request.get_request_type_display(),
        'full_name': cert_request.full_name,
        'address': cert_request.address,
        'age': cert_request.age,
        'purpose': cert_request.purpose,
        'purok': cert_request.purok,
        'current_date': timezone.now().strftime('%B %d, %Y'),
        'birthplace': cert_request.birthplace,
        'weight': cert_request.weight,
        'height': cert_request.height,
        'emergency_name': cert_request.emergency_name,
        'emergency_address': cert_request.emergency_address,
        'emergency_contact': cert_request.emergency_contact,
        'emergency_relationship': cert_request.emergency_relationship,
        'gender': cert_request.gender,
        'civil_status': cert_request.civil_status,
        'dob': cert_request.date_of_birth.strftime('%B %d, %Y') if cert_request.date_of_birth else '',
        'photo_url': cert_request.photo.url if cert_request.photo else '',
        'approved_by': cert_request.approved_by,
    }


def active_certificate_template(template_type):
    return (
        CertificateTemplate.objects
        .filter(template_type=template_type, is_active=True, is_deleted=False)
        .order_by('-updated_at', '-created_at')
        .first()
    )


def render_template_html(source, context):
    return mark_safe(Template(source or '').render(Context(context)))


def rendered_template_sections(template, cert_request=None, extra_context=None):
    context = certificate_context(cert_request) if cert_request else {}
    if extra_context:
        context.update(extra_context)
    context.update({
        'logo_url': template.logo.url if template and template.logo else '',
        'seal_url': template.seal.url if template and template.seal else '',
        'signature_url': template.signature.url if template and template.signature else '',
    })
    document_html = template.document_html or '\n'.join([
        template.header_html or '',
        template.body_html or '',
        template.footer_html or '',
    ])
    rendered_document = render_template_html(document_html, context)
    return {
        'document_html': rendered_document,
        'header_html': rendered_document,
        'body_html': '',
        'footer_html': '',
        'render_context': context,
    }


def strip_requester_preview_html(html):
    """
    Remove common signing/footer blocks from requester previews. This keeps
    public previews focused on the submitted content, without exposing official
    signature material or certificate log/footer data.
    """
    cleaned = html or ''
    class_patterns = [
        r'signature-block',
        r'signature-section',
        r'attested-block',
        r'certificate-footer',
        r'\bfooter\b',
    ]
    for pattern in class_patterns:
        cleaned = re.sub(
            r'<div\b[^>]*class=(["\'])(?=[^"\']*' + pattern + r')[^"\']*\1[^>]*>.*?</div>',
            '',
            cleaned,
            flags=re.I | re.S,
        )
    cleaned = re.sub(r'<img\b[^>]*(signature|kapitan)[^>]*>', '', cleaned, flags=re.I | re.S)
    cleaned = re.sub(r'<svg\b[^>]*(kapitan|signature)[^>]*>.*?</svg>', '', cleaned, flags=re.I | re.S)
    cleaned = re.sub(r'HON\.\s*WELMAR\s*TA-ALA', '', cleaned, flags=re.I)
    return cleaned


def rendered_requester_preview_sections(template, cert_request):
    context = certificate_context(cert_request)
    context.update({
        'logo_url': template.logo.url if template and template.logo else '',
        'seal_url': template.seal.url if template and template.seal else '',
        'signature_url': '',
        'approved_by': '',
    })

    if template.header_html or template.body_html:
        source = '\n'.join(part for part in [template.header_html, template.body_html] if part.strip())
    else:
        source = strip_requester_preview_html(template.document_html)

    rendered_document = render_template_html(source, context)
    return {
        'document_html': rendered_document,
        'header_html': rendered_document,
        'body_html': '',
        'footer_html': '',
        'render_context': context,
    }


def default_template_payload(template_type):
    label = dict(CertificateRequest.CERTIFICATE_TYPES).get(template_type, 'Certificate')
    return {
        'template_name': f'{label} Template',
        'template_type': template_type,
        'header_html': DEFAULT_HEADER_HTML.strip(),
        'body_html': DEFAULT_BODY_HTML.get(template_type, DEFAULT_BODY_HTML['clearance']).strip(),
        'footer_html': DEFAULT_FOOTER_HTML.strip(),
        'document_html': '\n'.join([
            DEFAULT_HEADER_HTML.strip(),
            DEFAULT_BODY_HTML.get(template_type, DEFAULT_BODY_HTML['clearance']).strip(),
            DEFAULT_FOOTER_HTML.strip(),
        ]),
        'is_active': True,
    }


def sanitize_certificate_html(html):
    """
    Keep editor HTML printable while removing active content. Placeholder
    serialization is intentionally preserved here: visual chips become
    Django placeholders such as {{ full_name }} before this function runs.
    """
    cleaned = html or ''
    cleaned = re.sub(r'<\s*(script|style|iframe|object|embed)[^>]*>.*?<\s*/\s*\1\s*>', '', cleaned, flags=re.I | re.S)
    cleaned = re.sub(r'\s+on[a-z]+\s*=\s*(".*?"|\'.*?\'|[^\s>]+)', '', cleaned, flags=re.I | re.S)
    cleaned = re.sub(r'(href|src)\s*=\s*([\'"])\s*javascript:.*?\2', r'\1="#"', cleaned, flags=re.I | re.S)

    def keep_known_placeholder(match):
        name = match.group(1).strip()
        if name in ALLOWED_PLACEHOLDERS:
            return '{{ ' + name + ' }}'
        return ''

    cleaned = re.sub(r'{{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*}}', keep_known_placeholder, cleaned)
    return cleaned
