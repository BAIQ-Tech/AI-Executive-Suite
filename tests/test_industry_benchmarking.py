"""
Tests for Industry Benchmarking Service

Tests industry data integration, peer comparison analysis,
competitive analysis features, and market trend analysis.
"""

import unittest
from decimal import Decimal
from datetime import datetime, timedelta
import sys
import os

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.industry_benchmarking import (
    IndustryBenchmarkingService, IndustryType, CompanySize, CompanyProfile,
    IndustryMetric, BenchmarkComparison, CompetitiveAnalysis, MarketTrend, IndustryReport
)


class TestIndustryBenchmarkingService(unittest.TestCase):
    """Test cases for Industry Benchmarking Service"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.service = IndustryBenchmarkingService()
        
        # Sample company profile for testing
        self.sample_company = CompanyProfile(
            company_id="test_company_1",
            name="Test Tech Company",
            industry=IndustryType.TECHNOLOGY,
            size=CompanySize.MEDIUM,
            revenue=Decimal('50000000'),  # $50M
            employees=200,
            founded_year=2015,
            location="San Francisco, CA",
            public_company=False
        )
        
        # Sample company metrics
        self.sample_metrics = {
            'revenue_growth_rate': Decimal('18.5'),
            'profit_margin': Decimal('25.2'),
            'employee_productivity': Decimal('250000')
        }
    
    def test_get_industry_benchmarks_basic(self):
        """Test basic industry benchmark retrieval"""
        benchmarks = self.service.get_industry_benchmarks(IndustryType.TECHNOLOGY)
        
        self.assertIsInstance(benchmarks, dict)
        self.assertGreater(len(benchmarks), 0)
        
        # Check that we get expected metrics
        expected_metrics = ['revenue_growth_rate', 'profit_margin', 'employee_productivity']
        for metric in expected_metrics:
            self.assertIn(metric, benchmarks)
            self.assertIsInstance(benchmarks[metric], IndustryMetric)
    
    def test_get_industry_benchmarks_specific_metrics(self):
        """Test retrieving specific metrics only"""
        requested_metrics = ['revenue_growth_rate', 'profit_margin']
        benchmarks = self.service.get_industry_benchmarks(
            IndustryType.TECHNOLOGY, 
            metrics=requested_metrics
        )
        
        self.assertEqual(len(benchmarks), 2)
        for metric in requested_metrics:
            self.assertIn(metric, benchmarks)
        
        # Should not include other metrics
        self.assertNotIn('employee_productivity', benchmarks)
    
    def test_get_industry_benchmarks_different_industries(self):
        """Test benchmark retrieval for different industries"""
        tech_benchmarks = self.service.get_industry_benchmarks(IndustryType.TECHNOLOGY)
        finance_benchmarks = self.service.get_industry_benchmarks(IndustryType.FINANCE)
        healthcare_benchmarks = self.service.get_industry_benchmarks(IndustryType.HEALTHCARE)
        
        # All should return data
        self.assertGreater(len(tech_benchmarks), 0)
        self.assertGreater(len(finance_benchmarks), 0)
        self.assertGreater(len(healthcare_benchmarks), 0)
        
        # Values should be different between industries
        if 'revenue_growth_rate' in tech_benchmarks and 'revenue_growth_rate' in finance_benchmarks:
            tech_growth = tech_benchmarks['revenue_growth_rate'].value
            finance_growth = finance_benchmarks['revenue_growth_rate'].value
            self.assertNotEqual(tech_growth, finance_growth)
    
    def test_get_industry_benchmarks_caching(self):
        """Test that benchmark data is cached properly"""
        # First call
        benchmarks1 = self.service.get_industry_benchmarks(IndustryType.TECHNOLOGY)
        
        # Second call should use cache
        benchmarks2 = self.service.get_industry_benchmarks(IndustryType.TECHNOLOGY)
        
        # Should be identical
        self.assertEqual(len(benchmarks1), len(benchmarks2))
        for metric_name in benchmarks1:
            self.assertEqual(
                benchmarks1[metric_name].value, 
                benchmarks2[metric_name].value
            )
    
    def test_get_industry_benchmarks_force_refresh(self):
        """Test force refresh of cached data"""
        # Get initial data
        benchmarks1 = self.service.get_industry_benchmarks(IndustryType.TECHNOLOGY)
        
        # Force refresh
        benchmarks2 = self.service.get_industry_benchmarks(
            IndustryType.TECHNOLOGY, 
            force_refresh=True
        )
        
        # Should still get data (even if same in mock implementation)
        self.assertGreater(len(benchmarks2), 0)
    
    def test_compare_to_industry_basic(self):
        """Test basic industry comparison"""
        comparisons = self.service.compare_to_industry(
            self.sample_metrics, 
            IndustryType.TECHNOLOGY
        )
        
        self.assertIsInstance(comparisons, dict)
        self.assertGreater(len(comparisons), 0)
        
        # Check comparison structure
        for metric_name, comparison in comparisons.items():
            self.assertIsInstance(comparison, BenchmarkComparison)
            self.assertIsInstance(comparison.company_value, Decimal)
            self.assertIsInstance(comparison.industry_median, Decimal)
            self.assertIsInstance(comparison.industry_average, Decimal)
            self.assertIsInstance(comparison.percentile_rank, float)
            self.assertIn(comparison.performance_rating, 
                         ["Excellent", "Above Average", "Average", "Below Average", "Poor"])
            self.assertIsInstance(comparison.peer_companies, list)
            self.assertIsInstance(comparison.improvement_potential, Decimal)
    
    def test_compare_to_industry_performance_ratings(self):
        """Test performance rating calculations"""
        # Test with high-performing metrics
        high_metrics = {
            'revenue_growth_rate': Decimal('30.0'),  # Very high
            'profit_margin': Decimal('35.0')         # Very high
        }
        
        comparisons = self.service.compare_to_industry(
            high_metrics, 
            IndustryType.TECHNOLOGY
        )
        
        # Should get good ratings for high values
        for comparison in comparisons.values():
            self.assertIn(comparison.performance_rating, 
                         ["Excellent", "Above Average"])
            self.assertGreater(comparison.percentile_rank, 50.0)
    
    def test_compare_to_industry_with_company_size(self):
        """Test industry comparison with company size consideration"""
        comparisons = self.service.compare_to_industry(
            self.sample_metrics, 
            IndustryType.TECHNOLOGY,
            CompanySize.MEDIUM
        )
        
        # Should still get valid comparisons
        self.assertGreater(len(comparisons), 0)
        
        # Peer companies should be limited for medium-sized companies
        for comparison in comparisons.values():
            self.assertLessEqual(len(comparison.peer_companies), 8)
    
    def test_compare_to_industry_missing_benchmarks(self):
        """Test comparison when some benchmarks are missing"""
        metrics_with_unknown = {
            'revenue_growth_rate': Decimal('15.0'),
            'unknown_metric': Decimal('100.0')
        }
        
        comparisons = self.service.compare_to_industry(
            metrics_with_unknown, 
            IndustryType.TECHNOLOGY
        )
        
        # Should only include metrics with available benchmarks
        self.assertIn('revenue_growth_rate', comparisons)
        self.assertNotIn('unknown_metric', comparisons)
    
    def test_perform_competitive_analysis_basic(self):
        """Test basic competitive analysis"""
        analysis = self.service.perform_competitive_analysis(self.sample_company)
        
        self.assertIsInstance(analysis, CompetitiveAnalysis)
        self.assertEqual(analysis.company_profile, self.sample_company)
        self.assertIsInstance(analysis.direct_competitors, list)
        self.assertGreater(len(analysis.direct_competitors), 0)
        self.assertIsInstance(analysis.market_position, str)
        self.assertIsInstance(analysis.competitive_advantages, list)
        self.assertIsInstance(analysis.competitive_disadvantages, list)
        self.assertIsInstance(analysis.growth_comparison, dict)
        
        # Market share should be reasonable
        if analysis.market_share_estimate is not None:
            self.assertGreater(analysis.market_share_estimate, 0)
            self.assertLessEqual(analysis.market_share_estimate, 50.0)
    
    def test_perform_competitive_analysis_different_sizes(self):
        """Test competitive analysis for different company sizes"""
        # Test startup
        startup_company = CompanyProfile(
            company_id="startup_1",
            name="Tech Startup",
            industry=IndustryType.TECHNOLOGY,
            size=CompanySize.STARTUP,
            revenue=Decimal('1000000'),
            employees=10,
            founded_year=2022,
            location="Austin, TX"
        )
        
        startup_analysis = self.service.perform_competitive_analysis(startup_company)
        
        # Should have startup-specific advantages/disadvantages
        advantages = startup_analysis.competitive_advantages
        disadvantages = startup_analysis.competitive_disadvantages
        
        self.assertTrue(any("agility" in adv.lower() or "flexibility" in adv.lower() 
                           for adv in advantages))
        self.assertTrue(any("resources" in dis.lower() or "capital" in dis.lower() 
                           for dis in disadvantages))
    
    def test_perform_competitive_analysis_without_financial_comparison(self):
        """Test competitive analysis without financial comparison"""
        analysis = self.service.perform_competitive_analysis(
            self.sample_company, 
            include_financial_comparison=False
        )
        
        # Growth comparison should be empty
        self.assertEqual(len(analysis.growth_comparison), 0)
    
    def test_get_market_trends_basic(self):
        """Test basic market trends retrieval"""
        trends = self.service.get_market_trends(IndustryType.TECHNOLOGY)
        
        self.assertIsInstance(trends, list)
        self.assertGreater(len(trends), 0)
        
        for trend in trends:
            self.assertIsInstance(trend, MarketTrend)
            self.assertEqual(trend.industry, IndustryType.TECHNOLOGY)
            self.assertIn(trend.trend_direction, ["increasing", "decreasing", "stable"])
            self.assertIsInstance(trend.growth_rate, float)
            self.assertIsInstance(trend.confidence_level, float)
            self.assertIsInstance(trend.key_drivers, list)
            self.assertIsInstance(trend.impact_assessment, str)
    
    def test_get_market_trends_different_industries(self):
        """Test market trends for different industries"""
        tech_trends = self.service.get_market_trends(IndustryType.TECHNOLOGY)
        finance_trends = self.service.get_market_trends(IndustryType.FINANCE)
        
        self.assertGreater(len(tech_trends), 0)
        self.assertGreater(len(finance_trends), 0)
        
        # Trends should be industry-specific
        for trend in tech_trends:
            self.assertEqual(trend.industry, IndustryType.TECHNOLOGY)
        
        for trend in finance_trends:
            self.assertEqual(trend.industry, IndustryType.FINANCE)
    
    def test_get_market_trends_time_horizons(self):
        """Test market trends filtering by time horizon"""
        short_term_trends = self.service.get_market_trends(
            IndustryType.TECHNOLOGY, 
            time_horizon="short_term"
        )
        
        long_term_trends = self.service.get_market_trends(
            IndustryType.TECHNOLOGY, 
            time_horizon="long_term"
        )
        
        # Should get trends (filtering logic may vary based on mock data)
        self.assertIsInstance(short_term_trends, list)
        self.assertIsInstance(long_term_trends, list)
    
    def test_generate_industry_report_basic(self):
        """Test basic industry report generation"""
        report = self.service.generate_industry_report(IndustryType.TECHNOLOGY)
        
        self.assertIsInstance(report, IndustryReport)
        self.assertEqual(report.industry, IndustryType.TECHNOLOGY)
        self.assertIsInstance(report.report_date, datetime)
        self.assertIsInstance(report.key_metrics, dict)
        self.assertIsInstance(report.market_trends, list)
        self.assertIsInstance(report.top_performers, list)
        self.assertIsInstance(report.industry_challenges, list)
        self.assertIsInstance(report.growth_opportunities, list)
        self.assertIsInstance(report.regulatory_environment, str)
        
        # Should have meaningful content
        self.assertGreater(len(report.key_metrics), 0)
        self.assertGreater(len(report.industry_challenges), 0)
        self.assertGreater(len(report.growth_opportunities), 0)
    
    def test_generate_industry_report_without_trends(self):
        """Test industry report generation without trends"""
        report = self.service.generate_industry_report(
            IndustryType.TECHNOLOGY, 
            include_trends=False
        )
        
        # Should have empty trends list
        self.assertEqual(len(report.market_trends), 0)
        
        # But should still have other content
        self.assertGreater(len(report.key_metrics), 0)
    
    def test_generate_industry_report_without_competitors(self):
        """Test industry report generation without competitors"""
        report = self.service.generate_industry_report(
            IndustryType.TECHNOLOGY, 
            include_competitors=False
        )
        
        # Should have empty top performers list
        self.assertEqual(len(report.top_performers), 0)
        
        # But should still have other content
        self.assertGreater(len(report.key_metrics), 0)
    
    def test_generate_industry_report_different_industries(self):
        """Test industry report generation for different industries"""
        tech_report = self.service.generate_industry_report(IndustryType.TECHNOLOGY)
        finance_report = self.service.generate_industry_report(IndustryType.FINANCE)
        healthcare_report = self.service.generate_industry_report(IndustryType.HEALTHCARE)
        
        # All should be valid reports
        self.assertEqual(tech_report.industry, IndustryType.TECHNOLOGY)
        self.assertEqual(finance_report.industry, IndustryType.FINANCE)
        self.assertEqual(healthcare_report.industry, IndustryType.HEALTHCARE)
        
        # Should have different challenges and opportunities
        self.assertNotEqual(
            tech_report.industry_challenges, 
            finance_report.industry_challenges
        )
        self.assertNotEqual(
            tech_report.growth_opportunities, 
            healthcare_report.growth_opportunities
        )
    
    def test_percentile_rank_calculation(self):
        """Test percentile rank calculation logic"""
        # Create a mock benchmark
        benchmark = IndustryMetric(
            metric_name="Test Metric",
            value=Decimal('100'),
            unit="percentage",
            percentile_25=Decimal('75'),
            percentile_50=Decimal('100'),
            percentile_75=Decimal('125'),
            sample_size=1000,
            data_source="Test",
            last_updated=datetime.utcnow()
        )
        
        # Test different values
        test_cases = [
            (Decimal('50'), 0, 25),    # Below 25th percentile
            (Decimal('75'), 25, 25),   # At 25th percentile
            (Decimal('87.5'), 25, 50), # Between 25th and 50th
            (Decimal('100'), 50, 50),  # At median
            (Decimal('112.5'), 50, 75), # Between 50th and 75th
            (Decimal('125'), 75, 75),  # At 75th percentile
            (Decimal('150'), 75, 95),  # Above 75th percentile
        ]
        
        for value, min_expected, max_expected in test_cases:
            percentile = self.service._calculate_percentile_rank(value, benchmark)
            self.assertGreaterEqual(percentile, min_expected)
            self.assertLessEqual(percentile, max_expected)
    
    def test_performance_rating_logic(self):
        """Test performance rating assignment"""
        test_cases = [
            (85, "Excellent"),
            (70, "Above Average"),
            (50, "Average"),
            (30, "Below Average"),
            (10, "Poor")
        ]
        
        for percentile, expected_rating in test_cases:
            rating = self.service._get_performance_rating(percentile)
            self.assertEqual(rating, expected_rating)
    
    def test_cache_validity_check(self):
        """Test cache validity checking"""
        # Test with non-existent cache key
        self.assertFalse(self.service._is_cache_valid("non_existent_key"))
        
        # Test with fresh cache entry
        cache_key = "test_cache"
        self.service._cache_timestamps[cache_key] = datetime.utcnow()
        self.assertTrue(self.service._is_cache_valid(cache_key))
        
        # Test with expired cache entry
        self.service._cache_timestamps[cache_key] = datetime.utcnow() - timedelta(hours=25)
        self.assertFalse(self.service._is_cache_valid(cache_key))
    
    def test_service_configuration(self):
        """Test service configuration options"""
        custom_config = {
            'cache_duration_hours': 12,
            'api_timeout_seconds': 60,
            'data_sources': {'primary': 'custom_api'}
        }
        
        service = IndustryBenchmarkingService(custom_config)
        
        self.assertEqual(service.cache_duration, 12)
        self.assertEqual(service.api_timeout, 60)
        self.assertEqual(service.data_sources['primary'], 'custom_api')
    
    def test_industry_type_enum(self):
        """Test IndustryType enum values"""
        # Test that all expected industries are available
        expected_industries = [
            "technology", "healthcare", "finance", "manufacturing", 
            "retail", "energy", "real_estate", "telecommunications"
        ]
        
        for industry_name in expected_industries:
            # Should be able to create IndustryType from string
            industry = IndustryType(industry_name)
            self.assertEqual(industry.value, industry_name)
    
    def test_company_size_enum(self):
        """Test CompanySize enum values"""
        expected_sizes = ["startup", "small", "medium", "large", "enterprise"]
        
        for size_name in expected_sizes:
            size = CompanySize(size_name)
            self.assertEqual(size.value, size_name)
    
    def test_company_profile_data_structure(self):
        """Test CompanyProfile data structure"""
        profile = CompanyProfile(
            company_id="test_123",
            name="Test Company",
            industry=IndustryType.TECHNOLOGY,
            size=CompanySize.MEDIUM,
            revenue=Decimal('10000000'),
            employees=100,
            founded_year=2020,
            location="New York, NY",
            public_company=True
        )
        
        self.assertEqual(profile.company_id, "test_123")
        self.assertEqual(profile.name, "Test Company")
        self.assertEqual(profile.industry, IndustryType.TECHNOLOGY)
        self.assertEqual(profile.size, CompanySize.MEDIUM)
        self.assertEqual(profile.revenue, Decimal('10000000'))
        self.assertEqual(profile.employees, 100)
        self.assertEqual(profile.founded_year, 2020)
        self.assertEqual(profile.location, "New York, NY")
        self.assertTrue(profile.public_company)


if __name__ == '__main__':
    unittest.main()