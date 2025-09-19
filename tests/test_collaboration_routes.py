"""
Tests for Collaboration Routes

Tests the collaboration API endpoints for the AI Executive Suite.
"""

import pytest
import json
from unittest.mock import Mock, patch

from models import (
    db, User, Decision, Comment, CollaborationSession, CollaborationParticipant,
    CollaborationRole, Notification, NotificationType, ExecutiveType
)


class TestCollaborationRoutes:
    """Test cases for collaboration routes"""
    
    @pytest.fixture(autouse=True)
    def setup_database(self, app):
        """Set up test database and test client"""
        self.app = app
        self.client = app.test_client()
        
        with app.app_context():
            db.create_all()
            
            # Create test users
            self.user1 = User(username="testuser1", email="test1@example.com", name="Test User 1")
            self.user1.set_password("password123")
            
            self.user2 = User(username="testuser2", email="test2@example.com", name="Test User 2")
            self.user2.set_password("password123")
            
            db.session.add_all([self.user1, self.user2])
            db.session.commit()
            
            # Create test decision
            self.decision = Decision(
                user_id=self.user1.id,
                title="Test Decision",
                context="Test context",
                decision="Test decision content",
                rationale="Test rationale",
                executive_type=ExecutiveType.CEO
            )
            
            db.session.add(self.decision)
            db.session.commit()
            
            yield
            db.drop_all()
    
    def login_user(self, user):
        """Helper method to log in a user"""
        with self.client.session_transaction() as sess:
            sess['_user_id'] = str(user.id)
            sess['_fresh'] = True
    
    def test_invite_collaborators_success(self):
        """Test successful collaborator invitation"""
        self.login_user(self.user1)
        
        response = self.client.post('/api/collaboration/invite', 
            json={
                'decision_id': self.decision.id,
                'user_ids': [self.user2.id],
                'role': 'commenter',
                'title': 'Test Collaboration',
                'description': 'Test description'
            },
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'session' in data
        assert data['message'] == 'Successfully invited 1 collaborators'
    
    def test_invite_collaborators_missing_data(self):
        """Test invitation with missing data"""
        self.login_user(self.user1)
        
        response = self.client.post('/api/collaboration/invite', 
            json={},
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'decision_id is required' in data['error']
    
    def test_invite_collaborators_invalid_role(self):
        """Test invitation with invalid role"""
        self.login_user(self.user1)
        
        response = self.client.post('/api/collaboration/invite', 
            json={
                'decision_id': self.decision.id,
                'user_ids': [self.user2.id],
                'role': 'invalid_role'
            },
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'Invalid role' in data['error']
    
    def test_invite_collaborators_permission_denied(self):
        """Test invitation by non-owner"""
        self.login_user(self.user2)  # User2 doesn't own the decision
        
        response = self.client.post('/api/collaboration/invite', 
            json={
                'decision_id': self.decision.id,
                'user_ids': [self.user1.id],
                'role': 'commenter'
            },
            content_type='application/json'
        )
        
        assert response.status_code == 403
        data = json.loads(response.data)
        assert data['error'] == 'Permission denied'
    
    def test_add_comment_success(self):
        """Test successful comment addition"""
        self.login_user(self.user1)
        
        response = self.client.post('/api/collaboration/comment', 
            json={
                'decision_id': self.decision.id,
                'content': 'This is a test comment'
            },
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'comment' in data
        assert data['comment']['content'] == 'This is a test comment'
    
    def test_add_comment_missing_content(self):
        """Test comment addition with missing content"""
        self.login_user(self.user1)
        
        response = self.client.post('/api/collaboration/comment', 
            json={
                'decision_id': self.decision.id,
                'content': ''
            },
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'content is required' in data['error']
    
    def test_add_comment_with_mentions(self):
        """Test comment addition with mentions"""
        self.login_user(self.user1)
        
        response = self.client.post('/api/collaboration/comment', 
            json={
                'decision_id': self.decision.id,
                'content': 'Test comment with @user2',
                'mentions': [self.user2.id]
            },
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
    
    def test_get_comments_success(self):
        """Test retrieving comments for a decision"""
        self.login_user(self.user1)
        
        # First add a comment
        comment = Comment(
            decision_id=self.decision.id,
            user_id=self.user1.id,
            content="Test comment"
        )
        db.session.add(comment)
        db.session.commit()
        
        response = self.client.get(f'/api/collaboration/comments/{self.decision.id}')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'comments' in data
        assert len(data['comments']) == 1
        assert data['comments'][0]['content'] == 'Test comment'
    
    def test_get_comments_permission_denied(self):
        """Test retrieving comments without permission"""
        # Create another user who doesn't have access
        user3 = User(username="testuser3", email="test3@example.com", name="Test User 3")
        user3.set_password("password123")
        db.session.add(user3)
        db.session.commit()
        
        self.login_user(user3)
        
        response = self.client.get(f'/api/collaboration/comments/{self.decision.id}')
        
        assert response.status_code == 403
        data = json.loads(response.data)
        assert data['error'] == 'Permission denied'
    
    def test_get_collaboration_history_success(self):
        """Test retrieving collaboration history"""
        self.login_user(self.user1)
        
        response = self.client.get(f'/api/collaboration/history/{self.decision.id}')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'history' in data
    
    def test_get_collaboration_session_success(self):
        """Test retrieving collaboration session"""
        self.login_user(self.user1)
        
        response = self.client.get(f'/api/collaboration/session/{self.decision.id}')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        # Should return None if no session exists
        assert data['session'] is None
    
    def test_get_collaboration_session_with_active_session(self):
        """Test retrieving active collaboration session"""
        self.login_user(self.user1)
        
        # Create a collaboration session
        session = CollaborationSession(
            decision_id=self.decision.id,
            created_by=self.user1.id,
            title="Test Session"
        )
        db.session.add(session)
        db.session.commit()
        
        response = self.client.get(f'/api/collaboration/session/{self.decision.id}')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['session'] is not None
        assert data['session']['title'] == 'Test Session'
    
    def test_update_permissions_success(self):
        """Test updating collaboration permissions"""
        self.login_user(self.user1)
        
        # Create collaboration session and participant
        session = CollaborationSession(
            decision_id=self.decision.id,
            created_by=self.user1.id,
            title="Test Session"
        )
        db.session.add(session)
        db.session.flush()
        
        participant = CollaborationParticipant(
            session_id=session.id,
            user_id=self.user2.id,
            role=CollaborationRole.VIEWER
        )
        db.session.add(participant)
        db.session.commit()
        
        response = self.client.put(f'/api/collaboration/session/{session.id}/permissions', 
            json={
                'user_id': self.user2.id,
                'role': 'editor'
            },
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['message'] == 'Permissions updated successfully'
    
    def test_update_permissions_not_creator(self):
        """Test updating permissions by non-creator"""
        self.login_user(self.user2)  # User2 is not the creator
        
        # Create collaboration session
        session = CollaborationSession(
            decision_id=self.decision.id,
            created_by=self.user1.id,  # User1 is the creator
            title="Test Session"
        )
        db.session.add(session)
        db.session.commit()
        
        response = self.client.put(f'/api/collaboration/session/{session.id}/permissions', 
            json={
                'user_id': self.user2.id,
                'role': 'editor'
            },
            content_type='application/json'
        )
        
        assert response.status_code == 403
        data = json.loads(response.data)
        assert data['error'] == 'Only session creator can update permissions'
    
    def test_remove_collaborator_success(self):
        """Test removing a collaborator"""
        self.login_user(self.user1)
        
        # Create collaboration session and participant
        session = CollaborationSession(
            decision_id=self.decision.id,
            created_by=self.user1.id,
            title="Test Session"
        )
        db.session.add(session)
        db.session.flush()
        
        participant = CollaborationParticipant(
            session_id=session.id,
            user_id=self.user2.id,
            role=CollaborationRole.COMMENTER
        )
        db.session.add(participant)
        db.session.commit()
        
        response = self.client.delete(f'/api/collaboration/session/{session.id}/remove/{self.user2.id}')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['message'] == 'Collaborator removed successfully'
    
    def test_remove_collaborator_self(self):
        """Test user removing themselves from collaboration"""
        self.login_user(self.user2)
        
        # Create collaboration session and participant
        session = CollaborationSession(
            decision_id=self.decision.id,
            created_by=self.user1.id,
            title="Test Session"
        )
        db.session.add(session)
        db.session.flush()
        
        participant = CollaborationParticipant(
            session_id=session.id,
            user_id=self.user2.id,
            role=CollaborationRole.COMMENTER
        )
        db.session.add(participant)
        db.session.commit()
        
        # User2 removing themselves
        response = self.client.delete(f'/api/collaboration/session/{session.id}/remove/{self.user2.id}')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
    
    def test_get_notifications_success(self):
        """Test retrieving notifications"""
        self.login_user(self.user1)
        
        # Create a test notification
        notification = Notification(
            user_id=self.user1.id,
            notification_type=NotificationType.COMMENT_ADDED,
            title="Test Notification",
            message="Test message"
        )
        db.session.add(notification)
        db.session.commit()
        
        response = self.client.get('/api/collaboration/notifications')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'notifications' in data
        assert len(data['notifications']) == 1
        assert data['notifications'][0]['title'] == 'Test Notification'
    
    def test_get_notifications_with_status_filter(self):
        """Test retrieving notifications with status filter"""
        self.login_user(self.user1)
        
        # Create notifications with different statuses
        notification1 = Notification(
            user_id=self.user1.id,
            notification_type=NotificationType.COMMENT_ADDED,
            title="Unread Notification",
            message="Unread message"
        )
        
        notification2 = Notification(
            user_id=self.user1.id,
            notification_type=NotificationType.COMMENT_ADDED,
            title="Read Notification",
            message="Read message"
        )
        notification2.mark_as_read()
        
        db.session.add_all([notification1, notification2])
        db.session.commit()
        
        # Test unread filter
        response = self.client.get('/api/collaboration/notifications?status=unread')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert len(data['notifications']) == 1
        assert data['notifications'][0]['title'] == 'Unread Notification'
    
    def test_mark_notification_read_success(self):
        """Test marking notification as read"""
        self.login_user(self.user1)
        
        # Create a test notification
        notification = Notification(
            user_id=self.user1.id,
            notification_type=NotificationType.COMMENT_ADDED,
            title="Test Notification",
            message="Test message"
        )
        db.session.add(notification)
        db.session.commit()
        
        response = self.client.put(f'/api/collaboration/notifications/{notification.id}/read')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['message'] == 'Notification marked as read'
        
        # Verify notification was marked as read
        db.session.refresh(notification)
        assert notification.status.value == 'read'
        assert notification.read_at is not None
    
    def test_mark_notification_read_permission_denied(self):
        """Test marking another user's notification as read"""
        self.login_user(self.user2)
        
        # Create notification for user1
        notification = Notification(
            user_id=self.user1.id,
            notification_type=NotificationType.COMMENT_ADDED,
            title="Test Notification",
            message="Test message"
        )
        db.session.add(notification)
        db.session.commit()
        
        # User2 trying to mark user1's notification as read
        response = self.client.put(f'/api/collaboration/notifications/{notification.id}/read')
        
        assert response.status_code == 403
        data = json.loads(response.data)
        assert data['error'] == 'Permission denied'
    
    def test_unauthenticated_access(self):
        """Test that unauthenticated users cannot access collaboration endpoints"""
        # Don't log in any user
        
        endpoints = [
            ('/api/collaboration/invite', 'POST'),
            ('/api/collaboration/comment', 'POST'),
            (f'/api/collaboration/comments/{self.decision.id}', 'GET'),
            (f'/api/collaboration/history/{self.decision.id}', 'GET'),
            (f'/api/collaboration/session/{self.decision.id}', 'GET'),
            ('/api/collaboration/notifications', 'GET')
        ]
        
        for endpoint, method in endpoints:
            if method == 'POST':
                response = self.client.post(endpoint, json={}, content_type='application/json')
            else:
                response = self.client.get(endpoint)
            
            # Should redirect to login or return 401
            assert response.status_code in [302, 401]


if __name__ == '__main__':
    pytest.main([__file__])