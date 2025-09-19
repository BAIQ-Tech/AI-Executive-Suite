"""
Configuration Management System

Centralized configuration management for the AI Executive Suite
with support for environment variables, secrets, and service settings.
"""

import os
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


@dataclass
class DatabaseConfig:
    """Database configuration"""
    url: str = field(default_factory=lambda: os.getenv('DATABASE_URL', 'sqlite:///ai_executive_suite.db'))
    pool_size: int = field(default_factory=lambda: int(os.getenv('DB_POOL_SIZE', '10')))
    max_overflow: int = field(default_factory=lambda: int(os.getenv('DB_MAX_OVERFLOW', '20')))
    pool_timeout: int = field(default_factory=lambda: int(os.getenv('DB_POOL_TIMEOUT', '30')))
    echo: bool = field(default_factory=lambda: os.getenv('DB_ECHO', 'false').lower() == 'true')


@dataclass
class RedisConfig:
    """Redis configuration"""
    url: str = field(default_factory=lambda: os.getenv('REDIS_URL', 'redis://localhost:6379/0'))
    max_connections: int = field(default_factory=lambda: int(os.getenv('REDIS_MAX_CONNECTIONS', '10')))
    socket_timeout: int = field(default_factory=lambda: int(os.getenv('REDIS_SOCKET_TIMEOUT', '5')))
    socket_connect_timeout: int = field(default_factory=lambda: int(os.getenv('REDIS_CONNECT_TIMEOUT', '5')))


@dataclass
class OpenAIConfig:
    """OpenAI API configuration"""
    api_key: str = field(default_factory=lambda: os.getenv('OPENAI_API_KEY', ''))
    model: str = field(default_factory=lambda: os.getenv('OPENAI_MODEL', 'gpt-4'))
    max_tokens: int = field(default_factory=lambda: int(os.getenv('OPENAI_MAX_TOKENS', '2000')))
    temperature: float = field(default_factory=lambda: float(os.getenv('OPENAI_TEMPERATURE', '0.7')))
    timeout: int = field(default_factory=lambda: int(os.getenv('OPENAI_TIMEOUT', '30')))
    max_retries: int = field(default_factory=lambda: int(os.getenv('OPENAI_MAX_RETRIES', '3')))


@dataclass
class VectorDBConfig:
    """Vector database configuration"""
    provider: str = field(default_factory=lambda: os.getenv('VECTOR_DB_PROVIDER', 'chromadb'))
    host: str = field(default_factory=lambda: os.getenv('VECTOR_DB_HOST', 'localhost'))
    port: int = field(default_factory=lambda: int(os.getenv('VECTOR_DB_PORT', '8000')))
    collection_name: str = field(default_factory=lambda: os.getenv('VECTOR_DB_COLLECTION', 'ai_executive_docs'))
    embedding_model: str = field(default_factory=lambda: os.getenv('EMBEDDING_MODEL', 'text-embedding-ada-002'))


@dataclass
class FileStorageConfig:
    """File storage configuration"""
    provider: str = field(default_factory=lambda: os.getenv('FILE_STORAGE_PROVIDER', 'local'))
    local_path: str = field(default_factory=lambda: os.getenv('FILE_STORAGE_LOCAL_PATH', './uploads'))
    aws_bucket: str = field(default_factory=lambda: os.getenv('AWS_S3_BUCKET', ''))
    aws_region: str = field(default_factory=lambda: os.getenv('AWS_REGION', 'us-east-1'))
    max_file_size: int = field(default_factory=lambda: int(os.getenv('MAX_FILE_SIZE', '50000000')))  # 50MB


