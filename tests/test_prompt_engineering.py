"""
Unit tests for Enhanced Prompt Engineering System
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch

from services.ai_integration import (
    PromptTemplate,
    PromptVersion,
    PromptManager,
    ABTestConfig,
    AIIntegrationService
)


class TestPromptTemplate:
    """Test PromptTemplate functionality"""
    
    def test_template_creation(self):
        template = PromptTemplate("Hello {name}", ["name"])
        assert template.template == "Hello {name}"
        assert template.variables == ["name"]
    
    def test_template_format(self):
        template = PromptTemplate("Hello {name}, you are {age} years old")
        result = template.format(name="Alice", age=30)
        assert result == "Hello Alice, you are 30 years old"
    
    def test_template_validation(self):
        template = PromptTemplate("Hello {name}", ["name"])
        
        # Should pass with required variable
        assert template.validate_variables(name="Alice") is True
        
        # Should fail without required variable
        with pytest.raises(ValueError, match="Missing required variables"):
            template.validate_variables()


class TestPromptVersion:
    """Test PromptVersion functionality"""
    
    def test_prompt_version_creation(self):
        template = PromptTemplate("Test template")
        version = PromptVersion(template, "1.0", "Initial version")
        
        assert version.template == template
        assert version.version == "1.0"
        assert version.description == "Initial version"
        assert isinstance(version.created_at, datetime)


class TestABTestConfig:
    """Test ABTestConfig functionality"""
    
    def test_ab_test_config_creation(self):
        config = ABTestConfig(
            template_name="test_template",
            version_a="1.0",
            version_b="2.0",
            traffic_split=0.3,
            success_metric="response_time"
        )
        
        assert config.template_name == "test_template"
        assert config.version_a == "1.0"
        assert config.version_b == "2.0"
        assert config.traffic_split == 0.3
        assert config.success_metric == "response_time"
        assert isinstance(config.created_at, datetime)
        assert config.results == {"a": [], "b": []}


class TestPromptManager:
    """Test enhanced PromptManager functionality"""
    
    @pytest.fixture
    def prompt_manager(self):
        return PromptManager()
    
    def test_prompt_manager_initialization(self, prompt_manager):
        # Check that enhanced templates are loaded
        assert "ceo_system" in prompt_manager.versions
        assert "cto_system" in prompt_manager.versions
        assert "cfo_system" in prompt_manager.versions
        assert "decision_prompt" in prompt_manager.versions
        assert "strategic_decision" in prompt_manager.versions
        assert "financial_decision" in prompt_manager.versions
        assert "technical_decision" in prompt_manager.versions
        
        # Check active versions are set
        assert len(prompt_manager.active_versions) > 0
    
    def test_get_template_with_version(self, prompt_manager):
        # Test getting template with specific version
        template = prompt_manager.get_template("ceo_system", "1.0")
        assert isinstance(template, PromptTemplate)
        
        # Test getting template with active version (default)
        template = prompt_manager.get_template("ceo_system")
        assert isinstance(template, PromptTemplate)
    
    def test_get_nonexistent_template(self, prompt_manager):
        with pytest.raises(ValueError, match="Template 'nonexistent' not found"):
            prompt_manager.get_template("nonexistent")
    
    def test_get_nonexistent_version(self, prompt_manager):
        with pytest.raises(ValueError, match="Version '999' not found"):
            prompt_manager.get_template("ceo_system", "999")
    
    def test_add_template_version(self, prompt_manager):
        new_template = PromptTemplate("New version template")
        prompt_manager.add_template_version("test_template", new_template, "1.0", "Test version")
        
        # Should be able to retrieve it
        retrieved = prompt_manager.get_template("test_template", "1.0")
        assert retrieved == new_template
        
        # Should appear in versions list
        versions = prompt_manager.get_template_versions("test_template")
        assert len(versions) == 1
        assert versions[0]["version"] == "1.0"
        assert versions[0]["description"] == "Test version"
    
    def test_set_active_version(self, prompt_manager):
        # Add multiple versions
        template_v1 = PromptTemplate("Version 1")
        template_v2 = PromptTemplate("Version 2")
        
        prompt_manager.add_template_version("test_template", template_v1, "1.0")
        prompt_manager.add_template_version("test_template", template_v2, "2.0")
        
        # Set active version
        prompt_manager.set_active_version("test_template", "2.0")
        
        # Should return v2 when getting without version specified
        retrieved = prompt_manager.get_template("test_template")
        assert retrieved == template_v2
        
        assert prompt_manager.active_versions["test_template"] == "2.0"
    
    def test_get_executive_system_prompt(self, prompt_manager):
        # Test getting system prompts for different executives
        ceo_prompt = prompt_manager.get_executive_system_prompt("ceo")
        assert "CEO" in ceo_prompt
        assert "strategic" in ceo_prompt.lower()
        
        cto_prompt = prompt_manager.get_executive_system_prompt("cto")
        assert "CTO" in cto_prompt
        assert "technical" in cto_prompt.lower()
        
        cfo_prompt = prompt_manager.get_executive_system_prompt("cfo")
        assert "CFO" in cfo_prompt
        assert "financial" in cfo_prompt.lower()
    
    def test_get_decision_prompt(self, prompt_manager):
        # Test general decision prompt
        prompt = prompt_manager.get_decision_prompt(
            executive_type="ceo",
            context="Test context",
            document_context="Test docs",
            conversation_history="Test history"
        )
        
        assert "Test context" in prompt
        assert "CEO" in prompt
        
        # Test strategic decision prompt
        strategic_prompt = prompt_manager.get_decision_prompt(
            executive_type="ceo",
            decision_type="strategic",
            context="Strategic decision needed"
        )
        
        assert "Strategic decision needed" in strategic_prompt
        assert "strategic" in strategic_prompt.lower()
    
    def test_list_templates(self, prompt_manager):
        templates = prompt_manager.list_templates()
        
        assert "ceo_system" in templates
        assert "cto_system" in templates
        assert "cfo_system" in templates
        assert "decision_prompt" in templates
        assert len(templates) >= 7  # At least the default templates
    
    def test_get_template_info(self, prompt_manager):
        info = prompt_manager.get_template_info("ceo_system")
        
        assert info["name"] == "ceo_system"
        assert "active_version" in info
        assert "total_versions" in info
        assert "versions" in info
        assert info["ab_test_active"] is False
    
    def test_start_ab_test(self, prompt_manager):
        # Add two versions for testing
        template_v1 = PromptTemplate("Version 1")
        template_v2 = PromptTemplate("Version 2")
        
        prompt_manager.add_template_version("test_template", template_v1, "1.0")
        prompt_manager.add_template_version("test_template", template_v2, "2.0")
        
        # Start A/B test
        ab_config = prompt_manager.start_ab_test(
            "test_template", "1.0", "2.0", 0.3, "confidence_score"
        )
        
        assert ab_config.template_name == "test_template"
        assert ab_config.version_a == "1.0"
        assert ab_config.version_b == "2.0"
        assert ab_config.traffic_split == 0.3
        assert ab_config.success_metric == "confidence_score"
        
        # Should be in active tests
        assert "test_template" in prompt_manager.ab_tests
    
    def test_get_template_for_ab_test(self, prompt_manager):
        # Add two versions and start A/B test
        template_v1 = PromptTemplate("Version 1")
        template_v2 = PromptTemplate("Version 2")
        
        prompt_manager.add_template_version("test_template", template_v1, "1.0")
        prompt_manager.add_template_version("test_template", template_v2, "2.0")
        prompt_manager.start_ab_test("test_template", "1.0", "2.0", 0.5)
        
        # Test consistent user assignment
        template1, version1 = prompt_manager.get_template_for_ab_test("test_template", "user1")
        template2, version2 = prompt_manager.get_template_for_ab_test("test_template", "user1")
        
        # Same user should get same version
        assert version1 == version2
        assert template1 == template2
        
        # Different users might get different versions
        template3, version3 = prompt_manager.get_template_for_ab_test("test_template", "user2")
        assert version3 in ["1.0", "2.0"]
    
    def test_record_ab_test_result(self, prompt_manager):
        # Set up A/B test
        template_v1 = PromptTemplate("Version 1")
        template_v2 = PromptTemplate("Version 2")
        
        prompt_manager.add_template_version("test_template", template_v1, "1.0")
        prompt_manager.add_template_version("test_template", template_v2, "2.0")
        prompt_manager.start_ab_test("test_template", "1.0", "2.0")
        
        # Record results
        result_data = {"confidence_score": 0.8, "response_time": 1.5}
        prompt_manager.record_ab_test_result("test_template", "1.0", result_data)
        
        ab_config = prompt_manager.ab_tests["test_template"]
        assert len(ab_config.results["a"]) == 1
        assert ab_config.results["a"][0] == result_data
    
    def test_stop_ab_test(self, prompt_manager):
        # Set up A/B test with some results
        template_v1 = PromptTemplate("Version 1")
        template_v2 = PromptTemplate("Version 2")
        
        prompt_manager.add_template_version("test_template", template_v1, "1.0")
        prompt_manager.add_template_version("test_template", template_v2, "2.0")
        prompt_manager.start_ab_test("test_template", "1.0", "2.0")
        
        # Add some test results
        for i in range(5):
            prompt_manager.record_ab_test_result("test_template", "1.0", {"confidence_score": 0.7 + i * 0.05})
            prompt_manager.record_ab_test_result("test_template", "2.0", {"confidence_score": 0.8 + i * 0.05})
        
        # Stop test and get results
        results = prompt_manager.stop_ab_test("test_template")
        
        assert results["status"] == "complete"
        assert results["template_name"] == "test_template"
        assert results["version_a"] == "1.0"
        assert results["version_b"] == "2.0"
        assert "improvement_percent" in results
        assert "winner" in results
        
        # Test should be removed
        assert "test_template" not in prompt_manager.ab_tests
    
    def test_get_ab_test_status(self, prompt_manager):
        # Test no active test
        status = prompt_manager.get_ab_test_status("nonexistent")
        assert status["active"] is False
        
        # Set up A/B test
        template_v1 = PromptTemplate("Version 1")
        template_v2 = PromptTemplate("Version 2")
        
        prompt_manager.add_template_version("test_template", template_v1, "1.0")
        prompt_manager.add_template_version("test_template", template_v2, "2.0")
        prompt_manager.start_ab_test("test_template", "1.0", "2.0")
        
        # Test active test status
        status = prompt_manager.get_ab_test_status("test_template")
        
        assert status["active"] is True
        assert status["template_name"] == "test_template"
        assert status["version_a"] == "1.0"
        assert status["version_b"] == "2.0"
        assert "started_at" in status


class TestAIIntegrationServicePromptManagement:
    """Test AI Integration Service prompt management features"""
    
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
    
    def test_service_has_enhanced_prompt_manager(self, service):
        assert hasattr(service, 'prompt_manager')
        assert isinstance(service.prompt_manager, PromptManager)
        
        # Should have enhanced templates
        templates = service.get_available_prompts()
        assert "strategic_decision" in templates
        assert "financial_decision" in templates
        assert "technical_decision" in templates
    
    def test_get_available_prompts(self, service):
        prompts = service.get_available_prompts()
        
        assert isinstance(prompts, list)
        assert len(prompts) >= 7  # At least the default templates
        assert "ceo_system" in prompts
    
    def test_get_prompt_info(self, service):
        info = service.get_prompt_info("ceo_system")
        
        assert "name" in info
        assert "active_version" in info
        assert "total_versions" in info
        assert "versions" in info
    
    def test_add_prompt_version(self, service):
        service.add_prompt_version(
            "test_template",
            "Test template content with {variable}",
            "1.0",
            ["variable"],
            "Test description"
        )
        
        # Should be able to retrieve it
        info = service.get_prompt_info("test_template")
        assert info["name"] == "test_template"
        assert info["total_versions"] == 1
    
    def test_set_active_prompt_version(self, service):
        # Add multiple versions
        service.add_prompt_version("test_template", "Version 1", "1.0")
        service.add_prompt_version("test_template", "Version 2", "2.0")
        
        # Set active version
        service.set_active_prompt_version("test_template", "2.0")
        
        info = service.get_prompt_info("test_template")
        assert info["active_version"] == "2.0"
    
    def test_start_prompt_ab_test(self, service):
        # Add versions for testing
        service.add_prompt_version("test_template", "Version 1", "1.0")
        service.add_prompt_version("test_template", "Version 2", "2.0")
        
        # Start A/B test
        result = service.start_prompt_ab_test("test_template", "1.0", "2.0", 0.3, "confidence_score")
        
        assert result["template_name"] == "test_template"
        assert result["version_a"] == "1.0"
        assert result["version_b"] == "2.0"
        assert result["traffic_split"] == 0.3
        assert result["success_metric"] == "confidence_score"
    
    def test_get_prompt_ab_test_status(self, service):
        # Test no active test
        status = service.get_prompt_ab_test_status("nonexistent")
        assert status["active"] is False
        
        # Start A/B test
        service.add_prompt_version("test_template", "Version 1", "1.0")
        service.add_prompt_version("test_template", "Version 2", "2.0")
        service.start_prompt_ab_test("test_template", "1.0", "2.0")
        
        # Test active test
        status = service.get_prompt_ab_test_status("test_template")
        assert status["active"] is True
    
    def test_stop_prompt_ab_test(self, service):
        # Start A/B test
        service.add_prompt_version("test_template", "Version 1", "1.0")
        service.add_prompt_version("test_template", "Version 2", "2.0")
        service.start_prompt_ab_test("test_template", "1.0", "2.0")
        
        # Stop test
        results = service.stop_prompt_ab_test("test_template")
        
        # Should return results (even if insufficient data)
        assert "status" in results


if __name__ == "__main__":
    pytest.main([__file__])