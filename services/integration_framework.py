"""
Integration Framework Service

Generic framework for integrating with external systems including REST APIs,
OAuth authentication, data synchronization, and error handling with retry logic.
"""

import logging
import time
import json
import hashlib
from typing import Dict, Any, Optional, List, Callable, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import redis
from threading import Lock
import asyncio
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)


class AuthType(Enum):
    """Authentication types supported by the integration framework"""
    API_KEY = "api_key"
    OAUTH2 = "oauth2"
    BASIC_AUTH = "basic_auth"
    BEARER_TOKEN = "bearer_token"
    CUSTOM = "custom"


class SyncStrategy(Enum):
    """Data synchronization strategies"""
    FULL_SYNC = "full_sync"
    INCREMENTAL = "incremental"
    REAL_TIME = "real_time"
    ON_DEMAND = "on_demand"


@dataclass
class AuthConfig:
    """Authentication configuration for external systems"""
    auth_type: AuthType
    api_key: Optional[str] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_expires_at: Optional[datetime] = None
    auth_url: Optional[str] = None
    token_url: Optional[str] = None
    scope: Optional[str] = None
    custom_headers: Dict[str, str] = field(default_factory=dict)


@dataclass
class IntegrationConfig:
    """Configuration for external system integration"""
    name: str
    base_url: str
    auth_config: AuthConfig
    timeout: int = 30
    max_retries: int = 3
    retry_backoff_factor: float = 0.3
    rate_limit_per_minute: int = 60
    cache_ttl: int = 300  # 5 minutes
    sync_strategy: SyncStrategy = SyncStrategy.ON_DEMAND
    sync_interval: int = 3600  # 1 hour
    enabled: bool = True
    custom_config: Dict[str, Any] = field(default_factory=dict)


@dataclass
class APIResponse:
    """Standardized API response wrapper"""
    success: bool
    status_code: int
    data: Any = None
    error: Optional[str] = None
    headers: Dict[str, str] = field(default_factory=dict)
    response_time: float = 0.0
    cached: bool = False


@dataclass
class SyncResult:
    """Result of a data synchronization operation"""
    success: bool
    records_processed: int = 0
    records_created: int = 0
    records_updated: int = 0
    records_failed: int = 0
    errors: List[str] = field(default_factory=list)
    sync_time: float = 0.0
    last_sync_timestamp: Optional[datetime] = None


class RateLimiter:
    """Rate limiter for API calls"""
    
    def __init__(self, redis_client: redis.Redis, max_calls: int, window_seconds: int = 60):
        self.redis_client = redis_client
        self.max_calls = max_calls
        self.window_seconds = window_seconds
        
    def is_allowed(self, key: str) -> bool:
        """Check if API call is allowed within rate limit"""
        try:
            current_time = int(time.time())
            window_start = current_time - self.window_seconds
            
            # Remove old entries
            self.redis_client.zremrangebyscore(key, 0, window_start)
            
            # Count current requests
            current_count = self.redis_client.zcard(key)
            
            if current_count >= self.max_calls:
                return False
                
            # Add current request
            self.redis_client.zadd(key, {str(current_time): current_time})
            self.redis_client.expire(key, self.window_seconds)
            
            return True
            
        except Exception as e:
            logger.error(f"Rate limiter error: {e}")
            return True  # Allow on error to avoid blocking


class CacheManager:
    """Cache manager for API responses"""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis_client = redis_client
        
    def get(self, key: str) -> Optional[Any]:
        """Get cached data"""
        try:
            cached_data = self.redis_client.get(key)
            if cached_data:
                return json.loads(cached_data)
        except Exception as e:
            logger.error(f"Cache get error: {e}")
        return None
        
    def set(self, key: str, data: Any, ttl: int = 300) -> None:
        """Set cached data"""
        try:
            self.redis_client.setex(key, ttl, json.dumps(data, default=str))
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            
    def delete(self, key: str) -> None:
        """Delete cached data"""
        try:
            self.redis_client.delete(key)
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            
    def generate_key(self, integration_name: str, endpoint: str, params: Dict = None) -> str:
        """Generate cache key"""
        key_parts = [integration_name, endpoint]
        if params:
            param_str = json.dumps(params, sort_keys=True)
            param_hash = hashlib.md5(param_str.encode()).hexdigest()
            key_parts.append(param_hash)
        return ":".join(key_parts)


