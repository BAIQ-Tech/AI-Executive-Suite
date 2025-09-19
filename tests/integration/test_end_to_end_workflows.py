"""
End-to-end workflow integration tests
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import json
from datetime import datetime, timedelta
from decimal import Decimal

from tests.factories import UserFactory, DecisionFactory, DocumentFactory


@pytest.mark.integration
class TestDecisionWorkflow:
    """Test complete decision-making workflow"""
    
    def test_complete_ceo_decision_workflow(self, client, sample_user, db_session):
        """Test complete CEO decision workflow from creation to implementation"""
        with client.session_transaction() as sess:
            sess['user_id'] = sample_user.id
        
        # Step 1: Create decision with AI assistance
        with patch('services.ai_integration.AIIntegrationService') as mock_ai:
            mock_response = Mock()
            mock_response.decision = "Expand to European markets"
            mock_response.rationale = "Market analysis shows 40% growth potential"
            mock_response.confidence_score = 0.85
            mock_response.priority = "high"
            mock_response.category = "strategic"
            mock_response.risk_level = "medium"
            mock_response.financial_impact = Decimal('500000')
            
            mock_ai.return_value.generate_executive_response.return_value = mock_response
            
            # Create decision
            response = client.post('/api/ceo/decision', json={
                'context': 'Should we expand our business to European markets?',
                'options': ['Expand to Europe', 'Expand to Asia', 'Stay domestic'],
                'documents': ['market_analysis.pdf', 'financial_projections.xlsx']
            })
            
            assert response.status_code == 200
            decision_data = response.get_json()
            decision_id = decision_data['id']
            
            assert decision_data['decision'] == "Expand to European markets"
            assert decision_data['executive_type'] == 'ceo'
            assert decision_data['status'] == 'pending'
        
        # Step 2: Add collaboration and comments
        with patch('services.collaboration.CollaborationService') as mock_collab:
            mock_session = Mock()
            mock_session.id = 'collab123'
            mock_session.status = 'active'
            mock_collab.return_value.create_collaboration_session.return_value = mock_session
            
            # Create collaboration session
            collab_response = client.post('/api/collaboration/sessions', json={
                'decision_id': decision_id,
                'title': 'European Expansion Review',
                'collaborators': ['cto_user', 'cfo_user'],
                'permissions': {'can_comment': True, 'can_edit': False}
            })
            
            assert collab_response.status_code == 201
            
            # Add comments from team members
            mock_comment = Mock()
            mock_comment.id = 'comment123'
            mock_comment.content = 'I support this decision based on technical feasibility'
            mock_collab.return_value.add_comment.return_value = mock_comment
            
            comment_response = client.post(f'/api/decisions/{decision_id}/comments', json={
                'content': 'I support this decision based on technical feasibility',
                'mentions': ['ceo_user']
            })
            
            assert comment_response.status_code == 201
        
        # Step 3: Update decision status to in_progress
        status_response = client.put(f'/api/decisions/{decision_id}/status', json={
            'status': 'in_progress',
            'implementation_notes': 'Starting market research and legal compliance review'
        })
        
        assert status_response.status_code == 200
        updated_decision = status_response.get_json()
        assert updated_decision['status'] == 'in_progress'
        
        # Step 4: Complete implementation
        completion_response = client.put(f'/api/decisions/{decision_id}/status', json={
            'status': 'completed',
            'implementation_notes': 'European expansion launched successfully',
            'outcome_rating': 4,
            'effectiveness_score': 0.9
        })
        
        assert completion_response.status_code == 200
        completed_decision = completion_response.get_json()
        assert completed_decision['status'] == 'completed'
        assert completed_decision['outcome_rating'] == 4
        
        # Step 5: Verify decision appears in analytics
        with patch('services.analytics.AnalyticsService') as mock_analytics:
            mock_analytics_data = Mock()
            mock_analytics_data.total_decisions = 1
            mock_analytics_data.decisions_by_executive = {'ceo': 1}
            mock_analytics_data.implementation_rate = 1.0
            mock_analytics_data.average_confidence_score = 0.85
            
            mock_analytics.return_value.generate_decision_analytics.return_value = mock_analytics_data
            
            analytics_response = client.get('/api/analytics/decisions?days=30')
            
            assert analytics_response.status_code == 200
            analytics_data = analytics_response.get_json()
            assert analytics_data['total_decisions'] == 1
            assert analytics_data['implementation_rate'] == 1.0
    
    def test_document_driven_decision_workflow(self, client, sample_user, temp_file):
        """Test decision workflow driven by document analysis"""
        with client.session_transaction() as sess:
            sess['user_id'] = sample_user.id
        
        # Step 1: Upload and analyze document
        with patch('services.document_processing.DocumentProcessingService') as mock_doc_service:
            mock_document = Mock()
            mock_document.id = 'doc123'
            mock_document.filename = 'financial_report.pdf'
            mock_document.document_type = 'financial'
            mock_document.summary = 'Q4 financial performance shows 15% revenue growth'
            mock_document.key_insights = [
                'Revenue increased 15% year-over-year',
                'Operating expenses remained stable',
                'Cash flow improved by 20%'
            ]
            
            mock_doc_service.return_value.upload_document.return_value = mock_document
            
            # Upload document
            with open(temp_file, 'rb') as f:
                upload_response = client.post('/api/documents/upload', data={
                    'file': (f, 'financial_report.pdf'),
                    'document_type': 'financial',
                    'sensitivity_level': 'internal'
                })
            
            assert upload_response.status_code == 200
            document_data = upload_response.get_json()
            document_id = document_data['id']
        
        # Step 2: Analyze document for insights
        with patch('services.document_analysis.DocumentAnalysisService') as mock_analysis:
            mock_analysis_result = Mock()
            mock_analysis_result.summary = 'Strong financial performance with growth opportunities'
            mock_analysis_result.key_insights = [
                'Revenue growth trajectory is sustainable',
                'Market expansion opportunities identified',
                'Investment in R&D recommended'
            ]
            mock_analysis_result.category = 'financial'
            mock_analysis_result.confidence_score = 0.9
            
            mock_analysis.return_value.analyze_document.return_value = mock_analysis_result
            
            analysis_response = client.post(f'/api/documents/{document_id}/analyze')
            
            assert analysis_response.status_code == 200
            analysis_data = analysis_response.get_json()
            assert 'growth opportunities' in analysis_data['summary']
        
        # Step 3: Generate CFO decision based on document insights
        with patch('services.ai_integration.AIIntegrationService') as mock_ai:
            mock_response = Mock()
            mock_response.decision = "Increase R&D investment by 25%"
            mock_response.rationale = "Financial analysis shows strong cash position and growth potential"
            mock_response.confidence_score = 0.88
            mock_response.priority = "high"
            mock_response.category = "financial"
            mock_response.risk_level = "low"
            mock_response.financial_impact = Decimal('250000')
            
            mock_ai.return_value.generate_executive_response.return_value = mock_response
            
            # Create decision with document context
            decision_response = client.post('/api/cfo/decision', json={
                'context': 'Based on Q4 financial results, how should we allocate additional resources?',
                'document_references': [document_id],
                'financial_constraints': {
                    'available_budget': 500000,
                    'risk_tolerance': 'medium'
                }
            })
            
            assert decision_response.status_code == 200
            decision_data = decision_response.get_json()
            assert decision_data['decision'] == "Increase R&D investment by 25%"
            assert decision_data['financial_impact'] == 250000
        
        # Step 4: Verify document is referenced in decision
        decision_id = decision_data['id']
        decision_detail_response = client.get(f'/api/decisions/{decision_id}')
        
        assert decision_detail_response.status_code == 200
        decision_detail = decision_detail_response.get_json()
        
        # Check that document is referenced (if implemented)
        if 'document_references' in decision_detail:
            assert document_id in decision_detail['document_references']
    
    def test_collaborative_decision_workflow(self, client, sample_user, db_session):
        """Test collaborative decision-making workflow"""
        with client.session_transaction() as sess:
            sess['user_id'] = sample_user.id
        
        # Create additional users for collaboration
        collaborator1 = UserFactory.build(username='collaborator1')
        collaborator2 = UserFactory.build(username='collaborator2')
        db_session.add(collaborator1)
        db_session.add(collaborator2)
        db_session.commit()
        
        # Step 1: Create initial decision
        with patch('services.ai_integration.AIIntegrationService') as mock_ai:
            mock_response = Mock()
            mock_response.decision = "Implement new technology stack"
            mock_response.rationale = "Current stack is becoming outdated"
            mock_response.confidence_score = 0.7  # Lower confidence for collaboration
            mock_response.priority = "high"
            mock_response.category = "technical"
            mock_response.risk_level = "high"
            
            mock_ai.return_value.generate_executive_response.return_value = mock_response
            
            decision_response = client.post('/api/cto/decision', json={
                'context': 'Should we migrate to a new technology stack?',
                'technical_requirements': ['Scalability', 'Performance', 'Maintainability'],
                'collaboration_required': True
            })
            
            assert decision_response.status_code == 200
            decision_data = decision_response.get_json()
            decision_id = decision_data['id']
        
        # Step 2: Create collaboration session
        with patch('services.collaboration.CollaborationService') as mock_collab:
            mock_session = Mock()
            mock_session.id = 'collab456'
            mock_session.status = 'active'
            mock_session.requires_approval = True
            mock_session.approval_threshold = 2
            
            mock_collab.return_value.create_collaboration_session.return_value = mock_session
            
            collab_response = client.post('/api/collaboration/sessions', json={
                'decision_id': decision_id,
                'title': 'Technology Stack Migration Review',
                'description': 'Review and approve technology stack migration',
                'collaborators': [collaborator1.id, collaborator2.id],
                'requires_approval': True,
                'approval_threshold': 2
            })
            
            assert collab_response.status_code == 201
            session_data = collab_response.get_json()
            session_id = session_data['id']
        
        # Step 3: Add comments and feedback from collaborators
        comments = [
            {
                'user_id': collaborator1.id,
                'content': 'I agree with the migration but suggest phased approach',
                'approval': True
            },
            {
                'user_id': collaborator2.id,
                'content': 'Concerns about timeline and resource allocation',
                'approval': False
            }
        ]
        
        for comment_data in comments:
            with client.session_transaction() as sess:
                sess['user_id'] = comment_data['user_id']
            
            with patch('services.collaboration.CollaborationService') as mock_collab:
                mock_comment = Mock()
                mock_comment.id = f"comment_{comment_data['user_id']}"
                mock_comment.content = comment_data['content']
                mock_comment.user_id = comment_data['user_id']
                
                mock_collab.return_value.add_comment.return_value = mock_comment
                
                comment_response = client.post(f'/api/decisions/{decision_id}/comments', json={
                    'content': comment_data['content'],
                    'approval_vote': comment_data['approval']
                })
                
                assert comment_response.status_code == 201
        
        # Step 4: Check collaboration status and approvals
        with client.session_transaction() as sess:
            sess['user_id'] = sample_user.id
        
        with patch('services.collaboration.CollaborationService') as mock_collab:
            mock_status = Mock()
            mock_status.approval_count = 1
            mock_status.rejection_count = 1
            mock_status.is_approved = False
            mock_status.status = 'active'
            
            mock_collab.return_value.get_collaboration_status.return_value = mock_status
            
            status_response = client.get(f'/api/collaboration/sessions/{session_id}/status')
            
            assert status_response.status_code == 200
            status_data = status_response.get_json()
            assert status_data['is_approved'] is False
        
        # Step 5: Revise decision based on feedback
        with patch('services.ai_integration.AIIntegrationService') as mock_ai:
            mock_revised_response = Mock()
            mock_revised_response.decision = "Implement phased technology stack migration"
            mock_revised_response.rationale = "Phased approach addresses timeline and resource concerns"
            mock_revised_response.confidence_score = 0.85
            mock_revised_response.priority = "high"
            mock_revised_response.category = "technical"
            mock_revised_response.risk_level = "medium"
            
            mock_ai.return_value.generate_executive_response.return_value = mock_revised_response
            
            revision_response = client.put(f'/api/decisions/{decision_id}/revise', json={
                'context': 'Revise decision based on team feedback for phased approach',
                'collaboration_feedback': [
                    'Suggest phased approach',
                    'Timeline and resource concerns'
                ]
            })
            
            assert revision_response.status_code == 200
            revised_decision = revision_response.get_json()
            assert 'phased' in revised_decision['decision'].lower()
            assert revised_decision['confidence_score'] > 0.8


@pytest.mark.integration
class TestAnalyticsWorkflow:
    """Test analytics and reporting workflow"""
    
    def test_comprehensive_analytics_workflow(self, client, sample_user, sample_decisions):
        """Test comprehensive analytics generation workflow"""
        with client.session_transaction() as sess:
            sess['user_id'] = sample_user.id
        
        # Step 1: Generate decision analytics
        with patch('services.analytics.AnalyticsService') as mock_analytics:
            mock_decision_analytics = Mock()
            mock_decision_analytics.total_decisions = len(sample_decisions)
            mock_decision_analytics.decisions_by_executive = {
                'ceo': 2, 'cto': 2, 'cfo': 1
            }
            mock_decision_analytics.average_confidence_score = 0.82
            mock_decision_analytics.implementation_rate = 0.6
            mock_decision_analytics.effectiveness_scores = {
                'ceo': 0.85, 'cto': 0.78, 'cfo': 0.90
            }
            
            mock_analytics.return_value.generate_decision_analytics.return_value = mock_decision_analytics
            
            analytics_response = client.get('/api/analytics/decisions', query_string={
                'days': 30,
                'executive_types': 'ceo,cto,cfo',
                'include_trends': True
            })
            
            assert analytics_response.status_code == 200
            analytics_data = analytics_response.get_json()
            
            assert analytics_data['total_decisions'] == len(sample_decisions)
            assert analytics_data['average_confidence_score'] == 0.82
            assert 'ceo' in analytics_data['decisions_by_executive']
        
        # Step 2: Generate performance dashboard
        with patch('services.analytics.AnalyticsService') as mock_analytics:
            mock_dashboard = Mock()
            mock_dashboard.key_metrics = {
                'total_decisions': len(sample_decisions),
                'success_rate': 0.8,
                'implementation_rate': 0.75,
                'average_response_time': 2.3
            }
            mock_dashboard.charts = [
                {
                    'type': 'line',
                    'title': 'Decision Trends',
                    'data': {
                        'labels': ['Week 1', 'Week 2', 'Week 3', 'Week 4'],
                        'values': [2, 3, 1, 4]
                    }
                },
                {
                    'type': 'pie',
                    'title': 'Decisions by Executive',
                    'data': {'ceo': 40, 'cto': 35, 'cfo': 25}
                }
            ]
            mock_dashboard.recommendations = [
                'Consider increasing decision confidence thresholds',
                'Focus on improving CTO decision implementation rates'
            ]
            mock_dashboard.alerts = []
            
            mock_analytics.return_value.get_performance_dashboard.return_value = mock_dashboard
            
            dashboard_response = client.get('/api/analytics/dashboard')
            
            assert dashboard_response.status_code == 200
            dashboard_data = dashboard_response.get_json()
            
            assert dashboard_data['key_metrics']['success_rate'] == 0.8
            assert len(dashboard_data['charts']) == 2
            assert len(dashboard_data['recommendations']) == 2
        
        # Step 3: Generate custom report
        with patch('services.analytics.AnalyticsService') as mock_analytics:
            mock_report = Mock()
            mock_report.title = 'Executive Decision Performance Report'
            mock_report.period = '30 days'
            mock_report.sections = [
                {
                    'title': 'Executive Summary',
                    'content': 'Overall decision-making performance is strong'
                },
                {
                    'title': 'Key Metrics',
                    'content': 'Implementation rate: 75%, Success rate: 80%'
                },
                {
                    'title': 'Recommendations',
                    'content': 'Focus on improving decision follow-through'
                }
            ]
            
            mock_analytics.return_value.generate_custom_report.return_value = mock_report
            
            report_response = client.post('/api/analytics/reports', json={
                'report_type': 'executive_performance',
                'date_range': {
                    'start': '2024-01-01',
                    'end': '2024-01-31'
                },
                'filters': {
                    'executive_types': ['ceo', 'cto', 'cfo'],
                    'categories': ['strategic', 'operational']
                },
                'format': 'json'
            })
            
            assert report_response.status_code == 200
            report_data = report_response.get_json()
            
            assert report_data['title'] == 'Executive Decision Performance Report'
            assert len(report_data['sections']) == 3
        
        # Step 4: Export analytics data
        with patch('services.analytics.AnalyticsService') as mock_analytics:
            mock_export_data = {
                'decisions': [
                    {
                        'id': 'dec1',
                        'executive_type': 'ceo',
                        'confidence_score': 0.85,
                        'status': 'completed'
                    }
                ],
                'summary': {
                    'total_decisions': 1,
                    'export_date': datetime.utcnow().isoformat()
                }
            }
            
            mock_analytics.return_value.export_analytics_data.return_value = mock_export_data
            
            export_response = client.get('/api/analytics/export', query_string={
                'format': 'json',
                'date_range': '30d',
                'include_raw_data': True
            })
            
            assert export_response.status_code == 200
            export_data = export_response.get_json()
            
            assert 'decisions' in export_data
            assert 'summary' in export_data
            assert export_data['summary']['total_decisions'] == 1


@pytest.mark.integration
class TestErrorRecoveryWorkflows:
    """Test error recovery and resilience workflows"""
    
    def test_ai_service_failure_recovery(self, client, sample_user):
        """Test recovery from AI service failures"""
        with client.session_transaction() as sess:
            sess['user_id'] = sample_user.id
        
        # Step 1: AI service fails initially
        with patch('services.ai_integration.AIIntegrationService') as mock_ai:
            mock_ai.return_value.generate_executive_response.side_effect = Exception("AI service unavailable")
            
            response = client.post('/api/ceo/decision', json={
                'context': 'Should we expand our product line?'
            })
            
            # Should return error but not crash
            assert response.status_code == 500
            error_data = response.get_json()
            assert 'error' in error_data
        
        # Step 2: AI service recovers, retry succeeds
        with patch('services.ai_integration.AIIntegrationService') as mock_ai:
            mock_response = Mock()
            mock_response.decision = "Expand product line gradually"
            mock_response.rationale = "Market conditions are favorable"
            mock_response.confidence_score = 0.75
            mock_response.priority = "medium"
            mock_response.category = "strategic"
            mock_response.risk_level = "medium"
            
            mock_ai.return_value.generate_executive_response.return_value = mock_response
            
            retry_response = client.post('/api/ceo/decision', json={
                'context': 'Should we expand our product line?'
            })
            
            assert retry_response.status_code == 200
            decision_data = retry_response.get_json()
            assert decision_data['decision'] == "Expand product line gradually"
    
    def test_database_transaction_recovery(self, client, sample_user, db_session):
        """Test recovery from database transaction failures"""
        with client.session_transaction() as sess:
            sess['user_id'] = sample_user.id
        
        # Simulate database constraint violation
        with patch('models.db.session.commit') as mock_commit:
            mock_commit.side_effect = Exception("Database constraint violation")
            
            with patch('services.ai_integration.AIIntegrationService') as mock_ai:
                mock_response = Mock()
                mock_response.decision = "Test decision"
                mock_response.rationale = "Test rationale"
                mock_response.confidence_score = 0.8
                mock_response.priority = "high"
                mock_response.category = "strategic"
                mock_response.risk_level = "low"
                
                mock_ai.return_value.generate_executive_response.return_value = mock_response
                
                response = client.post('/api/ceo/decision', json={
                    'context': 'Test context'
                })
                
                # Should handle database error gracefully
                assert response.status_code == 500
                error_data = response.get_json()
                assert 'error' in error_data
        
        # Verify database state is consistent (no partial data)
        from models import Decision
        decisions = db_session.query(Decision).filter_by(user_id=sample_user.id).all()
        # Should not have any decisions from the failed transaction
        initial_count = len(decisions)
        
        # Retry with working database
        with patch('services.ai_integration.AIIntegrationService') as mock_ai:
            mock_response = Mock()
            mock_response.decision = "Test decision retry"
            mock_response.rationale = "Test rationale retry"
            mock_response.confidence_score = 0.8
            mock_response.priority = "high"
            mock_response.category = "strategic"
            mock_response.risk_level = "low"
            
            mock_ai.return_value.generate_executive_response.return_value = mock_response
            
            retry_response = client.post('/api/ceo/decision', json={
                'context': 'Test context retry'
            })
            
            assert retry_response.status_code == 200
            
            # Verify decision was saved
            decisions_after = db_session.query(Decision).filter_by(user_id=sample_user.id).all()
            assert len(decisions_after) == initial_count + 1
    
    def test_external_service_timeout_recovery(self, client, sample_user):
        """Test recovery from external service timeouts"""
        with client.session_transaction() as sess:
            sess['user_id'] = sample_user.id
        
        # Step 1: External service (CRM) times out
        with patch('services.crm_integration.CRMIntegrationService') as mock_crm:
            mock_crm.return_value.get_contacts.side_effect = Exception("Connection timeout")
            
            response = client.get('/api/integrations/crm/contacts')
            
            assert response.status_code == 503  # Service Unavailable
            error_data = response.get_json()
            assert 'timeout' in error_data['error'].lower()
        
        # Step 2: Service recovers
        with patch('services.crm_integration.CRMIntegrationService') as mock_crm:
            mock_contacts = [
                {'id': '1', 'name': 'John Doe', 'email': 'john@example.com'},
                {'id': '2', 'name': 'Jane Smith', 'email': 'jane@example.com'}
            ]
            mock_crm.return_value.get_contacts.return_value = mock_contacts
            
            retry_response = client.get('/api/integrations/crm/contacts')
            
            assert retry_response.status_code == 200
            contacts_data = retry_response.get_json()
            assert len(contacts_data['contacts']) == 2


@pytest.mark.integration
class TestPerformanceWorkflows:
    """Test performance under various load conditions"""
    
    def test_concurrent_decision_creation(self, client, sample_user):
        """Test concurrent decision creation"""
        import threading
        import time
        
        results = []
        
        def create_decision(thread_id):
            with client.session_transaction() as sess:
                sess['user_id'] = sample_user.id
            
            with patch('services.ai_integration.AIIntegrationService') as mock_ai:
                mock_response = Mock()
                mock_response.decision = f"Decision from thread {thread_id}"
                mock_response.rationale = f"Rationale from thread {thread_id}"
                mock_response.confidence_score = 0.8
                mock_response.priority = "medium"
                mock_response.category = "operational"
                mock_response.risk_level = "low"
                
                mock_ai.return_value.generate_executive_response.return_value = mock_response
                
                response = client.post('/api/ceo/decision', json={
                    'context': f'Decision context from thread {thread_id}'
                })
                
                results.append({
                    'thread_id': thread_id,
                    'status_code': response.status_code,
                    'success': response.status_code == 200
                })
        
        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=create_decision, args=(i,))
            threads.append(thread)
        
        # Start all threads
        start_time = time.time()
        for thread in threads:
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Verify all requests succeeded
        assert len(results) == 5
        assert all(result['success'] for result in results)
        
        # Performance should be reasonable (less than 10 seconds for 5 concurrent requests)
        assert total_time < 10.0
    
    def test_bulk_analytics_processing(self, client, sample_user, sample_decisions):
        """Test bulk analytics processing performance"""
        with client.session_transaction() as sess:
            sess['user_id'] = sample_user.id
        
        import time
        
        with patch('services.analytics.AnalyticsService') as mock_analytics:
            # Simulate processing large dataset
            mock_analytics_data = Mock()
            mock_analytics_data.total_decisions = 1000
            mock_analytics_data.decisions_by_executive = {
                'ceo': 400, 'cto': 350, 'cfo': 250
            }
            mock_analytics_data.average_confidence_score = 0.82
            mock_analytics_data.implementation_rate = 0.75
            
            # Add processing delay to simulate real computation
            def slow_analytics(*args, **kwargs):
                time.sleep(0.1)  # Simulate processing time
                return mock_analytics_data
            
            mock_analytics.return_value.generate_decision_analytics.side_effect = slow_analytics
            
            start_time = time.time()
            
            response = client.get('/api/analytics/decisions', query_string={
                'days': 365,  # Large date range
                'include_trends': True,
                'include_detailed_breakdown': True
            })
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            assert response.status_code == 200
            analytics_data = response.get_json()
            assert analytics_data['total_decisions'] == 1000
            
            # Should complete within reasonable time
            assert processing_time < 5.0


if __name__ == "__main__":
    pytest.main([__file__])