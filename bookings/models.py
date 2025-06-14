from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
import uuid


class Amenity(models.Model):
    """Model for amenities that can be included with venues/rooms"""
    name = models.CharField(_('Name'), max_length=100)
    icon = models.CharField(_('Icon Class'), max_length=50, help_text="Font Awesome icon class", blank=True)
    description = models.TextField(_('Description'), blank=True, null=True)

    class Meta:
        verbose_name_plural = "Amenities"

    def __str__(self):
        return self.name


class VenueCategory(models.Model):
    """Categories for venues (e.g. Conference Hall, Restaurant, Hotel)"""
    name = models.CharField(_('Name'), max_length=100)
    description = models.TextField(_('Description'), blank=True, null=True)
    
    class Meta:
        verbose_name_plural = "Venue Categories"
        
    def __str__(self):
        return self.name


class Venue(models.Model):
    """Model representing a venue available for booking"""
    INDIA_STATES = [
        ('AN', 'Andaman and Nicobar Islands'),
        ('AP', 'Andhra Pradesh'),
        ('AR', 'Arunachal Pradesh'),
        ('AS', 'Assam'),
        ('BR', 'Bihar'),
        ('CH', 'Chandigarh'),
        ('CT', 'Chhattisgarh'),
        ('DN', 'Dadra and Nagar Haveli'),
        ('DD', 'Daman and Diu'),
        ('DL', 'Delhi'),
        ('GA', 'Goa'),
        ('GJ', 'Gujarat'),
        ('HR', 'Haryana'),
        ('HP', 'Himachal Pradesh'),
        ('JK', 'Jammu and Kashmir'),
        ('JH', 'Jharkhand'),
        ('KA', 'Karnataka'),
        ('KL', 'Kerala'),
        ('LA', 'Ladakh'),
        ('LD', 'Lakshadweep'),
        ('MP', 'Madhya Pradesh'),
        ('MH', 'Maharashtra'),
        ('MN', 'Manipur'),
        ('ML', 'Meghalaya'),
        ('MZ', 'Mizoram'),
        ('NL', 'Nagaland'),
        ('OR', 'Odisha'),
        ('PY', 'Puducherry'),
        ('PB', 'Punjab'),
        ('RJ', 'Rajasthan'),
        ('SK', 'Sikkim'),
        ('TN', 'Tamil Nadu'),
        ('TG', 'Telangana'),
        ('TR', 'Tripura'),
        ('UP', 'Uttar Pradesh'),
        ('UK', 'Uttarakhand'),
        ('WB', 'West Bengal'),
    ]
    
    VENUE_TYPES = [
        ('hotel', 'Hotel'),
        ('restaurant', 'Restaurant'),
        ('event_space', 'Event Space'),
        ('conference', 'Conference Center'),
        ('banquet', 'Banquet Hall'),
        ('cafe', 'Café'),
    ]
    
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='owned_venues')
    name = models.CharField(_('Venue Name'), max_length=255)
    category = models.ForeignKey(VenueCategory, on_delete=models.SET_NULL, null=True, related_name='venues')
    venue_type = models.CharField(_('Venue Type'), max_length=20, choices=VENUE_TYPES, default='event_space')
    description = models.TextField(_('Description'))
    address = models.CharField(_('Address'), max_length=255)
    city = models.CharField(_('City'), max_length=100)
    state = models.CharField(_('State'), max_length=100, choices=INDIA_STATES)
    postal_code = models.CharField(_('PIN Code'), max_length=20)
    country = models.CharField(_('Country'), max_length=100, default="India")
    latitude = models.DecimalField(_('Latitude'), max_digits=9, decimal_places=6, blank=True, null=True)
    longitude = models.DecimalField(_('Longitude'), max_digits=9, decimal_places=6, blank=True, null=True)
    phone = models.CharField(_('Contact Phone'), max_length=20)
    email = models.EmailField(_('Contact Email'))
    website = models.URLField(_('Website'), blank=True, null=True)
    max_capacity = models.PositiveIntegerField(_('Maximum Capacity'))
    amenities = models.ManyToManyField(Amenity, blank=True, related_name='venues')
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)
    is_active = models.BooleanField(_('Is Active'), default=True)
    is_featured = models.BooleanField(_('Is Featured'), default=False)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    @property
    def full_address(self):
        """Returns the venue's full address"""
        return f"{self.address}, {self.city}, {self.state} {self.postal_code}, {self.country}"
    
    @property
    def average_rating(self):
        """Calculate average rating from reviews"""
        reviews = self.reviews.all()
        if reviews.count() > 0:
            return sum(review.rating for review in reviews) / reviews.count()
        return 0


