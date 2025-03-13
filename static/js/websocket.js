// Initialize WebSocket connection
let socket = io();

// WebSocket connection status
socket.on('connect', () => {
    console.log('WebSocket connected');
});

socket.on('disconnect', () => {
    console.log('WebSocket disconnected');
});

// Handle position updates
socket.on('position_update', (data) => {
    console.log('Position update received:', data);
    
    // Only show notification if there's a significant change
    if (data.significant_change) {
        let message = `Position Update - ${data.symbol}: `;
        if (data.quantity === 0) {
            message += 'Position Closed';
        } else {
            message += `${data.quantity} shares @ $${data.avg_entry_price}`;
            if (data.unrealized_pl) {
                message += ` (P/L: ${data.unrealized_pl > 0 ? '+' : ''}${data.unrealized_pl.toFixed(2)})`;
            }
        }
        showNotification(message, data.quantity === 0 ? 'warning' : 'info');
    }
});

// Handle trade notifications
socket.on('trade_notification', (data) => {
    console.log('Trade notification received:', data);
    let message = `${data.action} ${data.symbol}: ${data.quantity} shares @ $${data.price}`;
    showNotification(message, data.action === 'BUY' ? 'success' : 'warning');
});

// Handle error notifications
socket.on('error_notification', (data) => {
    console.error('Error notification received:', data);
    showNotification(data.message, 'error');
});

// Handle system notifications
socket.on('system_notification', (data) => {
    console.log('System notification received:', data);
    showNotification(data.message, data.type || 'info');
}); 