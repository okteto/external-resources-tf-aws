// Dashboard state
let currentPage = 1;
let currentStatus = '';
let revenueChart = null;
let analyticsChart = null;

// Remove and complete icons in SVG format
var removeSVG = `
  <svg width="673" height="673" viewBox="0 0 673 673" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
    <path d="M336.667 0.333374C151.4 0.333374 0.679932 151.053 0.679932 336.307C0.679932 521.587 151.4 672.333 336.667 672.333C521.933 672.333 672.653 521.6 672.653 336.307C672.653 151.04 521.933 0.333374 336.667 0.333374ZM336.667 643.44C167.333 643.44 29.5733 505.68 29.5733 336.307C29.5733 166.987 167.347 29.2267 336.667 29.2267C506 29.2267 643.76 166.973 643.76 336.32C643.76 505.68 506 643.453 336.667 643.453V643.44Z" />
    <path d="M465.667 444.86L357.103 336.295L465.639 227.759C471.292 222.106 471.288 212.976 465.643 207.33C459.997 201.684 450.863 201.677 445.21 207.33L336.674 315.866L228.147 207.34C222.501 201.694 213.364 201.69 207.718 207.336C202.065 212.989 202.072 222.123 207.718 227.768L316.245 336.295L207.699 444.841C202.054 450.487 202.05 459.624 207.699 465.273C213.345 470.919 222.482 470.915 228.128 465.269L336.674 356.724L445.238 465.288C450.888 470.938 460.018 470.942 465.671 465.288C471.32 459.646 471.313 450.505 465.671 444.863L465.667 444.86Z" />
  </svg>
`;

// Tab switching functionality
function initTabs() {
  const navBtns = document.querySelectorAll('.nav-btn');
  const tabContents = document.querySelectorAll('.tab-content');

  navBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const targetTab = btn.getAttribute('data-tab');
      
      // Remove active class from all buttons and tabs
      navBtns.forEach(b => b.classList.remove('active'));
      tabContents.forEach(tab => tab.classList.remove('active'));
      
      // Add active class to clicked button and corresponding tab
      btn.classList.add('active');
      document.getElementById(`${targetTab}-tab`).classList.add('active');
      
      // Load data for the active tab
      if (targetTab === 'overview') {
        loadDashboardStats();
        loadRevenueChart();
      } else if (targetTab === 'orders') {
        loadChecks();
      } else if (targetTab === 'analytics') {
        loadAnalyticsChart();
      }
    });
  });
}

// Load dashboard statistics
async function loadDashboardStats() {
  try {
    const response = await fetch('/api/stats');
    const stats = await response.json();
    
    document.getElementById('total-checks').textContent = stats.total_checks;
    document.getElementById('total-revenue').textContent = `$${stats.total_revenue.toFixed(2)}`;
    document.getElementById('avg-order-value').textContent = `$${stats.avg_order_value.toFixed(2)}`;
    document.getElementById('checks-today').textContent = stats.checks_today;
    document.getElementById('revenue-today').textContent = `$${stats.revenue_today.toFixed(2)}`;
    
    // Display popular items
    const popularItemsList = document.getElementById('popular-items-list');
    popularItemsList.innerHTML = '';
    
    if (stats.popular_items.length === 0) {
      popularItemsList.innerHTML = '<p style="text-align: center; color: #7f8c8d;">No data available</p>';
    } else {
      stats.popular_items.forEach(item => {
        const itemDiv = document.createElement('div');
        itemDiv.className = 'popular-item';
        itemDiv.innerHTML = `
          <span class="item-name">${item.name}</span>
          <span class="item-count">${item.count}</span>
        `;
        popularItemsList.appendChild(itemDiv);
      });
    }
  } catch (error) {
    console.error('Error loading dashboard stats:', error);
  }
}

// Load revenue chart (last 7 days)
async function loadRevenueChart() {
  try {
    const response = await fetch('/api/checks/history?days=7');
    const data = await response.json();
    
    const ctx = document.getElementById('revenue-chart').getContext('2d');
    
    if (revenueChart) {
      revenueChart.destroy();
    }
    
    revenueChart = new Chart(ctx, {
      type: 'line',
      data: {
        labels: data.map(d => new Date(d.date).toLocaleDateString()),
        datasets: [{
          label: 'Revenue',
          data: data.map(d => d.revenue),
          borderColor: '#3498db',
          backgroundColor: 'rgba(52, 152, 219, 0.1)',
          tension: 0.4
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: {
          intersect: false,
        },
        plugins: {
          legend: {
            display: true,
            position: 'top'
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            ticks: {
              callback: function(value) {
                return '$' + value.toFixed(2);
              }
            }
          }
        }
      }
    });
  } catch (error) {
    console.error('Error loading revenue chart:', error);
  }
}

// Load analytics chart
async function loadAnalyticsChart() {
  const days = document.getElementById('days-select').value;
  
  try {
    const response = await fetch(`/api/checks/history?days=${days}`);
    const data = await response.json();
    
    const ctx = document.getElementById('analytics-chart').getContext('2d');
    
    if (analyticsChart) {
      analyticsChart.destroy();
    }
    
    analyticsChart = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: data.map(d => new Date(d.date).toLocaleDateString()),
        datasets: [
          {
            label: 'Revenue ($)',
            data: data.map(d => d.revenue),
            backgroundColor: 'rgba(52, 152, 219, 0.8)',
            yAxisID: 'y'
          },
          {
            label: 'Order Count',
            data: data.map(d => d.check_count),
            backgroundColor: 'rgba(155, 89, 182, 0.8)',
            yAxisID: 'y1'
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          y: {
            type: 'linear',
            display: true,
            position: 'left',
            beginAtZero: true,
            ticks: {
              callback: function(value) {
                return '$' + value.toFixed(2);
              }
            }
          },
          y1: {
            type: 'linear',
            display: true,
            position: 'right',
            beginAtZero: true,
            grid: {
              drawOnChartArea: false,
            },
          }
        }
      }
    });
  } catch (error) {
    console.error('Error loading analytics chart:', error);
  }
}

