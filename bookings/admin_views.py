from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Count, Avg, Q, Sum
from django.forms import modelformset_factory
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import json

from .models import (
    Venue, Room, VenueImage, RoomImage, Booking, 
    Review, TimeSlot, VenueCategory, Amenity
)
from accounts.models import CustomUser

from .forms import VenueForm, VenueImageForm, RoomForm, RoomImageForm, AmenityForm, CategoryForm
from payments.models import Transaction, Invoice, PaymentDistribution

# Admin access check
def is_admin(user):
    return user.is_authenticated and user.user_type == 'admin'

# Dashboard
@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    """
    Admin dashboard view showing platform statistics and allowing venue management.
    """
    # Calculate statistics
    total_bookings = Booking.objects.count()
    total_revenue = Booking.objects.filter(status__in=['confirmed', 'completed']).aggregate(
        total=Sum('total_price'))['total'] or 0
    
    # Calculate admin earnings (10% of all transactions)
    admin_earnings = PaymentDistribution.objects.aggregate(
        total=Sum('admin_amount'))['total'] or 0
    
    # Calculate pending payments to owners
    pending_payouts = PaymentDistribution.objects.filter(
        is_paid_to_owner=False).aggregate(
        total=Sum('owner_amount'))['total'] or 0
    
    active_users = CustomUser.objects.filter(is_active=True).count()
    total_venues = Venue.objects.count()
    
    # Get recent bookings with status colors
    recent_bookings = Booking.objects.select_related('room__venue', 'user').order_by('-created_at')[:10]
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
    
    # Get venues for management
    venues = Venue.objects.select_related('owner').all()
    
    # Generate revenue data for chart (last 6 months)
    revenue_data = {}
    admin_revenue_data = {}
    labels = []
    revenue_values = []
    admin_revenue_values = []
    
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=180)  # Last 6 months
    
    # Generate monthly revenue data
    for i in range(6):
        month_start = (end_date - timedelta(days=30 * i))
        month_end = (end_date - timedelta(days=30 * (i-1))) if i > 0 else end_date
        
        month_name = month_start.strftime('%b')
        labels.insert(0, month_name)
        
        # Total revenue for the month
        month_revenue = Booking.objects.filter(
            status__in=['confirmed', 'completed'],
            start_time__date__gte=month_start,
            start_time__date__lte=month_end
        ).aggregate(Sum('total_price'))['total_price__sum'] or 0
        
        revenue_values.insert(0, month_revenue)
        
        # Admin revenue for the month (10% of transactions)
        admin_month_revenue = PaymentDistribution.objects.filter(
            transaction__created_at__date__gte=month_start,
            transaction__created_at__date__lte=month_end
        ).aggregate(Sum('admin_amount'))['admin_amount__sum'] or 0
        
        admin_revenue_values.insert(0, admin_month_revenue)
    
    revenue_data = {
        'labels': labels,
        'data': revenue_values
    }
    
    admin_revenue_data = {
        'labels': labels,
        'data': admin_revenue_values
    }
    
    # Generate user growth data (last 6 months)
    user_data = {}
    user_labels = []
    user_counts = []
    
    for i in range(6):
        month_start = (end_date - timedelta(days=30 * i))
        month_name = month_start.strftime('%b')
        user_labels.insert(0, month_name)
        
        new_users = CustomUser.objects.filter(
            date_joined__year=month_start.year,
            date_joined__month=month_start.month
        ).count()
        
        user_counts.insert(0, new_users)
    
    user_growth_data = {
        'labels': user_labels,
        'data': user_counts
    }
    
    # Get recent payment distributions
    recent_distributions = PaymentDistribution.objects.select_related(
        'transaction', 'owner', 'transaction__booking__room__venue'
    ).order_by('-created_at')[:10]
    
    context = {
        'total_bookings': total_bookings,
        'total_revenue': total_revenue,
        'admin_earnings': admin_earnings,
        'pending_payouts': pending_payouts,
        'active_users': active_users,
        'total_venues': total_venues,
        'recent_bookings': recent_bookings,
        'recent_distributions': recent_distributions,
        'venues': venues,
        'revenue_data': json.dumps(revenue_data),
        'admin_revenue_data': json.dumps(admin_revenue_data),
        'user_growth_data': json.dumps(user_growth_data),
    }
    
    return render(request, 'admin/dashboard.html', context)

