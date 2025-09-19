"""
Compliance and Audit Routes

Provides API endpoints for GDPR compliance, SOX audit logging,
compliance reporting, and data privacy controls.
"""

from flask import Blueprint, request, jsonify, current_app, send_file
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from services.compliance import ComplianceService, ComplianceFramework, AuditEventType, DataSubjectRights
from models import db, AuditLog, DataProtectionRecord
import os

compliance_bp = Blueprint('compliance', __name__, url_prefix='/api/compliance')

# Initialize compliance service
compliance_service = ComplianceService()


@compliance_bp.route('/dashboard')
@login_required
def get_compliance_dashboard():
    """Get compliance dashboard overview."""
    try:
        dashboard = compliance_service.generate_compliance_dashboard()
        
        return jsonify({
            'success': True,
            'dashboard': dashboard
        })
        
    except Exception as e:
        current_app.logger.error(f"Compliance dashboard error: {e}")
        return jsonify({'error': 'Failed to get compliance dashboard'}), 500


@compliance_bp.route('/audit/log', methods=['POST'])
@login_required
def log_audit_event():
    """Log an audit event."""
    try:
        data = request.json
        event_type_str = data.get('event_type')
        details = data.get('details', {})
        resource_type = data.get('resource_type')
        resource_id = data.get('resource_id')
        
        if not event_type_str:
            return jsonify({'error': 'Event type is required'}), 400
        
        # Parse event type
        try:
            event_type = AuditEventType(event_type_str)
        except ValueError:
            return jsonify({'error': 'Invalid event type'}), 400
        
        # Log the event
        success = compliance_service.log_audit_event(
            event_type=event_type,
            user_id=current_user.id,
            details=details,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent'),
            resource_type=resource_type,
            resource_id=resource_id
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Audit event logged successfully'
            })
        else:
            return jsonify({'error': 'Failed to log audit event'}), 500
            
    except Exception as e:
        current_app.logger.error(f"Audit logging error: {e}")
        return jsonify({'error': 'Failed to log audit event'}), 500


