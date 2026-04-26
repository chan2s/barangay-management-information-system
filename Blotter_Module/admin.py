from django.contrib import admin
from .models import Blotter, Schedule, BlotterAuditLog, Notification


class ScheduleInline(admin.TabularInline):
    model = Schedule
    extra = 0
    readonly_fields = ('created_at', 'created_by')


class AuditLogInline(admin.TabularInline):
    model = BlotterAuditLog
    extra = 0
    readonly_fields = ('action', 'old_value', 'new_value', 'performed_by', 'timestamp')
    can_delete = False


@admin.register(Blotter)
class BlotterAdmin(admin.ModelAdmin):
    list_display = ('blotter_number', 'complainant_name', 'respondent_name', 'incident_type', 'status', 'created_at')
    list_filter = ('status', 'incident_type', 'created_at')
    search_fields = ('blotter_number', 'complainant_name', 'respondent_name')
    readonly_fields = ('blotter_number', 'created_at', 'updated_at', 'created_by')
    inlines = [ScheduleInline, AuditLogInline]

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ('blotter', 'hearing_date', 'is_completed', 'created_at')
    list_filter = ('is_completed', 'hearing_date')


@admin.register(BlotterAuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('blotter', 'action', 'performed_by', 'timestamp')
    readonly_fields = ('blotter', 'action', 'old_value', 'new_value', 'performed_by', 'timestamp')


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'message', 'is_read', 'created_at')
    list_filter = ('is_read',)