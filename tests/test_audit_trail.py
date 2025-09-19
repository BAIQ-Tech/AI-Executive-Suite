"""
Tests for Audit Trail Functionality

Tests the audit logging and history tracking features.
"""

import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from models import (
    db, User, Decision, Comment, AuditLog, AuditEventType,
    ExecutiveType, CollaborationSession
)


class TestAuditLog:
    """Test cases for AuditLog model"""
    
    @pytest.fixture(autouse=True)
    def setup_database(self, app):
        """Set up test database"""
        self.app = app
        with app.app_context():
            db.create_all()
            
            # Create test user
            self.user = User(username="testuser", email="test@example.com", name="Test User")
            db.session.add(self.user)
            db.session.commit()
            
            # Create test decision
            self.decision = Decision(
                user_id=self.user.id,
                title="Test Decision",
                context="Test context",
                decision="Test decision",
                rationale="Test rationale",
                executive_type=ExecutiveType.CEO
            )
            db.session.add(self.decision)
            db.session.commit()
            
            yield
            db.drop_all()
    
    def test_create_audit_log(self):
        """Test creating an audit log entry"""
        with self.app.app_context():
            audit_log = AuditLog(
                event_type=AuditEventType.DECISION_CREATED,
                event_description="Test decision created",
                user_id=self.user.id,
                decision_id=self.decision.id
            )
            
            db.session.add(audit_log)
            db.session.commit()
            
            assert audit_log.id is not None
            assert audit_log.event_type == AuditEventType.DECISION_CREATED
            assert audit_log.event_description == "Test decision created"
            assert audit_log.user_id == self.user.id
            assert audit_log.decision_id == self.decision.id
            assert audit_log.created_at is not None
    
    def test_audit_log_with_values(self):
        """Test audit log with old and new values"""
        with self.app.app_context():
            old_values = {'title': 'Old Title', 'status': 'pending'}
            new_values = {'title': 'New Title', 'status': 'completed'}
            metadata = {'change_reason': 'User update'}
            
            audit_log = AuditLog(
                event_type=AuditEventType.DECISION_UPDATED,
                event_description="Decision updated",
                user_id=self.user.id,
                decision_id=self.decision.id
            )
            
            audit_log.set_old_values(old_values)
            audit_log.set_new_values(new_values)
            audit_log.set_metadata(metadata)
            
            db.session.add(audit_log)
            db.session.commit()
            
            # Test retrieval
            retrieved_log = AuditLog.query.get(audit_log.id)
            assert retrieved_log.get_old_values() == old_values
            assert retrieved_log.get_new_values() == new_values
            assert retrieved_log.get_metadata() == metadata
    
    def test_log_event_class_method(self):
        """Test the log_event class method"""
        with self.app.app_context():
            audit_log = AuditLog.log_event(
                event_type=AuditEventType.COMMENT_ADDED,
                event_description="Comment added to decision",
                user_id=self.user.id,
                decision_id=self.decision.id,
                user_ip="192.168.1.1",
                user_agent="Test Browser",
                metadata={'comment_length': 100}
            )
            
            assert audit_log is not None
            assert audit_log.event_type == AuditEventType.COMMENT_ADDED
            assert audit_log.user_ip == "192.168.1.1"
            assert audit_log.user_agent == "Test Browser"
            assert audit_log.get_metadata()['comment_length'] == 100
    
    def test_get_decision_audit_trail(self):
        """Test retrieving audit trail for a decision"""
        with self.app.app_context():
            # Create multiple audit log entries
            events = [
                (AuditEventType.DECISION_CREATED, "Decision created"),
                (AuditEventType.COMMENT_ADDED, "Comment added"),
                (AuditEventType.DECISION_UPDATED, "Decision updated")
            ]
            
            for event_type, description in events:
                AuditLog.log_event(
                    event_type=event_type,
                    event_description=description,
                    user_id=self.user.id,
                    decision_id=self.decision.id
                )
            
            # Retrieve audit trail
            audit_trail = AuditLog.get_decision_audit_trail(self.decision.id)
            
            assert len(audit_trail) == 3
            # Should be ordered by created_at desc
            assert audit_trail[0].event_type == AuditEventType.DECISION_UPDATED
            assert audit_trail[1].event_type == AuditEventType.COMMENT_ADDED
            assert audit_trail[2].event_type == AuditEventType.DECISION_CREATED
    
    def test_get_user_activity(self):
        """Test retrieving user activity"""
        with self.app.app_context():
            # Create audit log entries for user
            AuditLog.log_event(
                event_type=AuditEventType.LOGIN,
                event_description="User logged in",
                user_id=self.user.id
            )
            
            AuditLog.log_event(
                event_type=AuditEventType.DECISION_CREATED,
                event_description="Decision created",
                user_id=self.user.id,
                decision_id=self.decision.id
            )
            
            # Retrieve user activity
            activity = AuditLog.get_user_activity(self.user.id)
            
            assert len(activity) == 2
            assert all(log.user_id == self.user.id for log in activity)
    
    def test_get_system_audit_trail(self):
        """Test retrieving system-wide audit trail"""
        with self.app.app_context():
            # Create audit log entries
            AuditLog.log_event(
                event_type=AuditEventType.DECISION_CREATED,
                event_description="Decision created",
                user_id=self.user.id,
                decision_id=self.decision.id
            )
            
            # Retrieve system audit trail
            audit_trail = AuditLog.get_system_audit_trail()
            
            assert len(audit_trail) >= 1
            assert any(log.event_type == AuditEventType.DECISION_CREATED for log in audit_trail)
    
    def test_get_compliance_report(self):
        """Test generating compliance report"""
        with self.app.app_context():
            # Create audit log entries with specific date range
            start_date = datetime.now() - timedelta(days=1)
            end_date = datetime.now() + timedelta(days=1)
            
            AuditLog.log_event(
                event_type=AuditEventType.DECISION_CREATED,
                event_description="Decision created",
                user_id=self.user.id,
                decision_id=self.decision.id
            )
            
            AuditLog.log_event(
                event_type=AuditEventType.COMMENT_ADDED,
                event_description="Comment added",
                user_id=self.user.id,
                decision_id=self.decision.id
            )
            
            # Generate compliance report
            report = AuditLog.get_compliance_report(
                start_date=start_date,
                end_date=end_date,
                event_types=[AuditEventType.DECISION_CREATED, AuditEventType.COMMENT_ADDED]
            )
            
            assert len(report) == 2
            assert all(log.created_at >= start_date and log.created_at <= end_date for log in report)
    
    def test_to_dict(self):
        """Test converting audit log to dictionary"""
        with self.app.app_context():
            audit_log = AuditLog.log_event(
                event_type=AuditEventType.DECISION_CREATED,
                event_description="Decision created",
                user_id=self.user.id,
                decision_id=self.decision.id,
                metadata={'test': 'value'}
            )
            
            audit_dict = audit_log.to_dict()
            
            assert audit_dict['event_type'] == 'decision_created'
            assert audit_dict['event_description'] == 'Decision created'
            assert audit_dict['user_id'] == self.user.id
            assert audit_dict['decision_id'] == self.decision.id
            assert audit_dict['metadata']['test'] == 'value'
            assert 'user' in audit_dict
            assert audit_dict['user']['username'] == self.user.username


