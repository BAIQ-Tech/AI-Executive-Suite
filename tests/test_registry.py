"""
Unit tests for Service Registry
"""

import pytest
from unittest.mock import Mock, patch

from services.registry import (
    ServiceRegistry,
    ServiceNotFoundError,
    ServiceRegistrationError,
    ServiceConfig,
    ServiceStatus
)


class TestServiceRegistry:
    """Test ServiceRegistry functionality"""
    
    @pytest.fixture
    def registry(self):
        return ServiceRegistry()
    
    def test_registry_initialization(self, registry):
        assert isinstance(registry._services, dict)
        assert len(registry._services) == 0
        assert isinstance(registry._configs, dict)
        assert len(registry._configs) == 0
    
    def test_register_service_success(self, registry):
        mock_service = Mock()
        config = ServiceConfig(
            name='test_service',
            version='1.0.0',
            dependencies=[],
            health_check_url='/health'
        )
        
        registry.register_service('test_service', mock_service, config)
        
        assert 'test_service' in registry._services
        assert registry._services['test_service'] == mock_service
        assert 'test_service' in registry._configs
        assert registry._configs['test_service'] == config
    
    def test_register_service_duplicate(self, registry):
        mock_service = Mock()
        config = ServiceConfig(name='test_service', version='1.0.0')
        
        registry.register_service('test_service', mock_service, config)
        
        with pytest.raises(ServiceRegistrationError, match="Service 'test_service' is already registered"):
            registry.register_service('test_service', mock_service, config)
    
    def test_get_service_success(self, registry):
        mock_service = Mock()
        config = ServiceConfig(name='test_service', version='1.0.0')
        
        registry.register_service('test_service', mock_service, config)
        
        retrieved_service = registry.get_service('test_service')
        assert retrieved_service == mock_service
    
    def test_get_service_not_found(self, registry):
        with pytest.raises(ServiceNotFoundError, match="Service 'nonexistent' not found"):
            registry.get_service('nonexistent')
    
    def test_unregister_service_success(self, registry):
        mock_service = Mock()
        config = ServiceConfig(name='test_service', version='1.0.0')
        
        registry.register_service('test_service', mock_service, config)
        
        result = registry.unregister_service('test_service')
        
        assert result is True
        assert 'test_service' not in registry._services
        assert 'test_service' not in registry._configs
    
    def test_unregister_service_not_found(self, registry):
        result = registry.unregister_service('nonexistent')
        assert result is False
    
    def test_list_services(self, registry):
        mock_service1 = Mock()
        mock_service2 = Mock()
        config1 = ServiceConfig(name='service1', version='1.0.0')
        config2 = ServiceConfig(name='service2', version='2.0.0')
        
        registry.register_service('service1', mock_service1, config1)
        registry.register_service('service2', mock_service2, config2)
        
        services = registry.list_services()
        
        assert isinstance(services, list)
        assert len(services) == 2
        assert 'service1' in services
        assert 'service2' in services
    
    def test_get_service_config(self, registry):
        mock_service = Mock()
        config = ServiceConfig(
            name='test_service',
            version='1.0.0',
            description='Test service',
            dependencies=['dep1', 'dep2']
        )
        
        registry.register_service('test_service', mock_service, config)
        
        retrieved_config = registry.get_service_config('test_service')
        assert retrieved_config == config
    
    def test_get_service_config_not_found(self, registry):
        with pytest.raises(ServiceNotFoundError, match="Service 'nonexistent' not found"):
            registry.get_service_config('nonexistent')
    
    def test_check_service_health_success(self, registry):
        mock_service = Mock()
        mock_service.health_check.return_value = {'status': 'healthy', 'details': 'All systems operational'}
        
        config = ServiceConfig(name='test_service', version='1.0.0')
        registry.register_service('test_service', mock_service, config)
        
        health = registry.check_service_health('test_service')
        
        assert health['status'] == 'healthy'
        assert health['details'] == 'All systems operational'
    
    def test_check_service_health_no_health_check(self, registry):
        mock_service = Mock()
        del mock_service.health_check  # Remove health_check method
        
        config = ServiceConfig(name='test_service', version='1.0.0')
        registry.register_service('test_service', mock_service, config)
        
        health = registry.check_service_health('test_service')
        
        assert health['status'] == 'unknown'
        assert 'No health check available' in health['details']
    
    def test_check_service_health_exception(self, registry):
        mock_service = Mock()
        mock_service.health_check.side_effect = Exception("Health check failed")
        
        config = ServiceConfig(name='test_service', version='1.0.0')
        registry.register_service('test_service', mock_service, config)
        
        health = registry.check_service_health('test_service')
        
        assert health['status'] == 'unhealthy'
        assert 'Health check failed' in health['details']
    
    def test_check_all_services_health(self, registry):
        # Register multiple services
        mock_service1 = Mock()
        mock_service1.health_check.return_value = {'status': 'healthy'}
        
        mock_service2 = Mock()
        mock_service2.health_check.side_effect = Exception("Service down")
        
        config1 = ServiceConfig(name='service1', version='1.0.0')
        config2 = ServiceConfig(name='service2', version='1.0.0')
        
        registry.register_service('service1', mock_service1, config1)
        registry.register_service('service2', mock_service2, config2)
        
        health_report = registry.check_all_services_health()
        
        assert isinstance(health_report, dict)
        assert 'service1' in health_report
        assert 'service2' in health_report
        assert health_report['service1']['status'] == 'healthy'
        assert health_report['service2']['status'] == 'unhealthy'
    
    def test_get_service_dependencies(self, registry):
        config = ServiceConfig(
            name='test_service',
            version='1.0.0',
            dependencies=['ai_service', 'db_service']
        )
        
        mock_service = Mock()
        registry.register_service('test_service', mock_service, config)
        
        dependencies = registry.get_service_dependencies('test_service')
        
        assert dependencies == ['ai_service', 'db_service']
    
    def test_validate_dependencies_success(self, registry):
        # Register dependencies first
        mock_ai_service = Mock()
        mock_db_service = Mock()
        ai_config = ServiceConfig(name='ai_service', version='1.0.0')
        db_config = ServiceConfig(name='db_service', version='1.0.0')
        
        registry.register_service('ai_service', mock_ai_service, ai_config)
        registry.register_service('db_service', mock_db_service, db_config)
        
        # Register service with dependencies
        mock_service = Mock()
        config = ServiceConfig(
            name='test_service',
            version='1.0.0',
            dependencies=['ai_service', 'db_service']
        )
        
        result = registry.validate_dependencies('test_service', config)
        assert result is True
    
    def test_validate_dependencies_missing(self, registry):
        config = ServiceConfig(
            name='test_service',
            version='1.0.0',
            dependencies=['missing_service']
        )
        
        with pytest.raises(ServiceRegistrationError, match="Missing dependency: missing_service"):
            registry.validate_dependencies('test_service', config)
    
    def test_get_registry_stats(self, registry):
        # Register some services
        for i in range(3):
            mock_service = Mock()
            config = ServiceConfig(name=f'service{i}', version='1.0.0')
            registry.register_service(f'service{i}', mock_service, config)
        
        stats = registry.get_registry_stats()
        
        assert isinstance(stats, dict)
        assert stats['total_services'] == 3
        assert stats['healthy_services'] >= 0
        assert stats['unhealthy_services'] >= 0
        assert 'service_versions' in stats
    
    def test_clear_registry(self, registry):
        # Register some services
        mock_service1 = Mock()
        mock_service2 = Mock()
        config1 = ServiceConfig(name='service1', version='1.0.0')
        config2 = ServiceConfig(name='service2', version='1.0.0')
        
        registry.register_service('service1', mock_service1, config1)
        registry.register_service('service2', mock_service2, config2)
        
        assert len(registry._services) == 2
        
        registry.clear_registry()
        
        assert len(registry._services) == 0
        assert len(registry._configs) == 0
    
    def test_service_exists(self, registry):
        mock_service = Mock()
        config = ServiceConfig(name='test_service', version='1.0.0')
        
        assert registry.service_exists('test_service') is False
        
        registry.register_service('test_service', mock_service, config)
        
        assert registry.service_exists('test_service') is True
    
    def test_get_service_status(self, registry):
        mock_service = Mock()
        mock_service.health_check.return_value = {'status': 'healthy'}
        
        config = ServiceConfig(name='test_service', version='1.0.0')
        registry.register_service('test_service', mock_service, config)
        
        status = registry.get_service_status('test_service')
        
        assert status == ServiceStatus.HEALTHY
    
    def test_get_service_status_unhealthy(self, registry):
        mock_service = Mock()
        mock_service.health_check.side_effect = Exception("Service error")
        
        config = ServiceConfig(name='test_service', version='1.0.0')
        registry.register_service('test_service', mock_service, config)
        
        status = registry.get_service_status('test_service')
        
        assert status == ServiceStatus.UNHEALTHY