@staff_member_required
@require_POST
def toggle_venue_status(request, venue_id):
    """
    Toggle a venue's active status (enable/disable).
    """
    venue = get_object_or_404(Venue, pk=venue_id)
    data = json.loads(request.body)
    new_status = data.get('status')
    
    if new_status == 'active':
        venue.is_active = True
    else:
        venue.is_active = False
    
    venue.save()
    
    return JsonResponse({'success': True})

@staff_member_required
@require_POST
def remove_venue(request, venue_id):
    """
    Remove a venue from the platform.
    """
    venue = get_object_or_404(Venue, pk=venue_id)
    venue.delete()
    
    return JsonResponse({'success': True})

# Venues
@login_required
@user_passes_test(is_admin)
def admin_venues(request):
    venues_list = Venue.objects.select_related('category', 'owner').prefetch_related('rooms', 'images')
    categories = VenueCategory.objects.all()
    
    # Search and filter
    q = request.GET.get('q')
    category_id = request.GET.get('category')
    
    if q:
        venues_list = venues_list.filter(
            Q(name__icontains=q) | 
            Q(city__icontains=q) | 
            Q(state__icontains=q) |
            Q(country__icontains=q)
        )
    
    if category_id:
        venues_list = venues_list.filter(category_id=category_id)
    
    # Pagination
    paginator = Paginator(venues_list, 10)
    page = request.GET.get('page', 1)
    venues = paginator.get_page(page)
    
    context = {
        'active_tab': 'venues',
        'venues': venues,
        'categories': categories,
        'paginator': paginator,
        'page_obj': venues,
    }
    
    return render(request, 'admin/venues.html', context)

@login_required
@user_passes_test(is_admin)
def admin_venues_add(request):
    # Create image formset
    ImageFormSet = modelformset_factory(
        VenueImage, 
        form=VenueImageForm,
        extra=1,
        can_delete=False
    )
    
    if request.method == 'POST':
        form = VenueForm(request.POST)
        formset = ImageFormSet(request.POST, request.FILES, queryset=VenueImage.objects.none(), prefix='images')
        
        if form.is_valid() and formset.is_valid():
            # Save venue
            venue = form.save()
            
            # Save images
            for image_form in formset:
                if image_form.cleaned_data.get('image'):
                    image = image_form.save(commit=False)
                    image.venue = venue
                    image.save()
            
            messages.success(request, f"Venue '{venue.name}' has been created successfully.")
            return redirect('admin_venues')
    else:
        form = VenueForm()
        formset = ImageFormSet(queryset=VenueImage.objects.none(), prefix='images')
    
    context = {
        'active_tab': 'venues',
        'form': form,
        'formset': formset,
        'title': 'Add New Venue'
    }
    
    return render(request, 'admin/venue_form.html', context)

