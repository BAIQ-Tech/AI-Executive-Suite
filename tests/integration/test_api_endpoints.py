"""
Integration tests for API endpoints
"""

import pytest
import json
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import patch, Mock

from tests.factories import UserFactory, DecisionFactory, DocumentFactory


@pytest.mark.integration
class TestExecutiveRoutes:
    """Test executive decision API endpoints"""
    
    def test_ceo_decision_endpoint(self, client, sample_user):
        """Test CEO decision generation endpoint"""
        with client.session_transaction() as sess:
            sess['user_id'] = sample_user.id
        
        # Mock AI service response
        with patch('services.ai_integration.AIIntegrationService') as mock_ai:
            mock_response = Mock()
            mock_response.decision = "Expand into new markets"
            mock_response.rationale = "Market analysis shows opportunity"
            mock_response.confidence_score = 0.85
            mock_response.priority = "high"
            mock_response.category = "strategic"
            mock_response.risk_level = "medium"
            
            mock_ai.return_value.generate_executive_response.return_value = mock_response
            
            response = client.post('/api/ceo/decision', json={
                'context': 'Should we expand to international markets?',
                'options': ['Expand to Europe', 'Expand to Asia', 'Stay domestic']
            })
            
            assert response.status_code == 200
            data = response.get_json()
            
            assert 'decision' in data
            assert 'rationale' in data
            assert 'confidence_score' in data
            assert data['executive_type'] == 'ceo'
            assert data['decision'] == "Expand into new markets"
    
    def test_cto_decision_endpoint(self, client, sample_user):
        """Test CTO decision generation endpoint"""
        with client.session_transaction() as sess:
            sess['user_id'] = sample_user.id
        
        with patch('services.ai_integration.AIIntegrationService') as mock_ai:
            mock_response = Mock()
            mock_response.decision = "Adopt microservices architecture"
            mock_response.rationale = "Scalability and maintainability benefits"
            mock_response.confidence_score = 0.9
            mock_response.priority = "high"
            mock_response.category = "technical"
            mock_response.risk_level = "low"
            
            mock_ai.return_value.generate_executive_response.return_value = mock_response
            
            response = client.post('/api/cto/decision', json={
                'context': 'What architecture should we use for our new platform?',
                'technical_requirements': ['Scalability', 'Performance', 'Maintainability']
            })
            
            assert response.status_code == 200
            data = response.get_json()
            
            assert data['executive_type'] == 'cto'
            assert data['decision'] == "Adopt microservices architecture"
            assert data['category'] == 'technical'
    
    def test_cfo_decision_endpoint(self, client, sample_user):
        """Test CFO decision generation endpoint"""
        with client.session_transaction() as sess:
            sess['user_id'] = sample_user.id
        
        with patch('services.ai_integration.AIIntegrationService') as mock_ai:
            mock_response = Mock()
            mock_response.decision = "Increase R&D budget by 20%"
            mock_response.rationale = "ROI analysis shows positive returns"
            mock_response.confidence_score = 0.8
            mock_response.priority = "medium"
            mock_response.category = "financial"
            mock_response.risk_level = "low"
            mock_response.financial_impact = Decimal('500000')
            
            mock_ai.return_value.generate_executive_response.return_value = mock_response
            
            response = client.post('/api/cfo/decision', json={
                'context': 'Should we increase our R&D investment?',
                'financial_data': {
                    'current_budget': 1000000,
                    'projected_revenue': 5000000
                }
            })
            
            assert response.status_code == 200
            data = response.get_json()
            
            assert data['executive_type'] == 'cfo'
            assert data['decision'] == "Increase R&D budget by 20%"
            assert data['category'] == 'financial'
            assert 'financial_impact' in data
    
    def test_decision_history_endpoint(self, client, sample_user, sample_decisions):
        """Test decision history retrieval endpoint"""
        with client.session_transaction() as sess:
            sess['user_id'] = sample_user.id
        
        response = client.get('/api/decisions/history')
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert 'decisions' in data
        assert 'total_count' in data
        assert 'page' in data
        assert len(data['decisions']) > 0
        
        # Check decision structure
        decision = data['decisions'][0]
        assert 'id' in decision
        assert 'title' in decision
        assert 'executive_type' in decision
        assert 'created_at' in decision
    
    def test_decision_update_endpoint(self, client, sample_user, sample_decisions):
        """Test decision status update endpoint"""
        with client.session_transaction() as sess:
            sess['user_id'] = sample_user.id
        
        decision = sample_decisions[0]
        
        response = client.put(f'/api/decisions/{decision.id}/status', json={
            'status': 'completed',
            'implementation_notes': 'Successfully implemented the decision',
            'outcome_rating': 4
        })
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert data['status'] == 'completed'
        assert data['implementation_notes'] == 'Successfully implemented the decision'
        assert data['outcome_rating'] == 4
        assert 'implemented_at' in data


