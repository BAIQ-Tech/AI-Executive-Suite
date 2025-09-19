"""
Service Registry

Central registry for managing all services in the AI Executive Suite.
Provides dependency injection and service lifecycle management.
"""

import logging
from typing import Dict, Any, Optional, Type, TypeVar
from dataclasses import dataclass

from config.settings import config_manager
from services.ai_integration import AIIntegrationService
from services.analytics import AnalyticsService
from services.collaboration import CollaborationService
from services.document_processing import DocumentProcessingService
from services.integration_framework import IntegrationService
from services.crm_integration import CRMIntegrationService
from services.erp_integration import ERPIntegrationService
from utils.logging import setup_logging
from utils.monitoring import monitoring_service

logger = logging.getLogger(__name__)

T = TypeVar('T')


@dataclass
class ServiceInfo:
    """Information about a registered service"""
    name: str
    service_class: Type
    instance: Optional[Any] = None
    initialized: bool = False
    dependencies: list = None


class ServiceRegistry:
    """Registry for managing application services"""
    
    def __init__(self):
        self._services: Dict[str, ServiceInfo] = {}
        self._initialized = False
        
    def register_service(
        self, 
        name: str, 
        service_class: Type[T], 
        dependencies: list = None
    ) -> None:
        """
        Register a service class
        
        Args:
            name: Service name
            service_class: Service class to register
            dependencies: List of service names this service depends on
        """
        self._services[name] = ServiceInfo(
            name=name,
            service_class=service_class,
            dependencies=dependencies or []
        )
        logger.info(f"Registered service: {name}")
        
    def get_service(self, name: str) -> Any:
        """
        Get a service instance
        
        Args:
            name: Service name
            
        Returns:
            Service instance
            
        Raises:
            ValueError: If service is not registered
        """
        if name not in self._services:
            raise ValueError(f"Service '{name}' is not registered")
            
        service_info = self._services[name]
        
        if not service_info.initialized:
            self._initialize_service(service_info)
            
        return service_info.instance
        
    def initialize_all(self) -> None:
        """Initialize all registered services"""
        if self._initialized:
            return
            
        logger.info("Initializing all services...")
        
        # Initialize services in dependency order
        initialized = set()
        
        def initialize_service_recursive(service_name: str):
            if service_name in initialized:
                return
                
            service_info = self._services[service_name]
            
            # Initialize dependencies first
            for dep_name in service_info.dependencies:
                if dep_name not in self._services:
                    raise ValueError(f"Dependency '{dep_name}' not found for service '{service_name}'")
                initialize_service_recursive(dep_name)
                
            # Initialize the service
            if not service_info.initialized:
                self._initialize_service(service_info)
                
            initialized.add(service_name)
            
        # Initialize all services
        for service_name in self._services:
            initialize_service_recursive(service_name)
            
        self._initialized = True
        logger.info("All services initialized successfully")
        
    def shutdown_all(self) -> None:
        """Shutdown all services"""
        logger.info("Shutting down all services...")
        
        for service_info in self._services.values():
            if service_info.initialized and hasattr(service_info.instance, 'shutdown'):
                try:
                    service_info.instance.shutdown()
                    logger.info(f"Service {service_info.name} shut down successfully")
                except Exception as e:
                    logger.error(f"Error shutting down service {service_info.name}: {e}")
                    
        self._initialized = False
        logger.info("All services shut down")
        
    def get_service_status(self) -> Dict[str, Any]:
        """Get status of all services"""
        status = {
            'initialized': self._initialized,
            'services': {}
        }
        
        for name, service_info in self._services.items():
            status['services'][name] = {
                'initialized': service_info.initialized,
                'dependencies': service_info.dependencies,
                'class': service_info.service_class.__name__
            }
            
        return status
        
    def _initialize_service(self, service_info: ServiceInfo) -> None:
        """Initialize a single service"""
        logger.info(f"Initializing service: {service_info.name}")
        
        try:
            # Get service configuration
            service_config = config_manager.get_service_config(service_info.name)
            
            # Create service instance
            service_info.instance = service_info.service_class(service_config)
            service_info.initialized = True
            
            logger.info(f"Service {service_info.name} initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize service {service_info.name}: {e}")
            raise


class ServiceManager:
    """High-level service manager"""
    
    def __init__(self):
        self.registry = ServiceRegistry()
        self._setup_services()
        
    def start(self) -> None:
        """Start all services"""
        logger.info("Starting AI Executive Suite services...")
        
        # Setup logging first
        setup_logging()
        
        # Initialize all services
        self.registry.initialize_all()
        
        # Start monitoring
        monitoring_service.start()
        
        logger.info("All services started successfully")
        
    def stop(self) -> None:
        """Stop all services"""
        logger.info("Stopping AI Executive Suite services...")
        
        # Stop monitoring
        monitoring_service.stop()
        
        # Shutdown all services
        self.registry.shutdown_all()
        
        logger.info("All services stopped")
        
    def get_service(self, name: str) -> Any:
        """Get a service instance"""
        return self.registry.get_service(name)
        
    def get_status(self) -> Dict[str, Any]:
        """Get status of all services"""
        return self.registry.get_service_status()
        
    def _setup_services(self) -> None:
        """Setup and register all services"""
        
        # Register core services
        self.registry.register_service(
            'ai_integration',
            AIIntegrationService
        )
        
        self.registry.register_service(
            'analytics',
            AnalyticsService
        )
        
        self.registry.register_service(
            'collaboration',
            CollaborationService
        )
        
        self.registry.register_service(
            'document_processing',
            DocumentProcessingService
        )
        
        self.registry.register_service(
            'integration',
            IntegrationService
        )
        
        self.registry.register_service(
            'crm_integration',
            CRMIntegrationService
        )
        
        self.registry.register_service(
            'erp_integration',
            ERPIntegrationService
        )


# Global service manager instance
service_manager = ServiceManager()


# Convenience functions for getting services
def get_ai_service() -> AIIntegrationService:
    """Get AI integration service"""
    return service_manager.get_service('ai_integration')


def get_analytics_service() -> AnalyticsService:
    """Get analytics service"""
    return service_manager.get_service('analytics')


def get_collaboration_service() -> CollaborationService:
    """Get collaboration service"""
    return service_manager.get_service('collaboration')


def get_document_service() -> DocumentProcessingService:
    """Get document processing service"""
    return service_manager.get_service('document_processing')


def get_integration_service() -> IntegrationService:
    """Get integration service"""
    return service_manager.get_service('integration')


def get_crm_integration_service() -> CRMIntegrationService:
    """Get CRM integration service"""
    return service_manager.get_service('crm_integration')


def get_erp_integration_service() -> ERPIntegrationService:
    """Get ERP integration service"""
    return service_manager.get_service('erp_integration')