@login_required
@user_passes_test(is_admin)
def admin_venues_edit(request, pk):
    venue = get_object_or_404(Venue, pk=pk)
    
    # Create image formset
    ImageFormSet = modelformset_factory(
        VenueImage, 
        form=VenueImageForm,
        extra=1,
        can_delete=True
    )
    
    if request.method == 'POST':
        form = VenueForm(request.POST, instance=venue)
        formset = ImageFormSet(request.POST, request.FILES, queryset=venue.images.all(), prefix='images')
        
        if form.is_valid() and formset.is_valid():
            # Save venue
            venue = form.save()
            
            # Save images
            for image_form in formset:
                if image_form.cleaned_data.get('DELETE'):
                    if image_form.instance.pk:
                        image_form.instance.delete()
                elif image_form.cleaned_data.get('image') or image_form.instance.pk:
                    image = image_form.save(commit=False)
                    image.venue = venue
                    image.save()
            
            messages.success(request, f"Venue '{venue.name}' has been updated successfully.")
            return redirect('admin_venues')
    else:
        form = VenueForm(instance=venue)
        formset = ImageFormSet(queryset=venue.images.all(), prefix='images')
    
    context = {
        'active_tab': 'venues',
        'form': form,
        'formset': formset,
        'title': f"Edit Venue: {venue.name}"
    }
    
    return render(request, 'admin/venue_form.html', context)

@login_required
@user_passes_test(is_admin)
def admin_venues_detail(request, pk):
    venue = get_object_or_404(
        Venue.objects.select_related('category', 'owner').prefetch_related('images', 'rooms', 'amenities'),
        pk=pk
    )
    
    # Get bookings for this venue
    bookings = Booking.objects.filter(room__venue=venue).order_by('-created_at')[:10]
    
    # Get reviews for this venue
    reviews = Review.objects.filter(venue=venue).order_by('-created_at')[:5]
    
    context = {
        'active_tab': 'venues',
        'venue': venue,
        'bookings': bookings,
        'reviews': reviews,
    }
    
    return render(request, 'admin/venue_detail.html', context)

@login_required
@user_passes_test(is_admin)
def admin_venues_delete(request, pk):
    venue = get_object_or_404(Venue, pk=pk)
    
    if request.method == 'POST':
        venue_name = venue.name
        venue.delete()
        messages.success(request, f"Venue '{venue_name}' has been deleted successfully.")
        return redirect('admin_venues')
    
    return redirect('admin_venues_detail', pk=pk)

# Rooms
@login_required
@user_passes_test(is_admin)
def admin_rooms(request):
    rooms_list = Room.objects.select_related('venue')
    venues = Venue.objects.all()
    
    # Search and filter
    q = request.GET.get('q')
    venue_id = request.GET.get('venue')
    
    if q:
        rooms_list = rooms_list.filter(
            Q(name__icontains=q) | 
            Q(venue__name__icontains=q)
        )
    
    if venue_id:
        rooms_list = rooms_list.filter(venue_id=venue_id)
    
    # Pagination
    paginator = Paginator(rooms_list, 10)
    page = request.GET.get('page', 1)
    rooms = paginator.get_page(page)
    
    context = {
        'active_tab': 'rooms',
        'rooms': rooms,
        'venues': venues,
        'paginator': paginator,
        'page_obj': rooms,
    }
    
    return render(request, 'admin/rooms.html', context)

@login_required
@user_passes_test(is_admin)
def admin_rooms_add(request):
    # Create image formset
    ImageFormSet = modelformset_factory(
        RoomImage, 
        form=RoomImageForm,
        extra=1,
        can_delete=False
    )
    
    if request.method == 'POST':
        form = RoomForm(request.POST)
        formset = ImageFormSet(request.POST, request.FILES, queryset=RoomImage.objects.none(), prefix='images')
        
        if form.is_valid() and formset.is_valid():
            # Save room
            room = form.save()
            
            # Save images
            for image_form in formset:
                if image_form.cleaned_data.get('image'):
                    image = image_form.save(commit=False)
                    image.room = room
                    image.save()
            
            messages.success(request, f"Room '{room.name}' has been created successfully.")
            return redirect('admin_rooms')
    else:
        form = RoomForm()
        formset = ImageFormSet(queryset=RoomImage.objects.none(), prefix='images')
    
    context = {
        'active_tab': 'rooms',
        'form': form,
        'formset': formset,
        'title': 'Add New Room'
    }
    
    return render(request, 'admin/room_form.html', context)