@dataclass
class SecurityConfig:
    """Security configuration"""
    secret_key: str = field(default_factory=lambda: os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production'))
    jwt_secret: str = field(default_factory=lambda: os.getenv('JWT_SECRET_KEY', ''))
    jwt_expiration: int = field(default_factory=lambda: int(os.getenv('JWT_EXPIRATION_HOURS', '24')))
    password_min_length: int = field(default_factory=lambda: int(os.getenv('PASSWORD_MIN_LENGTH', '8')))
    session_timeout: int = field(default_factory=lambda: int(os.getenv('SESSION_TIMEOUT_MINUTES', '60')))
    max_login_attempts: int = field(default_factory=lambda: int(os.getenv('MAX_LOGIN_ATTEMPTS', '5')))
    lockout_duration: int = field(default_factory=lambda: int(os.getenv('LOCKOUT_DURATION_MINUTES', '15')))


@dataclass
class LoggingConfig:
    """Logging configuration"""
    level: str = field(default_factory=lambda: os.getenv('LOG_LEVEL', 'INFO'))
    format: str = field(default_factory=lambda: os.getenv('LOG_FORMAT', '%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    file_path: str = field(default_factory=lambda: os.getenv('LOG_FILE_PATH', './logs/ai_executive_suite.log'))
    max_file_size: int = field(default_factory=lambda: int(os.getenv('LOG_MAX_FILE_SIZE', '10000000')))  # 10MB
    backup_count: int = field(default_factory=lambda: int(os.getenv('LOG_BACKUP_COUNT', '5')))


@dataclass
class MonitoringConfig:
    """Monitoring and metrics configuration"""
    enabled: bool = field(default_factory=lambda: os.getenv('MONITORING_ENABLED', 'true').lower() == 'true')
    metrics_port: int = field(default_factory=lambda: int(os.getenv('METRICS_PORT', '9090')))
    health_check_interval: int = field(default_factory=lambda: int(os.getenv('HEALTH_CHECK_INTERVAL', '30')))
    performance_tracking: bool = field(default_factory=lambda: os.getenv('PERFORMANCE_TRACKING', 'true').lower() == 'true')


@dataclass
class IntegrationConfig:
    """External integration configuration"""
    crm_enabled: bool = field(default_factory=lambda: os.getenv('CRM_INTEGRATION_ENABLED', 'false').lower() == 'true')
    
    # Salesforce configuration
    salesforce_enabled: bool = field(default_factory=lambda: os.getenv('SALESFORCE_ENABLED', 'false').lower() == 'true')
    salesforce_client_id: str = field(default_factory=lambda: os.getenv('SALESFORCE_CLIENT_ID', ''))
    salesforce_client_secret: str = field(default_factory=lambda: os.getenv('SALESFORCE_CLIENT_SECRET', ''))
    salesforce_access_token: str = field(default_factory=lambda: os.getenv('SALESFORCE_ACCESS_TOKEN', ''))
    salesforce_refresh_token: str = field(default_factory=lambda: os.getenv('SALESFORCE_REFRESH_TOKEN', ''))
    salesforce_instance_url: str = field(default_factory=lambda: os.getenv('SALESFORCE_INSTANCE_URL', ''))
    
    # HubSpot configuration
    hubspot_enabled: bool = field(default_factory=lambda: os.getenv('HUBSPOT_ENABLED', 'false').lower() == 'true')
    hubspot_access_token: str = field(default_factory=lambda: os.getenv('HUBSPOT_ACCESS_TOKEN', ''))
    
    erp_enabled: bool = field(default_factory=lambda: os.getenv('ERP_INTEGRATION_ENABLED', 'false').lower() == 'true')
    
    # QuickBooks configuration
    quickbooks_enabled: bool = field(default_factory=lambda: os.getenv('QUICKBOOKS_ENABLED', 'false').lower() == 'true')
    quickbooks_client_id: str = field(default_factory=lambda: os.getenv('QUICKBOOKS_CLIENT_ID', ''))
    quickbooks_client_secret: str = field(default_factory=lambda: os.getenv('QUICKBOOKS_CLIENT_SECRET', ''))
    quickbooks_access_token: str = field(default_factory=lambda: os.getenv('QUICKBOOKS_ACCESS_TOKEN', ''))
    quickbooks_refresh_token: str = field(default_factory=lambda: os.getenv('QUICKBOOKS_REFRESH_TOKEN', ''))
    quickbooks_company_id: str = field(default_factory=lambda: os.getenv('QUICKBOOKS_COMPANY_ID', ''))
    quickbooks_production: bool = field(default_factory=lambda: os.getenv('QUICKBOOKS_PRODUCTION', 'false').lower() == 'true')
    
    # SAP configuration
    sap_enabled: bool = field(default_factory=lambda: os.getenv('SAP_ENABLED', 'false').lower() == 'true')
    sap_username: str = field(default_factory=lambda: os.getenv('SAP_USERNAME', ''))
    sap_password: str = field(default_factory=lambda: os.getenv('SAP_PASSWORD', ''))
    sap_base_url: str = field(default_factory=lambda: os.getenv('SAP_BASE_URL', ''))
    
    financial_data_enabled: bool = field(default_factory=lambda: os.getenv('FINANCIAL_DATA_ENABLED', 'false').lower() == 'true')
    financial_api_key: str = field(default_factory=lambda: os.getenv('FINANCIAL_API_KEY', ''))


@dataclass
class AppConfig:
    """Main application configuration"""
    debug: bool = field(default_factory=lambda: os.getenv('DEBUG', 'false').lower() == 'true')
    testing: bool = field(default_factory=lambda: os.getenv('TESTING', 'false').lower() == 'true')
    host: str = field(default_factory=lambda: os.getenv('HOST', '0.0.0.0'))
    port: int = field(default_factory=lambda: int(os.getenv('PORT', '5000')))
    workers: int = field(default_factory=lambda: int(os.getenv('WORKERS', '4')))
    
    # Service configurations
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    redis: RedisConfig = field(default_factory=RedisConfig)
    openai: OpenAIConfig = field(default_factory=OpenAIConfig)
    vector_db: VectorDBConfig = field(default_factory=VectorDBConfig)
    file_storage: FileStorageConfig = field(default_factory=FileStorageConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)
    integrations: IntegrationConfig = field(default_factory=IntegrationConfig)


class ConfigManager:
    """Configuration manager for the application"""
    
    _instance: Optional['ConfigManager'] = None
    _config: Optional[AppConfig] = None
    
    def __new__(cls) -> 'ConfigManager':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._config is None:
            self._config = AppConfig()
            self._validate_config()
    
    @property
    def config(self) -> AppConfig:
        """Get the application configuration"""
        return self._config
    
    def _validate_config(self) -> None:
        """Validate configuration settings"""
        errors = []
        warnings = []
        
        # Check if we're in a development environment
        is_development = (
            self._config.debug or 
            os.getenv('FLASK_ENV') == 'development' or
            os.getenv('ENVIRONMENT', '').lower() in ['dev', 'development', 'local'] or
            os.getenv('DEBUG', 'false').lower() == 'true'
        )
        
        # Validate required settings
        if not self._config.security.secret_key or self._config.security.secret_key == 'dev-secret-key-change-in-production':
            if not is_development:
                errors.append("SECRET_KEY must be set in production")
            else:
                warnings.append("Using default SECRET_KEY in development mode")
        
        if self._config.openai.api_key and not self._config.openai.api_key.startswith('sk-'):
            warnings.append("OPENAI_API_KEY appears to be invalid or not set")
        
        # Validate file storage settings
        if self._config.file_storage.provider == 'aws' and not self._config.file_storage.aws_bucket:
            if not is_development:
                errors.append("AWS_S3_BUCKET must be set when using AWS file storage")
            else:
                warnings.append("AWS_S3_BUCKET not set, using local file storage")
        
        # Validate database URL - only warn in development
        if not self._config.database.url:
            if not is_development:
                errors.append("DATABASE_URL must be set")
            else:
                warnings.append("DATABASE_URL not set, using default SQLite database")
        
        # Log warnings
        if warnings:
            warning_msg = "Configuration warnings:\n" + "\n".join(f"- {warning}" for warning in warnings)
            logger.warning(warning_msg)
        
        # Handle errors
        if errors:
            error_msg = "Configuration validation failed:\n" + "\n".join(f"- {error}" for error in errors)
            logger.error(error_msg)
            raise ValueError(error_msg)
    
    def get_service_config(self, service_name: str) -> Dict[str, Any]:
        """
        Get configuration for a specific service
        
        Args:
            service_name: Name of the service
            
        Returns:
            Configuration dictionary for the service
        """
        service_configs = {
            'ai_integration': {
                'openai': self._config.openai,
                'vector_db': self._config.vector_db
            },
            'analytics': {
                'database': self._config.database,
                'redis': self._config.redis
            },
            'collaboration': {
                'database': self._config.database,
                'redis': self._config.redis
            },
            'document_processing': {
                'file_storage': self._config.file_storage,
                'vector_db': self._config.vector_db,
                'openai': self._config.openai
            },
            'integration': {
                'redis_url': self._config.redis.url,
                'integrations': self._config.integrations
            },
            'crm_integration': {
                'redis_url': self._config.redis.url,
                'integrations': {
                    'crm_enabled': self._config.integrations.crm_enabled,
                    'salesforce': {
                        'client_id': self._config.integrations.salesforce_client_id,
                        'client_secret': self._config.integrations.salesforce_client_secret,
                        'access_token': self._config.integrations.salesforce_access_token,
                        'refresh_token': self._config.integrations.salesforce_refresh_token,
                        'instance_url': self._config.integrations.salesforce_instance_url,
                        'enabled': self._config.integrations.salesforce_enabled
                    },
                    'hubspot': {
                        'access_token': self._config.integrations.hubspot_access_token,
                        'enabled': self._config.integrations.hubspot_enabled
                    }
                }
            },
            'erp_integration': {
                'redis_url': self._config.redis.url,
                'integrations': {
                    'erp_enabled': self._config.integrations.erp_enabled,
                    'quickbooks': {
                        'client_id': self._config.integrations.quickbooks_client_id,
                        'client_secret': self._config.integrations.quickbooks_client_secret,
                        'access_token': self._config.integrations.quickbooks_access_token,
                        'refresh_token': self._config.integrations.quickbooks_refresh_token,
                        'company_id': self._config.integrations.quickbooks_company_id,
                        'production': self._config.integrations.quickbooks_production,
                        'enabled': self._config.integrations.quickbooks_enabled
                    },
                    'sap': {
                        'username': self._config.integrations.sap_username,
                        'password': self._config.integrations.sap_password,
                        'base_url': self._config.integrations.sap_base_url,
                        'enabled': self._config.integrations.sap_enabled
                    }
                }
            }
        }
        
        return service_configs.get(service_name, {})
    
    def update_config(self, updates: Dict[str, Any]) -> None:
        """
        Update configuration with new values
        
        Args:
            updates: Dictionary of configuration updates
        """
        # This would implement dynamic configuration updates
        # For now, it's a placeholder
        logger.info(f"Configuration update requested: {list(updates.keys())}")


# Global configuration instance
config_manager = ConfigManager()
config = config_manager.config