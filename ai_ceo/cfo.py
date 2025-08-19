import random
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

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
        self.financial_vision = "To optimize financial performance, ensure sustainable growth, and maximize shareholder value through strategic financial management."
        self.financial_principles = [
            "Cash flow optimization",
            "Risk-adjusted returns",
            "Cost efficiency",
            "Strategic investment",
            "Financial transparency"
        ]
        
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
                              risk_level: str = "medium") -> FinancialDecision:
        """
        Make a financial decision based on the given context.
        
        Args:
            context: The financial context or problem statement
            category: Decision category (budget, investment, cost_reduction, revenue, risk_management)
            options: Optional list of possible financial solutions
            financial_impact: Expected financial impact in dollars
            risk_level: Risk level (low, medium, high, critical)
            
        Returns:
            A FinancialDecision object containing the chosen solution
        """
        decision_id = f"fin_dec_{len(self.financial_decisions) + 1}"
        
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
            risk_level=risk_level
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
