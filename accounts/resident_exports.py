from django.db.models import Q

from .models import Resident, ResidentExportRequest


AGE_GROUP_CHOICES = [
    ('', 'All age groups'),
    ('minor', 'Children / minors under 18'),
    ('youth', 'Youth residents (15-30)'),
    ('adult', 'Adults (18-59)'),
    ('voter_age', 'Voter-age residents (18+)'),
    ('senior', 'Senior citizens (60+)'),
]

SEX_FILTER_CHOICES = [('', 'All genders')] + Resident.SEX_CHOICES

VALID_AGE_GROUPS = {value for value, _label in AGE_GROUP_CHOICES if value}
VALID_CATEGORIES = {value for value, _label in ResidentExportRequest.CATEGORY_CHOICES}
VALID_PUROKS = {value for value, _label in Resident.PUROK_CHOICES}
VALID_SEXES = {value for value, _label in Resident.SEX_CHOICES}


def normalize_export_filters(data, *, allow_search=False, allow_category=True):
    category = (data.get('category') or 'filtered').strip()
    if not allow_category or category not in VALID_CATEGORIES:
        category = 'filtered'

    filters = {}

    if allow_search:
        search = (data.get('search') or '').strip()
        if search:
            filters['search'] = search

    purok = (data.get('purok') or '').strip()
    if purok in VALID_PUROKS:
        filters['purok'] = purok

    age_group = (data.get('age_group') or '').strip()
    if age_group in VALID_AGE_GROUPS:
        filters['age_group'] = age_group

    sex = (data.get('sex') or '').strip()
    if sex in VALID_SEXES:
        filters['sex'] = sex

    return category, filters


def apply_age_group(queryset, age_group):
    residents = list(queryset)
    if age_group == 'minor':
        ids = [resident.id for resident in residents if resident.age < 18]
        return queryset.filter(id__in=ids)
    if age_group == 'youth':
        ids = [resident.id for resident in residents if 15 <= resident.age <= 30]
        return queryset.filter(id__in=ids)
    if age_group == 'adult':
        ids = [resident.id for resident in residents if 18 <= resident.age <= 59]
        return queryset.filter(id__in=ids)
    if age_group == 'voter_age':
        ids = [resident.id for resident in residents if resident.age >= 18]
        return queryset.filter(id__in=ids)
    if age_group == 'senior':
        ids = [resident.id for resident in residents if resident.age >= 60]
        return queryset.filter(id__in=ids)
    return queryset


def apply_resident_category(queryset, category):
    if category == 'senior':
        return apply_age_group(queryset, 'senior')
    if category == 'youth':
        return apply_age_group(queryset, 'youth')
    if category == 'voter_age':
        return apply_age_group(queryset, 'voter_age')
    if category == 'solo_parent':
        return queryset.filter(is_solo_parent=True)
    if category == 'indigent':
        return queryset.filter(is_indigent=True)
    return queryset


def filtered_residents_from_request(export_request):
    filters = export_request.filters or {}
    queryset = Resident.objects.filter(is_deleted=False)

    search = filters.get('search')
    if search:
        queryset = queryset.filter(
            Q(full_name__icontains=search)
            | Q(resident_id__icontains=search)
            | Q(household_number__icontains=search)
        )

    purok = filters.get('purok')
    if purok in VALID_PUROKS:
        queryset = queryset.filter(purok=purok)

    sex = filters.get('sex')
    if sex in VALID_SEXES:
        queryset = queryset.filter(sex=sex)

    queryset = apply_age_group(queryset, filters.get('age_group'))
    return apply_resident_category(queryset, export_request.category)


def describe_export_request(export_request):
    filters = export_request.filters or {}
    parts = []

    if export_request.category and export_request.category != 'filtered':
        category_label = dict(ResidentExportRequest.CATEGORY_CHOICES).get(
            export_request.category,
            export_request.category,
        )
        parts.append(category_label)

    age_group = filters.get('age_group')
    if age_group:
        parts.append(f'Age group: {dict(AGE_GROUP_CHOICES).get(age_group, age_group)}')

    purok = filters.get('purok')
    if purok:
        parts.append(f'Purok: {dict(Resident.PUROK_CHOICES).get(purok, purok)}')

    sex = filters.get('sex')
    if sex:
        parts.append(f'Gender: {dict(Resident.SEX_CHOICES).get(sex, sex)}')

    if filters.get('search'):
        parts.append('Text search filter applied')

    return '; '.join(parts) if parts else 'All residents'
