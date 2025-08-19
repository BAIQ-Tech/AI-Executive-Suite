import random
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class Decision:
    """Represents a business decision made by the AI_CEO."""
    id: str
    timestamp: str
    decision: str
    rationale: str
    priority: str  # 'high', 'medium', 'low'
    status: str = 'pending'  # 'pending', 'in_progress', 'completed', 'rejected'

class AI_CEO:
    """An AI-powered CEO agent that can make business decisions and provide strategic guidance."""
    
    def __init__(self, name: str = "AI_CEO", company_name: str = "Your Company", language: str = "en"):
        self.name = name
        self.company_name = company_name
        self.language = language
        self.decisions: Dict[str, Decision] = {}
        
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
    
    def make_decision(self, context: str, options: List[str] = None) -> Decision:
        """
        Make a strategic business decision based on the given context.
        
        Args:
            context: The business context or problem statement
            options: Optional list of possible decisions to choose from
            
        Returns:
            A Decision object containing the chosen course of action
        """
        decision_id = f"dec_{len(self.decisions) + 1}"
        
        # Multilingual decision templates
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
        
        # In a real implementation, this would use an LLM to analyze the context
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
            priority=random.choice(['high', 'medium', 'low'])
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
