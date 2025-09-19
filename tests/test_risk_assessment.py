"""
Tests for Risk Assessment Service

Tests financial risk scoring algorithms, Monte Carlo simulation for risk analysis,
risk mitigation recommendation system, and regulatory compliance risk assessment.
"""

import unittest
from decimal import Decimal
from datetime import datetime, timedelta
import sys
import os

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.risk_assessment import (
    RiskAssessmentEngine, RiskType, RiskLevel, RiskImpact, RiskFactor,
    RiskScore, MonteCarloResult, RiskMitigationPlan, ComplianceRisk, RiskReport
)


class TestRiskAssessmentEngine(unittest.TestCase):
    """Test cases for Risk Assessment Engine"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.engine = RiskAssessmentEngine()
        
        # Sample risk factor for testing
        self.sample_risk_factor = RiskFactor(
            factor_id='test_risk',
            name='Test Risk Factor',
            risk_type=RiskType.FINANCIAL,
            probability=0.3,
            impact_score=7.0,
            financial_impact=Decimal('500000'),
            description='Test risk factor for unit testing',
            mitigation_strategies=[
                'Strategy 1: Implement controls',
                'Strategy 2: Monitor indicators',
                'Strategy 3: Diversify exposure'
            ],
            last_assessed=datetime.utcnow()
        )
        
        # Sample company profile
        self.sample_company_profile = {
            'company_id': 'test_company',
            'name': 'Test Company Inc.',
            'industry': 'technology',
            'size': 'medium',
            'public_company': True,
            'processes_personal_data': True,
            'processes_payments': False,
            'revenue': 50000000,
            'employees': 200
        }
    
    def test_calculate_risk_score_basic(self):
        """Test basic risk score calculation"""
        risk_factors = [self.sample_risk_factor]
        
        result = self.engine.calculate_risk_score(risk_factors)
        
        self.assertIsInstance(result, RiskScore)
        self.assertIsInstance(result.overall_score, float)
        self.assertGreaterEqual(result.overall_score, 0.0)
        self.assertLessEqual(result.overall_score, 100.0)
        self.assertIsInstance(result.risk_level, RiskLevel)
        self.assertEqual(len(result.risk_factors), 1)
        self.assertIn('Test Risk Factor', result.score_breakdown)
        self.assertIsInstance(result.confidence_interval, tuple)
        self.assertIsInstance(result.assessment_date, datetime)
        self.assertIsInstance(result.recommendations, list)
    
    def test_calculate_risk_score_default_factors(self):
        """Test risk score calculation with default risk factors"""
        result = self.engine.calculate_risk_score()
        
        self.assertIsInstance(result, RiskScore)
        self.assertGreater(len(result.risk_factors), 0)
        self.assertGreater(len(result.score_breakdown), 0)
        self.assertGreater(len(result.recommendations), 0)
    
    def test_calculate_risk_score_multiple_factors(self):
        """Test risk score calculation with multiple risk factors"""
        risk_factors = [
            self.sample_risk_factor,
            RiskFactor(
                factor_id='test_risk_2',
                name='Test Risk Factor 2',
                risk_type=RiskType.OPERATIONAL,
                probability=0.5,
                impact_score=6.0,
                financial_impact=Decimal('300000'),
                description='Second test risk factor',
                mitigation_strategies=['Strategy A', 'Strategy B'],
                last_assessed=datetime.utcnow()
            )
        ]
        
        result = self.engine.calculate_risk_score(risk_factors)
        
        self.assertEqual(len(result.risk_factors), 2)
        self.assertEqual(len(result.score_breakdown), 2)
        self.assertIn('Test Risk Factor', result.score_breakdown)
        self.assertIn('Test Risk Factor 2', result.score_breakdown)
    
    def test_risk_level_determination(self):
        """Test risk level determination logic"""
        test_cases = [
            (85, RiskLevel.CRITICAL),
            (70, RiskLevel.VERY_HIGH),
            (55, RiskLevel.HIGH),
            (40, RiskLevel.MEDIUM),
            (25, RiskLevel.LOW),
            (10, RiskLevel.VERY_LOW)
        ]
        
        for score, expected_level in test_cases:
            level = self.engine._determine_risk_level(score)
            self.assertEqual(level, expected_level)
    
    def test_risk_recommendations_generation(self):
        """Test risk recommendations generation"""
        # High risk scenario
        high_risk_factors = [
            RiskFactor(
                factor_id='high_risk',
                name='High Risk Factor',
                risk_type=RiskType.FINANCIAL,
                probability=0.8,
                impact_score=9.0,
                financial_impact=Decimal('1000000'),
                description='High risk factor',
                mitigation_strategies=['Urgent action required'],
                last_assessed=datetime.utcnow()
            )
        ]
        
        recommendations = self.engine._generate_risk_recommendations(high_risk_factors, 75.0)
        
        self.assertIsInstance(recommendations, list)
        self.assertGreater(len(recommendations), 0)
        
        # Should include urgent recommendations for high risk
        recommendation_text = ' '.join(recommendations).lower()
        self.assertTrue(any(word in recommendation_text 
                           for word in ['immediate', 'urgent', 'emergency']))
    
    def test_monte_carlo_simulation_basic(self):
        """Test basic Monte Carlo simulation"""
        base_scenario = {'base_outcome': 1000000}
        risk_parameters = {
            'market_risk': {
                'distribution': 'normal',
                'mean': 0,
                'std_dev': 100000,
                'impact_factor': 1.0
            }
        }
        
        result = self.engine.run_monte_carlo_simulation(
            base_scenario, risk_parameters, num_simulations=1000
        )
        
        self.assertIsInstance(result, MonteCarloResult)
        self.assertEqual(result.simulation_runs, 1000)
        self.assertIsInstance(result.mean_outcome, Decimal)
        self.assertIsInstance(result.median_outcome, Decimal)
        self.assertIsInstance(result.std_deviation, Decimal)
        self.assertIsInstance(result.percentile_5, Decimal)
        self.assertIsInstance(result.percentile_95, Decimal)
        self.assertIsInstance(result.var_95, Decimal)
        self.assertIsInstance(result.cvar_95, Decimal)
        self.assertIsInstance(result.probability_of_loss, float)
        self.assertIsInstance(result.worst_case_scenario, Decimal)
        self.assertIsInstance(result.best_case_scenario, Decimal)
        self.assertEqual(len(result.simulation_data), 1000)
        
        # Statistical properties
        self.assertGreaterEqual(result.probability_of_loss, 0.0)
        self.assertLessEqual(result.probability_of_loss, 1.0)
        self.assertLessEqual(result.percentile_5, result.median_outcome)
        self.assertLessEqual(result.median_outcome, result.percentile_95)
        self.assertLessEqual(result.worst_case_scenario, result.best_case_scenario)
    
    def test_monte_carlo_simulation_different_distributions(self):
        """Test Monte Carlo simulation with different distributions"""
        base_scenario = {'base_outcome': 500000}
        
        # Test uniform distribution
        risk_parameters_uniform = {
            'uniform_risk': {
                'distribution': 'uniform',
                'low': -100000,
                'high': 100000,
                'impact_factor': 1.0
            }
        }
        
        result_uniform = self.engine.run_monte_carlo_simulation(
            base_scenario, risk_parameters_uniform, num_simulations=500
        )
        
        self.assertEqual(result_uniform.simulation_runs, 500)
        
        # Test triangular distribution
        risk_parameters_triangular = {
            'triangular_risk': {
                'distribution': 'triangular',
                'low': -200000,
                'high': 50000,
                'mode': -25000,
                'impact_factor': 1.0
            }
        }
        
        result_triangular = self.engine.run_monte_carlo_simulation(
            base_scenario, risk_parameters_triangular, num_simulations=500
        )
        
        self.assertEqual(result_triangular.simulation_runs, 500)
    
    def test_monte_carlo_simulation_default_runs(self):
        """Test Monte Carlo simulation with default number of runs"""
        base_scenario = {'base_outcome': 750000}
        risk_parameters = {
            'test_risk': {
                'distribution': 'normal',
                'mean': 0,
                'std_dev': 50000,
                'impact_factor': 1.0
            }
        }
        
        result = self.engine.run_monte_carlo_simulation(base_scenario, risk_parameters)
        
        # Should use default number of runs
        self.assertEqual(result.simulation_runs, self.engine.monte_carlo_runs)
    
    def test_create_mitigation_plan_basic(self):
        """Test basic mitigation plan creation"""
        plan = self.engine.create_mitigation_plan(self.sample_risk_factor)
        
        self.assertIsInstance(plan, RiskMitigationPlan)
        self.assertEqual(plan.risk_factor_id, self.sample_risk_factor.factor_id)
        self.assertIsInstance(plan.mitigation_strategies, list)
        self.assertGreater(len(plan.mitigation_strategies), 0)
        self.assertIsInstance(plan.implementation_timeline, dict)
        self.assertIsInstance(plan.estimated_cost, Decimal)
        self.assertIsInstance(plan.expected_risk_reduction, float)
        self.assertIsInstance(plan.success_probability, float)
        self.assertIsInstance(plan.monitoring_metrics, list)
        self.assertIsInstance(plan.responsible_parties, list)
        
        # Check strategy structure
        for strategy in plan.mitigation_strategies:
            self.assertIn('name', strategy)
            self.assertIn('description', strategy)
            self.assertIn('estimated_cost', strategy)
            self.assertIn('effectiveness', strategy)
            self.assertIn('implementation_time_months', strategy)
            self.assertIn('priority', strategy)
            self.assertIn('success_probability', strategy)
    
    def test_create_mitigation_plan_with_budget_constraint(self):
        """Test mitigation plan creation with budget constraint"""
        budget_constraint = Decimal('100000')
        
        plan = self.engine.create_mitigation_plan(
            self.sample_risk_factor, 
            budget_constraint=budget_constraint
        )
        
        # Total cost should not exceed budget
        self.assertLessEqual(plan.estimated_cost, budget_constraint)
        
        # Should still have at least one strategy if budget allows
        if budget_constraint > Decimal('50000'):  # Minimum strategy cost
            self.assertGreater(len(plan.mitigation_strategies), 0)
    
    def test_create_mitigation_plan_with_timeline_constraint(self):
        """Test mitigation plan creation with timeline constraint"""
        timeline_constraint = 6  # 6 months
        
        plan = self.engine.create_mitigation_plan(
            self.sample_risk_factor, 
            timeline_constraint=timeline_constraint
        )
        
        # All strategies should fit within timeline
        for strategy in plan.mitigation_strategies:
            self.assertLessEqual(strategy['implementation_time_months'], timeline_constraint)
    
    def test_assess_compliance_risk_basic(self):
        """Test basic compliance risk assessment"""
        compliance_risks = self.engine.assess_compliance_risk(self.sample_company_profile)
        
        self.assertIsInstance(compliance_risks, list)
        self.assertGreater(len(compliance_risks), 0)
        
        for risk in compliance_risks:
            self.assertIsInstance(risk, ComplianceRisk)
            self.assertIsInstance(risk.regulation_name, str)
            self.assertIsInstance(risk.jurisdiction, str)
            self.assertIsInstance(risk.compliance_level, float)
            self.assertGreaterEqual(risk.compliance_level, 0.0)
            self.assertLessEqual(risk.compliance_level, 1.0)
            self.assertIsInstance(risk.risk_score, float)
            self.assertIsInstance(risk.potential_penalties, Decimal)
            self.assertIsInstance(risk.compliance_gaps, list)
            self.assertIsInstance(risk.remediation_actions, list)
            self.assertIn(risk.priority, ['Critical', 'High', 'Medium', 'Low'])
    
    def test_assess_compliance_risk_specific_regulations(self):
        """Test compliance risk assessment for specific regulations"""
        specific_regulations = ['SOX', 'GDPR']
        
        compliance_risks = self.engine.assess_compliance_risk(
            self.sample_company_profile, 
            applicable_regulations=specific_regulations
        )
        
        # Should only assess specified regulations
        regulation_names = [risk.regulation_name for risk in compliance_risks]
        self.assertTrue(any('Sarbanes-Oxley' in name for name in regulation_names))
        self.assertTrue(any('General Data Protection' in name for name in regulation_names))
    
    def test_assess_compliance_risk_different_company_types(self):
        """Test compliance risk assessment for different company types"""
        # Private company profile
        private_company = self.sample_company_profile.copy()
        private_company['public_company'] = False
        
        private_risks = self.engine.assess_compliance_risk(private_company)
        
        # Public company should have different (likely more) compliance risks
        public_risks = self.engine.assess_compliance_risk(self.sample_company_profile)
        
        # Both should return valid assessments
        self.assertIsInstance(private_risks, list)
        self.assertIsInstance(public_risks, list)
    
    def test_determine_applicable_regulations(self):
        """Test determination of applicable regulations"""
        # Test public company
        public_company = {'public_company': True, 'processes_personal_data': True}
        applicable = self.engine._determine_applicable_regulations(public_company)
        
        self.assertIn('SOX', applicable)
        self.assertIn('GDPR', applicable)
        
        # Test private company with payments
        payment_company = {'public_company': False, 'processes_payments': True}
        applicable = self.engine._determine_applicable_regulations(payment_company)
        
        self.assertIn('PCI_DSS', applicable)
    
    def test_compliance_level_assessment(self):
        """Test compliance level assessment logic"""
        # Test different company sizes
        large_company = {'size': 'large', 'industry': 'finance'}
        small_company = {'size': 'small', 'industry': 'technology'}
        
        large_compliance = self.engine._assess_compliance_level(large_company, 'SOX')
        small_compliance = self.engine._assess_compliance_level(small_company, 'SOX')
        
        # Large companies should generally have higher compliance
        self.assertGreaterEqual(large_compliance, 0.0)
        self.assertLessEqual(large_compliance, 1.0)
        self.assertGreaterEqual(small_compliance, 0.0)
        self.assertLessEqual(small_compliance, 1.0)
    
    def test_compliance_gaps_identification(self):
        """Test compliance gaps identification"""
        # Test low compliance scenario
        gaps = self.engine._identify_compliance_gaps(
            self.sample_company_profile, 'SOX', 0.4
        )
        
        self.assertIsInstance(gaps, list)
        self.assertGreater(len(gaps), 0)
        
        # Should have more gaps for lower compliance
        gaps_high = self.engine._identify_compliance_gaps(
            self.sample_company_profile, 'SOX', 0.9
        )
        
        self.assertGreaterEqual(len(gaps), len(gaps_high))
    
    def test_remediation_actions_generation(self):
        """Test remediation actions generation"""
        gaps = [
            "Incomplete documentation requirements",
            "Insufficient staff training",
            "Missing monitoring procedures"
        ]
        
        actions = self.engine._generate_remediation_actions('SOX', gaps)
        
        self.assertIsInstance(actions, list)
        self.assertGreater(len(actions), 0)
        
        # Should include relevant actions
        actions_text = ' '.join(actions).lower()
        self.assertTrue(any(word in actions_text 
                           for word in ['documentation', 'training', 'monitoring']))
    
    def test_generate_comprehensive_risk_report(self):
        """Test comprehensive risk report generation"""
        company_id = 'test_company_123'
        
        report = self.engine.generate_comprehensive_risk_report(
            company_id, self.sample_company_profile
        )
        
        self.assertIsInstance(report, RiskReport)
        self.assertEqual(report.company_id, company_id)
        self.assertIsInstance(report.assessment_date, datetime)
        self.assertIsInstance(report.overall_risk_score, RiskScore)
        self.assertIsInstance(report.risk_by_category, dict)
        self.assertIsInstance(report.monte_carlo_analysis, MonteCarloResult)
        self.assertIsInstance(report.compliance_risks, list)
        self.assertIsInstance(report.mitigation_plans, list)
        self.assertIsInstance(report.key_recommendations, list)
        self.assertIsInstance(report.next_review_date, datetime)
        
        # Check that risk categories are present
        self.assertGreater(len(report.risk_by_category), 0)
        
        # Check that mitigation plans are created for top risks
        self.assertGreater(len(report.mitigation_plans), 0)
        self.assertLessEqual(len(report.mitigation_plans), 3)  # Top 3 risks
        
        # Check that recommendations are provided
        self.assertGreater(len(report.key_recommendations), 0)
        
        # Next review should be in the future
        self.assertGreater(report.next_review_date, datetime.utcnow())
    
    def test_generate_comprehensive_risk_report_without_profile(self):
        """Test comprehensive risk report generation without company profile"""
        company_id = 'test_company_456'
        
        report = self.engine.generate_comprehensive_risk_report(company_id)
        
        # Should still generate a valid report
        self.assertIsInstance(report, RiskReport)
        self.assertEqual(report.company_id, company_id)
        
        # Compliance risks might be empty without profile
        self.assertIsInstance(report.compliance_risks, list)
    
    def test_scenario_simulation(self):
        """Test individual scenario simulation"""
        base_scenario = {'base_outcome': 100000}
        risk_parameters = {
            'test_risk': {
                'distribution': 'normal',
                'mean': 0,
                'std_dev': 10000,
                'impact_factor': 1.0
            }
        }
        
        outcome = self.engine._simulate_scenario(base_scenario, risk_parameters)
        
        self.assertIsInstance(outcome, Decimal)
        # Outcome should be reasonably close to base (within several standard deviations)
        self.assertGreater(outcome, Decimal('50000'))
        self.assertLess(outcome, Decimal('150000'))
    
    def test_engine_configuration(self):
        """Test engine configuration options"""
        custom_config = {
            'monte_carlo_runs': 5000,
            'confidence_level': 0.99,
            'risk_tolerance': 0.03
        }
        
        engine = RiskAssessmentEngine(custom_config)
        
        self.assertEqual(engine.monte_carlo_runs, 5000)
        self.assertEqual(engine.confidence_level, 0.99)
        self.assertEqual(engine.risk_tolerance, 0.03)
    
    def test_risk_factor_data_structure(self):
        """Test RiskFactor data structure"""
        factor = RiskFactor(
            factor_id='test_factor',
            name='Test Factor',
            risk_type=RiskType.STRATEGIC,
            probability=0.4,
            impact_score=6.5,
            financial_impact=Decimal('750000'),
            description='Test risk factor',
            mitigation_strategies=['Strategy 1', 'Strategy 2'],
            last_assessed=datetime.utcnow()
        )
        
        self.assertEqual(factor.factor_id, 'test_factor')
        self.assertEqual(factor.name, 'Test Factor')
        self.assertEqual(factor.risk_type, RiskType.STRATEGIC)
        self.assertEqual(factor.probability, 0.4)
        self.assertEqual(factor.impact_score, 6.5)
        self.assertEqual(factor.financial_impact, Decimal('750000'))
        self.assertEqual(len(factor.mitigation_strategies), 2)
    
    def test_risk_type_enum(self):
        """Test RiskType enum values"""
        expected_types = [
            "financial", "operational", "strategic", "compliance", 
            "market", "credit", "liquidity", "technology", "reputation", "regulatory"
        ]
        
        for risk_type_name in expected_types:
            risk_type = RiskType(risk_type_name)
            self.assertEqual(risk_type.value, risk_type_name)
    
    def test_risk_level_enum(self):
        """Test RiskLevel enum values"""
        expected_levels = ["very_low", "low", "medium", "high", "very_high", "critical"]
        
        for level_name in expected_levels:
            level = RiskLevel(level_name)
            self.assertEqual(level.value, level_name)
    
    def test_risk_impact_enum(self):
        """Test RiskImpact enum values"""
        expected_impacts = [
            "negligible", "minor", "moderate", "major", "severe", "catastrophic"
        ]
        
        for impact_name in expected_impacts:
            impact = RiskImpact(impact_name)
            self.assertEqual(impact.value, impact_name)


if __name__ == '__main__':
    unittest.main()