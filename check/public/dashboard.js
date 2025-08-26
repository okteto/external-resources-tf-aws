// Dashboard JavaScript for real-time updates and pagination

let currentPage = 1;
const ordersPerPage = 10;
let totalPages = 1;

// Initialize dashboard when page loads
$(document).ready(function() {
    loadDashboardData();
    // Refresh data every 30 seconds
    setInterval(loadDashboardData, 30000);
});

async function loadDashboardData() {
    try {
        // Load statistics
        await loadStatistics();
        
        // Load popular items
        await loadPopularItems();
        
        // Load orders for current page
        await loadOrders(currentPage);
    } catch (error) {
        console.error('Error loading dashboard data:', error);
    }
}

async function loadStatistics() {
    try {
        const response = await fetch('/api/dashboard/stats');
        if (!response.ok) {
            throw new Error('Failed to load statistics');
        }
        
        const stats = await response.json();
        
        $('#total-orders').text(stats.total_orders || 0);
        $('#total-revenue').text('$' + (stats.total_revenue || 0).toFixed(2));
        $('#average-order').text('$' + (stats.average_order || 0).toFixed(2));
    } catch (error) {
        console.error('Error loading statistics:', error);
        $('#total-orders').text('-');
        $('#total-revenue').text('$-');
        $('#average-order').text('$-');
    }
}

async function loadPopularItems() {
    try {
        const response = await fetch('/api/dashboard/popular-items?limit=10');
        if (!response.ok) {
            throw new Error('Failed to load popular items');
        }
        
        const items = await response.json();
        const popularItemsList = $('#popular-items');
        
        if (items.length === 0) {
            popularItemsList.html('<li class="empty-state">No items found</li>');
            return;
        }
        
        popularItemsList.empty();
        items.forEach(item => {
            const itemHtml = `
                <li class="popular-item">
                    <span class="popular-item-name">${escapeHtml(item.name)}</span>
                    <span class="popular-item-count">${item.count}</span>
                </li>
            `;
            popularItemsList.append(itemHtml);
        });
    } catch (error) {
        console.error('Error loading popular items:', error);
        $('#popular-items').html('<li class="empty-state">Failed to load popular items</li>');
    }
}

async function loadOrders(page = 1) {
    try {
        const response = await fetch(`/api/dashboard/orders?page=${page}&limit=${ordersPerPage}`);
        if (!response.ok) {
            throw new Error('Failed to load orders');
        }
        
        const data = await response.json();
        const ordersList = $('#orders-list');
        
        if (data.orders.length === 0) {
            ordersList.html('<div class="empty-state">No orders found</div>');
            updatePaginationControls(1, 1);
            return;
        }
        
        // Update pagination info
        totalPages = data.total_pages;
        currentPage = data.current_page;
        updatePaginationControls(currentPage, totalPages);
        
        // Clear and populate orders list
        ordersList.empty();
        data.orders.forEach(order => {
            const orderHtml = createOrderCardHtml(order);
            ordersList.append(orderHtml);
        });
    } catch (error) {
        console.error('Error loading orders:', error);
        $('#orders-list').html('<div class="empty-state">Failed to load orders</div>');
    }
}

function createOrderCardHtml(order) {
    const orderDate = new Date(order.created_at).toLocaleString();
    const itemsHtml = order.items.map(item => `
        <li class="order-item">
            <span class="item-name">${escapeHtml(item.name)}</span>
            ${item.quantity > 1 ? `<span class="item-quantity">×${item.quantity}</span>` : ''}
            <span class="item-price">$${item.price.toFixed(2)}</span>
        </li>
    `).join('');
    
    return `
        <div class="order-card">
            <div class="order-header">
                <span class="order-id">#${escapeHtml(order.order_id)}</span>
                <span class="order-date">${orderDate}</span>
                <span class="order-total">$${order.total.toFixed(2)}</span>
            </div>
            <ul class="order-items">
                ${itemsHtml}
            </ul>
        </div>
    `;
}

function updatePaginationControls(currentPage, totalPages) {
    $('#page-info').text(`Page ${currentPage} of ${totalPages}`);
    
    const prevBtn = $('#prev-page');
    const nextBtn = $('#next-page');
    
    if (currentPage <= 1) {
        prevBtn.prop('disabled', true);
    } else {
        prevBtn.prop('disabled', false);
    }
    
    if (currentPage >= totalPages) {
        nextBtn.prop('disabled', true);
    } else {
        nextBtn.prop('disabled', false);
    }
}

function previousPage() {
    if (currentPage > 1) {
        loadOrders(currentPage - 1);
    }
}

function nextPage() {
    if (currentPage < totalPages) {
        loadOrders(currentPage + 1);
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Add some visual feedback for loading states
function showLoading(elementId) {
    $(elementId).html('<div class="loading">Loading...</div>');
}

// Error handling for network issues
$(document).ajaxError(function(event, xhr, settings, error) {
    console.error('AJAX Error:', error);
    if (xhr.status === 0) {
        // Network error
        console.warn('Network error - retrying in 10 seconds...');
        setTimeout(loadDashboardData, 10000);
    }
});