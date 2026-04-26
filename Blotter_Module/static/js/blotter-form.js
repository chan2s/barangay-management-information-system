// Blotter Form JavaScript - BIMS

document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('blotterForm');
    const submitBtn = document.querySelector('.btn-submit');
    const resetBtn = document.querySelector('.btn-reset');

    // Form validation and submission handler
    if (form) {
        form.addEventListener('submit', function (e) {
            // Validate contact information (at least one)
            const phone = document.querySelector('[name="complainant_phone"]').value.trim();
            const email = document.querySelector('[name="complainant_email"]').value.trim();

            if (!phone && !email) {
                e.preventDefault();
                showAlert('Please provide at least a phone number or email address.', 'danger');
                document.querySelector('[name="complainant_phone"]').focus();
                return false;
            }

            // Validate certification checkbox
            const certify = document.getElementById('certify');
            if (!certify.checked) {
                e.preventDefault();
                showAlert('Please certify that the information provided is true and correct.', 'warning');
                certify.focus();
                return false;
            }

            // Validate data consent
            const dataConsent = document.getElementById('dataConsent');
            if (!dataConsent.checked) {
                e.preventDefault();
                showAlert('Please consent to the Data Privacy Act agreement.', 'warning');
                dataConsent.focus();
                return false;
            }

            // Show loading state
            if (submitBtn) {
                submitBtn.classList.add('loading');
                submitBtn.innerHTML = '<i class="bi bi-hourglass-split me-2"></i> Submitting...';
                submitBtn.disabled = true;
            }

            return true;
        });

        // Reset button handler
        if (resetBtn) {
            resetBtn.addEventListener('click', function (e) {
                if (confirm('Are you sure you want to clear all form data?')) {
                    form.reset();
                    showAlert('Form has been cleared.', 'info');
                }
            });
        }

        // Real-time validation for phone/email
        const phoneInput = document.querySelector('[name="complainant_phone"]');
        const emailInput = document.querySelector('[name="complainant_email"]');

        function validateContact() {
            const phone = phoneInput ? phoneInput.value.trim() : '';
            const email = emailInput ? emailInput.value.trim() : '';

            if (!phone && !email) {
                showInlineMessage('contact-warning', 'At least one contact method is required', 'warning');
            } else {
                hideInlineMessage('contact-warning');
            }
        }

        if (phoneInput) phoneInput.addEventListener('input', validateContact);
        if (emailInput) emailInput.addEventListener('input', validateContact);

        // Add character counter for description field
        const descriptionField = document.querySelector('[name="incident_description"]');
        if (descriptionField) {
            const counter = document.createElement('small');
            counter.className = 'text-muted mt-1 d-block';
            counter.style.fontSize = '0.7rem';
            descriptionField.parentNode.appendChild(counter);

            function updateCounter() {
                const length = descriptionField.value.length;
                const remaining = 2000 - length;
                if (remaining >= 0) {
                    counter.innerHTML = `<i class="bi bi-pencil"></i> ${length}/2000 characters`;
                    if (remaining < 100) {
                        counter.style.color = '#ef4444';
                    } else {
                        counter.style.color = '#6b7280';
                    }
                } else {
                    descriptionField.value = descriptionField.value.substring(0, 2000);
                    counter.innerHTML = `<i class="bi bi-exclamation-triangle"></i> Maximum 2000 characters reached`;
                    counter.style.color = '#ef4444';
                }
            }

            descriptionField.addEventListener('input', updateCounter);
            updateCounter();
        }

        // File upload validation
        const fileInput = document.querySelector('[name="evidence"]');
        if (fileInput) {
            fileInput.addEventListener('change', function (e) {
                const files = Array.from(e.target.files);
                const maxSize = 10 * 1024 * 1024; // 10MB
                let totalSize = 0;

                for (let file of files) {
                    if (file.size > maxSize) {
                        showAlert(`File "${file.name}" exceeds 10MB limit.`, 'danger');
                        fileInput.value = '';
                        return;
                    }
                    totalSize += file.size;
                }

                if (files.length > 0) {
                    const info = document.createElement('small');
                    info.className = 'text-success mt-1 d-block';
                    info.style.fontSize = '0.7rem';
                    info.innerHTML = `<i class="bi bi-check-circle"></i> ${files.length} file(s) selected (${(totalSize / 1024 / 1024).toFixed(2)} MB total)`;

                    // Remove old info if exists
                    const oldInfo = fileInput.parentNode.querySelector('.file-info');
                    if (oldInfo) oldInfo.remove();

                    info.classList.add('file-info');
                    fileInput.parentNode.appendChild(info);

                    setTimeout(() => {
                        if (info.parentNode) info.remove();
                    }, 3000);
                }
            });
        }

        // Auto-save draft functionality (optional)
        let autoSaveTimer;
        const formFields = form.querySelectorAll('input, select, textarea');

        function autoSaveDraft() {
            const formData = new FormData(form);
            const draft = {};
            for (let [key, value] of formData.entries()) {
                draft[key] = value;
            }
            localStorage.setItem('blotter_draft', JSON.stringify(draft));
            console.log('Draft saved');
        }

        formFields.forEach(field => {
            field.addEventListener('input', function () {
                clearTimeout(autoSaveTimer);
                autoSaveTimer = setTimeout(autoSaveDraft, 2000);
            });
        });

        // Load draft if exists
        const savedDraft = localStorage.getItem('blotter_draft');
        if (savedDraft) {
            const draft = JSON.parse(savedDraft);
            let hasData = false;

            for (let key in draft) {
                const field = form.querySelector(`[name="${key}"]`);
                if (field && draft[key]) {
                    hasData = true;
                    if (field.type === 'checkbox') {
                        field.checked = draft[key] === 'on';
                    } else {
                        field.value = draft[key];
                    }
                }
            }

            if (hasData) {
                showAlert('A saved draft was found and loaded. You can continue filling the form.', 'info');
            }
        }

        // Clear draft on successful submission (will be triggered by server response)
        function clearDraft() {
            localStorage.removeItem('blotter_draft');
        }

        // Expose clear draft function
        window.clearBlotterDraft = clearDraft;
    }

    // Helper function to show alerts
    function showAlert(message, type = 'info') {
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
        alertDiv.style.borderRadius = '12px';
        alertDiv.style.marginBottom = '1rem';
        alertDiv.innerHTML = `
            <i class="bi bi-${type === 'danger' ? 'exclamation-circle' : type === 'warning' ? 'exclamation-triangle' : 'info-circle'} me-2"></i>
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;

        const container = document.querySelector('.container');
        const noticeBox = document.querySelector('.notice-box');

        if (noticeBox) {
            noticeBox.insertAdjacentElement('afterend', alertDiv);
        } else if (container) {
            container.insertBefore(alertDiv, container.firstChild);
        }

        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alertDiv);
            bsAlert.close();
        }, 5000);
    }

    // Helper function for inline messages
    function showInlineMessage(id, message, type) {
        let existingMsg = document.getElementById(id);
        if (!existingMsg) {
            const contactDiv = document.querySelector('[name="complainant_phone"]').closest('.col-md-6').parentNode;
            existingMsg = document.createElement('div');
            existingMsg.id = id;
            existingMsg.className = `text-${type} mt-1`;
            existingMsg.style.fontSize = '0.7rem';
            contactDiv.appendChild(existingMsg);
        }
        existingMsg.innerHTML = `<i class="bi bi-${type === 'warning' ? 'exclamation-triangle' : 'info-circle'}"></i> ${message}`;
    }

    function hideInlineMessage(id) {
        const msg = document.getElementById(id);
        if (msg) msg.remove();
    }

    // Form field animations
    const formControls = document.querySelectorAll('.form-control, .form-select');
    formControls.forEach(control => {
        control.addEventListener('focus', function () {
            this.parentNode.classList.add('focused');
        });

        control.addEventListener('blur', function () {
            this.parentNode.classList.remove('focused');
        });
    });
});