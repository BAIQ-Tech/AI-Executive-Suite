"""
Tests for the monitoring system.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import time
from datetime import datetime, timedelta
import threading

from services.monitoring import (
    MonitoringService, MetricsCollector, HealthChecker, AlertManager,
    SystemMetrics, HealthCheck, Alert
)

class TestMetricsCollector(unittest.TestCase):
    """Test the MetricsCollector class."""
    
    def setUp(self):
        self.collector = MetricsCollector()
    
    def test_record_request(self):
        """Test recording request metrics."""
        # Record some requests
        self.collector.record_request(0.5, False)
        self.collector.record_request(1.0, True)
        self.collector.record_request(0.3, False)
        
        self.assertEqual(len(self.collector.request_times), 3)
        self.assertEqual(self.collector.request_count, 3)
        self.assertEqual(self.collector.error_count, 1)
    
    def test_record_ai_api_call(self):
        """Test recording AI API call metrics."""
        self.collector.record_ai_api_call(2.5)
        self.collector.record_ai_api_call(1.8)
        
        self.assertEqual(len(self.collector.ai_api_times), 2)
        self.assertIn(2.5, self.collector.ai_api_times)
        self.assertIn(1.8, self.collector.ai_api_times)
    
    def test_record_db_query(self):
        """Test recording database query metrics."""
        self.collector.record_db_query(0.1)
        self.collector.record_db_query(0.05)
        
        self.assertEqual(len(self.collector.db_query_times), 2)
        self.assertIn(0.1, self.collector.db_query_times)
        self.assertIn(0.05, self.collector.db_query_times)
    
    @patch('psutil.cpu_percent')
    @patch('psutil.virtual_memory')
    @patch('psutil.disk_usage')
    @patch('psutil.net_connections')
    def test_get_current_metrics(self, mock_connections, mock_disk, mock_memory, mock_cpu):
        """Test getting current system metrics."""
        # Mock system metrics
        mock_cpu.return_value = 45.5
        mock_memory.return_value = Mock(percent=60.2)
        mock_disk.return_value = Mock(percent=75.8)
        mock_connections.return_value = [Mock()] * 10  # 10 connections
        
        # Add some request data
        self.collector.record_request(0.5, False)
        self.collector.record_request(1.0, True)
        self.collector.record_ai_api_call(2.0)
        self.collector.record_db_query(0.1)
        
        metrics = self.collector.get_current_metrics()
        
        self.assertIsInstance(metrics, SystemMetrics)
        self.assertEqual(metrics.cpu_percent, 45.5)
        self.assertEqual(metrics.memory_percent, 60.2)
        self.assertEqual(metrics.disk_usage_percent, 75.8)
        self.assertEqual(metrics.active_connections, 10)
        self.assertEqual(metrics.response_time_avg, 0.75)  # (0.5 + 1.0) / 2
        self.assertEqual(metrics.error_rate, 50.0)  # 1 error out of 2 requests
        self.assertEqual(metrics.ai_api_latency, 2.0)
        self.assertEqual(metrics.database_query_time, 0.1)

class TestHealthChecker(unittest.TestCase):
    """Test the HealthChecker class."""
    
    def setUp(self):
        self.health_checker = HealthChecker()
    
    @patch('models.db')
    @patch('services.monitoring.current_app')
    def test_check_database_health_success(self, mock_app, mock_db):
        """Test successful database health check."""
        mock_app.app_context.return_value.__enter__.return_value = None
        mock_db.session.execute.return_value = None
        
        health_check = self.health_checker.check_database_health()
        
        self.assertIsInstance(health_check, HealthCheck)
        self.assertEqual(health_check.service, 'database')
        self.assertEqual(health_check.status, 'healthy')
        self.assertIsNotNone(health_check.response_time)
    
    @patch('models.db')
    @patch('services.monitoring.current_app')
    def test_check_database_health_failure(self, mock_app, mock_db):
        """Test failed database health check."""
        mock_app.app_context.return_value.__enter__.return_value = None
        mock_db.session.execute.side_effect = Exception("Connection failed")
        
        health_check = self.health_checker.check_database_health()
        
        self.assertEqual(health_check.service, 'database')
        self.assertEqual(health_check.status, 'critical')
        self.assertIn('Connection failed', health_check.message)
    
    @patch('psutil.disk_usage')
    def test_check_disk_space(self, mock_disk_usage):
        """Test disk space health check."""
        # Test normal usage
        mock_disk_usage.return_value = Mock(percent=70.0)
        health_check = self.health_checker.check_disk_space()
        self.assertEqual(health_check.status, 'healthy')
        
        # Test high usage
        mock_disk_usage.return_value = Mock(percent=85.0)
        health_check = self.health_checker.check_disk_space()
        self.assertEqual(health_check.status, 'warning')
        
        # Test critical usage
        mock_disk_usage.return_value = Mock(percent=95.0)
        health_check = self.health_checker.check_disk_space()
        self.assertEqual(health_check.status, 'critical')
    
    @patch('psutil.virtual_memory')
    def test_check_memory_usage(self, mock_memory):
        """Test memory usage health check."""
        # Test normal usage
        mock_memory.return_value = Mock(percent=70.0)
        health_check = self.health_checker.check_memory_usage()
        self.assertEqual(health_check.status, 'healthy')
        
        # Test high usage
        mock_memory.return_value = Mock(percent=85.0)
        health_check = self.health_checker.check_memory_usage()
        self.assertEqual(health_check.status, 'warning')
        
        # Test critical usage
        mock_memory.return_value = Mock(percent=95.0)
        health_check = self.health_checker.check_memory_usage()
        self.assertEqual(health_check.status, 'critical')

class TestAlertManager(unittest.TestCase):
    """Test the AlertManager class."""
    
    def setUp(self):
        self.alert_manager = AlertManager()
    
    def test_check_metrics_for_alerts_cpu(self):
        """Test CPU usage alert generation."""
        metrics = SystemMetrics(
            timestamp=datetime.now(),
            cpu_percent=85.0,  # Above threshold
            memory_percent=50.0,
            disk_usage_percent=50.0,
            active_connections=10,
            response_time_avg=1.0,
            requests_per_minute=100,
            error_rate=2.0,
            ai_api_latency=5.0,
            database_query_time=0.1
        )
        
        alerts = self.alert_manager.check_metrics_for_alerts(metrics)
        
        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0].type, 'performance')
        self.assertIn('CPU usage', alerts[0].message)
    
    def test_check_metrics_for_alerts_multiple(self):
        """Test multiple alert generation."""
        metrics = SystemMetrics(
            timestamp=datetime.now(),
            cpu_percent=85.0,  # Above threshold
            memory_percent=90.0,  # Above threshold
            disk_usage_percent=95.0,  # Above threshold
            active_connections=10,
            response_time_avg=3.0,  # Above threshold
            requests_per_minute=100,
            error_rate=10.0,  # Above threshold
            ai_api_latency=15.0,  # Above threshold
            database_query_time=0.1
        )
        
        alerts = self.alert_manager.check_metrics_for_alerts(metrics)
        
        self.assertEqual(len(alerts), 6)  # All thresholds exceeded
        alert_types = [alert.type for alert in alerts]
        self.assertIn('performance', alert_types)
        self.assertIn('error', alert_types)
    
    def test_resolve_alert(self):
        """Test alert resolution."""
        # Create an alert
        alert = Alert(
            id='test_alert_1',
            type='performance',
            severity='medium',
            message='Test alert',
            timestamp=datetime.now()
        )
        self.alert_manager.alerts.append(alert)
        
        # Resolve the alert
        success = self.alert_manager.resolve_alert('test_alert_1')
        
        self.assertTrue(success)
        self.assertTrue(alert.resolved)
        self.assertIsNotNone(alert.resolved_at)
    
    def test_get_active_alerts(self):
        """Test getting active alerts."""
        # Create alerts
        alert1 = Alert(
            id='alert_1',
            type='performance',
            severity='medium',
            message='Alert 1',
            timestamp=datetime.now()
        )
        alert2 = Alert(
            id='alert_2',
            type='error',
            severity='high',
            message='Alert 2',
            timestamp=datetime.now(),
            resolved=True
        )
        
        self.alert_manager.alerts.extend([alert1, alert2])
        
        active_alerts = self.alert_manager.get_active_alerts()
        
        self.assertEqual(len(active_alerts), 1)
        self.assertEqual(active_alerts[0].id, 'alert_1')

class TestMonitoringService(unittest.TestCase):
    """Test the MonitoringService class."""
    
    def setUp(self):
        self.monitoring_service = MonitoringService()
    
    def test_start_stop_monitoring(self):
        """Test starting and stopping monitoring."""
        self.assertFalse(self.monitoring_service._monitoring_active)
        
        self.monitoring_service.start_monitoring(interval=1)
        self.assertTrue(self.monitoring_service._monitoring_active)
        self.assertIsNotNone(self.monitoring_service._monitoring_thread)
        
        # Give it a moment to start
        time.sleep(0.1)
        
        self.monitoring_service.stop_monitoring()
        self.assertFalse(self.monitoring_service._monitoring_active)
    
    def test_record_request(self):
        """Test recording request metrics."""
        self.monitoring_service.record_request(0.5, False)
        
        # Check that the metrics collector received the data
        self.assertEqual(len(self.monitoring_service.metrics_collector.request_times), 1)
        self.assertEqual(self.monitoring_service.metrics_collector.request_count, 1)
        self.assertEqual(self.monitoring_service.metrics_collector.error_count, 0)
    
    def test_record_ai_api_call(self):
        """Test recording AI API call metrics."""
        self.monitoring_service.record_ai_api_call(2.0)
        
        # Check that the metrics collector received the data
        self.assertEqual(len(self.monitoring_service.metrics_collector.ai_api_times), 1)
        self.assertIn(2.0, self.monitoring_service.metrics_collector.ai_api_times)
    
    def test_record_db_query(self):
        """Test recording database query metrics."""
        self.monitoring_service.record_db_query(0.1)
        
        # Check that the metrics collector received the data
        self.assertEqual(len(self.monitoring_service.metrics_collector.db_query_times), 1)
        self.assertIn(0.1, self.monitoring_service.metrics_collector.db_query_times)
    
    @patch('services.monitoring.MonitoringService._get_overall_system_status')
    def test_get_dashboard_data(self, mock_status):
        """Test getting dashboard data."""
        mock_status.return_value = 'healthy'
        
        # Add some test data
        self.monitoring_service.record_request(0.5, False)
        
        dashboard_data = self.monitoring_service.get_dashboard_data()
        
        self.assertIn('current_metrics', dashboard_data)
        self.assertIn('health_checks', dashboard_data)
        self.assertIn('active_alerts', dashboard_data)
        self.assertIn('historical_metrics', dashboard_data)
        self.assertIn('system_status', dashboard_data)
        self.assertEqual(dashboard_data['system_status'], 'healthy')
    
    def test_get_overall_system_status_healthy(self):
        """Test overall system status calculation - healthy."""
        health_checks = [
            HealthCheck('service1', 'healthy', 'OK', datetime.now()),
            HealthCheck('service2', 'healthy', 'OK', datetime.now())
        ]
        alerts = []
        
        status = self.monitoring_service._get_overall_system_status(health_checks, alerts)
        self.assertEqual(status, 'healthy')
    
    def test_get_overall_system_status_warning(self):
        """Test overall system status calculation - warning."""
        health_checks = [
            HealthCheck('service1', 'healthy', 'OK', datetime.now()),
            HealthCheck('service2', 'warning', 'High usage', datetime.now())
        ]
        alerts = []
        
        status = self.monitoring_service._get_overall_system_status(health_checks, alerts)
        self.assertEqual(status, 'warning')
    
    def test_get_overall_system_status_critical(self):
        """Test overall system status calculation - critical."""
        health_checks = [
            HealthCheck('service1', 'critical', 'Failed', datetime.now())
        ]
        alerts = []
        
        status = self.monitoring_service._get_overall_system_status(health_checks, alerts)
        self.assertEqual(status, 'critical')

class TestRequestMonitoring(unittest.TestCase):
    """Test request monitoring middleware."""
    
    def setUp(self):
        from utils.request_monitoring import RequestMonitoringMiddleware
        self.middleware = RequestMonitoringMiddleware()
    
    @patch('utils.request_monitoring.monitoring_service')
    def test_monitor_ai_api_call_decorator(self, mock_monitoring):
        """Test AI API call monitoring decorator."""
        from utils.request_monitoring import monitor_ai_api_call
        
        @monitor_ai_api_call
        def mock_ai_call():
            time.sleep(0.1)  # Simulate API call
            return "response"
        
        result = mock_ai_call()
        
        self.assertEqual(result, "response")
        mock_monitoring.record_ai_api_call.assert_called_once()
        
        # Check that response time was recorded
        call_args = mock_monitoring.record_ai_api_call.call_args[0]
        self.assertGreater(call_args[0], 0.1)  # Should be at least 0.1 seconds
    
    @patch('utils.request_monitoring.monitoring_service')
    def test_monitor_db_query_decorator(self, mock_monitoring):
        """Test database query monitoring decorator."""
        from utils.request_monitoring import monitor_db_query
        
        @monitor_db_query
        def mock_db_query():
            time.sleep(0.05)  # Simulate DB query
            return "result"
        
        result = mock_db_query()
        
        self.assertEqual(result, "result")
        mock_monitoring.record_db_query.assert_called_once()
        
        # Check that query time was recorded
        call_args = mock_monitoring.record_db_query.call_args[0]
        self.assertGreater(call_args[0], 0.05)  # Should be at least 0.05 seconds

if __name__ == '__main__':
    unittest.main()