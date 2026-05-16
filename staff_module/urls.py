from django.urls import path, include
from . import views

app_name = 'staff_module'

urlpatterns = [
    # Dashboard
    path('dashboard/', views.staff_dashboard, name='staff_dashboard'),
    
    # Blotter Management
    path('blotters/', views.staff_blotter_list, name='staff_blotter_list'),
    path('blotters/<int:blotter_id>/', views.staff_blotter_detail, name='staff_blotter_detail'),
    path('blotters/<int:blotter_id>/schedule/', views.staff_schedule_hearing, name='staff_schedule_hearing'),
    path('blotters/<int:blotter_id>/status/', views.staff_update_status, name='staff_update_status'),
    path('blotters/<int:blotter_id>/evidence/', views.staff_upload_evidence, name='staff_upload_evidence'),
    path('blotters/<int:blotter_id>/summon/', views.staff_generate_summon, name='staff_generate_summon'),
    
    # Pending Approvals
    path('pending-approvals/', views.staff_pending_approvals, name='staff_pending_approvals'),
    path('approve/<int:blotter_id>/', views.staff_approve_blotter, name='staff_approve_blotter'),

    # Hearing Management
    path('hearing/<int:hearing_id>/status/', views.staff_update_hearing_status, name='staff_update_hearing_status'),

    # Staff Management (Admin only)
    path('list/', views.staff_list, name='staff_list'),
    path('create/', views.staff_create, name='staff_create'),
    path('edit/<int:staff_id>/', views.staff_edit, name='staff_edit'),
    path('delete/<int:staff_id>/', views.staff_delete, name='staff_delete'),
    
    # Certificates Module
    path('certificates/', include('certificates.urls')),
    
    # Admin panel
    path('admin-panel/', include('admin_panel.urls')),

    # Announcements - FIXED: Changed announcement_id to pk
    path('announcements/', views.announcement_list, name='announcement_list'),
    path('announcements/create/', views.announcement_create, name='announcement_create'),
    path('announcements/edit/<int:pk>/', views.announcement_edit, name='announcement_edit'),
    path('announcements/delete/<int:pk>/', views.announcement_delete, name='announcement_delete'),
    path('announcements/<int:pk>/toggle/', views.announcement_toggle_status, name='announcement_toggle_status'),
    
    # Appointments
    path('appointments/', views.appointment_list, name='appointment_list'),
    path('appointments/create/', views.appointment_create, name='appointment_create'),
    path('appointments/<int:pk>/', views.appointment_detail, name='appointment_detail'),
    path('appointments/<int:pk>/status/', views.appointment_update_status, name='appointment_update_status'),
    path('appointments/calendar/', views.appointment_calendar, name='appointment_calendar'),
    
    # Reports
    path('reports/', views.reports_dashboard, name='reports_dashboard'),
    path('reports/blotter/', views.blotter_report, name='blotter_report'),
    path('reports/certificate/', views.certificate_report, name='certificate_report'),
    path('reports/hearing/', views.hearing_report, name='hearing_report'),
    path('reports/summary/', views.summary_report, name='summary_report'),
    
    # AJAX endpoints
    path('blotters/<int:blotter_id>/approve-action/', views.staff_approve_blotter_action, name='staff_approve_blotter_action'),
]