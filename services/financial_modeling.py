"""
Financial Modeling Service

Provides advanced financial modeling capabilities including NPV, IRR calculations,
cash flow projections, scenario analysis, and sensitivity testing.
"""

import logging
import numpy as np
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
import statistics
import random

# Try to import scipy, fall back to iterative methods if not available
try:
    from scipy.optimize import fsolve
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False

logger = logging.getLogger(__name__)


@dataclass
class CashFlow:
    """Represents a cash flow at a specific time period"""
    period: int
    amount: Decimal
    description: str = ""
    category: str = ""


@dataclass
class NPVResult:
    """Net Present Value calculation result"""
    npv: Decimal
    discount_rate: float
    initial_investment: Decimal
    cash_flows: List[CashFlow]
    present_values: List[Decimal]
    calculation_date: datetime


@dataclass
class IRRResult:
    """Internal Rate of Return calculation result"""
    irr: float
    npv_at_irr: Decimal
    cash_flows: List[CashFlow]
    iterations: int
    converged: bool
    calculation_date: datetime


@dataclass
class CashFlowProjection:
    """Cash flow projection result"""
    periods: List[int]
    projected_cash_flows: List[Decimal]
    cumulative_cash_flows: List[Decimal]
    growth_rate: float
    base_amount: Decimal
    projection_method: str
    confidence_interval: Tuple[List[Decimal], List[Decimal]]  # (lower, upper)


@dataclass
class ScenarioAnalysis:
    """Scenario analysis result"""
    base_case: Dict[str, Any]
    optimistic_case: Dict[str, Any]
    pessimistic_case: Dict[str, Any]
    scenario_probabilities: Dict[str, float]
    expected_value: Decimal
    risk_metrics: Dict[str, float]


@dataclass
class SensitivityAnalysis:
    """Sensitivity analysis result"""
    base_npv: Decimal
    sensitivity_results: Dict[str, Dict[str, Decimal]]  # variable -> {change_pct -> npv}
    tornado_chart_data: List[Dict[str, Any]]
    most_sensitive_variables: List[str]


