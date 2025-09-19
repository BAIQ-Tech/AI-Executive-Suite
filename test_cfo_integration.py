#!/usr/bin/env python3
"""
Test script for CFO AI integration

This script tests the enhanced CFO functionality with AI integration.
"""

import os
import sys
from datetime import datetime
from decimal import Decimal

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ai_ceo.cfo import AI_CFO

def test_cfo_basic_functionality():
    """Test basic CFO functionality"""
    print("=== Testing Basic CFO Functionality ===")
    
    # Create CFO instance
    cfo = AI_CFO(name="Test CFO", company_name="Test Company")
    
    print(f"CFO Name: {cfo.name}")
    print(f"Company: {cfo.company_name}")
    print(f"AI Service Available: {cfo.ai_service is not None}")
    print(f"Financial Vision: {cfo.get_financial_vision()}")
    print(f"Financial Principles: {cfo.get_financial_principles()}")
    print(f"Budget Categories: {len(cfo.budget)}")
    print(f"Financial Metrics: {len(cfo.financial_metrics)}")
    
    # Test financial health score
    health_score, health_status = cfo.get_financial_health_score()
    print(f"Financial Health: {health_score}/100 ({health_status})")
    print()
    
    return cfo

def test_cfo_financial_decisions(cfo):
    """Test CFO financial decision making"""
    print("=== Testing CFO Financial Decision Making ===")
    
    # Test basic financial decision
    context = "We need to decide on the budget allocation for Q4. Marketing is requesting additional $100K for a new campaign, while R&D wants $150K for a new product development."
    
    print(f"Context: {context}")
    print("Making financial decision...")
    
    decision = cfo.make_financial_decision(
        context=context,
        category="budget",
        financial_impact=Decimal('250000')
    )
    
    print(f"Decision ID: {decision.id}")
    print(f"Decision: {decision.decision}")
    print(f"Rationale: {decision.rationale}")
    print(f"Priority: {decision.priority}")
    print(f"Category: {decision.category}")
    print(f"Financial Impact: ${decision.financial_impact}")
    print(f"Risk Level: {decision.risk_level}")
    print(f"Confidence Score: {decision.confidence_score}")
    print(f"ROI Estimate: {decision.roi_estimate}%")
    print(f"Payback Period: {decision.payback_period} months")
    print()
    
    # Test decision with options and financial data
    context2 = "Choose the best investment option for our expansion plans."
    options = ["Expand to European market", "Invest in AI technology", "Acquire competitor"]
    financial_data = {
        "investment_amount": 500000,
        "expected_return": 750000,
        "time_horizon": "18 months",
        "risk_tolerance": "medium"
    }
    
    print(f"Context: {context2}")
    print(f"Options: {options}")
    print(f"Financial Data: {financial_data}")
    print("Making decision with options and financial data...")
    
    decision2 = cfo.make_financial_decision(
        context=context2,
        category="investment",
        options=options,
        financial_impact=Decimal('500000'),
        financial_data=financial_data
    )
    
    print(f"Decision ID: {decision2.id}")
    print(f"Decision: {decision2.decision}")
    print(f"Rationale: {decision2.rationale}")
    print(f"Priority: {decision2.priority}")
    print(f"Confidence Score: {decision2.confidence_score}")
    print(f"ROI Estimate: {decision2.roi_estimate}%")
    print(f"Payback Period: {decision2.payback_period} months")
    print()
    
    return [decision, decision2]

def test_cfo_financial_analysis(cfo):
    """Test CFO financial analysis"""
    print("=== Testing CFO Financial Analysis ===")
    
    context = "Analyze the ROI of our proposed marketing automation system"
    financial_data = {
        "investment_cost": 200000,
        "annual_savings": 80000,
        "implementation_time": 6,
        "expected_revenue_increase": 150000
    }
    
    print(f"Analysis Context: {context}")
    print(f"Financial Data: {financial_data}")
    print("Getting financial analysis...")
    
    analysis = cfo.get_financial_analysis(
        context=context,
        financial_data=financial_data,
        analysis_type="roi"
    )
    
    print(f"Analysis: {analysis['analysis']}")
    print(f"Rationale: {analysis['rationale']}")
    print(f"Confidence: {analysis['confidence']}")
    print(f"Risk Level: {analysis['risk_level']}")
    print(f"Financial Impact: {analysis['financial_impact']}")
    print(f"Recommendations: {analysis['recommendations']}")
    print()

