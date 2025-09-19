from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from decimal import Decimal
import bcrypt
import json
from enum import Enum

# Initialize SQLAlchemy instance
db = SQLAlchemy()

# Enums for better type safety
class DecisionStatus(Enum):
    PENDING = 'pending'
    IN_PROGRESS = 'in_progress'
    COMPLETED = 'completed'
    REJECTED = 'rejected'
    UNDER_REVIEW = 'under_review'

class DecisionPriority(Enum):
    LOW = 'low'
    MEDIUM = 'medium'
    HIGH = 'high'
    CRITICAL = 'critical'

class ExecutiveType(Enum):
    CEO = 'ceo'
    CTO = 'cto'
    CFO = 'cfo'

class RiskLevel(Enum):
    LOW = 'low'
    MEDIUM = 'medium'
    HIGH = 'high'
    CRITICAL = 'critical'

class User(UserMixin, db.Model):
    """User model for authentication system."""
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=True)
    
    # OAuth provider information
    google_id = db.Column(db.String(100), unique=True, nullable=True)
    apple_id = db.Column(db.String(100), unique=True, nullable=True)
    
    # Web3 wallet information
    wallet_address = db.Column(db.String(42), unique=True, nullable=True)
    wallet_type = db.Column(db.String(20), nullable=True)  # 'metamask', 'walletconnect', etc.
    
    # Profile information
    name = db.Column(db.String(100), nullable=True)
    avatar_url = db.Column(db.String(200), nullable=True)
    preferred_language = db.Column(db.String(5), default='en')
    
    # Account status
    is_active = db.Column(db.Boolean, default=True)
    email_verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    
    # AI Executive Suite specific settings
    ai_preferences = db.Column(db.Text, nullable=True)  # JSON string for AI settings
    
    def __init__(self, username, email=None, name=None):
        self.username = username
        self.email = email
        self.name = name or username
        self.ai_preferences = json.dumps({
            'preferred_language': 'en',
            'voice_enabled': False,
            'default_agent': 'ceo'
        })
    
    def set_password(self, password):
        """Hash and set password."""
        if password:
            self.password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def check_password(self, password):
        """Check if provided password matches hash."""
        if not self.password_hash or not password:
            return False
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))
    
    def set_google_id(self, google_id):
        """Set Google OAuth ID."""
        self.google_id = google_id
    
    def set_apple_id(self, apple_id):
        """Set Apple Sign-In ID."""
        self.apple_id = apple_id
    
    def set_wallet(self, wallet_address, wallet_type='metamask'):
        """Set Web3 wallet information."""
        self.wallet_address = wallet_address.lower()
        self.wallet_type = wallet_type
    
    def get_ai_preferences(self):
        """Get AI preferences as dictionary."""
        if self.ai_preferences:
            return json.loads(self.ai_preferences)
        return {
            'preferred_language': 'en',
            'voice_enabled': False,
            'default_agent': 'ceo'
        }
    
    def set_ai_preferences(self, preferences):
        """Set AI preferences from dictionary."""
        self.ai_preferences = json.dumps(preferences)
    
    def update_last_login(self):
        """Update last login timestamp."""
        self.last_login = datetime.utcnow()
    
    def has_mfa_enabled(self):
        """Check if user has any MFA method enabled."""
        return any(method.is_enabled for method in self.mfa_methods)
    
    def get_enabled_mfa_methods(self):
        """Get list of enabled MFA methods."""
        return [method for method in self.mfa_methods if method.is_enabled]
    
    def get_mfa_method(self, method_type):
        """Get specific MFA method by type."""
        for method in self.mfa_methods:
            if method.method_type == method_type:
                return method
        return None
    
    def get_unused_backup_codes(self):
        """Get list of unused backup codes."""
        return [code for code in self.backup_codes if not code.is_used]
    
    def to_dict(self):
        """Convert user to dictionary for JSON responses."""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'name': self.name,
            'avatar_url': self.avatar_url,
            'preferred_language': self.preferred_language,
            'is_active': self.is_active,
            'email_verified': self.email_verified,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'has_google': bool(self.google_id),
            'has_apple': bool(self.apple_id),
            'has_wallet': bool(self.wallet_address),
            'wallet_type': self.wallet_type,
            'ai_preferences': self.get_ai_preferences(),
            'mfa_enabled': self.has_mfa_enabled(),
            'mfa_methods': [method.to_dict() for method in self.get_enabled_mfa_methods()]
        }

