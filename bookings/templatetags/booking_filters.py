from django import template
from django.utils import timezone

register = template.Library()

@register.filter
def filter_upcoming(bookings):
    """Filter bookings to show only upcoming ones (start time in future and not cancelled)"""
    now = timezone.now()
    return [b for b in bookings if b.start_time > now and b.status != 'cancelled']

@register.filter
def filter_past(bookings):
    """Filter bookings to show only past ones (start time in past and not cancelled)"""
    now = timezone.now()
    return [b for b in bookings if b.start_time <= now and b.status != 'cancelled']

@register.filter
def filter_cancelled(bookings):
    """Filter bookings to show only cancelled ones"""
    return [b for b in bookings if b.status == 'cancelled'] 