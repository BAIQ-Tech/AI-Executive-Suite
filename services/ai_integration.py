"""
AI Integration Service

Handles all AI model interactions and provides intelligent responses
for the AI Executive Suite.
"""

import logging
import time
import json
import asyncio
from typing import List, Dict, Optional, Any, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import tiktoken
import openai
from openai import OpenAI, AsyncOpenAI
from openai.types.chat import ChatCompletion
import backoff

logger = logging.getLogger(__name__)


class ExecutiveType(Enum):
    """Types of AI executives"""
    CEO = "ceo"
    CTO = "cto"
    CFO = "cfo"


@dataclass
class TokenUsage:
    """Token usage tracking"""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    estimated_cost: float


@dataclass
class AIResponse:
    """Base AI response with metadata"""
    content: str
    model: str
    token_usage: TokenUsage
    response_time: float
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutiveResponse(AIResponse):
    """Response from an AI executive"""
    decision: str
    rationale: str
    confidence_score: float
    priority: str
    category: str
    financial_impact: Optional[float] = None
    risk_level: str = "medium"
    executive_type: str = ""


@dataclass
class DocumentInsights(AIResponse):
    """Insights extracted from documents"""
    summary: str
    key_points: List[str]
    recommendations: List[str]
    confidence_score: float


@dataclass
class PatternAnalysis(AIResponse):
    """Analysis of decision patterns"""
    trends: Dict[str, Any]
    insights: List[str]
    recommendations: List[str]


@dataclass
class ConversationMessage:
    """Single conversation message"""
    role: str  # 'system', 'user', 'assistant'
    content: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConversationContext:
    """Conversation context with history"""
    messages: List[ConversationMessage]
    total_tokens: int = 0
    max_tokens: int = 4000
    
    def add_message(self, role: str, content: str, metadata: Dict[str, Any] = None):
        """Add a message to the conversation"""
        message = ConversationMessage(
            role=role,
            content=content,
            metadata=metadata or {}
        )
        self.messages.append(message)
    
    def to_openai_format(self) -> List[Dict[str, str]]:
        """Convert to OpenAI chat format"""
        return [
            {"role": msg.role, "content": msg.content}
            for msg in self.messages
        ]


class OpenAIError(Exception):
    """Custom OpenAI error"""
    pass


class TokenLimitError(OpenAIError):
    """Token limit exceeded error"""
    pass


class RateLimitError(OpenAIError):
    """Rate limit exceeded error"""
    pass


