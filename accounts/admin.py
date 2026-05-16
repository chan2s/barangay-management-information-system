from django.contrib import admin
from .models import Resident


@admin.register(Resident)
class ResidentAdmin(admin.ModelAdmin):
    list_display = ('resident_id', 'full_name', 'birthdate', 'age', 'sex', 'voter_status')
    search_fields = ('resident_id', 'full_name', 'contact_number', 'email')
    list_filter = ('sex', 'civil_status', 'voter_status')