class LoginAttempt(db.Model):
    """Track login attempts for security."""
    
    id = db.Column(db.Integer, primary_key=True)
    ip_address = db.Column(db.String(45), nullable=False)
    email = db.Column(db.String(120), nullable=True)
    wallet_address = db.Column(db.String(42), nullable=True)
    success = db.Column(db.Boolean, default=False)
    method = db.Column(db.String(20), nullable=False)  # 'email', 'google', 'apple', 'web3'
    user_agent = db.Column(db.String(200), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __init__(self, ip_address, method, email=None, wallet_address=None, success=False, user_agent=None):
        self.ip_address = ip_address
        self.method = method
        self.email = email
        self.wallet_address = wallet_address
        self.success = success
        self.user_agent = user_agent

class UserSession(db.Model):
    """Track active user sessions."""
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    session_token = db.Column(db.String(128), unique=True, nullable=False)
    ip_address = db.Column(db.String(45), nullable=False)
    user_agent = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_activity = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    
    user = db.relationship('User', backref=db.backref('sessions', lazy=True))
    
    def __init__(self, user_id, session_token, ip_address, expires_at, user_agent=None):
        self.user_id = user_id
        self.session_token = session_token
        self.ip_address = ip_address
        self.expires_at = expires_at
        self.user_agent = user_agent
    
    def is_expired(self):
        """Check if session is expired."""
        return datetime.utcnow() > self.expires_at
    
    def update_activity(self):
        """Update last activity timestamp."""
        self.last_activity = datetime.utcnow()


class MFAMethod(db.Model):
    """Multi-Factor Authentication methods for users."""
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    method_type = db.Column(db.String(20), nullable=False)  # 'totp', 'sms', 'email'
    is_enabled = db.Column(db.Boolean, default=False)
    is_verified = db.Column(db.Boolean, default=False)
    
    # TOTP specific fields
    totp_secret = db.Column(db.Text, nullable=True)  # Encrypted TOTP secret
    
    # SMS/Email specific fields
    phone_number = db.Column(db.String(20), nullable=True)  # For SMS
    email_address = db.Column(db.String(120), nullable=True)  # For email MFA (can be different from login email)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_used = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('mfa_methods', lazy=True, cascade='all, delete-orphan'))
    
    def __init__(self, user_id, method_type, **kwargs):
        self.user_id = user_id
        self.method_type = method_type
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def to_dict(self):
        """Convert MFA method to dictionary."""
        return {
            'id': self.id,
            'method_type': self.method_type,
            'is_enabled': self.is_enabled,
            'is_verified': self.is_verified,
            'phone_number': self.phone_number[-4:] if self.phone_number else None,  # Only show last 4 digits
            'email_address': self._mask_email(self.email_address) if self.email_address else None,
            'created_at': self.created_at.isoformat(),
            'last_used': self.last_used.isoformat() if self.last_used else None
        }
    
    def _mask_email(self, email):
        """Mask email address for security."""
        if not email or '@' not in email:
            return email
        
        local, domain = email.split('@', 1)
        if len(local) <= 2:
            masked_local = '*' * len(local)
        else:
            masked_local = local[0] + '*' * (len(local) - 2) + local[-1]
        
        return f"{masked_local}@{domain}"


class MFABackupCode(db.Model):
    """Backup codes for MFA recovery."""
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    code_hash = db.Column(db.String(128), nullable=False)  # Hashed backup code
    is_used = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    used_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('backup_codes', lazy=True, cascade='all, delete-orphan'))
    
    def __init__(self, user_id, code):
        self.user_id = user_id
        self.set_code(code)
    
    def set_code(self, code):
        """Hash and set backup code."""
        self.code_hash = bcrypt.hashpw(code.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def verify_code(self, code):
        """Verify backup code."""
        return bcrypt.checkpw(code.encode('utf-8'), self.code_hash.encode('utf-8'))
    
    def mark_used(self):
        """Mark backup code as used."""
        self.is_used = True
        self.used_at = datetime.utcnow()


class MFAVerificationAttempt(db.Model):
    """Track MFA verification attempts for security monitoring."""
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    method_type = db.Column(db.String(20), nullable=False)
    ip_address = db.Column(db.String(45), nullable=False)
    user_agent = db.Column(db.String(200), nullable=True)
    success = db.Column(db.Boolean, default=False)
    failure_reason = db.Column(db.String(100), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('mfa_attempts', lazy=True))
    
    def __init__(self, user_id, method_type, ip_address, success=False, failure_reason=None, user_agent=None):
        self.user_id = user_id
        self.method_type = method_type
        self.ip_address = ip_address
        self.success = success
        self.failure_reason = failure_reason
        self.user_agent = user_agent


class MFARecoveryToken(db.Model):
    """Recovery tokens for MFA account recovery."""
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    token_hash = db.Column(db.String(128), nullable=False)  # Hashed recovery token
    is_used = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    used_at = db.Column(db.DateTime, nullable=True)
    ip_address = db.Column(db.String(45), nullable=False)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('recovery_tokens', lazy=True, cascade='all, delete-orphan'))
    
    def __init__(self, user_id, token, ip_address, expires_at):
        self.user_id = user_id
        self.ip_address = ip_address
        self.expires_at = expires_at
        self.set_token(token)
    
    def set_token(self, token):
        """Hash and set recovery token."""
        self.token_hash = bcrypt.hashpw(token.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def verify_token(self, token):
        """Verify recovery token."""
        return bcrypt.checkpw(token.encode('utf-8'), self.token_hash.encode('utf-8'))
    
    def is_expired(self):
        """Check if recovery token is expired."""
        return datetime.utcnow() > self.expires_at
    
    def mark_used(self):
        """Mark recovery token as used."""
        self.is_used = True
        self.used_at = datetime.utcnow()


class PendingMFAVerification(db.Model):
    """Temporary storage for pending MFA verifications (SMS/Email codes)."""
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    method_type = db.Column(db.String(20), nullable=False)  # 'sms', 'email'
    code_hash = db.Column(db.String(128), nullable=False)  # Hashed verification code
    contact_info = db.Column(db.String(120), nullable=False)  # Phone or email
    attempts = db.Column(db.Integer, default=0)
    max_attempts = db.Column(db.Integer, default=3)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('pending_verifications', lazy=True, cascade='all, delete-orphan'))
    
    def __init__(self, user_id, method_type, code, contact_info, expires_at):
        self.user_id = user_id
        self.method_type = method_type
        self.contact_info = contact_info
        self.expires_at = expires_at
        self.set_code(code)
    
    def set_code(self, code):
        """Hash and set verification code."""
        self.code_hash = bcrypt.hashpw(code.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def verify_code(self, code):
        """Verify verification code."""
        return bcrypt.checkpw(code.encode('utf-8'), self.code_hash.encode('utf-8'))
    
    def is_expired(self):
        """Check if verification code is expired."""
        return datetime.utcnow() > self.expires_at
    
    def increment_attempts(self):
        """Increment verification attempts."""
        self.attempts += 1
    
    def is_max_attempts_reached(self):
        """Check if maximum attempts reached."""
        return self.attempts >= self.max_attempts


class DataProtectionRecord(db.Model):
    """Track data protection and encryption status for sensitive data."""
    
    id = db.Column(db.Integer, primary_key=True)
    data_type = db.Column(db.String(50), nullable=False)  # 'user_data', 'decision', 'document', etc.
    data_id = db.Column(db.String(100), nullable=False)  # ID of the protected data
    classification = db.Column(db.String(20), nullable=False)  # 'public', 'internal', 'confidential', 'restricted'
    retention_policy = db.Column(db.String(20), nullable=False)  # 'short_term', 'medium_term', 'long_term', 'permanent'
    
    # Encryption details
    is_encrypted = db.Column(db.Boolean, default=False)
    encryption_algorithm = db.Column(db.String(50), nullable=True)
    key_version = db.Column(db.String(20), nullable=True)
    
    # Hash for searchability without decryption
    data_hash = db.Column(db.String(128), nullable=True)
    hash_salt = db.Column(db.String(64), nullable=True)
    
    # Retention and compliance
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    deletion_date = db.Column(db.DateTime, nullable=True)
    last_accessed = db.Column(db.DateTime, nullable=True)
    access_count = db.Column(db.Integer, default=0)
    
    # Status tracking
    is_deleted = db.Column(db.Boolean, default=False)
    deleted_at = db.Column(db.DateTime, nullable=True)
    deletion_reason = db.Column(db.String(100), nullable=True)
    
    def __init__(self, data_type, data_id, classification, retention_policy, **kwargs):
        self.data_type = data_type
        self.data_id = data_id
        self.classification = classification
        self.retention_policy = retention_policy
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def update_access(self):
        """Update access tracking."""
        self.last_accessed = datetime.utcnow()
        self.access_count += 1
    
    def mark_deleted(self, reason='retention_policy'):
        """Mark record as deleted."""
        self.is_deleted = True
        self.deleted_at = datetime.utcnow()
        self.deletion_reason = reason
    
    def is_due_for_deletion(self):
        """Check if data is due for deletion based on retention policy."""
        if not self.deletion_date:
            return False
        return datetime.utcnow() >= self.deletion_date
    
    def days_until_deletion(self):
        """Calculate days until deletion (negative if overdue)."""
        if not self.deletion_date:
            return None
        delta = self.deletion_date - datetime.utcnow()
        return delta.days
    
    def to_dict(self):
        """Convert to dictionary for JSON responses."""
        return {
            'id': self.id,
            'data_type': self.data_type,
            'data_id': self.data_id,
            'classification': self.classification,
            'retention_policy': self.retention_policy,
            'is_encrypted': self.is_encrypted,
            'encryption_algorithm': self.encryption_algorithm,
            'created_at': self.created_at.isoformat(),
            'deletion_date': self.deletion_date.isoformat() if self.deletion_date else None,
            'last_accessed': self.last_accessed.isoformat() if self.last_accessed else None,
            'access_count': self.access_count,
            'is_deleted': self.is_deleted,
            'days_until_deletion': self.days_until_deletion()
        }


class EncryptedField(db.Model):
    """Store encrypted field data with metadata."""
    
    id = db.Column(db.Integer, primary_key=True)
    table_name = db.Column(db.String(50), nullable=False)
    record_id = db.Column(db.Integer, nullable=False)
    field_name = db.Column(db.String(50), nullable=False)
    
    # Encrypted data
    encrypted_value = db.Column(db.Text, nullable=False)
    classification = db.Column(db.String(20), nullable=False)
    
    # Searchable hash (for finding records without decryption)
    value_hash = db.Column(db.String(128), nullable=True)
    hash_salt = db.Column(db.String(64), nullable=True)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    protection_record_id = db.Column(db.Integer, db.ForeignKey('data_protection_record.id'), nullable=True)
    protection_record = db.relationship('DataProtectionRecord', backref=db.backref('encrypted_fields', lazy=True))
    
    def __init__(self, table_name, record_id, field_name, encrypted_value, classification, **kwargs):
        self.table_name = table_name
        self.record_id = record_id
        self.field_name = field_name
        self.encrypted_value = encrypted_value
        self.classification = classification
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def to_dict(self):
        """Convert to dictionary for JSON responses."""
        return {
            'id': self.id,
            'table_name': self.table_name,
            'record_id': self.record_id,
            'field_name': self.field_name,
            'classification': self.classification,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


class DataRetentionJob(db.Model):
    """Track data retention and deletion jobs."""
    
    id = db.Column(db.Integer, primary_key=True)
    job_type = db.Column(db.String(50), nullable=False)  # 'retention_check', 'secure_delete', 'cleanup'
    status = db.Column(db.String(20), default='pending')  # 'pending', 'running', 'completed', 'failed'
    
    # Job parameters
    data_type = db.Column(db.String(50), nullable=True)
    classification = db.Column(db.String(20), nullable=True)
    retention_policy = db.Column(db.String(20), nullable=True)
    
    # Results
    items_processed = db.Column(db.Integer, default=0)
    items_deleted = db.Column(db.Integer, default=0)
    items_failed = db.Column(db.Integer, default=0)
    error_message = db.Column(db.Text, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    started_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    
    def __init__(self, job_type, **kwargs):
        self.job_type = job_type
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def start_job(self):
        """Mark job as started."""
        self.status = 'running'
        self.started_at = datetime.utcnow()
    
    def complete_job(self, items_processed=0, items_deleted=0, items_failed=0):
        """Mark job as completed."""
        self.status = 'completed'
        self.completed_at = datetime.utcnow()
        self.items_processed = items_processed
        self.items_deleted = items_deleted
        self.items_failed = items_failed
    
    def fail_job(self, error_message):
        """Mark job as failed."""
        self.status = 'failed'
        self.completed_at = datetime.utcnow()
        self.error_message = error_message
    
    def to_dict(self):
        """Convert to dictionary for JSON responses."""
        return {
            'id': self.id,
            'job_type': self.job_type,
            'status': self.status,
            'data_type': self.data_type,
            'classification': self.classification,
            'retention_policy': self.retention_policy,
            'items_processed': self.items_processed,
            'items_deleted': self.items_deleted,
            'items_failed': self.items_failed,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }


# Association table for decision collaborators (many-to-many relationship)
decision_collaborators = db.Table('decision_collaborators',
    db.Column('decision_id', db.Integer, db.ForeignKey('decision.id'), primary_key=True),
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True)
)

# Association table for decision documents (many-to-many relationship)
decision_documents = db.Table('decision_documents',
    db.Column('decision_id', db.Integer, db.ForeignKey('decision.id'), primary_key=True),
    db.Column('document_id', db.Integer, db.ForeignKey('document.id'), primary_key=True)
)


class Decision(db.Model):
    """Enhanced decision model with AI integration and collaboration features."""
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Basic decision information
    title = db.Column(db.String(200), nullable=False)
    context = db.Column(db.Text, nullable=False)
    decision = db.Column(db.Text, nullable=False)
    rationale = db.Column(db.Text, nullable=False)
    
    # Executive and categorization
    executive_type = db.Column(db.Enum(ExecutiveType), nullable=False)
    category = db.Column(db.String(50), nullable=True)
    priority = db.Column(db.Enum(DecisionPriority), default=DecisionPriority.MEDIUM)
    status = db.Column(db.Enum(DecisionStatus), default=DecisionStatus.PENDING)
    
    # AI-specific fields
    confidence_score = db.Column(db.Float, nullable=True)  # 0.0 to 1.0
    effectiveness_score = db.Column(db.Float, nullable=True)  # 0.0 to 1.0
    ai_model_version = db.Column(db.String(50), nullable=True)
    prompt_version = db.Column(db.String(20), nullable=True)
    
    # Financial and risk assessment
    financial_impact = db.Column(db.Numeric(15, 2), nullable=True)
    risk_level = db.Column(db.Enum(RiskLevel), default=RiskLevel.MEDIUM)
    
    # Implementation tracking
    implementation_notes = db.Column(db.Text, nullable=True)
    outcome_rating = db.Column(db.Integer, nullable=True)  # 1-5 scale
    
    # Conversation context (stored as JSON)
    conversation_history = db.Column(db.Text, nullable=True)  # JSON string
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    implemented_at = db.Column(db.DateTime, nullable=True)
    reviewed_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('decisions', lazy=True))
    collaborators = db.relationship('User', secondary=decision_collaborators, 
                                  backref=db.backref('collaborated_decisions', lazy='dynamic'))
    documents = db.relationship('Document', secondary=decision_documents, 
                               backref=db.backref('related_decisions', lazy='dynamic'))
    comments = db.relationship('Comment', backref='decision', lazy=True, cascade='all, delete-orphan')
    
    def __init__(self, user_id, title, context, decision, rationale, executive_type, **kwargs):
        self.user_id = user_id
        self.title = title
        self.context = context
        self.decision = decision
        self.rationale = rationale
        self.executive_type = executive_type
        
        # Set optional fields
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def set_conversation_history(self, history):
        """Set conversation history as JSON string."""
        self.conversation_history = json.dumps(history) if history else None
    
    def get_conversation_history(self):
        """Get conversation history as Python object."""
        if self.conversation_history:
            return json.loads(self.conversation_history)
        return []
    
    def add_collaborator(self, user):
        """Add a collaborator to this decision."""
        if user not in self.collaborators:
            self.collaborators.append(user)
    
    def remove_collaborator(self, user):
        """Remove a collaborator from this decision."""
        if user in self.collaborators:
            self.collaborators.remove(user)
    
    def add_document(self, document):
        """Add a document reference to this decision."""
        if document not in self.documents:
            self.documents.append(document)
    
    def remove_document(self, document):
        """Remove a document reference from this decision."""
        if document in self.documents:
            self.documents.remove(document)
    
    def update_status(self, new_status, notes=None):
        """Update decision status with optional notes."""
        self.status = new_status
        if notes:
            self.implementation_notes = notes
        
        if new_status == DecisionStatus.COMPLETED:
            self.implemented_at = datetime.utcnow()
        elif new_status == DecisionStatus.UNDER_REVIEW:
            self.reviewed_at = datetime.utcnow()
    
    def calculate_effectiveness(self):
        """Calculate effectiveness score based on outcome rating and other factors."""
        if self.outcome_rating and self.confidence_score:
            # Simple effectiveness calculation: (outcome_rating / 5) * confidence_score
            self.effectiveness_score = (self.outcome_rating / 5.0) * self.confidence_score
        return self.effectiveness_score
    
    def to_dict(self):
        """Convert decision to dictionary for JSON responses."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'context': self.context,
            'decision': self.decision,
            'rationale': self.rationale,
            'executive_type': self.executive_type.value if self.executive_type else None,
            'category': self.category,
            'priority': self.priority.value if self.priority else None,
            'status': self.status.value if self.status else None,
            'confidence_score': float(self.confidence_score) if self.confidence_score else None,
            'effectiveness_score': float(self.effectiveness_score) if self.effectiveness_score else None,
            'financial_impact': float(self.financial_impact) if self.financial_impact else None,
            'risk_level': self.risk_level.value if self.risk_level else None,
            'implementation_notes': self.implementation_notes,
            'outcome_rating': self.outcome_rating,
            'ai_model_version': self.ai_model_version,
            'prompt_version': self.prompt_version,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'implemented_at': self.implemented_at.isoformat() if self.implemented_at else None,
            'reviewed_at': self.reviewed_at.isoformat() if self.reviewed_at else None,
            'collaborators': [{'id': c.id, 'username': c.username, 'name': c.name} for c in self.collaborators],
            'documents': [{'id': d.id, 'filename': d.filename} for d in self.documents],
            'conversation_history': self.get_conversation_history()
        }
    
    @classmethod
    def get_by_status(cls, status):
        """Get all decisions with a specific status."""
        return cls.query.filter_by(status=status).all()
    
    @classmethod
    def get_by_executive_type(cls, executive_type):
        """Get all decisions by executive type."""
        return cls.query.filter_by(executive_type=executive_type).all()
    
    @classmethod
    def get_by_user_and_status(cls, user_id, status):
        """Get user's decisions with specific status."""
        return cls.query.filter_by(user_id=user_id, status=status).all()
    
    def __repr__(self):
        return f'<Decision {self.id}: {self.title}>'


class DocumentType(Enum):
    FINANCIAL = 'financial'
    TECHNICAL = 'technical'
    STRATEGIC = 'strategic'
    LEGAL = 'legal'
    OPERATIONAL = 'operational'
    MARKETING = 'marketing'

class SensitivityLevel(Enum):
    PUBLIC = 'public'
    INTERNAL = 'internal'
    CONFIDENTIAL = 'confidential'
    RESTRICTED = 'restricted'


class Document(db.Model):
    """Document model for file storage and AI context integration."""
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # File information
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(50), nullable=False)  # 'pdf', 'docx', 'xlsx', 'txt', etc.
    file_size = db.Column(db.Integer, nullable=False)  # Size in bytes
    file_path = db.Column(db.String(500), nullable=False)  # Storage path
    content_hash = db.Column(db.String(64), nullable=False)  # SHA-256 hash for deduplication
    
    # Content extraction
    extracted_text = db.Column(db.Text, nullable=True)
    summary = db.Column(db.Text, nullable=True)
    key_insights = db.Column(db.Text, nullable=True)  # JSON array of insights
    
    # Classification and metadata
    document_type = db.Column(db.Enum(DocumentType), nullable=True)
    sensitivity_level = db.Column(db.Enum(SensitivityLevel), default=SensitivityLevel.INTERNAL)
    tags = db.Column(db.String(500), nullable=True)  # Comma-separated tags
    
    # AI and search integration
    embedding_id = db.Column(db.String(100), nullable=True)  # Vector database ID
    embedding_model = db.Column(db.String(50), nullable=True)  # Model used for embeddings
    
    # Usage tracking
    reference_count = db.Column(db.Integer, default=0)
    last_accessed = db.Column(db.DateTime, nullable=True)
    
    # Processing status
    processing_status = db.Column(db.String(20), default='pending')  # 'pending', 'processing', 'completed', 'failed'
    processing_error = db.Column(db.Text, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    processed_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('documents', lazy=True))
    contexts = db.relationship('DocumentContext', backref='document', lazy=True, cascade='all, delete-orphan')
    
    # Indexes for efficient querying
    __table_args__ = (
        db.Index('idx_document_user_type', 'user_id', 'document_type'),
        db.Index('idx_document_hash', 'content_hash'),
        db.Index('idx_document_created', 'created_at'),
        db.Index('idx_document_status', 'processing_status'),
    )
    
    def __init__(self, user_id, filename, original_filename, file_type, file_size, file_path, content_hash, **kwargs):
        self.user_id = user_id
        self.filename = filename
        self.original_filename = original_filename
        self.file_type = file_type
        self.file_size = file_size
        self.file_path = file_path
        self.content_hash = content_hash
        
        # Set optional fields
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def set_key_insights(self, insights):
        """Set key insights as JSON string."""
        self.key_insights = json.dumps(insights) if insights else None
    
    def get_key_insights(self):
        """Get key insights as Python list."""
        if self.key_insights:
            return json.loads(self.key_insights)
        return []
    
    def add_tag(self, tag):
        """Add a tag to the document."""
        current_tags = self.get_tags()
        if tag not in current_tags:
            current_tags.append(tag)
            self.tags = ','.join(current_tags)
    
    def remove_tag(self, tag):
        """Remove a tag from the document."""
        current_tags = self.get_tags()
        if tag in current_tags:
            current_tags.remove(tag)
            self.tags = ','.join(current_tags) if current_tags else None
    
    def get_tags(self):
        """Get tags as a list."""
        if self.tags:
            return [tag.strip() for tag in self.tags.split(',') if tag.strip()]
        return []
    
    def increment_reference_count(self):
        """Increment reference count and update last accessed time."""
        self.reference_count += 1
        self.last_accessed = datetime.utcnow()
    
    def update_processing_status(self, status, error=None):
        """Update processing status."""
        self.processing_status = status
        self.processing_error = error
        if status == 'completed':
            self.processed_at = datetime.utcnow()
    
    def get_file_size_human(self):
        """Get human-readable file size."""
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"
    
    def to_dict(self):
        """Convert document to dictionary for JSON responses."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'filename': self.filename,
            'original_filename': self.original_filename,
            'file_type': self.file_type,
            'file_size': self.file_size,
            'file_size_human': self.get_file_size_human(),
            'content_hash': self.content_hash,
            'extracted_text': self.extracted_text,
            'summary': self.summary,
            'key_insights': self.get_key_insights(),
            'document_type': self.document_type.value if self.document_type else None,
            'sensitivity_level': self.sensitivity_level.value if self.sensitivity_level else None,
            'tags': self.get_tags(),
            'embedding_id': self.embedding_id,
            'embedding_model': self.embedding_model,
            'reference_count': self.reference_count,
            'processing_status': self.processing_status,
            'processing_error': self.processing_error,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'processed_at': self.processed_at.isoformat() if self.processed_at else None,
            'last_accessed': self.last_accessed.isoformat() if self.last_accessed else None
        }
    
    @classmethod
    def get_by_type(cls, document_type):
        """Get all documents of a specific type."""
        return cls.query.filter_by(document_type=document_type).all()
    
    @classmethod
    def get_by_user_and_type(cls, user_id, document_type):
        """Get user's documents of a specific type."""
        return cls.query.filter_by(user_id=user_id, document_type=document_type).all()
    
    @classmethod
    def find_by_hash(cls, content_hash):
        """Find document by content hash (for deduplication)."""
        return cls.query.filter_by(content_hash=content_hash).first()
    
    def __repr__(self):
        return f'<Document {self.id}: {self.filename}>'


