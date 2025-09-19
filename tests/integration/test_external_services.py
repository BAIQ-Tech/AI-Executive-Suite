"""
Integration tests for external service integrations
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import json
import requests
from datetime import datetime, timedelta

from services.crm_integration import CRMIntegrationService
from services.erp_integration import ERPIntegrationService
from services.integration_framework import IntegrationFramework
from services.ai_integration import AIIntegrationService


@pytest.mark.integration
class TestCRMIntegration:
    """Test CRM system integration"""
    
    @pytest.fixture
    def crm_config(self):
        return {
            'crm': {
                'provider': 'salesforce',
                'api_url': 'https://api.salesforce.com',
                'client_id': 'test_client_id',
                'client_secret': 'test_client_secret',
                'username': 'test@example.com',
                'password': 'test_password',
                'security_token': 'test_token'
            }
        }
    
    @pytest.fixture
    def crm_service(self, crm_config):
        return CRMIntegrationService(crm_config)
    
    def test_salesforce_authentication(self, crm_service):
        """Test Salesforce authentication flow"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'access_token': 'test_access_token',
            'instance_url': 'https://test.salesforce.com',
            'token_type': 'Bearer'
        }
        
        with patch('requests.post', return_value=mock_response):
            auth_result = crm_service.authenticate()
            
            assert auth_result is True
            assert crm_service.access_token == 'test_access_token'
            assert crm_service.instance_url == 'https://test.salesforce.com'
    
    def test_salesforce_authentication_failure(self, crm_service):
        """Test Salesforce authentication failure"""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.return_value = {
            'error': 'invalid_grant',
            'error_description': 'authentication failure'
        }
        
        with patch('requests.post', return_value=mock_response):
            auth_result = crm_service.authenticate()
            
            assert auth_result is False
            assert crm_service.access_token is None
    
    def test_get_contacts(self, crm_service):
        """Test retrieving contacts from CRM"""
        # Mock authentication
        crm_service.access_token = 'test_token'
        crm_service.instance_url = 'https://test.salesforce.com'
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'records': [
                {
                    'Id': '001xx000003DHPh',
                    'Name': 'John Doe',
                    'Email': 'john@example.com',
                    'Phone': '+1234567890',
                    'Company': 'Test Company'
                },
                {
                    'Id': '001xx000003DHPi',
                    'Name': 'Jane Smith',
                    'Email': 'jane@example.com',
                    'Phone': '+1234567891',
                    'Company': 'Another Company'
                }
            ],
            'totalSize': 2
        }
        
        with patch('requests.get', return_value=mock_response):
            contacts = crm_service.get_contacts()
            
            assert len(contacts) == 2
            assert contacts[0]['Name'] == 'John Doe'
            assert contacts[1]['Email'] == 'jane@example.com'
    
    def test_get_opportunities(self, crm_service):
        """Test retrieving opportunities from CRM"""
        crm_service.access_token = 'test_token'
        crm_service.instance_url = 'https://test.salesforce.com'
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'records': [
                {
                    'Id': '006xx000004TmiQ',
                    'Name': 'Big Deal',
                    'Amount': 100000,
                    'StageName': 'Negotiation/Review',
                    'CloseDate': '2024-03-15',
                    'Probability': 75
                },
                {
                    'Id': '006xx000004TmiR',
                    'Name': 'Small Deal',
                    'Amount': 25000,
                    'StageName': 'Prospecting',
                    'CloseDate': '2024-04-01',
                    'Probability': 25
                }
            ],
            'totalSize': 2
        }
        
        with patch('requests.get', return_value=mock_response):
            opportunities = crm_service.get_opportunities()
            
            assert len(opportunities) == 2
            assert opportunities[0]['Amount'] == 100000
            assert opportunities[1]['StageName'] == 'Prospecting'
    
    def test_create_lead(self, crm_service):
        """Test creating a lead in CRM"""
        crm_service.access_token = 'test_token'
        crm_service.instance_url = 'https://test.salesforce.com'
        
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            'id': '00Qxx0000004C92',
            'success': True,
            'errors': []
        }
        
        lead_data = {
            'FirstName': 'New',
            'LastName': 'Lead',
            'Email': 'newlead@example.com',
            'Company': 'New Company'
        }
        
        with patch('requests.post', return_value=mock_response):
            result = crm_service.create_lead(lead_data)
            
            assert result['success'] is True
            assert result['id'] == '00Qxx0000004C92'
    
    def test_sync_data_with_ai_context(self, crm_service):
        """Test syncing CRM data for AI context"""
        crm_service.access_token = 'test_token'
        crm_service.instance_url = 'https://test.salesforce.com'
        
        # Mock multiple API calls
        contacts_response = Mock()
        contacts_response.status_code = 200
        contacts_response.json.return_value = {
            'records': [{'Id': '1', 'Name': 'Contact 1'}],
            'totalSize': 1
        }
        
        opportunities_response = Mock()
        opportunities_response.status_code = 200
        opportunities_response.json.return_value = {
            'records': [{'Id': '1', 'Name': 'Opportunity 1', 'Amount': 50000}],
            'totalSize': 1
        }
        
        with patch('requests.get') as mock_get:
            mock_get.side_effect = [contacts_response, opportunities_response]
            
            sync_data = crm_service.sync_data_for_ai_context()
            
            assert 'contacts' in sync_data
            assert 'opportunities' in sync_data
            assert len(sync_data['contacts']) == 1
            assert len(sync_data['opportunities']) == 1
            assert sync_data['opportunities'][0]['Amount'] == 50000


