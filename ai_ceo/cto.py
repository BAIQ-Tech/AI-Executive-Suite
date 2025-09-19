import random
import logging
from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass
from datetime import datetime

try:
    from services.ai_integration import AIIntegrationService
    from config.settings import config_manager
    AI_INTEGRATION_AVAILABLE = True
except ImportError:
    AI_INTEGRATION_AVAILABLE = False

logger = logging.getLogger(__name__)

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
    confidence_score: float = 0.7  # AI confidence score (0.0 to 1.0)
    risk_level: str = 'medium'  # 'low', 'medium', 'high', 'critical'

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
        self.conversation_history: List[Dict] = []
        self.technical_vision = "To build scalable, secure, and innovative technology solutions that drive business growth."
        self.architecture_principles = [
            "Scalability first",
            "Security by design", 
            "Maintainable code",
            "Performance optimization",
            "Cost efficiency"
        ]
        
        # Initialize AI integration service if available
        self.ai_service = None
        if AI_INTEGRATION_AVAILABLE:
            try:
                ai_config = config_manager.get_service_config('ai_integration')
                self.ai_service = AIIntegrationService(ai_config)
                logger.info("AI integration service initialized for CTO")
            except Exception as e:
                logger.warning(f"Failed to initialize AI service for CTO: {e}")
        
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
                              options: List[str] = None, impact: str = "medium", 
                              document_context: str = "", technical_requirements: Dict[str, str] = None) -> TechnicalDecision:
        """
        Make a technical decision based on the given context.
        
        Args:
            context: The technical context or problem statement
            category: Decision category (architecture, security, infrastructure, development, data)
            options: Optional list of possible technical solutions
            impact: Expected impact level (low, medium, high, critical)
            document_context: Optional document context for informed decisions
            technical_requirements: Optional technical requirements dictionary
            
        Returns:
            A TechnicalDecision object containing the chosen solution
        """
        decision_id = f"tech_dec_{len(self.technical_decisions) + 1}"
        
        # Try to use AI service for intelligent decision making
        if self.ai_service:
            try:
                # Prepare enhanced context with technical requirements
                enhanced_context = context
                if technical_requirements:
                    req_context = "\n\nTechnical Requirements:\n"
                    for req, level in technical_requirements.items():
                        req_context += f"- {req.title()}: {level}\n"
                    enhanced_context += req_context
                
                # Generate AI-powered response
                executive_response = self.ai_service.generate_executive_response(
                    executive_type='cto',
                    context=enhanced_context,
                    conversation_history=self.conversation_history,
                    document_context=document_context,
                    options=options
                )
                
                decision = executive_response.decision
                rationale = executive_response.rationale
                priority = executive_response.priority
                confidence_score = executive_response.confidence_score
                risk_level = executive_response.risk_level
                
                # Update conversation history
                self.conversation_history.append({
                    'role': 'user',
                    'content': enhanced_context,
                    'timestamp': datetime.now().isoformat()
                })
                self.conversation_history.append({
                    'role': 'assistant',
                    'content': decision,
                    'timestamp': datetime.now().isoformat()
                })
                
                # Keep conversation history manageable
                if len(self.conversation_history) > 20:
                    self.conversation_history = self.conversation_history[-20:]
                
                new_decision = TechnicalDecision(
                    id=decision_id,
                    timestamp=datetime.now().isoformat(),
                    decision=decision,
                    rationale=rationale,
                    priority=priority,
                    category=category,
                    impact=impact,
                    confidence_score=confidence_score,
                    risk_level=risk_level
                )
                
                self.technical_decisions[decision_id] = new_decision
                logger.info(f"AI-powered CTO decision created: {decision_id}")
                return new_decision
                
            except Exception as e:
                logger.error(f"AI service failed, falling back to template-based decision: {e}")
        
        # Fallback to template-based decision making
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
            impact=impact,
            confidence_score=0.6,  # Lower confidence for template-based decisions
            risk_level='medium'
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
    
    def get_architecture_analysis(self, context: str, current_architecture: str = "", 
                                requirements: List[str] = None, constraints: List[str] = None) -> Dict[str, Any]:
        """
        Get technical architecture analysis
        
        Args:
            context: Architecture analysis context
            current_architecture: Description of current system
            requirements: List of requirements
            constraints: List of constraints
            
        Returns:
            Dictionary with architecture analysis components
        """
        if self.ai_service:
            try:
                # Build comprehensive analysis context
                analysis_context = f"Architecture Analysis: {context}"
                
                if current_architecture:
                    analysis_context += f"\n\nCurrent Architecture: {current_architecture}"
                
                if requirements:
                    analysis_context += f"\n\nRequirements:\n" + "\n".join(f"- {req}" for req in requirements)
                
                if constraints:
                    analysis_context += f"\n\nConstraints:\n" + "\n".join(f"- {constraint}" for constraint in constraints)
                
                # Use AI service for architecture analysis
                executive_response = self.ai_service.generate_executive_response(
                    executive_type='cto',
                    context=analysis_context,
                    conversation_history=self.conversation_history
                )
                
                return {
                    "analysis": executive_response.decision,
                    "rationale": executive_response.rationale,
                    "confidence": executive_response.confidence_score,
                    "risk_level": executive_response.risk_level,
                    "category": executive_response.category,
                    "recommendations": executive_response.decision.split('\n')[:5]  # First 5 lines as recommendations
                }
                
            except Exception as e:
                logger.error(f"AI architecture analysis failed: {e}")
        
        # Fallback analysis
        return {
            "analysis": "Technical architecture analysis requires evaluation of scalability, maintainability, security, and performance requirements.",
            "rationale": "Based on standard architectural patterns and best practices.",
            "confidence": 0.6,
            "risk_level": "medium",
            "category": "architecture",
            "recommendations": [
                "Conduct thorough requirements analysis",
                "Evaluate existing system constraints",
                "Consider scalability requirements",
                "Assess security implications",
                "Plan for maintainability"
            ]
        }
    
    def get_technology_recommendation(self, context: str, category: str = "general") -> Dict[str, Any]:
        """
        Get technology stack recommendations
        
        Args:
            context: Technology selection context
            category: Technology category (frontend, backend, database, etc.)
            
        Returns:
            Dictionary with technology recommendations
        """
        if self.ai_service:
            try:
                tech_context = f"Technology Recommendation for {category}: {context}"
                
                # Add current stack context
                current_stack = self.get_technology_stack_by_category(category)
                if current_stack:
                    tech_context += f"\n\nCurrent {category} technologies:\n"
                    for tech in current_stack:
                        tech_context += f"- {tech.name} {tech.version} ({tech.status})\n"
                
                executive_response = self.ai_service.generate_executive_response(
                    executive_type='cto',
                    context=tech_context,
                    conversation_history=self.conversation_history
                )
                
                return {
                    "recommendation": executive_response.decision,
                    "rationale": executive_response.rationale,
                    "confidence": executive_response.confidence_score,
                    "risk_level": executive_response.risk_level,
                    "category": category
                }
                
            except Exception as e:
                logger.error(f"AI technology recommendation failed: {e}")
        
        # Fallback recommendation
        return {
            "recommendation": f"Evaluate {category} technologies based on scalability, maintainability, team expertise, and long-term support.",
            "rationale": "Technology selection should align with team capabilities and business requirements.",
            "confidence": 0.6,
            "risk_level": "medium",
            "category": category
        }
    
    def assess_technical_risk(self, context: str, proposed_solution: str = "") -> Dict[str, Any]:
        """
        Assess technical risks for a proposed solution
        
        Args:
            context: Risk assessment context
            proposed_solution: Proposed technical solution
            
        Returns:
            Dictionary with risk assessment
        """
        if self.ai_service:
            try:
                risk_context = f"Technical Risk Assessment: {context}"
                
                if proposed_solution:
                    risk_context += f"\n\nProposed Solution: {proposed_solution}"
                
                executive_response = self.ai_service.generate_executive_response(
                    executive_type='cto',
                    context=risk_context,
                    conversation_history=self.conversation_history
                )
                
                return {
                    "assessment": executive_response.decision,
                    "rationale": executive_response.rationale,
                    "risk_level": executive_response.risk_level,
                    "confidence": executive_response.confidence_score,
                    "mitigation_strategies": executive_response.decision.split('\n')[-3:]  # Last 3 lines as mitigation
                }
                
            except Exception as e:
                logger.error(f"AI risk assessment failed: {e}")
        
        # Fallback risk assessment
        return {
            "assessment": "Technical risk assessment requires evaluation of complexity, dependencies, team expertise, and potential failure points.",
            "rationale": "Risk mitigation should include thorough testing, documentation, and rollback plans.",
            "risk_level": "medium",
            "confidence": 0.6,
            "mitigation_strategies": [
                "Implement comprehensive testing",
                "Create detailed documentation",
                "Plan rollback procedures"
            ]
        }
    
    def clear_conversation_history(self):
        """Clear the conversation history"""
        self.conversation_history = []
        logger.info("CTO conversation history cleared")
    
    def get_conversation_summary(self) -> Dict[str, Any]:
        """Get a summary of the current conversation"""
        return {
            "message_count": len(self.conversation_history),
            "last_interaction": self.conversation_history[-1]['timestamp'] if self.conversation_history else None,
            "ai_enabled": self.ai_service is not None
        }
    
    def get_decision_insights(self) -> Dict[str, Any]:
        """Get insights about technical decision patterns"""
        if not self.technical_decisions:
            return {"message": "No technical decisions available for analysis"}
        
        decisions_list = list(self.technical_decisions.values())
        
        # Basic statistics
        total_decisions = len(decisions_list)
        priority_counts = {}
        category_counts = {}
        impact_counts = {}
        avg_confidence = 0.0
        
        for decision in decisions_list:
            # Count priorities
            priority = decision.priority
            priority_counts[priority] = priority_counts.get(priority, 0) + 1
            
            # Count categories
            category = decision.category
            category_counts[category] = category_counts.get(category, 0) + 1
            
            # Count impacts
            impact = decision.impact
            impact_counts[impact] = impact_counts.get(impact, 0) + 1
            
            # Sum confidence scores
            if hasattr(decision, 'confidence_score') and decision.confidence_score:
                avg_confidence += decision.confidence_score
        
        if total_decisions > 0:
            avg_confidence /= total_decisions
        
        return {
            "total_decisions": total_decisions,
            "priority_distribution": priority_counts,
            "category_distribution": category_counts,
            "impact_distribution": impact_counts,
            "average_confidence": round(avg_confidence, 2),
            "ai_enabled": self.ai_service is not None,
            "technology_stack_size": len(self.technology_stack)
        }
