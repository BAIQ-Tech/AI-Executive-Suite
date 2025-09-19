"""
Tests for CRM Integration Service

Tests CRM system integration including Salesforce and HubSpot connectors,
customer data synchronization, and sales pipeline analysis.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import json

from services.crm_integration import (
    CRMIntegrationService,
    SalesforceConnector,
    HubSpotConnector,
    CRMProvider,
    Contact,
    Deal,
    Company,
    SalesPipelineMetrics
)
from services.integration_framework import APIResponse, SyncResult


@pytest.fixture
def mock_framework():
    """Mock integration framework"""
    framework = Mock()
    framework.register_integration = Mock()
    framework.make_request = Mock()
    framework.sync_data = Mock()
    framework.list_integrations = Mock(return_value=[])
    framework.shutdown = Mock()
    return framework


@pytest.fixture
def crm_config():
    """Sample CRM configuration"""
    return {
        'redis_url': 'redis://localhost:6379/0',
        'integrations': {
            'crm_enabled': True,
            'salesforce': {
                'client_id': 'test_client_id',
                'client_secret': 'test_client_secret',
                'access_token': 'test_access_token',
                'refresh_token': 'test_refresh_token',
                'instance_url': 'https://test.salesforce.com',
                'enabled': True
            },
            'hubspot': {
                'access_token': 'test_hubspot_token',
                'enabled': True
            }
        }
    }


@pytest.fixture
def sample_salesforce_contacts():
    """Sample Salesforce contact data"""
    return {
        'records': [
            {
                'Id': 'contact_1',
                'Email': 'john@example.com',
                'FirstName': 'John',
                'LastName': 'Doe',
                'Account': {'Name': 'Example Corp'},
                'Phone': '+1234567890',
                'Title': 'Manager',
                'CreatedDate': '2024-01-01T10:00:00.000Z',
                'LastModifiedDate': '2024-01-02T10:00:00.000Z',
                'LeadSource': 'Website'
            }
        ]
    }


@pytest.fixture
def sample_salesforce_deals():
    """Sample Salesforce opportunity data"""
    return {
        'records': [
            {
                'Id': 'deal_1',
                'Name': 'Big Deal',
                'Amount': 50000.0,
                'StageName': 'Proposal',
                'Probability': 75.0,
                'CloseDate': '2024-03-01',
                'CreatedDate': '2024-01-01T10:00:00.000Z',
                'LastModifiedDate': '2024-01-02T10:00:00.000Z',
                'AccountId': 'account_1',
                'OwnerId': 'owner_1',
                'LeadSource': 'Referral'
            }
        ]
    }


@pytest.fixture
def sample_hubspot_contacts():
    """Sample HubSpot contact data"""
    return {
        'results': [
            {
                'id': 'hubspot_contact_1',
                'properties': {
                    'email': 'jane@example.com',
                    'firstname': 'Jane',
                    'lastname': 'Smith',
                    'company': 'Test Company',
                    'phone': '+1987654321',
                    'jobtitle': 'Director',
                    'createdate': '1640995200000',  # 2022-01-01 in milliseconds
                    'lastmodifieddate': '1641081600000',  # 2022-01-02 in milliseconds
                    'lifecyclestage': 'customer',
                    'hubspotscore': '85',
                    'hs_lead_status': 'NEW'
                }
            }
        ]
    }


class TestSalesforceConnector:
    """Test Salesforce connector functionality"""
    
    def test_setup_integration(self, mock_framework):
        """Test Salesforce integration setup"""
        connector = SalesforceConnector(mock_framework)
        
        config = {
            'client_id': 'test_client',
            'client_secret': 'test_secret',
            'access_token': 'test_token',
            'refresh_token': 'test_refresh',
            'instance_url': 'https://test.salesforce.com',
            'enabled': True
        }
        
        connector.setup_integration(config)
        
        mock_framework.register_integration.assert_called_once()
        integration_config = mock_framework.register_integration.call_args[0][0]
        assert integration_config.name == "salesforce"
        assert integration_config.base_url == "https://test.salesforce.com/services/data/v58.0"
        
    def test_get_contacts_success(self, mock_framework, sample_salesforce_contacts):
        """Test successful contact retrieval from Salesforce"""
        connector = SalesforceConnector(mock_framework)
        
        mock_response = APIResponse(
            success=True,
            status_code=200,
            data=sample_salesforce_contacts
        )
        mock_framework.make_request.return_value = mock_response
        
        contacts = connector.get_contacts(limit=10)
        
        assert len(contacts) == 1
        contact = contacts[0]
        assert contact.id == 'contact_1'
        assert contact.email == 'john@example.com'
        assert contact.first_name == 'John'
        assert contact.last_name == 'Doe'
        assert contact.company == 'Example Corp'
        
    def test_get_contacts_failure(self, mock_framework):
        """Test failed contact retrieval from Salesforce"""
        connector = SalesforceConnector(mock_framework)
        
        mock_response = APIResponse(
            success=False,
            status_code=401,
            error="Unauthorized"
        )
        mock_framework.make_request.return_value = mock_response
        
        contacts = connector.get_contacts()
        
        assert len(contacts) == 0
        
    def test_get_deals_success(self, mock_framework, sample_salesforce_deals):
        """Test successful deal retrieval from Salesforce"""
        connector = SalesforceConnector(mock_framework)
        
        mock_response = APIResponse(
            success=True,
            status_code=200,
            data=sample_salesforce_deals
        )
        mock_framework.make_request.return_value = mock_response
        
        deals = connector.get_deals(limit=10)
        
        assert len(deals) == 1
        deal = deals[0]
        assert deal.id == 'deal_1'
        assert deal.name == 'Big Deal'
        assert deal.amount == 50000.0
        assert deal.stage == 'Proposal'
        assert deal.probability == 75.0
        
    def test_parse_salesforce_date(self, mock_framework):
        """Test Salesforce date parsing"""
        connector = SalesforceConnector(mock_framework)
        
        # Test valid date
        date_str = '2024-01-01T10:00:00.000Z'
        parsed_date = connector._parse_salesforce_date(date_str)
        assert parsed_date is not None
        assert parsed_date.year == 2024
        assert parsed_date.month == 1
        assert parsed_date.day == 1
        
        # Test None date
        assert connector._parse_salesforce_date(None) is None
        
        # Test invalid date
        assert connector._parse_salesforce_date('invalid') is None


class TestHubSpotConnector:
    """Test HubSpot connector functionality"""
    
    def test_setup_integration(self, mock_framework):
        """Test HubSpot integration setup"""
        connector = HubSpotConnector(mock_framework)
        
        config = {
            'access_token': 'test_hubspot_token',
            'enabled': True
        }
        
        connector.setup_integration(config)
        
        mock_framework.register_integration.assert_called_once()
        integration_config = mock_framework.register_integration.call_args[0][0]
        assert integration_config.name == "hubspot"
        assert integration_config.base_url == "https://api.hubapi.com"
        
    def test_get_contacts_success(self, mock_framework, sample_hubspot_contacts):
        """Test successful contact retrieval from HubSpot"""
        connector = HubSpotConnector(mock_framework)
        
        mock_response = APIResponse(
            success=True,
            status_code=200,
            data=sample_hubspot_contacts
        )
        mock_framework.make_request.return_value = mock_response
        
        contacts = connector.get_contacts(limit=10)
        
        assert len(contacts) == 1
        contact = contacts[0]
        assert contact.id == 'hubspot_contact_1'
        assert contact.email == 'jane@example.com'
        assert contact.first_name == 'Jane'
        assert contact.last_name == 'Smith'
        assert contact.company == 'Test Company'
        assert contact.lifecycle_stage == 'customer'
        assert contact.lead_score == 85
        
    def test_parse_hubspot_date(self, mock_framework):
        """Test HubSpot date parsing"""
        connector = HubSpotConnector(mock_framework)
        
        # Test valid timestamp (milliseconds)
        timestamp_str = '1640995200000'  # 2022-01-01
        parsed_date = connector._parse_hubspot_date(timestamp_str)
        assert parsed_date is not None
        assert parsed_date.year == 2022
        assert parsed_date.month == 1
        assert parsed_date.day == 1
        
        # Test None timestamp
        assert connector._parse_hubspot_date(None) is None
        
        # Test invalid timestamp
        assert connector._parse_hubspot_date('invalid') is None


class TestCRMIntegrationService:
    """Test CRM integration service functionality"""
    
    @patch('services.crm_integration.IntegrationFramework')
    def test_service_initialization(self, mock_framework_class, crm_config):
        """Test CRM integration service initialization"""
        mock_framework = Mock()
        mock_framework_class.return_value = mock_framework
        
        service = CRMIntegrationService(crm_config)
        
        assert service.salesforce is not None
        assert service.hubspot is not None
        assert 'salesforce' in service.connectors
        assert 'hubspot' in service.connectors
        
    @patch('services.crm_integration.IntegrationFramework')
    def test_sync_crm_data_success(self, mock_framework_class, crm_config, sample_salesforce_contacts, sample_salesforce_deals):
        """Test successful CRM data synchronization"""
        mock_framework = Mock()
        mock_framework_class.return_value = mock_framework
        
        # Mock sync_data to call the sync function
        def mock_sync_data(integration_name, sync_function, force_full_sync=False):
            context = {'integration': None, 'sync_strategy': None, 'last_sync_timestamp': None, 'framework': mock_framework}
            return sync_function(context)
            
        mock_framework.sync_data = mock_sync_data
        
        service = CRMIntegrationService(crm_config)
        
        # Mock connector methods
        service.salesforce.get_contacts = Mock(return_value=[Contact(id='1', email='test@example.com')])
        service.salesforce.get_deals = Mock(return_value=[Deal(id='1', name='Test Deal')])
        service.salesforce.get_companies = Mock(return_value=[Company(id='1', name='Test Company')])
        
        result = service.sync_crm_data(CRMProvider.SALESFORCE)
        
        assert result.success is True
        assert result.records_processed == 3  # 1 contact + 1 deal + 1 company
        
    @patch('services.crm_integration.IntegrationFramework')
    def test_get_sales_pipeline_metrics(self, mock_framework_class, crm_config):
        """Test sales pipeline metrics calculation"""
        mock_framework = Mock()
        mock_framework_class.return_value = mock_framework
        
        service = CRMIntegrationService(crm_config)
        
        # Create sample deals
        sample_deals = [
            Deal(
                id='1',
                name='Deal 1',
                amount=10000.0,
                stage='Proposal',
                probability=50.0,
                created_date=datetime.now() - timedelta(days=30),
                close_date=datetime.now() + timedelta(days=30)
            ),
            Deal(
                id='2',
                name='Deal 2',
                amount=20000.0,
                stage='Closed Won',
                probability=100.0,
                created_date=datetime.now() - timedelta(days=60),
                close_date=datetime.now() - timedelta(days=10)
            )
        ]
        
        service.salesforce.get_deals = Mock(return_value=sample_deals)
        
        metrics = service.get_sales_pipeline_metrics(CRMProvider.SALESFORCE)
        
        assert metrics is not None
        assert metrics.total_deals == 2
        assert metrics.total_value == 30000.0
        assert metrics.average_deal_size == 15000.0
        assert 'Proposal' in metrics.deals_by_stage
        assert 'Closed Won' in metrics.deals_by_stage
        
    @patch('services.crm_integration.IntegrationFramework')
    def test_get_crm_context_for_ai(self, mock_framework_class, crm_config):
        """Test getting CRM context for AI decisions"""
        mock_framework = Mock()
        mock_framework_class.return_value = mock_framework
        
        service = CRMIntegrationService(crm_config)
        
        # Mock get_sales_pipeline_metrics
        mock_metrics = SalesPipelineMetrics(
            total_deals=10,
            total_value=100000.0,
            average_deal_size=10000.0,
            conversion_rate=25.0,
            average_sales_cycle=45,
            deals_by_stage={'Proposal': 5, 'Closed Won': 2},
            value_by_stage={'Proposal': 50000.0, 'Closed Won': 20000.0},
            monthly_trends={},
            top_sources=[],
            forecast={'pipeline_value': 80000.0, 'weighted_value': 40000.0}
        )
        
        service.get_sales_pipeline_metrics = Mock(return_value=mock_metrics)
        
        context = service.get_crm_context_for_ai(CRMProvider.SALESFORCE, "summary")
        
        assert context['crm_provider'] == 'salesforce'
        assert context['total_deals'] == 10
        assert context['total_pipeline_value'] == 100000.0
        assert context['average_deal_size'] == 10000.0
        assert context['conversion_rate'] == 25.0
        assert context['forecast_pipeline_value'] == 80000.0
        
    @patch('services.crm_integration.IntegrationFramework')
    def test_get_integration_status(self, mock_framework_class, crm_config):
        """Test getting integration status"""
        mock_framework = Mock()
        mock_framework.list_integrations.return_value = [
            {'name': 'salesforce', 'enabled': True},
            {'name': 'hubspot', 'enabled': True}
        ]
        mock_framework_class.return_value = mock_framework
        
        service = CRMIntegrationService(crm_config)
        
        # Mock connector methods to return empty lists (successful test)
        service.salesforce.get_contacts = Mock(return_value=[])
        service.hubspot.get_contacts = Mock(return_value=[])
        
        status = service.get_integration_status()
        
        assert 'framework_status' in status
        assert 'connectors' in status
        assert 'salesforce' in status['connectors']
        assert 'hubspot' in status['connectors']
        assert status['connectors']['salesforce']['available'] is True
        assert status['connectors']['hubspot']['available'] is True
        
    @patch('services.crm_integration.IntegrationFramework')
    def test_shutdown(self, mock_framework_class, crm_config):
        """Test service shutdown"""
        mock_framework = Mock()
        mock_framework_class.return_value = mock_framework
        
        service = CRMIntegrationService(crm_config)
        service.shutdown()
        
        mock_framework.shutdown.assert_called_once()


class TestDataModels:
    """Test CRM data models"""
    
    def test_contact_model(self):
        """Test Contact data model"""
        contact = Contact(
            id='test_id',
            email='test@example.com',
            first_name='John',
            last_name='Doe',
            company='Test Corp',
            phone='+1234567890',
            title='Manager',
            created_date=datetime.now(),
            lifecycle_stage='customer',
            lead_score=85,
            source='Website'
        )
        
        assert contact.id == 'test_id'
        assert contact.email == 'test@example.com'
        assert contact.first_name == 'John'
        assert contact.last_name == 'Doe'
        assert contact.company == 'Test Corp'
        assert contact.lifecycle_stage == 'customer'
        assert contact.lead_score == 85
        
    def test_deal_model(self):
        """Test Deal data model"""
        deal = Deal(
            id='deal_id',
            name='Big Deal',
            amount=50000.0,
            stage='Proposal',
            probability=75.0,
            close_date=datetime.now() + timedelta(days=30),
            created_date=datetime.now(),
            contact_id='contact_1',
            company_id='company_1',
            owner_id='owner_1',
            source='Referral'
        )
        
        assert deal.id == 'deal_id'
        assert deal.name == 'Big Deal'
        assert deal.amount == 50000.0
        assert deal.stage == 'Proposal'
        assert deal.probability == 75.0
        assert deal.source == 'Referral'
        
    def test_company_model(self):
        """Test Company data model"""
        company = Company(
            id='company_id',
            name='Test Corporation',
            domain='test.com',
            industry='Technology',
            size='100-500',
            annual_revenue=1000000.0,
            phone='+1234567890',
            address='123 Test St, Test City, TC 12345',
            created_date=datetime.now(),
            lifecycle_stage='customer'
        )
        
        assert company.id == 'company_id'
        assert company.name == 'Test Corporation'
        assert company.domain == 'test.com'
        assert company.industry == 'Technology'
        assert company.size == '100-500'
        assert company.annual_revenue == 1000000.0


if __name__ == '__main__':
    pytest.main([__file__])