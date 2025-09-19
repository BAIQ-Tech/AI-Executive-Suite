"""
Routes for personality profile management and configuration.
"""

import logging
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, session
from flask_login import login_required, current_user
from services.personality_service import PersonalityService
from models import ExecutiveType, CommunicationStyle, IndustrySpecialization, ExpertiseLevel

logger = logging.getLogger(__name__)

# Create blueprint
personality_bp = Blueprint('personality', __name__, url_prefix='/api/personality')

# Initialize service
personality_service = PersonalityService()


@personality_bp.route('/profiles', methods=['GET'])
@login_required
def get_user_profiles():
    """Get all personality profiles for the current user."""
    try:
        executive_type = request.args.get('executive_type')
        profiles = personality_service.get_user_profiles(
            current_user.id, 
            executive_type
        )
        
        return jsonify({
            'success': True,
            'profiles': [profile.to_dict() for profile in profiles]
        })
        
    except Exception as e:
        logger.error(f"Error getting user profiles: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve profiles'
        }), 500


@personality_bp.route('/profiles', methods=['POST'])
@login_required
def create_profile():
    """Create a new personality profile."""
    try:
        data = request.get_json()
        
        # Validate input data
        errors = personality_service.validate_profile_data(data)
        if errors:
            return jsonify({
                'success': False,
                'errors': errors
            }), 400
        
        profile = personality_service.create_profile(current_user.id, data)
        
        return jsonify({
            'success': True,
            'profile': profile.to_dict(include_sensitive=True)
        }), 201
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
    except Exception as e:
        logger.error(f"Error creating profile: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to create profile'
        }), 500


@personality_bp.route('/profiles/<int:profile_id>', methods=['GET'])
@login_required
def get_profile(profile_id):
    """Get a specific personality profile."""
    try:
        profile = personality_service.get_profile(profile_id, current_user.id)
        
        if not profile:
            return jsonify({
                'success': False,
                'error': 'Profile not found'
            }), 404
        
        # Include sensitive data only for owned profiles
        include_sensitive = profile.user_id == current_user.id
        
        return jsonify({
            'success': True,
            'profile': profile.to_dict(include_sensitive=include_sensitive)
        })
        
    except Exception as e:
        logger.error(f"Error getting profile {profile_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve profile'
        }), 500


@personality_bp.route('/profiles/<int:profile_id>', methods=['PUT'])
@login_required
def update_profile(profile_id):
    """Update a personality profile."""
    try:
        data = request.get_json()
        
        # Validate input data
        errors = personality_service.validate_profile_data(data)
        if errors:
            return jsonify({
                'success': False,
                'errors': errors
            }), 400
        
        profile = personality_service.update_profile(
            profile_id, 
            current_user.id, 
            data
        )
        
        return jsonify({
            'success': True,
            'profile': profile.to_dict(include_sensitive=True)
        })
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
    except Exception as e:
        logger.error(f"Error updating profile {profile_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to update profile'
        }), 500


@personality_bp.route('/profiles/<int:profile_id>', methods=['DELETE'])
@login_required
def delete_profile(profile_id):
    """Delete a personality profile."""
    try:
        success = personality_service.delete_profile(profile_id, current_user.id)
        
        if not success:
            return jsonify({
                'success': False,
                'error': 'Profile not found or cannot be deleted'
            }), 404
        
        return jsonify({
            'success': True,
            'message': 'Profile deleted successfully'
        })
        
    except Exception as e:
        logger.error(f"Error deleting profile {profile_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to delete profile'
        }), 500


@personality_bp.route('/profiles/<int:profile_id>/clone', methods=['POST'])
@login_required
def clone_profile(profile_id):
    """Clone an existing personality profile."""
    try:
        data = request.get_json()
        new_name = data.get('name')
        
        if not new_name:
            return jsonify({
                'success': False,
                'error': 'New profile name is required'
            }), 400
        
        cloned_profile = personality_service.clone_profile(
            profile_id, 
            current_user.id, 
            new_name
        )
        
        return jsonify({
            'success': True,
            'profile': cloned_profile.to_dict(include_sensitive=True)
        }), 201
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
    except Exception as e:
        logger.error(f"Error cloning profile {profile_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to clone profile'
        }), 500


@personality_bp.route('/profiles/<int:profile_id>/share', methods=['POST'])
@login_required
def share_profile(profile_id):
    """Share a personality profile."""
    try:
        data = request.get_json()
        
        # Parse expiration date if provided
        if data.get('expires_at'):
            try:
                data['expires_at'] = datetime.fromisoformat(data['expires_at'])
            except ValueError:
                return jsonify({
                    'success': False,
                    'error': 'Invalid expiration date format'
                }), 400
        
        share = personality_service.share_profile(
            profile_id, 
            current_user.id, 
            data
        )
        
        return jsonify({
            'success': True,
            'share': share.to_dict()
        }), 201
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
    except Exception as e:
        logger.error(f"Error sharing profile {profile_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to share profile'
        }), 500


@personality_bp.route('/profiles/<int:profile_id>/export', methods=['GET'])
@login_required
def export_profile(profile_id):
    """Export a personality profile."""
    try:
        export_data = personality_service.export_profile(
            profile_id, 
            current_user.id
        )
        
        return jsonify({
            'success': True,
            'export_data': export_data
        })
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
    except Exception as e:
        logger.error(f"Error exporting profile {profile_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to export profile'
        }), 500


