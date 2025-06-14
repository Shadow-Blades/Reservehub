# ReserveHub - Venue Booking Platform

ReserveHub is a comprehensive venue booking platform built with Django. It allows users to discover, book, and manage venues for various events and purposes.

## Features

### For Customers
- Browse and search venues by location, category, and availability
- Filter venues by type (hotels or restaurants), amenities, and price range
- View detailed venue information including photos, amenities, and reviews
- Book venues for specific dates and times using virtual coin payments
- Manage bookings (view, modify, cancel) with instant refunds
- Leave reviews for venues after booking
- Save favorite venues
- Track wallet transactions and booking history

### For Venue Hosts
- List venues with detailed information and photos
- Manage venue availability and booking requests
- Track bookings and revenue
- Respond to customer reviews
- Customize venue pricing and policies

### Technical Features
- Custom user authentication with different user roles (Customer, Host, Admin)
- RESTful API for mobile applications
- Virtual coin payment system with transaction history
- Interactive UI with animations and popups
- Advanced filters for venue search
- Responsive design for all devices

## Technology Stack

- **Backend**: Django 5.2
- **Frontend**: HTML, CSS, JavaScript, Bootstrap 5
- **Database**: SQLite (development), PostgreSQL (production)
- **API**: Django REST Framework
- **Authentication**: Django AllAuth
- **Deployment**: Docker, Gunicorn, Nginx

## Interview Demo Guide

Follow these steps to demonstrate ReserveHub in an interview:

1. **Setup & Login**
   - Run the development server: `python manage.py runserver`
   - Navigate to http://127.0.0.1:8000/
   - Login with the pre-created demo account:
     - Username: `customer`
     - Password: `password123`
   - Note the wallet balance displayed in the top-right corner (5000 coins)

2. **Browse Venues**
   - Click "Venues" in the navigation bar
   - Use the filter buttons to switch between Hotels and Restaurants
   - Try the sidebar filters for location, price range, and amenities
   - Notice the animated cards and hover effects

3. **View Venue Details**
   - Click on any venue card to see details
   - Explore the venue information, rooms, and reviews
   - Click the "Favorite" button to demonstrate the animation

4. **Book a Venue**
   - Select a room from any venue
   - Choose a date and time slot
   - Enter guest information
   - Complete the booking
   - Demonstrate the coin animation showing payment
   - Show the success notification popup

5. **Manage Bookings**
   - Go to "My Bookings" in the navigation
   - View your booking history with wallet balance
   - Show the transaction history in the sidebar
   - Demonstrate cancelling a booking
   - Watch the coin animation for refund
   - Show the confirmation modal and success notification

6. **API Demo**
   - Visit http://127.0.0.1:8000/api/ to show the API endpoints
   - Explain how this enables mobile app integration

## Project Structure

```
reservehub/
├── accounts/            # User authentication and profiles
├── bookings/            # Core booking functionality
│   ├── api/             # REST API endpoints
│   ├── management/      # Management commands (data seeding)
│   ├── migrations/      # Database migrations
│   ├── templates/       # HTML templates
│   └── ...
├── payments/            # Payment processing
├── reservehub/          # Project settings
├── static/              # Static assets
│   ├── css/
│   ├── js/
│   └── img/
├── templates/           # Global templates
├── media/               # User-uploaded files
└── manage.py
```

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/reservehub.git
cd reservehub
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Apply migrations:
```bash
python manage.py migrate
```

5. Load demo data:
```bash
python manage.py seed_dummy_data
```

6. Run the development server:
```bash
python manage.py runserver
```
7. To create users/admins/host:
   Navigate to folder and than - ```bash python manage.py shell```
   Paste the following there(Depending on the requirement)-
   from accounts.models import CustomUser

# Create a regular customer
customer = CustomUser.objects.create_user(
    username='customer1',
    email='customer1@example.com',
    password='your_password',
    user_type='customer',
    phone_number='1234567890'
)

# Create a host
host = CustomUser.objects.create_user(
    username='host1',
    email='host1@example.com',
    password='your_password',
    user_type='host',
    phone_number='9876543210'
)

# Create an admin
admin = CustomUser.objects.create_user(
    username='admin1',
    email='admin1@example.com',
    password='your_password',
    user_type='admin',
    phone_number='5555555555'
)

8. Access the application at http://127.0.0.1:8000/

## Demo Accounts

The following accounts are available for testing:

| Username | Password    | Role     | Wallet Balance |
|----------|-------------|----------|---------------|
| customer | password123 | Customer | 5000 coins    |
| host     | password123 | Host     | 1000 coins    |
| admin    | admin123    | Admin    | 10000 coins   |

## Key Technical Implementation Details

### Virtual Coin System
- Implemented in `accounts/models.py` with `wallet_balance` field on user model
- Transaction history tracked in `WalletTransaction` model
- Coin animations in frontend using custom JavaScript

### Filtering System
- Advanced filtering in `bookings/views.py` within the `VenueListView` class
- Frontend filters implemented in `templates/bookings/venue_list.html`
- Automatic URL parameter handling for filter state persistence

### UI Animations
- Custom animations defined in `static/css/style.css`
- Interactive elements powered by `static/js/main.js`
- Notification system for booking and cancellation events

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- [Django](https://www.djangoproject.com/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [Bootstrap](https://getbootstrap.com/)
- [Font Awesome](https://fontawesome.com/)
- [Stripe](https://stripe.com/) 
