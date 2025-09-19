"""
Monitoring routes for system performance dashboard.
"""

from flask import Blueprint, jsonify, render_template, request
from flask_login import login_required, current_user
from datetime import datetime, timedelta
import logging

from services.monitoring import monitoring_service

logger = logging.getLogger(__name__)

monitoring_bp = Blueprint('monitoring', __name__, url_prefix='/monitoring')

@monitoring_bp.route('/dashboard')
@login_required
def dashboard():
    """Render the monitoring dashboard page."""
    return render_template('monitoring/dashboard.html')

@monitoring_bp.route('/api/metrics')
@login_required
def get_metrics():
    """Get current system metrics."""
    try:
        dashboard_data = monitoring_service.get_dashboard_data()
        return jsonify({
            'success': True,
            'data': dashboard_data
        })
    except Exception as e:
        logger.error(f"Error getting metrics: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve metrics'
        }), 500

@monitoring_bp.route('/api/health')
@login_required
def get_health_status():
    """Get system health status."""
    try:
        health_checks = monitoring_service.health_checker.run_all_health_checks()
        return jsonify({
            'success': True,
            'health_checks': [
                {
                    'service': check.service,
                    'status': check.status,
                    'message': check.message,
                    'timestamp': check.timestamp.isoformat(),
                    'response_time': check.response_time
                }
                for check in health_checks
            ]
        })
    except Exception as e:
        logger.error(f"Error getting health status: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve health status'
        }), 500

@monitoring_bp.route('/api/alerts')
@login_required
def get_alerts():
    """Get active system alerts."""
    try:
        active_alerts = monitoring_service.alert_manager.get_active_alerts()
        return jsonify({
            'success': True,
            'alerts': [
                {
                    'id': alert.id,
                    'type': alert.type,
                    'severity': alert.severity,
                    'message': alert.message,
                    'timestamp': alert.timestamp.isoformat(),
                    'resolved': alert.resolved
                }
                for alert in active_alerts
            ]
        })
    except Exception as e:
        logger.error(f"Error getting alerts: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve alerts'
        }), 500

@monitoring_bp.route('/api/alerts/<alert_id>/resolve', methods=['POST'])
@login_required
def resolve_alert(alert_id):
    """Resolve a specific alert."""
    try:
        success = monitoring_service.alert_manager.resolve_alert(alert_id)
        if success:
            return jsonify({
                'success': True,
                'message': 'Alert resolved successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Alert not found or already resolved'
            }), 404
    except Exception as e:
        logger.error(f"Error resolving alert {alert_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to resolve alert'
        }), 500

@monitoring_bp.route('/api/metrics/historical')
@login_required
def get_historical_metrics():
    """Get historical metrics for charts."""
    try:
        # Get time range from query parameters
        hours = request.args.get('hours', 24, type=int)
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        
        # Filter historical metrics by time range
        historical_metrics = [
            metric for metric in monitoring_service.metrics_collector.metrics_history
            if start_time <= metric.timestamp <= end_time
        ]
        
        return jsonify({
            'success': True,
            'metrics': [
                {
                    'timestamp': metric.timestamp.isoformat(),
                    'cpu_percent': metric.cpu_percent,
                    'memory_percent': metric.memory_percent,
                    'disk_usage_percent': metric.disk_usage_percent,
                    'response_time_avg': metric.response_time_avg,
                    'requests_per_minute': metric.requests_per_minute,
                    'error_rate': metric.error_rate,
                    'ai_api_latency': metric.ai_api_latency,
                    'database_query_time': metric.database_query_time
                }
                for metric in historical_metrics
            ]
        })
    except Exception as e:
        logger.error(f"Error getting historical metrics: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve historical metrics'
        }), 500

@monitoring_bp.route('/api/system-info')
@login_required
def get_system_info():
    """Get basic system information."""
    try:
        import psutil
        import platform
        
        system_info = {
            'platform': platform.platform(),
            'python_version': platform.python_version(),
            'cpu_count': psutil.cpu_count(),
            'total_memory': psutil.virtual_memory().total,
            'disk_total': psutil.disk_usage('/').total,
            'boot_time': datetime.fromtimestamp(psutil.boot_time()).isoformat()
        }
        
        return jsonify({
            'success': True,
            'system_info': system_info
        })
    except Exception as e:
        logger.error(f"Error getting system info: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve system information'
        }), 500

@monitoring_bp.route('/api/performance-summary')
@login_required
def get_performance_summary():
    """Get performance summary for the last 24 hours."""
    try:
        # Get metrics from the last 24 hours
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=24)
        
        historical_metrics = [
            metric for metric in monitoring_service.metrics_collector.metrics_history
            if start_time <= metric.timestamp <= end_time
        ]
        
        if not historical_metrics:
            return jsonify({
                'success': True,
                'summary': {
                    'avg_response_time': 0,
                    'max_response_time': 0,
                    'avg_cpu_usage': 0,
                    'max_cpu_usage': 0,
                    'avg_memory_usage': 0,
                    'max_memory_usage': 0,
                    'total_requests': 0,
                    'total_errors': 0,
                    'uptime_percentage': 100
                }
            })
        
        # Calculate summary statistics
        response_times = [m.response_time_avg for m in historical_metrics if m.response_time_avg > 0]
        cpu_usages = [m.cpu_percent for m in historical_metrics]
        memory_usages = [m.memory_percent for m in historical_metrics]
        
        summary = {
            'avg_response_time': sum(response_times) / len(response_times) if response_times else 0,
            'max_response_time': max(response_times) if response_times else 0,
            'avg_cpu_usage': sum(cpu_usages) / len(cpu_usages) if cpu_usages else 0,
            'max_cpu_usage': max(cpu_usages) if cpu_usages else 0,
            'avg_memory_usage': sum(memory_usages) / len(memory_usages) if memory_usages else 0,
            'max_memory_usage': max(memory_usages) if memory_usages else 0,
            'total_requests': sum(m.requests_per_minute for m in historical_metrics),
            'avg_error_rate': sum(m.error_rate for m in historical_metrics) / len(historical_metrics) if historical_metrics else 0,
            'uptime_percentage': 100  # Simplified - would need more sophisticated calculation
        }
        
        return jsonify({
            'success': True,
            'summary': summary
        })
    except Exception as e:
        logger.error(f"Error getting performance summary: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve performance summary'
        }), 500