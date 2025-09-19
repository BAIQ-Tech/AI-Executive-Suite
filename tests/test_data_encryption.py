"""
Test Suite for Data Encryption and Protection System

Tests field-level encryption, data classification, retention policies, and secure deletion.
"""

import pytest
import os
import sys
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask
from models import db, DataProtectionRecord, EncryptedField, DataRetentionJob
from services.data_encryption import DataEncryptionService, DataClassification, RetentionPolicy


@pytest.fixture
def app():
    """Create test Flask application."""
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'test-secret-key'
    app.config['DATA_ENCRYPTION_MASTER_KEY'] = 'test-master-key-32-bytes-long-exactly'
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
def encryption_service(app):
    """Create encryption service instance."""
    with app.app_context():
        return DataEncryptionService()


class TestDataEncryptionService:
    """Test data encryption service functionality."""
    
    def test_field_encryption_decryption(self, encryption_service):
        """Test field-level encryption and decryption."""
        original_data = "sensitive information"
        classification = DataClassification.CONFIDENTIAL
        
        # Encrypt data
        encrypted_data = encryption_service.encrypt_field(original_data, classification)
        assert encrypted_data != original_data
        assert len(encrypted_data) > 0
        
        # Decrypt data
        decrypted_data = encryption_service.decrypt_field(encrypted_data, classification)
        assert decrypted_data == original_data
    
    def test_different_classification_encryption(self, encryption_service):
        """Test encryption with different classification levels."""
        original_data = "test data"
        
        # Test all classification levels
        for classification in DataClassification:
            encrypted = encryption_service.encrypt_field(original_data, classification)
            decrypted = encryption_service.decrypt_field(encrypted, classification)
            assert decrypted == original_data
    
    def test_empty_data_handling(self, encryption_service):
        """Test handling of empty or None data."""
        assert encryption_service.encrypt_field("") == ""
        assert encryption_service.encrypt_field(None) is None
        assert encryption_service.decrypt_field("") == ""
        assert encryption_service.decrypt_field(None) is None
    
    def test_data_hashing(self, encryption_service):
        """Test secure data hashing for searchability."""
        original_data = "searchable data"
        
        # Create hash
        hash_value, salt = encryption_service.hash_data(original_data)
        assert len(hash_value) > 0
        assert len(salt) > 0
        
        # Verify hash
        is_valid = encryption_service.verify_hash(original_data, hash_value, salt)
        assert is_valid is True
        
        # Test with wrong data
        is_invalid = encryption_service.verify_hash("wrong data", hash_value, salt)
        assert is_invalid is False
    
    def test_data_classification(self, encryption_service):
        """Test automatic data classification."""
        # Test restricted data
        ssn_data = "123-45-6789"
        classification = encryption_service.classify_data(ssn_data)
        assert classification == DataClassification.RESTRICTED
        
        # Test confidential data
        password_data = "password: secret123"
        classification = encryption_service.classify_data(password_data)
        assert classification == DataClassification.CONFIDENTIAL
        
        # Test internal data
        internal_data = "internal meeting notes"
        classification = encryption_service.classify_data(internal_data)
        assert classification == DataClassification.INTERNAL
        
        # Test with context
        context = {'field_name': 'credit_card_number'}
        classification = encryption_service.classify_data("4111111111111111", context)
        assert classification == DataClassification.RESTRICTED
    
    def test_retention_policies(self, encryption_service):
        """Test retention policy determination."""
        # Test classification-based policies
        policy = encryption_service.get_retention_policy(DataClassification.PUBLIC)
        assert policy == RetentionPolicy.PERMANENT
        
        policy = encryption_service.get_retention_policy(DataClassification.CONFIDENTIAL)
        assert policy == RetentionPolicy.MEDIUM_TERM
        
        # Test data type-based policies
        policy = encryption_service.get_retention_policy(DataClassification.INTERNAL, 'audit_log')
        assert policy == RetentionPolicy.LONG_TERM
        
        policy = encryption_service.get_retention_policy(DataClassification.INTERNAL, 'session')
        assert policy == RetentionPolicy.SHORT_TERM
    
    def test_retention_date_calculation(self, encryption_service):
        """Test retention date calculation."""
        created_date = datetime(2024, 1, 1)
        
        # Test short term (30 days)
        deletion_date = encryption_service.calculate_retention_date(
            RetentionPolicy.SHORT_TERM, created_date
        )
        expected_date = created_date + timedelta(days=30)
        assert deletion_date == expected_date
        
        # Test medium term (1 year)
        deletion_date = encryption_service.calculate_retention_date(
            RetentionPolicy.MEDIUM_TERM, created_date
        )
        expected_date = created_date + timedelta(days=365)
        assert deletion_date == expected_date
        
        # Test permanent (no deletion)
        deletion_date = encryption_service.calculate_retention_date(
            RetentionPolicy.PERMANENT, created_date
        )
        assert deletion_date is None
    
    def test_protection_metadata_creation(self, encryption_service):
        """Test creation of data protection metadata."""
        data = "sensitive user data"
        context = {
            'data_type': 'user_data',
            'field_name': 'personal_info'
        }
        
        metadata = encryption_service.create_data_protection_metadata(data, context)
        
        assert 'classification' in metadata
        assert 'retention_policy' in metadata
        assert 'created_date' in metadata
        assert 'encryption_used' in metadata
        assert metadata['encryption_used'] is True
    
    def test_retention_compliance_check(self, encryption_service):
        """Test retention compliance checking."""
        # Test data within retention period
        future_date = datetime.utcnow() + timedelta(days=30)
        metadata = {'deletion_date': future_date.isoformat()}
        
        compliance = encryption_service.check_retention_compliance(metadata)
        assert compliance['should_delete'] is False
        assert compliance['days_remaining'] > 0
        
        # Test data past retention period
        past_date = datetime.utcnow() - timedelta(days=30)
        metadata = {'deletion_date': past_date.isoformat()}
        
        compliance = encryption_service.check_retention_compliance(metadata)
        assert compliance['should_delete'] is True
        assert 'days_overdue' in compliance
        
        # Test permanent retention
        metadata = {'deletion_date': None}
        compliance = encryption_service.check_retention_compliance(metadata)
        assert compliance['should_delete'] is False
    
    def test_protection_report_generation(self, encryption_service):
        """Test data protection report generation."""
        # Create sample data items
        data_items = [
            {
                'metadata': {
                    'classification': 'confidential',
                    'retention_policy': 'medium_term',
                    'deletion_date': (datetime.utcnow() + timedelta(days=30)).isoformat(),
                    'encryption_used': True
                }
            },
            {
                'metadata': {
                    'classification': 'restricted',
                    'retention_policy': 'long_term',
                    'deletion_date': (datetime.utcnow() - timedelta(days=1)).isoformat(),
                    'encryption_used': True
                }
            }
        ]
        
        report = encryption_service.generate_data_protection_report(data_items)
        
        assert report['total_items'] == 2
        assert report['encrypted_items'] == 2
        assert report['items_due_for_deletion'] == 1
        assert 'classification_breakdown' in report
        assert 'retention_breakdown' in report


