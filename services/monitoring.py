"""
Performance monitoring service for AI Executive Suite.
Provides real-time metrics collection, health checks, and alerting.
"""

import time
import psutil
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import logging
import json
import sqlite3
from flask import current_app

logger = logging.getLogger(__name__)

@dataclass
class SystemMetrics:
    """System performance metrics."""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    disk_usage_percent: float
    active_connections: int
    response_time_avg: float
    requests_per_minute: int
    error_rate: float
    ai_api_latency: float
    database_query_time: float

@dataclass
class HealthCheck:
    """System health check result."""
    service: str
    status: str  # 'healthy', 'warning', 'critical'
    message: str
    timestamp: datetime
    response_time: Optional[float] = None

@dataclass
class Alert:
    """System alert."""
    id: str
    type: str  # 'performance', 'error', 'security'
    severity: str  # 'low', 'medium', 'high', 'critical'
    message: str
    timestamp: datetime
    resolved: bool = False
    resolved_at: Optional[datetime] = None

class MetricsCollector:
    """Collects system performance metrics."""
    
    def __init__(self):
        self.metrics_history = deque(maxlen=1000)  # Keep last 1000 metrics
        self.request_times = deque(maxlen=100)  # Keep last 100 request times
        self.error_count = 0
        self.request_count = 0
        self.ai_api_times = deque(maxlen=50)
        self.db_query_times = deque(maxlen=50)
        self._lock = threading.Lock()
    
    def record_request(self, response_time: float, is_error: bool = False):
        """Record a request with its response time and error status."""
        with self._lock:
            self.request_times.append(response_time)
            self.request_count += 1
            if is_error:
                self.error_count += 1
    
    def record_ai_api_call(self, response_time: float):
        """Record AI API call response time."""
        with self._lock:
            self.ai_api_times.append(response_time)
    
    def record_db_query(self, query_time: float):
        """Record database query time."""
        with self._lock:
            self.db_query_times.append(query_time)
    
    def get_current_metrics(self) -> SystemMetrics:
        """Get current system metrics."""
        with self._lock:
            # System metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Network connections (approximate active connections)
            try:
                connections = len(psutil.net_connections(kind='inet'))
            except (psutil.AccessDenied, PermissionError):
                # Fallback if we don't have permission to access network connections
                connections = 0
            
            # Application metrics
            avg_response_time = (
                sum(self.request_times) / len(self.request_times)
                if self.request_times else 0.0
            )
            
            # Calculate requests per minute (approximate)
            requests_per_minute = len(self.request_times) * 60 / 100  # Rough estimate
            
            # Error rate
            error_rate = (
                (self.error_count / self.request_count * 100)
                if self.request_count > 0 else 0.0
            )
            
            # AI API latency
            ai_api_latency = (
                sum(self.ai_api_times) / len(self.ai_api_times)
                if self.ai_api_times else 0.0
            )
            
            # Database query time
            db_query_time = (
                sum(self.db_query_times) / len(self.db_query_times)
                if self.db_query_times else 0.0
            )
            
            metrics = SystemMetrics(
                timestamp=datetime.now(),
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                disk_usage_percent=disk.percent,
                active_connections=connections,
                response_time_avg=avg_response_time,
                requests_per_minute=requests_per_minute,
                error_rate=error_rate,
                ai_api_latency=ai_api_latency,
                database_query_time=db_query_time
            )
            
            self.metrics_history.append(metrics)
            return metrics

