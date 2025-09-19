"""
Routes for AI response quality tracking and feedback collection.
"""

from flask import Blueprint, request, jsonify, render_template
from flask_login import login_required, current_user
from datetime import datetime, timedelta
import logging

from services.ai_quality_tracking import feedback_service, ai_quality_tracker

logger = logging.getLogger(__name__)

ai_quality_bp = Blueprint('ai_quality', __name__, url_prefix='/ai-quality')

@ai_quality_bp.route('/feedback/<decision_id>')
@login_required
def feedback_form(decision_id):
    """Render feedback form for a specific decision."""
    form_data = feedback_service.get_feedback_form_data(decision_id)
    return render_template('ai_quality/feedback_form.html', 
                         decision_id=decision_id, 
                         form_data=form_data)

@ai_quality_bp.route('/api/feedback', methods=['POST'])
@login_required
def submit_feedback():
    """Submit user feedback for an AI response."""
    try:
        data = request.get_json()
        
        required_fields = ['decision_id', 'executive_type', 'rating']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400
        
        success = feedback_service.submit_feedback(
            decision_id=data['decision_id'],
            user_id=str(current_user.id),
            executive_type=data['executive_type'],
            rating=int(data['rating']),
            accuracy_rating=int(data.get('accuracy_rating')) if data.get('accuracy_rating') else None,
            feedback_text=data.get('feedback_text'),
            response_time=float(data.get('response_time', 0.0))
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Feedback submitted successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to submit feedback'
            }), 500
            
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': f'Invalid data: {str(e)}'
        }), 400
    except Exception as e:
        logger.error(f"Error submitting feedback: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@ai_quality_bp.route('/api/metrics')
@login_required
def get_quality_metrics():
    """Get AI response quality metrics."""
    try:
        # Get query parameters
        executive_type = request.args.get('executive_type')
        days = request.args.get('days', 30, type=int)
        
        time_range = timedelta(days=days)
        metrics = ai_quality_tracker.get_quality_metrics(
            executive_type=executive_type,
            time_range=time_range
        )
        
        return jsonify({
            'success': True,
            'metrics': {
                'total_responses': metrics.total_responses,
                'average_rating': round(metrics.average_rating, 2),
                'average_accuracy': round(metrics.average_accuracy, 2),
                'response_time_avg': round(metrics.response_time_avg, 2),
                'satisfaction_distribution': metrics.satisfaction_distribution,
                'accuracy_distribution': metrics.accuracy_distribution,
                'improvement_trend': round(metrics.improvement_trend, 2)
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting quality metrics: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve quality metrics'
        }), 500

@ai_quality_bp.route('/api/executive-comparison')
@login_required
def get_executive_comparison():
    """Get performance comparison across executive types."""
    try:
        comparison = ai_quality_tracker.get_executive_performance_comparison()
        
        # Format the response
        formatted_comparison = {}
        for exec_type, metrics in comparison.items():
            formatted_comparison[exec_type] = {
                'total_responses': metrics.total_responses,
                'average_rating': round(metrics.average_rating, 2),
                'average_accuracy': round(metrics.average_accuracy, 2),
                'response_time_avg': round(metrics.response_time_avg, 2),
                'improvement_trend': round(metrics.improvement_trend, 2)
            }
        
        return jsonify({
            'success': True,
            'comparison': formatted_comparison
        })
        
    except Exception as e:
        logger.error(f"Error getting executive comparison: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve executive comparison'
        }), 500

@ai_quality_bp.route('/api/low-quality-responses')
@login_required
def get_low_quality_responses():
    """Get responses with low quality ratings."""
    try:
        threshold = request.args.get('threshold', 2.5, type=float)
        limit = request.args.get('limit', 50, type=int)
        
        low_quality = ai_quality_tracker.get_low_quality_responses(
            threshold=threshold,
            limit=limit
        )
        
        # Format the response
        formatted_responses = []
        for feedback in low_quality:
            formatted_responses.append({
                'id': feedback.id,
                'decision_id': feedback.decision_id,
                'executive_type': feedback.executive_type,
                'rating': feedback.rating.value,
                'rating_name': feedback.rating.name,
                'accuracy_rating': feedback.accuracy_rating.value if feedback.accuracy_rating else None,
                'feedback_text': feedback.feedback_text,
                'timestamp': feedback.timestamp.isoformat(),
                'response_time': feedback.response_time
            })
        
        return jsonify({
            'success': True,
            'low_quality_responses': formatted_responses
        })
        
    except Exception as e:
        logger.error(f"Error getting low quality responses: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve low quality responses'
        }), 500

@ai_quality_bp.route('/api/recommendations')
@login_required
def get_improvement_recommendations():
    """Get recommendations for improving AI response quality."""
    try:
        recommendations = ai_quality_tracker.get_improvement_recommendations()
        
        return jsonify({
            'success': True,
            'recommendations': recommendations
        })
        
    except Exception as e:
        logger.error(f"Error getting recommendations: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve recommendations'
        }), 500

@ai_quality_bp.route('/api/model-performance')
@login_required
def get_model_performance():
    """Get AI model performance metrics."""
    try:
        model_name = request.args.get('model_name')
        performance = ai_quality_tracker.get_model_performance(model_name)
        
        # Format the response
        formatted_performance = {}
        for name, perf in performance.items():
            if perf:  # Check if performance data exists
                formatted_performance[name] = {
                    'total_requests': perf.total_requests,
                    'average_response_time': round(perf.average_response_time, 2),
                    'success_rate': round(perf.success_rate, 2),
                    'error_rate': round(perf.error_rate, 2),
                    'cost_per_request': round(perf.cost_per_request, 4),
                    'quality_score': round(perf.quality_score, 2),
                    'last_updated': perf.last_updated.isoformat()
                }
        
        return jsonify({
            'success': True,
            'model_performance': formatted_performance
        })
        
    except Exception as e:
        logger.error(f"Error getting model performance: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve model performance'
        }), 500

@ai_quality_bp.route('/dashboard')
@login_required
def quality_dashboard():
    """Render the AI quality dashboard."""
    return render_template('ai_quality/dashboard.html')

@ai_quality_bp.route('/api/quality-trends')
@login_required
def get_quality_trends():
    """Get quality trends over time."""
    try:
        executive_type = request.args.get('executive_type')
        days = request.args.get('days', 30, type=int)
        
        # Get trend data from quality tracker
        if executive_type:
            trends = {executive_type: ai_quality_tracker.quality_trends.get(executive_type, [])}
        else:
            trends = dict(ai_quality_tracker.quality_trends)
        
        # Filter by time range
        cutoff_time = datetime.now() - timedelta(days=days)
        filtered_trends = {}
        
        for exec_type, trend_data in trends.items():
            filtered_data = [
                entry for entry in trend_data
                if entry['timestamp'] >= cutoff_time
            ]
            if filtered_data:
                filtered_trends[exec_type] = filtered_data
        
        return jsonify({
            'success': True,
            'trends': filtered_trends
        })
        
    except Exception as e:
        logger.error(f"Error getting quality trends: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve quality trends'
        }), 500