@pytest.mark.integration
class TestERPIntegration:
    """Test ERP system integration"""
    
    @pytest.fixture
    def erp_config(self):
        return {
            'erp': {
                'provider': 'quickbooks',
                'api_url': 'https://sandbox-quickbooks.api.intuit.com',
                'client_id': 'test_client_id',
                'client_secret': 'test_client_secret',
                'access_token': 'test_access_token',
                'refresh_token': 'test_refresh_token',
                'company_id': 'test_company_id'
            }
        }
    
    @pytest.fixture
    def erp_service(self, erp_config):
        return ERPIntegrationService(erp_config)
    
    def test_quickbooks_authentication(self, erp_service):
        """Test QuickBooks OAuth authentication"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'access_token': 'new_access_token',
            'refresh_token': 'new_refresh_token',
            'expires_in': 3600,
            'token_type': 'Bearer'
        }
        
        with patch('requests.post', return_value=mock_response):
            auth_result = erp_service.refresh_token()
            
            assert auth_result is True
            assert erp_service.access_token == 'new_access_token'
    
    def test_get_financial_data(self, erp_service):
        """Test retrieving financial data from ERP"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'QueryResponse': {
                'Item': [
                    {
                        'Id': '1',
                        'Name': 'Revenue',
                        'Type': 'Income',
                        'Balance': 1000000
                    },
                    {
                        'Id': '2',
                        'Name': 'Expenses',
                        'Type': 'Expense',
                        'Balance': 750000
                    }
                ]
            }
        }
        
        with patch('requests.get', return_value=mock_response):
            financial_data = erp_service.get_financial_data()
            
            assert 'revenue' in financial_data
            assert 'expenses' in financial_data
            assert financial_data['revenue'] == 1000000
            assert financial_data['expenses'] == 750000
    
    def test_get_inventory_data(self, erp_service):
        """Test retrieving inventory data from ERP"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'QueryResponse': {
                'Item': [
                    {
                        'Id': '1',
                        'Name': 'Product A',
                        'Type': 'Inventory',
                        'QtyOnHand': 100,
                        'UnitPrice': 50.00
                    },
                    {
                        'Id': '2',
                        'Name': 'Product B',
                        'Type': 'Inventory',
                        'QtyOnHand': 75,
                        'UnitPrice': 75.00
                    }
                ]
            }
        }
        
        with patch('requests.get', return_value=mock_response):
            inventory_data = erp_service.get_inventory_data()
            
            assert len(inventory_data) == 2
            assert inventory_data[0]['Name'] == 'Product A'
            assert inventory_data[0]['QtyOnHand'] == 100
            assert inventory_data[1]['UnitPrice'] == 75.00
    
    def test_create_invoice(self, erp_service):
        """Test creating an invoice in ERP"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'QueryResponse': {
                'Invoice': [{
                    'Id': '123',
                    'DocNumber': 'INV-001',
                    'TotalAmt': 1000.00,
                    'Balance': 1000.00
                }]
            }
        }
        
        invoice_data = {
            'CustomerRef': {'value': '1'},
            'Line': [{
                'Amount': 1000.00,
                'DetailType': 'SalesItemLineDetail',
                'SalesItemLineDetail': {
                    'ItemRef': {'value': '1'},
                    'Qty': 10,
                    'UnitPrice': 100.00
                }
            }]
        }
        
        with patch('requests.post', return_value=mock_response):
            result = erp_service.create_invoice(invoice_data)
            
            assert result['Id'] == '123'
            assert result['DocNumber'] == 'INV-001'
            assert result['TotalAmt'] == 1000.00


