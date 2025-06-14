from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse, HttpResponseRedirect
from django.contrib import messages
from django.db.models import Q, Avg, Count, Sum, Q
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal

from .models import Venue, Room, Booking, Review, Favorite, TimeSlot, VenueCategory, Amenity
from accounts.models import WalletTransaction
from payments.models import Transaction


class VenueListView(ListView):
    model = Venue
    template_name = 'bookings/venue_list.html'
    context_object_name = 'venue_list'
    paginate_by = 9
    
    def get_queryset(self):
        queryset = Venue.objects.filter(is_active=True).annotate(avg_rating=Avg('reviews__rating'))
        
        # Filter by venue type (restaurant or hotel)
        venue_type = self.request.GET.get('type')
        if venue_type:
            queryset = queryset.filter(category__name__icontains=venue_type)
            
        # Filter by amenities
        amenities = self.request.GET.getlist('amenities')
        if amenities:
            for amenity in amenities:
                queryset = queryset.filter(amenities__name__icontains=amenity)
            
        # Filter by price range
        price_range = self.request.GET.get('price_range')
        if price_range:
            if price_range == '0-1000':
                queryset = queryset.filter(rooms__price_per_hour__lte=1000)
            elif price_range == '1000-2000':
                queryset = queryset.filter(rooms__price_per_hour__gte=1000, rooms__price_per_hour__lte=2000)
            elif price_range == '2000-5000':
                queryset = queryset.filter(rooms__price_per_hour__gte=2000, rooms__price_per_hour__lte=5000)
            elif price_range == '5000+':
                queryset = queryset.filter(rooms__price_per_hour__gte=5000)
        
        # Filter by capacity
        capacity = self.request.GET.get('capacity')
        if capacity:
            if capacity == '1-10':
                queryset = queryset.filter(max_capacity__lte=10)
            elif capacity == '11-50':
                queryset = queryset.filter(max_capacity__gte=11, max_capacity__lte=50)
            elif capacity == '51-100':
                queryset = queryset.filter(max_capacity__gte=51, max_capacity__lte=100)
            elif capacity == '100+':
                queryset = queryset.filter(max_capacity__gte=100)
            
        # Filter by rating
        rating = self.request.GET.get('rating')
        if rating:
            if rating == '4+':
                queryset = queryset.filter(avg_rating__gte=4)
            elif rating == '3+':
                queryset = queryset.filter(avg_rating__gte=3)
            elif rating == '2+':
                queryset = queryset.filter(avg_rating__gte=2)
            
        return queryset.distinct()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = VenueCategory.objects.all()
        context['amenities'] = Amenity.objects.all()
        
        # Add filters to context
        context['venue_type'] = self.request.GET.get('type', '')
        context['selected_amenities'] = self.request.GET.getlist('amenities', [])
        context['price_range'] = self.request.GET.get('price_range', '')
        context['capacity'] = self.request.GET.get('capacity', '')
        context['rating'] = self.request.GET.get('rating', '')
        
        return context


class VenueDetailView(DetailView):
    model = Venue
    template_name = 'bookings/venue_detail.html'
    context_object_name = 'venue'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        venue = self.get_object()
        
        # Get rooms for this venue
        context['rooms'] = venue.rooms.filter(is_active=True)
        
        # Get reviews for this venue
        context['reviews'] = venue.reviews.all().order_by('-created_at')[:5]
        context['review_count'] = venue.reviews.count()
        
        # Check if user has favorited this venue
        if self.request.user.is_authenticated:
            context['is_favorite'] = Favorite.objects.filter(
                user=self.request.user, 
                venue=venue
            ).exists()
        
        return context


class VenueSearchView(ListView):
    model = Venue
    template_name = 'bookings/venue_search.html'
    context_object_name = 'venues'
    paginate_by = 9
    
    def get_queryset(self):
        queryset = Venue.objects.filter(is_active=True).annotate(avg_rating=Avg('reviews__rating'))
        
        # Filter by location
        location = self.request.GET.get('location')
        if location:
            queryset = queryset.filter(
                Q(city__icontains=location) |
                Q(state__icontains=location) |
                Q(country__icontains=location)
            )
        
        # Filter by category
        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(category_id=category)
        
        # Filter by venue type (restaurant or hotel)
        venue_type = self.request.GET.get('venue_type')
        if venue_type:
            queryset = queryset.filter(category__name__icontains=venue_type)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = VenueCategory.objects.all()
        context['amenities'] = Amenity.objects.all()
        
        # Add search parameters to context
        context['location'] = self.request.GET.get('location', '')
        context['category'] = self.request.GET.get('category', '')
        context['venue_type'] = self.request.GET.get('venue_type', '')
        
        return context


class RoomListView(ListView):
    model = Room
    template_name = 'bookings/room_list.html'
    context_object_name = 'rooms'
    paginate_by = 9
    
    def get_queryset(self):
        venue_id = self.kwargs.get('pk')
        return Room.objects.filter(venue_id=venue_id, is_active=True)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        venue_id = self.kwargs.get('pk')
        context['venue'] = get_object_or_404(Venue, pk=venue_id)
        return context