class TestServiceConfig:
    """Test ServiceConfig data class"""
    
    def test_service_config_creation(self):
        config = ServiceConfig(
            name='test_service',
            version='1.0.0',
            description='Test service description',
            dependencies=['dep1', 'dep2'],
            health_check_url='/health',
            metadata={'key': 'value'}
        )
        
        assert config.name == 'test_service'
        assert config.version == '1.0.0'
        assert config.description == 'Test service description'
        assert config.dependencies == ['dep1', 'dep2']
        assert config.health_check_url == '/health'
        assert config.metadata == {'key': 'value'}
    
    def test_service_config_defaults(self):
        config = ServiceConfig(name='test_service', version='1.0.0')
        
        assert config.name == 'test_service'
        assert config.version == '1.0.0'
        assert config.description is None
        assert config.dependencies == []
        assert config.health_check_url is None
        assert config.metadata == {}
    
    def test_service_config_to_dict(self):
        config = ServiceConfig(
            name='test_service',
            version='1.0.0',
            description='Test service',
            dependencies=['dep1'],
            metadata={'test': True}
        )
        
        config_dict = config.to_dict()
        
        assert isinstance(config_dict, dict)
        assert config_dict['name'] == 'test_service'
        assert config_dict['version'] == '1.0.0'
        assert config_dict['description'] == 'Test service'
        assert config_dict['dependencies'] == ['dep1']
        assert config_dict['metadata'] == {'test': True}


