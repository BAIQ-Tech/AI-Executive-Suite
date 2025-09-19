"""
Database Migration: MFA Tables

Creates tables for Multi-Factor Authentication system including:
- MFA methods (TOTP, SMS, Email)
- Backup codes
- Verification attempts
- Recovery tokens
- Pending verifications
"""

import os
import sys
from datetime import datetime

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def upgrade():
    """Create MFA tables."""
    from flask import Flask
    from models import db, MFAMethod, MFABackupCode, MFAVerificationAttempt, MFARecoveryToken, PendingMFAVerification
    
    # Create Flask app for database context
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///instance/ai_executive_suite.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize database
    db.init_app(app)
    
    with app.app_context():
        print("Creating MFA tables...")
        
        # Create all MFA tables
        db.create_all()
        
        print("✓ MFA tables created successfully")
        print("  - mfa_method: Multi-factor authentication methods")
        print("  - mfa_backup_code: Backup recovery codes")
        print("  - mfa_verification_attempt: Security audit log")
        print("  - mfa_recovery_token: Account recovery tokens")
        print("  - pending_mfa_verification: Temporary verification codes")

def downgrade():
    """Drop MFA tables."""
    from flask import Flask
    from models import db
    
    # Create Flask app for database context
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///instance/ai_executive_suite.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize database
    db.init_app(app)
    
    with app.app_context():
        print("Dropping MFA tables...")
        
        # Drop MFA tables
        table_names = [
            'pending_mfa_verification',
            'mfa_recovery_token', 
            'mfa_verification_attempt',
            'mfa_backup_code',
            'mfa_method'
        ]
        
        for table_name in table_names:
            try:
                db.engine.execute(f'DROP TABLE IF EXISTS {table_name}')
                print(f"✓ Dropped table: {table_name}")
            except Exception as e:
                print(f"Warning: Could not drop table {table_name}: {e}")

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='MFA Tables Migration')
    parser.add_argument('action', choices=['upgrade', 'downgrade'], help='Migration action')
    
    args = parser.parse_args()
    
    if args.action == 'upgrade':
        upgrade()
    elif args.action == 'downgrade':
        downgrade()
    
    print("Migration completed!")