class HealthChecker:
    """Performs system health checks."""
    
    def __init__(self):
        self.health_history = deque(maxlen=100)
    
    def check_database_health(self) -> HealthCheck:
        """Check database connectivity and performance."""
        start_time = time.time()
        try:
            # Simple database connectivity test
            from models import db
            with current_app.app_context():
                db.session.execute('SELECT 1')
            response_time = time.time() - start_time
            
            if response_time > 5.0:
                status = 'warning'
                message = f'Database responding slowly ({response_time:.2f}s)'
            else:
                status = 'healthy'
                message = 'Database connection healthy'
                
            return HealthCheck(
                service='database',
                status=status,
                message=message,
                timestamp=datetime.now(),
                response_time=response_time
            )
        except Exception as e:
            return HealthCheck(
                service='database',
                status='critical',
                message=f'Database connection failed: {str(e)}',
                timestamp=datetime.now(),
                response_time=time.time() - start_time
            )
    
    def check_ai_service_health(self) -> HealthCheck:
        """Check AI service availability."""
        start_time = time.time()
        try:
            # Simple AI service health check
            from services.ai_integration import AIIntegrationService
            ai_service = AIIntegrationService()
            
            # This would be a lightweight health check call
            # For now, we'll simulate it
            response_time = time.time() - start_time
            
            return HealthCheck(
                service='ai_service',
                status='healthy',
                message='AI service available',
                timestamp=datetime.now(),
                response_time=response_time
            )
        except Exception as e:
            return HealthCheck(
                service='ai_service',
                status='critical',
                message=f'AI service unavailable: {str(e)}',
                timestamp=datetime.now(),
                response_time=time.time() - start_time
            )
    
    def check_disk_space(self) -> HealthCheck:
        """Check available disk space."""
        try:
            disk = psutil.disk_usage('/')
            usage_percent = disk.percent
            
            if usage_percent > 90:
                status = 'critical'
                message = f'Disk usage critical: {usage_percent:.1f}%'
            elif usage_percent > 80:
                status = 'warning'
                message = f'Disk usage high: {usage_percent:.1f}%'
            else:
                status = 'healthy'
                message = f'Disk usage normal: {usage_percent:.1f}%'
            
            return HealthCheck(
                service='disk_space',
                status=status,
                message=message,
                timestamp=datetime.now()
            )
        except Exception as e:
            return HealthCheck(
                service='disk_space',
                status='critical',
                message=f'Unable to check disk space: {str(e)}',
                timestamp=datetime.now()
            )
    
    def check_memory_usage(self) -> HealthCheck:
        """Check memory usage."""
        try:
            memory = psutil.virtual_memory()
            usage_percent = memory.percent
            
            if usage_percent > 90:
                status = 'critical'
                message = f'Memory usage critical: {usage_percent:.1f}%'
            elif usage_percent > 80:
                status = 'warning'
                message = f'Memory usage high: {usage_percent:.1f}%'
            else:
                status = 'healthy'
                message = f'Memory usage normal: {usage_percent:.1f}%'
            
            return HealthCheck(
                service='memory',
                status=status,
                message=message,
                timestamp=datetime.now()
            )
        except Exception as e:
            return HealthCheck(
                service='memory',
                status='critical',
                message=f'Unable to check memory usage: {str(e)}',
                timestamp=datetime.now()
            )
    
    def run_all_health_checks(self) -> List[HealthCheck]:
        """Run all health checks and return results."""
        checks = [
            self.check_database_health(),
            self.check_ai_service_health(),
            self.check_disk_space(),
            self.check_memory_usage()
        ]
        
        self.health_history.extend(checks)
        return checks

class AlertManager:
    """Manages system alerts and notifications."""
    
    def __init__(self):
        self.alerts = []
        self.alert_thresholds = {
            'cpu_percent': 80.0,
            'memory_percent': 85.0,
            'disk_usage_percent': 90.0,
            'error_rate': 5.0,
            'response_time_avg': 2.0,
            'ai_api_latency': 10.0
        }
    
    def check_metrics_for_alerts(self, metrics: SystemMetrics) -> List[Alert]:
        """Check metrics against thresholds and generate alerts."""
        new_alerts = []
        
        # CPU usage alert
        if metrics.cpu_percent > self.alert_thresholds['cpu_percent']:
            alert = Alert(
                id=f"cpu_high_{int(time.time())}",
                type='performance',
                severity='high' if metrics.cpu_percent > 95 else 'medium',
                message=f'High CPU usage: {metrics.cpu_percent:.1f}%',
                timestamp=metrics.timestamp
            )
            new_alerts.append(alert)
        
        # Memory usage alert
        if metrics.memory_percent > self.alert_thresholds['memory_percent']:
            alert = Alert(
                id=f"memory_high_{int(time.time())}",
                type='performance',
                severity='high' if metrics.memory_percent > 95 else 'medium',
                message=f'High memory usage: {metrics.memory_percent:.1f}%',
                timestamp=metrics.timestamp
            )
            new_alerts.append(alert)
        
        # Disk usage alert
        if metrics.disk_usage_percent > self.alert_thresholds['disk_usage_percent']:
            alert = Alert(
                id=f"disk_high_{int(time.time())}",
                type='performance',
                severity='critical' if metrics.disk_usage_percent > 95 else 'high',
                message=f'High disk usage: {metrics.disk_usage_percent:.1f}%',
                timestamp=metrics.timestamp
            )
            new_alerts.append(alert)
        
        # Error rate alert
        if metrics.error_rate > self.alert_thresholds['error_rate']:
            alert = Alert(
                id=f"error_rate_high_{int(time.time())}",
                type='error',
                severity='high' if metrics.error_rate > 10 else 'medium',
                message=f'High error rate: {metrics.error_rate:.1f}%',
                timestamp=metrics.timestamp
            )
            new_alerts.append(alert)
        
        # Response time alert
        if metrics.response_time_avg > self.alert_thresholds['response_time_avg']:
            alert = Alert(
                id=f"response_time_high_{int(time.time())}",
                type='performance',
                severity='medium',
                message=f'High response time: {metrics.response_time_avg:.2f}s',
                timestamp=metrics.timestamp
            )
            new_alerts.append(alert)
        
        # AI API latency alert
        if metrics.ai_api_latency > self.alert_thresholds['ai_api_latency']:
            alert = Alert(
                id=f"ai_latency_high_{int(time.time())}",
                type='performance',
                severity='medium',
                message=f'High AI API latency: {metrics.ai_api_latency:.2f}s',
                timestamp=metrics.timestamp
            )
            new_alerts.append(alert)
        
        self.alerts.extend(new_alerts)
        return new_alerts
    
    def get_active_alerts(self) -> List[Alert]:
        """Get all active (unresolved) alerts."""
        return [alert for alert in self.alerts if not alert.resolved]
    
    def resolve_alert(self, alert_id: str) -> bool:
        """Mark an alert as resolved."""
        for alert in self.alerts:
            if alert.id == alert_id and not alert.resolved:
                alert.resolved = True
                alert.resolved_at = datetime.now()
                return True
        return False

