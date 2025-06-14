from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db import transaction
from bookings.models import Amenity, VenueCategory, Venue, Room, TimeSlot, Review, VenueImage, RoomImage
import random
from datetime import timedelta

User = get_user_model()


class Command(BaseCommand):
    help = 'Seed the database with dummy hotels and restaurants'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting to seed dummy data...'))
        
        # Create amenities if they don't exist
        self.create_amenities()
        
        # Create categories if they don't exist
        self.create_categories()
        
        # Create demo users if they don't exist
        self.create_users()
        
        # Create venues and related data
        self.create_venues()
        
        self.stdout.write(self.style.SUCCESS('Dummy data seeding completed successfully!'))
    
    def create_amenities(self):
        amenities = [
            {'name': 'Wi-Fi', 'icon': 'fa-wifi', 'description': 'Free high-speed Wi-Fi'},
            {'name': 'Parking', 'icon': 'fa-car', 'description': 'On-site parking available'},
            {'name': 'Air Conditioning', 'icon': 'fa-snowflake', 'description': 'Climate controlled environment'},
            {'name': 'Projector', 'icon': 'fa-projector', 'description': 'High-definition projector'},
            {'name': 'Catering', 'icon': 'fa-utensils', 'description': 'Catering services available'},
            {'name': 'Swimming Pool', 'icon': 'fa-swimming-pool', 'description': 'Outdoor swimming pool'},
            {'name': 'Gym', 'icon': 'fa-dumbbell', 'description': 'Fitness center'},
            {'name': 'Bar', 'icon': 'fa-glass-martini', 'description': 'On-site bar service'},
            {'name': 'Wheelchair Access', 'icon': 'fa-wheelchair', 'description': 'Accessible facilities'},
            {'name': 'Spa', 'icon': 'fa-spa', 'description': 'Spa and wellness center'},
        ]
        
        for amenity_data in amenities:
            Amenity.objects.get_or_create(
                name=amenity_data['name'],
                defaults={
                    'icon': amenity_data['icon'],
                    'description': amenity_data['description']
                }
            )
        
        self.stdout.write(self.style.SUCCESS(f'Created {len(amenities)} amenities'))
    
    def create_categories(self):
        categories = [
            {'name': 'Hotel', 'description': 'Accommodation with rooms and services'},
            {'name': 'Restaurant', 'description': 'Food and dining venues'},
            {'name': 'Conference Center', 'description': 'Venues for meetings and conferences'},
            {'name': 'Event Hall', 'description': 'Venues for parties and celebrations'},
            {'name': 'Studio', 'description': 'Creative spaces for photography or recording'},
        ]
        
        for category_data in categories:
            VenueCategory.objects.get_or_create(
                name=category_data['name'],
                defaults={
                    'description': category_data['description']
                }
            )
        
        self.stdout.write(self.style.SUCCESS(f'Created {len(categories)} categories'))
    
    def create_users(self):
        # Create a customer user
        customer, created = User.objects.get_or_create(
            username='customer',
            defaults={
                'email': 'customer@example.com',
                'user_type': 'customer',
                'is_verified': True,
                'wallet_balance': 5000.00,
            }
        )
        
        if created:
            customer.set_password('password123')
            customer.save()
            self.stdout.write(self.style.SUCCESS('Created customer user'))
        
        # Create a host user
        host, created = User.objects.get_or_create(
            username='host',
            defaults={
                'email': 'host@example.com',
                'user_type': 'host',
                'is_verified': True,
                'wallet_balance': 1000.00,
            }
        )
        
        if created:
            host.set_password('password123')
            host.save()
            self.stdout.write(self.style.SUCCESS('Created host user'))
        
        # Create an admin user
        admin, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@example.com',
                'user_type': 'admin',
                'is_verified': True,
                'is_staff': True,
                'is_superuser': True,
                'wallet_balance': 10000.00,
            }
        )
        
        if created:
            admin.set_password('admin123')
            admin.save()
            self.stdout.write(self.style.SUCCESS('Created admin user'))
    
    def create_venues(self):
        # Get categories
        hotel_category = VenueCategory.objects.get(name='Hotel')
        restaurant_category = VenueCategory.objects.get(name='Restaurant')
        
        # Get host user
        host = User.objects.get(username='host')
        
        # Get all amenities
        all_amenities = list(Amenity.objects.all())
        
        # Create hotels
        hotels = [
            {
                'name': 'Grand Luxury Hotel',
                'description': 'Experience the pinnacle of luxury in our five-star hotel. Featuring spacious rooms, world-class dining, and exceptional service.',
                'city': 'New York',
                'state': 'NY',
                'max_capacity': 500,
                'latitude': 40.7128,
                'longitude': -74.0060,
            },
            {
                'name': 'Seaside Resort & Spa',
                'description': 'A beautiful beachfront resort with stunning ocean views, multiple pools, and a full-service spa.',
                'city': 'Miami',
                'state': 'FL',
                'max_capacity': 300,
                'latitude': 25.7617,
                'longitude': -80.1918,
            },
            {
                'name': 'Mountain View Lodge',
                'description': 'Escape to our mountain retreat featuring rustic elegance, hiking trails, and breathtaking views.',
                'city': 'Denver',
                'state': 'CO',
                'max_capacity': 200,
                'latitude': 39.7392,
                'longitude': -104.9903,
            },
            {
                'name': 'City Center Hotel',
                'description': 'Located in the heart of downtown, our hotel offers convenience, comfort, and style for business and leisure travelers.',
                'city': 'Chicago',
                'state': 'IL',
                'max_capacity': 400,
                'latitude': 41.8781,
                'longitude': -87.6298,
            },
            {
                'name': 'Historic Boutique Inn',
                'description': 'A charming boutique hotel housed in a restored historic building, offering unique rooms and personalized service.',
                'city': 'Boston',
                'state': 'MA',
                'max_capacity': 100,
                'latitude': 42.3601,
                'longitude': -71.0589,
            },
        ]
        
        # Create restaurants
        restaurants = [
            {
                'name': 'The Golden Spoon',
                'description': 'Fine dining restaurant specializing in contemporary American cuisine using locally sourced ingredients.',
                'city': 'San Francisco',
                'state': 'CA',
                'max_capacity': 80,
                'latitude': 37.7749,
                'longitude': -122.4194,
            },
            {
                'name': 'La Trattoria',
                'description': 'Authentic Italian restaurant serving handmade pasta, wood-fired pizza, and traditional dishes in a warm atmosphere.',
                'city': 'New York',
                'state': 'NY',
                'max_capacity': 60,
                'latitude': 40.7143,
                'longitude': -74.0060,
            },
            {
                'name': 'Sakura Japanese Grill',
                'description': 'Japanese restaurant featuring sushi, teppanyaki, and izakaya-style dining in an elegant setting.',
                'city': 'Los Angeles',
                'state': 'CA',
                'max_capacity': 70,
                'latitude': 34.0522,
                'longitude': -118.2437,
            },
            {
                'name': 'Spice Route',
                'description': 'Indian cuisine restaurant offering a wide variety of traditional dishes with modern presentation.',
                'city': 'Seattle',
                'state': 'WA',
                'max_capacity': 50,
                'latitude': 47.6062,
                'longitude': -122.3321,
            },
            {
                'name': 'Texas BBQ House',
                'description': 'Authentic barbecue restaurant with slow-smoked meats, classic sides, and craft beers.',
                'city': 'Austin',
                'state': 'TX',
                'max_capacity': 90,
                'latitude': 30.2672,
                'longitude': -97.7431,
            },
        ]
        
        with transaction.atomic():
            # Create hotel venues
            for hotel_data in hotels:
                venue, created = Venue.objects.get_or_create(
                    name=hotel_data['name'],
                    defaults={
                        'owner': host,
                        'category': hotel_category,
                        'description': hotel_data['description'],
                        'address': f"{random.randint(100, 999)} Main Street",
                        'city': hotel_data['city'],
                        'state': hotel_data['state'],
                        'postal_code': f"{random.randint(10000, 99999)}",
                        'country': 'USA',
                        'latitude': hotel_data['latitude'],
                        'longitude': hotel_data['longitude'],
                        'phone': f"555-{random.randint(100, 999)}-{random.randint(1000, 9999)}",
                        'email': f"info@{hotel_data['name'].lower().replace(' ', '')}.com",
                        'website': f"https://www.{hotel_data['name'].lower().replace(' ', '')}.com",
                        'max_capacity': hotel_data['max_capacity'],
                        'is_active': True,
                    }
                )
                
                if created:
                    # Add random amenities
                    venue_amenities = random.sample(all_amenities, random.randint(5, 8))
                    venue.amenities.add(*venue_amenities)
                    
                    # Create hotel rooms
                    room_types = ['Standard', 'Deluxe', 'Suite', 'Presidential']
                    for i, room_type in enumerate(room_types):
                        room = Room.objects.create(
                            venue=venue,
                            name=f"{room_type} Room",
                            description=f"Comfortable {room_type.lower()} room with all amenities for a pleasant stay.",
                            capacity=random.randint(1, 4),
                            size_sqft=random.randint(200, 800),
                            price_per_hour=float(random.randint(50, 200)),
                            is_active=True,
                        )
                        
                        # Add random amenities to room
                        room_amenities = random.sample(all_amenities, random.randint(3, 5))
                        room.amenities.add(*room_amenities)
                        
                        # Create time slots for the next 30 days
                        self.create_time_slots_for_room(room)
                    
                    self.stdout.write(self.style.SUCCESS(f'Created hotel: {venue.name}'))
            
            # Create restaurant venues
            for restaurant_data in restaurants:
                venue, created = Venue.objects.get_or_create(
                    name=restaurant_data['name'],
                    defaults={
                        'owner': host,
                        'category': restaurant_category,
                        'description': restaurant_data['description'],
                        'address': f"{random.randint(100, 999)} Restaurant Row",
                        'city': restaurant_data['city'],
                        'state': restaurant_data['state'],
                        'postal_code': f"{random.randint(10000, 99999)}",
                        'country': 'USA',
                        'latitude': restaurant_data['latitude'],
                        'longitude': restaurant_data['longitude'],
                        'phone': f"555-{random.randint(100, 999)}-{random.randint(1000, 9999)}",
                        'email': f"info@{restaurant_data['name'].lower().replace(' ', '')}.com",
                        'website': f"https://www.{restaurant_data['name'].lower().replace(' ', '')}.com",
                        'max_capacity': restaurant_data['max_capacity'],
                        'is_active': True,
                    }
                )
                
                if created:
                    # Add random amenities
                    venue_amenities = random.sample(all_amenities, random.randint(4, 6))
                    venue.amenities.add(*venue_amenities)
                    
                    # Create restaurant dining areas
                    dining_areas = ['Main Dining', 'Private Dining', 'Outdoor Patio', 'Bar Area']
                    for i, area in enumerate(dining_areas):
                        room = Room.objects.create(
                            venue=venue,
                            name=f"{area}",
                            description=f"{area} section of the restaurant, perfect for {random.choice(['casual dining', 'special occasions', 'business meetings', 'private events'])}.",
                            capacity=random.randint(10, 40),
                            size_sqft=random.randint(200, 600),
                            price_per_hour=float(random.randint(30, 150)),
                            is_active=True,
                        )
                        
                        # Add random amenities to room
                        room_amenities = random.sample(all_amenities, random.randint(2, 4))
                        room.amenities.add(*room_amenities)
                        
                        # Create time slots for the next 30 days
                        self.create_time_slots_for_room(room)
                    
                    self.stdout.write(self.style.SUCCESS(f'Created restaurant: {venue.name}'))
    
    def create_time_slots_for_room(self, room):
        """Create time slots for the next 30 days for a given room"""
        today = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        for day in range(30):  # 30 days from today
            current_day = today + timedelta(days=day)
            
            # Create slots from 9 AM to 9 PM, 2-hour intervals
            for hour in range(9, 21, 2):
                start_time = current_day.replace(hour=hour)
                end_time = start_time + timedelta(hours=2)
                
                TimeSlot.objects.create(
                    room=room,
                    start_time=start_time,
                    end_time=end_time,
                    is_available=True
                ) 