@pytest.mark.integration
class TestIntegrationFramework:
    """Test the integration framework"""
    
    @pytest.fixture
    def framework_config(self):
        return {
            'integrations': {
                'enabled': ['crm', 'erp', 'financial'],
                'retry_attempts': 3,
                'timeout': 30,
                'rate_limiting': {
                    'requests_per_minute': 60
                }
            }
        }
    
    @pytest.fixture
    def integration_framework(self, framework_config):
        return IntegrationFramework(framework_config)
    
    def test_register_integration(self, integration_framework):
        """Test registering an integration"""
        mock_integration = Mock()
        mock_integration.name = 'test_integration'
        mock_integration.version = '1.0.0'
        
        result = integration_framework.register_integration('test', mock_integration)
        
        assert result is True
        assert 'test' in integration_framework.integrations
    
    def test_execute_integration_with_retry(self, integration_framework):
        """Test integration execution with retry logic"""
        mock_integration = Mock()
        
        # First two calls fail, third succeeds
        mock_integration.execute.side_effect = [
            Exception("Network error"),
            Exception("Timeout error"),
            {'success': True, 'data': 'test_data'}
        ]
        
        integration_framework.register_integration('test', mock_integration)
        
        result = integration_framework.execute_integration('test', 'test_method', {})
        
        assert result['success'] is True
        assert result['data'] == 'test_data'
        assert mock_integration.execute.call_count == 3
    
    def test_execute_integration_max_retries_exceeded(self, integration_framework):
        """Test integration execution when max retries exceeded"""
        mock_integration = Mock()
        mock_integration.execute.side_effect = Exception("Persistent error")
        
        integration_framework.register_integration('test', mock_integration)
        
        with pytest.raises(Exception, match="Persistent error"):
            integration_framework.execute_integration('test', 'test_method', {})
        
        assert mock_integration.execute.call_count == 3  # Default retry attempts
    
    def test_rate_limiting(self, integration_framework):
        """Test rate limiting functionality"""
        import time
        
        mock_integration = Mock()
        mock_integration.execute.return_value = {'success': True}
        
        integration_framework.register_integration('test', mock_integration)
        
        # Execute multiple requests rapidly
        start_time = time.time()
        
        for i in range(5):
            integration_framework.execute_integration('test', 'test_method', {})
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Should take some time due to rate limiting
        # (This is a simplified test - real rate limiting would be more sophisticated)
        assert mock_integration.execute.call_count == 5
    
    def test_integration_health_check(self, integration_framework):
        """Test integration health check"""
        mock_integration = Mock()
        mock_integration.health_check.return_value = {
            'status': 'healthy',
            'response_time': 0.5,
            'last_success': datetime.utcnow()
        }
        
        integration_framework.register_integration('test', mock_integration)
        
        health_status = integration_framework.check_integration_health('test')
        
        assert health_status['status'] == 'healthy'
        assert health_status['response_time'] == 0.5
    
    def test_bulk_data_sync(self, integration_framework):
        """Test bulk data synchronization"""
        mock_crm = Mock()
        mock_crm.sync_data_for_ai_context.return_value = {
            'contacts': [{'id': '1', 'name': 'Contact 1'}],
            'opportunities': [{'id': '1', 'name': 'Opportunity 1'}]
        }
        
        mock_erp = Mock()
        mock_erp.get_financial_data.return_value = {
            'revenue': 1000000,
            'expenses': 750000
        }
        
        integration_framework.register_integration('crm', mock_crm)
        integration_framework.register_integration('erp', mock_erp)
        
        sync_result = integration_framework.bulk_sync_data(['crm', 'erp'])
        
        assert 'crm' in sync_result
        assert 'erp' in sync_result
        assert sync_result['crm']['contacts'][0]['name'] == 'Contact 1'
        assert sync_result['erp']['revenue'] == 1000000