# Categories
@login_required
@user_passes_test(is_admin)
def admin_categories(request):
    categories = VenueCategory.objects.annotate(venue_count=Count('venues'))
    
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            category = form.save()
            messages.success(request, f"Category '{category.name}' has been created successfully.")
            return redirect('admin_categories')
    else:
        form = CategoryForm()
    
    context = {
        'active_tab': 'categories',
        'categories': categories,
        'form': form,
    }
    
    return render(request, 'admin/categories.html', context)

# Amenities
@login_required
@user_passes_test(is_admin)
def admin_amenities(request):
    amenities = Amenity.objects.annotate(venue_count=Count('venues'), room_count=Count('rooms'))
    
    if request.method == 'POST':
        form = AmenityForm(request.POST)
        if form.is_valid():
            amenity = form.save()
            messages.success(request, f"Amenity '{amenity.name}' has been created successfully.")
            return redirect('admin_amenities')
    else:
        form = AmenityForm()
    
    context = {
        'active_tab': 'amenities',
        'amenities': amenities,
        'form': form,
    }
    
    return render(request, 'admin/amenities.html', context)

# Bookings
@login_required
@user_passes_test(is_admin)
def admin_bookings(request):
    bookings_list = Booking.objects.select_related('user', 'room', 'room__venue')
    
    # Search and filter
    q = request.GET.get('q')
    status = request.GET.get('status')
    
    if q:
        bookings_list = bookings_list.filter(
            Q(booking_id__icontains=q) | 
            Q(user__email__icontains=q) |
            Q(room__venue__name__icontains=q)
        )
    
    if status:
        bookings_list = bookings_list.filter(status=status)
    
    # Pagination
    paginator = Paginator(bookings_list, 10)
    page = request.GET.get('page', 1)
    bookings = paginator.get_page(page)
    
    context = {
        'active_tab': 'bookings',
        'bookings': bookings,
        'paginator': paginator,
        'page_obj': bookings,
    }
    
    return render(request, 'admin/bookings.html', context)

# Reviews
@login_required
@user_passes_test(is_admin)
def admin_reviews(request):
    reviews_list = Review.objects.select_related('user', 'venue', 'booking')
    
    # Search and filter
    q = request.GET.get('q')
    rating = request.GET.get('rating')
    
    if q:
        reviews_list = reviews_list.filter(
            Q(comment__icontains=q) | 
            Q(user__email__icontains=q) |
            Q(venue__name__icontains=q)
        )
    
    if rating:
        reviews_list = reviews_list.filter(rating=rating)
    
    # Pagination
    paginator = Paginator(reviews_list, 10)
    page = request.GET.get('page', 1)
    reviews = paginator.get_page(page)
    
    context = {
        'active_tab': 'reviews',
        'reviews': reviews,
        'paginator': paginator,
        'page_obj': reviews,
        'ratings': range(1, 6),
    }
    
    return render(request, 'admin/reviews.html', context)

# Users
@login_required
@user_passes_test(is_admin)
def admin_users(request):
    users_list = CustomUser.objects.all()
    
    # Search and filter
    q = request.GET.get('q')
    user_type = request.GET.get('user_type')
    
    if q:
        users_list = users_list.filter(
            Q(email__icontains=q) | 
            Q(username__icontains=q) |
            Q(first_name__icontains=q) |
            Q(last_name__icontains=q)
        )
    
    if user_type:
        users_list = users_list.filter(user_type=user_type)
    
    # Pagination
    paginator = Paginator(users_list, 10)
    page = request.GET.get('page', 1)
    users = paginator.get_page(page)
    
    context = {
        'active_tab': 'users',
        'users': users,
        'paginator': paginator,
        'page_obj': users,
    }
    
    return render(request, 'admin/users.html', context)

# Admin settings
@login_required
@user_passes_test(is_admin)
def admin_settings(request):
    context = {
        'active_tab': 'settings',
    }
    
    return render(request, 'admin/settings.html', context) 