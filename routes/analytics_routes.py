"""
Analytics Routes

Routes for analytics dashboard and reporting functionality.
"""

from flask import Blueprint, render_template, request, jsonify, session
from datetime import datetime, timedelta
from decimal import Decimal
import logging

from services.analytics import AnalyticsService, DateRange, AnalyticsFilters
from models import db
from auth import login_required

logger = logging.getLogger(__name__)

analytics_bp = Blueprint('analytics', __name__, url_prefix='/analytics')


@analytics_bp.route('/dashboard')
@login_required
def dashboard():
    """Main analytics dashboard page"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return render_template('login.html', error="Please log in to access analytics")
        
        return render_template('analytics/dashboard.html', user_id=user_id)
        
    except Exception as e:
        logger.error(f"Error loading analytics dashboard: {str(e)}")
        return render_template('analytics/dashboard.html', error="Error loading dashboard")


@analytics_bp.route('/api/dashboard-data')
@login_required
def get_dashboard_data():
    """API endpoint to get dashboard data"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401
        
        # Initialize analytics service
        analytics_service = AnalyticsService({}, db.session)
        
        # Get dashboard data
        dashboard_data = analytics_service.get_performance_dashboard(str(user_id))
        
        # Convert to JSON-serializable format
        response_data = {
            'key_metrics': dashboard_data.key_metrics,
            'charts': dashboard_data.charts,
            'alerts': dashboard_data.alerts,
            'recommendations': dashboard_data.recommendations
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Error getting dashboard data: {str(e)}")
        return jsonify({'error': 'Failed to load dashboard data'}), 500


@analytics_bp.route('/api/decision-analytics')
@login_required
def get_decision_analytics():
    """API endpoint to get decision analytics"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401
        
        # Parse query parameters
        days = request.args.get('days', 30, type=int)
        executive_types = request.args.getlist('executive_types')
        categories = request.args.getlist('categories')
        priorities = request.args.getlist('priorities')
        status = request.args.getlist('status')
        
        # Create date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        time_range = DateRange(start_date, end_date)
        
        # Create filters
        filters = AnalyticsFilters(
            executive_types=executive_types if executive_types else None,
            categories=categories if categories else None,
            priorities=priorities if priorities else None,
            status=status if status else None
        )
        
        # Initialize analytics service
        analytics_service = AnalyticsService({}, db.session)
        
        # Get analytics data
        analytics_data = analytics_service.generate_decision_analytics(time_range, filters)
        
        # Convert to JSON-serializable format
        response_data = {
            'total_decisions': analytics_data.total_decisions,
            'decisions_by_executive': analytics_data.decisions_by_executive,
            'decisions_by_category': analytics_data.decisions_by_category,
            'decisions_by_priority': analytics_data.decisions_by_priority,
            'average_confidence_score': analytics_data.average_confidence_score,
            'implementation_rate': analytics_data.implementation_rate,
            'effectiveness_scores': analytics_data.effectiveness_scores,
            'decisions_over_time': [
                {
                    'timestamp': point.timestamp.isoformat(),
                    'value': point.value,
                    'metadata': point.metadata
                } for point in analytics_data.decisions_over_time
            ],
            'trends': {
                key: {
                    'direction': trend.direction,
                    'rate': trend.rate,
                    'confidence': trend.confidence
                } for key, trend in analytics_data.trends.items()
            },
            'total_financial_impact': float(analytics_data.total_financial_impact),
            'roi_by_category': {k: float(v) for k, v in analytics_data.roi_by_category.items()},
            'cost_savings': float(analytics_data.cost_savings)
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Error getting decision analytics: {str(e)}")
        return jsonify({'error': 'Failed to load analytics data'}), 500


@analytics_bp.route('/api/effectiveness-report/<int:decision_id>')
@login_required
def get_effectiveness_report(decision_id):
    """API endpoint to get effectiveness report for a specific decision"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401
        
        # Initialize analytics service
        analytics_service = AnalyticsService({}, db.session)
        
        # Get effectiveness report
        effectiveness_report = analytics_service.generate_effectiveness_report(decision_id)
        
        # Convert to JSON-serializable format
        response_data = {
            'decision_id': effectiveness_report.decision_id,
            'effectiveness_score': effectiveness_report.effectiveness_score,
            'outcome_rating': effectiveness_report.outcome_rating,
            'success_probability': effectiveness_report.success_probability,
            'implementation_timeliness': effectiveness_report.implementation_timeliness,
            'financial_impact_accuracy': effectiveness_report.financial_impact_accuracy,
            'confidence_alignment': effectiveness_report.confidence_alignment,
            'overall_grade': effectiveness_report.overall_grade,
            'improvement_areas': effectiveness_report.improvement_areas,
            'tracking_timestamp': effectiveness_report.tracking_timestamp.isoformat()
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Error getting effectiveness report: {str(e)}")
        return jsonify({'error': 'Failed to load effectiveness report'}), 500


@analytics_bp.route('/api/success-rate-report')
@login_required
def get_success_rate_report():
    """API endpoint to get success rate report"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401
        
        # Parse query parameters
        days = request.args.get('days', 30, type=int)
        
        # Create date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        time_range = DateRange(start_date, end_date)
        
        # Initialize analytics service
        analytics_service = AnalyticsService({}, db.session)
        
        # Get success rate report
        report = analytics_service.generate_success_rate_report(time_range)
        
        return jsonify(report)
        
    except Exception as e:
        logger.error(f"Error getting success rate report: {str(e)}")
        return jsonify({'error': 'Failed to load success rate report'}), 500


@analytics_bp.route('/api/top-performing-decisions')
@login_required
def get_top_performing_decisions():
    """API endpoint to get top performing decisions"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401
        
        # Parse query parameters
        days = request.args.get('days', 30, type=int)
        limit = request.args.get('limit', 10, type=int)
        
        # Create date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        time_range = DateRange(start_date, end_date)
        
        # Initialize analytics service
        analytics_service = AnalyticsService({}, db.session)
        
        # Get top performing decisions
        top_decisions = analytics_service.get_top_performing_decisions(time_range, limit)
        
        return jsonify({'decisions': top_decisions})
        
    except Exception as e:
        logger.error(f"Error getting top performing decisions: {str(e)}")
        return jsonify({'error': 'Failed to load top performing decisions'}), 500


@analytics_bp.route('/api/improvement-opportunities')
@login_required
def get_improvement_opportunities():
    """API endpoint to get improvement opportunities"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401
        
        # Parse query parameters
        days = request.args.get('days', 30, type=int)
        
        # Create date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        time_range = DateRange(start_date, end_date)
        
        # Initialize analytics service
        analytics_service = AnalyticsService({}, db.session)
        
        # Get improvement opportunities
        opportunities = analytics_service.get_improvement_opportunities(time_range)
        
        return jsonify({'opportunities': opportunities})
        
    except Exception as e:
        logger.error(f"Error getting improvement opportunities: {str(e)}")
        return jsonify({'error': 'Failed to load improvement opportunities'}), 500


@analytics_bp.route('/api/record-outcome', methods=['POST'])
@login_required
def record_decision_outcome():
    """API endpoint to record decision outcome"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        decision_id = data.get('decision_id')
        outcome_rating = data.get('outcome_rating')
        outcome_notes = data.get('outcome_notes')
        financial_impact = data.get('financial_impact')
        
        if not decision_id or not outcome_rating:
            return jsonify({'error': 'Decision ID and outcome rating are required'}), 400
        
        # Convert financial impact to Decimal if provided
        if financial_impact is not None:
            financial_impact = Decimal(str(financial_impact))
        
        # Initialize analytics service
        analytics_service = AnalyticsService({}, db.session)
        
        # Record outcome
        success = analytics_service.record_decision_outcome(
            decision_id, outcome_rating, outcome_notes, financial_impact
        )
        
        if success:
            return jsonify({'message': 'Outcome recorded successfully'})
        else:
            return jsonify({'error': 'Failed to record outcome'}), 500
        
    except Exception as e:
        logger.error(f"Error recording decision outcome: {str(e)}")
        return jsonify({'error': 'Failed to record outcome'}), 500


@analytics_bp.route('/api/track-impact', methods=['POST'])
@login_required
def track_decision_impact():
    """API endpoint to track decision impact"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        decision_id = data.get('decision_id')
        impact_metrics = data.get('impact_metrics', {})
        
        if not decision_id:
            return jsonify({'error': 'Decision ID is required'}), 400
        
        # Initialize analytics service
        analytics_service = AnalyticsService({}, db.session)
        
        # Track impact
        success = analytics_service.track_decision_impact(decision_id, impact_metrics)
        
        if success:
            return jsonify({'message': 'Impact tracked successfully'})
        else:
            return jsonify({'error': 'Failed to track impact'}), 500
        
    except Exception as e:
        logger.error(f"Error tracking decision impact: {str(e)}")
        return jsonify({'error': 'Failed to track impact'}), 500


@analytics_bp.route('/reports')
@login_required
def reports():
    """Analytics reports page"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return render_template('login.html', error="Please log in to access reports")
        
        return render_template('analytics/reports.html', user_id=user_id)
        
    except Exception as e:
        logger.error(f"Error loading analytics reports: {str(e)}")
        return render_template('analytics/reports.html', error="Error loading reports")


@analytics_bp.route('/effectiveness')
@login_required
def effectiveness():
    """Decision effectiveness tracking page"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return render_template('login.html', error="Please log in to access effectiveness tracking")
        
        return render_template('analytics/effectiveness.html', user_id=user_id)
        
    except Exception as e:
        logger.error(f"Error loading effectiveness page: {str(e)}")
        return render_template('analytics/effectiveness.html', error="Error loading effectiveness tracking")