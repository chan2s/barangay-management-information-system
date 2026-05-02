// certificates/static/js/certificates.js
// Complete JavaScript for Certificate Filing Module (Contact Info Removed)

// Wait for DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {

    // ============================================
    // 1. AGE CALCULATION FUNCTION
    // ============================================
    function calculateAge(birthDate) {
        if (!birthDate) return '';
        const today = new Date();
        const birth = new Date(birthDate);
        let age = today.getFullYear() - birth.getFullYear();
        const monthDiff = today.getMonth() - birth.getMonth();
        if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birth.getDate())) {
            age--;
        }
        return age;
    }

    // ============================================
    // 2. UPDATE AGE FIELD WHEN DOB CHANGES
    // ============================================
    const dobInput = document.getElementById('dob');
    const ageInput = document.getElementById('age');

    if (dobInput && ageInput) {
        dobInput.addEventListener('change', function() {
            if (this.value) {
                ageInput.value = calculateAge(this.value);
            } else {
                ageInput.value = '';
            }
        });
    }

    // ============================================
    // 3. SHOW/HIDE CONDITIONAL FIELDS BASED ON CERTIFICATE TYPE
    // ============================================
    const requestTypeSelect = document.getElementById('requestType');

    if (requestTypeSelect) {
        requestTypeSelect.addEventListener('change', function() {
            const certType = this.value;

            // Get all conditional field containers
            const healthFields = document.getElementById('healthFields');
            const indigencyFields = document.getElementById('indigencyFields');
            const residencyFields = document.getElementById('residencyFields');
            const clearanceFields = document.getElementById('clearanceFields');
            const idFields = document.getElementById('idFields');

            // Hide all conditional sections first
            if (healthFields) healthFields.style.display = 'none';
            if (indigencyFields) indigencyFields.style.display = 'none';
            if (residencyFields) residencyFields.style.display = 'none';
            if (clearanceFields) clearanceFields.style.display = 'none';
            if (idFields) idFields.style.display = 'none';

            // Show relevant fields based on certificate type
            if (certType === 'Health Certification') {
                if (healthFields) healthFields.style.display = 'block';
                // Remove required from other fields
                removeRequiredFromConditionalFields();
                // Add required to health fields
                addRequiredToHealthFields();
            }
            else if (certType === 'Certificate of Indigency') {
                if (indigencyFields) indigencyFields.style.display = 'block';
                removeRequiredFromConditionalFields();
                addRequiredToIndigencyFields();
            }
            else if (certType === 'Certificate of Residency') {
                if (residencyFields) residencyFields.style.display = 'block';
                removeRequiredFromConditionalFields();
                addRequiredToResidencyFields();
            }
            else if (certType === 'Barangay Clearance') {
                if (clearanceFields) clearanceFields.style.display = 'block';
                removeRequiredFromConditionalFields();
                addRequiredToClearanceFields();
            }
            else if (certType === 'Barangay ID') {
                if (idFields) idFields.style.display = 'block';
                removeRequiredFromConditionalFields();
                addRequiredToIDFields();
            }
        });
    }

    // ============================================
    // 4. HELPER FUNCTIONS FOR REQUIRED FIELDS
    // ============================================
    function removeRequiredFromConditionalFields() {
        // Health fields
        const healthInputs = ['sex', 'birthplace', 'parents', 'date_first_seen'];
        healthInputs.forEach(id => {
            const field = document.getElementById(id);
            if (field) field.removeAttribute('required');
        });

        // Indigency fields
        const indigencyInputs = ['purok', 'purpose'];
        indigencyInputs.forEach(id => {
            const field = document.getElementById(id);
            if (field) field.removeAttribute('required');
        });

        // Residency fields
        const residencyInputs = ['purok', 'purpose'];
        residencyInputs.forEach(id => {
            const field = document.getElementById(id);
            if (field) field.removeAttribute('required');
        });

        // Clearance fields
        const clearancePurpose = document.getElementById('purpose');
        if (clearancePurpose) clearancePurpose.removeAttribute('required');

        // ID fields
        const idPurok = document.getElementById('purok');
        if (idPurok) idPurok.removeAttribute('required');
    }

    function addRequiredToHealthFields() {
        const sex = document.getElementById('sex');
        const birthplace = document.getElementById('birthplace');

        if (sex) sex.setAttribute('required', 'required');
        if (birthplace) birthplace.setAttribute('required', 'required');
    }

    function addRequiredToIndigencyFields() {
        const purok = document.getElementById('purok');
        const purpose = document.getElementById('purpose');

        if (purok) purok.setAttribute('required', 'required');
        if (purpose) purpose.setAttribute('required', 'required');
    }

    function addRequiredToResidencyFields() {
        const purok = document.getElementById('purok');
        const purpose = document.getElementById('purpose');

        if (purok) purok.setAttribute('required', 'required');
        if (purpose) purpose.setAttribute('required', 'required');
    }

    function addRequiredToClearanceFields() {
        const purpose = document.getElementById('purpose');
        if (purpose) purpose.setAttribute('required', 'required');
    }

    function addRequiredToIDFields() {
        const purok = document.getElementById('purok');
        const purpose = document.getElementById('purpose');

        if (purok) purok.setAttribute('required', 'required');
        if (purpose) purpose.setAttribute('required', 'required');
    }

    // ============================================
    // 5. FULL NAME VALIDATION
    // ============================================
    const fullNameInput = document.getElementById('fullName');
    if (fullNameInput) {
        fullNameInput.addEventListener('blur', function() {
            if (this.value && this.value.trim().length < 3) {
                this.style.borderColor = '#e53e3e';
                showError('fullName', 'Please enter a valid full name');
            } else {
                this.style.borderColor = '';
                hideError('fullName');
            }
        });

        fullNameInput.addEventListener('focus', function() {
            this.style.borderColor = '';
            hideError('fullName');
        });
    }

    // ============================================
