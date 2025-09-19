#!/usr/bin/env python3
"""
Simple test script for personality service functionality.
"""

import os
import sys
import tempfile
from flask import Flask
from models import db, User, PersonalityProfile, ExecutiveType
from services.personality_service import PersonalityService

def test_personality_service():
    """Test basic personality service functionality."""
    
    # Create test app with in-memory database
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'test-secret-key'
    
    db.init_app(app)
    
    with app.app_context():
        # Create all tables
        db.create_all()
        
        # Create test user
        user = User(username='testuser', email='test@example.com')
        db.session.add(user)
        db.session.commit()
        
        # Initialize personality service
        personality_service = PersonalityService()
        
        # Test 1: Create a personality profile
        print("Test 1: Creating personality profile...")
        profile_data = {
            'name': 'Test CEO Profile',
            'description': 'A test CEO personality profile',
            'executive_type': 'ceo',
            'industry_specialization': 'technology',
            'communication_style': 'formal',
            'decision_making_style': 'analytical',
            'risk_tolerance': 'medium',
            'experience_level': 'expert',
            'background_context': 'Experienced technology executive',
            'expertise_domains': ['Strategic Planning', 'Technology Strategy'],
            'tone_preferences': {
                'formality': 0.8,
                'enthusiasm': 0.6,
                'directness': 0.7,
                'technical_depth': 0.5
            },
            'personality_traits': {
                'analytical': 0.9,
                'collaborative': 0.7,
                'innovative': 0.8,
                'detail_oriented': 0.6,
                'decisive': 0.8
            },
            'is_default': True,
            'is_public': False
        }
        
        try:
            profile = personality_service.create_profile(user.id, profile_data)
            print(f"✓ Created profile: {profile.name} (ID: {profile.id})")
            
            # Verify profile data
            assert profile.name == profile_data['name']
            assert profile.executive_type == ExecutiveType.CEO
            assert profile.is_default == True
            assert profile.get_expertise_domains() == profile_data['expertise_domains']
            print("✓ Profile data verification passed")
            
        except Exception as e:
            print(f"✗ Failed to create profile: {e}")
            return False
        
        # Test 2: Get user profiles
        print("\nTest 2: Getting user profiles...")
        try:
            profiles = personality_service.get_user_profiles(user.id)
            assert len(profiles) == 1
            assert profiles[0].id == profile.id
            print(f"✓ Retrieved {len(profiles)} profile(s)")
        except Exception as e:
            print(f"✗ Failed to get user profiles: {e}")
            return False
        
        # Test 3: Get default profile
        print("\nTest 3: Getting default profile...")
        try:
            default_profile = personality_service.get_default_profile(user.id, 'ceo')
            assert default_profile is not None
            assert default_profile.is_default == True
            print(f"✓ Retrieved default profile: {default_profile.name}")
        except Exception as e:
            print(f"✗ Failed to get default profile: {e}")
            return False
        
        # Test 4: Update profile
        print("\nTest 4: Updating profile...")
        try:
            update_data = {
                'name': 'Updated CEO Profile',
                'communication_style': 'casual',
                'risk_tolerance': 'high'
            }
            
            updated_profile = personality_service.update_profile(
                profile.id, user.id, update_data
            )
            
            assert updated_profile.name == 'Updated CEO Profile'
            assert updated_profile.communication_style.value == 'casual'
            assert updated_profile.risk_tolerance == 'high'
            print("✓ Profile updated successfully")
        except Exception as e:
            print(f"✗ Failed to update profile: {e}")
            return False
        
        # Test 5: Clone profile
        print("\nTest 5: Cloning profile...")
        try:
            cloned_profile = personality_service.clone_profile(
                profile.id, user.id, 'Cloned CEO Profile'
            )
            
            assert cloned_profile.name == 'Cloned CEO Profile'
            assert cloned_profile.parent_profile_id == profile.id
            assert cloned_profile.is_default == False
            print(f"✓ Profile cloned successfully: {cloned_profile.name}")
        except Exception as e:
            print(f"✗ Failed to clone profile: {e}")
            return False
        
        # Test 6: Export/Import profile
        print("\nTest 6: Export/Import profile...")
        try:
            # Export profile
            export_data = personality_service.export_profile(profile.id, user.id)
            assert 'name' in export_data
            assert 'export_metadata' in export_data
            print("✓ Profile exported successfully")
            
            # Import profile
            imported_profile = personality_service.import_profile(user.id, export_data)
            assert imported_profile.name.startswith('Imported:')
            print(f"✓ Profile imported successfully: {imported_profile.name}")
        except Exception as e:
            print(f"✗ Failed to export/import profile: {e}")
            return False
        
        # Test 7: Validation
        print("\nTest 7: Testing validation...")
        try:
            # Test valid data
            valid_data = {
                'name': 'Valid Profile',
                'executive_type': 'cto'
            }
            errors = personality_service.validate_profile_data(valid_data)
            assert len(errors) == 0
            print("✓ Valid data passed validation")
            
            # Test invalid data
            invalid_data = {
                'executive_type': 'invalid_type'
            }
            errors = personality_service.validate_profile_data(invalid_data)
            assert len(errors) > 0
            print(f"✓ Invalid data caught {len(errors)} validation errors")
        except Exception as e:
            print(f"✗ Failed validation test: {e}")
            return False
        
        print("\n🎉 All personality service tests passed!")
        return True

if __name__ == '__main__':
    success = test_personality_service()
    sys.exit(0 if success else 1)