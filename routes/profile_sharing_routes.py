"""
Routes for personality profile sharing and marketplace functionality.
"""

import logging
from datetime import datetime
from flask import Blueprint, request, jsonify, redirect, url_for
from flask_login import login_required, current_user
from services.profile_sharing_service import ProfileSharingService

logger = logging.getLogger(__name__)

# Create blueprint
profile_sharing_bp = Blueprint('profile_sharing', __name__, url_prefix='/api/profile-sharing')

# Initialize service
sharing_service = ProfileSharingService()


@profile_sharing_bp.route('/share', methods=['POST'])
@login_required
def create_share():
    """Create a shareable link for a personality profile."""
    try:
        data = request.get_json()
        
        profile_id = data.get('profile_id')
        if not profile_id:
            return jsonify({
                'success': False,
                'error': 'Profile ID is required'
            }), 400
        
        result = sharing_service.create_share_link(
            profile_id, 
            current_user.id, 
            data
        )
        
        if result['success']:
            return jsonify(result), 201
        else:
            return jsonify(result), 400
        
    except Exception as e:
        logger.error(f"Error creating share: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to create share link'
        }), 500


@profile_sharing_bp.route('/shared/<int:share_id>', methods=['GET'])
def access_shared_profile(share_id):
    """Access a shared personality profile."""
    try:
        user_id = current_user.id if current_user.is_authenticated else None
        
        result = sharing_service.access_shared_profile(share_id, user_id)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 404 if 'not found' in result['error'].lower() else 403
        
    except Exception as e:
        logger.error(f"Error accessing shared profile: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to access shared profile'
        }), 500


@profile_sharing_bp.route('/shared/<int:share_id>/copy', methods=['POST'])
@login_required
def copy_shared_profile(share_id):
    """Copy a shared profile to user's collection."""
    try:
        data = request.get_json()
        new_name = data.get('name')
        
        if not new_name:
            return jsonify({
                'success': False,
                'error': 'New profile name is required'
            }), 400
        
        result = sharing_service.copy_shared_profile(
            share_id, 
            current_user.id, 
            new_name
        )
        
        if result['success']:
            return jsonify(result), 201
        else:
            return jsonify(result), 400
        
    except Exception as e:
        logger.error(f"Error copying shared profile: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to copy shared profile'
        }), 500


@profile_sharing_bp.route('/my-shares', methods=['GET'])
@login_required
def get_my_shares():
    """Get all shares created by the current user."""
    try:
        result = sharing_service.get_user_shares(current_user.id)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 500
        
    except Exception as e:
        logger.error(f"Error getting user shares: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve shares'
        }), 500


@profile_sharing_bp.route('/shared-with-me', methods=['GET'])
@login_required
def get_shared_with_me():
    """Get all profiles shared with the current user."""
    try:
        result = sharing_service.get_shared_with_user(current_user.id)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 500
        
    except Exception as e:
        logger.error(f"Error getting shared profiles: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve shared profiles'
        }), 500


@profile_sharing_bp.route('/share/<int:share_id>/revoke', methods=['DELETE'])
@login_required
def revoke_share(share_id):
    """Revoke a profile share."""
    try:
        result = sharing_service.revoke_share(share_id, current_user.id)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 404 if 'not found' in result['error'].lower() else 403
        
    except Exception as e:
        logger.error(f"Error revoking share: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to revoke share'
        }), 500


@profile_sharing_bp.route('/marketplace', methods=['GET'])
def get_marketplace_profiles():
    """Get public profiles for the marketplace."""
    try:
        filters = {
            'executive_type': request.args.get('executive_type'),
            'industry_specialization': request.args.get('industry'),
            'experience_level': request.args.get('experience_level')
        }
        
        # Remove None values
        filters = {k: v for k, v in filters.items() if v}
        
        result = sharing_service.get_marketplace_profiles(filters)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 500
        
    except Exception as e:
        logger.error(f"Error getting marketplace profiles: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve marketplace profiles'
        }), 500


