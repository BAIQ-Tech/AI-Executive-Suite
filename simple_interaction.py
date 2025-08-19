#!/usr/bin/env python3
"""
Simple interactive script to use the AI Executive Suite
"""

from ai_ceo import AI_CEO, AI_CTO, AI_CFO
from decimal import Decimal

def main():
    print("🏢 AI Executive Suite - Interactive Demo")
    print("=" * 50)
    
    # Initialize your executive team
    ceo = AI_CEO(name="Alex", company_name="Your Company")
    cto = AI_CTO(name="Sarah", company_name="Your Company") 
    cfo = AI_CFO(name="Michael", company_name="Your Company")
    
    while True:
        print("\nChoose an agent to interact with:")
        print("1. CEO - Strategic Business Decisions")
        print("2. CTO - Technical Decisions") 
        print("3. CFO - Financial Decisions")
        print("4. View All Agent Status")
        print("5. Exit")
        
        choice = input("\nEnter your choice (1-5): ").strip()
        
        if choice == "1":
            interact_with_ceo(ceo)
        elif choice == "2":
            interact_with_cto(cto)
        elif choice == "3":
            interact_with_cfo(cfo)
        elif choice == "4":
            show_all_status(ceo, cto, cfo)
        elif choice == "5":
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please try again.")

def interact_with_ceo(ceo):
    print(f"\n💼 CEO {ceo.name} - Strategic Leadership")
    print(f"Vision: {ceo.get_vision_statement()}")
    
    context = input("\nDescribe the business situation: ")
    if context.strip():
        decision = ceo.make_decision(context)
        print(f"\n✅ CEO Decision: {decision.decision}")
        print(f"📋 Rationale: {decision.rationale}")
        print(f"⚡ Priority: {decision.priority}")

def interact_with_cto(cto):
    print(f"\n💻 CTO {cto.name} - Technical Leadership")
    print(f"Vision: {cto.get_technical_vision()}")
    
    context = input("\nDescribe the technical challenge: ")
    if context.strip():
        print("\nSelect category:")
        print("1. Architecture  2. Security  3. Infrastructure  4. Development")
        cat_choice = input("Enter choice (1-4): ").strip()
        
        categories = {"1": "architecture", "2": "security", "3": "infrastructure", "4": "development"}
        category = categories.get(cat_choice, "development")
        
        decision = cto.make_technical_decision(context, category, impact="medium")
        print(f"\n✅ CTO Decision: {decision.decision}")
        print(f"📋 Category: {decision.category}")
        print(f"⚡ Priority: {decision.priority}")

def interact_with_cfo(cfo):
    print(f"\n💰 CFO {cfo.name} - Financial Leadership")
    print(f"Vision: {cfo.get_financial_vision()}")
    
    # Show current budget status
    print("\n📊 Current Budget Status:")
    utilization = cfo.get_budget_utilization()
    for category, percent in utilization.items():
        print(f"  {category.title()}: {percent:.1f}% utilized")
    
    context = input("\nDescribe the financial decision needed: ")
    if context.strip():
        print("\nSelect category:")
        print("1. Budget  2. Investment  3. Cost Reduction  4. Revenue")
        cat_choice = input("Enter choice (1-4): ").strip()
        
        categories = {"1": "budget", "2": "investment", "3": "cost_reduction", "4": "revenue"}
        category = categories.get(cat_choice, "budget")
        
        impact_str = input("Expected financial impact ($): ").strip()
        try:
            impact = Decimal(impact_str) if impact_str else Decimal('0')
        except:
            impact = Decimal('0')
        
        decision = cfo.make_financial_decision(context, category, financial_impact=impact)
        print(f"\n✅ CFO Decision: {decision.decision}")
        print(f"📋 Category: {decision.category}")
        print(f"💵 Financial Impact: ${decision.financial_impact:,}")

def show_all_status(ceo, cto, cfo):
    print("\n📈 Executive Team Status")
    print("=" * 30)
    
    print(f"\n💼 CEO Decisions: {len(ceo.decisions)}")
    for decision in list(ceo.decisions.values())[-3:]:  # Show last 3
        print(f"  • {decision.decision[:50]}... ({decision.status})")
    
    print(f"\n💻 CTO Decisions: {len(cto.technical_decisions)}")
    for decision in list(cto.technical_decisions.values())[-3:]:  # Show last 3
        print(f"  • {decision.decision[:50]}... ({decision.status})")
    
    print(f"\n💰 CFO Decisions: {len(cfo.financial_decisions)}")
    for decision in list(cfo.financial_decisions.values())[-3:]:  # Show last 3
        print(f"  • {decision.decision[:50]}... ({decision.status})")
    
    # Financial health
    health_score, health_status = cfo.get_financial_health_score()
    print(f"\n🏥 Financial Health: {health_score}/100 ({health_status})")

if __name__ == "__main__":
    main()
