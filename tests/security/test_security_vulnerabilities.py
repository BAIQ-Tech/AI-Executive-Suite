"""
Security vulnerability testing
"""

import pytest
import json
from unittest.mock import Mock, patch
import base64
import hashlib
import secrets

from tests.factories import UserFactory


@pytest.mark.security
class TestAuthenticationSecurity:
    """Test authentication security vulnerabilities"""
    
    def test_sql_injection_in_login(self, client, security_test_data):
        """Test SQL injection attempts in login"""
        sql_payloads = security_test_data['sql_injection_payloads']
        
        for payload in sql_payloads:
            response = client.post('/auth/login', json={
                'username': payload,
                'password': 'test_password'
            })
            
            # Should not return 500 error or expose database errors
            assert response.status_code in [400, 401, 403], f"SQL injection payload '{payload}' caused unexpected response"
            
            if response.status_code != 500:
                data = response.get_json()
                if data and 'error' in data:
                    error_msg = data['error'].lower()
                    # Should not expose database-specific error messages
                    assert 'sql' not in error_msg, f"SQL error exposed for payload: {payload}"
                    assert 'database' not in error_msg, f"Database error exposed for payload: {payload}"
                    assert 'mysql' not in error_msg, f"MySQL error exposed for payload: {payload}"
                    assert 'postgresql' not in error_msg, f"PostgreSQL error exposed for payload: {payload}"
    
    def test_password_brute_force_protection(self, client):
        """Test protection against password brute force attacks"""
        username = 'testuser'
        
        # Attempt multiple failed logins
        failed_attempts = 0
        max_attempts = 10
        
        for i in range(max_attempts):
            response = client.post('/auth/login', json={
                'username': username,
                'password': f'wrong_password_{i}'
            })
            
            if response.status_code == 401:
                failed_attempts += 1
            elif response.status_code == 429:  # Too Many Requests
                # Rate limiting should kick in
                assert failed_attempts >= 3, "Rate limiting should activate after multiple failures"
                break
            elif response.status_code == 423:  # Locked
                # Account lockout should occur
                assert failed_attempts >= 5, "Account lockout should occur after multiple failures"
                break
        
        # Should have some form of protection
        assert failed_attempts < max_attempts, "No brute force protection detected"
    
    def test_session_security(self, client, sample_user):
        """Test session security measures"""
        # Login to get session
        with client.session_transaction() as sess:
            sess['user_id'] = sample_user.id
        
        # Test session fixation protection
        response = client.get('/api/decisions/history')
        assert response.status_code == 200
        
        # Test session timeout (simulate)
        with client.session_transaction() as sess:
            sess['last_activity'] = 0  # Very old timestamp
        
        response = client.get('/api/decisions/history')
        # Should require re-authentication for expired session
        assert response.status_code in [401, 403], "Expired session should be rejected"
    
    def test_mfa_bypass_attempts(self, client):
        """Test MFA bypass attempts"""
        user = UserFactory.build()
        user.mfa_enabled = True
        user.mfa_secret = 'test_secret'
        
        with patch('models.User.query') as mock_query:
            mock_query.filter_by.return_value.first.return_value = user
            
            # Try to bypass MFA by going directly to protected endpoint
            response = client.post('/api/ceo/decision', json={
                'context': 'Test context'
            })
            
            # Should require MFA completion
            assert response.status_code in [401, 403], "MFA bypass attempt should be blocked"
    
    def test_weak_password_rejection(self, client):
        """Test rejection of weak passwords"""
        weak_passwords = [
            '123456',
            'password',
            'qwerty',
            'abc123',
            '12345678',
            'password123',
            'admin',
            'test'
        ]
        
        for weak_password in weak_passwords:
            response = client.post('/auth/register', json={
                'username': f'testuser_{weak_password}',
                'email': f'test_{weak_password}@example.com',
                'password': weak_password
            })
            
            # Should reject weak passwords
            assert response.status_code == 400, f"Weak password '{weak_password}' should be rejected"
            
            if response.status_code == 400:
                data = response.get_json()
                assert 'password' in data.get('error', '').lower(), "Should indicate password strength issue"


