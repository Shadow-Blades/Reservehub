from django import forms
from .models import Venue, Room, VenueImage, RoomImage, Amenity, VenueCategory, Review, Booking
from accounts.models import CustomUser

class VenueForm(forms.ModelForm):
    class Meta:
        model = Venue
        fields = [
            'name', 'category', 'description', 'address', 'city', 
            'state', 'postal_code', 'country', 'latitude', 'longitude',
            'phone', 'email', 'website', 'max_capacity', 'amenities',
            'owner', 'is_active'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'latitude': forms.NumberInput(attrs={'step': '0.000001'}),
            'longitude': forms.NumberInput(attrs={'step': '0.000001'}),
            'amenities': forms.CheckboxSelectMultiple(),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter owners to only be users with host user_type
        self.fields['owner'].queryset = CustomUser.objects.filter(user_type='host')


class VenueImageForm(forms.ModelForm):
    class Meta:
        model = VenueImage
        fields = ['image', 'caption', 'is_primary']
        widgets = {
            'caption': forms.TextInput(attrs={'placeholder': 'Image caption'}),
        }


class RoomForm(forms.ModelForm):
    class Meta:
        model = Room
        fields = [
            'venue', 'name', 'description', 'capacity', 'size_sqft',
            'price_per_hour', 'amenities', 'is_active'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'amenities': forms.CheckboxSelectMultiple(),
        }


class RoomImageForm(forms.ModelForm):
    class Meta:
        model = RoomImage
        fields = ['image', 'caption', 'is_primary']
        widgets = {
            'caption': forms.TextInput(attrs={'placeholder': 'Image caption'}),
        }


class CategoryForm(forms.ModelForm):
    class Meta:
        model = VenueCategory
        fields = ['name', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }


class AmenityForm(forms.ModelForm):
    class Meta:
        model = Amenity
        fields = ['name', 'icon', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'icon': forms.TextInput(attrs={'placeholder': 'Font Awesome icon class (e.g., fa-wifi)'}),
        }


class BookingFilterForm(forms.Form):
    STATUS_CHOICES = (
        ('', 'All Statuses'),
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    )
    
    q = forms.CharField(
        label='Search',
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Search bookings...'})
    )
    status = forms.ChoiceField(
        label='Status',
        choices=STATUS_CHOICES,
        required=False
    )


class ReviewFilterForm(forms.Form):
    RATING_CHOICES = (
        ('', 'All Ratings'),
        ('5', '5 Stars'),
        ('4', '4 Stars'),
        ('3', '3 Stars'),
        ('2', '2 Stars'),
        ('1', '1 Star'),
    )
    
    q = forms.CharField(
        label='Search',
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Search reviews...'})
    )
    rating = forms.ChoiceField(
        label='Rating',
        choices=RATING_CHOICES,
        required=False
    ) 