class TestAuditTrailRoutes:
    """Test cases for audit trail routes"""
    
    @pytest.fixture(autouse=True)
    def setup_database(self, app):
        """Set up test database and test client"""
        self.app = app
        self.client = app.test_client()
        
        with app.app_context():
            db.create_all()
            
            # Create test user
            self.user = User(username="testuser", email="test@example.com", name="Test User")
            self.user.set_password("password123")
            db.session.add(self.user)
            db.session.commit()
            
            # Create test decision
            self.decision = Decision(
                user_id=self.user.id,
                title="Test Decision",
                context="Test context",
                decision="Test decision",
                rationale="Test rationale",
                executive_type=ExecutiveType.CEO
            )
            db.session.add(self.decision)
            db.session.commit()
            
            # Create test audit logs
            AuditLog.log_event(
                event_type=AuditEventType.DECISION_CREATED,
                event_description="Decision created",
                user_id=self.user.id,
                decision_id=self.decision.id
            )
            
            AuditLog.log_event(
                event_type=AuditEventType.COMMENT_ADDED,
                event_description="Comment added",
                user_id=self.user.id,
                decision_id=self.decision.id
            )
            
            yield
            db.drop_all()
    
    def login_user(self, user):
        """Helper method to log in a user"""
        with self.client.session_transaction() as sess:
            sess['_user_id'] = str(user.id)
            sess['_fresh'] = True
    
    def test_get_decision_audit_trail_success(self):
        """Test retrieving decision audit trail"""
        self.login_user(self.user)
        
        response = self.client.get(f'/api/collaboration/audit/decision/{self.decision.id}')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'audit_trail' in data
        assert len(data['audit_trail']) >= 2
        assert data['count'] >= 2
    
    def test_get_decision_audit_trail_permission_denied(self):
        """Test audit trail access denied for non-owner"""
        # Create another user
        with self.app.app_context():
            other_user = User(username="otheruser", email="other@example.com", name="Other User")
            other_user.set_password("password123")
            db.session.add(other_user)
            db.session.commit()
        
        self.login_user(other_user)
        
        response = self.client.get(f'/api/collaboration/audit/decision/{self.decision.id}')
        
        assert response.status_code == 403
        data = json.loads(response.data)
        assert data['error'] == 'Permission denied'
    
    def test_get_user_audit_trail_success(self):
        """Test retrieving user audit trail"""
        self.login_user(self.user)
        
        response = self.client.get(f'/api/collaboration/audit/user/{self.user.id}')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'audit_trail' in data
        assert len(data['audit_trail']) >= 2
    
    def test_get_user_audit_trail_own_activity(self):
        """Test user can access their own audit trail"""
        self.login_user(self.user)
        
        response = self.client.get(f'/api/collaboration/audit/user/{self.user.id}')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert all(log['user_id'] == self.user.id for log in data['audit_trail'])
    
    def test_get_decision_timeline_success(self):
        """Test retrieving decision timeline"""
        self.login_user(self.user)
        
        response = self.client.get(f'/api/collaboration/timeline/{self.decision.id}')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'timeline' in data
        assert 'decision' in data
        assert data['decision']['id'] == self.decision.id
        assert len(data['timeline']) >= 2
        
        # Check timeline event structure
        timeline_event = data['timeline'][0]
        assert 'type' in timeline_event
        assert 'title' in timeline_event
        assert 'timestamp' in timeline_event
        assert 'icon' in timeline_event
        assert 'color' in timeline_event
    
    def test_unauthenticated_access_denied(self):
        """Test that unauthenticated users cannot access audit trails"""
        endpoints = [
            f'/api/collaboration/audit/decision/{self.decision.id}',
            f'/api/collaboration/audit/user/{self.user.id}',
            '/api/collaboration/audit/system',
            f'/api/collaboration/timeline/{self.decision.id}'
        ]
        
        for endpoint in endpoints:
            response = self.client.get(endpoint)
            # Should redirect to login or return 401
            assert response.status_code in [302, 401]


