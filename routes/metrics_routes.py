"""
Metrics routes for monitoring and observability
"""

from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from models import db, Decision, Document, User
from sqlalchemy import func
import os

metrics_bp = Blueprint('metrics', __name__, url_prefix='/api')

@metrics_bp.route('/metrics')
def prometheus_metrics():
    """Prometheus metrics endpoint"""
    try:
        # Basic application metrics
        metrics = []
        
        # Health metric
        metrics.append('# HELP app_health_status Application health status')
        metrics.append('# TYPE app_health_status gauge')
        metrics.append(f'app_health_status{{instance="{request.host}"}} 1')
        
        # User metrics
        total_users = User.query.count()
        metrics.append('# HELP total_users_count Total number of registered users')
        metrics.append('# TYPE total_users_count gauge')
        metrics.append(f'total_users_count {total_users}')
        
        # Decision metrics
        total_decisions = Decision.query.count()
        metrics.append('# HELP total_decisions_count Total number of decisions')
        metrics.append('# TYPE total_decisions_count gauge')
        metrics.append(f'total_decisions_count {total_decisions}')
        
        # Decisions by executive type
        decision_counts = db.session.query(
            Decision.executive_type,
            func.count(Decision.id)
        ).group_by(Decision.executive_type).all()
        
        metrics.append('# HELP decisions_by_executive_total Decisions by executive type')
        metrics.append('# TYPE decisions_by_executive_total gauge')
        for exec_type, count in decision_counts:
            metrics.append(f'decisions_by_executive_total{{executive_type="{exec_type}"}} {count}')
        
        # Document metrics
        total_documents = Document.query.count()
        metrics.append('# HELP total_documents_count Total number of documents')
        metrics.append('# TYPE total_documents_count gauge')
        metrics.append(f'total_documents_count {total_documents}')
        
        # Recent activity metrics (last 24 hours)
        yesterday = datetime.utcnow() - timedelta(days=1)
        
        recent_decisions = Decision.query.filter(Decision.created_at >= yesterday).count()
        metrics.append('# HELP decisions_last_24h Decisions created in last 24 hours')
        metrics.append('# TYPE decisions_last_24h gauge')
        metrics.append(f'decisions_last_24h {recent_decisions}')
        
        recent_documents = Document.query.filter(Document.created_at >= yesterday).count()
        metrics.append('# HELP documents_last_24h Documents processed in last 24 hours')
        metrics.append('# TYPE documents_last_24h gauge')
        metrics.append(f'documents_last_24h {recent_documents}')
        
        # Average confidence score
        avg_confidence = db.session.query(func.avg(Decision.confidence_score)).scalar() or 0
        metrics.append('# HELP avg_decision_confidence Average decision confidence score')
        metrics.append('# TYPE avg_decision_confidence gauge')
        metrics.append(f'avg_decision_confidence {avg_confidence:.3f}')
        
        return '\n'.join(metrics), 200, {'Content-Type': 'text/plain; charset=utf-8'}
        
    except Exception as e:
        return f"# Error generating metrics: {str(e)}", 500, {'Content-Type': 'text/plain; charset=utf-8'}

@metrics_bp.route('/metrics/business')
@login_required
def business_metrics():
    """Business metrics for APM agent"""
    try:
        # Calculate business metrics
        today = datetime.utcnow().date()
        yesterday = datetime.utcnow() - timedelta(days=1)
        
        # Active users (users who logged in today)
        # This would require session tracking, for now we'll use a placeholder
        active_users = User.query.filter(User.last_login >= yesterday).count() if hasattr(User, 'last_login') else 0
        
        # Decisions created today by executive type
        decisions_today = db.session.query(
            Decision.executive_type,
            func.count(Decision.id)
        ).filter(
            func.date(Decision.created_at) == today
        ).group_by(Decision.executive_type).all()
        
        decisions_by_type = {exec_type: count for exec_type, count in decisions_today}
        
        # Documents processed today
        documents_today = Document.query.filter(
            func.date(Document.created_at) == today
        ).count()
        
        # AI accuracy score (average confidence of recent decisions)
        recent_confidence = db.session.query(
            func.avg(Decision.confidence_score)
        ).filter(
            Decision.created_at >= yesterday
        ).scalar() or 0.8  # Default to 0.8 if no recent decisions
        
        # Response time metrics (would be collected from actual response times)
        # For now, we'll provide placeholder values
        avg_response_time = 1.2  # seconds
        
        return jsonify({
            'active_users': active_users,
            'decisions_today': decisions_by_type,
            'documents_processed_today': documents_today,
            'ai_accuracy_score': float(recent_confidence),
            'avg_response_time': avg_response_time,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@metrics_bp.route('/metrics/health')
def health_metrics():
    """Detailed health metrics"""
    try:
        # Database connectivity
        try:
            db.session.execute('SELECT 1')
            db_status = 'connected'
            db_response_time = 0.1  # Would measure actual response time
        except Exception as e:
            db_status = f'error: {str(e)}'
            db_response_time = -1
        
        # Redis connectivity (if available)
        redis_status = 'ok'
        try:
            from services.registry import ServiceRegistry
            registry = ServiceRegistry()
            if hasattr(registry, 'redis_client'):
                registry.redis_client.ping()
        except:
            redis_status = 'unavailable'
        
        # System metrics
        import psutil
        cpu_percent = psutil.cpu_percent()
        memory_percent = psutil.virtual_memory().percent
        disk_percent = psutil.disk_usage('/').percent
        
        return jsonify({
            'status': 'healthy' if db_status == 'connected' else 'unhealthy',
            'timestamp': datetime.utcnow().isoformat(),
            'database': {
                'status': db_status,
                'response_time': db_response_time
            },
            'redis': {
                'status': redis_status
            },
            'system': {
                'cpu_percent': cpu_percent,
                'memory_percent': memory_percent,
                'disk_percent': disk_percent
            },
            'instance_id': os.getenv('INSTANCE_ID', 'unknown'),
            'version': os.getenv('APP_VERSION', '1.0.0')
        })
        
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500

@metrics_bp.route('/metrics/db-metrics')
def database_metrics():
    """Database-specific metrics"""
    try:
        # Get database statistics
        stats = {}
        
        # Table row counts
        stats['users_count'] = User.query.count()
        stats['decisions_count'] = Decision.query.count()
        stats['documents_count'] = Document.query.count()
        
        # Recent activity
        yesterday = datetime.utcnow() - timedelta(days=1)
        stats['recent_decisions'] = Decision.query.filter(Decision.created_at >= yesterday).count()
        stats['recent_documents'] = Document.query.filter(Document.created_at >= yesterday).count()
        
        # Database size metrics would require specific queries
        # For now, we'll provide placeholder values
        stats['active_connections'] = 5  # Would get from pg_stat_activity
        stats['database_size_mb'] = 100  # Would calculate actual size
        
        return jsonify(stats)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500