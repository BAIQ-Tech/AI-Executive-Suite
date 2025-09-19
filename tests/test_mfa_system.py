"""
Test Suite for Multi-Factor Authentication System

Tests TOTP, SMS, Email MFA, backup codes, and security features.
"""

import pytest
import os
import sys
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask
from models import db, User, MFAMethod, MFABackupCode, MFAVerificationAttempt, PendingMFAVerification, MFARecoveryToken
from services.mfa import MFAService
import pyotp


@pytest.fixture
def app():
    """Create test Flask application."""
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'test-secret-key'
    app.config['MFA_ENCRYPTION_KEY'] = 'test-mfa-key-32-bytes-long-exactly'
    app.config['WTF_CSRF_ENABLED'] = False
    
    db.init_app(app)
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def test_user(app):
    """Create test user."""
    with app.app_context():
        user = User(
            username='testuser',
            email='test@example.com',
            name='Test User'
        )
        user.set_password('testpassword')
        db.session.add(user)
        db.session.commit()
        return user


@pytest.fixture
def mfa_service(app):
    """Create MFA service instance."""
    with app.app_context():
        return MFAService()


class TestMFAService:
    """Test MFA service functionality."""
    
    def test_generate_totp_secret(self, mfa_service):
        """Test TOTP secret generation."""
        secret, provisioning_uri = mfa_service.generate_totp_secret(1, 'testuser')
        
        assert len(secret) == 32  # Base32 encoded secret
        assert 'testuser' in provisioning_uri
        assert 'AI Executive Suite' in provisioning_uri
        assert secret in provisioning_uri
    
    def test_verify_totp_token(self, mfa_service):
        """Test TOTP token verification."""
        secret = pyotp.random_base32()
        totp = pyotp.TOTP(secret)
        valid_token = totp.now()
        
        # Test valid token
        assert mfa_service.verify_totp_token(secret, valid_token) is True
        
        # Test invalid token
        assert mfa_service.verify_totp_token(secret, '000000') is False
        
        # Test invalid secret
        assert mfa_service.verify_totp_token('invalid', valid_token) is False
    
    def test_generate_backup_codes(self, mfa_service):
        """Test backup code generation."""
        codes = mfa_service.generate_backup_codes(5)
        
        assert len(codes) == 5
        for code in codes:
            assert len(code) == 9  # XXXX-XXXX format
            assert '-' in code
            assert code.isupper()
    
    def test_validate_backup_code(self, mfa_service):
        """Test backup code validation."""
        codes = ['ABCD-1234', 'EFGH-5678']
        
        # Test valid code
        is_valid, remaining = mfa_service.validate_backup_code(codes, 'ABCD-1234')
        assert is_valid is True
        assert 'ABCD-1234' not in remaining
        assert len(remaining) == 1
        
        # Test invalid code
        is_valid, remaining = mfa_service.validate_backup_code(codes, 'INVALID')
        assert is_valid is False
        assert len(remaining) == 2
        
        # Test case insensitive and format flexible
        is_valid, remaining = mfa_service.validate_backup_code(codes, 'efgh5678')
        assert is_valid is True
    
    def test_encryption_decryption(self, mfa_service):
        """Test data encryption and decryption."""
        original_data = "sensitive-totp-secret"
        
        encrypted = mfa_service.encrypt_sensitive_data(original_data)
        assert encrypted != original_data
        
        decrypted = mfa_service.decrypt_sensitive_data(encrypted)
        assert decrypted == original_data
    
    def test_generate_verification_code(self, mfa_service):
        """Test verification code generation."""
        code = mfa_service.generate_verification_code()
        
        assert len(code) == 6
        assert code.isdigit()
        
        # Test custom length
        code_8 = mfa_service.generate_verification_code(8)
        assert len(code_8) == 8
        assert code_8.isdigit()
    
    @patch('smtplib.SMTP')
    def test_send_email_verification(self, mock_smtp, app, mfa_service):
        """Test email verification sending."""
        with app.app_context():
            app.config.update({
                'SMTP_SERVER': 'smtp.test.com',
                'SMTP_USERNAME': 'test@test.com',
                'SMTP_PASSWORD': 'password'
            })
            
            mock_server = Mock()
            mock_smtp.return_value = mock_server
            
            result = mfa_service.send_email_verification('user@test.com', '123456')
            
            assert result is True
            mock_smtp.assert_called_once()
            mock_server.starttls.assert_called_once()
            mock_server.login.assert_called_once()
            mock_server.send_message.assert_called_once()
    
    @patch('requests.post')
    def test_send_sms_verification(self, mock_post, app, mfa_service):
        """Test SMS verification sending."""
        with app.app_context():
            app.config.update({
                'TWILIO_ACCOUNT_SID': 'test_sid',
                'TWILIO_AUTH_TOKEN': 'test_token',
                'TWILIO_PHONE_NUMBER': '+1234567890'
            })
            
            mock_response = Mock()
            mock_response.status_code = 201
            mock_post.return_value = mock_response
            
            result = mfa_service.send_sms_verification('+1987654321', '123456')
            
            assert result is True
            mock_post.assert_called_once()


