"""
Analytics Service

Provides business intelligence and decision analytics
for the AI Executive Suite, including advanced financial modeling,
industry benchmarking, and risk assessment capabilities.
"""

import logging
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy import func, and_, or_
from collections import defaultdict
import statistics

# Import advanced analytics modules
from .financial_modeling import FinancialModelingEngine, CashFlow
from .industry_benchmarking import IndustryBenchmarkingService, IndustryType, CompanySize, CompanyProfile
from .risk_assessment import RiskAssessmentEngine, RiskType

logger = logging.getLogger(__name__)


@dataclass
class DateRange:
    """Date range for analytics queries"""
    start_date: datetime
    end_date: datetime


@dataclass
class AnalyticsFilters:
    """Filters for analytics queries"""
    executive_types: Optional[List[str]] = None
    categories: Optional[List[str]] = None
    priorities: Optional[List[str]] = None
    status: Optional[List[str]] = None


@dataclass
class TimeSeriesPoint:
    """Single point in time series data"""
    timestamp: datetime
    value: float
    metadata: Dict[str, Any] = None


@dataclass
class TrendData:
    """Trend analysis data"""
    direction: str  # 'increasing', 'decreasing', 'stable'
    rate: float
    confidence: float


@dataclass
class BenchmarkData:
    """Industry benchmark comparison data"""
    metric_name: str
    company_value: float
    industry_average: float
    percentile: float


@dataclass
class DecisionAnalytics:
    """Comprehensive decision analytics"""
    total_decisions: int
    decisions_by_executive: Dict[str, int]
    decisions_by_category: Dict[str, int]
    decisions_by_priority: Dict[str, int]
    average_confidence_score: float
    implementation_rate: float
    effectiveness_scores: Dict[str, float]
    decisions_over_time: List[TimeSeriesPoint]
    trends: Dict[str, TrendData]
    total_financial_impact: Decimal
    roi_by_category: Dict[str, Decimal]
    cost_savings: Decimal


@dataclass
class FinancialMetrics:
    """Financial performance metrics"""
    revenue_metrics: Dict[str, Decimal]
    cost_metrics: Dict[str, Decimal]
    profitability_metrics: Dict[str, Decimal]
    efficiency_ratios: Dict[str, float]
    growth_rates: Dict[str, float]
    benchmark_comparisons: Dict[str, BenchmarkData]


@dataclass
class EffectivenessMetrics:
    """Decision effectiveness tracking metrics"""
    decision_id: int
    effectiveness_score: float
    outcome_rating: Optional[int]
    success_probability: float
    implementation_timeliness: float
    financial_impact_accuracy: float
    confidence_alignment: float
    overall_grade: str  # A, B, C, D, F
    improvement_areas: List[str]
    tracking_timestamp: datetime


@dataclass
class SuccessRateReport:
    """Success rate analysis report"""
    total_decisions: int
    overall_success_rate: float
    success_rates_by_executive: Dict[str, float]
    success_rates_by_category: Dict[str, float]
    success_rates_by_priority: Dict[str, float]
    trend_analysis: Dict[str, TrendData]
    recommendations: List[str]
    time_range: DateRange


@dataclass
class DashboardData:
    """Dashboard data for user interface"""
    key_metrics: Dict[str, Any]
    charts: List[Dict[str, Any]]
    alerts: List[Dict[str, Any]]
    recommendations: List[str]


