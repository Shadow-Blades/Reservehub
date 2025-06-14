from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Sum, Count, Avg
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib import messages
import json
from datetime import datetime, timedelta
from decimal import Decimal

from .models import Venue, Booking, Room, Review
from .forms import VenueForm, RoomForm
from payments.models import PaymentDistribution, Transaction

@login_required
def host_dashboard(request):
    """
    Host dashboard view showing venue statistics and bookings for the logged in host.
    """
    # Check if user is a host
    if request.user.user_type != 'host':
        return redirect('home')
    
    # Get venues owned by this host
    venues = Venue.objects.filter(owner=request.user)
    venue_ids = venues.values_list('id', flat=True)
    
    # Calculate statistics
    rooms = Room.objects.filter(venue__in=venue_ids)
    bookings = Booking.objects.filter(room__venue__in=venue_ids)
    total_bookings = bookings.count()
    
    # Get earnings from payment distributions (90% of booking revenue)
    owner_earnings = PaymentDistribution.objects.filter(
        owner=request.user
    ).aggregate(total=Sum('owner_amount'))['total'] or 0
    
    # Get pending earnings (not yet paid to owner)
    pending_earnings = PaymentDistribution.objects.filter(
        owner=request.user,
        is_paid_to_owner=False
    ).aggregate(total=Sum('owner_amount'))['total'] or 0
    
    # Get total bookings revenue for comparison
    total_booking_revenue = bookings.filter(status__in=['confirmed', 'completed']).aggregate(
        total=Sum('total_price'))['total'] or 0
    
    active_venues = venues.filter(is_active=True).count()
    
    # Calculate average rating across all venues
    reviews = Review.objects.filter(venue__in=venue_ids)
    total_reviews = reviews.count()
    avg_rating = reviews.aggregate(avg=Avg('rating'))['avg'] or 0
    
    # Add room count to each venue
    for venue in venues:
        venue.room_count = Room.objects.filter(venue=venue).count()
    
    # Get recent bookings with status colors
    recent_bookings = bookings.select_related('room__venue', 'user').order_by('-created_at')[:10]
    for booking in recent_bookings:
        # Add status color for badge display
        if booking.status == 'pending':
            booking.status_color = 'warning'
        elif booking.status == 'confirmed':
            booking.status_color = 'success'
        elif booking.status == 'cancelled':
            booking.status_color = 'danger'
        elif booking.status == 'completed':
            booking.status_color = 'info'
    
    # Get recent earnings
    recent_earnings = PaymentDistribution.objects.filter(
        owner=request.user
    ).select_related(
        'transaction', 'transaction__booking', 'transaction__booking__room__venue'
    ).order_by('-created_at')[:5]
    
    # Generate monthly revenue data for chart (last 6 months)
    monthly_revenue = {}
    labels = []
    data = []
    owner_data = []
    
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=180)  # Last 6 months
    
    # Generate monthly revenue data
    for i in range(6):
        month_start = (end_date - timedelta(days=30 * i))
        month_end = (end_date - timedelta(days=30 * (i-1))) if i > 0 else end_date
        
        month_name = month_start.strftime('%b')
        labels.insert(0, month_name)
        
        # Total booking revenue
        month_revenue = bookings.filter(
            status__in=['confirmed', 'completed'],
            start_time__date__gte=month_start,
            start_time__date__lte=month_end
        ).aggregate(Sum('total_price'))['total_price__sum'] or 0
        
        # Convert Decimal to float for JSON serialization
        if isinstance(month_revenue, Decimal):
            month_revenue = float(month_revenue)
        
        data.insert(0, month_revenue)
        
        # Owner's actual earnings (90%)
        month_owner_earnings = PaymentDistribution.objects.filter(
            owner=request.user,
            transaction__created_at__date__gte=month_start,
            transaction__created_at__date__lte=month_end
        ).aggregate(Sum('owner_amount'))['owner_amount__sum'] or 0
        
        if isinstance(month_owner_earnings, Decimal):
            month_owner_earnings = float(month_owner_earnings)
            
        owner_data.insert(0, month_owner_earnings)
    
    monthly_revenue_data = {
        'labels': labels,
        'total_data': data,
        'owner_data': owner_data
    }
    
    # Generate venue popularity data (bookings per venue)
    venue_popularity = {}
    venue_labels = []
    venue_data = []
    
    # Get top venues by booking count
    top_venues = Venue.objects.filter(id__in=venue_ids).annotate(
        booking_count=Count('rooms__bookings')
    ).order_by('-booking_count')[:8]  # Limit to 8 venues for chart readability
    
    for venue in top_venues:
        venue_labels.append(venue.name)
        venue_data.append(venue.booking_count)
    
    venue_popularity_data = {
        'labels': venue_labels,
        'data': venue_data
    }
    
    # Convert Decimal values to float for JSON serialization
    if isinstance(owner_earnings, Decimal):
        owner_earnings = float(owner_earnings)
    if isinstance(pending_earnings, Decimal):
        pending_earnings = float(pending_earnings)
    if isinstance(total_booking_revenue, Decimal):
        total_booking_revenue = float(total_booking_revenue)
    if isinstance(avg_rating, Decimal):
        avg_rating = float(avg_rating)
    
    context = {
        'total_bookings': total_bookings,
        'owner_earnings': owner_earnings,
        'pending_earnings': pending_earnings,
        'total_booking_revenue': total_booking_revenue,
        'active_venues': active_venues,
        'avg_rating': avg_rating,
        'total_reviews': total_reviews,
        'recent_bookings': recent_bookings,
        'recent_earnings': recent_earnings,
        'venues': venues,
        'monthly_revenue_data': json.dumps(monthly_revenue_data),
        'venue_popularity_data': json.dumps(venue_popularity_data),
    }
    
    return render(request, 'bookings/host_dashboard.html', context)