class RoomDetailView(DetailView):
    model = Room
    template_name = 'bookings/room_detail.html'
    context_object_name = 'room'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        room = self.get_object()
        context['venue'] = room.venue
        
        # Get available time slots for the next 7 days
        today = timezone.now().date()
        next_week = today + timezone.timedelta(days=7)
        context['time_slots'] = room.time_slots.filter(
            start_time__date__gte=today,
            start_time__date__lte=next_week,
            is_available=True
        ).order_by('start_time')
        
        # Add user wallet balance to context
        if self.request.user.is_authenticated:
            context['wallet_balance'] = self.request.user.wallet_balance
        
        return context


@login_required
def room_availability(request, pk):
    """AJAX endpoint to check room availability for specific dates"""
    room = get_object_or_404(Room, pk=pk)
    return JsonResponse({'room_id': room.id})


class BookingCreateView(LoginRequiredMixin, CreateView):
    model = Booking
    template_name = 'bookings/booking_create.html'
    fields = ['num_guests', 'special_requests']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        room_id = self.kwargs.get('room_id')
        room = get_object_or_404(Room, pk=room_id)
        context['room'] = room
        context['wallet_balance'] = self.request.user.wallet_balance
        
        # Get venue category
        venue_category = room.venue.category.name.lower() if room.venue.category else ""
        context['venue_category'] = venue_category
        context['is_hotel'] = 'hotel' in venue_category
        context['is_restaurant'] = 'restaurant' in venue_category or 'café' in venue_category or 'cafe' in venue_category
        
        # Generate available time slots for the next 7 days
        today = timezone.now().date()
        if not TimeSlot.objects.filter(room=room, start_time__date__gte=today).exists():
            self.generate_time_slots(room)
        
        # Get available time slots for today by default
        date_str = self.request.GET.get('date', today.strftime('%Y-%m-%d'))
        try:
            selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            selected_date = today
        
        # Get all time slots for the selected date
        start_of_day = timezone.make_aware(datetime.combine(selected_date, datetime.min.time()))
        end_of_day = timezone.make_aware(datetime.combine(selected_date, datetime.max.time()))
        
        available_slots = TimeSlot.objects.filter(
            room=room,
            start_time__gte=start_of_day,
            start_time__lte=end_of_day,
            is_available=True
        ).order_by('start_time')
        
        # Format slots for template
        context['available_slots'] = [
            {
                'start': slot.start_time,
                'end': slot.end_time,
                'price': float(room.price_per_hour) * ((slot.end_time - slot.start_time).total_seconds() / 3600)
            } for slot in available_slots
        ]
        context['has_available_slots'] = len(context['available_slots']) > 0
        context['selected_date'] = selected_date
        
        return context
    
    def generate_time_slots(self, room):
        """Generate time slots for the next 7 days"""
        today = timezone.now().date()
        for day_offset in range(7):
            current_date = today + timedelta(days=day_offset)
            
            # For hotels, create full-day slots (check-in/check-out)
            if 'hotel' in (room.venue.category.name.lower() if room.venue.category else ""):
                # Create a full-day slot (2pm check-in to 12pm checkout next day)
                checkin_time = timezone.make_aware(datetime.combine(current_date, datetime.strptime("14:00", "%H:%M").time()))
                checkout_time = timezone.make_aware(datetime.combine(current_date + timedelta(days=1), datetime.strptime("12:00", "%H:%M").time()))
                
                TimeSlot.objects.create(
                    room=room,
                    start_time=checkin_time,
                    end_time=checkout_time,
                    is_available=True
                )
            
            # For restaurants, create 2-hour slots from 10am to 10pm
            elif 'restaurant' in (room.venue.category.name.lower() if room.venue.category else "") or 'café' in (room.venue.category.name.lower() if room.venue.category else "") or 'cafe' in (room.venue.category.name.lower() if room.venue.category else ""):
                for hour in range(10, 22, 2):  # 10am to 10pm in 2-hour slots
                    start_time = timezone.make_aware(datetime.combine(current_date, datetime.strptime(f"{hour}:00", "%H:%M").time()))
                    end_time = start_time + timedelta(hours=2)
                    
                    TimeSlot.objects.create(
                        room=room,
                        start_time=start_time,
                        end_time=end_time,
                        is_available=True
                    )
            
            # For regular venues, create hourly slots from 9am to 9pm
            else:
                for hour in range(9, 21):  # 9am to 9pm
                    start_time = timezone.make_aware(datetime.combine(current_date, datetime.strptime(f"{hour}:00", "%H:%M").time()))
                    end_time = start_time + timedelta(hours=1)
                    
                    TimeSlot.objects.create(
                        room=room,
                        start_time=start_time,
                        end_time=end_time,
                        is_available=True
                    )
    
    def form_valid(self, form):
        room_id = self.kwargs.get('room_id')
        room = get_object_or_404(Room, pk=room_id)
        
        # Set the user and room
        form.instance.user = self.request.user
        form.instance.room = room
        
        # Get start and end times from POST data
        start_time_str = self.request.POST.get('start_time')
        end_time_str = self.request.POST.get('end_time')
        start_date_str = self.request.POST.get('start_time_date')
        end_date_str = self.request.POST.get('end_time_date')
        
        if not (start_time_str and end_time_str and start_date_str and end_date_str):
            messages.error(self.request, "Please select valid start and end times.")
            return self.form_invalid(form)
        
        try:
            # Parse datetime objects
            start_time = timezone.make_aware(datetime.strptime(f"{start_date_str} {start_time_str}", "%Y-%m-%d %H:%M"))
            end_time = timezone.make_aware(datetime.strptime(f"{end_date_str} {end_time_str}", "%Y-%m-%d %H:%M"))
            
            # Make sure the booking is not in the past
            if start_time < timezone.now():
                messages.error(self.request, "Cannot book a time slot in the past.")
                return self.form_invalid(form)
            
            # Make sure end time is after start time
            if end_time <= start_time:
                messages.error(self.request, "End time must be after start time.")
                return self.form_invalid(form)
                
            form.instance.start_time = start_time
            form.instance.end_time = end_time
            
            # Calculate total price
            duration_hours = (end_time - start_time).total_seconds() / 3600
            total_price = float(room.price_per_hour) * duration_hours
            form.instance.total_price = Decimal(str(total_price))
            
            # Check if user has enough balance
            if self.request.user.wallet_balance < Decimal(str(total_price)):
                messages.error(self.request, "Insufficient coins in your wallet! Please add more coins.")
                return self.form_invalid(form)
            
            # Check if the time slot is available (no overlapping bookings)
            existing_bookings = Booking.objects.filter(
                room=room,
                status__in=['pending', 'confirmed'],
                start_time__lt=end_time,
                end_time__gt=start_time
            ).exists()
            
            if existing_bookings:
                messages.error(self.request, "The selected time slot is already booked by someone else.")
                return self.form_invalid(form)
            
            # Check if corresponding TimeSlot objects are available
            overlapping_slots = TimeSlot.objects.filter(
                room=room,
                start_time__lte=end_time,
                end_time__gte=start_time,
                is_available=True
            )
            
            if not overlapping_slots.exists():
                messages.error(self.request, "The selected time slot is no longer available.")
                return self.form_invalid(form)
            
            # Process the payment
            if self.request.user.deduct_from_wallet(total_price):
                # Create wallet transaction record
                WalletTransaction.objects.create(
                    user=self.request.user,
                    amount=-Decimal(str(total_price)),
                    transaction_type='booking',
                    description=f"Payment for booking at {room.venue.name} - {room.name}",
                    reference_id=f"BOOK-{timezone.now().strftime('%Y%m%d%H%M%S')}"
                )
                
                # Mark time slots as unavailable
                overlapping_slots.update(is_available=False)
                
                # Set status as confirmed by default (can be changed to pending if needed)
                form.instance.status = 'confirmed'
                
                messages.success(self.request, f"{total_price} coins deducted from your wallet. Booking confirmed!")
                return super().form_valid(form)
            else:
                messages.error(self.request, "Payment failed! Please try again.")
                return self.form_invalid(form)
                
        except ValueError:
            messages.error(self.request, "Invalid date or time format.")
            return self.form_invalid(form)
    
    def get_success_url(self):
        return reverse('bookings:booking_detail', kwargs={'booking_id': self.object.booking_id})