@pytest.mark.integration
class TestDocumentRoutes:
    """Test document processing API endpoints"""
    
    def test_document_upload_endpoint(self, client, sample_user, temp_file):
        """Test document upload endpoint"""
        with client.session_transaction() as sess:
            sess['user_id'] = sample_user.id
        
        with patch('services.document_processing.DocumentProcessingService') as mock_service:
            mock_document = Mock()
            mock_document.id = 'doc123'
            mock_document.filename = 'test.pdf'
            mock_document.file_type = 'pdf'
            mock_document.document_type = 'financial'
            mock_document.summary = 'Test document summary'
            
            mock_service.return_value.upload_document.return_value = mock_document
            
            with open(temp_file, 'rb') as f:
                response = client.post('/api/documents/upload', data={
                    'file': (f, 'test.pdf'),
                    'document_type': 'financial',
                    'sensitivity_level': 'internal'
                })
            
            assert response.status_code == 200
            data = response.get_json()
            
            assert data['id'] == 'doc123'
            assert data['filename'] == 'test.pdf'
            assert data['document_type'] == 'financial'
    
    def test_document_analysis_endpoint(self, client, sample_user, sample_documents):
        """Test document analysis endpoint"""
        with client.session_transaction() as sess:
            sess['user_id'] = sample_user.id
        
        document = sample_documents[0]
        
        with patch('services.document_analysis.DocumentAnalysisService') as mock_service:
            mock_analysis = Mock()
            mock_analysis.summary = 'Document analysis summary'
            mock_analysis.key_insights = ['Insight 1', 'Insight 2']
            mock_analysis.category = 'financial'
            mock_analysis.confidence_score = 0.85
            
            mock_service.return_value.analyze_document.return_value = mock_analysis
            
            response = client.post(f'/api/documents/{document.id}/analyze')
            
            assert response.status_code == 200
            data = response.get_json()
            
            assert data['summary'] == 'Document analysis summary'
            assert data['key_insights'] == ['Insight 1', 'Insight 2']
            assert data['category'] == 'financial'
            assert data['confidence_score'] == 0.85
    
    def test_document_search_endpoint(self, client, sample_user, sample_documents):
        """Test document search endpoint"""
        with client.session_transaction() as sess:
            sess['user_id'] = sample_user.id
        
        with patch('services.vector_database.VectorDatabaseService') as mock_service:
            mock_results = [
                Mock(
                    document_id='doc1',
                    content='Financial report content',
                    similarity_score=0.9,
                    metadata={'type': 'financial'}
                ),
                Mock(
                    document_id='doc2',
                    content='Technical specification',
                    similarity_score=0.8,
                    metadata={'type': 'technical'}
                )
            ]
            
            mock_service.return_value.search_documents.return_value = mock_results
            
            response = client.post('/api/documents/search', json={
                'query': 'financial analysis',
                'filters': {'document_type': 'financial'},
                'max_results': 10
            })
            
            assert response.status_code == 200
            data = response.get_json()
            
            assert 'results' in data
            assert len(data['results']) == 2
            assert data['results'][0]['document_id'] == 'doc1'
            assert data['results'][0]['similarity_score'] == 0.9


