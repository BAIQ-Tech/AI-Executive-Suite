#!/usr/bin/env python3
"""
Interactive example showing different ways to use the AI Executive Suite
"""

from ai_ceo import AI_CEO, AI_CTO, AI_CFO
from decimal import Decimal

def demonstrate_individual_agents():
    """Show how to use each agent individually."""
    print("=== INDIVIDUAL AGENT USAGE ===\n")
    
    # CEO Agent
    print("1. AI_CEO - Strategic Business Decisions")
    ceo = AI_CEO(name="Alex", company_name="TechNova Inc.")
    
    # Make a strategic decision
    business_context = "Should we expand to the European market next quarter?"
    business_options = ["Yes, full expansion", "Pilot program first", "Wait until next year"]
    ceo_decision = ceo.make_decision(business_context, business_options)
    
    print(f"CEO Decision: {ceo_decision.decision}")
    print(f"Rationale: {ceo_decision.rationale}")
    print()
    
    # CTO Agent
    print("2. AI_CTO - Technical Decisions")
    cto = AI_CTO(name="Sarah", company_name="TechNova Inc.")
    
    # Make a technical decision
    tech_context = "Our API response times are too slow. How should we optimize?"
    tech_options = ["Add Redis caching", "Optimize database queries", "Implement CDN"]
    cto_decision = cto.make_technical_decision(tech_context, "infrastructure", tech_options, "high")
    
    print(f"CTO Decision: {cto_decision.decision}")
    print(f"Category: {cto_decision.category}, Impact: {cto_decision.impact}")
    print()
    
    # CFO Agent
    print("3. AI_CFO - Financial Decisions")
    cfo = AI_CFO(name="Michael", company_name="TechNova Inc.")
    
    # Make a financial decision
    financial_context = "Should we invest in new development tools?"
    financial_options = ["Invest $75K in premium tools", "Use free alternatives", "Gradual upgrade"]
    cfo_decision = cfo.make_financial_decision(
        financial_context, "investment", financial_options, 
        Decimal('200000'), "medium"
    )
    
    print(f"CFO Decision: {cfo_decision.decision}")
    print(f"Expected Impact: ${cfo_decision.financial_impact:,}")
    print()

def demonstrate_collaborative_decision():
    """Show how agents can work together on complex decisions."""
    print("=== COLLABORATIVE DECISION MAKING ===\n")
    
    # Initialize all three agents
    ceo = AI_CEO(name="Alex", company_name="TechNova Inc.")
    cto = AI_CTO(name="Sarah", company_name="TechNova Inc.")
    cfo = AI_CFO(name="Michael", company_name="TechNova Inc.")
    
    print("Scenario: Company wants to build a new AI product")
    print()
    
    # CEO makes strategic decision
    print("CEO Perspective:")
    ceo_context = "Should we develop a new AI-powered analytics product?"
    ceo_decision = ceo.make_decision(ceo_context, ["Yes, high priority", "Yes, but low priority", "No, focus on core product"])
    print(f"Strategic Decision: {ceo_decision.decision}")
    print()
    
    # CTO evaluates technical feasibility
    print("CTO Perspective:")
    cto_context = "What technology stack should we use for the AI analytics product?"
    cto_options = ["Python + TensorFlow + AWS", "Node.js + PyTorch + Azure", "Go + Custom ML + GCP"]
    cto_decision = cto.make_technical_decision(cto_context, "architecture", cto_options, "critical")
    print(f"Technical Decision: {cto_decision.decision}")
    print()
    
    # CFO analyzes financial impact
    print("CFO Perspective:")
    cfo_context = "What's the budget allocation for the AI product development?"
    cfo_options = ["$500K over 6 months", "$300K over 9 months", "$200K over 12 months"]
    cfo_decision = cfo.make_financial_decision(
        cfo_context, "budget", cfo_options, 
        Decimal('1500000'), "high"  # Expected revenue
    )
    print(f"Financial Decision: {cfo_decision.decision}")
    print(f"Expected ROI: {cfo.calculate_roi(Decimal('500000'), Decimal('1500000'), 12):.1f}%")
    print()

def demonstrate_status_tracking():
    """Show how to track and update decision status."""
    print("=== DECISION STATUS TRACKING ===\n")
    
    ceo = AI_CEO(name="Alex", company_name="TechNova Inc.")
    
    # Make multiple decisions
    decision1 = ceo.make_decision("Launch new marketing campaign", ["Social media focus", "Traditional media", "Influencer partnerships"])
    decision2 = ceo.make_decision("Hire new team members", ["5 developers", "3 developers + 2 designers", "Focus on senior hires"])
    
    print("Initial Decisions:")
    print(f"1. {decision1.decision} - Status: {decision1.status}")
    print(f"2. {decision2.decision} - Status: {decision2.status}")
    print()
    
    # Update statuses
    ceo.update_decision_status(decision1.id, 'in_progress')
    ceo.update_decision_status(decision2.id, 'completed')
    
    print("Updated Statuses:")
    print(f"1. {ceo.get_decision(decision1.id).decision} - Status: {ceo.get_decision(decision1.id).status}")
    print(f"2. {ceo.get_decision(decision2.id).decision} - Status: {ceo.get_decision(decision2.id).status}")
    print()

def demonstrate_data_access():
    """Show how to access and analyze agent data."""
    print("=== DATA ACCESS & ANALYSIS ===\n")
    
    cfo = AI_CFO(name="Michael", company_name="TechNova Inc.")
    
    # Add some spending
    cfo.update_budget_spending("Marketing", Decimal('50000'))
    cfo.update_budget_spending("R&D", Decimal('75000'))
    cfo.update_budget_spending("Personnel", Decimal('200000'))
    
    print("Budget Analysis:")
    utilization = cfo.get_budget_utilization()
    for category, percent in utilization.items():
        budget_item = cfo.budget[category]
        print(f"{category.title()}: ${budget_item.spent_amount:,} / ${budget_item.allocated_amount:,} ({percent:.1f}%)")
    
    print()
    
    # Financial health
    health_score, health_status = cfo.get_financial_health_score()
    print(f"Financial Health: {health_score}/100 ({health_status})")
    print()
    
    # Technology stack analysis
    cto = AI_CTO(name="Sarah", company_name="TechNova Inc.")
    print("Technology Stack by Category:")
    for category in ['frontend', 'backend', 'database', 'infrastructure']:
        techs = cto.get_technology_stack_by_category(category)
        if techs:
            print(f"{category.title()}:")
            for tech in techs:
                print(f"  - {tech.name} v{tech.version} ({tech.status})")

def main():
    """Run all demonstration examples."""
    demonstrate_individual_agents()
    print("\n" + "="*60 + "\n")
    
    demonstrate_collaborative_decision()
    print("\n" + "="*60 + "\n")
    
    demonstrate_status_tracking()
    print("\n" + "="*60 + "\n")
    
    demonstrate_data_access()

if __name__ == "__main__":
    main()