class TestMFAModels:
    """Test MFA database models."""
    
    def test_mfa_method_creation(self, app, test_user):
        """Test MFA method model creation."""
        with app.app_context():
            mfa_method = MFAMethod(
                user_id=test_user.id,
                method_type='totp',
                totp_secret='encrypted_secret',
                is_enabled=True,
                is_verified=True
            )
            db.session.add(mfa_method)
            db.session.commit()
            
            retrieved = MFAMethod.query.filter_by(user_id=test_user.id).first()
            assert retrieved.method_type == 'totp'
            assert retrieved.is_enabled is True
            assert retrieved.totp_secret == 'encrypted_secret'
    
    def test_backup_code_creation(self, app, test_user):
        """Test backup code model creation."""
        with app.app_context():
            backup_code = MFABackupCode(test_user.id, 'ABCD-1234')
            db.session.add(backup_code)
            db.session.commit()
            
            retrieved = MFABackupCode.query.filter_by(user_id=test_user.id).first()
            assert retrieved.verify_code('ABCD-1234') is True
            assert retrieved.verify_code('WRONG-CODE') is False
            assert retrieved.is_used is False
    
    def test_backup_code_usage(self, app, test_user):
        """Test backup code usage tracking."""
        with app.app_context():
            backup_code = MFABackupCode(test_user.id, 'ABCD-1234')
            db.session.add(backup_code)
            db.session.commit()
            
            # Mark as used
            backup_code.mark_used()
            db.session.commit()
            
            assert backup_code.is_used is True
            assert backup_code.used_at is not None
    
    def test_verification_attempt_logging(self, app, test_user):
        """Test MFA verification attempt logging."""
        with app.app_context():
            attempt = MFAVerificationAttempt(
                user_id=test_user.id,
                method_type='totp',
                ip_address='192.168.1.1',
                success=True,
                user_agent='Test Browser'
            )
            db.session.add(attempt)
            db.session.commit()
            
            retrieved = MFAVerificationAttempt.query.filter_by(user_id=test_user.id).first()
            assert retrieved.method_type == 'totp'
            assert retrieved.success is True
            assert retrieved.ip_address == '192.168.1.1'
    
    def test_pending_verification(self, app, test_user):
        """Test pending verification model."""
        with app.app_context():
            expires_at = datetime.utcnow() + timedelta(minutes=10)
            pending = PendingMFAVerification(
                user_id=test_user.id,
                method_type='sms',
                code='123456',
                contact_info='+1234567890',
                expires_at=expires_at
            )
            db.session.add(pending)
            db.session.commit()
            
            retrieved = PendingMFAVerification.query.filter_by(user_id=test_user.id).first()
            assert retrieved.verify_code('123456') is True
            assert retrieved.verify_code('wrong') is False
            assert retrieved.is_expired() is False
            
            # Test expiration
            retrieved.expires_at = datetime.utcnow() - timedelta(minutes=1)
            assert retrieved.is_expired() is True
    
    def test_recovery_token(self, app, test_user):
        """Test recovery token model."""
        with app.app_context():
            expires_at = datetime.utcnow() + timedelta(hours=24)
            recovery = MFARecoveryToken(
                user_id=test_user.id,
                token='recovery_token_123',
                ip_address='192.168.1.1',
                expires_at=expires_at
            )
            db.session.add(recovery)
            db.session.commit()
            
            retrieved = MFARecoveryToken.query.filter_by(user_id=test_user.id).first()
            assert retrieved.verify_token('recovery_token_123') is True
            assert retrieved.verify_token('wrong_token') is False
            assert retrieved.is_expired() is False
            assert retrieved.is_used is False


