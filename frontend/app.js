// Configuration
const API_BASE = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    ? 'http://localhost:8000'
    : 'https://ide-k1r8.onrender.com';
const CATEGORIES = [
    "General store", "Grocery store", "Chemist shop", "Medical store", "Electronics Store",
    "Furniture shop", "Sofa Shop", "Curtains Shop", "Clothing Shop", "Garments Shop",
    "Hardware Shop", "Tiles Shop", "Plywood Shop", "Decorative items Shop", "Footwear Shop",
    "Paint Shop", "Gas stove Shop", "Ro Filter Shop", "Utensils Shop", "Stationery Shop",
    "Sweets Shop", "Cakes and Bakery Shop", "Vet Shop", "Pet Shop", "Veterinary Medicine shops",
    "Labs", "Diagnostic Centres"
];

// State
let currentJobId = null;
let pollingInterval = null;
let selectedCategories = [];
let selectedFields = ['name', 'address', 'phone', 'category'];
let displayedLogs = new Set(); // Track displayed log messages to avoid duplicates

// DOM Elements
const cityInput = document.getElementById('city-input');
const startBtn = document.getElementById('start-btn');
const stopBtn = document.getElementById('stop-btn');
const clearBtn = document.getElementById('clear-btn');
const selectAllBtn = document.getElementById('select-all-btn');
const clearLogsBtn = document.getElementById('clear-logs-btn');
const statusText = document.getElementById('status-text');
const statusDot = document.getElementById('status-dot');
const progressItem = document.getElementById('progress-item');
const progressFill = document.getElementById('progress-fill');
const progressText = document.getElementById('progress-text');
const logsContainer = document.getElementById('logs-container');
const categoriesList = document.getElementById('categories-list');
const categoriesCount = document.getElementById('categories-count');

// Insights elements
const refreshInsightsBtn = document.getElementById('refresh-insights-btn');
const insightsContent = document.getElementById('insights-content');
const insightsEmpty = document.getElementById('insights-empty');
const insightsLoading = document.getElementById('insights-loading');
const totalRecordsEl = document.getElementById('total-records');
const totalCategoriesEl = document.getElementById('total-categories');
const recordsWithPhoneEl = document.getElementById('records-with-phone');
const recordsWithAddressEl = document.getElementById('records-with-address');

// Chart instances
let categoryChart = null;
let pieChart = null;

// Initialize
function init() {
    renderCategories();
    setupEventListeners();
    updateStartButton();
    addLog('Application ready. Configure and start scraping.', 'info');
}

// Render Categories
function renderCategories() {
    categoriesList.innerHTML = CATEGORIES.map(category => `
        <label class="checkbox-item">
            <input type="checkbox" value="${category}" onchange="handleCategoryToggle(this)">
            <span>${category}</span>
        </label>
    `).join('');
    updateCategoriesCount();
}

// Event Listeners
function setupEventListeners() {
    // Field checkboxes
    document.querySelectorAll('#field-name, #field-address, #field-phone, #field-category').forEach(cb => {
        cb.addEventListener('change', (e) => {
            const field = e.target.value;
            if (e.target.checked) {
                if (!selectedFields.includes(field)) {
                    selectedFields.push(field);
                }
            } else {
                selectedFields = selectedFields.filter(f => f !== field);
            }
            updateStartButton();
        });
    });

    // City input
    cityInput.addEventListener('input', updateStartButton);

    // Buttons
    startBtn.addEventListener('click', handleStart);
    stopBtn.addEventListener('click', handleStop);
    clearBtn.addEventListener('click', handleClear);
    selectAllBtn.addEventListener('click', handleSelectAll);
    clearLogsBtn.addEventListener('click', () => {
        logsContainer.innerHTML = '<p class="no-logs">No activity yet.</p>';
    });
    
    // Insights
    if (refreshInsightsBtn) {
        refreshInsightsBtn.addEventListener('click', loadInsights);
    }
}

// Category Toggle
function handleCategoryToggle(checkbox) {
    const category = checkbox.value;
    if (checkbox.checked) {
        if (!selectedCategories.includes(category)) {
            selectedCategories.push(category);
        }
    } else {
        selectedCategories = selectedCategories.filter(c => c !== category);
    }
    updateCategoriesCount();
    updateStartButton();
}