class TestDataProtectionModels:
    """Test data protection database models."""
    
    def test_data_protection_record_creation(self, app):
        """Test DataProtectionRecord model creation."""
        with app.app_context():
            record = DataProtectionRecord(
                data_type='user_data',
                data_id='user_123',
                classification='confidential',
                retention_policy='medium_term',
                is_encrypted=True,
                deletion_date=datetime.utcnow() + timedelta(days=365)
            )
            
            db.session.add(record)
            db.session.commit()
            
            retrieved = DataProtectionRecord.query.first()
            assert retrieved.data_type == 'user_data'
            assert retrieved.classification == 'confidential'
            assert retrieved.is_encrypted is True
    
    def test_access_tracking(self, app):
        """Test access tracking functionality."""
        with app.app_context():
            record = DataProtectionRecord(
                data_type='test_data',
                data_id='test_123',
                classification='internal',
                retention_policy='short_term'
            )
            
            db.session.add(record)
            db.session.commit()
            
            # Track access
            initial_count = record.access_count
            record.update_access()
            db.session.commit()
            
            assert record.access_count == initial_count + 1
            assert record.last_accessed is not None
    
    def test_deletion_tracking(self, app):
        """Test deletion tracking functionality."""
        with app.app_context():
            record = DataProtectionRecord(
                data_type='test_data',
                data_id='test_123',
                classification='internal',
                retention_policy='short_term'
            )
            
            db.session.add(record)
            db.session.commit()
            
            # Mark as deleted
            record.mark_deleted('retention_policy')
            db.session.commit()
            
            assert record.is_deleted is True
            assert record.deleted_at is not None
            assert record.deletion_reason == 'retention_policy'
    
    def test_retention_due_check(self, app):
        """Test retention due date checking."""
        with app.app_context():
            # Create record due for deletion
            past_date = datetime.utcnow() - timedelta(days=1)
            record = DataProtectionRecord(
                data_type='test_data',
                data_id='test_123',
                classification='internal',
                retention_policy='short_term',
                deletion_date=past_date
            )
            
            db.session.add(record)
            db.session.commit()
            
            assert record.is_due_for_deletion() is True
            assert record.days_until_deletion() < 0  # Negative means overdue
    
    def test_encrypted_field_model(self, app):
        """Test EncryptedField model."""
        with app.app_context():
            encrypted_field = EncryptedField(
                table_name='users',
                record_id=123,
                field_name='email',
                encrypted_value='encrypted_email_data',
                classification='confidential'
            )
            
            db.session.add(encrypted_field)
            db.session.commit()
            
            retrieved = EncryptedField.query.first()
            assert retrieved.table_name == 'users'
            assert retrieved.field_name == 'email'
            assert retrieved.classification == 'confidential'
    
    def test_retention_job_model(self, app):
        """Test DataRetentionJob model."""
        with app.app_context():
            job = DataRetentionJob(
                job_type='retention_check',
                data_type='user_data'
            )
            
            db.session.add(job)
            db.session.commit()
            
            # Start job
            job.start_job()
            assert job.status == 'running'
            assert job.started_at is not None
            
            # Complete job
            job.complete_job(items_processed=10, items_deleted=5, items_failed=1)
            assert job.status == 'completed'
            assert job.items_processed == 10
            assert job.items_deleted == 5
            assert job.items_failed == 1
            
            # Test failure
            job2 = DataRetentionJob(job_type='secure_delete')
            db.session.add(job2)
            db.session.commit()
            
            job2.fail_job('Test error message')
            assert job2.status == 'failed'
            assert job2.error_message == 'Test error message'


