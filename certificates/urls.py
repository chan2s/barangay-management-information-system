from django.urls import path
from . import views

app_name = 'certificates'

urlpatterns = [
    path('', views.request_form, name='request_form'),
    path('submit/', views.submit_request, name='submit_request'),
    path('list/', views.request_list, name='request_list'),
    path('view/<int:request_id>/', views.view_request, name='view_request'),
    path('process/<int:request_id>/', views.process_request, name='process_request'),
    path('release/<int:request_id>/', views.release_request, name='release_request'),
    path('track/', views.track_request, name='track_request'),
    path('generate/<int:request_id>/', views.generate_certificate, name='generate_certificate'),
    path('generate/clearance/<int:request_id>/', views.generate_clearance, name='generate_clearance'),
    path('generate/residency/<int:request_id>/', views.generate_residency, name='generate_residency'),
    path('generate/indigency/<int:request_id>/', views.generate_indigency, name='generate_indigency'),
    path('generate-id/<int:request_id>/', views.generate_barangay_id, name='generate_barangay_id'),
    
    # Kapitan approval URLs
    path('for-approval/', views.for_approval_list, name='for_approval_list'),
    path('kapitan-approve/<int:request_id>/', views.kapitan_approve_request, name='kapitan_approve_request'),
    path('kapitan-reject/<int:request_id>/', views.kapitan_reject_request, name='kapitan_reject_request'),
]