@pytest.mark.integration
class TestAIIntegrationWithExternalData:
    """Test AI integration with external data sources"""
    
    @pytest.fixture
    def ai_service_config(self):
        return {
            'openai': {
                'api_key': 'test-key',
                'model': 'gpt-4',
                'max_tokens': 2000,
                'temperature': 0.7
            }
        }
    
    def test_ai_decision_with_crm_context(self, ai_service_config, mock_external_api):
        """Test AI decision generation with CRM context"""
        with patch('services.ai_integration.OpenAIClient') as mock_openai:
            mock_response = Mock()
            mock_response.content = json.dumps({
                'decision': 'Focus on high-value opportunities',
                'rationale': 'Based on CRM data showing $35K average deal size',
                'confidence_score': 0.85,
                'priority': 'high',
                'category': 'strategic',
                'risk_level': 'low'
            })
            
            mock_openai.return_value.generate_completion.return_value = mock_response
            
            ai_service = AIIntegrationService(ai_service_config)
            
            # Simulate CRM data context
            crm_context = [
                "Current pipeline shows 5 opportunities totaling $175,000",
                "Average deal size is $35,000",
                "Conversion rate is 60% in Q4"
            ]
            
            response = ai_service.generate_executive_response(
                executive_type='ceo',
                context='How should we prioritize our sales efforts?',
                document_context=crm_context
            )
            
            assert response.decision == 'Focus on high-value opportunities'
            assert 'CRM data' in response.rationale
            assert response.confidence_score == 0.85
    
    def test_ai_decision_with_erp_context(self, ai_service_config, mock_external_api):
        """Test AI decision generation with ERP context"""
        with patch('services.ai_integration.OpenAIClient') as mock_openai:
            mock_response = Mock()
            mock_response.content = json.dumps({
                'decision': 'Optimize inventory levels for Product A',
                'rationale': 'ERP data shows high inventory turnover and strong demand',
                'confidence_score': 0.9,
                'priority': 'medium',
                'category': 'operational',
                'risk_level': 'low'
            })
            
            mock_openai.return_value.generate_completion.return_value = mock_response
            
            ai_service = AIIntegrationService(ai_service_config)
            
            # Simulate ERP data context
            erp_context = [
                "Product A inventory: 100 units, turnover rate: 8x/year",
                "Product B inventory: 50 units, turnover rate: 4x/year",
                "Total inventory value: $12,500"
            ]
            
            response = ai_service.generate_executive_response(
                executive_type='cto',
                context='How should we manage our inventory?',
                document_context=erp_context
            )
            
            assert response.decision == 'Optimize inventory levels for Product A'
            assert 'ERP data' in response.rationale
            assert response.confidence_score == 0.9
    
    def test_ai_decision_with_combined_external_data(self, ai_service_config):
        """Test AI decision with combined external data sources"""
        with patch('services.ai_integration.OpenAIClient') as mock_openai:
            mock_response = Mock()
            mock_response.content = json.dumps({
                'decision': 'Increase marketing budget by 25% for Q1',
                'rationale': 'Combined CRM and financial data shows strong ROI potential',
                'confidence_score': 0.88,
                'priority': 'high',
                'category': 'strategic',
                'risk_level': 'medium',
                'financial_impact': 50000
            })
            
            mock_openai.return_value.generate_completion.return_value = mock_response
            
            ai_service = AIIntegrationService(ai_service_config)
            
            # Simulate combined context from multiple sources
            combined_context = [
                "CRM: Pipeline value increased 30% this quarter",
                "ERP: Marketing ROI currently at 4:1 ratio",
                "Financial: Available budget for marketing expansion: $75,000",
                "Market data: Competitor spending increased 20%"
            ]
            
            response = ai_service.generate_executive_response(
                executive_type='cfo',
                context='Should we increase our marketing investment?',
                document_context=combined_context
            )
            
            assert response.decision == 'Increase marketing budget by 25% for Q1'
            assert 'Combined CRM and financial data' in response.rationale
            assert response.financial_impact == 50000