@login_required
def host_venues(request):
    """
    View for a host to manage their venues.
    """
    # Check if user is a host
    if request.user.user_type != 'host':
        return redirect('home')
    
    # Get venues owned by this host
    venues = Venue.objects.filter(owner=request.user)
    
    # Add stats to each venue
    for venue in venues:
        venue.room_count = Room.objects.filter(venue=venue).count()
        venue.booking_count = Booking.objects.filter(room__venue=venue).count()
        venue.revenue = Booking.objects.filter(
            room__venue=venue, 
            status__in=['confirmed', 'completed']
        ).aggregate(Sum('total_price'))['total_price__sum'] or 0
        venue.rating = Review.objects.filter(venue=venue).aggregate(Avg('rating'))['rating__avg'] or 0
    
    context = {
        'venues': venues
    }
    
    return render(request, 'bookings/host_venues.html', context)

@login_required
def host_bookings(request):
    """
    View for a host to manage their bookings.
    """
    # Check if user is a host
    if request.user.user_type != 'host':
        return redirect('home')
    
    # Get venues owned by this host
    venues = Venue.objects.filter(owner=request.user)
    venue_ids = venues.values_list('id', flat=True)
    
    # Get all bookings for these venues
    bookings = Booking.objects.filter(room__venue__in=venue_ids).select_related(
        'room', 'room__venue', 'user'
    ).order_by('-created_at')
    
    # Add status colors for UI display
    for booking in bookings:
        if booking.status == 'pending':
            booking.status_color = 'warning'
        elif booking.status == 'confirmed':
            booking.status_color = 'success'
        elif booking.status == 'cancelled':
            booking.status_color = 'danger'
        elif booking.status == 'completed':
            booking.status_color = 'info'
    
    context = {
        'bookings': bookings
    }
    
    return render(request, 'bookings/host_bookings.html', context)

@login_required
def venue_create(request):
    """Create a new venue"""
    # Check if user is a host
    if request.user.user_type != 'host':
        return redirect('home')
        
    if request.method == 'POST':
        form = VenueForm(request.POST, request.FILES)
        if form.is_valid():
            venue = form.save(commit=False)
            venue.owner = request.user
            venue.save()
            form.save_m2m()  # Save many-to-many relationships
            messages.success(request, 'Venue created successfully!')
            return redirect('bookings:host_venues')
    else:
        form = VenueForm()
    
    return render(request, 'bookings/venue_form.html', {'form': form, 'action': 'Create'})

