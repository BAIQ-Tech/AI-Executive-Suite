import random
import logging
from typing import Dict, List, Optional, Any
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
class Decision:
    """Represents a business decision made by the AI_CEO."""
    id: str
    timestamp: str
    decision: str
    rationale: str
    priority: str  # 'high', 'medium', 'low'
    status: str = 'pending'  # 'pending', 'in_progress', 'completed', 'rejected'
    confidence_score: float = 0.7  # AI confidence score (0.0 to 1.0)

class AI_CEO:
    """An AI-powered CEO agent that can make business decisions and provide strategic guidance."""
    
    def __init__(self, name: str = "AI_CEO", company_name: str = "Your Company", language: str = "en"):
        self.name = name
        self.company_name = company_name
        self.language = language
        self.decisions: Dict[str, Decision] = {}
        self.conversation_history: List[Dict] = []
        
        # Initialize AI integration service if available
        self.ai_service = None
        if AI_INTEGRATION_AVAILABLE:
            try:
                ai_config = config_manager.get_service_config('ai_integration')
                self.ai_service = AIIntegrationService(ai_config)
                logger.info("AI integration service initialized for CEO")
            except Exception as e:
                logger.warning(f"Failed to initialize AI service for CEO: {e}")
        
        # Multilingual vision and mission statements
        self._visions = {
            "en": f"To be the most innovative and customer-centric company in our industry.",
            "ja": f"私たちの業界で最も革新的で顧客中心の企業になること。",
            "zh": f"成为我们行业中最具创新性和以客户为中心的公司。"
        }
        
        self._missions = {
            "en": f"To deliver exceptional value to our customers, employees, and stakeholders through cutting-edge technology and outstanding service.",
            "ja": f"最先端技術と優れたサービスを通じて、お客様、従業員、ステークホルダーに卓越した価値を提供すること。",
            "zh": f"通过前沿技术和卓越服务，为我们的客户、员工和利益相关者提供卓越价值。"
        }
        
        self.vision = self._visions.get(language, self._visions["en"])
        self.mission = self._missions.get(language, self._missions["en"])
    
    def make_decision(self, context: str, options: List[str] = None, document_context: str = "") -> Decision:
        """
        Make a strategic business decision based on the given context.
        
        Args:
            context: The business context or problem statement
            options: Optional list of possible decisions to choose from
            document_context: Optional document context for informed decisions
            
        Returns:
            A Decision object containing the chosen course of action
        """
        decision_id = f"dec_{len(self.decisions) + 1}"
        
        # Try to use AI service for intelligent decision making
        if self.ai_service:
            try:
                # Generate AI-powered response
                executive_response = self.ai_service.generate_executive_response(
                    executive_type='ceo',
                    context=context,
                    conversation_history=self.conversation_history,
                    document_context=document_context,
                    options=options
                )
                
                decision = executive_response.decision
                rationale = executive_response.rationale
                priority = executive_response.priority
                confidence_score = executive_response.confidence_score
                
                # Update conversation history
                self.conversation_history.append({
                    'role': 'user',
                    'content': context,
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
                
                new_decision = Decision(
                    id=decision_id,
                    timestamp=datetime.now().isoformat(),
                    decision=decision,
                    rationale=rationale,
                    priority=priority,
                    confidence_score=confidence_score
                )
                
                self.decisions[decision_id] = new_decision
                logger.info(f"AI-powered CEO decision created: {decision_id}")
                return new_decision
                
            except Exception as e:
                logger.error(f"AI service failed, falling back to template-based decision: {e}")
        
        # Fallback to template-based decision making
        decision_templates = {
            "en": {
                "with_options": "Selected the most strategic option based on current business priorities.",
                "default": "Proceed with the recommended course of action.",
                "rationale_with_options": "Based on comprehensive analysis of available data and business objectives.",
                "rationale_default": "Based on comprehensive analysis of available data and business objectives."
            },
            "ja": {
                "with_options": "現在のビジネス優先度に基づいて最も戦略的な選択肢を選択しました。",
                "default": "推奨される行動方針に従って進めます。",
                "rationale_with_options": "利用可能なデータとビジネス目標の包括的な分析に基づいています。",
                "rationale_default": "利用可能なデータとビジネス目標の包括的な分析に基づいています。"
            },
            "zh": {
                "with_options": "基于当前业务优先级选择了最具战略性的选项。",
                "default": "按照推荐的行动方案进行。",
                "rationale_with_options": "基于对可用数据和业务目标的全面分析。",
                "rationale_default": "基于对可用数据和业务目标的全面分析。"
            }
        }
        
        templates = decision_templates.get(self.language, decision_templates["en"])
        
        if options:
            decision = random.choice(options)
            rationale = templates["rationale_with_options"]
        else:
            decision = templates["default"]
            rationale = templates["rationale_default"]
        
        new_decision = Decision(
            id=decision_id,
            timestamp=datetime.now().isoformat(),
            decision=decision,
            rationale=rationale,
            priority=random.choice(['high', 'medium', 'low']),
            confidence_score=0.6  # Lower confidence for template-based decisions
        )
        
        self.decisions[decision_id] = new_decision
        return new_decision
    
    def get_vision_statement(self) -> str:
        """Return the company's vision statement."""
        return self.vision
    
    def get_mission_statement(self) -> str:
        """Return the company's mission statement."""
        return self.mission
    
    def set_vision(self, new_vision: str):
        """Update the company's vision statement."""
        self.vision = new_vision
        
    def set_mission(self, new_mission: str):
        """Update the company's mission statement."""
        self.mission = new_mission
    
    def set_language(self, language: str):
        """Change the language and update vision/mission statements accordingly."""
        self.language = language
        self.vision = self._visions.get(language, self._visions["en"])
        self.mission = self._missions.get(language, self._missions["en"])
    
    def get_decision(self, decision_id: str) -> Optional[Decision]:
        """Retrieve a specific decision by its ID."""
        return self.decisions.get(decision_id)
    
    def update_decision_status(self, decision_id: str, new_status: str) -> bool:
        """Update the status of a decision."""
        if decision_id in self.decisions:
            self.decisions[decision_id].status = new_status
            return True
        return False
    
    def get_strategic_analysis(self, context: str, document_context: str = "") -> Dict[str, str]:
        """
        Get strategic analysis for a business situation
        
        Args:
            context: Business situation to analyze
            document_context: Optional document context
            
        Returns:
            Dictionary with strategic analysis components
        """
        if self.ai_service:
            try:
                # Use AI service for strategic analysis
                executive_response = self.ai_service.generate_executive_response(
                    executive_type='ceo',
                    context=f"Provide strategic analysis for: {context}",
                    conversation_history=self.conversation_history,
                    document_context=document_context
                )
                
                return {
                    "analysis": executive_response.decision,
                    "rationale": executive_response.rationale,
                    "confidence": str(executive_response.confidence_score),
                    "risk_level": executive_response.risk_level,
                    "category": executive_response.category
                }
                
            except Exception as e:
                logger.error(f"AI strategic analysis failed: {e}")
        
        # Fallback analysis
        return {
            "analysis": "Strategic analysis requires comprehensive evaluation of market conditions, competitive landscape, and organizational capabilities.",
            "rationale": "Based on standard strategic frameworks and business best practices.",
            "confidence": "0.6",
            "risk_level": "medium",
            "category": "strategic"
        }
    
    def clear_conversation_history(self):
        """Clear the conversation history"""
        self.conversation_history = []
        logger.info("CEO conversation history cleared")
    
    def get_conversation_summary(self) -> Dict[str, Any]:
        """Get a summary of the current conversation"""
        return {
            "message_count": len(self.conversation_history),
            "last_interaction": self.conversation_history[-1]['timestamp'] if self.conversation_history else None,
            "ai_enabled": self.ai_service is not None
        }
    
    def set_document_context(self, document_context: str):
        """Set document context for future decisions"""
        self.document_context = document_context
        logger.info("Document context updated for CEO")
    
    def get_decision_insights(self) -> Dict[str, Any]:
        """Get insights about decision patterns"""
        if not self.decisions:
            return {"message": "No decisions available for analysis"}
        
        decisions_list = list(self.decisions.values())
        
        # Basic statistics
        total_decisions = len(decisions_list)
        priority_counts = {}
        status_counts = {}
        avg_confidence = 0.0
        
        for decision in decisions_list:
            # Count priorities
            priority = decision.priority
            priority_counts[priority] = priority_counts.get(priority, 0) + 1
            
            # Count statuses
            status = decision.status
            status_counts[status] = status_counts.get(status, 0) + 1
            
            # Sum confidence scores
            if hasattr(decision, 'confidence_score') and decision.confidence_score:
                avg_confidence += decision.confidence_score
        
        if total_decisions > 0:
            avg_confidence /= total_decisions
        
        return {
            "total_decisions": total_decisions,
            "priority_distribution": priority_counts,
            "status_distribution": status_counts,
            "average_confidence": round(avg_confidence, 2),
            "ai_enabled": self.ai_service is not None
        }
