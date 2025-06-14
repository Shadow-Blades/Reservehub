from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy, reverse
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models import PaymentMethod, Transaction, Invoice
from bookings.models import Booking

import stripe
import json
from datetime import datetime, timedelta


class PaymentMethodListView(LoginRequiredMixin, ListView):
    model = PaymentMethod
    template_name = 'payments/payment_method_list.html'
    context_object_name = 'payment_methods'
    
    def get_queryset(self):
        return PaymentMethod.objects.filter(user=self.request.user)


@login_required
def wallet(request):
    """View for managing user's wallet balance and adding funds"""
    user = request.user
    recent_transactions = Transaction.objects.filter(user=user).order_by('-created_at')[:10]
    
    context = {
        'wallet_balance': user.wallet_balance,
        'recent_transactions': recent_transactions
    }
    
    return render(request, 'payments/wallet.html', context)


class PaymentMethodCreateView(LoginRequiredMixin, CreateView):
    model = PaymentMethod
    template_name = 'payments/payment_method_form.html'
    fields = ['payment_type', 'name', 'is_default']
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('payments:payment_methods')


class PaymentMethodUpdateView(LoginRequiredMixin, UpdateView):
    model = PaymentMethod
    template_name = 'payments/payment_method_form.html'
    fields = ['payment_type', 'name', 'is_default']
    
    def get_queryset(self):
        return PaymentMethod.objects.filter(user=self.request.user)
    
    def get_success_url(self):
        return reverse('payments:payment_methods')


class PaymentMethodDeleteView(LoginRequiredMixin, DeleteView):
    model = PaymentMethod
    template_name = 'payments/payment_method_confirm_delete.html'
    success_url = reverse_lazy('payments:payment_methods')
    
    def get_queryset(self):
        return PaymentMethod.objects.filter(user=self.request.user)


@login_required
def set_default_payment_method(request, pk):
    payment_method = get_object_or_404(PaymentMethod, pk=pk, user=request.user)
    payment_method.is_default = True
    payment_method.save()  # This will trigger the save method that sets other methods to non-default
    
    messages.success(request, f"{payment_method.name} set as default payment method.")
    return redirect('payments:payment_methods')


class TransactionListView(LoginRequiredMixin, ListView):
    model = Transaction
    template_name = 'payments/transaction_list.html'
    context_object_name = 'transactions'
    paginate_by = 10
    
    def get_queryset(self):
        return Transaction.objects.filter(user=self.request.user).order_by('-created_at')


class TransactionDetailView(LoginRequiredMixin, DetailView):
    model = Transaction
    template_name = 'payments/transaction_detail.html'
    context_object_name = 'transaction'
    
    def get_object(self):
        transaction_id = self.kwargs.get('transaction_id')
        return get_object_or_404(Transaction, transaction_id=transaction_id, user=self.request.user)


@login_required
def checkout(request, booking_id):
    booking = get_object_or_404(Booking, booking_id=booking_id, user=request.user)
    
    # Check if the booking is already paid
    if Transaction.objects.filter(booking=booking, status='completed').exists():
        messages.info(request, "This booking has already been paid for.")
        return redirect('bookings:booking_detail', booking_id=booking_id)
    
    # Get user's payment methods
    payment_methods = PaymentMethod.objects.filter(user=request.user)
    default_payment_method = payment_methods.filter(is_default=True).first()
    
    if request.method == 'POST':
        payment_method_id = request.POST.get('payment_method')
        
        if payment_method_id:
            payment_method = get_object_or_404(PaymentMethod, pk=payment_method_id, user=request.user)
            
            # In a real implementation, this would integrate with Stripe or another payment processor
            # For now, we'll create a successful transaction
            transaction = Transaction.objects.create(
                booking=booking,
                user=request.user,
                payment_method=payment_method,
                amount=booking.total_price,
                status='completed'
            )
            
            # Note: Payment distribution is automatically created by the Transaction.save() method
            # which allocates 10% to admin and 90% to venue owner
            
            # Update booking status
            booking.status = 'confirmed'
            booking.save()
            
            # Create invoice
            invoice_number = f"INV-{datetime.now().strftime('%Y%m%d')}-{booking.id}"
            due_date = datetime.now().date() + timedelta(days=7)
            
            Invoice.objects.create(
                invoice_number=invoice_number,
                booking=booking,
                user=request.user,
                due_date=due_date,
                total_amount=booking.total_price,
                status='paid'
            )
            
            messages.success(request, "Payment successful! Your booking has been confirmed.")
            return redirect('payments:checkout_success', booking_id=booking_id)
        else:
            messages.error(request, "Please select a payment method.")
    
    context = {
        'booking': booking,
        'payment_methods': payment_methods,
        'default_payment_method': default_payment_method,
        'stripe_publishable_key': settings.STRIPE_PUBLISHABLE_KEY
    }
    
    return render(request, 'payments/checkout.html', context)


