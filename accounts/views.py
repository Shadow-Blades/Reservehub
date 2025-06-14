from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate, get_user_model
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from .forms import CustomUserCreationForm, ProfileUpdateForm, OTPVerificationForm, PasswordResetForm

class CustomLoginView(LoginView):
    template_name = 'account/login.html'
    
    def get_success_url(self):
        user = self.request.user
        if user.user_type == 'admin':
            return reverse_lazy('admin_dashboard')
        elif user.user_type == 'host':
            return reverse_lazy('bookings:host_dashboard')
        return reverse_lazy('home')

def signup_view(request):
    """Handle user registration"""
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Account created successfully!')
            
            # Redirect based on user type
            if user.user_type == 'host':
                return redirect('bookings:host_dashboard')
            elif user.user_type == 'admin':
                return redirect('admin_dashboard')
            return redirect('home')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'account/signup.html', {'form': form})

@login_required
def profile_view(request):
    """Handle user profile update"""
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('accounts:profile')
    else:
        form = ProfileUpdateForm(instance=request.user)
    
    return render(request, 'account/profile.html', {'form': form})

@require_http_methods(["GET", "POST"])
def logout_view(request):
    """Handle user logout with both GET and POST requests"""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('home')

def password_reset_request(request):
    """Handle password reset request"""
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = get_user_model().objects.get(email=email)
            # In a real system, you would send OTP via email
            # For now, we'll just show the OTP verification page
            request.session['reset_email'] = email
            return redirect('accounts:verify_otp')
        except get_user_model().DoesNotExist:
            messages.error(request, 'No user found with this email address.')
    
    return render(request, 'account/password_reset.html')

def verify_otp(request):
    """Verify OTP and show password reset form"""
    if 'reset_email' not in request.session:
        return redirect('accounts:password_reset')
    
    if request.method == 'POST':
        form = OTPVerificationForm(request.POST)
        if form.is_valid():
            return redirect('accounts:reset_password')
    else:
        form = OTPVerificationForm()
    
    return render(request, 'account/verify_otp.html', {'form': form})

def reset_password(request):
    """Handle password reset"""
    if 'reset_email' not in request.session:
        return redirect('accounts:password_reset')
    
    if request.method == 'POST':
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            email = request.session['reset_email']
            user = get_user_model().objects.get(email=email)
            user.set_password(form.cleaned_data['new_password1'])
            user.save()
            del request.session['reset_email']
            messages.success(request, 'Your password has been reset successfully.')
            return redirect('accounts:login')
    else:
        form = PasswordResetForm()
    
    return render(request, 'account/reset_password.html', {'form': form})