def test_cfo_investment_recommendations(cfo):
    """Test CFO investment recommendations"""
    print("=== Testing CFO Investment Recommendations ===")
    
    context = "We have $1M available for strategic investments. What should be our priorities?"
    investment_data = {
        "available_capital": 1000000,
        "investment_horizon": "3 years",
        "risk_tolerance": "moderate",
        "strategic_goals": ["market_expansion", "technology_upgrade", "talent_acquisition"]
    }
    
    print(f"Context: {context}")
    print(f"Investment Data: {investment_data}")
    print("Getting investment recommendation...")
    
    recommendation = cfo.get_investment_recommendation(context, investment_data)
    
    print(f"Recommendation: {recommendation['recommendation']}")
    print(f"Rationale: {recommendation['rationale']}")
    print(f"Confidence: {recommendation['confidence']}")
    print(f"Risk Level: {recommendation['risk_level']}")
    print(f"Financial Impact: {recommendation['financial_impact']}")
    print()

def test_cfo_risk_assessment(cfo):
    """Test CFO financial risk assessment"""
    print("=== Testing CFO Financial Risk Assessment ===")
    
    context = "Assess the financial risks of expanding operations during economic uncertainty"
    financial_scenario = {
        "expansion_cost": 800000,
        "monthly_operating_increase": 50000,
        "revenue_uncertainty": "high",
        "market_conditions": "volatile"
    }
    
    print(f"Context: {context}")
    print(f"Financial Scenario: {financial_scenario}")
    print("Getting risk assessment...")
    
    assessment = cfo.assess_financial_risk(context, financial_scenario)
    
    print(f"Assessment: {assessment['assessment']}")
    print(f"Rationale: {assessment['rationale']}")
    print(f"Risk Level: {assessment['risk_level']}")
    print(f"Confidence: {assessment['confidence']}")
    print(f"Mitigation Strategies: {assessment['mitigation_strategies']}")
    print()

def test_cfo_budget_management(cfo):
    """Test CFO budget management"""
    print("=== Testing CFO Budget Management ===")
    
    # Test budget utilization
    print("Current Budget Utilization:")
    utilization = cfo.get_budget_utilization()
    for category, util in utilization.items():
        print(f"  {category.title()}: {util:.1f}%")
    print()
    
    # Update some spending
    print("Updating marketing spending...")
    success = cfo.update_budget_spending("marketing", Decimal('50000'))
    print(f"Update successful: {success}")
    
    # Get budget recommendations
    print("Getting budget recommendations...")
    recommendations = cfo.get_budget_recommendations("Optimize budget allocation for maximum ROI")
    
    print(f"Recommendations: {recommendations['recommendations']}")
    print(f"Rationale: {recommendations['rationale']}")
    print(f"Confidence: {recommendations['confidence']}")
    print(f"Priority Areas: {recommendations['priority_areas']}")
    print()

def test_cfo_financial_calculations(cfo):
    """Test CFO financial calculations"""
    print("=== Testing CFO Financial Calculations ===")
    
    # Test ROI calculation
    investment = Decimal('100000')
    returns = Decimal('125000')
    roi = cfo.calculate_roi(investment, returns)
    print(f"ROI Calculation: Investment ${investment}, Returns ${returns}, ROI: {roi}%")
    
    # Test NPV calculation
    cash_flows = [Decimal('-100000'), Decimal('30000'), Decimal('40000'), Decimal('50000')]
    discount_rate = Decimal('10')
    npv = cfo.calculate_npv(cash_flows, discount_rate)
    print(f"NPV Calculation: Cash flows {cash_flows}, Discount rate {discount_rate}%, NPV: ${npv}")
    
    # Test payback period
    initial_investment = Decimal('200000')
    annual_cash_flow = Decimal('60000')
    payback = cfo.calculate_payback_period(initial_investment, annual_cash_flow)
    print(f"Payback Period: Investment ${initial_investment}, Annual cash flow ${annual_cash_flow}, Payback: {payback} years")
    print()

def test_cfo_insights(cfo):
    """Test CFO decision insights"""
    print("=== Testing CFO Decision Insights ===")
    
    insights = cfo.get_decision_insights()
    
    print("Financial Decision Insights:")
    for key, value in insights.items():
        print(f"  {key}: {value}")
    print()
    
    # Test conversation summary
    summary = cfo.get_conversation_summary()
    print("Conversation Summary:")
    for key, value in summary.items():
        print(f"  {key}: {value}")
    print()

def main():
    """Main test function"""
    print("💰 Testing Enhanced AI CFO Integration")
    print("=" * 50)
    print()
    
    try:
        # Test basic functionality
        cfo = test_cfo_basic_functionality()
        
        # Test financial decision making
        decisions = test_cfo_financial_decisions(cfo)
        
        # Test financial analysis
        test_cfo_financial_analysis(cfo)
        
        # Test investment recommendations
        test_cfo_investment_recommendations(cfo)
        
        # Test risk assessment
        test_cfo_risk_assessment(cfo)
        
        # Test budget management
        test_cfo_budget_management(cfo)
        
        # Test financial calculations
        test_cfo_financial_calculations(cfo)
        
        # Test insights
        test_cfo_insights(cfo)
        
        print("✅ All CFO tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)