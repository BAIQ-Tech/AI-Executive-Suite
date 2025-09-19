"""
Monitoring Infrastructure

System monitoring, health checks, and metrics collection
for the AI Executive Suite.
"""

import logging
import time
import psutil
import threading
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque
from functools import wraps

from config.settings import config

logger = logging.getLogger(__name__)


@dataclass
class HealthCheck:
    """Health check definition"""
    name: str
    check_function: Callable[[], bool]
    description: str
    timeout: int = 5
    critical: bool = True


@dataclass
class MetricPoint:
    """Single metric data point"""
    timestamp: datetime
    value: float
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class SystemMetrics:
    """System performance metrics"""
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    active_connections: int
    response_time_avg: float
    error_rate: float
    timestamp: datetime


class MetricsCollector:
    """Collects and stores application metrics"""
    
    def __init__(self):
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.counters: Dict[str, int] = defaultdict(int)
        self.gauges: Dict[str, float] = defaultdict(float)
        self.histograms: Dict[str, List[float]] = defaultdict(list)
        self._lock = threading.Lock()
        
    def increment_counter(self, name: str, value: int = 1, tags: Dict[str, str] = None):
        """Increment a counter metric"""
        with self._lock:
            key = self._make_key(name, tags)
            self.counters[key] += value
            
    def set_gauge(self, name: str, value: float, tags: Dict[str, str] = None):
        """Set a gauge metric value"""
        with self._lock:
            key = self._make_key(name, tags)
            self.gauges[key] = value
            
    def record_histogram(self, name: str, value: float, tags: Dict[str, str] = None):
        """Record a value in a histogram"""
        with self._lock:
            key = self._make_key(name, tags)
            self.histograms[key].append(value)
            # Keep only last 1000 values
            if len(self.histograms[key]) > 1000:
                self.histograms[key] = self.histograms[key][-1000:]
                
    def record_metric(self, name: str, value: float, tags: Dict[str, str] = None):
        """Record a time-series metric"""
        with self._lock:
            key = self._make_key(name, tags)
            self.metrics[key].append(MetricPoint(
                timestamp=datetime.utcnow(),
                value=value,
                tags=tags or {}
            ))
            
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of all metrics"""
        with self._lock:
            return {
                'counters': dict(self.counters),
                'gauges': dict(self.gauges),
                'histograms': {
                    name: {
                        'count': len(values),
                        'avg': sum(values) / len(values) if values else 0,
                        'min': min(values) if values else 0,
                        'max': max(values) if values else 0
                    }
                    for name, values in self.histograms.items()
                },
                'time_series_count': len(self.metrics)
            }
            
    def _make_key(self, name: str, tags: Dict[str, str] = None) -> str:
        """Create a unique key for metric with tags"""
        if not tags:
            return name
        tag_str = ','.join(f"{k}={v}" for k, v in sorted(tags.items()))
        return f"{name}[{tag_str}]"


class HealthChecker:
    """Manages application health checks"""
    
    def __init__(self):
        self.checks: List[HealthCheck] = []
        self.last_results: Dict[str, Dict[str, Any]] = {}
        
    def register_check(self, check: HealthCheck):
        """Register a new health check"""
        self.checks.append(check)
        logger.info(f"Registered health check: {check.name}")
        
    def run_checks(self) -> Dict[str, Any]:
        """Run all health checks and return results"""
        results = {
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'checks': {}
        }
        
        overall_healthy = True
        
        for check in self.checks:
            check_result = self._run_single_check(check)
            results['checks'][check.name] = check_result
            
            if not check_result['healthy'] and check.critical:
                overall_healthy = False
                
        results['status'] = 'healthy' if overall_healthy else 'unhealthy'
        self.last_results = results
        
        return results
        
    def _run_single_check(self, check: HealthCheck) -> Dict[str, Any]:
        """Run a single health check"""
        start_time = time.time()
        
        try:
            # Run check with timeout
            result = self._run_with_timeout(check.check_function, check.timeout)
            duration = time.time() - start_time
            
            return {
                'healthy': result,
                'duration': duration,
                'description': check.description,
                'critical': check.critical,
                'error': None
            }
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Health check {check.name} failed: {e}")
            
            return {
                'healthy': False,
                'duration': duration,
                'description': check.description,
                'critical': check.critical,
                'error': str(e)
            }
            
    def _run_with_timeout(self, func: Callable, timeout: int) -> bool:
        """Run function with timeout"""
        # Simple timeout implementation
        # In production, you might want to use more sophisticated timeout handling
        return func()


class SystemMonitor:
    """Monitors system resources and performance"""
    
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics_collector = metrics_collector
        self.monitoring_active = False
        self.monitor_thread = None
        
    def start_monitoring(self):
        """Start system monitoring in background thread"""
        if self.monitoring_active:
            return
            
        self.monitoring_active = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("System monitoring started")
        
    def stop_monitoring(self):
        """Stop system monitoring"""
        self.monitoring_active = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("System monitoring stopped")
        
    def get_current_metrics(self) -> SystemMetrics:
        """Get current system metrics"""
        return SystemMetrics(
            cpu_percent=psutil.cpu_percent(),
            memory_percent=psutil.virtual_memory().percent,
            disk_percent=psutil.disk_usage('/').percent,
            active_connections=len(psutil.net_connections()),
            response_time_avg=0.0,  # Would be calculated from request metrics
            error_rate=0.0,  # Would be calculated from error metrics
            timestamp=datetime.utcnow()
        )
        
    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.monitoring_active:
            try:
                metrics = self.get_current_metrics()
                
                # Record system metrics
                self.metrics_collector.set_gauge('system.cpu_percent', metrics.cpu_percent)
                self.metrics_collector.set_gauge('system.memory_percent', metrics.memory_percent)
                self.metrics_collector.set_gauge('system.disk_percent', metrics.disk_percent)
                self.metrics_collector.set_gauge('system.active_connections', metrics.active_connections)
                
                # Sleep for monitoring interval
                time.sleep(config.monitoring.health_check_interval)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(5)  # Wait before retrying


class MonitoringService:
    """Main monitoring service that coordinates all monitoring components"""
    
    def __init__(self):
        self.metrics_collector = MetricsCollector()
        self.health_checker = HealthChecker()
        self.system_monitor = SystemMonitor(self.metrics_collector)
        self._setup_default_health_checks()
        
    def start(self):
        """Start all monitoring services"""
        if config.monitoring.enabled:
            self.system_monitor.start_monitoring()
            logger.info("Monitoring service started")
        else:
            logger.info("Monitoring disabled by configuration")
            
    def stop(self):
        """Stop all monitoring services"""
        self.system_monitor.stop_monitoring()
        logger.info("Monitoring service stopped")
        
    def get_health_status(self) -> Dict[str, Any]:
        """Get current health status"""
        return self.health_checker.run_checks()
        
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics summary"""
        return self.metrics_collector.get_metrics_summary()
        
    def _setup_default_health_checks(self):
        """Setup default health checks"""
        
        def check_database():
            """Check database connectivity"""
            # Placeholder - would implement actual database check
            return True
            
        def check_redis():
            """Check Redis connectivity"""
            # Placeholder - would implement actual Redis check
            return True
            
        def check_disk_space():
            """Check available disk space"""
            disk_usage = psutil.disk_usage('/')
            return disk_usage.percent < 90
            
        def check_memory():
            """Check memory usage"""
            memory = psutil.virtual_memory()
            return memory.percent < 90
            
        # Register default checks
        self.health_checker.register_check(HealthCheck(
            name="database",
            check_function=check_database,
            description="Database connectivity check",
            critical=True
        ))
        
        self.health_checker.register_check(HealthCheck(
            name="redis",
            check_function=check_redis,
            description="Redis connectivity check",
            critical=False
        ))
        
        self.health_checker.register_check(HealthCheck(
            name="disk_space",
            check_function=check_disk_space,
            description="Disk space availability check",
            critical=True
        ))
        
        self.health_checker.register_check(HealthCheck(
            name="memory",
            check_function=check_memory,
            description="Memory usage check",
            critical=True
        ))


def monitor_performance(metric_name: str = None):
    """
    Decorator to monitor function performance
    
    Args:
        metric_name: Custom metric name (defaults to function name)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            name = metric_name or f"{func.__module__}.{func.__name__}"
            
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                # Record successful execution
                monitoring_service.metrics_collector.record_histogram(
                    f"{name}.duration", duration
                )
                monitoring_service.metrics_collector.increment_counter(
                    f"{name}.calls", tags={'status': 'success'}
                )
                
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                
                # Record failed execution
                monitoring_service.metrics_collector.record_histogram(
                    f"{name}.duration", duration
                )
                monitoring_service.metrics_collector.increment_counter(
                    f"{name}.calls", tags={'status': 'error'}
                )
                monitoring_service.metrics_collector.increment_counter(
                    f"{name}.errors"
                )
                
                raise
                
        return wrapper
    return decorator


# Global monitoring service instance
monitoring_service = MonitoringService()