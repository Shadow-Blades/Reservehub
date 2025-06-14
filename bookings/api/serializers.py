from rest_framework import serializers
from bookings.models import Venue, Room, Booking, Review, Favorite, VenueImage, RoomImage, Amenity, TimeSlot
from django.contrib.auth import get_user_model

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Serializer for user data"""
    
    class Meta:
        model = User
        fields = ['id', 'email', 'username']
        

class AmenitySerializer(serializers.ModelSerializer):
    """Serializer for amenities"""
    
    class Meta:
        model = Amenity
        fields = ['id', 'name', 'icon', 'description']


class VenueImageSerializer(serializers.ModelSerializer):
    """Serializer for venue images"""
    
    class Meta:
        model = VenueImage
        fields = ['id', 'image', 'caption', 'is_primary']


class RoomImageSerializer(serializers.ModelSerializer):
    """Serializer for room images"""
    
    class Meta:
        model = RoomImage
        fields = ['id', 'image', 'caption', 'is_primary']


class TimeSlotSerializer(serializers.ModelSerializer):
    """Serializer for time slots"""
    
    class Meta:
        model = TimeSlot
        fields = ['id', 'start_time', 'end_time', 'is_available']


class RoomSerializer(serializers.ModelSerializer):
    """Serializer for rooms"""
    amenities = AmenitySerializer(many=True, read_only=True)
    images = RoomImageSerializer(many=True, read_only=True)
    time_slots = TimeSlotSerializer(many=True, read_only=True)
    
    class Meta:
        model = Room
        fields = ['id', 'venue', 'name', 'description', 'capacity', 'size_sqft',
                 'price_per_hour', 'amenities', 'images', 'time_slots', 'is_active']


class VenueListSerializer(serializers.ModelSerializer):
    """Serializer for venue list view"""
    primary_image = serializers.SerializerMethodField()
    average_rating = serializers.FloatField(read_only=True)
    
    class Meta:
        model = Venue
        fields = ['id', 'name', 'city', 'address', 'max_capacity', 'primary_image', 'average_rating']
    
    def get_primary_image(self, obj):
        """Get the primary image URL"""
        primary_image = obj.images.filter(is_primary=True).first()
        if primary_image:
            return self.context['request'].build_absolute_uri(primary_image.image.url)
        return None


class VenueDetailSerializer(serializers.ModelSerializer):
    """Serializer for venue detail view"""
    owner = UserSerializer(read_only=True)
    amenities = AmenitySerializer(many=True, read_only=True)
    images = VenueImageSerializer(many=True, read_only=True)
    rooms = RoomSerializer(many=True, read_only=True)
    average_rating = serializers.FloatField(read_only=True)
    
    class Meta:
        model = Venue
        fields = ['id', 'owner', 'name', 'description', 'address', 'city', 'state',
                 'postal_code', 'country', 'latitude', 'longitude', 'phone', 'email',
                 'website', 'max_capacity', 'amenities', 'images', 'rooms',
                 'average_rating', 'is_active']


class BookingSerializer(serializers.ModelSerializer):
    """Serializer for bookings"""
    user = UserSerializer(read_only=True)
    room_name = serializers.CharField(source='room.name', read_only=True)
    venue_name = serializers.CharField(source='room.venue.name', read_only=True)
    
    class Meta:
        model = Booking
        fields = ['booking_id', 'user', 'room', 'room_name', 'venue_name', 'start_time',
                 'end_time', 'num_guests', 'special_requests', 'status', 'total_price',
                 'created_at', 'updated_at']
        read_only_fields = ['booking_id', 'total_price', 'created_at', 'updated_at']


class ReviewSerializer(serializers.ModelSerializer):
    """Serializer for reviews"""
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Review
        fields = ['id', 'user', 'venue', 'booking', 'rating', 'comment', 'created_at']
        read_only_fields = ['created_at']


class FavoriteSerializer(serializers.ModelSerializer):
    """Serializer for favorites"""
    venue = VenueListSerializer(read_only=True)
    venue_id = serializers.PrimaryKeyRelatedField(
        queryset=Venue.objects.all(),
        write_only=True,
        source='venue'
    )
    
    class Meta:
        model = Favorite
        fields = ['id', 'user', 'venue', 'venue_id', 'created_at']
        read_only_fields = ['user', 'created_at']
    
    def create(self, validated_data):
        """Create a new favorite"""
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data) 