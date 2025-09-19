"""
Test data factories using factory_boy for AI Executive Suite
"""

import factory
from datetime import datetime, timedelta
from decimal import Decimal
from factory import fuzzy
import random

from models import User, Decision, Document, Comment, CollaborationSession


class UserFactory(factory.Factory):
    """Factory for creating User instances"""
    
    class Meta:
        model = User
    
    username = factory.Sequence(lambda n: f'user{n}')
    email = factory.LazyAttribute(lambda obj: f'{obj.username}@example.com')
    password_hash = factory.LazyFunction(lambda: 'hashed_password_123')
    is_active = True
    created_at = factory.LazyFunction(datetime.utcnow)
    last_login = factory.LazyFunction(lambda: datetime.utcnow() - timedelta(hours=1))
    
    # MFA fields
    mfa_enabled = False
    mfa_secret = None
    backup_codes = factory.LazyFunction(lambda: [])
    
    # Profile fields
    full_name = factory.LazyAttribute(lambda obj: f'Full Name {obj.username}')
    company = factory.Faker('company')
    role = factory.Faker('job')
    timezone = 'UTC'
    preferences = factory.LazyFunction(lambda: {
        'theme': 'light',
        'notifications': True,
        'language': 'en'
    })


class DecisionFactory(factory.Factory):
    """Factory for creating Decision instances"""
    
    class Meta:
        model = Decision
    
    user_id = factory.SubFactory(UserFactory)
    executive_type = fuzzy.FuzzyChoice(['ceo', 'cto', 'cfo'])
    title = factory.Faker('sentence', nb_words=4)
    context = factory.Faker('text', max_nb_chars=500)
    decision = factory.Faker('text', max_nb_chars=300)
    rationale = factory.Faker('text', max_nb_chars=400)
    
    confidence_score = fuzzy.FuzzyFloat(0.5, 1.0)
    priority = fuzzy.FuzzyChoice(['low', 'medium', 'high'])
    category = fuzzy.FuzzyChoice(['strategic', 'operational', 'financial', 'technical'])
    status = fuzzy.FuzzyChoice(['pending', 'in_progress', 'completed', 'cancelled'])
    
    financial_impact = factory.LazyFunction(
        lambda: Decimal(str(random.randint(1000, 100000)))
    )
    risk_level = fuzzy.FuzzyChoice(['low', 'medium', 'high'])
    
    implementation_notes = factory.Faker('text', max_nb_chars=200)
    outcome_rating = fuzzy.FuzzyInteger(1, 5)
    effectiveness_score = fuzzy.FuzzyFloat(0.0, 1.0)
    
    created_at = factory.LazyFunction(
        lambda: datetime.utcnow() - timedelta(days=random.randint(0, 30))
    )
    updated_at = factory.LazyAttribute(lambda obj: obj.created_at + timedelta(hours=1))
    implemented_at = factory.LazyAttribute(
        lambda obj: obj.created_at + timedelta(days=random.randint(1, 7)) 
        if obj.status == 'completed' else None
    )
    reviewed_at = factory.LazyAttribute(
        lambda obj: obj.implemented_at + timedelta(days=1) 
        if obj.implemented_at else None
    )
    
    # AI Context
    conversation_history = factory.LazyFunction(lambda: [
        {
            'role': 'user',
            'content': 'What should we do about this situation?',
            'timestamp': datetime.utcnow().isoformat()
        },
        {
            'role': 'assistant',
            'content': 'Based on the analysis, I recommend...',
            'timestamp': datetime.utcnow().isoformat()
        }
    ])
    ai_model_version = 'gpt-4'
    prompt_version = '1.0'


class DocumentFactory(factory.Factory):
    """Factory for creating Document instances"""
    
    class Meta:
        model = Document
    
    user_id = factory.SubFactory(UserFactory)
    filename = factory.LazyFunction(
        lambda: f'document_{random.randint(1000, 9999)}.pdf'
    )
    file_type = fuzzy.FuzzyChoice(['pdf', 'docx', 'xlsx', 'txt'])
    file_size = fuzzy.FuzzyInteger(1024, 10 * 1024 * 1024)  # 1KB to 10MB
    content_hash = factory.LazyFunction(
        lambda: f'hash_{random.randint(100000, 999999)}'
    )
    
    extracted_text = factory.Faker('text', max_nb_chars=2000)
    summary = factory.Faker('text', max_nb_chars=300)
    key_insights = factory.LazyFunction(lambda: [
        f'Key insight {i+1}: {factory.Faker("sentence").generate()}'
        for i in range(random.randint(2, 5))
    ])
    
    document_type = fuzzy.FuzzyChoice(['financial', 'technical', 'strategic', 'legal'])
    sensitivity_level = fuzzy.FuzzyChoice(['public', 'internal', 'confidential', 'restricted'])
    
    embedding_id = factory.LazyFunction(
        lambda: f'embedding_{random.randint(100000, 999999)}'
    )
    
    created_at = factory.LazyFunction(
        lambda: datetime.utcnow() - timedelta(days=random.randint(0, 90))
    )
    processed_at = factory.LazyAttribute(
        lambda obj: obj.created_at + timedelta(minutes=random.randint(1, 60))
    )
    last_accessed = factory.LazyAttribute(
        lambda obj: obj.processed_at + timedelta(days=random.randint(0, 30))
    )
    
    reference_count = fuzzy.FuzzyInteger(0, 20)
    decisions_referenced = factory.LazyFunction(lambda: [])


