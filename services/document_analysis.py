"""
Document Analysis Service

Provides advanced document analysis features including:
- Automatic document summarization
- Key insight extraction
- Document categorization
- Sentiment analysis
- Entity extraction
- Topic modeling
"""

import logging
import os
import re
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import json

# For advanced text analysis
try:
    import openai
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

logger = logging.getLogger(__name__)


class AnalysisType(Enum):
    """Types of document analysis"""
    SUMMARY = "summary"
    KEY_INSIGHTS = "key_insights"
    CATEGORIZATION = "categorization"
    SENTIMENT = "sentiment"
    ENTITIES = "entities"
    TOPICS = "topics"
    FINANCIAL_METRICS = "financial_metrics"
    TECHNICAL_SPECS = "technical_specs"
    STRATEGIC_POINTS = "strategic_points"


@dataclass
class DocumentSummary:
    """Document summary with different levels of detail"""
    executive_summary: str  # 1-2 sentences
    detailed_summary: str   # 1-2 paragraphs
    key_points: List[str]   # Bullet points
    word_count: int
    reading_time_minutes: int


@dataclass
class KeyInsight:
    """A key insight extracted from document"""
    insight: str
    category: str  # financial, technical, strategic, operational, etc.
    confidence: float  # 0.0 to 1.0
    supporting_text: str
    importance: str  # high, medium, low


@dataclass
class DocumentCategory:
    """Document categorization result"""
    primary_category: str
    confidence: float
    secondary_categories: List[Tuple[str, float]]
    reasoning: str


@dataclass
class SentimentAnalysis:
    """Sentiment analysis result"""
    overall_sentiment: str  # positive, negative, neutral
    confidence: float
    sentiment_scores: Dict[str, float]  # positive, negative, neutral scores
    emotional_tone: List[str]  # professional, urgent, optimistic, etc.


@dataclass
class EntityExtraction:
    """Named entity extraction result"""
    people: List[str]
    organizations: List[str]
    locations: List[str]
    dates: List[str]
    monetary_amounts: List[str]
    percentages: List[str]
    products: List[str]
    technologies: List[str]


@dataclass
class TopicAnalysis:
    """Topic modeling result"""
    main_topics: List[Tuple[str, float]]  # topic, weight
    topic_distribution: Dict[str, float]
    related_keywords: Dict[str, List[str]]


@dataclass
class FinancialMetrics:
    """Financial metrics extracted from document"""
    revenue_figures: List[Dict[str, Any]]
    profit_margins: List[Dict[str, Any]]
    growth_rates: List[Dict[str, Any]]
    cost_figures: List[Dict[str, Any]]
    financial_ratios: List[Dict[str, Any]]
    projections: List[Dict[str, Any]]


@dataclass
class TechnicalSpecs:
    """Technical specifications extracted from document"""
    technologies: List[str]
    architectures: List[str]
    performance_metrics: List[Dict[str, Any]]
    requirements: List[str]
    constraints: List[str]
    recommendations: List[str]


@dataclass
class StrategicPoints:
    """Strategic points extracted from document"""
    objectives: List[str]
    opportunities: List[str]
    threats: List[str]
    recommendations: List[str]
    market_analysis: List[str]
    competitive_insights: List[str]


