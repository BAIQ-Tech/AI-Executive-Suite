#!/usr/bin/env python3
"""
Simple verification script to check the enhanced project setup
"""

import sys
from pathlib import Path

def check_project_structure():
    """Check that all required files exist"""
    print("🔍 Checking project structure...")
    
    required_paths = [
        'services/__init__.py',
        'services/ai_integration.py',
        'services/analytics.py',
        'services/collaboration.py',
        'services/document_processing.py',
        'services/registry.py',
        'config/__init__.py',
        'config/settings.py',
        'utils/__init__.py',
        'utils/logging.py',
        'utils/monitoring.py',
        'scripts/__init__.py',
        'scripts/setup.py',
        'requirements.txt',
        '.env.example'
    ]
    
    missing = []
    for path in required_paths:
        if not Path(path).exists():
            missing.append(path)
        else:
            print(f"✓ {path}")
    
    if missing:
        print(f"\n❌ Missing files: {missing}")
        return False
    
    print("✅ All required files present")
    return True

def check_imports():
    """Check that modules can be imported"""
    print("\n🔍 Checking imports...")
    
    try:
        from config.settings import config
        print("✓ Configuration imported successfully")
        
        from services.ai_integration import AIIntegrationService
        from services.analytics import AnalyticsService
        from services.collaboration import CollaborationService
        from services.document_processing import DocumentProcessingService
        print("✓ Services imported successfully")
        
        from utils.logging import setup_logging
        from utils.monitoring import monitoring_service
        print("✓ Utilities imported successfully")
        
        from services.registry import service_manager
        print("✓ Service registry imported successfully")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def check_service_initialization():
    """Check that services can be initialized"""
    print("\n🔍 Checking service initialization...")
    
    try:
        from services.ai_integration import AIIntegrationService
        from config.settings import config_manager
        
        service_config = config_manager.get_service_config('ai_integration')
        service = AIIntegrationService(service_config)
        print("✓ AI Integration service initialized")
        
        from services.registry import service_manager
        status = service_manager.get_status()
        print(f"✓ Service manager status: {len(status['services'])} services registered")
        
        return True
        
    except Exception as e:
        print(f"❌ Service initialization error: {e}")
        return False

def main():
    """Main verification function"""
    print("🚀 AI Executive Suite Enhanced Setup Verification")
    print("=" * 60)
    
    checks = [
        check_project_structure,
        check_imports,
        check_service_initialization
    ]
    
    passed = 0
    for check in checks:
        if check():
            passed += 1
    
    print(f"\n📊 Results: {passed}/{len(checks)} checks passed")
    
    if passed == len(checks):
        print("✅ Setup verification successful!")
        print("\nNext steps:")
        print("1. Copy .env.example to .env")
        print("2. Set your OPENAI_API_KEY in .env")
        print("3. Run: python3 scripts/setup.py")
        print("4. Run: python3 app.py")
        return True
    else:
        print("❌ Setup verification failed!")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)