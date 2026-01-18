document.addEventListener('DOMContentLoaded', function() {
    const tooltips = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    tooltips.forEach(tooltip => new bootstrap.Tooltip(tooltip));

    autoHideAlerts();
});

function autoHideAlerts() {
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000); 
    });
}
function getCSRFToken() {
    const name = 'csrftoken';
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

function makeRequest(url, method = 'GET', data = null) {
    const headers = {
        'X-CSRFToken': getCSRFToken()
    };
    
    if (data && !(data instanceof FormData)) {
        headers['Content-Type'] = 'application/json';
        data = JSON.stringify(data);
    }
    
    const options = {
        method: method,
        headers: headers,
        credentials: 'same-origin'
    };
    
    if (data) {
        options.body = data;
    }
    
    return fetch(url, options)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        });
}

window.FreshTracker = {
    makeRequest,
    getCSRFToken
};