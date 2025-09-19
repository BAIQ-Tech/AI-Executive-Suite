"""
Test Setup and Configuration

Basic tests to verify the enhanced project structure and configuration.
"""

import pytest
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_project_structure():
    """Test that all required directories and files exist"""
    required_paths = [
        'services/__init__.py',
        'services/ai_integration.py',
        'services/analytics.py',
        'services/collaboration.py',
        'services/document_processing.py',
        'services/registry.py',
        'config/__init__.py',
        'config/settings.py',
        'utils/__init__.py',
        'utils/logging.py',
        'utils/monitoring.py',
        'scripts/__init__.py',
        'scripts/setup.py',
        'requirements.txt',
        '.env.example'
    ]
    
    for path in required_paths:
        full_path = project_root / path
        assert full_path.exists(), f"Required path does not exist: {path}"


def test_configuration_import():
    """Test that configuration can be imported"""
    try:
        from config.settings import config, ConfigManager
        assert config is not None
        assert isinstance(config.debug, bool)
        assert config.database.url is not None
    except ImportError as e:
        pytest.fail(f"Failed to import configuration: {e}")


def test_services_import():
    """Test that services can be imported"""
    try:
        from services.ai_integration import AIIntegrationService
        from services.analytics import AnalyticsService
        from services.collaboration import CollaborationService
        from services.document_processing import DocumentProcessingService
        from services.registry import ServiceRegistry, service_manager
        
        # Test service registry
        assert service_manager is not None
        status = service_manager.get_status()
        assert 'services' in status
        
    except ImportError as e:
        pytest.fail(f"Failed to import services: {e}")


def test_utils_import():
    """Test that utilities can be imported"""
    try:
        from utils.logging import setup_logging, get_logger
        from utils.monitoring import monitoring_service, MetricsCollector
        
        # Test logger creation
        logger = get_logger(__name__)
        assert logger is not None
        
        # Test metrics collector
        collector = MetricsCollector()
        collector.increment_counter('test_counter')
        summary = collector.get_metrics_summary()
        assert 'counters' in summary
        
    except ImportError as e:
        pytest.fail(f"Failed to import utilities: {e}")


def test_service_initialization():
    """Test that services can be initialized with config"""
    from services.ai_integration import AIIntegrationService
    from config.settings import config_manager
    
    # Get service config
    service_config = config_manager.get_service_config('ai_integration')
    
    # Initialize service
    service = AIIntegrationService(service_config)
    assert service is not None
    assert service.config is not None


def test_environment_example():
    """Test that .env.example contains required variables"""
    env_example_path = project_root / '.env.example'
    assert env_example_path.exists()
    
    content = env_example_path.read_text()
    
    required_vars = [
        'SECRET_KEY',
        'DATABASE_URL',
        'OPENAI_API_KEY',
        'REDIS_URL',
        'LOG_LEVEL'
    ]
    
    for var in required_vars:
        assert var in content, f"Required environment variable {var} not found in .env.example"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])