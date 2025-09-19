/**
 * Usage Analytics Dashboard JavaScript
 */

class UsageAnalyticsDashboard {
    constructor() {
        this.charts = {};
        this.currentTimeRange = 30;
        this.currentData = null;
        
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
        
        document.getElementById('priority-filter').addEventListener('change', (e) => {
            this.filterRecommendations(e.target.value);
        });
    }
    
    initializeCharts() {
        // Feature Usage Chart
        const featureUsageCtx = document.getElementById('feature-usage-chart').getContext('2d');
        this.charts.featureUsage = new Chart(featureUsageCtx, {
            type: 'doughnut',
            data: {
                labels: [],
                datasets: [{
                    data: [],
                    backgroundColor: [
                        '#007bff', '#28a745', '#ffc107', '#dc3545', '#17a2b8',
                        '#6f42c1', '#fd7e14', '#20c997', '#6c757d', '#e83e8c'
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
        
        // User Engagement Chart
        const engagementCtx = document.getElementById('engagement-chart').getContext('2d');
        this.charts.engagement = new Chart(engagementCtx, {
            type: 'bar',
            data: {
                labels: ['Low (0-30)', 'Medium (31-60)', 'High (61-100)'],
                datasets: [{
                    label: 'Users',
                    data: [],
                    backgroundColor: ['#dc3545', '#ffc107', '#28a745']
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    }
                }
            }
        });
        
        // Session Duration Chart
        const sessionDurationCtx = document.getElementById('session-duration-chart').getContext('2d');
        this.charts.sessionDuration = new Chart(sessionDurationCtx, {
            type: 'histogram',
            data: {
                labels: ['0-2 min', '2-5 min', '5-10 min', '10-20 min', '20+ min'],
                datasets: [{
                    label: 'Sessions',
                    data: [],
                    backgroundColor: '#007bff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    }
                }
            }
        });
        
        // Usage Trends Chart
        const trendsCtx = document.getElementById('usage-trends-chart').getContext('2d');
        this.charts.trends = new Chart(trendsCtx, {
            type: 'line',
            data: {
                labels: [],
                datasets: []
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                },
                plugins: {
                    legend: {
                        position: 'top'
                    }
                }
            }
        });
    }
    
    async loadDashboardData() {
        const refreshBtn = document.getElementById('refresh-btn');
        refreshBtn.textContent = 'Loading...';
        refreshBtn.disabled = true;
        
        try {
            await Promise.all([
                this.loadUsageSummary(),
                this.loadFeatureUsage(),
                this.loadUserBehavior(),
                this.loadPerformanceIssues(),
                this.loadOptimizationRecommendations()
            ]);
        } catch (error) {
            console.error('Error loading dashboard data:', error);
            this.showError('Failed to load dashboard data');
        } finally {
            refreshBtn.textContent = 'Refresh';
            refreshBtn.disabled = false;
        }
    }
    
    async loadUsageSummary() {
        try {
            const response = await fetch('/usage-analytics/api/usage-summary');
            const result = await response.json();
            
            if (result.success) {
                this.updateUsageSummary(result.summary);
            }
        } catch (error) {
            console.error('Error loading usage summary:', error);
        }
    }
    
    updateUsageSummary(summary) {
        document.getElementById('total-events').textContent = summary.total_events || '--';
        document.getElementById('active-users').textContent = summary.active_users || '--';
        document.getElementById('avg-session-duration').textContent = 
            summary.avg_session_duration ? `${summary.avg_session_duration} min` : '--';
        document.getElementById('most-popular-feature').textContent = 
            summary.most_popular_feature || '--';
        document.getElementById('peak-usage-hour').textContent = 
            summary.peak_usage_hour !== undefined ? `${summary.peak_usage_hour}:00` : '--';
    }
    
    async loadFeatureUsage() {
        try {
            const response = await fetch(`/usage-analytics/api/feature-usage?days=${this.currentTimeRange}`);
            const result = await response.json();
            
            if (result.success) {
                this.updateFeatureUsage(result.feature_usage);
            }
        } catch (error) {
            console.error('Error loading feature usage:', error);
        }
    }
    
    updateFeatureUsage(featureUsage) {
        // Update chart
        const labels = featureUsage.map(f => f.feature_name.replace('_', ' '));
        const data = featureUsage.map(f => f.total_uses);
        
        this.charts.featureUsage.data.labels = labels;
        this.charts.featureUsage.data.datasets[0].data = data;
        this.charts.featureUsage.update();
        
        // Update feature stats list
        const container = document.getElementById('feature-stats-list');
        container.innerHTML = '';
        
        featureUsage.forEach(feature => {
            const item = document.createElement('div');
            item.className = 'feature-stat-item';
            
            const trendClass = feature.usage_trend > 0.1 ? 'positive' : 
                              feature.usage_trend < -0.1 ? 'negative' : 'neutral';
            const trendSymbol = feature.usage_trend > 0.1 ? '↗' : 
                               feature.usage_trend < -0.1 ? '↘' : '→';
            
            item.innerHTML = `
                <div class="feature-name">${feature.feature_name.replace('_', ' ')}</div>
                <div class="feature-metrics">
                    <div class="feature-metric">
                        <span class="feature-metric-value">${feature.total_uses}</span>
                        <span class="feature-metric-label">Uses</span>
                    </div>
                    <div class="feature-metric">
                        <span class="feature-metric-value">${feature.unique_users}</span>
                        <span class="feature-metric-label">Users</span>
                    </div>
                    <div class="feature-metric">
                        <span class="feature-metric-value">${feature.success_rate.toFixed(1)}%</span>
                        <span class="feature-metric-label">Success</span>
                    </div>
                    <div class="feature-metric">
                        <span class="trend-indicator ${trendClass}">${trendSymbol}</span>
                        <span class="feature-metric-label">Trend</span>
                    </div>
                </div>
            `;
            
            container.appendChild(item);
        });
    }
    
    async loadUserBehavior() {
        try {
            const response = await fetch('/usage-analytics/api/user-behavior?limit=20');
            const result = await response.json();
            
            if (result.success) {
                this.updateUserBehavior(result.user_behavior);
            }
        } catch (error) {
            console.error('Error loading user behavior:', error);
        }
    }
    
    updateUserBehavior(userBehavior) {
        // Update engagement chart
        const engagementBuckets = [0, 0, 0]; // Low, Medium, High
        userBehavior.forEach(user => {
            if (user.engagement_score <= 30) engagementBuckets[0]++;
            else if (user.engagement_score <= 60) engagementBuckets[1]++;
            else engagementBuckets[2]++;
        });
        
        this.charts.engagement.data.datasets[0].data = engagementBuckets;
        this.charts.engagement.update();
        
        // Update session duration chart
        const durationBuckets = [0, 0, 0, 0, 0]; // 0-2, 2-5, 5-10, 10-20, 20+
        userBehavior.forEach(user => {
            const duration = user.avg_session_duration / 60; // Convert to minutes
            if (duration <= 2) durationBuckets[0]++;
            else if (duration <= 5) durationBuckets[1]++;
            else if (duration <= 10) durationBuckets[2]++;
            else if (duration <= 20) durationBuckets[3]++;
            else durationBuckets[4]++;
        });
        
        this.charts.sessionDuration.data.datasets[0].data = durationBuckets;
        this.charts.sessionDuration.update();
        
        // Update user behavior table
        const container = document.getElementById('user-behavior-table');
        container.innerHTML = '';
        
        if (userBehavior.length === 0) {
            container.innerHTML = '<p>No user behavior data available.</p>';
            return;
        }
        
        const table = document.createElement('table');
        table.className = 'behavior-table';
        
        table.innerHTML = `
            <thead>
                <tr>
                    <th>User ID</th>
                    <th>Sessions</th>
                    <th>Avg Duration</th>
                    <th>Top Feature</th>
                    <th>Preferred Executive</th>
                    <th>Engagement</th>
                </tr>
            </thead>
            <tbody>
                ${userBehavior.slice(0, 10).map(user => {
                    const engagementClass = user.engagement_score > 60 ? 'high' :
                                          user.engagement_score > 30 ? 'medium' : 'low';
                    const topFeature = user.most_used_features.length > 0 ? 
                                     user.most_used_features[0].feature : 'None';
                    
                    return `
                        <tr>
                            <td>${user.user_id}</td>
                            <td>${user.total_sessions}</td>
                            <td>${(user.avg_session_duration / 60).toFixed(1)} min</td>
                            <td>${topFeature}</td>
                            <td>${user.preferred_executive.toUpperCase()}</td>
                            <td><span class="engagement-score ${engagementClass}">${user.engagement_score.toFixed(1)}</span></td>
                        </tr>
                    `;
                }).join('')}
            </tbody>
        `;
        
        container.appendChild(table);
    }
    
    async loadPerformanceIssues() {
        try {
            const response = await fetch(`/usage-analytics/api/performance-issues?days=${this.currentTimeRange}`);
            const result = await response.json();
            
            if (result.success) {
                this.updatePerformanceIssues(result.performance_issues);
            }
        } catch (error) {
            console.error('Error loading performance issues:', error);
        }
    }
    
    updatePerformanceIssues(performanceIssues) {
        const section = document.getElementById('performance-issues-section');
        const container = document.getElementById('performance-issues-container');
        
        if (performanceIssues.length === 0) {
            section.style.display = 'none';
            return;
        }
        
        section.style.display = 'block';
        container.innerHTML = '';
        
        performanceIssues.forEach(issue => {
            const item = document.createElement('div');
            item.className = `performance-issue-item ${issue.severity}`;
            
            item.innerHTML = `
                <div class="issue-header">
                    <span class="issue-type">${issue.issue_type.replace('_', ' ')}</span>
                    <span class="issue-severity ${issue.severity}">${issue.severity}</span>
                </div>
                <div class="issue-details">
                    Affected Feature: <strong>${issue.affected_feature}</strong>
                </div>
                <div class="issue-stats">
                    <span>Frequency: ${issue.frequency}</span>
                    <span>Avg Impact: ${issue.avg_impact_time.toFixed(2)}s</span>
                    <span>Affected Users: ${issue.affected_users}</span>
                    <span>Last Detected: ${new Date(issue.last_detected).toLocaleString()}</span>
                </div>
                <div class="issue-recommendation">
                    <strong>Recommendation:</strong> ${issue.recommendation}
                </div>
            `;
            
            container.appendChild(item);
        });
    }
    
    async loadOptimizationRecommendations() {
        try {
            const response = await fetch('/usage-analytics/api/optimization-recommendations');
            const result = await response.json();
            
            if (result.success) {
                this.updateOptimizationRecommendations(result.recommendations);
            }
        } catch (error) {
            console.error('Error loading optimization recommendations:', error);
        }
    }
    
    updateOptimizationRecommendations(recommendations) {
        const section = document.getElementById('recommendations-section');
        const container = document.getElementById('recommendations-container');
        
        if (recommendations.length === 0) {
            section.style.display = 'none';
            return;
        }
        
        section.style.display = 'block';
        this.allRecommendations = recommendations; // Store for filtering
        this.renderRecommendations(recommendations);
    }
    
    renderRecommendations(recommendations) {
        const container = document.getElementById('recommendations-container');
        container.innerHTML = '';
        
        recommendations.forEach(rec => {
            const item = document.createElement('div');
            item.className = `recommendation-item ${rec.priority}`;
            
            item.innerHTML = `
                <div class="recommendation-header">
                    <span class="recommendation-title">${rec.title}</span>
                    <span class="recommendation-priority ${rec.priority}">${rec.priority}</span>
                </div>
                <div class="recommendation-description">${rec.description}</div>
                <div class="recommendation-impact">Expected Impact: ${rec.expected_impact}</div>
                <div class="recommendation-effort">Implementation Effort: ${rec.implementation_effort}</div>
                <div class="recommendation-metrics">
                    ${rec.metrics_to_track.map(metric => 
                        `<span class="metric-tag">${metric}</span>`
                    ).join('')}
                </div>
            `;
            
            container.appendChild(item);
        });
    }
    
    filterRecommendations(priority) {
        if (!this.allRecommendations) return;
        
        let filteredRecommendations = this.allRecommendations;
        
        if (priority !== 'all') {
            filteredRecommendations = this.allRecommendations.filter(rec => rec.priority === priority);
        }
        
        this.renderRecommendations(filteredRecommendations);
    }
    
    showError(message) {
        console.error(message);
        // You could implement a proper notification system here
        alert(`Error: ${message}`);
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new UsageAnalyticsDashboard();
});