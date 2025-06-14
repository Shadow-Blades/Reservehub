from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .forms import CustomUserCreationForm, CustomUserChangeForm
from .models import CustomUser, WalletTransaction


class CustomUserAdmin(UserAdmin):
    """Custom admin for our user model"""
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = CustomUser
    list_display = ['email', 'username', 'user_type', 'phone_number', 'is_verified', 'is_staff', 'wallet_balance']
    list_filter = ['user_type', 'is_verified', 'is_staff', 'is_superuser']
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('user_type', 'phone_number', 'profile_image',
                                       'bio', 'address', 'city', 'state', 
                                       'postal_code', 'country', 'is_verified', 'wallet_balance')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Additional Info', {'fields': ('user_type', 'phone_number', 'wallet_balance')}),
    )
    search_fields = ['email', 'username', 'phone_number']
    ordering = ['email']


class WalletTransactionAdmin(admin.ModelAdmin):
    """Admin for wallet transactions"""
    list_display = ['user', 'amount', 'transaction_type', 'description', 'created_at']
    list_filter = ['transaction_type', 'created_at']
    search_fields = ['user__email', 'user__username', 'description', 'reference_id']
    date_hierarchy = 'created_at'


admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(WalletTransaction, WalletTransactionAdmin)
