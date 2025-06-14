from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from bookings.models import Booking
import uuid
from decimal import Decimal


class PaymentMethod(models.Model):
    """Payment methods saved by users"""
    TYPE_CHOICES = (
        ('card', 'Credit/Debit Card'),
        ('paypal', 'PayPal'),
        ('bank', 'Bank Transfer'),
    )
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='payment_methods')
    payment_type = models.CharField(_('Payment Type'), max_length=10, choices=TYPE_CHOICES)
    name = models.CharField(_('Name'), max_length=100)
    is_default = models.BooleanField(_('Default Method'), default=False)
    # Card specific fields (encrypted in production)
    last_four = models.CharField(_('Last Four Digits'), max_length=4, blank=True, null=True)
    exp_month = models.CharField(_('Expiry Month'), max_length=2, blank=True, null=True)
    exp_year = models.CharField(_('Expiry Year'), max_length=4, blank=True, null=True)
    card_brand = models.CharField(_('Card Brand'), max_length=20, blank=True, null=True)
    # PayPal specific fields
    email = models.EmailField(_('Email'), blank=True, null=True)
    # Common fields
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)
    
    class Meta:
        ordering = ['-is_default', '-created_at']
        
    def __str__(self):
        if self.payment_type == 'card':
            return f"{self.card_brand} ending in {self.last_four}"
        elif self.payment_type == 'paypal':
            return f"PayPal ({self.email})"
        else:
            return self.name
    
    def save(self, *args, **kwargs):
        """Ensure only one default payment method per user"""
        if self.is_default:
            PaymentMethod.objects.filter(
                user=self.user, 
                is_default=True
            ).exclude(id=self.id).update(is_default=False)
        super().save(*args, **kwargs)


class Transaction(models.Model):
    """Payment transactions"""
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    )
    
    transaction_id = models.UUIDField(_('Transaction ID'), default=uuid.uuid4, editable=False, unique=True)
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='transactions')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='transactions')
    payment_method = models.ForeignKey(PaymentMethod, on_delete=models.SET_NULL, null=True, related_name='transactions')
    amount = models.DecimalField(_('Amount'), max_digits=10, decimal_places=2)
    currency = models.CharField(_('Currency'), max_length=3, default='USD')
    status = models.CharField(_('Status'), max_length=10, choices=STATUS_CHOICES, default='pending')
    gateway_response = models.TextField(_('Gateway Response'), blank=True, null=True)
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return f"Transaction {self.transaction_id} - {self.status}"
    
    @property
    def is_successful(self):
        return self.status == 'completed'
    
    def save(self, *args, **kwargs):
        """Override save method to create payment distribution when transaction is completed"""
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        # Create payment distribution when a transaction is completed
        if self.status == 'completed' and (is_new or 'status' in kwargs.get('update_fields', [])):
            # Check if distribution already exists
            if not PaymentDistribution.objects.filter(transaction=self).exists():
                # Calculate admin fee (10%) and owner amount (90%)
                admin_amount = self.amount * Decimal('0.1')
                owner_amount = self.amount - admin_amount
                
                PaymentDistribution.objects.create(
                    transaction=self,
                    admin_amount=admin_amount,
                    owner_amount=owner_amount,
                    owner=self.booking.room.venue.owner
                )


class Invoice(models.Model):
    """Invoices for bookings"""
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled'),
        ('overdue', 'Overdue'),
    )
    
    invoice_number = models.CharField(_('Invoice Number'), max_length=50, unique=True)
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='invoice')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='invoices')
    issued_date = models.DateField(_('Issued Date'), auto_now_add=True)
    due_date = models.DateField(_('Due Date'))
    total_amount = models.DecimalField(_('Total Amount'), max_digits=10, decimal_places=2)
    status = models.CharField(_('Status'), max_length=10, choices=STATUS_CHOICES, default='draft')
    notes = models.TextField(_('Notes'), blank=True, null=True)
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)
    
    class Meta:
        ordering = ['-issued_date']
        
    def __str__(self):
        return f"Invoice {self.invoice_number} - {self.status}"
    
    @property
    def is_paid(self):
        return self.status == 'paid'
    
    @property
    def is_overdue(self):
        from django.utils import timezone
        return self.due_date < timezone.now().date() and self.status != 'paid'


class PaymentDistribution(models.Model):
    """
    Tracks how payment is distributed between admin (platform) and venue owners
    Admin gets 10% of each booking payment, venue owner gets 90%
    """
    transaction = models.OneToOneField(Transaction, on_delete=models.CASCADE, related_name='distribution')
    admin_amount = models.DecimalField(_('Admin Amount (10%)'), max_digits=10, decimal_places=2)
    owner_amount = models.DecimalField(_('Owner Amount (90%)'), max_digits=10, decimal_places=2)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='earnings')
    is_paid_to_owner = models.BooleanField(_('Paid to Owner'), default=False)
    paid_date = models.DateTimeField(_('Paid Date'), null=True, blank=True)
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    
    def __str__(self):
        return f"Payment Distribution for {self.transaction.transaction_id}"
    
    @property
    def admin_percentage(self):
        """Calculate admin fee as percentage of total amount"""
        if self.transaction.amount > 0:
            return (self.admin_amount / self.transaction.amount) * 100
        return 0
    
    @property
    def owner_percentage(self):
        """Calculate owner amount as percentage of total amount"""
        if self.transaction.amount > 0:
            return (self.owner_amount / self.transaction.amount) * 100
        return 0
