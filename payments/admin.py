from django.contrib import admin
from .models import PaymentMethod, Transaction, Invoice


@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ['user', 'payment_type', 'name', 'is_default']
    list_filter = ['payment_type', 'is_default']
    search_fields = ['user__email', 'user__username', 'name']


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['transaction_id', 'user', 'booking', 'amount', 'currency', 'status', 'created_at']
    list_filter = ['status', 'currency', 'created_at']
    search_fields = ['transaction_id', 'user__email', 'booking__booking_id']
    readonly_fields = ['transaction_id']


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ['invoice_number', 'booking', 'user', 'total_amount', 'issued_date', 'due_date', 'status']
    list_filter = ['status', 'issued_date', 'due_date']
    search_fields = ['invoice_number', 'user__email', 'booking__booking_id']
    readonly_fields = ['invoice_number', 'issued_date']
    fieldsets = (
        (None, {
            'fields': ('invoice_number', 'booking', 'user')
        }),
        ('Invoice Details', {
            'fields': ('issued_date', 'due_date', 'total_amount', 'status', 'notes')
        }),
    )