class BookingDetailView(LoginRequiredMixin, DetailView):
    model = Booking
    template_name = 'bookings/booking_detail.html'
    context_object_name = 'booking'
    
    def get_object(self):
        booking_id = self.kwargs.get('booking_id')
        booking = get_object_or_404(Booking, booking_id=booking_id)
        
        # Check if the user is authorized to view this booking
        if booking.user != self.request.user and booking.room.venue.owner != self.request.user:
            messages.error(self.request, "You don't have permission to view this booking.")
            return HttpResponseRedirect(reverse('bookings:user_bookings'))
        
        return booking
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['now'] = timezone.now()  # Add current time for template comparison
        return context


@login_required
def cancel_booking(request, booking_id):
    """Cancel a booking and refund the payment"""
    booking = get_object_or_404(Booking, booking_id=booking_id)
    
    # Check if the user is authorized to cancel this booking
    if booking.user != request.user and booking.room.venue.owner != request.user:
        messages.error(request, "You don't have permission to cancel this booking.")
        return redirect('bookings:user_bookings')
    
    # Check if booking can be cancelled
    if booking.status == 'cancelled':
        messages.info(request, "This booking is already cancelled.")
        return redirect('bookings:booking_detail', booking_id=booking.booking_id)
    
    if booking.start_time <= timezone.now():
        messages.error(request, "You cannot cancel a booking that has already started or completed.")
        return redirect('bookings:booking_detail', booking_id=booking.booking_id)
    
    # Process refund
    if request.method == 'POST':
        # Calculate refund amount based on how far in advance the cancellation is
        hours_before = (booking.start_time - timezone.now()).total_seconds() / 3600
        
        refund_percentage = 100  # Full refund by default
        
        # If less than 24 hours before the booking, provide partial refund
        if hours_before < 24:
            refund_percentage = 50  # 50% refund for late cancellations
        
        refund_amount = Decimal(str(float(booking.total_price) * (refund_percentage / 100)))
        
        # Process the refund
        booking.user.wallet_balance += refund_amount
        booking.user.save()
        
        # Create wallet transaction record for refund
        WalletTransaction.objects.create(
            user=booking.user,
            amount=refund_amount,
            transaction_type='refund',
            description=f"Refund ({refund_percentage}%) for cancelled booking at {booking.room.venue.name} - {booking.room.name}",
            reference_id=f"REF-{timezone.now().strftime('%Y%m%d%H%M%S')}"
        )
        
        # Update booking status
        booking.status = 'cancelled'
        booking.save()
        
        # Mark the time slot as available again
        time_slots = TimeSlot.objects.filter(
            room=booking.room,
            start_time__lte=booking.end_time,
            end_time__gte=booking.start_time
        )
        time_slots.update(is_available=True)
        
        messages.success(
            request, 
            f"Booking successfully cancelled. {refund_amount} coins have been refunded to your wallet."
        )
        
        return redirect('bookings:user_bookings')
    
    return redirect('bookings:booking_detail', booking_id=booking.booking_id)


class BookingUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Booking
    template_name = 'bookings/booking_update.html'
    fields = ['start_time', 'end_time', 'num_guests', 'special_requests']
    
    def test_func(self):
        return True


class UserBookingsListView(LoginRequiredMixin, ListView):
    model = Booking
    template_name = 'bookings/user_bookings.html'
    context_object_name = 'bookings'
    paginate_by = 10
    
    def get_queryset(self):
        return Booking.objects.filter(user=self.request.user).order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['wallet_balance'] = self.request.user.wallet_balance
        context['recent_transactions'] = WalletTransaction.objects.filter(
            user=self.request.user
        ).order_by('-created_at')[:5]
        return context


class FavoriteListView(LoginRequiredMixin, ListView):
    model = Favorite
    template_name = 'bookings/favorites.html'
    context_object_name = 'favorites'
    paginate_by = 10
    
    def get_queryset(self):
        return Favorite.objects.filter(user=self.request.user).select_related('venue')


@login_required
def add_to_favorites(request, venue_id):
    venue = get_object_or_404(Venue, pk=venue_id)
    favorite, created = Favorite.objects.get_or_create(user=request.user, venue=venue)
    
    if created:
        messages.success(request, f"Added {venue.name} to your favorites")
    else:
        messages.info(request, f"{venue.name} was already in your favorites")
        
    return redirect('bookings:venue_detail', pk=venue_id)


@login_required
def remove_from_favorites(request, venue_id):
    venue = get_object_or_404(Venue, pk=venue_id)
    favorite = get_object_or_404(Favorite, user=request.user, venue=venue)
    favorite.delete()
    messages.success(request, f"Removed {venue.name} from your favorites")
    return redirect('bookings:venue_detail', pk=venue_id)


@login_required
def check_availability(request, room_id):
    """Check availability for a specific room"""
    room = get_object_or_404(Room, pk=room_id)
    
    # Get the date from request parameters or use today
    date_str = request.GET.get('date')
    if date_str:
        try:
            selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            selected_date = timezone.now().date()
    else:
        selected_date = timezone.now().date()
    
    # Get existing bookings for this room on the selected date
    bookings = Booking.objects.filter(
        room=room,
        booking_date=selected_date,
        status__in=['pending', 'confirmed']
    )
    
    # Get the room's opening hours
    opening_time = datetime.strptime('09:00', '%H:%M').time()  # Default 9 AM
    closing_time = datetime.strptime('20:00', '%H:%M').time()  # Default 8 PM
    
    # Create time slots (hourly for simplicity)
    time_slots = []
    current_time = datetime.combine(selected_date, opening_time)
    end_time = datetime.combine(selected_date, closing_time)
    
    while current_time < end_time:
        time_slot = {
            'time': current_time.time().strftime('%H:%M'),
            'available': True
        }
        
        # Check if this slot is booked
        slot_end = (current_time + timedelta(hours=1)).time()
        for booking in bookings:
            booking_start = booking.start_time.time()
            booking_end = booking.end_time.time()
            
            if (booking_start <= current_time.time() < booking_end) or \
               (booking_start < slot_end <= booking_end) or \
               (current_time.time() <= booking_start and slot_end >= booking_end):
                time_slot['available'] = False
                break
        
        time_slots.append(time_slot)
        current_time += timedelta(hours=1)
    
    context = {
        'room': room,
        'venue': room.venue,
        'date': selected_date,
        'time_slots': time_slots,
    }
    
    return render(request, 'bookings/availability.html', context)


@login_required
def get_available_times(request, room_id):
    """Get available times for a room on a specific date (AJAX endpoint)"""
    room = get_object_or_404(Room, pk=room_id)
    
    # Get date from request
    date_str = request.GET.get('date')
    try:
        selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        selected_date = timezone.now().date()
    
    # Get bookings for this room on selected date
    bookings = Booking.objects.filter(
        room=room,
        booking_date=selected_date,
        status__in=['pending', 'confirmed']
    )
    
    # Default opening hours (can be stored in venue/room model in a real app)
    opening_time = datetime.strptime('09:00', '%H:%M').time()
    closing_time = datetime.strptime('20:00', '%H:%M').time()
    
    # Generate time slots
    slots = []
    current = datetime.combine(selected_date, opening_time)
    end = datetime.combine(selected_date, closing_time)
    
    while current < end:
        slot_end = current + timedelta(hours=1)
        is_available = True
        
        # Check against existing bookings
        for booking in bookings:
            booking_start = datetime.combine(selected_date, booking.start_time.time())
            booking_end = datetime.combine(selected_date, booking.end_time.time())
            
            if (booking_start <= current < booking_end) or \
               (booking_start < slot_end <= booking_end) or \
               (current <= booking_start and slot_end >= booking_end):
                is_available = False
                break
        
        if is_available:
            slots.append({
                'start': current.strftime('%H:%M'),
                'end': slot_end.strftime('%H:%M')
            })
        
        current = slot_end
    
    return JsonResponse({'slots': slots})


class HostVenueListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Venue
    template_name = 'bookings/host_venues.html'
    context_object_name = 'venues'
    paginate_by = 10
    
    def test_func(self):
        return self.request.user.user_type in ['host', 'admin']
    
    def get_queryset(self):
        # Only show venues owned by the current user
        return Venue.objects.filter(owner=self.request.user)


class VenueCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Venue
    template_name = 'bookings/venue_form.html'
    fields = ['name', 'category', 'description', 'address', 'city', 'state', 
              'postal_code', 'country', 'phone', 'email', 'website', 'max_capacity',
              'amenities']
    
    def test_func(self):
        return self.request.user.user_type in ['host', 'admin']
    
    def form_valid(self, form):
        form.instance.owner = self.request.user
        messages.success(self.request, f"Venue '{form.instance.name}' has been created successfully.")
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('bookings:host_venues')


class VenueUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Venue
    template_name = 'bookings/venue_form.html'
    fields = ['name', 'category', 'description', 'address', 'city', 'state', 
              'postal_code', 'country', 'phone', 'email', 'website', 'max_capacity',
              'amenities', 'is_active']
    
    def test_func(self):
        venue = self.get_object()
        # Only allow the owner or an admin to edit
        return self.request.user == venue.owner or self.request.user.user_type == 'admin'
    
    def form_valid(self, form):
        messages.success(self.request, f"Venue '{form.instance.name}' has been updated successfully.")
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('bookings:host_venues')


class VenueDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Venue
    template_name = 'bookings/venue_confirm_delete.html'
    success_url = reverse_lazy('bookings:host_venues')
    
    def test_func(self):
        venue = self.get_object()
        # Only allow the owner or an admin to delete
        return self.request.user == venue.owner or self.request.user.user_type == 'admin'
    
    def delete(self, request, *args, **kwargs):
        venue = self.get_object()
        messages.success(self.request, f"Venue '{venue.name}' has been deleted successfully.")
        return super().delete(request, *args, **kwargs)


class RoomCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Room
    template_name = 'bookings/room_form.html'
    fields = ['name', 'description', 'capacity', 'size_sqft', 'price_per_hour']
    
    def test_func(self):
        return True


class RoomUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Room
    template_name = 'bookings/room_form.html'
    fields = ['name', 'description', 'capacity', 'size_sqft', 'price_per_hour', 'is_active']
    
    def test_func(self):
        return True


class RoomDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Room
    template_name = 'bookings/room_confirm_delete.html'
    
    def test_func(self):
        return True


class HostBookingsListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Booking
    template_name = 'bookings/host_bookings.html'
    context_object_name = 'bookings'
    paginate_by = 10
    
    def test_func(self):
        return self.request.user.user_type in ['host', 'admin']
    
    def get_queryset(self):
        # Get venues owned by the current user
        user_venues = Venue.objects.filter(owner=self.request.user)
        # Get rooms in those venues
        venue_rooms = Room.objects.filter(venue__in=user_venues)
        # Get bookings for those rooms
        return Booking.objects.filter(room__in=venue_rooms).order_by('-created_at')


@login_required
def confirm_booking(request, booking_id):
    booking = get_object_or_404(Booking, booking_id=booking_id)
    
    # Check if the user is the owner of the venue
    if booking.room.venue.owner != request.user and not request.user.user_type == 'admin':
        messages.error(request, "You don't have permission to confirm this booking.")
        return redirect('bookings:host_bookings')
    
    # Update booking status
    booking.status = 'confirmed'
    booking.save()
    
    # Send confirmation email (could be implemented later)
    
    messages.success(request, f"Booking #{booking.booking_id} has been confirmed successfully.")
    return redirect('bookings:host_bookings')


class ReviewCreateView(LoginRequiredMixin, CreateView):
    model = Review
    template_name = 'bookings/review_form.html'
    fields = ['rating', 'comment']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        venue_id = self.kwargs.get('venue_id')
        venue = get_object_or_404(Venue, pk=venue_id)
        context['venue'] = venue
        return context
    
    def form_valid(self, form):
        venue_id = self.kwargs.get('venue_id')
        booking_id = self.kwargs.get('booking_id')
        
        venue = get_object_or_404(Venue, pk=venue_id)
        booking = get_object_or_404(Booking, booking_id=booking_id)
        
        # Ensure the user owns the booking and it's for this venue
        if booking.user != self.request.user:
            messages.error(self.request, "You can only review your own bookings.")
            return self.form_invalid(form)
        
        if booking.room.venue != venue:
            messages.error(self.request, "The booking must be for this venue.")
            return self.form_invalid(form)
        
        # Set the user, venue, and booking
        form.instance.user = self.request.user
        form.instance.venue = venue
        form.instance.booking = booking
        
        messages.success(self.request, "Thank you for your review!")
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('bookings:venue_detail', args=[self.kwargs.get('venue_id')])