@login_required
def checkout_success(request, booking_id):
    booking = get_object_or_404(Booking, booking_id=booking_id, user=request.user)
    transaction = Transaction.objects.filter(booking=booking, status='completed').first()
    
    context = {
        'booking': booking,
        'transaction': transaction
    }
    
    return render(request, 'payments/checkout_success.html', context)


@login_required
def checkout_failed(request, booking_id):
    booking = get_object_or_404(Booking, booking_id=booking_id, user=request.user)
    transaction = Transaction.objects.filter(booking=booking, status='failed').first()
    
    context = {
        'booking': booking,
        'transaction': transaction,
        'error_message': request.GET.get('error', 'An error occurred during payment processing.')
    }
    
    return render(request, 'payments/checkout_failed.html', context)


class InvoiceListView(LoginRequiredMixin, ListView):
    model = Invoice
    template_name = 'payments/invoice_list.html'
    context_object_name = 'invoices'
    paginate_by = 10
    
    def get_queryset(self):
        return Invoice.objects.filter(user=self.request.user).order_by('-issued_date')


class InvoiceDetailView(LoginRequiredMixin, DetailView):
    model = Invoice
    template_name = 'payments/invoice_detail.html'
    context_object_name = 'invoice'
    
    def get_object(self):
        invoice_number = self.kwargs.get('invoice_number')
        return get_object_or_404(Invoice, invoice_number=invoice_number, user=self.request.user)


@login_required
def invoice_download(request, invoice_number):
    invoice = get_object_or_404(Invoice, invoice_number=invoice_number, user=request.user)
    
    # In a real implementation, this would generate a PDF invoice
    # For now, we'll just return a simple text response
    response = HttpResponse(content_type='text/plain')
    response['Content-Disposition'] = f'attachment; filename="{invoice_number}.txt"'
    
    response.write(f"Invoice: {invoice_number}\n")
    response.write(f"Date: {invoice.issued_date}\n")
    response.write(f"Due Date: {invoice.due_date}\n")
    response.write(f"Status: {invoice.get_status_display()}\n")
    response.write(f"Customer: {invoice.user.get_full_name() or invoice.user.username}\n")
    response.write(f"Booking ID: {invoice.booking.booking_id}\n")
    response.write(f"Venue: {invoice.booking.room.venue.name}\n")
    response.write(f"Room: {invoice.booking.room.name}\n")
    response.write(f"Date: {invoice.booking.start_time.strftime('%Y-%m-%d %H:%M')} - {invoice.booking.end_time.strftime('%H:%M')}\n")
    response.write(f"Amount: ${invoice.total_amount}\n")
    
    return response


@csrf_exempt
@require_POST
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        # Invalid payload
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        return HttpResponse(status=400)
    
    # Handle the event
    if event['type'] == 'payment_intent.succeeded':
        payment_intent = event['data']['object']
        # Extract metadata from the payment intent
        booking_id = payment_intent.get('metadata', {}).get('booking_id')
        
        if booking_id:
            try:
                booking = Booking.objects.get(booking_id=booking_id)
                
                # Update transaction status
                transaction = Transaction.objects.filter(booking=booking).first()
                if transaction:
                    transaction.status = 'completed'
                    transaction.gateway_response = json.dumps(payment_intent)
                    transaction.save()
                
                # Update booking status
                booking.status = 'confirmed'
                booking.save()
                
                # Update invoice status
                invoice = Invoice.objects.filter(booking=booking).first()
                if invoice:
                    invoice.status = 'paid'
                    invoice.save()
                
            except Booking.DoesNotExist:
                pass
    
    return HttpResponse(status=200)