class TestAuditTrailIntegration:
    """Integration tests for audit trail functionality"""
    
    @pytest.fixture(autouse=True)
    def setup_database(self, app):
        """Set up test database"""
        self.app = app
        with app.app_context():
            db.create_all()
            yield
            db.drop_all()
    
    def test_collaboration_service_audit_logging(self):
        """Test that collaboration service creates audit logs"""
        from services.collaboration import CollaborationService
        
        with self.app.app_context():
            service = CollaborationService()
            
            # Create test user and decision
            user = User(username="testuser", email="test@example.com", name="Test User")
            db.session.add(user)
            db.session.commit()
            
            decision = Decision(
                user_id=user.id,
                title="Test Decision",
                context="Test context",
                decision="Test decision",
                rationale="Test rationale",
                executive_type=ExecutiveType.CEO
            )
            db.session.add(decision)
            db.session.commit()
            
            # Add comment (should create audit log)
            comment = service.add_comment(
                decision_id=decision.id,
                user_id=user.id,
                content="Test comment"
            )
            
            # Check that audit log was created
            audit_logs = AuditLog.query.filter_by(
                event_type=AuditEventType.COMMENT_ADDED,
                decision_id=decision.id
            ).all()
            
            assert len(audit_logs) == 1
            assert audit_logs[0].user_id == user.id
            assert audit_logs[0].comment_id == comment.id
            assert "Comment added to decision" in audit_logs[0].event_description
    
    def test_audit_log_error_handling(self):
        """Test that audit logging failures don't break main operations"""
        with self.app.app_context():
            # Mock database session to simulate failure
            with patch('models.db.session.commit') as mock_commit:
                mock_commit.side_effect = Exception("Database error")
                
                # This should not raise an exception even if audit logging fails
                audit_log = AuditLog.log_event(
                    event_type=AuditEventType.DECISION_CREATED,
                    event_description="Test event",
                    user_id=1
                )
                
                # Should return None on failure
                assert audit_log is None


if __name__ == '__main__':
    pytest.main([__file__])