// 6. ADDRESS VALIDATION (Poblacion, Santa Catalina)
// ============================================
const addressInput = document.getElementById('address');
if (addressInput) {
    addressInput.addEventListener('blur', function() {
        if (this.value && this.value.trim().length < 5) {
            this.style.borderColor = '#e53e3e';
            showError('address', 'Please enter a valid address');
        } else if (this.value && !this.value.toLowerCase().includes('poblacion')) {
            this.style.borderColor = '#e53e3e';
            showError('address', 'Address must be in Poblacion, Santa Catalina');
        } else {
            this.style.borderColor = '';
            hideError('address');
        }
    });

    addressInput.addEventListener('focus', function() {
        this.style.borderColor = '';
        hideError('address');
    });
}

    // ============================================
    // 7. ERROR MESSAGE DISPLAY FUNCTIONS
    // ============================================
    function showError(fieldId, message) {
        let errorSpan = document.getElementById(`${fieldId}Error`);
        if (!errorSpan) {
            const field = document.getElementById(fieldId);
            if (field) {
                errorSpan = document.createElement('span');
                errorSpan.id = `${fieldId}Error`;
                errorSpan.className = 'error-message';
                errorSpan.style.color = '#e53e3e';
                errorSpan.style.fontSize = '12px';
                errorSpan.style.marginTop = '5px';
                errorSpan.style.display = 'block';
                field.parentNode.appendChild(errorSpan);
            }
        }
        if (errorSpan) {
            errorSpan.textContent = message;
        }
    }

    function hideError(fieldId) {
        const errorSpan = document.getElementById(`${fieldId}Error`);
        if (errorSpan) {
            errorSpan.remove();
        }
    }

    // ============================================
    // 8. CLEAR FORM CONFIRMATION
    // ============================================
    const resetBtn = document.querySelector('button[type="reset"]');
    if (resetBtn) {
        resetBtn.addEventListener('click', function(e) {
            e.preventDefault();
            if (confirm('Are you sure you want to clear all form data?')) {
                document.getElementById('certificateForm').reset();
                // Clear age field
                if (ageInput) ageInput.value = '';
                // Clear conditional fields display
                const allConditionalFields = document.querySelectorAll('.conditional-fields');
                allConditionalFields.forEach(field => {
                    field.style.display = 'none';
                });
                // Remove all error messages
                const errorMessages = document.querySelectorAll('.error-message');
                errorMessages.forEach(error => error.remove());
                // Reset border colors
                const allInputs = document.querySelectorAll('input, select, textarea');
                allInputs.forEach(input => {
                    input.style.borderColor = '';
                });
                alert('Form has been cleared!');
            }
        });
    }

    // ============================================
    // 9. FORM SUBMISSION VALIDATION
    // ============================================
    const form = document.getElementById('certificateForm');
    if (form) {
        form.addEventListener('submit', function(e) {
            let isValid = true;

            // Validate request type
            const requestType = document.getElementById('requestType');
            if (!requestType.value) {
                alert('Please select a certificate type.');
                isValid = false;
            }

            // Validate full name
            const fullName = document.getElementById('fullName');
            if (!fullName.value || fullName.value.trim().length < 3) {
                alert('Please enter a valid full name.');
                isValid = false;
            }

            // Validate address
            const address = document.getElementById('address');
            if (!address.value || address.value.trim().length < 5) {
                alert('Please enter a valid address.');
                isValid = false;
            }

            // Validate date of birth
            const dob = document.getElementById('dob');
            if (dob.value) {
                const birthDate = new Date(dob.value);
                if (birthDate > new Date()) {
                    alert('Date of birth cannot be in the future.');
                    isValid = false;
                }
            }

            // Validate conditional fields based on certificate type
            const certType = requestType.value;

            if (certType === 'Health Certification') {
                const sex = document.getElementById('sex');
                const birthplace = document.getElementById('birthplace');
                if (!sex.value || !birthplace.value) {
                    alert('Please fill in all Health Certification fields.');
                    isValid = false;
                }
            }

            if (certType === 'Certificate of Indigency') {
                const purok = document.getElementById('purok');
                const purpose = document.getElementById('purpose');
                if (!purok.value || !purpose.value) {
                    alert('Please fill in Purok/Zone and Purpose for Indigency Certificate.');
                    isValid = false;
                }
            }

            if (certType === 'Certificate of Residency') {
                const purok = document.getElementById('purok');
                const purpose = document.getElementById('purpose');
                if (!purok.value || !purpose.value) {
                    alert('Please fill in Purok/Zone and Purpose for Residency Certificate.');
                    isValid = false;
                }
            }

            if (certType === 'Barangay Clearance') {
                const purpose = document.getElementById('purpose');
                if (!purpose.value) {
                    alert('Please state the purpose for Barangay Clearance.');
                    isValid = false;
                }
            }

            if (certType === 'Barangay ID') {
                const purok = document.getElementById('purok');
                const purpose = document.getElementById('purpose');
                if (!purok.value || !purpose.value) {
                    alert('Please fill in Purok/Zone and Purpose for Barangay ID.');
                    isValid = false;
                }
            }

            if (!isValid) {
                e.preventDefault();
            }
        });
    }

    // ============================================
