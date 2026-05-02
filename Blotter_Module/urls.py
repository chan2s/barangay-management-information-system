from django.urls import path
from . import views

app_name = 'blotter'

urlpatterns = [
    # Public Views - Order matters
    path('verify/', views.choose_verification, name='choose_verification'),
    path('file/', views.file_blotter, name='file_blotter'),
    path('verify-email/', views.blotter_verify_email, name='blotter_verify_email'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),
    path('track/', views.track_blotter, name='track_blotter'),
    path('success/', views.blotter_success, name='blotter_success'),
    path('api/blotter-stats/', views.blotter_stats_api, name='blotter_stats_api'),
    
    # Staff/Admin Views
    path('staff/dashboard/', views.staff_dashboard, name='staff_dashboard'),
    path('staff/blotters/', views.blotter_list, name='blotter_list'),
    path('staff/blotters/<int:blotter_id>/', views.blotter_detail, name='blotter_detail'),
    path('staff/blotters/<int:blotter_id>/status/', views.blotter_update_status, name='blotter_update_status'),
    path('staff/blotters/<int:blotter_id>/schedule/', views.schedule_hearing, name='schedule_hearing'),
    path('staff/blotters/<int:blotter_id>/evidence/', views.upload_evidence, name='upload_evidence'),
    path('staff/blotters/<int:blotter_id>/comment/', views.add_comment, name='add_comment'),
    path('staff/blotters/<int:blotter_id>/pdf/', views.download_pdf, name='download_pdf'),
    path('staff/notifications/<int:notification_id>/read/', views.mark_notification_read, name='mark_notification_read'),
    path('staff/pending-id-verifications/', views.pending_id_verifications, name='pending_id_verifications'),
    path('staff/verify-id/<int:blotter_id>/', views.verify_id, name='verify_id'),
    # path('staff/pending-approvals/', views.pending_approvals, name='pending_approvals'),
    # path('staff/approve/<int:blotter_id>/', views.approve_blotter, name='approve_blotter'),
]