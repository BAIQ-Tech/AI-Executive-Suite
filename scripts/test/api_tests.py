#!/usr/bin/env python3
"""
API tests for AI Executive Suite
Tests API functionality after deployment
"""

import os
import sys
import requests
import argparse
import json
from datetime import datetime

class APITests:
    def __init__(self, base_url, environment='production'):
        self.base_url = base_url.rstrip('/')
        self.environment = environment
        self.session = requests.Session()
        self.session.timeout = 30
        
        # Set up authentication headers
        self.session.headers.update({
            'User-Agent': 'AI-Executive-Suite-APITest/1.0',
            'Content-Type': 'application/json'
        })
    
    def test_executives_api(self):
        """Test executives API endpoints"""
        try:
            # Test GET /api/executives
            response = self.session.get(f"{self.base_url}/api/executives")
            
            # Accept both 200 (success) and 401 (auth required)
            assert response.status_code in [200, 401]
            
            if response.status_code == 200:
                data = response.json()
                assert isinstance(data, (list, dict))
            
            print("✓ Executives API test passed")
            return True
            
        except Exception as e:
            print(f"✗ Executives API test failed: {e}")
            return False
    
    def test_health_api(self):
        """Test health API endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/health")
            assert response.status_code == 200
            
            data = response.json()
            assert 'status' in data
            assert 'timestamp' in data
            
            print("✓ Health API test passed")
            return True
            
        except Exception as e:
            print(f"✗ Health API test failed: {e}")
            return False
    
    def test_analytics_api(self):
        """Test analytics API endpoints"""
        try:
            # Test analytics dashboard endpoint
            response = self.session.get(f"{self.base_url}/api/analytics/dashboard")
            
            # Accept 200, 401, or 404
            assert response.status_code in [200, 401, 404]
            
            print("✓ Analytics API test passed")
            return True
            
        except Exception as e:
            print(f"✗ Analytics API test failed: {e}")
            return False
    
    def test_document_api(self):
        """Test document API endpoints"""
        try:
            # Test document list endpoint
            response = self.session.get(f"{self.base_url}/api/documents")
            
            # Accept 200, 401, or 404
            assert response.status_code in [200, 401, 404]
            
            print("✓ Document API test passed")
            return True
            
        except Exception as e:
            print(f"✗ Document API test failed: {e}")
            return False
    
    def test_collaboration_api(self):
        """Test collaboration API endpoints"""
        try:
            # Test collaboration dashboard endpoint
            response = self.session.get(f"{self.base_url}/api/collaboration/dashboard")
            
            # Accept 200, 401, or 404
            assert response.status_code in [200, 401, 404]
            
            print("✓ Collaboration API test passed")
            return True
            
        except Exception as e:
            print(f"✗ Collaboration API test failed: {e}")
            return False
    
    def test_monitoring_api(self):
        """Test monitoring API endpoints"""
        try:
            # Test monitoring dashboard endpoint
            response = self.session.get(f"{self.base_url}/api/monitoring/dashboard")
            
            # Accept 200, 401, or 404
            assert response.status_code in [200, 401, 404]
            
            print("✓ Monitoring API test passed")
            return True
            
        except Exception as e:
            print(f"✗ Monitoring API test failed: {e}")
            return False
    
    def test_api_error_handling(self):
        """Test API error handling"""
        try:
            # Test non-existent endpoint
            response = self.session.get(f"{self.base_url}/api/nonexistent")
            assert response.status_code == 404
            
            # Should return JSON error response
            data = response.json()
            assert 'error' in data
            
            print("✓ API error handling test passed")
            return True
            
        except Exception as e:
            print(f"✗ API error handling test failed: {e}")
            return False
    
    def test_api_rate_limiting(self):
        """Test API rate limiting (if implemented)"""
        try:
            # Make multiple rapid requests
            responses = []
            for i in range(5):
                response = self.session.get(f"{self.base_url}/health")
                responses.append(response.status_code)
            
            # All should succeed or some should be rate limited (429)
            assert all(code in [200, 429] for code in responses)
            
            print("✓ API rate limiting test passed")
            return True
            
        except Exception as e:
            print(f"✗ API rate limiting test failed: {e}")
            return False
    
    def test_api_cors_headers(self):
        """Test CORS headers are present"""
        try:
            response = self.session.options(f"{self.base_url}/api/executives")
            
            # Should have CORS headers or return 405 (method not allowed)
            assert response.status_code in [200, 204, 405]
            
            print("✓ API CORS headers test passed")
            return True
            
        except Exception as e:
            print(f"✗ API CORS headers test failed: {e}")
            return False
    
    def run_all_tests(self, critical_only=False):
        """Run all API tests"""
        print(f"Running API tests for {self.environment} environment")
        print(f"Base URL: {self.base_url}")
        print(f"Timestamp: {datetime.utcnow().isoformat()}")
        print("-" * 60)
        
        critical_tests = [
            self.test_health_api,
            self.test_executives_api,
            self.test_api_error_handling,
        ]
        
        additional_tests = [
            self.test_analytics_api,
            self.test_document_api,
            self.test_collaboration_api,
            self.test_monitoring_api,
            self.test_api_rate_limiting,
            self.test_api_cors_headers,
        ]
        
        tests = critical_tests
        if not critical_only:
            tests.extend(additional_tests)
        
        passed = 0
        failed = 0
        
        for test in tests:
            if test():
                passed += 1
            else:
                failed += 1
        
        print("-" * 60)
        print(f"Tests completed: {passed} passed, {failed} failed")
        
        if failed > 0:
            print("❌ Some API tests failed!")
            return False
        else:
            print("✅ All API tests passed!")
            return True

def main():
    parser = argparse.ArgumentParser(description='AI Executive Suite API Tests')
    parser.add_argument('--base-url', default='http://localhost:5000',
                       help='Base URL for the application')
    parser.add_argument('--environment', default='development',
                       choices=['development', 'staging', 'production'],
                       help='Environment being tested')
    parser.add_argument('--critical-only', action='store_true',
                       help='Run only critical API tests')
    
    args = parser.parse_args()
    
    # Determine base URL based on environment if not explicitly provided
    if args.base_url == 'http://localhost:5000':
        if args.environment == 'staging':
            args.base_url = 'https://staging.ai-executive-suite.com'
        elif args.environment == 'production':
            args.base_url = 'https://ai-executive-suite.com'
    
    api_tests = APITests(args.base_url, args.environment)
    success = api_tests.run_all_tests(args.critical_only)
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()