class VenueImage(models.Model):
    """Images for venues"""
    venue = models.ForeignKey(Venue, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(_('Image'), upload_to='venue_images/')
    caption = models.CharField(_('Caption'), max_length=255, blank=True, null=True)
    is_primary = models.BooleanField(_('Primary Image'), default=False)
    uploaded_at = models.DateTimeField(_('Uploaded At'), auto_now_add=True)
    
    class Meta:
        ordering = ['-is_primary', 'uploaded_at']
    
    def __str__(self):
        return f"{self.venue.name} - {self.caption if self.caption else 'Image'}"


class Room(models.Model):
    """Individual rooms/spaces within a venue that can be booked separately"""
    venue = models.ForeignKey(Venue, on_delete=models.CASCADE, related_name='rooms')
    name = models.CharField(_('Room Name'), max_length=255)
    description = models.TextField(_('Description'))
    capacity = models.PositiveIntegerField(_('Capacity'))
    size_sqft = models.PositiveIntegerField(_('Size (sq ft)'), blank=True, null=True)
    price_per_hour = models.DecimalField(_('Price per Hour (₹)'), max_digits=10, decimal_places=2)
    amenities = models.ManyToManyField(Amenity, blank=True, related_name='rooms')
    is_active = models.BooleanField(_('Is Active'), default=True)
    
    def __str__(self):
        return f"{self.venue.name} - {self.name}"


class RoomImage(models.Model):
    """Images for rooms"""
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(_('Image'), upload_to='room_images/')
    caption = models.CharField(_('Caption'), max_length=255, blank=True, null=True)
    is_primary = models.BooleanField(_('Primary Image'), default=False)
    uploaded_at = models.DateTimeField(_('Uploaded At'), auto_now_add=True)
    
    class Meta:
        ordering = ['-is_primary', 'uploaded_at']
    
    def __str__(self):
        return f"{self.room.name} - {self.caption if self.caption else 'Image'}"


class TimeSlot(models.Model):
    """Available time slots for venues/rooms"""
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='time_slots')
    start_time = models.DateTimeField(_('Start Time'))
    end_time = models.DateTimeField(_('End Time'))
    is_available = models.BooleanField(_('Is Available'), default=True)
    
    class Meta:
        ordering = ['start_time']
    
    def __str__(self):
        return f"{self.room.name}: {self.start_time.strftime('%Y-%m-%d %H:%M')} - {self.end_time.strftime('%H:%M')}"


class Booking(models.Model):
    """Model for bookings"""
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    )
    
    booking_id = models.UUIDField(_('Booking ID'), default=uuid.uuid4, editable=False, unique=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bookings')
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='bookings')
    start_time = models.DateTimeField(_('Start Time'))
    end_time = models.DateTimeField(_('End Time'))
    num_guests = models.PositiveIntegerField(_('Number of Guests'))
    special_requests = models.TextField(_('Special Requests'), blank=True, null=True)
    status = models.CharField(_('Status'), max_length=20, choices=STATUS_CHOICES, default='pending')
    total_price = models.DecimalField(_('Total Price'), max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return f"Booking {self.booking_id} - {self.user.email}"
    
    @property
    def duration_hours(self):
        """Calculate duration in hours"""
        delta = self.end_time - self.start_time
        return delta.total_seconds() / 3600
    
    def calculate_price(self):
        """Calculate the total price based on duration and room price"""
        hours = self.duration_hours
        return float(self.room.price_per_hour) * hours
    
    def save(self, *args, **kwargs):
        """Override save method to calculate total price"""
        if not self.total_price:
            self.total_price = self.calculate_price()
        super().save(*args, **kwargs)
        
    @property
    def reviewed(self):
        """Check if the booking has a review"""
        return hasattr(self, 'review') and self.review is not None


class Review(models.Model):
    """Reviews for venues after booking"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reviews')
    venue = models.ForeignKey(Venue, on_delete=models.CASCADE, related_name='reviews')
    booking = models.OneToOneField(Booking, on_delete=models.SET_NULL, null=True, blank=True, related_name='review')
    rating = models.PositiveSmallIntegerField(_('Rating'), validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField(_('Comment'))
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['user', 'booking']
        
    def __str__(self):
        return f"{self.venue.name} - {self.rating} stars by {self.user.email}"


class Favorite(models.Model):
    """User's favorite venues"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='favorites')
    venue = models.ForeignKey(Venue, on_delete=models.CASCADE, related_name='favorited_by')
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'venue']
        
    def __str__(self):
        return f"{self.user.email} - {self.venue.name}"
