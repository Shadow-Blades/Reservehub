from django.shortcuts import redirect, render
from django.views.generic import TemplateView

def home_view(request):
    """
    Home view that redirects authenticated users to their appropriate dashboards
    based on their user type, or shows the home page to unauthenticated users.
    """
    # Check if the user is authenticated
    if request.user.is_authenticated:
        # Redirect based on user type
        if request.user.user_type == 'admin':
            # Admin users go to admin dashboard
            return redirect('admin_dashboard')
        elif request.user.user_type == 'host':
            # Host users go to host dashboard
            return redirect('bookings:host_dashboard')
        else:
            # Regular users see the home page
            return render(request, 'home.html')
    else:
        # Unauthenticated users see the home page
        return render(request, 'home.html') 