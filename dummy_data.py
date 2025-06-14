import os
import django
import random
from datetime import datetime, timedelta
from django.utils import timezone
from django.core.files import File
from django.contrib.auth import get_user_model
import requests
from io import BytesIO

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'reservehub.settings')
django.setup()

# Now import models after setting up Django
from accounts.models import CustomUser, WalletTransaction
from bookings.models import Venue, VenueImage, Room, RoomImage, Amenity, Review, Booking, VenueCategory
from payments.models import Transaction

def create_amenities():
    """Create common amenities"""
    amenities = [
        {'name': 'WiFi', 'icon': 'fas fa-wifi', 'description': 'Free high-speed WiFi'},
        {'name': 'Swimming Pool', 'icon': 'fas fa-swimming-pool', 'description': 'Outdoor swimming pool'},
        {'name': 'Gym', 'icon': 'fas fa-dumbbell', 'description': 'Fully equipped fitness center'},
        {'name': 'Parking', 'icon': 'fas fa-parking', 'description': 'Free parking available'},
        {'name': 'Restaurant', 'icon': 'fas fa-utensils', 'description': 'On-site restaurant'},
        {'name': 'Air Conditioning', 'icon': 'fas fa-snowflake', 'description': 'Climate controlled'},
        {'name': 'Spa', 'icon': 'fas fa-spa', 'description': 'Spa and wellness center'},
        {'name': 'Room Service', 'icon': 'fas fa-concierge-bell', 'description': '24/7 room service'},
        {'name': 'Conference Room', 'icon': 'fas fa-chalkboard', 'description': 'Meeting and conference facilities'},
        {'name': 'Pet Friendly', 'icon': 'fas fa-paw', 'description': 'Pets allowed'},
        {'name': 'Bar', 'icon': 'fas fa-glass-martini-alt', 'description': 'On-site bar'},
        {'name': 'Breakfast', 'icon': 'fas fa-coffee', 'description': 'Complimentary breakfast'},
    ]
    
    created_amenities = []
    for amenity_data in amenities:
        amenity, created = Amenity.objects.get_or_create(
            name=amenity_data['name'],
            defaults={
                'icon': amenity_data.get('icon', ''),
                'description': amenity_data.get('description', '')
            }
        )
        created_amenities.append(amenity)
        if created:
            print(f"Created amenity: {amenity.name}")
    
    return created_amenities

def create_users():
    """Create admin, venue owners and regular users"""
    User = get_user_model()
    
    # Create admin user
    admin_user, created = User.objects.get_or_create(
        username='admin',
        defaults={
            'email': 'admin@reservehub.com',
            'first_name': 'Admin',
            'last_name': 'User',
            'is_staff': True,
            'is_superuser': True,
            'user_type': 'admin',
        }
    )
    
    if created:
        admin_user.set_password('adminpassword')
        admin_user.wallet_balance = 200.00
        admin_user.save()
        print("Created admin user: admin@reservehub.com")
    
    # Create venue owners
    owners = []
    owner_data = [
        {'username': 'owner1', 'email': 'owner1@example.com', 'first_name': 'Rahul', 'last_name': 'Sharma'},
        {'username': 'owner2', 'email': 'owner2@example.com', 'first_name': 'Priya', 'last_name': 'Patel'},
        {'username': 'owner3', 'email': 'owner3@example.com', 'first_name': 'Amit', 'last_name': 'Singh'},
    ]
    
    for data in owner_data:
        owner, created = User.objects.get_or_create(
            username=data['username'],
            defaults={
                'email': data['email'],
                'first_name': data['first_name'],
                'last_name': data['last_name'],
                'is_staff': False,
                'is_superuser': False,
                'user_type': 'host',  # Using 'host' as it corresponds to venue owners
            }
        )
        
        if created:
            owner.set_password('password123')
            owner.wallet_balance = 200.00
            owner.save()
            print(f"Created owner: {data['email']}")
        
        owners.append(owner)
    
    # Create regular users
    users = []
    user_data = [
        {'username': 'user1', 'email': 'user1@example.com', 'first_name': 'Ananya', 'last_name': 'Gupta'},
        {'username': 'user2', 'email': 'user2@example.com', 'first_name': 'Vikas', 'last_name': 'Kumar'},
        {'username': 'user3', 'email': 'user3@example.com', 'first_name': 'Meera', 'last_name': 'Desai'},
        {'username': 'user4', 'email': 'user4@example.com', 'first_name': 'Ravi', 'last_name': 'Verma'},
        {'username': 'user5', 'email': 'user5@example.com', 'first_name': 'Neha', 'last_name': 'Reddy'},
    ]
    
    for data in user_data:
        user, created = User.objects.get_or_create(
            username=data['username'],
            defaults={
                'email': data['email'],
                'first_name': data['first_name'],
                'last_name': data['last_name'],
                'is_staff': False,
                'is_superuser': False,
                'user_type': 'customer',  # Using 'customer' for regular users
            }
        )
        
        if created:
            user.set_password('password123')
            user.wallet_balance = 200.00
            user.save()
            print(f"Created user: {data['email']}")
        
        users.append(user)
    
    return {'admin': admin_user, 'owners': owners, 'users': users}

