"""
AI Response Quality Tracking Service.
Tracks user satisfaction, response accuracy, and AI model performance.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import json
import statistics
from enum import Enum

logger = logging.getLogger(__name__)

class ResponseRating(Enum):
    """User satisfaction ratings for AI responses."""
    VERY_POOR = 1
    POOR = 2
    AVERAGE = 3
    GOOD = 4
    EXCELLENT = 5

class AccuracyLevel(Enum):
    """AI response accuracy levels."""
    INACCURATE = 1
    PARTIALLY_ACCURATE = 2
    MOSTLY_ACCURATE = 3
    ACCURATE = 4
    HIGHLY_ACCURATE = 5

@dataclass
class ResponseFeedback:
    """User feedback for an AI response."""
    id: str
    decision_id: str
    user_id: str
    executive_type: str  # 'ceo', 'cto', 'cfo'
    rating: ResponseRating
    accuracy_rating: Optional[AccuracyLevel] = None
    feedback_text: Optional[str] = None
    response_time: float = 0.0
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

@dataclass
class ResponseMetrics:
    """Metrics for AI response quality."""
    total_responses: int
    average_rating: float
    average_accuracy: float
    response_time_avg: float
    satisfaction_distribution: Dict[str, int]
    accuracy_distribution: Dict[str, int]
    improvement_trend: float  # Positive = improving, negative = declining

@dataclass
class ModelPerformance:
    """Performance metrics for AI models."""
    model_name: str
    total_requests: int
    average_response_time: float
    success_rate: float
    error_rate: float
    cost_per_request: float
    quality_score: float
    last_updated: datetime

class AIQualityTracker:
    """Tracks AI response quality and user satisfaction."""
    
    def __init__(self):
        self.feedback_history = deque(maxlen=10000)  # Keep last 10k feedback entries
        self.response_times = defaultdict(list)  # By executive type
        self.model_performance = {}
        self.quality_trends = defaultdict(list)
        
    def record_feedback(self, feedback: ResponseFeedback):
        """Record user feedback for an AI response."""
        self.feedback_history.append(feedback)
        
        # Update quality trends
        self.quality_trends[feedback.executive_type].append({
            'timestamp': feedback.timestamp,
            'rating': feedback.rating.value,
            'accuracy': feedback.accuracy_rating.value if feedback.accuracy_rating else None
        })
        
        # Keep only last 100 entries per executive type
        if len(self.quality_trends[feedback.executive_type]) > 100:
            self.quality_trends[feedback.executive_type].pop(0)
        
        logger.info(f"Recorded feedback for {feedback.executive_type}: {feedback.rating.name}")
    
    def record_response_time(self, executive_type: str, response_time: float):
        """Record response time for an executive type."""
        self.response_times[executive_type].append(response_time)
        
        # Keep only last 100 response times
        if len(self.response_times[executive_type]) > 100:
            self.response_times[executive_type].pop(0)
    
    def get_quality_metrics(self, 
                           executive_type: Optional[str] = None,
                           time_range: Optional[timedelta] = None) -> ResponseMetrics:
        """Get quality metrics for responses."""
        if time_range is None:
            time_range = timedelta(days=30)  # Default to last 30 days
        
        cutoff_time = datetime.now() - time_range
        
        # Filter feedback by time range and executive type
        filtered_feedback = [
            f for f in self.feedback_history
            if f.timestamp >= cutoff_time and 
            (executive_type is None or f.executive_type == executive_type)
        ]
        
        if not filtered_feedback:
            return ResponseMetrics(
                total_responses=0,
                average_rating=0.0,
                average_accuracy=0.0,
                response_time_avg=0.0,
                satisfaction_distribution={},
                accuracy_distribution={},
                improvement_trend=0.0
            )
        
        # Calculate metrics
        ratings = [f.rating.value for f in filtered_feedback]
        accuracy_ratings = [f.accuracy_rating.value for f in filtered_feedback 
                          if f.accuracy_rating is not None]
        response_times = [f.response_time for f in filtered_feedback if f.response_time > 0]
        
        # Satisfaction distribution
        satisfaction_dist = defaultdict(int)
        for rating in ratings:
            satisfaction_dist[ResponseRating(rating).name] += 1
        
        # Accuracy distribution
        accuracy_dist = defaultdict(int)
        for rating in accuracy_ratings:
            accuracy_dist[AccuracyLevel(rating).name] += 1
        
        # Calculate improvement trend (last 10 vs previous 10)
        improvement_trend = self._calculate_improvement_trend(filtered_feedback)
        
        return ResponseMetrics(
            total_responses=len(filtered_feedback),
            average_rating=statistics.mean(ratings),
            average_accuracy=statistics.mean(accuracy_ratings) if accuracy_ratings else 0.0,
            response_time_avg=statistics.mean(response_times) if response_times else 0.0,
            satisfaction_distribution=dict(satisfaction_dist),
            accuracy_distribution=dict(accuracy_dist),
            improvement_trend=improvement_trend
        )
    
    def _calculate_improvement_trend(self, feedback_list: List[ResponseFeedback]) -> float:
        """Calculate improvement trend based on recent vs older feedback."""
        if len(feedback_list) < 20:  # Need at least 20 data points
            return 0.0
        
        # Sort by timestamp
        sorted_feedback = sorted(feedback_list, key=lambda x: x.timestamp)
        
        # Compare last 10 vs previous 10
        recent_ratings = [f.rating.value for f in sorted_feedback[-10:]]
        older_ratings = [f.rating.value for f in sorted_feedback[-20:-10]]
        
        recent_avg = statistics.mean(recent_ratings)
        older_avg = statistics.mean(older_ratings)
        
        return recent_avg - older_avg
    
    def get_executive_performance_comparison(self) -> Dict[str, ResponseMetrics]:
        """Compare performance across different executive types."""
        executive_types = ['ceo', 'cto', 'cfo']
        comparison = {}
        
        for exec_type in executive_types:
            comparison[exec_type] = self.get_quality_metrics(executive_type=exec_type)
        
        return comparison
    
    def get_low_quality_responses(self, 
                                 threshold: float = 2.5,
                                 limit: int = 50) -> List[ResponseFeedback]:
        """Get responses with low quality ratings for analysis."""
        low_quality = [
            f for f in self.feedback_history
            if f.rating.value <= threshold
        ]
        
        # Sort by timestamp (most recent first) and limit
        low_quality.sort(key=lambda x: x.timestamp, reverse=True)
        return low_quality[:limit]
    
    def get_improvement_recommendations(self) -> List[Dict[str, Any]]:
        """Generate recommendations for improving AI response quality."""
        recommendations = []
        
        # Analyze performance by executive type
        performance = self.get_executive_performance_comparison()
        
        for exec_type, metrics in performance.items():
            if metrics.total_responses == 0:
                continue
                
            # Low satisfaction recommendation
            if metrics.average_rating < 3.0:
                recommendations.append({
                    'type': 'low_satisfaction',
                    'executive_type': exec_type,
                    'priority': 'high',
                    'message': f'{exec_type.upper()} responses have low satisfaction ({metrics.average_rating:.1f}/5)',
                    'suggestion': 'Review and improve prompts, add more context, or retrain model'
                })
            
            # Low accuracy recommendation
            if metrics.average_accuracy < 3.0 and metrics.average_accuracy > 0:
                recommendations.append({
                    'type': 'low_accuracy',
                    'executive_type': exec_type,
                    'priority': 'high',
                    'message': f'{exec_type.upper()} responses have low accuracy ({metrics.average_accuracy:.1f}/5)',
                    'suggestion': 'Improve knowledge base, update training data, or enhance fact-checking'
                })
            
            # Slow response time recommendation
            if metrics.response_time_avg > 5.0:
                recommendations.append({
                    'type': 'slow_response',
                    'executive_type': exec_type,
                    'priority': 'medium',
                    'message': f'{exec_type.upper()} responses are slow ({metrics.response_time_avg:.1f}s)',
                    'suggestion': 'Optimize prompts, use faster model, or implement caching'
                })
            
            # Declining trend recommendation
            if metrics.improvement_trend < -0.5:
                recommendations.append({
                    'type': 'declining_quality',
                    'executive_type': exec_type,
                    'priority': 'medium',
                    'message': f'{exec_type.upper()} quality is declining (trend: {metrics.improvement_trend:.2f})',
                    'suggestion': 'Investigate recent changes, update prompts, or retrain model'
                })
        
        return recommendations
    
    def record_model_performance(self, performance: ModelPerformance):
        """Record performance metrics for an AI model."""
        self.model_performance[performance.model_name] = performance
        logger.info(f"Updated performance for model {performance.model_name}")
    
    def get_model_performance(self, model_name: Optional[str] = None) -> Dict[str, ModelPerformance]:
        """Get performance metrics for AI models."""
        if model_name:
            return {model_name: self.model_performance.get(model_name)}
        return self.model_performance.copy()

class FeedbackCollectionService:
    """Service for collecting user feedback on AI responses."""
    
    def __init__(self, quality_tracker: AIQualityTracker):
        self.quality_tracker = quality_tracker
    
    def submit_feedback(self, 
                       decision_id: str,
                       user_id: str,
                       executive_type: str,
                       rating: int,
                       accuracy_rating: Optional[int] = None,
                       feedback_text: Optional[str] = None,
                       response_time: float = 0.0) -> bool:
        """Submit user feedback for an AI response."""
        try:
            feedback = ResponseFeedback(
                id=f"feedback_{decision_id}_{int(datetime.now().timestamp())}",
                decision_id=decision_id,
                user_id=user_id,
                executive_type=executive_type,
                rating=ResponseRating(rating),
                accuracy_rating=AccuracyLevel(accuracy_rating) if accuracy_rating else None,
                feedback_text=feedback_text,
                response_time=response_time
            )
            
            self.quality_tracker.record_feedback(feedback)
            return True
            
        except (ValueError, Exception) as e:
            logger.error(f"Error submitting feedback: {str(e)}")
            return False
    
    def get_feedback_form_data(self, decision_id: str) -> Dict[str, Any]:
        """Get data needed for feedback form."""
        return {
            'decision_id': decision_id,
            'rating_options': [
                {'value': r.value, 'label': r.name.replace('_', ' ').title()}
                for r in ResponseRating
            ],
            'accuracy_options': [
                {'value': a.value, 'label': a.name.replace('_', ' ').title()}
                for a in AccuracyLevel
            ]
        }

# Global quality tracker instance
ai_quality_tracker = AIQualityTracker()
feedback_service = FeedbackCollectionService(ai_quality_tracker)