from django.urls import path
from . import views

urlpatterns = [
    path('file/', views.file_blotter, name='file_blotter'),
    path('track/', views.track_blotter, name='track_blotter'),
    path('success/', views.blotter_success, name='blotter_success'),
    path('api/blotter-stats/', views.blotter_stats_api, name='blotter_stats_api')
]