// 10. ADDRESS AUTO-COMPLETE SUGGESTIONS (Poblacion, Santa Catalina)
// ============================================
if (addressInput) {
    const poblacionSuggestions = [
        'Purok 1, Poblacion, Santa Catalina, Negros Oriental',
        'Purok 2, Poblacion, Santa Catalina, Negros Oriental',
        'Purok 3, Poblacion, Santa Catalina, Negros Oriental',
        'Purok 4, Poblacion, Santa Catalina, Negros Oriental',
        'Purok 5, Poblacion, Santa Catalina, Negros Oriental',
        'Purok 6, Poblacion, Santa Catalina, Negros Oriental',
        'Purok 7, Poblacion, Santa Catalina, Negros Oriental',
        'Purok 8, Poblacion, Santa Catalina, Negros Oriental',
        'Purok 9, Poblacion, Santa Catalina, Negros Oriental',
        'Purok 10, Poblacion, Santa Catalina, Negros Oriental',
        'Sitio Riverside, Poblacion, Santa Catalina, Negros Oriental',
        'Sitio Centro, Poblacion, Santa Catalina, Negros Oriental',
        'Sitio Proper, Poblacion, Santa Catalina, Negros Oriental',
        'Poblacion Proper, Santa Catalina, Negros Oriental'
    ];

    // Remove existing datalist if any
    const existingDatalist = document.getElementById('addressSuggestions');
    if (existingDatalist) {
        existingDatalist.remove();
    }

    let datalist = document.createElement('datalist');
    datalist.id = 'addressSuggestions';
    addressInput.setAttribute('list', 'addressSuggestions');
    addressInput.setAttribute('placeholder', 'Enter Purok/Sitio, Poblacion, Santa Catalina');

    poblacionSuggestions.forEach(suggestion => {
        const option = document.createElement('option');
        option.value = suggestion;
        datalist.appendChild(option);
    });

    addressInput.parentNode.appendChild(datalist);
}

    // ============================================
    // 11. LOADING STATE FOR SUBMIT BUTTON
    // ============================================
    const submitBtn = document.querySelector('button[type="submit"]');
    if (submitBtn && form) {
        form.addEventListener('submit', function() {
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.textContent = 'Processing...';
                setTimeout(function() {
                    submitBtn.disabled = false;
                    submitBtn.textContent = 'Submit Request';
                }, 3000);
            }
        });
    }

    // ============================================
    // 12. RESULT PAGE - PRINT FUNCTIONALITY
    // ============================================
    const printBtn = document.querySelector('.btn-print');
    if (printBtn) {
        printBtn.addEventListener('click', function() {
            window.print();
        });
    }

    // ============================================
    // 13. STORAGE FUNCTIONS (localStorage for draft)
    // ============================================
    function saveFormDraft() {
        const formData = {
            requestType: document.getElementById('requestType')?.value || '',
            fullName: document.getElementById('fullName')?.value || '',
            address: document.getElementById('address')?.value || '',
            dob: document.getElementById('dob')?.value || '',
            civilStatus: document.getElementById('civilStatus')?.value || '',
            gender: document.getElementById('gender')?.value || '',
            purok: document.getElementById('purok')?.value || '',
            purpose: document.getElementById('purpose')?.value || '',
            birthplace: document.getElementById('birthplace')?.value || '',
            parents: document.getElementById('parents')?.value || '',
            sex: document.getElementById('sex')?.value || '',
            savedAt: new Date().toISOString()
        };

        localStorage.setItem('certificateFormDraft', JSON.stringify(formData));
        console.log('Form draft saved to localStorage');
    }

    function loadFormDraft() {
        const savedData = localStorage.getItem('certificateFormDraft');
        if (savedData) {
            const formData = JSON.parse(savedData);
            const confirmLoad = confirm('You have a saved draft. Load it?');
            if (confirmLoad) {
                if (formData.requestType) document.getElementById('requestType').value = formData.requestType;
                if (formData.fullName) document.getElementById('fullName').value = formData.fullName;
                if (formData.address) document.getElementById('address').value = formData.address;
                if (formData.dob) document.getElementById('dob').value = formData.dob;
                if (formData.civilStatus) document.getElementById('civilStatus').value = formData.civilStatus;
                if (formData.gender) document.getElementById('gender').value = formData.gender;
                if (formData.purok) document.getElementById('purok').value = formData.purok;
                if (formData.purpose) document.getElementById('purpose').value = formData.purpose;
                if (formData.birthplace) document.getElementById('birthplace').value = formData.birthplace;
                if (formData.parents) document.getElementById('parents').value = formData.parents;
                if (formData.sex) document.getElementById('sex').value = formData.sex;

                // Trigger age calculation
                if (formData.dob && ageInput) {
                    ageInput.value = calculateAge(formData.dob);
                }

                // Trigger conditional fields
                if (requestTypeSelect) {
                    requestTypeSelect.dispatchEvent(new Event('change'));
                }

                alert('Draft loaded successfully!');
            }
        }
    }

    // Auto-save draft every 30 seconds
    let autoSaveInterval;
    if (form) {
        autoSaveInterval = setInterval(function() {
            const hasData = document.getElementById('fullName')?.value ||
                           document.getElementById('address')?.value;
            if (hasData) {
                saveFormDraft();
            }
        }, 30000);
    }

    // Clear draft on successful submit
    if (form) {
        form.addEventListener('submit', function() {
            localStorage.removeItem('certificateFormDraft');
            if (autoSaveInterval) {
                clearInterval(autoSaveInterval);
            }
        });
    }

    // Check for draft on page load
    const urlParams = new URLSearchParams(window.location.search);
    if (!urlParams.has('submitted')) {
        loadFormDraft();
    }

    // ============================================
    // 14. DEBUG FUNCTIONS (Available in console)
    // ============================================
    window.certificateDebug = {
        clearDraft: function() {
            localStorage.removeItem('certificateFormDraft');
            console.log('Draft cleared!');
        },
        getFormData: function() {
            const formData = {
                requestType: document.getElementById('requestType')?.value,
                fullName: document.getElementById('fullName')?.value,
                address: document.getElementById('address')?.value,
                dob: document.getElementById('dob')?.value,
                age: document.getElementById('age')?.value,
                civilStatus: document.getElementById('civilStatus')?.value,
                gender: document.getElementById('gender')?.value,
                purok: document.getElementById('purok')?.value,
                purpose: document.getElementById('purpose')?.value
            };
            console.log('Current Form Data:', formData);
            return formData;
        },
        showStorage: function() {
            console.log('Local Storage:', localStorage.getItem('certificateFormDraft'));
        }
    };
    
    console.log('Certificate module loaded. Use certificateDebug in console for debugging.');
    
    // ============================================
    // 15. KEYBOARD SHORTCUTS
    // ============================================
    document.addEventListener('keydown', function(e) {
        // Ctrl + S to save draft
        if (e.ctrlKey && e.key === 's') {
            e.preventDefault();
            saveFormDraft();
            alert('Form draft saved!');
        }
        // Ctrl + R to reset form
        if (e.ctrlKey && e.key === 'r') {
            e.preventDefault();
            if (confirm('Reset all form fields?')) {
                form.reset();
                if (ageInput) ageInput.value = '';
            }
        }
    });

    // ============================================
    // 16. INITIAL TRIGGER FOR CONDITIONAL FIELDS
    // ============================================
    if (requestTypeSelect) {
        requestTypeSelect.dispatchEvent(new Event('change'));
    }
    
    // ============================================
    // 17. RESULT PAGE - DISPLAY DATA
    // ============================================
    function displayResultData() {
        // This function runs on the result page
        const trackingId = document.querySelector('.request-id');
        if (trackingId) {
            console.log('Result page loaded with ID:', trackingId.textContent);
        }
    }
    
    displayResultData();
    
    // ============================================
    // 18. EXPORT FUNCTIONS FOR EXTERNAL USE
    // ============================================
    window.CertificateModule = {
        calculateAge: calculateAge,
        saveDraft: saveFormDraft,
        loadDraft: loadFormDraft,
        validateForm: function() {
            const isValid = form ? form.dispatchEvent(new Event('submit')) : false;
            return isValid;
        }
    };
    
    console.log('Certificate module fully initialized!');
});

// ============================================
// 19. ADDITIONAL STYLES FOR DYNAMIC ELEMENTS
// ============================================
const style = document.createElement('style');
style.textContent = `
    .error-message {
        color: #e53e3e;
        font-size: 12px;
        margin-top: 5px;
        display: block;
    }
    
    input.error, select.error, textarea.error {
        border-color: #e53e3e;
    }
    
    .conditional-fields {
        transition: all 0.3s ease;
    }
    
    .btn:disabled {
        opacity: 0.6;
        cursor: not-allowed;
    }
    
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    .loading-spinner {
        display: inline-block;
        width: 16px;
        height: 16px;
        border: 2px solid #f3f3f3;
        border-top: 2px solid #3498db;
        border-radius: 50%;
        animation: spin 1s linear infinite;
        margin-right: 8px;
    }
`;
document.head.appendChild(style);