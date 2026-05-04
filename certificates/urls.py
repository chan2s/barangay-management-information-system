from django.urls import path
from . import views

app_name = 'certificates'

urlpatterns = [
    path('', views.request_form, name='request_form'),
    path('submit/', views.submit_request, name='submit_request'),
    path('list/', views.request_list, name='request_list'),
    path('view/<int:request_id>/', views.view_request, name='view_request'),
    path('approve/<int:request_id>/', views.approve_request, name='approve_request'),
    path('reject/<int:request_id>/', views.reject_request, name='reject_request'),
    path('released/<int:request_id>/', views.mark_as_released, name='mark_as_released'),
    path('track/', views.track_request, name='track_request'),
    path('generate/<int:request_id>/', views.generate_certificate, name='generate_certificate'),  # ADD THIS
    
    path('generate/clearance/<int:request_id>/', views.generate_clearance, name='generate_clearance'),
    path('generate/residency/<int:request_id>/', views.generate_residency, name='generate_residency'),
    path('generate/indigency/<int:request_id>/', views.generate_indigency, name='generate_indigency'),
    path('generate/barangay-id/<int:request_id>/', views.generate_barangay_id, name='generate_barangay_id'),
]   