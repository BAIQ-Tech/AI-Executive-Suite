"""
Tests for Integration Framework Service

Tests the generic integration framework including REST API integration,
authentication handling, data synchronization, and error handling.
"""

import pytest
import json
import time
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import requests
import redis

from services.integration_framework import (
    IntegrationFramework,
    IntegrationService,
    IntegrationConfig,
    AuthConfig,
    AuthType,
    SyncStrategy,
    APIResponse,
    SyncResult,
    RateLimiter,
    CacheManager,
    AuthManager
)


@pytest.fixture
def mock_redis():
    """Mock Redis client"""
    mock_client = Mock(spec=redis.Redis)
    mock_client.get.return_value = None
    mock_client.setex.return_value = True
    mock_client.delete.return_value = True
    mock_client.zremrangebyscore.return_value = 0
    mock_client.zcard.return_value = 0
    mock_client.zadd.return_value = True
    mock_client.expire.return_value = True
    mock_client.keys.return_value = []
    mock_client.flushdb.return_value = True
    return mock_client


@pytest.fixture
def integration_config():
    """Sample integration configuration"""
    auth_config = AuthConfig(
        auth_type=AuthType.API_KEY,
        api_key="test-api-key"
    )
    
    return IntegrationConfig(
        name="test_integration",
        base_url="https://api.example.com",
        auth_config=auth_config,
        timeout=30,
        max_retries=3,
        rate_limit_per_minute=60,
        cache_ttl=300
    )


@pytest.fixture
def integration_framework(mock_redis, integration_config):
    """Integration framework instance for testing"""
    config = {
        'redis_url': 'redis://localhost:6379/0'
    }
    
    with patch('redis.Redis.from_url', return_value=mock_redis):
        framework = IntegrationFramework(config)
        framework.register_integration(integration_config)
        return framework


class TestRateLimiter:
    """Test rate limiter functionality"""
    
    def test_rate_limiter_allows_requests_within_limit(self, mock_redis):
        """Test that rate limiter allows requests within the limit"""
        mock_redis.zcard.return_value = 5  # Current count
        
        rate_limiter = RateLimiter(mock_redis, max_calls=10, window_seconds=60)
        
        assert rate_limiter.is_allowed("test_key") is True
        mock_redis.zadd.assert_called_once()
        
    def test_rate_limiter_blocks_requests_over_limit(self, mock_redis):
        """Test that rate limiter blocks requests over the limit"""
        mock_redis.zcard.return_value = 10  # At limit
        
        rate_limiter = RateLimiter(mock_redis, max_calls=10, window_seconds=60)
        
        assert rate_limiter.is_allowed("test_key") is False
        mock_redis.zadd.assert_not_called()
        
    def test_rate_limiter_handles_redis_errors(self, mock_redis):
        """Test that rate limiter handles Redis errors gracefully"""
        mock_redis.zcard.side_effect = Exception("Redis error")
        
        rate_limiter = RateLimiter(mock_redis, max_calls=10, window_seconds=60)
        
        # Should allow on error to avoid blocking
        assert rate_limiter.is_allowed("test_key") is True


class TestCacheManager:
    """Test cache manager functionality"""
    
    def test_cache_get_returns_cached_data(self, mock_redis):
        """Test that cache manager returns cached data"""
        test_data = {"key": "value"}
        mock_redis.get.return_value = json.dumps(test_data)
        
        cache_manager = CacheManager(mock_redis)
        result = cache_manager.get("test_key")
        
        assert result == test_data
        mock_redis.get.assert_called_once_with("test_key")
        
    def test_cache_get_returns_none_for_missing_data(self, mock_redis):
        """Test that cache manager returns None for missing data"""
        mock_redis.get.return_value = None
        
        cache_manager = CacheManager(mock_redis)
        result = cache_manager.get("test_key")
        
        assert result is None
        
    def test_cache_set_stores_data(self, mock_redis):
        """Test that cache manager stores data"""
        test_data = {"key": "value"}
        
        cache_manager = CacheManager(mock_redis)
        cache_manager.set("test_key", test_data, 300)
        
        mock_redis.setex.assert_called_once_with("test_key", 300, json.dumps(test_data, default=str))
        
    def test_cache_generate_key_creates_consistent_keys(self, mock_redis):
        """Test that cache key generation is consistent"""
        cache_manager = CacheManager(mock_redis)
        
        key1 = cache_manager.generate_key("integration", "endpoint", {"param": "value"})
        key2 = cache_manager.generate_key("integration", "endpoint", {"param": "value"})
        
        assert key1 == key2
        assert "integration" in key1
        assert "endpoint" in key1