class AuthManager:
    """Authentication manager for external systems"""
    
    def __init__(self, cache_manager: CacheManager):
        self.cache_manager = cache_manager
        self._auth_locks: Dict[str, Lock] = {}
        
    def get_auth_headers(self, integration_name: str, auth_config: AuthConfig) -> Dict[str, str]:
        """Get authentication headers for API requests"""
        if auth_config.auth_type == AuthType.API_KEY:
            return self._get_api_key_headers(auth_config)
        elif auth_config.auth_type == AuthType.BEARER_TOKEN:
            return self._get_bearer_token_headers(auth_config)
        elif auth_config.auth_type == AuthType.OAUTH2:
            return self._get_oauth2_headers(integration_name, auth_config)
        elif auth_config.auth_type == AuthType.BASIC_AUTH:
            return self._get_basic_auth_headers(auth_config)
        elif auth_config.auth_type == AuthType.CUSTOM:
            return auth_config.custom_headers
        else:
            return {}
            
    def _get_api_key_headers(self, auth_config: AuthConfig) -> Dict[str, str]:
        """Get API key headers"""
        if not auth_config.api_key:
            return {}
        return {"Authorization": f"Bearer {auth_config.api_key}"}
        
    def _get_bearer_token_headers(self, auth_config: AuthConfig) -> Dict[str, str]:
        """Get bearer token headers"""
        if not auth_config.access_token:
            return {}
        return {"Authorization": f"Bearer {auth_config.access_token}"}
        
    def _get_basic_auth_headers(self, auth_config: AuthConfig) -> Dict[str, str]:
        """Get basic auth headers"""
        if not auth_config.client_id or not auth_config.client_secret:
            return {}
        import base64
        credentials = f"{auth_config.client_id}:{auth_config.client_secret}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        return {"Authorization": f"Basic {encoded_credentials}"}
        
    def _get_oauth2_headers(self, integration_name: str, auth_config: AuthConfig) -> Dict[str, str]:
        """Get OAuth2 headers, refreshing token if necessary"""
        if not auth_config.access_token:
            return {}
            
        # Check if token needs refresh
        if (auth_config.token_expires_at and 
            auth_config.token_expires_at <= datetime.now() + timedelta(minutes=5)):
            self._refresh_oauth2_token(integration_name, auth_config)
            
        return {"Authorization": f"Bearer {auth_config.access_token}"}
        
    def _refresh_oauth2_token(self, integration_name: str, auth_config: AuthConfig) -> None:
        """Refresh OAuth2 token"""
        if integration_name not in self._auth_locks:
            self._auth_locks[integration_name] = Lock()
            
        with self._auth_locks[integration_name]:
            if not auth_config.refresh_token or not auth_config.token_url:
                logger.error(f"Cannot refresh token for {integration_name}: missing refresh_token or token_url")
                return
                
            try:
                response = requests.post(
                    auth_config.token_url,
                    data={
                        'grant_type': 'refresh_token',
                        'refresh_token': auth_config.refresh_token,
                        'client_id': auth_config.client_id,
                        'client_secret': auth_config.client_secret
                    },
                    timeout=30
                )
                
                if response.status_code == 200:
                    token_data = response.json()
                    auth_config.access_token = token_data.get('access_token')
                    auth_config.refresh_token = token_data.get('refresh_token', auth_config.refresh_token)
                    
                    if 'expires_in' in token_data:
                        auth_config.token_expires_at = datetime.now() + timedelta(seconds=token_data['expires_in'])
                        
                    logger.info(f"Successfully refreshed OAuth2 token for {integration_name}")
                else:
                    logger.error(f"Failed to refresh OAuth2 token for {integration_name}: {response.status_code}")
                    
            except Exception as e:
                logger.error(f"Error refreshing OAuth2 token for {integration_name}: {e}")


