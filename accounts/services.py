from difflib import SequenceMatcher

from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from django.db.models import Q


def normalize_name(value):
    return ' '.join((value or '').strip().lower().split())


def find_possible_resident_duplicates(resident_data, exclude_pk=None):
    from .models import Resident

    full_name = normalize_name(resident_data.get('full_name'))
    birthdate = resident_data.get('birthdate')
    contact_number = (resident_data.get('contact_number') or '').strip()
    email = (resident_data.get('email') or '').strip().lower()
    resident_id = (resident_data.get('resident_id') or '').strip()
    national_id_hash = (resident_data.get('national_id_hash') or '').strip()
    household_number = (resident_data.get('household_number') or '').strip()
    address = (resident_data.get('address') or '').strip()

    query = Q()
    if birthdate and full_name:
        query |= Q(full_name__iexact=resident_data.get('full_name'), birthdate=birthdate)
    if contact_number:
        query |= Q(contact_number=contact_number)
    if email:
        query |= Q(email__iexact=email)
    if resident_id:
        query |= Q(resident_id__iexact=resident_id)
    if national_id_hash:
        query |= Q(national_id_hash=national_id_hash)
    if household_number and address:
        query |= Q(household_number__iexact=household_number, address__iexact=address)

    candidates = Resident.objects.none()
    if query:
        candidates = Resident.objects.filter(query)
        if exclude_pk:
            candidates = candidates.exclude(pk=exclude_pk)

    fuzzy_matches = []
    if full_name:
        fuzzy_pool = Resident.objects.filter(is_deleted=False)
        if exclude_pk:
            fuzzy_pool = fuzzy_pool.exclude(pk=exclude_pk)
        if birthdate:
            fuzzy_pool = fuzzy_pool.filter(birthdate=birthdate)
        for resident in fuzzy_pool[:200]:
            score = SequenceMatcher(None, full_name, normalize_name(resident.full_name)).ratio()
            if score >= 0.86:
                fuzzy_matches.append(resident.pk)

    fuzzy_queryset = Resident.objects.filter(pk__in=fuzzy_matches)
    return (candidates | fuzzy_queryset).distinct()


def user_account_exists(email=None, username=None):
    query = Q()
    if email:
        query |= Q(email__iexact=email.strip())
    if username:
        query |= Q(username__iexact=username.strip())
    return User.objects.filter(query).exists() if query else False


def fingerprint_sensitive_value(value):
    value = ''.join(ch for ch in (value or '') if ch.isalnum())
    return make_password(value, salt='bims-resident-id') if value else ''
