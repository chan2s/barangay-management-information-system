from django.urls import path
from . import views

app_name = 'admin_panel'

urlpatterns = [
    path('dashboard/', views.admin_dashboard, name='dashboard'),
    path('users/', views.user_list, name='user_list'),
    path('users/create/', views.user_create, name='user_create'),
    path('users/edit/<int:user_id>/', views.user_edit, name='user_edit'),
    path('users/delete/<int:user_id>/', views.user_delete, name='user_delete'),
    path('residents/', views.resident_list, name='resident_list'),
    path('residents/create/', views.resident_create, name='resident_create'),
    path('residents/edit/<int:resident_id>/', views.resident_edit, name='resident_edit'),
    path('residents/delete/<int:resident_id>/', views.resident_delete, name='resident_delete'),
    path('residents/export/request/', views.resident_export_request, name='resident_export_request'),
    path('residents/export/review/<int:request_id>/', views.resident_export_review, name='resident_export_review'),
    path('residents/export/download/<int:request_id>/', views.resident_export_download, name='resident_export_download'),
    path('settings/', views.system_settings, name='system_settings'),
    path('audit-log/', views.audit_log, name='audit_log'),
    path('audit-log/export/', views.export_audit_log, name='export_audit_log'),
    path('backup/', views.backup_database, name='backup_database'),
    path('health/', views.system_health, name='system_health'),
]
