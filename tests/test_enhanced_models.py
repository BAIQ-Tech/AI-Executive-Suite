"""
Tests for enhanced database models.
"""

import pytest
import json
from datetime import datetime, timedelta
from decimal import Decimal
from models import (
    db, User, Decision, Document, DocumentContext, Comment, 
    CollaborationSession, CollaborationParticipant, Notification,
    DecisionStatus, DecisionPriority, ExecutiveType, RiskLevel,
    DocumentType, SensitivityLevel, CollaborationRole, NotificationType, NotificationStatus
)
from flask import Flask


@pytest.fixture
def app():
    """Create test Flask application."""
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['TESTING'] = True
    
    db.init_app(app)
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def test_user(app):
    """Create a test user."""
    with app.app_context():
        user = User(username='testuser', email='test@example.com', name='Test User')
        db.session.add(user)
        db.session.commit()
        return user


@pytest.fixture
def test_user2(app):
    """Create a second test user."""
    with app.app_context():
        user = User(username='testuser2', email='test2@example.com', name='Test User 2')
        db.session.add(user)
        db.session.commit()
        return user


class TestEnhancedDecisionModel:
    """Test cases for the enhanced Decision model."""
    
    def test_decision_creation(self, app, test_user):
        """Test basic decision creation."""
        with app.app_context():
            decision = Decision(
                user_id=test_user.id,
                title="Test Strategic Decision",
                context="We need to decide on market expansion",
                decision="Expand to European markets",
                rationale="Market analysis shows strong potential",
                executive_type=ExecutiveType.CEO,
                priority=DecisionPriority.HIGH,
                confidence_score=0.85,
                financial_impact=Decimal('1000000.00'),
                risk_level=RiskLevel.MEDIUM
            )
            
            db.session.add(decision)
            db.session.commit()
            
            assert decision.id is not None
            assert decision.title == "Test Strategic Decision"
            assert decision.executive_type == ExecutiveType.CEO
            assert decision.priority == DecisionPriority.HIGH
            assert decision.confidence_score == 0.85
            assert decision.financial_impact == Decimal('1000000.00')
            assert decision.risk_level == RiskLevel.MEDIUM
            assert decision.status == DecisionStatus.PENDING
    
    def test_decision_conversation_history(self, app, test_user):
        """Test conversation history functionality."""
        with app.app_context():
            decision = Decision(
                user_id=test_user.id,
                title="Test Decision",
                context="Test context",
                decision="Test decision",
                rationale="Test rationale",
                executive_type=ExecutiveType.CTO
            )
            
            # Test setting and getting conversation history
            history = [
                {"role": "user", "content": "What should we do about the server issues?"},
                {"role": "assistant", "content": "I recommend upgrading the infrastructure."}
            ]
            
            decision.set_conversation_history(history)
            db.session.add(decision)
            db.session.commit()
            
            retrieved_history = decision.get_conversation_history()
            assert len(retrieved_history) == 2
            assert retrieved_history[0]["role"] == "user"
            assert retrieved_history[1]["role"] == "assistant"
    
    def test_decision_collaborators(self, app, test_user, test_user2):
        """Test decision collaborator functionality."""
        with app.app_context():
            decision = Decision(
                user_id=test_user.id,
                title="Collaborative Decision",
                context="Team decision needed",
                decision="Proceed with plan A",
                rationale="Team consensus",
                executive_type=ExecutiveType.CEO
            )
            
            db.session.add(decision)
            db.session.commit()
            
            # Add collaborator
            decision.add_collaborator(test_user2)
            db.session.commit()
            
            assert len(decision.collaborators) == 1
            assert test_user2 in decision.collaborators
            
            # Remove collaborator
            decision.remove_collaborator(test_user2)
            db.session.commit()
            
            assert len(decision.collaborators) == 0
    
    def test_decision_status_update(self, app, test_user):
        """Test decision status update functionality."""
        with app.app_context():
            decision = Decision(
                user_id=test_user.id,
                title="Status Test Decision",
                context="Testing status updates",
                decision="Test decision",
                rationale="Test rationale",
                executive_type=ExecutiveType.CFO
            )
            
            db.session.add(decision)
            db.session.commit()
            
            # Test status update to completed
            decision.update_status(DecisionStatus.COMPLETED, "Implementation successful")
            db.session.commit()
            
            assert decision.status == DecisionStatus.COMPLETED
            assert decision.implementation_notes == "Implementation successful"
            assert decision.implemented_at is not None
    
    def test_decision_effectiveness_calculation(self, app, test_user):
        """Test effectiveness score calculation."""
        with app.app_context():
            decision = Decision(
                user_id=test_user.id,
                title="Effectiveness Test",
                context="Testing effectiveness",
                decision="Test decision",
                rationale="Test rationale",
                executive_type=ExecutiveType.CEO,
                confidence_score=0.8,
                outcome_rating=4
            )
            
            db.session.add(decision)
            db.session.commit()
            
            effectiveness = decision.calculate_effectiveness()
            expected = (4 / 5.0) * 0.8  # (outcome_rating / 5) * confidence_score
            
            assert effectiveness == expected
            assert decision.effectiveness_score == expected
    
    def test_decision_to_dict(self, app, test_user):
        """Test decision serialization to dictionary."""
        with app.app_context():
            decision = Decision(
                user_id=test_user.id,
                title="Serialization Test",
                context="Testing serialization",
                decision="Test decision",
                rationale="Test rationale",
                executive_type=ExecutiveType.CTO,
                priority=DecisionPriority.HIGH,
                confidence_score=0.9
            )
            
            db.session.add(decision)
            db.session.commit()
            
            decision_dict = decision.to_dict()
            
            assert decision_dict['id'] == decision.id
            assert decision_dict['title'] == "Serialization Test"
            assert decision_dict['executive_type'] == 'cto'
            assert decision_dict['priority'] == 'high'
            assert decision_dict['confidence_score'] == 0.9
            assert 'created_at' in decision_dict
            assert 'collaborators' in decision_dict
            assert 'documents' in decision_dict


