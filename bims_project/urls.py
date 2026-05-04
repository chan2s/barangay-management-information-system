"""
URL configuration for bims_project project.
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', TemplateView.as_view(template_name='dashboard.html'), name='home'),
    path('blotter/', include('Blotter_Module.urls')),
    path('accounts/', include('accounts.urls')),
    path('staff/', include('staff_module.urls')),
    path('certificates/', include('certificates.urls')),
    path('kapitan/', include('kapitan_portal.urls')),
    path('admin-panel/', include('admin_panel.urls')),


]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)