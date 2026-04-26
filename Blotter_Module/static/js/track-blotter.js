// Track Blotter JavaScript - BIMS

document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('trackForm');
    const searchBtn = document.getElementById('searchBtn');
    const blotterNumberInput = document.getElementById('blotterNumber');

    // Form validation and submission
    if (form) {
        form.addEventListener('submit', function (e) {
            const blotterNumber = blotterNumberInput ? blotterNumberInput.value.trim() : '';

            // Validate blotter number
            if (!blotterNumber) {
                e.preventDefault();
                showMessage('Please enter a blotter number.', 'warning');
                if (blotterNumberInput) blotterNumberInput.focus();
                return false;
            }

            // Validate format (optional - adjust pattern as needed)
            const pattern = /^BL-\d{4}-\d{3,}$/i;
            if (!pattern.test(blotterNumber)) {
                e.preventDefault();
                showMessage('Invalid blotter number format. Expected format: BL-YYYY-XXX (e.g., BL-2024-001)', 'warning');
                if (blotterNumberInput) blotterNumberInput.focus();
                return false;
            }

            // Show loading state
            if (searchBtn) {
                searchBtn.classList.add('loading');
                searchBtn.innerHTML = '<i class="bi bi-hourglass-split me-2"></i> Searching...';
                searchBtn.disabled = true;
            }

            return true;
        });
    }

    // Input validation - real-time
    if (blotterNumberInput) {
        blotterNumberInput.addEventListener('input', function (e) {
            let value = this.value.toUpperCase();
            // Auto-format if needed
            if (value.length === 2 && value !== 'BL') {
                this.value = 'BL-' + value.replace('BL-', '');
            }
        });

        // Remove any existing message when user starts typing
        blotterNumberInput.addEventListener('focus', function () {
            removeMessage();
        });
    }

    // Helper function to show messages
    function showMessage(message, type = 'info') {
        removeMessage();

        const messageDiv = document.createElement('div');
        messageDiv.className = `alert alert-${type === 'warning' ? 'warning' : type === 'error' ? 'danger' : 'info'} alert-dismissible fade show`;
        messageDiv.style.marginTop = '1rem';
        messageDiv.style.borderRadius = '8px';
        messageDiv.innerHTML = `
            <i class="bi bi-${type === 'warning' ? 'exclamation-triangle' : type === 'error' ? 'x-circle' : 'info-circle'} me-2"></i>
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;

        const trackCard = document.querySelector('.track-card');
        if (trackCard) {
            trackCard.insertAdjacentElement('beforeend', messageDiv);
        }

        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(messageDiv);
            if (bsAlert) bsAlert.close();
        }, 5000);
    }

    function removeMessage() {
        const existingAlerts = document.querySelectorAll('.alert');
        existingAlerts.forEach(alert => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }

    // Restore button state if form fails to submit
    window.addEventListener('pageshow', function () {
        if (searchBtn) {
            searchBtn.classList.remove('loading');
            searchBtn.innerHTML = '<i class="bi bi-search me-2"></i> Track Blotter';
            searchBtn.disabled = false;
        }
    });

    // Add keyboard shortcut (Enter key on input)
    if (blotterNumberInput) {
        blotterNumberInput.addEventListener('keypress', function (e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                if (form) {
                    const submitEvent = new Event('submit', { cancelable: true });
                    form.dispatchEvent(submitEvent);
                    if (submitEvent.defaultPrevented === false && form.checkValidity()) {
                        form.submit();
                    }
                }
            }
        });
    }

    // Animation for result cards
    const resultCard = document.querySelector('.result-card');
    if (resultCard) {
        resultCard.style.opacity = '0';
        resultCard.style.transform = 'translateY(20px)';

        setTimeout(() => {
            resultCard.style.transition = 'all 0.4s ease-out';
            resultCard.style.opacity = '1';
            resultCard.style.transform = 'translateY(0)';
        }, 100);
    }
});