@login_required
def venue_update(request, pk):
    """Update a venue"""
    venue = get_object_or_404(Venue, pk=pk)
    
    # Check if user is authorized to update this venue
    if venue.owner != request.user and not request.user.is_staff:
        messages.error(request, "You don't have permission to update this venue.")
        return redirect('bookings:host_venues')
    
    if request.method == 'POST':
        form = VenueForm(request.POST, request.FILES, instance=venue)
        if form.is_valid():
            form.save()
            messages.success(request, 'Venue updated successfully!')
            return redirect('bookings:host_venues')
    else:
        form = VenueForm(instance=venue)
    
    return render(request, 'bookings/venue_form.html', {'form': form, 'venue': venue, 'action': 'Update'})

@login_required
def venue_delete(request, pk):
    """Delete a venue"""
    venue = get_object_or_404(Venue, pk=pk)
    
    # Check if user is authorized to delete this venue
    if venue.owner != request.user and not request.user.is_staff:
        messages.error(request, "You don't have permission to delete this venue.")
        return redirect('bookings:host_venues')
    
    if request.method == 'POST':
        venue.delete()
        messages.success(request, 'Venue deleted successfully!')
        return redirect('bookings:host_venues')
    
    return render(request, 'bookings/venue_confirm_delete.html', {'venue': venue})

@login_required
def add_room(request, venue_id):
    """Add a room to a venue"""
    venue = get_object_or_404(Venue, pk=venue_id)
    
    # Check if user is authorized to add rooms to this venue
    if venue.owner != request.user and not request.user.is_staff:
        messages.error(request, "You don't have permission to add rooms to this venue.")
        return redirect('bookings:host_venues')
    
    if request.method == 'POST':
        form = RoomForm(request.POST, request.FILES)
        if form.is_valid():
            room = form.save(commit=False)
            room.venue = venue
            room.save()
            form.save_m2m()  # Save many-to-many relationships
            messages.success(request, 'Room added successfully!')
            return redirect('bookings:host_venues')
    else:
        form = RoomForm()
    
    return render(request, 'bookings/room_form.html', {'form': form, 'venue': venue, 'action': 'Add'})

@login_required
def room_update(request, venue_id, pk):
    """Update a room"""
    venue = get_object_or_404(Venue, pk=venue_id)
    room = get_object_or_404(Room, pk=pk, venue=venue)
    
    # Check if user is authorized to update this room
    if venue.owner != request.user and not request.user.is_staff:
        messages.error(request, "You don't have permission to update this room.")
        return redirect('bookings:host_venues')
    
    if request.method == 'POST':
        form = RoomForm(request.POST, request.FILES, instance=room)
        if form.is_valid():
            form.save()
            messages.success(request, 'Room updated successfully!')
            return redirect('bookings:host_venues')
    else:
        form = RoomForm(instance=room)
    
    return render(request, 'bookings/room_form.html', {'form': form, 'venue': venue, 'room': room, 'action': 'Update'})

@login_required
def room_delete(request, venue_id, pk):
    """Delete a room"""
    venue = get_object_or_404(Venue, pk=venue_id)
    room = get_object_or_404(Room, pk=pk, venue=venue)
    
    # Check if user is authorized to delete this room
    if venue.owner != request.user and not request.user.is_staff:
        messages.error(request, "You don't have permission to delete this room.")
        return redirect('bookings:host_venues')
    
    if request.method == 'POST':
        room.delete()
        messages.success(request, 'Room deleted successfully!')
        return redirect('bookings:host_venues')
    
    return render(request, 'bookings/room_confirm_delete.html', {'room': room, 'venue': venue})

@login_required
def confirm_booking(request, booking_id):
    """Confirm a booking"""
    booking = get_object_or_404(Booking, booking_id=booking_id)
    venue = booking.room.venue
    
    # Check if user is authorized
    if venue.owner != request.user and not request.user.is_staff:
        messages.error(request, "You don't have permission to confirm this booking.")
        return redirect('bookings:host_bookings')
    
    # Update booking status
    booking.status = 'confirmed'
    booking.save()
    
    messages.success(request, 'Booking confirmed successfully!')
    return redirect('bookings:host_bookings') 