class VenueReviewsListView(DetailView):
    model = Venue
    template_name = 'bookings/venue_reviews.html'
    context_object_name = 'venue'


@login_required
def add_favorite(request, venue_id):
    venue = get_object_or_404(Venue, pk=venue_id)
    return redirect('bookings:venue_detail', pk=venue_id)


@login_required
def remove_favorite(request, venue_id):
    venue = get_object_or_404(Venue, pk=venue_id)
    return redirect('bookings:venue_detail', pk=venue_id)


class HostDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'bookings/host_dashboard.html'
    
    def test_func(self):
        return self.request.user.user_type in ['host', 'admin']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get venues owned by the current user
        user_venues = Venue.objects.filter(owner=user)
        venue_count = user_venues.count()
        
        # Get rooms in those venues
        venue_rooms = Room.objects.filter(venue__in=user_venues)
        
        # Get bookings for those rooms
        user_bookings = Booking.objects.filter(room__in=venue_rooms)
        booking_count = user_bookings.count()
        
        # Get recent bookings
        recent_bookings = user_bookings.select_related('user', 'room', 'room__venue').order_by('-created_at')[:5]
        
        # Get recent reviews for the user's venues
        recent_reviews = Review.objects.filter(venue__in=user_venues).select_related('user', 'venue').order_by('-created_at')[:5]
        
        # Calculate average rating
        avg_rating = Review.objects.filter(venue__in=user_venues).aggregate(Avg('rating'))['rating__avg'] or 0
        avg_rating = round(avg_rating, 1)
        
        # Revenue data
        venue_transactions = Transaction.objects.filter(
            booking__room__venue__in=user_venues,
            status='completed'
        )
        
        total_revenue = venue_transactions.aggregate(Sum('amount'))['amount__sum'] or 0
        
        # Monthly revenue data for chart
        monthly_revenue = []
        
        # Get data for the last 12 months
        now = timezone.now()
        for i in range(12):
            month_start = now - timedelta(days=now.day) - timedelta(days=30 * i)
            
            # Get revenue for this month
            month_revenue = venue_transactions.filter(
                created_at__year=month_start.year,
                created_at__month=month_start.month
            ).aggregate(Sum('amount'))['amount__sum'] or 0
            
            monthly_revenue.insert(0, float(month_revenue))
        
        # Get top performing venues
        top_venues = user_venues.annotate(
            booking_count=Count('rooms__bookings'),
            revenue=Sum('rooms__bookings__transactions__amount', filter=Q(rooms__bookings__transactions__status='completed'))
        ).order_by('-revenue')[:5]
        
        context.update({
            'venue_count': venue_count,
            'booking_count': booking_count,
            'recent_bookings': recent_bookings,
            'recent_reviews': recent_reviews,
            'avg_rating': avg_rating,
            'total_revenue': total_revenue,
            'monthly_revenue': monthly_revenue,
            'top_venues': top_venues,
        })
        
        return context


def index_view(request):
    """Homepage view"""
    # Featured venues
    featured_venues = Venue.objects.filter(is_active=True, is_featured=True)[:4]
    
    # Recently added venues
    recent_venues = Venue.objects.filter(is_active=True).order_by('-created_at')[:4]
    
    # Get venue types from the model
    venue_types = dict(Venue.VENUE_TYPES)
    
    context = {
        'featured_venues': featured_venues,
        'recent_venues': recent_venues,
        'venue_types': venue_types,
    }
    
    return render(request, 'home.html', context)


def venue_rooms(request, venue_id):
    """View rooms for a specific venue"""
    venue = get_object_or_404(Venue, pk=venue_id, is_active=True)
    rooms = Room.objects.filter(venue=venue, is_active=True)
    
    context = {
        'venue': venue,
        'rooms': rooms,
    }
    
    return render(request, 'bookings/venue_rooms.html', context)


def room_availability(request, room_id):
    """View availability calendar for a specific room"""
    room = get_object_or_404(Room, pk=room_id, is_active=True)
    
    context = {
        'room': room,
        'venue': room.venue,
    }
    
    return render(request, 'bookings/room_availability.html', context)


@login_required
def book_room(request, room_id):
    """Book a room"""
    room = get_object_or_404(Room, pk=room_id, is_active=True)
    
    if request.method == 'POST':
        # Process booking form
        date_str = request.POST.get('booking_date')
        start_time_str = request.POST.get('start_time')
        end_time_str = request.POST.get('end_time')
        
        try:
            booking_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            start_time = datetime.strptime(start_time_str, '%H:%M').time()
            end_time = datetime.strptime(end_time_str, '%H:%M').time()
            
            # Create booking
            booking = Booking.objects.create(
                user=request.user,
                room=room,
                booking_date=booking_date,
                start_time=datetime.combine(booking_date, start_time),
                end_time=datetime.combine(booking_date, end_time),
                status='pending',
                total_amount=room.hourly_rate * ((datetime.combine(booking_date, end_time) - 
                                               datetime.combine(booking_date, start_time)).seconds / 3600)
            )
            
            messages.success(request, 'Booking request submitted successfully!')
            return redirect('bookings:booking_detail', pk=booking.id)
            
        except ValueError:
            messages.error(request, 'Invalid date or time format.')
    
    context = {
        'room': room,
        'venue': room.venue,
    }
    