class IntegrationFramework:
    """Main integration framework class"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.redis_client = redis.Redis.from_url(config.get('redis_url', 'redis://localhost:6379/0'))
        self.cache_manager = CacheManager(self.redis_client)
        self.auth_manager = AuthManager(self.cache_manager)
        self.integrations: Dict[str, IntegrationConfig] = {}
        self.rate_limiters: Dict[str, RateLimiter] = {}
        self.executor = ThreadPoolExecutor(max_workers=10)
        
        # Setup HTTP session with retry strategy
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=0.3,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
    def register_integration(self, integration_config: IntegrationConfig) -> None:
        """Register a new integration"""
        self.integrations[integration_config.name] = integration_config
        
        # Setup rate limiter
        self.rate_limiters[integration_config.name] = RateLimiter(
            self.redis_client,
            integration_config.rate_limit_per_minute,
            60
        )
        
        logger.info(f"Registered integration: {integration_config.name}")
        
    def make_request(
        self,
        integration_name: str,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        data: Optional[Dict] = None,
        headers: Optional[Dict] = None,
        use_cache: bool = True
    ) -> APIResponse:
        """Make an API request to an external system"""
        
        if integration_name not in self.integrations:
            return APIResponse(
                success=False,
                status_code=0,
                error=f"Integration '{integration_name}' not found"
            )
            
        integration = self.integrations[integration_name]
        
        if not integration.enabled:
            return APIResponse(
                success=False,
                status_code=0,
                error=f"Integration '{integration_name}' is disabled"
            )
            
        # Check rate limit
        rate_limiter = self.rate_limiters[integration_name]
        if not rate_limiter.is_allowed(f"rate_limit:{integration_name}"):
            return APIResponse(
                success=False,
                status_code=429,
                error="Rate limit exceeded"
            )
            
        # Check cache for GET requests
        cache_key = None
        if method.upper() == 'GET' and use_cache:
            cache_key = self.cache_manager.generate_key(integration_name, endpoint, params)
            cached_response = self.cache_manager.get(cache_key)
            if cached_response:
                return APIResponse(
                    success=True,
                    status_code=200,
                    data=cached_response,
                    cached=True
                )
                
        # Prepare request
        url = f"{integration.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        
        # Get authentication headers
        auth_headers = self.auth_manager.get_auth_headers(integration_name, integration.auth_config)
        
        # Merge headers
        request_headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'AI-Executive-Suite/1.0'
        }
        request_headers.update(auth_headers)
        if headers:
            request_headers.update(headers)
            
        start_time = time.time()
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                json=data if data else None,
                headers=request_headers,
                timeout=integration.timeout
            )
            
            response_time = time.time() - start_time
            
            # Parse response
            try:
                response_data = response.json() if response.content else None
            except json.JSONDecodeError:
                response_data = response.text
                
            api_response = APIResponse(
                success=response.status_code < 400,
                status_code=response.status_code,
                data=response_data,
                headers=dict(response.headers),
                response_time=response_time
            )
            
            if not api_response.success:
                api_response.error = f"HTTP {response.status_code}: {response.reason}"
                
            # Cache successful GET responses
            if (method.upper() == 'GET' and api_response.success and 
                use_cache and cache_key and integration.cache_ttl > 0):
                self.cache_manager.set(cache_key, response_data, integration.cache_ttl)
                
            return api_response
            
        except requests.exceptions.Timeout:
            return APIResponse(
                success=False,
                status_code=0,
                error="Request timeout",
                response_time=time.time() - start_time
            )
        except requests.exceptions.ConnectionError:
            return APIResponse(
                success=False,
                status_code=0,
                error="Connection error",
                response_time=time.time() - start_time
            )
        except Exception as e:
            return APIResponse(
                success=False,
                status_code=0,
                error=f"Request failed: {str(e)}",
                response_time=time.time() - start_time
            )
            
    def sync_data(
        self,
        integration_name: str,
        sync_function: Callable[[Any], SyncResult],
        force_full_sync: bool = False
    ) -> SyncResult:
        """Synchronize data from external system"""
        
        if integration_name not in self.integrations:
            return SyncResult(
                success=False,
                errors=[f"Integration '{integration_name}' not found"]
            )
            
        integration = self.integrations[integration_name]
        
        if not integration.enabled:
            return SyncResult(
                success=False,
                errors=[f"Integration '{integration_name}' is disabled"]
            )
            
        start_time = time.time()
        
        try:
            # Determine sync strategy
            sync_strategy = integration.sync_strategy
            if force_full_sync:
                sync_strategy = SyncStrategy.FULL_SYNC
                
            # Get last sync timestamp
            last_sync_key = f"last_sync:{integration_name}"
            last_sync_timestamp = None
            
            if sync_strategy == SyncStrategy.INCREMENTAL:
                cached_timestamp = self.cache_manager.get(last_sync_key)
                if cached_timestamp:
                    last_sync_timestamp = datetime.fromisoformat(cached_timestamp)
                    
            # Execute sync function
            sync_result = sync_function({
                'integration': integration,
                'sync_strategy': sync_strategy,
                'last_sync_timestamp': last_sync_timestamp,
                'framework': self
            })
            
            sync_result.sync_time = time.time() - start_time
            
            # Update last sync timestamp on success
            if sync_result.success:
                current_timestamp = datetime.now().isoformat()
                self.cache_manager.set(last_sync_key, current_timestamp, 86400)  # 24 hours
                sync_result.last_sync_timestamp = datetime.now()
                
            return sync_result
            
        except Exception as e:
            logger.error(f"Data sync error for {integration_name}: {e}")
            return SyncResult(
                success=False,
                errors=[f"Sync failed: {str(e)}"],
                sync_time=time.time() - start_time
            )
            
    def get_integration_status(self, integration_name: str) -> Dict[str, Any]:
        """Get status of an integration"""
        if integration_name not in self.integrations:
            return {"error": f"Integration '{integration_name}' not found"}
            
        integration = self.integrations[integration_name]
        
        # Test connectivity
        try:
            test_response = self.make_request(integration_name, 'GET', '', use_cache=False)
            connectivity = test_response.success
        except Exception:
            connectivity = False
            
        # Get last sync info
        last_sync_key = f"last_sync:{integration_name}"
        last_sync = self.cache_manager.get(last_sync_key)
        
        return {
            "name": integration.name,
            "enabled": integration.enabled,
            "base_url": integration.base_url,
            "auth_type": integration.auth_config.auth_type.value,
            "connectivity": connectivity,
            "last_sync": last_sync,
            "rate_limit": integration.rate_limit_per_minute,
            "cache_ttl": integration.cache_ttl,
            "sync_strategy": integration.sync_strategy.value
        }
        
    def list_integrations(self) -> List[Dict[str, Any]]:
        """List all registered integrations"""
        return [self.get_integration_status(name) for name in self.integrations.keys()]
        
    def enable_integration(self, integration_name: str) -> bool:
        """Enable an integration"""
        if integration_name in self.integrations:
            self.integrations[integration_name].enabled = True
            logger.info(f"Enabled integration: {integration_name}")
            return True
        return False
        
    def disable_integration(self, integration_name: str) -> bool:
        """Disable an integration"""
        if integration_name in self.integrations:
            self.integrations[integration_name].enabled = False
            logger.info(f"Disabled integration: {integration_name}")
            return True
        return False
        
    def clear_cache(self, integration_name: str = None) -> None:
        """Clear integration cache"""
        if integration_name:
            # Clear cache for specific integration
            pattern = f"{integration_name}:*"
            keys = self.redis_client.keys(pattern)
            if keys:
                self.redis_client.delete(*keys)
                logger.info(f"Cleared cache for integration: {integration_name}")
        else:
            # Clear all integration cache
            self.redis_client.flushdb()
            logger.info("Cleared all integration cache")
            
    def shutdown(self) -> None:
        """Shutdown the integration framework"""
        logger.info("Shutting down integration framework...")
        self.executor.shutdown(wait=True)
        self.session.close()
        logger.info("Integration framework shut down successfully")


class IntegrationService:
    """High-level integration service"""
    
    def __init__(self, config: Dict[str, Any]):
        self.framework = IntegrationFramework(config)
        self._setup_default_integrations()
        
    def _setup_default_integrations(self) -> None:
        """Setup default integrations based on configuration"""
        # This will be implemented in the specific integration services
        pass
        
    def get_framework(self) -> IntegrationFramework:
        """Get the integration framework instance"""
        return self.framework
        
    def shutdown(self) -> None:
        """Shutdown the integration service"""
        self.framework.shutdown()