@pytest.mark.security
class TestInputValidationSecurity:
    """Test input validation security"""
    
    def test_xss_prevention(self, client, sample_user, security_test_data):
        """Test XSS prevention in user inputs"""
        xss_payloads = security_test_data['xss_payloads']
        
        with client.session_transaction() as sess:
            sess['user_id'] = sample_user.id
        
        for payload in xss_payloads:
            with patch('services.ai_integration.AIIntegrationService') as mock_ai:
                mock_response = Mock()
                mock_response.decision = "Safe decision"
                mock_response.rationale = "Safe rationale"
                mock_response.confidence_score = 0.8
                mock_response.priority = "medium"
                mock_response.category = "strategic"
                mock_response.risk_level = "low"
                
                mock_ai.return_value.generate_executive_response.return_value = mock_response
                
                response = client.post('/api/ceo/decision', json={
                    'context': payload  # XSS payload in context
                })
                
                if response.status_code == 200:
                    data = response.get_json()
                    # Response should not contain unescaped script tags
                    response_str = json.dumps(data)
                    assert '<script>' not in response_str, f"XSS payload not properly escaped: {payload}"
                    assert 'javascript:' not in response_str, f"JavaScript URL not blocked: {payload}"
    
    def test_command_injection_prevention(self, client, sample_user, security_test_data):
        """Test command injection prevention"""
        command_payloads = security_test_data['command_injection_payloads']
        
        with client.session_transaction() as sess:
            sess['user_id'] = sample_user.id
        
        for payload in command_payloads:
            # Test in document upload filename
            response = client.post('/api/documents/upload', data={
                'file': (b'test content', payload),  # Malicious filename
                'document_type': 'technical'
            })
            
            # Should reject or sanitize malicious filenames
            if response.status_code == 200:
                data = response.get_json()
                filename = data.get('filename', '')
                # Filename should be sanitized
                assert ';' not in filename, f"Command injection chars not sanitized: {payload}"
                assert '|' not in filename, f"Command injection chars not sanitized: {payload}"
                assert '&' not in filename, f"Command injection chars not sanitized: {payload}"
    
    def test_path_traversal_prevention(self, client, sample_user, security_test_data):
        """Test path traversal prevention"""
        path_payloads = security_test_data['path_traversal_payloads']
        
        with client.session_transaction() as sess:
            sess['user_id'] = sample_user.id
        
        for payload in path_payloads:
            # Test in document access
            response = client.get(f'/api/documents/{payload}')
            
            # Should not allow path traversal
            assert response.status_code in [400, 404], f"Path traversal not blocked: {payload}"
            
            if response.status_code != 404:
                data = response.get_json()
                if data and 'error' in data:
                    error_msg = data['error'].lower()
                    # Should not expose file system paths
                    assert '/etc/' not in error_msg, f"File system path exposed: {payload}"
                    assert 'c:\\' not in error_msg.lower(), f"File system path exposed: {payload}"
    
    def test_file_upload_security(self, client, sample_user):
        """Test file upload security measures"""
        # Test malicious file types
        malicious_files = [
            ('malware.exe', b'MZ\x90\x00'),  # PE executable header
            ('script.php', b'<?php system($_GET["cmd"]); ?>'),
            ('shell.jsp', b'<%@ page import="java.io.*" %>'),
            ('backdoor.asp', b'<%eval request("cmd")%>'),
        ]
        
        with client.session_transaction() as sess:
            sess['user_id'] = sample_user.id
        
        for filename, content in malicious_files:
            response = client.post('/api/documents/upload', data={
                'file': (content, filename),
                'document_type': 'technical'
            })
            
            # Should reject malicious file types
            assert response.status_code in [400, 415], f"Malicious file type not blocked: {filename}"
        
        # Test oversized files
        large_content = b'A' * (50 * 1024 * 1024)  # 50MB
        response = client.post('/api/documents/upload', data={
            'file': (large_content, 'large_file.txt'),
            'document_type': 'technical'
        })
        
        # Should reject oversized files
        assert response.status_code in [400, 413], "Oversized file not rejected"