class TestServiceStatus:
    """Test ServiceStatus enum"""
    
    def test_service_status_values(self):
        assert ServiceStatus.HEALTHY.value == 'healthy'
        assert ServiceStatus.UNHEALTHY.value == 'unhealthy'
        assert ServiceStatus.UNKNOWN.value == 'unknown'
        assert ServiceStatus.STARTING.value == 'starting'
        assert ServiceStatus.STOPPING.value == 'stopping'
    
    def test_service_status_from_string(self):
        assert ServiceStatus.from_string('healthy') == ServiceStatus.HEALTHY
        assert ServiceStatus.from_string('unhealthy') == ServiceStatus.UNHEALTHY
        assert ServiceStatus.from_string('unknown') == ServiceStatus.UNKNOWN
        
        with pytest.raises(ValueError, match="Unknown service status"):
            ServiceStatus.from_string('invalid_status')


class TestServiceRegistryIntegration:
    """Integration tests for ServiceRegistry with real services"""
    
    @pytest.fixture
    def registry_with_services(self):
        registry = ServiceRegistry()
        
        # Create mock services that simulate real service behavior
        ai_service = Mock()
        ai_service.health_check.return_value = {'status': 'healthy', 'model': 'gpt-4'}
        ai_service.generate_response.return_value = "AI response"
        
        db_service = Mock()
        db_service.health_check.return_value = {'status': 'healthy', 'connections': 5}
        db_service.query.return_value = []
        
        analytics_service = Mock()
        analytics_service.health_check.return_value = {'status': 'healthy', 'metrics_count': 1000}
        analytics_service.get_metrics.return_value = {}
        
        # Register services with dependencies
        ai_config = ServiceConfig(name='ai_service', version='1.0.0')
        db_config = ServiceConfig(name='db_service', version='1.0.0')
        analytics_config = ServiceConfig(
            name='analytics_service',
            version='1.0.0',
            dependencies=['db_service']
        )
        
        registry.register_service('ai_service', ai_service, ai_config)
        registry.register_service('db_service', db_service, db_config)
        registry.register_service('analytics_service', analytics_service, analytics_config)
        
        return registry
    
    def test_service_interaction(self, registry_with_services):
        # Test that services can interact through the registry
        ai_service = registry_with_services.get_service('ai_service')
        db_service = registry_with_services.get_service('db_service')
        
        # Simulate AI service using DB service
        response = ai_service.generate_response("test query")
        data = db_service.query("SELECT * FROM decisions")
        
        assert response == "AI response"
        assert data == []
    
    def test_dependency_validation_integration(self, registry_with_services):
        # Test that dependency validation works with real service structure
        dependencies = registry_with_services.get_service_dependencies('analytics_service')
        assert 'db_service' in dependencies
        
        # Verify dependency exists
        db_service = registry_with_services.get_service('db_service')
        assert db_service is not None
    
    def test_health_check_cascade(self, registry_with_services):
        # Test health checks across all services
        health_report = registry_with_services.check_all_services_health()
        
        assert len(health_report) == 3
        assert all(service_health['status'] == 'healthy' for service_health in health_report.values())
    
    def test_service_failure_handling(self, registry_with_services):
        # Simulate service failure
        db_service = registry_with_services.get_service('db_service')
        db_service.health_check.side_effect = Exception("Database connection failed")
        
        health = registry_with_services.check_service_health('db_service')
        assert health['status'] == 'unhealthy'
        
        # Analytics service should still be registered but may be affected
        analytics_service = registry_with_services.get_service('analytics_service')
        assert analytics_service is not None


if __name__ == "__main__":
    pytest.main([__file__])