class FinancialModelingEngine:
    """Advanced financial modeling engine"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Default configuration
        self.default_discount_rate = self.config.get('default_discount_rate', 0.10)
        self.max_irr_iterations = self.config.get('max_irr_iterations', 1000)
        self.irr_tolerance = self.config.get('irr_tolerance', 1e-6)
    
    def calculate_npv(
        self, 
        cash_flows: List[CashFlow], 
        discount_rate: float,
        initial_investment: Decimal = None
    ) -> NPVResult:
        """
        Calculate Net Present Value for a series of cash flows
        
        Args:
            cash_flows: List of cash flows
            discount_rate: Discount rate (as decimal, e.g., 0.10 for 10%)
            initial_investment: Initial investment (if not included in cash flows)
            
        Returns:
            NPVResult with detailed calculation
        """
        try:
            if not cash_flows:
                raise ValueError("Cash flows list cannot be empty")
            
            if discount_rate < 0:
                raise ValueError("Discount rate cannot be negative")
            
            present_values = []
            npv = Decimal('0')
            
            # Add initial investment if provided
            if initial_investment is not None:
                npv -= initial_investment
            
            # Calculate present value for each cash flow
            for cf in cash_flows:
                if cf.period < 0:
                    raise ValueError(f"Period cannot be negative: {cf.period}")
                
                # PV = CF / (1 + r)^n
                discount_factor = Decimal(str((1 + discount_rate) ** cf.period))
                present_value = cf.amount / discount_factor
                present_values.append(present_value)
                npv += present_value
            
            self.logger.info(f"NPV calculated: {npv} at discount rate {discount_rate}")
            
            return NPVResult(
                npv=npv.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
                discount_rate=discount_rate,
                initial_investment=initial_investment or Decimal('0'),
                cash_flows=cash_flows,
                present_values=present_values,
                calculation_date=datetime.utcnow()
            )
            
        except Exception as e:
            self.logger.error(f"Error calculating NPV: {str(e)}")
            raise
    
    def calculate_irr(self, cash_flows: List[CashFlow]) -> IRRResult:
        """
        Calculate Internal Rate of Return for a series of cash flows
        
        Args:
            cash_flows: List of cash flows (must include initial investment as negative)
            
        Returns:
            IRRResult with detailed calculation
        """
        try:
            if not cash_flows:
                raise ValueError("Cash flows list cannot be empty")
            
            if len(cash_flows) < 2:
                raise ValueError("At least 2 cash flows required for IRR calculation")
            
            # Convert to numpy arrays for calculation
            periods = np.array([cf.period for cf in cash_flows])
            amounts = np.array([float(cf.amount) for cf in cash_flows])
            
            # Define NPV function for IRR calculation
            def npv_function(rate):
                return np.sum(amounts / (1 + rate) ** periods)
            
            # Initial guess for IRR
            initial_guess = 0.1
            
            if HAS_SCIPY:
                try:
                    # Use scipy's fsolve to find the rate where NPV = 0
                    irr_solution = fsolve(npv_function, initial_guess, full_output=True)
                    irr = float(irr_solution[0][0])
                    converged = irr_solution[2] == 1
                    iterations = irr_solution[1]['nfev']
                    
                    # Verify the solution
                    npv_at_irr = Decimal(str(npv_function(irr)))
                    
                    # Check if IRR is reasonable (between -100% and 1000%)
                    if irr < -1.0 or irr > 10.0:
                        self.logger.warning(f"IRR result may be unrealistic: {irr:.4f}")
                    
                except Exception as solve_error:
                    self.logger.warning(f"IRR calculation failed with fsolve: {solve_error}")
                    # Fallback to simple iteration method
                    irr, npv_at_irr, iterations, converged = self._calculate_irr_iterative(cash_flows)
            else:
                # Use iterative method if scipy is not available
                irr, npv_at_irr, iterations, converged = self._calculate_irr_iterative(cash_flows)
            
            self.logger.info(f"IRR calculated: {irr:.4f} ({irr*100:.2f}%)")
            
            return IRRResult(
                irr=irr,
                npv_at_irr=npv_at_irr.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
                cash_flows=cash_flows,
                iterations=iterations,
                converged=converged,
                calculation_date=datetime.utcnow()
            )
            
        except Exception as e:
            self.logger.error(f"Error calculating IRR: {str(e)}")
            raise
    
    def _calculate_irr_iterative(self, cash_flows: List[CashFlow]) -> Tuple[float, Decimal, int, bool]:
        """
        Fallback iterative method for IRR calculation
        """
        def npv_at_rate(rate):
            npv = Decimal('0')
            for cf in cash_flows:
                npv += cf.amount / Decimal(str((1 + rate) ** cf.period))
            return npv
        
        # Binary search for IRR
        low_rate = -0.99  # -99%
        high_rate = 10.0  # 1000%
        tolerance = self.irr_tolerance
        max_iterations = self.max_irr_iterations
        
        for iteration in range(max_iterations):
            mid_rate = (low_rate + high_rate) / 2
            npv = npv_at_rate(mid_rate)
            
            if abs(float(npv)) < tolerance:
                return mid_rate, npv, iteration + 1, True
            
            if npv > 0:
                low_rate = mid_rate
            else:
                high_rate = mid_rate
        
        # Return best approximation if not converged
        final_rate = (low_rate + high_rate) / 2
        final_npv = npv_at_rate(final_rate)
        return final_rate, final_npv, max_iterations, False
    
    def project_cash_flows(
        self,
        base_cash_flow: Decimal,
        periods: int,
        growth_rate: float = 0.0,
        volatility: float = 0.0,
        method: str = 'linear'
    ) -> CashFlowProjection:
        """
        Project future cash flows based on various methods
        
        Args:
            base_cash_flow: Starting cash flow amount
            periods: Number of periods to project
            growth_rate: Annual growth rate (as decimal)
            volatility: Volatility for confidence intervals
            method: Projection method ('linear', 'compound', 'declining')
            
        Returns:
            CashFlowProjection with detailed projections
        """
        try:
            if periods <= 0:
                raise ValueError("Periods must be positive")
            
            projected_flows = []
            cumulative_flows = []
            cumulative = Decimal('0')
            
            for period in range(1, periods + 1):
                if method == 'linear':
                    # Linear growth: CF_t = CF_0 * (1 + growth_rate * t)
                    projected_cf = base_cash_flow * Decimal(str(1 + growth_rate * period))
                elif method == 'compound':
                    # Compound growth: CF_t = CF_0 * (1 + growth_rate)^t
                    projected_cf = base_cash_flow * Decimal(str((1 + growth_rate) ** period))
                elif method == 'declining':
                    # Declining growth: CF_t = CF_0 * (1 - growth_rate)^t
                    projected_cf = base_cash_flow * Decimal(str((1 - abs(growth_rate)) ** period))
                else:
                    raise ValueError(f"Unknown projection method: {method}")
                
                projected_flows.append(projected_cf)
                cumulative += projected_cf
                cumulative_flows.append(cumulative)
            
            # Calculate confidence intervals if volatility is provided
            lower_bounds = []
            upper_bounds = []
            
            if volatility > 0:
                for i, cf in enumerate(projected_flows):
                    # Simple confidence interval based on volatility
                    std_dev = cf * Decimal(str(volatility * ((i + 1) ** 0.5)))
                    lower_bounds.append(cf - std_dev * Decimal('1.96'))  # 95% CI
                    upper_bounds.append(cf + std_dev * Decimal('1.96'))
            else:
                lower_bounds = projected_flows.copy()
                upper_bounds = projected_flows.copy()
            
            self.logger.info(f"Projected {periods} periods of cash flows using {method} method")
            
            return CashFlowProjection(
                periods=list(range(1, periods + 1)),
                projected_cash_flows=projected_flows,
                cumulative_cash_flows=cumulative_flows,
                growth_rate=growth_rate,
                base_amount=base_cash_flow,
                projection_method=method,
                confidence_interval=(lower_bounds, upper_bounds)
            )
            
        except Exception as e:
            self.logger.error(f"Error projecting cash flows: {str(e)}")
            raise
    
    def perform_scenario_analysis(
        self,
        base_case_params: Dict[str, Any],
        scenario_adjustments: Dict[str, Dict[str, float]] = None
    ) -> ScenarioAnalysis:
        """
        Perform scenario analysis with optimistic, base, and pessimistic cases
        
        Args:
            base_case_params: Base case parameters
            scenario_adjustments: Adjustments for different scenarios
            
        Returns:
            ScenarioAnalysis with detailed results
        """
        try:
            # Default scenario adjustments if not provided
            if scenario_adjustments is None:
                scenario_adjustments = {
                    'optimistic': {
                        'revenue_growth': 0.2,  # 20% higher
                        'cost_reduction': -0.1,  # 10% lower costs
                        'discount_rate': -0.02   # 2% lower discount rate
                    },
                    'pessimistic': {
                        'revenue_growth': -0.2,  # 20% lower
                        'cost_increase': 0.15,   # 15% higher costs
                        'discount_rate': 0.03    # 3% higher discount rate
                    }
                }
            
            scenarios = {}
            
            # Base case
            base_npv = self._calculate_scenario_npv(base_case_params)
            scenarios['base'] = {
                'npv': base_npv,
                'parameters': base_case_params.copy(),
                'probability': 0.5
            }
            
            # Optimistic case
            optimistic_params = base_case_params.copy()
            for param, adjustment in scenario_adjustments.get('optimistic', {}).items():
                if param in optimistic_params:
                    if isinstance(optimistic_params[param], (int, float)):
                        optimistic_params[param] *= (1 + adjustment)
                    elif isinstance(optimistic_params[param], Decimal):
                        optimistic_params[param] *= Decimal(str(1 + adjustment))
            
            optimistic_npv = self._calculate_scenario_npv(optimistic_params)
            scenarios['optimistic'] = {
                'npv': optimistic_npv,
                'parameters': optimistic_params,
                'probability': 0.25
            }
            
            # Pessimistic case
            pessimistic_params = base_case_params.copy()
            for param, adjustment in scenario_adjustments.get('pessimistic', {}).items():
                if param in pessimistic_params:
                    if isinstance(pessimistic_params[param], (int, float)):
                        pessimistic_params[param] *= (1 + adjustment)
                    elif isinstance(pessimistic_params[param], Decimal):
                        pessimistic_params[param] *= Decimal(str(1 + adjustment))
            
            pessimistic_npv = self._calculate_scenario_npv(pessimistic_params)
            scenarios['pessimistic'] = {
                'npv': pessimistic_npv,
                'parameters': pessimistic_params,
                'probability': 0.25
            }
            
            # Calculate expected value
            expected_value = (
                scenarios['base']['npv'] * Decimal(str(scenarios['base']['probability'])) +
                scenarios['optimistic']['npv'] * Decimal(str(scenarios['optimistic']['probability'])) +
                scenarios['pessimistic']['npv'] * Decimal(str(scenarios['pessimistic']['probability']))
            )
            
            # Calculate risk metrics
            npv_values = [float(s['npv']) for s in scenarios.values()]
            risk_metrics = {
                'standard_deviation': statistics.stdev(npv_values) if len(npv_values) > 1 else 0.0,
                'coefficient_of_variation': statistics.stdev(npv_values) / statistics.mean(npv_values) if statistics.mean(npv_values) != 0 else 0.0,
                'downside_risk': max(0, float(base_npv - pessimistic_npv)),
                'upside_potential': max(0, float(optimistic_npv - base_npv))
            }
            
            self.logger.info(f"Scenario analysis completed. Expected NPV: {expected_value}")
            
            return ScenarioAnalysis(
                base_case=scenarios['base'],
                optimistic_case=scenarios['optimistic'],
                pessimistic_case=scenarios['pessimistic'],
                scenario_probabilities={k: v['probability'] for k, v in scenarios.items()},
                expected_value=expected_value,
                risk_metrics=risk_metrics
            )
            
        except Exception as e:
            self.logger.error(f"Error performing scenario analysis: {str(e)}")
            raise
    
    def _calculate_scenario_npv(self, params: Dict[str, Any]) -> Decimal:
        """
        Calculate NPV for a specific scenario
        """
        # Extract parameters
        initial_investment = params.get('initial_investment', Decimal('100000'))
        annual_cash_flow = params.get('annual_cash_flow', Decimal('25000'))
        periods = params.get('periods', 5)
        discount_rate = params.get('discount_rate', 0.10)
        growth_rate = params.get('growth_rate', 0.05)
        
        # Generate cash flows
        cash_flows = []
        for period in range(1, periods + 1):
            cf_amount = annual_cash_flow * Decimal(str((1 + growth_rate) ** period))
            cash_flows.append(CashFlow(period=period, amount=cf_amount))
        
        # Calculate NPV
        npv_result = self.calculate_npv(cash_flows, discount_rate, initial_investment)
        return npv_result.npv
    
    def perform_sensitivity_analysis(
        self,
        base_case_params: Dict[str, Any],
        sensitivity_variables: List[str] = None,
        change_percentages: List[float] = None
    ) -> SensitivityAnalysis:
        """
        Perform sensitivity analysis on key variables
        
        Args:
            base_case_params: Base case parameters
            sensitivity_variables: Variables to analyze
            change_percentages: Percentage changes to test
            
        Returns:
            SensitivityAnalysis with detailed results
        """
        try:
            # Default variables and changes if not provided
            if sensitivity_variables is None:
                sensitivity_variables = ['annual_cash_flow', 'discount_rate', 'growth_rate', 'initial_investment']
            
            if change_percentages is None:
                change_percentages = [-0.3, -0.2, -0.1, 0.0, 0.1, 0.2, 0.3]  # -30% to +30%
            
            # Calculate base case NPV
            base_npv = self._calculate_scenario_npv(base_case_params)
            
            sensitivity_results = {}
            tornado_data = []
            
            for variable in sensitivity_variables:
                if variable not in base_case_params:
                    continue
                
                variable_results = {}
                npv_changes = []
                
                for change_pct in change_percentages:
                    # Create modified parameters
                    modified_params = base_case_params.copy()
                    
                    if isinstance(modified_params[variable], (int, float)):
                        modified_params[variable] *= (1 + change_pct)
                    elif isinstance(modified_params[variable], Decimal):
                        modified_params[variable] *= Decimal(str(1 + change_pct))
                    
                    # Calculate NPV with modified parameter
                    modified_npv = self._calculate_scenario_npv(modified_params)
                    variable_results[f"{change_pct:.1%}"] = modified_npv
                    
                    if change_pct != 0.0:
                        npv_change = modified_npv - base_npv
                        npv_changes.append(abs(float(npv_change)))
                
                sensitivity_results[variable] = variable_results
                
                # Calculate sensitivity measure for tornado chart
                if npv_changes:
                    max_impact = max(npv_changes)
                    tornado_data.append({
                        'variable': variable,
                        'max_impact': max_impact,
                        'low_npv': min(variable_results.values()),
                        'high_npv': max(variable_results.values())
                    })
            
            # Sort variables by impact for tornado chart
            tornado_data.sort(key=lambda x: x['max_impact'], reverse=True)
            most_sensitive = [item['variable'] for item in tornado_data[:3]]
            
            self.logger.info(f"Sensitivity analysis completed. Most sensitive variables: {most_sensitive}")
            
            return SensitivityAnalysis(
                base_npv=base_npv,
                sensitivity_results=sensitivity_results,
                tornado_chart_data=tornado_data,
                most_sensitive_variables=most_sensitive
            )
            
        except Exception as e:
            self.logger.error(f"Error performing sensitivity analysis: {str(e)}")
            raise
    
    def calculate_payback_period(self, cash_flows: List[CashFlow], initial_investment: Decimal) -> Dict[str, Any]:
        """
        Calculate simple and discounted payback periods
        
        Args:
            cash_flows: List of cash flows
            initial_investment: Initial investment amount
            
        Returns:
            Dictionary with payback period calculations
        """
        try:
            if not cash_flows:
                raise ValueError("Cash flows list cannot be empty")
            
            # Sort cash flows by period
            sorted_flows = sorted(cash_flows, key=lambda x: x.period)
            
            # Simple payback period
            cumulative_simple = Decimal('0')
            simple_payback = None
            
            for cf in sorted_flows:
                cumulative_simple += cf.amount
                if cumulative_simple >= initial_investment and simple_payback is None:
                    # Interpolate for exact payback period
                    previous_cumulative = cumulative_simple - cf.amount
                    remaining = initial_investment - previous_cumulative
                    fraction = remaining / cf.amount if cf.amount > 0 else 0
                    simple_payback = cf.period - 1 + float(fraction)
                    break
            
            # Discounted payback period
            discount_rate = self.default_discount_rate
            cumulative_discounted = Decimal('0')
            discounted_payback = None
            
            for cf in sorted_flows:
                pv = cf.amount / Decimal(str((1 + discount_rate) ** cf.period))
                cumulative_discounted += pv
                if cumulative_discounted >= initial_investment and discounted_payback is None:
                    # Interpolate for exact payback period
                    previous_cumulative = cumulative_discounted - pv
                    remaining = initial_investment - previous_cumulative
                    fraction = remaining / pv if pv > 0 else 0
                    discounted_payback = cf.period - 1 + float(fraction)
                    break
            
            return {
                'simple_payback_period': simple_payback,
                'discounted_payback_period': discounted_payback,
                'discount_rate_used': discount_rate,
                'initial_investment': initial_investment,
                'total_undiscounted_cash_flows': sum(cf.amount for cf in cash_flows),
                'calculation_date': datetime.utcnow()
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating payback period: {str(e)}")
            raise
    
    def calculate_profitability_index(
        self, 
        cash_flows: List[CashFlow], 
        initial_investment: Decimal,
        discount_rate: float = None
    ) -> Dict[str, Any]:
        """
        Calculate Profitability Index (PI)
        
        Args:
            cash_flows: List of cash flows
            initial_investment: Initial investment amount
            discount_rate: Discount rate (uses default if not provided)
            
        Returns:
            Dictionary with PI calculation results
        """
        try:
            if discount_rate is None:
                discount_rate = self.default_discount_rate
            
            # Calculate NPV
            npv_result = self.calculate_npv(cash_flows, discount_rate, initial_investment)
            
            # Calculate present value of cash inflows
            pv_inflows = sum(npv_result.present_values)
            
            # Profitability Index = PV of inflows / Initial Investment
            if initial_investment > 0:
                pi = pv_inflows / initial_investment
            else:
                pi = Decimal('0')
            
            # Interpretation
            if pi > 1:
                interpretation = "Profitable - Accept project"
            elif pi == 1:
                interpretation = "Break-even - Indifferent"
            else:
                interpretation = "Unprofitable - Reject project"
            
            return {
                'profitability_index': pi,
                'pv_of_inflows': pv_inflows,
                'initial_investment': initial_investment,
                'npv': npv_result.npv,
                'discount_rate': discount_rate,
                'interpretation': interpretation,
                'calculation_date': datetime.utcnow()
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating profitability index: {str(e)}")
            raise