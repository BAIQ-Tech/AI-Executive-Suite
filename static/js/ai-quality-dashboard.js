/**
 * AI Quality Dashboard JavaScript
 */

class AIQualityDashboard {
    constructor() {
        this.charts = {};
        this.currentTimeRange = 30;
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.initializeCharts();
        this.loadDashboardData();
    }
    
    setupEventListeners() {
        document.getElementById('refresh-btn').addEventListener('click', () => {
            this.loadDashboardData();
        });
        
        document.getElementById('time-range').addEventListener('change', (e) => {
            this.currentTimeRange = parseInt(e.target.value);
            this.loadDashboardData();
        });
        
        document.getElementById('load-low-quality').addEventListener('click', () => {
            this.loadLowQualityResponses();
        });
    }
    
    initializeCharts() {
        // Quality Trends Chart
        const trendsCtx = document.getElementById('quality-trends-chart').getContext('2d');
        this.charts.trends = new Chart(trendsCtx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [
                    {
                        label: 'CEO',
                        data: [],
                        borderColor: '#007bff',
                        backgroundColor: 'rgba(0, 123, 255, 0.1)',
                        fill: false,
                        tension: 0.4
                    },
                    {
                        label: 'CTO',
                        data: [],
                        borderColor: '#28a745',
                        backgroundColor: 'rgba(40, 167, 69, 0.1)',
                        fill: false,
                        tension: 0.4
                    },
                    {
                        label: 'CFO',
                        data: [],
                        borderColor: '#ffc107',
                        backgroundColor: 'rgba(255, 193, 7, 0.1)',
                        fill: false,
                        tension: 0.4
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 5,
                        title: {
                            display: true,
                            text: 'Rating (1-5)'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'Time'
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: true,
                        position: 'top'
                    }
                }
            }
        });
        