@pytest.mark.security
class TestAuthorizationSecurity:
    """Test authorization and access control security"""
    
    def test_unauthorized_access_prevention(self, client):
        """Test prevention of unauthorized access"""
        protected_endpoints = [
            ('/api/decisions/history', 'GET'),
            ('/api/ceo/decision', 'POST'),
            ('/api/analytics/decisions', 'GET'),
            ('/api/documents/upload', 'POST'),
            ('/api/collaboration/sessions', 'POST'),
        ]
        
        for endpoint, method in protected_endpoints:
            if method == 'GET':
                response = client.get(endpoint)
            elif method == 'POST':
                response = client.post(endpoint, json={'test': 'data'})
            
            # Should require authentication
            assert response.status_code in [401, 403], f"Unauthorized access allowed to {method} {endpoint}"
    
    def test_privilege_escalation_prevention(self, client, sample_user):
        """Test prevention of privilege escalation"""
        with client.session_transaction() as sess:
            sess['user_id'] = sample_user.id
        
        # Try to access admin endpoints (if they exist)
        admin_endpoints = [
            '/api/admin/users',
            '/api/admin/system',
            '/api/admin/logs',
        ]
        
        for endpoint in admin_endpoints:
            response = client.get(endpoint)
            
            # Should deny access to admin endpoints for regular users
            assert response.status_code in [401, 403, 404], f"Privilege escalation possible at {endpoint}"
    
    def test_horizontal_privilege_escalation(self, client, sample_user, db_session):
        """Test prevention of horizontal privilege escalation"""
        # Create another user
        other_user = UserFactory.build()
        db_session.add(other_user)
        db_session.commit()
        
        # Create decision for other user
        other_decision = DecisionFactory.build(user_id=other_user.id)
        db_session.add(other_decision)
        db_session.commit()
        
        # Login as sample_user
        with client.session_transaction() as sess:
            sess['user_id'] = sample_user.id
        
        # Try to access other user's decision
        response = client.get(f'/api/decisions/{other_decision.id}')
        
        # Should deny access to other user's data
        assert response.status_code in [403, 404], "Horizontal privilege escalation possible"
    
    def test_role_based_access_control(self, client, sample_user):
        """Test role-based access control"""
        with client.session_transaction() as sess:
            sess['user_id'] = sample_user.id
            sess['user_role'] = 'user'  # Regular user role
        
        # Try to access role-restricted endpoints
        admin_actions = [
            ('/api/admin/users', 'GET'),
            ('/api/system/config', 'PUT'),
            ('/api/audit/logs', 'GET'),
        ]
        
        for endpoint, method in admin_actions:
            if method == 'GET':
                response = client.get(endpoint)
            elif method == 'PUT':
                response = client.put(endpoint, json={'config': 'value'})
            
            # Should deny access based on role
            assert response.status_code in [403, 404], f"Role-based access control failed for {method} {endpoint}"


