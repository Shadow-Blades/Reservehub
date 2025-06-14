from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    # Wallet
    path('wallet/', views.wallet, name='wallet'),
    
    # Payment methods
    path('methods/', views.PaymentMethodListView.as_view(), name='payment_methods'),
    path('methods/create/', views.PaymentMethodCreateView.as_view(), name='payment_method_create'),
    path('methods/<int:pk>/update/', views.PaymentMethodUpdateView.as_view(), name='payment_method_update'),
    path('methods/<int:pk>/delete/', views.PaymentMethodDeleteView.as_view(), name='payment_method_delete'),
    path('methods/<int:pk>/set-default/', views.set_default_payment_method, name='set_default_payment_method'),
    
    # Transactions
    path('transactions/', views.TransactionListView.as_view(), name='transaction_list'),
    path('transaction/<uuid:transaction_id>/', views.TransactionDetailView.as_view(), name='transaction_detail'),
    
    # Checkout
    path('checkout/<uuid:booking_id>/', views.checkout, name='checkout'),
    path('checkout/success/<uuid:booking_id>/', views.checkout_success, name='checkout_success'),
    path('checkout/failed/<uuid:booking_id>/', views.checkout_failed, name='checkout_failed'),
    
    # Invoices
    path('invoices/', views.InvoiceListView.as_view(), name='invoice_list'),
    path('invoice/<str:invoice_number>/', views.InvoiceDetailView.as_view(), name='invoice_detail'),
    path('invoice/<str:invoice_number>/download/', views.invoice_download, name='invoice_download'),
    
    # Stripe webhook
    path('webhook/stripe/', views.stripe_webhook, name='stripe_webhook'),
] 