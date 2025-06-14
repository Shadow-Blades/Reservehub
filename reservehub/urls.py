"""
URL configuration for reservehub project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

from bookings.views import index_view
from bookings.admin_views import admin_dashboard, toggle_venue_status, remove_venue

urlpatterns = [
    # Django admin
    path('admin/', admin.site.urls),
    
    # Main pages
    path('', index_view, name='home'),
    path('home/', index_view, name='home_page'),
    
    # Admin dashboard
    path('admin-dashboard/', admin_dashboard, name='admin_dashboard'),
    path('admin/venues/<int:venue_id>/toggle-status/', toggle_venue_status, name='toggle_venue_status'),
    path('admin/venues/<int:venue_id>/remove/', remove_venue, name='remove_venue'),
    
    # App URLs
    path('bookings/', include('bookings.urls')),
    path('accounts/', include('accounts.urls')),
    path('payments/', include('payments.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