@pytest.mark.security
class TestDataProtectionSecurity:
    """Test data protection and privacy security"""
    
    def test_sensitive_data_exposure(self, client, sample_user):
        """Test prevention of sensitive data exposure"""
        with client.session_transaction() as sess:
            sess['user_id'] = sample_user.id
        
        # Get user profile
        response = client.get('/api/user/profile')
        
        if response.status_code == 200:
            data = response.get_json()
            
            # Should not expose sensitive data
            assert 'password' not in data, "Password exposed in profile"
            assert 'password_hash' not in data, "Password hash exposed in profile"
            assert 'mfa_secret' not in data, "MFA secret exposed in profile"
            
            # Check for other sensitive fields
            sensitive_fields = ['ssn', 'credit_card', 'api_key', 'secret']
            for field in sensitive_fields:
                assert field not in data, f"Sensitive field '{field}' exposed in profile"
    
    def test_data_encryption_at_rest(self, db_session, sample_user):
        """Test data encryption at rest"""
        # Create user with sensitive data
        user = UserFactory.build()
        user.set_password('test_password')
        user.setup_mfa()
        
        db_session.add(user)
        db_session.commit()
        
        # Check that sensitive data is encrypted/hashed
        from models import User
        stored_user = db_session.query(User).filter_by(id=user.id).first()
        
        # Password should be hashed, not plain text
        assert stored_user.password_hash != 'test_password', "Password not hashed"
        assert len(stored_user.password_hash) > 20, "Password hash too short"
        
        # MFA secret should be encrypted/encoded
        if stored_user.mfa_secret:
            assert stored_user.mfa_secret != 'plain_secret', "MFA secret not encrypted"
    
    def test_pii_data_handling(self, client, sample_user):
        """Test PII data handling compliance"""
        with client.session_transaction() as sess:
            sess['user_id'] = sample_user.id
        
        # Test data export (GDPR compliance)
        response = client.get('/api/user/data-export')
        
        if response.status_code == 200:
            data = response.get_json()
            
            # Should include user's data
            assert 'user_data' in data, "User data not included in export"
            assert 'decisions' in data, "User decisions not included in export"
            
            # Should include privacy notice
            assert 'privacy_notice' in data or 'data_usage' in data, "Privacy notice missing"
        
        # Test data deletion (right to be forgotten)
        response = client.delete('/api/user/data')
        
        # Should support data deletion request
        assert response.status_code in [200, 202, 204], "Data deletion not supported"
    
    def test_audit_logging(self, client, sample_user):
        """Test security audit logging"""
        with client.session_transaction() as sess:
            sess['user_id'] = sample_user.id
        
        # Perform sensitive operations
        sensitive_operations = [
            ('POST', '/api/ceo/decision', {'context': 'Sensitive decision'}),
            ('GET', '/api/user/profile', None),
            ('PUT', '/api/user/profile', {'email': 'new@example.com'}),
        ]
        
        for method, endpoint, data in sensitive_operations:
            if method == 'GET':
                response = client.get(endpoint)
            elif method == 'POST':
                response = client.post(endpoint, json=data)
            elif method == 'PUT':
                response = client.put(endpoint, json=data)
            
            # Operations should be logged (check if audit log endpoint exists)
            audit_response = client.get('/api/audit/logs')
            
            # If audit logging is implemented, should return logs
            if audit_response.status_code == 200:
                logs = audit_response.get_json()
                assert isinstance(logs, (list, dict)), "Audit logs should be structured data"