class TestDocumentModel:
    """Test cases for the Document model."""
    
    def test_document_creation(self, app, test_user):
        """Test basic document creation."""
        with app.app_context():
            document = Document(
                user_id=test_user.id,
                filename="test_document.pdf",
                original_filename="Test Document.pdf",
                file_type="pdf",
                file_size=1024000,
                file_path="/uploads/test_document.pdf",
                content_hash="abc123def456",
                document_type=DocumentType.FINANCIAL,
                sensitivity_level=SensitivityLevel.CONFIDENTIAL
            )
            
            db.session.add(document)
            db.session.commit()
            
            assert document.id is not None
            assert document.filename == "test_document.pdf"
            assert document.document_type == DocumentType.FINANCIAL
            assert document.sensitivity_level == SensitivityLevel.CONFIDENTIAL
            assert document.processing_status == 'pending'
    
    def test_document_key_insights(self, app, test_user):
        """Test key insights functionality."""
        with app.app_context():
            document = Document(
                user_id=test_user.id,
                filename="insights_test.pdf",
                original_filename="Insights Test.pdf",
                file_type="pdf",
                file_size=500000,
                file_path="/uploads/insights_test.pdf",
                content_hash="insights123"
            )
            
            insights = [
                "Revenue increased by 15%",
                "Customer satisfaction improved",
                "Market share expanded"
            ]
            
            document.set_key_insights(insights)
            db.session.add(document)
            db.session.commit()
            
            retrieved_insights = document.get_key_insights()
            assert len(retrieved_insights) == 3
            assert "Revenue increased by 15%" in retrieved_insights
    
    def test_document_tags(self, app, test_user):
        """Test document tagging functionality."""
        with app.app_context():
            document = Document(
                user_id=test_user.id,
                filename="tagged_doc.pdf",
                original_filename="Tagged Document.pdf",
                file_type="pdf",
                file_size=300000,
                file_path="/uploads/tagged_doc.pdf",
                content_hash="tagged123"
            )
            
            db.session.add(document)
            db.session.commit()
            
            # Add tags
            document.add_tag("quarterly-report")
            document.add_tag("financial")
            document.add_tag("2024")
            db.session.commit()
            
            tags = document.get_tags()
            assert len(tags) == 3
            assert "quarterly-report" in tags
            assert "financial" in tags
            assert "2024" in tags
            
            # Remove tag
            document.remove_tag("2024")
            db.session.commit()
            
            tags = document.get_tags()
            assert len(tags) == 2
            assert "2024" not in tags
    
    def test_document_reference_count(self, app, test_user):
        """Test reference count functionality."""
        with app.app_context():
            document = Document(
                user_id=test_user.id,
                filename="ref_test.pdf",
                original_filename="Reference Test.pdf",
                file_type="pdf",
                file_size=200000,
                file_path="/uploads/ref_test.pdf",
                content_hash="ref123"
            )
            
            db.session.add(document)
            db.session.commit()
            
            assert document.reference_count == 0
            
            # Increment reference count
            document.increment_reference_count()
            db.session.commit()
            
            assert document.reference_count == 1
            assert document.last_accessed is not None


