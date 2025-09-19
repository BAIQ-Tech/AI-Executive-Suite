"""
Industry Benchmarking Service

Provides industry data integration, peer comparison analysis,
competitive analysis features, and market trend analysis.
"""

import logging
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
import statistics
import json
import requests
from enum import Enum

logger = logging.getLogger(__name__)


class IndustryType(Enum):
    """Industry classification types"""
    TECHNOLOGY = "technology"
    HEALTHCARE = "healthcare"
    FINANCE = "finance"
    MANUFACTURING = "manufacturing"
    RETAIL = "retail"
    ENERGY = "energy"
    REAL_ESTATE = "real_estate"
    TELECOMMUNICATIONS = "telecommunications"
    AUTOMOTIVE = "automotive"
    AEROSPACE = "aerospace"
    CONSUMER_GOODS = "consumer_goods"
    MEDIA = "media"
    EDUCATION = "education"
    HOSPITALITY = "hospitality"
    AGRICULTURE = "agriculture"


class CompanySize(Enum):
    """Company size classifications"""
    STARTUP = "startup"
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
    ENTERPRISE = "enterprise"


@dataclass
class IndustryMetric:
    """Industry benchmark metric"""
    metric_name: str
    value: Decimal
    unit: str
    percentile_25: Decimal
    percentile_50: Decimal  # Median
    percentile_75: Decimal
    sample_size: int
    data_source: str
    last_updated: datetime


@dataclass
class CompanyProfile:
    """Company profile for benchmarking"""
    company_id: str
    name: str
    industry: IndustryType
    size: CompanySize
    revenue: Optional[Decimal]
    employees: Optional[int]
    founded_year: Optional[int]
    location: Optional[str]
    public_company: bool = False


@dataclass
class BenchmarkComparison:
    """Benchmark comparison result"""
    company_value: Decimal
    industry_median: Decimal
    industry_average: Decimal
    percentile_rank: float
    performance_rating: str  # "Excellent", "Above Average", "Average", "Below Average", "Poor"
    peer_companies: List[str]
    improvement_potential: Decimal


@dataclass
class CompetitiveAnalysis:
    """Competitive analysis result"""
    company_profile: CompanyProfile
    direct_competitors: List[CompanyProfile]
    market_position: str
    competitive_advantages: List[str]
    competitive_disadvantages: List[str]
    market_share_estimate: Optional[float]
    growth_comparison: Dict[str, float]


@dataclass
class MarketTrend:
    """Market trend data"""
    trend_name: str
    industry: IndustryType
    trend_direction: str  # "increasing", "decreasing", "stable"
    growth_rate: float
    confidence_level: float
    time_period: str
    key_drivers: List[str]
    impact_assessment: str


@dataclass
class IndustryReport:
    """Comprehensive industry report"""
    industry: IndustryType
    report_date: datetime
    key_metrics: Dict[str, IndustryMetric]
    market_trends: List[MarketTrend]
    top_performers: List[CompanyProfile]
    industry_challenges: List[str]
    growth_opportunities: List[str]
    regulatory_environment: str