@pytest.mark.security
class TestCryptographicSecurity:
    """Test cryptographic security measures"""
    
    def test_password_hashing_strength(self):
        """Test password hashing strength"""
        from models import User
        
        user = User(username='test', email='test@example.com')
        password = 'test_password_123'
        
        user.set_password(password)
        
        # Should use strong hashing
        assert user.password_hash != password, "Password not hashed"
        assert len(user.password_hash) >= 60, "Hash too short (should use bcrypt or similar)"
        assert user.password_hash.startswith('$2'), "Should use bcrypt hashing"
        
        # Should verify correctly
        assert user.check_password(password) is True, "Password verification failed"
        assert user.check_password('wrong_password') is False, "Wrong password accepted"
    
    def test_session_token_security(self, client, sample_user):
        """Test session token security"""
        with client.session_transaction() as sess:
            sess['user_id'] = sample_user.id
            session_token = sess.get('csrf_token') or sess.get('session_token')
        
        if session_token:
            # Session token should be sufficiently random
            assert len(session_token) >= 32, "Session token too short"
            
            # Should not be predictable
            with client.session_transaction() as sess2:
                sess2['user_id'] = sample_user.id
                session_token2 = sess2.get('csrf_token') or sess2.get('session_token')
            
            if session_token2:
                assert session_token != session_token2, "Session tokens are predictable"
    
    def test_api_key_security(self, client, sample_user):
        """Test API key security if implemented"""
        with client.session_transaction() as sess:
            sess['user_id'] = sample_user.id
        
        # Try to generate API key
        response = client.post('/api/user/api-key')
        
        if response.status_code == 200:
            data = response.get_json()
            api_key = data.get('api_key')
            
            if api_key:
                # API key should be sufficiently long and random
                assert len(api_key) >= 32, "API key too short"
                assert api_key.isalnum() or '-' in api_key or '_' in api_key, "API key format invalid"
                
                # Should be able to use API key for authentication
                headers = {'Authorization': f'Bearer {api_key}'}
                api_response = client.get('/api/decisions/history', headers=headers)
                
                assert api_response.status_code == 200, "API key authentication failed"
    
    def test_encryption_key_management(self):
        """Test encryption key management"""
        from services.data_encryption import DataEncryptionService
        
        config = {
            'encryption': {
                'algorithm': 'AES-256-GCM',
                'key_rotation_days': 90
            }
        }
        
        service = DataEncryptionService(config)
        
        # Test data encryption
        sensitive_data = "This is sensitive information"
        encrypted_data = service.encrypt(sensitive_data)
        
        # Should be encrypted (different from original)
        assert encrypted_data != sensitive_data, "Data not encrypted"
        assert len(encrypted_data) > len(sensitive_data), "Encrypted data should be longer"
        
        # Should decrypt correctly
        decrypted_data = service.decrypt(encrypted_data)
        assert decrypted_data == sensitive_data, "Decryption failed"
        
        # Should use different encryption each time (nonce/IV)
        encrypted_data2 = service.encrypt(sensitive_data)
        assert encrypted_data != encrypted_data2, "Encryption not using random nonce/IV"


@pytest.mark.security
class TestNetworkSecurity:
    """Test network security measures"""
    
    def test_https_enforcement(self, client):
        """Test HTTPS enforcement"""
        # Test if HTTP requests are redirected to HTTPS
        response = client.get('/', base_url='http://localhost')
        
        # Should redirect to HTTPS or return security headers
        if response.status_code in [301, 302]:
            assert 'https://' in response.location, "HTTP not redirected to HTTPS"
        else:
            # Check for security headers
            headers = response.headers
            assert 'Strict-Transport-Security' in headers, "HSTS header missing"
    
    def test_security_headers(self, client, sample_user):
        """Test security headers"""
        with client.session_transaction() as sess:
            sess['user_id'] = sample_user.id
        
        response = client.get('/api/decisions/history')
        
        headers = response.headers
        
        # Check for important security headers
        security_headers = {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': ['DENY', 'SAMEORIGIN'],
            'X-XSS-Protection': '1; mode=block',
            'Content-Security-Policy': None,  # Should exist
            'Referrer-Policy': None,  # Should exist
        }
        
        for header, expected_value in security_headers.items():
            if header in headers:
                if expected_value is None:
                    # Just check that header exists
                    assert headers[header], f"Security header '{header}' is empty"
                elif isinstance(expected_value, list):
                    # Check if value is one of the expected values
                    assert headers[header] in expected_value, f"Security header '{header}' has unexpected value"
                else:
                    # Check exact value
                    assert headers[header] == expected_value, f"Security header '{header}' has wrong value"
    
    def test_cors_security(self, client):
        """Test CORS security configuration"""
        # Test preflight request
        response = client.options('/api/decisions/history', headers={
            'Origin': 'https://malicious-site.com',
            'Access-Control-Request-Method': 'GET',
            'Access-Control-Request-Headers': 'Content-Type'
        })
        
        if 'Access-Control-Allow-Origin' in response.headers:
            allowed_origin = response.headers['Access-Control-Allow-Origin']
            
            # Should not allow all origins in production
            assert allowed_origin != '*', "CORS allows all origins (security risk)"
            
            # Should only allow trusted origins
            trusted_domains = ['localhost', '127.0.0.1', 'yourdomain.com']
            is_trusted = any(domain in allowed_origin for domain in trusted_domains)
            assert is_trusted, f"CORS allows untrusted origin: {allowed_origin}"


if __name__ == "__main__":
    pytest.main([__file__])