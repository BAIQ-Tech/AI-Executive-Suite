"""
Pytest configuration and shared fixtures for AI Executive Suite tests
"""

import pytest
import os
import tempfile
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import Mock, MagicMock
from typing import Dict, Any, List

# Set test environment
os.environ['TESTING'] = 'True'
os.environ['DATABASE_URL'] = 'sqlite:///:memory:'

from app import create_app
from models import db, User, Decision, Document, Comment, CollaborationSession
from services.ai_integration import AIIntegrationService
from services.analytics import AnalyticsService
from services.document_processing import DocumentProcessingService
from services.collaboration import CollaborationService


@pytest.fixture(scope='session')
def app():
    """Create application for testing"""
    app = create_app({
        'TESTING': True,
        'DATABASE_URL': 'sqlite:///:memory:',
        'SECRET_KEY': 'test-secret-key',
        'WTF_CSRF_ENABLED': False,
        'OPENAI_API_KEY': 'test-openai-key',
        'REDIS_URL': 'redis://localhost:6379/1'
    })
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


@pytest.fixture
def db_session(app):
    """Create database session for testing"""
    with app.app_context():
        db.create_all()
        yield db.session
        db.session.rollback()
        db.drop_all()


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for testing"""
    mock_client = Mock()
    mock_client.model = 'gpt-4'
    mock_client.max_tokens = 2000
    mock_client.temperature = 0.7
    
    # Mock successful response
    mock_response = Mock()
    mock_response.content = '{"decision": "Test decision", "rationale": "Test rationale", "confidence_score": 0.8, "priority": "high", "category": "strategic", "risk_level": "low"}'
    mock_response.model = 'gpt-4'
    mock_response.token_usage = Mock()
    mock_response.token_usage.prompt_tokens = 100
    mock_response.token_usage.completion_tokens = 50
    mock_response.token_usage.total_tokens = 150
    mock_response.token_usage.estimated_cost = 0.005
    mock_response.response_time = 1.5
    
    mock_client.generate_completion.return_value = mock_response
    mock_client.count_tokens.return_value = 50
    mock_client.count_message_tokens.return_value = 150
    mock_client.calculate_cost.return_value = 0.005
    
    return mock_client


@pytest.fixture
def mock_redis():
    """Mock Redis client for testing"""
    mock_redis = Mock()
    mock_redis.get.return_value = None
    mock_redis.set.return_value = True
    mock_redis.delete.return_value = True
    mock_redis.exists.return_value = False
    mock_redis.expire.return_value = True
    return mock_redis


@pytest.fixture
def mock_vector_db():
    """Mock vector database for testing"""
    mock_vector_db = Mock()
    mock_vector_db.add_documents.return_value = True
    mock_vector_db.search.return_value = [
        {'content': 'Test document content', 'score': 0.9, 'metadata': {'id': 'doc1'}},
        {'content': 'Another document', 'score': 0.8, 'metadata': {'id': 'doc2'}}
    ]
    mock_vector_db.delete_document.return_value = True
    return mock_vector_db


@pytest.fixture
def sample_user(db_session):
    """Create a sample user for testing"""
    user = User(
        username='testuser',
        email='test@example.com',
        password_hash='hashed_password'
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def sample_decisions(db_session, sample_user):
    """Create sample decisions for testing"""
    decisions = []
    
    for i in range(5):
        decision = Decision(
            user_id=sample_user.id,
            executive_type=f'ceo' if i % 3 == 0 else ('cto' if i % 3 == 1 else 'cfo'),
            title=f'Test Decision {i+1}',
            context=f'Test context for decision {i+1}',
            decision=f'Test decision content {i+1}',
            rationale=f'Test rationale {i+1}',
            confidence_score=0.7 + (i * 0.05),
            priority='high' if i < 2 else ('medium' if i < 4 else 'low'),
            category='strategic' if i % 2 == 0 else 'operational',
            status='completed' if i < 3 else 'pending',
            financial_impact=Decimal(str(1000 * (i + 1))),
            risk_level='low' if i < 2 else ('medium' if i < 4 else 'high'),
            created_at=datetime.utcnow() - timedelta(days=i),
            ai_model_version='gpt-4',
            prompt_version='1.0'
        )
        decisions.append(decision)
        db_session.add(decision)
    
    db_session.commit()
    return decisions


@pytest.fixture
def sample_documents(db_session, sample_user):
    """Create sample documents for testing"""
    documents = []
    
    for i in range(3):
        document = Document(
            user_id=sample_user.id,
            filename=f'test_document_{i+1}.pdf',
            file_type='pdf',
            file_size=1024 * (i + 1),
            content_hash=f'hash_{i+1}',
            extracted_text=f'This is the extracted text from document {i+1}',
            summary=f'Summary of document {i+1}',
            key_insights=[f'Insight {i+1}.1', f'Insight {i+1}.2'],
            document_type='financial' if i == 0 else ('technical' if i == 1 else 'strategic'),
            sensitivity_level='internal',
            embedding_id=f'embedding_{i+1}',
            created_at=datetime.utcnow() - timedelta(days=i),
            processed_at=datetime.utcnow() - timedelta(days=i, hours=1),
            reference_count=i + 1
        )
        documents.append(document)
        db_session.add(document)
    
    db_session.commit()
    return documents


@pytest.fixture
def temp_file():
    """Create temporary file for testing file uploads"""
    with tempfile.NamedTemporaryFile(mode='w+', suffix='.txt', delete=False) as f:
        f.write('This is test file content for upload testing.')
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    try:
        os.unlink(temp_path)
    except OSError:
        pass


@pytest.fixture
def mock_external_api():
    """Mock external API responses"""
    mock_api = Mock()
    
    # CRM API responses
    mock_api.get_crm_data.return_value = {
        'contacts': [
            {'id': '1', 'name': 'John Doe', 'email': 'john@example.com'},
            {'id': '2', 'name': 'Jane Smith', 'email': 'jane@example.com'}
        ],
        'deals': [
            {'id': '1', 'value': 10000, 'stage': 'negotiation'},
            {'id': '2', 'value': 25000, 'stage': 'closed-won'}
        ]
    }
    
    # ERP API responses
    mock_api.get_erp_data.return_value = {
        'financial_data': {
            'revenue': 1000000,
            'expenses': 750000,
            'profit': 250000
        },
        'inventory': [
            {'item': 'Product A', 'quantity': 100, 'value': 5000},
            {'item': 'Product B', 'quantity': 50, 'value': 7500}
        ]
    }
    
    # Financial API responses
    mock_api.get_financial_data.return_value = {
        'stock_price': 150.25,
        'market_cap': 50000000,
        'pe_ratio': 18.5,
        'industry_avg_pe': 20.2
    }
    
    return mock_api


class MockServiceFactory:
    """Factory for creating mock services"""
    
    @staticmethod
    def create_ai_service(config=None):
        """Create mock AI integration service"""
        if config is None:
            config = {
                'openai': {
                    'api_key': 'test-key',
                    'model': 'gpt-4',
                    'max_tokens': 2000,
                    'temperature': 0.7
                }
            }
        
        service = Mock(spec=AIIntegrationService)
        service.config = config
        service.total_tokens_used = 0
        service.total_cost = 0.0
        
        # Mock successful response
        mock_response = Mock()
        mock_response.decision = 'Test decision'
        mock_response.rationale = 'Test rationale'
        mock_response.confidence_score = 0.8
        mock_response.priority = 'high'
        mock_response.category = 'strategic'
        mock_response.risk_level = 'low'
        mock_response.executive_type = 'ceo'
        mock_response.metadata = {}
        
        service.generate_executive_response.return_value = mock_response
        
        return service
    
    @staticmethod
    def create_analytics_service(config=None, db=None):
        """Create mock analytics service"""
        if config is None:
            config = {
                'analytics': {
                    'default_interval_days': 7,
                    'trend_confidence_threshold': 0.7
                }
            }
        
        service = Mock(spec=AnalyticsService)
        service.config = config
        service.db = db
        
        return service
    
    @staticmethod
    def create_document_service(config=None):
        """Create mock document processing service"""
        if config is None:
            config = {
                'document_processing': {
                    'max_file_size': 10 * 1024 * 1024,  # 10MB
                    'allowed_extensions': ['.pdf', '.docx', '.txt', '.xlsx']
                }
            }
        
        service = Mock(spec=DocumentProcessingService)
        service.config = config
        
        return service
    
    @staticmethod
    def create_collaboration_service(config=None, db=None):
        """Create mock collaboration service"""
        if config is None:
            config = {
                'collaboration': {
                    'max_collaborators': 10,
                    'notification_enabled': True
                }
            }
        
        service = Mock(spec=CollaborationService)
        service.config = config
        service.db = db
        
        return service


@pytest.fixture
def mock_service_factory():
    """Provide mock service factory"""
    return MockServiceFactory


# Test data generators
class TestDataGenerator:
    """Generate test data for various scenarios"""
    
    @staticmethod
    def generate_decision_data(count=5, user_id=1):
        """Generate decision test data"""
        decisions = []
        
        for i in range(count):
            decision_data = {
                'user_id': user_id,
                'executive_type': ['ceo', 'cto', 'cfo'][i % 3],
                'title': f'Test Decision {i+1}',
                'context': f'Context for decision {i+1}',
                'decision': f'Decision content {i+1}',
                'rationale': f'Rationale {i+1}',
                'confidence_score': 0.6 + (i * 0.08),
                'priority': ['high', 'medium', 'low'][i % 3],
                'category': ['strategic', 'operational', 'financial'][i % 3],
                'status': ['pending', 'in_progress', 'completed'][i % 3],
                'financial_impact': Decimal(str(1000 * (i + 1))),
                'risk_level': ['low', 'medium', 'high'][i % 3],
                'created_at': datetime.utcnow() - timedelta(days=i),
                'ai_model_version': 'gpt-4',
                'prompt_version': '1.0'
            }
            decisions.append(decision_data)
        
        return decisions
    
    @staticmethod
    def generate_document_data(count=3, user_id=1):
        """Generate document test data"""
        documents = []
        
        for i in range(count):
            document_data = {
                'user_id': user_id,
                'filename': f'test_doc_{i+1}.pdf',
                'file_type': 'pdf',
                'file_size': 1024 * (i + 1),
                'content_hash': f'hash_{i+1}',
                'extracted_text': f'Extracted text from document {i+1}',
                'summary': f'Document {i+1} summary',
                'key_insights': [f'Insight {i+1}.1', f'Insight {i+1}.2'],
                'document_type': ['financial', 'technical', 'strategic'][i % 3],
                'sensitivity_level': 'internal',
                'embedding_id': f'embedding_{i+1}',
                'created_at': datetime.utcnow() - timedelta(days=i),
                'processed_at': datetime.utcnow() - timedelta(days=i, hours=1),
                'reference_count': i + 1
            }
            documents.append(document_data)
        
        return documents
    
    @staticmethod
    def generate_financial_data():
        """Generate financial test data"""
        return {
            'revenue': {
                'total_revenue': 1000000,
                'recurring_revenue': 800000,
                'one_time_revenue': 200000
            },
            'costs': {
                'total_costs': 600000,
                'operating_costs': 500000,
                'capital_costs': 100000
            },
            'assets': {
                'total_assets': 2000000,
                'current_assets': 800000,
                'fixed_assets': 1200000
            },
            'liabilities': {
                'total_liabilities': 800000,
                'current_liabilities': 300000,
                'long_term_liabilities': 500000
            },
            'previous_revenue': 900000,
            'previous_costs': 550000
        }


@pytest.fixture
def test_data_generator():
    """Provide test data generator"""
    return TestDataGenerator


# Performance testing utilities
@pytest.fixture
def performance_timer():
    """Timer for performance testing"""
    import time
    
    class Timer:
        def __init__(self):
            self.start_time = None
            self.end_time = None
        
        def start(self):
            self.start_time = time.time()
        
        def stop(self):
            self.end_time = time.time()
            return self.elapsed_time
        
        @property
        def elapsed_time(self):
            if self.start_time and self.end_time:
                return self.end_time - self.start_time
            return None
    
    return Timer()


# Security testing utilities
@pytest.fixture
def security_test_data():
    """Provide security test data"""
    return {
        'sql_injection_payloads': [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "' UNION SELECT * FROM users --",
            "'; INSERT INTO users VALUES ('hacker', 'password'); --"
        ],
        'xss_payloads': [
            "<script>alert('XSS')</script>",
            "javascript:alert('XSS')",
            "<img src=x onerror=alert('XSS')>",
            "';alert('XSS');//"
        ],
        'path_traversal_payloads': [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "....//....//....//etc/passwd",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd"
        ],
        'command_injection_payloads': [
            "; ls -la",
            "| cat /etc/passwd",
            "&& whoami",
            "`id`"
        ]
    }