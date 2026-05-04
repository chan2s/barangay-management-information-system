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
]