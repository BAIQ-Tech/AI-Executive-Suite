#!/usr/bin/env python3
"""
Smoke tests for AI Executive Suite
Tests critical functionality after deployment
"""

import os
import sys
import requests
import argparse
import time
from datetime import datetime

class SmokeTests:
    def __init__(self, base_url, environment='production'):
        self.base_url = base_url.rstrip('/')
        self.environment = environment
        self.session = requests.Session()
        self.session.timeout = 30
        
        # Set up authentication if needed
        if environment == 'production':
            self.session.headers.update({
                'User-Agent': 'AI-Executive-Suite-SmokeTest/1.0'
            })
    
    def test_health_endpoint(self):
        """Test application health endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/health")
            assert response.status_code == 200
            
            data = response.json()
            assert data['status'] == 'healthy'
            assert 'timestamp' in data
            assert 'database' in data
            
            print("✓ Health endpoint test passed")
            return True
            
        except Exception as e:
            print(f"✗ Health endpoint test failed: {e}")
            return False
    
    def test_main_page(self):
        """Test main application page loads"""
        try:
            response = self.session.get(f"{self.base_url}/")
            assert response.status_code == 200
            
            # Check for key elements in response
            if 'text/html' in response.headers.get('content-type', ''):
                assert 'AI Executive Suite' in response.text
            else:
                # JSON response
                data = response.json()
                assert 'message' in data or 'status' in data
            
            print("✓ Main page test passed")
            return True
            
        except Exception as e:
            print(f"✗ Main page test failed: {e}")
            return False
    
    def test_api_endpoints(self):
        """Test critical API endpoints"""
        try:
            # Test executives endpoint
            response = self.session.get(f"{self.base_url}/api/executives")
            assert response.status_code in [200, 401]  # 401 if auth required
            
            print("✓ API endpoints test passed")
            return True
            
        except Exception as e:
            print(f"✗ API endpoints test failed: {e}")
            return False
    
    def test_static_files(self):
        """Test static file serving"""
        try:
            # Test CSS file
            response = self.session.get(f"{self.base_url}/static/css/style.css")
            assert response.status_code == 200
            assert 'text/css' in response.headers.get('content-type', '')
            
            print("✓ Static files test passed")
            return True
            
        except Exception as e:
            print(f"✗ Static files test failed: {e}")
            return False
    
    def test_database_connectivity(self):
        """Test database connectivity through health endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/health")
            assert response.status_code == 200
            
            data = response.json()
            assert data.get('database') == 'connected'
            
            print("✓ Database connectivity test passed")
            return True
            
        except Exception as e:
            print(f"✗ Database connectivity test failed: {e}")
            return False
    
    def test_response_times(self):
        """Test response times are acceptable"""
        try:
            start_time = time.time()
            response = self.session.get(f"{self.base_url}/health")
            response_time = time.time() - start_time
            
            assert response.status_code == 200
            assert response_time < 5.0  # Should respond within 5 seconds
            
            print(f"✓ Response time test passed ({response_time:.2f}s)")
            return True
            
        except Exception as e:
            print(f"✗ Response time test failed: {e}")
            return False
    
    def test_ssl_certificate(self):
        """Test SSL certificate is valid (for HTTPS)"""
        if not self.base_url.startswith('https://'):
            print("⚠ SSL test skipped (not HTTPS)")
            return True
            
        try:
            response = self.session.get(f"{self.base_url}/health")
            assert response.status_code == 200
            
            print("✓ SSL certificate test passed")
            return True
            
        except requests.exceptions.SSLError as e:
            print(f"✗ SSL certificate test failed: {e}")
            return False
        except Exception as e:
            print(f"✗ SSL certificate test failed: {e}")
            return False
    
    def run_all_tests(self, critical_only=False):
        """Run all smoke tests"""
        print(f"Running smoke tests for {self.environment} environment")
        print(f"Base URL: {self.base_url}")
        print(f"Timestamp: {datetime.utcnow().isoformat()}")
        print("-" * 60)
        
        tests = [
            self.test_health_endpoint,
            self.test_main_page,
            self.test_database_connectivity,
            self.test_response_times,
        ]
        
        if not critical_only:
            tests.extend([
                self.test_api_endpoints,
                self.test_static_files,
                self.test_ssl_certificate,
            ])
        
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
            print("❌ Some tests failed!")
            return False
        else:
            print("✅ All tests passed!")
            return True

def main():
    parser = argparse.ArgumentParser(description='AI Executive Suite Smoke Tests')
    parser.add_argument('--base-url', default='http://localhost:5000',
                       help='Base URL for the application')
    parser.add_argument('--environment', default='development',
                       choices=['development', 'staging', 'production'],
                       help='Environment being tested')
    parser.add_argument('--critical-only', action='store_true',
                       help='Run only critical tests')
    
    args = parser.parse_args()
    
    # Determine base URL based on environment if not explicitly provided
    if args.base_url == 'http://localhost:5000':
        if args.environment == 'staging':
            args.base_url = 'https://staging.ai-executive-suite.com'
        elif args.environment == 'production':
            args.base_url = 'https://ai-executive-suite.com'
    
    smoke_tests = SmokeTests(args.base_url, args.environment)
    success = smoke_tests.run_all_tests(args.critical_only)
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()