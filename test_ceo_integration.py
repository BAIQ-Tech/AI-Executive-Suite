#!/usr/bin/env python3
"""
Test script for CEO AI integration

This script tests the enhanced CEO functionality with AI integration.
"""

import os
import sys
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ai_ceo.ceo import AI_CEO

def test_ceo_basic_functionality():
    """Test basic CEO functionality"""
    print("=== Testing Basic CEO Functionality ===")
    
    # Create CEO instance
    ceo = AI_CEO(name="Test CEO", company_name="Test Company")
    
    print(f"CEO Name: {ceo.name}")
    print(f"Company: {ceo.company_name}")
    print(f"AI Service Available: {ceo.ai_service is not None}")
    print(f"Vision: {ceo.get_vision_statement()}")
    print(f"Mission: {ceo.get_mission_statement()}")
    print()
    
    return ceo

def test_ceo_decision_making(ceo):
    """Test CEO decision making"""
    print("=== Testing CEO Decision Making ===")
    
    # Test basic decision
    context = "Our company is considering expanding into the European market. We have the capital and resources, but need to evaluate the strategic implications."
    
    print(f"Context: {context}")
    print("Making decision...")
    
    decision = ceo.make_decision(context)
    
    print(f"Decision ID: {decision.id}")
    print(f"Decision: {decision.decision}")
    print(f"Rationale: {decision.rationale}")
    print(f"Priority: {decision.priority}")
    print(f"Confidence Score: {decision.confidence_score}")
    print(f"Status: {decision.status}")
    print()
    
    # Test decision with options
    context2 = "We need to choose our primary technology stack for the new product."
    options = ["React + Node.js", "Vue.js + Python", "Angular + Java"]
    
    print(f"Context: {context2}")
    print(f"Options: {options}")
    print("Making decision with options...")
    
    decision2 = ceo.make_decision(context2, options=options)
    
    print(f"Decision ID: {decision2.id}")
    print(f"Decision: {decision2.decision}")
    print(f"Rationale: {decision2.rationale}")
    print(f"Priority: {decision2.priority}")
    print(f"Confidence Score: {decision2.confidence_score}")
    print()
    
    return [decision, decision2]

def test_ceo_strategic_analysis(ceo):
    """Test CEO strategic analysis"""
    print("=== Testing CEO Strategic Analysis ===")
    
    context = "Analyze the competitive landscape for our SaaS product in the current market conditions."
    
    print(f"Analysis Context: {context}")
    print("Getting strategic analysis...")
    
    analysis = ceo.get_strategic_analysis(context)
    
    print(f"Analysis: {analysis['analysis']}")
    print(f"Rationale: {analysis['rationale']}")
    print(f"Confidence: {analysis['confidence']}")
    print(f"Risk Level: {analysis['risk_level']}")
    print(f"Category: {analysis['category']}")
    print()

def test_ceo_insights(ceo):
    """Test CEO decision insights"""
    print("=== Testing CEO Decision Insights ===")
    
    insights = ceo.get_decision_insights()
    
    print("Decision Insights:")
    for key, value in insights.items():
        print(f"  {key}: {value}")
    print()
    
    # Test conversation summary
    summary = ceo.get_conversation_summary()
    print("Conversation Summary:")
    for key, value in summary.items():
        print(f"  {key}: {value}")
    print()

def test_ceo_status_updates(ceo, decisions):
    """Test decision status updates"""
    print("=== Testing Decision Status Updates ===")
    
    if decisions:
        decision = decisions[0]
        print(f"Updating status of decision {decision.id} to 'in_progress'")
        
        success = ceo.update_decision_status(decision.id, 'in_progress')
        print(f"Update successful: {success}")
        print(f"New status: {ceo.get_decision(decision.id).status}")
        print()

def main():
    """Main test function"""
    print("🧠 Testing Enhanced AI CEO Integration")
    print("=" * 50)
    print()
    
    try:
        # Test basic functionality
        ceo = test_ceo_basic_functionality()
        
        # Test decision making
        decisions = test_ceo_decision_making(ceo)
        
        # Test strategic analysis
        test_ceo_strategic_analysis(ceo)
        
        # Test insights
        test_ceo_insights(ceo)
        
        # Test status updates
        test_ceo_status_updates(ceo, decisions)
        
        print("✅ All tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)