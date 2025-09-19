"""
Routes for usage analytics and optimization.
"""

from flask import Blueprint, request, jsonify, render_template
from flask_login import login_required, current_user
from datetime import datetime, timedelta
import logging

from services.usage_analytics import usage_analytics_service, PerformanceBottleneck, PerformanceIssue

logger = logging.getLogger(__name__)

usage_analytics_bp = Blueprint('usage_analytics', __name__, url_prefix='/usage-analytics')

@usage_analytics_bp.route('/dashboard')
@login_required
def analytics_dashboard():
    """Render the usage analytics dashboard."""
    return render_template('usage_analytics/dashboard.html')

@usage_analytics_bp.route('/api/dashboard-data')
@login_required
def get_dashboard_data():
    """Get comprehensive usage analytics dashboard data."""
    try:
        dashboard_data = usage_analytics_service.get_usage_dashboard_data()
        return jsonify({
            'success': True,
            'data': dashboard_data
        })
    except Exception as e:
        logger.error(f"Error getting dashboard data: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve dashboard data'
        }), 500

@usage_analytics_bp.route('/api/feature-usage')
@login_required
def get_feature_usage():
    """Get feature usage statistics."""
    try:
        days = request.args.get('days', 30, type=int)
        time_range = timedelta(days=days)
        
        feature_stats = usage_analytics_service.usage_tracker.get_feature_usage_stats(time_range)
        
        return jsonify({
            'success': True,
            'feature_usage': [
                {
                    'feature_name': stat.feature_name,
                    'total_uses': stat.total_uses,
                    'unique_users': stat.unique_users,
                    'avg_session_duration': round(stat.avg_session_duration, 2),
                    'success_rate': round(stat.success_rate, 2),
                    'last_used': stat.last_used.isoformat() if stat.last_used else None,
                    'usage_trend': round(stat.usage_trend, 3)
                }
                for stat in feature_stats
            ]
        })
    except Exception as e:
        logger.error(f"Error getting feature usage: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve feature usage data'
        }), 500

@usage_analytics_bp.route('/api/user-behavior')
@login_required
def get_user_behavior():
    """Get user behavior patterns."""
    try:
        user_id = request.args.get('user_id')
        limit = request.args.get('limit', 20, type=int)
        
        behavior_patterns = usage_analytics_service.usage_tracker.get_user_behavior_patterns(user_id)
        
        # Limit results
        limited_patterns = behavior_patterns[:limit]
        
        return jsonify({
            'success': True,
            'user_behavior': [
                {
                    'user_id': pattern.user_id,
                    'total_sessions': pattern.total_sessions,
                    'avg_session_duration': round(pattern.avg_session_duration, 2),
                    'most_used_features': [{'feature': f[0], 'count': f[1]} for f in pattern.most_used_features],
                    'preferred_executive': pattern.preferred_executive,
                    'peak_usage_hours': [{'hour': h[0], 'count': h[1]} for h in pattern.peak_usage_hours],
                    'device_types': pattern.device_types,
                    'engagement_score': round(pattern.engagement_score, 1)
                }
                for pattern in limited_patterns
            ]
        })
    except Exception as e:
        logger.error(f"Error getting user behavior: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve user behavior data'
        }), 500

@usage_analytics_bp.route('/api/performance-issues')
@login_required
def get_performance_issues():
    """Get performance bottlenecks."""
    try:
        days = request.args.get('days', 7, type=int)
        time_range = timedelta(days=days)
        
        performance_issues = usage_analytics_service.usage_tracker.get_performance_bottlenecks(time_range)
        
        return jsonify({
            'success': True,
            'performance_issues': [
                {
                    'issue_type': issue.issue_type.value,
                    'affected_feature': issue.affected_feature,
                    'severity': issue.severity,
                    'frequency': issue.frequency,
                    'avg_impact_time': round(issue.avg_impact_time, 2),
                    'affected_users': issue.affected_users,
                    'first_detected': issue.first_detected.isoformat(),
                    'last_detected': issue.last_detected.isoformat(),
                    'recommendation': issue.recommendation
                }
                for issue in performance_issues
            ]
        })
    except Exception as e:
        logger.error(f"Error getting performance issues: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve performance issues'
        }), 500

@usage_analytics_bp.route('/api/optimization-recommendations')
@login_required
def get_optimization_recommendations():
    """Get optimization recommendations."""
    try:
        recommendations = usage_analytics_service.optimization_engine.generate_recommendations()
        
        return jsonify({
            'success': True,
            'recommendations': [
                {
                    'id': rec.id,
                    'category': rec.category,
                    'priority': rec.priority,
                    'title': rec.title,
                    'description': rec.description,
                    'expected_impact': rec.expected_impact,
                    'implementation_effort': rec.implementation_effort,
                    'metrics_to_track': rec.metrics_to_track,
                    'timestamp': rec.timestamp.isoformat()
                }
                for rec in recommendations
            ]
        })
    except Exception as e:
        logger.error(f"Error getting optimization recommendations: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve optimization recommendations'
        }), 500

