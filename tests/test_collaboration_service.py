"""
Tests for Collaboration Service

Tests the team collaboration functionality for the AI Executive Suite.
"""

import pytest
import json
from datetime import datetime
from unittest.mock import Mock, patch

from services.collaboration import CollaborationService
from models import (
    db, User, Decision, Comment, CollaborationSession, CollaborationParticipant,
    CollaborationRole, Notification, NotificationType, DecisionStatus, ExecutiveType
)


class TestCollaborationService:
    """Test cases for CollaborationService"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.service = CollaborationService()
        
        # Create test users
        self.user1 = User(username="testuser1", email="test1@example.com", name="Test User 1")
        self.user2 = User(username="testuser2", email="test2@example.com", name="Test User 2")
        self.user3 = User(username="testuser3", email="test3@example.com", name="Test User 3")
        
        # Create test decision
        self.decision = Decision(
            user_id=1,  # Will be set to user1.id after commit
            title="Test Decision",
            context="Test context",
            decision="Test decision content",
            rationale="Test rationale",
            executive_type=ExecutiveType.CEO
        )
    
    @patch('models.db.session')
    def test_invite_collaborators_success(self, mock_session):
        """Test successful collaborator invitation"""
        # Mock database operations
        mock_session.add = Mock()
        mock_session.commit = Mock()
        mock_session.flush = Mock()
        
        # Mock queries
        with patch('models.Decision.query') as mock_decision_query, \
             patch('models.User.query') as mock_user_query, \
             patch('models.CollaborationSession.query') as mock_session_query:
            
            mock_decision_query.get.return_value = self.decision
            mock_user_query.get.side_effect = [self.user2, self.user3]
            mock_session_query.filter_by.return_value.first.return_value = None
            
            # Test invitation
            session = self.service.invite_collaborators(
                decision_id=1,
                user_ids=[2, 3],
                role=CollaborationRole.COMMENTER,
                inviter_id=1,
                title="Test Collaboration",
                description="Test description"
            )
            
            # Verify session creation
            assert session is not None
            assert session.decision_id == 1
            assert session.created_by == 1
            assert session.title == "Test Collaboration"
            assert session.description == "Test description"
            
            # Verify database operations
            mock_session.add.assert_called()
            mock_session.commit.assert_called()
    
    @patch('models.db.session')
    def test_invite_collaborators_decision_not_found(self, mock_session):
        """Test invitation with non-existent decision"""
        with patch('models.Decision.query') as mock_query:
            mock_query.get.return_value = None
            
            with pytest.raises(ValueError, match="Decision 999 not found"):
                self.service.invite_collaborators(
                    decision_id=999,
                    user_ids=[2, 3],
                    role=CollaborationRole.COMMENTER,
                    inviter_id=1
                )
    
    @patch('models.db.session')
    def test_add_comment_success(self, mock_session):
        """Test successful comment addition"""
        mock_session.add = Mock()
        mock_session.commit = Mock()
        
        with patch('models.Decision.query') as mock_decision_query, \
             patch('models.User.query') as mock_user_query:
            
            mock_decision_query.get.return_value = self.decision
            mock_user_query.get.return_value = self.user1
            
            comment = self.service.add_comment(
                decision_id=1,
                user_id=1,
                content="Test comment content"
            )
            
            assert comment is not None
            assert comment.decision_id == 1
            assert comment.user_id == 1
            assert comment.content == "Test comment content"
            
            mock_session.add.assert_called()
            mock_session.commit.assert_called()
    
    @patch('models.db.session')
    def test_add_comment_with_mentions(self, mock_session):
        """Test comment addition with user mentions"""
        mock_session.add = Mock()
        mock_session.commit = Mock()
        
        with patch('models.Decision.query') as mock_decision_query, \
             patch('models.User.query') as mock_user_query:
            
            mock_decision_query.get.return_value = self.decision
            mock_user_query.get.side_effect = [self.user1, self.user2]  # Author, then mentioned user
            
            # Mock the _send_notification method
            with patch.object(self.service, '_send_notification') as mock_notify:
                comment = self.service.add_comment(
                    decision_id=1,
                    user_id=1,
                    content="Test comment with @user2",
                    mentions=[2]
                )
                
                assert comment is not None
                # Verify notification was sent for mention
                mock_notify.assert_called()
    
    def test_get_decision_comments(self):
        """Test retrieving comments for a decision"""
        with patch('models.Comment.get_by_decision') as mock_get_comments:
            mock_comments = [
                Mock(id=1, content="Comment 1"),
                Mock(id=2, content="Comment 2")
            ]
            mock_get_comments.return_value = mock_comments
            
            comments = self.service.get_decision_comments(decision_id=1)
            
            assert len(comments) == 2
            assert comments == mock_comments
            mock_get_comments.assert_called_once_with(1)
    
    def test_get_collaboration_history(self):
        """Test retrieving collaboration history"""
        # Mock comments
        mock_comment = Mock()
        mock_comment.id = 1
        mock_comment.decision_id = 1
        mock_comment.user_id = 1
        mock_comment.content = "Test comment"
        mock_comment.parent_id = None
        mock_comment.created_at = datetime.now()
        mock_comment.user = self.user1
        
        # Mock collaboration session
        mock_session = Mock()
        mock_session.id = 1
        mock_session.decision_id = 1
        mock_session.created_by = 1
        mock_session.title = "Test Session"
        mock_session.created_at = datetime.now()
        mock_session.creator = self.user1
        mock_session.participants = []
        mock_session.get_active_participants.return_value = []
        
        with patch('models.Comment.query') as mock_comment_query, \
             patch('models.CollaborationSession.query') as mock_session_query:
            
            mock_comment_query.filter_by.return_value.order_by.return_value.all.return_value = [mock_comment]
            mock_session_query.filter_by.return_value.all.return_value = [mock_session]
            
            history = self.service.get_collaboration_history(decision_id=1)
            
            assert len(history) >= 1
            assert any(event['event_type'] == 'comment_added' for event in history)
            assert any(event['event_type'] == 'collaboration_started' for event in history)
    
    @patch('models.db.session')
    def test_update_collaboration_permissions(self, mock_session):
        """Test updating collaboration permissions"""
        mock_session.commit = Mock()
        
        # Mock participant
        mock_participant = Mock()
        mock_participant.role = CollaborationRole.VIEWER
        mock_participant.change_role = Mock()
        
        with patch('models.CollaborationParticipant.query') as mock_query, \
             patch.object(self.service, '_send_notification') as mock_notify:
            
            mock_query.filter_by.return_value.first.return_value = mock_participant
            
            result = self.service.update_collaboration_permissions(
                session_id=1,
                user_id=2,
                new_role=CollaborationRole.EDITOR
            )
            
            assert result is True
            mock_participant.change_role.assert_called_once_with(CollaborationRole.EDITOR)
            mock_session.commit.assert_called()
            mock_notify.assert_called()
    
    def test_update_collaboration_permissions_participant_not_found(self):
        """Test updating permissions for non-existent participant"""
        with patch('models.CollaborationParticipant.query') as mock_query:
            mock_query.filter_by.return_value.first.return_value = None
            
            result = self.service.update_collaboration_permissions(
                session_id=1,
                user_id=999,
                new_role=CollaborationRole.EDITOR
            )
            
            assert result is False
    
    def test_get_collaboration_session(self):
        """Test retrieving collaboration session"""
        mock_session = Mock()
        
        with patch('models.CollaborationSession.query') as mock_query:
            mock_query.filter_by.return_value.first.return_value = mock_session
            
            result = self.service.get_collaboration_session(decision_id=1)
            
            assert result == mock_session
            mock_query.filter_by.assert_called_once_with(decision_id=1, is_active=True)
    
    @patch('models.db.session')
    def test_remove_collaborator(self, mock_session):
        """Test removing a collaborator"""
        mock_session.commit = Mock()
        
        mock_participant = Mock()
        mock_participant.leave_session = Mock()
        
        with patch('models.CollaborationParticipant.query') as mock_query:
            mock_query.filter_by.return_value.first.return_value = mock_participant
            
            result = self.service.remove_collaborator(session_id=1, user_id=2)
            
            assert result is True
            mock_participant.leave_session.assert_called_once()
            mock_session.commit.assert_called()
    
    @patch('models.db.session')
    def test_send_notification(self, mock_session):
        """Test sending notifications"""
        mock_session.add = Mock()
        mock_session.commit = Mock()
        
        result = self.service._send_notification(
            user_id=1,
            notification_type=NotificationType.COMMENT_ADDED,
            title="Test Notification",
            message="Test message",
            decision_id=1
        )
        
        assert result is True
        mock_session.add.assert_called()
        mock_session.commit.assert_called()
    
    def test_notify_decision_participants(self):
        """Test notifying decision participants"""
        # Mock decision with collaborators
        mock_decision = Mock()
        mock_decision.id = 1
        mock_decision.user_id = 1
        mock_decision.collaborators = [self.user2, self.user3]
        
        with patch.object(self.service, '_send_notification') as mock_notify:
            self.service._notify_decision_participants(
                decision=mock_decision,
                notification_type=NotificationType.COMMENT_ADDED,
                title="Test Notification",
                message="Test message",
                exclude_user_id=1  # Exclude decision owner
            )
            
            # Should notify collaborators but not the excluded user
            assert mock_notify.call_count == 2  # Two collaborators


class TestCollaborationServiceIntegration:
    """Integration tests for CollaborationService"""
    
    @pytest.fixture(autouse=True)
    def setup_database(self, app):
        """Set up test database"""
        with app.app_context():
            db.create_all()
            yield
            db.drop_all()
    
    def test_full_collaboration_workflow(self, app):
        """Test complete collaboration workflow"""
        with app.app_context():
            service = CollaborationService()
            
            # Create test users
            user1 = User(username="owner", email="owner@test.com", name="Owner")
            user2 = User(username="collaborator", email="collab@test.com", name="Collaborator")
            
            db.session.add_all([user1, user2])
            db.session.commit()
            
            # Create test decision
            decision = Decision(
                user_id=user1.id,
                title="Integration Test Decision",
                context="Test context",
                decision="Test decision",
                rationale="Test rationale",
                executive_type=ExecutiveType.CEO
            )
            
            db.session.add(decision)
            db.session.commit()
            
            # Invite collaborator
            session = service.invite_collaborators(
                decision_id=decision.id,
                user_ids=[user2.id],
                role=CollaborationRole.COMMENTER,
                inviter_id=user1.id
            )
            
            assert session is not None
            assert len(session.participants) == 1
            
            # Add comment
            comment = service.add_comment(
                decision_id=decision.id,
                user_id=user2.id,
                content="This is a test comment"
            )
            
            assert comment is not None
            assert comment.content == "This is a test comment"
            
            # Get comments
            comments = service.get_decision_comments(decision.id)
            assert len(comments) == 1
            assert comments[0].id == comment.id
            
            # Get collaboration history
            history = service.get_collaboration_history(decision.id)
            assert len(history) >= 2  # Session creation + comment
            
            # Update permissions
            success = service.update_collaboration_permissions(
                session_id=session.id,
                user_id=user2.id,
                new_role=CollaborationRole.EDITOR
            )
            
            assert success is True
            
            # Verify permission change
            participant = CollaborationParticipant.query.filter_by(
                session_id=session.id,
                user_id=user2.id
            ).first()
            
            assert participant.role == CollaborationRole.EDITOR


if __name__ == '__main__':
    pytest.main([__file__])