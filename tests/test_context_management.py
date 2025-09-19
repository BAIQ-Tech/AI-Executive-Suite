"""
Unit tests for Context Management System
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from services.ai_integration import (
    ContextManager,
    ConversationContext,
    ConversationMessage,
    AIIntegrationService
)


class TestConversationMessage:
    """Test ConversationMessage functionality"""
    
    def test_message_creation(self):
        msg = ConversationMessage("user", "Hello world")
        
        assert msg.role == "user"
        assert msg.content == "Hello world"
        assert isinstance(msg.timestamp, datetime)
        assert msg.metadata == {}
    
    def test_message_with_metadata(self):
        metadata = {"test": True, "priority": "high"}
        msg = ConversationMessage("assistant", "Response", metadata=metadata)
        
        assert msg.metadata == metadata


class TestConversationContext:
    """Test ConversationContext functionality"""
    
    def test_context_creation(self):
        context = ConversationContext(messages=[], max_tokens=1000)
        
        assert len(context.messages) == 0
        assert context.total_tokens == 0
        assert context.max_tokens == 1000
    
    def test_add_message(self):
        context = ConversationContext(messages=[])
        context.add_message("user", "Test message", {"test": True})
        
        assert len(context.messages) == 1
        assert context.messages[0].role == "user"
        assert context.messages[0].content == "Test message"
        assert context.messages[0].metadata == {"test": True}
    
    def test_to_openai_format(self):
        context = ConversationContext(messages=[])
        context.add_message("system", "You are a helpful assistant")
        context.add_message("user", "Hello")
        context.add_message("assistant", "Hi there!")
        
        openai_format = context.to_openai_format()
        
        expected = [
            {"role": "system", "content": "You are a helpful assistant"},
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"}
        ]
        
        assert openai_format == expected


class TestContextManager:
    """Test ContextManager functionality"""
    
    @pytest.fixture
    def context_manager(self):
        return ContextManager(max_context_tokens=1000, max_history_length=10)
    
    def test_context_manager_creation(self, context_manager):
        assert context_manager.max_context_tokens == 1000
        assert context_manager.max_history_length == 10
        assert len(context_manager.contexts) == 0
    
    def test_get_or_create_context(self, context_manager):
        # Test creating new context
        context = context_manager.get_or_create_context("test-context")
        
        assert isinstance(context, ConversationContext)
        assert len(context.messages) == 0
        assert "test-context" in context_manager.contexts
        
        # Test getting existing context
        same_context = context_manager.get_or_create_context("test-context")
        assert same_context is context
    
    def test_add_message(self, context_manager):
        context = context_manager.add_message("test-context", "user", "Hello")
        
        assert len(context.messages) == 1
        assert context.messages[0].role == "user"
        assert context.messages[0].content == "Hello"
    
    def test_get_context_messages(self, context_manager):
        # Add some messages
        context_manager.add_message("test-context", "system", "System prompt")
        context_manager.add_message("test-context", "user", "User message")
        context_manager.add_message("test-context", "assistant", "Assistant response")
        
        # Test getting all messages
        messages = context_manager.get_context_messages("test-context")
        assert len(messages) == 3
        
        # Test excluding system messages
        messages = context_manager.get_context_messages("test-context", include_system=False)
        assert len(messages) == 2
        assert all(msg["role"] != "system" for msg in messages)
        
        # Test limiting messages
        messages = context_manager.get_context_messages("test-context", max_messages=1)
        assert len(messages) == 2  # 1 system + 1 other message
    
    def test_clear_context(self, context_manager):
        context_manager.add_message("test-context", "user", "Hello")
        assert "test-context" in context_manager.contexts
        
        context_manager.clear_context("test-context")
        assert "test-context" not in context_manager.contexts
    
    def test_get_context_summary(self, context_manager):
        # Test non-existent context
        summary = context_manager.get_context_summary("non-existent")
        assert summary["exists"] is False
        
        # Test existing context
        context_manager.add_message("test-context", "user", "Hello")
        summary = context_manager.get_context_summary("test-context")
        
        assert summary["exists"] is True
        assert summary["message_count"] == 1
        assert "last_message_time" in summary
    
    def test_prune_context_by_length(self, context_manager):
        # Create context with many messages
        for i in range(15):  # More than max_history_length (10)
            if i == 0:
                context_manager.add_message("test-context", "system", "System prompt")
            else:
                role = "user" if i % 2 == 1 else "assistant"
                context_manager.add_message("test-context", role, f"Message {i}")
        
        context = context_manager.contexts["test-context"]
        
        # Should be pruned to max_history_length
        assert len(context.messages) <= context_manager.max_history_length
        
        # System message should be preserved
        system_messages = [msg for msg in context.messages if msg.role == "system"]
        assert len(system_messages) >= 1
    
    def test_inject_document_context(self, context_manager):
        documents = [
            "Document 1 content here",
            "Document 2 content here",
            "Document 3 content here"
        ]
        
        context_manager.inject_document_context("test-context", documents)
        
        context = context_manager.contexts["test-context"]
        assert len(context.messages) == 1
        assert context.messages[0].role == "system"
        assert "Document Context" in context.messages[0].content
        assert "Document 1 content here" in context.messages[0].content
    
    def test_inject_document_context_truncation(self, context_manager):
        # Test with very long document
        long_document = "x" * 1000  # Longer than max_doc_length (500)
        
        context_manager.inject_document_context("test-context", [long_document])
        
        context = context_manager.contexts["test-context"]
        content = context.messages[0].content
        
        # Should be truncated
        assert "..." in content
        assert len(content) < len(long_document) + 100  # Account for formatting


class TestAIIntegrationServiceContextManagement:
    """Test AI Integration Service context management features"""
    
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
    
    def test_service_has_context_manager(self, service):
        assert hasattr(service, 'context_manager')
        assert isinstance(service.context_manager, ContextManager)
    
    def test_get_conversation_context(self, service):
        # Test non-existent context
        summary = service.get_conversation_context("non-existent")
        assert summary["exists"] is False
        
        # Create a context
        service.context_manager.add_message("test-context", "user", "Hello")
        
        # Test existing context
        summary = service.get_conversation_context("test-context")
        assert summary["exists"] is True
        assert summary["message_count"] == 1
    
    def test_clear_conversation_context(self, service):
        service.context_manager.add_message("test-context", "user", "Hello")
        assert "test-context" in service.context_manager.contexts
        
        service.clear_conversation_context("test-context")
        assert "test-context" not in service.context_manager.contexts
    
    def test_get_conversation_history(self, service):
        # Add messages to context
        service.context_manager.add_message("test-context", "system", "System prompt")
        service.context_manager.add_message("test-context", "user", "User message")
        service.context_manager.add_message("test-context", "assistant", "Assistant response")
        
        # Test getting history without system messages
        history = service.get_conversation_history("test-context", include_system=False)
        assert len(history) == 2
        assert all(msg["role"] != "system" for msg in history)
        
        # Test getting history with system messages
        history = service.get_conversation_history("test-context", include_system=True)
        assert len(history) == 3
        
        # Test limiting messages
        history = service.get_conversation_history("test-context", max_messages=1)
        assert len(history) == 1
    
    def test_inject_context_documents(self, service):
        documents = ["Doc 1", "Doc 2"]
        service.inject_context_documents("test-context", documents)
        
        context = service.context_manager.contexts["test-context"]
        assert len(context.messages) == 1
        assert context.messages[0].role == "system"
        assert "Doc 1" in context.messages[0].content
    
    def test_prune_old_contexts(self, service):
        # Create some contexts with different ages
        old_time = datetime.utcnow() - timedelta(hours=25)  # Older than 24 hours
        recent_time = datetime.utcnow() - timedelta(hours=1)  # Recent
        
        # Mock the timestamps
        with patch('services.ai_integration.datetime') as mock_datetime:
            mock_datetime.utcnow.return_value = old_time
            service.context_manager.add_message("old-context", "user", "Old message")
            
            mock_datetime.utcnow.return_value = recent_time
            service.context_manager.add_message("recent-context", "user", "Recent message")
        
        # Reset datetime mock for prune operation
        with patch('services.ai_integration.datetime') as mock_datetime:
            mock_datetime.utcnow.return_value = datetime.utcnow()
            
            # Prune old contexts
            pruned_count = service.prune_old_contexts(max_age_hours=24)
            
            # Should have pruned the old context
            assert pruned_count == 1
            assert "old-context" not in service.context_manager.contexts
            assert "recent-context" in service.context_manager.contexts
    
    def test_usage_stats_includes_context_count(self, service):
        # Add some contexts
        service.context_manager.add_message("context1", "user", "Message 1")
        service.context_manager.add_message("context2", "user", "Message 2")
        
        stats = service.get_usage_stats()
        
        assert "active_contexts" in stats
        assert stats["active_contexts"] == 2


if __name__ == "__main__":
    pytest.main([__file__])