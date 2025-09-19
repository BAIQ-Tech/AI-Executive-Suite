"""
Routes for expertise domain configuration and validation.
"""

import logging
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from services.expertise_service import ExpertiseService

logger = logging.getLogger(__name__)

# Create blueprint
expertise_bp = Blueprint('expertise', __name__, url_prefix='/api/expertise')

# Initialize service
expertise_service = ExpertiseService()


@expertise_bp.route('/domains', methods=['GET'])
@login_required
def get_available_domains():
    """Get available expertise domains."""
    try:
        executive_type = request.args.get('executive_type')
        industry = request.args.get('industry')
        
        domains = expertise_service.get_available_domains(executive_type, industry)
        
        return jsonify({
            'success': True,
            'domains': domains
        })
        
    except Exception as e:
        logger.error(f"Error getting available domains: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve available domains'
        }), 500


@expertise_bp.route('/domains/validate', methods=['POST'])
@login_required
def validate_domains():
    """Validate expertise domains for a profile."""
    try:
        data = request.get_json()
        
        domains = data.get('domains', [])
        executive_type = data.get('executive_type', '')
        industry = data.get('industry')
        
        if not domains or not executive_type:
            return jsonify({
                'success': False,
                'error': 'Domains and executive type are required'
            }), 400
        
        validation_result = expertise_service.validate_expertise_domains(
            domains, executive_type, industry
        )
        
        return jsonify({
            'success': True,
            'validation': validation_result
        })
        
    except Exception as e:
        logger.error(f"Error validating domains: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to validate domains'
        }), 500


@expertise_bp.route('/domains/suggest', methods=['POST'])
@login_required
def suggest_domains():
    """Suggest expertise domains based on profile characteristics."""
    try:
        data = request.get_json()
        
        executive_type = data.get('executive_type', '')
        industry = data.get('industry', 'general')
        experience_level = data.get('experience_level', 'intermediate')
        current_domains = data.get('current_domains', [])
        
        if not executive_type:
            return jsonify({
                'success': False,
                'error': 'Executive type is required'
            }), 400
        
        suggestions = expertise_service.suggest_domains_for_profile(
            executive_type, industry, experience_level, current_domains
        )
        
        return jsonify({
            'success': True,
            'suggestions': suggestions
        })
        
    except Exception as e:
        logger.error(f"Error suggesting domains: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to suggest domains'
        }), 500


@expertise_bp.route('/knowledge-base', methods=['POST'])
@login_required
def create_knowledge_base():
    """Create a custom knowledge base entry."""
    try:
        data = request.get_json()
        
        result = expertise_service.create_custom_knowledge_base(
            current_user.id, data
        )
        
        if result['success']:
            return jsonify({
                'success': True,
                'knowledge_entry': result['knowledge_entry']
            }), 201
        else:
            return jsonify({
                'success': False,
                'errors': result['errors']
            }), 400
        
    except Exception as e:
        logger.error(f"Error creating knowledge base: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to create knowledge base entry'
        }), 500


@expertise_bp.route('/knowledge-sources/validate', methods=['POST'])
@login_required
def validate_knowledge_sources():
    """Validate knowledge sources for credibility."""
    try:
        data = request.get_json()
        sources = data.get('sources', [])
        
        if not sources:
            return jsonify({
                'success': False,
                'error': 'Sources are required'
            }), 400
        
        validation_result = expertise_service.validate_knowledge_sources(sources)
        
        return jsonify({
            'success': True,
            'validation': validation_result
        })
        
    except Exception as e:
        logger.error(f"Error validating knowledge sources: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to validate knowledge sources'
        }), 500


@expertise_bp.route('/level/assess', methods=['POST'])
@login_required
def assess_expertise_level():
    """Assess and recommend expertise level."""
    try:
        data = request.get_json()
        
        domains = data.get('domains', [])
        experience_years = data.get('experience_years', 0)
        industry = data.get('industry', 'general')
        achievements = data.get('achievements', [])
        
        assessment = expertise_service.assess_expertise_level(
            domains, experience_years, industry, achievements
        )
        
        return jsonify({
            'success': True,
            'assessment': assessment
        })
        
    except Exception as e:
        logger.error(f"Error assessing expertise level: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to assess expertise level'
        }), 500


@expertise_bp.route('/testing/scenarios', methods=['POST'])
@login_required
def get_testing_scenarios():
    """Get testing scenarios for expertise validation."""
    try:
        data = request.get_json()
        
        domains = data.get('domains', [])
        executive_type = data.get('executive_type', '')
        
        if not domains or not executive_type:
            return jsonify({
                'success': False,
                'error': 'Domains and executive type are required'
            }), 400
        
        scenarios = expertise_service.get_expertise_testing_scenarios(
            domains, executive_type
        )
        
        return jsonify({
            'success': True,
            'scenarios': scenarios
        })
        
    except Exception as e:
        logger.error(f"Error getting testing scenarios: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to generate testing scenarios'
        }), 500


@expertise_bp.route('/config/skill-levels', methods=['GET'])
@login_required
def get_skill_level_definitions():
    """Get skill level definitions and requirements."""
    try:
        return jsonify({
            'success': True,
            'skill_levels': expertise_service.skill_levels
        })
        
    except Exception as e:
        logger.error(f"Error getting skill level definitions: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve skill level definitions'
        }), 500


@expertise_bp.route('/config/categories', methods=['GET'])
@login_required
def get_domain_categories():
    """Get domain categories by executive type."""
    try:
        return jsonify({
            'success': True,
            'categories': expertise_service.domain_categories
        })
        
    except Exception as e:
        logger.error(f"Error getting domain categories: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve domain categories'
        }), 500


@expertise_bp.route('/config/industry-domains', methods=['GET'])
@login_required
def get_industry_domains():
    """Get industry-specific domains."""
    try:
        return jsonify({
            'success': True,
            'industry_domains': expertise_service.industry_domains
        })
        
    except Exception as e:
        logger.error(f"Error getting industry domains: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve industry domains'
        }), 500


# Error handlers
@expertise_bp.errorhandler(400)
def bad_request(error):
    return jsonify({
        'success': False,
        'error': 'Bad request'
    }), 400


@expertise_bp.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 'Resource not found'
    }), 404


@expertise_bp.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'error': 'Internal server error'
    }), 500