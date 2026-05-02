from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import CertificateRequest


class CertificateRequestAdmin(admin.ModelAdmin):
    list_display = ['request_id', 'full_name', 'request_type', 'status', 'date_submitted']
    list_filter = ['request_type', 'status', 'date_submitted']
    search_fields = ['request_id', 'full_name', 'contact_number']
    readonly_fields = ['request_id', 'date_submitted', 'age']

    fieldsets = (
        ('Tracking Information', {
            'fields': ('request_id', 'status', 'date_submitted', 'date_processed', 'date_released')
        }),
        ('Personal Information', {
            'fields': ('full_name', 'address', 'contact_number', 'date_of_birth', 'age', 'civil_status', 'gender')
        }),
        ('Certificate Details', {
            'fields': ('request_type', 'purok', 'purpose')
        }),
        ('Health Certification Details', {
            'fields': ('birthplace', 'parents', 'date_first_seen', 'sex'),
            'classes': ('collapse',)
        }),
        ('Processing Information', {
            'fields': ('processed_by', 'remarks'),
            'classes': ('collapse',)
        })
    )


admin.site.register(CertificateRequest, CertificateRequestAdmin)