class AnalyticsService:
    """Service for business intelligence and analytics"""
    
    def __init__(self, config: Dict[str, Any], db_session=None):
        self.config = config
        self.db = db_session
        self.logger = logging.getLogger(__name__)
        
        # Initialize advanced analytics engines
        self.financial_modeling = FinancialModelingEngine(config.get('financial_modeling', {}))
        self.industry_benchmarking = IndustryBenchmarkingService(config.get('industry_benchmarking', {}))
        self.risk_assessment = RiskAssessmentEngine(config.get('risk_assessment', {}))
        
    def _get_decisions_query(self, time_range: DateRange, filters: AnalyticsFilters = None):
        """Build base query for decisions with time range and filters"""
        from models import Decision, DecisionStatus, DecisionPriority, ExecutiveType
        
        query = self.db.query(Decision).filter(
            Decision.created_at >= time_range.start_date,
            Decision.created_at <= time_range.end_date
        )
        
        if filters:
            if filters.executive_types:
                exec_types = [ExecutiveType(et) for et in filters.executive_types]
                query = query.filter(Decision.executive_type.in_(exec_types))
            
            if filters.categories:
                query = query.filter(Decision.category.in_(filters.categories))
            
            if filters.priorities:
                priorities = [DecisionPriority(p) for p in filters.priorities]
                query = query.filter(Decision.priority.in_(priorities))
            
            if filters.status:
                statuses = [DecisionStatus(s) for s in filters.status]
                query = query.filter(Decision.status.in_(statuses))
        
        return query
    
    def _calculate_trend_data(self, time_series: List[TimeSeriesPoint]) -> TrendData:
        """Calculate trend direction and rate from time series data"""
        if len(time_series) < 2:
            return TrendData(direction='stable', rate=0.0, confidence=0.0)
        
        values = [point.value for point in time_series]
        
        # Simple linear trend calculation
        n = len(values)
        x_values = list(range(n))
        
        # Calculate slope using least squares
        x_mean = sum(x_values) / n
        y_mean = sum(values) / n
        
        numerator = sum((x_values[i] - x_mean) * (values[i] - y_mean) for i in range(n))
        denominator = sum((x_values[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            slope = 0
        else:
            slope = numerator / denominator
        
        # Determine direction and confidence
        if abs(slope) < 0.01:
            direction = 'stable'
        elif slope > 0:
            direction = 'increasing'
        else:
            direction = 'decreasing'
        
        # Calculate R-squared for confidence
        y_pred = [y_mean + slope * (x - x_mean) for x in x_values]
        ss_res = sum((values[i] - y_pred[i]) ** 2 for i in range(n))
        ss_tot = sum((values[i] - y_mean) ** 2 for i in range(n))
        
        confidence = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
        confidence = max(0.0, min(1.0, confidence))
        
        return TrendData(direction=direction, rate=abs(slope), confidence=confidence)
    
    def _generate_time_series(self, decisions, time_range: DateRange, interval_days: int = 7) -> List[TimeSeriesPoint]:
        """Generate time series data from decisions"""
        time_series = []
        current_date = time_range.start_date
        
        while current_date <= time_range.end_date:
            next_date = current_date + timedelta(days=interval_days)
            
            # Count decisions in this interval
            count = sum(1 for d in decisions 
                       if current_date <= d.created_at < next_date)
            
            time_series.append(TimeSeriesPoint(
                timestamp=current_date,
                value=float(count),
                metadata={'interval_days': interval_days}
            ))
            
            current_date = next_date
        
        return time_series
    
    def generate_decision_analytics(
        self, 
        time_range: DateRange,
        filters: AnalyticsFilters = None
    ) -> DecisionAnalytics:
        """
        Generate comprehensive decision analytics
        
        Args:
            time_range: Date range for analysis
            filters: Optional filters to apply
            
        Returns:
            DecisionAnalytics with comprehensive metrics
        """
        self.logger.info(f"Generating decision analytics for {time_range.start_date} to {time_range.end_date}")
        
        if not self.db:
            self.logger.warning("No database session available, returning mock data")
            return self._generate_mock_analytics()
        
        try:
            # Get decisions for the time range
            decisions = self._get_decisions_query(time_range, filters).all()
            
            if not decisions:
                return self._generate_empty_analytics()
            
            # Calculate basic metrics
            total_decisions = len(decisions)
            
            # Group by executive type
            decisions_by_executive = defaultdict(int)
            for decision in decisions:
                exec_type = decision.executive_type.value if decision.executive_type else 'unknown'
                decisions_by_executive[exec_type] += 1
            
            # Group by category
            decisions_by_category = defaultdict(int)
            for decision in decisions:
                category = decision.category or 'uncategorized'
                decisions_by_category[category] += 1
            
            # Group by priority
            decisions_by_priority = defaultdict(int)
            for decision in decisions:
                priority = decision.priority.value if decision.priority else 'unknown'
                decisions_by_priority[priority] += 1
            
            # Calculate confidence scores
            confidence_scores = [d.confidence_score for d in decisions if d.confidence_score is not None]
            average_confidence_score = statistics.mean(confidence_scores) if confidence_scores else 0.0
            
            # Calculate implementation rate
            completed_decisions = [d for d in decisions if d.status and d.status.value == 'completed']
            implementation_rate = len(completed_decisions) / total_decisions if total_decisions > 0 else 0.0
            
            # Calculate effectiveness scores by executive
            effectiveness_scores = {}
            for exec_type in ['ceo', 'cto', 'cfo']:
                exec_decisions = [d for d in decisions if d.executive_type and d.executive_type.value == exec_type]
                exec_effectiveness = [d.effectiveness_score for d in exec_decisions if d.effectiveness_score is not None]
                effectiveness_scores[exec_type] = statistics.mean(exec_effectiveness) if exec_effectiveness else 0.0
            
            # Generate time series data
            decisions_over_time = self._generate_time_series(decisions, time_range)
            
            # Calculate trends
            trends = {
                'decisions_trend': self._calculate_trend_data(decisions_over_time)
            }
            
            # Calculate financial impact
            financial_impacts = [d.financial_impact for d in decisions if d.financial_impact is not None]
            total_financial_impact = sum(financial_impacts) if financial_impacts else Decimal('0')
            
            # ROI by category (simplified calculation)
            roi_by_category = {}
            for category in decisions_by_category.keys():
                category_decisions = [d for d in decisions if (d.category or 'uncategorized') == category]
                category_impacts = [d.financial_impact for d in category_decisions if d.financial_impact is not None]
                if category_impacts:
                    roi_by_category[category] = sum(category_impacts)
            
            # Estimate cost savings (simplified)
            positive_impacts = [impact for impact in financial_impacts if impact > 0]
            cost_savings = sum(positive_impacts) * Decimal('0.3') if positive_impacts else Decimal('0')
            
            return DecisionAnalytics(
                total_decisions=total_decisions,
                decisions_by_executive=dict(decisions_by_executive),
                decisions_by_category=dict(decisions_by_category),
                decisions_by_priority=dict(decisions_by_priority),
                average_confidence_score=average_confidence_score,
                implementation_rate=implementation_rate,
                effectiveness_scores=effectiveness_scores,
                decisions_over_time=decisions_over_time,
                trends=trends,
                total_financial_impact=total_financial_impact,
                roi_by_category=roi_by_category,
                cost_savings=cost_savings
            )
            
        except Exception as e:
            self.logger.error(f"Error generating decision analytics: {str(e)}")
            return self._generate_mock_analytics()
    
    def _generate_mock_analytics(self) -> DecisionAnalytics:
        """Generate mock analytics data for testing"""
        return DecisionAnalytics(
            total_decisions=100,
            decisions_by_executive={"ceo": 40, "cto": 35, "cfo": 25},
            decisions_by_category={"strategic": 30, "technical": 35, "financial": 35},
            decisions_by_priority={"high": 25, "medium": 50, "low": 25},
            average_confidence_score=0.82,
            implementation_rate=0.75,
            effectiveness_scores={"ceo": 0.85, "cto": 0.80, "cfo": 0.88},
            decisions_over_time=[],
            trends={},
            total_financial_impact=Decimal('1000000'),
            roi_by_category={},
            cost_savings=Decimal('250000')
        )
    
    def _generate_empty_analytics(self) -> DecisionAnalytics:
        """Generate empty analytics data when no decisions found"""
        return DecisionAnalytics(
            total_decisions=0,
            decisions_by_executive={},
            decisions_by_category={},
            decisions_by_priority={},
            average_confidence_score=0.0,
            implementation_rate=0.0,
            effectiveness_scores={"ceo": 0.0, "cto": 0.0, "cfo": 0.0},
            decisions_over_time=[],
            trends={},
            total_financial_impact=Decimal('0'),
            roi_by_category={},
            cost_savings=Decimal('0')
        )
    
    def calculate_decision_effectiveness_metrics(self, decisions: List) -> Dict[str, float]:
        """
        Calculate various effectiveness metrics for decisions
        
        Args:
            decisions: List of Decision objects
            
        Returns:
            Dictionary of effectiveness metrics
        """
        if not decisions:
            return {}
        
        metrics = {}
        
        # Overall effectiveness
        effectiveness_scores = [d.effectiveness_score for d in decisions if d.effectiveness_score is not None]
        if effectiveness_scores:
            metrics['average_effectiveness'] = statistics.mean(effectiveness_scores)
            metrics['median_effectiveness'] = statistics.median(effectiveness_scores)
            metrics['effectiveness_std'] = statistics.stdev(effectiveness_scores) if len(effectiveness_scores) > 1 else 0.0
        
        # Success rate (decisions with outcome rating >= 4)
        rated_decisions = [d for d in decisions if d.outcome_rating is not None]
        if rated_decisions:
            successful_decisions = [d for d in rated_decisions if d.outcome_rating >= 4]
            metrics['success_rate'] = len(successful_decisions) / len(rated_decisions)
        
        # Implementation rate
        total_decisions = len(decisions)
        implemented_decisions = [d for d in decisions if d.implemented_at is not None]
        metrics['implementation_rate'] = len(implemented_decisions) / total_decisions if total_decisions > 0 else 0.0
        
        # Average time to implementation
        implementation_times = []
        for decision in implemented_decisions:
            if decision.created_at and decision.implemented_at:
                time_diff = (decision.implemented_at - decision.created_at).total_seconds() / 86400  # days
                implementation_times.append(time_diff)
        
        if implementation_times:
            metrics['avg_implementation_time_days'] = statistics.mean(implementation_times)
        
        return metrics
    
    def record_decision_outcome(self, decision_id: int, outcome_rating: int, 
                              outcome_notes: str = None, financial_impact: Decimal = None) -> bool:
        """
        Record the outcome of a decision for effectiveness tracking
        
        Args:
            decision_id: ID of the decision
            outcome_rating: Rating from 1-5 (1=poor, 5=excellent)
            outcome_notes: Optional notes about the outcome
            financial_impact: Actual financial impact (if different from estimated)
            
        Returns:
            True if outcome was recorded successfully
        """
        if not self.db:
            self.logger.warning("No database session available for recording outcome")
            return False
        
        try:
            from models import Decision
            
            decision = self.db.query(Decision).filter(Decision.id == decision_id).first()
            if not decision:
                self.logger.error(f"Decision {decision_id} not found")
                return False
            
            # Update outcome information
            decision.outcome_rating = max(1, min(5, outcome_rating))  # Ensure 1-5 range
            
            if outcome_notes:
                if decision.implementation_notes:
                    decision.implementation_notes += f"\n\nOutcome Notes: {outcome_notes}"
                else:
                    decision.implementation_notes = f"Outcome Notes: {outcome_notes}"
            
            if financial_impact is not None:
                decision.financial_impact = financial_impact
            
            # Recalculate effectiveness score
            decision.calculate_effectiveness()
            
            # Update reviewed timestamp
            decision.reviewed_at = datetime.utcnow()
            
            self.db.commit()
            
            self.logger.info(f"Recorded outcome for decision {decision_id}: rating={outcome_rating}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error recording decision outcome: {str(e)}")
            if self.db:
                self.db.rollback()
            return False
    
    def calculate_effectiveness_score(self, decision_data: Dict[str, Any]) -> float:
        """
        Calculate effectiveness score for a decision based on multiple factors
        
        Args:
            decision_data: Dictionary containing decision information
            
        Returns:
            Effectiveness score between 0.0 and 1.0
        """
        score = 0.0
        weight_sum = 0.0
        
        # Outcome rating (40% weight)
        outcome_rating = decision_data.get('outcome_rating')
        if outcome_rating is not None:
            score += (outcome_rating / 5.0) * 0.4
            weight_sum += 0.4
        
        # Confidence score (20% weight)
        confidence_score = decision_data.get('confidence_score')
        if confidence_score is not None:
            score += confidence_score * 0.2
            weight_sum += 0.2
        
        # Implementation timeliness (20% weight)
        created_at = decision_data.get('created_at')
        implemented_at = decision_data.get('implemented_at')
        if created_at and implemented_at:
            time_diff_days = (implemented_at - created_at).total_seconds() / 86400
            # Score decreases as implementation time increases (optimal: 1-7 days)
            if time_diff_days <= 7:
                timeliness_score = 1.0
            elif time_diff_days <= 30:
                timeliness_score = 1.0 - ((time_diff_days - 7) / 23) * 0.5
            else:
                timeliness_score = 0.5
            
            score += timeliness_score * 0.2
            weight_sum += 0.2
        
        # Financial impact achievement (20% weight)
        estimated_impact = decision_data.get('estimated_financial_impact')
        actual_impact = decision_data.get('actual_financial_impact')
        if estimated_impact is not None and actual_impact is not None:
            if estimated_impact == 0:
                impact_score = 1.0 if actual_impact >= 0 else 0.0
            else:
                # Score based on how close actual is to estimated
                ratio = actual_impact / estimated_impact
                if ratio >= 1.0:
                    impact_score = 1.0
                elif ratio >= 0.5:
                    impact_score = ratio
                else:
                    impact_score = 0.5 * ratio
            
            score += impact_score * 0.2
            weight_sum += 0.2
        
        # Normalize score based on available data
        if weight_sum > 0:
            return min(1.0, score / weight_sum)
        else:
            return 0.0
    
    def track_decision_impact(self, decision_id: int, impact_metrics: Dict[str, Any]) -> bool:
        """
        Track the impact of a decision with detailed metrics
        
        Args:
            decision_id: ID of the decision
            impact_metrics: Dictionary containing impact measurements
            
        Returns:
            True if impact was tracked successfully
        """
        if not self.db:
            self.logger.warning("No database session available for tracking impact")
            return False
        
        try:
            from models import Decision
            
            decision = self.db.query(Decision).filter(Decision.id == decision_id).first()
            if not decision:
                self.logger.error(f"Decision {decision_id} not found")
                return False
            
            # Update financial impact if provided
            if 'financial_impact' in impact_metrics:
                decision.financial_impact = Decimal(str(impact_metrics['financial_impact']))
            
            # Update outcome rating if provided
            if 'outcome_rating' in impact_metrics:
                decision.outcome_rating = impact_metrics['outcome_rating']
            
            # Add impact notes
            impact_notes = impact_metrics.get('notes', '')
            if impact_notes:
                timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
                impact_entry = f"\n[{timestamp}] Impact Tracking: {impact_notes}"
                
                if decision.implementation_notes:
                    decision.implementation_notes += impact_entry
                else:
                    decision.implementation_notes = impact_entry.strip()
            
            # Recalculate effectiveness score
            effectiveness_data = {
                'outcome_rating': decision.outcome_rating,
                'confidence_score': decision.confidence_score,
                'created_at': decision.created_at,
                'implemented_at': decision.implemented_at,
                'estimated_financial_impact': decision.financial_impact,
                'actual_financial_impact': impact_metrics.get('financial_impact', decision.financial_impact)
            }
            
            decision.effectiveness_score = self.calculate_effectiveness_score(effectiveness_data)
            
            self.db.commit()
            
            self.logger.info(f"Tracked impact for decision {decision_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error tracking decision impact: {str(e)}")
            if self.db:
                self.db.rollback()
            return False
    
    def generate_success_rate_report(self, time_range: DateRange, 
                                   filters: AnalyticsFilters = None) -> Dict[str, Any]:
        """
        Generate detailed success rate report for decisions
        
        Args:
            time_range: Date range for analysis
            filters: Optional filters to apply
            
        Returns:
            Dictionary containing success rate analysis
        """
        if not self.db:
            return {'error': 'No database session available'}
        
        try:
            decisions = self._get_decisions_query(time_range, filters).all()
            
            if not decisions:
                return {'total_decisions': 0, 'success_rates': {}}
            
            report = {
                'total_decisions': len(decisions),
                'time_range': {
                    'start': time_range.start_date.isoformat(),
                    'end': time_range.end_date.isoformat()
                },
                'success_rates': {},
                'trends': {},
                'recommendations': []
            }
            
            # Overall success rate
            rated_decisions = [d for d in decisions if d.outcome_rating is not None]
            if rated_decisions:
                successful = [d for d in rated_decisions if d.outcome_rating >= 4]
                report['success_rates']['overall'] = {
                    'rate': len(successful) / len(rated_decisions),
                    'total_rated': len(rated_decisions),
                    'successful': len(successful)
                }
            
            # Success rate by executive type
            for exec_type in ['ceo', 'cto', 'cfo']:
                exec_decisions = [d for d in rated_decisions 
                                if d.executive_type and d.executive_type.value == exec_type]
                if exec_decisions:
                    exec_successful = [d for d in exec_decisions if d.outcome_rating >= 4]
                    report['success_rates'][exec_type] = {
                        'rate': len(exec_successful) / len(exec_decisions),
                        'total_rated': len(exec_decisions),
                        'successful': len(exec_successful)
                    }
            
            # Success rate by category
            categories = set(d.category for d in rated_decisions if d.category)
            for category in categories:
                cat_decisions = [d for d in rated_decisions if d.category == category]
                cat_successful = [d for d in cat_decisions if d.outcome_rating >= 4]
                report['success_rates'][f'category_{category}'] = {
                    'rate': len(cat_successful) / len(cat_decisions),
                    'total_rated': len(cat_decisions),
                    'successful': len(cat_successful)
                }
            
            # Generate recommendations
            overall_rate = report['success_rates'].get('overall', {}).get('rate', 0)
            if overall_rate < 0.7:
                report['recommendations'].append(
                    f"Overall success rate ({overall_rate:.1%}) is below target. "
                    "Consider reviewing decision-making processes."
                )
            
            # Compare executive performance
            exec_rates = {k: v['rate'] for k, v in report['success_rates'].items() 
                         if k in ['ceo', 'cto', 'cfo']}
            if exec_rates:
                lowest_exec = min(exec_rates, key=exec_rates.get)
                if exec_rates[lowest_exec] < 0.6:
                    report['recommendations'].append(
                        f"{lowest_exec.upper()} decisions have lower success rate "
                        f"({exec_rates[lowest_exec]:.1%}). Consider additional training or support."
                    )
            
            return report
            
        except Exception as e:
            self.logger.error(f"Error generating success rate report: {str(e)}")
            return {'error': str(e)}
    
    # Advanced Financial Analytics Methods
    
    def calculate_npv_analysis(
        self, 
        cash_flows: List[Dict[str, Any]], 
        discount_rate: float,
        initial_investment: Decimal = None
    ) -> Dict[str, Any]:
        """
        Calculate Net Present Value analysis for investment decisions
        
        Args:
            cash_flows: List of cash flow dictionaries
            discount_rate: Discount rate for NPV calculation
            initial_investment: Initial investment amount
            
        Returns:
            Dictionary with NPV analysis results
        """
        try:
            # Convert cash flow dictionaries to CashFlow objects
            cf_objects = []
            for cf_data in cash_flows:
                cf = CashFlow(
                    period=cf_data['period'],
                    amount=Decimal(str(cf_data['amount'])),
                    description=cf_data.get('description', ''),
                    category=cf_data.get('category', '')
                )
                cf_objects.append(cf)
            
            # Calculate NPV
            npv_result = self.financial_modeling.calculate_npv(
                cf_objects, discount_rate, initial_investment
            )
            
            # Calculate additional metrics
            payback_result = self.financial_modeling.calculate_payback_period(
                cf_objects, initial_investment or Decimal('0')
            )
            
            pi_result = self.financial_modeling.calculate_profitability_index(
                cf_objects, initial_investment or Decimal('0'), discount_rate
            )
            
            return {
                'npv': {
                    'value': float(npv_result.npv),
                    'discount_rate': npv_result.discount_rate,
                    'initial_investment': float(npv_result.initial_investment),
                    'present_values': [float(pv) for pv in npv_result.present_values]
                },
                'payback_period': {
                    'simple': payback_result.get('simple_payback_period'),
                    'discounted': payback_result.get('discounted_payback_period')
                },
                'profitability_index': {
                    'value': float(pi_result['profitability_index']),
                    'interpretation': pi_result['interpretation']
                },
                'calculation_date': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating NPV analysis: {str(e)}")
            return {'error': str(e)}
    
    def calculate_irr_analysis(self, cash_flows: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate Internal Rate of Return analysis
        
        Args:
            cash_flows: List of cash flow dictionaries (must include initial investment)
            
        Returns:
            Dictionary with IRR analysis results
        """
        try:
            # Convert cash flow dictionaries to CashFlow objects
            cf_objects = []
            for cf_data in cash_flows:
                cf = CashFlow(
                    period=cf_data['period'],
                    amount=Decimal(str(cf_data['amount'])),
                    description=cf_data.get('description', ''),
                    category=cf_data.get('category', '')
                )
                cf_objects.append(cf)
            
            # Calculate IRR
            irr_result = self.financial_modeling.calculate_irr(cf_objects)
            
            return {
                'irr': irr_result.irr,
                'irr_percentage': irr_result.irr * 100,
                'npv_at_irr': float(irr_result.npv_at_irr),
                'converged': irr_result.converged,
                'iterations': irr_result.iterations,
                'calculation_date': irr_result.calculation_date.isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating IRR analysis: {str(e)}")
            return {'error': str(e)}
    
    def perform_scenario_analysis(
        self, 
        base_case_params: Dict[str, Any],
        scenario_adjustments: Dict[str, Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        Perform financial scenario analysis
        
        Args:
            base_case_params: Base case parameters
            scenario_adjustments: Scenario adjustment parameters
            
        Returns:
            Dictionary with scenario analysis results
        """
        try:
            scenario_result = self.financial_modeling.perform_scenario_analysis(
                base_case_params, scenario_adjustments
            )
            
            return {
                'base_case': {
                    'npv': float(scenario_result.base_case['npv']),
                    'probability': scenario_result.base_case['probability']
                },
                'optimistic_case': {
                    'npv': float(scenario_result.optimistic_case['npv']),
                    'probability': scenario_result.optimistic_case['probability']
                },
                'pessimistic_case': {
                    'npv': float(scenario_result.pessimistic_case['npv']),
                    'probability': scenario_result.pessimistic_case['probability']
                },
                'expected_value': float(scenario_result.expected_value),
                'risk_metrics': scenario_result.risk_metrics
            }
            
        except Exception as e:
            self.logger.error(f"Error performing scenario analysis: {str(e)}")
            return {'error': str(e)}
    
    def perform_sensitivity_analysis(
        self,
        base_case_params: Dict[str, Any],
        sensitivity_variables: List[str] = None
    ) -> Dict[str, Any]:
        """
        Perform sensitivity analysis on financial parameters
        
        Args:
            base_case_params: Base case parameters
            sensitivity_variables: Variables to analyze
            
        Returns:
            Dictionary with sensitivity analysis results
        """
        try:
            sensitivity_result = self.financial_modeling.perform_sensitivity_analysis(
                base_case_params, sensitivity_variables
            )
            
            return {
                'base_npv': float(sensitivity_result.base_npv),
                'sensitivity_results': {
                    var: {change: float(npv) for change, npv in results.items()}
                    for var, results in sensitivity_result.sensitivity_results.items()
                },
                'most_sensitive_variables': sensitivity_result.most_sensitive_variables,
                'tornado_chart_data': [
                    {
                        'variable': item['variable'],
                        'max_impact': item['max_impact'],
                        'low_npv': float(item['low_npv']),
                        'high_npv': float(item['high_npv'])
                    }
                    for item in sensitivity_result.tornado_chart_data
                ]
            }
            
        except Exception as e:
            self.logger.error(f"Error performing sensitivity analysis: {str(e)}")
            return {'error': str(e)}
    
    def get_industry_benchmarks(
        self, 
        industry: str, 
        company_metrics: Dict[str, float] = None
    ) -> Dict[str, Any]:
        """
        Get industry benchmarks and compare company performance
        
        Args:
            industry: Industry type
            company_metrics: Company metrics to compare
            
        Returns:
            Dictionary with industry benchmark data and comparisons
        """
        try:
            industry_type = IndustryType(industry.lower())
            
            # Get industry benchmarks
            benchmarks = self.industry_benchmarking.get_industry_benchmarks(industry_type)
            
            result = {
                'industry': industry,
                'benchmarks': {}
            }
            
            # Convert benchmarks to dictionary format
            for metric_name, benchmark in benchmarks.items():
                result['benchmarks'][metric_name] = {
                    'industry_average': float(benchmark.value),
                    'percentile_25': float(benchmark.percentile_25),
                    'percentile_50': float(benchmark.percentile_50),
                    'percentile_75': float(benchmark.percentile_75),
                    'unit': benchmark.unit,
                    'sample_size': benchmark.sample_size,
                    'data_source': benchmark.data_source
                }
            
            # Perform comparison if company metrics provided
            if company_metrics:
                company_metrics_decimal = {
                    k: Decimal(str(v)) for k, v in company_metrics.items()
                }
                
                comparisons = self.industry_benchmarking.compare_to_industry(
                    company_metrics_decimal, industry_type
                )
                
                result['comparisons'] = {}
                for metric_name, comparison in comparisons.items():
                    result['comparisons'][metric_name] = {
                        'company_value': float(comparison.company_value),
                        'industry_median': float(comparison.industry_median),
                        'industry_average': float(comparison.industry_average),
                        'percentile_rank': comparison.percentile_rank,
                        'performance_rating': comparison.performance_rating,
                        'improvement_potential': float(comparison.improvement_potential),
                        'peer_companies': comparison.peer_companies
                    }
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error getting industry benchmarks: {str(e)}")
            return {'error': str(e)}
    
    def perform_competitive_analysis(
        self, 
        company_profile: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Perform competitive analysis for a company
        
        Args:
            company_profile: Company profile information
            
        Returns:
            Dictionary with competitive analysis results
        """
        try:
            # Create CompanyProfile object
            profile = CompanyProfile(
                company_id=company_profile.get('company_id', 'unknown'),
                name=company_profile.get('name', 'Unknown Company'),
                industry=IndustryType(company_profile.get('industry', 'technology')),
                size=CompanySize(company_profile.get('size', 'medium')),
                revenue=Decimal(str(company_profile.get('revenue', 0))) if company_profile.get('revenue') else None,
                employees=company_profile.get('employees'),
                founded_year=company_profile.get('founded_year'),
                location=company_profile.get('location'),
                public_company=company_profile.get('public_company', False)
            )
            
            # Perform competitive analysis
            analysis = self.industry_benchmarking.perform_competitive_analysis(profile)
            
            return {
                'company_profile': {
                    'name': analysis.company_profile.name,
                    'industry': analysis.company_profile.industry.value,
                    'size': analysis.company_profile.size.value,
                    'revenue': float(analysis.company_profile.revenue) if analysis.company_profile.revenue else None
                },
                'market_position': analysis.market_position,
                'competitive_advantages': analysis.competitive_advantages,
                'competitive_disadvantages': analysis.competitive_disadvantages,
                'market_share_estimate': analysis.market_share_estimate,
                'growth_comparison': analysis.growth_comparison,
                'direct_competitors': [
                    {
                        'name': comp.name,
                        'revenue': float(comp.revenue) if comp.revenue else None,
                        'employees': comp.employees
                    }
                    for comp in analysis.direct_competitors
                ]
            }
            
        except Exception as e:
            self.logger.error(f"Error performing competitive analysis: {str(e)}")
            return {'error': str(e)}
    
    def assess_financial_risk(
        self, 
        company_profile: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Assess financial and operational risks
        
        Args:
            company_profile: Company profile for risk assessment
            
        Returns:
            Dictionary with risk assessment results
        """
        try:
            # Calculate overall risk score
            risk_score = self.risk_assessment.calculate_risk_score()
            
            # Generate comprehensive risk report if company profile provided
            if company_profile:
                company_id = company_profile.get('company_id', 'unknown')
                risk_report = self.risk_assessment.generate_comprehensive_risk_report(
                    company_id, company_profile
                )
                
                return {
                    'overall_risk_score': risk_score.overall_score,
                    'risk_level': risk_score.risk_level.value,
                    'confidence_interval': risk_score.confidence_interval,
                    'recommendations': risk_score.recommendations,
                    'risk_by_category': {
                        category: {
                            'score': cat_score.overall_score,
                            'level': cat_score.risk_level.value
                        }
                        for category, cat_score in risk_report.risk_by_category.items()
                    },
                    'monte_carlo_analysis': {
                        'mean_outcome': float(risk_report.monte_carlo_analysis.mean_outcome),
                        'var_95': float(risk_report.monte_carlo_analysis.var_95),
                        'probability_of_loss': risk_report.monte_carlo_analysis.probability_of_loss
                    },
                    'compliance_risks': [
                        {
                            'regulation': risk.regulation_name,
                            'compliance_level': risk.compliance_level,
                            'risk_score': risk.risk_score,
                            'priority': risk.priority
                        }
                        for risk in risk_report.compliance_risks
                    ],
                    'key_recommendations': risk_report.key_recommendations
                }
            else:
                return {
                    'overall_risk_score': risk_score.overall_score,
                    'risk_level': risk_score.risk_level.value,
                    'confidence_interval': risk_score.confidence_interval,
                    'recommendations': risk_score.recommendations,
                    'score_breakdown': risk_score.score_breakdown
                }
            
        except Exception as e:
            self.logger.error(f"Error assessing financial risk: {str(e)}")
            return {'error': str(e)}
    
    def run_monte_carlo_risk_simulation(
        self,
        base_scenario: Dict[str, Any],
        risk_parameters: Dict[str, Dict[str, float]],
        num_simulations: int = 10000
    ) -> Dict[str, Any]:
        """
        Run Monte Carlo simulation for risk analysis
        
        Args:
            base_scenario: Base scenario parameters
            risk_parameters: Risk parameter distributions
            num_simulations: Number of simulation runs
            
        Returns:
            Dictionary with Monte Carlo simulation results
        """
        try:
            simulation_result = self.risk_assessment.run_monte_carlo_simulation(
                base_scenario, risk_parameters, num_simulations
            )
            
            return {
                'simulation_runs': simulation_result.simulation_runs,
                'mean_outcome': float(simulation_result.mean_outcome),
                'median_outcome': float(simulation_result.median_outcome),
                'std_deviation': float(simulation_result.std_deviation),
                'percentile_5': float(simulation_result.percentile_5),
                'percentile_95': float(simulation_result.percentile_95),
                'var_95': float(simulation_result.var_95),
                'cvar_95': float(simulation_result.cvar_95),
                'probability_of_loss': simulation_result.probability_of_loss,
                'worst_case_scenario': float(simulation_result.worst_case_scenario),
                'best_case_scenario': float(simulation_result.best_case_scenario)
            }
            
        except Exception as e:
            self.logger.error(f"Error running Monte Carlo simulation: {str(e)}")
            return {'error': str(e)}
    
    def generate_effectiveness_report(self, decision_id: int) -> EffectivenessMetrics:
        """
        Generate detailed effectiveness report for a specific decision
        
        Args:
            decision_id: ID of the decision to analyze
            
        Returns:
            EffectivenessMetrics with detailed analysis
        """
        if not self.db:
            self.logger.warning("No database session available")
            return self._generate_mock_effectiveness_metrics(decision_id)
        
        try:
            from models import Decision
            
            decision = self.db.query(Decision).filter(Decision.id == decision_id).first()
            if not decision:
                self.logger.error(f"Decision {decision_id} not found")
                return self._generate_mock_effectiveness_metrics(decision_id)
            
            # Calculate individual components
            outcome_score = (decision.outcome_rating / 5.0) if decision.outcome_rating else 0.0
            confidence_score = decision.confidence_score or 0.0
            
            # Calculate implementation timeliness
            timeliness_score = 0.0
            if decision.created_at and decision.implemented_at:
                time_diff_days = (decision.implemented_at - decision.created_at).total_seconds() / 86400
                if time_diff_days <= 7:
                    timeliness_score = 1.0
                elif time_diff_days <= 30:
                    timeliness_score = 1.0 - ((time_diff_days - 7) / 23) * 0.5
                else:
                    timeliness_score = 0.5
            
            # Calculate financial impact accuracy (simplified)
            impact_accuracy = 0.8  # Default assumption
            
            # Calculate overall effectiveness score
            effectiveness_data = {
                'outcome_rating': decision.outcome_rating,
                'confidence_score': decision.confidence_score,
                'created_at': decision.created_at,
                'implemented_at': decision.implemented_at,
                'estimated_financial_impact': decision.financial_impact,
                'actual_financial_impact': decision.financial_impact
            }
            
            effectiveness_score = self.calculate_effectiveness_score(effectiveness_data)
            
            # Determine grade
            if effectiveness_score >= 0.9:
                grade = 'A'
            elif effectiveness_score >= 0.8:
                grade = 'B'
            elif effectiveness_score >= 0.7:
                grade = 'C'
            elif effectiveness_score >= 0.6:
                grade = 'D'
            else:
                grade = 'F'
            
            # Identify improvement areas
            improvement_areas = []
            if outcome_score < 0.7:
                improvement_areas.append("Outcome quality - consider better planning and execution")
            if confidence_score < 0.7:
                improvement_areas.append("Decision confidence - gather more information before deciding")
            if timeliness_score < 0.7:
                improvement_areas.append("Implementation speed - reduce time from decision to action")
            if not decision.outcome_rating:
                improvement_areas.append("Outcome tracking - record results to improve future decisions")
            
            return EffectivenessMetrics(
                decision_id=decision_id,
                effectiveness_score=effectiveness_score,
                outcome_rating=decision.outcome_rating,
                success_probability=effectiveness_score,  # Simplified
                implementation_timeliness=timeliness_score,
                financial_impact_accuracy=impact_accuracy,
                confidence_alignment=confidence_score,
                overall_grade=grade,
                improvement_areas=improvement_areas,
                tracking_timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            self.logger.error(f"Error generating effectiveness report: {str(e)}")
            return self._generate_mock_effectiveness_metrics(decision_id)
    
    def _generate_mock_effectiveness_metrics(self, decision_id: int) -> EffectivenessMetrics:
        """Generate mock effectiveness metrics for testing"""
        return EffectivenessMetrics(
            decision_id=decision_id,
            effectiveness_score=0.75,
            outcome_rating=4,
            success_probability=0.75,
            implementation_timeliness=0.8,
            financial_impact_accuracy=0.7,
            confidence_alignment=0.8,
            overall_grade='B',
            improvement_areas=["Consider gathering more market data"],
            tracking_timestamp=datetime.utcnow()
        )
    
    def bulk_update_effectiveness_scores(self, time_range: DateRange = None) -> Dict[str, int]:
        """
        Bulk update effectiveness scores for decisions in a time range
        
        Args:
            time_range: Optional date range to limit updates
            
        Returns:
            Dictionary with update statistics
        """
        if not self.db:
            self.logger.warning("No database session available")
            return {'error': 'No database session'}
        
        try:
            from models import Decision
            
            query = self.db.query(Decision)
            
            if time_range:
                query = query.filter(
                    Decision.created_at >= time_range.start_date,
                    Decision.created_at <= time_range.end_date
                )
            
            # Only update decisions that have outcome ratings but no effectiveness score
            decisions = query.filter(
                Decision.outcome_rating.isnot(None),
                or_(Decision.effectiveness_score.is_(None), Decision.effectiveness_score == 0)
            ).all()
            
            updated_count = 0
            error_count = 0
            
            for decision in decisions:
                try:
                    effectiveness_data = {
                        'outcome_rating': decision.outcome_rating,
                        'confidence_score': decision.confidence_score,
                        'created_at': decision.created_at,
                        'implemented_at': decision.implemented_at,
                        'estimated_financial_impact': decision.financial_impact,
                        'actual_financial_impact': decision.financial_impact
                    }
                    
                    decision.effectiveness_score = self.calculate_effectiveness_score(effectiveness_data)
                    updated_count += 1
                    
                except Exception as e:
                    self.logger.error(f"Error updating effectiveness for decision {decision.id}: {str(e)}")
                    error_count += 1
            
            self.db.commit()
            
            self.logger.info(f"Bulk updated effectiveness scores: {updated_count} updated, {error_count} errors")
            
            return {
                'updated': updated_count,
                'errors': error_count,
                'total_processed': len(decisions)
            }
            
        except Exception as e:
            self.logger.error(f"Error in bulk effectiveness update: {str(e)}")
            if self.db:
                self.db.rollback()
            return {'error': str(e)}
    
    def get_decision_impact_timeline(self, decision_id: int) -> List[Dict[str, Any]]:
        """
        Get timeline of impact tracking for a decision
        
        Args:
            decision_id: ID of the decision
            
        Returns:
            List of timeline events
        """
        if not self.db:
            return []
        
        try:
            from models import Decision
            
            decision = self.db.query(Decision).filter(Decision.id == decision_id).first()
            if not decision:
                return []
            
            timeline = []
            
            # Decision created
            timeline.append({
                'timestamp': decision.created_at,
                'event': 'Decision Created',
                'description': f'Decision "{decision.title}" was created',
                'confidence_score': decision.confidence_score,
                'estimated_impact': float(decision.financial_impact) if decision.financial_impact else None
            })
            
            # Decision implemented
            if decision.implemented_at:
                timeline.append({
                    'timestamp': decision.implemented_at,
                    'event': 'Decision Implemented',
                    'description': 'Decision was put into action',
                    'implementation_notes': decision.implementation_notes
                })
            
            # Decision reviewed
            if decision.reviewed_at:
                timeline.append({
                    'timestamp': decision.reviewed_at,
                    'event': 'Outcome Reviewed',
                    'description': f'Decision outcome rated: {decision.outcome_rating}/5',
                    'outcome_rating': decision.outcome_rating,
                    'effectiveness_score': decision.effectiveness_score
                })
            
            # Sort by timestamp
            timeline.sort(key=lambda x: x['timestamp'])
            
            return timeline
            
        except Exception as e:
            self.logger.error(f"Error getting decision timeline: {str(e)}")
            return []
    
    def calculate_financial_metrics(
        self, 
        financial_data: Dict[str, Any]
    ) -> FinancialMetrics:
        """
        Calculate comprehensive financial metrics
        
        Args:
            financial_data: Raw financial data
            
        Returns:
            FinancialMetrics with calculated ratios and comparisons
        """
        self.logger.info("Calculating financial metrics")
        
        try:
            # Extract basic financial data
            revenue = financial_data.get('revenue', {})
            costs = financial_data.get('costs', {})
            assets = financial_data.get('assets', {})
            
            # Calculate revenue metrics
            revenue_metrics = {}
            if 'total_revenue' in revenue:
                revenue_metrics['total_revenue'] = Decimal(str(revenue['total_revenue']))
            if 'recurring_revenue' in revenue:
                revenue_metrics['recurring_revenue'] = Decimal(str(revenue['recurring_revenue']))
            
            # Calculate cost metrics
            cost_metrics = {}
            if 'total_costs' in costs:
                cost_metrics['total_costs'] = Decimal(str(costs['total_costs']))
            if 'operating_costs' in costs:
                cost_metrics['operating_costs'] = Decimal(str(costs['operating_costs']))
            
            # Calculate profitability metrics
            profitability_metrics = {}
            if revenue_metrics.get('total_revenue') and cost_metrics.get('total_costs'):
                gross_profit = revenue_metrics['total_revenue'] - cost_metrics['total_costs']
                profitability_metrics['gross_profit'] = gross_profit
                profitability_metrics['gross_margin'] = gross_profit / revenue_metrics['total_revenue']
            
            # Calculate efficiency ratios
            efficiency_ratios = {}
            if revenue_metrics.get('total_revenue') and assets.get('total_assets'):
                efficiency_ratios['asset_turnover'] = float(revenue_metrics['total_revenue'] / Decimal(str(assets['total_assets'])))
            
            # Calculate growth rates (requires historical data)
            growth_rates = {}
            if 'previous_revenue' in financial_data:
                current_revenue = revenue_metrics.get('total_revenue', Decimal('0'))
                previous_revenue = Decimal(str(financial_data['previous_revenue']))
                if previous_revenue > 0:
                    growth_rates['revenue_growth'] = float((current_revenue - previous_revenue) / previous_revenue)
            
            # Benchmark comparisons (placeholder - would integrate with external data)
            benchmark_comparisons = {}
            
            return FinancialMetrics(
                revenue_metrics=revenue_metrics,
                cost_metrics=cost_metrics,
                profitability_metrics=profitability_metrics,
                efficiency_ratios=efficiency_ratios,
                growth_rates=growth_rates,
                benchmark_comparisons=benchmark_comparisons
            )
            
        except Exception as e:
            self.logger.error(f"Error calculating financial metrics: {str(e)}")
            # Return default metrics
            return FinancialMetrics(
                revenue_metrics={"total_revenue": Decimal('0')},
                cost_metrics={"total_costs": Decimal('0')},
                profitability_metrics={"gross_profit": Decimal('0')},
                efficiency_ratios={},
                growth_rates={},
                benchmark_comparisons={}
            )
    
    def get_performance_dashboard(
        self, 
        user_id: str
    ) -> DashboardData:
        """
        Generate performance dashboard data for a user
        
        Args:
            user_id: ID of the user requesting dashboard
            
        Returns:
            DashboardData with personalized metrics and charts
        """
        self.logger.info(f"Generating dashboard for user {user_id}")
        
        if not self.db:
            return self._generate_mock_dashboard()
        
        try:
            from models import Decision, User
            
            # Get user's decisions from last 30 days
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            user_decisions = self.db.query(Decision).filter(
                Decision.user_id == user_id,
                Decision.created_at >= thirty_days_ago
            ).all()
            
            # Calculate key metrics
            total_decisions = len(user_decisions)
            
            # Success rate based on outcome ratings
            rated_decisions = [d for d in user_decisions if d.outcome_rating is not None]
            successful_decisions = [d for d in rated_decisions if d.outcome_rating >= 4]
            success_rate = len(successful_decisions) / len(rated_decisions) if rated_decisions else 0.0
            
            # Average confidence score
            confidence_scores = [d.confidence_score for d in user_decisions if d.confidence_score is not None]
            avg_confidence = statistics.mean(confidence_scores) if confidence_scores else 0.0
            
            # Generate charts data
            charts = []
            
            # Decisions over time chart
            decisions_time_series = self._generate_time_series(
                user_decisions, 
                DateRange(thirty_days_ago, datetime.utcnow()),
                interval_days=7
            )
            
            charts.append({
                "type": "line",
                "title": "Decisions Over Time (Last 30 Days)",
                "data": [
                    {
                        "x": point.timestamp.isoformat(),
                        "y": point.value
                    } for point in decisions_time_series
                ]
            })
            
            # Decisions by executive type
            exec_counts = defaultdict(int)
            for decision in user_decisions:
                exec_type = decision.executive_type.value if decision.executive_type else 'unknown'
                exec_counts[exec_type] += 1
            
            charts.append({
                "type": "pie",
                "title": "Decisions by Executive Type",
                "data": [
                    {"label": exec_type, "value": count}
                    for exec_type, count in exec_counts.items()
                ]
            })
            
            # Generate alerts
            alerts = []
            if success_rate < 0.7:
                alerts.append({
                    "type": "warning",
                    "message": f"Decision success rate ({success_rate:.1%}) is below target (70%)"
                })
            
            if avg_confidence < 0.6:
                alerts.append({
                    "type": "info",
                    "message": f"Average confidence score ({avg_confidence:.2f}) could be improved"
                })
            
            # Generate recommendations
            recommendations = []
            if total_decisions < 5:
                recommendations.append("Consider making more decisions to improve analytics accuracy")
            
            if len([d for d in user_decisions if d.outcome_rating is None]) > total_decisions * 0.5:
                recommendations.append("Rate more of your implemented decisions to track effectiveness")
            
            low_confidence_decisions = [d for d in user_decisions if d.confidence_score and d.confidence_score < 0.5]
            if low_confidence_decisions:
                recommendations.append(f"Review {len(low_confidence_decisions)} low-confidence decisions for improvement opportunities")
            
            return DashboardData(
                key_metrics={
                    "total_decisions": total_decisions,
                    "success_rate": success_rate,
                    "avg_confidence": avg_confidence,
                    "implementation_rate": len([d for d in user_decisions if d.implemented_at]) / total_decisions if total_decisions > 0 else 0.0
                },
                charts=charts,
                alerts=alerts,
                recommendations=recommendations
            )
            
        except Exception as e:
            self.logger.error(f"Error generating dashboard for user {user_id}: {str(e)}")
            return self._generate_mock_dashboard()
    
    def _generate_mock_dashboard(self) -> DashboardData:
        """Generate mock dashboard data"""
        return DashboardData(
            key_metrics={
                "total_decisions": 15,
                "success_rate": 0.85,
                "avg_confidence": 0.78
            },
            charts=[
                {
                    "type": "line",
                    "title": "Decisions Over Time",
                    "data": []
                }
            ],
            alerts=[
                {
                    "type": "info",
                    "message": "All systems operating normally"
                }
            ],
            recommendations=[
                "Continue current decision-making patterns",
                "Consider documenting decision outcomes for better tracking"
            ]
        )   
 
    def get_effectiveness_trends(self, time_range: DateRange, 
                               filters: AnalyticsFilters = None) -> Dict[str, TrendData]:
        """
        Analyze effectiveness trends over time
        
        Args:
            time_range: Date range for analysis
            filters: Optional filters to apply
            
        Returns:
            Dictionary of trend data for different metrics
        """
        if not self.db:
            return {}
        
        try:
            decisions = self._get_decisions_query(time_range, filters).all()
            
            if not decisions:
                return {}
            
            # Group decisions by week
            weekly_data = defaultdict(list)
            for decision in decisions:
                if decision.effectiveness_score is not None:
                    week_start = decision.created_at - timedelta(days=decision.created_at.weekday())
                    week_key = week_start.strftime('%Y-%W')
                    weekly_data[week_key].append(decision.effectiveness_score)
            
            # Calculate weekly averages
            weekly_averages = []
            for week_key in sorted(weekly_data.keys()):
                avg_effectiveness = statistics.mean(weekly_data[week_key])
                week_date = datetime.strptime(week_key + '-1', '%Y-%W-%w')
                weekly_averages.append(TimeSeriesPoint(week_date, avg_effectiveness))
            
            trends = {}
            if len(weekly_averages) >= 2:
                trends['effectiveness'] = self._calculate_trend_data(weekly_averages)
            
            # Calculate success rate trend
            weekly_success = []
            for week_key in sorted(weekly_data.keys()):
                week_decisions = [d for d in decisions 
                                if (d.created_at - timedelta(days=d.created_at.weekday())).strftime('%Y-%W') == week_key
                                and d.outcome_rating is not None]
                if week_decisions:
                    successful = [d for d in week_decisions if d.outcome_rating >= 4]
                    success_rate = len(successful) / len(week_decisions)
                    week_date = datetime.strptime(week_key + '-1', '%Y-%W-%w')
                    weekly_success.append(TimeSeriesPoint(week_date, success_rate))
            
            if len(weekly_success) >= 2:
                trends['success_rate'] = self._calculate_trend_data(weekly_success)
            
            return trends
            
        except Exception as e:
            self.logger.error(f"Error calculating effectiveness trends: {str(e)}")
            return {}
    
    def get_top_performing_decisions(self, time_range: DateRange, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get top performing decisions based on effectiveness scores
        
        Args:
            time_range: Date range for analysis
            limit: Maximum number of decisions to return
            
        Returns:
            List of top performing decisions with metrics
        """
        if not self.db:
            return []
        
        try:
            from models import Decision
            
            decisions = self.db.query(Decision).filter(
                Decision.created_at >= time_range.start_date,
                Decision.created_at <= time_range.end_date,
                Decision.effectiveness_score.isnot(None)
            ).order_by(Decision.effectiveness_score.desc()).limit(limit).all()
            
            top_decisions = []
            for decision in decisions:
                decision_data = {
                    'id': decision.id,
                    'title': decision.title,
                    'executive_type': decision.executive_type.value if decision.executive_type else None,
                    'effectiveness_score': decision.effectiveness_score,
                    'outcome_rating': decision.outcome_rating,
                    'confidence_score': decision.confidence_score,
                    'financial_impact': float(decision.financial_impact) if decision.financial_impact else None,
                    'created_at': decision.created_at.isoformat(),
                    'implemented_at': decision.implemented_at.isoformat() if decision.implemented_at else None,
                    'category': decision.category,
                    'priority': decision.priority.value if decision.priority else None
                }
                top_decisions.append(decision_data)
            
            return top_decisions
            
        except Exception as e:
            self.logger.error(f"Error getting top performing decisions: {str(e)}")
            return []
    
    def get_improvement_opportunities(self, time_range: DateRange, 
                                   filters: AnalyticsFilters = None) -> List[Dict[str, Any]]:
        """
        Identify decisions and patterns that need improvement
        
        Args:
            time_range: Date range for analysis
            filters: Optional filters to apply
            
        Returns:
            List of improvement opportunities
        """
        if not self.db:
            return []
        
        try:
            decisions = self._get_decisions_query(time_range, filters).all()
            
            if not decisions:
                return []
            
            opportunities = []
            
            # Find low-performing decisions
            low_effectiveness = [d for d in decisions 
                               if d.effectiveness_score is not None and d.effectiveness_score < 0.6]
            
            if low_effectiveness:
                opportunities.append({
                    'type': 'low_effectiveness',
                    'title': 'Low Effectiveness Decisions',
                    'description': f'{len(low_effectiveness)} decisions have effectiveness scores below 60%',
                    'count': len(low_effectiveness),
                    'priority': 'high',
                    'recommendations': [
                        'Review decision-making process for these cases',
                        'Analyze common factors in low-performing decisions',
                        'Provide additional training or resources'
                    ]
                })
            
            # Find decisions with poor outcomes
            poor_outcomes = [d for d in decisions 
                           if d.outcome_rating is not None and d.outcome_rating <= 2]
            
            if poor_outcomes:
                opportunities.append({
                    'type': 'poor_outcomes',
                    'title': 'Poor Outcome Decisions',
                    'description': f'{len(poor_outcomes)} decisions had poor outcomes (rating ≤ 2)',
                    'count': len(poor_outcomes),
                    'priority': 'high',
                    'recommendations': [
                        'Conduct post-mortem analysis on failed decisions',
                        'Identify root causes of poor outcomes',
                        'Implement preventive measures'
                    ]
                })
            
            # Find untracked decisions
            untracked = [d for d in decisions if d.outcome_rating is None and d.implemented_at is not None]
            
            if untracked:
                opportunities.append({
                    'type': 'untracked_outcomes',
                    'title': 'Untracked Decision Outcomes',
                    'description': f'{len(untracked)} implemented decisions lack outcome ratings',
                    'count': len(untracked),
                    'priority': 'medium',
                    'recommendations': [
                        'Follow up on implemented decisions to track outcomes',
                        'Establish regular review cycles',
                        'Create outcome tracking reminders'
                    ]
                })
            
            # Find slow implementation
            slow_implementation = []
            for decision in decisions:
                if decision.created_at and decision.implemented_at:
                    days_to_implement = (decision.implemented_at - decision.created_at).days
                    if days_to_implement > 30:
                        slow_implementation.append(decision)
            
            if slow_implementation:
                opportunities.append({
                    'type': 'slow_implementation',
                    'title': 'Slow Decision Implementation',
                    'description': f'{len(slow_implementation)} decisions took over 30 days to implement',
                    'count': len(slow_implementation),
                    'priority': 'medium',
                    'recommendations': [
                        'Streamline decision implementation process',
                        'Identify and remove implementation bottlenecks',
                        'Set implementation deadlines and track progress'
                    ]
                })
            
            return opportunities
            
        except Exception as e:
            self.logger.error(f"Error identifying improvement opportunities: {str(e)}")
            return []