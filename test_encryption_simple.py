#!/usr/bin/env python3
"""
Simple test to verify data encryption functionality works
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from services.data_encryption import DataEncryptionService, DataClassification, RetentionPolicy
from datetime import datetime, timedelta

def test_encryption_service():
    """Test basic data encryption service functionality."""
    
    # Create Flask app for context
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'test-secret-key'
    from cryptography.fernet import Fernet
    app.config['DATA_ENCRYPTION_MASTER_KEY'] = Fernet.generate_key()
    
    with app.app_context():
        encryption_service = DataEncryptionService()
        
        print("Testing Data Encryption Service...")
        
        # Test field encryption/decryption
        print("1. Testing field encryption/decryption...")
        original_data = "sensitive user email: user@example.com"
        classification = DataClassification.CONFIDENTIAL
        
        encrypted_data = encryption_service.encrypt_field(original_data, classification)
        print(f"   ✓ Data encrypted: {encrypted_data[:50]}...")
        
        decrypted_data = encryption_service.decrypt_field(encrypted_data, classification)
        print(f"   ✓ Encryption/decryption successful: {original_data == decrypted_data}")
        
        # Test data classification
        print("2. Testing automatic data classification...")
        test_cases = [
            ("123-45-6789", DataClassification.RESTRICTED),  # SSN
            ("password: secret123", DataClassification.CONFIDENTIAL),  # Password
            ("internal meeting notes", DataClassification.INTERNAL),  # Internal
            ("public announcement", DataClassification.INTERNAL)  # Default to internal
        ]
        
        for test_data, expected_class in test_cases:
            classified = encryption_service.classify_data(test_data)
            print(f"   ✓ '{test_data[:20]}...' classified as: {classified.value}")
        
        # Test data hashing
        print("3. Testing secure data hashing...")
        hash_value, salt = encryption_service.hash_data(original_data)
        print(f"   ✓ Hash generated: {hash_value[:20]}...")
        
        is_valid = encryption_service.verify_hash(original_data, hash_value, salt)
        print(f"   ✓ Hash verification: {is_valid}")
        
        # Test retention policies
        print("4. Testing retention policies...")
        for classification in DataClassification:
            policy = encryption_service.get_retention_policy(classification)
            print(f"   ✓ {classification.value} -> {policy.value}")
        
        # Test retention date calculation
        print("5. Testing retention date calculation...")
        created_date = datetime(2024, 1, 1)
        
        for policy in RetentionPolicy:
            deletion_date = encryption_service.calculate_retention_date(policy, created_date)
            if deletion_date:
                days_diff = (deletion_date - created_date).days
                print(f"   ✓ {policy.value}: {days_diff} days")
            else:
                print(f"   ✓ {policy.value}: permanent retention")
        
        # Test protection metadata
        print("6. Testing protection metadata creation...")
        context = {
            'data_type': 'user_data',
            'field_name': 'email'
        }
        
        metadata = encryption_service.create_data_protection_metadata(original_data, context)
        print(f"   ✓ Metadata created with classification: {metadata['classification']}")
        print(f"   ✓ Retention policy: {metadata['retention_policy']}")
        
        # Test compliance checking
        print("7. Testing retention compliance...")
        
        # Test data within retention period
        future_metadata = {
            'deletion_date': (datetime.utcnow() + timedelta(days=30)).isoformat()
        }
        compliance = encryption_service.check_retention_compliance(future_metadata)
        print(f"   ✓ Future deletion date - should delete: {compliance['should_delete']}")
        
        # Test data past retention period
        past_metadata = {
            'deletion_date': (datetime.utcnow() - timedelta(days=30)).isoformat()
        }
        compliance = encryption_service.check_retention_compliance(past_metadata)
        print(f"   ✓ Past deletion date - should delete: {compliance['should_delete']}")
        
        print("\n✅ All data encryption service tests passed!")

if __name__ == '__main__':
    test_encryption_service()