@profile_sharing_bp.route('/marketplace/submit', methods=['POST'])
@login_required
def submit_to_marketplace():
    """Submit a profile to the public marketplace."""
    try:
        data = request.get_json()
        
        profile_id = data.get('profile_id')
        if not profile_id:
            return jsonify({
                'success': False,
                'error': 'Profile ID is required'
            }), 400
        
        result = sharing_service.submit_to_marketplace(
            profile_id, 
            current_user.id, 
            data
        )
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
        
    except Exception as e:
        logger.error(f"Error submitting to marketplace: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to submit profile to marketplace'
        }), 500


@profile_sharing_bp.route('/marketplace/<int:profile_id>/rate', methods=['POST'])
@login_required
def rate_marketplace_profile(profile_id):
    """Rate a marketplace profile."""
    try:
        data = request.get_json()
        
        result = sharing_service.rate_marketplace_profile(
            profile_id, 
            current_user.id, 
            data
        )
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
        
    except Exception as e:
        logger.error(f"Error rating profile: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to submit rating'
        }), 500


@profile_sharing_bp.route('/profiles/<int:profile_id>/versions', methods=['GET'])
@login_required
def get_profile_versions(profile_id):
    """Get version history of a profile."""
    try:
        result = sharing_service.get_profile_versions(profile_id, current_user.id)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 404 if 'not found' in result['error'].lower() else 403
        
    except Exception as e:
        logger.error(f"Error getting profile versions: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve profile versions'
        }), 500


@profile_sharing_bp.route('/profiles/<int:profile_id>/versions', methods=['POST'])
@login_required
def create_profile_version(profile_id):
    """Create a new version of a profile."""
    try:
        data = request.get_json()
        
        result = sharing_service.create_profile_version(
            profile_id, 
            current_user.id, 
            data
        )
        
        if result['success']:
            return jsonify(result), 201
        else:
            return jsonify(result), 400
        
    except Exception as e:
        logger.error(f"Error creating profile version: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to create profile version'
        }), 500


@profile_sharing_bp.route('/collaboration/stats', methods=['GET'])
@login_required
def get_collaboration_stats():
    """Get collaboration statistics for the current user."""
    try:
        result = sharing_service.get_collaboration_stats(current_user.id)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 500
        
    except Exception as e:
        logger.error(f"Error getting collaboration stats: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve collaboration statistics'
        }), 500


@profile_sharing_bp.route('/config/share-types', methods=['GET'])
def get_share_types():
    """Get available share types."""
    try:
        return jsonify({
            'success': True,
            'share_types': [
                {
                    'value': 'view',
                    'label': 'View Only',
                    'description': 'Recipients can view the profile but cannot copy or modify it'
                },
                {
                    'value': 'copy',
                    'label': 'View & Copy',
                    'description': 'Recipients can view and copy the profile to their collection'
                },
                {
                    'value': 'collaborate',
                    'label': 'Collaborate',
                    'description': 'Recipients can view, copy, and suggest modifications'
                }
            ]
        })
        
    except Exception as e:
        logger.error(f"Error getting share types: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve share types'
        }), 500


@profile_sharing_bp.route('/config/marketplace-categories', methods=['GET'])
def get_marketplace_categories():
    """Get marketplace categories."""
    try:
        return jsonify({
            'success': True,
            'categories': sharing_service.marketplace_categories
        })
        
    except Exception as e:
        logger.error(f"Error getting marketplace categories: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve marketplace categories'
        }), 500


# Web routes for shared profile pages
@profile_sharing_bp.route('/shared/<int:share_id>/view', methods=['GET'])
def view_shared_profile_page(share_id):
    """Web page for viewing a shared profile."""
    try:
        # This would render a template for viewing shared profiles
        # For now, redirect to API endpoint
        return redirect(url_for('profile_sharing.access_shared_profile', share_id=share_id))
        
    except Exception as e:
        logger.error(f"Error viewing shared profile page: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to load shared profile page'
        }), 500


# Error handlers
@profile_sharing_bp.errorhandler(400)
def bad_request(error):
    return jsonify({
        'success': False,
        'error': 'Bad request'
    }), 400


@profile_sharing_bp.errorhandler(403)
def forbidden(error):
    return jsonify({
        'success': False,
        'error': 'Access forbidden'
    }), 403


@profile_sharing_bp.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 'Resource not found'
    }), 404


@profile_sharing_bp.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'error': 'Internal server error'
    }), 500