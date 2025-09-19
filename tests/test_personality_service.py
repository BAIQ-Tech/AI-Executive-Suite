"""
Tests for the personality service functionality.
"""

import pytest
import json
from datetime import datetime, timedelta
from flask import Flask
from models import (
    db, User, PersonalityProfile, PersonalityProfileShare,
    ExecutiveType, CommunicationStyle, IndustrySpecialization, ExpertiseLevel
)
from services.personality_service import PersonalityService


@pytest.fixture
def app():
    """Create test Flask app."""
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def personality_service():
    """Create personality service instance."""
    return PersonalityService()


@pytest.fixture
def test_user(app):
    """Create test user."""
    with app.app_context():
        user = User(username='testuser', email='test@example.com')
        db.session.add(user)
        db.session.commit()
        return user


@pytest.fixture
def sample_profile_data():
    """Sample profile data for testing."""
    return {
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


class TestPersonalityService:
    """Test personality service functionality."""
    
    def test_create_profile(self, app, personality_service, test_user, sample_profile_data):
        """Test creating a personality profile."""
        with app.app_context():
            profile = personality_service.create_profile(test_user.id, sample_profile_data)
            
            assert profile is not None
            assert profile.name == sample_profile_data['name']
            assert profile.executive_type == ExecutiveType.CEO
            assert profile.industry_specialization == IndustrySpecialization.TECHNOLOGY
            assert profile.communication_style == CommunicationStyle.FORMAL
            assert profile.is_default == True
            assert profile.user_id == test_user.id
            
            # Check JSON fields
            assert profile.get_expertise_domains() == sample_profile_data['expertise_domains']
            assert profile.get_tone_preferences() == sample_profile_data['tone_preferences']
            assert profile.get_personality_traits() == sample_profile_data['personality_traits']
    
    def test_create_profile_validation(self, app, personality_service, test_user):
        """Test profile creation validation."""
        with app.app_context():
            # Test missing required fields
            with pytest.raises(ValueError, match="Profile name is required"):
                personality_service.create_profile(test_user.id, {})
            
            with pytest.raises(ValueError, match="Executive type is required"):
                personality_service.create_profile(test_user.id, {'name': 'Test'})
    
    def test_update_profile(self, app, personality_service, test_user, sample_profile_data):
        """Test updating a personality profile."""
        with app.app_context():
            # Create profile
            profile = personality_service.create_profile(test_user.id, sample_profile_data)
            
            # Update profile
            update_data = {
                'name': 'Updated CEO Profile',
                'description': 'Updated description',
                'communication_style': 'casual',
                'risk_tolerance': 'high'
            }
            
            updated_profile = personality_service.update_profile(
                profile.id, test_user.id, update_data
            )
            
            assert updated_profile.name == 'Updated CEO Profile'
            assert updated_profile.description == 'Updated description'
            assert updated_profile.communication_style == CommunicationStyle.CASUAL
            assert updated_profile.risk_tolerance == 'high'
    
    def test_get_profile(self, app, personality_service, test_user, sample_profile_data):
        """Test getting a personality profile."""
        with app.app_context():
            # Create profile
            created_profile = personality_service.create_profile(test_user.id, sample_profile_data)
            
            # Get profile
            profile = personality_service.get_profile(created_profile.id, test_user.id)
            
            assert profile is not None
            assert profile.id == created_profile.id
            assert profile.name == sample_profile_data['name']
    
    def test_get_user_profiles(self, app, personality_service, test_user, sample_profile_data):
        """Test getting all profiles for a user."""
        with app.app_context():
            # Create multiple profiles
            ceo_data = sample_profile_data.copy()
            ceo_data['name'] = 'CEO Profile'
            ceo_data['executive_type'] = 'ceo'
            
            cto_data = sample_profile_data.copy()
            cto_data['name'] = 'CTO Profile'
            cto_data['executive_type'] = 'cto'
            
            personality_service.create_profile(test_user.id, ceo_data)
            personality_service.create_profile(test_user.id, cto_data)
            
            # Get all profiles
            all_profiles = personality_service.get_user_profiles(test_user.id)
            assert len(all_profiles) == 2
            
            # Get CEO profiles only
            ceo_profiles = personality_service.get_user_profiles(test_user.id, 'ceo')
            assert len(ceo_profiles) == 1
            assert ceo_profiles[0].executive_type == ExecutiveType.CEO
    
    def test_get_default_profile(self, app, personality_service, test_user):
        """Test getting default profile."""
        with app.app_context():
            # Should create default profile if none exists
            profile = personality_service.get_default_profile(test_user.id, 'ceo')
            
            assert profile is not None
            assert profile.is_default == True
            assert profile.executive_type == ExecutiveType.CEO
            assert profile.name == 'Default CEO'
    
    def test_delete_profile(self, app, personality_service, test_user, sample_profile_data):
        """Test deleting a personality profile."""
        with app.app_context():
            # Create profile
            profile = personality_service.create_profile(test_user.id, sample_profile_data)
            profile_id = profile.id
            
            # Delete profile
            success = personality_service.delete_profile(profile_id, test_user.id)
            assert success == True
            
            # Verify profile is deleted/deactivated
            deleted_profile = PersonalityProfile.query.get(profile_id)
            # Default profiles are deactivated, not deleted
            if profile.is_default:
                assert deleted_profile.is_active == False
            else:
                assert deleted_profile is None
    
    def test_clone_profile(self, app, personality_service, test_user, sample_profile_data):
        """Test cloning a personality profile."""
        with app.app_context():
            # Create original profile
            original = personality_service.create_profile(test_user.id, sample_profile_data)
            
            # Clone profile
            cloned = personality_service.clone_profile(original.id, test_user.id, 'Cloned Profile')
            
            assert cloned is not None
            assert cloned.name == 'Cloned Profile'
            assert cloned.executive_type == original.executive_type
            assert cloned.industry_specialization == original.industry_specialization
            assert cloned.parent_profile_id == original.id
            assert cloned.is_default == False  # Cloned profiles are never default
            assert cloned.is_public == False   # Cloned profiles are private
            
            # Check that JSON fields are copied
            assert cloned.get_expertise_domains() == original.get_expertise_domains()
            assert cloned.get_tone_preferences() == original.get_tone_preferences()
    
    def test_share_profile(self, app, personality_service, test_user, sample_profile_data):
        """Test sharing a personality profile."""
        with app.app_context():
            # Create another user
            other_user = User(username='otheruser', email='other@example.com')
            db.session.add(other_user)
            db.session.commit()
            
            # Create profile
            profile = personality_service.create_profile(test_user.id, sample_profile_data)
            
            # Share profile
            share_data = {
                'shared_with': other_user.id,
                'share_type': 'view',
                'expires_at': datetime.utcnow() + timedelta(days=30)
            }
            
            share = personality_service.share_profile(profile.id, test_user.id, share_data)
            
            assert share is not None
            assert share.profile_id == profile.id
            assert share.shared_by == test_user.id
            assert share.shared_with == other_user.id
            assert share.share_type == 'view'
    
    def test_export_import_profile(self, app, personality_service, test_user, sample_profile_data):
        """Test exporting and importing personality profiles."""
        with app.app_context():
            # Create profile
            original = personality_service.create_profile(test_user.id, sample_profile_data)
            
            # Export profile
            export_data = personality_service.export_profile(original.id, test_user.id)
            
            assert 'name' in export_data
            assert 'executive_type' in export_data
            assert 'export_metadata' in export_data
            assert export_data['name'] == sample_profile_data['name']
            
            # Import profile
            imported = personality_service.import_profile(test_user.id, export_data)
            
            assert imported is not None
            assert imported.name == f"Imported: {sample_profile_data['name']}"
            assert imported.executive_type == original.executive_type
            assert imported.is_default == False
            assert imported.is_public == False
    
    def test_validate_profile_data(self, personality_service):
        """Test profile data validation."""
        # Valid data
        valid_data = {
            'name': 'Test Profile',
            'executive_type': 'ceo',
            'industry_specialization': 'technology',
            'communication_style': 'formal',
            'experience_level': 'expert'
        }
        
        errors = personality_service.validate_profile_data(valid_data)
        assert len(errors) == 0
        
        # Invalid data
        invalid_data = {
            'executive_type': 'invalid_type',
            'industry_specialization': 'invalid_industry',
            'tone_preferences': 'not_a_dict',
            'personality_traits': {'invalid_trait': 2.0}  # Out of range
        }
        
        errors = personality_service.validate_profile_data(invalid_data)
        assert len(errors) > 0
        assert any('Profile name is required' in error for error in errors)
        assert any('Invalid executive type' in error for error in errors)
    
    def test_get_public_profiles(self, app, personality_service, test_user, sample_profile_data):
        """Test getting public personality profiles."""
        with app.app_context():
            # Create public profile
            public_data = sample_profile_data.copy()
            public_data['is_public'] = True
            public_data['name'] = 'Public CEO Profile'
            
            # Create private profile
            private_data = sample_profile_data.copy()
            private_data['is_public'] = False
            private_data['name'] = 'Private CEO Profile'
            
            personality_service.create_profile(test_user.id, public_data)
            personality_service.create_profile(test_user.id, private_data)
            
            # Get public profiles
            public_profiles = personality_service.get_public_profiles()
            
            assert len(public_profiles) == 1
            assert public_profiles[0].name == 'Public CEO Profile'
            assert public_profiles[0].is_public == True
    
    def test_get_shared_profiles(self, app, personality_service, test_user, sample_profile_data):
        """Test getting profiles shared with a user."""
        with app.app_context():
            # Create another user
            other_user = User(username='otheruser', email='other@example.com')
            db.session.add(other_user)
            db.session.commit()
            
            # Create and share profile
            profile = personality_service.create_profile(test_user.id, sample_profile_data)
            share_data = {'shared_with': other_user.id, 'share_type': 'view'}
            personality_service.share_profile(profile.id, test_user.id, share_data)
            
            # Get shared profiles
            shared_profiles = personality_service.get_shared_profiles(other_user.id)
            
            assert len(shared_profiles) == 1
            assert shared_profiles[0].profile_id == profile.id
            assert shared_profiles[0].shared_with == other_user.id
    
    def test_default_profiles_creation(self, app, personality_service, test_user):
        """Test that default profiles are created correctly."""
        with app.app_context():
            # Test each executive type
            for exec_type in ['ceo', 'cto', 'cfo']:
                profile = personality_service.get_default_profile(test_user.id, exec_type)
                
                assert profile is not None
                assert profile.is_default == True
                assert profile.executive_type.value == exec_type
                assert profile.name == f'Default {exec_type.upper()}'
                
                # Check that default values are set
                assert profile.get_expertise_domains() is not None
                assert len(profile.get_expertise_domains()) > 0
                assert profile.get_tone_preferences() is not None
                assert profile.get_personality_traits() is not None


class TestPersonalityProfileModel:
    """Test personality profile model functionality."""
    
    def test_profile_creation(self, app, test_user):
        """Test creating a personality profile model."""
        with app.app_context():
            profile = PersonalityProfile(
                user_id=test_user.id,
                name='Test Profile',
                executive_type=ExecutiveType.CEO
            )
            
            db.session.add(profile)
            db.session.commit()
            
            assert profile.id is not None
            assert profile.user_id == test_user.id
            assert profile.name == 'Test Profile'
            assert profile.executive_type == ExecutiveType.CEO
    
    def test_json_field_methods(self, app, test_user):
        """Test JSON field getter/setter methods."""
        with app.app_context():
            profile = PersonalityProfile(
                user_id=test_user.id,
                name='Test Profile',
                executive_type=ExecutiveType.CEO
            )
            
            # Test expertise domains
            domains = ['Strategic Planning', 'Leadership']
            profile.set_expertise_domains(domains)
            assert profile.get_expertise_domains() == domains
            
            # Test tone preferences
            tone_prefs = {'formality': 0.8, 'enthusiasm': 0.6}
            profile.set_tone_preferences(tone_prefs)
            assert profile.get_tone_preferences() == tone_prefs
            
            # Test personality traits
            traits = {'analytical': 0.9, 'collaborative': 0.7}
            profile.set_personality_traits(traits)
            assert profile.get_personality_traits() == traits
    
    def test_usage_tracking(self, app, test_user):
        """Test usage tracking functionality."""
        with app.app_context():
            profile = PersonalityProfile(
                user_id=test_user.id,
                name='Test Profile',
                executive_type=ExecutiveType.CEO
            )
            
            db.session.add(profile)
            db.session.commit()
            
            initial_count = profile.usage_count
            initial_last_used = profile.last_used
            
            # Increment usage
            profile.increment_usage()
            
            assert profile.usage_count == initial_count + 1
            assert profile.last_used > initial_last_used
    
    def test_child_profile_creation(self, app, test_user):
        """Test creating child profiles."""
        with app.app_context():
            parent = PersonalityProfile(
                user_id=test_user.id,
                name='Parent Profile',
                executive_type=ExecutiveType.CEO,
                industry_specialization=IndustrySpecialization.TECHNOLOGY
            )
            
            parent.set_expertise_domains(['Strategic Planning'])
            parent.set_tone_preferences({'formality': 0.8})
            
            db.session.add(parent)
            db.session.commit()
            
            # Create child profile
            child = parent.create_child_profile('Child Profile')
            
            assert child.name == 'Child Profile'
            assert child.parent_profile_id == parent.id
            assert child.executive_type == parent.executive_type
            assert child.industry_specialization == parent.industry_specialization
            assert child.get_expertise_domains() == parent.get_expertise_domains()
            assert child.get_tone_preferences() == parent.get_tone_preferences()


if __name__ == '__main__':
    pytest.main([__file__])