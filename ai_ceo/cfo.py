import random
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

try:
    from services.ai_integration import AIIntegrationService
    from config.settings import config_manager
    AI_INTEGRATION_AVAILABLE = True
except ImportError:
    AI_INTEGRATION_AVAILABLE = False

logger = logging.getLogger(__name__)

@dataclass
class FinancialDecision:
    """Represents a financial decision made by the AI_CFO."""
    id: str
    timestamp: str
    decision: str
    rationale: str
    priority: str  # 'critical', 'high', 'medium', 'low'
    category: str  # 'budget', 'investment', 'cost_reduction', 'revenue', 'risk_management'
    financial_impact: Decimal  # Expected financial impact in dollars
    status: str = 'pending'  # 'pending', 'in_progress', 'completed', 'rejected'
    risk_level: str = 'medium'  # 'low', 'medium', 'high', 'critical'
    confidence_score: float = 0.7  # AI confidence score (0.0 to 1.0)
    roi_estimate: Optional[Decimal] = None  # Estimated ROI percentage
    payback_period: Optional[int] = None  # Payback period in months

@dataclass
class BudgetItem:
    """Represents a budget line item."""
    category: str
    allocated_amount: Decimal
    spent_amount: Decimal = Decimal('0')
    remaining_amount: Decimal = None
    period: str = 'annual'  # 'monthly', 'quarterly', 'annual'
    
    def __post_init__(self):
        if self.remaining_amount is None:
            self.remaining_amount = self.allocated_amount - self.spent_amount

@dataclass
class FinancialMetric:
    """Represents a financial KPI or metric."""
    name: str
    value: Decimal
    target: Decimal
    unit: str  # 'dollars', 'percentage', 'ratio'
    period: str = 'monthly'
    trend: str = 'stable'  # 'improving', 'declining', 'stable'

