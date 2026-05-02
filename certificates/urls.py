from django.urls import path
from . import views

app_name = 'certificates'

urlpatterns = [
    path('', views.request_form, name='request_form'),
    path('submit/', views.submit_request, name='submit_request'),
]