class TestDocumentContextModel:
    """Test cases for the DocumentContext model."""
    
    def test_context_creation(self, app, test_user):
        """Test document context creation."""
        with app.app_context():
            document = Document(
                user_id=test_user.id,
                filename="context_test.pdf",
                original_filename="Context Test.pdf",
                file_type="pdf",
                file_size=100000,
                file_path="/uploads/context_test.pdf",
                content_hash="context123"
            )
            
            db.session.add(document)
            db.session.commit()
            
            context = DocumentContext(
                document_id=document.id,
                chunk_index=0,
                content="This is the first paragraph of the document.",
                content_type="paragraph",
                page_number=1,
                importance_score=0.8
            )
            
            db.session.add(context)
            db.session.commit()
            
            assert context.id is not None
            assert context.document_id == document.id
            assert context.chunk_index == 0
            assert context.importance_score == 0.8
    
    def test_context_embedding_vector(self, app, test_user):
        """Test embedding vector functionality."""
        with app.app_context():
            document = Document(
                user_id=test_user.id,
                filename="embedding_test.pdf",
                original_filename="Embedding Test.pdf",
                file_type="pdf",
                file_size=100000,
                file_path="/uploads/embedding_test.pdf",
                content_hash="embedding123"
            )
            
            db.session.add(document)
            db.session.commit()
            
            context = DocumentContext(
                document_id=document.id,
                chunk_index=0,
                content="Test content for embedding"
            )
            
            # Set embedding vector
            vector = [0.1, 0.2, 0.3, 0.4, 0.5]
            context.set_embedding_vector(vector)
            
            db.session.add(context)
            db.session.commit()
            
            retrieved_vector = context.get_embedding_vector()
            assert retrieved_vector == vector
    
    def test_context_keywords(self, app, test_user):
        """Test context keywords functionality."""
        with app.app_context():
            document = Document(
                user_id=test_user.id,
                filename="keywords_test.pdf",
                original_filename="Keywords Test.pdf",
                file_type="pdf",
                file_size=100000,
                file_path="/uploads/keywords_test.pdf",
                content_hash="keywords123"
            )
            
            db.session.add(document)
            db.session.commit()
            
            context = DocumentContext(
                document_id=document.id,
                chunk_index=0,
                content="Financial analysis and revenue projections"
            )
            
            db.session.add(context)
            db.session.commit()
            
            # Add keywords
            context.add_keyword("financial")
            context.add_keyword("revenue")
            context.add_keyword("analysis")
            db.session.commit()
            
            keywords = context.get_keywords()
            assert len(keywords) == 3
            assert "financial" in keywords
            assert "revenue" in keywords
            assert "analysis" in keywords