class TestUserMFAMethods:
    """Test User model MFA-related methods."""
    
    def test_has_mfa_enabled(self, app, test_user):
        """Test MFA enabled check."""
        with app.app_context():
            # Initially no MFA
            assert test_user.has_mfa_enabled() is False
            
            # Add disabled MFA method
            mfa_method = MFAMethod(
                user_id=test_user.id,
                method_type='totp',
                is_enabled=False
            )
            db.session.add(mfa_method)
            db.session.commit()
            
            assert test_user.has_mfa_enabled() is False
            
            # Enable MFA method
            mfa_method.is_enabled = True
            db.session.commit()
            
            assert test_user.has_mfa_enabled() is True
    
    def test_get_enabled_mfa_methods(self, app, test_user):
        """Test getting enabled MFA methods."""
        with app.app_context():
            # Add multiple MFA methods
            totp_method = MFAMethod(
                user_id=test_user.id,
                method_type='totp',
                is_enabled=True
            )
            sms_method = MFAMethod(
                user_id=test_user.id,
                method_type='sms',
                is_enabled=False
            )
            email_method = MFAMethod(
                user_id=test_user.id,
                method_type='email',
                is_enabled=True
            )
            
            db.session.add_all([totp_method, sms_method, email_method])
            db.session.commit()
            
            enabled_methods = test_user.get_enabled_mfa_methods()
            assert len(enabled_methods) == 2
            
            method_types = [method.method_type for method in enabled_methods]
            assert 'totp' in method_types
            assert 'email' in method_types
            assert 'sms' not in method_types
    
    def test_get_mfa_method(self, app, test_user):
        """Test getting specific MFA method."""
        with app.app_context():
            totp_method = MFAMethod(
                user_id=test_user.id,
                method_type='totp',
                is_enabled=True
            )
            db.session.add(totp_method)
            db.session.commit()
            
            retrieved = test_user.get_mfa_method('totp')
            assert retrieved is not None
            assert retrieved.method_type == 'totp'
            
            # Test non-existent method
            assert test_user.get_mfa_method('sms') is None
    
    def test_get_unused_backup_codes(self, app, test_user):
        """Test getting unused backup codes."""
        with app.app_context():
            # Add backup codes
            code1 = MFABackupCode(test_user.id, 'CODE-0001')
            code2 = MFABackupCode(test_user.id, 'CODE-0002')
            code3 = MFABackupCode(test_user.id, 'CODE-0003')
            
            db.session.add_all([code1, code2, code3])
            db.session.commit()
            
            # All codes should be unused initially
            unused = test_user.get_unused_backup_codes()
            assert len(unused) == 3
            
            # Mark one as used
            code2.mark_used()
            db.session.commit()
            
            unused = test_user.get_unused_backup_codes()
            assert len(unused) == 2
    
    def test_user_to_dict_with_mfa(self, app, test_user):
        """Test user dictionary representation with MFA info."""
        with app.app_context():
            # Add MFA method
            mfa_method = MFAMethod(
                user_id=test_user.id,
                method_type='totp',
                is_enabled=True,
                is_verified=True
            )
            db.session.add(mfa_method)
            db.session.commit()
            
            user_dict = test_user.to_dict()
            
            assert 'mfa_enabled' in user_dict
            assert user_dict['mfa_enabled'] is True
            assert 'mfa_methods' in user_dict
            assert len(user_dict['mfa_methods']) == 1
            assert user_dict['mfa_methods'][0]['method_type'] == 'totp'


class TestMFAIntegration:
    """Test MFA integration scenarios."""
    
    def test_complete_totp_setup_flow(self, app, test_user, mfa_service):
        """Test complete TOTP setup flow."""
        with app.app_context():
            # Generate TOTP secret
            secret, provisioning_uri = mfa_service.generate_totp_secret(
                test_user.id, 
                test_user.username
            )
            
            # Encrypt and store secret
            encrypted_secret = mfa_service.encrypt_sensitive_data(secret)
            
            # Create MFA method
            mfa_method = MFAMethod(
                user_id=test_user.id,
                method_type='totp',
                totp_secret=encrypted_secret
            )
            db.session.add(mfa_method)
            db.session.commit()
            
            # Generate valid TOTP token
            totp = pyotp.TOTP(secret)
            valid_token = totp.now()
            
            # Verify token
            decrypted_secret = mfa_service.decrypt_sensitive_data(encrypted_secret)
            is_valid = mfa_service.verify_totp_token(decrypted_secret, valid_token)
            
            assert is_valid is True
            
            # Enable MFA after successful verification
            mfa_method.is_enabled = True
            mfa_method.is_verified = True
            db.session.commit()
            
            assert test_user.has_mfa_enabled() is True
    
    def test_backup_code_recovery_flow(self, app, test_user, mfa_service):
        """Test backup code recovery flow."""
        with app.app_context():
            # Generate backup codes
            backup_codes = mfa_service.generate_backup_codes(3)
            
            # Store backup codes
            for code in backup_codes:
                backup_code_obj = MFABackupCode(test_user.id, code)
                db.session.add(backup_code_obj)
            
            db.session.commit()
            
            # Use one backup code
            user_codes = [code.code_hash for code in test_user.backup_codes]
            
            # Find the backup code object and verify
            backup_code_obj = test_user.backup_codes[0]
            original_code = backup_codes[0]  # We know the original code
            
            assert backup_code_obj.verify_code(original_code) is True
            
            # Mark as used
            backup_code_obj.mark_used()
            db.session.commit()
            
            # Verify it's marked as used
            assert backup_code_obj.is_used is True
            
            # Verify unused codes count decreased
            unused_codes = test_user.get_unused_backup_codes()
            assert len(unused_codes) == 2


if __name__ == '__main__':
    pytest.main([__file__, '-v'])