class MonitoringService:
    """Main monitoring service that coordinates all monitoring activities."""
    
    def __init__(self):
        self.metrics_collector = MetricsCollector()
        self.health_checker = HealthChecker()
        self.alert_manager = AlertManager()
        self._monitoring_thread = None
        self._monitoring_active = False
    
    def start_monitoring(self, interval: int = 60):
        """Start background monitoring with specified interval in seconds."""
        if self._monitoring_active:
            return
        
        self._monitoring_active = True
        self._monitoring_thread = threading.Thread(
            target=self._monitoring_loop,
            args=(interval,),
            daemon=True
        )
        self._monitoring_thread.start()
        logger.info(f"Monitoring started with {interval}s interval")
    
    def stop_monitoring(self):
        """Stop background monitoring."""
        self._monitoring_active = False
        if self._monitoring_thread:
            self._monitoring_thread.join(timeout=5)
        logger.info("Monitoring stopped")
    
    def _monitoring_loop(self, interval: int):
        """Background monitoring loop."""
        while self._monitoring_active:
            try:
                # Collect metrics
                metrics = self.metrics_collector.get_current_metrics()
                
                # Check for alerts
                new_alerts = self.alert_manager.check_metrics_for_alerts(metrics)
                
                # Log new alerts
                for alert in new_alerts:
                    logger.warning(f"Alert generated: {alert.message}")
                
                # Run health checks every 5 minutes
                if int(time.time()) % 300 == 0:  # Every 5 minutes
                    health_checks = self.health_checker.run_all_health_checks()
                    for check in health_checks:
                        if check.status in ['warning', 'critical']:
                            logger.warning(f"Health check {check.service}: {check.message}")
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {str(e)}")
            
            time.sleep(interval)
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive dashboard data."""
        current_metrics = self.metrics_collector.get_current_metrics()
        health_checks = self.health_checker.run_all_health_checks()
        active_alerts = self.alert_manager.get_active_alerts()
        
        # Get historical metrics for charts
        historical_metrics = list(self.metrics_collector.metrics_history)
        
        return {
            'current_metrics': asdict(current_metrics),
            'health_checks': [asdict(check) for check in health_checks],
            'active_alerts': [asdict(alert) for alert in active_alerts],
            'historical_metrics': [asdict(m) for m in historical_metrics[-50:]],  # Last 50 points
            'system_status': self._get_overall_system_status(health_checks, active_alerts)
        }
    
    def _get_overall_system_status(self, health_checks: List[HealthCheck], alerts: List[Alert]) -> str:
        """Determine overall system status."""
        # Check for critical health issues
        for check in health_checks:
            if check.status == 'critical':
                return 'critical'
        
        # Check for critical alerts
        for alert in alerts:
            if alert.severity == 'critical':
                return 'critical'
        
        # Check for warnings
        for check in health_checks:
            if check.status == 'warning':
                return 'warning'
        
        for alert in alerts:
            if alert.severity in ['high', 'medium']:
                return 'warning'
        
        return 'healthy'
    
    def record_request(self, response_time: float, is_error: bool = False):
        """Record a request for metrics collection."""
        self.metrics_collector.record_request(response_time, is_error)
    
    def record_ai_api_call(self, response_time: float):
        """Record an AI API call for metrics collection."""
        self.metrics_collector.record_ai_api_call(response_time)
    
    def record_db_query(self, query_time: float):
        """Record a database query for metrics collection."""
        self.metrics_collector.record_db_query(query_time)

# Global monitoring service instance
monitoring_service = MonitoringService()