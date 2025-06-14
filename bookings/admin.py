from django.contrib import admin
from .models import (Amenity, VenueCategory, Venue, VenueImage, Room, RoomImage, 
                     TimeSlot, Booking, Review, Favorite)


@admin.register(Amenity)
class AmenityAdmin(admin.ModelAdmin):
    list_display = ['name', 'icon']
    search_fields = ['name', 'description']


@admin.register(VenueCategory)
class VenueCategoryAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name', 'description']


class VenueImageInline(admin.TabularInline):
    model = VenueImage
    extra = 1


class RoomInline(admin.TabularInline):
    model = Room
    extra = 1
    show_change_link = True


@admin.register(Venue)
class VenueAdmin(admin.ModelAdmin):
    list_display = ['name', 'owner', 'city', 'max_capacity', 'is_active']
    list_filter = ['is_active', 'city', 'state', 'country']
    search_fields = ['name', 'description', 'address', 'city']
    inlines = [VenueImageInline, RoomInline]
    fieldsets = (
        (None, {
            'fields': ('owner', 'name', 'category', 'description')
        }),
        ('Location', {
            'fields': ('address', 'city', 'state', 'postal_code', 'country', 'latitude', 'longitude')
        }),
        ('Contact', {
            'fields': ('phone', 'email', 'website')
        }),
        ('Details', {
            'fields': ('max_capacity', 'amenities', 'is_active')
        }),
    )


class RoomImageInline(admin.TabularInline):
    model = RoomImage
    extra = 1


class TimeSlotInline(admin.TabularInline):
    model = TimeSlot
    extra = 1


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ['name', 'venue', 'capacity', 'price_per_hour', 'is_active']
    list_filter = ['is_active', 'venue']
    search_fields = ['name', 'description', 'venue__name']
    inlines = [RoomImageInline, TimeSlotInline]


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ['booking_id', 'user', 'room', 'start_time', 'end_time', 'status', 'total_price']
    list_filter = ['status', 'start_time']
    search_fields = ['booking_id', 'user__email', 'user__username', 'room__name', 'room__venue__name']
    readonly_fields = ['booking_id', 'total_price']
    fieldsets = (
        (None, {
            'fields': ('booking_id', 'user', 'room')
        }),
        ('Booking Details', {
            'fields': ('start_time', 'end_time', 'num_guests', 'special_requests', 'status', 'total_price')
        }),
    )


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['user', 'venue', 'rating', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['user__email', 'venue__name', 'comment']


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ['user', 'venue', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__email', 'venue__name']
