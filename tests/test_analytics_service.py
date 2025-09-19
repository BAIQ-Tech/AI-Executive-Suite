"""
Tests for Analytics Service

Tests the analytics service functionality including data aggregation,
trend analysis, and performance metrics calculation.
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import Mock, MagicMock
import statistics

from services.analytics import (
    AnalyticsService, DateRange, AnalyticsFilters, TimeSeriesPoint, 
    TrendData, DecisionAnalytics, FinancialMetrics, DashboardData
)


class TestAnalyticsService:
    """Test cases for AnalyticsService"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.config = {
            'analytics': {
                'default_interval_days': 7,
                'trend_confidence_threshold': 0.7
            }
        }
        self.mock_db = Mock()
        self.service = AnalyticsService(self.config, self.mock_db)
    
    def test_init(self):
        """Test service initialization"""
        assert self.service.config == self.config
        assert self.service.db == self.mock_db
        assert self.service.logger is not None
    
    def test_init_without_db(self):
        """Test service initialization without database"""
        service = AnalyticsService(self.config)
        assert service.db is None
    
    def test_calculate_trend_data_increasing(self):
        """Test trend calculation for increasing data"""
        time_series = [
            TimeSeriesPoint(datetime.now(), 10.0),
            TimeSeriesPoint(datetime.now(), 15.0),
            TimeSeriesPoint(datetime.now(), 20.0),
            TimeSeriesPoint(datetime.now(), 25.0)
        ]
        
        trend = self.service._calculate_trend_data(time_series)
        
        assert trend.direction == 'increasing'
        assert trend.rate > 0
        assert 0 <= trend.confidence <= 1
    
    def test_calculate_trend_data_decreasing(self):
        """Test trend calculation for decreasing data"""
        time_series = [
            TimeSeriesPoint(datetime.now(), 25.0),
            TimeSeriesPoint(datetime.now(), 20.0),
            TimeSeriesPoint(datetime.now(), 15.0),
            TimeSeriesPoint(datetime.now(), 10.0)
        ]
        
        trend = self.service._calculate_trend_data(time_series)
        
        assert trend.direction == 'decreasing'
        assert trend.rate > 0
        assert 0 <= trend.confidence <= 1
    
    def test_calculate_trend_data_stable(self):
        """Test trend calculation for stable data"""
        time_series = [
            TimeSeriesPoint(datetime.now(), 20.0),
            TimeSeriesPoint(datetime.now(), 20.1),
            TimeSeriesPoint(datetime.now(), 19.9),
            TimeSeriesPoint(datetime.now(), 20.0)
        ]
        
        trend = self.service._calculate_trend_data(time_series)
        
        assert trend.direction == 'stable'
        assert trend.rate < 0.1
    
    def test_calculate_trend_data_empty(self):
        """Test trend calculation with empty data"""
        trend = self.service._calculate_trend_data([])
        
        assert trend.direction == 'stable'
        assert trend.rate == 0.0
        assert trend.confidence == 0.0
    
    def test_calculate_trend_data_single_point(self):
        """Test trend calculation with single data point"""
        time_series = [TimeSeriesPoint(datetime.now(), 10.0)]
        
        trend = self.service._calculate_trend_data(time_series)
        
        assert trend.direction == 'stable'
        assert trend.rate == 0.0
        assert trend.confidence == 0.0
    
    def test_generate_time_series(self):
        """Test time series generation from decisions"""
        # Mock decisions with different timestamps
        now = datetime.utcnow()
        decisions = []
        
        # Create decisions over 21 days
        for i in range(21):
            decision = Mock()
            decision.created_at = now - timedelta(days=20-i)
            decisions.append(decision)
        
        time_range = DateRange(now - timedelta(days=21), now)
        time_series = self.service._generate_time_series(decisions, time_range, interval_days=7)
        
        # Should have 4 intervals (0-7, 7-14, 14-21, 21+)
        assert len(time_series) >= 3
        
        # Check that values are reasonable
        for point in time_series:
            assert isinstance(point.value, float)
            assert point.value >= 0
    
    def test_generate_decision_analytics_no_db(self):
        """Test analytics generation without database"""
        service = AnalyticsService(self.config, None)
        time_range = DateRange(datetime.now() - timedelta(days=30), datetime.now())
        
        analytics = service.generate_decision_analytics(time_range)
        
        assert isinstance(analytics, DecisionAnalytics)
        assert analytics.total_decisions > 0  # Mock data
        assert isinstance(analytics.decisions_by_executive, dict)
        assert isinstance(analytics.average_confidence_score, float)
    
    def test_generate_decision_analytics_with_empty_data(self):
        """Test analytics generation with no decisions"""
        # Mock empty query result
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []
        self.mock_db.query.return_value = mock_query
        
        time_range = DateRange(datetime.now() - timedelta(days=30), datetime.now())
        analytics = self.service.generate_decision_analytics(time_range)
        
        assert analytics.total_decisions == 0
        assert analytics.decisions_by_executive == {}
        assert analytics.average_confidence_score == 0.0
        assert analytics.implementation_rate == 0.0
    
    def test_generate_decision_analytics_with_data(self):
        """Test analytics generation with mock decision data"""
        # Create mock decisions
        mock_decisions = []
        for i in range(10):
            decision = Mock()
            decision.executive_type = Mock()
            decision.executive_type.value = ['ceo', 'cto', 'cfo'][i % 3]
            decision.category = ['strategic', 'technical', 'financial'][i % 3]
            decision.priority = Mock()
            decision.priority.value = ['high', 'medium', 'low'][i % 3]
            decision.status = Mock()
            decision.status.value = 'completed' if i < 7 else 'pending'
            decision.confidence_score = 0.8 + (i % 3) * 0.1
            decision.effectiveness_score = 0.7 + (i % 4) * 0.1
            decision.financial_impact = Decimal(str(1000 * (i + 1)))
            decision.created_at = datetime.now() - timedelta(days=i)
            decision.implemented_at = datetime.now() - timedelta(days=i//2) if i < 7 else None
            mock_decisions.append(decision)
        
        # Mock database query
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = mock_decisions
        self.mock_db.query.return_value = mock_query
        
        time_range = DateRange(datetime.now() - timedelta(days=30), datetime.now())
        analytics = self.service.generate_decision_analytics(time_range)
        
        assert analytics.total_decisions == 10
        assert len(analytics.decisions_by_executive) == 3
        assert 'ceo' in analytics.decisions_by_executive
        assert 'cto' in analytics.decisions_by_executive
        assert 'cfo' in analytics.decisions_by_executive
        assert analytics.implementation_rate == 0.7  # 7 out of 10 completed
        assert analytics.average_confidence_score > 0.8
        assert analytics.total_financial_impact > 0
    
    def test_calculate_decision_effectiveness_metrics(self):
        """Test decision effectiveness metrics calculation"""
        # Create mock decisions with various effectiveness scores
        decisions = []
        for i in range(5):
            decision = Mock()
            decision.effectiveness_score = 0.6 + i * 0.1
            decision.outcome_rating = 3 + i % 3  # Ratings 3, 4, 5, 3, 4
            decision.created_at = datetime.now() - timedelta(days=10)
            decision.implemented_at = datetime.now() - timedelta(days=5) if i < 3 else None
            decisions.append(decision)
        
        metrics = self.service.calculate_decision_effectiveness_metrics(decisions)
        
        assert 'average_effectiveness' in metrics
        assert 'success_rate' in metrics
        assert 'implementation_rate' in metrics
        assert metrics['average_effectiveness'] == 0.8  # Mean of 0.6, 0.7, 0.8, 0.9, 1.0
        assert metrics['success_rate'] == 0.6  # 3 out of 5 have rating >= 4
        assert metrics['implementation_rate'] == 0.6  # 3 out of 5 implemented
    
    def test_calculate_decision_effectiveness_metrics_empty(self):
        """Test effectiveness metrics with empty decision list"""
        metrics = self.service.calculate_decision_effectiveness_metrics([])
        assert metrics == {}
    
    def test_calculate_financial_metrics(self):
        """Test financial metrics calculation"""
        financial_data = {
            'revenue': {
                'total_revenue': 1000000,
                'recurring_revenue': 800000
            },
            'costs': {
                'total_costs': 600000,
                'operating_costs': 500000
            },
            'assets': {
                'total_assets': 2000000
            },
            'previous_revenue': 900000
        }
        
        metrics = self.service.calculate_financial_metrics(financial_data)
        
        assert isinstance(metrics, FinancialMetrics)
        assert metrics.revenue_metrics['total_revenue'] == Decimal('1000000')
        assert metrics.cost_metrics['total_costs'] == Decimal('600000')
        assert metrics.profitability_metrics['gross_profit'] == Decimal('400000')
        assert metrics.efficiency_ratios['asset_turnover'] == 0.5
        assert abs(metrics.growth_rates['revenue_growth'] - 0.1111) < 0.01  # (1M - 900K) / 900K
    
    def test_calculate_financial_metrics_minimal_data(self):
        """Test financial metrics with minimal data"""
        financial_data = {
            'revenue': {'total_revenue': 100000}
        }
        
        metrics = self.service.calculate_financial_metrics(financial_data)
        
        assert isinstance(metrics, FinancialMetrics)
        assert metrics.revenue_metrics['total_revenue'] == Decimal('100000')
        assert len(metrics.cost_metrics) == 0
        assert len(metrics.profitability_metrics) == 0
    
    def test_calculate_financial_metrics_error_handling(self):
        """Test financial metrics error handling"""
        # Invalid data that should cause an error
        financial_data = {
            'revenue': {
                'total_revenue': 'invalid_number'
            }
        }
        
        metrics = self.service.calculate_financial_metrics(financial_data)
        
        # Should return default metrics without crashing
        assert isinstance(metrics, FinancialMetrics)
        assert metrics.revenue_metrics['total_revenue'] == Decimal('0')
    
    def test_get_performance_dashboard_no_db(self):
        """Test dashboard generation without database"""
        service = AnalyticsService(self.config, None)
        
        dashboard = service.get_performance_dashboard("user123")
        
        assert isinstance(dashboard, DashboardData)
        assert 'total_decisions' in dashboard.key_metrics
        assert len(dashboard.charts) > 0
        assert len(dashboard.recommendations) > 0
    
    def test_get_performance_dashboard_with_data(self):
        """Test dashboard generation with user data"""
        # Create mock user decisions
        mock_decisions = []
        for i in range(8):
            decision = Mock()
            decision.outcome_rating = 4 if i < 6 else 3  # 6 successful, 2 not
            decision.confidence_score = 0.7 + i * 0.05
            decision.executive_type = Mock()
            decision.executive_type.value = ['ceo', 'cto', 'cfo'][i % 3]
            decision.created_at = datetime.now() - timedelta(days=i*3)
            decision.implemented_at = datetime.now() - timedelta(days=i) if i < 5 else None
            mock_decisions.append(decision)
        
        # Mock database query
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = mock_decisions
        self.mock_db.query.return_value = mock_query
        
        dashboard = self.service.get_performance_dashboard("user123")
        
        assert dashboard.key_metrics['total_decisions'] == 8
        assert dashboard.key_metrics['success_rate'] == 0.75  # 6 out of 8
        assert dashboard.key_metrics['implementation_rate'] == 0.625  # 5 out of 8
        assert len(dashboard.charts) == 2  # Line chart and pie chart
        assert dashboard.charts[0]['type'] == 'line'
        assert dashboard.charts[1]['type'] == 'pie'
    
    def test_get_performance_dashboard_with_alerts(self):
        """Test dashboard generation with performance alerts"""
        # Create mock decisions with poor performance
        mock_decisions = []
        for i in range(5):
            decision = Mock()
            decision.outcome_rating = 2  # Poor ratings
            decision.confidence_score = 0.4  # Low confidence
            decision.executive_type = Mock()
            decision.executive_type.value = 'ceo'
            decision.created_at = datetime.now() - timedelta(days=i)
            decision.implemented_at = None  # Not implemented
            mock_decisions.append(decision)
        
        # Mock database query
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = mock_decisions
        self.mock_db.query.return_value = mock_query
        
        dashboard = self.service.get_performance_dashboard("user123")
        
        # Should generate alerts for poor performance
        assert len(dashboard.alerts) > 0
        alert_messages = [alert['message'] for alert in dashboard.alerts]
        assert any('success rate' in msg.lower() for msg in alert_messages)
        assert any('confidence' in msg.lower() for msg in alert_messages)
    
    def test_filters_application(self):
        """Test that analytics filters are properly applied"""
        filters = AnalyticsFilters(
            executive_types=['ceo', 'cto'],
            categories=['strategic'],
            priorities=['high'],
            status=['completed']
        )
        
        # Mock the query building
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []
        self.mock_db.query.return_value = mock_query
        
        time_range = DateRange(datetime.now() - timedelta(days=30), datetime.now())
        
        # This should not raise an error and should call filter multiple times
        analytics = self.service.generate_decision_analytics(time_range, filters)
        
        # Verify that filters were applied (query.filter called multiple times)
        assert mock_query.filter.call_count >= 4  # Time range + 4 filter criteria


class TestAnalyticsDataClasses:
    """Test analytics data classes"""
    
    def test_date_range(self):
        """Test DateRange data class"""
        start = datetime.now()
        end = start + timedelta(days=30)
        date_range = DateRange(start, end)
        
        assert date_range.start_date == start
        assert date_range.end_date == end
    
    def test_analytics_filters(self):
        """Test AnalyticsFilters data class"""
        filters = AnalyticsFilters(
            executive_types=['ceo'],
            categories=['strategic'],
            priorities=['high'],
            status=['completed']
        )
        
        assert filters.executive_types == ['ceo']
        assert filters.categories == ['strategic']
        assert filters.priorities == ['high']
        assert filters.status == ['completed']
    
    def test_analytics_filters_defaults(self):
        """Test AnalyticsFilters with default values"""
        filters = AnalyticsFilters()
        
        assert filters.executive_types is None
        assert filters.categories is None
        assert filters.priorities is None
        assert filters.status is None
    
    def test_time_series_point(self):
        """Test TimeSeriesPoint data class"""
        timestamp = datetime.now()
        point = TimeSeriesPoint(timestamp, 42.5, {'test': 'metadata'})
        
        assert point.timestamp == timestamp
        assert point.value == 42.5
        assert point.metadata == {'test': 'metadata'}
    
    def test_trend_data(self):
        """Test TrendData data class"""
        trend = TrendData('increasing', 0.15, 0.85)
        
        assert trend.direction == 'increasing'
        assert trend.rate == 0.15
        assert trend.confidence == 0.85
    
    def test_decision_analytics(self):
        """Test DecisionAnalytics data class"""
        analytics = DecisionAnalytics(
            total_decisions=100,
            decisions_by_executive={'ceo': 50, 'cto': 30, 'cfo': 20},
            decisions_by_category={'strategic': 40, 'technical': 35, 'financial': 25},
            decisions_by_priority={'high': 30, 'medium': 50, 'low': 20},
            average_confidence_score=0.82,
            implementation_rate=0.75,
            effectiveness_scores={'ceo': 0.85, 'cto': 0.80, 'cfo': 0.88},
            decisions_over_time=[],
            trends={},
            total_financial_impact=Decimal('1000000'),
            roi_by_category={},
            cost_savings=Decimal('250000')
        )
        
        assert analytics.total_decisions == 100
        assert analytics.decisions_by_executive['ceo'] == 50
        assert analytics.average_confidence_score == 0.82
        assert analytics.total_financial_impact == Decimal('1000000')


if __name__ == '__main__':
    pytest.main([__file__])