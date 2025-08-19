from ai_ceo.cfo import AI_CFO
from decimal import Decimal

def main():
    # Create a new AI CFO instance
    cfo = AI_CFO(name="Michael", company_name="TechNova Inc.")
    
    # Display financial vision and principles
    print(f"Financial Vision: {cfo.get_financial_vision()}")
    print(f"\nFinancial Principles:")
    for i, principle in enumerate(cfo.get_financial_principles(), 1):
        print(f"  {i}. {principle}")
    
    # Display current budget
    print(f"\nCurrent Budget Allocation:")
    for category, item in cfo.budget.items():
        utilization = cfo.get_budget_utilization(category)[category]
        print(f"  {item.category}: ${item.allocated_amount:,} allocated, ${item.spent_amount:,} spent ({utilization:.1f}% utilized)")
    
    # Display financial metrics
    print(f"\nKey Financial Metrics:")
    for name, metric in cfo.financial_metrics.items():
        status = "✓" if metric.value >= metric.target else "⚠"
        print(f"  {status} {metric.name}: ${metric.value:,} (Target: ${metric.target:,}) - {metric.trend}")
    
    # Calculate financial health score
    health_score, health_status = cfo.get_financial_health_score()
    print(f"\nFinancial Health Score: {health_score}/100 ({health_status})")
    
    # Make a budget decision
    context = "We need to decide on budget allocation for Q4 marketing campaign to drive year-end sales."
    options = [
        "Increase marketing budget by $100,000 for digital advertising",
        "Reallocate $50,000 from operations to marketing",
        "Maintain current marketing budget and focus on organic growth"
    ]
    
    print(f"\nMaking a financial decision...")
    decision = cfo.make_financial_decision(
        context, 
        category="budget", 
        options=options, 
        financial_impact=Decimal('250000'),  # Expected revenue increase
        risk_level="medium"
    )
    
    # Display the decision
    print(f"\nFinancial Decision:")
    print(f"  ID: {decision.id}")
    print(f"  Category: {decision.category}")
    print(f"  Decision: {decision.decision}")
    print(f"  Rationale: {decision.rationale}")
    print(f"  Priority: {decision.priority}")
    print(f"  Financial Impact: ${decision.financial_impact:,}")
    print(f"  Risk Level: {decision.risk_level}")
    print(f"  Status: {decision.status}")
    
    # Update budget spending
    print(f"\nUpdating budget spending...")
    cfo.update_budget_spending("Marketing", Decimal('25000'))
    cfo.update_budget_spending("Operations", Decimal('75000'))
    
    # Show updated utilization
    print(f"Updated Budget Utilization:")
    utilization = cfo.get_budget_utilization()
    for category, percent in utilization.items():
        print(f"  {category.title()}: {percent:.1f}%")
    
    # Make an investment decision
    investment_context = "Evaluating investment in new AI development tools to improve productivity."
    investment_options = [
        "Invest $50,000 in enterprise AI development platform",
        "Start with $20,000 pilot program for 3 months",
        "Delay investment until next fiscal year"
    ]
    
    investment_decision = cfo.make_financial_decision(
        investment_context,
        category="investment",
        options=investment_options,
        financial_impact=Decimal('150000'),  # Expected productivity gains
        risk_level="low"
    )
    
    print(f"\nInvestment Decision: {investment_decision.decision}")
    print(f"Expected ROI: {cfo.calculate_roi(Decimal('50000'), Decimal('150000'), 12):.1f}%")
    
    # Add new financial metric
    cfo.add_financial_metric("Monthly Recurring Revenue", Decimal('180000'), Decimal('200000'), 'dollars', 'monthly')
    
    # Update decision status
    cfo.update_decision_status(decision.id, 'approved')
    print(f"\nDecision status updated: {cfo.get_financial_decision(decision.id).status}")
    
    # Show high-impact decisions
    high_impact = cfo.get_high_impact_decisions(Decimal('100000'))
    if high_impact:
        print(f"\nHigh-Impact Decisions (>$100K):")
        for dec in high_impact:
            print(f"  - {dec.decision} (${dec.financial_impact:,})")

if __name__ == "__main__":
    main()
