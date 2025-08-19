from ai_ceo.cto import AI_CTO

def main():
    # Create a new AI CTO instance
    cto = AI_CTO(name="Sarah", company_name="TechNova Inc.")
    
    # Display technical vision and architecture principles
    print(f"Technical Vision: {cto.get_technical_vision()}")
    print(f"\nArchitecture Principles:")
    for i, principle in enumerate(cto.get_architecture_principles(), 1):
        print(f"  {i}. {principle}")
    
    # Display current technology stack
    print(f"\nCurrent Technology Stack:")
    for category in ['frontend', 'backend', 'database', 'infrastructure']:
        techs = cto.get_technology_stack_by_category(category)
        if techs:
            print(f"  {category.title()}:")
            for tech in techs:
                print(f"    - {tech.name} v{tech.version} ({tech.status})")
    
    # Make a technical decision about microservices architecture
    context = "We need to decide on our backend architecture for scaling our application to handle 10x more users."
    options = [
        "Migrate to microservices architecture with Docker containers",
        "Scale vertically with more powerful servers and optimize current monolith",
        "Implement serverless architecture with AWS Lambda"
    ]
    
    print(f"\nMaking a technical decision...")
    decision = cto.make_technical_decision(context, category="architecture", options=options, impact="high")
    
    # Display the decision
    print(f"\nTechnical Decision:")
    print(f"  ID: {decision.id}")
    print(f"  Category: {decision.category}")
    print(f"  Decision: {decision.decision}")
    print(f"  Rationale: {decision.rationale}")
    print(f"  Priority: {decision.priority}")
    print(f"  Impact: {decision.impact}")
    print(f"  Status: {decision.status}")
    
    # Add a new technology to the stack
    print(f"\nAdding new technology to stack...")
    cto.add_technology("Redis", "database", "7.x", "planned")
    cto.add_technology("Kubernetes", "infrastructure", "1.28", "experimental")
    
    # Update decision status
    cto.update_decision_status(decision.id, 'in_progress')
    print(f"Updated decision status: {cto.get_technical_decision(decision.id).status}")
    
    # Show critical decisions
    critical_decisions = cto.get_critical_decisions()
    if critical_decisions:
        print(f"\nCritical Decisions:")
        for dec in critical_decisions:
            print(f"  - {dec.decision} ({dec.category})")
    
    # Make a security decision
    security_context = "We need to implement better authentication for our API endpoints."
    security_options = [
        "Implement OAuth 2.0 with JWT tokens",
        "Use API keys with rate limiting",
        "Implement multi-factor authentication"
    ]
    
    security_decision = cto.make_technical_decision(
        security_context, 
        category="security", 
        options=security_options, 
        impact="critical"
    )
    
    print(f"\nSecurity Decision: {security_decision.decision}")
    print(f"Priority: {security_decision.priority}")

if __name__ == "__main__":
    main()
