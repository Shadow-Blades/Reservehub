// ReserveHub main JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize all tooltips
    var tooltips = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltips.map(function(tooltip) {
        return new bootstrap.Tooltip(tooltip);
    });

    // Favorite toggle functionality
    const favoriteButtons = document.querySelectorAll('.favorite-toggle');
    favoriteButtons.forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            const venueId = this.dataset.venueId;
            const isFavorite = this.classList.contains('active');
            
            // Toggle visually immediately for better UX
            this.classList.toggle('active');
            const icon = this.querySelector('i');
            if (icon) {
                icon.classList.toggle('far');
                icon.classList.toggle('fas');
            }
            
            // Call API to update favorite status
            const url = isFavorite 
                ? `/bookings/venue/remove-favorite/${venueId}/` 
                : `/bookings/venue/add-favorite/${venueId}/`;
            
            fetch(url, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
                    'Content-Type': 'application/json'
                },
                credentials: 'same-origin'
            })
            .then(response => {
                if (!response.ok) {
                    // Revert visual change if request failed
                    this.classList.toggle('active');
                    if (icon) {
                        icon.classList.toggle('far');
                        icon.classList.toggle('fas');
                    }
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                console.log('Success:', data);
            })
            .catch(error => {
                console.error('Error:', error);
            });
        });
    });
    
    // Time slot selection
    const timeSlots = document.querySelectorAll('.time-slot.available');
    timeSlots.forEach(slot => {
        slot.addEventListener('click', function() {
            // Deselect all slots
            document.querySelectorAll('.time-slot.selected').forEach(s => {
                s.classList.remove('selected');
            });
            
            // Select this slot
            this.classList.add('selected');
            
            // Update form inputs
            const startTime = this.dataset.startTime;
            const endTime = this.dataset.endTime;
            const price = this.dataset.price;
            
            document.getElementById('id_start_time').value = startTime;
            document.getElementById('id_end_time').value = endTime;
            
            // Update price display if exists
            const priceDisplay = document.getElementById('booking-price');
            if (priceDisplay && price) {
                priceDisplay.textContent = `$${price}`;
            }
        });
    });
    
    // Payment animation
    const paymentButtons = document.querySelectorAll('.pay-with-coins-btn');
    paymentButtons.forEach(btn => {
        btn.addEventListener('click', function(e) {
            // Don't prevent default as we want the form to submit
            
            // Create coin animation
            const amount = parseInt(this.dataset.amount || 1);
            for (let i = 0; i < Math.min(amount, 10); i++) { // Cap at 10 coins for performance
                setTimeout(() => {
                    createCoinAnimation(e);
                }, i * 100);
            }
        });
    });
    
    // Cancel booking confirmation
    const cancelButtons = document.querySelectorAll('.cancel-booking-btn');
    cancelButtons.forEach(btn => {
        btn.addEventListener('click', function(e) {
            if (!confirm('Are you sure you want to cancel this booking? This action cannot be undone.')) {
                e.preventDefault();
            }
        });
    });
});

// Helper function to create coin animation
function createCoinAnimation(e) {
    const coin = document.createElement('div');
    coin.classList.add('coin');
    
    // Position coin near the click
    coin.style.left = `${e.clientX - 25}px`;
    coin.style.top = `${e.clientY - 25}px`;
    
    document.body.appendChild(coin);
    
    // Remove coin after animation completes
    setTimeout(() => {
        document.body.removeChild(coin);
    }, 1500);
}

// Helper function to get CSRF token
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
} 