// Load checks with pagination and filtering
async function loadChecks(page = 1, status = '') {
  try {
    const offset = (page - 1) * 10;
    let url = `/checks?limit=10&offset=${offset}`;
    if (status) {
      url += `&status=${status}`;
    }
    
    const response = await fetch(url);
    const checks = await response.json();
    
    const checksList = document.getElementById('check');
    checksList.innerHTML = '';
    
    if (checks.length === 0) {
      checksList.innerHTML = '<li style="text-align: center; padding: 40px; color: #7f8c8d;">No checks found</li>';
    } else {
      checks.forEach(check => {
        addItemToDOM(check.orderId, check.total, check.items, check.url, check.status, check.created_at);
      });
    }
    
    // Update pagination
    document.getElementById('page-info').textContent = `Page ${page}`;
    document.getElementById('prev-page').disabled = page === 1;
    document.getElementById('next-page').disabled = checks.length < 10;
    
    currentPage = page;
  } catch (error) {
    console.error('Error loading checks:', error);
  }
}

// Remove/Pay check
function removeItem() {
  var item = this.parentNode.parentNode;
  var parent = item.parentNode;
  var orderId = item.id;

  fetch(`/checks/${orderId}`, {
    method: "DELETE",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
    },
  })
    .then((response) => {
      if (response.status >= 200 && response.status < 300) {
        parent.removeChild(item);
        // Refresh stats if on overview tab
        if (document.getElementById('overview-tab').classList.contains('active')) {
          loadDashboardStats();
        }
      } else {
        console.log(`error ${response.status}`);
      }
    })
    .catch((error) => {
      console.log(error);
    });
}

// Add item to DOM with enhanced information
function addItemToDOM(checkId, total, items, url, status, createdAt) {
  var list = document.getElementById("check");
  var foodItem = document.getElementById(checkId);
  if (foodItem) {
    return;
  }

  var item = document.createElement("li");
  const food = items.map(i => i.name).join(", ");
  const date = new Date(createdAt).toLocaleString();
  
  item.innerHTML = `
    <div>
      <dl>
        <dt>Check ID</dt>
        <dd>${checkId}</dd>
        <dt>Order</dt>
        <dd>${food}</dd>
        <dt>Total</dt>
        <dd>$${total}</dd>
        <dt>Status</dt>
        <dd><span class="status-badge status-${status}">${status}</span></dd>
        <dt>Created</dt>
        <dd>${date}</dd>
      </dl>
      <a href="${url}" class="download-link">Download Receipt</a>
    </div>`;
  item.id = checkId;

  var buttons = document.createElement("div");
  buttons.classList.add("buttons");

  if (status === 'active') {
    var remove = document.createElement("button");
    remove.classList.add("button-remove");
    remove.innerHTML = removeSVG;
    remove.addEventListener("click", removeItem);
    buttons.appendChild(remove);
  }

  item.appendChild(buttons);
  list.appendChild(item);
}

// Initialize event listeners
function initEventListeners() {
  // Status filter
  document.getElementById('status-filter').addEventListener('change', (e) => {
    currentStatus = e.target.value;
    currentPage = 1;
    loadChecks(currentPage, currentStatus);
  });
  
  // Refresh button
  document.getElementById('refresh-orders').addEventListener('click', () => {
    loadChecks(currentPage, currentStatus);
  });
  
  // Pagination
  document.getElementById('prev-page').addEventListener('click', () => {
    if (currentPage > 1) {
      loadChecks(currentPage - 1, currentStatus);
    }
  });
  
  document.getElementById('next-page').addEventListener('click', () => {
    loadChecks(currentPage + 1, currentStatus);
  });
  
  // Analytics time period selector
  document.getElementById('days-select').addEventListener('change', () => {
    loadAnalyticsChart();
  });
}

// Auto-refresh for active orders
function startAutoRefresh() {
  setInterval(() => {
    // Only refresh if on orders tab and showing active orders
    if (document.getElementById('orders-tab').classList.contains('active') && 
        (currentStatus === '' || currentStatus === 'active')) {
      loadChecks(currentPage, currentStatus);
    }
    
    // Refresh overview stats if on overview tab
    if (document.getElementById('overview-tab').classList.contains('active')) {
      loadDashboardStats();
    }
  }, 5000); // Refresh every 5 seconds
}

// Initialize dashboard
window.onload = function() {
  initTabs();
  initEventListeners();
  loadDashboardStats();
  loadRevenueChart();
  startAutoRefresh();
};