"""
Enhanced Models Migration
Creates tables for enhanced Decision model, Document storage, and Collaboration features.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask
from models import db, Decision, Document, DocumentContext, Comment, CollaborationSession, CollaborationParticipant, Notification


def upgrade(app):
    """Apply the migration - create all new tables and indexes."""
    with app.app_context():
        # Create all tables defined in models
        db.create_all()
        
        # Create additional indexes for performance
        db.engine.execute("""
            CREATE INDEX IF NOT EXISTS idx_decision_user_executive 
            ON decision(user_id, executive_type);
        """)
        
        db.engine.execute("""
            CREATE INDEX IF NOT EXISTS idx_decision_status_priority 
            ON decision(status, priority);
        """)
        
        db.engine.execute("""
            CREATE INDEX IF NOT EXISTS idx_decision_financial_impact 
            ON decision(financial_impact) WHERE financial_impact IS NOT NULL;
        """)
        
        db.engine.execute("""
            CREATE INDEX IF NOT EXISTS idx_document_user_sensitivity 
            ON document(user_id, sensitivity_level);
        """)
        
        db.engine.execute("""
            CREATE INDEX IF NOT EXISTS idx_document_type_created 
            ON document(document_type, created_at);
        """)
        
        db.engine.execute("""
            CREATE INDEX IF NOT EXISTS idx_context_importance_desc 
            ON document_context(importance_score DESC) WHERE importance_score IS NOT NULL;
        """)
        
        print("Enhanced models migration completed successfully!")


def downgrade(app):
    """Rollback the migration - drop all new tables."""
    with app.app_context():
        # Drop tables in reverse dependency order
        db.engine.execute("DROP TABLE IF EXISTS notification CASCADE;")
        db.engine.execute("DROP TABLE IF EXISTS collaboration_participant CASCADE;")
        db.engine.execute("DROP TABLE IF EXISTS collaboration_session CASCADE;")
        db.engine.execute("DROP TABLE IF EXISTS comment CASCADE;")
        db.engine.execute("DROP TABLE IF EXISTS document_context CASCADE;")
        db.engine.execute("DROP TABLE IF EXISTS decision_documents CASCADE;")
        db.engine.execute("DROP TABLE IF EXISTS decision_collaborators CASCADE;")
        db.engine.execute("DROP TABLE IF EXISTS document CASCADE;")
        db.engine.execute("DROP TABLE IF EXISTS decision CASCADE;")
        
        print("Enhanced models migration rolled back successfully!")


def run_migration():
    """Run the migration standalone."""
    app = Flask(__name__)
    
    # Configure database
    database_url = os.getenv('DATABASE_URL', 'sqlite:///instance/ai_executive_suite.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize database
    db.init_app(app)
    
    # Run upgrade
    upgrade(app)


if __name__ == '__main__':
    run_migration()