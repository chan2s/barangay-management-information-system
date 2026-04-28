// Dashboard JavaScript - BIMS

document.addEventListener('DOMContentLoaded', function () {
    // Animate statistics counters
    function animateCounter(element, start, end, duration) {
        let startTimestamp = null;
        const step = (timestamp) => {
            if (!startTimestamp) startTimestamp = timestamp;
            const progress = Math.min((timestamp - startTimestamp) / duration, 1);
            const value = Math.floor(progress * (end - start) + start);
            if (element) {
                element.textContent = value.toLocaleString();
            }
            if (progress < 1) {
                window.requestAnimationFrame(step);
            }
        };
        window.requestAnimationFrame(step);
    }

    // Fetch blotter statistics from server
    // Fetch blotter statistics from server
    function fetchBlotterStats() {
        fetch('/blotter/api/blotter-stats/')
            .then(data => {
                if (!data.error) {
                    const totalEl = document.getElementById('totalBlotters');
                    const pendingEl = document.getElementById('pendingBlotters');
                    const resolvedEl = document.getElementById('resolvedBlotters');

                    if (totalEl) animateCounter(totalEl, 0, data.total || 0, 1500);
                    if (pendingEl) animateCounter(pendingEl, 0, data.pending || 0, 1500);
                    if (resolvedEl) animateCounter(resolvedEl, 0, data.resolved || 0, 1500);
                } else {
                    console.log('Stats API error:', data.error);
                    setDefaultStats();
                }
            })
            .catch(error => {
                console.log('Stats API not available yet:', error);
                setDefaultStats();
            });
    }

    function setDefaultStats() {
        const totalEl = document.getElementById('totalBlotters');
        const pendingEl = document.getElementById('pendingBlotters');
        const resolvedEl = document.getElementById('resolvedBlotters');

        if (totalEl) animateCounter(totalEl, 0, 0, 500);
        if (pendingEl) animateCounter(pendingEl, 0, 0, 500);
        if (resolvedEl) animateCounter(resolvedEl, 0, 0, 500);
    }

    // Check for messages in URL (for redirects)
    function checkForMessages() {
        const urlParams = new URLSearchParams(window.location.search);
        const message = urlParams.get('message');
        const messageType = urlParams.get('type');

        if (message) {
            showToast(message, messageType || 'success');
        }
    }

    // Toast notification function
    function showToast(message, type = 'success') {
        // Create toast container if it doesn't exist
        let toastContainer = document.querySelector('.toast-container-custom');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.className = 'toast-container-custom position-fixed bottom-0 end-0 p-3';
            toastContainer.style.zIndex = '1050';
            document.body.appendChild(toastContainer);
        }

        const toastEl = document.createElement('div');
        toastEl.className = `toast align-items-center text-white bg-${type === 'success' ? 'success' : 'danger'} border-0 show`;
        toastEl.setAttribute('role', 'alert');
        toastEl.setAttribute('aria-live', 'assertive');
        toastEl.setAttribute('aria-atomic', 'true');

        toastEl.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">
                    <i class="bi bi-${type === 'success' ? 'check-circle-fill' : 'exclamation-triangle-fill'} me-2"></i>
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        `;

        toastContainer.appendChild(toastEl);

        // Auto remove after 3 seconds
        setTimeout(() => {
            toastEl.classList.remove('show');
            setTimeout(() => toastEl.remove(), 300);
        }, 3000);

        // Manual close
        const closeBtn = toastEl.querySelector('.btn-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => {
                toastEl.classList.remove('show');
                setTimeout(() => toastEl.remove(), 300);
            });
        }
    }

    // Add smooth scroll for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            const href = this.getAttribute('href');
            if (href !== '#' && href !== '#!') {
                const target = document.querySelector(href);
                if (target) {
                    e.preventDefault();
                    target.scrollIntoView({ behavior: 'smooth' });
                }
            }
        });
    });

    // Add fade-in animation on scroll
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);

    document.querySelectorAll('.feature-card, .stat-card, .step-card').forEach(el => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(30px)';
        el.style.transition = 'all 0.6s ease-out';
        observer.observe(el);
    });

    // Initialize
    fetchBlotterStats();
    checkForMessages();

    // Add year to footer
    const yearElement = document.querySelector('.footer .mb-0');
    if (yearElement) {
        const year = new Date().getFullYear();
        yearElement.textContent = yearElement.textContent.replace('2026', year);
    }
});