        // Satisfaction Distribution Chart
        const satisfactionCtx = document.getElementById('satisfaction-chart').getContext('2d');
        this.charts.satisfaction = new Chart(satisfactionCtx, {
            type: 'doughnut',
            data: {
                labels: [],
                datasets: [{
                    data: [],
                    backgroundColor: [
                        '#dc3545',
                        '#fd7e14',
                        '#ffc107',
                        '#28a745',
                        '#007bff'
                    ]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
        
        // Accuracy Distribution Chart
        const accuracyCtx = document.getElementById('accuracy-chart').getContext('2d');
        this.charts.accuracy = new Chart(accuracyCtx, {
            type: 'doughnut',
            data: {
                labels: [],
                datasets: [{
                    data: [],
                    backgroundColor: [
                        '#dc3545',
                        '#fd7e14',
                        '#ffc107',
                        '#28a745',
                        '#007bff'
                    ]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    }
    
    async loadDashboardData() {
        try {
            await Promise.all([
                this.loadQualityMetrics(),
                this.loadExecutiveComparison(),
                this.loadQualityTrends(),
                this.loadRecommendations()
            ]);
        } catch (error) {
            console.error('Error loading dashboard data:', error);
            this.showError('Failed to load dashboard data');
        }
    }
    
    async loadQualityMetrics() {
        try {
            const response = await fetch(`/ai-quality/api/metrics?days=${this.currentTimeRange}`);
            const result = await response.json();
            
            if (result.success) {
                this.updateOverviewMetrics(result.metrics);
                this.updateDistributionCharts(result.metrics);
            }
        } catch (error) {
            console.error('Error loading quality metrics:', error);
        }
    }
    
    updateOverviewMetrics(metrics) {
        document.getElementById('overall-satisfaction').textContent = 
            metrics.average_rating ? `${metrics.average_rating}/5` : '--';
        document.getElementById('overall-accuracy').textContent = 
            metrics.average_accuracy ? `${metrics.average_accuracy}/5` : '--';
        document.getElementById('avg-response-time').textContent = 
            metrics.response_time_avg ? `${metrics.response_time_avg}s` : '--';
        document.getElementById('total-responses').textContent = 
            metrics.total_responses || '--';
        
        // Update trends
        this.updateTrendIndicator('satisfaction-trend', metrics.improvement_trend);
        this.updateTrendIndicator('accuracy-trend', metrics.improvement_trend);
        this.updateTrendIndicator('response-time-trend', -metrics.improvement_trend); // Negative for response time
        this.updateTrendIndicator('responses-trend', metrics.improvement_trend);
    }
    
    updateTrendIndicator(elementId, trend) {
        const element = document.getElementById(elementId);
        if (!element) return;
        
        element.className = 'metric-trend';
        
        if (trend > 0.1) {
            element.classList.add('positive');
            element.textContent = `↗ +${trend.toFixed(2)}`;
        } else if (trend < -0.1) {
            element.classList.add('negative');
            element.textContent = `↘ ${trend.toFixed(2)}`;
        } else {
            element.classList.add('neutral');
            element.textContent = '→ Stable';
        }
    }
    
    updateDistributionCharts(metrics) {
        // Update satisfaction chart
        if (metrics.satisfaction_distribution && Object.keys(metrics.satisfaction_distribution).length > 0) {
            const satisfactionLabels = Object.keys(metrics.satisfaction_distribution);
            const satisfactionData = Object.values(metrics.satisfaction_distribution);
            
            this.charts.satisfaction.data.labels = satisfactionLabels;
            this.charts.satisfaction.data.datasets[0].data = satisfactionData;
            this.charts.satisfaction.update();
        }
        
        // Update accuracy chart
        if (metrics.accuracy_distribution && Object.keys(metrics.accuracy_distribution).length > 0) {
            const accuracyLabels = Object.keys(metrics.accuracy_distribution);
            const accuracyData = Object.values(metrics.accuracy_distribution);
            
            this.charts.accuracy.data.labels = accuracyLabels;
            this.charts.accuracy.data.datasets[0].data = accuracyData;
            this.charts.accuracy.update();
        }
    }
    
    async loadExecutiveComparison() {
        try {
            const response = await fetch('/ai-quality/api/executive-comparison');
            const result = await response.json();
            
            if (result.success) {
                this.updateExecutiveComparison(result.comparison);
            }
        } catch (error) {
            console.error('Error loading executive comparison:', error);
        }
    }
    
    updateExecutiveComparison(comparison) {
        const container = document.getElementById('executive-comparison');
        container.innerHTML = '';
        
        const executives = ['ceo', 'cto', 'cfo'];
        
        executives.forEach(execType => {
            const metrics = comparison[execType] || {};
            
            const card = document.createElement('div');
            card.className = 'executive-card';
            
            card.innerHTML = `
                <h4>${execType.toUpperCase()}</h4>
                <div class="executive-metrics">
                    <div class="executive-metric">
                        <div class="executive-metric-label">Satisfaction</div>
                        <div class="executive-metric-value">${metrics.average_rating || '--'}</div>
                    </div>
                    <div class="executive-metric">
                        <div class="executive-metric-label">Accuracy</div>
                        <div class="executive-metric-value">${metrics.average_accuracy || '--'}</div>
                    </div>
                    <div class="executive-metric">
                        <div class="executive-metric-label">Response Time</div>
                        <div class="executive-metric-value">${metrics.response_time_avg ? metrics.response_time_avg + 's' : '--'}</div>
                    </div>
                    <div class="executive-metric">
                        <div class="executive-metric-label">Responses</div>
                        <div class="executive-metric-value">${metrics.total_responses || '--'}</div>
                    </div>
                </div>
            `;
            
            container.appendChild(card);
        });
    }
    
    async loadQualityTrends() {
        try {
            const response = await fetch(`/ai-quality/api/quality-trends?days=${this.currentTimeRange}`);
            const result = await response.json();
            
            if (result.success) {
                this.updateTrendsChart(result.trends);
            }
        } catch (error) {
            console.error('Error loading quality trends:', error);
        }
    }
    
    updateTrendsChart(trends) {
        // Process trends data for chart
        const allTimestamps = new Set();
        
        // Collect all unique timestamps
        Object.values(trends).forEach(execTrends => {
            execTrends.forEach(entry => {
                allTimestamps.add(entry.timestamp);
            });
        });
        
        const sortedTimestamps = Array.from(allTimestamps).sort();
        const labels = sortedTimestamps.map(ts => new Date(ts).toLocaleDateString());
        
        // Update chart data
        this.charts.trends.data.labels = labels;
        
        const executives = ['ceo', 'cto', 'cfo'];
        executives.forEach((execType, index) => {
            const execTrends = trends[execType] || [];
            const data = sortedTimestamps.map(timestamp => {
                const entry = execTrends.find(e => e.timestamp === timestamp);
                return entry ? entry.rating : null;
            });
            
            this.charts.trends.data.datasets[index].data = data;
        });
        
        this.charts.trends.update();
    }
    
    async loadRecommendations() {
        try {
            const response = await fetch('/ai-quality/api/recommendations');
            const result = await response.json();
            
            if (result.success) {
                this.updateRecommendations(result.recommendations);
            }
        } catch (error) {
            console.error('Error loading recommendations:', error);
        }
    }
    
    updateRecommendations(recommendations) {
        const section = document.getElementById('recommendations-section');
        const container = document.getElementById('recommendations-container');
        
        if (recommendations.length === 0) {
            section.style.display = 'none';
            return;
        }
        
        section.style.display = 'block';
        container.innerHTML = '';
        
        recommendations.forEach(rec => {
            const item = document.createElement('div');
            item.className = `recommendation-item ${rec.priority}`;
            
            item.innerHTML = `
                <div class="recommendation-header">
                    <span class="recommendation-type">${rec.type.replace('_', ' ')}</span>
                    <span class="recommendation-priority ${rec.priority}">${rec.priority}</span>
                </div>
                <div class="recommendation-message">${rec.message}</div>
                <div class="recommendation-suggestion">${rec.suggestion}</div>
            `;
            
            container.appendChild(item);
        });
    }
    
    async loadLowQualityResponses() {
        try {
            const threshold = document.getElementById('quality-threshold').value;
            const response = await fetch(`/ai-quality/api/low-quality-responses?threshold=${threshold}&limit=20`);
            const result = await response.json();
            
            if (result.success) {
                this.updateLowQualityResponses(result.low_quality_responses);
            }
        } catch (error) {
            console.error('Error loading low quality responses:', error);
        }
    }
    
    updateLowQualityResponses(responses) {
        const container = document.getElementById('low-quality-responses');
        container.innerHTML = '';
        
        if (responses.length === 0) {
            container.innerHTML = '<p>No low quality responses found for the selected threshold.</p>';
            return;
        }
        
        responses.forEach(response => {
            const item = document.createElement('div');
            item.className = 'low-quality-item';
            
            const stars = '★'.repeat(response.rating) + '☆'.repeat(5 - response.rating);
            
            item.innerHTML = `
                <div class="low-quality-header">
                    <span class="low-quality-executive">${response.executive_type}</span>
                    <div class="low-quality-rating">
                        <span class="rating-value">${response.rating}/5</span>
                        <span class="rating-stars-display">${stars}</span>
                    </div>
                </div>
                ${response.feedback_text ? `<div class="low-quality-feedback">"${response.feedback_text}"</div>` : ''}
                <div class="low-quality-meta">
                    <span>Decision ID: ${response.decision_id}</span>
                    <span>${new Date(response.timestamp).toLocaleString()}</span>
                </div>
            `;
            
            container.appendChild(item);
        });
    }
    
    showError(message) {
        console.error(message);
        // You could implement a proper notification system here
        alert(`Error: ${message}`);
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new AIQualityDashboard();
});