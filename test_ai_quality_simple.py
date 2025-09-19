#!/usr/bin/env python3
"""
Simple test for AI quality tracking functionality.
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from services.ai_quality_tracking import (
    AIQualityTracker, FeedbackCollectionService, ResponseFeedback, 
    ResponseRating, AccuracyLevel
)
from datetime import datetime, timedelta

def test_feedback_collection():
    """Test basic feedback collection functionality."""
    print("Testing Feedback Collection...")
    
    tracker = AIQualityTracker()
    service = FeedbackCollectionService(tracker)
    
    # Submit some test feedback
    success1 = service.submit_feedback(
        decision_id="test_decision_1",
        user_id="user_1",
        executive_type="ceo",
        rating=4,
        accuracy_rating=4,
        feedback_text="Good response, very helpful",
        response_time=2.5
    )
    
    success2 = service.submit_feedback(
        decision_id="test_decision_2",
        user_id="user_2",
        executive_type="cto",
        rating=2,
        accuracy_rating=2,
        feedback_text="Response was not accurate",
        response_time=3.0
    )
    
    success3 = service.submit_feedback(
        decision_id="test_decision_3",
        user_id="user_1",
        executive_type="cfo",
        rating=5,
        accuracy_rating=5,
        feedback_text="Excellent financial analysis",
        response_time=1.8
    )
    
    print(f"✓ Feedback submission 1: {success1}")
    print(f"✓ Feedback submission 2: {success2}")
    print(f"✓ Feedback submission 3: {success3}")
    print(f"✓ Total feedback entries: {len(tracker.feedback_history)}")
    
    return tracker

def test_quality_metrics(tracker):
    """Test quality metrics calculation."""
    print("\nTesting Quality Metrics...")
    
    # Get overall metrics
    overall_metrics = tracker.get_quality_metrics()
    print(f"✓ Total responses: {overall_metrics.total_responses}")
    print(f"✓ Average rating: {overall_metrics.average_rating:.2f}")
    print(f"✓ Average accuracy: {overall_metrics.average_accuracy:.2f}")
    print(f"✓ Average response time: {overall_metrics.response_time_avg:.2f}s")
    print(f"✓ Satisfaction distribution: {overall_metrics.satisfaction_distribution}")
    
    # Get CEO-specific metrics
    ceo_metrics = tracker.get_quality_metrics(executive_type="ceo")
    print(f"✓ CEO responses: {ceo_metrics.total_responses}")
    print(f"✓ CEO average rating: {ceo_metrics.average_rating:.2f}")
    
    return True

def test_executive_comparison(tracker):
    """Test executive performance comparison."""
    print("\nTesting Executive Comparison...")
    
    comparison = tracker.get_executive_performance_comparison()
    
    for exec_type, metrics in comparison.items():
        print(f"✓ {exec_type.upper()}:")
        print(f"  - Responses: {metrics.total_responses}")
        print(f"  - Avg Rating: {metrics.average_rating:.2f}")
        print(f"  - Avg Accuracy: {metrics.average_accuracy:.2f}")
    
    return True

def test_low_quality_detection(tracker):
    """Test low quality response detection."""
    print("\nTesting Low Quality Detection...")
    
    low_quality = tracker.get_low_quality_responses(threshold=2.5)
    print(f"✓ Low quality responses found: {len(low_quality)}")
    
    for response in low_quality:
        print(f"  - {response.executive_type}: {response.rating.value}/5 - {response.feedback_text}")
    
    return True

def test_recommendations(tracker):
    """Test improvement recommendations."""
    print("\nTesting Recommendations...")
    
    recommendations = tracker.get_improvement_recommendations()
    print(f"✓ Recommendations generated: {len(recommendations)}")
    
    for rec in recommendations:
        print(f"  - {rec['type']} ({rec['priority']}): {rec['message']}")
    
    return True

def main():
    """Run simple AI quality tracking tests."""
    print("🎯 Testing AI Quality Tracking System")
    print("=" * 50)
    
    try:
        tracker = test_feedback_collection()
        test_quality_metrics(tracker)
        test_executive_comparison(tracker)
        test_low_quality_detection(tracker)
        test_recommendations(tracker)
        
        print("\n✅ All AI quality tracking tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)