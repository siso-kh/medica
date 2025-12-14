// Medica - Main JavaScript File

// Initialize tooltips and popovers if Bootstrap is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize Bootstrap tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Auto-hide flash messages after 5 seconds
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });
    
    // Smooth scroll for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            const href = this.getAttribute('href');
            if (href !== '#') {
                e.preventDefault();
                const target = document.querySelector(href);
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            }
        });
    });
    
    const searchForm = document.getElementById('medicine-search-form');
    const useLocationCheckbox = document.getElementById('use-location');
    const searchButton = document.getElementById('search-button');
    const resultsDiv = document.getElementById('search-results');
    const loadingDiv = document.getElementById('loading-indicator');

    // Hide loading initially
    if (loadingDiv) loadingDiv.style.display = 'none';

    searchForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const medicineName = document.getElementById('medicine-name').value.trim();
        if (!medicineName) {
            alert('Please enter a medicine name.');
            return;
        }

        // Show loading
        if (loadingDiv) loadingDiv.style.display = 'block';
        if (resultsDiv) resultsDiv.innerHTML = '';
        searchButton.disabled = true;

        let lat = null, lng = null;

        if (useLocationCheckbox && useLocationCheckbox.checked) {
            try {
                // Get location with 10-second timeout
                const position = await Promise.race([
                    new Promise((resolve, reject) => {
                        navigator.geolocation.getCurrentPosition(resolve, reject, {
                            enableHighAccuracy: false,  // Faster, less accurate
                            timeout: 10000,
                            maximumAge: 300000  // Use cached location if <5 min old
                        });
                    }),
                    new Promise((_, reject) => setTimeout(() => reject(new Error('Timeout')), 10000))
                ]);
                lat = position.coords.latitude;
                lng = position.coords.longitude;
            } catch (error) {
                console.warn('Geolocation failed:', error);
                alert('Unable to get your location. Searching without location (using default area).');
                // Proceed without location (API will use default)
            }
        }

        // Send API request
        try {
            const response = await fetch('/api/search-medicines', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ medicine_name: medicineName, lat, lng })
            });

            const data = await response.json();

            if (data.error) {
                resultsDiv.innerHTML = `<div class="alert alert-danger">${data.error}</div>`;
            } else {
                // Display results as divs with specified layout
                let html = `<h3>${data.medicine.name}</h3><p>${data.medicine.description}</p><h4>Nearby Pharmacies:</h4><div class="row">`;
                data.pharmacies.forEach(pharm => {
                    const distanceText = pharm.distance ? `${pharm.distance} km away` : 'Distance unknown';
                    html += `
                        <div class="col-md-6 mb-3">
                            <div class="card h-100 position-relative">
                                <div class="card-body">
                                    <h5 class="card-title">${pharm.pharmacy_name}</h5>
                                    <p class="card-text">${pharm.address}</p>
                                    <p class="card-text"><small class="text-muted">${distanceText}</small></p>
                                    <a href="https://www.google.com/maps/dir/?api=1&destination=${pharm.lat},${pharm.lng}" target="_blank" class="btn btn-success position-absolute bottom-0 end-0 m-2">Get Directions</a>
                                </div>
                            </div>
                        </div>
                    `;
                });
                html += '</div>';
                resultsDiv.innerHTML = html;
            }
        } catch (error) {
            console.error('API error:', error);
            resultsDiv.innerHTML = '<div class="alert alert-danger">Search failed. Please try again.</div>';
        } finally {
            // Hide loading
            if (loadingDiv) loadingDiv.style.display = 'none';
            searchButton.disabled = false;
        }
    });
});

// Utility function to escape HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Utility function to format dates
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });
}

// Show loading state
function showLoading(element) {
    if (element) {
        element.style.display = 'block';
    }
}

// Hide loading state
function hideLoading(element) {
    if (element) {
        element.style.display = 'none';
    }
}

// Show error message
function showError(message, elementId = 'errorState') {
    const errorElement = document.getElementById(elementId);
    if (errorElement) {
        errorElement.textContent = message;
        errorElement.style.display = 'block';
    } else {
        alert(message);
    }
}

// Hide error message
function hideError(elementId = 'errorState') {
    const errorElement = document.getElementById(elementId);
    if (errorElement) {
        errorElement.style.display = 'none';
    }
}

// Example: Handle location toggle and search
const useLocationCheckbox = document.getElementById('use-location');
const searchButton = document.getElementById('search-medicine');

searchButton.addEventListener('click', async () => {
    const medicineName = document.getElementById('medicine-name').value;
    let lat = null, lng = null;
    
    if (useLocationCheckbox.checked) {
        try {
            // Get location with timeout
            const position = await new Promise((resolve, reject) => {
                navigator.geolocation.getCurrentPosition(resolve, reject, { timeout: 10000 });  // 10s timeout
            });
            lat = position.coords.latitude;
            lng = position.coords.longitude;
        } catch (error) {
            alert('Location access failed or timed out. Searching without location.');
            // Fallback: proceed without location
        }
    }
    
    // Send API request
    fetch('/api/search-medicines', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ medicine_name: medicineName, lat, lng })
    })
    .then(response => response.json())
    .then(data => {
        // Handle and display results
        console.log(data);
        // Update UI with pharmacies
    })
    .catch(error => console.error('Error:', error));
});