class OpenAIClient:
    """OpenAI API client with retry logic and error handling"""
    
    # Token pricing per 1K tokens (as of 2024)
    TOKEN_PRICING = {
        "gpt-4": {"input": 0.03, "output": 0.06},
        "gpt-4-turbo": {"input": 0.01, "output": 0.03},
        "gpt-3.5-turbo": {"input": 0.0015, "output": 0.002},
    }
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize OpenAI clients
        self.client = OpenAI(
            api_key=config.get('api_key'),
            timeout=config.get('timeout', 30)
        )
        self.async_client = AsyncOpenAI(
            api_key=config.get('api_key'),
            timeout=config.get('timeout', 30)
        )
        
        # Initialize tokenizer
        self.model = config.get('model', 'gpt-4')
        try:
            self.tokenizer = tiktoken.encoding_for_model(self.model)
        except KeyError:
            # Fallback to cl100k_base for newer models
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
        
        # Configuration
        self.max_tokens = config.get('max_tokens', 2000)
        self.temperature = config.get('temperature', 0.7)
        self.max_retries = config.get('max_retries', 3)
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        try:
            return len(self.tokenizer.encode(text))
        except Exception as e:
            self.logger.warning(f"Token counting failed: {e}")
            # Rough estimation: 1 token ≈ 4 characters
            return len(text) // 4
    
    def count_message_tokens(self, messages: List[Dict[str, str]]) -> int:
        """Count tokens in a list of messages"""
        total_tokens = 0
        for message in messages:
            # Add tokens for message content
            total_tokens += self.count_tokens(message.get('content', ''))
            # Add overhead tokens for message structure
            total_tokens += 4  # Overhead per message
        
        # Add overhead for the conversation
        total_tokens += 2
        return total_tokens
    
    def calculate_cost(self, prompt_tokens: int, completion_tokens: int, model: str = None) -> float:
        """Calculate estimated cost for token usage"""
        model = model or self.model
        pricing = self.TOKEN_PRICING.get(model, self.TOKEN_PRICING["gpt-4"])
        
        prompt_cost = (prompt_tokens / 1000) * pricing["input"]
        completion_cost = (completion_tokens / 1000) * pricing["output"]
        
        return prompt_cost + completion_cost
    
    @backoff.on_exception(
        backoff.expo,
        (openai.RateLimitError, openai.APITimeoutError, openai.InternalServerError),
        max_tries=3,
        max_time=60
    )
    def _make_request(self, messages: List[Dict[str, str]], **kwargs) -> ChatCompletion:
        """Make request to OpenAI with retry logic"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                **kwargs
            )
            return response
        except openai.RateLimitError as e:
            self.logger.warning(f"Rate limit exceeded: {e}")
            raise RateLimitError(f"Rate limit exceeded: {e}")
        except openai.APITimeoutError as e:
            self.logger.error(f"API timeout: {e}")
            raise OpenAIError(f"API timeout: {e}")
        except openai.AuthenticationError as e:
            self.logger.error(f"Authentication failed: {e}")
            raise OpenAIError(f"Authentication failed: {e}")
        except openai.BadRequestError as e:
            self.logger.error(f"Bad request: {e}")
            raise OpenAIError(f"Bad request: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            raise OpenAIError(f"Unexpected error: {e}")
    
    def generate_completion(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> AIResponse:
        """Generate completion with full tracking"""
        start_time = time.time()
        
        # Count input tokens
        prompt_tokens = self.count_message_tokens(messages)
        
        # Check token limits
        if prompt_tokens > (4096 - self.max_tokens):  # Leave room for completion
            raise TokenLimitError(f"Prompt too long: {prompt_tokens} tokens")
        
        try:
            # Make the request
            response = self._make_request(messages, **kwargs)
            
            # Calculate metrics
            response_time = time.time() - start_time
            completion_tokens = response.usage.completion_tokens
            total_tokens = response.usage.total_tokens
            estimated_cost = self.calculate_cost(prompt_tokens, completion_tokens)
            
            # Create token usage object
            token_usage = TokenUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                estimated_cost=estimated_cost
            )
            
            # Extract content
            content = response.choices[0].message.content
            
            return AIResponse(
                content=content,
                model=self.model,
                token_usage=token_usage,
                response_time=response_time,
                metadata={
                    'finish_reason': response.choices[0].finish_reason,
                    'response_id': response.id
                }
            )
            
        except Exception as e:
            self.logger.error(f"Failed to generate completion: {e}")
            raise
    
    async def generate_completion_async(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> AIResponse:
        """Async version of generate_completion"""
        start_time = time.time()
        
        # Count input tokens
        prompt_tokens = self.count_message_tokens(messages)
        
        # Check token limits
        if prompt_tokens > (4096 - self.max_tokens):
            raise TokenLimitError(f"Prompt too long: {prompt_tokens} tokens")
        
        try:
            # Make the async request
            response = await self.async_client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                **kwargs
            )
            
            # Calculate metrics
            response_time = time.time() - start_time
            completion_tokens = response.usage.completion_tokens
            total_tokens = response.usage.total_tokens
            estimated_cost = self.calculate_cost(prompt_tokens, completion_tokens)
            
            # Create token usage object
            token_usage = TokenUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                estimated_cost=estimated_cost
            )
            
            # Extract content
            content = response.choices[0].message.content
            
            return AIResponse(
                content=content,
                model=self.model,
                token_usage=token_usage,
                response_time=response_time,
                metadata={
                    'finish_reason': response.choices[0].finish_reason,
                    'response_id': response.id
                }
            )
            
        except Exception as e:
            self.logger.error(f"Failed to generate async completion: {e}")
            raise


class PromptTemplate:
    """Template for AI prompts with variable substitution"""
    
    def __init__(self, template: str, variables: List[str] = None):
        self.template = template
        self.variables = variables or []
    
    def format(self, **kwargs) -> str:
        """Format template with provided variables"""
        try:
            return self.template.format(**kwargs)
        except KeyError as e:
            raise ValueError(f"Missing required variable: {e}")
    
    def validate_variables(self, **kwargs) -> bool:
        """Validate that all required variables are provided"""
        missing = [var for var in self.variables if var not in kwargs]
        if missing:
            raise ValueError(f"Missing required variables: {missing}")
        return True


class PromptVersion:
    """Represents a versioned prompt template"""
    
    def __init__(self, template: PromptTemplate, version: str, description: str = ""):
        self.template = template
        self.version = version
        self.description = description
        self.created_at = datetime.utcnow()


class ABTestConfig:
    """Configuration for A/B testing prompts"""
    
    def __init__(
        self, 
        template_name: str,
        version_a: str,
        version_b: str,
        traffic_split: float = 0.5,
        success_metric: str = "confidence_score"
    ):
        self.template_name = template_name
        self.version_a = version_a
        self.version_b = version_b
        self.traffic_split = traffic_split  # Percentage of traffic to version B
        self.success_metric = success_metric
        self.created_at = datetime.utcnow()
        self.results = {"a": [], "b": []}  # Store test results


class PromptManager:
    """Manages prompt templates for different executive roles with versioning and A/B testing"""
    
    def __init__(self):
        self.templates = {}
        self.versions = {}  # template_name -> {version -> PromptVersion}
        self.active_versions = {}  # template_name -> version
        self.ab_tests = {}  # template_name -> ABTestConfig
        self._load_default_templates()
    
    def _load_default_templates(self):
        """Load default prompt templates with enhanced executive-specific prompts"""
        
        # Enhanced CEO System Prompt
        ceo_system_v1 = PromptTemplate(
            """You are an AI CEO with 20+ years of executive leadership experience across multiple industries. 
            You excel at strategic thinking, stakeholder management, and driving organizational transformation.
            
            Your core competencies include:
            
            STRATEGIC LEADERSHIP:
            - Long-term vision development and strategic planning (3-10 year horizons)
            - Market analysis and competitive positioning
            - Business model innovation and transformation
            - Mergers, acquisitions, and partnership strategies
            - International expansion and market entry strategies
            
            ORGANIZATIONAL EXCELLENCE:
            - Corporate culture development and change management
            - Executive team building and succession planning
            - Performance management and KPI development
            - Organizational design and operational efficiency
            - Crisis management and business continuity
            
            STAKEHOLDER MANAGEMENT:
            - Board relations and investor communications
            - Customer relationship strategies
            - Public relations and brand management
            - Regulatory compliance and government relations
            - ESG (Environmental, Social, Governance) initiatives
            
            DECISION-MAKING FRAMEWORK:
            1. Analyze the strategic context and business environment
            2. Consider multiple stakeholder perspectives
            3. Evaluate short-term vs. long-term trade-offs
            4. Assess risks and develop mitigation strategies
            5. Ensure alignment with company vision and values
            6. Consider resource allocation and opportunity costs
            7. Plan for implementation and change management
            
            Always provide decisions that are:
            - Strategically sound and data-driven
            - Aligned with long-term business objectives
            - Considerate of all stakeholder impacts
            - Implementable with clear next steps
            - Measurable with defined success metrics"""
        )
        
        # Enhanced CTO System Prompt
        cto_system_v1 = PromptTemplate(
            """You are an AI CTO with deep technical expertise and 15+ years of experience leading engineering organizations.
            You bridge the gap between business strategy and technical execution.
            
            Your core competencies include:
            
            TECHNICAL ARCHITECTURE:
            - System design and architectural patterns (microservices, serverless, distributed systems)
            - Technology stack evaluation and selection
            - Scalability planning and performance optimization
            - Security architecture and compliance frameworks
            - Cloud strategy and infrastructure planning
            
            ENGINEERING LEADERSHIP:
            - Engineering team structure and scaling strategies
            - Technical hiring and talent development
            - Engineering culture and best practices
            - Agile/DevOps methodology implementation
            - Technical debt management and refactoring strategies
            
            INNOVATION & TECHNOLOGY:
            - Emerging technology evaluation (AI/ML, blockchain, IoT, etc.)
            - R&D strategy and innovation processes
            - Technical product roadmap development
            - API strategy and platform development
            - Data architecture and analytics platforms
            
            BUSINESS-TECH ALIGNMENT:
            - Technology ROI analysis and business case development
            - Technical risk assessment and mitigation
            - Vendor evaluation and technology partnerships
            - Digital transformation strategy
            - Technical compliance and regulatory requirements
            
            DECISION-MAKING FRAMEWORK:
            1. Understand business requirements and constraints
            2. Evaluate technical alternatives and trade-offs
            3. Consider scalability, maintainability, and security
            4. Assess team capabilities and resource requirements
            5. Analyze cost implications and ROI
            6. Plan for implementation timeline and milestones
            7. Identify risks and develop contingency plans
            
            Always provide decisions that are:
            - Technically sound and architecturally robust
            - Aligned with business objectives and timelines
            - Scalable and maintainable long-term
            - Implementable with current team capabilities
            - Cost-effective with clear ROI justification"""
        )
        
        # Enhanced CFO System Prompt
        cfo_system_v1 = PromptTemplate(
            """You are an AI CFO with extensive financial expertise and 18+ years of experience in corporate finance.
            You provide strategic financial leadership and ensure fiscal responsibility across the organization.
            
            Your core competencies include:
            
            FINANCIAL PLANNING & ANALYSIS:
            - Strategic financial planning and budgeting (annual and multi-year)
            - Financial modeling and scenario analysis
            - Cash flow management and working capital optimization
            - Capital allocation and investment prioritization
            - Financial forecasting and variance analysis
            
            INVESTMENT & CAPITAL MANAGEMENT:
            - Investment evaluation using NPV, IRR, and payback analysis
            - Capital structure optimization and financing strategies
            - M&A financial due diligence and valuation
            - Risk management and hedging strategies
            - Treasury management and liquidity planning
            
            PERFORMANCE MANAGEMENT:
            - KPI development and financial metrics design
            - Profitability analysis by product, segment, and geography
            - Cost management and operational efficiency initiatives
            - Pricing strategy and margin optimization
            - Financial performance benchmarking
            
            COMPLIANCE & GOVERNANCE:
            - Financial reporting and regulatory compliance
            - Internal controls and audit management
            - Tax strategy and optimization
            - ESG reporting and sustainability metrics
            - Investor relations and stakeholder communications
            
            DECISION-MAKING FRAMEWORK:
            1. Analyze financial data and identify key trends
            2. Evaluate financial impact and ROI of alternatives
            3. Assess risks and develop sensitivity analysis
            4. Consider cash flow and liquidity implications
            5. Evaluate impact on financial ratios and covenants
            6. Benchmark against industry standards
            7. Ensure compliance with regulations and policies
            
            Always provide decisions that are:
            - Financially sound with quantitative backing
            - Risk-adjusted with clear sensitivity analysis
            - Aligned with company financial objectives
            - Compliant with regulatory requirements
            - Supported by industry benchmarks and best practices"""
        )
        
        # Enhanced Decision Prompt with Executive-Specific Formatting
        decision_prompt_v1 = PromptTemplate(
            """EXECUTIVE DECISION REQUEST

            Context: {context}

            {document_context}

            {conversation_history}

            As a {executive_type}, analyze this situation and provide your executive decision.

            REQUIRED ANALYSIS:
            1. SITUATION ASSESSMENT: Summarize the key issues and context
            2. STRATEGIC CONSIDERATIONS: Identify strategic implications and alignment
            3. OPTIONS ANALYSIS: Evaluate available alternatives with pros/cons
            4. RECOMMENDATION: Provide your clear decision with rationale
            5. IMPLEMENTATION: Outline key implementation steps and timeline
            6. RISK ASSESSMENT: Identify risks and mitigation strategies
            7. SUCCESS METRICS: Define how success will be measured

            FORMAT YOUR RESPONSE AS JSON:
            {{
                "situation_assessment": "Brief summary of the situation and key issues",
                "strategic_considerations": ["Strategic factor 1", "Strategic factor 2"],
                "options_analysis": [
                    {{"option": "Option 1", "pros": ["Pro 1", "Pro 2"], "cons": ["Con 1", "Con 2"]}},
                    {{"option": "Option 2", "pros": ["Pro 1", "Pro 2"], "cons": ["Con 1", "Con 2"]}}
                ],
                "decision": "Your clear executive decision",
                "rationale": "Detailed explanation of your reasoning and decision criteria",
                "implementation_steps": ["Step 1", "Step 2", "Step 3"],
                "timeline": "Expected implementation timeline",
                "confidence_score": 0.85,
                "priority": "high",
                "category": "strategic",
                "risk_level": "medium",
                "financial_impact": 50000,
                "risks": ["Risk 1", "Risk 2"],
                "mitigation_strategies": ["Strategy 1", "Strategy 2"],
                "success_metrics": ["Metric 1", "Metric 2"],
                "next_review_date": "2024-03-15"
            }}""",
            variables=["context", "executive_type"]
        )
        
        # Specialized prompts for different decision types
        strategic_decision_prompt = PromptTemplate(
            """STRATEGIC DECISION ANALYSIS

            Strategic Context: {context}
            
            {document_context}
            
            As a {executive_type}, you are making a strategic decision that will impact the organization's long-term direction.
            
            Consider these strategic frameworks:
            - Porter's Five Forces (competitive dynamics)
            - SWOT Analysis (strengths, weaknesses, opportunities, threats)
            - Blue Ocean Strategy (value innovation)
            - Resource-Based View (core competencies)
            - Stakeholder Theory (stakeholder impacts)
            
            Provide a comprehensive strategic analysis and recommendation.""",
            variables=["context", "executive_type"]
        )
        
        financial_decision_prompt = PromptTemplate(
            """FINANCIAL DECISION ANALYSIS

            Financial Context: {context}
            
            {document_context}
            
            As a CFO, analyze this financial decision using these frameworks:
            - NPV and IRR analysis
            - Payback period calculation
            - Risk-adjusted return analysis
            - Cash flow impact assessment
            - Financial ratio implications
            - Industry benchmark comparison
            
            Provide detailed financial analysis with quantitative backing.""",
            variables=["context"]
        )
        
        technical_decision_prompt = PromptTemplate(
            """TECHNICAL DECISION ANALYSIS

            Technical Context: {context}
            
            {document_context}
            
            As a CTO, evaluate this technical decision considering:
            - Technical architecture implications
            - Scalability and performance requirements
            - Security and compliance considerations
            - Team capabilities and resource requirements
            - Technology lifecycle and maintenance
            - Integration and compatibility factors
            
            Provide technical analysis with implementation considerations.""",
            variables=["context"]
        )
        
        # Store templates with versions
        self._add_template_version("ceo_system", ceo_system_v1, "1.0", "Enhanced CEO prompt with strategic frameworks")
        self._add_template_version("cto_system", cto_system_v1, "1.0", "Enhanced CTO prompt with technical leadership focus")
        self._add_template_version("cfo_system", cfo_system_v1, "1.0", "Enhanced CFO prompt with financial analysis frameworks")
        self._add_template_version("decision_prompt", decision_prompt_v1, "1.0", "Enhanced decision prompt with structured analysis")
        self._add_template_version("strategic_decision", strategic_decision_prompt, "1.0", "Strategic decision analysis prompt")
        self._add_template_version("financial_decision", financial_decision_prompt, "1.0", "Financial decision analysis prompt")
        self._add_template_version("technical_decision", technical_decision_prompt, "1.0", "Technical decision analysis prompt")
        
        # Set active versions
        for template_name in self.versions.keys():
            self.active_versions[template_name] = "1.0"
    
    def _add_template_version(self, name: str, template: PromptTemplate, version: str, description: str = ""):
        """Add a versioned template"""
        if name not in self.versions:
            self.versions[name] = {}
        
        prompt_version = PromptVersion(template, version, description)
        self.versions[name][version] = prompt_version
        
        # Also add to legacy templates dict for backward compatibility
        self.templates[name] = template
    
    def get_template(self, template_name: str, version: str = None) -> PromptTemplate:
        """Get a prompt template by name and optional version"""
        if version is None:
            version = self.active_versions.get(template_name)
        
        if template_name not in self.versions:
            raise ValueError(f"Template '{template_name}' not found")
        
        if version not in self.versions[template_name]:
            available_versions = list(self.versions[template_name].keys())
            raise ValueError(f"Version '{version}' not found for template '{template_name}'. Available versions: {available_versions}")
        
        return self.versions[template_name][version].template
    
    def add_template_version(self, name: str, template: PromptTemplate, version: str, description: str = ""):
        """Add a new version of a prompt template"""
        self._add_template_version(name, template, version, description)
    
    def set_active_version(self, template_name: str, version: str):
        """Set the active version for a template"""
        if template_name not in self.versions:
            raise ValueError(f"Template '{template_name}' not found")
        
        if version not in self.versions[template_name]:
            raise ValueError(f"Version '{version}' not found for template '{template_name}'")
        
        self.active_versions[template_name] = version
        # Update legacy templates dict
        self.templates[template_name] = self.versions[template_name][version].template
    
    def get_template_versions(self, template_name: str) -> List[Dict[str, Any]]:
        """Get all versions of a template"""
        if template_name not in self.versions:
            return []
        
        versions = []
        for version, prompt_version in self.versions[template_name].items():
            versions.append({
                "version": version,
                "description": prompt_version.description,
                "created_at": prompt_version.created_at.isoformat(),
                "is_active": version == self.active_versions.get(template_name)
            })
        
        return sorted(versions, key=lambda x: x["created_at"], reverse=True)
    
    def get_executive_system_prompt(self, executive_type: str, version: str = None) -> str:
        """Get system prompt for executive type"""
        template_name = f"{executive_type}_system"
        template = self.get_template(template_name, version)
        return template.format()
    
    def get_decision_prompt(
        self, 
        executive_type: str, 
        decision_type: str = "general",
        context: str = "",
        document_context: str = "",
        conversation_history: str = "",
        version: str = None
    ) -> str:
        """Get decision prompt based on executive type and decision type"""
        
        # Choose appropriate prompt template
        if decision_type == "strategic":
            template_name = "strategic_decision"
        elif decision_type == "financial":
            template_name = "financial_decision"
        elif decision_type == "technical":
            template_name = "technical_decision"
        else:
            template_name = "decision_prompt"
        
        template = self.get_template(template_name, version)
        
        # Format the template
        format_args = {
            "context": context,
            "document_context": document_context,
            "conversation_history": conversation_history
        }
        
        # Add executive_type if the template requires it
        if "executive_type" in template.variables:
            format_args["executive_type"] = executive_type.upper()
        
        return template.format(**format_args)
    
    def list_templates(self) -> List[str]:
        """List all available template names"""
        return list(self.versions.keys())
    
    def get_template_info(self, template_name: str) -> Dict[str, Any]:
        """Get information about a template"""
        if template_name not in self.versions:
            raise ValueError(f"Template '{template_name}' not found")
        
        versions = self.get_template_versions(template_name)
        active_version = self.active_versions.get(template_name)
        
        return {
            "name": template_name,
            "active_version": active_version,
            "total_versions": len(versions),
            "versions": versions,
            "ab_test_active": template_name in self.ab_tests
        }
    
    def start_ab_test(
        self, 
        template_name: str, 
        version_a: str, 
        version_b: str,
        traffic_split: float = 0.5,
        success_metric: str = "confidence_score"
    ):
        """Start an A/B test between two template versions"""
        if template_name not in self.versions:
            raise ValueError(f"Template '{template_name}' not found")
        
        if version_a not in self.versions[template_name]:
            raise ValueError(f"Version '{version_a}' not found for template '{template_name}'")
        
        if version_b not in self.versions[template_name]:
            raise ValueError(f"Version '{version_b}' not found for template '{template_name}'")
        
        if not 0 < traffic_split < 1:
            raise ValueError("Traffic split must be between 0 and 1")
        
        ab_config = ABTestConfig(
            template_name=template_name,
            version_a=version_a,
            version_b=version_b,
            traffic_split=traffic_split,
            success_metric=success_metric
        )
        
        self.ab_tests[template_name] = ab_config
        return ab_config
    
    def stop_ab_test(self, template_name: str) -> Dict[str, Any]:
        """Stop an A/B test and return results"""
        if template_name not in self.ab_tests:
            raise ValueError(f"No active A/B test for template '{template_name}'")
        
        ab_config = self.ab_tests[template_name]
        results = self._analyze_ab_test_results(ab_config)
        
        # Remove the A/B test
        del self.ab_tests[template_name]
        
        return results
    
    def get_template_for_ab_test(self, template_name: str, user_id: str = None) -> tuple[PromptTemplate, str]:
        """Get template version for A/B test based on user assignment"""
        if template_name not in self.ab_tests:
            # No A/B test active, return active version
            version = self.active_versions.get(template_name)
            template = self.get_template(template_name, version)
            return template, version
        
        ab_config = self.ab_tests[template_name]
        
        # Determine which version to use
        if user_id:
            # Use hash of user_id for consistent assignment
            import hashlib
            hash_value = int(hashlib.md5(user_id.encode()).hexdigest(), 16)
            use_version_b = (hash_value % 100) < (ab_config.traffic_split * 100)
        else:
            # Random assignment
            import random
            use_version_b = random.random() < ab_config.traffic_split
        
        version = ab_config.version_b if use_version_b else ab_config.version_a
        template = self.get_template(template_name, version)
        
        return template, version
    
    def record_ab_test_result(
        self, 
        template_name: str, 
        version: str, 
        result_data: Dict[str, Any]
    ):
        """Record result for A/B test analysis"""
        if template_name not in self.ab_tests:
            return  # No active test
        
        ab_config = self.ab_tests[template_name]
        
        if version == ab_config.version_a:
            ab_config.results["a"].append(result_data)
        elif version == ab_config.version_b:
            ab_config.results["b"].append(result_data)
    
    def _analyze_ab_test_results(self, ab_config: ABTestConfig) -> Dict[str, Any]:
        """Analyze A/B test results"""
        results_a = ab_config.results["a"]
        results_b = ab_config.results["b"]
        
        if not results_a or not results_b:
            return {
                "status": "insufficient_data",
                "version_a_count": len(results_a),
                "version_b_count": len(results_b)
            }
        
        # Calculate metrics
        metric = ab_config.success_metric
        
        values_a = [r.get(metric, 0) for r in results_a if metric in r]
        values_b = [r.get(metric, 0) for r in results_b if metric in r]
        
        if not values_a or not values_b:
            return {
                "status": "no_metric_data",
                "metric": metric,
                "version_a_count": len(results_a),
                "version_b_count": len(results_b)
            }
        
        avg_a = sum(values_a) / len(values_a)
        avg_b = sum(values_b) / len(values_b)
        
        improvement = ((avg_b - avg_a) / avg_a) * 100 if avg_a > 0 else 0
        
        # Simple statistical significance test (t-test approximation)
        import math
        n_a, n_b = len(values_a), len(values_b)
        var_a = sum((x - avg_a) ** 2 for x in values_a) / (n_a - 1) if n_a > 1 else 0
        var_b = sum((x - avg_b) ** 2 for x in values_b) / (n_b - 1) if n_b > 1 else 0
        
        pooled_se = math.sqrt(var_a / n_a + var_b / n_b) if var_a > 0 or var_b > 0 else 0
        t_stat = (avg_b - avg_a) / pooled_se if pooled_se > 0 else 0
        
        # Rough significance check (t > 1.96 for 95% confidence)
        is_significant = abs(t_stat) > 1.96
        
        return {
            "status": "complete",
            "template_name": ab_config.template_name,
            "version_a": ab_config.version_a,
            "version_b": ab_config.version_b,
            "metric": metric,
            "version_a_avg": avg_a,
            "version_b_avg": avg_b,
            "improvement_percent": improvement,
            "sample_size_a": n_a,
            "sample_size_b": n_b,
            "t_statistic": t_stat,
            "is_significant": is_significant,
            "winner": ab_config.version_b if avg_b > avg_a and is_significant else ab_config.version_a,
            "recommendation": "Deploy version B" if avg_b > avg_a and is_significant else "Keep version A"
        }
    
    def get_ab_test_status(self, template_name: str) -> Dict[str, Any]:
        """Get current status of A/B test"""
        if template_name not in self.ab_tests:
            return {"active": False}
        
        ab_config = self.ab_tests[template_name]
        
        return {
            "active": True,
            "template_name": template_name,
            "version_a": ab_config.version_a,
            "version_b": ab_config.version_b,
            "traffic_split": ab_config.traffic_split,
            "success_metric": ab_config.success_metric,
            "started_at": ab_config.created_at.isoformat(),
            "results_count_a": len(ab_config.results["a"]),
            "results_count_b": len(ab_config.results["b"])
        }


class ContextManager:
    """Manages conversation context and history"""
    
    def __init__(self, max_context_tokens: int = 4000, max_history_length: int = 20):
        self.max_context_tokens = max_context_tokens
        self.max_history_length = max_history_length
        self.contexts: Dict[str, ConversationContext] = {}
        self.logger = logging.getLogger(__name__)
    
    def get_or_create_context(self, context_id: str) -> ConversationContext:
        """Get existing context or create new one"""
        if context_id not in self.contexts:
            self.contexts[context_id] = ConversationContext(
                messages=[],
                max_tokens=self.max_context_tokens
            )
        return self.contexts[context_id]
    
    def add_message(
        self, 
        context_id: str, 
        role: str, 
        content: str, 
        metadata: Dict[str, Any] = None
    ) -> ConversationContext:
        """Add a message to the conversation context"""
        context = self.get_or_create_context(context_id)
        context.add_message(role, content, metadata)
        
        # Prune context if it gets too long
        self._prune_context(context)
        
        return context
    
    def get_context_messages(
        self, 
        context_id: str, 
        include_system: bool = True,
        max_messages: int = None
    ) -> List[Dict[str, str]]:
        """Get messages in OpenAI format"""
        if context_id not in self.contexts:
            return []
        
        context = self.contexts[context_id]
        messages = context.to_openai_format()
        
        if not include_system:
            messages = [msg for msg in messages if msg["role"] != "system"]
        
        if max_messages:
            # Keep system messages and limit user/assistant messages
            system_messages = [msg for msg in messages if msg["role"] == "system"]
            other_messages = [msg for msg in messages if msg["role"] != "system"]
            other_messages = other_messages[-max_messages:]
            messages = system_messages + other_messages
        
        return messages
    
    def clear_context(self, context_id: str):
        """Clear conversation context"""
        if context_id in self.contexts:
            del self.contexts[context_id]
    
    def get_context_summary(self, context_id: str) -> Dict[str, Any]:
        """Get summary of context state"""
        if context_id not in self.contexts:
            return {"exists": False}
        
        context = self.contexts[context_id]
        return {
            "exists": True,
            "message_count": len(context.messages),
            "total_tokens": context.total_tokens,
            "max_tokens": context.max_tokens,
            "last_message_time": context.messages[-1].timestamp.isoformat() if context.messages else None
        }
    
    def _prune_context(self, context: ConversationContext):
        """Prune context to stay within token limits"""
        if len(context.messages) <= 2:  # Keep at least system + one exchange
            return
        
        # Estimate tokens (rough calculation)
        total_estimated_tokens = sum(
            len(msg.content) // 4 for msg in context.messages  # ~4 chars per token
        )
        
        # If we're over the limit, remove older messages (but keep system messages)
        while (total_estimated_tokens > context.max_tokens and 
               len(context.messages) > 2):
            
            # Find first non-system message to remove
            for i, msg in enumerate(context.messages):
                if msg.role != "system":
                    removed_msg = context.messages.pop(i)
                    total_estimated_tokens -= len(removed_msg.content) // 4
                    self.logger.debug(f"Pruned message from context: {removed_msg.role}")
                    break
            else:
                # If only system messages left, break
                break
        
        # Also limit by message count
        if len(context.messages) > self.max_history_length:
            # Keep system messages and most recent exchanges
            system_messages = [msg for msg in context.messages if msg.role == "system"]
            other_messages = [msg for msg in context.messages if msg.role != "system"]
            
            # Keep most recent messages
            keep_count = self.max_history_length - len(system_messages)
            other_messages = other_messages[-keep_count:] if keep_count > 0 else []
            
            context.messages = system_messages + other_messages
            self.logger.debug(f"Pruned context to {len(context.messages)} messages")
        
        # Update token count
        context.total_tokens = total_estimated_tokens
    
    def inject_document_context(
        self, 
        context_id: str, 
        documents: List[str], 
        max_doc_length: int = 500
    ):
        """Inject document context into conversation"""
        if not documents:
            return
        
        # Truncate documents if too long
        truncated_docs = []
        for doc in documents[:3]:  # Limit to 3 documents
            if len(doc) > max_doc_length:
                truncated_docs.append(doc[:max_doc_length] + "...")
            else:
                truncated_docs.append(doc)
        
        doc_context = "\n\n--- Document Context ---\n" + "\n\n".join(
            f"Document {i+1}:\n{doc}" for i, doc in enumerate(truncated_docs)
        ) + "\n--- End Document Context ---\n"
        
        self.add_message(
            context_id, 
            "system", 
            doc_context, 
            {"type": "document_context", "doc_count": len(documents)}
        )


class AIIntegrationService:
    """Service for managing AI model interactions"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize OpenAI client
        openai_config = config.get('openai', {})
        self.openai_client = OpenAIClient(openai_config)
        
        # Initialize prompt manager
        self.prompt_manager = PromptManager()
        
        # Initialize context manager
        self.context_manager = ContextManager(
            max_context_tokens=openai_config.get('max_tokens', 4000),
            max_history_length=20
        )
        
        # Usage tracking
        self.total_tokens_used = 0
        self.total_cost = 0.0
        
    def generate_executive_response(
        self, 
        executive_type: str, 
        context: str, 
        conversation_history: List[Dict] = None,
        document_context: List[str] = None,
        options: List[str] = None,
        context_id: str = None
    ) -> ExecutiveResponse:
        """
        Generate intelligent response from AI executive
        
        Args:
            executive_type: Type of executive (ceo, cto, cfo)
            context: The context or question for the executive
            conversation_history: Previous conversation messages (deprecated, use context_id)
            document_context: Relevant document excerpts
            options: Available options to choose from
            context_id: ID for conversation context management
            
        Returns:
            ExecutiveResponse with decision and reasoning
        """
        self.logger.info(f"Generating {executive_type} response for context: {context[:100]}...")
        
        try:
            # Use context manager if context_id provided
            if context_id:
                # Add system prompt if this is a new context
                context_summary = self.context_manager.get_context_summary(context_id)
                if not context_summary["exists"]:
                    system_prompt = self.prompt_manager.get_executive_system_prompt(executive_type)
                    self.context_manager.add_message(
                        context_id, 
                        "system", 
                        system_prompt,
                        {"executive_type": executive_type}
                    )
                
                # Inject document context if provided
                if document_context:
                    self.context_manager.inject_document_context(context_id, document_context)
                
                # Add user message
                self.context_manager.add_message(context_id, "user", context)
                
                # Get messages for API call
                messages = self.context_manager.get_context_messages(context_id, max_messages=10)
            
            else:
                # Fallback to legacy approach
                messages = []
                
                # Add system prompt for the executive type
                system_prompt = self.prompt_manager.get_executive_system_prompt(executive_type)
                messages.append({"role": "system", "content": system_prompt})
                
                # Add conversation history if provided
                if conversation_history:
                    for msg in conversation_history[-5:]:  # Keep last 5 messages for context
                        messages.append({
                            "role": msg.get("role", "user"),
                            "content": msg.get("content", "")
                        })
                
                # Prepare document context string
                doc_context_str = ""
                if document_context:
                    doc_context_str = "\n\nRelevant Documents:\n" + "\n".join(
                        f"- {doc}" for doc in document_context[:3]  # Limit to 3 documents
                    )
                
                # Prepare conversation history string
                conv_history_str = ""
                if conversation_history:
                    conv_history_str = "\n\nPrevious Conversation:\n" + "\n".join(
                        f"{msg.get('role', 'user')}: {msg.get('content', '')}"
                        for msg in conversation_history[-3:]  # Last 3 exchanges
                    )
                
                # Format the decision prompt using enhanced prompt system
                decision_prompt = self.prompt_manager.get_decision_prompt(
                    executive_type=executive_type,
                    decision_type="general",  # Could be determined from context
                    context=context,
                    document_context=doc_context_str,
                    conversation_history=conv_history_str
                )
                
                messages.append({"role": "user", "content": decision_prompt})
            
            # Generate response using OpenAI
            ai_response = self.openai_client.generate_completion(messages)
            
            # Add assistant response to context if using context manager
            if context_id:
                self.context_manager.add_message(
                    context_id, 
                    "assistant", 
                    ai_response.content,
                    {
                        "executive_type": executive_type,
                        "token_usage": ai_response.token_usage.__dict__,
                        "response_time": ai_response.response_time
                    }
                )
            
            # Update usage tracking
            self.total_tokens_used += ai_response.token_usage.total_tokens
            self.total_cost += ai_response.token_usage.estimated_cost
            
            # Parse the JSON response
            try:
                response_data = json.loads(ai_response.content)
            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                self.logger.warning("Failed to parse JSON response, using fallback")
                response_data = {
                    "decision": ai_response.content[:200] + "..." if len(ai_response.content) > 200 else ai_response.content,
                    "rationale": "AI provided detailed analysis",
                    "confidence_score": 0.7,
                    "priority": "medium",
                    "category": "general",
                    "risk_level": "medium"
                }
            
            # Create ExecutiveResponse
            executive_response = ExecutiveResponse(
                content=ai_response.content,
                model=ai_response.model,
                token_usage=ai_response.token_usage,
                response_time=ai_response.response_time,
                timestamp=ai_response.timestamp,
                metadata=ai_response.metadata,
                decision=response_data.get("decision", "No decision provided"),
                rationale=response_data.get("rationale", "No rationale provided"),
                confidence_score=float(response_data.get("confidence_score", 0.7)),
                priority=response_data.get("priority", "medium"),
                category=response_data.get("category", "general"),
                financial_impact=response_data.get("financial_impact"),
                risk_level=response_data.get("risk_level", "medium"),
                executive_type=executive_type
            )
            
            # Add context information to metadata
            if context_id:
                context_summary = self.context_manager.get_context_summary(context_id)
                executive_response.metadata.update({
                    "context_id": context_id,
                    "context_summary": context_summary
                })
            
            return executive_response
            
        except Exception as e:
            self.logger.error(f"Failed to generate executive response: {e}")
            # Return a fallback response
            return ExecutiveResponse(
                content=f"Error generating response: {str(e)}",
                model=self.openai_client.model,
                token_usage=TokenUsage(0, 0, 0, 0.0),
                response_time=0.0,
                decision="Unable to generate decision due to technical error",
                rationale="Please try again or contact support",
                confidence_score=0.0,
                priority="low",
                category="error",
                risk_level="high",
                executive_type=executive_type,
                metadata={"error": str(e)}
            )
    
    def get_document_insights(
        self, 
        document_id: str, 
        query: str
    ) -> DocumentInsights:
        """
        Extract insights from a document based on a query
        
        Args:
            document_id: ID of the document to analyze
            query: Specific question or area of interest
            
        Returns:
            DocumentInsights with summary and key points
        """
        self.logger.info(f"Extracting insights from document {document_id}")
        
        try:
            # This would typically fetch document content from storage
            # For now, we'll use a placeholder implementation
            document_content = f"Document {document_id} content would be loaded here"
            
            # Build messages for document analysis
            messages = [
                {
                    "role": "system",
                    "content": """You are an expert document analyst. Analyze the provided document 
                    and extract key insights based on the user's query. Provide a comprehensive summary,
                    key points, and actionable recommendations."""
                },
                {
                    "role": "user",
                    "content": f"""Document Content:
{document_content}

Query: {query}

Please analyze this document and provide:
1. A comprehensive summary
2. Key points relevant to the query
3. Actionable recommendations
4. Confidence level in your analysis

Format your response as JSON:
{{
    "summary": "Comprehensive summary here",
    "key_points": ["Point 1", "Point 2", "Point 3"],
    "recommendations": ["Recommendation 1", "Recommendation 2"],
    "confidence_score": 0.85
}}"""
                }
            ]
            
            # Generate insights using OpenAI
            ai_response = self.openai_client.generate_completion(messages)
            
            # Update usage tracking
            self.total_tokens_used += ai_response.token_usage.total_tokens
            self.total_cost += ai_response.token_usage.estimated_cost
            
            # Parse the JSON response
            try:
                insights_data = json.loads(ai_response.content)
            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                insights_data = {
                    "summary": ai_response.content[:300] + "..." if len(ai_response.content) > 300 else ai_response.content,
                    "key_points": ["Analysis provided by AI"],
                    "recommendations": ["Review document for specific insights"],
                    "confidence_score": 0.6
                }
            
            return DocumentInsights(
                content=ai_response.content,
                model=ai_response.model,
                token_usage=ai_response.token_usage,
                response_time=ai_response.response_time,
                timestamp=ai_response.timestamp,
                metadata=ai_response.metadata,
                summary=insights_data.get("summary", "No summary available"),
                key_points=insights_data.get("key_points", []),
                recommendations=insights_data.get("recommendations", []),
                confidence_score=float(insights_data.get("confidence_score", 0.7))
            )
            
        except Exception as e:
            self.logger.error(f"Failed to extract document insights: {e}")
            # Return fallback insights
            return DocumentInsights(
                content=f"Error analyzing document: {str(e)}",
                model=self.openai_client.model,
                token_usage=TokenUsage(0, 0, 0, 0.0),
                response_time=0.0,
                summary="Unable to analyze document due to technical error",
                key_points=["Error occurred during analysis"],
                recommendations=["Please try again or contact support"],
                confidence_score=0.0,
                metadata={"error": str(e)}
            )
    
    def analyze_decision_patterns(
        self, 
        decisions: List[Dict]
    ) -> PatternAnalysis:
        """
        Analyze patterns in historical decisions
        
        Args:
            decisions: List of historical decisions
            
        Returns:
            PatternAnalysis with trends and insights
        """
        self.logger.info(f"Analyzing patterns in {len(decisions)} decisions")
        
        try:
            # Prepare decision data for analysis
            decision_summary = []
            for decision in decisions[-20:]:  # Analyze last 20 decisions
                summary = {
                    "type": decision.get("executive_type", "unknown"),
                    "category": decision.get("category", "general"),
                    "priority": decision.get("priority", "medium"),
                    "confidence": decision.get("confidence_score", 0.5),
                    "outcome": decision.get("outcome_rating", "unknown")
                }
                decision_summary.append(summary)
            
            # Build messages for pattern analysis
            messages = [
                {
                    "role": "system",
                    "content": """You are an expert business analyst specializing in decision pattern analysis.
                    Analyze the provided decision data to identify trends, patterns, and insights that can
                    improve future decision-making processes."""
                },
                {
                    "role": "user",
                    "content": f"""Decision Data:
{json.dumps(decision_summary, indent=2)}

Please analyze these decisions and provide:
1. Key trends and patterns
2. Insights about decision-making effectiveness
3. Recommendations for improvement

Format your response as JSON:
{{
    "trends": {{
        "decision_frequency": "trend description",
        "confidence_patterns": "pattern description",
        "category_distribution": "distribution analysis"
    }},
    "insights": ["Insight 1", "Insight 2", "Insight 3"],
    "recommendations": ["Recommendation 1", "Recommendation 2"]
}}"""
                }
            ]
            
            # Generate analysis using OpenAI
            ai_response = self.openai_client.generate_completion(messages)
            
            # Update usage tracking
            self.total_tokens_used += ai_response.token_usage.total_tokens
            self.total_cost += ai_response.token_usage.estimated_cost
            
            # Parse the JSON response
            try:
                analysis_data = json.loads(ai_response.content)
            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                analysis_data = {
                    "trends": {"general": "Analysis provided by AI"},
                    "insights": ["Pattern analysis completed"],
                    "recommendations": ["Review decision patterns regularly"]
                }
            
            return PatternAnalysis(
                content=ai_response.content,
                model=ai_response.model,
                token_usage=ai_response.token_usage,
                response_time=ai_response.response_time,
                timestamp=ai_response.timestamp,
                metadata=ai_response.metadata,
                trends=analysis_data.get("trends", {}),
                insights=analysis_data.get("insights", []),
                recommendations=analysis_data.get("recommendations", [])
            )
            
        except Exception as e:
            self.logger.error(f"Failed to analyze decision patterns: {e}")
            # Return fallback analysis
            return PatternAnalysis(
                content=f"Error analyzing patterns: {str(e)}",
                model=self.openai_client.model,
                token_usage=TokenUsage(0, 0, 0, 0.0),
                response_time=0.0,
                trends={"error": "Analysis failed"},
                insights=["Unable to analyze patterns due to technical error"],
                recommendations=["Please try again or contact support"],
                metadata={"error": str(e)}
            )
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get usage statistics for the AI service"""
        return {
            "total_tokens_used": self.total_tokens_used,
            "total_cost": self.total_cost,
            "model": self.openai_client.model,
            "active_contexts": len(self.context_manager.contexts),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def get_conversation_context(self, context_id: str) -> Dict[str, Any]:
        """Get conversation context summary"""
        return self.context_manager.get_context_summary(context_id)
    
    def clear_conversation_context(self, context_id: str):
        """Clear a conversation context"""
        self.context_manager.clear_context(context_id)
        self.logger.info(f"Cleared conversation context: {context_id}")
    
    def get_conversation_history(
        self, 
        context_id: str, 
        include_system: bool = False,
        max_messages: int = None
    ) -> List[Dict[str, Any]]:
        """Get conversation history for a context"""
        if context_id not in self.context_manager.contexts:
            return []
        
        context = self.context_manager.contexts[context_id]
        history = []
        
        for msg in context.messages:
            if not include_system and msg.role == "system":
                continue
            
            history.append({
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat(),
                "metadata": msg.metadata
            })
        
        if max_messages:
            history = history[-max_messages:]
        
        return history
    
    def inject_context_documents(
        self, 
        context_id: str, 
        documents: List[str]
    ):
        """Inject document context into a conversation"""
        self.context_manager.inject_document_context(context_id, documents)
        self.logger.info(f"Injected {len(documents)} documents into context {context_id}")
    
    def prune_old_contexts(self, max_age_hours: int = 24):
        """Remove old conversation contexts"""
        cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
        contexts_to_remove = []
        
        for context_id, context in self.context_manager.contexts.items():
            if context.messages:
                last_message_time = context.messages[-1].timestamp
                if last_message_time < cutoff_time:
                    contexts_to_remove.append(context_id)
        
        for context_id in contexts_to_remove:
            self.context_manager.clear_context(context_id)
        
        self.logger.info(f"Pruned {len(contexts_to_remove)} old contexts")
        return len(contexts_to_remove)
    
    # Prompt Management Methods
    
    def get_available_prompts(self) -> List[str]:
        """Get list of available prompt templates"""
        return self.prompt_manager.list_templates()
    
    def get_prompt_info(self, template_name: str) -> Dict[str, Any]:
        """Get information about a prompt template"""
        return self.prompt_manager.get_template_info(template_name)
    
    def add_prompt_version(
        self, 
        template_name: str, 
        template_content: str, 
        version: str,
        variables: List[str] = None,
        description: str = ""
    ):
        """Add a new version of a prompt template"""
        template = PromptTemplate(template_content, variables or [])
        self.prompt_manager.add_template_version(template_name, template, version, description)
        self.logger.info(f"Added prompt version {version} for template {template_name}")
    
    def set_active_prompt_version(self, template_name: str, version: str):
        """Set the active version for a prompt template"""
        self.prompt_manager.set_active_version(template_name, version)
        self.logger.info(f"Set active version {version} for template {template_name}")
    
    def start_prompt_ab_test(
        self, 
        template_name: str, 
        version_a: str, 
        version_b: str,
        traffic_split: float = 0.5,
        success_metric: str = "confidence_score"
    ) -> Dict[str, Any]:
        """Start an A/B test for prompt templates"""
        ab_config = self.prompt_manager.start_ab_test(
            template_name, version_a, version_b, traffic_split, success_metric
        )
        
        self.logger.info(f"Started A/B test for {template_name}: {version_a} vs {version_b}")
        
        return {
            "template_name": template_name,
            "version_a": version_a,
            "version_b": version_b,
            "traffic_split": traffic_split,
            "success_metric": success_metric,
            "started_at": ab_config.created_at.isoformat()
        }
    
    def stop_prompt_ab_test(self, template_name: str) -> Dict[str, Any]:
        """Stop an A/B test and get results"""
        results = self.prompt_manager.stop_ab_test(template_name)
        self.logger.info(f"Stopped A/B test for {template_name}")
        return results
    
    def get_prompt_ab_test_status(self, template_name: str) -> Dict[str, Any]:
        """Get status of A/B test for a prompt"""
        return self.prompt_manager.get_ab_test_status(template_name)
    
    def generate_executive_response(
        self, 
        executive_type: str, 
        context: str, 
        conversation_history: List[Dict] = None,
        document_context: str = "",
        options: List[str] = None,
        context_id: str = None
    ) -> ExecutiveResponse:
        """
        Generate an executive response using AI with role-specific prompts
        
        Args:
            executive_type: Type of executive ('ceo', 'cto', 'cfo')
            context: Business context or problem statement
            conversation_history: Previous conversation messages
            document_context: Relevant document content
            options: Optional list of decision options
            context_id: Optional context ID for conversation tracking
            
        Returns:
            ExecutiveResponse with decision, rationale, and metadata
        """
        self.logger.info(f"Generating {executive_type} response for context: {context[:100]}...")
        
        try:
            # Get executive-specific system prompt
            system_prompt = self.prompt_manager.get_executive_system_prompt(executive_type)
            
            # Prepare document context section
            doc_context_section = ""
            if document_context:
                doc_context_section = f"\n\nRELEVANT DOCUMENTS:\n{document_context}"
            
            # Prepare conversation history section
            history_section = ""
            if conversation_history:
                history_section = "\n\nCONVERSATION HISTORY:\n"
                for msg in conversation_history[-6:]:  # Last 6 messages
                    role = msg.get('role', 'unknown')
                    content = msg.get('content', '')
                    history_section += f"{role.upper()}: {content}\n"
            
            # Prepare options section
            options_section = ""
            if options:
                options_section = f"\n\nAVAILABLE OPTIONS:\n"
                for i, option in enumerate(options, 1):
                    options_section += f"{i}. {option}\n"
            
            # Get decision prompt template
            decision_prompt = self.prompt_manager.get_decision_prompt(
                executive_type=executive_type,
                context=context,
                document_context=doc_context_section,
                conversation_history=history_section
            )
            
            # Add options to the prompt if provided
            if options_section:
                decision_prompt += options_section
            
            # Build messages for OpenAI
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": decision_prompt}
            ]
            
            # Generate AI response
            ai_response = self.openai_client.generate_completion(messages)
            
            # Update usage tracking
            self.total_tokens_used += ai_response.token_usage.total_tokens
            self.total_cost += ai_response.token_usage.estimated_cost
            
            # Parse the JSON response
            try:
                response_data = json.loads(ai_response.content)
            except json.JSONDecodeError:
                # Fallback parsing if JSON is malformed
                self.logger.warning("Failed to parse JSON response, using fallback parsing")
                response_data = self._parse_fallback_response(ai_response.content, executive_type)
            
            # Extract executive response components
            decision = response_data.get("decision", "Proceed with the recommended approach.")
            rationale = response_data.get("rationale", "Based on comprehensive analysis of the situation.")
            confidence_score = float(response_data.get("confidence_score", 0.7))
            priority = response_data.get("priority", "medium")
            category = response_data.get("category", "strategic")
            financial_impact = response_data.get("financial_impact")
            risk_level = response_data.get("risk_level", "medium")
            
            # Ensure confidence score is within valid range
            confidence_score = max(0.0, min(1.0, confidence_score))
            
            # Update conversation context if context_id provided
            if context_id:
                self.context_manager.add_message(
                    context_id, "user", context
                )
                self.context_manager.add_message(
                    context_id, "assistant", decision
                )
            
            return ExecutiveResponse(
                content=ai_response.content,
                model=ai_response.model,
                token_usage=ai_response.token_usage,
                response_time=ai_response.response_time,
                timestamp=ai_response.timestamp,
                metadata=ai_response.metadata,
                decision=decision,
                rationale=rationale,
                confidence_score=confidence_score,
                priority=priority,
                category=category,
                financial_impact=financial_impact,
                risk_level=risk_level,
                executive_type=executive_type
            )
            
        except Exception as e:
            self.logger.error(f"Failed to generate {executive_type} response: {e}")
            # Return fallback response
            return self._create_fallback_executive_response(executive_type, context, str(e))
    
    def _parse_fallback_response(self, content: str, executive_type: str) -> Dict[str, Any]:
        """Parse response when JSON parsing fails"""
        # Simple fallback parsing
        lines = content.split('\n')
        
        decision = "Proceed with the recommended approach based on the analysis."
        rationale = "Based on comprehensive evaluation of the situation and available options."
        
        # Try to extract decision and rationale from content
        for line in lines:
            if line.strip().lower().startswith('decision:'):
                decision = line.split(':', 1)[1].strip()
            elif line.strip().lower().startswith('rationale:'):
                rationale = line.split(':', 1)[1].strip()
        
        return {
            "decision": decision,
            "rationale": rationale,
            "confidence_score": 0.7,
            "priority": "medium",
            "category": "strategic" if executive_type == "ceo" else "operational",
            "risk_level": "medium"
        }
    
    def _create_fallback_executive_response(
        self, 
        executive_type: str, 
        context: str, 
        error: str
    ) -> ExecutiveResponse:
        """Create a fallback response when AI generation fails"""
        
        fallback_decisions = {
            "ceo": "Proceed with strategic analysis and stakeholder consultation before making final decision.",
            "cto": "Conduct technical feasibility study and architecture review before implementation.",
            "cfo": "Perform detailed financial analysis and risk assessment before proceeding."
        }
        
        fallback_rationales = {
            "ceo": "This approach ensures all strategic considerations are evaluated and stakeholder alignment is achieved.",
            "cto": "Technical due diligence is essential to ensure scalable and maintainable solutions.",
            "cfo": "Financial prudence requires thorough analysis of costs, benefits, and risks."
        }
        
        decision = fallback_decisions.get(executive_type, "Proceed with careful analysis and consultation.")
        rationale = fallback_rationales.get(executive_type, "This approach ensures thorough evaluation before action.")
        
        return ExecutiveResponse(
            content=f"Fallback response due to error: {error}",
            model=self.openai_client.model,
            token_usage=TokenUsage(0, 0, 0, 0.0),
            response_time=0.0,
            decision=decision,
            rationale=rationale,
            confidence_score=0.5,
            priority="medium",
            category="strategic",
            financial_impact=None,
            risk_level="medium",
            executive_type=executive_type,
            metadata={"fallback": True, "error": error}
        )

    def generate_executive_response_with_ab_test(
        self, 
        executive_type: str, 
        context: str, 
        user_id: str = None,
        document_context: List[str] = None,
        context_id: str = None
    ) -> ExecutiveResponse:
        """Generate response using A/B tested prompts"""
        
        # This is a specialized version that tracks A/B test results
        # For now, we'll use the regular method and add A/B test tracking
        response = self.generate_executive_response(
            executive_type=executive_type,
            context=context,
            document_context=document_context,
            context_id=context_id
        )
        
        # Record A/B test result if there's an active test
        decision_template_name = "decision_prompt"
        if decision_template_name in self.prompt_manager.ab_tests:
            # We would need to track which version was used
            # This is a simplified implementation
            result_data = {
                "confidence_score": response.confidence_score,
                "response_time": response.response_time,
                "user_id": user_id,
                "timestamp": response.timestamp.isoformat()
            }
            
            # For now, we'll assume we can determine the version used
            # In a full implementation, this would be tracked during generation
            version_used = self.prompt_manager.active_versions.get(decision_template_name, "1.0")
            self.prompt_manager.record_ab_test_result(
                decision_template_name, version_used, result_data
            )
        
        return response