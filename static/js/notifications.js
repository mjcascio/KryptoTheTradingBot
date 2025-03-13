// Notification system
function showNotification(message, type = 'error', duration = 5000) {
    // Create notification container if it doesn't exist
    let container = document.getElementById('notification-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'notification-container';
        container.style.position = 'fixed';
        container.style.top = '20px';
        container.style.right = '20px';
        container.style.zIndex = '9999';
        document.body.appendChild(container);
    }
    
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.innerHTML = `
        <div class="notification-icon">
            <i class="fas ${type === 'success' ? 'fa-check-circle' : type === 'warning' ? 'fa-exclamation-triangle' : 'fa-times-circle'}"></i>
        </div>
        <div class="notification-content">
            <div class="notification-message">${message}</div>
        </div>
        <div class="notification-close">
            <i class="fas fa-times"></i>
        </div>
    `;
    
    // Style notification
    notification.style.display = 'flex';
    notification.style.alignItems = 'center';
    notification.style.padding = '12px 15px';
    notification.style.marginBottom = '10px';
    notification.style.borderRadius = '10px';
    notification.style.boxShadow = '0 4px 12px rgba(0, 0, 0, 0.15)';
    notification.style.backgroundColor = type === 'success' ? 'rgba(48, 209, 88, 0.9)' : 
                                        type === 'warning' ? 'rgba(255, 214, 10, 0.9)' : 
                                        'rgba(255, 69, 58, 0.9)';
    notification.style.color = 'white';
    notification.style.backdropFilter = 'blur(10px)';
    notification.style.webkitBackdropFilter = 'blur(10px)';
    notification.style.transition = 'all 0.3s ease';
    notification.style.cursor = 'pointer';
    
    // Add notification to container
    container.appendChild(notification);
    
    // Add click event to close notification
    notification.querySelector('.notification-close').addEventListener('click', function() {
        container.removeChild(notification);
    });
    
    // Auto-remove notification after duration
    setTimeout(() => {
        if (notification.parentNode === container) {
            container.removeChild(notification);
        }
    }, duration);
}

// Helper functions
function formatCurrency(value) {
    return '$' + parseFloat(value).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function formatDateTime(dateStr) {
    if (!dateStr) return '--';
    const date = new Date(dateStr);
    if (isNaN(date.getTime())) return '--';
    return date.toLocaleString();
} 