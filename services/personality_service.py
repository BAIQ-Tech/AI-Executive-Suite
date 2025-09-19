"""
Personality Service for managing AI executive personality profiles and configurations.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from flask import current_app
from models import (
    db, PersonalityProfile, PersonalityProfileShare, User, 
    ExecutiveType, CommunicationStyle, IndustrySpecialization, ExpertiseLevel
)

logger = logging.getLogger(__name__)


class PersonalityService:
    """Service for managing AI personality profiles and configurations."""
    
    def __init__(self):
        self.default_profiles = self._get_default_profiles()
    
    def create_profile(self, user_id: int, profile_data: Dict[str, Any]) -> PersonalityProfile:
        """Create a new personality profile."""
        try:
            # Validate required fields
            if not profile_data.get('name'):
                raise ValueError("Profile name is required")
            
            if not profile_data.get('executive_type'):
                raise ValueError("Executive type is required")
            
            # Create the profile
            profile = PersonalityProfile(
                user_id=user_id,
                name=profile_data['name'],
                executive_type=ExecutiveType(profile_data['executive_type']),
                description=profile_data.get('description'),
                industry_specialization=IndustrySpecialization(
                    profile_data.get('industry_specialization', 'general')
                ),
                communication_style=CommunicationStyle(
                    profile_data.get('communication_style', 'formal')
                ),
                decision_making_style=profile_data.get('decision_making_style'),
                risk_tolerance=profile_data.get('risk_tolerance', 'medium'),
                experience_level=ExpertiseLevel(
                    profile_data.get('experience_level', 'senior')
                ),
                background_context=profile_data.get('background_context'),
                is_default=profile_data.get('is_default', False),
                is_public=profile_data.get('is_public', False)
            )
            
            # Set JSON fields
            if profile_data.get('expertise_domains'):
                profile.set_expertise_domains(profile_data['expertise_domains'])
            
            if profile_data.get('tone_preferences'):
                profile.set_tone_preferences(profile_data['tone_preferences'])
            
            if profile_data.get('personality_traits'):
                profile.set_personality_traits(profile_data['personality_traits'])
            
            if profile_data.get('custom_knowledge'):
                profile.set_custom_knowledge(profile_data['custom_knowledge'])
            
            if profile_data.get('knowledge_sources'):
                profile.set_knowledge_sources(profile_data['knowledge_sources'])
            
            # If this is set as default, unset other defaults for this user/type
            if profile.is_default:
                self._unset_other_defaults(user_id, profile.executive_type)
            
            db.session.add(profile)
            db.session.commit()
            
            logger.info(f"Created personality profile {profile.id} for user {user_id}")
            return profile
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating personality profile: {str(e)}")
            raise
    
    def update_profile(self, profile_id: int, user_id: int, profile_data: Dict[str, Any]) -> PersonalityProfile:
        """Update an existing personality profile."""
        try:
            profile = PersonalityProfile.query.filter_by(
                id=profile_id, 
                user_id=user_id
            ).first()
            
            if not profile:
                raise ValueError("Profile not found or access denied")
            
            # Update basic fields
            if 'name' in profile_data:
                profile.name = profile_data['name']
            
            if 'description' in profile_data:
                profile.description = profile_data['description']
            
            if 'industry_specialization' in profile_data:
                profile.industry_specialization = IndustrySpecialization(
                    profile_data['industry_specialization']
                )
            
            if 'communication_style' in profile_data:
                profile.communication_style = CommunicationStyle(
                    profile_data['communication_style']
                )
            
            if 'decision_making_style' in profile_data:
                profile.decision_making_style = profile_data['decision_making_style']
            
            if 'risk_tolerance' in profile_data:
                profile.risk_tolerance = profile_data['risk_tolerance']
            
            if 'experience_level' in profile_data:
                profile.experience_level = ExpertiseLevel(
                    profile_data['experience_level']
                )
            
            if 'background_context' in profile_data:
                profile.background_context = profile_data['background_context']
            
            if 'is_public' in profile_data:
                profile.is_public = profile_data['is_public']
            
            # Update JSON fields
            if 'expertise_domains' in profile_data:
                profile.set_expertise_domains(profile_data['expertise_domains'])
            
            if 'tone_preferences' in profile_data:
                profile.set_tone_preferences(profile_data['tone_preferences'])
            
            if 'personality_traits' in profile_data:
                profile.set_personality_traits(profile_data['personality_traits'])
            
            if 'custom_knowledge' in profile_data:
                profile.set_custom_knowledge(profile_data['custom_knowledge'])
            
            if 'knowledge_sources' in profile_data:
                profile.set_knowledge_sources(profile_data['knowledge_sources'])
            
            # Handle default setting
            if 'is_default' in profile_data and profile_data['is_default']:
                self._unset_other_defaults(user_id, profile.executive_type)
                profile.is_default = True
            elif 'is_default' in profile_data and not profile_data['is_default']:
                profile.is_default = False
            
            profile.updated_at = datetime.utcnow()
            db.session.commit()
            
            logger.info(f"Updated personality profile {profile_id}")
            return profile
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating personality profile {profile_id}: {str(e)}")
            raise
    
    def get_profile(self, profile_id: int, user_id: Optional[int] = None) -> Optional[PersonalityProfile]:
        """Get a personality profile by ID."""
        try:
            query = PersonalityProfile.query.filter_by(id=profile_id)
            
            # If user_id is provided, check ownership or public access
            if user_id is not None:
                query = query.filter(
                    (PersonalityProfile.user_id == user_id) | 
                    (PersonalityProfile.is_public == True)
                )
            
            profile = query.first()
            
            if profile and profile.user_id != user_id:
                # Increment usage count for public profiles
                profile.increment_usage()
                db.session.commit()
            
            return profile
            
        except Exception as e:
            logger.error(f"Error getting personality profile {profile_id}: {str(e)}")
            return None
    
    def get_user_profiles(self, user_id: int, executive_type: Optional[str] = None) -> List[PersonalityProfile]:
        """Get all personality profiles for a user."""
        try:
            query = PersonalityProfile.query.filter_by(
                user_id=user_id,
                is_active=True
            )
            
            if executive_type:
                query = query.filter_by(executive_type=ExecutiveType(executive_type))
            
            return query.order_by(PersonalityProfile.updated_at.desc()).all()
            
        except Exception as e:
            logger.error(f"Error getting user profiles for user {user_id}: {str(e)}")
            return []
    
    def get_default_profile(self, user_id: int, executive_type: str) -> Optional[PersonalityProfile]:
        """Get the default personality profile for a user and executive type."""
        try:
            profile = PersonalityProfile.get_default_for_user(
                user_id, 
                ExecutiveType(executive_type)
            )
            
            # If no default profile exists, create one from template
            if not profile:
                profile = self.create_default_profile(user_id, executive_type)
            
            return profile
            
        except Exception as e:
            logger.error(f"Error getting default profile for user {user_id}, type {executive_type}: {str(e)}")
            return None
    
    def create_default_profile(self, user_id: int, executive_type: str) -> PersonalityProfile:
        """Create a default personality profile for a user."""
        try:
            template = self.default_profiles.get(executive_type)
            if not template:
                raise ValueError(f"No default template for executive type: {executive_type}")
            
            profile_data = template.copy()
            profile_data['name'] = f"Default {executive_type.upper()}"
            profile_data['is_default'] = True
            profile_data['executive_type'] = executive_type
            
            return self.create_profile(user_id, profile_data)
            
        except Exception as e:
            logger.error(f"Error creating default profile: {str(e)}")
            raise
    
    def delete_profile(self, profile_id: int, user_id: int) -> bool:
        """Delete a personality profile."""
        try:
            profile = PersonalityProfile.query.filter_by(
                id=profile_id,
                user_id=user_id
            ).first()
            
            if not profile:
                return False
            
            # Don't allow deletion of default profiles, just deactivate
            if profile.is_default:
                profile.is_active = False
            else:
                # Delete associated shares first
                PersonalityProfileShare.query.filter_by(profile_id=profile_id).delete()
                db.session.delete(profile)
            
            db.session.commit()
            logger.info(f"Deleted personality profile {profile_id}")
            return True
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error deleting personality profile {profile_id}: {str(e)}")
            return False
    
    def clone_profile(self, profile_id: int, user_id: int, new_name: str) -> PersonalityProfile:
        """Clone an existing personality profile."""
        try:
            original = self.get_profile(profile_id, user_id)
            if not original:
                raise ValueError("Profile not found or access denied")
            
            # Create a child profile
            cloned = original.create_child_profile(new_name, user_id)
            cloned.is_default = False  # Cloned profiles are never default
            cloned.is_public = False   # Cloned profiles are private by default
            
            db.session.add(cloned)
            db.session.commit()
            
            logger.info(f"Cloned personality profile {profile_id} to {cloned.id}")
            return cloned
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error cloning personality profile {profile_id}: {str(e)}")
            raise
    
    def share_profile(self, profile_id: int, user_id: int, share_data: Dict[str, Any]) -> PersonalityProfileShare:
        """Share a personality profile with another user or publicly."""
        try:
            profile = PersonalityProfile.query.filter_by(
                id=profile_id,
                user_id=user_id
            ).first()
            
            if not profile:
                raise ValueError("Profile not found or access denied")
            
            # Create the share
            share = PersonalityProfileShare(
                profile_id=profile_id,
                shared_by=user_id,
                shared_with=share_data.get('shared_with'),
                share_type=share_data.get('share_type', 'view'),
                expires_at=share_data.get('expires_at')
            )
            
            db.session.add(share)
            db.session.commit()
            
            logger.info(f"Shared personality profile {profile_id}")
            return share
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error sharing personality profile {profile_id}: {str(e)}")
            raise
    
    def get_public_profiles(self, executive_type: Optional[str] = None) -> List[PersonalityProfile]:
        """Get public personality profiles."""
        try:
            exec_type = ExecutiveType(executive_type) if executive_type else None
            return PersonalityProfile.get_public_profiles(exec_type)
            
        except Exception as e:
            logger.error(f"Error getting public profiles: {str(e)}")
            return []
    
    def get_shared_profiles(self, user_id: int) -> List[PersonalityProfileShare]:
        """Get profiles shared with a user."""
        try:
            return PersonalityProfileShare.query.filter_by(
                shared_with=user_id,
                is_active=True
            ).filter(
                PersonalityProfileShare.expires_at.is_(None) |
                (PersonalityProfileShare.expires_at > datetime.utcnow())
            ).all()
            
        except Exception as e:
            logger.error(f"Error getting shared profiles for user {user_id}: {str(e)}")
            return []
    
    def export_profile(self, profile_id: int, user_id: int) -> Dict[str, Any]:
        """Export a personality profile for sharing or backup."""
        try:
            profile = PersonalityProfile.query.filter_by(
                id=profile_id,
                user_id=user_id
            ).first()
            
            if not profile:
                raise ValueError("Profile not found or access denied")
            
            export_data = profile.to_dict(include_sensitive=True)
            
            # Add export metadata
            export_data['export_metadata'] = {
                'exported_at': datetime.utcnow().isoformat(),
                'exported_by': user_id,
                'export_version': '1.0'
            }
            
            return export_data
            
        except Exception as e:
            logger.error(f"Error exporting personality profile {profile_id}: {str(e)}")
            raise
    
    def import_profile(self, user_id: int, import_data: Dict[str, Any]) -> PersonalityProfile:
        """Import a personality profile from exported data."""
        try:
            # Validate import data
            if not import_data.get('name') or not import_data.get('executive_type'):
                raise ValueError("Invalid import data: missing required fields")
            
            # Create profile from import data
            profile_data = {
                'name': f"Imported: {import_data['name']}",
                'description': import_data.get('description'),
                'executive_type': import_data['executive_type'],
                'industry_specialization': import_data.get('industry_specialization', 'general'),
                'expertise_domains': import_data.get('expertise_domains', []),
                'communication_style': import_data.get('communication_style', 'formal'),
                'tone_preferences': import_data.get('tone_preferences', {}),
                'decision_making_style': import_data.get('decision_making_style'),
                'risk_tolerance': import_data.get('risk_tolerance', 'medium'),
                'experience_level': import_data.get('experience_level', 'senior'),
                'background_context': import_data.get('background_context'),
                'personality_traits': import_data.get('personality_traits', {}),
                'custom_knowledge': import_data.get('custom_knowledge', []),
                'knowledge_sources': import_data.get('knowledge_sources', []),
                'is_default': False,  # Imported profiles are never default
                'is_public': False    # Imported profiles are private by default
            }
            
            return self.create_profile(user_id, profile_data)
            
        except Exception as e:
            logger.error(f"Error importing personality profile: {str(e)}")
            raise
    
    def validate_profile_data(self, profile_data: Dict[str, Any]) -> List[str]:
        """Validate personality profile data and return list of errors."""
        errors = []
        
        # Required fields
        if not profile_data.get('name'):
            errors.append("Profile name is required")
        
        if not profile_data.get('executive_type'):
            errors.append("Executive type is required")
        elif profile_data['executive_type'] not in [e.value for e in ExecutiveType]:
            errors.append("Invalid executive type")
        
        # Validate enums
        if profile_data.get('industry_specialization'):
            if profile_data['industry_specialization'] not in [i.value for i in IndustrySpecialization]:
                errors.append("Invalid industry specialization")
        
        if profile_data.get('communication_style'):
            if profile_data['communication_style'] not in [c.value for c in CommunicationStyle]:
                errors.append("Invalid communication style")
        
        if profile_data.get('experience_level'):
            if profile_data['experience_level'] not in [e.value for e in ExpertiseLevel]:
                errors.append("Invalid experience level")
        
        # Validate tone preferences
        if profile_data.get('tone_preferences'):
            tone_prefs = profile_data['tone_preferences']
            if not isinstance(tone_prefs, dict):
                errors.append("Tone preferences must be a dictionary")
            else:
                for key, value in tone_prefs.items():
                    if not isinstance(value, (int, float)) or not (0.0 <= value <= 1.0):
                        errors.append(f"Tone preference '{key}' must be a number between 0.0 and 1.0")
        
        # Validate personality traits
        if profile_data.get('personality_traits'):
            traits = profile_data['personality_traits']
            if not isinstance(traits, dict):
                errors.append("Personality traits must be a dictionary")
            else:
                for key, value in traits.items():
                    if not isinstance(value, (int, float)) or not (0.0 <= value <= 1.0):
                        errors.append(f"Personality trait '{key}' must be a number between 0.0 and 1.0")
        
        return errors
    
    def _unset_other_defaults(self, user_id: int, executive_type: ExecutiveType):
        """Unset other default profiles for the same user and executive type."""
        PersonalityProfile.query.filter_by(
            user_id=user_id,
            executive_type=executive_type,
            is_default=True
        ).update({'is_default': False})
    
    def _get_default_profiles(self) -> Dict[str, Dict[str, Any]]:
        """Get default personality profile templates."""
        return {
            'ceo': {
                'description': 'Strategic executive focused on high-level business decisions',
                'industry_specialization': 'general',
                'expertise_domains': [
                    'Strategic Planning',
                    'Business Development',
                    'Leadership',
                    'Market Analysis',
                    'Stakeholder Management'
                ],
                'communication_style': 'formal',
                'tone_preferences': {
                    'formality': 0.8,
                    'enthusiasm': 0.6,
                    'directness': 0.7,
                    'technical_depth': 0.5
                },
                'decision_making_style': 'strategic',
                'risk_tolerance': 'medium',
                'experience_level': 'expert',
                'personality_traits': {
                    'analytical': 0.8,
                    'collaborative': 0.7,
                    'innovative': 0.8,
                    'detail_oriented': 0.6,
                    'decisive': 0.9
                },
                'background_context': 'Experienced executive with focus on strategic growth and organizational leadership.'
            },
            'cto': {
                'description': 'Technical executive focused on technology strategy and implementation',
                'industry_specialization': 'technology',
                'expertise_domains': [
                    'Software Architecture',
                    'Technology Strategy',
                    'Engineering Management',
                    'System Design',
                    'Innovation'
                ],
                'communication_style': 'technical',
                'tone_preferences': {
                    'formality': 0.6,
                    'enthusiasm': 0.7,
                    'directness': 0.8,
                    'technical_depth': 0.9
                },
                'decision_making_style': 'analytical',
                'risk_tolerance': 'medium',
                'experience_level': 'expert',
                'personality_traits': {
                    'analytical': 0.9,
                    'collaborative': 0.6,
                    'innovative': 0.9,
                    'detail_oriented': 0.8,
                    'decisive': 0.7
                },
                'background_context': 'Senior technology leader with deep expertise in software development and system architecture.'
            },
            'cfo': {
                'description': 'Financial executive focused on fiscal responsibility and business metrics',
                'industry_specialization': 'finance',
                'expertise_domains': [
                    'Financial Analysis',
                    'Budget Management',
                    'Risk Assessment',
                    'Investment Strategy',
                    'Compliance'
                ],
                'communication_style': 'formal',
                'tone_preferences': {
                    'formality': 0.9,
                    'enthusiasm': 0.4,
                    'directness': 0.8,
                    'technical_depth': 0.7
                },
                'decision_making_style': 'analytical',
                'risk_tolerance': 'low',
                'experience_level': 'expert',
                'personality_traits': {
                    'analytical': 0.9,
                    'collaborative': 0.5,
                    'innovative': 0.6,
                    'detail_oriented': 0.9,
                    'decisive': 0.8
                },
                'background_context': 'Experienced financial executive with expertise in corporate finance and risk management.'
            }
        }