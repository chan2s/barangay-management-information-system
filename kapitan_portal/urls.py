from django.urls import path
from . import views

app_name = 'kapitan_portal'

urlpatterns = [
    # Dashboard
    path('dashboard/', views.kapitan_dashboard, name='dashboard'),
    
    # Appointment management (NEW)
    path('appointments/', views.appointment_list, name='appointment_list'),
    path('appointments/<int:appt_id>/', views.appointment_detail, name='appointment_detail'),
    path('appointments/approve/<int:appt_id>/', views.appointment_approve, name='appointment_approve'),
    path('appointments/reject/<int:appt_id>/', views.appointment_reject, name='appointment_reject'),
    path('for-approval/appointments/', views.for_approval_appointments, name='for_approval_appointments'),
    
    # Hearing management
    path('hearings/', views.hearing_list, name='hearing_list'),
    path('hearings/<int:hearing_id>/', views.hearing_detail, name='hearing_detail'),
    
    # Certificate management
    path('certificates/', views.certificate_list, name='certificate_list'),
    path('certificates/<int:cert_id>/', views.certificate_detail, name='certificate_detail'),
    path('certificates/approve/<int:cert_id>/', views.certificate_approve, name='certificate_approve'),
    path('certificates/reject/<int:cert_id>/', views.certificate_reject, name='certificate_reject'),
    path('for-approval/', views.for_approval_list, name='for_approval_list'),
]