"""
Unit tests for Usage Analytics Service
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
from decimal import Decimal

from services.usage_analytics import (
    UsageAnalyticsService,
    UsageMetrics,
    UserActivity,
    FeatureUsage,
    PerformanceMetrics,
    UsageReport,
    UsageTrend
)
from tests.factories import UserFactory, DecisionFactory


class TestUsageAnalyticsService:
    """Test UsageAnalyticsService functionality"""
    
    @pytest.fixture
    def mock_config(self):
        return {
            'usage_analytics': {
                'retention_days': 90,
                'aggregation_intervals': ['hourly', 'daily', 'weekly', 'monthly'],
                'track_performance': True,
                'track_features': True
            }
        }
    
    @pytest.fixture
    def mock_db(self):
        db = Mock()
        
        # Mock query results
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = []
        mock_query.count.return_value = 0
        mock_query.first.return_value = None
        
        db.query.return_value = mock_query
        db.session = Mock()
        
        return db
    
    @pytest.fixture
    def service(self, mock_config, mock_db):
        return UsageAnalyticsService(mock_config, mock_db)
    
    def test_service_initialization(self, service, mock_config):
        assert service.config == mock_config
        assert service.retention_days == 90
        assert service.track_performance is True
        assert service.track_features is True
    
    def test_track_user_activity_success(self, service):
        activity = UserActivity(
            user_id='user123',
            action='decision_created',
            resource_type='decision',
            resource_id='dec123',
            timestamp=datetime.utcnow(),
            metadata={'executive_type': 'ceo'}
        )
        
        result = service.track_user_activity(activity)
        
        assert result is True
        service.db.session.add.assert_called_once()
        service.db.session.commit.assert_called_once()
    
    def test_track_user_activity_db_error(self, service):
        service.db.session.commit.side_effect = Exception("Database error")
        
        activity = UserActivity(
            user_id='user123',
            action='test_action',
            resource_type='test',
            resource_id='test123',
            timestamp=datetime.utcnow()
        )
        
        result = service.track_user_activity(activity)
        
        assert result is False
        service.db.session.rollback.assert_called_once()
    
    def test_track_feature_usage_success(self, service):
        feature_usage = FeatureUsage(
            user_id='user123',
            feature_name='ai_decision_generation',
            usage_count=1,
            timestamp=datetime.utcnow(),
            metadata={'executive_type': 'cfo', 'response_time': 2.5}
        )
        
        result = service.track_feature_usage(feature_usage)
        
        assert result is True
        service.db.session.add.assert_called_once()
        service.db.session.commit.assert_called_once()
    
    def test_track_performance_metrics_success(self, service):
        metrics = PerformanceMetrics(
            endpoint='/api/decisions',
            method='POST',
            response_time=1.5,
            status_code=200,
            timestamp=datetime.utcnow(),
            user_id='user123',
            metadata={'ai_model': 'gpt-4', 'tokens_used': 150}
        )
        
        result = service.track_performance_metrics(metrics)
        
        assert result is True
        service.db.session.add.assert_called_once()
        service.db.session.commit.assert_called_once()
    
    def test_get_user_activity_summary(self, service):
        # Mock database response
        mock_activities = [
            Mock(action='decision_created', timestamp=datetime.utcnow()),
            Mock(action='document_uploaded', timestamp=datetime.utcnow() - timedelta(hours=1)),
            Mock(action='decision_created', timestamp=datetime.utcnow() - timedelta(hours=2))
        ]
        
        service.db.query.return_value.filter.return_value.all.return_value = mock_activities
        
        summary = service.get_user_activity_summary('user123', days=7)
        
        assert isinstance(summary, dict)
        assert 'total_activities' in summary
        assert 'activities_by_action' in summary
        assert 'activities_by_day' in summary
        assert 'most_active_hours' in summary
        
        assert summary['total_activities'] == 3
        assert summary['activities_by_action']['decision_created'] == 2
        assert summary['activities_by_action']['document_uploaded'] == 1
    
    def test_get_feature_usage_stats(self, service):
        # Mock database response
        mock_usage = [
            Mock(feature_name='ai_decision_generation', usage_count=5, timestamp=datetime.utcnow()),
            Mock(feature_name='document_analysis', usage_count=3, timestamp=datetime.utcnow()),
            Mock(feature_name='ai_decision_generation', usage_count=2, timestamp=datetime.utcnow() - timedelta(days=1))
        ]
        
        service.db.query.return_value.filter.return_value.all.return_value = mock_usage
        
        stats = service.get_feature_usage_stats(days=30)
        
        assert isinstance(stats, dict)
        assert 'total_usage' in stats
        assert 'usage_by_feature' in stats
        assert 'usage_trends' in stats
        assert 'top_features' in stats
        
        assert stats['total_usage'] == 10  # 5 + 3 + 2
        assert stats['usage_by_feature']['ai_decision_generation'] == 7  # 5 + 2
        assert stats['usage_by_feature']['document_analysis'] == 3
    
    def test_get_performance_analytics(self, service):
        # Mock database response
        mock_metrics = [
            Mock(endpoint='/api/decisions', response_time=1.5, status_code=200),
            Mock(endpoint='/api/decisions', response_time=2.0, status_code=200),
            Mock(endpoint='/api/documents', response_time=0.8, status_code=200),
            Mock(endpoint='/api/decisions', response_time=3.0, status_code=500)
        ]
        
        service.db.query.return_value.filter.return_value.all.return_value = mock_metrics
        
        analytics = service.get_performance_analytics(days=7)
        
        assert isinstance(analytics, dict)
        assert 'average_response_time' in analytics
        assert 'response_times_by_endpoint' in analytics
        assert 'status_code_distribution' in analytics
        assert 'error_rate' in analytics
        assert 'slowest_endpoints' in analytics
        
        assert analytics['error_rate'] == 0.25  # 1 error out of 4 requests
        assert analytics['status_code_distribution'][200] == 3
        assert analytics['status_code_distribution'][500] == 1
    
    def test_generate_usage_report(self, service):
        # Mock various data sources
        service.get_user_activity_summary = Mock(return_value={
            'total_activities': 100,
            'activities_by_action': {'decision_created': 50, 'document_uploaded': 30}
        })
        
        service.get_feature_usage_stats = Mock(return_value={
            'total_usage': 200,
            'usage_by_feature': {'ai_decision_generation': 120, 'document_analysis': 80}
        })
        
        service.get_performance_analytics = Mock(return_value={
            'average_response_time': 1.8,
            'error_rate': 0.05
        })
        
        report = service.generate_usage_report(days=30)
        
        assert isinstance(report, UsageReport)
        assert report.period_days == 30
        assert report.total_users > 0
        assert report.total_activities == 100
        assert report.total_feature_usage == 200
        assert report.average_response_time == 1.8
        assert report.error_rate == 0.05
    
    def test_get_user_engagement_metrics(self, service):
        # Mock user activity data
        mock_users = [
            Mock(id='user1', created_at=datetime.utcnow() - timedelta(days=30)),
            Mock(id='user2', created_at=datetime.utcnow() - timedelta(days=60)),
            Mock(id='user3', created_at=datetime.utcnow() - timedelta(days=90))
        ]
        
        service.db.query.return_value.all.return_value = mock_users
        
        # Mock recent activity
        service.db.query.return_value.filter.return_value.distinct.return_value.count.return_value = 2
        
        metrics = service.get_user_engagement_metrics(days=30)
        
        assert isinstance(metrics, dict)
        assert 'total_users' in metrics
        assert 'active_users' in metrics
        assert 'engagement_rate' in metrics
        assert 'new_users' in metrics
        assert 'retention_rate' in metrics
        
        assert metrics['total_users'] == 3
        assert metrics['active_users'] == 2
        assert metrics['engagement_rate'] == 2/3  # 2 active out of 3 total
    
    def test_analyze_usage_trends(self, service):
        # Mock time series data
        mock_data = []
        for i in range(30):
            date = datetime.utcnow() - timedelta(days=i)
            mock_data.append(Mock(date=date.date(), count=10 + i))
        
        service.db.query.return_value.group_by.return_value.all.return_value = mock_data
        
        trends = service.analyze_usage_trends(metric='user_activity', days=30)
        
        assert isinstance(trends, UsageTrend)
        assert trends.metric == 'user_activity'
        assert trends.period_days == 30
        assert len(trends.data_points) == 30
        assert trends.trend_direction in ['increasing', 'decreasing', 'stable']
        assert 0 <= trends.trend_strength <= 1
    
    def test_get_top_users_by_activity(self, service):
        # Mock user activity aggregation
        mock_user_stats = [
            Mock(user_id='user1', activity_count=50, last_activity=datetime.utcnow()),
            Mock(user_id='user2', activity_count=35, last_activity=datetime.utcnow() - timedelta(hours=2)),
            Mock(user_id='user3', activity_count=20, last_activity=datetime.utcnow() - timedelta(days=1))
        ]
        
        service.db.query.return_value.group_by.return_value.order_by.return_value.limit.return_value.all.return_value = mock_user_stats
        
        top_users = service.get_top_users_by_activity(limit=10, days=30)
        
        assert isinstance(top_users, list)
        assert len(top_users) == 3
        
        for user_stat in top_users:
            assert 'user_id' in user_stat
            assert 'activity_count' in user_stat
            assert 'last_activity' in user_stat
        
        # Should be ordered by activity count (descending)
        assert top_users[0]['activity_count'] >= top_users[1]['activity_count']
        assert top_users[1]['activity_count'] >= top_users[2]['activity_count']
    
    def test_get_feature_adoption_rate(self, service):
        # Mock total users
        service.db.query.return_value.count.return_value = 100
        
        # Mock users who used specific feature
        service.db.query.return_value.filter.return_value.distinct.return_value.count.return_value = 75
        
        adoption_rate = service.get_feature_adoption_rate('ai_decision_generation', days=30)
        
        assert adoption_rate == 0.75  # 75 out of 100 users
    
    def test_get_feature_adoption_rate_no_users(self, service):
        service.db.query.return_value.count.return_value = 0
        
        adoption_rate = service.get_feature_adoption_rate('ai_decision_generation', days=30)
        
        assert adoption_rate == 0.0
    
    def test_cleanup_old_data(self, service):
        # Mock deletion
        service.db.query.return_value.filter.return_value.delete.return_value = 50
        
        deleted_count = service.cleanup_old_data()
        
        assert deleted_count > 0
        service.db.session.commit.assert_called()
    
    def test_export_usage_data(self, service):
        # Mock data for export
        mock_activities = [
            Mock(user_id='user1', action='decision_created', timestamp=datetime.utcnow()),
            Mock(user_id='user2', action='document_uploaded', timestamp=datetime.utcnow())
        ]
        
        service.db.query.return_value.filter.return_value.all.return_value = mock_activities
        
        export_data = service.export_usage_data(days=30, format='json')
        
        assert isinstance(export_data, dict)
        assert 'activities' in export_data
        assert 'feature_usage' in export_data
        assert 'performance_metrics' in export_data
        assert 'metadata' in export_data
        
        assert export_data['metadata']['export_date'] is not None
        assert export_data['metadata']['period_days'] == 30
    
    def test_get_real_time_metrics(self, service):
        # Mock current metrics
        service.db.query.return_value.filter.return_value.count.return_value = 5
        
        metrics = service.get_real_time_metrics()
        
        assert isinstance(metrics, dict)
        assert 'active_users_last_hour' in metrics
        assert 'requests_last_hour' in metrics
        assert 'errors_last_hour' in metrics
        assert 'average_response_time_last_hour' in metrics
        assert 'timestamp' in metrics
    
    def test_calculate_user_lifetime_value(self, service):
        # Mock user data
        user_data = {
            'total_decisions': 50,
            'total_documents': 20,
            'subscription_months': 12,
            'feature_usage_score': 0.8
        }
        
        ltv = service.calculate_user_lifetime_value('user123', user_data)
        
        assert isinstance(ltv, dict)
        assert 'estimated_ltv' in ltv
        assert 'engagement_score' in ltv
        assert 'usage_score' in ltv
        assert 'retention_probability' in ltv
        
        assert ltv['estimated_ltv'] > 0
        assert 0 <= ltv['engagement_score'] <= 1
        assert 0 <= ltv['retention_probability'] <= 1


class TestUsageMetrics:
    """Test UsageMetrics data class"""
    
    def test_usage_metrics_creation(self):
        metrics = UsageMetrics(
            total_users=100,
            active_users=75,
            total_sessions=500,
            average_session_duration=15.5,
            page_views=2000,
            unique_page_views=1500
        )
        
        assert metrics.total_users == 100
        assert metrics.active_users == 75
        assert metrics.total_sessions == 500
        assert metrics.average_session_duration == 15.5
        assert metrics.page_views == 2000
        assert metrics.unique_page_views == 1500
    
    def test_usage_metrics_engagement_rate(self):
        metrics = UsageMetrics(
            total_users=100,
            active_users=80,
            total_sessions=400,
            average_session_duration=12.0,
            page_views=1600,
            unique_page_views=1200
        )
        
        engagement_rate = metrics.engagement_rate
        assert engagement_rate == 0.8  # 80/100


class TestUserActivity:
    """Test UserActivity data class"""
    
    def test_user_activity_creation(self):
        activity = UserActivity(
            user_id='user123',
            action='decision_created',
            resource_type='decision',
            resource_id='dec123',
            timestamp=datetime.utcnow(),
            metadata={'executive_type': 'ceo'}
        )
        
        assert activity.user_id == 'user123'
        assert activity.action == 'decision_created'
        assert activity.resource_type == 'decision'
        assert activity.resource_id == 'dec123'
        assert isinstance(activity.timestamp, datetime)
        assert activity.metadata == {'executive_type': 'ceo'}


class TestFeatureUsage:
    """Test FeatureUsage data class"""
    
    def test_feature_usage_creation(self):
        usage = FeatureUsage(
            user_id='user123',
            feature_name='ai_decision_generation',
            usage_count=5,
            timestamp=datetime.utcnow(),
            metadata={'response_time': 2.5}
        )
        
        assert usage.user_id == 'user123'
        assert usage.feature_name == 'ai_decision_generation'
        assert usage.usage_count == 5
        assert isinstance(usage.timestamp, datetime)
        assert usage.metadata == {'response_time': 2.5}


class TestPerformanceMetrics:
    """Test PerformanceMetrics data class"""
    
    def test_performance_metrics_creation(self):
        metrics = PerformanceMetrics(
            endpoint='/api/decisions',
            method='POST',
            response_time=1.5,
            status_code=200,
            timestamp=datetime.utcnow(),
            user_id='user123',
            metadata={'tokens_used': 150}
        )
        
        assert metrics.endpoint == '/api/decisions'
        assert metrics.method == 'POST'
        assert metrics.response_time == 1.5
        assert metrics.status_code == 200
        assert isinstance(metrics.timestamp, datetime)
        assert metrics.user_id == 'user123'
        assert metrics.metadata == {'tokens_used': 150}


class TestUsageReport:
    """Test UsageReport data class"""
    
    def test_usage_report_creation(self):
        report = UsageReport(
            period_start=datetime.utcnow() - timedelta(days=30),
            period_end=datetime.utcnow(),
            period_days=30,
            total_users=100,
            active_users=75,
            total_activities=500,
            total_feature_usage=1000,
            average_response_time=1.8,
            error_rate=0.05,
            top_features=['ai_decision_generation', 'document_analysis'],
            user_engagement_metrics={'engagement_rate': 0.75}
        )
        
        assert isinstance(report.period_start, datetime)
        assert isinstance(report.period_end, datetime)
        assert report.period_days == 30
        assert report.total_users == 100
        assert report.active_users == 75
        assert report.total_activities == 500
        assert report.total_feature_usage == 1000
        assert report.average_response_time == 1.8
        assert report.error_rate == 0.05
        assert report.top_features == ['ai_decision_generation', 'document_analysis']
        assert report.user_engagement_metrics == {'engagement_rate': 0.75}


class TestUsageTrend:
    """Test UsageTrend data class"""
    
    def test_usage_trend_creation(self):
        data_points = [
            {'date': '2023-01-01', 'value': 10},
            {'date': '2023-01-02', 'value': 12},
            {'date': '2023-01-03', 'value': 15}
        ]
        
        trend = UsageTrend(
            metric='user_activity',
            period_days=30,
            data_points=data_points,
            trend_direction='increasing',
            trend_strength=0.8,
            statistical_significance=0.95
        )
        
        assert trend.metric == 'user_activity'
        assert trend.period_days == 30
        assert trend.data_points == data_points
        assert trend.trend_direction == 'increasing'
        assert trend.trend_strength == 0.8
        assert trend.statistical_significance == 0.95


if __name__ == "__main__":
    pytest.main([__file__])