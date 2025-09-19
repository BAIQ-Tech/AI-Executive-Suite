#!/usr/bin/env python3
"""
Simple test for usage analytics functionality.
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from services.usage_analytics import (
    UsageAnalyticsService, UsageTracker, OptimizationEngine,
    UserEvent, EventType, PerformanceBottleneck, PerformanceIssue
)
from datetime import datetime, timedelta

def test_event_tracking():
    """Test basic event tracking functionality."""
    print("Testing Event Tracking...")
    
    service = UsageAnalyticsService()
    
    # Track various events
    service.track_page_view(
        user_id="user_1",
        page_url="/dashboard",
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        session_id="session_1",
        duration=30.5
    )
    
    service.track_decision_request(
        user_id="user_1",
        executive_type="ceo",
        session_id="session_1",
        response_time=2.5,
        success=True
    )
    
    service.track_document_upload(
        user_id="user_2",
        session_id="session_2",
        file_size=1024000,
        file_type="pdf",
        success=True
    )
    
    print(f"✓ Total events tracked: {len(service.usage_tracker.events)}")
    print(f"✓ Feature usage data: {len(service.usage_tracker.feature_usage)} features")
    
    return service

def test_feature_usage_stats(service):
    """Test feature usage statistics."""
    print("\nTesting Feature Usage Stats...")
    
    feature_stats = service.usage_tracker.get_feature_usage_stats()
    
    print(f"✓ Feature statistics generated: {len(feature_stats)} features")
    
    for stat in feature_stats:
        print(f"  - {stat.feature_name}: {stat.total_uses} uses, {stat.unique_users} users")
    
    return True

def test_user_behavior_analysis(service):
    """Test user behavior pattern analysis."""
    print("\nTesting User Behavior Analysis...")
    
    # Add more events for better analysis
    for i in range(5):
        service.track_page_view(
            user_id="user_1",
            page_url=f"/page_{i}",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            session_id="session_1",
            duration=10.0 + i
        )
    
    behavior_patterns = service.usage_tracker.get_user_behavior_patterns()
    
    print(f"✓ User behavior patterns analyzed: {len(behavior_patterns)} users")
    
    for pattern in behavior_patterns:
        print(f"  - User {pattern.user_id}: {pattern.total_sessions} sessions, "
              f"engagement score: {pattern.engagement_score:.1f}")
    
    return True

def test_performance_issue_tracking(service):
    """Test performance issue tracking."""
    print("\nTesting Performance Issue Tracking...")
    
    # Report some performance issues
    issue1 = PerformanceBottleneck(
        issue_type=PerformanceIssue.SLOW_RESPONSE,
        affected_feature="ai_executive_ceo",
        severity="medium",
        frequency=3,
        avg_impact_time=5.2,
        affected_users=2,
        first_detected=datetime.now() - timedelta(hours=2),
        last_detected=datetime.now(),
        recommendation="Optimize AI API calls and implement caching"
    )
    
    issue2 = PerformanceBottleneck(
        issue_type=PerformanceIssue.HIGH_ERROR_RATE,
        affected_feature="document_processing",
        severity="high",
        frequency=5,
        avg_impact_time=0.0,
        affected_users=3,
        first_detected=datetime.now() - timedelta(hours=1),
        last_detected=datetime.now(),
        recommendation="Fix document parsing errors and improve validation"
    )
    
    service.usage_tracker.record_performance_issue(issue1)
    service.usage_tracker.record_performance_issue(issue2)
    
    performance_issues = service.usage_tracker.get_performance_bottlenecks()
    
    print(f"✓ Performance issues tracked: {len(performance_issues)}")
    
    for issue in performance_issues:
        print(f"  - {issue.issue_type.value} in {issue.affected_feature}: {issue.severity} severity")
    
    return True

def test_optimization_recommendations(service):
    """Test optimization recommendation generation."""
    print("\nTesting Optimization Recommendations...")
    
    recommendations = service.optimization_engine.generate_recommendations()
    
    print(f"✓ Optimization recommendations generated: {len(recommendations)}")
    
    for rec in recommendations:
        print(f"  - {rec.priority.upper()}: {rec.title}")
        print(f"    {rec.description}")
    
    return True

def test_dashboard_data(service):
    """Test dashboard data compilation."""
    print("\nTesting Dashboard Data...")
    
    dashboard_data = service.get_usage_dashboard_data()
    
    print(f"✓ Dashboard data compiled:")
    print(f"  - Feature usage entries: {len(dashboard_data['feature_usage'])}")
    print(f"  - User behavior patterns: {len(dashboard_data['user_behavior'])}")
    print(f"  - Performance issues: {len(dashboard_data['performance_issues'])}")
    print(f"  - Recommendations: {len(dashboard_data['recommendations'])}")
    print(f"  - Summary: {dashboard_data['summary']}")
    
    return True

def main():
    """Run simple usage analytics tests."""
    print("📊 Testing Usage Analytics System")
    print("=" * 50)
    
    try:
        service = test_event_tracking()
        test_feature_usage_stats(service)
        test_user_behavior_analysis(service)
        test_performance_issue_tracking(service)
        test_optimization_recommendations(service)
        test_dashboard_data(service)
        
        print("\n✅ All usage analytics tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)