class TestCollaborationModels:
    """Test cases for collaboration models."""
    
    def test_comment_creation(self, app, test_user):
        """Test comment creation."""
        with app.app_context():
            decision = Decision(
                user_id=test_user.id,
                title="Comment Test Decision",
                context="Testing comments",
                decision="Test decision",
                rationale="Test rationale",
                executive_type=ExecutiveType.CEO
            )
            
            db.session.add(decision)
            db.session.commit()
            
            comment = Comment(
                decision_id=decision.id,
                user_id=test_user.id,
                content="This is a test comment"
            )
            
            db.session.add(comment)
            db.session.commit()
            
            assert comment.id is not None
            assert comment.decision_id == decision.id
            assert comment.user_id == test_user.id
            assert comment.content == "This is a test comment"
            assert not comment.is_edited
            assert not comment.is_deleted
    
    def test_comment_editing(self, app, test_user):
        """Test comment editing functionality."""
        with app.app_context():
            decision = Decision(
                user_id=test_user.id,
                title="Edit Test Decision",
                context="Testing comment editing",
                decision="Test decision",
                rationale="Test rationale",
                executive_type=ExecutiveType.CTO
            )
            
            db.session.add(decision)
            db.session.commit()
            
            comment = Comment(
                decision_id=decision.id,
                user_id=test_user.id,
                content="Original comment content"
            )
            
            db.session.add(comment)
            db.session.commit()
            
            # Edit the comment
            comment.edit_content("Updated comment content")
            db.session.commit()
            
            assert comment.content == "Updated comment content"
            assert comment.is_edited
            
            edit_history = comment.get_edit_history()
            assert len(edit_history) == 1
            assert edit_history[0]["content"] == "Original comment content"
    
    def test_threaded_comments(self, app, test_user, test_user2):
        """Test threaded comment functionality."""
        with app.app_context():
            decision = Decision(
                user_id=test_user.id,
                title="Thread Test Decision",
                context="Testing threaded comments",
                decision="Test decision",
                rationale="Test rationale",
                executive_type=ExecutiveType.CFO
            )
            
            db.session.add(decision)
            db.session.commit()
            
            # Create parent comment
            parent_comment = Comment(
                decision_id=decision.id,
                user_id=test_user.id,
                content="Parent comment"
            )
            
            db.session.add(parent_comment)
            db.session.commit()
            
            # Create reply
            reply_comment = Comment(
                decision_id=decision.id,
                user_id=test_user2.id,
                content="Reply to parent comment",
                parent_id=parent_comment.id
            )
            
            db.session.add(reply_comment)
            db.session.commit()
            
            assert reply_comment.parent_id == parent_comment.id
            assert len(parent_comment.replies) == 1
            assert parent_comment.get_reply_count() == 1
    
    def test_collaboration_session(self, app, test_user, test_user2):
        """Test collaboration session functionality."""
        with app.app_context():
            decision = Decision(
                user_id=test_user.id,
                title="Collaboration Test Decision",
                context="Testing collaboration",
                decision="Test decision",
                rationale="Test rationale",
                executive_type=ExecutiveType.CEO
            )
            
            db.session.add(decision)
            db.session.commit()
            
            # Create collaboration session
            session = CollaborationSession(
                decision_id=decision.id,
                created_by=test_user.id,
                title="Test Collaboration Session",
                description="Testing collaboration features"
            )
            
            db.session.add(session)
            db.session.commit()
            
            assert session.id is not None
            assert session.decision_id == decision.id
            assert session.created_by == test_user.id
            assert session.is_active
            
            # Add participant
            participant = session.add_participant(
                user_id=test_user2.id,
                role=CollaborationRole.EDITOR,
                invited_by=test_user.id
            )
            
            db.session.commit()
            
            assert participant is not None
            assert len(session.get_active_participants()) == 1
            
            # End session
            session.end_session()
            db.session.commit()
            
            assert not session.is_active
            assert session.ended_at is not None
    
    def test_notification_creation(self, app, test_user):
        """Test notification creation."""
        with app.app_context():
            decision = Decision(
                user_id=test_user.id,
                title="Notification Test Decision",
                context="Testing notifications",
                decision="Test decision",
                rationale="Test rationale",
                executive_type=ExecutiveType.CEO
            )
            
            db.session.add(decision)
            db.session.commit()
            
            notification = Notification(
                user_id=test_user.id,
                notification_type=NotificationType.DECISION_CREATED,
                title="New Decision Created",
                message="A new decision has been created",
                decision_id=decision.id
            )
            
            db.session.add(notification)
            db.session.commit()
            
            assert notification.id is not None
            assert notification.type == NotificationType.DECISION_CREATED
            assert notification.status == NotificationStatus.UNREAD
            assert notification.decision_id == decision.id
            
            # Mark as read
            notification.mark_as_read()
            db.session.commit()
            
            assert notification.status == NotificationStatus.READ
            assert notification.read_at is not None


class TestModelValidation:
    """Test model validation and constraints."""
    
    def test_decision_required_fields(self, app, test_user):
        """Test that required fields are enforced."""
        with app.app_context():
            # Test missing title
            with pytest.raises(Exception):
                decision = Decision(
                    user_id=test_user.id,
                    # title missing
                    context="Test context",
                    decision="Test decision",
                    rationale="Test rationale",
                    executive_type=ExecutiveType.CEO
                )
                db.session.add(decision)
                db.session.commit()
    
    def test_document_hash_uniqueness(self, app, test_user):
        """Test that content hash can be used for deduplication."""
        with app.app_context():
            # Create first document
            doc1 = Document(
                user_id=test_user.id,
                filename="doc1.pdf",
                original_filename="Document 1.pdf",
                file_type="pdf",
                file_size=100000,
                file_path="/uploads/doc1.pdf",
                content_hash="same_hash_123"
            )
            
            db.session.add(doc1)
            db.session.commit()
            
            # Find by hash
            found_doc = Document.find_by_hash("same_hash_123")
            assert found_doc is not None
            assert found_doc.id == doc1.id
    
    def test_collaboration_participant_uniqueness(self, app, test_user, test_user2):
        """Test that a user can only be added once to a collaboration session."""
        with app.app_context():
            decision = Decision(
                user_id=test_user.id,
                title="Uniqueness Test Decision",
                context="Testing uniqueness",
                decision="Test decision",
                rationale="Test rationale",
                executive_type=ExecutiveType.CEO
            )
            
            db.session.add(decision)
            db.session.commit()
            
            session = CollaborationSession(
                decision_id=decision.id,
                created_by=test_user.id
            )
            
            db.session.add(session)
            db.session.commit()
            
            # Add participant first time
            participant1 = session.add_participant(test_user2.id)
            db.session.commit()
            
            # Try to add same participant again
            participant2 = session.add_participant(test_user2.id)
            
            # Should return existing participant, not create new one
            assert participant1.id == participant2.id


if __name__ == '__main__':
    pytest.main([__file__])