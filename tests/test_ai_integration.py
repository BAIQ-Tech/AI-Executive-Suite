"""
Unit tests for AI Integration Service
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from dataclasses import asdict

from services.ai_integration import (
    AIIntegrationService,
    OpenAIClient,
    PromptManager,
    PromptTemplate,
    ExecutiveResponse,
    DocumentInsights,
    PatternAnalysis,
    TokenUsage,
    AIResponse,
    ConversationContext,
    ConversationMessage,
    OpenAIError,
    TokenLimitError,
    RateLimitError
)


class TestTokenUsage:
    """Test TokenUsage dataclass"""
    
    def test_token_usage_creation(self):
        usage = TokenUsage(
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150,
            estimated_cost=0.005
        )
        
        assert usage.prompt_tokens == 100
        assert usage.completion_tokens == 50
        assert usage.total_tokens == 150
        assert usage.estimated_cost == 0.005


class TestConversationContext:
    """Test ConversationContext functionality"""
    
    def test_conversation_context_creation(self):
        context = ConversationContext(messages=[], max_tokens=4000)
        assert len(context.messages) == 0
        assert context.max_tokens == 4000
        assert context.total_tokens == 0
    
    def test_add_message(self):
        context = ConversationContext(messages=[])
        context.add_message("user", "Hello", {"test": True})
        
        assert len(context.messages) == 1
        assert context.messages[0].role == "user"
        assert context.messages[0].content == "Hello"
        assert context.messages[0].metadata == {"test": True}
    
    def test_to_openai_format(self):
        context = ConversationContext(messages=[])
        context.add_message("user", "Hello")
        context.add_message("assistant", "Hi there")
        
        openai_format = context.to_openai_format()
        expected = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there"}
        ]
        
        assert openai_format == expected


class TestPromptTemplate:
    """Test PromptTemplate functionality"""
    
    def test_prompt_template_creation(self):
        template = PromptTemplate("Hello {name}", ["name"])
        assert template.template == "Hello {name}"
        assert template.variables == ["name"]
    
    def test_format_template(self):
        template = PromptTemplate("Hello {name}, you are {age} years old")
        result = template.format(name="Alice", age=30)
        assert result == "Hello Alice, you are 30 years old"
    
    def test_format_missing_variable(self):
        template = PromptTemplate("Hello {name}", ["name"])
        with pytest.raises(ValueError, match="Missing required variable"):
            template.format()
    
    def test_validate_variables(self):
        template = PromptTemplate("Hello {name}", ["name"])
        
        # Should pass with required variable
        assert template.validate_variables(name="Alice") is True
        
        # Should fail without required variable
        with pytest.raises(ValueError, match="Missing required variables"):
            template.validate_variables()


class TestPromptManager:
    """Test PromptManager functionality"""
    
    def test_prompt_manager_initialization(self):
        manager = PromptManager()
        
        # Check that default templates are loaded
        assert "ceo_system" in manager.templates
        assert "cto_system" in manager.templates
        assert "cfo_system" in manager.templates
        assert "decision_prompt" in manager.templates
    
    def test_get_template(self):
        manager = PromptManager()
        template = manager.get_template("ceo_system")
        assert isinstance(template, PromptTemplate)
    
    def test_get_nonexistent_template(self):
        manager = PromptManager()
        with pytest.raises(ValueError, match="Template 'nonexistent' not found"):
            manager.get_template("nonexistent")
    
    def test_add_template(self):
        manager = PromptManager()
        new_template = PromptTemplate("Test template")
        manager.add_template("test", new_template)
        
        retrieved = manager.get_template("test")
        assert retrieved == new_template
    
    def test_get_executive_system_prompt(self):
        manager = PromptManager()
        
        # Test valid executive types
        ceo_prompt = manager.get_executive_system_prompt("ceo")
        assert "CEO" in ceo_prompt
        
        cto_prompt = manager.get_executive_system_prompt("cto")
        assert "CTO" in cto_prompt
        
        cfo_prompt = manager.get_executive_system_prompt("cfo")
        assert "CFO" in cfo_prompt
    
    def test_get_invalid_executive_system_prompt(self):
        manager = PromptManager()
        with pytest.raises(ValueError, match="No system prompt for executive type"):
            manager.get_executive_system_prompt("invalid")


class TestOpenAIClient:
    """Test OpenAIClient functionality"""
    
    @pytest.fixture
    def mock_config(self):
        return {
            'api_key': 'test-key',
            'model': 'gpt-4',
            'max_tokens': 2000,
            'temperature': 0.7,
            'timeout': 30,
            'max_retries': 3
        }
    
    @pytest.fixture
    def client(self, mock_config):
        with patch('services.ai_integration.OpenAI'), \
             patch('services.ai_integration.AsyncOpenAI'), \
             patch('services.ai_integration.tiktoken.encoding_for_model') as mock_tiktoken:
            
            mock_encoder = Mock()
            mock_encoder.encode.return_value = [1, 2, 3, 4, 5]  # 5 tokens
            mock_tiktoken.return_value = mock_encoder
            
            return OpenAIClient(mock_config)
    
    def test_client_initialization(self, client):
        assert client.model == 'gpt-4'
        assert client.max_tokens == 2000
        assert client.temperature == 0.7
        assert client.max_retries == 3
    
    def test_count_tokens(self, client):
        tokens = client.count_tokens("Hello world")
        assert tokens == 5  # Mocked to return 5 tokens
    
    def test_count_message_tokens(self, client):
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there"}
        ]
        tokens = client.count_message_tokens(messages)
        # 5 tokens per message + 4 overhead per message + 2 conversation overhead
        assert tokens == (5 + 4) * 2 + 2
    
    def test_calculate_cost(self, client):
        cost = client.calculate_cost(100, 50, "gpt-4")
        expected = (100 / 1000) * 0.03 + (50 / 1000) * 0.06  # GPT-4 pricing
        assert cost == expected
    
    @patch('services.ai_integration.time.time')
    def test_generate_completion_success(self, mock_time, client):
        # Mock time for response time calculation
        mock_time.side_effect = [0, 1.5]  # Start and end times
        
        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Test response"
        mock_response.choices[0].finish_reason = "stop"
        mock_response.usage.completion_tokens = 50
        mock_response.usage.total_tokens = 150
        mock_response.id = "test-id"
        
        client.client.chat.completions.create = Mock(return_value=mock_response)
        
        messages = [{"role": "user", "content": "Hello"}]
        response = client.generate_completion(messages)
        
        assert isinstance(response, AIResponse)
        assert response.content == "Test response"
        assert response.response_time == 1.5
        assert response.token_usage.completion_tokens == 50
        assert response.token_usage.total_tokens == 150
    
    def test_generate_completion_token_limit_error(self, client):
        # Create a message that would exceed token limits
        long_messages = [{"role": "user", "content": "x" * 10000}]
        
        with pytest.raises(TokenLimitError):
            client.generate_completion(long_messages)
    
    def test_generate_completion_openai_error(self, client):
        import openai
        
        # Mock OpenAI to raise an error
        client.client.chat.completions.create = Mock(
            side_effect=openai.AuthenticationError("Invalid API key", response=Mock(), body=None)
        )
        
        messages = [{"role": "user", "content": "Hello"}]
        
        with pytest.raises(OpenAIError, match="Authentication failed"):
            client.generate_completion(messages)


class TestAIIntegrationService:
    """Test AIIntegrationService functionality"""
    
    @pytest.fixture
    def mock_config(self):
        return {
            'openai': {
                'api_key': 'test-key',
                'model': 'gpt-4',
                'max_tokens': 2000,
                'temperature': 0.7
            }
        }
    
    @pytest.fixture
    def service(self, mock_config):
        with patch('services.ai_integration.OpenAIClient') as mock_client_class:
            mock_client = Mock()
            mock_client.model = 'gpt-4'
            mock_client_class.return_value = mock_client
            
            return AIIntegrationService(mock_config)
    
    def test_service_initialization(self, service):
        assert service.total_tokens_used == 0
        assert service.total_cost == 0.0
        assert isinstance(service.prompt_manager, PromptManager)
    
    def test_generate_executive_response_success(self, service):
        # Mock successful AI response
        mock_ai_response = AIResponse(
            content='{"decision": "Test decision", "rationale": "Test rationale", "confidence_score": 0.8, "priority": "high", "category": "strategic", "risk_level": "low"}',
            model='gpt-4',
            token_usage=TokenUsage(100, 50, 150, 0.005),
            response_time=1.5
        )
        
        service.openai_client.generate_completion = Mock(return_value=mock_ai_response)
        
        response = service.generate_executive_response(
            executive_type="ceo",
            context="Should we expand to new markets?"
        )
        
        assert isinstance(response, ExecutiveResponse)
        assert response.decision == "Test decision"
        assert response.rationale == "Test rationale"
        assert response.confidence_score == 0.8
        assert response.priority == "high"
        assert response.category == "strategic"
        assert response.executive_type == "ceo"
    
    def test_generate_executive_response_json_parse_error(self, service):
        # Mock AI response with invalid JSON
        mock_ai_response = AIResponse(
            content='Invalid JSON response',
            model='gpt-4',
            token_usage=TokenUsage(100, 50, 150, 0.005),
            response_time=1.5
        )
        
        service.openai_client.generate_completion = Mock(return_value=mock_ai_response)
        
        response = service.generate_executive_response(
            executive_type="ceo",
            context="Test context"
        )
        
        assert isinstance(response, ExecutiveResponse)
        assert "Invalid JSON response" in response.decision
        assert response.confidence_score == 0.7  # Fallback value
    
    def test_generate_executive_response_with_context(self, service):
        # Mock successful AI response
        mock_ai_response = AIResponse(
            content='{"decision": "Context-aware decision", "rationale": "Based on provided context", "confidence_score": 0.9, "priority": "high", "category": "strategic", "risk_level": "medium"}',
            model='gpt-4',
            token_usage=TokenUsage(200, 100, 300, 0.01),
            response_time=2.0
        )
        
        service.openai_client.generate_completion = Mock(return_value=mock_ai_response)
        
        conversation_history = [
            {"role": "user", "content": "Previous question"},
            {"role": "assistant", "content": "Previous answer"}
        ]
        
        document_context = [
            "Document 1 content",
            "Document 2 content"
        ]
        
        response = service.generate_executive_response(
            executive_type="cto",
            context="Technical decision needed",
            conversation_history=conversation_history,
            document_context=document_context
        )
        
        assert response.decision == "Context-aware decision"
        assert response.executive_type == "cto"
        
        # Verify that the OpenAI client was called with proper context
        service.openai_client.generate_completion.assert_called_once()
        call_args = service.openai_client.generate_completion.call_args[0][0]
        
        # Check that system prompt was included
        assert call_args[0]["role"] == "system"
        assert "CTO" in call_args[0]["content"]
        
        # Check that user prompt includes context
        user_message = call_args[-1]["content"]
        assert "Technical decision needed" in user_message
        assert "Document 1 content" in user_message
        assert "Previous question" in user_message
    
    def test_generate_executive_response_error_handling(self, service):
        # Mock OpenAI client to raise an error
        service.openai_client.generate_completion = Mock(
            side_effect=Exception("API Error")
        )
        
        response = service.generate_executive_response(
            executive_type="cfo",
            context="Financial analysis needed"
        )
        
        assert isinstance(response, ExecutiveResponse)
        assert "Unable to generate decision due to technical error" in response.decision
        assert response.confidence_score == 0.0
        assert response.risk_level == "high"
        assert "error" in response.metadata
    
    def test_get_document_insights_success(self, service):
        # Mock successful AI response
        mock_ai_response = AIResponse(
            content='{"summary": "Document summary", "key_points": ["Point 1", "Point 2"], "recommendations": ["Rec 1", "Rec 2"], "confidence_score": 0.85}',
            model='gpt-4',
            token_usage=TokenUsage(150, 75, 225, 0.0075),
            response_time=1.8
        )
        
        service.openai_client.generate_completion = Mock(return_value=mock_ai_response)
        
        insights = service.get_document_insights("doc-123", "What are the key findings?")
        
        assert isinstance(insights, DocumentInsights)
        assert insights.summary == "Document summary"
        assert insights.key_points == ["Point 1", "Point 2"]
        assert insights.recommendations == ["Rec 1", "Rec 2"]
        assert insights.confidence_score == 0.85
    
    def test_analyze_decision_patterns_success(self, service):
        # Mock successful AI response
        mock_ai_response = AIResponse(
            content='{"trends": {"frequency": "increasing"}, "insights": ["Insight 1", "Insight 2"], "recommendations": ["Rec 1"]}',
            model='gpt-4',
            token_usage=TokenUsage(200, 100, 300, 0.01),
            response_time=2.2
        )
        
        service.openai_client.generate_completion = Mock(return_value=mock_ai_response)
        
        decisions = [
            {"executive_type": "ceo", "category": "strategic", "priority": "high"},
            {"executive_type": "cfo", "category": "financial", "priority": "medium"}
        ]
        
        analysis = service.analyze_decision_patterns(decisions)
        
        assert isinstance(analysis, PatternAnalysis)
        assert analysis.trends == {"frequency": "increasing"}
        assert analysis.insights == ["Insight 1", "Insight 2"]
        assert analysis.recommendations == ["Rec 1"]
    
    def test_get_usage_stats(self, service):
        # Set some usage data
        service.total_tokens_used = 1000
        service.total_cost = 0.05
        
        stats = service.get_usage_stats()
        
        assert stats["total_tokens_used"] == 1000
        assert stats["total_cost"] == 0.05
        assert stats["model"] == service.openai_client.model
        assert "timestamp" in stats


if __name__ == "__main__":
    pytest.main([__file__])