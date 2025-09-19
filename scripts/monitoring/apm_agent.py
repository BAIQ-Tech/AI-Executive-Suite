#!/usr/bin/env python3
"""
Application Performance Monitoring Agent for AI Executive Suite
Collects custom business metrics and system performance data
"""

import os
import time
import logging
import requests
import schedule
import psutil
from datetime import datetime
from prometheus_client import start_http_server, Gauge, Counter, Histogram
from threading import Thread

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class APMAgent:
    def __init__(self):
        self.application_url = os.getenv('APPLICATION_URL', 'http://localhost:5000')
        self.check_interval = int(os.getenv('CHECK_INTERVAL', 30))
        
        # Prometheus metrics
        self.setup_metrics()
        
        # Start metrics server
        start_http_server(8000)
        logger.info("APM Agent metrics server started on port 8000")
    
    def setup_metrics(self):
        """Initialize Prometheus metrics"""
        # Application health metrics
        self.app_health = Gauge('app_health_status', 'Application health status', ['instance'])
        self.response_time = Histogram('app_response_time_seconds', 'Application response time', ['endpoint'])
        
        # Business metrics
        self.active_users = Gauge('active_users_total', 'Number of active users')
        self.decisions_created = Counter('decisions_created_total', 'Total decisions created', ['executive_type'])
        self.documents_processed = Counter('documents_processed_total', 'Total documents processed')
        self.documents_processed_success = Counter('documents_processed_success_total', 'Successfully processed documents')
        
        # AI metrics
        self.ai_response_time = Histogram('ai_response_duration_seconds', 'AI response time')
        self.ai_accuracy = Gauge('ai_decision_accuracy_score', 'AI decision accuracy score')
        self.decision_confidence = Histogram('decision_confidence_score', 'Decision confidence scores')
        
        # System metrics
        self.cpu_usage = Gauge('system_cpu_usage_percent', 'System CPU usage percentage')
        self.memory_usage = Gauge('system_memory_usage_percent', 'System memory usage percentage')
        self.disk_usage = Gauge('system_disk_usage_percent', 'System disk usage percentage', ['mountpoint'])
        
        # Database metrics
        self.db_connections = Gauge('database_connections_active', 'Active database connections')
        self.db_query_time = Histogram('database_query_duration_seconds', 'Database query duration')
        
        # Cache metrics
        self.cache_hit_rate = Gauge('cache_hit_rate', 'Cache hit rate')
        self.cache_memory_usage = Gauge('cache_memory_usage_bytes', 'Cache memory usage')
    
    def check_application_health(self):
        """Check application health and collect metrics"""
        try:
            start_time = time.time()
            response = requests.get(f"{self.application_url}/health", timeout=10)
            response_time = time.time() - start_time
            
            # Record response time
            self.response_time.labels(endpoint='/health').observe(response_time)
            
            if response.status_code == 200:
                self.app_health.labels(instance=self.application_url).set(1)
                
                # Parse health response for additional metrics
                try:
                    health_data = response.json()
                    if 'database' in health_data and health_data['database'] == 'connected':
                        logger.info("Database connection healthy")
                    if 'redis' in health_data and health_data['redis'] == 'ok':
                        logger.info("Redis connection healthy")
                except:
                    pass
                    
            else:
                self.app_health.labels(instance=self.application_url).set(0)
                logger.warning(f"Application health check failed: {response.status_code}")
                
        except Exception as e:
            self.app_health.labels(instance=self.application_url).set(0)
            logger.error(f"Application health check error: {e}")
    
    def collect_business_metrics(self):
        """Collect business-specific metrics from the application"""
        try:
            # Try to get business metrics from application API
            response = requests.get(f"{self.application_url}/api/metrics", timeout=10)
            
            if response.status_code == 200:
                metrics_data = response.json()
                
                # Update business metrics
                if 'active_users' in metrics_data:
                    self.active_users.set(metrics_data['active_users'])
                
                if 'decisions_today' in metrics_data:
                    for exec_type, count in metrics_data['decisions_today'].items():
                        self.decisions_created.labels(executive_type=exec_type)._value._value = count
                
                if 'documents_processed_today' in metrics_data:
                    self.documents_processed._value._value = metrics_data['documents_processed_today']
                
                if 'ai_accuracy_score' in metrics_data:
                    self.ai_accuracy.set(metrics_data['ai_accuracy_score'])
                
                logger.info("Business metrics collected successfully")
                
        except requests.exceptions.RequestException:
            # API endpoint might not exist yet, that's okay
            logger.debug("Business metrics API not available")
        except Exception as e:
            logger.error(f"Error collecting business metrics: {e}")
    
    def collect_system_metrics(self):
        """Collect system performance metrics"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            self.cpu_usage.set(cpu_percent)
            
            # Memory usage
            memory = psutil.virtual_memory()
            self.memory_usage.set(memory.percent)
            
            # Disk usage
            for partition in psutil.disk_partitions():
                try:
                    disk_usage = psutil.disk_usage(partition.mountpoint)
                    usage_percent = (disk_usage.used / disk_usage.total) * 100
                    self.disk_usage.labels(mountpoint=partition.mountpoint).set(usage_percent)
                except PermissionError:
                    # Skip partitions we can't access
                    continue
            
            logger.debug(f"System metrics: CPU {cpu_percent}%, Memory {memory.percent}%")
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
    
    def collect_database_metrics(self):
        """Collect database performance metrics"""
        try:
            # This would typically connect to the database to get metrics
            # For now, we'll simulate or try to get from application API
            response = requests.get(f"{self.application_url}/api/db-metrics", timeout=5)
            
            if response.status_code == 200:
                db_data = response.json()
                
                if 'active_connections' in db_data:
                    self.db_connections.set(db_data['active_connections'])
                
                logger.debug("Database metrics collected")
                
        except:
            # Database metrics API might not be available
            logger.debug("Database metrics not available")
    
    def run_checks(self):
        """Run all monitoring checks"""
        logger.info("Running APM checks...")
        
        self.check_application_health()
        self.collect_business_metrics()
        self.collect_system_metrics()
        self.collect_database_metrics()
        
        logger.info("APM checks completed")
    
    def start(self):
        """Start the APM agent"""
        logger.info("Starting APM Agent...")
        
        # Schedule regular checks
        schedule.every(self.check_interval).seconds.do(self.run_checks)
        
        # Run initial check
        self.run_checks()
        
        # Keep running
        while True:
            schedule.run_pending()
            time.sleep(1)

if __name__ == "__main__":
    agent = APMAgent()
    agent.start()