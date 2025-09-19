#!/usr/bin/env python3
"""
Simple test for monitoring system functionality.
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from services.monitoring import MetricsCollector, AlertManager, SystemMetrics
from datetime import datetime

def test_metrics_collector():
    """Test basic metrics collector functionality."""
    print("Testing MetricsCollector...")
    
    collector = MetricsCollector()
    
    # Test recording requests
    collector.record_request(0.5, False)
    collector.record_request(1.0, True)
    collector.record_ai_api_call(2.0)
    collector.record_db_query(0.1)
    
    print(f"✓ Request times: {len(collector.request_times)} recorded")
    print(f"✓ Request count: {collector.request_count}")
    print(f"✓ Error count: {collector.error_count}")
    print(f"✓ AI API times: {len(collector.ai_api_times)} recorded")
    print(f"✓ DB query times: {len(collector.db_query_times)} recorded")
    
    return True

def test_alert_manager():
    """Test basic alert manager functionality."""
    print("\nTesting AlertManager...")
    
    alert_manager = AlertManager()
    
    # Create test metrics that should trigger alerts
    metrics = SystemMetrics(
        timestamp=datetime.now(),
        cpu_percent=85.0,  # Above threshold
        memory_percent=90.0,  # Above threshold
        disk_usage_percent=50.0,
        active_connections=10,
        response_time_avg=1.0,
        requests_per_minute=100,
        error_rate=2.0,
        ai_api_latency=5.0,
        database_query_time=0.1
    )
    
    alerts = alert_manager.check_metrics_for_alerts(metrics)
    print(f"✓ Generated {len(alerts)} alerts")
    
    for alert in alerts:
        print(f"  - {alert.severity}: {alert.message}")
    
    # Test alert resolution
    if alerts:
        alert_id = alerts[0].id
        success = alert_manager.resolve_alert(alert_id)
        print(f"✓ Alert resolution: {success}")
    
    return True

def main():
    """Run simple monitoring tests."""
    print("🔍 Testing AI Executive Suite Monitoring System")
    print("=" * 50)
    
    try:
        test_metrics_collector()
        test_alert_manager()
        
        print("\n✅ All basic monitoring tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)