from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
import bcrypt
import json

# Initialize SQLAlchemy instance
db = SQLAlchemy()

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
            'ai_preferences': self.get_ai_preferences()
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
