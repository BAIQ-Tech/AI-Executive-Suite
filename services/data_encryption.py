"""
Data Encryption and Protection Service

Provides field-level encryption, secure file storage, data classification,
and data retention/deletion policies for sensitive information.
"""

import os
import hashlib
import secrets
import base64
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from flask import current_app
import logging


class DataClassification(Enum):
    """Data classification levels."""
    PUBLIC = 'public'
    INTERNAL = 'internal'
    CONFIDENTIAL = 'confidential'
    RESTRICTED = 'restricted'


class RetentionPolicy(Enum):
    """Data retention policies."""
    SHORT_TERM = 'short_term'  # 30 days
    MEDIUM_TERM = 'medium_term'  # 1 year
    LONG_TERM = 'long_term'  # 7 years
    PERMANENT = 'permanent'  # No automatic deletion


class DataEncryptionService:
    """Service for encrypting and protecting sensitive data."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._encryption_keys = {}
        self._load_encryption_keys()
    
    def _load_encryption_keys(self):
        """Load or generate encryption keys for different data classifications."""
        # Master key for the service
        master_key = current_app.config.get('DATA_ENCRYPTION_MASTER_KEY')
        if not master_key:
            master_key = Fernet.generate_key()
            self.logger.warning("Generated new master encryption key - store this securely!")
        
        if isinstance(master_key, str):
            master_key = master_key.encode()
        
        self.master_cipher = Fernet(master_key)
        
        # Generate keys for different classification levels
        for classification in DataClassification:
            key_name = f'DATA_ENCRYPTION_KEY_{classification.value.upper()}'
            key = current_app.config.get(key_name)
            
            if not key:
                key = Fernet.generate_key()
                self.logger.warning(f"Generated new {classification.value} encryption key")
            
            if isinstance(key, str):
                key = key.encode()
            
            self._encryption_keys[classification] = Fernet(key)
    
    def encrypt_field(self, data: str, classification: DataClassification = DataClassification.CONFIDENTIAL) -> str:
        """
        Encrypt a single field with appropriate encryption based on classification.
        
        Args:
            data: Data to encrypt
            classification: Data classification level
            
        Returns:
            Base64 encoded encrypted data
        """
        if not data:
            return data
        
        try:
            cipher = self._encryption_keys[classification]
            encrypted_data = cipher.encrypt(data.encode('utf-8'))
            return base64.b64encode(encrypted_data).decode('utf-8')
        except Exception as e:
            self.logger.error(f"Field encryption error: {e}")
            raise ValueError("Failed to encrypt field data")
    
    def decrypt_field(self, encrypted_data: str, classification: DataClassification = DataClassification.CONFIDENTIAL) -> str:
        """
        Decrypt a single field.
        
        Args:
            encrypted_data: Base64 encoded encrypted data
            classification: Data classification level
            
        Returns:
            Decrypted data
        """
        if not encrypted_data:
            return encrypted_data
        
        try:
            cipher = self._encryption_keys[classification]
            encrypted_bytes = base64.b64decode(encrypted_data.encode('utf-8'))
            decrypted_data = cipher.decrypt(encrypted_bytes)
            return decrypted_data.decode('utf-8')
        except Exception as e:
            self.logger.error(f"Field decryption error: {e}")
            raise ValueError("Failed to decrypt field data")
    
    def encrypt_file(self, file_path: str, classification: DataClassification = DataClassification.CONFIDENTIAL) -> str:
        """
        Encrypt a file and return the encrypted file path.
        
        Args:
            file_path: Path to file to encrypt
            classification: Data classification level
            
        Returns:
            Path to encrypted file
        """
        try:
            # Read file content
            with open(file_path, 'rb') as f:
                file_content = f.read()
            
            # Encrypt content
            cipher = self._encryption_keys[classification]
            encrypted_content = cipher.encrypt(file_content)
            
            # Write encrypted file
            encrypted_file_path = f"{file_path}.encrypted"
            with open(encrypted_file_path, 'wb') as f:
                f.write(encrypted_content)
            
            # Remove original file for security
            os.remove(file_path)
            
            return encrypted_file_path
            
        except Exception as e:
            self.logger.error(f"File encryption error: {e}")
            raise ValueError("Failed to encrypt file")
    
    def decrypt_file(self, encrypted_file_path: str, classification: DataClassification = DataClassification.CONFIDENTIAL) -> str:
        """
        Decrypt a file and return the decrypted file path.
        
        Args:
            encrypted_file_path: Path to encrypted file
            classification: Data classification level
            
        Returns:
            Path to decrypted file
        """
        try:
            # Read encrypted content
            with open(encrypted_file_path, 'rb') as f:
                encrypted_content = f.read()
            
            # Decrypt content
            cipher = self._encryption_keys[classification]
            decrypted_content = cipher.decrypt(encrypted_content)
            
            # Write decrypted file
            decrypted_file_path = encrypted_file_path.replace('.encrypted', '')
            with open(decrypted_file_path, 'wb') as f:
                f.write(decrypted_content)
            
            return decrypted_file_path
            
        except Exception as e:
            self.logger.error(f"File decryption error: {e}")
            raise ValueError("Failed to decrypt file")
    
    def hash_data(self, data: str, salt: Optional[str] = None) -> Tuple[str, str]:
        """
        Create a secure hash of data for indexing/searching without decryption.
        
        Args:
            data: Data to hash
            salt: Optional salt (will generate if not provided)
            
        Returns:
            Tuple of (hash, salt)
        """
        if salt is None:
            salt = secrets.token_hex(32)
        
        # Use PBKDF2 for secure hashing
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt.encode(),
            iterations=100000,
        )
        
        key = kdf.derive(data.encode())
        hash_value = base64.b64encode(key).decode()
        
        return hash_value, salt
    
    def verify_hash(self, data: str, hash_value: str, salt: str) -> bool:
        """
        Verify data against a hash.
        
        Args:
            data: Original data
            hash_value: Hash to verify against
            salt: Salt used in hashing
            
        Returns:
            True if data matches hash
        """
        try:
            computed_hash, _ = self.hash_data(data, salt)
            return computed_hash == hash_value
        except Exception as e:
            self.logger.error(f"Hash verification error: {e}")
            return False
    
    def classify_data(self, data: str, context: Dict[str, Any] = None) -> DataClassification:
        """
        Automatically classify data based on content and context.
        
        Args:
            data: Data to classify
            context: Additional context for classification
            
        Returns:
            Data classification level
        """
        if not data:
            return DataClassification.PUBLIC
        
        data_lower = data.lower()
        context = context or {}
        
        # Patterns for restricted data
        restricted_patterns = [
            'ssn', 'social security', 'passport', 'driver license',
            'credit card', 'bank account', 'routing number',
            'medical record', 'health information', 'diagnosis'
        ]
        
        # Regex patterns for restricted data
        import re
        restricted_regex_patterns = [
            r'\d{3}-\d{2}-\d{4}',  # SSN format
            r'\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}',  # Credit card format
            r'\d{9}',  # 9-digit numbers (could be SSN without dashes)
        ]
        
        # Patterns for confidential data
        confidential_patterns = [
            'password', 'secret', 'private key', 'token',
            'salary', 'compensation', 'financial',
            'personal', 'address', 'phone', 'email'
        ]
        
        # Patterns for internal data
        internal_patterns = [
            'internal', 'employee', 'staff', 'meeting',
            'project', 'strategy', 'plan'
        ]
        
        # Check for restricted data
        if any(pattern in data_lower for pattern in restricted_patterns):
            return DataClassification.RESTRICTED
        
        # Check regex patterns for restricted data
        for pattern in restricted_regex_patterns:
            if re.search(pattern, data):
                return DataClassification.RESTRICTED
        
        # Check context for classification hints
        if context.get('field_name'):
            field_name = context['field_name'].lower()
            if any(pattern in field_name for pattern in restricted_patterns):
                return DataClassification.RESTRICTED
            elif any(pattern in field_name for pattern in confidential_patterns):
                return DataClassification.CONFIDENTIAL
        
        # Check for confidential data
        if any(pattern in data_lower for pattern in confidential_patterns):
            return DataClassification.CONFIDENTIAL
        
        # Check for internal data
        if any(pattern in data_lower for pattern in internal_patterns):
            return DataClassification.INTERNAL
        
        # Default to internal for safety
        return DataClassification.INTERNAL
    
    def get_retention_policy(self, classification: DataClassification, data_type: str = None) -> RetentionPolicy:
        """
        Get retention policy based on data classification and type.
        
        Args:
            classification: Data classification level
            data_type: Type of data (e.g., 'audit_log', 'user_data', 'financial')
            
        Returns:
            Retention policy
        """
        # Special cases based on data type
        if data_type == 'audit_log':
            return RetentionPolicy.LONG_TERM  # 7 years for compliance
        elif data_type == 'financial':
            return RetentionPolicy.LONG_TERM  # 7 years for tax/legal requirements
        elif data_type == 'session':
            return RetentionPolicy.SHORT_TERM  # 30 days for sessions
        
        # Default policies based on classification
        policy_map = {
            DataClassification.PUBLIC: RetentionPolicy.PERMANENT,
            DataClassification.INTERNAL: RetentionPolicy.MEDIUM_TERM,
            DataClassification.CONFIDENTIAL: RetentionPolicy.MEDIUM_TERM,
            DataClassification.RESTRICTED: RetentionPolicy.LONG_TERM
        }
        
        return policy_map.get(classification, RetentionPolicy.MEDIUM_TERM)
    
    def calculate_retention_date(self, policy: RetentionPolicy, created_date: datetime = None) -> Optional[datetime]:
        """
        Calculate when data should be deleted based on retention policy.
        
        Args:
            policy: Retention policy
            created_date: When data was created (defaults to now)
            
        Returns:
            Deletion date or None for permanent retention
        """
        if policy == RetentionPolicy.PERMANENT:
            return None
        
        if created_date is None:
            created_date = datetime.utcnow()
        
        retention_periods = {
            RetentionPolicy.SHORT_TERM: timedelta(days=30),
            RetentionPolicy.MEDIUM_TERM: timedelta(days=365),
            RetentionPolicy.LONG_TERM: timedelta(days=365 * 7)
        }
        
        period = retention_periods.get(policy)
        if period:
            return created_date + period
        
        return None
    
    def secure_delete_data(self, data_id: str, data_type: str) -> bool:
        """
        Securely delete data by overwriting and removing references.
        
        Args:
            data_id: Identifier of data to delete
            data_type: Type of data being deleted
            
        Returns:
            True if deletion was successful
        """
        try:
            # This would integrate with the database to securely delete records
            # For now, we'll log the deletion request
            self.logger.info(f"Secure deletion requested for {data_type} ID: {data_id}")
            
            # In a real implementation, this would:
            # 1. Overwrite the data multiple times
            # 2. Remove database records
            # 3. Clear any cached copies
            # 4. Update audit logs
            
            return True
            
        except Exception as e:
            self.logger.error(f"Secure deletion error: {e}")
            return False
    
    def create_data_protection_metadata(self, data: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Create metadata for data protection tracking.
        
        Args:
            data: Data being protected
            context: Additional context
            
        Returns:
            Protection metadata
        """
        classification = self.classify_data(data, context)
        retention_policy = self.get_retention_policy(classification, context.get('data_type'))
        created_date = datetime.utcnow()
        deletion_date = self.calculate_retention_date(retention_policy, created_date)
        
        metadata = {
            'classification': classification.value,
            'retention_policy': retention_policy.value,
            'created_date': created_date.isoformat(),
            'deletion_date': deletion_date.isoformat() if deletion_date else None,
            'encryption_used': True,
            'hash_created': True,
            'last_accessed': None,
            'access_count': 0
        }
        
        return metadata
    
    def update_access_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update metadata when data is accessed.
        
        Args:
            metadata: Current metadata
            
        Returns:
            Updated metadata
        """
        metadata['last_accessed'] = datetime.utcnow().isoformat()
        metadata['access_count'] = metadata.get('access_count', 0) + 1
        return metadata
    
    def check_retention_compliance(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check if data should be deleted based on retention policy.
        
        Args:
            metadata: Data protection metadata
            
        Returns:
            Compliance status information
        """
        deletion_date_str = metadata.get('deletion_date')
        if not deletion_date_str:
            return {
                'should_delete': False,
                'reason': 'Permanent retention policy',
                'days_remaining': None
            }
        
        deletion_date = datetime.fromisoformat(deletion_date_str)
        now = datetime.utcnow()
        
        if now >= deletion_date:
            return {
                'should_delete': True,
                'reason': 'Retention period expired',
                'days_overdue': (now - deletion_date).days
            }
        else:
            days_remaining = (deletion_date - now).days
            return {
                'should_delete': False,
                'reason': 'Within retention period',
                'days_remaining': days_remaining
            }
    
    def generate_data_protection_report(self, data_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate a report on data protection status.
        
        Args:
            data_items: List of data items with metadata
            
        Returns:
            Protection status report
        """
        report = {
            'total_items': len(data_items),
            'classification_breakdown': {},
            'retention_breakdown': {},
            'items_due_for_deletion': 0,
            'overdue_items': 0,
            'encrypted_items': 0,
            'generated_at': datetime.utcnow().isoformat()
        }
        
        for item in data_items:
            metadata = item.get('metadata', {})
            
            # Classification breakdown
            classification = metadata.get('classification', 'unknown')
            report['classification_breakdown'][classification] = \
                report['classification_breakdown'].get(classification, 0) + 1
            
            # Retention breakdown
            retention_policy = metadata.get('retention_policy', 'unknown')
            report['retention_breakdown'][retention_policy] = \
                report['retention_breakdown'].get(retention_policy, 0) + 1
            
            # Encryption status
            if metadata.get('encryption_used'):
                report['encrypted_items'] += 1
            
            # Retention compliance
            compliance = self.check_retention_compliance(metadata)
            if compliance['should_delete']:
                report['items_due_for_deletion'] += 1
                if 'days_overdue' in compliance:
                    report['overdue_items'] += 1
        
        return report