@login_required
def add_review(request, venue_id):
    """Add a review for a venue"""
    venue = get_object_or_404(Venue, pk=venue_id)
    
    if request.method == 'POST':
        rating = request.POST.get('rating')
        comment = request.POST.get('comment')
        
        if rating and comment:
            Review.objects.create(
                user=request.user,
                venue=venue,
                rating=rating,
                comment=comment
            )
            messages.success(request, 'Thank you for your review!')
            return redirect('bookings:venue_detail', pk=venue_id)
        else:
            messages.error(request, 'Please provide both rating and comment.')
    
    return render(request, 'bookings/review_form.html', {'venue': venue})


@login_required
def venue_create(request):
    """Create a new venue"""
    if request.method == 'POST':
        form = VenueForm(request.POST)
        if form.is_valid():
            venue = form.save(commit=False)
            venue.owner = request.user
            venue.save()
            form.save_m2m()  # Save many-to-many relationships
            messages.success(request, 'Venue created successfully!')
            return redirect('bookings:venue_detail', pk=venue.pk)
    else:
        form = VenueForm()
    
    return render(request, 'bookings/venue_form.html', {'form': form, 'action': 'Create'})


@login_required
def venue_update(request, venue_id):
    """Update a venue"""
    venue = get_object_or_404(Venue, pk=venue_id)
    
    # Check if user is authorized to update this venue
    if venue.owner != request.user and not request.user.is_staff:
        messages.error(request, "You don't have permission to update this venue.")
        return redirect('bookings:venue_detail', pk=venue_id)
    
    if request.method == 'POST':
        form = VenueForm(request.POST, instance=venue)
        if form.is_valid():
            form.save()
            messages.success(request, 'Venue updated successfully!')
            return redirect('bookings:venue_detail', pk=venue_id)
    else:
        form = VenueForm(instance=venue)
    
    return render(request, 'bookings/venue_form.html', {'form': form, 'action': 'Update'})


@login_required
def venue_delete(request, venue_id):
    """Delete a venue"""
    venue = get_object_or_404(Venue, pk=venue_id)
    
    # Check if user is authorized to delete this venue
    if venue.owner != request.user and not request.user.is_staff:
        messages.error(request, "You don't have permission to delete this venue.")
        return redirect('bookings:venue_detail', pk=venue_id)
    
    if request.method == 'POST':
        venue.delete()
        messages.success(request, 'Venue deleted successfully!')
        return redirect('bookings:venue_list')
    
    return render(request, 'bookings/venue_confirm_delete.html', {'venue': venue})


@login_required
def add_room(request, venue_id):
    """Add a room to a venue"""
    venue = get_object_or_404(Venue, pk=venue_id)
    
    # Check if user is authorized to add rooms to this venue
    if venue.owner != request.user and not request.user.is_staff:
        messages.error(request, "You don't have permission to add rooms to this venue.")
        return redirect('bookings:venue_detail', pk=venue_id)
    
    if request.method == 'POST':
        form = RoomForm(request.POST)
        if form.is_valid():
            room = form.save(commit=False)
            room.venue = venue
            room.save()
            form.save_m2m()  # Save many-to-many relationships
            messages.success(request, 'Room added successfully!')
            return redirect('bookings:venue_detail', pk=venue_id)
    else:
        form = RoomForm()
    
    return render(request, 'bookings/room_form.html', {'form': form, 'venue': venue, 'action': 'Add'})


@login_required
def room_update(request, room_id):
    """Update a room"""
    room = get_object_or_404(Room, pk=room_id)
    
    # Check if user is authorized to update this room
    if room.venue.owner != request.user and not request.user.is_staff:
        messages.error(request, "You don't have permission to update this room.")
        return redirect('bookings:room_detail', pk=room_id)
    
    if request.method == 'POST':
        form = RoomForm(request.POST, instance=room)
        if form.is_valid():
            form.save()
            messages.success(request, 'Room updated successfully!')
            return redirect('bookings:room_detail', pk=room_id)
    else:
        form = RoomForm(instance=room)
    
    return render(request, 'bookings/room_form.html', {'form': form, 'venue': room.venue, 'action': 'Update'})


@login_required
def room_delete(request, room_id):
    """Delete a room"""
    room = get_object_or_404(Room, pk=room_id)
    venue_id = room.venue.id
    
    # Check if user is authorized to delete this room
    if room.venue.owner != request.user and not request.user.is_staff:
        messages.error(request, "You don't have permission to delete this room.")
        return redirect('bookings:room_detail', pk=room_id)
    
    if request.method == 'POST':
        room.delete()
        messages.success(request, 'Room deleted successfully!')
        return redirect('bookings:venue_detail', pk=venue_id)
    
    return render(request, 'bookings/room_confirm_delete.html', {'room': room})


