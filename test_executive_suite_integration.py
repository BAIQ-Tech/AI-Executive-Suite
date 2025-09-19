#!/usr/bin/env python3
"""
Comprehensive test script for AI Executive Suite integration

This script demonstrates the enhanced AI-powered executive decision system
with CEO, CTO, and CFO working together on business scenarios.
"""

import os
import sys
from datetime import datetime
from decimal import Decimal

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ai_ceo.ceo import AI_CEO
from ai_ceo.cto import AI_CTO
from ai_ceo.cfo import AI_CFO

def test_executive_suite_initialization():
    """Test initialization of all executives"""
    print("=== Initializing AI Executive Suite ===")
    
    # Initialize all executives
    ceo = AI_CEO(name="Alex Chen", company_name="TechCorp Inc.")
    cto = AI_CTO(name="Sarah Kim", company_name="TechCorp Inc.")
    cfo = AI_CFO(name="Michael Rodriguez", company_name="TechCorp Inc.")
    
    print(f"✓ CEO {ceo.name} initialized (AI: {ceo.ai_service is not None})")
    print(f"✓ CTO {cto.name} initialized (AI: {cto.ai_service is not None})")
    print(f"✓ CFO {cfo.name} initialized (AI: {cfo.ai_service is not None})")
    print()
    
    return ceo, cto, cfo

def test_collaborative_decision_scenario(ceo, cto, cfo):
    """Test a collaborative decision scenario involving all executives"""
    print("=== Collaborative Decision Scenario: Cloud Migration ===")
    
    # Business scenario: Cloud migration decision
    scenario = """
    TechCorp Inc. is considering migrating its on-premise infrastructure to the cloud.
    The current system is becoming expensive to maintain and lacks scalability.
    We need to evaluate this from strategic, technical, and financial perspectives.
    """
    
    print(f"Scenario: {scenario.strip()}")
    print()
    
    # CEO Strategic Decision
    print("--- CEO Strategic Analysis ---")
    ceo_context = f"{scenario} From a strategic perspective, evaluate the competitive advantages and market positioning implications."
    
    ceo_decision = ceo.make_decision(
        context=ceo_context,
        options=["Proceed with full migration", "Hybrid approach", "Stay on-premise"]
    )
    
    print(f"CEO Decision: {ceo_decision.decision}")
    print(f"CEO Rationale: {ceo_decision.rationale}")
    print(f"CEO Confidence: {ceo_decision.confidence_score}")
    print()
    
    # CTO Technical Analysis
    print("--- CTO Technical Analysis ---")
    cto_context = f"{scenario} From a technical perspective, analyze the architecture implications and implementation approach."
    
    tech_requirements = {
        "scalability": "high",
        "security": "critical",
        "performance": "important",
        "maintainability": "high"
    }
    
    cto_decision = cto.make_technical_decision(
        context=cto_context,
        category="infrastructure",
        impact="high",
        technical_requirements=tech_requirements
    )
    
    print(f"CTO Decision: {cto_decision.decision}")
    print(f"CTO Rationale: {cto_decision.rationale}")
    print(f"CTO Confidence: {cto_decision.confidence_score}")
    print(f"CTO Risk Level: {cto_decision.risk_level}")
    print()
    
    # CFO Financial Analysis
    print("--- CFO Financial Analysis ---")
    cfo_context = f"{scenario} From a financial perspective, analyze the costs, ROI, and budget implications."
    
    financial_data = {
        "current_infrastructure_cost": 500000,  # Annual
        "migration_cost": 200000,  # One-time
        "projected_cloud_cost": 300000,  # Annual
        "expected_savings": 200000,  # Annual
        "implementation_time": 6  # Months
    }
    
    cfo_decision = cfo.make_financial_decision(
        context=cfo_context,
        category="investment",
        financial_impact=Decimal('200000'),
        financial_data=financial_data
    )
    
    print(f"CFO Decision: {cfo_decision.decision}")
    print(f"CFO Rationale: {cfo_decision.rationale}")
    print(f"CFO Confidence: {cfo_decision.confidence_score}")
    print(f"CFO Financial Impact: ${cfo_decision.financial_impact}")
    print(f"CFO ROI Estimate: {cfo_decision.roi_estimate}%")
    print()
    
    return ceo_decision, cto_decision, cfo_decision

def test_executive_insights(ceo, cto, cfo):
    """Test insights from all executives"""
    print("=== Executive Decision Insights ===")
    
    # CEO Insights
    print("--- CEO Insights ---")
    ceo_insights = ceo.get_decision_insights()
    for key, value in ceo_insights.items():
        print(f"  {key}: {value}")
    print()
    
    # CTO Insights
    print("--- CTO Insights ---")
    cto_insights = cto.get_decision_insights()
    for key, value in cto_insights.items():
        print(f"  {key}: {value}")
    print()
    
    # CFO Insights
    print("--- CFO Insights ---")
    cfo_insights = cfo.get_decision_insights()
    for key, value in cfo_insights.items():
        print(f"  {key}: {value}")
    print()