@pytest.mark.integration
class TestExternalServiceErrorHandling:
    """Test error handling for external service integrations"""
    
    def test_network_timeout_handling(self):
        """Test handling of network timeouts"""
        config = {
            'crm': {
                'provider': 'salesforce',
                'api_url': 'https://api.salesforce.com',
                'timeout': 1  # Very short timeout
            }
        }
        
        crm_service = CRMIntegrationService(config)
        
        with patch('requests.post') as mock_post:
            mock_post.side_effect = requests.exceptions.Timeout("Request timed out")
            
            result = crm_service.authenticate()
            
            assert result is False
            assert crm_service.last_error is not None
            assert 'timeout' in crm_service.last_error.lower()
    
    def test_api_rate_limit_handling(self):
        """Test handling of API rate limits"""
        config = {
            'crm': {
                'provider': 'salesforce',
                'api_url': 'https://api.salesforce.com'
            }
        }
        
        crm_service = CRMIntegrationService(config)
        crm_service.access_token = 'test_token'
        
        mock_response = Mock()
        mock_response.status_code = 429  # Too Many Requests
        mock_response.headers = {'Retry-After': '60'}
        mock_response.json.return_value = {
            'error': 'rate_limit_exceeded',
            'message': 'API rate limit exceeded'
        }
        
        with patch('requests.get', return_value=mock_response):
            contacts = crm_service.get_contacts()
            
            assert contacts is None
            assert crm_service.last_error is not None
            assert 'rate limit' in crm_service.last_error.lower()
    
    def test_authentication_expiry_handling(self):
        """Test handling of expired authentication tokens"""
        config = {
            'erp': {
                'provider': 'quickbooks',
                'api_url': 'https://sandbox-quickbooks.api.intuit.com',
                'access_token': 'expired_token',
                'refresh_token': 'refresh_token'
            }
        }
        
        erp_service = ERPIntegrationService(config)
        
        # First request fails with 401 (expired token)
        expired_response = Mock()
        expired_response.status_code = 401
        expired_response.json.return_value = {
            'error': 'invalid_token',
            'message': 'Token has expired'
        }
        
        # Token refresh succeeds
        refresh_response = Mock()
        refresh_response.status_code = 200
        refresh_response.json.return_value = {
            'access_token': 'new_access_token',
            'refresh_token': 'new_refresh_token'
        }
        
        # Retry request succeeds
        success_response = Mock()
        success_response.status_code = 200
        success_response.json.return_value = {
            'QueryResponse': {
                'Item': [{'Id': '1', 'Name': 'Test Item'}]
            }
        }
        
        with patch('requests.get', side_effect=[expired_response, success_response]), \
             patch('requests.post', return_value=refresh_response):
            
            financial_data = erp_service.get_financial_data()
            
            assert financial_data is not None
            assert erp_service.access_token == 'new_access_token'


if __name__ == "__main__":
    pytest.main([__file__])