class CommentFactory(factory.Factory):
    """Factory for creating Comment instances"""
    
    class Meta:
        model = Comment
    
    decision_id = factory.SubFactory(DecisionFactory)
    user_id = factory.SubFactory(UserFactory)
    content = factory.Faker('text', max_nb_chars=500)
    
    created_at = factory.LazyFunction(
        lambda: datetime.utcnow() - timedelta(hours=random.randint(1, 48))
    )
    updated_at = factory.LazyAttribute(lambda obj: obj.created_at)
    
    # Threading support
    parent_comment_id = None
    thread_level = 0
    
    # Metadata
    metadata = factory.LazyFunction(lambda: {
        'edited': False,
        'mentions': [],
        'attachments': []
    })


class CollaborationSessionFactory(factory.Factory):
    """Factory for creating CollaborationSession instances"""
    
    class Meta:
        model = CollaborationSession
    
    decision_id = factory.SubFactory(DecisionFactory)
    owner_id = factory.SubFactory(UserFactory)
    title = factory.LazyAttribute(
        lambda obj: f'Collaboration on {obj.decision_id.title}'
    )
    description = factory.Faker('text', max_nb_chars=300)
    
    status = fuzzy.FuzzyChoice(['active', 'completed', 'cancelled'])
    
    created_at = factory.LazyFunction(
        lambda: datetime.utcnow() - timedelta(days=random.randint(0, 14))
    )
    updated_at = factory.LazyAttribute(lambda obj: obj.created_at)
    completed_at = factory.LazyAttribute(
        lambda obj: obj.created_at + timedelta(days=random.randint(1, 7))
        if obj.status == 'completed' else None
    )
    
    # Collaboration settings
    permissions = factory.LazyFunction(lambda: {
        'can_comment': True,
        'can_edit': False,
        'can_approve': False
    })
    
    # Participants (will be set separately)
    participants = factory.LazyFunction(lambda: [])
    
    # Workflow settings
    requires_approval = False
    approval_threshold = 1
    
    # Metadata
    metadata = factory.LazyFunction(lambda: {
        'notification_settings': {
            'email': True,
            'in_app': True
        },
        'workflow_stage': 'discussion'
    })


# Specialized factories for different scenarios

class HighPriorityDecisionFactory(DecisionFactory):
    """Factory for high-priority decisions"""
    priority = 'high'
    confidence_score = fuzzy.FuzzyFloat(0.8, 1.0)
    financial_impact = factory.LazyFunction(
        lambda: Decimal(str(random.randint(50000, 500000)))
    )


class CompletedDecisionFactory(DecisionFactory):
    """Factory for completed decisions"""
    status = 'completed'
    implemented_at = factory.LazyFunction(
        lambda: datetime.utcnow() - timedelta(days=random.randint(1, 30))
    )
    outcome_rating = fuzzy.FuzzyInteger(3, 5)
    effectiveness_score = fuzzy.FuzzyFloat(0.6, 1.0)


class FinancialDocumentFactory(DocumentFactory):
    """Factory for financial documents"""
    document_type = 'financial'
    file_type = fuzzy.FuzzyChoice(['pdf', 'xlsx'])
    sensitivity_level = fuzzy.FuzzyChoice(['internal', 'confidential'])
    
    key_insights = factory.LazyFunction(lambda: [
        'Revenue increased by 15% compared to last quarter',
        'Operating expenses are within budget',
        'Cash flow remains positive',
        'ROI on recent investments exceeds expectations'
    ])


class TechnicalDocumentFactory(DocumentFactory):
    """Factory for technical documents"""
    document_type = 'technical'
    file_type = fuzzy.FuzzyChoice(['pdf', 'docx'])
    
    key_insights = factory.LazyFunction(lambda: [
        'System architecture supports current load',
        'Security vulnerabilities identified and patched',
        'Performance optimization opportunities available',
        'Technology stack alignment with industry standards'
    ])


