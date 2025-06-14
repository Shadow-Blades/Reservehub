from django.urls import path
from . import admin_views

# Admin URL patterns
urlpatterns = [
    # Dashboard
    path('', admin_views.admin_dashboard, name='admin_dashboard'),
    
    # Venues
    path('venues/', admin_views.admin_venues, name='admin_venues'),
    path('venues/add/', admin_views.admin_venues_add, name='admin_venues_add'),
    path('venues/<int:pk>/', admin_views.admin_venues_detail, name='admin_venues_detail'),
    path('venues/<int:pk>/edit/', admin_views.admin_venues_edit, name='admin_venues_edit'),
    path('venues/<int:pk>/delete/', admin_views.admin_venues_delete, name='admin_venues_delete'),
    
    # Rooms
    path('rooms/', admin_views.admin_rooms, name='admin_rooms'),
    path('rooms/add/', admin_views.admin_rooms_add, name='admin_rooms_add'),
    
    # Categories
    path('categories/', admin_views.admin_categories, name='admin_categories'),
    
    # Amenities
    path('amenities/', admin_views.admin_amenities, name='admin_amenities'),
    
    # Bookings
    path('bookings/', admin_views.admin_bookings, name='admin_bookings'),
    
    # Reviews
    path('reviews/', admin_views.admin_reviews, name='admin_reviews'),
    
    # Users
    path('users/', admin_views.admin_users, name='admin_users'),
    
    # Settings
    path('settings/', admin_views.admin_settings, name='admin_settings'),
] 