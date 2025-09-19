"""
Usage Analytics and Optimization Service.
Tracks user behavior, feature usage, and provides optimization recommendations.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict, deque, Counter
import json
import statistics
from enum import Enum
import threading
import time

logger = logging.getLogger(__name__)

class EventType(Enum):
    """Types of user events to track."""
    PAGE_VIEW = "page_view"
    DECISION_REQUEST = "decision_request"
    DOCUMENT_UPLOAD = "document_upload"
    FEEDBACK_SUBMISSION = "feedback_submission"
    COLLABORATION_ACTION = "collaboration_action"
    SEARCH_QUERY = "search_query"
    EXPORT_ACTION = "export_action"
    SETTINGS_CHANGE = "settings_change"
    ERROR_ENCOUNTERED = "error_encountered"

class PerformanceIssue(Enum):
    """Types of performance issues."""
    SLOW_RESPONSE = "slow_response"
    HIGH_ERROR_RATE = "high_error_rate"
    MEMORY_USAGE = "memory_usage"
    DATABASE_SLOW = "database_slow"
    AI_API_SLOW = "ai_api_slow"

@dataclass
class UserEvent:
    """Represents a user interaction event."""
    id: str
    user_id: str
    event_type: EventType
    page_url: str
    user_agent: str
    session_id: str
    timestamp: datetime
    duration: Optional[float] = None  # Time spent on page/action
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

@dataclass
class FeatureUsage:
    """Feature usage statistics."""
    feature_name: str
    total_uses: int
    unique_users: int
    avg_session_duration: float
    success_rate: float
    last_used: datetime
    usage_trend: float  # Positive = increasing, negative = decreasing

@dataclass
class UserBehaviorPattern:
    """User behavior analysis."""
    user_id: str
    total_sessions: int
    avg_session_duration: float
    most_used_features: List[str]
    preferred_executive: str
    peak_usage_hours: List[int]
    device_types: List[str]
    engagement_score: float  # 0-100

@dataclass
class PerformanceBottleneck:
    """Performance bottleneck identification."""
    issue_type: PerformanceIssue
    affected_feature: str
    severity: str  # 'low', 'medium', 'high', 'critical'
    frequency: int
    avg_impact_time: float
    affected_users: int
    first_detected: datetime
    last_detected: datetime
    recommendation: str

@dataclass
class OptimizationRecommendation:
    """System optimization recommendation."""
    id: str
    category: str  # 'performance', 'user_experience', 'feature_usage'
    priority: str  # 'low', 'medium', 'high', 'critical'
    title: str
    description: str
    expected_impact: str
    implementation_effort: str  # 'low', 'medium', 'high'
    metrics_to_track: List[str]
    timestamp: datetime

class UsageTracker:
    """Tracks user behavior and system usage patterns."""
    
    def __init__(self):
        self.events = deque(maxlen=50000)  # Keep last 50k events
        self.session_data = defaultdict(dict)  # Session tracking
        self.feature_usage = defaultdict(lambda: {
            'total_uses': 0,
            'unique_users': set(),
            'durations': [],
            'success_count': 0,
            'error_count': 0,
            'last_used': None
        })
        self.performance_issues = deque(maxlen=1000)
        self._lock = threading.Lock()
    
    def track_event(self, event: UserEvent):
        """Track a user event."""
        with self._lock:
            self.events.append(event)
            
            # Update session data
            session_key = f"{event.user_id}_{event.session_id}"
            if session_key not in self.session_data:
                self.session_data[session_key] = {
                    'start_time': event.timestamp,
                    'last_activity': event.timestamp,
                    'events': [],
                    'pages_visited': set(),
                    'features_used': set()
                }
            
            session = self.session_data[session_key]
            session['last_activity'] = event.timestamp
            session['events'].append(event)
            session['pages_visited'].add(event.page_url)
            
            # Track feature usage
            feature_name = self._extract_feature_name(event)
            if feature_name:
                session['features_used'].add(feature_name)
                self._update_feature_usage(feature_name, event)
        
        logger.debug(f"Tracked event: {event.event_type.value} for user {event.user_id}")
    
    def _extract_feature_name(self, event: UserEvent) -> Optional[str]:
        """Extract feature name from event."""
        if event.event_type == EventType.DECISION_REQUEST:
            return f"ai_executive_{event.metadata.get('executive_type', 'unknown')}"
        elif event.event_type == EventType.DOCUMENT_UPLOAD:
            return "document_processing"
        elif event.event_type == EventType.COLLABORATION_ACTION:
            return "collaboration"
        elif event.event_type == EventType.FEEDBACK_SUBMISSION:
            return "feedback_system"
        elif event.page_url:
            # Extract feature from URL
            if '/analytics' in event.page_url:
                return "analytics_dashboard"
            elif '/monitoring' in event.page_url:
                return "system_monitoring"
            elif '/ai-quality' in event.page_url:
                return "quality_tracking"
        
        return None
    
    def _update_feature_usage(self, feature_name: str, event: UserEvent):
        """Update feature usage statistics."""
        usage = self.feature_usage[feature_name]
        usage['total_uses'] += 1
        usage['unique_users'].add(event.user_id)
        usage['last_used'] = event.timestamp
        
        if event.duration:
            usage['durations'].append(event.duration)
        
        # Track success/error based on event metadata
        if event.metadata:
            if event.metadata.get('success', True):
                usage['success_count'] += 1
            else:
                usage['error_count'] += 1
    
    def get_feature_usage_stats(self, time_range: Optional[timedelta] = None) -> List[FeatureUsage]:
        """Get feature usage statistics."""
        if time_range is None:
            time_range = timedelta(days=30)
        
        cutoff_time = datetime.now() - time_range
        stats = []
        
        for feature_name, usage_data in self.feature_usage.items():
            if usage_data['last_used'] and usage_data['last_used'] >= cutoff_time:
                # Calculate trend (simplified)
                trend = self._calculate_usage_trend(feature_name, time_range)
                
                # Calculate success rate
                total_attempts = usage_data['success_count'] + usage_data['error_count']
                success_rate = (usage_data['success_count'] / total_attempts * 100) if total_attempts > 0 else 100
                
                # Calculate average duration
                avg_duration = statistics.mean(usage_data['durations']) if usage_data['durations'] else 0
                
                stats.append(FeatureUsage(
                    feature_name=feature_name,
                    total_uses=usage_data['total_uses'],
                    unique_users=len(usage_data['unique_users']),
                    avg_session_duration=avg_duration,
                    success_rate=success_rate,
                    last_used=usage_data['last_used'],
                    usage_trend=trend
                ))
        
        return sorted(stats, key=lambda x: x.total_uses, reverse=True)
    
    def _calculate_usage_trend(self, feature_name: str, time_range: timedelta) -> float:
        """Calculate usage trend for a feature."""
        cutoff_time = datetime.now() - time_range
        half_time = datetime.now() - (time_range / 2)
        
        # Count usage in first half vs second half of time range
        first_half = sum(1 for event in self.events 
                        if cutoff_time <= event.timestamp < half_time and 
                        self._extract_feature_name(event) == feature_name)
        
        second_half = sum(1 for event in self.events 
                         if half_time <= event.timestamp and 
                         self._extract_feature_name(event) == feature_name)
        
        if first_half == 0:
            return 1.0 if second_half > 0 else 0.0
        
        return (second_half - first_half) / first_half
    
    def get_user_behavior_patterns(self, user_id: Optional[str] = None) -> List[UserBehaviorPattern]:
        """Analyze user behavior patterns."""
        patterns = []
        
        # Group events by user
        user_events = defaultdict(list)
        for event in self.events:
            if user_id is None or event.user_id == user_id:
                user_events[event.user_id].append(event)
        
        for uid, events in user_events.items():
            if len(events) < 5:  # Skip users with too few events
                continue
            
            # Analyze sessions
            sessions = self._group_events_by_session(events)
            
            # Calculate metrics
            total_sessions = len(sessions)
            session_durations = []
            all_features = []
            executive_usage = Counter()
            hourly_usage = Counter()
            device_types = Counter()
            
            for session_events in sessions.values():
                if len(session_events) > 1:
                    duration = (session_events[-1].timestamp - session_events[0].timestamp).total_seconds()
                    session_durations.append(duration)
                
                for event in session_events:
                    feature = self._extract_feature_name(event)
                    if feature:
                        all_features.append(feature)
                    
                    if event.metadata and 'executive_type' in event.metadata:
                        executive_usage[event.metadata['executive_type']] += 1
                    
                    hourly_usage[event.timestamp.hour] += 1
                    
                    # Extract device type from user agent (simplified)
                    if 'Mobile' in event.user_agent:
                        device_types['mobile'] += 1
                    elif 'Tablet' in event.user_agent:
                        device_types['tablet'] += 1
                    else:
                        device_types['desktop'] += 1
            
            # Calculate engagement score (0-100)
            engagement_score = min(100, (
                len(events) * 2 +  # Event frequency
                total_sessions * 5 +  # Session frequency
                len(set(all_features)) * 10  # Feature diversity
            ))
            
            patterns.append(UserBehaviorPattern(
                user_id=uid,
                total_sessions=total_sessions,
                avg_session_duration=statistics.mean(session_durations) if session_durations else 0,
                most_used_features=list(Counter(all_features).most_common(5)),
                preferred_executive=executive_usage.most_common(1)[0][0] if executive_usage else 'none',
                peak_usage_hours=list(hourly_usage.most_common(3)),
                device_types=list(device_types.keys()),
                engagement_score=engagement_score
            ))
        
        return sorted(patterns, key=lambda x: x.engagement_score, reverse=True)
    
    def _group_events_by_session(self, events: List[UserEvent]) -> Dict[str, List[UserEvent]]:
        """Group events by session ID."""
        sessions = defaultdict(list)
        for event in events:
            sessions[event.session_id].append(event)
        
        # Sort events within each session by timestamp
        for session_events in sessions.values():
            session_events.sort(key=lambda x: x.timestamp)
        
        return sessions
    
    def record_performance_issue(self, issue: PerformanceBottleneck):
        """Record a performance issue."""
        with self._lock:
            self.performance_issues.append(issue)
        
        logger.warning(f"Performance issue recorded: {issue.issue_type.value} in {issue.affected_feature}")
    
    def get_performance_bottlenecks(self, time_range: Optional[timedelta] = None) -> List[PerformanceBottleneck]:
        """Get performance bottlenecks within time range."""
        if time_range is None:
            time_range = timedelta(days=7)
        
        cutoff_time = datetime.now() - time_range
        
        return [issue for issue in self.performance_issues 
                if issue.last_detected >= cutoff_time]

class OptimizationEngine:
    """Generates optimization recommendations based on usage analytics."""
    
    def __init__(self, usage_tracker: UsageTracker):
        self.usage_tracker = usage_tracker
    
    def generate_recommendations(self) -> List[OptimizationRecommendation]:
        """Generate optimization recommendations."""
        recommendations = []
        
        # Analyze feature usage
        feature_stats = self.usage_tracker.get_feature_usage_stats()
        recommendations.extend(self._analyze_feature_usage(feature_stats))
        
        # Analyze user behavior
        behavior_patterns = self.usage_tracker.get_user_behavior_patterns()
        recommendations.extend(self._analyze_user_behavior(behavior_patterns))
        
        # Analyze performance issues
        performance_issues = self.usage_tracker.get_performance_bottlenecks()
        recommendations.extend(self._analyze_performance_issues(performance_issues))
        
        return sorted(recommendations, key=lambda x: self._get_priority_score(x.priority), reverse=True)
    
    def _analyze_feature_usage(self, feature_stats: List[FeatureUsage]) -> List[OptimizationRecommendation]:
        """Analyze feature usage and generate recommendations."""
        recommendations = []
        
        for feature in feature_stats:
            # Low usage features
            if feature.total_uses < 10 and feature.unique_users < 5:
                recommendations.append(OptimizationRecommendation(
                    id=f"low_usage_{feature.feature_name}",
                    category="feature_usage",
                    priority="medium",
                    title=f"Low usage of {feature.feature_name}",
                    description=f"Feature has only {feature.total_uses} uses by {feature.unique_users} users",
                    expected_impact="Improve feature adoption or consider removal",
                    implementation_effort="medium",
                    metrics_to_track=["feature_usage", "user_engagement"],
                    timestamp=datetime.now()
                ))
            
            # High error rate features
            if feature.success_rate < 80:
                recommendations.append(OptimizationRecommendation(
                    id=f"high_error_{feature.feature_name}",
                    category="performance",
                    priority="high",
                    title=f"High error rate in {feature.feature_name}",
                    description=f"Feature has {feature.success_rate:.1f}% success rate",
                    expected_impact="Improve user experience and reduce frustration",
                    implementation_effort="high",
                    metrics_to_track=["error_rate", "user_satisfaction"],
                    timestamp=datetime.now()
                ))
            
            # Declining usage trend
            if feature.usage_trend < -0.3:
                recommendations.append(OptimizationRecommendation(
                    id=f"declining_usage_{feature.feature_name}",
                    category="user_experience",
                    priority="medium",
                    title=f"Declining usage of {feature.feature_name}",
                    description=f"Feature usage has declined by {abs(feature.usage_trend)*100:.1f}%",
                    expected_impact="Investigate and improve feature to regain user interest",
                    implementation_effort="medium",
                    metrics_to_track=["feature_usage", "user_feedback"],
                    timestamp=datetime.now()
                ))
        
        return recommendations
    
    def _analyze_user_behavior(self, behavior_patterns: List[UserBehaviorPattern]) -> List[OptimizationRecommendation]:
        """Analyze user behavior and generate recommendations."""
        recommendations = []
        
        if not behavior_patterns:
            return recommendations
        
        # Low engagement users
        low_engagement_users = [p for p in behavior_patterns if p.engagement_score < 30]
        if len(low_engagement_users) > len(behavior_patterns) * 0.3:  # More than 30% low engagement
            recommendations.append(OptimizationRecommendation(
                id="low_user_engagement",
                category="user_experience",
                priority="high",
                title="High percentage of low-engagement users",
                description=f"{len(low_engagement_users)} users have low engagement scores",
                expected_impact="Improve onboarding and user experience",
                implementation_effort="high",
                metrics_to_track=["user_engagement", "session_duration", "feature_adoption"],
                timestamp=datetime.now()
            ))
        
        # Short session durations
        avg_session_duration = statistics.mean([p.avg_session_duration for p in behavior_patterns])
        if avg_session_duration < 300:  # Less than 5 minutes
            recommendations.append(OptimizationRecommendation(
                id="short_sessions",
                category="user_experience",
                priority="medium",
                title="Users have short session durations",
                description=f"Average session duration is {avg_session_duration/60:.1f} minutes",
                expected_impact="Increase user engagement and value delivery",
                implementation_effort="medium",
                metrics_to_track=["session_duration", "page_views", "feature_usage"],
                timestamp=datetime.now()
            ))
        
        return recommendations
    
    def _analyze_performance_issues(self, performance_issues: List[PerformanceBottleneck]) -> List[OptimizationRecommendation]:
        """Analyze performance issues and generate recommendations."""
        recommendations = []
        
        # Group issues by type
        issue_groups = defaultdict(list)
        for issue in performance_issues:
            issue_groups[issue.issue_type].append(issue)
        
        for issue_type, issues in issue_groups.items():
            if len(issues) > 5:  # Frequent issues
                total_affected_users = sum(issue.affected_users for issue in issues)
                avg_impact_time = statistics.mean([issue.avg_impact_time for issue in issues])
                
                recommendations.append(OptimizationRecommendation(
                    id=f"frequent_{issue_type.value}",
                    category="performance",
                    priority="high" if total_affected_users > 10 else "medium",
                    title=f"Frequent {issue_type.value.replace('_', ' ')} issues",
                    description=f"{len(issues)} instances affecting {total_affected_users} users",
                    expected_impact=f"Reduce average impact time from {avg_impact_time:.1f}s",
                    implementation_effort="high",
                    metrics_to_track=["response_time", "error_rate", "user_satisfaction"],
                    timestamp=datetime.now()
                ))
        
        return recommendations
    
    def _get_priority_score(self, priority: str) -> int:
        """Get numeric score for priority."""
        priority_scores = {
            'critical': 4,
            'high': 3,
            'medium': 2,
            'low': 1
        }
        return priority_scores.get(priority, 0)

class UsageAnalyticsService:
    """Main service for usage analytics and optimization."""
    
    def __init__(self):
        self.usage_tracker = UsageTracker()
        self.optimization_engine = OptimizationEngine(self.usage_tracker)
    
    def track_page_view(self, user_id: str, page_url: str, user_agent: str, 
                       session_id: str, duration: Optional[float] = None):
        """Track a page view event."""
        event = UserEvent(
            id=f"pv_{int(datetime.now().timestamp())}_{user_id}",
            user_id=user_id,
            event_type=EventType.PAGE_VIEW,
            page_url=page_url,
            user_agent=user_agent,
            session_id=session_id,
            timestamp=datetime.now(),
            duration=duration
        )
        self.usage_tracker.track_event(event)
    
    def track_decision_request(self, user_id: str, executive_type: str, 
                              session_id: str, response_time: float, 
                              success: bool = True):
        """Track an AI decision request."""
        event = UserEvent(
            id=f"dr_{int(datetime.now().timestamp())}_{user_id}",
            user_id=user_id,
            event_type=EventType.DECISION_REQUEST,
            page_url="/executive",
            user_agent="",
            session_id=session_id,
            timestamp=datetime.now(),
            duration=response_time,
            metadata={
                'executive_type': executive_type,
                'success': success
            }
        )
        self.usage_tracker.track_event(event)
    
    def track_document_upload(self, user_id: str, session_id: str, 
                             file_size: int, file_type: str, success: bool = True):
        """Track a document upload event."""
        event = UserEvent(
            id=f"du_{int(datetime.now().timestamp())}_{user_id}",
            user_id=user_id,
            event_type=EventType.DOCUMENT_UPLOAD,
            page_url="/upload",
            user_agent="",
            session_id=session_id,
            timestamp=datetime.now(),
            metadata={
                'file_size': file_size,
                'file_type': file_type,
                'success': success
            }
        )
        self.usage_tracker.track_event(event)
    
    def get_usage_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive usage analytics data."""
        feature_stats = self.usage_tracker.get_feature_usage_stats()
        behavior_patterns = self.usage_tracker.get_user_behavior_patterns()
        performance_issues = self.usage_tracker.get_performance_bottlenecks()
        recommendations = self.optimization_engine.generate_recommendations()
        
        return {
            'feature_usage': [asdict(stat) for stat in feature_stats],
            'user_behavior': [asdict(pattern) for pattern in behavior_patterns[:10]],  # Top 10
            'performance_issues': [asdict(issue) for issue in performance_issues],
            'recommendations': [asdict(rec) for rec in recommendations],
            'summary': {
                'total_events': len(self.usage_tracker.events),
                'active_users': len(set(event.user_id for event in self.usage_tracker.events)),
                'total_features': len(self.usage_tracker.feature_usage),
                'critical_issues': len([r for r in recommendations if r.priority == 'critical'])
            }
        }

# Global usage analytics service instance
usage_analytics_service = UsageAnalyticsService()