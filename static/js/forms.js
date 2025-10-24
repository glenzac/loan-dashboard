/**
 * Custom JavaScript for Loan Dashboard Forms
 * Handles form validation, AJAX requests, and dynamic UI updates
 */

// ===========================
// Document Ready
// ===========================
document.addEventListener('DOMContentLoaded', function() {
    console.log('Loan Dashboard JavaScript Loaded');

    // Initialize tooltips
    initializeTooltips();

    // Initialize form validation
    initializeFormValidation();

    // Auto-hide alerts after 5 seconds
    autoHideAlerts();
});

// ===========================
// Tooltip Initialization
// ===========================
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// ===========================
// Form Validation
// ===========================
function initializeFormValidation() {
    // Fetch all forms with 'needs-validation' class
    const forms = document.querySelectorAll('.needs-validation');

    // Loop over forms and prevent submission if invalid
    Array.from(forms).forEach(form => {
        form.addEventListener('submit', event => {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }

            form.classList.add('was-validated');
        }, false);
    });
}

// ===========================
// Auto-hide Alerts
// ===========================
function autoHideAlerts() {
    const alerts = document.querySelectorAll('.alert-dismissible');

    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000); // 5 seconds
    });
}

// ===========================
// Number Formatting (Indian Currency)
// ===========================
function formatIndianCurrency(amount, showDecimals = true) {
    const decimals = showDecimals ? 2 : 0;
    const formatted = new Intl.NumberFormat('en-IN', {
        style: 'currency',
        currency: 'INR',
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals
    }).format(amount);

    return formatted;
}

// ===========================
// Date Formatting
// ===========================
function formatDate(dateString, format = 'DD-MMM-YYYY') {
    const date = new Date(dateString);
    const options = {
        day: '2-digit',
        month: 'short',
        year: 'numeric'
    };

    return date.toLocaleDateString('en-IN', options);
}

// ===========================
// Show Loading Spinner
// ===========================
function showLoadingSpinner(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.innerHTML = `
            <div class="spinner-container">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
            </div>
        `;
    }
}

// ===========================
// Confirmation Dialog
// ===========================
function confirmAction(message) {
    return confirm(message);
}

// ===========================
// AJAX Helper Function
// ===========================
function makeAjaxRequest(url, method, data, successCallback, errorCallback) {
    fetch(url, {
        method: method,
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: method !== 'GET' ? JSON.stringify(data) : null
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (successCallback) {
            successCallback(data);
        }
    })
    .catch(error => {
        console.error('AJAX Error:', error);
        if (errorCallback) {
            errorCallback(error);
        }
    });
}

// ===========================
// Export Functions for Global Use
// ===========================
window.loanDashboard = {
    formatIndianCurrency,
    formatDate,
    showLoadingSpinner,
    confirmAction,
    makeAjaxRequest
};