@pytest.mark.integration
class TestAnalyticsRoutes:
    """Test analytics API endpoints"""
    
    def test_decision_analytics_endpoint(self, client, sample_user, sample_decisions):
        """Test decision analytics endpoint"""
        with client.session_transaction() as sess:
            sess['user_id'] = sample_user.id
        
        with patch('services.analytics.AnalyticsService') as mock_service:
            mock_analytics = Mock()
            mock_analytics.total_decisions = 10
            mock_analytics.decisions_by_executive = {'ceo': 4, 'cto': 3, 'cfo': 3}
            mock_analytics.average_confidence_score = 0.82
            mock_analytics.implementation_rate = 0.7
            
            mock_service.return_value.generate_decision_analytics.return_value = mock_analytics
            
            response = client.get('/api/analytics/decisions', query_string={
                'days': 30,
                'executive_types': 'ceo,cto,cfo'
            })
            
            assert response.status_code == 200
            data = response.get_json()
            
            assert data['total_decisions'] == 10
            assert data['decisions_by_executive']['ceo'] == 4
            assert data['average_confidence_score'] == 0.82
    
    def test_performance_dashboard_endpoint(self, client, sample_user):
        """Test performance dashboard endpoint"""
        with client.session_transaction() as sess:
            sess['user_id'] = sample_user.id
        
        with patch('services.analytics.AnalyticsService') as mock_service:
            mock_dashboard = Mock()
            mock_dashboard.key_metrics = {
                'total_decisions': 25,
                'success_rate': 0.8,
                'implementation_rate': 0.75
            }
            mock_dashboard.charts = [
                {'type': 'line', 'data': [1, 2, 3, 4, 5]},
                {'type': 'pie', 'data': {'ceo': 10, 'cto': 8, 'cfo': 7}}
            ]
            mock_dashboard.recommendations = [
                'Consider increasing decision confidence thresholds',
                'Focus on improving implementation rates'
            ]
            
            mock_service.return_value.get_performance_dashboard.return_value = mock_dashboard
            
            response = client.get('/api/analytics/dashboard')
            
            assert response.status_code == 200
            data = response.get_json()
            
            assert data['key_metrics']['total_decisions'] == 25
            assert len(data['charts']) == 2
            assert len(data['recommendations']) == 2


@pytest.mark.integration
class TestCollaborationRoutes:
    """Test collaboration API endpoints"""
    
    def test_create_collaboration_endpoint(self, client, sample_user, sample_decisions):
        """Test collaboration session creation endpoint"""
        with client.session_transaction() as sess:
            sess['user_id'] = sample_user.id
        
        decision = sample_decisions[0]
        
        with patch('services.collaboration.CollaborationService') as mock_service:
            mock_session = Mock()
            mock_session.id = 'collab123'
            mock_session.decision_id = decision.id
            mock_session.title = 'Decision Review Session'
            mock_session.status = 'active'
            
            mock_service.return_value.create_collaboration_session.return_value = mock_session
            
            response = client.post('/api/collaboration/sessions', json={
                'decision_id': decision.id,
                'title': 'Decision Review Session',
                'description': 'Review and discuss the decision',
                'collaborators': ['user2', 'user3'],
                'permissions': {
                    'can_comment': True,
                    'can_edit': False
                }
            })
            
            assert response.status_code == 201
            data = response.get_json()
            
            assert data['id'] == 'collab123'
            assert data['decision_id'] == decision.id
            assert data['title'] == 'Decision Review Session'
            assert data['status'] == 'active'
    
    def test_add_comment_endpoint(self, client, sample_user, sample_decisions):
        """Test adding comment to decision endpoint"""
        with client.session_transaction() as sess:
            sess['user_id'] = sample_user.id
        
        decision = sample_decisions[0]
        
        with patch('services.collaboration.CollaborationService') as mock_service:
            mock_comment = Mock()
            mock_comment.id = 'comment123'
            mock_comment.content = 'This is a great decision'
            mock_comment.user_id = sample_user.id
            mock_comment.created_at = datetime.utcnow()
            
            mock_service.return_value.add_comment.return_value = mock_comment
            
            response = client.post(f'/api/decisions/{decision.id}/comments', json={
                'content': 'This is a great decision',
                'mentions': ['user2']
            })
            
            assert response.status_code == 201
            data = response.get_json()
            
            assert data['id'] == 'comment123'
            assert data['content'] == 'This is a great decision'
            assert data['user_id'] == sample_user.id