@usage_analytics_bp.route('/api/track-event', methods=['POST'])
@login_required
def track_event():
    """Track a user event."""
    try:
        data = request.get_json()
        event_type = data.get('event_type')
        
        if event_type == 'page_view':
            usage_analytics_service.track_page_view(
                user_id=str(current_user.id),
                page_url=data.get('page_url', ''),
                user_agent=request.headers.get('User-Agent', ''),
                session_id=data.get('session_id', ''),
                duration=data.get('duration')
            )
        elif event_type == 'decision_request':
            usage_analytics_service.track_decision_request(
                user_id=str(current_user.id),
                executive_type=data.get('executive_type', ''),
                session_id=data.get('session_id', ''),
                response_time=data.get('response_time', 0.0),
                success=data.get('success', True)
            )
        elif event_type == 'document_upload':
            usage_analytics_service.track_document_upload(
                user_id=str(current_user.id),
                session_id=data.get('session_id', ''),
                file_size=data.get('file_size', 0),
                file_type=data.get('file_type', ''),
                success=data.get('success', True)
            )
        else:
            return jsonify({
                'success': False,
                'error': f'Unknown event type: {event_type}'
            }), 400
        
        return jsonify({
            'success': True,
            'message': 'Event tracked successfully'
        })
    except Exception as e:
        logger.error(f"Error tracking event: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to track event'
        }), 500

@usage_analytics_bp.route('/api/report-performance-issue', methods=['POST'])
@login_required
def report_performance_issue():
    """Report a performance issue."""
    try:
        data = request.get_json()
        
        required_fields = ['issue_type', 'affected_feature', 'severity']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400
        
        issue = PerformanceBottleneck(
            issue_type=PerformanceIssue(data['issue_type']),
            affected_feature=data['affected_feature'],
            severity=data['severity'],
            frequency=data.get('frequency', 1),
            avg_impact_time=data.get('avg_impact_time', 0.0),
            affected_users=data.get('affected_users', 1),
            first_detected=datetime.now(),
            last_detected=datetime.now(),
            recommendation=data.get('recommendation', 'Investigate and optimize')
        )
        
        usage_analytics_service.usage_tracker.record_performance_issue(issue)
        
        return jsonify({
            'success': True,
            'message': 'Performance issue reported successfully'
        })
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': f'Invalid data: {str(e)}'
        }), 400
    except Exception as e:
        logger.error(f"Error reporting performance issue: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to report performance issue'
        }), 500

@usage_analytics_bp.route('/api/usage-summary')
@login_required
def get_usage_summary():
    """Get usage summary statistics."""
    try:
        # Calculate summary statistics
        events = usage_analytics_service.usage_tracker.events
        
        if not events:
            return jsonify({
                'success': True,
                'summary': {
                    'total_events': 0,
                    'active_users': 0,
                    'avg_session_duration': 0,
                    'most_popular_feature': 'None',
                    'peak_usage_hour': 0
                }
            })
        
        # Basic statistics
        total_events = len(events)
        active_users = len(set(event.user_id for event in events))
        
        # Calculate average session duration
        session_durations = []
        user_sessions = {}
        
        for event in events:
            session_key = f"{event.user_id}_{event.session_id}"
            if session_key not in user_sessions:
                user_sessions[session_key] = {'start': event.timestamp, 'end': event.timestamp}
            else:
                user_sessions[session_key]['end'] = max(user_sessions[session_key]['end'], event.timestamp)
        
        for session in user_sessions.values():
            duration = (session['end'] - session['start']).total_seconds()
            if duration > 0:
                session_durations.append(duration)
        
        avg_session_duration = sum(session_durations) / len(session_durations) if session_durations else 0
        
        # Most popular feature
        feature_usage = usage_analytics_service.usage_tracker.feature_usage
        most_popular_feature = max(feature_usage.keys(), 
                                 key=lambda k: feature_usage[k]['total_uses']) if feature_usage else 'None'
        
        # Peak usage hour
        hourly_usage = {}
        for event in events:
            hour = event.timestamp.hour
            hourly_usage[hour] = hourly_usage.get(hour, 0) + 1
        
        peak_usage_hour = max(hourly_usage.keys(), key=lambda k: hourly_usage[k]) if hourly_usage else 0
        
        return jsonify({
            'success': True,
            'summary': {
                'total_events': total_events,
                'active_users': active_users,
                'avg_session_duration': round(avg_session_duration / 60, 1),  # Convert to minutes
                'most_popular_feature': most_popular_feature,
                'peak_usage_hour': peak_usage_hour
            }
        })
    except Exception as e:
        logger.error(f"Error getting usage summary: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve usage summary'
        }), 500