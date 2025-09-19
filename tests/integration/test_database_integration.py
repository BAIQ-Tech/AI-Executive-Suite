"""
Database integration tests
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy import text

from models import (
    db, User, Decision, Document, Comment, CollaborationSession,
    DecisionStatus, Priority, RiskLevel
)
from tests.factories import (
    UserFactory, DecisionFactory, DocumentFactory,
    CommentFactory, CollaborationSessionFactory
)


@pytest.mark.integration
class TestDatabaseModels:
    """Test database model operations"""
    
    def test_user_crud_operations(self, db_session):
        """Test User CRUD operations"""
        # Create
        user = User(
            username='testuser',
            email='test@example.com',
            password_hash='hashed_password'
        )
        db_session.add(user)
        db_session.commit()
        
        assert user.id is not None
        assert user.created_at is not None
        
        # Read
        retrieved_user = db_session.query(User).filter_by(username='testuser').first()
        assert retrieved_user is not None
        assert retrieved_user.email == 'test@example.com'
        
        # Update
        retrieved_user.email = 'updated@example.com'
        db_session.commit()
        
        updated_user = db_session.query(User).filter_by(id=user.id).first()
        assert updated_user.email == 'updated@example.com'
        
        # Delete
        db_session.delete(updated_user)
        db_session.commit()
        
        deleted_user = db_session.query(User).filter_by(id=user.id).first()
        assert deleted_user is None
    
    def test_decision_crud_operations(self, db_session, sample_user):
        """Test Decision CRUD operations"""
        # Create
        decision = Decision(
            user_id=sample_user.id,
            executive_type='ceo',
            title='Test Decision',
            context='Test context',
            decision='Test decision content',
            rationale='Test rationale',
            confidence_score=0.8,
            priority='high',
            category='strategic',
            status='pending',
            financial_impact=Decimal('10000'),
            risk_level='medium'
        )
        db_session.add(decision)
        db_session.commit()
        
        assert decision.id is not None
        
        # Read
        retrieved_decision = db_session.query(Decision).filter_by(id=decision.id).first()
        assert retrieved_decision is not None
        assert retrieved_decision.title == 'Test Decision'
        assert retrieved_decision.financial_impact == Decimal('10000')
        
        # Update
        retrieved_decision.status = 'completed'
        retrieved_decision.implemented_at = datetime.utcnow()
        db_session.commit()
        
        updated_decision = db_session.query(Decision).filter_by(id=decision.id).first()
        assert updated_decision.status == 'completed'
        assert updated_decision.implemented_at is not None
        
        # Delete
        db_session.delete(updated_decision)
        db_session.commit()
        
        deleted_decision = db_session.query(Decision).filter_by(id=decision.id).first()
        assert deleted_decision is None
    
    def test_document_crud_operations(self, db_session, sample_user):
        """Test Document CRUD operations"""
        # Create
        document = Document(
            user_id=sample_user.id,
            filename='test.pdf',
            file_type='pdf',
            file_size=1024,
            content_hash='hash123',
            extracted_text='Test content',
            summary='Test summary',
            key_insights=['Insight 1', 'Insight 2'],
            document_type='financial',
            sensitivity_level='internal'
        )
        db_session.add(document)
        db_session.commit()
        
        assert document.id is not None
        
        # Read
        retrieved_document = db_session.query(Document).filter_by(id=document.id).first()
        assert retrieved_document is not None
        assert retrieved_document.filename == 'test.pdf'
        assert retrieved_document.key_insights == ['Insight 1', 'Insight 2']
        
        # Update
        retrieved_document.processed_at = datetime.utcnow()
        retrieved_document.reference_count = 5
        db_session.commit()
        
        updated_document = db_session.query(Document).filter_by(id=document.id).first()
        assert updated_document.processed_at is not None
        assert updated_document.reference_count == 5
        
        # Delete
        db_session.delete(updated_document)
        db_session.commit()
        
        deleted_document = db_session.query(Document).filter_by(id=document.id).first()
        assert deleted_document is None


@pytest.mark.integration
class TestDatabaseRelationships:
    """Test database relationships"""
    
    def test_user_decision_relationship(self, db_session, sample_user):
        """Test User-Decision relationship"""
        # Create decisions for user
        decisions = []
        for i in range(3):
            decision = Decision(
                user_id=sample_user.id,
                executive_type='ceo',
                title=f'Decision {i+1}',
                context=f'Context {i+1}',
                decision=f'Decision content {i+1}',
                rationale=f'Rationale {i+1}'
            )
            decisions.append(decision)
            db_session.add(decision)
        
        db_session.commit()
        
        # Test relationship
        user_decisions = db_session.query(Decision).filter_by(user_id=sample_user.id).all()
        assert len(user_decisions) == 3
        
        # Test reverse relationship (if defined)
        user = db_session.query(User).filter_by(id=sample_user.id).first()
        if hasattr(user, 'decisions'):
            assert len(user.decisions) == 3
    
    def test_decision_comment_relationship(self, db_session, sample_user, sample_decisions):
        """Test Decision-Comment relationship"""
        decision = sample_decisions[0]
        
        # Create comments for decision
        comments = []
        for i in range(2):
            comment = Comment(
                decision_id=decision.id,
                user_id=sample_user.id,
                content=f'Comment {i+1}'
            )
            comments.append(comment)
            db_session.add(comment)
        
        db_session.commit()
        
        # Test relationship
        decision_comments = db_session.query(Comment).filter_by(decision_id=decision.id).all()
        assert len(decision_comments) == 2
        
        # Test reverse relationship (if defined)
        retrieved_decision = db_session.query(Decision).filter_by(id=decision.id).first()
        if hasattr(retrieved_decision, 'comments'):
            assert len(retrieved_decision.comments) == 2
    
    def test_collaboration_session_relationship(self, db_session, sample_user, sample_decisions):
        """Test CollaborationSession relationships"""
        decision = sample_decisions[0]
        
        # Create collaboration session
        session = CollaborationSession(
            decision_id=decision.id,
            owner_id=sample_user.id,
            title='Test Collaboration',
            description='Test collaboration session'
        )
        db_session.add(session)
        db_session.commit()
        
        # Test relationships
        retrieved_session = db_session.query(CollaborationSession).filter_by(id=session.id).first()
        assert retrieved_session.decision_id == decision.id
        assert retrieved_session.owner_id == sample_user.id


@pytest.mark.integration
class TestDatabaseConstraints:
    """Test database constraints and validations"""
    
    def test_user_unique_constraints(self, db_session):
        """Test User unique constraints"""
        # Create first user
        user1 = User(
            username='testuser',
            email='test@example.com',
            password_hash='hash1'
        )
        db_session.add(user1)
        db_session.commit()
        
        # Try to create user with same username
        user2 = User(
            username='testuser',  # Same username
            email='different@example.com',
            password_hash='hash2'
        )
        db_session.add(user2)
        
        with pytest.raises(Exception):  # Should raise integrity error
            db_session.commit()
        
        db_session.rollback()
        
        # Try to create user with same email
        user3 = User(
            username='differentuser',
            email='test@example.com',  # Same email
            password_hash='hash3'
        )
        db_session.add(user3)
        
        with pytest.raises(Exception):  # Should raise integrity error
            db_session.commit()
    
    def test_foreign_key_constraints(self, db_session):
        """Test foreign key constraints"""
        # Try to create decision with non-existent user
        decision = Decision(
            user_id=99999,  # Non-existent user ID
            executive_type='ceo',
            title='Test Decision',
            context='Test context',
            decision='Test decision',
            rationale='Test rationale'
        )
        db_session.add(decision)
        
        with pytest.raises(Exception):  # Should raise foreign key error
            db_session.commit()
    
    def test_not_null_constraints(self, db_session, sample_user):
        """Test NOT NULL constraints"""
        # Try to create decision without required fields
        decision = Decision(
            user_id=sample_user.id,
            executive_type='ceo'
            # Missing required fields: title, context, decision, rationale
        )
        db_session.add(decision)
        
        with pytest.raises(Exception):  # Should raise not null error
            db_session.commit()


@pytest.mark.integration
class TestDatabaseQueries:
    """Test complex database queries"""
    
    def test_decision_filtering_queries(self, db_session, sample_user):
        """Test decision filtering queries"""
        # Create test decisions with different attributes
        decisions_data = [
            {'executive_type': 'ceo', 'priority': 'high', 'status': 'completed', 'category': 'strategic'},
            {'executive_type': 'cto', 'priority': 'medium', 'status': 'pending', 'category': 'technical'},
            {'executive_type': 'cfo', 'priority': 'high', 'status': 'completed', 'category': 'financial'},
            {'executive_type': 'ceo', 'priority': 'low', 'status': 'pending', 'category': 'operational'},
        ]
        
        for i, data in enumerate(decisions_data):
            decision = Decision(
                user_id=sample_user.id,
                title=f'Decision {i+1}',
                context=f'Context {i+1}',
                decision=f'Decision content {i+1}',
                rationale=f'Rationale {i+1}',
                **data
            )
            db_session.add(decision)
        
        db_session.commit()
        
        # Test filtering by executive type
        ceo_decisions = db_session.query(Decision).filter_by(
            user_id=sample_user.id,
            executive_type='ceo'
        ).all()
        assert len(ceo_decisions) == 2
        
        # Test filtering by priority
        high_priority = db_session.query(Decision).filter_by(
            user_id=sample_user.id,
            priority='high'
        ).all()
        assert len(high_priority) == 2
        
        # Test filtering by status
        completed = db_session.query(Decision).filter_by(
            user_id=sample_user.id,
            status='completed'
        ).all()
        assert len(completed) == 2
        
        # Test complex filtering
        ceo_high_priority = db_session.query(Decision).filter_by(
            user_id=sample_user.id,
            executive_type='ceo',
            priority='high'
        ).all()
        assert len(ceo_high_priority) == 1
    
    def test_decision_aggregation_queries(self, db_session, sample_user):
        """Test decision aggregation queries"""
        # Create test decisions with different confidence scores
        confidence_scores = [0.9, 0.8, 0.7, 0.6, 0.5]
        
        for i, score in enumerate(confidence_scores):
            decision = Decision(
                user_id=sample_user.id,
                executive_type='ceo',
                title=f'Decision {i+1}',
                context=f'Context {i+1}',
                decision=f'Decision content {i+1}',
                rationale=f'Rationale {i+1}',
                confidence_score=score
            )
            db_session.add(decision)
        
        db_session.commit()
        
        # Test count query
        count = db_session.query(Decision).filter_by(user_id=sample_user.id).count()
        assert count == 5
        
        # Test average confidence score
        from sqlalchemy import func
        avg_confidence = db_session.query(
            func.avg(Decision.confidence_score)
        ).filter_by(user_id=sample_user.id).scalar()
        
        assert abs(avg_confidence - 0.7) < 0.01  # Average of 0.9, 0.8, 0.7, 0.6, 0.5
        
        # Test max/min confidence scores
        max_confidence = db_session.query(
            func.max(Decision.confidence_score)
        ).filter_by(user_id=sample_user.id).scalar()
        assert max_confidence == 0.9
        
        min_confidence = db_session.query(
            func.min(Decision.confidence_score)
        ).filter_by(user_id=sample_user.id).scalar()
        assert min_confidence == 0.5
    
    def test_date_range_queries(self, db_session, sample_user):
        """Test date range queries"""
        now = datetime.utcnow()
        
        # Create decisions with different creation dates
        dates = [
            now - timedelta(days=1),
            now - timedelta(days=7),
            now - timedelta(days=15),
            now - timedelta(days=30),
            now - timedelta(days=60)
        ]
        
        for i, date in enumerate(dates):
            decision = Decision(
                user_id=sample_user.id,
                executive_type='ceo',
                title=f'Decision {i+1}',
                context=f'Context {i+1}',
                decision=f'Decision content {i+1}',
                rationale=f'Rationale {i+1}',
                created_at=date
            )
            db_session.add(decision)
        
        db_session.commit()
        
        # Test last 7 days
        week_ago = now - timedelta(days=7)
        recent_decisions = db_session.query(Decision).filter(
            Decision.user_id == sample_user.id,
            Decision.created_at >= week_ago
        ).all()
        assert len(recent_decisions) == 2  # 1 day and 7 days ago
        
        # Test last 30 days
        month_ago = now - timedelta(days=30)
        monthly_decisions = db_session.query(Decision).filter(
            Decision.user_id == sample_user.id,
            Decision.created_at >= month_ago
        ).all()
        assert len(monthly_decisions) == 4  # All except 60 days ago
        
        # Test specific date range
        start_date = now - timedelta(days=20)
        end_date = now - timedelta(days=10)
        range_decisions = db_session.query(Decision).filter(
            Decision.user_id == sample_user.id,
            Decision.created_at >= start_date,
            Decision.created_at <= end_date
        ).all()
        assert len(range_decisions) == 1  # Only 15 days ago


@pytest.mark.integration
class TestDatabaseTransactions:
    """Test database transaction handling"""
    
    def test_transaction_rollback(self, db_session, sample_user):
        """Test transaction rollback on error"""
        initial_count = db_session.query(Decision).filter_by(user_id=sample_user.id).count()
        
        try:
            # Create valid decision
            decision1 = Decision(
                user_id=sample_user.id,
                executive_type='ceo',
                title='Valid Decision',
                context='Valid context',
                decision='Valid decision',
                rationale='Valid rationale'
            )
            db_session.add(decision1)
            
            # Create invalid decision (this should cause an error)
            decision2 = Decision(
                user_id=99999,  # Non-existent user
                executive_type='ceo',
                title='Invalid Decision',
                context='Invalid context',
                decision='Invalid decision',
                rationale='Invalid rationale'
            )
            db_session.add(decision2)
            
            db_session.commit()
        except Exception:
            db_session.rollback()
        
        # Verify that no decisions were added due to rollback
        final_count = db_session.query(Decision).filter_by(user_id=sample_user.id).count()
        assert final_count == initial_count
    
    def test_transaction_commit(self, db_session, sample_user):
        """Test successful transaction commit"""
        initial_count = db_session.query(Decision).filter_by(user_id=sample_user.id).count()
        
        # Create multiple valid decisions
        decisions = []
        for i in range(3):
            decision = Decision(
                user_id=sample_user.id,
                executive_type='ceo',
                title=f'Decision {i+1}',
                context=f'Context {i+1}',
                decision=f'Decision content {i+1}',
                rationale=f'Rationale {i+1}'
            )
            decisions.append(decision)
            db_session.add(decision)
        
        db_session.commit()
        
        # Verify all decisions were added
        final_count = db_session.query(Decision).filter_by(user_id=sample_user.id).count()
        assert final_count == initial_count + 3


@pytest.mark.integration
class TestDatabasePerformance:
    """Test database performance with larger datasets"""
    
    def test_bulk_insert_performance(self, db_session, sample_user):
        """Test bulk insert performance"""
        import time
        
        start_time = time.time()
        
        # Create 100 decisions
        decisions = []
        for i in range(100):
            decision = Decision(
                user_id=sample_user.id,
                executive_type=['ceo', 'cto', 'cfo'][i % 3],
                title=f'Bulk Decision {i+1}',
                context=f'Bulk context {i+1}',
                decision=f'Bulk decision content {i+1}',
                rationale=f'Bulk rationale {i+1}',
                confidence_score=0.5 + (i % 5) * 0.1,
                priority=['low', 'medium', 'high'][i % 3],
                category=['strategic', 'operational', 'financial'][i % 3]
            )
            decisions.append(decision)
        
        db_session.add_all(decisions)
        db_session.commit()
        
        end_time = time.time()
        insert_time = end_time - start_time
        
        # Verify all decisions were inserted
        count = db_session.query(Decision).filter_by(user_id=sample_user.id).count()
        assert count == 100
        
        # Performance should be reasonable (less than 5 seconds for 100 records)
        assert insert_time < 5.0
    
    def test_query_performance_with_indexes(self, db_session, sample_user):
        """Test query performance with indexed columns"""
        import time
        
        # First create a larger dataset
        decisions = []
        for i in range(1000):
            decision = Decision(
                user_id=sample_user.id,
                executive_type=['ceo', 'cto', 'cfo'][i % 3],
                title=f'Performance Decision {i+1}',
                context=f'Performance context {i+1}',
                decision=f'Performance decision content {i+1}',
                rationale=f'Performance rationale {i+1}',
                created_at=datetime.utcnow() - timedelta(days=i % 365)
            )
            decisions.append(decision)
        
        db_session.add_all(decisions)
        db_session.commit()
        
        # Test query performance
        start_time = time.time()
        
        # Query by user_id (should be indexed)
        user_decisions = db_session.query(Decision).filter_by(user_id=sample_user.id).all()
        
        end_time = time.time()
        query_time = end_time - start_time
        
        assert len(user_decisions) == 1000
        # Query should be fast (less than 1 second)
        assert query_time < 1.0


@pytest.mark.integration
class TestDatabaseMigrations:
    """Test database migration scenarios"""
    
    def test_schema_compatibility(self, db_session):
        """Test that current schema is compatible with expected structure"""
        # Test that all expected tables exist
        inspector = db.inspect(db.engine)
        tables = inspector.get_table_names()
        
        expected_tables = ['users', 'decisions', 'documents', 'comments', 'collaboration_sessions']
        for table in expected_tables:
            assert table in tables, f"Table {table} not found in database"
        
        # Test that expected columns exist in users table
        user_columns = [col['name'] for col in inspector.get_columns('users')]
        expected_user_columns = ['id', 'username', 'email', 'password_hash', 'created_at']
        for column in expected_user_columns:
            assert column in user_columns, f"Column {column} not found in users table"
        
        # Test that expected columns exist in decisions table
        decision_columns = [col['name'] for col in inspector.get_columns('decisions')]
        expected_decision_columns = [
            'id', 'user_id', 'executive_type', 'title', 'context', 
            'decision', 'rationale', 'confidence_score', 'created_at'
        ]
        for column in expected_decision_columns:
            assert column in decision_columns, f"Column {column} not found in decisions table"


if __name__ == "__main__":
    pytest.main([__file__])