def venue_list(request):
    """List all active venues with filtering options"""
    queryset = Venue.objects.filter(is_active=True).annotate(avg_rating=Avg('reviews__rating'))
    
    # Filter by venue type (category)
    venue_type = request.GET.get('type')
    if venue_type:
        queryset = queryset.filter(category__name__icontains=venue_type)
        
    # Filter by amenities
    amenities = request.GET.getlist('amenities')
    if amenities:
        for amenity in amenities:
            queryset = queryset.filter(amenities__name__icontains=amenity)
        
    # Filter by price range
    price_range = request.GET.get('price_range')
    if price_range:
        if price_range == '0-1000':
            queryset = queryset.filter(rooms__price_per_hour__lte=1000)
        elif price_range == '1000-2000':
            queryset = queryset.filter(rooms__price_per_hour__gte=1000, rooms__price_per_hour__lte=2000)
        elif price_range == '2000-5000':
            queryset = queryset.filter(rooms__price_per_hour__gte=2000, rooms__price_per_hour__lte=5000)
        elif price_range == '5000+':
            queryset = queryset.filter(rooms__price_per_hour__gte=5000)
    
    # Filter by capacity
    capacity = request.GET.get('capacity')
    if capacity:
        if capacity == '1-10':
            queryset = queryset.filter(max_capacity__lte=10)
        elif capacity == '11-50':
            queryset = queryset.filter(max_capacity__gte=11, max_capacity__lte=50)
        elif capacity == '51-100':
            queryset = queryset.filter(max_capacity__gte=51, max_capacity__lte=100)
        elif capacity == '100+':
            queryset = queryset.filter(max_capacity__gte=100)
        
    # Filter by rating
    rating = request.GET.get('rating')
    if rating:
        if rating == '4+':
            queryset = queryset.filter(avg_rating__gte=4)
        elif rating == '3+':
            queryset = queryset.filter(avg_rating__gte=3)
        elif rating == '2+':
            queryset = queryset.filter(avg_rating__gte=2)
    
    # Get filters for context
    categories = VenueCategory.objects.all()
    amenities_list = Amenity.objects.all()
    
    context = {
        'venue_list': queryset.distinct(),
        'categories': categories,
        'amenities': amenities_list,
        'venue_type': venue_type or '',
        'selected_amenities': amenities or [],
        'price_range': price_range or '',
        'capacity': capacity or '',
        'rating': rating or ''
    }
    
    return render(request, 'bookings/venue_list.html', context)

def venue_detail(request, pk):
    """Show details for a specific venue"""
    venue = get_object_or_404(Venue, pk=pk)
    
    # Get rooms for this venue
    rooms = venue.rooms.filter(is_active=True)
    
    # Get reviews for this venue
    reviews = venue.reviews.all().order_by('-created_at')[:5]
    review_count = venue.reviews.count()
    
    # Check if user has favorited this venue
    is_favorite = False
    if request.user.is_authenticated:
        is_favorite = Favorite.objects.filter(
            user=request.user, 
            venue=venue
        ).exists()
    
    context = {
        'venue': venue,
        'rooms': rooms,
        'reviews': reviews,
        'review_count': review_count,
        'is_favorite': is_favorite
    }
    
    return render(request, 'bookings/venue_detail.html', context)

def room_detail(request, venue_id, room_id):
    """Show details for a specific room"""
    venue = get_object_or_404(Venue, pk=venue_id)
    room = get_object_or_404(Room, pk=room_id, venue=venue)
    
    # Get available time slots for the next 7 days
    today = timezone.now().date()
    next_week = today + timezone.timedelta(days=7)
    time_slots = room.time_slots.filter(
        start_time__date__gte=today,
        start_time__date__lte=next_week,
        is_available=True
    ).order_by('start_time')
    
    # Add user wallet balance to context
    wallet_balance = 0
    if request.user.is_authenticated:
        wallet_balance = request.user.wallet_balance
    
    context = {
        'venue': venue,
        'room': room,
        'time_slots': time_slots,
        'wallet_balance': wallet_balance
    }
    
    return render(request, 'bookings/room_detail.html', context)

@login_required
def user_bookings(request):
    """Show bookings for the logged-in user"""
    bookings = Booking.objects.filter(user=request.user).order_by('-created_at')
    
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
        'bookings': bookings,
        'wallet_balance': request.user.wallet_balance,
        'recent_transactions': WalletTransaction.objects.filter(
            user=request.user
        ).order_by('-created_at')[:5]
    }
    
    return render(request, 'bookings/user_bookings.html', context)

@login_required
def booking_detail(request, booking_id):
    """Show details for a specific booking"""
    booking = get_object_or_404(Booking, booking_id=booking_id)
    
    # Check if the user is authorized to view this booking
    if booking.user != request.user and booking.room.venue.owner != request.user and not request.user.is_staff:
        messages.error(request, "You don't have permission to view this booking.")
        return redirect('bookings:user_bookings')
    
    context = {
        'booking': booking,
        'now': timezone.now()  # Add current time for template comparison
    }
    
    return render(request, 'bookings/booking_detail.html', context)
