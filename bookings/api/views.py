from rest_framework import viewsets, permissions, generics, filters, serializers
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from bookings.models import Venue, Room, Booking, Review, TimeSlot, Favorite
from .serializers import (VenueListSerializer, VenueDetailSerializer, RoomSerializer,
                         BookingSerializer, ReviewSerializer, TimeSlotSerializer,
                         FavoriteSerializer)
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Avg, Count, Q
from django.shortcuts import get_object_or_404


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions are only allowed to the owner
        return obj.owner == request.user or obj.user == request.user


class VenueViewSet(viewsets.ModelViewSet):
    """API endpoint for venues"""
    queryset = Venue.objects.all().prefetch_related('amenities', 'images')
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['city', 'state', 'country', 'is_active']
    search_fields = ['name', 'description', 'address', 'city']
    ordering_fields = ['name', 'created_at', 'max_capacity']
    
    def get_queryset(self):
        """Return the appropriate queryset based on request"""
        queryset = Venue.objects.all().prefetch_related('amenities', 'images')
        
        if self.action == 'list':
            queryset = queryset.annotate(average_rating=Avg('reviews__rating'))
            
        # Filter by max capacity if specified
        capacity = self.request.query_params.get('capacity')
        if capacity:
            queryset = queryset.filter(max_capacity__gte=int(capacity))
            
        # Filter by amenities if specified
        amenities = self.request.query_params.getlist('amenities')
        if amenities:
            queryset = queryset.filter(amenities__id__in=amenities).distinct()
        
        # Show only active venues for non-owners
        if self.action == 'list' and not self.request.query_params.get('all'):
            queryset = queryset.filter(is_active=True)
            
        return queryset
    
    def get_serializer_class(self):
        """Return the appropriate serializer based on action"""
        if self.action == 'list':
            return VenueListSerializer
        return VenueDetailSerializer
    
    def perform_create(self, serializer):
        """Set the owner to the current user when creating a venue"""
        serializer.save(owner=self.request.user)


class RoomViewSet(viewsets.ModelViewSet):
    """API endpoint for rooms"""
    queryset = Room.objects.all().prefetch_related('amenities', 'images', 'time_slots')
    serializer_class = RoomSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['venue', 'capacity', 'is_active']
    search_fields = ['name', 'description']
    
    def perform_create(self, serializer):
        """Ensure the user is the owner of the venue when creating a room"""
        venue = serializer.validated_data['venue']
        if venue.owner != self.request.user:
            raise PermissionDenied("You do not have permission to add rooms to this venue.")
        serializer.save()
    
    def perform_update(self, serializer):
        """Ensure the user is the owner of the venue when updating a room"""
        venue = serializer.instance.venue
        if venue.owner != self.request.user:
            raise PermissionDenied("You do not have permission to update rooms for this venue.")
        serializer.save()


class BookingViewSet(viewsets.ModelViewSet):
    """API endpoint for bookings"""
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'room__venue']
    ordering_fields = ['start_time', 'created_at', 'total_price']
    
    def get_queryset(self):
        """Return bookings for the current user or venue owner"""
        user = self.request.user
        
        # If user is checking their own bookings
        if self.request.query_params.get('my_bookings') == 'true':
            return Booking.objects.filter(user=user).select_related('room', 'room__venue')
            
        # If user is a venue owner checking bookings for their venues
        venues_owned = Venue.objects.filter(owner=user)
        if self.request.query_params.get('owned_venues') == 'true' and venues_owned.exists():
            return Booking.objects.filter(room__venue__in=venues_owned).select_related('room', 'room__venue', 'user')
        
        # Default: return user's bookings
        return Booking.objects.filter(user=user).select_related('room', 'room__venue')
    
    def perform_create(self, serializer):
        """Create a booking ensuring availability and calculating price"""
        room = serializer.validated_data['room']
        start_time = serializer.validated_data['start_time']
        end_time = serializer.validated_data['end_time']
        
        # Check if room is available for the requested time
        overlapping_bookings = Booking.objects.filter(
            room=room,
            status__in=['pending', 'confirmed'],
            start_time__lt=end_time,
            end_time__gt=start_time
        ).exists()
        
        if overlapping_bookings:
            raise serializers.ValidationError({'non_field_errors': ['This room is not available for the selected time period.']})
        
        # Calculate total price based on duration and room price
        duration_hours = (end_time - start_time).total_seconds() / 3600
        total_price = float(room.price_per_hour) * duration_hours
        
        serializer.save(user=self.request.user, total_price=total_price)


