from django.urls import path
from . import views

app_name = 'kapitan_portal'

urlpatterns = [
    path('dashboard/', views.kapitan_dashboard, name='dashboard'),
    path('hearing/<int:hearing_id>/', views.hearing_detail, name='hearing_detail'),
]