def test_specialized_analyses(ceo, cto, cfo):
    """Test specialized analysis capabilities"""
    print("=== Specialized Executive Analyses ===")
    
    # CEO Strategic Analysis
    print("--- CEO Strategic Analysis ---")
    strategic_analysis = ceo.get_strategic_analysis(
        "Analyze our competitive position in the AI/ML market and recommend strategic initiatives"
    )
    print(f"Strategic Analysis: {strategic_analysis['analysis'][:200]}...")
    print(f"Confidence: {strategic_analysis['confidence']}")
    print()
    
    # CTO Architecture Analysis
    print("--- CTO Architecture Analysis ---")
    arch_analysis = cto.get_architecture_analysis(
        context="Design a microservices architecture for our new AI platform",
        requirements=["Handle 100K+ requests/day", "Real-time ML inference", "Multi-tenant"],
        constraints=["6-month timeline", "Existing Java team", "$300K budget"]
    )
    print(f"Architecture Analysis: {arch_analysis['analysis'][:200]}...")
    print(f"Confidence: {arch_analysis['confidence']}")
    print(f"Recommendations: {arch_analysis['recommendations'][:2]}")
    print()
    
    # CFO Financial Analysis
    print("--- CFO Financial Analysis ---")
    financial_analysis = cfo.get_financial_analysis(
        context="Evaluate the ROI of investing in AI/ML capabilities",
        financial_data={
            "investment_amount": 500000,
            "expected_annual_revenue": 200000,
            "cost_savings": 100000,
            "time_horizon": "3 years"
        },
        analysis_type="roi"
    )
    print(f"Financial Analysis: {financial_analysis['analysis'][:200]}...")
    print(f"Confidence: {financial_analysis['confidence']}")
    print(f"Risk Level: {financial_analysis['risk_level']}")
    print()

def test_executive_coordination():
    """Test how executives can work together on complex decisions"""
    print("=== Executive Coordination Test ===")
    
    # Initialize executives
    ceo, cto, cfo = test_executive_suite_initialization()
    
    # Run collaborative scenario
    decisions = test_collaborative_decision_scenario(ceo, cto, cfo)
    
    # Get insights
    test_executive_insights(ceo, cto, cfo)
    
    # Test specialized analyses
    test_specialized_analyses(ceo, cto, cfo)
    
    return decisions

def test_conversation_management(ceo, cto, cfo):
    """Test conversation history management"""
    print("=== Conversation Management Test ===")
    
    # Test conversation summaries
    print("--- Conversation Summaries ---")
    ceo_summary = ceo.get_conversation_summary()
    cto_summary = cto.get_conversation_summary()
    cfo_summary = cfo.get_conversation_summary()
    
    print(f"CEO Conversation: {ceo_summary}")
    print(f"CTO Conversation: {cto_summary}")
    print(f"CFO Conversation: {cfo_summary}")
    print()
    
    # Clear conversations
    print("--- Clearing Conversation Histories ---")
    ceo.clear_conversation_history()
    cto.clear_conversation_history()
    cfo.clear_conversation_history()
    
    print("✓ All conversation histories cleared")
    print()

def generate_executive_summary(decisions):
    """Generate a summary of the executive decisions"""
    print("=== Executive Decision Summary ===")
    
    ceo_decision, cto_decision, cfo_decision = decisions
    
    print("CLOUD MIGRATION DECISION SUMMARY")
    print("=" * 40)
    print()
    
    print("STRATEGIC PERSPECTIVE (CEO):")
    print(f"  Decision: {ceo_decision.decision}")
    print(f"  Priority: {ceo_decision.priority}")
    print(f"  Confidence: {ceo_decision.confidence_score}")
    print()
    
    print("TECHNICAL PERSPECTIVE (CTO):")
    print(f"  Decision: {cto_decision.decision}")
    print(f"  Risk Level: {cto_decision.risk_level}")
    print(f"  Confidence: {cto_decision.confidence_score}")
    print()
    
    print("FINANCIAL PERSPECTIVE (CFO):")
    print(f"  Decision: {cfo_decision.decision}")
    print(f"  Financial Impact: ${cfo_decision.financial_impact}")
    print(f"  Confidence: {cfo_decision.confidence_score}")
    print()
    
    # Calculate overall recommendation
    avg_confidence = (ceo_decision.confidence_score + cto_decision.confidence_score + cfo_decision.confidence_score) / 3
    
    print("OVERALL RECOMMENDATION:")
    print(f"  Average Confidence: {avg_confidence:.2f}")
    print(f"  Consensus: {'PROCEED' if avg_confidence > 0.6 else 'REVIEW FURTHER'}")
    print()

def main():
    """Main test function"""
    print("🏢 AI Executive Suite Integration Test")
    print("=" * 50)
    print()
    
    try:
        # Test executive coordination
        decisions = test_executive_coordination()
        
        # Test conversation management
        ceo, cto, cfo = test_executive_suite_initialization()
        test_conversation_management(ceo, cto, cfo)
        
        # Generate executive summary
        generate_executive_summary(decisions)
        
        print("✅ All AI Executive Suite integration tests completed successfully!")
        print()
        print("SUMMARY:")
        print("- ✓ CEO strategic decision making with AI integration")
        print("- ✓ CTO technical analysis and architecture recommendations")
        print("- ✓ CFO financial analysis and investment evaluation")
        print("- ✓ Collaborative decision making across all executives")
        print("- ✓ Conversation history management")
        print("- ✓ Specialized analysis capabilities")
        print("- ✓ Decision insights and reporting")
        print()
        print("The AI Executive Suite is ready for enhanced decision making!")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)