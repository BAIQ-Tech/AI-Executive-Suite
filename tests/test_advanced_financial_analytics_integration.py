"""
Integration Tests for Advanced Financial Analytics

Tests the integration of financial modeling, industry benchmarking,
and risk assessment into the main analytics service.
"""

import unittest
from decimal import Decimal
import sys
import os

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.analytics import AnalyticsService


class TestAdvancedFinancialAnalyticsIntegration(unittest.TestCase):
    """Test cases for Advanced Financial Analytics Integration"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.service = AnalyticsService({})
        
        # Sample cash flows for testing
        self.sample_cash_flows = [
            {'period': 1, 'amount': 25000, 'description': 'Year 1 cash flow'},
            {'period': 2, 'amount': 30000, 'description': 'Year 2 cash flow'},
            {'period': 3, 'amount': 35000, 'description': 'Year 3 cash flow'},
            {'period': 4, 'amount': 40000, 'description': 'Year 4 cash flow'},
            {'period': 5, 'amount': 45000, 'description': 'Year 5 cash flow'}
        ]
        
        # Sample IRR cash flows (including initial investment)
        self.irr_cash_flows = [
            {'period': 0, 'amount': -100000, 'description': 'Initial investment'},
            {'period': 1, 'amount': 25000, 'description': 'Year 1 return'},
            {'period': 2, 'amount': 30000, 'description': 'Year 2 return'},
            {'period': 3, 'amount': 35000, 'description': 'Year 3 return'},
            {'period': 4, 'amount': 40000, 'description': 'Year 4 return'},
            {'period': 5, 'amount': 45000, 'description': 'Year 5 return'}
        ]
        
        # Sample company profile
        self.sample_company_profile = {
            'company_id': 'test_company_123',
            'name': 'Test Technology Company',
            'industry': 'technology',
            'size': 'medium',
            'revenue': 50000000,
            'employees': 200,
            'founded_year': 2015,
            'location': 'San Francisco, CA',
            'public_company': False
        }
    
    def test_npv_analysis_integration(self):
        """Test NPV analysis integration"""
        result = self.service.calculate_npv_analysis(
            self.sample_cash_flows, 
            0.10, 
            Decimal('100000')
        )
        
        self.assertIsInstance(result, dict)
        self.assertIn('npv', result)
        self.assertIn('payback_period', result)
        self.assertIn('profitability_index', result)
        self.assertIn('calculation_date', result)
        
        # Check NPV structure
        npv_data = result['npv']
        self.assertIn('value', npv_data)
        self.assertIn('discount_rate', npv_data)
        self.assertIn('initial_investment', npv_data)
        self.assertIn('present_values', npv_data)
        
        # Check payback period structure
        payback_data = result['payback_period']
        self.assertIn('simple', payback_data)
        self.assertIn('discounted', payback_data)
        
        # Check profitability index structure
        pi_data = result['profitability_index']
        self.assertIn('value', pi_data)
        self.assertIn('interpretation', pi_data)
    
    def test_irr_analysis_integration(self):
        """Test IRR analysis integration"""
        result = self.service.calculate_irr_analysis(self.irr_cash_flows)
        
        self.assertIsInstance(result, dict)
        self.assertIn('irr', result)
        self.assertIn('irr_percentage', result)
        self.assertIn('npv_at_irr', result)
        self.assertIn('converged', result)
        self.assertIn('iterations', result)
        self.assertIn('calculation_date', result)
        
        # IRR should be reasonable
        self.assertIsInstance(result['irr'], float)
        self.assertGreater(result['irr'], 0.0)
        self.assertLess(result['irr'], 1.0)
        
        # IRR percentage should be IRR * 100
        self.assertAlmostEqual(result['irr_percentage'], result['irr'] * 100, places=2)
    
    def test_scenario_analysis_integration(self):
        """Test scenario analysis integration"""
        base_params = {
            'initial_investment': Decimal('100000'),
            'annual_cash_flow': Decimal('25000'),
            'periods': 5,
            'discount_rate': 0.10,
            'growth_rate': 0.05
        }
        
        result = self.service.perform_scenario_analysis(base_params)
        
        self.assertIsInstance(result, dict)
        self.assertIn('base_case', result)
        self.assertIn('optimistic_case', result)
        self.assertIn('pessimistic_case', result)
        self.assertIn('expected_value', result)
        self.assertIn('risk_metrics', result)
        
        # Check case structures
        for case in ['base_case', 'optimistic_case', 'pessimistic_case']:
            case_data = result[case]
            self.assertIn('npv', case_data)
            self.assertIn('probability', case_data)
        
        # Optimistic should be better than base, base better than pessimistic
        self.assertGreater(result['optimistic_case']['npv'], result['base_case']['npv'])
        self.assertGreater(result['base_case']['npv'], result['pessimistic_case']['npv'])
    
    def test_sensitivity_analysis_integration(self):
        """Test sensitivity analysis integration"""
        base_params = {
            'initial_investment': Decimal('100000'),
            'annual_cash_flow': Decimal('30000'),
            'periods': 5,
            'discount_rate': 0.12,
            'growth_rate': 0.04
        }
        
        result = self.service.perform_sensitivity_analysis(base_params)
        
        self.assertIsInstance(result, dict)
        self.assertIn('base_npv', result)
        self.assertIn('sensitivity_results', result)
        self.assertIn('most_sensitive_variables', result)
        self.assertIn('tornado_chart_data', result)
        
        # Check sensitivity results structure
        sensitivity_results = result['sensitivity_results']
        self.assertIsInstance(sensitivity_results, dict)
        self.assertGreater(len(sensitivity_results), 0)
        
        # Check tornado chart data
        tornado_data = result['tornado_chart_data']
        self.assertIsInstance(tornado_data, list)
        if tornado_data:
            item = tornado_data[0]
            self.assertIn('variable', item)
            self.assertIn('max_impact', item)
            self.assertIn('low_npv', item)
            self.assertIn('high_npv', item)
    
    def test_industry_benchmarks_integration(self):
        """Test industry benchmarks integration"""
        # Test without company metrics
        result = self.service.get_industry_benchmarks('technology')
        
        self.assertIsInstance(result, dict)
        self.assertIn('industry', result)
        self.assertIn('benchmarks', result)
        self.assertEqual(result['industry'], 'technology')
        
        benchmarks = result['benchmarks']
        self.assertIsInstance(benchmarks, dict)
        self.assertGreater(len(benchmarks), 0)
        
        # Check benchmark structure
        for metric_name, benchmark_data in benchmarks.items():
            self.assertIn('industry_average', benchmark_data)
            self.assertIn('percentile_25', benchmark_data)
            self.assertIn('percentile_50', benchmark_data)
            self.assertIn('percentile_75', benchmark_data)
            self.assertIn('unit', benchmark_data)
            self.assertIn('sample_size', benchmark_data)
            self.assertIn('data_source', benchmark_data)
        
        # Test with company metrics
        company_metrics = {
            'revenue_growth_rate': 18.5,
            'profit_margin': 25.2
        }
        
        result_with_comparison = self.service.get_industry_benchmarks(
            'technology', company_metrics
        )
        
        self.assertIn('comparisons', result_with_comparison)
        comparisons = result_with_comparison['comparisons']
        
        for metric_name, comparison_data in comparisons.items():
            self.assertIn('company_value', comparison_data)
            self.assertIn('industry_median', comparison_data)
            self.assertIn('industry_average', comparison_data)
            self.assertIn('percentile_rank', comparison_data)
            self.assertIn('performance_rating', comparison_data)
            self.assertIn('improvement_potential', comparison_data)
            self.assertIn('peer_companies', comparison_data)
    
    def test_competitive_analysis_integration(self):
        """Test competitive analysis integration"""
        result = self.service.perform_competitive_analysis(self.sample_company_profile)
        
        self.assertIsInstance(result, dict)
        self.assertIn('company_profile', result)
        self.assertIn('market_position', result)
        self.assertIn('competitive_advantages', result)
        self.assertIn('competitive_disadvantages', result)
        self.assertIn('market_share_estimate', result)
        self.assertIn('growth_comparison', result)
        self.assertIn('direct_competitors', result)
        
        # Check company profile structure
        company_profile = result['company_profile']
        self.assertIn('name', company_profile)
        self.assertIn('industry', company_profile)
        self.assertIn('size', company_profile)
        
        # Check competitive advantages and disadvantages
        self.assertIsInstance(result['competitive_advantages'], list)
        self.assertIsInstance(result['competitive_disadvantages'], list)
        
        # Check direct competitors
        competitors = result['direct_competitors']
        self.assertIsInstance(competitors, list)
        if competitors:
            competitor = competitors[0]
            self.assertIn('name', competitor)
    
    def test_financial_risk_assessment_integration(self):
        """Test financial risk assessment integration"""
        # Test without company profile
        result = self.service.assess_financial_risk()
        
        self.assertIsInstance(result, dict)
        self.assertIn('overall_risk_score', result)
        self.assertIn('risk_level', result)
        self.assertIn('confidence_interval', result)
        self.assertIn('recommendations', result)
        self.assertIn('score_breakdown', result)
        
        # Test with company profile
        result_with_profile = self.service.assess_financial_risk(self.sample_company_profile)
        
        self.assertIn('risk_by_category', result_with_profile)
        self.assertIn('monte_carlo_analysis', result_with_profile)
        self.assertIn('compliance_risks', result_with_profile)
        self.assertIn('key_recommendations', result_with_profile)
        
        # Check risk by category
        risk_by_category = result_with_profile['risk_by_category']
        self.assertIsInstance(risk_by_category, dict)
        
        # Check Monte Carlo analysis
        mc_analysis = result_with_profile['monte_carlo_analysis']
        self.assertIn('mean_outcome', mc_analysis)
        self.assertIn('var_95', mc_analysis)
        self.assertIn('probability_of_loss', mc_analysis)
        
        # Check compliance risks
        compliance_risks = result_with_profile['compliance_risks']
        self.assertIsInstance(compliance_risks, list)
    
    def test_monte_carlo_simulation_integration(self):
        """Test Monte Carlo simulation integration"""
        base_scenario = {'base_outcome': 1000000}
        risk_parameters = {
            'market_risk': {
                'distribution': 'normal',
                'mean': 0,
                'std_dev': 200000,
                'impact_factor': 1.0
            },
            'operational_risk': {
                'distribution': 'triangular',
                'low': -500000,
                'high': 100000,
                'mode': -50000,
                'impact_factor': 0.5
            }
        }
        
        result = self.service.run_monte_carlo_risk_simulation(
            base_scenario, risk_parameters, 1000
        )
        
        self.assertIsInstance(result, dict)
        self.assertIn('simulation_runs', result)
        self.assertIn('mean_outcome', result)
        self.assertIn('median_outcome', result)
        self.assertIn('std_deviation', result)
        self.assertIn('percentile_5', result)
        self.assertIn('percentile_95', result)
        self.assertIn('var_95', result)
        self.assertIn('cvar_95', result)
        self.assertIn('probability_of_loss', result)
        self.assertIn('worst_case_scenario', result)
        self.assertIn('best_case_scenario', result)
        
        # Check simulation runs
        self.assertEqual(result['simulation_runs'], 1000)
        
        # Check statistical properties
        self.assertGreaterEqual(result['probability_of_loss'], 0.0)
        self.assertLessEqual(result['probability_of_loss'], 1.0)
        self.assertLessEqual(result['percentile_5'], result['median_outcome'])
        self.assertLessEqual(result['median_outcome'], result['percentile_95'])
    
    def test_error_handling(self):
        """Test error handling in integrated methods"""
        # Test with invalid cash flows
        invalid_cash_flows = [{'invalid': 'data'}]
        
        result = self.service.calculate_npv_analysis(invalid_cash_flows, 0.10)
        self.assertIn('error', result)
        
        # Test with invalid industry
        result = self.service.get_industry_benchmarks('invalid_industry')
        self.assertIn('error', result)
    
    def test_service_initialization_with_config(self):
        """Test service initialization with custom configuration"""
        custom_config = {
            'financial_modeling': {
                'default_discount_rate': 0.12,
                'max_irr_iterations': 500
            },
            'industry_benchmarking': {
                'cache_duration_hours': 12
            },
            'risk_assessment': {
                'monte_carlo_runs': 5000,
                'confidence_level': 0.99
            }
        }
        
        service = AnalyticsService(custom_config)
        
        # Should initialize without errors
        self.assertIsNotNone(service.financial_modeling)
        self.assertIsNotNone(service.industry_benchmarking)
        self.assertIsNotNone(service.risk_assessment)
        
        # Check that configuration was passed through
        self.assertEqual(service.financial_modeling.default_discount_rate, 0.12)
        self.assertEqual(service.risk_assessment.monte_carlo_runs, 5000)


if __name__ == '__main__':
    unittest.main()