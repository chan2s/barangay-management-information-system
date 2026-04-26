// Blotter Success Page JavaScript - BIMS

document.addEventListener('DOMContentLoaded', function () {
    const printBtn = document.getElementById('printBtn');
    const newComplaintBtn = document.getElementById('newComplaintBtn');

    // Print functionality with enhanced formatting
    if (printBtn) {
        printBtn.addEventListener('click', function () {
            // Add print timestamp
            const timestamp = document.createElement('div');
            timestamp.className = 'print-timestamp text-center text-muted mt-3';
            timestamp.style.fontSize = '0.7rem';
            timestamp.innerHTML = `Printed on: ${new Date().toLocaleString()}`;

            const container = document.querySelector('.container');
            if (container && !document.querySelector('.print-timestamp')) {
                container.appendChild(timestamp);
            }

            // Trigger print
            window.print();

            // Remove timestamp after print dialog closes
            setTimeout(() => {
                const ts = document.querySelector('.print-timestamp');
                if (ts) ts.remove();
            }, 100);
        });
    }

    // Track print success
    window.addEventListener('beforeprint', function () {
        console.log('Print dialog opened');
    });

    window.addEventListener('afterprint', function () {
        console.log('Print completed or cancelled');
    });

    // Copy blotter number to clipboard functionality (optional enhancement)
    const blotterNumberElement = document.querySelector('.blotter-number-box .number');
    if (blotterNumberElement) {
        // Create copy button
        const copyButton = document.createElement('button');
        copyButton.className = 'btn btn-sm btn-outline-light mt-2';
        copyButton.innerHTML = '<i class="bi bi-clipboard"></i> Copy Number';
        copyButton.style.fontSize = '0.7rem';

        const blotterBox = document.querySelector('.blotter-number-box');
        if (blotterBox) {
            blotterBox.appendChild(copyButton);

            copyButton.addEventListener('click', async function () {
                const blotterNumber = blotterNumberElement.textContent;
                try {
                    await navigator.clipboard.writeText(blotterNumber);

                    // Show success feedback
                    const originalText = copyButton.innerHTML;
                    copyButton.innerHTML = '<i class="bi bi-check-lg"></i> Copied!';
                    copyButton.classList.add('btn-success');
                    copyButton.classList.remove('btn-outline-light');

                    setTimeout(() => {
                        copyButton.innerHTML = originalText;
                        copyButton.classList.remove('btn-success');
                        copyButton.classList.add('btn-outline-light');
                    }, 2000);

                    // Optional: Show a toast notification
                    showToast('Blotter number copied to clipboard!', 'success');
                } catch (err) {
                    console.error('Failed to copy:', err);
                    showToast('Failed to copy. Please select manually.', 'error');
                }
            });
        }
    }

    // Toast notification function
    function showToast(message, type = 'info') {
        // Create toast container if it doesn't exist
        let toastContainer = document.querySelector('.toast-container');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.className = 'toast-container position-fixed bottom-0 end-0 p-3';
            toastContainer.style.zIndex = '1050';
            document.body.appendChild(toastContainer);
        }

        // Create toast
        const toastEl = document.createElement('div');
        toastEl.className = `toast align-items-center text-white bg-${type === 'success' ? 'success' : type === 'error' ? 'danger' : 'primary'} border-0`;
        toastEl.setAttribute('role', 'alert');
        toastEl.setAttribute('aria-live', 'assertive');
        toastEl.setAttribute('aria-atomic', 'true');

        toastEl.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">
                    <i class="bi bi-${type === 'success' ? 'check-circle' : type === 'error' ? 'x-circle' : 'info-circle'} me-2"></i>
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        `;

        toastContainer.appendChild(toastEl);

        // Initialize and show toast
        const toast = new bootstrap.Toast(toastEl, { delay: 3000 });
        toast.show();

        // Remove toast after hidden
        toastEl.addEventListener('hidden.bs.toast', function () {
            toastEl.remove();
        });
    }

    // Prevent accidental navigation when form has unsaved data
    let hasUserInteracted = false;

    // Track user interaction
    const interactiveElements = document.querySelectorAll('button, a');
    interactiveElements.forEach(el => {
        el.addEventListener('click', function () {
            hasUserInteracted = true;
        });
    });

    // Warning before leaving if needed (optional)
    window.addEventListener('beforeunload', function (e) {
        // Only show warning if this is a new page and user hasn't interacted much
        // This is commented out to avoid being annoying, but can be enabled if needed
        /*
        if (!hasUserInteracted) {
            e.preventDefault();
            e.returnValue = 'You have not saved your blotter number. Are you sure you want to leave?';
            return e.returnValue;
        }
        */
    });

    // Add analytics or tracking (optional)
    if (blotterNumberElement) {
        console.log('Blotter success page loaded with number:', blotterNumberElement.textContent);
        // You can send analytics here if needed
        // gtag('event', 'blotter_submitted', { 'blotter_number': blotterNumberElement.textContent });
    }

    // Add print instruction tooltip
    if (printBtn) {
        printBtn.setAttribute('title', 'Print or save as PDF for your records');
        const tooltip = new bootstrap.Tooltip(printBtn, { placement: 'top' });
    }

    // Auto-scroll to top on page load (smooth)
    if (window.location.hash === '') {
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    }
});

// Add print styles dynamically
const printStyle = document.createElement('style');
printStyle.textContent = `
    @media print {
        .btn, .toast-container, .no-print {
            display: none !important;
        }
        .card {
            box-shadow: none !important;
            border: 1px solid #ddd !important;
        }
        .blotter-number-box {
            background: #1a3c5e !important;
            -webkit-print-color-adjust: exact !important;
            print-color-adjust: exact !important;
        }
        .print-timestamp {
            display: block !important;
        }
    }
`;
document.head.appendChild(printStyle);