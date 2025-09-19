"""
Collaboration Routes

Flask routes for team collaboration features in the AI Executive Suite.
"""

import logging
from flask import Blueprint, request, jsonify, render_template
from flask_login import login_required, current_user
from typing import List, Dict, Any

from models import (
    db, User, Decision, Comment, CollaborationSession, CollaborationParticipant,
    CollaborationRole, Notification, NotificationType, AuditLog, AuditEventType
)
from services.collaboration import CollaborationService

# Create blueprint
collaboration_bp = Blueprint('collaboration', __name__, url_prefix='/api/collaboration')

# Initialize service
collaboration_service = CollaborationService()

logger = logging.getLogger(__name__)


@collaboration_bp.route('/invite', methods=['POST'])
@login_required
def invite_collaborators():
    """
    Invite users to collaborate on a decision
    
    Expected JSON payload:
    {
        "decision_id": int,
        "user_ids": [int],
        "role": "viewer|commenter|editor",
        "title": "optional session title",
        "description": "optional description"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        decision_id = data.get('decision_id')
        user_ids = data.get('user_ids', [])
        role_str = data.get('role', 'commenter')
        title = data.get('title')
        description = data.get('description')
        
        # Validate required fields
        if not decision_id:
            return jsonify({'error': 'decision_id is required'}), 400
        
        if not user_ids:
            return jsonify({'error': 'user_ids is required'}), 400
        
        # Validate role
        try:
            role = CollaborationRole(role_str)
        except ValueError:
            return jsonify({'error': f'Invalid role: {role_str}'}), 400
        
        # Check if user owns the decision or has permission to invite
        decision = Decision.query.get(decision_id)
        if not decision:
            return jsonify({'error': 'Decision not found'}), 404
        
        if decision.user_id != current_user.id and current_user not in decision.collaborators:
            return jsonify({'error': 'Permission denied'}), 403
        
        # Invite collaborators
        session = collaboration_service.invite_collaborators(
            decision_id=decision_id,
            user_ids=user_ids,
            role=role,
            inviter_id=current_user.id,
            title=title,
            description=description
        )
        
        return jsonify({
            'success': True,
            'session': session.to_dict(),
            'message': f'Successfully invited {len(user_ids)} collaborators'
        })
        
    except Exception as e:
        logger.error(f"Error inviting collaborators: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@collaboration_bp.route('/comment', methods=['POST'])
@login_required
def add_comment():
    """
    Add a comment to a decision
    
    Expected JSON payload:
    {
        "decision_id": int,
        "content": "comment content",
        "parent_id": int (optional, for replies),
        "mentions": [int] (optional, user IDs mentioned)
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        decision_id = data.get('decision_id')
        content = data.get('content', '').strip()
        parent_id = data.get('parent_id')
        mentions = data.get('mentions', [])
        
        # Validate required fields
        if not decision_id:
            return jsonify({'error': 'decision_id is required'}), 400
        
        if not content:
            return jsonify({'error': 'content is required'}), 400
        
        # Check if user has permission to comment
        decision = Decision.query.get(decision_id)
        if not decision:
            return jsonify({'error': 'Decision not found'}), 404
        
        # Check if user is owner, collaborator, or has access through collaboration session
        has_permission = (
            decision.user_id == current_user.id or
            current_user in decision.collaborators
        )
        
        if not has_permission:
            # Check collaboration session
            session = collaboration_service.get_collaboration_session(decision_id)
            if session:
                participant = CollaborationParticipant.query.filter_by(
                    session_id=session.id,
                    user_id=current_user.id,
                    is_active=True
                ).first()
                has_permission = participant is not None
        
        if not has_permission:
            return jsonify({'error': 'Permission denied'}), 403
        
        # Add comment
        comment = collaboration_service.add_comment(
            decision_id=decision_id,
            user_id=current_user.id,
            content=content,
            parent_id=parent_id,
            mentions=mentions
        )
        
        return jsonify({
            'success': True,
            'comment': comment.to_dict(),
            'message': 'Comment added successfully'
        })
        
    except Exception as e:
        logger.error(f"Error adding comment: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@collaboration_bp.route('/comments/<int:decision_id>', methods=['GET'])
@login_required
def get_comments(decision_id: int):
    """
    Get all comments for a decision
    """
    try:
        # Check if user has permission to view comments
        decision = Decision.query.get(decision_id)
        if not decision:
            return jsonify({'error': 'Decision not found'}), 404
        
        # Check permissions
        has_permission = (
            decision.user_id == current_user.id or
            current_user in decision.collaborators
        )
        
        if not has_permission:
            # Check collaboration session
            session = collaboration_service.get_collaboration_session(decision_id)
            if session:
                participant = CollaborationParticipant.query.filter_by(
                    session_id=session.id,
                    user_id=current_user.id,
                    is_active=True
                ).first()
                has_permission = participant is not None
        
        if not has_permission:
            return jsonify({'error': 'Permission denied'}), 403
        
        # Get comments
        comments = collaboration_service.get_decision_comments(decision_id)
        
        # Organize comments into threaded structure
        comment_dict = {}
        top_level_comments = []
        
        for comment in comments:
            comment_data = comment.to_dict()
            comment_dict[comment.id] = comment_data
            
            if comment.parent_id is None:
                comment_data['replies'] = []
                top_level_comments.append(comment_data)
        
        # Add replies to their parents
        for comment in comments:
            if comment.parent_id and comment.parent_id in comment_dict:
                parent = comment_dict[comment.parent_id]
                if 'replies' not in parent:
                    parent['replies'] = []
                parent['replies'].append(comment_dict[comment.id])
        
        return jsonify({
            'success': True,
            'comments': top_level_comments,
            'total_count': len(comments)
        })
        
    except Exception as e:
        logger.error(f"Error fetching comments: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@collaboration_bp.route('/history/<int:decision_id>', methods=['GET'])
@login_required
def get_collaboration_history(decision_id: int):
    """
    Get collaboration history for a decision
    """
    try:
        # Check permissions
        decision = Decision.query.get(decision_id)
        if not decision:
            return jsonify({'error': 'Decision not found'}), 404
        
        has_permission = (
            decision.user_id == current_user.id or
            current_user in decision.collaborators
        )
        
        if not has_permission:
            session = collaboration_service.get_collaboration_session(decision_id)
            if session:
                participant = CollaborationParticipant.query.filter_by(
                    session_id=session.id,
                    user_id=current_user.id,
                    is_active=True
                ).first()
                has_permission = participant is not None
        
        if not has_permission:
            return jsonify({'error': 'Permission denied'}), 403
        
        # Get history
        history = collaboration_service.get_collaboration_history(decision_id)
        
        return jsonify({
            'success': True,
            'history': history
        })
        
    except Exception as e:
        logger.error(f"Error fetching collaboration history: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@collaboration_bp.route('/session/<int:decision_id>', methods=['GET'])
@login_required
def get_collaboration_session(decision_id: int):
    """
    Get collaboration session for a decision
    """
    try:
        # Check permissions
        decision = Decision.query.get(decision_id)
        if not decision:
            return jsonify({'error': 'Decision not found'}), 404
        
        has_permission = (
            decision.user_id == current_user.id or
            current_user in decision.collaborators
        )
        
        if not has_permission:
            return jsonify({'error': 'Permission denied'}), 403
        
        # Get session
        session = collaboration_service.get_collaboration_session(decision_id)
        
        if not session:
            return jsonify({
                'success': True,
                'session': None,
                'message': 'No active collaboration session found'
            })
        
        return jsonify({
            'success': True,
            'session': session.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Error fetching collaboration session: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@collaboration_bp.route('/session/<int:session_id>/permissions', methods=['PUT'])
@login_required
def update_permissions(session_id: int):
    """
    Update collaboration permissions for a user
    
    Expected JSON payload:
    {
        "user_id": int,
        "role": "viewer|commenter|editor"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        user_id = data.get('user_id')
        role_str = data.get('role')
        
        if not user_id or not role_str:
            return jsonify({'error': 'user_id and role are required'}), 400
        
        # Validate role
        try:
            role = CollaborationRole(role_str)
        except ValueError:
            return jsonify({'error': f'Invalid role: {role_str}'}), 400
        
        # Check if current user has permission to update roles
        session = CollaborationSession.query.get(session_id)
        if not session:
            return jsonify({'error': 'Session not found'}), 404
        
        if session.created_by != current_user.id:
            return jsonify({'error': 'Only session creator can update permissions'}), 403
        
        # Update permissions
        success = collaboration_service.update_collaboration_permissions(
            session_id=session_id,
            user_id=user_id,
            new_role=role
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Permissions updated successfully'
            })
        else:
            return jsonify({'error': 'Failed to update permissions'}), 400
        
    except Exception as e:
        logger.error(f"Error updating permissions: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@collaboration_bp.route('/session/<int:session_id>/remove/<int:user_id>', methods=['DELETE'])
@login_required
def remove_collaborator(session_id: int, user_id: int):
    """
    Remove a collaborator from a session
    """
    try:
        # Check if current user has permission to remove collaborators
        session = CollaborationSession.query.get(session_id)
        if not session:
            return jsonify({'error': 'Session not found'}), 404
        
        if session.created_by != current_user.id and user_id != current_user.id:
            return jsonify({'error': 'Permission denied'}), 403
        
        # Remove collaborator
        success = collaboration_service.remove_collaborator(session_id, user_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Collaborator removed successfully'
            })
        else:
            return jsonify({'error': 'Failed to remove collaborator'}), 400
        
    except Exception as e:
        logger.error(f"Error removing collaborator: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@collaboration_bp.route('/notifications', methods=['GET'])
@login_required
def get_notifications():
    """
    Get notifications for the current user
    """
    try:
        # Get query parameters
        status = request.args.get('status', 'unread')  # 'unread', 'read', 'all'
        limit = int(request.args.get('limit', 50))
        
        if status == 'unread':
            notifications = Notification.get_unread_for_user(current_user.id)
        else:
            notifications = Notification.get_recent_for_user(current_user.id, limit)
            if status == 'read':
                notifications = [n for n in notifications if n.status.value == 'read']
        
        return jsonify({
            'success': True,
            'notifications': [n.to_dict() for n in notifications],
            'count': len(notifications)
        })
        
    except Exception as e:
        logger.error(f"Error fetching notifications: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@collaboration_bp.route('/comment/<int:comment_id>/edit', methods=['PUT'])
@login_required
def edit_comment(comment_id: int):
    """
    Edit a comment
    
    Expected JSON payload:
    {
        "content": "updated comment content"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        content = data.get('content', '').strip()
        
        if not content:
            return jsonify({'error': 'content is required'}), 400
        
        # Edit comment
        comment = collaboration_service.edit_comment(
            comment_id=comment_id,
            user_id=current_user.id,
            new_content=content
        )
        
        return jsonify({
            'success': True,
            'comment': comment.to_dict(),
            'message': 'Comment updated successfully'
        })
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 403
    except Exception as e:
        logger.error(f"Error editing comment: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@collaboration_bp.route('/comment/<int:comment_id>/delete', methods=['DELETE'])
@login_required
def delete_comment(comment_id: int):
    """
    Delete a comment
    """
    try:
        # Check if user is a moderator (simplified check)
        is_moderator = False  # Would be implemented based on user roles
        
        success = collaboration_service.delete_comment(
            comment_id=comment_id,
            user_id=current_user.id,
            is_moderator=is_moderator
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Comment deleted successfully'
            })
        else:
            return jsonify({'error': 'Failed to delete comment'}), 400
        
    except Exception as e:
        logger.error(f"Error deleting comment: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@collaboration_bp.route('/comment/<int:comment_id>/pin', methods=['PUT'])
@login_required
def pin_comment(comment_id: int):
    """
    Pin a comment to the top of the discussion
    
    Expected JSON payload:
    {
        "decision_id": int
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        decision_id = data.get('decision_id')
        
        if not decision_id:
            return jsonify({'error': 'decision_id is required'}), 400
        
        success = collaboration_service.pin_comment(
            comment_id=comment_id,
            user_id=current_user.id,
            decision_id=decision_id
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Comment pinned successfully'
            })
        else:
            return jsonify({'error': 'Failed to pin comment'}), 400
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 403
    except Exception as e:
        logger.error(f"Error pinning comment: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@collaboration_bp.route('/comment/<int:comment_id>/thread', methods=['GET'])
@login_required
def get_comment_thread(comment_id: int):
    """
    Get a comment thread (comment and all replies)
    """
    try:
        thread = collaboration_service.get_comment_thread(comment_id)
        
        return jsonify({
            'success': True,
            'thread': [comment.to_dict() for comment in thread]
        })
        
    except Exception as e:
        logger.error(f"Error fetching comment thread: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@collaboration_bp.route('/mentions', methods=['GET'])
@login_required
def get_user_mentions():
    """
    Get comments where the current user was mentioned
    """
    try:
        limit = int(request.args.get('limit', 50))
        
        mentions = collaboration_service.get_user_mentions(
            user_id=current_user.id,
            limit=limit
        )
        
        return jsonify({
            'success': True,
            'mentions': [comment.to_dict() for comment in mentions],
            'count': len(mentions)
        })
        
    except Exception as e:
        logger.error(f"Error fetching mentions: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@collaboration_bp.route('/comment/<int:comment_id>/moderate', methods=['PUT'])
@login_required
def moderate_comment(comment_id: int):
    """
    Moderate a comment (admin/moderator only)
    
    Expected JSON payload:
    {
        "action": "hide|flag|approve",
        "reason": "optional reason"
    }
    """
    try:
        # Check if user is a moderator (simplified check)
        is_moderator = False  # Would be implemented based on user roles
        
        if not is_moderator:
            return jsonify({'error': 'Permission denied - moderator access required'}), 403
        
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        action = data.get('action')
        reason = data.get('reason')
        
        if not action or action not in ['hide', 'flag', 'approve']:
            return jsonify({'error': 'Invalid action'}), 400
        
        success = collaboration_service.moderate_comment(
            comment_id=comment_id,
            moderator_id=current_user.id,
            action=action,
            reason=reason
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Comment {action}d successfully'
            })
        else:
            return jsonify({'error': 'Failed to moderate comment'}), 400
        
    except Exception as e:
        logger.error(f"Error moderating comment: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@collaboration_bp.route('/notifications/<int:notification_id>/read', methods=['PUT'])
@login_required
def mark_notification_read(notification_id: int):
    """
    Mark a notification as read
    """
    try:
        notification = Notification.query.get(notification_id)
        
        if not notification:
            return jsonify({'error': 'Notification not found'}), 404
        
        if notification.user_id != current_user.id:
            return jsonify({'error': 'Permission denied'}), 403
        
        notification.mark_as_read()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Notification marked as read'
        })
        
    except Exception as e:
        logger.error(f"Error marking notification as read: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@collaboration_bp.route('/audit/decision/<int:decision_id>', methods=['GET'])
@login_required
def get_decision_audit_trail(decision_id: int):
    """
    Get audit trail for a specific decision
    """
    try:
        # Check permissions
        decision = Decision.query.get(decision_id)
        if not decision:
            return jsonify({'error': 'Decision not found'}), 404
        
        has_permission = (
            decision.user_id == current_user.id or
            current_user in decision.collaborators
        )
        
        if not has_permission:
            return jsonify({'error': 'Permission denied'}), 403
        
        # Get audit trail
        limit = int(request.args.get('limit', 100))
        audit_logs = AuditLog.get_decision_audit_trail(decision_id, limit)
        
        return jsonify({
            'success': True,
            'audit_trail': [log.to_dict() for log in audit_logs],
            'count': len(audit_logs)
        })
        
    except Exception as e:
        logger.error(f"Error fetching decision audit trail: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@collaboration_bp.route('/audit/user/<int:user_id>', methods=['GET'])
@login_required
def get_user_audit_trail(user_id: int):
    """
    Get audit trail for a specific user (admin only or own activity)
    """
    try:
        # Check permissions - users can only see their own activity unless they're admin
        if user_id != current_user.id:
            # Check if current user is admin (simplified check)
            is_admin = False  # Would be implemented based on user roles
            if not is_admin:
                return jsonify({'error': 'Permission denied'}), 403
        
        # Get audit trail
        limit = int(request.args.get('limit', 100))
        audit_logs = AuditLog.get_user_activity(user_id, limit)
        
        return jsonify({
            'success': True,
            'audit_trail': [log.to_dict() for log in audit_logs],
            'count': len(audit_logs)
        })
        
    except Exception as e:
        logger.error(f"Error fetching user audit trail: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@collaboration_bp.route('/audit/system', methods=['GET'])
@login_required
def get_system_audit_trail():
    """
    Get system-wide audit trail (admin only)
    """
    try:
        # Check if current user is admin
        is_admin = False  # Would be implemented based on user roles
        if not is_admin:
            return jsonify({'error': 'Permission denied - admin access required'}), 403
        
        # Parse date filters
        from datetime import datetime
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        limit = int(request.args.get('limit', 1000))
        
        if start_date:
            start_date = datetime.fromisoformat(start_date)
        if end_date:
            end_date = datetime.fromisoformat(end_date)
        
        # Get audit trail
        audit_logs = AuditLog.get_system_audit_trail(start_date, end_date, limit)
        
        return jsonify({
            'success': True,
            'audit_trail': [log.to_dict() for log in audit_logs],
            'count': len(audit_logs)
        })
        
    except Exception as e:
        logger.error(f"Error fetching system audit trail: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@collaboration_bp.route('/audit/compliance-report', methods=['GET'])
@login_required
def get_compliance_report():
    """
    Generate compliance report for a date range (admin only)
    """
    try:
        # Check if current user is admin
        is_admin = False  # Would be implemented based on user roles
        if not is_admin:
            return jsonify({'error': 'Permission denied - admin access required'}), 403
        
        # Parse parameters
        from datetime import datetime, timedelta
        
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        event_types_str = request.args.get('event_types')
        
        if not start_date_str or not end_date_str:
            return jsonify({'error': 'start_date and end_date are required'}), 400
        
        start_date = datetime.fromisoformat(start_date_str)
        end_date = datetime.fromisoformat(end_date_str)
        
        event_types = None
        if event_types_str:
            event_types = [AuditEventType(et.strip()) for et in event_types_str.split(',')]
        
        # Generate report
        audit_logs = AuditLog.get_compliance_report(start_date, end_date, event_types)
        
        # Generate summary statistics
        event_counts = {}
        user_activity = {}
        
        for log in audit_logs:
            # Count events by type
            event_type = log.event_type.value
            event_counts[event_type] = event_counts.get(event_type, 0) + 1
            
            # Count activity by user
            if log.user_id:
                user_activity[log.user_id] = user_activity.get(log.user_id, 0) + 1
        
        return jsonify({
            'success': True,
            'report': {
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat()
                },
                'summary': {
                    'total_events': len(audit_logs),
                    'event_counts': event_counts,
                    'active_users': len(user_activity),
                    'most_active_users': sorted(
                        user_activity.items(), 
                        key=lambda x: x[1], 
                        reverse=True
                    )[:10]
                },
                'audit_trail': [log.to_dict() for log in audit_logs]
            }
        })
        
    except Exception as e:
        logger.error(f"Error generating compliance report: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@collaboration_bp.route('/timeline/<int:decision_id>', methods=['GET'])
@login_required
def get_decision_timeline(decision_id: int):
    """
    Get visual timeline for a decision showing all events
    """
    try:
        # Check permissions
        decision = Decision.query.get(decision_id)
        if not decision:
            return jsonify({'error': 'Decision not found'}), 404
        
        has_permission = (
            decision.user_id == current_user.id or
            current_user in decision.collaborators
        )
        
        if not has_permission:
            return jsonify({'error': 'Permission denied'}), 403
        
        # Get all events for this decision
        audit_logs = AuditLog.get_decision_audit_trail(decision_id, 1000)
        
        # Format for timeline visualization
        timeline_events = []
        for log in audit_logs:
            timeline_events.append({
                'id': log.id,
                'type': log.event_type.value,
                'title': log.event_description,
                'timestamp': log.created_at.isoformat(),
                'user': {
                    'id': log.user.id,
                    'name': log.user.name or log.user.username
                } if log.user else None,
                'metadata': log.get_metadata(),
                'icon': self._get_event_icon(log.event_type),
                'color': self._get_event_color(log.event_type)
            })
        
        return jsonify({
            'success': True,
            'timeline': timeline_events,
            'decision': {
                'id': decision.id,
                'title': decision.title,
                'created_at': decision.created_at.isoformat(),
                'status': decision.status.value
            }
        })
        
    except Exception as e:
        logger.error(f"Error fetching decision timeline: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


def _get_event_icon(event_type: AuditEventType) -> str:
    """Get icon for event type"""
    icon_map = {
        AuditEventType.DECISION_CREATED: '📝',
        AuditEventType.DECISION_UPDATED: '✏️',
        AuditEventType.DECISION_STATUS_CHANGED: '🔄',
        AuditEventType.COLLABORATION_STARTED: '👥',
        AuditEventType.USER_INVITED: '📧',
        AuditEventType.USER_JOINED: '👋',
        AuditEventType.COMMENT_ADDED: '💬',
        AuditEventType.COMMENT_EDITED: '✏️',
        AuditEventType.COMMENT_DELETED: '🗑️',
        AuditEventType.COMMENT_PINNED: '📌',
        AuditEventType.DOCUMENT_UPLOADED: '📄',
    }
    return icon_map.get(event_type, '📋')


def _get_event_color(event_type: AuditEventType) -> str:
    """Get color for event type"""
    color_map = {
        AuditEventType.DECISION_CREATED: '#4CAF50',
        AuditEventType.DECISION_UPDATED: '#2196F3',
        AuditEventType.DECISION_STATUS_CHANGED: '#FF9800',
        AuditEventType.COLLABORATION_STARTED: '#9C27B0',
        AuditEventType.USER_INVITED: '#00BCD4',
        AuditEventType.USER_JOINED: '#4CAF50',
        AuditEventType.COMMENT_ADDED: '#2196F3',
        AuditEventType.COMMENT_EDITED: '#FF9800',
        AuditEventType.COMMENT_DELETED: '#F44336',
        AuditEventType.COMMENT_PINNED: '#FF5722',
        AuditEventType.DOCUMENT_UPLOADED: '#795548',
    }
    return color_map.get(event_type, '#607D8B')


# Error handlers
@collaboration_bp.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404


@collaboration_bp.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500