from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'api'

router = DefaultRouter()
router.register('venues', views.VenueViewSet)
router.register('rooms', views.RoomViewSet)
router.register('bookings', views.BookingViewSet)
router.register('reviews', views.ReviewViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('availability/<int:room_id>/', views.RoomAvailabilityAPIView.as_view(), name='room_availability'),
    path('favorites/', views.FavoriteListCreateAPIView.as_view(), name='favorite-list-create'),
    path('favorites/<int:pk>/', views.FavoriteDestroyAPIView.as_view(), name='favorite-destroy'),
] 