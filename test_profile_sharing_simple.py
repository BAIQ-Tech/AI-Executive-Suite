#!/usr/bin/env python3
"""
Simple test script for profile sharing service functionality.
"""

import os
import sys
import tempfile
from datetime import datetime, timedelta
from flask import Flask
from models import db, User, PersonalityProfile, PersonalityProfileShare, ExecutiveType
from services.profile_sharing_service import ProfileSharingService

def test_profile_sharing_service():
    """Test basic profile sharing service functionality."""
    
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
        
        # Create test users
        user1 = User(username='user1', email='user1@example.com')
        user2 = User(username='user2', email='user2@example.com')
        db.session.add(user1)
        db.session.add(user2)
        db.session.commit()
        
        # Create test profile
        profile = PersonalityProfile(
            user_id=user1.id,
            name='Test CEO Profile',
            executive_type=ExecutiveType.CEO,
            description='A test profile for sharing'
        )
        db.session.add(profile)
        db.session.commit()
        
        # Initialize sharing service
        sharing_service = ProfileSharingService()
        
        # Test 1: Create share link
        print("Test 1: Creating share link...")
        try:
            share_config = {
                'share_type': 'copy',
                'expires_at': (datetime.utcnow() + timedelta(days=7)).isoformat()
            }
            
            result = sharing_service.create_share_link(profile.id, user1.id, share_config)
            
            assert result['success'] == True
            assert 'share' in result
            assert result['share']['share_type'] == 'copy'
            assert result['share']['link'].startswith('/personality/shared/')
            
            share_id = result['share']['id']
            print(f"✓ Created share link: {result['share']['link']}")
            
        except Exception as e:
            print(f"✗ Failed to create share link: {e}")
            return False
        
        # Test 2: Access shared profile
        print("\nTest 2: Accessing shared profile...")
        try:
            access_result = sharing_service.access_shared_profile(share_id, user2.id)
            
            assert access_result['success'] == True
            assert 'profile' in access_result
            assert 'share_info' in access_result
            assert access_result['profile']['name'] == 'Test CEO Profile'
            assert access_result['share_info']['can_copy'] == True
            
            print(f"✓ Accessed shared profile: {access_result['profile']['name']}")
            
        except Exception as e:
            print(f"✗ Failed to access shared profile: {e}")
            return False
        
        # Test 3: Copy shared profile
        print("\nTest 3: Copying shared profile...")
        try:
            copy_result = sharing_service.copy_shared_profile(
                share_id, user2.id, 'Copied CEO Profile'
            )
            
            assert copy_result['success'] == True
            assert 'profile' in copy_result
            assert copy_result['profile']['name'] == 'Copied CEO Profile'
            assert copy_result['profile']['user_id'] == user2.id
            
            print(f"✓ Copied profile: {copy_result['profile']['name']}")
            
        except Exception as e:
            print(f"✗ Failed to copy shared profile: {e}")
            return False
        
        # Test 4: Get user shares
        print("\nTest 4: Getting user shares...")
        try:
            shares_result = sharing_service.get_user_shares(user1.id)
            
            assert shares_result['success'] == True
            assert 'shares' in shares_result
            assert len(shares_result['shares']) == 1
            assert shares_result['shares'][0]['profile_id'] == profile.id
            
            print(f"✓ Retrieved {len(shares_result['shares'])} share(s)")
            
        except Exception as e:
            print(f"✗ Failed to get user shares: {e}")
            return False
        
        # Test 5: Get shared with user
        print("\nTest 5: Getting profiles shared with user...")
        try:
            # Create a direct share to user2
            direct_share = PersonalityProfileShare(
                profile_id=profile.id,
                shared_by=user1.id,
                shared_with=user2.id,
                share_type='view'
            )
            db.session.add(direct_share)
            db.session.commit()
            
            shared_result = sharing_service.get_shared_with_user(user2.id)
            
            assert shared_result['success'] == True
            assert 'shares' in shared_result
            assert len(shared_result['shares']) >= 1
            
            print(f"✓ Retrieved {len(shared_result['shares'])} shared profile(s)")
            
        except Exception as e:
            print(f"✗ Failed to get shared profiles: {e}")
            return False
        
        # Test 6: Revoke share
        print("\nTest 6: Revoking share...")
        try:
            revoke_result = sharing_service.revoke_share(share_id, user1.id)
            
            assert revoke_result['success'] == True
            
            # Verify share is revoked
            revoked_share = PersonalityProfileShare.query.get(share_id)
            assert revoked_share.is_active == False
            
            print("✓ Share revoked successfully")
            
        except Exception as e:
            print(f"✗ Failed to revoke share: {e}")
            return False
        
        # Test 7: Submit to marketplace
        print("\nTest 7: Submitting to marketplace...")
        try:
            marketplace_data = {
                'description': 'A great CEO profile for the marketplace',
                'category': 'executive',
                'tags': ['leadership', 'strategy']
            }
            
            submit_result = sharing_service.submit_to_marketplace(
                profile.id, user1.id, marketplace_data
            )
            
            assert submit_result['success'] == True
            assert 'profile' in submit_result
            
            # Verify profile is now public
            updated_profile = PersonalityProfile.query.get(profile.id)
            assert updated_profile.is_public == True
            
            print("✓ Profile submitted to marketplace")
            
        except Exception as e:
            print(f"✗ Failed to submit to marketplace: {e}")
            return False
        
        # Test 8: Get marketplace profiles
        print("\nTest 8: Getting marketplace profiles...")
        try:
            marketplace_result = sharing_service.get_marketplace_profiles()
            
            assert marketplace_result['success'] == True
            assert 'profiles' in marketplace_result
            assert marketplace_result['total_count'] >= 1
            
            print(f"✓ Retrieved {marketplace_result['total_count']} marketplace profile(s)")
            
        except Exception as e:
            print(f"✗ Failed to get marketplace profiles: {e}")
            return False
        
        # Test 9: Get profile versions
        print("\nTest 9: Getting profile versions...")
        try:
            versions_result = sharing_service.get_profile_versions(profile.id, user1.id)
            
            assert versions_result['success'] == True
            assert 'versions' in versions_result
            assert len(versions_result['versions']) >= 1
            
            print(f"✓ Retrieved {len(versions_result['versions'])} version(s)")
            
        except Exception as e:
            print(f"✗ Failed to get profile versions: {e}")
            return False
        
        # Test 10: Create profile version
        print("\nTest 10: Creating profile version...")
        try:
            version_data = {
                'name': 'Test CEO Profile v2.0',
                'version': '2.0'
            }
            
            version_result = sharing_service.create_profile_version(
                profile.id, user1.id, version_data
            )
            
            assert version_result['success'] == True
            assert 'version' in version_result
            assert version_result['version']['name'] == version_data['name']
            assert version_result['version']['version'] == version_data['version']
            
            print(f"✓ Created profile version: {version_result['version']['name']}")
            
        except Exception as e:
            print(f"✗ Failed to create profile version: {e}")
            return False
        
        # Test 11: Get collaboration stats
        print("\nTest 11: Getting collaboration stats...")
        try:
            stats_result = sharing_service.get_collaboration_stats(user1.id)
            
            assert stats_result['success'] == True
            assert 'stats' in stats_result
            assert 'profiles_shared' in stats_result['stats']
            assert 'collaboration_score' in stats_result['stats']
            
            stats = stats_result['stats']
            print(f"✓ Collaboration stats: {stats['profiles_shared']} shared, score: {stats['collaboration_score']:.2f}")
            
        except Exception as e:
            print(f"✗ Failed to get collaboration stats: {e}")
            return False
        
        # Test 12: Rate marketplace profile
        print("\nTest 12: Rating marketplace profile...")
        try:
            rating_data = {
                'rating': 5,
                'comment': 'Excellent profile!'
            }
            
            rating_result = sharing_service.rate_marketplace_profile(
                profile.id, user2.id, rating_data
            )
            
            assert rating_result['success'] == True
            
            print("✓ Profile rated successfully")
            
        except Exception as e:
            print(f"✗ Failed to rate profile: {e}")
            return False
        
        print("\n🎉 All profile sharing service tests passed!")
        return True

if __name__ == '__main__':
    success = test_profile_sharing_service()
    sys.exit(0 if success else 1)