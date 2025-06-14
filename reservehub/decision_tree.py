"""
Decision tree for routing users to their appropriate dashboards based on user type.
This file handles the routing logic for different types of users in the ReserveHub application.
"""

from django.shortcuts import redirect
from django.urls import reverse

def route_user_to_dashboard(user):
    """
    Routes a user to their appropriate dashboard based on their user type.
    
    Args:
        user: The user object from request.user
    
    Returns:
        A redirect to the appropriate dashboard URL
    """
    if not user.is_authenticated:
        # Unauthenticated users go to home page
        return redirect('home')
    
    # Route based on user type
    if user.user_type == 'admin':
        # Admin users go to admin dashboard
        return redirect('admin_dashboard')
    elif user.user_type == 'host':
        # Host users go to their host dashboard
        return redirect('bookings:host_dashboard')
    else:
        # Regular customers go to home page
        return redirect('home')

def get_dashboard_url(user_type):
    """
    Returns the appropriate dashboard URL based on user type without redirecting
    
    Args:
        user_type: String indicating user type ('admin', 'host', or 'customer')
    
    Returns:
        String URL for the user's dashboard
    """
    if user_type == 'admin':
        return reverse('admin_dashboard')
    elif user_type == 'host':
        return reverse('bookings:host_dashboard')
    else:
        return reverse('home') 