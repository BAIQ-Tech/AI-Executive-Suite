"""
Collaboration Service

Manages team collaboration on decisions for the AI Executive Suite.
"""

import logging
from typing import List, Dict, Optional, Any
from datetime import datetime
from flask import current_app
from sqlalchemy.exc import IntegrityError

# Import models
from models import (
    db, User, Decision, Comment, CollaborationSession, CollaborationParticipant,
    CollaborationRole, Notification, NotificationType, NotificationStatus,
    AuditLog, AuditEventType
)

logger = logging.getLogger(__name__)


class CollaborationService:
    """Service for managing team collaboration"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
    def invite_collaborators(
        self, 
        decision_id: int, 
        user_ids: List[int],
        role: CollaborationRole = CollaborationRole.COMMENTER,
        inviter_id: int = None,
        title: str = None,
        description: str = None
    ) -> CollaborationSession:
        """
        Invite collaborators to work on a decision
        
        Args:
            decision_id: ID of the decision
            user_ids: List of user IDs to invite
            role: Role for invited users
            inviter_id: ID of user sending invitations
            title: Optional title for the collaboration session
            description: Optional description
            
        Returns:
            CollaborationSession with participant details
        """
        try:
            self.logger.info(f"Inviting {len(user_ids)} collaborators to decision {decision_id}")
            
            # Check if decision exists
            decision = Decision.query.get(decision_id)
            if not decision:
                raise ValueError(f"Decision {decision_id} not found")
            
            # Check if collaboration session already exists for this decision
            existing_session = CollaborationSession.query.filter_by(
                decision_id=decision_id,
                is_active=True
            ).first()
            
            if existing_session:
                session = existing_session
            else:
                # Create new collaboration session
                session = CollaborationSession(
                    decision_id=decision_id,
                    created_by=inviter_id or decision.user_id,
                    title=title or f"Collaboration on: {decision.title}",
                    description=description
                )
                db.session.add(session)
                db.session.flush()  # Get the session ID
            
            # Add participants
            invited_users = []
            for user_id in user_ids:
                # Check if user exists
                user = User.query.get(user_id)
                if not user:
                    self.logger.warning(f"User {user_id} not found, skipping invitation")
                    continue
                
                # Add participant
                participant = session.add_participant(
                    user_id=user_id,
                    role=role,
                    invited_by=inviter_id
                )
                
                if participant:
                    invited_users.append(user)
            
            db.session.commit()
            
            # Send notifications to invited users
            for user in invited_users:
                self._send_notification(
                    user_id=user.id,
                    notification_type=NotificationType.COLLABORATION_INVITED,
                    title="Collaboration Invitation",
                    message=f"You've been invited to collaborate on decision: {decision.title}",
                    decision_id=decision_id,
                    session_id=session.id
                )
            
            # Log audit event
            AuditLog.log_event(
                event_type=AuditEventType.COLLABORATION_STARTED,
                event_description=f"Started collaboration session for decision: {decision.title}",
                user_id=inviter_id,
                decision_id=decision_id,
                session_id=session.id,
                metadata={
                    'invited_users': [user.id for user in invited_users],
                    'session_title': session.title
                }
            )
            
            # Log user invitations
            for user in invited_users:
                AuditLog.log_event(
                    event_type=AuditEventType.USER_INVITED,
                    event_description=f"User {user.username} invited to collaborate on decision: {decision.title}",
                    user_id=inviter_id,
                    decision_id=decision_id,
                    session_id=session.id,
                    metadata={
                        'invited_user_id': user.id,
                        'invited_user_name': user.username,
                        'role': role.value
                    }
                )
            
            self.logger.info(f"Successfully invited {len(invited_users)} users to collaboration session {session.id}")
            return session
            
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Error inviting collaborators: {str(e)}")
            raise
    
    def add_comment(
        self, 
        decision_id: int, 
        user_id: int,
        content: str,
        parent_id: int = None,
        mentions: List[int] = None
    ) -> Comment:
        """
        Add a comment to a decision
        
        Args:
            decision_id: ID of the decision
            user_id: ID of the user adding the comment
            content: Comment content
            parent_id: ID of parent comment for replies
            mentions: List of user IDs mentioned in the comment
            
        Returns:
            Comment object
        """
        try:
            self.logger.info(f"Adding comment to decision {decision_id} by user {user_id}")
            
            # Check if decision exists
            decision = Decision.query.get(decision_id)
            if not decision:
                raise ValueError(f"Decision {decision_id} not found")
            
            # Check if user exists
            user = User.query.get(user_id)
            if not user:
                raise ValueError(f"User {user_id} not found")
            
            # Create comment
            comment = Comment(
                decision_id=decision_id,
                user_id=user_id,
                content=content,
                parent_id=parent_id
            )
            
            db.session.add(comment)
            db.session.commit()
            
            # Send notifications for mentions
            if mentions:
                for mentioned_user_id in mentions:
                    mentioned_user = User.query.get(mentioned_user_id)
                    if mentioned_user:
                        self._send_notification(
                            user_id=mentioned_user_id,
                            notification_type=NotificationType.COMMENT_ADDED,
                            title="You were mentioned",
                            message=f"{user.name or user.username} mentioned you in a comment on: {decision.title}",
                            decision_id=decision_id,
                            comment_id=comment.id
                        )
            
            # Notify decision owner and collaborators about new comment
            self._notify_decision_participants(
                decision=decision,
                notification_type=NotificationType.COMMENT_ADDED,
                title="New comment added",
                message=f"{user.name or user.username} added a comment to: {decision.title}",
                exclude_user_id=user_id,
                comment_id=comment.id
            )
            
            # Log audit event
            AuditLog.log_event(
                event_type=AuditEventType.COMMENT_ADDED,
                event_description=f"Comment added to decision: {decision.title}",
                user_id=user_id,
                decision_id=decision_id,
                comment_id=comment.id,
                metadata={
                    'comment_content_preview': content[:100] + ('...' if len(content) > 100 else ''),
                    'parent_comment_id': parent_id,
                    'mentions': mentions
                }
            )
            
            self.logger.info(f"Successfully added comment {comment.id}")
            return comment
            
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Error adding comment: {str(e)}")
            raise
    
    def get_collaboration_history(
        self, 
        decision_id: int
    ) -> List[Dict[str, Any]]:
        """
        Get collaboration history for a decision
        
        Args:
            decision_id: ID of the decision
            
        Returns:
            List of collaboration events
        """
        try:
            self.logger.info(f"Fetching collaboration history for decision {decision_id}")
            
            events = []
            
            # Get comments
            comments = Comment.query.filter_by(
                decision_id=decision_id,
                is_deleted=False
            ).order_by(Comment.created_at).all()
            
            for comment in comments:
                events.append({
                    'id': f"comment_{comment.id}",
                    'decision_id': decision_id,
                    'event_type': 'comment_added',
                    'user_id': comment.user_id,
                    'user_name': comment.user.name or comment.user.username,
                    'description': f"Added a comment: {comment.content[:100]}{'...' if len(comment.content) > 100 else ''}",
                    'metadata': {
                        'comment_id': comment.id,
                        'parent_id': comment.parent_id,
                        'is_reply': comment.parent_id is not None
                    },
                    'timestamp': comment.created_at
                })
            
            # Get collaboration sessions
            sessions = CollaborationSession.query.filter_by(decision_id=decision_id).all()
            
            for session in sessions:
                events.append({
                    'id': f"session_{session.id}",
                    'decision_id': decision_id,
                    'event_type': 'collaboration_started',
                    'user_id': session.created_by,
                    'user_name': session.creator.name or session.creator.username,
                    'description': f"Started collaboration session: {session.title}",
                    'metadata': {
                        'session_id': session.id,
                        'participant_count': len(session.get_active_participants())
                    },
                    'timestamp': session.created_at
                })
                
                # Add participant join events
                for participant in session.participants:
                    if participant.user_id != session.created_by:  # Don't duplicate creator
                        events.append({
                            'id': f"participant_{participant.id}",
                            'decision_id': decision_id,
                            'event_type': 'user_joined',
                            'user_id': participant.user_id,
                            'user_name': participant.user.name or participant.user.username,
                            'description': f"Joined collaboration as {participant.role.value}",
                            'metadata': {
                                'session_id': session.id,
                                'role': participant.role.value,
                                'invited_by': participant.invited_by
                            },
                            'timestamp': participant.joined_at
                        })
            
            # Sort events by timestamp
            events.sort(key=lambda x: x['timestamp'])
            
            return events
            
        except Exception as e:
            self.logger.error(f"Error fetching collaboration history: {str(e)}")
            return []
    
    def get_decision_comments(
        self, 
        decision_id: int,
        include_replies: bool = True
    ) -> List[Comment]:
        """
        Get all comments for a decision
        
        Args:
            decision_id: ID of the decision
            include_replies: Whether to include reply comments
            
        Returns:
            List of comments
        """
        try:
            self.logger.info(f"Fetching comments for decision {decision_id}")
            
            if include_replies:
                comments = Comment.get_by_decision(decision_id)
            else:
                comments = Comment.get_top_level_comments(decision_id)
            
            return comments
            
        except Exception as e:
            self.logger.error(f"Error fetching comments: {str(e)}")
            return []
    
    def update_collaboration_permissions(
        self, 
        session_id: int, 
        user_id: int, 
        new_role: CollaborationRole
    ) -> bool:
        """
        Update collaboration permissions for a user
        
        Args:
            session_id: ID of the collaboration session
            user_id: ID of the user
            new_role: New role for the user
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.logger.info(f"Updating role for user {user_id} in session {session_id}")
            
            participant = CollaborationParticipant.query.filter_by(
                session_id=session_id,
                user_id=user_id
            ).first()
            
            if not participant:
                self.logger.warning(f"Participant not found: user {user_id} in session {session_id}")
                return False
            
            old_role = participant.role
            participant.change_role(new_role)
            db.session.commit()
            
            # Send notification about role change
            self._send_notification(
                user_id=user_id,
                notification_type=NotificationType.STATUS_CHANGED,
                title="Role Updated",
                message=f"Your role has been changed from {old_role.value} to {new_role.value}",
                session_id=session_id
            )
            
            return True
            
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Error updating permissions: {str(e)}")
            return False
    
    def get_collaboration_session(self, decision_id: int) -> Optional[CollaborationSession]:
        """
        Get active collaboration session for a decision
        
        Args:
            decision_id: ID of the decision
            
        Returns:
            CollaborationSession if found, None otherwise
        """
        try:
            return CollaborationSession.query.filter_by(
                decision_id=decision_id,
                is_active=True
            ).first()
        except Exception as e:
            self.logger.error(f"Error fetching collaboration session: {str(e)}")
            return None
    
    def remove_collaborator(self, session_id: int, user_id: int) -> bool:
        """
        Remove a collaborator from a session
        
        Args:
            session_id: ID of the collaboration session
            user_id: ID of the user to remove
            
        Returns:
            True if successful, False otherwise
        """
        try:
            participant = CollaborationParticipant.query.filter_by(
                session_id=session_id,
                user_id=user_id
            ).first()
            
            if participant:
                participant.leave_session()
                db.session.commit()
                return True
            
            return False
            
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Error removing collaborator: {str(e)}")
            return False
    
    def _send_notification(
        self, 
        user_id: int,
        notification_type: NotificationType,
        title: str,
        message: str,
        decision_id: int = None,
        comment_id: int = None,
        session_id: int = None,
        data: Dict[str, Any] = None
    ) -> bool:
        """
        Send notification to a user
        
        Args:
            user_id: ID of the user to notify
            notification_type: Type of notification
            title: Notification title
            message: Notification message
            decision_id: Related decision ID
            comment_id: Related comment ID
            session_id: Related session ID
            data: Additional data
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.logger.info(f"Sending notification to user {user_id}")
            
            notification = Notification(
                user_id=user_id,
                notification_type=notification_type,
                title=title,
                message=message,
                decision_id=decision_id,
                comment_id=comment_id,
                session_id=session_id
            )
            
            if data:
                notification.set_data(data)
            
            db.session.add(notification)
            db.session.commit()
            
            return True
            
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Error sending notification: {str(e)}")
            return False
    
    def edit_comment(
        self,
        comment_id: int,
        user_id: int,
        new_content: str
    ) -> Optional[Comment]:
        """
        Edit a comment
        
        Args:
            comment_id: ID of the comment to edit
            user_id: ID of the user editing the comment
            new_content: New content for the comment
            
        Returns:
            Updated Comment object or None if not found/unauthorized
        """
        try:
            comment = Comment.query.get(comment_id)
            if not comment:
                raise ValueError(f"Comment {comment_id} not found")
            
            # Check if user can edit this comment
            if comment.user_id != user_id:
                raise ValueError("User can only edit their own comments")
            
            # Edit the comment
            comment.edit_content(new_content)
            db.session.commit()
            
            # Log audit event
            AuditLog.log_event(
                event_type=AuditEventType.COMMENT_EDITED,
                event_description=f"Comment edited on decision: {comment.decision.title}",
                user_id=user_id,
                decision_id=comment.decision_id,
                comment_id=comment_id,
                old_values={'content': comment.get_edit_history()[-1]['content'] if comment.get_edit_history() else ''},
                new_values={'content': new_content},
                metadata={'edit_count': len(comment.get_edit_history())}
            )
            
            self.logger.info(f"Comment {comment_id} edited by user {user_id}")
            return comment
            
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Error editing comment: {str(e)}")
            raise
    
    def delete_comment(
        self,
        comment_id: int,
        user_id: int,
        is_moderator: bool = False
    ) -> bool:
        """
        Delete (soft delete) a comment
        
        Args:
            comment_id: ID of the comment to delete
            user_id: ID of the user deleting the comment
            is_moderator: Whether the user is a moderator
            
        Returns:
            True if successful, False otherwise
        """
        try:
            comment = Comment.query.get(comment_id)
            if not comment:
                raise ValueError(f"Comment {comment_id} not found")
            
            # Check permissions
            can_delete = (
                comment.user_id == user_id or  # User can delete their own comments
                is_moderator  # Moderators can delete any comment
            )
            
            if not can_delete:
                raise ValueError("User does not have permission to delete this comment")
            
            # Soft delete the comment
            comment.soft_delete()
            db.session.commit()
            
            # Log audit event
            AuditLog.log_event(
                event_type=AuditEventType.COMMENT_DELETED,
                event_description=f"Comment deleted from decision: {comment.decision.title}",
                user_id=user_id,
                decision_id=comment.decision_id,
                comment_id=comment_id,
                metadata={
                    'deleted_by_moderator': is_moderator,
                    'original_content_preview': comment.content[:100] + ('...' if len(comment.content) > 100 else '')
                }
            )
            
            self.logger.info(f"Comment {comment_id} deleted by user {user_id}")
            return True
            
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Error deleting comment: {str(e)}")
            return False
    
    def pin_comment(
        self,
        comment_id: int,
        user_id: int,
        decision_id: int
    ) -> bool:
        """
        Pin a comment to the top of the discussion
        
        Args:
            comment_id: ID of the comment to pin
            user_id: ID of the user pinning the comment
            decision_id: ID of the decision
            
        Returns:
            True if successful, False otherwise
        """
        try:
            comment = Comment.query.get(comment_id)
            if not comment:
                raise ValueError(f"Comment {comment_id} not found")
            
            decision = Decision.query.get(decision_id)
            if not decision:
                raise ValueError(f"Decision {decision_id} not found")
            
            # Check if user has permission to pin comments (decision owner or moderator)
            if decision.user_id != user_id:
                raise ValueError("Only decision owner can pin comments")
            
            # Unpin other comments first
            Comment.query.filter_by(decision_id=decision_id, is_pinned=True).update({'is_pinned': False})
            
            # Pin this comment
            comment.is_pinned = True
            db.session.commit()
            
            self.logger.info(f"Comment {comment_id} pinned by user {user_id}")
            return True
            
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Error pinning comment: {str(e)}")
            return False
    
    def get_comment_thread(
        self,
        comment_id: int
    ) -> List[Comment]:
        """
        Get a comment and all its replies in thread order
        
        Args:
            comment_id: ID of the root comment
            
        Returns:
            List of comments in thread order
        """
        try:
            root_comment = Comment.query.get(comment_id)
            if not root_comment:
                return []
            
            # Get all replies recursively
            def get_replies(parent_id):
                replies = Comment.query.filter_by(
                    parent_id=parent_id,
                    is_deleted=False
                ).order_by(Comment.created_at).all()
                
                result = []
                for reply in replies:
                    result.append(reply)
                    result.extend(get_replies(reply.id))
                
                return result
            
            thread = [root_comment]
            thread.extend(get_replies(comment_id))
            
            return thread
            
        except Exception as e:
            self.logger.error(f"Error getting comment thread: {str(e)}")
            return []
    
    def moderate_comment(
        self,
        comment_id: int,
        moderator_id: int,
        action: str,
        reason: str = None
    ) -> bool:
        """
        Moderate a comment (hide, flag, etc.)
        
        Args:
            comment_id: ID of the comment to moderate
            moderator_id: ID of the moderator
            action: Moderation action ('hide', 'flag', 'approve')
            reason: Optional reason for moderation
            
        Returns:
            True if successful, False otherwise
        """
        try:
            comment = Comment.query.get(comment_id)
            if not comment:
                raise ValueError(f"Comment {comment_id} not found")
            
            # For now, we'll implement basic moderation
            # In a full implementation, you'd have a separate moderation table
            
            if action == 'hide':
                comment.soft_delete()
            elif action == 'flag':
                # Add flag to comment metadata
                pass
            elif action == 'approve':
                # Remove any flags or restrictions
                pass
            
            db.session.commit()
            
            # Send notification to comment author about moderation action
            if action in ['hide', 'flag']:
                self._send_notification(
                    user_id=comment.user_id,
                    notification_type=NotificationType.STATUS_CHANGED,
                    title="Comment Moderated",
                    message=f"Your comment has been {action}d" + (f": {reason}" if reason else ""),
                    comment_id=comment_id
                )
            
            self.logger.info(f"Comment {comment_id} moderated by user {moderator_id}: {action}")
            return True
            
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Error moderating comment: {str(e)}")
            return False
    
    def get_user_mentions(
        self,
        user_id: int,
        limit: int = 50
    ) -> List[Comment]:
        """
        Get comments where a user was mentioned
        
        Args:
            user_id: ID of the user
            limit: Maximum number of mentions to return
            
        Returns:
            List of comments where user was mentioned
        """
        try:
            # This is a simplified implementation
            # In a full implementation, you'd store mentions in a separate table
            user = User.query.get(user_id)
            if not user:
                return []
            
            # Search for comments containing @username
            username_pattern = f"@{user.username}"
            comments = Comment.query.filter(
                Comment.content.contains(username_pattern),
                Comment.is_deleted == False
            ).order_by(Comment.created_at.desc()).limit(limit).all()
            
            return comments
            
        except Exception as e:
            self.logger.error(f"Error getting user mentions: {str(e)}")
            return []
    
    def _notify_decision_participants(
        self,
        decision: Decision,
        notification_type: NotificationType,
        title: str,
        message: str,
        exclude_user_id: int = None,
        comment_id: int = None
    ) -> None:
        """
        Notify all participants of a decision about an event
        
        Args:
            decision: Decision object
            notification_type: Type of notification
            title: Notification title
            message: Notification message
            exclude_user_id: User ID to exclude from notifications
            comment_id: Related comment ID
        """
        try:
            # Notify decision owner
            if decision.user_id != exclude_user_id:
                self._send_notification(
                    user_id=decision.user_id,
                    notification_type=notification_type,
                    title=title,
                    message=message,
                    decision_id=decision.id,
                    comment_id=comment_id
                )
            
            # Notify collaborators
            for collaborator in decision.collaborators:
                if collaborator.id != exclude_user_id:
                    self._send_notification(
                        user_id=collaborator.id,
                        notification_type=notification_type,
                        title=title,
                        message=message,
                        decision_id=decision.id,
                        comment_id=comment_id
                    )
                    
        except Exception as e:
            self.logger.error(f"Error notifying decision participants: {str(e)}")