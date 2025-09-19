/**
 * Monitoring Dashboard JavaScript
 * Handles real-time updates and chart rendering
 */

class MonitoringDashboard {
    constructor() {
        this.charts = {};
        this.refreshInterval = null;
        this.refreshRate = 30000; // 30 seconds
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.initializeCharts();
        this.loadInitialData();
        this.startAutoRefresh();
    }
    
    setupEventListeners() {
        document.getElementById('refresh-btn').addEventListener('click', () => {
            this.refreshData();
        });
        
        // Handle alert resolution
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('resolve-btn')) {
                const alertId = e.target.dataset.alertId;
                this.resolveAlert(alertId);
            }
        });
    }
    
    initializeCharts() {
        const chartOptions = {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100
                }
            },
            plugins: {
                legend: {
                    display: false
                }
            }
        };
        
        // CPU Chart
        const cpuCtx = document.getElementById('cpu-chart').getContext('2d');
        this.charts.cpu = new Chart(cpuCtx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    data: [],
                    borderColor: '#007bff',
                    backgroundColor: 'rgba(0, 123, 255, 0.1)',
                    fill: true,
                    tension: 0.4
                }]
            },
            options: chartOptions
        });
        
        // Memory Chart
        const memoryCtx = document.getElementById('memory-chart').getContext('2d');
        this.charts.memory = new Chart(memoryCtx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    data: [],
                    borderColor: '#28a745',
                    backgroundColor: 'rgba(40, 167, 69, 0.1)',
                    fill: true,
                    tension: 0.4
                }]
            },
            options: chartOptions
        });
        
        // Response Time Chart
        const responseTimeCtx = document.getElementById('response-time-chart').getContext('2d');
        this.charts.responseTime = new Chart(responseTimeCtx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    data: [],
                    borderColor: '#ffc107',
                    backgroundColor: 'rgba(255, 193, 7, 0.1)',
                    fill: true,
                    tension: 0.4
                }]
            },
            options: {
                ...chartOptions,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
        
        // Error Rate Chart
        const errorRateCtx = document.getElementById('error-rate-chart').getContext('2d');
        this.charts.errorRate = new Chart(errorRateCtx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    data: [],
                    borderColor: '#dc3545',
                    backgroundColor: 'rgba(220, 53, 69, 0.1)',
                    fill: true,
                    tension: 0.4
                }]
            },
            options: chartOptions
        });
    }
    
    async loadInitialData() {
        try {
            await Promise.all([
                this.updateMetrics(),
                this.updateHealthChecks(),
                this.updateAlerts(),
                this.updateSystemInfo()
            ]);
        } catch (error) {
            console.error('Error loading initial data:', error);
            this.showError('Failed to load dashboard data');
        }
    }
    
    async refreshData() {
        const refreshBtn = document.getElementById('refresh-btn');
        refreshBtn.textContent = 'Refreshing...';
        refreshBtn.disabled = true;
        
        try {
            await this.loadInitialData();
        } finally {
            refreshBtn.textContent = 'Refresh';
            refreshBtn.disabled = false;
        }
    }
    
    async updateMetrics() {
        try {
            const response = await fetch('/monitoring/api/metrics');
            const result = await response.json();
            
            if (result.success) {
                this.updateDashboardData(result.data);
            } else {
                throw new Error(result.error);
            }
        } catch (error) {
            console.error('Error updating metrics:', error);
            throw error;
        }
    }
    
    updateDashboardData(data) {
        // Update status overview
        this.updateSystemStatus(data.system_status);
        this.updateCurrentMetrics(data.current_metrics);
        
        // Update charts with historical data
        if (data.historical_metrics && data.historical_metrics.length > 0) {
            this.updateCharts(data.historical_metrics);
        }
    }
    
    updateSystemStatus(status) {
        const statusIndicator = document.getElementById('status-indicator');
        const statusDot = statusIndicator.querySelector('.status-dot');
        const statusText = statusIndicator.querySelector('.status-text');
        
        statusDot.className = 'status-dot';
        if (status === 'critical') {
            statusDot.classList.add('critical');
            statusText.textContent = 'Critical Issues';
        } else if (status === 'warning') {
            statusDot.classList.add('warning');
            statusText.textContent = 'Warning';
        } else {
            statusText.textContent = 'Healthy';
        }
    }
    
    updateCurrentMetrics(metrics) {
        // Update metric values
        document.getElementById('requests-value').textContent = 
            Math.round(metrics.requests_per_minute);
        document.getElementById('response-time-value').textContent = 
            `${metrics.response_time_avg.toFixed(2)}s`;
        
        // Update current values in charts
        document.getElementById('cpu-current').textContent = 
            `${metrics.cpu_percent.toFixed(1)}%`;
        document.getElementById('memory-current').textContent = 
            `${metrics.memory_percent.toFixed(1)}%`;
        document.getElementById('response-time-current').textContent = 
            `${metrics.response_time_avg.toFixed(2)}s`;
        document.getElementById('error-rate-current').textContent = 
            `${metrics.error_rate.toFixed(1)}%`;
    }
    
    updateCharts(historicalMetrics) {
        const maxPoints = 20; // Show last 20 data points
        const recentMetrics = historicalMetrics.slice(-maxPoints);
        
        const labels = recentMetrics.map(m => {
            const date = new Date(m.timestamp);
            return date.toLocaleTimeString();
        });
        
        // Update CPU chart
        this.charts.cpu.data.labels = labels;
        this.charts.cpu.data.datasets[0].data = recentMetrics.map(m => m.cpu_percent);
        this.charts.cpu.update('none');
        
        // Update Memory chart
        this.charts.memory.data.labels = labels;
        this.charts.memory.data.datasets[0].data = recentMetrics.map(m => m.memory_percent);
        this.charts.memory.update('none');
        
        // Update Response Time chart
        this.charts.responseTime.data.labels = labels;
        this.charts.responseTime.data.datasets[0].data = recentMetrics.map(m => m.response_time_avg);
        this.charts.responseTime.update('none');
        
        // Update Error Rate chart
        this.charts.errorRate.data.labels = labels;
        this.charts.errorRate.data.datasets[0].data = recentMetrics.map(m => m.error_rate);
        this.charts.errorRate.update('none');
    }
    
    async updateHealthChecks() {
        try {
            const response = await fetch('/monitoring/api/health');
            const result = await response.json();
            
            if (result.success) {
                this.renderHealthChecks(result.health_checks);
            } else {
                throw new Error(result.error);
            }
        } catch (error) {
            console.error('Error updating health checks:', error);
            throw error;
        }
    }
    
    renderHealthChecks(healthChecks) {
        const container = document.getElementById('health-checks');
        container.innerHTML = '';
        
        healthChecks.forEach(check => {
            const checkElement = document.createElement('div');
            checkElement.className = `health-check ${check.status}`;
            
            checkElement.innerHTML = `
                <div class="health-check-header">
                    <span class="health-service">${check.service.replace('_', ' ')}</span>
                    <span class="health-status ${check.status}">${check.status}</span>
                </div>
                <div class="health-message">${check.message}</div>
                ${check.response_time ? 
                    `<div class="health-response-time">Response time: ${check.response_time.toFixed(2)}s</div>` : 
                    ''
                }
            `;
            
            container.appendChild(checkElement);
        });
    }
    
    async updateAlerts() {
        try {
            const response = await fetch('/monitoring/api/alerts');
            const result = await response.json();
            
            if (result.success) {
                this.renderAlerts(result.alerts);
            } else {
                throw new Error(result.error);
            }
        } catch (error) {
            console.error('Error updating alerts:', error);
            throw error;
        }
    }
    
    renderAlerts(alerts) {
        const alertsSection = document.getElementById('alerts-section');
        const alertsContainer = document.getElementById('alerts-container');
        
        if (alerts.length === 0) {
            alertsSection.style.display = 'none';
            return;
        }
        
        alertsSection.style.display = 'block';
        alertsContainer.innerHTML = '';
        
        alerts.forEach(alert => {
            const alertElement = document.createElement('div');
            alertElement.className = `alert-item ${alert.severity}`;
            
            const timestamp = new Date(alert.timestamp).toLocaleString();
            
            alertElement.innerHTML = `
                <div class="alert-header">
                    <span class="alert-severity ${alert.severity}">${alert.severity}</span>
                    <span class="alert-type">${alert.type}</span>
                </div>
                <div class="alert-message">${alert.message}</div>
                <div class="alert-timestamp">${timestamp}</div>
                <div class="alert-actions">
                    <button class="resolve-btn" data-alert-id="${alert.id}">Resolve</button>
                </div>
            `;
            
            alertsContainer.appendChild(alertElement);
        });
    }
    
    async updateSystemInfo() {
        try {
            const response = await fetch('/monitoring/api/system-info');
            const result = await response.json();
            
            if (result.success) {
                this.renderSystemInfo(result.system_info);
            } else {
                throw new Error(result.error);
            }
        } catch (error) {
            console.error('Error updating system info:', error);
            throw error;
        }
    }
    
    renderSystemInfo(systemInfo) {
        const container = document.getElementById('system-info');
        container.innerHTML = '';
        
        const infoItems = [
            { label: 'Platform', value: systemInfo.platform },
            { label: 'Python Version', value: systemInfo.python_version },
            { label: 'CPU Cores', value: systemInfo.cpu_count },
            { label: 'Total Memory', value: this.formatBytes(systemInfo.total_memory) },
            { label: 'Total Disk', value: this.formatBytes(systemInfo.disk_total) },
            { label: 'Boot Time', value: new Date(systemInfo.boot_time).toLocaleString() }
        ];
        
        infoItems.forEach(item => {
            const infoElement = document.createElement('div');
            infoElement.className = 'info-item';
            
            infoElement.innerHTML = `
                <div class="info-label">${item.label}</div>
                <div class="info-value">${item.value}</div>
            `;
            
            container.appendChild(infoElement);
        });
    }
    
    async resolveAlert(alertId) {
        try {
            const response = await fetch(`/monitoring/api/alerts/${alertId}/resolve`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            const result = await response.json();
            
            if (result.success) {
                // Refresh alerts to show updated state
                await this.updateAlerts();
                this.showSuccess('Alert resolved successfully');
            } else {
                throw new Error(result.error);
            }
        } catch (error) {
            console.error('Error resolving alert:', error);
            this.showError('Failed to resolve alert');
        }
    }
    
    startAutoRefresh() {
        this.refreshInterval = setInterval(() => {
            this.updateMetrics();
            this.updateAlerts();
        }, this.refreshRate);
    }
    
    stopAutoRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
        }
    }
    
    formatBytes(bytes) {
        if (bytes === 0) return '0 Bytes';
        
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
    
    showError(message) {
        // Simple error display - could be enhanced with a proper notification system
        console.error(message);
        alert(`Error: ${message}`);
    }
    
    showSuccess(message) {
        // Simple success display - could be enhanced with a proper notification system
        console.log(message);
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new MonitoringDashboard();
});