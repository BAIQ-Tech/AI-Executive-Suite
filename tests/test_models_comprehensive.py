"""
Comprehensive unit tests for Models
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import Mock, patch

from models import (
    User, Decision, Document, Comment, CollaborationSession,
    DecisionStatus, Priority, RiskLevel, DocumentType, SensitivityLevel
)
from tests.factories import (
    UserFactory, DecisionFactory, DocumentFactory, 
    CommentFactory, CollaborationSessionFactory
)


class TestUser:
    """Test User model"""
    
    def test_user_creation(self):
        user = User(
            username='testuser',
            email='test@example.com',
            password_hash='hashed_password'
        )
        
        assert user.username == 'testuser'
        assert user.email == 'test@example.com'
        assert user.password_hash == 'hashed_password'
        assert user.is_active is True
        assert user.mfa_enabled is False
        assert isinstance(user.created_at, datetime)
    
    def test_user_factory(self):
        user = UserFactory.build()
        
        assert user.username is not None
        assert user.email is not None
        assert user.password_hash is not None
        assert '@example.com' in user.email
    
    def test_user_password_methods(self):
        user = User(username='test', email='test@example.com')
        
        # Test password setting
        user.set_password('test_password')
        assert user.password_hash is not None
        assert user.password_hash != 'test_password'  # Should be hashed
        
        # Test password verification
        assert user.check_password('test_password') is True
        assert user.check_password('wrong_password') is False
    
    def test_user_mfa_methods(self):
        user = User(username='test', email='test@example.com')
        
        # Test MFA setup
        secret = user.setup_mfa()
        assert secret is not None
        assert user.mfa_secret is not None
        assert user.mfa_enabled is True
        
        # Test MFA verification (mock TOTP)
        with patch('pyotp.TOTP') as mock_totp:
            mock_totp.return_value.verify.return_value = True
            assert user.verify_mfa_token('123456') is True
            
            mock_totp.return_value.verify.return_value = False
            assert user.verify_mfa_token('wrong_token') is False
    
    def test_user_backup_codes(self):
        user = User(username='test', email='test@example.com')
        
        # Generate backup codes
        codes = user.generate_backup_codes()
        assert len(codes) == 10
        assert all(len(code) == 8 for code in codes)
        assert user.backup_codes is not None
        
        # Use backup code
        assert user.use_backup_code(codes[0]) is True
        assert user.use_backup_code(codes[0]) is False  # Should not work twice
        assert user.use_backup_code('invalid_code') is False
    
    def test_user_preferences(self):
        user = User(username='test', email='test@example.com')
        
        # Test default preferences
        assert user.get_preference('theme') == 'light'
        assert user.get_preference('notifications') is True
        
        # Test setting preferences
        user.set_preference('theme', 'dark')
        assert user.get_preference('theme') == 'dark'
        
        # Test bulk preference update
        user.update_preferences({
            'language': 'es',
            'timezone': 'EST'
        })
        assert user.get_preference('language') == 'es'
        assert user.get_preference('timezone') == 'EST'
    
    def test_user_activity_tracking(self):
        user = User(username='test', email='test@example.com')
        
        # Test login tracking
        user.record_login()
        assert user.last_login is not None
        assert user.login_count == 1
        
        # Test activity update
        user.update_last_activity()
        assert user.last_activity is not None
    
    def test_user_string_representation(self):
        user = User(username='testuser', email='test@example.com')
        assert str(user) == 'testuser'
        assert repr(user) == '<User testuser>'


class TestDecision:
    """Test Decision model"""
    
    def test_decision_creation(self):
        decision = Decision(
            user_id=1,
            executive_type='ceo',
            title='Test Decision',
            context='Test context',
            decision='Test decision content',
            rationale='Test rationale'
        )
        
        assert decision.user_id == 1
        assert decision.executive_type == 'ceo'
        assert decision.title == 'Test Decision'
        assert decision.context == 'Test context'
        assert decision.decision == 'Test decision content'
        assert decision.rationale == 'Test rationale'
        assert isinstance(decision.created_at, datetime)
    
    def test_decision_factory(self):
        decision = DecisionFactory.build()
        
        assert decision.executive_type in ['ceo', 'cto', 'cfo']
        assert decision.priority in ['low', 'medium', 'high']
        assert decision.category is not None
        assert decision.status is not None
        assert isinstance(decision.confidence_score, float)
        assert 0.5 <= decision.confidence_score <= 1.0
    
    def test_decision_status_enum(self):
        assert DecisionStatus.PENDING.value == 'pending'
        assert DecisionStatus.IN_PROGRESS.value == 'in_progress'
        assert DecisionStatus.COMPLETED.value == 'completed'
        assert DecisionStatus.CANCELLED.value == 'cancelled'
    
    def test_decision_priority_enum(self):
        assert Priority.LOW.value == 'low'
        assert Priority.MEDIUM.value == 'medium'
        assert Priority.HIGH.value == 'high'
    
    def test_decision_risk_level_enum(self):
        assert RiskLevel.LOW.value == 'low'
        assert RiskLevel.MEDIUM.value == 'medium'
        assert RiskLevel.HIGH.value == 'high'
    
    def test_decision_status_transitions(self):
        decision = Decision(
            user_id=1,
            executive_type='ceo',
            title='Test',
            context='Test',
            decision='Test',
            rationale='Test'
        )
        
        # Test status transitions
        assert decision.can_transition_to(DecisionStatus.IN_PROGRESS) is True
        
        decision.status = DecisionStatus.IN_PROGRESS
        assert decision.can_transition_to(DecisionStatus.COMPLETED) is True
        assert decision.can_transition_to(DecisionStatus.CANCELLED) is True
        
        decision.status = DecisionStatus.COMPLETED
        assert decision.can_transition_to(DecisionStatus.PENDING) is False
    
    def test_decision_implementation_tracking(self):
        decision = Decision(
            user_id=1,
            executive_type='ceo',
            title='Test',
            context='Test',
            decision='Test',
            rationale='Test'
        )
        
        # Test implementation
        decision.mark_implemented('Implementation completed successfully')
        assert decision.status == DecisionStatus.COMPLETED
        assert decision.implemented_at is not None
        assert decision.implementation_notes == 'Implementation completed successfully'
    
    def test_decision_effectiveness_calculation(self):
        decision = Decision(
            user_id=1,
            executive_type='ceo',
            title='Test',
            context='Test',
            decision='Test',
            rationale='Test',
            outcome_rating=4,
            confidence_score=0.8
        )
        
        effectiveness = decision.calculate_effectiveness()
        assert isinstance(effectiveness, float)
        assert 0 <= effectiveness <= 1
    
    def test_decision_financial_impact(self):
        decision = Decision(
            user_id=1,
            executive_type='cfo',
            title='Budget Decision',
            context='Budget allocation',
            decision='Allocate budget',
            rationale='Cost optimization',
            financial_impact=Decimal('50000')
        )
        
        assert decision.financial_impact == Decimal('50000')
        assert decision.has_financial_impact() is True
        
        decision.financial_impact = None
        assert decision.has_financial_impact() is False
    
    def test_decision_collaboration_methods(self):
        decision = Decision(
            user_id=1,
            executive_type='ceo',
            title='Test',
            context='Test',
            decision='Test',
            rationale='Test'
        )
        
        # Test adding collaborators
        decision.add_collaborator(2)
        decision.add_collaborator(3)
        assert 2 in decision.collaborators
        assert 3 in decision.collaborators
        
        # Test removing collaborators
        decision.remove_collaborator(2)
        assert 2 not in decision.collaborators
        assert 3 in decision.collaborators
    
    def test_decision_document_references(self):
        decision = Decision(
            user_id=1,
            executive_type='ceo',
            title='Test',
            context='Test',
            decision='Test',
            rationale='Test'
        )
        
        # Test adding document references
        decision.add_document_reference('doc1')
        decision.add_document_reference('doc2')
        assert 'doc1' in decision.documents
        assert 'doc2' in decision.documents
        
        # Test removing document references
        decision.remove_document_reference('doc1')
        assert 'doc1' not in decision.documents
        assert 'doc2' in decision.documents
    
    def test_decision_string_representation(self):
        decision = Decision(
            user_id=1,
            executive_type='ceo',
            title='Test Decision',
            context='Test',
            decision='Test',
            rationale='Test'
        )
        
        assert str(decision) == 'Test Decision'
        assert 'Test Decision' in repr(decision)


class TestDocument:
    """Test Document model"""
    
    def test_document_creation(self):
        document = Document(
            user_id=1,
            filename='test.pdf',
            file_type='pdf',
            file_size=1024,
            content_hash='hash123',
            extracted_text='Test content'
        )
        
        assert document.user_id == 1
        assert document.filename == 'test.pdf'
        assert document.file_type == 'pdf'
        assert document.file_size == 1024
        assert document.content_hash == 'hash123'
        assert document.extracted_text == 'Test content'
        assert isinstance(document.created_at, datetime)
    
    def test_document_factory(self):
        document = DocumentFactory.build()
        
        assert document.filename is not None
        assert document.file_type in ['pdf', 'docx', 'xlsx', 'txt']
        assert document.document_type in ['financial', 'technical', 'strategic', 'legal']
        assert document.sensitivity_level in ['public', 'internal', 'confidential', 'restricted']
        assert isinstance(document.file_size, int)
        assert document.file_size > 0
    
    def test_document_type_enum(self):
        assert DocumentType.FINANCIAL.value == 'financial'
        assert DocumentType.TECHNICAL.value == 'technical'
        assert DocumentType.STRATEGIC.value == 'strategic'
        assert DocumentType.LEGAL.value == 'legal'
    
    def test_sensitivity_level_enum(self):
        assert SensitivityLevel.PUBLIC.value == 'public'
        assert SensitivityLevel.INTERNAL.value == 'internal'
        assert SensitivityLevel.CONFIDENTIAL.value == 'confidential'
        assert SensitivityLevel.RESTRICTED.value == 'restricted'
    
    def test_document_processing_status(self):
        document = Document(
            user_id=1,
            filename='test.pdf',
            file_type='pdf',
            file_size=1024,
            content_hash='hash123'
        )
        
        # Test processing status
        assert document.is_processed() is False
        
        document.mark_processed('Extracted text content')
        assert document.is_processed() is True
        assert document.processed_at is not None
        assert document.extracted_text == 'Extracted text content'
    
    def test_document_insights_management(self):
        document = Document(
            user_id=1,
            filename='test.pdf',
            file_type='pdf',
            file_size=1024,
            content_hash='hash123'
        )
        
        # Test adding insights
        document.add_insight('Revenue increased by 15%')
        document.add_insight('Market share grew')
        assert len(document.key_insights) == 2
        assert 'Revenue increased by 15%' in document.key_insights
        
        # Test removing insights
        document.remove_insight('Revenue increased by 15%')
        assert len(document.key_insights) == 1
        assert 'Revenue increased by 15%' not in document.key_insights
    
    def test_document_reference_tracking(self):
        document = Document(
            user_id=1,
            filename='test.pdf',
            file_type='pdf',
            file_size=1024,
            content_hash='hash123'
        )
        
        # Test reference counting
        assert document.reference_count == 0
        
        document.increment_reference_count()
        assert document.reference_count == 1
        
        document.add_decision_reference('decision123')
        assert 'decision123' in document.decisions_referenced
        assert document.reference_count == 2
    
    def test_document_access_tracking(self):
        document = Document(
            user_id=1,
            filename='test.pdf',
            file_type='pdf',
            file_size=1024,
            content_hash='hash123'
        )
        
        # Test access tracking
        assert document.last_accessed is None
        
        document.record_access()
        assert document.last_accessed is not None
        
        first_access = document.last_accessed
        document.record_access()
        assert document.last_accessed > first_access
    
    def test_document_security_methods(self):
        document = Document(
            user_id=1,
            filename='test.pdf',
            file_type='pdf',
            file_size=1024,
            content_hash='hash123',
            sensitivity_level='confidential'
        )
        
        # Test security checks
        assert document.is_sensitive() is True
        assert document.requires_encryption() is True
        
        document.sensitivity_level = 'public'
        assert document.is_sensitive() is False
        assert document.requires_encryption() is False
    
    def test_document_string_representation(self):
        document = Document(
            user_id=1,
            filename='test.pdf',
            file_type='pdf',
            file_size=1024,
            content_hash='hash123'
        )
        
        assert str(document) == 'test.pdf'
        assert 'test.pdf' in repr(document)


class TestComment:
    """Test Comment model"""
    
    def test_comment_creation(self):
        comment = Comment(
            decision_id=1,
            user_id=1,
            content='This is a test comment'
        )
        
        assert comment.decision_id == 1
        assert comment.user_id == 1
        assert comment.content == 'This is a test comment'
        assert isinstance(comment.created_at, datetime)
        assert comment.updated_at == comment.created_at
    
    def test_comment_factory(self):
        comment = CommentFactory.build()
        
        assert comment.content is not None
        assert len(comment.content) > 0
        assert comment.thread_level == 0
        assert comment.parent_comment_id is None
    
    def test_comment_threading(self):
        parent_comment = Comment(
            decision_id=1,
            user_id=1,
            content='Parent comment'
        )
        
        reply_comment = Comment(
            decision_id=1,
            user_id=2,
            content='Reply comment',
            parent_comment_id=parent_comment.id,
            thread_level=1
        )
        
        assert reply_comment.parent_comment_id == parent_comment.id
        assert reply_comment.thread_level == 1
        assert reply_comment.is_reply() is True
        assert parent_comment.is_reply() is False
    
    def test_comment_editing(self):
        comment = Comment(
            decision_id=1,
            user_id=1,
            content='Original content'
        )
        
        original_created = comment.created_at
        
        # Test editing
        comment.edit_content('Updated content')
        assert comment.content == 'Updated content'
        assert comment.updated_at > original_created
        assert comment.metadata.get('edited') is True
    
    def test_comment_mentions(self):
        comment = Comment(
            decision_id=1,
            user_id=1,
            content='Hello @user2 and @user3'
        )
        
        # Test mention extraction
        mentions = comment.extract_mentions()
        assert 'user2' in mentions
        assert 'user3' in mentions
        
        # Test adding mentions to metadata
        comment.add_mention('user4')
        assert 'user4' in comment.metadata.get('mentions', [])
    
    def test_comment_string_representation(self):
        comment = Comment(
            decision_id=1,
            user_id=1,
            content='Test comment content'
        )
        
        assert 'Test comment content' in str(comment)
        assert 'Comment' in repr(comment)


class TestCollaborationSession:
    """Test CollaborationSession model"""
    
    def test_collaboration_session_creation(self):
        session = CollaborationSession(
            decision_id=1,
            owner_id=1,
            title='Test Collaboration',
            description='Test collaboration session'
        )
        
        assert session.decision_id == 1
        assert session.owner_id == 1
        assert session.title == 'Test Collaboration'
        assert session.description == 'Test collaboration session'
        assert session.status == 'active'
        assert isinstance(session.created_at, datetime)
    
    def test_collaboration_session_factory(self):
        session = CollaborationSessionFactory.build()
        
        assert session.title is not None
        assert session.status in ['active', 'completed', 'cancelled']
        assert isinstance(session.permissions, dict)
        assert isinstance(session.participants, list)
    
    def test_collaboration_participant_management(self):
        session = CollaborationSession(
            decision_id=1,
            owner_id=1,
            title='Test Collaboration'
        )
        
        # Test adding participants
        session.add_participant(2, {'can_comment': True, 'can_edit': False})
        session.add_participant(3, {'can_comment': True, 'can_edit': True})
        
        assert len(session.participants) == 2
        assert session.is_participant(2) is True
        assert session.is_participant(4) is False
        
        # Test removing participants
        session.remove_participant(2)
        assert len(session.participants) == 1
        assert session.is_participant(2) is False
    
    def test_collaboration_permissions(self):
        session = CollaborationSession(
            decision_id=1,
            owner_id=1,
            title='Test Collaboration'
        )
        
        session.add_participant(2, {'can_comment': True, 'can_edit': False})
        
        # Test permission checks
        assert session.can_user_comment(2) is True
        assert session.can_user_edit(2) is False
        assert session.can_user_comment(3) is False  # Not a participant
    
    def test_collaboration_status_management(self):
        session = CollaborationSession(
            decision_id=1,
            owner_id=1,
            title='Test Collaboration'
        )
        
        assert session.is_active() is True
        
        # Test completing session
        session.complete('Collaboration completed successfully')
        assert session.status == 'completed'
        assert session.completed_at is not None
        assert session.is_active() is False
        
        # Test cancelling session
        session.status = 'active'
        session.cancel('Collaboration cancelled')
        assert session.status == 'cancelled'
    
    def test_collaboration_workflow(self):
        session = CollaborationSession(
            decision_id=1,
            owner_id=1,
            title='Test Collaboration',
            requires_approval=True,
            approval_threshold=2
        )
        
        # Test approval workflow
        assert session.requires_approval is True
        assert session.approval_threshold == 2
        
        session.add_approval(2)
        session.add_approval(3)
        
        assert session.get_approval_count() == 2
        assert session.is_approved() is True
    
    def test_collaboration_string_representation(self):
        session = CollaborationSession(
            decision_id=1,
            owner_id=1,
            title='Test Collaboration Session'
        )
        
        assert str(session) == 'Test Collaboration Session'
        assert 'Test Collaboration Session' in repr(session)


if __name__ == "__main__":
    pytest.main([__file__])