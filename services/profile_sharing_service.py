"""
Profile Sharing Service for managing personality profile sharing and collaboration.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from flask import current_app
from models import (
    db, PersonalityProfile, PersonalityProfileShare, User,
    ExecutiveType, CommunicationStyle, IndustrySpecialization
)

logger = logging.getLogger(__name__)


class ProfileSharingService:
    """Service for managing personality profile sharing and marketplace."""
    
    def __init__(self):
        self.share_types = ['view', 'copy', 'collaborate']
        self.marketplace_categories = self._get_marketplace_categories()
    
    def create_share_link(self, profile_id: int, user_id: int, 
                         share_config: Dict[str, Any]) -> Dict[str, Any]:
        """Create a shareable link for a personality profile."""
        try:
            # Verify profile ownership
            profile = PersonalityProfile.query.filter_by(
                id=profile_id, 
                user_id=user_id
            ).first()
            
            if not profile:
                return {
                    'success': False,
                    'error': 'Profile not found or access denied'
                }
            
            # Create share record
            share = PersonalityProfileShare(
                profile_id=profile_id,
                shared_by=user_id,
                shared_with=share_config.get('shared_with'),  # None for public shares
                share_type=share_config.get('share_type', 'view'),
                expires_at=self._parse_expiration(share_config.get('expires_at'))
            )
            
            db.session.add(share)
            db.session.commit()
            
            # Generate share link
            share_link = f"/personality/shared/{share.id}"
            
            return {
                'success': True,
                'share': {
                    'id': share.id,
                    'link': share_link,
                    'share_type': share.share_type,
                    'expires_at': share.expires_at.isoformat() if share.expires_at else None,
                    'is_public': share.shared_with is None,
                    'created_at': share.created_at.isoformat()
                }
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating share link: {str(e)}")
            return {
                'success': False,
                'error': 'Failed to create share link'
            }
    
    def access_shared_profile(self, share_id: int, user_id: Optional[int] = None) -> Dict[str, Any]:
        """Access a shared personality profile."""
        try:
            share = PersonalityProfileShare.query.get(share_id)
            
            if not share or not share.is_active:
                return {
                    'success': False,
                    'error': 'Share link not found or expired'
                }
            
            # Check expiration
            if share.is_expired():
                return {
                    'success': False,
                    'error': 'Share link has expired'
                }
            
            # Check access permissions
            if share.shared_with and (not user_id or share.shared_with != user_id):
                return {
                    'success': False,
                    'error': 'Access denied - this profile is privately shared'
                }
            
            # Update access tracking
            share.increment_access()
            db.session.commit()
            
            # Get profile data
            profile = share.profile
            if not profile or not profile.is_active:
                return {
                    'success': False,
                    'error': 'Profile is no longer available'
                }
            
            # Return profile data based on share type
            include_sensitive = share.share_type in ['copy', 'collaborate']
            
            return {
                'success': True,
                'profile': profile.to_dict(include_sensitive=include_sensitive),
                'share_info': {
                    'share_type': share.share_type,
                    'shared_by': {
                        'id': share.sharer.id,
                        'username': share.sharer.username,
                        'name': share.sharer.name
                    },
                    'access_count': share.access_count,
                    'can_copy': share.share_type in ['copy', 'collaborate'],
                    'can_collaborate': share.share_type == 'collaborate'
                }
            }
            
        except Exception as e:
            logger.error(f"Error accessing shared profile: {str(e)}")
            return {
                'success': False,
                'error': 'Failed to access shared profile'
            }
    
    def copy_shared_profile(self, share_id: int, user_id: int, 
                           new_name: str) -> Dict[str, Any]:
        """Copy a shared profile to user's collection."""
        try:
            # Access the shared profile
            access_result = self.access_shared_profile(share_id, user_id)
            
            if not access_result['success']:
                return access_result
            
            if not access_result['share_info']['can_copy']:
                return {
                    'success': False,
                    'error': 'This profile cannot be copied'
                }
            
            # Get the original profile
            original_profile = PersonalityProfile.query.get(
                access_result['profile']['id']
            )
            
            if not original_profile:
                return {
                    'success': False,
                    'error': 'Original profile not found'
                }
            
            # Create a copy
            copied_profile = original_profile.create_child_profile(new_name, user_id)
            copied_profile.is_default = False
            copied_profile.is_public = False
            
            db.session.add(copied_profile)
            db.session.commit()
            
            return {
                'success': True,
                'profile': copied_profile.to_dict(include_sensitive=True)
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error copying shared profile: {str(e)}")
            return {
                'success': False,
                'error': 'Failed to copy profile'
            }
    
    def get_user_shares(self, user_id: int) -> Dict[str, Any]:
        """Get all shares created by a user."""
        try:
            shares = PersonalityProfileShare.query.filter_by(
                shared_by=user_id,
                is_active=True
            ).order_by(PersonalityProfileShare.created_at.desc()).all()
            
            return {
                'success': True,
                'shares': [share.to_dict() for share in shares]
            }
            
        except Exception as e:
            logger.error(f"Error getting user shares: {str(e)}")
            return {
                'success': False,
                'error': 'Failed to retrieve shares'
            }
    
    def get_shared_with_user(self, user_id: int) -> Dict[str, Any]:
        """Get all profiles shared with a user."""
        try:
            shares = PersonalityProfileShare.query.filter_by(
                shared_with=user_id,
                is_active=True
            ).filter(
                PersonalityProfileShare.expires_at.is_(None) |
                (PersonalityProfileShare.expires_at > datetime.utcnow())
            ).order_by(PersonalityProfileShare.created_at.desc()).all()
            
            return {
                'success': True,
                'shares': [share.to_dict() for share in shares]
            }
            
        except Exception as e:
            logger.error(f"Error getting shared profiles: {str(e)}")
            return {
                'success': False,
                'error': 'Failed to retrieve shared profiles'
            }
    
    def revoke_share(self, share_id: int, user_id: int) -> Dict[str, Any]:
        """Revoke a profile share."""
        try:
            share = PersonalityProfileShare.query.filter_by(
                id=share_id,
                shared_by=user_id
            ).first()
            
            if not share:
                return {
                    'success': False,
                    'error': 'Share not found or access denied'
                }
            
            share.revoke()
            db.session.commit()
            
            return {
                'success': True,
                'message': 'Share revoked successfully'
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error revoking share: {str(e)}")
            return {
                'success': False,
                'error': 'Failed to revoke share'
            }
    
    def get_marketplace_profiles(self, filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Get public profiles for the marketplace."""
        try:
            filters = filters or {}
            
            query = PersonalityProfile.query.filter_by(
                is_public=True,
                is_active=True
            )
            
            # Apply filters
            if filters.get('executive_type'):
                query = query.filter_by(
                    executive_type=ExecutiveType(filters['executive_type'])
                )
            
            if filters.get('industry_specialization'):
                query = query.filter_by(
                    industry_specialization=IndustrySpecialization(filters['industry_specialization'])
                )
            
            if filters.get('experience_level'):
                query = query.filter_by(
                    experience_level=filters['experience_level']
                )
            
            # Sort by usage count (popularity)
            profiles = query.order_by(
                PersonalityProfile.usage_count.desc(),
                PersonalityProfile.created_at.desc()
            ).limit(50).all()
            
            # Group by categories
            categorized_profiles = self._categorize_marketplace_profiles(profiles)
            
            return {
                'success': True,
                'profiles': categorized_profiles,
                'total_count': len(profiles)
            }
            
        except Exception as e:
            logger.error(f"Error getting marketplace profiles: {str(e)}")
            return {
                'success': False,
                'error': 'Failed to retrieve marketplace profiles'
            }
    
    def submit_to_marketplace(self, profile_id: int, user_id: int, 
                            marketplace_data: Dict[str, Any]) -> Dict[str, Any]:
        """Submit a profile to the public marketplace."""
        try:
            profile = PersonalityProfile.query.filter_by(
                id=profile_id,
                user_id=user_id
            ).first()
            
            if not profile:
                return {
                    'success': False,
                    'error': 'Profile not found or access denied'
                }
            
            # Update profile for marketplace
            profile.is_public = True
            profile.description = marketplace_data.get('description', profile.description)
            
            # Add marketplace-specific metadata
            marketplace_metadata = {
                'submitted_at': datetime.utcnow().isoformat(),
                'category': marketplace_data.get('category', 'general'),
                'tags': marketplace_data.get('tags', []),
                'featured': False,
                'rating': 0.0,
                'review_count': 0
            }
            
            # Store metadata in a custom field (you might want to add this to the model)
            # For now, we'll use the existing fields
            
            db.session.commit()
            
            return {
                'success': True,
                'message': 'Profile submitted to marketplace successfully',
                'profile': profile.to_dict()
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error submitting to marketplace: {str(e)}")
            return {
                'success': False,
                'error': 'Failed to submit profile to marketplace'
            }
    
    def rate_marketplace_profile(self, profile_id: int, user_id: int, 
                               rating_data: Dict[str, Any]) -> Dict[str, Any]:
        """Rate a marketplace profile."""
        try:
            profile = PersonalityProfile.query.filter_by(
                id=profile_id,
                is_public=True
            ).first()
            
            if not profile:
                return {
                    'success': False,
                    'error': 'Profile not found in marketplace'
                }
            
            if profile.user_id == user_id:
                return {
                    'success': False,
                    'error': 'Cannot rate your own profile'
                }
            
            rating = rating_data.get('rating', 0)
            comment = rating_data.get('comment', '')
            
            if not (1 <= rating <= 5):
                return {
                    'success': False,
                    'error': 'Rating must be between 1 and 5'
                }
            
            # In a real implementation, you'd store ratings in a separate table
            # For now, we'll simulate the rating system
            
            return {
                'success': True,
                'message': 'Rating submitted successfully'
            }
            
        except Exception as e:
            logger.error(f"Error rating profile: {str(e)}")
            return {
                'success': False,
                'error': 'Failed to submit rating'
            }
    
    def get_profile_versions(self, profile_id: int, user_id: int) -> Dict[str, Any]:
        """Get version history of a profile."""
        try:
            # Get the main profile
            profile = PersonalityProfile.query.filter_by(
                id=profile_id,
                user_id=user_id
            ).first()
            
            if not profile:
                return {
                    'success': False,
                    'error': 'Profile not found or access denied'
                }
            
            # Get child profiles (versions)
            versions = PersonalityProfile.query.filter_by(
                parent_profile_id=profile_id,
                user_id=user_id,
                is_active=True
            ).order_by(PersonalityProfile.created_at.desc()).all()
            
            version_data = []
            
            # Add current version
            version_data.append({
                'id': profile.id,
                'version': profile.version,
                'name': profile.name,
                'created_at': profile.created_at.isoformat(),
                'updated_at': profile.updated_at.isoformat(),
                'is_current': True,
                'changes': 'Current version'
            })
            
            # Add historical versions
            for version in versions:
                version_data.append({
                    'id': version.id,
                    'version': version.version,
                    'name': version.name,
                    'created_at': version.created_at.isoformat(),
                    'updated_at': version.updated_at.isoformat(),
                    'is_current': False,
                    'changes': f'Cloned from version {profile.version}'
                })
            
            return {
                'success': True,
                'versions': version_data
            }
            
        except Exception as e:
            logger.error(f"Error getting profile versions: {str(e)}")
            return {
                'success': False,
                'error': 'Failed to retrieve profile versions'
            }
    
    def create_profile_version(self, profile_id: int, user_id: int, 
                             version_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new version of a profile."""
        try:
            original_profile = PersonalityProfile.query.filter_by(
                id=profile_id,
                user_id=user_id
            ).first()
            
            if not original_profile:
                return {
                    'success': False,
                    'error': 'Profile not found or access denied'
                }
            
            # Create new version
            new_version = original_profile.create_child_profile(
                version_data.get('name', f"{original_profile.name} v{self._get_next_version(original_profile)}"),
                user_id
            )
            
            new_version.version = version_data.get('version', self._get_next_version(original_profile))
            new_version.is_default = False
            new_version.is_public = False
            
            db.session.add(new_version)
            db.session.commit()
            
            return {
                'success': True,
                'version': new_version.to_dict(include_sensitive=True)
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating profile version: {str(e)}")
            return {
                'success': False,
                'error': 'Failed to create profile version'
            }
    
    def get_collaboration_stats(self, user_id: int) -> Dict[str, Any]:
        """Get collaboration statistics for a user."""
        try:
            # Profiles shared by user
            shared_count = PersonalityProfileShare.query.filter_by(
                shared_by=user_id,
                is_active=True
            ).count()
            
            # Profiles shared with user
            received_count = PersonalityProfileShare.query.filter_by(
                shared_with=user_id,
                is_active=True
            ).count()
            
            # Public profiles by user
            public_count = PersonalityProfile.query.filter_by(
                user_id=user_id,
                is_public=True,
                is_active=True
            ).count()
            
            # Total usage of user's public profiles
            public_profiles = PersonalityProfile.query.filter_by(
                user_id=user_id,
                is_public=True,
                is_active=True
            ).all()
            
            total_usage = sum(profile.usage_count for profile in public_profiles)
            
            return {
                'success': True,
                'stats': {
                    'profiles_shared': shared_count,
                    'profiles_received': received_count,
                    'public_profiles': public_count,
                    'total_profile_usage': total_usage,
                    'collaboration_score': self._calculate_collaboration_score(
                        shared_count, received_count, public_count, total_usage
                    )
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting collaboration stats: {str(e)}")
            return {
                'success': False,
                'error': 'Failed to retrieve collaboration statistics'
            }
    
    def _parse_expiration(self, expires_at: Optional[str]) -> Optional[datetime]:
        """Parse expiration date string."""
        if not expires_at:
            return None
        
        try:
            if isinstance(expires_at, str):
                return datetime.fromisoformat(expires_at)
            elif isinstance(expires_at, datetime):
                return expires_at
        except ValueError:
            pass
        
        return None
    
    def _categorize_marketplace_profiles(self, profiles: List[PersonalityProfile]) -> Dict[str, List[Dict]]:
        """Categorize marketplace profiles."""
        categories = {
            'featured': [],
            'popular': [],
            'recent': [],
            'by_type': {
                'ceo': [],
                'cto': [],
                'cfo': []
            },
            'by_industry': {}
        }
        
        # Sort profiles
        popular_profiles = sorted(profiles, key=lambda p: p.usage_count, reverse=True)[:10]
        recent_profiles = sorted(profiles, key=lambda p: p.created_at, reverse=True)[:10]
        
        categories['popular'] = [p.to_dict() for p in popular_profiles]
        categories['recent'] = [p.to_dict() for p in recent_profiles]
        
        # Group by executive type
        for profile in profiles:
            exec_type = profile.executive_type.value
            if exec_type in categories['by_type']:
                categories['by_type'][exec_type].append(profile.to_dict())
        
        # Group by industry
        for profile in profiles:
            industry = profile.industry_specialization.value
            if industry not in categories['by_industry']:
                categories['by_industry'][industry] = []
            categories['by_industry'][industry].append(profile.to_dict())
        
        return categories
    
    def _get_next_version(self, profile: PersonalityProfile) -> str:
        """Get next version number for a profile."""
        try:
            current_version = profile.version or '1.0'
            major, minor = current_version.split('.')
            return f"{major}.{int(minor) + 1}"
        except:
            return '1.1'
    
    def _calculate_collaboration_score(self, shared: int, received: int, 
                                     public: int, usage: int) -> float:
        """Calculate collaboration score based on sharing activity."""
        # Simple scoring algorithm
        score = (shared * 2 + received * 1 + public * 3 + usage * 0.1)
        return min(score / 100.0, 1.0)  # Normalize to 0-1
    
    def _get_marketplace_categories(self) -> Dict[str, List[str]]:
        """Get marketplace categories."""
        return {
            'executive_type': ['ceo', 'cto', 'cfo'],
            'industry': [
                'technology', 'finance', 'healthcare', 'manufacturing',
                'retail', 'consulting', 'education', 'government'
            ],
            'experience_level': ['junior', 'intermediate', 'senior', 'expert', 'thought_leader'],
            'specialization': [
                'startup', 'enterprise', 'non_profit', 'government',
                'consulting', 'academic', 'international'
            ]
        }