class TestAuthManager:
    """Test authentication manager functionality"""
    
    def test_api_key_auth_headers(self, mock_redis):
        """Test API key authentication headers"""
        cache_manager = CacheManager(mock_redis)
        auth_manager = AuthManager(cache_manager)
        
        auth_config = AuthConfig(
            auth_type=AuthType.API_KEY,
            api_key="test-api-key"
        )
        
        headers = auth_manager.get_auth_headers("test", auth_config)
        
        assert headers == {"Authorization": "Bearer test-api-key"}
        
    def test_bearer_token_auth_headers(self, mock_redis):
        """Test bearer token authentication headers"""
        cache_manager = CacheManager(mock_redis)
        auth_manager = AuthManager(cache_manager)
        
        auth_config = AuthConfig(
            auth_type=AuthType.BEARER_TOKEN,
            access_token="test-token"
        )
        
        headers = auth_manager.get_auth_headers("test", auth_config)
        
        assert headers == {"Authorization": "Bearer test-token"}
        
    def test_basic_auth_headers(self, mock_redis):
        """Test basic authentication headers"""
        cache_manager = CacheManager(mock_redis)
        auth_manager = AuthManager(cache_manager)
        
        auth_config = AuthConfig(
            auth_type=AuthType.BASIC_AUTH,
            client_id="test-id",
            client_secret="test-secret"
        )
        
        headers = auth_manager.get_auth_headers("test", auth_config)
        
        assert "Authorization" in headers
        assert headers["Authorization"].startswith("Basic ")
        
    def test_custom_auth_headers(self, mock_redis):
        """Test custom authentication headers"""
        cache_manager = CacheManager(mock_redis)
        auth_manager = AuthManager(cache_manager)
        
        custom_headers = {"X-API-Key": "custom-key", "X-Client-ID": "client-123"}
        auth_config = AuthConfig(
            auth_type=AuthType.CUSTOM,
            custom_headers=custom_headers
        )
        
        headers = auth_manager.get_auth_headers("test", auth_config)
        
        assert headers == custom_headers