@personality_bp.route('/profiles/import', methods=['POST'])
@login_required
def import_profile():
    """Import a personality profile."""
    try:
        data = request.get_json()
        import_data = data.get('import_data')
        
        if not import_data:
            return jsonify({
                'success': False,
                'error': 'Import data is required'
            }), 400
        
        profile = personality_service.import_profile(
            current_user.id, 
            import_data
        )
        
        return jsonify({
            'success': True,
            'profile': profile.to_dict(include_sensitive=True)
        }), 201
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
    except Exception as e:
        logger.error(f"Error importing profile: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to import profile'
        }), 500


@personality_bp.route('/profiles/default/<executive_type>', methods=['GET'])
@login_required
def get_default_profile(executive_type):
    """Get the default personality profile for an executive type."""
    try:
        if executive_type not in [e.value for e in ExecutiveType]:
            return jsonify({
                'success': False,
                'error': 'Invalid executive type'
            }), 400
        
        profile = personality_service.get_default_profile(
            current_user.id, 
            executive_type
        )
        
        if not profile:
            return jsonify({
                'success': False,
                'error': 'Default profile not found'
            }), 404
        
        return jsonify({
            'success': True,
            'profile': profile.to_dict(include_sensitive=True)
        })
        
    except Exception as e:
        logger.error(f"Error getting default profile for {executive_type}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve default profile'
        }), 500


@personality_bp.route('/profiles/public', methods=['GET'])
@login_required
def get_public_profiles():
    """Get public personality profiles."""
    try:
        executive_type = request.args.get('executive_type')
        profiles = personality_service.get_public_profiles(executive_type)
        
        return jsonify({
            'success': True,
            'profiles': [profile.to_dict() for profile in profiles]
        })
        
    except Exception as e:
        logger.error(f"Error getting public profiles: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve public profiles'
        }), 500


@personality_bp.route('/profiles/shared', methods=['GET'])
@login_required
def get_shared_profiles():
    """Get profiles shared with the current user."""
    try:
        shares = personality_service.get_shared_profiles(current_user.id)
        
        return jsonify({
            'success': True,
            'shares': [share.to_dict() for share in shares]
        })
        
    except Exception as e:
        logger.error(f"Error getting shared profiles: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve shared profiles'
        }), 500


@personality_bp.route('/config/options', methods=['GET'])
@login_required
def get_configuration_options():
    """Get available configuration options for personality profiles."""
    try:
        return jsonify({
            'success': True,
            'options': {
                'executive_types': [e.value for e in ExecutiveType],
                'communication_styles': [c.value for c in CommunicationStyle],
                'industry_specializations': [i.value for i in IndustrySpecialization],
                'experience_levels': [e.value for e in ExpertiseLevel],
                'risk_tolerance_levels': ['low', 'medium', 'high'],
                'decision_making_styles': [
                    'analytical', 'intuitive', 'collaborative', 
                    'directive', 'consultative', 'consensus'
                ],
                'default_tone_preferences': {
                    'formality': 0.7,
                    'enthusiasm': 0.5,
                    'directness': 0.6,
                    'technical_depth': 0.7
                },
                'default_personality_traits': {
                    'analytical': 0.8,
                    'collaborative': 0.6,
                    'innovative': 0.7,
                    'detail_oriented': 0.8,
                    'decisive': 0.7
                },
                'common_expertise_domains': {
                    'ceo': [
                        'Strategic Planning', 'Business Development', 'Leadership',
                        'Market Analysis', 'Stakeholder Management', 'Corporate Governance',
                        'Mergers & Acquisitions', 'Organizational Development'
                    ],
                    'cto': [
                        'Software Architecture', 'Technology Strategy', 'Engineering Management',
                        'System Design', 'Innovation', 'DevOps', 'Cloud Computing',
                        'Cybersecurity', 'Data Architecture', 'AI/ML'
                    ],
                    'cfo': [
                        'Financial Analysis', 'Budget Management', 'Risk Assessment',
                        'Investment Strategy', 'Compliance', 'Tax Planning',
                        'Financial Reporting', 'Treasury Management', 'Audit'
                    ]
                }
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting configuration options: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve configuration options'
        }), 500


@personality_bp.route('/profiles/<int:profile_id>/test', methods=['POST'])
@login_required
def test_profile(profile_id):
    """Test a personality profile with a sample scenario."""
    try:
        data = request.get_json()
        test_scenario = data.get('scenario', 'What should be our strategy for the next quarter?')
        
        profile = personality_service.get_profile(profile_id, current_user.id)
        if not profile:
            return jsonify({
                'success': False,
                'error': 'Profile not found'
            }), 404
        
        # Generate a test response using the profile configuration
        # This would integrate with the AI service to generate a response
        # using the personality profile settings
        
        test_response = {
            'scenario': test_scenario,
            'profile_used': profile.to_dict(),
            'sample_response': f"Based on the {profile.name} personality profile, here's how I would approach this scenario...",
            'personality_influence': {
                'communication_style': profile.communication_style.value,
                'tone_applied': profile.get_tone_preferences(),
                'expertise_domains': profile.get_expertise_domains(),
                'decision_making_approach': profile.decision_making_style
            }
        }
        
        return jsonify({
            'success': True,
            'test_result': test_response
        })
        
    except Exception as e:
        logger.error(f"Error testing profile {profile_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to test profile'
        }), 500


# Error handlers
@personality_bp.errorhandler(400)
def bad_request(error):
    return jsonify({
        'success': False,
        'error': 'Bad request'
    }), 400


@personality_bp.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 'Resource not found'
    }), 404


@personality_bp.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'error': 'Internal server error'
    }), 500