class DocumentAnalysisService:
    """Service for advanced document analysis"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # OpenAI configuration
        self.openai_api_key = config.get('openai_api_key') or os.getenv('OPENAI_API_KEY')
        self.model = config.get('analysis_model', 'gpt-3.5-turbo')
        
        # Initialize OpenAI client
        if self.openai_api_key and HAS_OPENAI:
            self.openai_client = OpenAI(api_key=self.openai_api_key)
            self.logger.info("OpenAI client initialized for document analysis")
        else:
            self.openai_client = None
            self.logger.warning("OpenAI client not available - using fallback analysis methods")
        
        # Analysis patterns and keywords
        self._initialize_patterns()
    
    def analyze_document(
        self, 
        content: str, 
        analysis_types: List[AnalysisType] = None,
        document_metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Perform comprehensive document analysis
        
        Args:
            content: Document text content
            analysis_types: Types of analysis to perform (default: all)
            document_metadata: Additional document metadata
            
        Returns:
            Dictionary containing all analysis results
        """
        if analysis_types is None:
            analysis_types = list(AnalysisType)
        
        self.logger.info(f"Analyzing document with {len(analysis_types)} analysis types")
        
        results = {}
        
        # Basic document statistics
        results['statistics'] = self._calculate_document_statistics(content)
        
        # Perform requested analyses
        for analysis_type in analysis_types:
            try:
                if analysis_type == AnalysisType.SUMMARY:
                    results['summary'] = self.generate_summary(content)
                elif analysis_type == AnalysisType.KEY_INSIGHTS:
                    results['key_insights'] = self.extract_key_insights(content)
                elif analysis_type == AnalysisType.CATEGORIZATION:
                    results['categorization'] = self.categorize_document(content)
                elif analysis_type == AnalysisType.SENTIMENT:
                    results['sentiment'] = self.analyze_sentiment(content)
                elif analysis_type == AnalysisType.ENTITIES:
                    results['entities'] = self.extract_entities(content)
                elif analysis_type == AnalysisType.TOPICS:
                    results['topics'] = self.analyze_topics(content)
                elif analysis_type == AnalysisType.FINANCIAL_METRICS:
                    results['financial_metrics'] = self.extract_financial_metrics(content)
                elif analysis_type == AnalysisType.TECHNICAL_SPECS:
                    results['technical_specs'] = self.extract_technical_specs(content)
                elif analysis_type == AnalysisType.STRATEGIC_POINTS:
                    results['strategic_points'] = self.extract_strategic_points(content)
                    
            except Exception as e:
                self.logger.error(f"Error in {analysis_type.value} analysis: {str(e)}")
                results[analysis_type.value] = None
        
        return results
    
    def generate_summary(self, content: str) -> DocumentSummary:
        """Generate document summary at multiple levels"""
        if self.openai_client:
            return self._generate_ai_summary(content)
        else:
            return self._generate_rule_based_summary(content)
    
    def extract_key_insights(self, content: str) -> List[KeyInsight]:
        """Extract key insights from document"""
        if self.openai_client:
            return self._extract_ai_insights(content)
        else:
            return self._extract_rule_based_insights(content)
    
    def categorize_document(self, content: str) -> DocumentCategory:
        """Categorize document based on content"""
        if self.openai_client:
            return self._categorize_with_ai(content)
        else:
            return self._categorize_with_rules(content)
    
    def analyze_sentiment(self, content: str) -> SentimentAnalysis:
        """Analyze document sentiment and tone"""
        if self.openai_client:
            return self._analyze_sentiment_with_ai(content)
        else:
            return self._analyze_sentiment_with_rules(content)
    
    def extract_entities(self, content: str) -> EntityExtraction:
        """Extract named entities from document"""
        return self._extract_entities_with_rules(content)
    
    def analyze_topics(self, content: str) -> TopicAnalysis:
        """Analyze document topics and themes"""
        return self._analyze_topics_with_rules(content)
    
    def extract_financial_metrics(self, content: str) -> FinancialMetrics:
        """Extract financial metrics and figures"""
        return self._extract_financial_metrics_with_rules(content)
    
    def extract_technical_specs(self, content: str) -> TechnicalSpecs:
        """Extract technical specifications and requirements"""
        return self._extract_technical_specs_with_rules(content)
    
    def extract_strategic_points(self, content: str) -> StrategicPoints:
        """Extract strategic insights and recommendations"""
        return self._extract_strategic_points_with_rules(content)
    
    def _initialize_patterns(self):
        """Initialize regex patterns and keyword lists for analysis"""
        # Financial patterns
        self.financial_patterns = {
            'revenue': re.compile(r'revenue|sales|income|earnings', re.IGNORECASE),
            'profit': re.compile(r'profit|margin|ebitda|net income', re.IGNORECASE),
            'growth': re.compile(r'growth|increase|decrease|change', re.IGNORECASE),
            'percentage': re.compile(r'(\d+(?:\.\d+)?)\s*%'),
            'currency': re.compile(r'\$[\d,]+(?:\.\d{2})?|\d+(?:\.\d+)?\s*(?:million|billion|thousand|k|m|b)', re.IGNORECASE)
        }
        
        # Technical patterns
        self.technical_patterns = {
            'technologies': re.compile(r'python|java|javascript|react|angular|vue|docker|kubernetes|aws|azure|gcp', re.IGNORECASE),
            'architecture': re.compile(r'microservices|monolith|api|rest|graphql|database|sql|nosql', re.IGNORECASE),
            'performance': re.compile(r'performance|latency|throughput|scalability|availability', re.IGNORECASE)
        }
        
        # Strategic patterns
        self.strategic_patterns = {
            'objectives': re.compile(r'objective|goal|target|aim|mission|vision', re.IGNORECASE),
            'opportunities': re.compile(r'opportunity|potential|advantage|benefit', re.IGNORECASE),
            'threats': re.compile(r'threat|risk|challenge|concern|issue', re.IGNORECASE),
            'market': re.compile(r'market|competition|competitor|industry|sector', re.IGNORECASE)
        }
        
        # Sentiment keywords
        self.sentiment_keywords = {
            'positive': ['excellent', 'outstanding', 'successful', 'growth', 'improvement', 'opportunity', 'advantage', 'strong', 'effective'],
            'negative': ['poor', 'decline', 'loss', 'problem', 'issue', 'challenge', 'threat', 'weak', 'ineffective'],
            'neutral': ['analysis', 'report', 'data', 'information', 'summary', 'overview', 'description']
        }
    
    def _calculate_document_statistics(self, content: str) -> Dict[str, Any]:
        """Calculate basic document statistics"""
        words = content.split()
        sentences = re.split(r'[.!?]+', content)
        paragraphs = content.split('\n\n')
        
        return {
            'word_count': len(words),
            'sentence_count': len([s for s in sentences if s.strip()]),
            'paragraph_count': len([p for p in paragraphs if p.strip()]),
            'character_count': len(content),
            'reading_time_minutes': max(1, len(words) // 200)  # Assume 200 words per minute
        }
    
    def _generate_rule_based_summary(self, content: str) -> DocumentSummary:
        """Generate summary using rule-based approach"""
        sentences = re.split(r'[.!?]+', content)
        sentences = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 20]
        
        # Simple extractive summarization - take first and last sentences, plus any with keywords
        key_sentences = []
        
        # Add first sentence
        if sentences:
            key_sentences.append(sentences[0])
        
        # Add sentences with important keywords
        important_keywords = ['revenue', 'profit', 'growth', 'strategy', 'objective', 'recommendation', 'conclusion']
        for sentence in sentences[1:-1]:
            if any(keyword in sentence.lower() for keyword in important_keywords):
                key_sentences.append(sentence)
                if len(key_sentences) >= 5:
                    break
        
        # Add last sentence
        if len(sentences) > 1:
            key_sentences.append(sentences[-1])
        
        # Remove duplicates while preserving order
        unique_sentences = []
        for sentence in key_sentences:
            if sentence not in unique_sentences:
                unique_sentences.append(sentence)
        
        executive_summary = unique_sentences[0] if unique_sentences else "No summary available."
        detailed_summary = ' '.join(unique_sentences[:3])
        key_points = unique_sentences[:5]
        
        stats = self._calculate_document_statistics(content)
        
        return DocumentSummary(
            executive_summary=executive_summary,
            detailed_summary=detailed_summary,
            key_points=key_points,
            word_count=stats['word_count'],
            reading_time_minutes=stats['reading_time_minutes']
        )
    
    def _extract_rule_based_insights(self, content: str) -> List[KeyInsight]:
        """Extract insights using rule-based approach"""
        insights = []
        content_lower = content.lower()
        
        # Financial insights
        if self.financial_patterns['revenue'].search(content):
            revenue_matches = self.financial_patterns['currency'].findall(content)
            if revenue_matches:
                insights.append(KeyInsight(
                    insight=f"Document contains revenue information: {', '.join(revenue_matches[:3])}",
                    category="financial",
                    confidence=0.8,
                    supporting_text="Revenue figures found in document",
                    importance="high"
                ))
        
        # Growth insights
        growth_matches = self.financial_patterns['percentage'].findall(content)
        if growth_matches:
            insights.append(KeyInsight(
                insight=f"Document mentions percentage changes: {', '.join(growth_matches[:3])}%",
                category="financial",
                confidence=0.7,
                supporting_text="Percentage figures indicating growth or changes",
                importance="medium"
            ))
        
        # Technical insights
        tech_matches = self.technical_patterns['technologies'].findall(content)
        if tech_matches:
            insights.append(KeyInsight(
                insight=f"Document discusses technologies: {', '.join(set(tech_matches[:5]))}",
                category="technical",
                confidence=0.8,
                supporting_text="Technology keywords found",
                importance="medium"
            ))
        
        # Strategic insights
        if self.strategic_patterns['objectives'].search(content):
            insights.append(KeyInsight(
                insight="Document contains strategic objectives and goals",
                category="strategic",
                confidence=0.7,
                supporting_text="Objective-related keywords found",
                importance="high"
            ))
        
        return insights[:10]  # Limit to top 10 insights
    
    def _categorize_with_rules(self, content: str) -> DocumentCategory:
        """Categorize document using rule-based approach"""
        content_lower = content.lower()
        
        # Category scoring
        scores = {
            'financial': 0,
            'technical': 0,
            'strategic': 0,
            'operational': 0,
            'legal': 0,
            'marketing': 0
        }
        
        # Financial scoring
        financial_keywords = ['revenue', 'profit', 'budget', 'cost', 'financial', 'accounting', 'investment']
        scores['financial'] = sum(1 for keyword in financial_keywords if keyword in content_lower)
        
        # Technical scoring
        technical_keywords = ['system', 'software', 'technology', 'development', 'architecture', 'database', 'api']
        scores['technical'] = sum(1 for keyword in technical_keywords if keyword in content_lower)
        
        # Strategic scoring
        strategic_keywords = ['strategy', 'market', 'competition', 'business', 'planning', 'vision', 'mission']
        scores['strategic'] = sum(1 for keyword in strategic_keywords if keyword in content_lower)
        
        # Operational scoring
        operational_keywords = ['process', 'procedure', 'operations', 'workflow', 'efficiency', 'productivity']
        scores['operational'] = sum(1 for keyword in operational_keywords if keyword in content_lower)
        
        # Legal scoring
        legal_keywords = ['contract', 'agreement', 'legal', 'compliance', 'regulation', 'policy']
        scores['legal'] = sum(1 for keyword in legal_keywords if keyword in content_lower)
        
        # Marketing scoring
        marketing_keywords = ['marketing', 'campaign', 'brand', 'customer', 'sales', 'promotion']
        scores['marketing'] = sum(1 for keyword in marketing_keywords if keyword in content_lower)
        
        # Find primary category
        primary_category = max(scores, key=scores.get)
        max_score = scores[primary_category]
        total_score = sum(scores.values())
        
        confidence = max_score / max(total_score, 1) if total_score > 0 else 0.5
        
        # Secondary categories
        secondary_categories = [(cat, score/max(total_score, 1)) for cat, score in scores.items() 
                               if cat != primary_category and score > 0]
        secondary_categories.sort(key=lambda x: x[1], reverse=True)
        
        return DocumentCategory(
            primary_category=primary_category,
            confidence=confidence,
            secondary_categories=secondary_categories[:3],
            reasoning=f"Based on keyword analysis, found {max_score} relevant keywords for {primary_category} category"
        )
    
    def _analyze_sentiment_with_rules(self, content: str) -> SentimentAnalysis:
        """Analyze sentiment using rule-based approach"""
        content_lower = content.lower()
        
        # Count sentiment keywords
        positive_count = sum(1 for word in self.sentiment_keywords['positive'] if word in content_lower)
        negative_count = sum(1 for word in self.sentiment_keywords['negative'] if word in content_lower)
        neutral_count = sum(1 for word in self.sentiment_keywords['neutral'] if word in content_lower)
        
        total_count = positive_count + negative_count + neutral_count
        
        if total_count == 0:
            return SentimentAnalysis(
                overall_sentiment="neutral",
                confidence=0.5,
                sentiment_scores={"positive": 0.33, "negative": 0.33, "neutral": 0.34},
                emotional_tone=["professional"]
            )
        
        # Calculate scores
        positive_score = positive_count / total_count
        negative_score = negative_count / total_count
        neutral_score = neutral_count / total_count
        
        # Determine overall sentiment
        if positive_score > negative_score and positive_score > neutral_score:
            overall_sentiment = "positive"
            confidence = positive_score
        elif negative_score > positive_score and negative_score > neutral_score:
            overall_sentiment = "negative"
            confidence = negative_score
        else:
            overall_sentiment = "neutral"
            confidence = neutral_score
        
        # Determine emotional tone
        emotional_tone = ["professional"]  # Default
        if positive_score > 0.4:
            emotional_tone.append("optimistic")
        if negative_score > 0.4:
            emotional_tone.append("concerned")
        
        return SentimentAnalysis(
            overall_sentiment=overall_sentiment,
            confidence=confidence,
            sentiment_scores={
                "positive": positive_score,
                "negative": negative_score,
                "neutral": neutral_score
            },
            emotional_tone=emotional_tone
        )
    
    def _extract_entities_with_rules(self, content: str) -> EntityExtraction:
        """Extract entities using rule-based approach"""
        # Simple regex patterns for entity extraction
        
        # People (capitalized names)
        people_pattern = re.compile(r'\b[A-Z][a-z]+ [A-Z][a-z]+\b')
        people = list(set(people_pattern.findall(content)))
        
        # Organizations (common suffixes)
        org_pattern = re.compile(r'\b[A-Z][a-zA-Z\s]+ (?:Inc|Corp|LLC|Ltd|Company|Corporation|Group|Partners)\b')
        organizations = list(set(org_pattern.findall(content)))
        
        # Dates
        date_pattern = re.compile(r'\b(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}[/-]\d{1,2}[/-]\d{1,2}|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4})\b')
        dates = list(set(date_pattern.findall(content)))
        
        # Monetary amounts
        money_pattern = re.compile(r'\$[\d,]+(?:\.\d{2})?|\d+(?:\.\d+)?\s*(?:million|billion|thousand|k|m|b)', re.IGNORECASE)
        monetary_amounts = list(set(money_pattern.findall(content)))
        
        # Percentages
        percentage_pattern = re.compile(r'\d+(?:\.\d+)?%')
        percentages = list(set(percentage_pattern.findall(content)))
        
        # Technologies (from our technical patterns)
        tech_pattern = re.compile(r'\b(?:Python|Java|JavaScript|React|Angular|Vue|Docker|Kubernetes|AWS|Azure|GCP|SQL|NoSQL|API|REST|GraphQL)\b', re.IGNORECASE)
        technologies = list(set(tech_pattern.findall(content)))
        
        return EntityExtraction(
            people=people[:10],
            organizations=organizations[:10],
            locations=[],  # Would need more sophisticated location detection
            dates=dates[:10],
            monetary_amounts=monetary_amounts[:10],
            percentages=percentages[:10],
            products=[],  # Would need product-specific patterns
            technologies=technologies[:10]
        )
    
    def _analyze_topics_with_rules(self, content: str) -> TopicAnalysis:
        """Analyze topics using rule-based approach"""
        content_lower = content.lower()
        
        # Define topic keywords
        topic_keywords = {
            'finance': ['revenue', 'profit', 'budget', 'cost', 'investment', 'financial', 'money', 'income'],
            'technology': ['system', 'software', 'development', 'architecture', 'database', 'api', 'technology'],
            'strategy': ['strategy', 'market', 'competition', 'business', 'planning', 'vision', 'mission'],
            'operations': ['process', 'procedure', 'operations', 'workflow', 'efficiency', 'productivity'],
            'marketing': ['marketing', 'campaign', 'brand', 'customer', 'sales', 'promotion'],
            'legal': ['contract', 'agreement', 'legal', 'compliance', 'regulation', 'policy']
        }
        
        # Calculate topic scores
        topic_scores = {}
        total_keywords = 0
        
        for topic, keywords in topic_keywords.items():
            score = sum(1 for keyword in keywords if keyword in content_lower)
            topic_scores[topic] = score
            total_keywords += score
        
        # Normalize scores
        if total_keywords > 0:
            topic_distribution = {topic: score/total_keywords for topic, score in topic_scores.items()}
        else:
            topic_distribution = {topic: 1/len(topic_keywords) for topic in topic_keywords}
        
        # Get main topics (sorted by score)
        main_topics = [(topic, score) for topic, score in topic_distribution.items() if score > 0.1]
        main_topics.sort(key=lambda x: x[1], reverse=True)
        
        # Related keywords
        related_keywords = {topic: keywords for topic, keywords in topic_keywords.items() 
                           if topic_distribution.get(topic, 0) > 0.1}
        
        return TopicAnalysis(
            main_topics=main_topics[:5],
            topic_distribution=topic_distribution,
            related_keywords=related_keywords
        )
    
    def _extract_financial_metrics_with_rules(self, content: str) -> FinancialMetrics:
        """Extract financial metrics using rule-based approach"""
        # Revenue figures
        revenue_pattern = re.compile(r'revenue[^.]*?(\$[\d,]+(?:\.\d{2})?|\d+(?:\.\d+)?\s*(?:million|billion|thousand|k|m|b))', re.IGNORECASE)
        revenue_matches = revenue_pattern.findall(content)
        revenue_figures = [{'amount': match, 'context': 'revenue'} for match in revenue_matches]
        
        # Profit margins
        margin_pattern = re.compile(r'(?:profit|margin)[^.]*?(\d+(?:\.\d+)?%)', re.IGNORECASE)
        margin_matches = margin_pattern.findall(content)
        profit_margins = [{'percentage': match, 'context': 'profit margin'} for match in margin_matches]
        
        # Growth rates
        growth_pattern = re.compile(r'(?:growth|increase|decrease)[^.]*?(\d+(?:\.\d+)?%)', re.IGNORECASE)
        growth_matches = growth_pattern.findall(content)
        growth_rates = [{'percentage': match, 'context': 'growth rate'} for match in growth_matches]
        
        return FinancialMetrics(
            revenue_figures=revenue_figures[:5],
            profit_margins=profit_margins[:5],
            growth_rates=growth_rates[:5],
            cost_figures=[],
            financial_ratios=[],
            projections=[]
        )
    
    def _extract_technical_specs_with_rules(self, content: str) -> TechnicalSpecs:
        """Extract technical specifications using rule-based approach"""
        # Technologies
        tech_pattern = re.compile(r'\b(?:Python|Java|JavaScript|React|Angular|Vue|Docker|Kubernetes|AWS|Azure|GCP|SQL|NoSQL|API|REST|GraphQL|MongoDB|PostgreSQL|Redis|Elasticsearch)\b', re.IGNORECASE)
        technologies = list(set(tech_pattern.findall(content)))
        
        # Architectures
        arch_pattern = re.compile(r'\b(?:microservices|monolith|serverless|cloud|distributed|scalable|architecture)\b', re.IGNORECASE)
        architectures = list(set(arch_pattern.findall(content)))
        
        # Performance metrics
        perf_pattern = re.compile(r'(?:performance|latency|throughput|response time)[^.]*?(\d+(?:\.\d+)?\s*(?:ms|seconds|requests/sec|rps))', re.IGNORECASE)
        perf_matches = perf_pattern.findall(content)
        performance_metrics = [{'metric': match, 'context': 'performance'} for match in perf_matches]
        
        # Requirements (sentences with "must", "should", "required")
        req_pattern = re.compile(r'[^.]*(?:must|should|required|requirement)[^.]*\.', re.IGNORECASE)
        requirements = req_pattern.findall(content)[:5]
        
        return TechnicalSpecs(
            technologies=technologies[:10],
            architectures=architectures[:5],
            performance_metrics=performance_metrics[:5],
            requirements=requirements,
            constraints=[],
            recommendations=[]
        )
    
    def _extract_strategic_points_with_rules(self, content: str) -> StrategicPoints:
        """Extract strategic points using rule-based approach"""
        # Objectives
        obj_pattern = re.compile(r'[^.]*(?:objective|goal|target|aim)[^.]*\.', re.IGNORECASE)
        objectives = obj_pattern.findall(content)[:5]
        
        # Opportunities
        opp_pattern = re.compile(r'[^.]*(?:opportunity|potential|advantage)[^.]*\.', re.IGNORECASE)
        opportunities = opp_pattern.findall(content)[:5]
        
        # Threats/Risks
        threat_pattern = re.compile(r'[^.]*(?:threat|risk|challenge|concern)[^.]*\.', re.IGNORECASE)
        threats = threat_pattern.findall(content)[:5]
        
        # Recommendations
        rec_pattern = re.compile(r'[^.]*(?:recommend|suggest|propose|should)[^.]*\.', re.IGNORECASE)
        recommendations = rec_pattern.findall(content)[:5]
        
        # Market analysis
        market_pattern = re.compile(r'[^.]*(?:market|competition|competitor|industry)[^.]*\.', re.IGNORECASE)
        market_analysis = market_pattern.findall(content)[:5]
        
        return StrategicPoints(
            objectives=objectives,
            opportunities=opportunities,
            threats=threats,
            recommendations=recommendations,
            market_analysis=market_analysis,
            competitive_insights=[]
        )
    
    # AI-powered methods (would be implemented if OpenAI is available)
    def _generate_ai_summary(self, content: str) -> DocumentSummary:
        """Generate summary using AI (placeholder)"""
        # Would implement actual AI summarization here
        return self._generate_rule_based_summary(content)
    
    def _extract_ai_insights(self, content: str) -> List[KeyInsight]:
        """Extract insights using AI (placeholder)"""
        # Would implement actual AI insight extraction here
        return self._extract_rule_based_insights(content)
    
    def _categorize_with_ai(self, content: str) -> DocumentCategory:
        """Categorize using AI (placeholder)"""
        # Would implement actual AI categorization here
        return self._categorize_with_rules(content)
    
    def _analyze_sentiment_with_ai(self, content: str) -> SentimentAnalysis:
        """Analyze sentiment using AI (placeholder)"""
        # Would implement actual AI sentiment analysis here
        return self._analyze_sentiment_with_rules(content)