class ReviewViewSet(viewsets.ModelViewSet):
    """API endpoint for reviews"""
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['venue', 'rating']
    ordering_fields = ['created_at', 'rating']
    
    def get_queryset(self):
        """Return all reviews or filter by venue"""
        venue_id = self.request.query_params.get('venue_id')
        if venue_id:
            return Review.objects.filter(venue_id=venue_id).select_related('user', 'venue')
        return Review.objects.all().select_related('user', 'venue')
    
    def perform_create(self, serializer):
        """Create a review ensuring the user has a completed booking for this venue"""
        venue = serializer.validated_data['venue']
        booking = serializer.validated_data.get('booking')
        
        if booking:
            # Check if booking belongs to user and is completed
            if booking.user != self.request.user:
                raise PermissionDenied("You can only review venues you have booked.")
            
            if booking.status != 'completed':
                raise PermissionDenied("You can only review venues after your booking is completed.")
            
            # Check if booking is for a room in this venue
            if booking.room.venue != venue:
                raise PermissionDenied("The booking must be for this venue.")
        else:
            # If no booking specified, check if user has any completed bookings for this venue
            has_completed_booking = Booking.objects.filter(
                user=self.request.user,
                room__venue=venue,
                status='completed'
            ).exists()
            
            if not has_completed_booking:
                raise PermissionDenied("You can only review venues you have booked and completed.")
        
        serializer.save(user=self.request.user)


class RoomAvailabilityAPIView(generics.RetrieveAPIView):
    """API endpoint to check room availability"""
    queryset = Room.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return get_object_or_404(Room, pk=self.kwargs.get('room_id'))
        
    def get(self, request, room_id):
        """Get available time slots for a room"""
        try:
            room = Room.objects.get(pk=room_id)
        except Room.DoesNotExist:
            return Response({"detail": "Room not found."}, status=404)
        
        # Get date range from query params or use next 7 days
        start_date_str = request.query_params.get('start_date')
        end_date_str = request.query_params.get('end_date')
        
        try:
            if start_date_str:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            else:
                start_date = timezone.now().date()
                
            if end_date_str:
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            else:
                end_date = start_date + timedelta(days=7)
        except ValueError:
            return Response({"detail": "Invalid date format. Use YYYY-MM-DD."}, status=400)
        
        # Get time slots for the room in the date range
        time_slots = TimeSlot.objects.filter(
            room=room,
            start_time__date__gte=start_date,
            start_time__date__lte=end_date,
            is_available=True
        ).order_by('start_time')
        
        # Get existing bookings for the room in the date range
        bookings = Booking.objects.filter(
            room=room,
            status__in=['pending', 'confirmed'],
            start_time__date__gte=start_date,
            start_time__date__lte=end_date
        ).order_by('start_time')
        
        # Serialize the data
        time_slot_data = TimeSlotSerializer(time_slots, many=True).data
        booking_data = BookingSerializer(bookings, many=True).data
        
        return Response({
            'room_id': room.id,
            'room_name': room.name,
            'time_slots': time_slot_data,
            'existing_bookings': booking_data
        })


class FavoriteListCreateAPIView(generics.ListCreateAPIView):
    """API endpoint to list and create favorites"""
    serializer_class = FavoriteSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Return favorites for the current user"""
        return Favorite.objects.filter(user=self.request.user).select_related('venue')


class FavoriteDestroyAPIView(generics.DestroyAPIView):
    """API endpoint to remove a favorite"""
    queryset = Favorite.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Return favorites for the current user"""
        return Favorite.objects.filter(user=self.request.user) 