// Select All Categories
function handleSelectAll() {
    const allSelected = selectedCategories.length === CATEGORIES.length;
    const checkboxes = categoriesList.querySelectorAll('input[type="checkbox"]');
    
    checkboxes.forEach(cb => {
        cb.checked = !allSelected;
        if (!allSelected) {
            if (!selectedCategories.includes(cb.value)) {
                selectedCategories.push(cb.value);
            }
        } else {
            selectedCategories = [];
        }
    });
    
    updateCategoriesCount();
    updateStartButton();
    addLog(allSelected ? 'All categories deselected' : 'All categories selected', 'info');
}

// Update Categories Count
function updateCategoriesCount() {
    categoriesCount.textContent = `${selectedCategories.length} of ${CATEGORIES.length} categories selected`;
}

// Update Start Button
function updateStartButton() {
    const city = cityInput.value.trim();
    const hasFields = selectedFields.length > 0;
    const hasCategories = selectedCategories.length > 0;
    
    startBtn.disabled = !city || !hasFields || !hasCategories;
}

// Start Scraping
async function handleStart() {
    const city = cityInput.value.trim();
    if (!city || selectedCategories.length === 0) {
        addLog('Please fill in all required fields', 'error');
        return;
    }

    try {
        addLog(`Starting scrape for: ${city}`, 'info');
        addLog(`Selected ${selectedCategories.length} categories`, 'info');
        addLog(`Fields to scrape: ${selectedFields.join(', ')}`, 'info');

        const response = await fetch(`${API_BASE}/scrape`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                city: city,
                categories: selectedCategories,
                fields: selectedFields
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        currentJobId = data.job_id;
        
        // Clear displayed logs for new job
        displayedLogs.clear();
        
        updateStatus('running');
        startBtn.style.display = 'none';
        stopBtn.style.display = 'flex';
        
        addLog(`Job started with ID: ${currentJobId}`, 'success');
        startPolling();

    } catch (error) {
        console.error('Error starting scrape:', error);
        addLog(`Error: ${error.message}`, 'error');
        addLog('Make sure the backend is running on http://localhost:8000', 'error');
        updateStatus('error');
    }
}

// Stop Scraping
function handleStop() {
    if (pollingInterval) {
        clearInterval(pollingInterval);
        pollingInterval = null;
    }
    
    updateStatus('idle');
    startBtn.style.display = 'flex';
    stopBtn.style.display = 'none';
    progressItem.style.display = 'none';
    currentJobId = null;
    
    addLog('Scraping stopped by user', 'info');
}

// Clear
function handleClear() {
    handleStop();
    cityInput.value = '';
    selectedCategories = [];
    selectedFields = ['name', 'address', 'phone', 'category'];
    
    // Reset checkboxes
    document.querySelectorAll('#categories-list input[type="checkbox"]').forEach(cb => cb.checked = false);
    document.querySelectorAll('#field-name, #field-address, #field-phone, #field-category').forEach(cb => cb.checked = true);
    
    updateCategoriesCount();
    updateStartButton();
    addLog('Configuration cleared', 'info');
}

// Polling
function startPolling() {
    if (pollingInterval) {
        clearInterval(pollingInterval);
    }

    pollingInterval = setInterval(async () => {
        if (!currentJobId) return;

        try {
            const response = await fetch(`${API_BASE}/status/${currentJobId}`);
            const status = await response.json();

            if (status.status === 'completed') {
                clearInterval(pollingInterval);
                updateStatus('completed');
                startBtn.style.display = 'flex';
                stopBtn.style.display = 'none';
                progressItem.style.display = 'none';
                
                addLog('✅ Scraping completed successfully!', 'success');
                if (status.output_file) {
                    addLog(`Output saved to: ${status.output_file}`, 'success');
                }
                currentJobId = null;
                // Load insights after scraping completes
                loadInsights();
            } else if (status.status === 'failed') {
                clearInterval(pollingInterval);
                updateStatus('error');
                startBtn.style.display = 'flex';
                stopBtn.style.display = 'none';
                progressItem.style.display = 'none';
                
                addLog(`❌ Scraping failed: ${status.error || 'Unknown error'}`, 'error');
                currentJobId = null;
            } else if (status.status === 'running') {
                // Show running status - display actual status message
                updateStatus('running');
                if (status.message) {
                    statusText.textContent = status.message;
                } else {
                    statusText.textContent = 'Processing...';
                }
                // Hide progress bar, just show status text
                progressItem.style.display = 'none';
                
                // Display logs from backend - track which logs we've already shown
                if (status.logs && Array.isArray(status.logs)) {
                    status.logs.forEach(log => {
                        const logType = log.level === 'ERROR' ? 'error' : 
                                       log.level === 'WARNING' ? 'error' : 
                                       log.level === 'INFO' ? 'info' : 'info';
                        
                        // Extract just the message part (remove timestamp and level if present)
                        const logMessage = log.message.split('|').pop()?.trim() || log.message;
                        
                        // Create unique key for this log (message + time to handle same message at different times)
                        const logKey = `${log.time || Date.now()}_${logMessage}`;
                        
                        // Only add if not already displayed
                        if (!displayedLogs.has(logKey)) {
                            addLog(logMessage, logType);
                            displayedLogs.add(logKey);
                        }
                    });
                }
            }
        } catch (error) {
            console.error('Error polling status:', error);
        }
    }, 2000);
}

// Update Status
function updateStatus(status) {
    statusText.textContent = status.charAt(0).toUpperCase() + status.slice(1);
    statusDot.className = `status-dot ${status}`;
    
    if (status === 'running') {
        progressItem.style.display = 'flex';
    }
}

// Update Progress
function updateProgress(current, total) {
    const percentage = total > 0 ? (current / total) * 100 : 0;
    progressFill.style.width = `${percentage}%`;
    progressText.textContent = `${Math.floor(current)}/${total}`;
}

// Add Log
function addLog(message, type = 'info') {
    const time = new Date().toLocaleTimeString();
    const icon = type === 'success' ? '✓' : type === 'error' ? '✗' : 'ℹ';
    
    const logEntry = document.createElement('div');
    logEntry.className = `log-entry ${type}`;
    logEntry.innerHTML = `
        <span class="log-time">${time}</span>
        <span class="log-icon">${icon}</span>
        <span class="log-message">${message}</span>
    `;
    
    // Remove "no logs" message if present
    const noLogs = logsContainer.querySelector('.no-logs');
    if (noLogs) {
        noLogs.remove();
    }
    
    logsContainer.insertBefore(logEntry, logsContainer.firstChild);
    
    // Keep only last 100 logs
    const logs = logsContainer.querySelectorAll('.log-entry');
    if (logs.length > 100) {
        logs[logs.length - 1].remove();
    }
}

// Check Backend Connection
async function checkBackend() {
    try {
        const response = await fetch(`${API_BASE}/health`);
        if (response.ok) {
            addLog('✓ Backend connected', 'success');
            return true;
        }
    } catch (error) {
        addLog('⚠ Backend not available. Start server with: python run_server.py', 'error');
        return false;
    }
    return false;
}

// Load Insights
async function loadInsights() {
    if (!insightsLoading || !insightsContent || !insightsEmpty) {
        return;
    }
    
    try {
        insightsLoading.style.display = 'block';
        insightsContent.classList.remove('active');
        insightsEmpty.classList.add('hidden');

        const response = await fetch(`${API_BASE}/data`);
        if (!response.ok) {
            const errorText = await response.text();
            let errorMessage = 'Failed to fetch data';
            try {
                const errorData = JSON.parse(errorText);
                errorMessage = errorData.error || errorMessage;
            } catch (e) {
                errorMessage = errorText || `HTTP ${response.status}: ${response.statusText}`;
            }
            throw new Error(errorMessage);
        }

        const data = await response.json();
        
        // Handle error response
        if (data.error) {
            throw new Error(data.error);
        }
        
        // Handle empty array or no data
        if (!data || !Array.isArray(data) || data.length === 0) {
            insightsEmpty.classList.remove('hidden');
            insightsContent.classList.remove('active');
            insightsLoading.style.display = 'none';
            return;
        }

        // Update stats
        updateStats(data);
        
        // Update charts
        updateCharts(data);
        
        insightsContent.classList.add('active');
        insightsEmpty.classList.add('hidden');
        insightsLoading.style.display = 'none';
        
        addLog(`✅ Insights loaded: ${data.length} records`, 'success');
        
    } catch (error) {
        console.error('Error loading insights:', error);
        addLog(`⚠️ Failed to load insights: ${error.message}`, 'error');
        insightsEmpty.classList.remove('hidden');
        insightsContent.classList.remove('active');
        insightsLoading.style.display = 'none';
    }
}

// Update Stats
function updateStats(data) {
    if (!totalRecordsEl || !totalCategoriesEl || !recordsWithPhoneEl || !recordsWithAddressEl) {
        return;
    }
    
    const total = data.length;
    const categories = new Set(
        data.map(item => {
            const cat = item.category;
            return cat ? String(cat).trim() : null;
        }).filter(Boolean)
    );
    const withPhone = data.filter(
        item => {
            const phone = item.phone;
            return phone && String(phone).trim() !== '';
        }
    ).length;
      
    const withAddress = data.filter(item => {
        const address = item.address;
        return address && String(address).trim() !== '';
    }).length;

    totalRecordsEl.textContent = total.toLocaleString();
    totalCategoriesEl.textContent = categories.size;
    recordsWithPhoneEl.textContent = withPhone.toLocaleString();
    recordsWithAddressEl.textContent = withAddress.toLocaleString();
}

// Get CSS Variable Value
function getCSSVariable(variable) {
    return getComputedStyle(document.documentElement).getPropertyValue(variable).trim();
}

// Update Charts
function updateCharts(data) {
    // Get current theme
    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    
    // Category Chart
    const categoryCounts = {};
    data.forEach(item => {
        const cat = item.category ? String(item.category).trim() : 'Unknown';
        categoryCounts[cat] = (categoryCounts[cat] || 0) + 1;
    });

    const categoryLabels = Object.keys(categoryCounts);
    const categoryValues = Object.values(categoryCounts);

    const categoryCtx = document.getElementById('categoryChart');
    if (categoryChart) {
        categoryChart.destroy();
    }
    
    // Professional bright/pastel color palette (adapts to theme)
    const professionalColors = isDark ? [
        'rgba(0, 212, 255, 0.8)',    // Neon blue
        'rgba(0, 255, 136, 0.8)',    // Neon green
        'rgba(183, 148, 246, 0.8)',  // Neon purple
        'rgba(255, 215, 0, 0.8)',    // Neon yellow
        'rgba(255, 20, 147, 0.8)',   // Neon pink
        'rgba(79, 209, 199, 0.8)',   // Neon teal
        'rgba(184, 197, 214, 0.8)',  // Light blue-gray
        'rgba(255, 165, 0, 0.8)',    // Neon orange
        'rgba(142, 68, 173, 0.8)',   // Bright violet
        'rgba(22, 160, 133, 0.8)',   // Bright emerald
    ] : [
        'rgba(52, 152, 219, 0.8)',   // Bright blue
        'rgba(46, 204, 113, 0.8)',   // Bright green
        'rgba(155, 89, 182, 0.8)',   // Bright purple
        'rgba(241, 196, 15, 0.8)',   // Bright yellow
        'rgba(231, 76, 60, 0.8)',    // Bright red
        'rgba(26, 188, 156, 0.8)',   // Bright teal
        'rgba(52, 73, 94, 0.8)',     // Dark blue-gray
        'rgba(243, 156, 18, 0.8)',   // Bright orange
        'rgba(142, 68, 173, 0.8)',   // Bright violet
        'rgba(22, 160, 133, 0.8)',   // Bright emerald
    ];
    
    const professionalBorders = isDark ? [
        'rgba(0, 212, 255, 1)',
        'rgba(0, 255, 136, 1)',
        'rgba(183, 148, 246, 1)',
        'rgba(255, 215, 0, 1)',
        'rgba(255, 20, 147, 1)',
        'rgba(79, 209, 199, 1)',
        'rgba(184, 197, 214, 1)',
        'rgba(255, 165, 0, 1)',
        'rgba(142, 68, 173, 1)',
        'rgba(22, 160, 133, 1)',
    ] : [
        'rgba(52, 152, 219, 1)',
        'rgba(46, 204, 113, 1)',
        'rgba(155, 89, 182, 1)',
        'rgba(241, 196, 15, 1)',
        'rgba(231, 76, 60, 1)',
        'rgba(26, 188, 156, 1)',
        'rgba(52, 73, 94, 1)',
        'rgba(243, 156, 18, 1)',
        'rgba(142, 68, 173, 1)',
        'rgba(22, 160, 133, 1)',
    ];
    
    categoryChart = new Chart(categoryCtx, {
        type: 'bar',
        data: {
            labels: categoryLabels,
            datasets: [{
                label: 'Records',
                data: categoryValues,
                backgroundColor: categoryLabels.map((_, i) => professionalColors[i % professionalColors.length]),
                borderColor: categoryLabels.map((_, i) => professionalBorders[i % professionalBorders.length]),
                borderWidth: 2,
                borderRadius: 8
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    backgroundColor: isDark ? 'rgba(15, 20, 25, 0.95)' : 'rgba(26, 26, 26, 0.95)',
                    padding: 12,
                    titleFont: { size: 14, weight: 'bold', color: '#ffffff' },
                    bodyFont: { size: 13, color: '#e0e0e0' },
                    borderColor: isDark ? 'rgba(0, 212, 255, 0.5)' : 'rgba(52, 152, 219, 0.5)',
                    borderWidth: 1
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        stepSize: 1,
                        color: isDark ? '#b8c5d6' : '#1a1a1a',
                        font: {
                            weight: '500'
                        }
                    },
                    grid: {
                        color: isDark ? 'rgba(255, 255, 255, 0.1)' : 'rgba(52, 152, 219, 0.15)',
                        lineWidth: 1
                    }
                },
                x: {
                    grid: {
                        display: false
                    },
                    ticks: {
                        maxRotation: 45,
                        minRotation: 45,
                        color: isDark ? '#b8c5d6' : '#1a1a1a',
                        font: {
                            weight: '500'
                        }
                    }
                }
            }
        }
    });

    // Pie Chart - Percentage of entries by category
    const pieCategoryCounts = {};
    data.forEach(item => {
        const cat = item.category ? String(item.category).trim() : 'Unknown';
        pieCategoryCounts[cat] = (pieCategoryCounts[cat] || 0) + 1;
    });
    
    const pieLabels = Object.keys(pieCategoryCounts);
    const pieValues = Object.values(pieCategoryCounts);
    const total = pieValues.reduce((a, b) => a + b, 0);
    
    const pieCtx = document.getElementById('pieChart');
    if (pieChart) {
        pieChart.destroy();
    }
    
    // Professional bright/pastel color palette (adapts to theme)
    const pieColors = isDark ? [
        'rgba(0, 212, 255, 0.85)',    // Neon blue
        'rgba(0, 255, 136, 0.85)',    // Neon green
        'rgba(183, 148, 246, 0.85)',  // Neon purple
        'rgba(255, 215, 0, 0.85)',    // Neon yellow
        'rgba(255, 20, 147, 0.85)',   // Neon pink
        'rgba(79, 209, 199, 0.85)',   // Neon teal
        'rgba(184, 197, 214, 0.85)',  // Light blue-gray
        'rgba(255, 165, 0, 0.85)',    // Neon orange
        'rgba(142, 68, 173, 0.85)',   // Bright violet
        'rgba(22, 160, 133, 0.85)',   // Bright emerald
    ] : [
        'rgba(52, 152, 219, 0.85)',   // Bright blue
        'rgba(46, 204, 113, 0.85)',   // Bright green
        'rgba(155, 89, 182, 0.85)',   // Bright purple
        'rgba(241, 196, 15, 0.85)',   // Bright yellow
        'rgba(231, 76, 60, 0.85)',    // Bright red
        'rgba(26, 188, 156, 0.85)',   // Bright teal
        'rgba(52, 73, 94, 0.85)',     // Dark blue-gray
        'rgba(243, 156, 18, 0.85)',   // Bright orange
        'rgba(142, 68, 173, 0.85)',   // Bright violet
        'rgba(22, 160, 133, 0.85)',   // Bright emerald
    ];
    
    const pieBorders = isDark ? [
        'rgba(0, 212, 255, 1)',
        'rgba(0, 255, 136, 1)',
        'rgba(183, 148, 246, 1)',
        'rgba(255, 215, 0, 1)',
        'rgba(255, 20, 147, 1)',
        'rgba(79, 209, 199, 1)',
        'rgba(184, 197, 214, 1)',
        'rgba(255, 165, 0, 1)',
        'rgba(142, 68, 173, 1)',
        'rgba(22, 160, 133, 1)',
    ] : [
        'rgba(52, 152, 219, 1)',
        'rgba(46, 204, 113, 1)',
        'rgba(155, 89, 182, 1)',
        'rgba(241, 196, 15, 1)',
        'rgba(231, 76, 60, 1)',
        'rgba(26, 188, 156, 1)',
        'rgba(52, 73, 94, 1)',
        'rgba(243, 156, 18, 1)',
        'rgba(142, 68, 173, 1)',
        'rgba(22, 160, 133, 1)',
    ];
    
    pieChart = new Chart(pieCtx, {
        type: 'pie',
        data: {
            labels: pieLabels,
            datasets: [{
                data: pieValues,
                backgroundColor: pieLabels.map((_, i) => pieColors[i % pieColors.length]),
                borderColor: pieLabels.map((_, i) => pieBorders[i % pieBorders.length]),
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        padding: 15,
                        font: {
                            size: 12,
                            weight: '500'
                        },
                        color: isDark ? '#b8c5d6' : '#1a1a1a',
                        usePointStyle: true,
                        pointStyle: 'circle',
                        generateLabels: function(chart) {
                            const data = chart.data;
                            if (data.labels.length && data.datasets.length) {
                                return data.labels.map((label, i) => {
                                    const value = data.datasets[0].data[i];
                                    const percentage = ((value / total) * 100).toFixed(1);
                                    return {
                                        text: `${label}: ${percentage}% (${value})`,
                                        fillStyle: data.datasets[0].backgroundColor[i],
                                        strokeStyle: data.datasets[0].borderColor[i],
                                        lineWidth: data.datasets[0].borderWidth,
                                        hidden: false,
                                        index: i
                                    };
                                });
                            }
                            return [];
                        }
                    }
                },
                tooltip: {
                    backgroundColor: isDark ? 'rgba(15, 20, 25, 0.95)' : 'rgba(26, 26, 26, 0.95)',
                    padding: 12,
                    titleFont: { size: 14, weight: 'bold', color: '#ffffff' },
                    bodyFont: { size: 13, color: '#e0e0e0' },
                    borderColor: isDark ? 'rgba(0, 212, 255, 0.5)' : 'rgba(52, 152, 219, 0.5)',
                    borderWidth: 1,
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.parsed || 0;
                            const percentage = ((value / total) * 100).toFixed(1);
                            return `${label}: ${value} (${percentage}%)`;
                        }
                    }
                }
            }
        }
    });
}

// Theme Toggle Functionality
function initThemeToggle() {
    const themeToggle = document.getElementById('theme-toggle');
    if (!themeToggle) return;
    
    // Check for saved theme preference or default to light
    const savedTheme = localStorage.getItem('dashboard-theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);
    updateThemeIcon(savedTheme);
    
    themeToggle.addEventListener('click', () => {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        
        document.documentElement.setAttribute('data-theme', newTheme);
        localStorage.setItem('dashboard-theme', newTheme);
        updateThemeIcon(newTheme);
        
        // Update chart colors based on theme
        if (categoryChart || completenessChart) {
            loadInsights();
        }
    });
}

function updateThemeIcon(theme) {
    const themeIcon = document.querySelector('.theme-icon');
    if (themeIcon) {
        themeIcon.textContent = theme === 'dark' ? '☀️' : '🌙';
    }
}

// Initialize on load
document.addEventListener('DOMContentLoaded', () => {
    init();
    initThemeToggle();
    checkBackend();
    // Load insights on page load
    setTimeout(loadInsights, 1000);
});