class StrategicDocumentFactory(DocumentFactory):
    """Factory for strategic documents"""
    document_type = 'strategic'
    sensitivity_level = fuzzy.FuzzyChoice(['confidential', 'restricted'])
    
    key_insights = factory.LazyFunction(lambda: [
        'Market expansion opportunities in emerging markets',
        'Competitive advantage through innovation',
        'Strategic partnerships could accelerate growth',
        'Long-term sustainability initiatives required'
    ])


# Batch factories for creating multiple related objects

class DecisionWithCommentsFactory(DecisionFactory):
    """Factory that creates a decision with comments"""
    
    @factory.post_generation
    def comments(self, create, extracted, **kwargs):
        if not create:
            return
        
        if extracted:
            # Create specified number of comments
            for _ in range(extracted):
                CommentFactory(decision_id=self.id)
        else:
            # Create random number of comments (0-5)
            for _ in range(random.randint(0, 5)):
                CommentFactory(decision_id=self.id)


class DecisionWithCollaborationFactory(DecisionFactory):
    """Factory that creates a decision with collaboration session"""
    
    @factory.post_generation
    def collaboration(self, create, extracted, **kwargs):
        if not create:
            return
        
        # Create collaboration session
        CollaborationSessionFactory(
            decision_id=self.id,
            owner_id=self.user_id
        )


class UserWithDecisionsFactory(UserFactory):
    """Factory that creates a user with multiple decisions"""
    
    @factory.post_generation
    def decisions(self, create, extracted, **kwargs):
        if not create:
            return
        
        if extracted:
            # Create specified number of decisions
            for _ in range(extracted):
                DecisionFactory(user_id=self.id)
        else:
            # Create random number of decisions (1-10)
            for _ in range(random.randint(1, 10)):
                DecisionFactory(user_id=self.id)


class UserWithDocumentsFactory(UserFactory):
    """Factory that creates a user with multiple documents"""
    
    @factory.post_generation
    def documents(self, create, extracted, **kwargs):
        if not create:
            return
        
        if extracted:
            # Create specified number of documents
            for _ in range(extracted):
                DocumentFactory(user_id=self.id)
        else:
            # Create random number of documents (1-5)
            for _ in range(random.randint(1, 5)):
                DocumentFactory(user_id=self.id)


# Utility functions for creating test scenarios

def create_test_scenario_basic():
    """Create basic test scenario with user, decisions, and documents"""
    user = UserFactory()
    decisions = [DecisionFactory(user_id=user.id) for _ in range(3)]
    documents = [DocumentFactory(user_id=user.id) for _ in range(2)]
    
    return {
        'user': user,
        'decisions': decisions,
        'documents': documents
    }


def create_test_scenario_collaboration():
    """Create collaboration test scenario"""
    owner = UserFactory()
    collaborators = [UserFactory() for _ in range(3)]
    
    decision = DecisionFactory(user_id=owner.id)
    collaboration = CollaborationSessionFactory(
        decision_id=decision.id,
        owner_id=owner.id
    )
    
    comments = [
        CommentFactory(decision_id=decision.id, user_id=collaborator.id)
        for collaborator in collaborators
    ]
    
    return {
        'owner': owner,
        'collaborators': collaborators,
        'decision': decision,
        'collaboration': collaboration,
        'comments': comments
    }


def create_test_scenario_analytics():
    """Create analytics test scenario with varied data"""
    users = [UserFactory() for _ in range(3)]
    
    decisions = []
    for user in users:
        # Create decisions with different patterns
        for i in range(5):
            decision = DecisionFactory(
                user_id=user.id,
                executive_type=['ceo', 'cto', 'cfo'][i % 3],
                status=['completed', 'in_progress', 'pending'][i % 3],
                priority=['high', 'medium', 'low'][i % 3],
                created_at=datetime.utcnow() - timedelta(days=i * 2)
            )
            decisions.append(decision)
    
    documents = []
    for user in users:
        for doc_type in ['financial', 'technical', 'strategic']:
            document = DocumentFactory(
                user_id=user.id,
                document_type=doc_type
            )
            documents.append(document)
    
    return {
        'users': users,
        'decisions': decisions,
        'documents': documents
    }


def create_test_scenario_performance():
    """Create performance test scenario with large dataset"""
    users = [UserFactory() for _ in range(10)]
    
    decisions = []
    for user in users:
        user_decisions = [
            DecisionFactory(user_id=user.id) 
            for _ in range(random.randint(20, 50))
        ]
        decisions.extend(user_decisions)
    
    documents = []
    for user in users:
        user_documents = [
            DocumentFactory(user_id=user.id)
            for _ in range(random.randint(5, 15))
        ]
        documents.extend(user_documents)
    
    return {
        'users': users,
        'decisions': decisions,
        'documents': documents
    }