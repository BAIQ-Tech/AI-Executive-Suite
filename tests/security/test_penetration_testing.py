"""
Automated penetration testing
"""

import pytest
import requests
import json
import time
import random
import string
from unittest.mock import Mock, patch
from concurrent.futures import ThreadPoolExecutor, as_completed

from tests.factories import UserFactory


@pytest.mark.security
class TestAutomatedPenetrationTesting:
    """Automated penetration testing suite"""
    
    def test_fuzzing_api_endpoints(self, client, sample_user):
        """Fuzz API endpoints with malformed data"""
        with client.session_transaction() as sess:
            sess['user_id'] = sample_user.id
        
        # Define fuzzing payloads
        fuzz_payloads = [
            # Null bytes
            '\x00',
            'test\x00test',
            # Unicode attacks
            '\u0000',
            '\uffff',
            '\u202e',  # Right-to-left override
            # Format string attacks
            '%s%s%s%s',
            '%x%x%x%x',
            '%n%n%n%n',
            # Buffer overflow attempts
            'A' * 1000,
            'A' * 10000,
            # JSON injection
            '{"test": "value", "admin": true}',
            '{"__proto__": {"admin": true}}',
            # XML/XXE attempts
            '<?xml version="1.0"?><!DOCTYPE test [<!ENTITY xxe SYSTEM "file:///etc/passwd">]><test>&xxe;</test>',
            # LDAP injection
            '*)(uid=*))(|(uid=*',
            # NoSQL injection
            '{"$ne": null}',
            '{"$gt": ""}',
            # Template injection
            '{{7*7}}',
            '${7*7}',
            '#{7*7}',
        ]
        
        endpoints_to_fuzz = [
            ('/api/ceo/decision', 'POST', {'context': 'FUZZ_PAYLOAD'}),
            ('/api/decisions/search', 'POST', {'query': 'FUZZ_PAYLOAD'}),
            ('/api/user/profile', 'PUT', {'name': 'FUZZ_PAYLOAD'}),
        ]
        
        vulnerabilities_found = []
        
        for endpoint, method, base_data in endpoints_to_fuzz:
            for payload in fuzz_payloads:
                # Replace FUZZ_PAYLOAD with actual payload
                fuzz_data = {}
                for key, value in base_data.items():
                    if value == 'FUZZ_PAYLOAD':
                        fuzz_data[key] = payload
                    else:
                        fuzz_data[key] = value
                
                try:
                    if method == 'POST':
                        response = client.post(endpoint, json=fuzz_data)
                    elif method == 'PUT':
                        response = client.put(endpoint, json=fuzz_data)
                    
                    # Check for potential vulnerabilities
                    if response.status_code == 500:
                        # Server error might indicate vulnerability
                        error_data = response.get_json()
                        if error_data and 'error' in error_data:
                            error_msg = error_data['error'].lower()
                            
                            # Check for information disclosure
                            dangerous_keywords = [
                                'traceback', 'stack trace', 'exception',
                                'sql', 'database', 'mysql', 'postgresql',
                                'file not found', 'permission denied',
                                'internal server error'
                            ]
                            
                            for keyword in dangerous_keywords:
                                if keyword in error_msg:
                                    vulnerabilities_found.append({
                                        'endpoint': endpoint,
                                        'method': method,
                                        'payload': payload,
                                        'vulnerability': f'Information disclosure: {keyword}',
                                        'response': error_msg[:200]
                                    })
                    
                    elif response.status_code == 200:
                        # Check if payload was reflected without sanitization
                        response_data = response.get_json()
                        if response_data:
                            response_str = json.dumps(response_data)
                            if payload in response_str and len(payload) > 10:
                                vulnerabilities_found.append({
                                    'endpoint': endpoint,
                                    'method': method,
                                    'payload': payload,
                                    'vulnerability': 'Potential XSS/injection - payload reflected',
                                    'response': response_str[:200]
                                })
                
                except Exception as e:
                    # Unexpected exceptions might indicate vulnerabilities
                    vulnerabilities_found.append({
                        'endpoint': endpoint,
                        'method': method,
                        'payload': payload,
                        'vulnerability': f'Unexpected exception: {type(e).__name__}',
                        'response': str(e)[:200]
                    })
        
        # Report findings
        if vulnerabilities_found:
            print(f"\nPotential vulnerabilities found during fuzzing:")
            for vuln in vulnerabilities_found[:10]:  # Limit output
                print(f"- {vuln['endpoint']} ({vuln['method']}): {vuln['vulnerability']}")
                print(f"  Payload: {repr(vuln['payload'][:50])}")
                print(f"  Response: {vuln['response'][:100]}")
        
        # For testing purposes, we'll allow some findings but flag critical ones
        critical_vulns = [v for v in vulnerabilities_found if 'sql' in v['vulnerability'].lower()]
        assert len(critical_vulns) == 0, f"Critical SQL injection vulnerabilities found: {critical_vulns}"
    
    def test_authentication_bypass_attempts(self, client):
        """Test various authentication bypass techniques"""
        bypass_attempts = [
            # JWT manipulation (if JWT is used)
            {'Authorization': 'Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJub25lIn0.eyJ1c2VyX2lkIjoxLCJhZG1pbiI6dHJ1ZX0.'},
            # Session manipulation
            {'Cookie': 'session=admin; user_id=1; role=admin'},
            # Header injection
            {'X-User-ID': '1', 'X-Admin': 'true'},
            {'X-Forwarded-User': 'admin'},
            {'X-Remote-User': 'admin'},
            # HTTP parameter pollution
            {'user_id': ['1', '2'], 'admin': ['false', 'true']},
        ]
        
        protected_endpoint = '/api/decisions/history'
        
        bypass_successful = []
        
        for headers in bypass_attempts:
            try:
                response = client.get(protected_endpoint, headers=headers)
                
                if response.status_code == 200:
                    # Potential bypass
                    bypass_successful.append({
                        'headers': headers,
                        'status_code': response.status_code,
                        'response_length': len(response.data)
                    })
                
            except Exception as e:
                # Log unexpected errors
                print(f"Unexpected error with headers {headers}: {e}")
        
        # Should not have successful bypasses
        assert len(bypass_successful) == 0, f"Authentication bypass successful: {bypass_successful}"
    
    def test_privilege_escalation_attempts(self, client, sample_user):
        """Test privilege escalation attempts"""
        with client.session_transaction() as sess:
            sess['user_id'] = sample_user.id
        
        escalation_attempts = [
            # Role manipulation in requests
            {'role': 'admin', 'context': 'Test decision'},
            {'user_role': 'admin', 'context': 'Test decision'},
            {'is_admin': True, 'context': 'Test decision'},
            {'admin': 1, 'context': 'Test decision'},
            # User ID manipulation
            {'user_id': 0, 'context': 'Test decision'},  # Often admin
            {'user_id': -1, 'context': 'Test decision'},
            {'uid': 0, 'context': 'Test decision'},
            # Permission manipulation
            {'permissions': ['admin', 'read', 'write'], 'context': 'Test decision'},
            {'access_level': 'admin', 'context': 'Test decision'},
        ]
        
        escalation_successful = []
        
        for payload in escalation_attempts:
            try:
                response = client.post('/api/ceo/decision', json=payload)
                
                if response.status_code == 200:
                    data = response.get_json()
                    
                    # Check if escalated privileges are reflected
                    response_str = json.dumps(data).lower()
                    if 'admin' in response_str or 'elevated' in response_str:
                        escalation_successful.append({
                            'payload': payload,
                            'response': response_str[:200]
                        })
                
            except Exception as e:
                print(f"Error during privilege escalation test: {e}")
        
        # Should not have successful escalations
        assert len(escalation_successful) == 0, f"Privilege escalation successful: {escalation_successful}"
    
    def test_race_condition_vulnerabilities(self, client, sample_user):
        """Test for race condition vulnerabilities"""
        def concurrent_request(request_id):
            """Make concurrent request that might expose race conditions"""
            try:
                with client.session_transaction() as sess:
                    sess['user_id'] = sample_user.id
                
                # Simulate account balance or resource manipulation
                response = client.post('/api/user/credits', json={
                    'action': 'spend',
                    'amount': 1,
                    'request_id': request_id
                })
                
                return {
                    'request_id': request_id,
                    'status_code': response.status_code,
                    'success': response.status_code == 200
                }
            
            except Exception as e:
                return {
                    'request_id': request_id,
                    'error': str(e),
                    'success': False
                }
        
        # Execute concurrent requests
        num_requests = 20
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [
                executor.submit(concurrent_request, i) 
                for i in range(num_requests)
            ]
            
            results = [future.result() for future in as_completed(futures)]
        
        successful_requests = [r for r in results if r['success']]
        
        # Check for race condition indicators
        # If all requests succeeded when they should have been limited, it might indicate a race condition
        if len(successful_requests) == num_requests:
            print(f"Warning: All {num_requests} concurrent requests succeeded - potential race condition")
    
    def test_business_logic_vulnerabilities(self, client, sample_user):
        """Test business logic vulnerabilities"""
        with client.session_transaction() as sess:
            sess['user_id'] = sample_user.id
        
        business_logic_tests = [
            # Negative values
            {'context': 'Test', 'priority': -1},
            {'context': 'Test', 'confidence_score': -0.5},
            # Extreme values
            {'context': 'Test', 'confidence_score': 999.9},
            {'context': 'Test', 'financial_impact': -999999999},
            # Type confusion
            {'context': 'Test', 'priority': 'true'},
            {'context': 'Test', 'confidence_score': 'high'},
            # Array/object injection
            {'context': ['test1', 'test2'], 'priority': 'high'},
            {'context': {'nested': 'object'}, 'priority': 'high'},
            # Workflow manipulation
            {'context': 'Test', 'status': 'completed'},  # Skip workflow
            {'context': 'Test', 'implemented_at': '2024-01-01'},  # Backdated
        ]
        
        logic_vulnerabilities = []
        
        for payload in business_logic_tests:
            try:
                with patch('services.ai_integration.AIIntegrationService') as mock_ai:
                    mock_response = Mock()
                    mock_response.decision = "Test decision"
                    mock_response.rationale = "Test rationale"
                    mock_response.confidence_score = 0.8
                    mock_response.priority = "medium"
                    mock_response.category = "strategic"
                    mock_response.risk_level = "low"
                    
                    mock_ai.return_value.generate_executive_response.return_value = mock_response
                    
                    response = client.post('/api/ceo/decision', json=payload)
                    
                    if response.status_code == 200:
                        data = response.get_json()
                        
                        # Check for business logic violations
                        if 'confidence_score' in data:
                            score = data['confidence_score']
                            if score < 0 or score > 1:
                                logic_vulnerabilities.append({
                                    'payload': payload,
                                    'violation': f'Invalid confidence score: {score}',
                                    'response': data
                                })
                        
                        # Check for status manipulation
                        if 'status' in data and payload.get('status') == 'completed':
                            if data['status'] == 'completed':
                                logic_vulnerabilities.append({
                                    'payload': payload,
                                    'violation': 'Workflow bypass - status set to completed',
                                    'response': data
                                })
            
            except Exception as e:
                print(f"Error in business logic test: {e}")
        
        # Report business logic vulnerabilities
        if logic_vulnerabilities:
            print(f"\nBusiness logic vulnerabilities found:")
            for vuln in logic_vulnerabilities:
                print(f"- {vuln['violation']}")
                print(f"  Payload: {vuln['payload']}")
        
        # Should not have critical business logic vulnerabilities
        critical_logic_vulns = [v for v in logic_vulnerabilities if 'bypass' in v['violation'].lower()]
        assert len(critical_logic_vulns) == 0, f"Critical business logic vulnerabilities: {critical_logic_vulns}"


