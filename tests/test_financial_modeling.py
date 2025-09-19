"""
Tests for Financial Modeling Service

Tests NPV, IRR calculations, cash flow projections, scenario analysis,
and sensitivity testing functionality.
"""

import unittest
from decimal import Decimal
from datetime import datetime, timedelta
import sys
import os

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.financial_modeling import (
    FinancialModelingEngine, CashFlow, NPVResult, IRRResult,
    CashFlowProjection, ScenarioAnalysis, SensitivityAnalysis
)


class TestFinancialModelingEngine(unittest.TestCase):
    """Test cases for Financial Modeling Engine"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.engine = FinancialModelingEngine()
        
        # Sample cash flows for testing
        self.sample_cash_flows = [
            CashFlow(period=1, amount=Decimal('25000'), description="Year 1 cash flow"),
            CashFlow(period=2, amount=Decimal('30000'), description="Year 2 cash flow"),
            CashFlow(period=3, amount=Decimal('35000'), description="Year 3 cash flow"),
            CashFlow(period=4, amount=Decimal('40000'), description="Year 4 cash flow"),
            CashFlow(period=5, amount=Decimal('45000'), description="Year 5 cash flow")
        ]
        
        # Cash flows with initial investment for IRR testing
        self.irr_cash_flows = [
            CashFlow(period=0, amount=Decimal('-100000'), description="Initial investment"),
            CashFlow(period=1, amount=Decimal('25000'), description="Year 1 return"),
            CashFlow(period=2, amount=Decimal('30000'), description="Year 2 return"),
            CashFlow(period=3, amount=Decimal('35000'), description="Year 3 return"),
            CashFlow(period=4, amount=Decimal('40000'), description="Year 4 return"),
            CashFlow(period=5, amount=Decimal('45000'), description="Year 5 return")
        ]
    
    def test_npv_calculation_basic(self):
        """Test basic NPV calculation"""
        discount_rate = 0.10
        initial_investment = Decimal('100000')
        
        result = self.engine.calculate_npv(
            self.sample_cash_flows, 
            discount_rate, 
            initial_investment
        )
        
        self.assertIsInstance(result, NPVResult)
        self.assertIsInstance(result.npv, Decimal)
        self.assertEqual(result.discount_rate, discount_rate)
        self.assertEqual(result.initial_investment, initial_investment)
        self.assertEqual(len(result.present_values), len(self.sample_cash_flows))
        self.assertIsInstance(result.calculation_date, datetime)
        
        # NPV should be positive for this profitable project
        self.assertGreater(result.npv, Decimal('0'))
    
    def test_npv_calculation_without_initial_investment(self):
        """Test NPV calculation without separate initial investment"""
        discount_rate = 0.08
        
        result = self.engine.calculate_npv(self.sample_cash_flows, discount_rate)
        
        self.assertIsInstance(result, NPVResult)
        self.assertEqual(result.initial_investment, Decimal('0'))
        self.assertGreater(result.npv, Decimal('0'))
    
    def test_npv_calculation_edge_cases(self):
        """Test NPV calculation edge cases"""
        # Empty cash flows should raise error
        with self.assertRaises(ValueError):
            self.engine.calculate_npv([], 0.10)
        
        # Negative discount rate should raise error
        with self.assertRaises(ValueError):
            self.engine.calculate_npv(self.sample_cash_flows, -0.05)
        
        # Negative period should raise error
        bad_cash_flows = [CashFlow(period=-1, amount=Decimal('1000'))]
        with self.assertRaises(ValueError):
            self.engine.calculate_npv(bad_cash_flows, 0.10)
    
    def test_irr_calculation_basic(self):
        """Test basic IRR calculation"""
        result = self.engine.calculate_irr(self.irr_cash_flows)
        
        self.assertIsInstance(result, IRRResult)
        self.assertIsInstance(result.irr, float)
        self.assertIsInstance(result.npv_at_irr, Decimal)
        self.assertTrue(result.converged)
        self.assertGreater(result.iterations, 0)
        self.assertIsInstance(result.calculation_date, datetime)
        
        # IRR should be reasonable (between 0% and 100% for this example)
        self.assertGreater(result.irr, 0.0)
        self.assertLess(result.irr, 1.0)
        
        # NPV at IRR should be close to zero
        self.assertLess(abs(result.npv_at_irr), Decimal('1'))
    
    def test_irr_calculation_edge_cases(self):
        """Test IRR calculation edge cases"""
        # Empty cash flows should raise error
        with self.assertRaises(ValueError):
            self.engine.calculate_irr([])
        
        # Single cash flow should raise error
        with self.assertRaises(ValueError):
            self.engine.calculate_irr([CashFlow(period=0, amount=Decimal('1000'))])
    
    def test_cash_flow_projection_linear(self):
        """Test linear cash flow projection"""
        base_cf = Decimal('10000')
        periods = 5
        growth_rate = 0.05
        
        result = self.engine.project_cash_flows(
            base_cf, periods, growth_rate, method='linear'
        )
        
        self.assertIsInstance(result, CashFlowProjection)
        self.assertEqual(len(result.projected_cash_flows), periods)
        self.assertEqual(len(result.cumulative_cash_flows), periods)
        self.assertEqual(result.growth_rate, growth_rate)
        self.assertEqual(result.base_amount, base_cf)
        self.assertEqual(result.projection_method, 'linear')
        
        # Check that cash flows are increasing
        for i in range(1, len(result.projected_cash_flows)):
            self.assertGreater(result.projected_cash_flows[i], result.projected_cash_flows[i-1])
        
        # Check cumulative flows are increasing
        for i in range(1, len(result.cumulative_cash_flows)):
            self.assertGreater(result.cumulative_cash_flows[i], result.cumulative_cash_flows[i-1])
    
    def test_cash_flow_projection_compound(self):
        """Test compound cash flow projection"""
        base_cf = Decimal('10000')
        periods = 5
        growth_rate = 0.10
        
        result = self.engine.project_cash_flows(
            base_cf, periods, growth_rate, method='compound'
        )
        
        self.assertEqual(result.projection_method, 'compound')
        
        # Compound growth should result in exponential increase
        expected_cf_period_2 = base_cf * Decimal('1.21')  # (1.10)^2
        self.assertAlmostEqual(
            float(result.projected_cash_flows[1]), 
            float(expected_cf_period_2), 
            places=2
        )
    
    def test_cash_flow_projection_declining(self):
        """Test declining cash flow projection"""
        base_cf = Decimal('10000')
        periods = 5
        decline_rate = 0.05
        
        result = self.engine.project_cash_flows(
            base_cf, periods, decline_rate, method='declining'
        )
        
        self.assertEqual(result.projection_method, 'declining')
        
        # Cash flows should be decreasing
        for i in range(1, len(result.projected_cash_flows)):
            self.assertLess(result.projected_cash_flows[i], result.projected_cash_flows[i-1])
    
    def test_cash_flow_projection_with_volatility(self):
        """Test cash flow projection with confidence intervals"""
        base_cf = Decimal('10000')
        periods = 3
        volatility = 0.2
        
        result = self.engine.project_cash_flows(
            base_cf, periods, volatility=volatility
        )
        
        lower_bounds, upper_bounds = result.confidence_interval
        
        # Check that confidence intervals exist
        self.assertEqual(len(lower_bounds), periods)
        self.assertEqual(len(upper_bounds), periods)
        
        # Lower bounds should be less than upper bounds
        for i in range(periods):
            self.assertLess(lower_bounds[i], upper_bounds[i])
    
    def test_cash_flow_projection_edge_cases(self):
        """Test cash flow projection edge cases"""
        # Zero or negative periods should raise error
        with self.assertRaises(ValueError):
            self.engine.project_cash_flows(Decimal('1000'), 0)
        
        with self.assertRaises(ValueError):
            self.engine.project_cash_flows(Decimal('1000'), -1)
        
        # Unknown method should raise error
        with self.assertRaises(ValueError):
            self.engine.project_cash_flows(Decimal('1000'), 5, method='unknown')
    
    def test_scenario_analysis_basic(self):
        """Test basic scenario analysis"""
        base_params = {
            'initial_investment': Decimal('100000'),
            'annual_cash_flow': Decimal('25000'),
            'periods': 5,
            'discount_rate': 0.10,
            'growth_rate': 0.05
        }
        
        result = self.engine.perform_scenario_analysis(base_params)
        
        self.assertIsInstance(result, ScenarioAnalysis)
        self.assertIn('npv', result.base_case)
        self.assertIn('npv', result.optimistic_case)
        self.assertIn('npv', result.pessimistic_case)
        
        # Optimistic case should have higher NPV than base case
        self.assertGreater(result.optimistic_case['npv'], result.base_case['npv'])
        
        # Pessimistic case should have lower NPV than base case
        self.assertLess(result.pessimistic_case['npv'], result.base_case['npv'])
        
        # Check probabilities sum to 1
        total_prob = sum(result.scenario_probabilities.values())
        self.assertAlmostEqual(total_prob, 1.0, places=2)
        
        # Check risk metrics
        self.assertIn('standard_deviation', result.risk_metrics)
        self.assertIn('coefficient_of_variation', result.risk_metrics)
        self.assertIn('downside_risk', result.risk_metrics)
        self.assertIn('upside_potential', result.risk_metrics)
    
    def test_scenario_analysis_custom_adjustments(self):
        """Test scenario analysis with custom adjustments"""
        base_params = {
            'initial_investment': Decimal('50000'),
            'annual_cash_flow': Decimal('15000'),
            'periods': 4,
            'discount_rate': 0.08,
            'growth_rate': 0.03
        }
        
        custom_adjustments = {
            'optimistic': {
                'annual_cash_flow': 0.3,  # 30% higher
                'growth_rate': 0.5        # 50% higher growth
            },
            'pessimistic': {
                'annual_cash_flow': -0.2,  # 20% lower
                'discount_rate': 0.25      # 25% higher discount rate
            }
        }
        
        result = self.engine.perform_scenario_analysis(base_params, custom_adjustments)
        
        self.assertIsInstance(result, ScenarioAnalysis)
        
        # Check that adjustments were applied
        base_cf = base_params['annual_cash_flow']
        opt_cf = result.optimistic_case['parameters']['annual_cash_flow']
        self.assertGreater(opt_cf, base_cf)
    
    def test_sensitivity_analysis_basic(self):
        """Test basic sensitivity analysis"""
        base_params = {
            'initial_investment': Decimal('100000'),
            'annual_cash_flow': Decimal('30000'),
            'periods': 5,
            'discount_rate': 0.12,
            'growth_rate': 0.04
        }
        
        result = self.engine.perform_sensitivity_analysis(base_params)
        
        self.assertIsInstance(result, SensitivityAnalysis)
        self.assertIsInstance(result.base_npv, Decimal)
        self.assertIsInstance(result.sensitivity_results, dict)
        self.assertIsInstance(result.tornado_chart_data, list)
        self.assertIsInstance(result.most_sensitive_variables, list)
        
        # Check that sensitivity results contain expected variables
        expected_vars = ['annual_cash_flow', 'discount_rate', 'growth_rate', 'initial_investment']
        for var in expected_vars:
            if var in base_params:
                self.assertIn(var, result.sensitivity_results)
        
        # Check tornado chart data structure
        if result.tornado_chart_data:
            tornado_item = result.tornado_chart_data[0]
            self.assertIn('variable', tornado_item)
            self.assertIn('max_impact', tornado_item)
            self.assertIn('low_npv', tornado_item)
            self.assertIn('high_npv', tornado_item)
        
        # Most sensitive variables should be sorted by impact
        self.assertLessEqual(len(result.most_sensitive_variables), 3)
    
    def test_sensitivity_analysis_custom_variables(self):
        """Test sensitivity analysis with custom variables"""
        base_params = {
            'initial_investment': Decimal('75000'),
            'annual_cash_flow': Decimal('20000'),
            'periods': 6,
            'discount_rate': 0.09
        }
        
        custom_variables = ['annual_cash_flow', 'discount_rate']
        custom_changes = [-0.1, 0.0, 0.1]  # -10%, 0%, +10%
        
        result = self.engine.perform_sensitivity_analysis(
            base_params, custom_variables, custom_changes
        )
        
        # Should only analyze specified variables
        for var in custom_variables:
            self.assertIn(var, result.sensitivity_results)
        
        # Should not analyze variables not in the list
        self.assertNotIn('growth_rate', result.sensitivity_results)
        
        # Check that custom change percentages were used
        for var in custom_variables:
            var_results = result.sensitivity_results[var]
            self.assertIn('-10.0%', var_results)
            self.assertIn('0.0%', var_results)
            self.assertIn('10.0%', var_results)
    
    def test_payback_period_calculation(self):
        """Test payback period calculation"""
        initial_investment = Decimal('80000')
        
        result = self.engine.calculate_payback_period(
            self.sample_cash_flows, initial_investment
        )
        
        self.assertIn('simple_payback_period', result)
        self.assertIn('discounted_payback_period', result)
        self.assertIn('discount_rate_used', result)
        self.assertIn('initial_investment', result)
        self.assertIn('calculation_date', result)
        
        # Simple payback should be shorter than discounted payback
        if result['simple_payback_period'] and result['discounted_payback_period']:
            self.assertLessEqual(
                result['simple_payback_period'], 
                result['discounted_payback_period']
            )
        
        # Payback periods should be positive
        if result['simple_payback_period']:
            self.assertGreater(result['simple_payback_period'], 0)
        if result['discounted_payback_period']:
            self.assertGreater(result['discounted_payback_period'], 0)
    
    def test_payback_period_no_payback(self):
        """Test payback period when investment is never recovered"""
        # Very high initial investment that won't be recovered
        initial_investment = Decimal('1000000')
        
        result = self.engine.calculate_payback_period(
            self.sample_cash_flows, initial_investment
        )
        
        # Should return None when payback is not achieved
        self.assertIsNone(result['simple_payback_period'])
        self.assertIsNone(result['discounted_payback_period'])
    
    def test_profitability_index_calculation(self):
        """Test profitability index calculation"""
        initial_investment = Decimal('90000')
        discount_rate = 0.11
        
        result = self.engine.calculate_profitability_index(
            self.sample_cash_flows, initial_investment, discount_rate
        )
        
        self.assertIn('profitability_index', result)
        self.assertIn('pv_of_inflows', result)
        self.assertIn('initial_investment', result)
        self.assertIn('npv', result)
        self.assertIn('discount_rate', result)
        self.assertIn('interpretation', result)
        self.assertIn('calculation_date', result)
        
        # PI should be positive
        self.assertGreater(result['profitability_index'], Decimal('0'))
        
        # Check interpretation logic
        pi = result['profitability_index']
        interpretation = result['interpretation']
        
        if pi > 1:
            self.assertIn('Accept', interpretation)
        elif pi == 1:
            self.assertIn('Indifferent', interpretation)
        else:
            self.assertIn('Reject', interpretation)
    
    def test_profitability_index_default_discount_rate(self):
        """Test profitability index with default discount rate"""
        initial_investment = Decimal('70000')
        
        result = self.engine.calculate_profitability_index(
            self.sample_cash_flows, initial_investment
        )
        
        # Should use default discount rate
        self.assertEqual(result['discount_rate'], self.engine.default_discount_rate)
    
    def test_profitability_index_zero_investment(self):
        """Test profitability index with zero initial investment"""
        initial_investment = Decimal('0')
        
        result = self.engine.calculate_profitability_index(
            self.sample_cash_flows, initial_investment
        )
        
        # PI should be 0 when initial investment is 0
        self.assertEqual(result['profitability_index'], Decimal('0'))
    
    def test_engine_configuration(self):
        """Test engine configuration options"""
        custom_config = {
            'default_discount_rate': 0.15,
            'max_irr_iterations': 500,
            'irr_tolerance': 1e-8
        }
        
        engine = FinancialModelingEngine(custom_config)
        
        self.assertEqual(engine.default_discount_rate, 0.15)
        self.assertEqual(engine.max_irr_iterations, 500)
        self.assertEqual(engine.irr_tolerance, 1e-8)
    
    def test_cash_flow_data_structure(self):
        """Test CashFlow data structure"""
        cf = CashFlow(
            period=3, 
            amount=Decimal('15000'), 
            description="Test cash flow",
            category="revenue"
        )
        
        self.assertEqual(cf.period, 3)
        self.assertEqual(cf.amount, Decimal('15000'))
        self.assertEqual(cf.description, "Test cash flow")
        self.assertEqual(cf.category, "revenue")


if __name__ == '__main__':
    unittest.main()