from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from decimal import Decimal


class CustomUser(AbstractUser):
    """Extended user model for ReserveHub"""
    USER_TYPE_CHOICES = (
        ('customer', 'Customer'),
        ('host', 'Host'),
        ('admin', 'Admin'),
    )
    
    user_type = models.CharField(_('User Type'), max_length=10, choices=USER_TYPE_CHOICES, default='customer')
    phone_number = models.CharField(_('Phone Number'), max_length=15, blank=True, null=True)
    profile_image = models.ImageField(_('Profile Image'), upload_to='profile_images/', blank=True, null=True)
    bio = models.TextField(_('Bio'), blank=True, null=True)
    address = models.CharField(_('Address'), max_length=255, blank=True, null=True)
    city = models.CharField(_('City'), max_length=100, blank=True, null=True)
    state = models.CharField(_('State'), max_length=100, blank=True, null=True)
    postal_code = models.CharField(_('Postal Code'), max_length=20, blank=True, null=True)
    country = models.CharField(_('Country'), max_length=100, blank=True, null=True)
    date_joined = models.DateTimeField(_('Date Joined'), auto_now_add=True)
    is_verified = models.BooleanField(_('Is Verified'), default=False)
    wallet_balance = models.DecimalField(_('Wallet Balance'), max_digits=10, decimal_places=2, default=1000.00)
    
    def __str__(self):
        return self.username
        
    @property
    def full_address(self):
        """Returns the user's full address"""
        address_parts = [
            part for part in [
                self.address,
                self.city,
                self.state,
                self.postal_code,
                self.country
            ] if part
        ]
        return ", ".join(address_parts)
        
    def save(self, *args, **kwargs):
        # Set default wallet balance based on user type when creating a new user
        if not self.pk:  # Only for new users
            if self.user_type in ['host', 'admin']:
                self.wallet_balance = 0.00
            else:  # customer
                self.wallet_balance = 1000.00
        super().save(*args, **kwargs)
        
    def add_to_wallet(self, amount):
        """Add amount to user wallet"""
        self.wallet_balance += Decimal(str(amount))
        self.save(update_fields=['wallet_balance'])
        return self.wallet_balance
    
    def deduct_from_wallet(self, amount):
        """Deduct amount from user wallet if sufficient balance exists"""
        decimal_amount = Decimal(str(amount))
        if self.wallet_balance >= decimal_amount:
            self.wallet_balance -= decimal_amount
            self.save(update_fields=['wallet_balance'])
            return True
        return False


class WalletTransaction(models.Model):
    """Model for tracking wallet transactions"""
    TRANSACTION_TYPES = (
        ('booking', 'Booking Payment'),
        ('refund', 'Booking Refund'),
        ('deposit', 'Deposit'),
        ('withdrawal', 'Withdrawal'),
        ('bonus', 'Bonus'),
    )
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='wallet_transactions')
    amount = models.DecimalField(_('Amount'), max_digits=10, decimal_places=2)
    transaction_type = models.CharField(_('Transaction Type'), max_length=20, choices=TRANSACTION_TYPES)
    description = models.CharField(_('Description'), max_length=255)
    reference_id = models.CharField(_('Reference ID'), max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.transaction_type} - {self.amount} - {self.user.username}"