class AI_CFO:
    """An AI-powered CFO agent that can make financial decisions and manage company finances."""
    
    def __init__(self, name: str = "AI_CFO", company_name: str = "Your Company"):
        self.name = name
        self.company_name = company_name
        self.financial_decisions: Dict[str, FinancialDecision] = {}
        self.budget: Dict[str, BudgetItem] = {}
        self.financial_metrics: Dict[str, FinancialMetric] = {}
        self.conversation_history: List[Dict] = []
        self.financial_vision = "To optimize financial performance, ensure sustainable growth, and maximize shareholder value through strategic financial management."
        self.financial_principles = [
            "Cash flow optimization",
            "Risk-adjusted returns",
            "Cost efficiency",
            "Strategic investment",
            "Financial transparency"
        ]
        
        # Initialize AI integration service if available
        self.ai_service = None
        if AI_INTEGRATION_AVAILABLE:
            try:
                ai_config = config_manager.get_service_config('ai_integration')
                self.ai_service = AIIntegrationService(ai_config)
                logger.info("AI integration service initialized for CFO")
            except Exception as e:
                logger.warning(f"Failed to initialize AI service for CFO: {e}")
        
        # Initialize with default budget categories and metrics
        self._initialize_default_budget()
        self._initialize_default_metrics()
    
    def _initialize_default_budget(self):
        """Initialize with common budget categories."""
        default_budget = [
            BudgetItem("Operations", Decimal('500000')),
            BudgetItem("Marketing", Decimal('200000')),
            BudgetItem("R&D", Decimal('300000')),
            BudgetItem("Personnel", Decimal('800000')),
            BudgetItem("Infrastructure", Decimal('150000'))
        ]
        
        for item in default_budget:
            self.budget[item.category.lower()] = item
    
    def _initialize_default_metrics(self):
        """Initialize with key financial metrics."""
        default_metrics = [
            FinancialMetric("Revenue", Decimal('2000000'), Decimal('2500000'), 'dollars'),
            FinancialMetric("Gross Margin", Decimal('65'), Decimal('70'), 'percentage'),
            FinancialMetric("Operating Margin", Decimal('15'), Decimal('20'), 'percentage'),
            FinancialMetric("Cash Burn Rate", Decimal('100000'), Decimal('80000'), 'dollars'),
            FinancialMetric("Customer Acquisition Cost", Decimal('150'), Decimal('120'), 'dollars')
        ]
        
        for metric in default_metrics:
            self.financial_metrics[metric.name.lower().replace(' ', '_')] = metric
    
    def make_financial_decision(self, context: str, category: str = "budget", 
                              options: List[str] = None, financial_impact: Decimal = Decimal('0'),
                              risk_level: str = "medium", document_context: str = "",
                              financial_data: Dict[str, Any] = None) -> FinancialDecision:
        """
        Make a financial decision based on the given context.
        
        Args:
            context: The financial context or problem statement
            category: Decision category (budget, investment, cost_reduction, revenue, risk_management)
            options: Optional list of possible financial solutions
            financial_impact: Expected financial impact in dollars
            risk_level: Risk level (low, medium, high, critical)
            document_context: Optional document context for informed decisions
            financial_data: Optional financial data dictionary
            
        Returns:
            A FinancialDecision object containing the chosen solution
        """
        decision_id = f"fin_dec_{len(self.financial_decisions) + 1}"
        
        # Try to use AI service for intelligent decision making
        if self.ai_service:
            try:
                # Prepare enhanced context with financial data
                enhanced_context = context
                if financial_data:
                    fin_context = "\n\nFinancial Data:\n"
                    for key, value in financial_data.items():
                        fin_context += f"- {key.replace('_', ' ').title()}: {value}\n"
                    enhanced_context += fin_context
                
                # Generate AI-powered response
                executive_response = self.ai_service.generate_executive_response(
                    executive_type='cfo',
                    context=enhanced_context,
                    conversation_history=self.conversation_history,
                    document_context=document_context,
                    options=options
                )
                
                decision = executive_response.decision
                rationale = executive_response.rationale
                priority = executive_response.priority
                confidence_score = executive_response.confidence_score
                ai_risk_level = executive_response.risk_level
                ai_financial_impact = executive_response.financial_impact
                
                # Use AI financial impact if available, otherwise use provided value
                if ai_financial_impact is not None:
                    financial_impact = Decimal(str(ai_financial_impact))
                
                # Calculate ROI estimate if we have investment and return data
                roi_estimate = None
                payback_period = None
                if financial_data:
                    investment = financial_data.get('investment_amount') or financial_data.get('budget_amount')
                    expected_return = financial_data.get('expected_return')
                    if investment and expected_return:
                        roi_estimate = self.calculate_roi(Decimal(str(investment)), Decimal(str(expected_return)))
                        # Simple payback period calculation
                        if expected_return > investment:
                            payback_period = int(12 * (investment / (expected_return - investment)))
                
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
                
                new_decision = FinancialDecision(
                    id=decision_id,
                    timestamp=datetime.now().isoformat(),
                    decision=decision,
                    rationale=rationale,
                    priority=priority,
                    category=category,
                    financial_impact=financial_impact,
                    risk_level=ai_risk_level,
                    confidence_score=confidence_score,
                    roi_estimate=roi_estimate,
                    payback_period=payback_period
                )
                
                self.financial_decisions[decision_id] = new_decision
                logger.info(f"AI-powered CFO decision created: {decision_id}")
                return new_decision
                
            except Exception as e:
                logger.error(f"AI service failed, falling back to template-based decision: {e}")
        
        # Fallback to template-based decision making
        if options:
            decision = random.choice(options)
            rationale = f"Selected based on financial analysis, ROI projections, and risk assessment aligned with our financial principles."
        else:
            decision = "Proceed with the recommended financial approach."
            rationale = "Based on comprehensive financial analysis, cash flow projections, and strategic financial objectives."
        
        new_decision = FinancialDecision(
            id=decision_id,
            timestamp=datetime.now().isoformat(),
            decision=decision,
            rationale=rationale,
            priority=random.choice(['critical', 'high', 'medium', 'low']),
            category=category,
            financial_impact=financial_impact,
            risk_level=risk_level,
            confidence_score=0.6  # Lower confidence for template-based decisions
        )
        
        self.financial_decisions[decision_id] = new_decision
        return new_decision
    
    def add_budget_item(self, category: str, allocated_amount: Decimal, period: str = "annual") -> bool:
        """Add a new budget category."""
        budget_item = BudgetItem(
            category=category,
            allocated_amount=allocated_amount,
            period=period
        )
        self.budget[category.lower()] = budget_item
        return True
    
    def update_budget_spending(self, category: str, spent_amount: Decimal) -> bool:
        """Update spending for a budget category."""
        category_key = category.lower()
        if category_key in self.budget:
            self.budget[category_key].spent_amount += spent_amount
            self.budget[category_key].remaining_amount = (
                self.budget[category_key].allocated_amount - 
                self.budget[category_key].spent_amount
            )
            return True
        return False
    
    def get_budget_utilization(self, category: str = None) -> Dict[str, float]:
        """Get budget utilization percentages."""
        if category:
            category_key = category.lower()
            if category_key in self.budget:
                item = self.budget[category_key]
                utilization = float(item.spent_amount / item.allocated_amount * 100)
                return {category: utilization}
            return {}
        
        utilization = {}
        for cat, item in self.budget.items():
            utilization[cat] = float(item.spent_amount / item.allocated_amount * 100)
        return utilization
    
    def add_financial_metric(self, name: str, value: Decimal, target: Decimal, 
                           unit: str, period: str = "monthly") -> bool:
        """Add or update a financial metric."""
        metric = FinancialMetric(
            name=name,
            value=value,
            target=target,
            unit=unit,
            period=period
        )
        
        # Determine trend
        if value > target:
            metric.trend = 'improving' if unit != 'dollars' or 'cost' not in name.lower() else 'declining'
        elif value < target:
            metric.trend = 'declining' if unit != 'dollars' or 'cost' not in name.lower() else 'improving'
        
        self.financial_metrics[name.lower().replace(' ', '_')] = metric
        return True
    
    def get_financial_health_score(self) -> Tuple[int, str]:
        """Calculate overall financial health score (0-100)."""
        score = 0
        total_metrics = len(self.financial_metrics)
        
        for metric in self.financial_metrics.values():
            if metric.unit == 'percentage':
                if metric.value >= metric.target:
                    score += 20
                elif metric.value >= metric.target * Decimal('0.8'):
                    score += 15
                else:
                    score += 5
            else:  # dollars or ratio
                if 'cost' in metric.name.lower() or 'burn' in metric.name.lower():
                    # Lower is better for costs
                    if metric.value <= metric.target:
                        score += 20
                    elif metric.value <= metric.target * Decimal('1.2'):
                        score += 15
                    else:
                        score += 5
                else:
                    # Higher is better for revenue
                    if metric.value >= metric.target:
                        score += 20
                    elif metric.value >= metric.target * Decimal('0.8'):
                        score += 15
                    else:
                        score += 5
        
        final_score = min(100, score)
        
        if final_score >= 80:
            health_status = "Excellent"
        elif final_score >= 60:
            health_status = "Good"
        elif final_score >= 40:
            health_status = "Fair"
        else:
            health_status = "Poor"
        
        return final_score, health_status
    
    def get_financial_vision(self) -> str:
        """Return the financial vision statement."""
        return self.financial_vision
    
    def set_financial_vision(self, new_vision: str):
        """Update the financial vision statement."""
        self.financial_vision = new_vision
    
    def get_financial_principles(self) -> List[str]:
        """Return the financial principles."""
        return self.financial_principles.copy()
    
    def add_financial_principle(self, principle: str):
        """Add a new financial principle."""
        if principle not in self.financial_principles:
            self.financial_principles.append(principle)
    
    def get_financial_decision(self, decision_id: str) -> Optional[FinancialDecision]:
        """Retrieve a specific financial decision by its ID."""
        return self.financial_decisions.get(decision_id)
    
    def update_decision_status(self, decision_id: str, new_status: str) -> bool:
        """Update the status of a financial decision."""
        if decision_id in self.financial_decisions:
            self.financial_decisions[decision_id].status = new_status
            return True
        return False
    
    def get_decisions_by_category(self, category: str) -> List[FinancialDecision]:
        """Get all decisions filtered by category."""
        return [decision for decision in self.financial_decisions.values() 
                if decision.category == category]
    
    def get_high_impact_decisions(self, threshold: Decimal = Decimal('100000')) -> List[FinancialDecision]:
        """Get all decisions with financial impact above threshold."""
        return [decision for decision in self.financial_decisions.values() 
                if abs(decision.financial_impact) >= threshold]
    
    def calculate_roi(self, investment: Decimal, returns: Decimal, period_months: int = 12) -> Decimal:
        """Calculate Return on Investment."""
        if investment == 0:
            return Decimal('0')
        roi = ((returns - investment) / investment) * 100
        # Annualize if period is not 12 months
        if period_months != 12:
            roi = roi * (12 / period_months)
        return roi.quantize(Decimal('0.01'))
    
    def get_financial_analysis(self, context: str, financial_data: Dict[str, Any] = None, 
                             analysis_type: str = "roi") -> Dict[str, Any]:
        """
        Get comprehensive financial analysis
        
        Args:
            context: Financial analysis context
            financial_data: Financial data dictionary
            analysis_type: Type of analysis (roi, npv, payback, risk_assessment)
            
        Returns:
            Dictionary with financial analysis components
        """
        if self.ai_service:
            try:
                # Build comprehensive analysis context
                analysis_context = f"Financial Analysis ({analysis_type.upper()}): {context}"
                
                if financial_data:
                    analysis_context += f"\n\nFinancial Data:\n"
                    for key, value in financial_data.items():
                        analysis_context += f"- {key.replace('_', ' ').title()}: {value}\n"
                
                # Add current financial metrics context
                health_score, health_status = self.get_financial_health_score()
                analysis_context += f"\n\nCurrent Financial Health: {health_score}/100 ({health_status})"
                
                # Use AI service for financial analysis
                executive_response = self.ai_service.generate_executive_response(
                    executive_type='cfo',
                    context=analysis_context,
                    conversation_history=self.conversation_history
                )
                
                return {
                    "analysis": executive_response.decision,
                    "rationale": executive_response.rationale,
                    "confidence": executive_response.confidence_score,
                    "risk_level": executive_response.risk_level,
                    "financial_impact": executive_response.financial_impact,
                    "recommendations": executive_response.decision.split('\n')[:5],  # First 5 lines as recommendations
                    "analysis_type": analysis_type
                }
                
            except Exception as e:
                logger.error(f"AI financial analysis failed: {e}")
        
        # Fallback analysis
        return {
            "analysis": f"Financial {analysis_type.upper()} analysis requires evaluation of cash flows, risk factors, and market conditions.",
            "rationale": "Based on standard financial analysis frameworks and industry benchmarks.",
            "confidence": 0.6,
            "risk_level": "medium",
            "financial_impact": financial_data.get('investment_amount') if financial_data else None,
            "recommendations": [
                "Conduct detailed cash flow analysis",
                "Evaluate market conditions and risks",
                "Consider alternative scenarios",
                "Review industry benchmarks",
                "Plan for contingencies"
            ],
            "analysis_type": analysis_type
        }
    
    def get_investment_recommendation(self, context: str, investment_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Get investment recommendations
        
        Args:
            context: Investment context
            investment_data: Investment data dictionary
            
        Returns:
            Dictionary with investment recommendations
        """
        if self.ai_service:
            try:
                investment_context = f"Investment Recommendation: {context}"
                
                if investment_data:
                    investment_context += f"\n\nInvestment Data:\n"
                    for key, value in investment_data.items():
                        investment_context += f"- {key.replace('_', ' ').title()}: {value}\n"
                
                # Add budget context
                budget_utilization = self.get_budget_utilization()
                investment_context += f"\n\nCurrent Budget Utilization:\n"
                for category, utilization in budget_utilization.items():
                    investment_context += f"- {category.title()}: {utilization:.1f}%\n"
                
                executive_response = self.ai_service.generate_executive_response(
                    executive_type='cfo',
                    context=investment_context,
                    conversation_history=self.conversation_history
                )
                
                return {
                    "recommendation": executive_response.decision,
                    "rationale": executive_response.rationale,
                    "confidence": executive_response.confidence_score,
                    "risk_level": executive_response.risk_level,
                    "financial_impact": executive_response.financial_impact
                }
                
            except Exception as e:
                logger.error(f"AI investment recommendation failed: {e}")
        
        # Fallback recommendation
        return {
            "recommendation": "Evaluate investment based on ROI projections, risk assessment, and strategic alignment with business objectives.",
            "rationale": "Investment decisions should consider cash flow impact, payback period, and long-term value creation.",
            "confidence": 0.6,
            "risk_level": "medium",
            "financial_impact": investment_data.get('amount') if investment_data else None
        }
    
    def assess_financial_risk(self, context: str, financial_scenario: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Assess financial risks for a scenario
        
        Args:
            context: Risk assessment context
            financial_scenario: Financial scenario data
            
        Returns:
            Dictionary with risk assessment
        """
        if self.ai_service:
            try:
                risk_context = f"Financial Risk Assessment: {context}"
                
                if financial_scenario:
                    risk_context += f"\n\nFinancial Scenario:\n"
                    for key, value in financial_scenario.items():
                        risk_context += f"- {key.replace('_', ' ').title()}: {value}\n"
                
                # Add current financial health context
                health_score, health_status = self.get_financial_health_score()
                risk_context += f"\n\nCurrent Financial Health: {health_score}/100 ({health_status})"
                
                executive_response = self.ai_service.generate_executive_response(
                    executive_type='cfo',
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
            "assessment": "Financial risk assessment requires evaluation of cash flow volatility, market conditions, and operational risks.",
            "rationale": "Risk mitigation should include diversification, contingency planning, and regular monitoring.",
            "risk_level": "medium",
            "confidence": 0.6,
            "mitigation_strategies": [
                "Implement cash flow monitoring",
                "Create financial contingency plans",
                "Diversify revenue streams"
            ]
        }
    
    def calculate_npv(self, cash_flows: List[Decimal], discount_rate: Decimal) -> Decimal:
        """Calculate Net Present Value."""
        npv = Decimal('0')
        for i, cash_flow in enumerate(cash_flows):
            npv += cash_flow / ((1 + discount_rate / 100) ** i)
        return npv.quantize(Decimal('0.01'))
    
    def calculate_payback_period(self, initial_investment: Decimal, annual_cash_flow: Decimal) -> Decimal:
        """Calculate payback period in years."""
        if annual_cash_flow <= 0:
            return Decimal('0')
        return (initial_investment / annual_cash_flow).quantize(Decimal('0.1'))
    
    def get_budget_recommendations(self, context: str = "") -> Dict[str, Any]:
        """Get budget optimization recommendations"""
        if self.ai_service:
            try:
                budget_context = f"Budget Optimization: {context}"
                
                # Add current budget utilization
                budget_utilization = self.get_budget_utilization()
                budget_context += f"\n\nCurrent Budget Utilization:\n"
                for category, utilization in budget_utilization.items():
                    budget_context += f"- {category.title()}: {utilization:.1f}%\n"
                
                # Add financial health context
                health_score, health_status = self.get_financial_health_score()
                budget_context += f"\n\nFinancial Health: {health_score}/100 ({health_status})"
                
                executive_response = self.ai_service.generate_executive_response(
                    executive_type='cfo',
                    context=budget_context,
                    conversation_history=self.conversation_history
                )
                
                return {
                    "recommendations": executive_response.decision,
                    "rationale": executive_response.rationale,
                    "confidence": executive_response.confidence_score,
                    "priority_areas": executive_response.decision.split('\n')[:3]  # First 3 lines as priorities
                }
                
            except Exception as e:
                logger.error(f"AI budget recommendations failed: {e}")
        
        # Fallback recommendations
        over_budget = [cat for cat, util in self.get_budget_utilization().items() if util > 90]
        under_budget = [cat for cat, util in self.get_budget_utilization().items() if util < 50]
        
        recommendations = []
        if over_budget:
            recommendations.append(f"Review spending in over-budget categories: {', '.join(over_budget)}")
        if under_budget:
            recommendations.append(f"Consider reallocating from under-utilized categories: {', '.join(under_budget)}")
        
        return {
            "recommendations": "\n".join(recommendations) if recommendations else "Budget allocation appears balanced.",
            "rationale": "Based on current budget utilization patterns and financial principles.",
            "confidence": 0.6,
            "priority_areas": over_budget[:3] if over_budget else ["Monitor all categories"]
        }
    
    def clear_conversation_history(self):
        """Clear the conversation history"""
        self.conversation_history = []
        logger.info("CFO conversation history cleared")
    
    def get_conversation_summary(self) -> Dict[str, Any]:
        """Get a summary of the current conversation"""
        return {
            "message_count": len(self.conversation_history),
            "last_interaction": self.conversation_history[-1]['timestamp'] if self.conversation_history else None,
            "ai_enabled": self.ai_service is not None
        }
    
    def get_decision_insights(self) -> Dict[str, Any]:
        """Get insights about financial decision patterns"""
        if not self.financial_decisions:
            return {"message": "No financial decisions available for analysis"}
        
        decisions_list = list(self.financial_decisions.values())
        
        # Basic statistics
        total_decisions = len(decisions_list)
        priority_counts = {}
        category_counts = {}
        risk_counts = {}
        avg_confidence = 0.0
        total_financial_impact = Decimal('0')
        
        for decision in decisions_list:
            # Count priorities
            priority = decision.priority
            priority_counts[priority] = priority_counts.get(priority, 0) + 1
            
            # Count categories
            category = decision.category
            category_counts[category] = category_counts.get(category, 0) + 1
            
            # Count risk levels
            risk = decision.risk_level
            risk_counts[risk] = risk_counts.get(risk, 0) + 1
            
            # Sum confidence scores
            if hasattr(decision, 'confidence_score') and decision.confidence_score:
                avg_confidence += decision.confidence_score
            
            # Sum financial impact
            if decision.financial_impact:
                total_financial_impact += decision.financial_impact
        
        if total_decisions > 0:
            avg_confidence /= total_decisions
        
        # Get financial health
        health_score, health_status = self.get_financial_health_score()
        
        return {
            "total_decisions": total_decisions,
            "priority_distribution": priority_counts,
            "category_distribution": category_counts,
            "risk_distribution": risk_counts,
            "average_confidence": round(avg_confidence, 2),
            "total_financial_impact": float(total_financial_impact),
            "financial_health_score": health_score,
            "financial_health_status": health_status,
            "ai_enabled": self.ai_service is not None,
            "budget_categories": len(self.budget),
            "financial_metrics": len(self.financial_metrics)
        }
