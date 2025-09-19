"""
Migration: Add Audit Log Table

This migration adds the audit log table for comprehensive tracking
of all system events and changes.
"""

from flask import Flask
from models import db, AuditLog, AuditEventType
import logging

logger = logging.getLogger(__name__)


def upgrade():
    """Apply the migration"""
    try:
        logger.info("Creating audit_log table...")
        
        # Create the audit log table
        db.create_all()
        
        logger.info("✓ Audit log table created successfully")
        
        # Create initial system event
        try:
            from models import AuditLog, AuditEventType
            AuditLog.log_event(
                event_type=AuditEventType.PERMISSION_CHANGED,
                event_description="Audit logging system initialized",
                metadata={
                    'migration': '002_audit_log',
                    'system_event': True
                }
            )
            logger.info("✓ Initial audit log entry created")
        except Exception as e:
            logger.warning(f"Could not create initial audit log entry: {e}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error creating audit log table: {e}")
        return False


def downgrade():
    """Rollback the migration"""
    try:
        logger.info("Dropping audit_log table...")
        
        # Drop the audit log table
        db.drop_all(tables=[AuditLog.__table__])
        
        logger.info("✓ Audit log table dropped successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error dropping audit log table: {e}")
        return False


def run_migration():
    """Run the migration with proper Flask app context"""
    from app import create_app
    
    app = create_app()
    
    with app.app_context():
        print("🔄 Running audit log migration...")
        
        if upgrade():
            print("✅ Migration completed successfully")
        else:
            print("❌ Migration failed")
            return False
    
    return True


if __name__ == '__main__':
    run_migration()