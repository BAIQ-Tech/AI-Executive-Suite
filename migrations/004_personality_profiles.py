"""
Migration 004: Add personality profile tables for customizable AI personalities
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from models import db

def upgrade(app):
    """Apply the migration."""
    with app.app_context():
        # Use SQLAlchemy's create_all to create tables from models
        db.create_all()
        print("✓ Created personality profile tables and indexes")

def downgrade(app):
    """Rollback the migration."""
    with app.app_context():
        with db.engine.connect() as conn:
            # Drop tables
            conn.execute(db.text("DROP TABLE IF EXISTS personality_profile_share"))
            conn.execute(db.text("DROP TABLE IF EXISTS personality_profile"))
        
        print("✓ Dropped personality profile tables and indexes")

if __name__ == "__main__":
    from app import create_app
    app = create_app()
    upgrade(app)