class TestIntegrationFramework:
    """Test integration framework functionality"""
    
    def test_register_integration(self, integration_framework, integration_config):
        """Test integration registration"""
        assert "test_integration" in integration_framework.integrations
        assert integration_framework.integrations["test_integration"] == integration_config
        
    @patch('requests.Session.request')
    def test_make_request_success(self, mock_request, integration_framework):
        """Test successful API request"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "test"}
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.content = b'{"data": "test"}'
        mock_request.return_value = mock_response
        
        response = integration_framework.make_request(
            "test_integration",
            "GET",
            "test-endpoint"
        )
        
        assert response.success is True
        assert response.status_code == 200
        assert response.data == {"data": "test"}
        
    @patch('requests.Session.request')
    def test_make_request_failure(self, mock_request, integration_framework):
        """Test failed API request"""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.reason = "Not Found"
        mock_response.json.return_value = {"error": "Not found"}
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.content = b'{"error": "Not found"}'
        mock_request.return_value = mock_response
        
        response = integration_framework.make_request(
            "test_integration",
            "GET",
            "nonexistent-endpoint"
        )
        
        assert response.success is False
        assert response.status_code == 404
        assert "HTTP 404" in response.error
        
    def test_make_request_nonexistent_integration(self, integration_framework):
        """Test request to nonexistent integration"""
        response = integration_framework.make_request(
            "nonexistent_integration",
            "GET",
            "test-endpoint"
        )
        
        assert response.success is False
        assert "not found" in response.error
        
    @patch('requests.Session.request')
    def test_make_request_timeout(self, mock_request, integration_framework):
        """Test request timeout handling"""
        mock_request.side_effect = requests.exceptions.Timeout()
        
        response = integration_framework.make_request(
            "test_integration",
            "GET",
            "test-endpoint"
        )
        
        assert response.success is False
        assert "timeout" in response.error.lower()
        
    @patch('requests.Session.request')
    def test_make_request_connection_error(self, mock_request, integration_framework):
        """Test connection error handling"""
        mock_request.side_effect = requests.exceptions.ConnectionError()
        
        response = integration_framework.make_request(
            "test_integration",
            "GET",
            "test-endpoint"
        )
        
        assert response.success is False
        assert "connection error" in response.error.lower()
        
    def test_sync_data_success(self, integration_framework):
        """Test successful data synchronization"""
        def mock_sync_function(context):
            return SyncResult(
                success=True,
                records_processed=100,
                records_created=50,
                records_updated=30
            )
            
        result = integration_framework.sync_data(
            "test_integration",
            mock_sync_function
        )
        
        assert result.success is True
        assert result.records_processed == 100
        assert result.records_created == 50
        assert result.records_updated == 30
        
    def test_sync_data_failure(self, integration_framework):
        """Test failed data synchronization"""
        def mock_sync_function(context):
            raise Exception("Sync failed")
            
        result = integration_framework.sync_data(
            "test_integration",
            mock_sync_function
        )
        
        assert result.success is False
        assert "Sync failed" in result.errors[0]
        
    def test_get_integration_status(self, integration_framework):
        """Test getting integration status"""
        status = integration_framework.get_integration_status("test_integration")
        
        assert status["name"] == "test_integration"
        assert status["enabled"] is True
        assert status["base_url"] == "https://api.example.com"
        assert status["auth_type"] == "api_key"
        
    def test_list_integrations(self, integration_framework):
        """Test listing all integrations"""
        integrations = integration_framework.list_integrations()
        
        assert len(integrations) == 1
        assert integrations[0]["name"] == "test_integration"
        
    def test_enable_disable_integration(self, integration_framework):
        """Test enabling and disabling integrations"""
        # Disable integration
        result = integration_framework.disable_integration("test_integration")
        assert result is True
        assert integration_framework.integrations["test_integration"].enabled is False
        
        # Enable integration
        result = integration_framework.enable_integration("test_integration")
        assert result is True
        assert integration_framework.integrations["test_integration"].enabled is True
        
    def test_clear_cache(self, integration_framework, mock_redis):
        """Test clearing integration cache"""
        # Clear specific integration cache
        integration_framework.clear_cache("test_integration")
        mock_redis.keys.assert_called_with("test_integration:*")
        
        # Clear all cache
        integration_framework.clear_cache()
        mock_redis.flushdb.assert_called_once()


class TestIntegrationService:
    """Test integration service functionality"""
    
    @patch('redis.Redis.from_url')
    def test_integration_service_initialization(self, mock_redis_from_url):
        """Test integration service initialization"""
        mock_redis_from_url.return_value = Mock(spec=redis.Redis)
        
        config = {
            'redis_url': 'redis://localhost:6379/0'
        }
        
        service = IntegrationService(config)
        
        assert service.framework is not None
        assert isinstance(service.framework, IntegrationFramework)
        
    @patch('redis.Redis.from_url')
    def test_integration_service_get_framework(self, mock_redis_from_url):
        """Test getting framework from integration service"""
        mock_redis_from_url.return_value = Mock(spec=redis.Redis)
        
        config = {
            'redis_url': 'redis://localhost:6379/0'
        }
        
        service = IntegrationService(config)
        framework = service.get_framework()
        
        assert framework is service.framework
        
    @patch('redis.Redis.from_url')
    def test_integration_service_shutdown(self, mock_redis_from_url):
        """Test integration service shutdown"""
        mock_redis_from_url.return_value = Mock(spec=redis.Redis)
        
        config = {
            'redis_url': 'redis://localhost:6379/0'
        }
        
        service = IntegrationService(config)
        
        # Mock the framework shutdown method
        service.framework.shutdown = Mock()
        
        service.shutdown()
        
        service.framework.shutdown.assert_called_once()


class TestOAuth2TokenRefresh:
    """Test OAuth2 token refresh functionality"""
    
    @patch('requests.post')
    def test_oauth2_token_refresh_success(self, mock_post, mock_redis):
        """Test successful OAuth2 token refresh"""
        # Setup mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'access_token': 'new-access-token',
            'refresh_token': 'new-refresh-token',
            'expires_in': 3600
        }
        mock_post.return_value = mock_response
        
        # Setup auth config
        auth_config = AuthConfig(
            auth_type=AuthType.OAUTH2,
            access_token="old-token",
            refresh_token="refresh-token",
            token_expires_at=datetime.now() - timedelta(minutes=1),  # Expired
            token_url="https://api.example.com/oauth/token",
            client_id="client-id",
            client_secret="client-secret"
        )
        
        cache_manager = CacheManager(mock_redis)
        auth_manager = AuthManager(cache_manager)
        
        # This should trigger token refresh
        headers = auth_manager.get_auth_headers("test", auth_config)
        
        # Verify token was refreshed
        assert auth_config.access_token == "new-access-token"
        assert auth_config.refresh_token == "new-refresh-token"
        assert headers == {"Authorization": "Bearer new-access-token"}
        
    @patch('requests.post')
    def test_oauth2_token_refresh_failure(self, mock_post, mock_redis):
        """Test failed OAuth2 token refresh"""
        # Setup mock response
        mock_response = Mock()
        mock_response.status_code = 400
        mock_post.return_value = mock_response
        
        # Setup auth config
        auth_config = AuthConfig(
            auth_type=AuthType.OAUTH2,
            access_token="old-token",
            refresh_token="refresh-token",
            token_expires_at=datetime.now() - timedelta(minutes=1),  # Expired
            token_url="https://api.example.com/oauth/token",
            client_id="client-id",
            client_secret="client-secret"
        )
        
        cache_manager = CacheManager(mock_redis)
        auth_manager = AuthManager(cache_manager)
        
        # This should attempt token refresh but fail
        headers = auth_manager.get_auth_headers("test", auth_config)
        
        # Token should remain unchanged
        assert auth_config.access_token == "old-token"
        assert headers == {"Authorization": "Bearer old-token"}


if __name__ == '__main__':
    pytest.main([__file__])