class TestDataProtectionIntegration:
    """Test integration scenarios for data protection."""
    
    def test_complete_encryption_workflow(self, app, encryption_service):
        """Test complete encryption workflow with database tracking."""
        with app.app_context():
            # Original data
            sensitive_data = "user@example.com"
            context = {
                'data_type': 'user_data',
                'data_id': 'user_123',
                'field_name': 'email'
            }
            
            # Classify data
            classification = encryption_service.classify_data(sensitive_data, context)
            
            # Encrypt data
            encrypted_data = encryption_service.encrypt_field(sensitive_data, classification)
            
            # Create hash for searchability
            data_hash, salt = encryption_service.hash_data(sensitive_data)
            
            # Create protection record
            retention_policy = encryption_service.get_retention_policy(classification, context['data_type'])
            deletion_date = encryption_service.calculate_retention_date(retention_policy)
            
            record = DataProtectionRecord(
                data_type=context['data_type'],
                data_id=context['data_id'],
                classification=classification.value,
                retention_policy=retention_policy.value,
                is_encrypted=True,
                data_hash=data_hash,
                hash_salt=salt,
                deletion_date=deletion_date
            )
            
            db.session.add(record)
            db.session.commit()
            
            # Verify record was created
            assert record.id is not None
            assert record.is_encrypted is True
            
            # Test decryption
            decrypted_data = encryption_service.decrypt_field(encrypted_data, classification)
            assert decrypted_data == sensitive_data
            
            # Test hash verification
            is_valid = encryption_service.verify_hash(sensitive_data, data_hash, salt)
            assert is_valid is True
    
    def test_retention_cleanup_workflow(self, app, encryption_service):
        """Test retention-based cleanup workflow."""
        with app.app_context():
            # Create records with different retention periods
            records = []
            
            # Record due for deletion
            past_date = datetime.utcnow() - timedelta(days=1)
            record1 = DataProtectionRecord(
                data_type='session_data',
                data_id='session_123',
                classification='internal',
                retention_policy='short_term',
                deletion_date=past_date
            )
            records.append(record1)
            
            # Record not due for deletion
            future_date = datetime.utcnow() + timedelta(days=30)
            record2 = DataProtectionRecord(
                data_type='user_data',
                data_id='user_456',
                classification='confidential',
                retention_policy='medium_term',
                deletion_date=future_date
            )
            records.append(record2)
            
            # Permanent record
            record3 = DataProtectionRecord(
                data_type='public_data',
                data_id='public_789',
                classification='public',
                retention_policy='permanent',
                deletion_date=None
            )
            records.append(record3)
            
            db.session.add_all(records)
            db.session.commit()
            
            # Check which records are due for deletion
            due_records = []
            for record in records:
                if record.is_due_for_deletion():
                    due_records.append(record)
            
            assert len(due_records) == 1
            assert due_records[0].data_id == 'session_123'
            
            # Simulate deletion process
            for record in due_records:
                success = encryption_service.secure_delete_data(record.data_id, record.data_type)
                if success:
                    record.mark_deleted('retention_policy')
            
            db.session.commit()
            
            # Verify deletion tracking
            deleted_record = DataProtectionRecord.query.filter_by(data_id='session_123').first()
            assert deleted_record.is_deleted is True
            assert deleted_record.deletion_reason == 'retention_policy'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])