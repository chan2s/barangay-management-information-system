from django.urls import path
from . import views

app_name = 'staff_module'

urlpatterns = [
    path('dashboard/', views.staff_dashboard, name='staff_dashboard'),
    path('list/', views.staff_list, name='staff_list'),
    path('create/', views.staff_create, name='staff_create'),
    path('edit/<int:staff_id>/', views.staff_edit, name='staff_edit'),
    path('blotters/', views.staff_blotter_list, name='staff_blotter_list'),  # Add this
    path('blotters/<int:blotter_id>/', views.staff_blotter_detail, name='staff_blotter_detail'),  # Add this

]