def download_image(url):
    """Download image from URL and return as file object"""
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return BytesIO(response.content)
    except Exception as e:
        print(f"Error downloading image from {url}: {e}")
    
    return None

def create_venues_and_rooms(owners, amenities):
    """Create venues and rooms"""
    
    # Hotel images from Unsplash
    hotel_images = [
        'https://images.unsplash.com/photo-1566073771259-6a8506099945',
        'https://images.unsplash.com/photo-1542314831-068cd1dbfeeb',
        'https://images.unsplash.com/photo-1520250497591-112f2f40a3f4',
        'https://images.unsplash.com/photo-1571896349842-33c89424de2d',
    ]
    
    # Restaurant images from Unsplash
    restaurant_images = [
        'https://images.unsplash.com/photo-1517248135467-4c7edcad34c4',
        'https://images.unsplash.com/photo-1555396273-367ea4eb4db5',
        'https://images.unsplash.com/photo-1514933651103-005eec06c04b',
        'https://images.unsplash.com/photo-1525610553991-2bede1a236e2',
    ]
    
    # Event space images from Unsplash
    event_space_images = [
        'https://images.unsplash.com/photo-1505373877841-8d25f7d46678',
        'https://images.unsplash.com/photo-1519167758481-83f550bb49b3',
        'https://images.unsplash.com/photo-1531058020387-3be344556be6',
        'https://images.unsplash.com/photo-1519750783826-e2420f4d687f',
    ]
    
    # Room images from Unsplash
    room_images = [
        'https://images.unsplash.com/photo-1598928506311-c55ded91a20c',
        'https://images.unsplash.com/photo-1566665797739-1674de7a421a',
        'https://images.unsplash.com/photo-1582719478250-c89cae4dc85b',
        'https://images.unsplash.com/photo-1631049307264-da0ec9d70304',
        'https://images.unsplash.com/photo-1595526114035-0d45ed16cfbf',
    ]
    
    # Cities in India
    indian_cities = [
        {'city': 'Mumbai', 'state': 'Maharashtra', 'postal_code': '400001', 'country': 'India'},
        {'city': 'Delhi', 'state': 'Delhi', 'postal_code': '110001', 'country': 'India'},
        {'city': 'Bangalore', 'state': 'Karnataka', 'postal_code': '560001', 'country': 'India'},
        {'city': 'Hyderabad', 'state': 'Telangana', 'postal_code': '500001', 'country': 'India'},
        {'city': 'Chennai', 'state': 'Tamil Nadu', 'postal_code': '600001', 'country': 'India'},
        {'city': 'Kolkata', 'state': 'West Bengal', 'postal_code': '700001', 'country': 'India'},
        {'city': 'Pune', 'state': 'Maharashtra', 'postal_code': '411001', 'country': 'India'},
        {'city': 'Jaipur', 'state': 'Rajasthan', 'postal_code': '302001', 'country': 'India'},
        {'city': 'Ahmedabad', 'state': 'Gujarat', 'postal_code': '380001', 'country': 'India'},
        {'city': 'Kochi', 'state': 'Kerala', 'postal_code': '682001', 'country': 'India'},
    ]
    
    # First, let's create venue categories
    categories = {
        'hotel': VenueCategory.objects.create(name='Hotel', description='Accommodation venues with multiple rooms'),
        'restaurant': VenueCategory.objects.create(name='Restaurant', description='Food and dining venues'),
        'event_space': VenueCategory.objects.create(name='Event Space', description='Venues for events and gatherings')
    }
    
    # Hotel Data
    hotels = [
        {
            'name': 'Grand Luxury Hotel',
            'description': 'Experience luxury at its finest at this 5-star hotel. Featuring elegant rooms, world-class dining, and impeccable service.',
            'max_capacity': 500,
            'amenities': ['WiFi', 'Swimming Pool', 'Gym', 'Restaurant', 'Spa', 'Room Service', 'Air Conditioning', 'Parking'],
            'rooms': [
                {'name': 'Deluxe Room', 'description': 'Spacious room with king-size bed and city view', 'capacity': 2, 'price_per_hour': 1500},
                {'name': 'Executive Suite', 'description': 'Luxurious suite with separate living area and premium amenities', 'capacity': 4, 'price_per_hour': 3000},
                {'name': 'Royal Penthouse', 'description': 'Ultimate luxury with panoramic views and private balcony', 'capacity': 6, 'price_per_hour': 6000},
            ]
        },
        {
            'name': 'Business Bay Hotel',
            'description': 'Ideal for business travelers, this hotel offers modern amenities, conference facilities, and convenient location near the business district.',
            'max_capacity': 300,
            'amenities': ['WiFi', 'Conference Room', 'Gym', 'Restaurant', 'Room Service', 'Air Conditioning', 'Parking'],
            'rooms': [
                {'name': 'Standard Room', 'description': 'Comfortable room with work desk and high-speed internet', 'capacity': 2, 'price_per_hour': 1000},
                {'name': 'Business Suite', 'description': 'Spacious suite with separate work area and meeting space', 'capacity': 3, 'price_per_hour': 2500},
                {'name': 'Conference Hall', 'description': 'Fully equipped conference room for business meetings', 'capacity': 50, 'price_per_hour': 5000},
            ]
        },
        {
            'name': 'Serene Resort & Spa',
            'description': 'A peaceful retreat with lush gardens, spa treatments, and beautiful swimming pools for a relaxing getaway.',
            'max_capacity': 400,
            'amenities': ['WiFi', 'Swimming Pool', 'Spa', 'Restaurant', 'Air Conditioning', 'Parking', 'Breakfast'],
            'rooms': [
                {'name': 'Garden View Room', 'description': 'Cozy room with view of the lush gardens', 'capacity': 2, 'price_per_hour': 1200},
                {'name': 'Spa Suite', 'description': 'Luxurious suite with direct access to spa facilities', 'capacity': 2, 'price_per_hour': 2800},
                {'name': 'Family Villa', 'description': 'Spacious villa with multiple bedrooms and private pool', 'capacity': 8, 'price_per_hour': 7000},
            ]
        },
        {
            'name': 'Heritage Palace Hotel',
            'description': 'Experience the grandeur of Indian heritage in this beautifully restored palace hotel with royal service.',
            'max_capacity': 250,
            'amenities': ['WiFi', 'Swimming Pool', 'Restaurant', 'Spa', 'Air Conditioning', 'Room Service', 'Breakfast'],
            'rooms': [
                {'name': 'Heritage Room', 'description': 'Traditional room with antique furnishings', 'capacity': 2, 'price_per_hour': 1800},
                {'name': 'Royal Chamber', 'description': 'Opulent room decorated in royal style', 'capacity': 3, 'price_per_hour': 3500},
                {'name': 'Maharaja Suite', 'description': 'Extravagant suite once used by royalty', 'capacity': 4, 'price_per_hour': 8000},
            ]
        },
    ]
    
    # Restaurant Data
    restaurants = [
        {
            'name': 'Spice Garden Restaurant',
            'description': 'Authentic Indian cuisine featuring flavors from across the country in an elegant setting.',
            'max_capacity': 150,
            'amenities': ['WiFi', 'Air Conditioning', 'Parking', 'Bar'],
            'rooms': [
                {'name': 'Main Dining Hall', 'description': 'Elegant dining space with ambient lighting', 'capacity': 100, 'price_per_hour': 2000},
                {'name': 'Private Dining Room', 'description': 'Intimate space for private gatherings', 'capacity': 20, 'price_per_hour': 1500},
                {'name': 'Outdoor Terrace', 'description': 'Al fresco dining with garden views', 'capacity': 30, 'price_per_hour': 1800},
            ]
        },
        {
            'name': 'Fusion Flavors',
            'description': 'Innovative cuisine combining international techniques with local ingredients for a unique dining experience.',
            'max_capacity': 120,
            'amenities': ['WiFi', 'Air Conditioning', 'Parking', 'Bar'],
            'rooms': [
                {'name': 'Modern Dining Area', 'description': 'Contemporary space with stylish décor', 'capacity': 80, 'price_per_hour': 2500},
                {'name': 'Chef\'s Table', 'description': 'Exclusive dining experience with direct view of the kitchen', 'capacity': 10, 'price_per_hour': 3000},
                {'name': 'Lounge Bar', 'description': 'Trendy space for cocktails and appetizers', 'capacity': 30, 'price_per_hour': 2000},
            ]
        },
        {
            'name': 'Coastal Delight Restaurant',
            'description': 'Specializing in fresh seafood and coastal cuisine from India\'s vast shorelines.',
            'max_capacity': 100,
            'amenities': ['WiFi', 'Air Conditioning', 'Parking'],
            'rooms': [
                {'name': 'Seaside Hall', 'description': 'Main dining area with ocean-inspired décor', 'capacity': 60, 'price_per_hour': 1800},
                {'name': 'Family Section', 'description': 'Comfortable space ideal for family gatherings', 'capacity': 40, 'price_per_hour': 1500},
            ]
        },
    ]
    
    # Event Spaces Data
    event_spaces = [
        {
            'name': 'Grand Celebration Hall',
            'description': 'Magnificent venue perfect for weddings, corporate events, and large-scale celebrations.',
            'max_capacity': 1000,
            'amenities': ['WiFi', 'Air Conditioning', 'Parking'],
            'rooms': [
                {'name': 'Main Ballroom', 'description': 'Expansive space with high ceilings and crystal chandeliers', 'capacity': 800, 'price_per_hour': 10000},
                {'name': 'Pre-function Area', 'description': 'Elegant space for cocktail receptions', 'capacity': 200, 'price_per_hour': 5000},
                {'name': 'VIP Lounge', 'description': 'Exclusive area for special guests', 'capacity': 50, 'price_per_hour': 3000},
            ]
        },
        {
            'name': 'Creative Conference Center',
            'description': 'Modern venue with state-of-the-art facilities for corporate meetings, seminars, and conferences.',
            'max_capacity': 500,
            'amenities': ['WiFi', 'Air Conditioning', 'Parking', 'Conference Room'],
            'rooms': [
                {'name': 'Main Conference Hall', 'description': 'Large hall with advanced audiovisual equipment', 'capacity': 300, 'price_per_hour': 8000},
                {'name': 'Breakout Room A', 'description': 'Medium-sized room for group discussions', 'capacity': 50, 'price_per_hour': 2500},
                {'name': 'Breakout Room B', 'description': 'Medium-sized room for group discussions', 'capacity': 50, 'price_per_hour': 2500},
                {'name': 'Executive Boardroom', 'description': 'Sophisticated room for high-level meetings', 'capacity': 20, 'price_per_hour': 3500},
            ]
        },
        {
            'name': 'Cultural Event Space',
            'description': 'Versatile venue for cultural performances, art exhibitions, and community events.',
            'max_capacity': 600,
            'amenities': ['WiFi', 'Air Conditioning', 'Parking'],
            'rooms': [
                {'name': 'Exhibition Hall', 'description': 'Open space with customizable layout for exhibitions', 'capacity': 400, 'price_per_hour': 7000},
                {'name': 'Performance Stage', 'description': 'Professional stage with lighting and sound system', 'capacity': 200, 'price_per_hour': 6000},
                {'name': 'Artist Lounge', 'description': 'Comfortable area for performers', 'capacity': 30, 'price_per_hour': 2000},
            ]
        },
    ]
    
    created_venues = []
    venue_type_map = {
        'hotel': {'data': hotels, 'images': hotel_images, 'category': categories['hotel']},
        'restaurant': {'data': restaurants, 'images': restaurant_images, 'category': categories['restaurant']},
        'event_space': {'data': event_spaces, 'images': event_space_images, 'category': categories['event_space']}
    }
    
    for venue_type, values in venue_type_map.items():
        for i, venue_data in enumerate(values['data']):
            # Select a random owner and city
            owner = random.choice(owners)
            location = random.choice(indian_cities)
            
            # Create venue
            venue = Venue.objects.create(
                owner=owner,
                name=venue_data['name'],
                description=venue_data['description'],
                category=values['category'],
                address=f"{i+100} Sample Street",
                city=location['city'],
                state=location['state'],
                postal_code=location['postal_code'],
                country=location['country'],
                latitude=random.uniform(8.0, 37.0),  # India's latitude range
                longitude=random.uniform(68.0, 97.0),  # India's longitude range
                phone=f"+91-{random.randint(7000000000, 9999999999)}",
                email=f"contact@{venue_data['name'].lower().replace(' ', '')}.com",
                website=f"https://www.{venue_data['name'].lower().replace(' ', '')}.com",
                max_capacity=venue_data['max_capacity'],
                is_active=True
            )
            print(f"Created {venue_type}: {venue.name}")
            
            # Add amenities
            for amenity_name in venue_data['amenities']:
                try:
                    amenity = next(a for a in amenities if a.name == amenity_name)
                    venue.amenities.add(amenity)
                except StopIteration:
                    continue
            
            # Add venue images
            for idx, image_url in enumerate(values['images']):
                image_data = download_image(f"{image_url}?w=800&auto=format&fit=crop")
                if image_data:
                    img_name = f"{venue_type}_{i+1}_image_{idx+1}.jpg"
                    venue_image = VenueImage(venue=venue, is_primary=(idx==0))
                    venue_image.image.save(img_name, File(image_data), save=True)
                    print(f"Added image to {venue.name}: {img_name}")
            
            # Create rooms for this venue
            for j, room_data in enumerate(venue_data['rooms']):
                room = Room.objects.create(
                    venue=venue,
                    name=room_data['name'],
                    description=room_data['description'],
                    capacity=room_data['capacity'],
                    size_sqft=random.randint(100, 1000),  # Random size between 100-1000 sq ft
                    price_per_hour=room_data['price_per_hour'],
                    is_active=True
                )
                
                # Add room amenities (subset of venue amenities)
                for amenity in venue.amenities.all()[:min(3, venue.amenities.count())]:
                    room.amenities.add(amenity)
                
                # Add room images
                image_url = random.choice(room_images)
                image_data = download_image(f"{image_url}?w=800&auto=format&fit=crop")
                if image_data:
                    img_name = f"{venue_type}_room_{i+1}_{j+1}.jpg"
                    room_image = RoomImage(room=room, is_primary=True)
                    room_image.image.save(img_name, File(image_data), save=True)
                    print(f"Added image to room {room.name}")
            
            created_venues.append(venue)
    
    return created_venues