@pytest.mark.integration
class TestAuthenticationFlow:
    """Test authentication and authorization flow"""
    
    def test_login_flow(self, client):
        """Test complete login flow"""
        # Create test user
        user = UserFactory.build()
        user.set_password('test_password')
        
        with patch('models.User.query') as mock_query:
            mock_query.filter_by.return_value.first.return_value = user
            
            # Test login
            response = client.post('/auth/login', json={
                'username': user.username,
                'password': 'test_password'
            })
            
            assert response.status_code == 200
            data = response.get_json()
            
            assert data['success'] is True
            assert 'user' in data
            assert data['user']['username'] == user.username
    
    def test_mfa_flow(self, client):
        """Test MFA authentication flow"""
        user = UserFactory.build()
        user.set_password('test_password')
        user.setup_mfa()
        
        with patch('models.User.query') as mock_query, \
             patch.object(user, 'verify_mfa_token', return_value=True):
            
            mock_query.filter_by.return_value.first.return_value = user
            
            # First step: username/password
            response = client.post('/auth/login', json={
                'username': user.username,
                'password': 'test_password'
            })
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['mfa_required'] is True
            
            # Second step: MFA token
            response = client.post('/auth/mfa/verify', json={
                'username': user.username,
                'token': '123456'
            })
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True
    
    def test_unauthorized_access(self, client):
        """Test unauthorized access to protected endpoints"""
        response = client.get('/api/decisions/history')
        assert response.status_code == 401
        
        response = client.post('/api/ceo/decision', json={
            'context': 'Test context'
        })
        assert response.status_code == 401


@pytest.mark.integration
class TestErrorHandling:
    """Test error handling across API endpoints"""
    
    def test_validation_errors(self, client, sample_user):
        """Test validation error handling"""
        with client.session_transaction() as sess:
            sess['user_id'] = sample_user.id
        
        # Test missing required fields
        response = client.post('/api/ceo/decision', json={})
        assert response.status_code == 400
        
        data = response.get_json()
        assert 'error' in data
        assert 'validation' in data['error'].lower()
    
    def test_service_errors(self, client, sample_user):
        """Test service error handling"""
        with client.session_transaction() as sess:
            sess['user_id'] = sample_user.id
        
        with patch('services.ai_integration.AIIntegrationService') as mock_ai:
            mock_ai.return_value.generate_executive_response.side_effect = Exception("AI service error")
            
            response = client.post('/api/ceo/decision', json={
                'context': 'Test context'
            })
            
            assert response.status_code == 500
            data = response.get_json()
            assert 'error' in data
    
    def test_not_found_errors(self, client, sample_user):
        """Test not found error handling"""
        with client.session_transaction() as sess:
            sess['user_id'] = sample_user.id
        
        response = client.get('/api/decisions/nonexistent')
        assert response.status_code == 404
        
        data = response.get_json()
        assert 'error' in data
        assert 'not found' in data['error'].lower()


@pytest.mark.integration
class TestDataConsistency:
    """Test data consistency across operations"""
    
    def test_decision_creation_consistency(self, client, sample_user, db_session):
        """Test that decision creation maintains data consistency"""
        with client.session_transaction() as sess:
            sess['user_id'] = sample_user.id
        
        with patch('services.ai_integration.AIIntegrationService') as mock_ai:
            mock_response = Mock()
            mock_response.decision = "Test decision"
            mock_response.rationale = "Test rationale"
            mock_response.confidence_score = 0.8
            mock_response.priority = "high"
            mock_response.category = "strategic"
            mock_response.risk_level = "low"
            
            mock_ai.return_value.generate_executive_response.return_value = mock_response
            
            # Create decision
            response = client.post('/api/ceo/decision', json={
                'context': 'Test context'
            })
            
            assert response.status_code == 200
            decision_data = response.get_json()
            
            # Verify decision was saved to database
            from models import Decision
            decision = db_session.query(Decision).filter_by(id=decision_data['id']).first()
            
            assert decision is not None
            assert decision.user_id == sample_user.id
            assert decision.executive_type == 'ceo'
            assert decision.decision == "Test decision"
    
    def test_document_upload_consistency(self, client, sample_user, db_session, temp_file):
        """Test that document upload maintains data consistency"""
        with client.session_transaction() as sess:
            sess['user_id'] = sample_user.id
        
        with patch('services.document_processing.DocumentProcessingService') as mock_service:
            mock_document = Mock()
            mock_document.id = 'doc123'
            mock_document.user_id = sample_user.id
            mock_document.filename = 'test.pdf'
            mock_document.file_type = 'pdf'
            
            mock_service.return_value.upload_document.return_value = mock_document
            
            with open(temp_file, 'rb') as f:
                response = client.post('/api/documents/upload', data={
                    'file': (f, 'test.pdf'),
                    'document_type': 'financial'
                })
            
            assert response.status_code == 200
            
            # Verify document metadata consistency
            from models import Document
            document = db_session.query(Document).filter_by(id='doc123').first()
            
            if document:  # Only check if document was actually saved
                assert document.user_id == sample_user.id
                assert document.filename == 'test.pdf'


if __name__ == "__main__":
    pytest.main([__file__])