@pytest.mark.security
class TestAdvancedSecurityScanning:
    """Advanced security scanning techniques"""
    
    def test_timing_attack_detection(self, client):
        """Test for timing attack vulnerabilities"""
        # Test login timing differences
        valid_username = 'testuser'
        invalid_username = 'nonexistentuser12345'
        
        # Measure timing for valid username, wrong password
        valid_user_times = []
        for _ in range(10):
            start_time = time.time()
            client.post('/auth/login', json={
                'username': valid_username,
                'password': 'wrong_password'
            })
            end_time = time.time()
            valid_user_times.append(end_time - start_time)
        
        # Measure timing for invalid username
        invalid_user_times = []
        for _ in range(10):
            start_time = time.time()
            client.post('/auth/login', json={
                'username': invalid_username,
                'password': 'wrong_password'
            })
            end_time = time.time()
            invalid_user_times.append(end_time - start_time)
        
        # Calculate average times
        avg_valid_time = sum(valid_user_times) / len(valid_user_times)
        avg_invalid_time = sum(invalid_user_times) / len(invalid_user_times)
        
        # Check for significant timing difference
        time_difference = abs(avg_valid_time - avg_invalid_time)
        
        # Should not have significant timing differences (> 100ms)
        assert time_difference < 0.1, f"Timing attack vulnerability: {time_difference:.3f}s difference"
    
    def test_information_disclosure_scanning(self, client, sample_user):
        """Scan for information disclosure vulnerabilities"""
        with client.session_transaction() as sess:
            sess['user_id'] = sample_user.id
        
        # Test various endpoints for information disclosure
        endpoints_to_scan = [
            '/api/user/profile',
            '/api/decisions/history',
            '/api/analytics/decisions',
            '/api/system/status',
            '/api/health',
            '/.env',
            '/config.json',
            '/admin',
            '/debug',
        ]
        
        information_disclosures = []
        
        for endpoint in endpoints_to_scan:
            try:
                response = client.get(endpoint)
                
                if response.status_code == 200:
                    data = response.get_json() or response.get_data(as_text=True)
                    
                    if isinstance(data, str):
                        content = data.lower()
                    else:
                        content = json.dumps(data).lower()
                    
                    # Check for sensitive information
                    sensitive_patterns = [
                        'password', 'secret', 'key', 'token',
                        'database', 'connection', 'config',
                        'api_key', 'private_key', 'credential',
                        'internal', 'debug', 'trace',
                        'version', 'build', 'commit'
                    ]
                    
                    found_patterns = [pattern for pattern in sensitive_patterns if pattern in content]
                    
                    if found_patterns:
                        information_disclosures.append({
                            'endpoint': endpoint,
                            'patterns': found_patterns,
                            'content_preview': content[:200]
                        })
            
            except Exception as e:
                # Some endpoints might not exist, which is fine
                pass
        
        # Report information disclosures
        if information_disclosures:
            print(f"\nPotential information disclosures:")
            for disclosure in information_disclosures:
                print(f"- {disclosure['endpoint']}: {disclosure['patterns']}")
        
        # Check for critical disclosures
        critical_disclosures = [
            d for d in information_disclosures 
            if any(pattern in ['password', 'secret', 'key', 'credential'] 
                   for pattern in d['patterns'])
        ]
        
        assert len(critical_disclosures) == 0, f"Critical information disclosures: {critical_disclosures}"
    
    def test_session_security_scanning(self, client, sample_user):
        """Comprehensive session security scanning"""
        # Login to establish session
        with client.session_transaction() as sess:
            sess['user_id'] = sample_user.id
        
        # Test session fixation
        original_session_id = None
        with client.session_transaction() as sess:
            original_session_id = sess.get('session_id') or id(sess)
        
        # Perform login
        response = client.post('/auth/login', json={
            'username': 'testuser',
            'password': 'testpass'
        })
        
        # Check if session ID changed after login
        new_session_id = None
        with client.session_transaction() as sess:
            new_session_id = sess.get('session_id') or id(sess)
        
        if original_session_id and new_session_id:
            assert original_session_id != new_session_id, "Session fixation vulnerability - session ID not changed after login"
        
        # Test session timeout
        with client.session_transaction() as sess:
            sess['last_activity'] = time.time() - 86400  # 24 hours ago
        
        response = client.get('/api/decisions/history')
        
        # Should require re-authentication for old sessions
        if response.status_code == 200:
            print("Warning: Session timeout not enforced")
        
        # Test concurrent sessions
        session_responses = []
        for i in range(5):
            with client.session_transaction() as sess:
                sess['user_id'] = sample_user.id
                sess['session_id'] = f'session_{i}'
            
            response = client.get('/api/decisions/history')
            session_responses.append(response.status_code)
        
        # Check if all concurrent sessions are allowed
        successful_sessions = sum(1 for status in session_responses if status == 200)
        
        if successful_sessions == 5:
            print("Warning: Unlimited concurrent sessions allowed")
    
    def test_api_security_scanning(self, client, sample_user):
        """Comprehensive API security scanning"""
        with client.session_transaction() as sess:
            sess['user_id'] = sample_user.id
        
        # Test HTTP methods on endpoints
        endpoints = [
            '/api/decisions/history',
            '/api/ceo/decision',
            '/api/user/profile',
        ]
        
        methods = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS', 'TRACE']
        
        method_vulnerabilities = []
        
        for endpoint in endpoints:
            for method in methods:
                try:
                    response = getattr(client, method.lower())(endpoint)
                    
                    # Check for unexpected method support
                    if method in ['TRACE', 'TRACK'] and response.status_code != 405:
                        method_vulnerabilities.append({
                            'endpoint': endpoint,
                            'method': method,
                            'status': response.status_code,
                            'vulnerability': 'Dangerous HTTP method allowed'
                        })
                    
                    # Check for method override vulnerabilities
                    if method == 'POST':
                        override_response = client.post(endpoint, headers={
                            'X-HTTP-Method-Override': 'DELETE'
                        })
                        
                        if override_response.status_code != response.status_code:
                            method_vulnerabilities.append({
                                'endpoint': endpoint,
                                'method': 'POST with DELETE override',
                                'vulnerability': 'HTTP method override vulnerability'
                            })
                
                except Exception as e:
                    # Method not supported, which is expected
                    pass
        
        # Report method vulnerabilities
        if method_vulnerabilities:
            print(f"\nHTTP method vulnerabilities:")
            for vuln in method_vulnerabilities:
                print(f"- {vuln['endpoint']} {vuln['method']}: {vuln['vulnerability']}")
        
        # Should not allow dangerous methods
        dangerous_methods = [v for v in method_vulnerabilities if 'TRACE' in v['method'] or 'DELETE override' in v['method']]
        assert len(dangerous_methods) == 0, f"Dangerous HTTP methods allowed: {dangerous_methods}"


if __name__ == "__main__":
    pytest.main([__file__])