def create_bookings_and_reviews(venues, users):
    """Create sample bookings and reviews"""
    for venue in venues:
        # Create 2-5 reviews per venue
        for _ in range(random.randint(2, 5)):
            user = random.choice(users)
            rating = random.randint(3, 5)  # Mostly positive reviews
            
            review = Review.objects.create(
                venue=venue,
                user=user,
                rating=rating,
                comment=f"{'Great' if rating >= 4 else 'Good'} {venue.category.name}! The {random.choice(['service', 'amenities', 'location', 'ambiance'])} was {'excellent' if rating == 5 else 'very good' if rating == 4 else 'decent'}.",
                created_at=timezone.now() - timedelta(days=random.randint(1, 60))
            )
            print(f"Created review for {venue.name} by {user.username}")
        
        # Create 3-8 bookings per venue
        for _ in range(random.randint(3, 8)):
            user = random.choice(users)
            room = random.choice(venue.rooms.all())
            
            # Random date in next 30 days
            booking_date = timezone.now().date() + timedelta(days=random.randint(1, 30))
            
            # Random time (9 AM - 9 PM)
            hour = random.randint(9, 21)
            start_time = datetime.combine(booking_date, datetime.strptime(f"{hour}:00", "%H:%M").time())
            
            # Duration (1-4 hours)
            duration = random.randint(1, 4)
            end_time = start_time + timedelta(hours=duration)
            
            # Total price calculation
            total_price = room.price_per_hour * duration
            
            status_choices = ['confirmed', 'pending', 'cancelled']
            status_weights = [0.7, 0.2, 0.1]  # 70% confirmed, 20% pending, 10% cancelled
            status = random.choices(status_choices, weights=status_weights)[0]
            
            booking = Booking.objects.create(
                room=room,
                user=user,
                start_time=start_time,
                end_time=end_time,
                num_guests=random.randint(1, room.capacity),
                total_price=total_price,
                special_requests="None" if random.random() > 0.3 else "Special setup requested",
                status=status,
                created_at=timezone.now() - timedelta(days=random.randint(1, 10))
            )
            print(f"Created booking for {room.name} at {venue.name}")
            
            # Create wallet transaction for confirmed bookings
            if status == 'confirmed':
                WalletTransaction.objects.create(
                    user=user,
                    amount=total_price,
                    transaction_type='booking',
                    description=f"Booking for {room.name} at {venue.name}",
                    reference_id=f"booking_{booking.id}",
                    created_at=booking.created_at
                )
                print(f"Created wallet transaction for booking #{booking.id}")

def run():
    """Execute the script to create dummy data"""
    print("Creating dummy data for ReserveHub...")
    
    # Create amenities
    amenities = create_amenities()
    print(f"Created {len(amenities)} amenities")
    
    # Create users
    users_dict = create_users()
    print(f"Created admin, {len(users_dict['owners'])} owners and {len(users_dict['users'])} users")
    
    # Create venues and rooms
    venues = create_venues_and_rooms(users_dict['owners'], amenities)
    print(f"Created {len(venues)} venues with rooms and images")
    
    # Create bookings and reviews
    create_bookings_and_reviews(venues, users_dict['users'])
    print("Created bookings and reviews")
    
    print("Dummy data creation complete!")

if __name__ == "__main__":
    run() 