#!/usr/bin/env python3
"""
Test script for CTO AI integration

This script tests the enhanced CTO functionality with AI integration.
"""

import os
import sys
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ai_ceo.cto import AI_CTO

def test_cto_basic_functionality():
    """Test basic CTO functionality"""
    print("=== Testing Basic CTO Functionality ===")
    
    # Create CTO instance
    cto = AI_CTO(name="Test CTO", company_name="Test Company")
    
    print(f"CTO Name: {cto.name}")
    print(f"Company: {cto.company_name}")
    print(f"AI Service Available: {cto.ai_service is not None}")
    print(f"Technical Vision: {cto.get_technical_vision()}")
    print(f"Architecture Principles: {cto.get_architecture_principles()}")
    print(f"Technology Stack Size: {len(cto.technology_stack)}")
    print()
    
    return cto

def test_cto_technical_decisions(cto):
    """Test CTO technical decision making"""
    print("=== Testing CTO Technical Decision Making ===")
    
    # Test basic technical decision
    context = "We need to choose a database solution for our new microservices architecture. The system needs to handle high throughput and provide ACID compliance."
    
    print(f"Context: {context}")
    print("Making technical decision...")
    
    decision = cto.make_technical_decision(
        context=context,
        category="architecture",
        impact="high"
    )
    
    print(f"Decision ID: {decision.id}")
    print(f"Decision: {decision.decision}")
    print(f"Rationale: {decision.rationale}")
    print(f"Priority: {decision.priority}")
    print(f"Category: {decision.category}")
    print(f"Impact: {decision.impact}")
    print(f"Confidence Score: {decision.confidence_score}")
    print(f"Risk Level: {decision.risk_level}")
    print()
    
    # Test decision with options and technical requirements
    context2 = "Select the best frontend framework for our new dashboard application."
    options = ["React", "Vue.js", "Angular", "Svelte"]
    tech_requirements = {
        "scalability": "high",
        "performance": "critical",
        "maintainability": "high",
        "team_expertise": "medium"
    }
    
    print(f"Context: {context2}")
    print(f"Options: {options}")
    print(f"Technical Requirements: {tech_requirements}")
    print("Making decision with options and requirements...")
    
    decision2 = cto.make_technical_decision(
        context=context2,
        category="development",
        options=options,
        impact="medium",
        technical_requirements=tech_requirements
    )
    
    print(f"Decision ID: {decision2.id}")
    print(f"Decision: {decision2.decision}")
    print(f"Rationale: {decision2.rationale}")
    print(f"Priority: {decision2.priority}")
    print(f"Confidence Score: {decision2.confidence_score}")
    print()
    
    return [decision, decision2]

def test_cto_architecture_analysis(cto):
    """Test CTO architecture analysis"""
    print("=== Testing CTO Architecture Analysis ===")
    
    context = "Design a scalable microservices architecture for our e-commerce platform"
    current_arch = "Monolithic application with MySQL database"
    requirements = [
        "Handle 10,000+ concurrent users",
        "Support multiple payment gateways",
        "Real-time inventory updates",
        "Mobile API support"
    ]
    constraints = [
        "Budget limit of $50,000",
        "Must migrate within 6 months",
        "Existing team has Java expertise"
    ]
    
    print(f"Analysis Context: {context}")
    print(f"Current Architecture: {current_arch}")
    print(f"Requirements: {requirements}")
    print(f"Constraints: {constraints}")
    print("Getting architecture analysis...")
    
    analysis = cto.get_architecture_analysis(
        context=context,
        current_architecture=current_arch,
        requirements=requirements,
        constraints=constraints
    )
    
    print(f"Analysis: {analysis['analysis']}")
    print(f"Rationale: {analysis['rationale']}")
    print(f"Confidence: {analysis['confidence']}")
    print(f"Risk Level: {analysis['risk_level']}")
    print(f"Recommendations: {analysis['recommendations']}")
    print()

def test_cto_technology_recommendations(cto):
    """Test CTO technology recommendations"""
    print("=== Testing CTO Technology Recommendations ===")
    
    context = "We need to modernize our backend API to support GraphQL and improve performance"
    category = "backend"
    
    print(f"Context: {context}")
    print(f"Category: {category}")
    print("Getting technology recommendation...")
    
    recommendation = cto.get_technology_recommendation(context, category)
    
    print(f"Recommendation: {recommendation['recommendation']}")
    print(f"Rationale: {recommendation['rationale']}")
    print(f"Confidence: {recommendation['confidence']}")
    print(f"Risk Level: {recommendation['risk_level']}")
    print()

def test_cto_risk_assessment(cto):
    """Test CTO technical risk assessment"""
    print("=== Testing CTO Technical Risk Assessment ===")
    
    context = "Migrating from on-premise servers to AWS cloud infrastructure"
    proposed_solution = "Containerize applications using Docker and deploy on EKS with auto-scaling"
    
    print(f"Context: {context}")
    print(f"Proposed Solution: {proposed_solution}")
    print("Getting risk assessment...")
    
    assessment = cto.assess_technical_risk(context, proposed_solution)
    
    print(f"Assessment: {assessment['assessment']}")
    print(f"Rationale: {assessment['rationale']}")
    print(f"Risk Level: {assessment['risk_level']}")
    print(f"Confidence: {assessment['confidence']}")
    print(f"Mitigation Strategies: {assessment['mitigation_strategies']}")
    print()

def test_cto_insights(cto):
    """Test CTO decision insights"""
    print("=== Testing CTO Decision Insights ===")
    
    insights = cto.get_decision_insights()
    
    print("Technical Decision Insights:")
    for key, value in insights.items():
        print(f"  {key}: {value}")
    print()
    
    # Test conversation summary
    summary = cto.get_conversation_summary()
    print("Conversation Summary:")
    for key, value in summary.items():
        print(f"  {key}: {value}")
    print()

def test_cto_technology_stack(cto):
    """Test CTO technology stack management"""
    print("=== Testing CTO Technology Stack Management ===")
    
    # Add new technology
    print("Adding new technology: Redis")
    success = cto.add_technology("Redis", "database", "7.0", "planned")
    print(f"Add successful: {success}")
    
    # Update technology status
    print("Updating Redis status to active")
    success = cto.update_technology_status("Redis", "active")
    print(f"Update successful: {success}")
    
    # Get technologies by category
    db_technologies = cto.get_technology_stack_by_category("database")
    print(f"Database technologies: {[tech.name for tech in db_technologies]}")
    
    print()

def main():
    """Main test function"""
    print("🔧 Testing Enhanced AI CTO Integration")
    print("=" * 50)
    print()
    
    try:
        # Test basic functionality
        cto = test_cto_basic_functionality()
        
        # Test technical decision making
        decisions = test_cto_technical_decisions(cto)
        
        # Test architecture analysis
        test_cto_architecture_analysis(cto)
        
        # Test technology recommendations
        test_cto_technology_recommendations(cto)
        
        # Test risk assessment
        test_cto_risk_assessment(cto)
        
        # Test insights
        test_cto_insights(cto)
        
        # Test technology stack management
        test_cto_technology_stack(cto)
        
        print("✅ All CTO tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)