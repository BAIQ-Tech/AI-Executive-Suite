#!/usr/bin/env python3
"""
Setup Script for AI Executive Suite

This script helps initialize the enhanced AI Executive Suite with
proper directory structure, database setup, and configuration validation.
"""

import os
import sys
import logging
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.settings import config
from utils.logging import setup_logging


def create_directories():
    """Create necessary directories"""
    directories = [
        'logs',
        'uploads',
        'instance',
        'data/vector_db',
        'data/backups'
    ]
    
    for directory in directories:
        dir_path = project_root / directory
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"✓ Created directory: {directory}")


def validate_configuration():
    """Validate configuration settings"""
    print("\n🔍 Validating configuration...")
    
    warnings = []
    errors = []
    
    # Check required environment variables
    if config.security.secret_key == 'dev-secret-key-change-in-production':
        if not config.debug:
            errors.append("SECRET_KEY must be changed in production")
        else:
            warnings.append("Using default SECRET_KEY (OK for development)")
    
    # Check OpenAI configuration
    if not config.openai.api_key:
        warnings.append("OPENAI_API_KEY not set - AI features will use placeholders")
    elif not config.openai.api_key.startswith('sk-'):
        warnings.append("OPENAI_API_KEY format appears invalid")
    
    # Check database configuration
    if config.database.url.startswith('sqlite:'):
        warnings.append("Using SQLite database (consider PostgreSQL for production)")
    
    # Check file storage
    if config.file_storage.provider == 'local':
        upload_path = Path(config.file_storage.local_path)
        if not upload_path.exists():
            upload_path.mkdir(parents=True, exist_ok=True)
            print(f"✓ Created upload directory: {config.file_storage.local_path}")
    
    # Print results
    if errors:
        print("\n❌ Configuration Errors:")
        for error in errors:
            print(f"  - {error}")
    
    if warnings:
        print("\n⚠️  Configuration Warnings:")
        for warning in warnings:
            print(f"  - {warning}")
    
    if not errors and not warnings:
        print("✓ Configuration looks good!")
    
    return len(errors) == 0


def setup_database():
    """Setup database tables"""
    print("\n🗄️  Setting up database...")
    
    try:
        # Import Flask app to trigger database initialization
        from app import app
        
        with app.app_context():
            from models import db
            db.create_all()
            print("✓ Database tables created successfully")
            
    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        return False
        
    return True


def check_dependencies():
    """Check if required dependencies are installed"""
    print("\n📦 Checking dependencies...")
    
    required_packages = [
        'flask',
        'flask_sqlalchemy',
        'python-dotenv',
        'psutil'
    ]
    
    optional_packages = [
        ('openai', 'AI integration features'),
        ('chromadb', 'Vector database for document search'),
        ('redis', 'Caching and session storage'),
        ('celery', 'Background task processing')
    ]
    
    missing_required = []
    missing_optional = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✓ {package}")
        except ImportError:
            missing_required.append(package)
            print(f"❌ {package} (required)")
    
    for package, description in optional_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✓ {package} - {description}")
        except ImportError:
            missing_optional.append((package, description))
            print(f"⚠️  {package} - {description} (optional)")
    
    if missing_required:
        print(f"\n❌ Missing required packages: {', '.join(missing_required)}")
        print("Run: pip install -r requirements.txt")
        return False
    
    if missing_optional:
        print(f"\n⚠️  Missing optional packages for enhanced features:")
        for package, description in missing_optional:
            print(f"  - {package}: {description}")
    
    return True


def main():
    """Main setup function"""
    print("🚀 AI Executive Suite Enhanced Setup")
    print("=" * 50)
    
    # Setup logging
    setup_logging()
    
    # Check dependencies
    if not check_dependencies():
        print("\n❌ Setup failed due to missing dependencies")
        sys.exit(1)
    
    # Create directories
    print("\n📁 Creating directories...")
    create_directories()
    
    # Validate configuration
    if not validate_configuration():
        print("\n❌ Setup failed due to configuration errors")
        sys.exit(1)
    
    # Setup database
    if not setup_database():
        print("\n❌ Setup failed due to database errors")
        sys.exit(1)
    
    print("\n✅ Setup completed successfully!")
    print("\nNext steps:")
    print("1. Copy .env.example to .env and update with your settings")
    print("2. Set your OPENAI_API_KEY in .env for AI features")
    print("3. Run: python app.py")
    print("\nFor production deployment:")
    print("1. Use PostgreSQL instead of SQLite")
    print("2. Set up Redis for caching")
    print("3. Configure proper SECRET_KEY")
    print("4. Enable monitoring and logging")


if __name__ == '__main__':
    main()