class IndustryBenchmarkingService:
    """Service for industry benchmarking and competitive analysis"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Configuration
        self.data_sources = self.config.get('data_sources', {})
        self.cache_duration = self.config.get('cache_duration_hours', 24)
        self.api_timeout = self.config.get('api_timeout_seconds', 30)
        
        # In-memory cache for industry data
        self._industry_cache = {}
        self._cache_timestamps = {}
        
        # Mock data for demonstration (in production, this would come from real APIs)
        self._initialize_mock_data()
    
    def _initialize_mock_data(self):
        """Initialize mock industry data for demonstration"""
        self._mock_industry_data = {
            IndustryType.TECHNOLOGY: {
                'revenue_growth_rate': IndustryMetric(
                    metric_name="Revenue Growth Rate",
                    value=Decimal('15.2'),
                    unit="percentage",
                    percentile_25=Decimal('8.5'),
                    percentile_50=Decimal('12.3'),
                    percentile_75=Decimal('18.7'),
                    sample_size=1250,
                    data_source="TechMetrics Database",
                    last_updated=datetime.utcnow()
                ),
                'profit_margin': IndustryMetric(
                    metric_name="Net Profit Margin",
                    value=Decimal('22.8'),
                    unit="percentage",
                    percentile_25=Decimal('15.2'),
                    percentile_50=Decimal('20.1'),
                    percentile_75=Decimal('28.5'),
                    sample_size=1250,
                    data_source="TechMetrics Database",
                    last_updated=datetime.utcnow()
                ),
                'employee_productivity': IndustryMetric(
                    metric_name="Revenue per Employee",
                    value=Decimal('285000'),
                    unit="USD",
                    percentile_25=Decimal('180000'),
                    percentile_50=Decimal('245000'),
                    percentile_75=Decimal('350000'),
                    sample_size=1250,
                    data_source="TechMetrics Database",
                    last_updated=datetime.utcnow()
                )
            },
            IndustryType.FINANCE: {
                'revenue_growth_rate': IndustryMetric(
                    metric_name="Revenue Growth Rate",
                    value=Decimal('8.7'),
                    unit="percentage",
                    percentile_25=Decimal('4.2'),
                    percentile_50=Decimal('7.1'),
                    percentile_75=Decimal('11.8'),
                    sample_size=850,
                    data_source="Financial Industry Report",
                    last_updated=datetime.utcnow()
                ),
                'profit_margin': IndustryMetric(
                    metric_name="Net Profit Margin",
                    value=Decimal('18.5'),
                    unit="percentage",
                    percentile_25=Decimal('12.3'),
                    percentile_50=Decimal('16.8'),
                    percentile_75=Decimal('23.2'),
                    sample_size=850,
                    data_source="Financial Industry Report",
                    last_updated=datetime.utcnow()
                ),
                'roe': IndustryMetric(
                    metric_name="Return on Equity",
                    value=Decimal('14.2'),
                    unit="percentage",
                    percentile_25=Decimal('9.5'),
                    percentile_50=Decimal('12.8'),
                    percentile_75=Decimal('17.6'),
                    sample_size=850,
                    data_source="Financial Industry Report",
                    last_updated=datetime.utcnow()
                )
            },
            IndustryType.HEALTHCARE: {
                'revenue_growth_rate': IndustryMetric(
                    metric_name="Revenue Growth Rate",
                    value=Decimal('11.3'),
                    unit="percentage",
                    percentile_25=Decimal('6.8'),
                    percentile_50=Decimal('9.5'),
                    percentile_75=Decimal('14.2'),
                    sample_size=650,
                    data_source="Healthcare Analytics",
                    last_updated=datetime.utcnow()
                ),
                'profit_margin': IndustryMetric(
                    metric_name="Net Profit Margin",
                    value=Decimal('16.7'),
                    unit="percentage",
                    percentile_25=Decimal('10.2'),
                    percentile_50=Decimal('14.5'),
                    percentile_75=Decimal('21.3'),
                    sample_size=650,
                    data_source="Healthcare Analytics",
                    last_updated=datetime.utcnow()
                ),
                'rd_intensity': IndustryMetric(
                    metric_name="R&D Intensity",
                    value=Decimal('12.8'),
                    unit="percentage",
                    percentile_25=Decimal('7.5'),
                    percentile_50=Decimal('10.2'),
                    percentile_75=Decimal('16.8'),
                    sample_size=650,
                    data_source="Healthcare Analytics",
                    last_updated=datetime.utcnow()
                )
            }
        }
        
        # Mock market trends
        self._mock_trends = {
            IndustryType.TECHNOLOGY: [
                MarketTrend(
                    trend_name="AI/ML Adoption",
                    industry=IndustryType.TECHNOLOGY,
                    trend_direction="increasing",
                    growth_rate=0.35,
                    confidence_level=0.92,
                    time_period="2024-2025",
                    key_drivers=["Digital transformation", "Automation demand", "Cost reduction"],
                    impact_assessment="High positive impact on productivity and innovation"
                ),
                MarketTrend(
                    trend_name="Cloud Migration",
                    industry=IndustryType.TECHNOLOGY,
                    trend_direction="increasing",
                    growth_rate=0.28,
                    confidence_level=0.88,
                    time_period="2024-2026",
                    key_drivers=["Scalability needs", "Remote work", "Cost optimization"],
                    impact_assessment="Significant infrastructure and operational changes"
                )
            ],
            IndustryType.FINANCE: [
                MarketTrend(
                    trend_name="Digital Banking",
                    industry=IndustryType.FINANCE,
                    trend_direction="increasing",
                    growth_rate=0.22,
                    confidence_level=0.85,
                    time_period="2024-2025",
                    key_drivers=["Customer expectations", "Cost reduction", "Regulatory support"],
                    impact_assessment="Transformation of customer experience and operations"
                ),
                MarketTrend(
                    trend_name="ESG Investing",
                    industry=IndustryType.FINANCE,
                    trend_direction="increasing",
                    growth_rate=0.18,
                    confidence_level=0.78,
                    time_period="2024-2027",
                    key_drivers=["Regulatory requirements", "Investor demand", "Risk management"],
                    impact_assessment="New product development and compliance requirements"
                )
            ]
        }
    
    def get_industry_benchmarks(
        self, 
        industry: IndustryType, 
        metrics: List[str] = None,
        force_refresh: bool = False
    ) -> Dict[str, IndustryMetric]:
        """
        Get industry benchmark data for specified metrics
        
        Args:
            industry: Industry type
            metrics: List of specific metrics to retrieve (None for all)
            force_refresh: Force refresh of cached data
            
        Returns:
            Dictionary of industry metrics
        """
        try:
            cache_key = f"benchmarks_{industry.value}"
            
            # Check cache first
            if not force_refresh and self._is_cache_valid(cache_key):
                cached_data = self._industry_cache.get(cache_key, {})
                if metrics:
                    return {k: v for k, v in cached_data.items() if k in metrics}
                return cached_data
            
            # Fetch fresh data
            industry_data = self._fetch_industry_data(industry)
            
            # Cache the data
            self._industry_cache[cache_key] = industry_data
            self._cache_timestamps[cache_key] = datetime.utcnow()
            
            # Filter by requested metrics
            if metrics:
                industry_data = {k: v for k, v in industry_data.items() if k in metrics}
            
            self.logger.info(f"Retrieved {len(industry_data)} benchmarks for {industry.value}")
            return industry_data
            
        except Exception as e:
            self.logger.error(f"Error getting industry benchmarks: {str(e)}")
            return {}
    
    def _fetch_industry_data(self, industry: IndustryType) -> Dict[str, IndustryMetric]:
        """
        Fetch industry data from external sources
        In production, this would integrate with real industry databases
        """
        # For now, return mock data
        return self._mock_industry_data.get(industry, {})
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached data is still valid"""
        if cache_key not in self._cache_timestamps:
            return False
        
        cache_time = self._cache_timestamps[cache_key]
        expiry_time = cache_time + timedelta(hours=self.cache_duration)
        return datetime.utcnow() < expiry_time
    
    def compare_to_industry(
        self, 
        company_metrics: Dict[str, Decimal],
        industry: IndustryType,
        company_size: CompanySize = None
    ) -> Dict[str, BenchmarkComparison]:
        """
        Compare company metrics to industry benchmarks
        
        Args:
            company_metrics: Company's metric values
            industry: Industry to compare against
            company_size: Company size for more targeted comparison
            
        Returns:
            Dictionary of benchmark comparisons
        """
        try:
            # Get industry benchmarks
            industry_benchmarks = self.get_industry_benchmarks(industry)
            
            comparisons = {}
            
            for metric_name, company_value in company_metrics.items():
                if metric_name not in industry_benchmarks:
                    self.logger.warning(f"No industry benchmark available for {metric_name}")
                    continue
                
                benchmark = industry_benchmarks[metric_name]
                
                # Calculate percentile rank
                percentile_rank = self._calculate_percentile_rank(
                    company_value, benchmark
                )
                
                # Determine performance rating
                performance_rating = self._get_performance_rating(percentile_rank)
                
                # Calculate improvement potential
                improvement_potential = max(
                    Decimal('0'), 
                    benchmark.percentile_75 - company_value
                )
                
                # Get peer companies (mock data for now)
                peer_companies = self._get_peer_companies(industry, company_size)
                
                comparisons[metric_name] = BenchmarkComparison(
                    company_value=company_value,
                    industry_median=benchmark.percentile_50,
                    industry_average=benchmark.value,
                    percentile_rank=percentile_rank,
                    performance_rating=performance_rating,
                    peer_companies=peer_companies,
                    improvement_potential=improvement_potential
                )
            
            self.logger.info(f"Generated {len(comparisons)} benchmark comparisons")
            return comparisons
            
        except Exception as e:
            self.logger.error(f"Error comparing to industry: {str(e)}")
            return {}
    
    def _calculate_percentile_rank(
        self, 
        company_value: Decimal, 
        benchmark: IndustryMetric
    ) -> float:
        """
        Calculate percentile rank of company value within industry distribution
        """
        # Simple interpolation between percentiles
        if company_value <= benchmark.percentile_25:
            # Below 25th percentile
            if benchmark.percentile_25 > 0:
                ratio = float(company_value / benchmark.percentile_25)
                return min(25.0, 25.0 * ratio)
            else:
                return 25.0
        elif company_value <= benchmark.percentile_50:
            # Between 25th and 50th percentile
            range_size = benchmark.percentile_50 - benchmark.percentile_25
            if range_size > 0:
                position = (company_value - benchmark.percentile_25) / range_size
                return 25.0 + (25.0 * float(position))
            else:
                return 37.5
        elif company_value <= benchmark.percentile_75:
            # Between 50th and 75th percentile
            range_size = benchmark.percentile_75 - benchmark.percentile_50
            if range_size > 0:
                position = (company_value - benchmark.percentile_50) / range_size
                return 50.0 + (25.0 * float(position))
            else:
                return 62.5
        else:
            # Above 75th percentile
            excess = company_value - benchmark.percentile_75
            if benchmark.percentile_75 > 0:
                excess_ratio = float(excess / benchmark.percentile_75)
                return min(95.0, 75.0 + (20.0 * excess_ratio))
            else:
                return 85.0
    
    def _get_performance_rating(self, percentile_rank: float) -> str:
        """Convert percentile rank to performance rating"""
        if percentile_rank >= 80:
            return "Excellent"
        elif percentile_rank >= 60:
            return "Above Average"
        elif percentile_rank >= 40:
            return "Average"
        elif percentile_rank >= 20:
            return "Below Average"
        else:
            return "Poor"
    
    def _get_peer_companies(
        self, 
        industry: IndustryType, 
        company_size: CompanySize = None
    ) -> List[str]:
        """
        Get list of peer companies for comparison
        In production, this would query a company database
        """
        # Mock peer companies by industry
        peer_data = {
            IndustryType.TECHNOLOGY: [
                "Microsoft", "Google", "Apple", "Amazon", "Meta",
                "Salesforce", "Adobe", "Oracle", "IBM", "Intel"
            ],
            IndustryType.FINANCE: [
                "JPMorgan Chase", "Bank of America", "Wells Fargo", "Goldman Sachs",
                "Morgan Stanley", "Citigroup", "American Express", "Charles Schwab"
            ],
            IndustryType.HEALTHCARE: [
                "Johnson & Johnson", "Pfizer", "UnitedHealth", "Merck", "AbbVie",
                "Bristol Myers Squibb", "Eli Lilly", "Amgen", "Gilead Sciences"
            ]
        }
        
        peers = peer_data.get(industry, [])
        
        # Filter by company size if specified
        if company_size == CompanySize.STARTUP:
            return peers[:3]  # Smaller peer set for startups
        elif company_size == CompanySize.SMALL:
            return peers[:5]
        else:
            return peers[:8]
    
    def perform_competitive_analysis(
        self, 
        company_profile: CompanyProfile,
        include_financial_comparison: bool = True
    ) -> CompetitiveAnalysis:
        """
        Perform comprehensive competitive analysis
        
        Args:
            company_profile: Company to analyze
            include_financial_comparison: Include financial metrics comparison
            
        Returns:
            CompetitiveAnalysis with detailed competitive insights
        """
        try:
            # Get direct competitors
            direct_competitors = self._identify_direct_competitors(company_profile)
            
            # Determine market position
            market_position = self._assess_market_position(company_profile, direct_competitors)
            
            # Identify competitive advantages and disadvantages
            advantages, disadvantages = self._analyze_competitive_position(
                company_profile, direct_competitors
            )
            
            # Estimate market share (simplified calculation)
            market_share = self._estimate_market_share(company_profile)
            
            # Compare growth rates
            growth_comparison = {}
            if include_financial_comparison:
                growth_comparison = self._compare_growth_rates(
                    company_profile, direct_competitors
                )
            
            self.logger.info(f"Completed competitive analysis for {company_profile.name}")
            
            return CompetitiveAnalysis(
                company_profile=company_profile,
                direct_competitors=direct_competitors,
                market_position=market_position,
                competitive_advantages=advantages,
                competitive_disadvantages=disadvantages,
                market_share_estimate=market_share,
                growth_comparison=growth_comparison
            )
            
        except Exception as e:
            self.logger.error(f"Error performing competitive analysis: {str(e)}")
            raise
    
    def _identify_direct_competitors(self, company_profile: CompanyProfile) -> List[CompanyProfile]:
        """Identify direct competitors based on industry and size"""
        # Mock competitor identification
        competitors = []
        peer_names = self._get_peer_companies(company_profile.industry, company_profile.size)
        
        for i, name in enumerate(peer_names[:5]):  # Top 5 competitors
            competitor = CompanyProfile(
                company_id=f"comp_{i+1}",
                name=name,
                industry=company_profile.industry,
                size=company_profile.size,
                revenue=company_profile.revenue * Decimal(str(0.8 + (i * 0.1))) if company_profile.revenue else None,
                employees=company_profile.employees + (i * 1000) if company_profile.employees else None,
                founded_year=company_profile.founded_year - (i * 2) if company_profile.founded_year else None,
                location="Various",
                public_company=True
            )
            competitors.append(competitor)
        
        return competitors
    
    def _assess_market_position(
        self, 
        company_profile: CompanyProfile, 
        competitors: List[CompanyProfile]
    ) -> str:
        """Assess company's market position relative to competitors"""
        if not company_profile.revenue:
            return "Position unclear - insufficient financial data"
        
        # Compare revenue to competitors
        competitor_revenues = [c.revenue for c in competitors if c.revenue]
        if not competitor_revenues:
            return "Market leader - no comparable competitor data"
        
        avg_competitor_revenue = sum(competitor_revenues) / len(competitor_revenues)
        
        if company_profile.revenue > avg_competitor_revenue * Decimal('1.5'):
            return "Market leader"
        elif company_profile.revenue > avg_competitor_revenue:
            return "Strong competitor"
        elif company_profile.revenue > avg_competitor_revenue * Decimal('0.7'):
            return "Established player"
        else:
            return "Emerging competitor"
    
    def _analyze_competitive_position(
        self, 
        company_profile: CompanyProfile, 
        competitors: List[CompanyProfile]
    ) -> Tuple[List[str], List[str]]:
        """Analyze competitive advantages and disadvantages"""
        advantages = []
        disadvantages = []
        
        # Size-based analysis
        if company_profile.size in [CompanySize.STARTUP, CompanySize.SMALL]:
            advantages.extend([
                "Agility and quick decision-making",
                "Innovation and flexibility",
                "Lower operational overhead"
            ])
            disadvantages.extend([
                "Limited resources and capital",
                "Smaller market presence",
                "Less established customer base"
            ])
        else:
            advantages.extend([
                "Established market presence",
                "Significant resources and capital",
                "Economies of scale"
            ])
            disadvantages.extend([
                "Potential bureaucracy",
                "Slower adaptation to market changes",
                "Higher operational costs"
            ])
        
        # Industry-specific advantages
        if company_profile.industry == IndustryType.TECHNOLOGY:
            advantages.append("Access to cutting-edge technology")
            if company_profile.founded_year and company_profile.founded_year > 2010:
                advantages.append("Modern technology stack")
            else:
                disadvantages.append("Legacy system constraints")
        
        return advantages, disadvantages
    
    def _estimate_market_share(self, company_profile: CompanyProfile) -> Optional[float]:
        """Estimate market share (simplified calculation)"""
        if not company_profile.revenue:
            return None
        
        # Mock market size data by industry
        market_sizes = {
            IndustryType.TECHNOLOGY: Decimal('5000000000'),  # $5B
            IndustryType.FINANCE: Decimal('3000000000'),     # $3B
            IndustryType.HEALTHCARE: Decimal('4000000000')   # $4B
        }
        
        market_size = market_sizes.get(company_profile.industry, Decimal('2000000000'))
        market_share = float(company_profile.revenue / market_size) * 100
        
        return min(market_share, 50.0)  # Cap at 50% for realism
    
    def _compare_growth_rates(
        self, 
        company_profile: CompanyProfile, 
        competitors: List[CompanyProfile]
    ) -> Dict[str, float]:
        """Compare growth rates with competitors"""
        # Mock growth rate comparison
        return {
            "company_growth_rate": 15.2,
            "industry_average_growth": 12.8,
            "top_competitor_growth": 18.5,
            "growth_rank": 3  # Out of analyzed companies
        }
    
    def get_market_trends(
        self, 
        industry: IndustryType,
        time_horizon: str = "short_term"
    ) -> List[MarketTrend]:
        """
        Get market trends for specified industry
        
        Args:
            industry: Industry to analyze
            time_horizon: "short_term", "medium_term", or "long_term"
            
        Returns:
            List of market trends
        """
        try:
            trends = self._mock_trends.get(industry, [])
            
            # Filter by time horizon if needed
            if time_horizon == "short_term":
                trends = [t for t in trends if "2024" in t.time_period]
            elif time_horizon == "long_term":
                trends = [t for t in trends if "2026" in t.time_period or "2027" in t.time_period]
            
            self.logger.info(f"Retrieved {len(trends)} market trends for {industry.value}")
            return trends
            
        except Exception as e:
            self.logger.error(f"Error getting market trends: {str(e)}")
            return []
    
    def generate_industry_report(
        self, 
        industry: IndustryType,
        include_trends: bool = True,
        include_competitors: bool = True
    ) -> IndustryReport:
        """
        Generate comprehensive industry report
        
        Args:
            industry: Industry to analyze
            include_trends: Include market trends analysis
            include_competitors: Include competitive landscape
            
        Returns:
            IndustryReport with comprehensive analysis
        """
        try:
            # Get key metrics
            key_metrics = self.get_industry_benchmarks(industry)
            
            # Get market trends
            market_trends = []
            if include_trends:
                market_trends = self.get_market_trends(industry)
            
            # Get top performers (mock data)
            top_performers = []
            if include_competitors:
                peer_names = self._get_peer_companies(industry)[:3]
                for i, name in enumerate(peer_names):
                    performer = CompanyProfile(
                        company_id=f"top_{i+1}",
                        name=name,
                        industry=industry,
                        size=CompanySize.LARGE,
                        revenue=Decimal(str(1000000000 + (i * 500000000))),
                        employees=10000 + (i * 5000),
                        founded_year=1990 + (i * 10),
                        location="Global",
                        public_company=True
                    )
                    top_performers.append(performer)
            
            # Industry challenges and opportunities (mock data)
            challenges_by_industry = {
                IndustryType.TECHNOLOGY: [
                    "Rapid technological change",
                    "Talent shortage",
                    "Regulatory uncertainty",
                    "Cybersecurity threats"
                ],
                IndustryType.FINANCE: [
                    "Regulatory compliance",
                    "Digital transformation pressure",
                    "Interest rate volatility",
                    "Fintech competition"
                ],
                IndustryType.HEALTHCARE: [
                    "Regulatory approval processes",
                    "Rising R&D costs",
                    "Pricing pressure",
                    "Aging population demands"
                ]
            }
            
            opportunities_by_industry = {
                IndustryType.TECHNOLOGY: [
                    "AI and machine learning adoption",
                    "Cloud computing growth",
                    "IoT expansion",
                    "Digital transformation services"
                ],
                IndustryType.FINANCE: [
                    "Digital banking services",
                    "ESG investing growth",
                    "Cryptocurrency adoption",
                    "Robo-advisory services"
                ],
                IndustryType.HEALTHCARE: [
                    "Personalized medicine",
                    "Telemedicine expansion",
                    "Digital health solutions",
                    "Aging population services"
                ]
            }
            
            challenges = challenges_by_industry.get(industry, [])
            opportunities = opportunities_by_industry.get(industry, [])
            
            # Regulatory environment assessment
            regulatory_environment = self._assess_regulatory_environment(industry)
            
            self.logger.info(f"Generated comprehensive industry report for {industry.value}")
            
            return IndustryReport(
                industry=industry,
                report_date=datetime.utcnow(),
                key_metrics=key_metrics,
                market_trends=market_trends,
                top_performers=top_performers,
                industry_challenges=challenges,
                growth_opportunities=opportunities,
                regulatory_environment=regulatory_environment
            )
            
        except Exception as e:
            self.logger.error(f"Error generating industry report: {str(e)}")
            raise
    
    def _assess_regulatory_environment(self, industry: IndustryType) -> str:
        """Assess regulatory environment for industry"""
        assessments = {
            IndustryType.TECHNOLOGY: "Moderate - Increasing focus on data privacy and antitrust",
            IndustryType.FINANCE: "High - Heavily regulated with strict compliance requirements",
            IndustryType.HEALTHCARE: "Very High - Extensive FDA and safety regulations",
            IndustryType.MANUFACTURING: "Moderate - Environmental and safety regulations",
            IndustryType.ENERGY: "High - Environmental and safety regulations"
        }
        
        return assessments.get(industry, "Moderate - Standard business regulations apply")