class DocumentContext(db.Model):
    """Document context model for AI reference data and semantic chunks."""
    
    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, db.ForeignKey('document.id'), nullable=False)
    
    # Context information
    chunk_index = db.Column(db.Integer, nullable=False)  # Order within document
    content = db.Column(db.Text, nullable=False)  # Text chunk
    content_type = db.Column(db.String(50), nullable=True)  # 'paragraph', 'table', 'header', etc.
    
    # Position information
    page_number = db.Column(db.Integer, nullable=True)
    start_position = db.Column(db.Integer, nullable=True)
    end_position = db.Column(db.Integer, nullable=True)
    
    # AI processing
    embedding_vector = db.Column(db.Text, nullable=True)  # JSON array of embedding values
    summary = db.Column(db.Text, nullable=True)
    keywords = db.Column(db.String(500), nullable=True)  # Comma-separated keywords
    
    # Relevance scoring
    importance_score = db.Column(db.Float, nullable=True)  # 0.0 to 1.0
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Indexes for efficient querying
    __table_args__ = (
        db.Index('idx_context_document_chunk', 'document_id', 'chunk_index'),
        db.Index('idx_context_importance', 'importance_score'),
    )
    
    def __init__(self, document_id, chunk_index, content, **kwargs):
        self.document_id = document_id
        self.chunk_index = chunk_index
        self.content = content
        
        # Set optional fields
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def set_embedding_vector(self, vector):
        """Set embedding vector as JSON string."""
        self.embedding_vector = json.dumps(vector) if vector else None
    
    def get_embedding_vector(self):
        """Get embedding vector as Python list."""
        if self.embedding_vector:
            return json.loads(self.embedding_vector)
        return []
    
    def add_keyword(self, keyword):
        """Add a keyword to the context."""
        current_keywords = self.get_keywords()
        if keyword not in current_keywords:
            current_keywords.append(keyword)
            self.keywords = ','.join(current_keywords)
    
    def get_keywords(self):
        """Get keywords as a list."""
        if self.keywords:
            return [kw.strip() for kw in self.keywords.split(',') if kw.strip()]
        return []
    
    def to_dict(self):
        """Convert document context to dictionary for JSON responses."""
        return {
            'id': self.id,
            'document_id': self.document_id,
            'chunk_index': self.chunk_index,
            'content': self.content,
            'content_type': self.content_type,
            'page_number': self.page_number,
            'start_position': self.start_position,
            'end_position': self.end_position,
            'summary': self.summary,
            'keywords': self.get_keywords(),
            'importance_score': float(self.importance_score) if self.importance_score else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def get_by_document(cls, document_id):
        """Get all contexts for a document, ordered by chunk index."""
        return cls.query.filter_by(document_id=document_id).order_by(cls.chunk_index).all()
    
    @classmethod
    def get_high_importance(cls, document_id, threshold=0.7):
        """Get high-importance contexts for a document."""
        return cls.query.filter(
            cls.document_id == document_id,
            cls.importance_score >= threshold
        ).order_by(cls.importance_score.desc()).all()
    
    def __repr__(self):
        return f'<DocumentContext {self.id}: Doc {self.document_id}, Chunk {self.chunk_index}>'


class CollaborationRole(Enum):
    VIEWER = 'viewer'
    COMMENTER = 'commenter'
    EDITOR = 'editor'
    OWNER = 'owner'

class NotificationType(Enum):
    DECISION_CREATED = 'decision_created'
    DECISION_UPDATED = 'decision_updated'
    DECISION_COMPLETED = 'decision_completed'
    COMMENT_ADDED = 'comment_added'
    COLLABORATION_INVITED = 'collaboration_invited'
    STATUS_CHANGED = 'status_changed'

class NotificationStatus(Enum):
    UNREAD = 'unread'
    READ = 'read'
    ARCHIVED = 'archived'


class Comment(db.Model):
    """Comment model for decision discussions."""
    
    id = db.Column(db.Integer, primary_key=True)
    decision_id = db.Column(db.Integer, db.ForeignKey('decision.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('comment.id'), nullable=True)  # For threaded comments
    
    # Comment content
    content = db.Column(db.Text, nullable=False)
    is_edited = db.Column(db.Boolean, default=False)
    edit_history = db.Column(db.Text, nullable=True)  # JSON array of edit history
    
    # Status and metadata
    is_deleted = db.Column(db.Boolean, default=False)
    is_pinned = db.Column(db.Boolean, default=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('comments', lazy=True))
    replies = db.relationship('Comment', backref=db.backref('parent', remote_side=[id]), lazy=True)
    
    # Indexes for efficient querying
    __table_args__ = (
        db.Index('idx_comment_decision', 'decision_id'),
        db.Index('idx_comment_user', 'user_id'),
        db.Index('idx_comment_created', 'created_at'),
        db.Index('idx_comment_parent', 'parent_id'),
    )
    
    def __init__(self, decision_id, user_id, content, parent_id=None):
        self.decision_id = decision_id
        self.user_id = user_id
        self.content = content
        self.parent_id = parent_id
    
    def edit_content(self, new_content):
        """Edit comment content and track history."""
        if not self.edit_history:
            self.edit_history = json.dumps([])
        
        history = json.loads(self.edit_history)
        history.append({
            'content': self.content,
            'edited_at': datetime.utcnow().isoformat()
        })
        
        self.edit_history = json.dumps(history)
        self.content = new_content
        self.is_edited = True
    
    def get_edit_history(self):
        """Get edit history as Python list."""
        if self.edit_history:
            return json.loads(self.edit_history)
        return []
    
    def soft_delete(self):
        """Soft delete the comment."""
        self.is_deleted = True
        self.content = "[Comment deleted]"
    
    def get_reply_count(self):
        """Get number of replies to this comment."""
        return Comment.query.filter_by(parent_id=self.id, is_deleted=False).count()
    
    def to_dict(self, include_replies=False):
        """Convert comment to dictionary for JSON responses."""
        result = {
            'id': self.id,
            'decision_id': self.decision_id,
            'user_id': self.user_id,
            'parent_id': self.parent_id,
            'content': self.content,
            'is_edited': self.is_edited,
            'is_deleted': self.is_deleted,
            'is_pinned': self.is_pinned,
            'reply_count': self.get_reply_count(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'user': {
                'id': self.user.id,
                'username': self.user.username,
                'name': self.user.name,
                'avatar_url': self.user.avatar_url
            } if self.user else None
        }
        
        if include_replies:
            result['replies'] = [reply.to_dict() for reply in self.replies if not reply.is_deleted]
        
        return result
    
    @classmethod
    def get_by_decision(cls, decision_id, include_deleted=False):
        """Get all comments for a decision."""
        query = cls.query.filter_by(decision_id=decision_id)
        if not include_deleted:
            query = query.filter_by(is_deleted=False)
        return query.order_by(cls.created_at).all()
    
    @classmethod
    def get_top_level_comments(cls, decision_id):
        """Get top-level comments (no parent) for a decision."""
        return cls.query.filter_by(
            decision_id=decision_id,
            parent_id=None,
            is_deleted=False
        ).order_by(cls.created_at).all()
    
    def __repr__(self):
        return f'<Comment {self.id}: Decision {self.decision_id}>'


class CollaborationSession(db.Model):
    """Collaboration session model for team interactions."""
    
    id = db.Column(db.Integer, primary_key=True)
    decision_id = db.Column(db.Integer, db.ForeignKey('decision.id'), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Session information
    title = db.Column(db.String(200), nullable=True)
    description = db.Column(db.Text, nullable=True)
    
    # Status and settings
    is_active = db.Column(db.Boolean, default=True)
    is_public = db.Column(db.Boolean, default=False)  # Public sessions can be joined by anyone
    requires_approval = db.Column(db.Boolean, default=True)  # Require approval to join
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    ended_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    decision = db.relationship('Decision', backref=db.backref('collaboration_sessions', lazy=True))
    creator = db.relationship('User', backref=db.backref('created_sessions', lazy=True))
    participants = db.relationship('CollaborationParticipant', backref='session', lazy=True, cascade='all, delete-orphan')
    
    def __init__(self, decision_id, created_by, title=None, description=None):
        self.decision_id = decision_id
        self.created_by = created_by
        self.title = title
        self.description = description
    
    def add_participant(self, user_id, role=CollaborationRole.COMMENTER, invited_by=None):
        """Add a participant to the collaboration session."""
        existing = CollaborationParticipant.query.filter_by(
            session_id=self.id,
            user_id=user_id
        ).first()
        
        if not existing:
            participant = CollaborationParticipant(
                session_id=self.id,
                user_id=user_id,
                role=role,
                invited_by=invited_by
            )
            db.session.add(participant)
            return participant
        return existing
    
    def remove_participant(self, user_id):
        """Remove a participant from the collaboration session."""
        participant = CollaborationParticipant.query.filter_by(
            session_id=self.id,
            user_id=user_id
        ).first()
        
        if participant:
            db.session.delete(participant)
    
    def get_active_participants(self):
        """Get all active participants."""
        return [p for p in self.participants if p.is_active]
    
    def end_session(self):
        """End the collaboration session."""
        self.is_active = False
        self.ended_at = datetime.utcnow()
    
    def to_dict(self):
        """Convert collaboration session to dictionary for JSON responses."""
        return {
            'id': self.id,
            'decision_id': self.decision_id,
            'created_by': self.created_by,
            'title': self.title,
            'description': self.description,
            'is_active': self.is_active,
            'is_public': self.is_public,
            'requires_approval': self.requires_approval,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'ended_at': self.ended_at.isoformat() if self.ended_at else None,
            'creator': {
                'id': self.creator.id,
                'username': self.creator.username,
                'name': self.creator.name
            } if self.creator else None,
            'participants': [p.to_dict() for p in self.get_active_participants()]
        }
    
    def __repr__(self):
        return f'<CollaborationSession {self.id}: Decision {self.decision_id}>'


class CollaborationParticipant(db.Model):
    """Collaboration participant model for tracking user roles in sessions."""
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('collaboration_session.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    invited_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    
    # Participation details
    role = db.Column(db.Enum(CollaborationRole), default=CollaborationRole.COMMENTER)
    is_active = db.Column(db.Boolean, default=True)
    
    # Timestamps
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_activity = db.Column(db.DateTime, default=datetime.utcnow)
    left_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], backref=db.backref('collaboration_participations', lazy=True))
    inviter = db.relationship('User', foreign_keys=[invited_by])
    
    # Unique constraint to prevent duplicate participants
    __table_args__ = (
        db.UniqueConstraint('session_id', 'user_id', name='unique_session_participant'),
        db.Index('idx_participant_session', 'session_id'),
        db.Index('idx_participant_user', 'user_id'),
    )
    
    def __init__(self, session_id, user_id, role=CollaborationRole.COMMENTER, invited_by=None):
        self.session_id = session_id
        self.user_id = user_id
        self.role = role
        self.invited_by = invited_by
    
    def update_activity(self):
        """Update last activity timestamp."""
        self.last_activity = datetime.utcnow()
    
    def leave_session(self):
        """Mark participant as having left the session."""
        self.is_active = False
        self.left_at = datetime.utcnow()
    
    def change_role(self, new_role):
        """Change participant's role."""
        self.role = new_role
        self.update_activity()
    
    def to_dict(self):
        """Convert participant to dictionary for JSON responses."""
        return {
            'id': self.id,
            'session_id': self.session_id,
            'user_id': self.user_id,
            'role': self.role.value if self.role else None,
            'is_active': self.is_active,
            'joined_at': self.joined_at.isoformat() if self.joined_at else None,
            'last_activity': self.last_activity.isoformat() if self.last_activity else None,
            'left_at': self.left_at.isoformat() if self.left_at else None,
            'user': {
                'id': self.user.id,
                'username': self.user.username,
                'name': self.user.name,
                'avatar_url': self.user.avatar_url
            } if self.user else None,
            'inviter': {
                'id': self.inviter.id,
                'username': self.inviter.username,
                'name': self.inviter.name
            } if self.inviter else None
        }
    
    def __repr__(self):
        return f'<CollaborationParticipant {self.id}: User {self.user_id} in Session {self.session_id}>'


class Notification(db.Model):
    """Notification model for workflow tracking."""
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Notification content
    type = db.Column(db.Enum(NotificationType), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    
    # Related entities
    decision_id = db.Column(db.Integer, db.ForeignKey('decision.id'), nullable=True)
    comment_id = db.Column(db.Integer, db.ForeignKey('comment.id'), nullable=True)
    session_id = db.Column(db.Integer, db.ForeignKey('collaboration_session.id'), nullable=True)
    
    # Notification metadata
    data = db.Column(db.Text, nullable=True)  # JSON data for additional context
    
    # Status
    status = db.Column(db.Enum(NotificationStatus), default=NotificationStatus.UNREAD)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    read_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('notifications', lazy=True))
    decision = db.relationship('Decision', backref=db.backref('notifications', lazy=True))
    comment = db.relationship('Comment', backref=db.backref('notifications', lazy=True))
    collaboration_session = db.relationship('CollaborationSession', backref=db.backref('notifications', lazy=True))
    
    # Indexes for efficient querying
    __table_args__ = (
        db.Index('idx_notification_user_status', 'user_id', 'status'),
        db.Index('idx_notification_created', 'created_at'),
        db.Index('idx_notification_type', 'type'),
    )
    
    def __init__(self, user_id, notification_type, title, message, **kwargs):
        self.user_id = user_id
        self.type = notification_type
        self.title = title
        self.message = message
        
        # Set optional fields
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def mark_as_read(self):
        """Mark notification as read."""
        self.status = NotificationStatus.READ
        self.read_at = datetime.utcnow()
    
    def mark_as_unread(self):
        """Mark notification as unread."""
        self.status = NotificationStatus.UNREAD
        self.read_at = None
    
    def archive(self):
        """Archive the notification."""
        self.status = NotificationStatus.ARCHIVED
    
    def set_data(self, data):
        """Set notification data as JSON string."""
        self.data = json.dumps(data) if data else None
    
    def get_data(self):
        """Get notification data as Python object."""
        if self.data:
            return json.loads(self.data)
        return {}
    
    def to_dict(self):
        """Convert notification to dictionary for JSON responses."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'type': self.type.value if self.type else None,
            'title': self.title,
            'message': self.message,
            'decision_id': self.decision_id,
            'comment_id': self.comment_id,
            'session_id': self.session_id,
            'data': self.get_data(),
            'status': self.status.value if self.status else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'read_at': self.read_at.isoformat() if self.read_at else None
        }
    
    @classmethod
    def get_unread_for_user(cls, user_id):
        """Get all unread notifications for a user."""
        return cls.query.filter_by(
            user_id=user_id,
            status=NotificationStatus.UNREAD
        ).order_by(cls.created_at.desc()).all()
    
    @classmethod
    def get_recent_for_user(cls, user_id, limit=50):
        """Get recent notifications for a user."""
        return cls.query.filter_by(user_id=user_id).order_by(
            cls.created_at.desc()
        ).limit(limit).all()
    
    @classmethod
    def create_decision_notification(cls, user_id, decision, notification_type, message):
        """Create a decision-related notification."""
        title_map = {
            NotificationType.DECISION_CREATED: f"New decision: {decision.title}",
            NotificationType.DECISION_UPDATED: f"Decision updated: {decision.title}",
            NotificationType.DECISION_COMPLETED: f"Decision completed: {decision.title}",
            NotificationType.STATUS_CHANGED: f"Status changed: {decision.title}"
        }
        
        return cls(
            user_id=user_id,
            notification_type=notification_type,
            title=title_map.get(notification_type, "Decision notification"),
            message=message,
            decision_id=decision.id
        )
    
    def __repr__(self):
        return f'<Notification {self.id}: {self.type.value} for User {self.user_id}>'


class AuditEventType(Enum):
    # Decision events
    DECISION_CREATED = 'decision_created'
    DECISION_UPDATED = 'decision_updated'
    DECISION_STATUS_CHANGED = 'decision_status_changed'
    DECISION_DELETED = 'decision_deleted'
    
    # Collaboration events
    COLLABORATION_STARTED = 'collaboration_started'
    COLLABORATION_ENDED = 'collaboration_ended'
    USER_INVITED = 'user_invited'
    USER_JOINED = 'user_joined'
    USER_LEFT = 'user_left'
    USER_REMOVED = 'user_removed'
    ROLE_CHANGED = 'role_changed'
    
    # Comment events
    COMMENT_ADDED = 'comment_added'
    COMMENT_EDITED = 'comment_edited'
    COMMENT_DELETED = 'comment_deleted'
    COMMENT_PINNED = 'comment_pinned'
    COMMENT_UNPINNED = 'comment_unpinned'
    COMMENT_MODERATED = 'comment_moderated'
    
    # Document events
    DOCUMENT_UPLOADED = 'document_uploaded'
    DOCUMENT_SHARED = 'document_shared'
    DOCUMENT_REMOVED = 'document_removed'
    
    # System events
    LOGIN = 'login'
    LOGOUT = 'logout'
    PERMISSION_CHANGED = 'permission_changed'


class CommunicationStyle(Enum):
    FORMAL = 'formal'
    CASUAL = 'casual'
    TECHNICAL = 'technical'
    FRIENDLY = 'friendly'
    DIRECT = 'direct'
    DIPLOMATIC = 'diplomatic'

class IndustrySpecialization(Enum):
    TECHNOLOGY = 'technology'
    FINANCE = 'finance'
    HEALTHCARE = 'healthcare'
    MANUFACTURING = 'manufacturing'
    RETAIL = 'retail'
    CONSULTING = 'consulting'
    EDUCATION = 'education'
    GOVERNMENT = 'government'
    NONPROFIT = 'nonprofit'
    GENERAL = 'general'

class ExpertiseLevel(Enum):
    JUNIOR = 'junior'
    INTERMEDIATE = 'intermediate'
    SENIOR = 'senior'
    EXPERT = 'expert'
    THOUGHT_LEADER = 'thought_leader'


class PersonalityProfile(db.Model):
    """AI personality profile model for customizable executive personalities."""
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Basic profile information
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    executive_type = db.Column(db.Enum(ExecutiveType), nullable=False)
    
    # Industry and specialization
    industry_specialization = db.Column(db.Enum(IndustrySpecialization), default=IndustrySpecialization.GENERAL)
    expertise_domains = db.Column(db.Text, nullable=True)  # JSON array of expertise areas
    
    # Communication preferences
    communication_style = db.Column(db.Enum(CommunicationStyle), default=CommunicationStyle.FORMAL)
    tone_preferences = db.Column(db.Text, nullable=True)  # JSON object with tone settings
    
    # Decision-making approach
    decision_making_style = db.Column(db.String(50), nullable=True)  # 'analytical', 'intuitive', 'collaborative', etc.
    risk_tolerance = db.Column(db.String(20), default='medium')  # 'low', 'medium', 'high'
    
    # Experience and background
    experience_level = db.Column(db.Enum(ExpertiseLevel), default=ExpertiseLevel.SENIOR)
    background_context = db.Column(db.Text, nullable=True)  # Custom background information
    
    # Personality traits
    personality_traits = db.Column(db.Text, nullable=True)  # JSON object with trait scores
    
    # Custom knowledge base
    custom_knowledge = db.Column(db.Text, nullable=True)  # JSON array of custom knowledge items
    knowledge_sources = db.Column(db.Text, nullable=True)  # JSON array of knowledge source references
    
    # Profile settings
    is_active = db.Column(db.Boolean, default=True)
    is_default = db.Column(db.Boolean, default=False)
    is_public = db.Column(db.Boolean, default=False)  # Can be shared with other users
    
    # Version control
    version = db.Column(db.String(20), default='1.0')
    parent_profile_id = db.Column(db.Integer, db.ForeignKey('personality_profile.id'), nullable=True)
    
    # Usage statistics
    usage_count = db.Column(db.Integer, default=0)
    last_used = db.Column(db.DateTime, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('personality_profiles', lazy=True))
    parent_profile = db.relationship('PersonalityProfile', remote_side=[id], backref='child_profiles')
    
    # Indexes for efficient querying
    __table_args__ = (
        db.Index('idx_personality_user_type', 'user_id', 'executive_type'),
        db.Index('idx_personality_industry', 'industry_specialization'),
        db.Index('idx_personality_active', 'is_active'),
        db.Index('idx_personality_public', 'is_public'),
    )
    
    def __init__(self, user_id, name, executive_type, **kwargs):
        self.user_id = user_id
        self.name = name
        self.executive_type = executive_type
        
        # Set optional fields
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def set_expertise_domains(self, domains):
        """Set expertise domains as JSON string."""
        self.expertise_domains = json.dumps(domains) if domains else None
    
    def get_expertise_domains(self):
        """Get expertise domains as Python list."""
        if self.expertise_domains:
            return json.loads(self.expertise_domains)
        return []
    
    def set_tone_preferences(self, preferences):
        """Set tone preferences as JSON string."""
        self.tone_preferences = json.dumps(preferences) if preferences else None
    
    def get_tone_preferences(self):
        """Get tone preferences as Python dict."""
        if self.tone_preferences:
            return json.loads(self.tone_preferences)
        return {
            'formality': 0.7,  # 0.0 = very casual, 1.0 = very formal
            'enthusiasm': 0.5,  # 0.0 = reserved, 1.0 = very enthusiastic
            'directness': 0.6,  # 0.0 = diplomatic, 1.0 = very direct
            'technical_depth': 0.7  # 0.0 = high-level, 1.0 = very technical
        }
    
    def set_personality_traits(self, traits):
        """Set personality traits as JSON string."""
        self.personality_traits = json.dumps(traits) if traits else None
    
    def get_personality_traits(self):
        """Get personality traits as Python dict."""
        if self.personality_traits:
            return json.loads(self.personality_traits)
        return {
            'analytical': 0.8,  # 0.0 = intuitive, 1.0 = highly analytical
            'collaborative': 0.6,  # 0.0 = independent, 1.0 = highly collaborative
            'innovative': 0.7,  # 0.0 = traditional, 1.0 = highly innovative
            'detail_oriented': 0.8,  # 0.0 = big picture, 1.0 = detail focused
            'decisive': 0.7  # 0.0 = deliberative, 1.0 = quick decisions
        }
    
    def set_custom_knowledge(self, knowledge):
        """Set custom knowledge as JSON string."""
        self.custom_knowledge = json.dumps(knowledge) if knowledge else None
    
    def get_custom_knowledge(self):
        """Get custom knowledge as Python list."""
        if self.custom_knowledge:
            return json.loads(self.custom_knowledge)
        return []
    
    def set_knowledge_sources(self, sources):
        """Set knowledge sources as JSON string."""
        self.knowledge_sources = json.dumps(sources) if sources else None
    
    def get_knowledge_sources(self):
        """Get knowledge sources as Python list."""
        if self.knowledge_sources:
            return json.loads(self.knowledge_sources)
        return []
    
    def increment_usage(self):
        """Increment usage count and update last used timestamp."""
        self.usage_count += 1
        self.last_used = datetime.utcnow()
    
    def create_child_profile(self, name, user_id=None):
        """Create a child profile based on this profile."""
        child = PersonalityProfile(
            user_id=user_id or self.user_id,
            name=name,
            executive_type=self.executive_type,
            industry_specialization=self.industry_specialization,
            communication_style=self.communication_style,
            decision_making_style=self.decision_making_style,
            risk_tolerance=self.risk_tolerance,
            experience_level=self.experience_level,
            background_context=self.background_context,
            parent_profile_id=self.id,
            version='1.0'
        )
        
        # Copy JSON fields
        child.set_expertise_domains(self.get_expertise_domains())
        child.set_tone_preferences(self.get_tone_preferences())
        child.set_personality_traits(self.get_personality_traits())
        child.set_custom_knowledge(self.get_custom_knowledge())
        child.set_knowledge_sources(self.get_knowledge_sources())
        
        return child
    
    def to_dict(self, include_sensitive=False):
        """Convert personality profile to dictionary for JSON responses."""
        result = {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'description': self.description,
            'executive_type': self.executive_type.value if self.executive_type else None,
            'industry_specialization': self.industry_specialization.value if self.industry_specialization else None,
            'expertise_domains': self.get_expertise_domains(),
            'communication_style': self.communication_style.value if self.communication_style else None,
            'tone_preferences': self.get_tone_preferences(),
            'decision_making_style': self.decision_making_style,
            'risk_tolerance': self.risk_tolerance,
            'experience_level': self.experience_level.value if self.experience_level else None,
            'personality_traits': self.get_personality_traits(),
            'is_active': self.is_active,
            'is_default': self.is_default,
            'is_public': self.is_public,
            'version': self.version,
            'parent_profile_id': self.parent_profile_id,
            'usage_count': self.usage_count,
            'last_used': self.last_used.isoformat() if self.last_used else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_sensitive:
            result.update({
                'background_context': self.background_context,
                'custom_knowledge': self.get_custom_knowledge(),
                'knowledge_sources': self.get_knowledge_sources()
            })
        
        return result
    
    @classmethod
    def get_by_user_and_type(cls, user_id, executive_type):
        """Get user's personality profiles for a specific executive type."""
        return cls.query.filter_by(
            user_id=user_id,
            executive_type=executive_type,
            is_active=True
        ).order_by(cls.updated_at.desc()).all()
    
    @classmethod
    def get_default_for_user(cls, user_id, executive_type):
        """Get user's default personality profile for an executive type."""
        return cls.query.filter_by(
            user_id=user_id,
            executive_type=executive_type,
            is_default=True,
            is_active=True
        ).first()
    
    @classmethod
    def get_public_profiles(cls, executive_type=None):
        """Get public personality profiles, optionally filtered by executive type."""
        query = cls.query.filter_by(is_public=True, is_active=True)
        if executive_type:
            query = query.filter_by(executive_type=executive_type)
        return query.order_by(cls.usage_count.desc()).all()
    
    def __repr__(self):
        return f'<PersonalityProfile {self.id}: {self.name} ({self.executive_type.value})>'


class PersonalityProfileShare(db.Model):
    """Model for tracking personality profile sharing and collaboration."""
    
    id = db.Column(db.Integer, primary_key=True)
    profile_id = db.Column(db.Integer, db.ForeignKey('personality_profile.id'), nullable=False)
    shared_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    shared_with = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # Null for public shares
    
    # Share settings
    share_type = db.Column(db.String(20), default='view')  # 'view', 'copy', 'collaborate'
    is_active = db.Column(db.Boolean, default=True)
    
    # Access tracking
    access_count = db.Column(db.Integer, default=0)
    last_accessed = db.Column(db.DateTime, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    profile = db.relationship('PersonalityProfile', backref=db.backref('shares', lazy=True))
    sharer = db.relationship('User', foreign_keys=[shared_by], backref=db.backref('shared_profiles', lazy=True))
    recipient = db.relationship('User', foreign_keys=[shared_with], backref=db.backref('received_profiles', lazy=True))
    
    # Indexes for efficient querying
    __table_args__ = (
        db.Index('idx_profile_share_profile', 'profile_id'),
        db.Index('idx_profile_share_recipient', 'shared_with'),
        db.Index('idx_profile_share_active', 'is_active'),
    )
    
    def __init__(self, profile_id, shared_by, shared_with=None, share_type='view', **kwargs):
        self.profile_id = profile_id
        self.shared_by = shared_by
        self.shared_with = shared_with
        self.share_type = share_type
        
        # Set optional fields
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def increment_access(self):
        """Increment access count and update last accessed timestamp."""
        self.access_count += 1
        self.last_accessed = datetime.utcnow()
    
    def is_expired(self):
        """Check if the share has expired."""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at
    
    def revoke(self):
        """Revoke the share."""
        self.is_active = False
    
    def to_dict(self):
        """Convert profile share to dictionary for JSON responses."""
        return {
            'id': self.id,
            'profile_id': self.profile_id,
            'shared_by': self.shared_by,
            'shared_with': self.shared_with,
            'share_type': self.share_type,
            'is_active': self.is_active,
            'access_count': self.access_count,
            'last_accessed': self.last_accessed.isoformat() if self.last_accessed else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'is_expired': self.is_expired(),
            'profile': self.profile.to_dict() if self.profile else None,
            'sharer': {
                'id': self.sharer.id,
                'username': self.sharer.username,
                'name': self.sharer.name
            } if self.sharer else None,
            'recipient': {
                'id': self.recipient.id,
                'username': self.recipient.username,
                'name': self.recipient.name
            } if self.recipient else None
        }
    
    def __repr__(self):
        return f'<PersonalityProfileShare {self.id}: Profile {self.profile_id}>'


class AuditLog(db.Model):
    """Audit log model for tracking all system events and changes."""
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Event information
    event_type = db.Column(db.Enum(AuditEventType), nullable=False)
    event_description = db.Column(db.String(500), nullable=False)
    
    # User information
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # Nullable for system events
    user_ip = db.Column(db.String(45), nullable=True)  # IPv4/IPv6 address
    user_agent = db.Column(db.String(500), nullable=True)
    
    # Related entities
    decision_id = db.Column(db.Integer, db.ForeignKey('decision.id'), nullable=True)
    comment_id = db.Column(db.Integer, db.ForeignKey('comment.id'), nullable=True)
    session_id = db.Column(db.Integer, db.ForeignKey('collaboration_session.id'), nullable=True)
    document_id = db.Column(db.Integer, db.ForeignKey('document.id'), nullable=True)
    
    # Change tracking
    old_values = db.Column(db.Text, nullable=True)  # JSON string of old values
    new_values = db.Column(db.Text, nullable=True)  # JSON string of new values
    
    # Additional metadata
    extra_metadata = db.Column(db.Text, nullable=True)  # JSON string for additional context
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('audit_logs', lazy=True))
    decision = db.relationship('Decision', backref=db.backref('audit_logs', lazy=True))
    comment = db.relationship('Comment', backref=db.backref('audit_logs', lazy=True))
    collaboration_session = db.relationship('CollaborationSession', backref=db.backref('audit_logs', lazy=True))
    document = db.relationship('Document', backref=db.backref('audit_logs', lazy=True))
    
    # Indexes for efficient querying
    __table_args__ = (
        db.Index('idx_audit_event_type', 'event_type'),
        db.Index('idx_audit_user', 'user_id'),
        db.Index('idx_audit_decision', 'decision_id'),
        db.Index('idx_audit_created', 'created_at'),
        db.Index('idx_audit_user_created', 'user_id', 'created_at'),
    )
    
    def __init__(self, event_type, event_description, user_id=None, **kwargs):
        self.event_type = event_type
        self.event_description = event_description
        self.user_id = user_id
        
        # Set optional fields
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def set_old_values(self, values):
        """Set old values as JSON string."""
        self.old_values = json.dumps(values) if values else None
    
    def get_old_values(self):
        """Get old values as Python object."""
        if self.old_values:
            return json.loads(self.old_values)
        return {}
    
    def set_new_values(self, values):
        """Set new values as JSON string."""
        self.new_values = json.dumps(values) if values else None
    
    def get_new_values(self):
        """Get new values as Python object."""
        if self.new_values:
            return json.loads(self.new_values)
        return {}
    
    def set_metadata(self, metadata):
        """Set metadata as JSON string."""
        self.extra_metadata = json.dumps(metadata) if metadata else None
    
    def get_metadata(self):
        """Get metadata as Python object."""
        if self.extra_metadata:
            return json.loads(self.extra_metadata)
        return {}
    
    def to_dict(self):
        """Convert audit log to dictionary for JSON responses."""
        return {
            'id': self.id,
            'event_type': self.event_type.value if self.event_type else None,
            'event_description': self.event_description,
            'user_id': self.user_id,
            'user_ip': self.user_ip,
            'user_agent': self.user_agent,
            'decision_id': self.decision_id,
            'comment_id': self.comment_id,
            'session_id': self.session_id,
            'document_id': self.document_id,
            'old_values': self.get_old_values(),
            'new_values': self.get_new_values(),
            'metadata': self.get_metadata(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'user': {
                'id': self.user.id,
                'username': self.user.username,
                'name': self.user.name
            } if self.user else None
        }
    
    @classmethod
    def log_event(
        cls,
        event_type: AuditEventType,
        event_description: str,
        user_id: int = None,
        user_ip: str = None,
        user_agent: str = None,
        decision_id: int = None,
        comment_id: int = None,
        session_id: int = None,
        document_id: int = None,
        old_values: dict = None,
        new_values: dict = None,
        metadata: dict = None
    ):
        """
        Create and save an audit log entry
        
        Args:
            event_type: Type of event
            event_description: Human-readable description
            user_id: ID of user who performed the action
            user_ip: IP address of the user
            user_agent: User agent string
            decision_id: Related decision ID
            comment_id: Related comment ID
            session_id: Related session ID
            document_id: Related document ID
            old_values: Previous values (for updates)
            new_values: New values (for updates)
            metadata: Additional context data
            
        Returns:
            AuditLog instance
        """
        try:
            audit_log = cls(
                event_type=event_type,
                event_description=event_description,
                user_id=user_id,
                user_ip=user_ip,
                user_agent=user_agent,
                decision_id=decision_id,
                comment_id=comment_id,
                session_id=session_id,
                document_id=document_id
            )
            
            if old_values:
                audit_log.set_old_values(old_values)
            if new_values:
                audit_log.set_new_values(new_values)
            if metadata:
                audit_log.set_metadata(metadata)
            
            db.session.add(audit_log)
            db.session.commit()
            
            return audit_log
            
        except Exception as e:
            db.session.rollback()
            # Log the error but don't fail the main operation
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to create audit log: {str(e)}")
            return None
    
    @classmethod
    def get_decision_audit_trail(cls, decision_id: int, limit: int = 100):
        """Get audit trail for a specific decision."""
        return cls.query.filter_by(decision_id=decision_id).order_by(
            cls.created_at.desc()
        ).limit(limit).all()
    
    @classmethod
    def get_user_activity(cls, user_id: int, limit: int = 100):
        """Get activity log for a specific user."""
        return cls.query.filter_by(user_id=user_id).order_by(
            cls.created_at.desc()
        ).limit(limit).all()
    
    @classmethod
    def get_system_audit_trail(cls, start_date=None, end_date=None, limit: int = 1000):
        """Get system-wide audit trail with optional date filtering."""
        query = cls.query
        
        if start_date:
            query = query.filter(cls.created_at >= start_date)
        if end_date:
            query = query.filter(cls.created_at <= end_date)
        
        return query.order_by(cls.created_at.desc()).limit(limit).all()
    
    @classmethod
    def get_compliance_report(cls, start_date, end_date, event_types=None):
        """Generate compliance report for a date range."""
        query = cls.query.filter(
            cls.created_at >= start_date,
            cls.created_at <= end_date
        )
        
        if event_types:
            query = query.filter(cls.event_type.in_(event_types))
        
        return query.order_by(cls.created_at.desc()).all()
    
    def __repr__(self):
        return f'<AuditLog {self.id}: {self.event_type.value} by User {self.user_id}>'