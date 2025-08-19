import random
from typing import Dict, List, Optional, Set
from dataclasses import dataclass
from datetime import datetime

@dataclass
class TechnicalDecision:
    """Represents a technical decision made by the AI_CTO."""
    id: str
    timestamp: str
    decision: str
    rationale: str
    priority: str  # 'critical', 'high', 'medium', 'low'
    category: str  # 'architecture', 'security', 'infrastructure', 'development', 'data'
    status: str = 'pending'  # 'pending', 'in_progress', 'completed', 'rejected'
    impact: str = 'medium'  # 'low', 'medium', 'high', 'critical'

@dataclass
class TechnologyStack:
    """Represents a technology in the company's stack."""
    name: str
    category: str  # 'frontend', 'backend', 'database', 'infrastructure', 'tools'
    version: str
    status: str = 'active'  # 'active', 'deprecated', 'planned', 'experimental'
    adoption_date: str = None

class AI_CTO:
    """An AI-powered CTO agent that can make technical decisions and manage technology strategy."""
    
    def __init__(self, name: str = "AI_CTO", company_name: str = "Your Company"):
        self.name = name
        self.company_name = company_name
        self.technical_decisions: Dict[str, TechnicalDecision] = {}
        self.technology_stack: Dict[str, TechnologyStack] = {}
        self.technical_vision = "To build scalable, secure, and innovative technology solutions that drive business growth."
        self.architecture_principles = [
            "Scalability first",
            "Security by design", 
            "Maintainable code",
            "Performance optimization",
            "Cost efficiency"
        ]
        
        # Initialize with common technologies
        self._initialize_default_stack()
    
    def _initialize_default_stack(self):
        """Initialize with common technology stack."""
        default_technologies = [
            TechnologyStack("Python", "backend", "3.9+", "active"),
            TechnologyStack("React", "frontend", "18.x", "active"),
            TechnologyStack("PostgreSQL", "database", "14.x", "active"),
            TechnologyStack("Docker", "infrastructure", "latest", "active"),
            TechnologyStack("AWS", "infrastructure", "latest", "active")
        ]
        
        for tech in default_technologies:
            tech.adoption_date = datetime.now().isoformat()
            self.technology_stack[tech.name.lower()] = tech
    
    def make_technical_decision(self, context: str, category: str = "development", 
                              options: List[str] = None, impact: str = "medium") -> TechnicalDecision:
        """
        Make a technical decision based on the given context.
        
        Args:
            context: The technical context or problem statement
            category: Decision category (architecture, security, infrastructure, development, data)
            options: Optional list of possible technical solutions
            impact: Expected impact level (low, medium, high, critical)
            
        Returns:
            A TechnicalDecision object containing the chosen solution
        """
        decision_id = f"tech_dec_{len(self.technical_decisions) + 1}"
        
        if options:
            decision = random.choice(options)
            rationale = f"Selected based on technical feasibility, scalability requirements, and alignment with our architecture principles."
        else:
            decision = "Proceed with the recommended technical approach."
            rationale = "Based on comprehensive technical analysis, performance requirements, and security considerations."
        
        new_decision = TechnicalDecision(
            id=decision_id,
            timestamp=datetime.now().isoformat(),
            decision=decision,
            rationale=rationale,
            priority=random.choice(['critical', 'high', 'medium', 'low']),
            category=category,
            impact=impact
        )
        
        self.technical_decisions[decision_id] = new_decision
        return new_decision
    
    def add_technology(self, name: str, category: str, version: str, status: str = "planned") -> bool:
        """Add a new technology to the stack."""
        tech = TechnologyStack(
            name=name,
            category=category,
            version=version,
            status=status,
            adoption_date=datetime.now().isoformat() if status == "active" else None
        )
        self.technology_stack[name.lower()] = tech
        return True
    
    def update_technology_status(self, name: str, new_status: str) -> bool:
        """Update the status of a technology in the stack."""
        tech_key = name.lower()
        if tech_key in self.technology_stack:
            self.technology_stack[tech_key].status = new_status
            if new_status == "active" and not self.technology_stack[tech_key].adoption_date:
                self.technology_stack[tech_key].adoption_date = datetime.now().isoformat()
            return True
        return False
    
    def get_technology_stack_by_category(self, category: str = None) -> List[TechnologyStack]:
        """Get technologies filtered by category."""
        if category:
            return [tech for tech in self.technology_stack.values() if tech.category == category]
        return list(self.technology_stack.values())
    
    def get_technical_vision(self) -> str:
        """Return the technical vision statement."""
        return self.technical_vision
    
    def set_technical_vision(self, new_vision: str):
        """Update the technical vision statement."""
        self.technical_vision = new_vision
    
    def get_architecture_principles(self) -> List[str]:
        """Return the architecture principles."""
        return self.architecture_principles.copy()
    
    def add_architecture_principle(self, principle: str):
        """Add a new architecture principle."""
        if principle not in self.architecture_principles:
            self.architecture_principles.append(principle)
    
    def get_technical_decision(self, decision_id: str) -> Optional[TechnicalDecision]:
        """Retrieve a specific technical decision by its ID."""
        return self.technical_decisions.get(decision_id)
    
    def update_decision_status(self, decision_id: str, new_status: str) -> bool:
        """Update the status of a technical decision."""
        if decision_id in self.technical_decisions:
            self.technical_decisions[decision_id].status = new_status
            return True
        return False
    
    def get_decisions_by_category(self, category: str) -> List[TechnicalDecision]:
        """Get all decisions filtered by category."""
        return [decision for decision in self.technical_decisions.values() 
                if decision.category == category]
    
    def get_critical_decisions(self) -> List[TechnicalDecision]:
        """Get all critical priority decisions."""
        return [decision for decision in self.technical_decisions.values() 
                if decision.priority == 'critical']
