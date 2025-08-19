from ai_ceo.ceo import AI_CEO

def main():
    # Create a new AI CEO instance
    ceo = AI_CEO(name="Alex", company_name="TechNova Inc.")
    
    # Display vision and mission
    print(f"Vision: {ceo.get_vision_statement()}")
    print(f"Mission: {ceo.get_mission_statement()}")
    
    # Make a strategic decision
    context = "We need to decide on our product pricing strategy for the new AI assistant."
    options = [
        "Premium pricing at $99/month",
        "Freemium model with $49/month premium features",
        "Tiered pricing from $19 to $199/month"
    ]
    
    print("\nMaking a strategic decision...")
    decision = ceo.make_decision(context, options)
    
    # Display the decision
    print(f"\nDecision ID: {decision.id}")
    print(f"Timestamp: {decision.timestamp}")
    print(f"Decision: {decision.decision}")
    print(f"Rationale: {decision.rationale}")
    print(f"Priority: {decision.priority}")
    print(f"Status: {decision.status}")
    
    # Update decision status
    ceo.update_decision_status(decision.id, 'in_progress')
    print(f"\nUpdated status: {ceo.get_decision(decision.id).status}")

if __name__ == "__main__":
    main()
