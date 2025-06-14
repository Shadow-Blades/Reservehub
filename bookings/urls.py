from django.urls import path
from . import views, host_views

app_name = 'bookings'

urlpatterns = [
    # Public views
    path('', views.index_view, name='home'),
    path('venues/', views.venue_list, name='venue_list'),
    path('venues/<int:pk>/', views.venue_detail, name='venue_detail'),
    path('venues/<int:venue_id>/rooms/<int:room_id>/', views.room_detail, name='room_detail'),
    path('bookings/', views.user_bookings, name='user_bookings'),
    path('bookings/<uuid:booking_id>/', views.booking_detail, name='booking_detail'),
    path('add-review/<int:venue_id>/', views.add_review, name='add_review'),
    path('rooms/<int:room_id>/book/', views.BookingCreateView.as_view(), name='booking_create'),
    
    # Host views
    path('host/dashboard/', host_views.host_dashboard, name='host_dashboard'),
    path('host/venues/', host_views.host_venues, name='host_venues'),
    path('host/venues/add/', host_views.venue_create, name='venue_create'),
    path('host/venues/<int:pk>/edit/', host_views.venue_update, name='venue_update'),
    path('host/venues/<int:pk>/delete/', host_views.venue_delete, name='venue_delete'),
    path('host/venues/<int:venue_id>/rooms/add/', host_views.add_room, name='add_room'),
    path('host/venues/<int:venue_id>/rooms/<int:pk>/edit/', host_views.room_update, name='room_update'),
    path('host/venues/<int:venue_id>/rooms/<int:pk>/delete/', host_views.room_delete, name='room_delete'),
    path('host/bookings/', host_views.host_bookings, name='host_bookings'),
    path('host/bookings/<uuid:booking_id>/confirm/', host_views.confirm_booking, name='confirm_booking'),
] 