@compliance_bp.route('/audit/events')
@login_required
def get_audit_events():
    """Get audit events with filtering."""
    try:
        # Query parameters
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 50, type=int), 100)
        event_type = request.args.get('event_type')
        user_id = request.args.get('user_id', type=int)
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Build query
        query = AuditLog.query
        
        if event_type:
            query = query.filter_by(event_type=event_type)
        
        if user_id:
            query = query.filter_by(user_id=user_id)
        
        if start_date:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            query = query.filter(AuditLog.timestamp >= start_dt)
        
        if end_date:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            query = query.filter(AuditLog.timestamp <= end_dt)
        
        # Paginate results
        events = query.order_by(AuditLog.timestamp.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'success': True,
            'events': [event.to_dict() for event in events.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': events.total,
                'pages': events.pages,
                'has_next': events.has_next,
                'has_prev': events.has_prev
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Audit events error: {e}")
        return jsonify({'error': 'Failed to get audit events'}), 500


@compliance_bp.route('/gdpr/data-export')
@login_required
def gdpr_data_export():
    """Generate GDPR data export for current user."""
    try:
        export_data = compliance_service.generate_gdpr_data_export(current_user.id)
        
        return jsonify({
            'success': True,
            'data': export_data,
            'message': 'GDPR data export generated successfully'
        })
        
    except Exception as e:
        current_app.logger.error(f"GDPR data export error: {e}")
        return jsonify({'error': 'Failed to generate GDPR data export'}), 500


@compliance_bp.route('/gdpr/data-subject-request', methods=['POST'])
@login_required
def process_data_subject_request():
    """Process GDPR data subject rights request."""
    try:
        data = request.json
        request_type_str = data.get('request_type')
        details = data.get('details', {})
        
        if not request_type_str:
            return jsonify({'error': 'Request type is required'}), 400
        
        # Parse request type
        try:
            request_type = DataSubjectRights(request_type_str)
        except ValueError:
            return jsonify({'error': 'Invalid request type'}), 400
        
        # Process the request
        result = compliance_service.process_data_subject_request(
            request_type=request_type,
            user_id=current_user.id,
            details=details
        )
        
        return jsonify({
            'success': result.get('success', False),
            'result': result
        })
        
    except Exception as e:
        current_app.logger.error(f"Data subject request error: {e}")
        return jsonify({'error': 'Failed to process data subject request'}), 500


@compliance_bp.route('/sox/report')
@login_required
def generate_sox_report():
    """Generate SOX compliance report."""
    try:
        # Get date range from query parameters
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        
        if not start_date_str or not end_date_str:
            # Default to last 30 days
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=30)
        else:
            start_date = datetime.fromisoformat(start_date_str.replace('Z', '+00:00'))
            end_date = datetime.fromisoformat(end_date_str.replace('Z', '+00:00'))
        
        # Generate report
        report = compliance_service.generate_sox_compliance_report(start_date, end_date)
        
        return jsonify({
            'success': True,
            'report': report
        })
        
    except Exception as e:
        current_app.logger.error(f"SOX report error: {e}")
        return jsonify({'error': 'Failed to generate SOX report'}), 500


@compliance_bp.route('/export', methods=['POST'])
@login_required
def export_compliance_data():
    """Export compliance data in specified format."""
    try:
        data = request.json
        framework_str = data.get('framework')
        start_date_str = data.get('start_date')
        end_date_str = data.get('end_date')
        format_type = data.get('format', 'json')
        
        if not framework_str:
            return jsonify({'error': 'Framework is required'}), 400
        
        # Parse framework
        try:
            framework = ComplianceFramework(framework_str)
        except ValueError:
            return jsonify({'error': 'Invalid framework'}), 400
        
        # Parse dates
        if not start_date_str or not end_date_str:
            return jsonify({'error': 'Start date and end date are required'}), 400
        
        start_date = datetime.fromisoformat(start_date_str.replace('Z', '+00:00'))
        end_date = datetime.fromisoformat(end_date_str.replace('Z', '+00:00'))
        
        # Export data
        filepath = compliance_service.export_compliance_data(
            framework=framework,
            start_date=start_date,
            end_date=end_date,
            format=format_type
        )
        
        # Return file for download
        return send_file(
            filepath,
            as_attachment=True,
            download_name=os.path.basename(filepath)
        )
        
    except Exception as e:
        current_app.logger.error(f"Compliance export error: {e}")
        return jsonify({'error': 'Failed to export compliance data'}), 500


@compliance_bp.route('/frameworks')
@login_required
def get_supported_frameworks():
    """Get list of supported compliance frameworks."""
    try:
        frameworks = []
        for framework in ComplianceFramework:
            frameworks.append({
                'value': framework.value,
                'name': framework.name,
                'description': {
                    'gdpr': 'General Data Protection Regulation (EU)',
                    'sox': 'Sarbanes-Oxley Act (US)',
                    'hipaa': 'Health Insurance Portability and Accountability Act (US)',
                    'ccpa': 'California Consumer Privacy Act (US)',
                    'pci_dss': 'Payment Card Industry Data Security Standard'
                }.get(framework.value, framework.name)
            })
        
        return jsonify({
            'success': True,
            'frameworks': frameworks
        })
        
    except Exception as e:
        current_app.logger.error(f"Frameworks error: {e}")
        return jsonify({'error': 'Failed to get frameworks'}), 500


@compliance_bp.route('/data-subject-rights')
@login_required
def get_data_subject_rights():
    """Get list of GDPR data subject rights."""
    try:
        rights = []
        for right in DataSubjectRights:
            rights.append({
                'value': right.value,
                'name': right.name.replace('_', ' ').title(),
                'description': {
                    'right_to_access': 'Request access to personal data',
                    'right_to_rectification': 'Request correction of inaccurate data',
                    'right_to_erasure': 'Request deletion of personal data',
                    'right_to_restrict_processing': 'Request restriction of data processing',
                    'right_to_data_portability': 'Request data in portable format',
                    'right_to_object': 'Object to data processing',
                    'right_to_withdraw_consent': 'Withdraw consent for data processing'
                }.get(right.value, right.name)
            })
        
        return jsonify({
            'success': True,
            'rights': rights
        })
        
    except Exception as e:
        current_app.logger.error(f"Data subject rights error: {e}")
        return jsonify({'error': 'Failed to get data subject rights'}), 500


@compliance_bp.route('/audit-event-types')
@login_required
def get_audit_event_types():
    """Get list of audit event types."""
    try:
        event_types = []
        for event_type in AuditEventType:
            event_types.append({
                'value': event_type.value,
                'name': event_type.name.replace('_', ' ').title(),
                'description': {
                    'data_access': 'User accessed data',
                    'data_modification': 'User modified data',
                    'data_deletion': 'User deleted data',
                    'data_export': 'User exported data',
                    'user_login': 'User logged in',
                    'user_logout': 'User logged out',
                    'permission_change': 'User permissions changed',
                    'system_configuration': 'System configuration changed',
                    'security_event': 'Security-related event',
                    'compliance_action': 'Compliance-related action'
                }.get(event_type.value, event_type.name)
            })
        
        return jsonify({
            'success': True,
            'event_types': event_types
        })
        
    except Exception as e:
        current_app.logger.error(f"Audit event types error: {e}")
        return jsonify({'error': 'Failed to get audit event types'}), 500


@compliance_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def manage_compliance_settings():
    """Get or update compliance settings."""
    if request.method == 'GET':
        try:
            # Get current compliance settings
            settings = {
                'gdpr_enabled': current_app.config.get('GDPR_COMPLIANCE_ENABLED', True),
                'sox_enabled': current_app.config.get('SOX_COMPLIANCE_ENABLED', True),
                'audit_retention_days': current_app.config.get('AUDIT_RETENTION_DAYS', 2555),
                'data_subject_request_response_days': 30,
                'breach_notification_hours': 72,
                'consent_management': {
                    'enabled': True,
                    'granular_consent': True,
                    'consent_withdrawal': True
                },
                'data_minimization': {
                    'enabled': True,
                    'automatic_classification': True,
                    'retention_enforcement': True
                },
                'privacy_by_design': {
                    'enabled': True,
                    'default_encryption': True,
                    'access_controls': True
                }
            }
            
            return jsonify({
                'success': True,
                'settings': settings
            })
            
        except Exception as e:
            current_app.logger.error(f"Get compliance settings error: {e}")
            return jsonify({'error': 'Failed to get compliance settings'}), 500
    
    else:  # POST
        try:
            settings = request.json
            
            # Log settings change
            compliance_service.log_audit_event(
                AuditEventType.SYSTEM_CONFIGURATION,
                current_user.id,
                {
                    'action': 'compliance_settings_updated',
                    'changes': settings
                },
                request.remote_addr,
                request.headers.get('User-Agent')
            )
            
            # In a real implementation, these would be saved to database or config
            return jsonify({
                'success': True,
                'message': 'Compliance settings updated successfully'
            })
            
        except Exception as e:
            current_app.logger.error(f"Update compliance settings error: {e}")
            return jsonify({'error': 'Failed to update compliance settings'}), 500


@compliance_bp.route('/privacy-policy')
def get_privacy_policy():
    """Get privacy policy information."""
    try:
        privacy_policy = {
            'last_updated': '2024-01-01',
            'version': '1.0',
            'sections': [
                {
                    'title': 'Data Collection',
                    'content': 'We collect personal data necessary to provide our AI Executive Suite services.'
                },
                {
                    'title': 'Data Usage',
                    'content': 'Personal data is used to provide personalized AI recommendations and maintain your account.'
                },
                {
                    'title': 'Data Sharing',
                    'content': 'We do not sell personal data. Data may be shared with AI service providers for processing.'
                },
                {
                    'title': 'Data Retention',
                    'content': 'Data is retained according to our retention policies and legal requirements.'
                },
                {
                    'title': 'Your Rights',
                    'content': 'You have rights to access, correct, delete, and port your personal data.'
                },
                {
                    'title': 'Contact Information',
                    'content': 'Contact us at privacy@aiexecutivesuite.com for privacy-related inquiries.'
                }
            ]
        }
        
        return jsonify({
            'success': True,
            'privacy_policy': privacy_policy
        })
        
    except Exception as e:
        current_app.logger.error(f"Privacy policy error: {e}")
        return jsonify({'error': 'Failed to get privacy policy'}), 500


@compliance_bp.route('/consent', methods=['GET', 'POST'])
@login_required
def manage_consent():
    """Get or update user consent preferences."""
    if request.method == 'GET':
        try:
            # Get current user consent preferences
            consent_preferences = {
                'marketing_communications': False,
                'analytics_tracking': True,
                'personalization': True,
                'third_party_integrations': True,
                'data_processing_for_ai': True,
                'last_updated': datetime.utcnow().isoformat()
            }
            
            return jsonify({
                'success': True,
                'consent_preferences': consent_preferences
            })
            
        except Exception as e:
            current_app.logger.error(f"Get consent error: {e}")
            return jsonify({'error': 'Failed to get consent preferences'}), 500
    
    else:  # POST
        try:
            consent_data = request.json
            
            # Log consent change
            compliance_service.log_audit_event(
                AuditEventType.COMPLIANCE_ACTION,
                current_user.id,
                {
                    'action': 'consent_updated',
                    'consent_changes': consent_data
                },
                request.remote_addr,
                request.headers.get('User-Agent')
            )
            
            # In a real implementation, consent would be saved to database
            return jsonify({
                'success': True,
                'message': 'Consent preferences updated successfully'
            })
            
        except Exception as e:
            current_app.logger.error(f"Update consent error: {e}")
            return jsonify({'error': 'Failed to update consent preferences'}), 500