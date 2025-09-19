"""
Tests for ERP Integration Service

Tests ERP system integration including QuickBooks and SAP connectors,
financial data synchronization, and automated financial reporting.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from decimal import Decimal

from services.erp_integration import (
    ERPIntegrationService,
    QuickBooksConnector,
    SAPConnector,
    ERPProvider,
    TransactionType,
    Account,
    Transaction,
    Customer,
    Vendor,
    FinancialReport,
    ERPMetrics
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
def erp_config():
    """Sample ERP configuration"""
    return {
        'redis_url': 'redis://localhost:6379/0',
        'integrations': {
            'erp_enabled': True,
            'quickbooks': {
                'client_id': 'test_client_id',
                'client_secret': 'test_client_secret',
                'access_token': 'test_access_token',
                'refresh_token': 'test_refresh_token',
                'company_id': 'test_company_id',
                'production': False,
                'enabled': True
            },
            'sap': {
                'username': 'test_user',
                'password': 'test_password',
                'base_url': 'https://test.sap.com',
                'enabled': True
            }
        }
    }


@pytest.fixture
def sample_quickbooks_accounts():
    """Sample QuickBooks account data"""
    return {
        'QueryResponse': {
            'Account': [
                {
                    'Id': '1',
                    'Name': 'Checking Account',
                    'AccountType': 'Bank',
                    'AcctNum': '1000',
                    'CurrentBalance': 50000.00,
                    'Active': True,
                    'MetaData': {
                        'CreateTime': '2024-01-01T10:00:00-08:00',
                        'LastUpdatedTime': '2024-01-02T10:00:00-08:00'
                    }
                }
            ]
        }
    }


@pytest.fixture
def sample_quickbooks_invoices():
    """Sample QuickBooks invoice data"""
    return {
        'QueryResponse': {
            'Invoice': [
                {
                    'Id': 'inv_1',
                    'TotalAmt': 1000.00,
                    'TxnDate': '2024-01-15',
                    'DocNumber': 'INV-001',
                    'PrivateNote': 'Test invoice',
                    'CustomerRef': {'value': 'cust_1'},
                    'TxnStatus': 'Pending',
                    'MetaData': {
                        'CreateTime': '2024-01-15T10:00:00-08:00',
                        'LastUpdatedTime': '2024-01-15T10:00:00-08:00'
                    },
                    'Line': [
                        {
                            'Amount': 1000.00,
                            'DetailType': 'SalesItemLineDetail',
                            'SalesItemLineDetail': {
                                'ItemRef': {'value': 'item_1'}
                            }
                        }
                    ]
                }
            ]
        }
    }


@pytest.fixture
def sample_quickbooks_customers():
    """Sample QuickBooks customer data"""
    return {
        'QueryResponse': {
            'Customer': [
                {
                    'Id': 'cust_1',
                    'Name': 'Test Customer',
                    'PrimaryEmailAddr': {'Address': 'customer@test.com'},
                    'PrimaryPhone': {'FreeFormNumber': '+1234567890'},
                    'BillAddr': {
                        'Line1': '123 Test St',
                        'City': 'Test City',
                        'CountrySubDivisionCode': 'CA',
                        'PostalCode': '12345'
                    },
                    'Balance': 500.00,
                    'Active': True,
                    'MetaData': {
                        'CreateTime': '2024-01-01T10:00:00-08:00',
                        'LastUpdatedTime': '2024-01-02T10:00:00-08:00'
                    }
                }
            ]
        }
    }


class TestQuickBooksConnector:
    """Test QuickBooks connector functionality"""
    
    def test_setup_integration(self, mock_framework):
        """Test QuickBooks integration setup"""
        connector = QuickBooksConnector(mock_framework)
        
        config = {
            'client_id': 'test_client',
            'client_secret': 'test_secret',
            'access_token': 'test_token',
            'refresh_token': 'test_refresh',
            'company_id': 'test_company',
            'production': False,
            'enabled': True
        }
        
        connector.setup_integration(config)
        
        mock_framework.register_integration.assert_called_once()
        integration_config = mock_framework.register_integration.call_args[0][0]
        assert integration_config.name == "quickbooks"
        assert "sandbox-quickbooks.api.intuit.com" in integration_config.base_url
        
    def test_get_accounts_success(self, mock_framework, sample_quickbooks_accounts):
        """Test successful account retrieval from QuickBooks"""
        connector = QuickBooksConnector(mock_framework)
        
        mock_response = APIResponse(
            success=True,
            status_code=200,
            data=sample_quickbooks_accounts
        )
        mock_framework.make_request.return_value = mock_response
        
        accounts = connector.get_accounts()
        
        assert len(accounts) == 1
        account = accounts[0]
        assert account.id == '1'
        assert account.name == 'Checking Account'
        assert account.account_type == 'Bank'
        assert account.account_number == '1000'
        assert account.balance == Decimal('50000.00')
        assert account.is_active is True
        
    def test_get_accounts_failure(self, mock_framework):
        """Test failed account retrieval from QuickBooks"""
        connector = QuickBooksConnector(mock_framework)
        
        mock_response = APIResponse(
            success=False,
            status_code=401,
            error="Unauthorized"
        )
        mock_framework.make_request.return_value = mock_response
        
        accounts = connector.get_accounts()
        
        assert len(accounts) == 0
        
    def test_get_transactions_success(self, mock_framework, sample_quickbooks_invoices):
        """Test successful transaction retrieval from QuickBooks"""
        connector = QuickBooksConnector(mock_framework)
        
        mock_response = APIResponse(
            success=True,
            status_code=200,
            data=sample_quickbooks_invoices
        )
        mock_framework.make_request.return_value = mock_response
        
        transactions = connector.get_transactions(TransactionType.INVOICE)
        
        assert len(transactions) == 1
        transaction = transactions[0]
        assert transaction.id == 'inv_1'
        assert transaction.transaction_type == TransactionType.INVOICE
        assert transaction.amount == Decimal('1000.00')
        assert transaction.reference_number == 'INV-001'
        assert transaction.customer_id == 'cust_1'
        assert transaction.status == 'Pending'
        
    def test_get_customers_success(self, mock_framework, sample_quickbooks_customers):
        """Test successful customer retrieval from QuickBooks"""
        connector = QuickBooksConnector(mock_framework)
        
        mock_response = APIResponse(
            success=True,
            status_code=200,
            data=sample_quickbooks_customers
        )
        mock_framework.make_request.return_value = mock_response
        
        customers = connector.get_customers()
        
        assert len(customers) == 1
        customer = customers[0]
        assert customer.id == 'cust_1'
        assert customer.name == 'Test Customer'
        assert customer.email == 'customer@test.com'
        assert customer.phone == '+1234567890'
        assert customer.balance == Decimal('500.00')
        assert "123 Test St" in customer.address
        
    def test_parse_quickbooks_date(self, mock_framework):
        """Test QuickBooks date parsing"""
        connector = QuickBooksConnector(mock_framework)
        
        # Test ISO format with timezone
        date_str = '2024-01-01T10:00:00-08:00'
        parsed_date = connector._parse_quickbooks_date(date_str)
        assert parsed_date is not None
        assert parsed_date.year == 2024
        assert parsed_date.month == 1
        assert parsed_date.day == 1
        
        # Test date only format
        date_str = '2024-01-01'
        parsed_date = connector._parse_quickbooks_date(date_str)
        assert parsed_date is not None
        assert parsed_date.year == 2024
        
        # Test None date
        assert connector._parse_quickbooks_date(None) is None
        
        # Test invalid date
        assert connector._parse_quickbooks_date('invalid') is None


class TestSAPConnector:
    """Test SAP connector functionality"""
    
    def test_setup_integration(self, mock_framework):
        """Test SAP integration setup"""
        connector = SAPConnector(mock_framework)
        
        config = {
            'username': 'test_user',
            'password': 'test_password',
            'base_url': 'https://test.sap.com',
            'enabled': True
        }
        
        connector.setup_integration(config)
        
        mock_framework.register_integration.assert_called_once()
        integration_config = mock_framework.register_integration.call_args[0][0]
        assert integration_config.name == "sap"
        assert integration_config.base_url == "https://test.sap.com"
        
    def test_get_accounts_success(self, mock_framework):
        """Test successful account retrieval from SAP"""
        connector = SAPConnector(mock_framework)
        
        sample_sap_accounts = {
            'd': {
                'results': [
                    {
                        'GLAccount': '1000',
                        'GLAccountName': 'Cash Account',
                        'GLAccountType': 'Assets',
                        'IsBlocked': '',
                        'CreationDate': '/Date(1640995200000)/',
                        'LastChangeDate': '/Date(1641081600000)/'
                    }
                ]
            }
        }
        
        mock_response = APIResponse(
            success=True,
            status_code=200,
            data=sample_sap_accounts
        )
        mock_framework.make_request.return_value = mock_response
        
        accounts = connector.get_accounts()
        
        assert len(accounts) == 1
        account = accounts[0]
        assert account.id == '1000'
        assert account.name == 'Cash Account'
        assert account.account_type == 'Assets'
        assert account.is_active is True
        
    def test_parse_sap_date(self, mock_framework):
        """Test SAP date parsing"""
        connector = SAPConnector(mock_framework)
        
        # Test SAP /Date(timestamp)/ format
        date_str = '/Date(1640995200000)/'  # 2022-01-01
        parsed_date = connector._parse_sap_date(date_str)
        assert parsed_date is not None
        assert parsed_date.year == 2022
        assert parsed_date.month == 1
        assert parsed_date.day == 1
        
        # Test None date
        assert connector._parse_sap_date(None) is None
        
        # Test invalid date
        assert connector._parse_sap_date('invalid') is None


class TestERPIntegrationService:
    """Test ERP integration service functionality"""
    
    @patch('services.erp_integration.IntegrationFramework')
    def test_service_initialization(self, mock_framework_class, erp_config):
        """Test ERP integration service initialization"""
        mock_framework = Mock()
        mock_framework_class.return_value = mock_framework
        
        service = ERPIntegrationService(erp_config)
        
        assert service.quickbooks is not None
        assert service.sap is not None
        assert 'quickbooks' in service.connectors
        assert 'sap' in service.connectors
        
    @patch('services.erp_integration.IntegrationFramework')
    def test_sync_erp_data_success(self, mock_framework_class, erp_config):
        """Test successful ERP data synchronization"""
        mock_framework = Mock()
        mock_framework_class.return_value = mock_framework
        
        # Mock sync_data to call the sync function
        def mock_sync_data(integration_name, sync_function, force_full_sync=False):
            context = {'integration': None, 'sync_strategy': None, 'last_sync_timestamp': None, 'framework': mock_framework}
            return sync_function(context)
            
        mock_framework.sync_data = mock_sync_data
        
        service = ERPIntegrationService(erp_config)
        
        # Mock connector methods
        service.quickbooks.get_accounts = Mock(return_value=[Account(id='1', name='Test Account', account_type='Bank')])
        service.quickbooks.get_customers = Mock(return_value=[Customer(id='1', name='Test Customer')])
        service.quickbooks.get_vendors = Mock(return_value=[Vendor(id='1', name='Test Vendor')])
        service.quickbooks.get_transactions = Mock(return_value=[Transaction(id='1', transaction_type=TransactionType.INVOICE, amount=Decimal('1000'))])
        
        result = service.sync_erp_data(ERPProvider.QUICKBOOKS)
        
        assert result.success is True
        assert result.records_processed > 0
        
    @patch('services.erp_integration.IntegrationFramework')
    def test_get_erp_metrics(self, mock_framework_class, erp_config):
        """Test ERP metrics calculation"""
        mock_framework = Mock()
        mock_framework_class.return_value = mock_framework
        
        service = ERPIntegrationService(erp_config)
        
        # Create sample transactions
        sample_invoices = [
            Transaction(
                id='1',
                transaction_type=TransactionType.INVOICE,
                amount=Decimal('1000'),
                date=datetime.now() - timedelta(days=10),
                status='Pending'
            ),
            Transaction(
                id='2',
                transaction_type=TransactionType.INVOICE,
                amount=Decimal('2000'),
                date=datetime.now() - timedelta(days=20),
                status='Paid'
            )
        ]
        
        sample_expenses = [
            Transaction(
                id='3',
                transaction_type=TransactionType.EXPENSE,
                amount=Decimal('500'),
                date=datetime.now() - timedelta(days=15),
                status='Paid'
            )
        ]
        
        service.quickbooks.get_transactions = Mock(side_effect=lambda tx_type, limit=100: 
            sample_invoices if tx_type == TransactionType.INVOICE else sample_expenses)
        service.quickbooks.get_customers = Mock(return_value=[Customer(id='1', name='Customer 1', is_active=True)])
        service.quickbooks.get_vendors = Mock(return_value=[Vendor(id='1', name='Vendor 1', is_active=True)])
        
        metrics = service.get_erp_metrics(ERPProvider.QUICKBOOKS)
        
        assert metrics is not None
        assert metrics.total_revenue == Decimal('3000')
        assert metrics.total_expenses == Decimal('500')
        assert metrics.net_income == Decimal('2500')
        assert metrics.customer_count == 1
        assert metrics.vendor_count == 1
        assert metrics.outstanding_invoices == 1  # One pending invoice
        
    @patch('services.erp_integration.IntegrationFramework')
    def test_get_erp_context_for_ai(self, mock_framework_class, erp_config):
        """Test getting ERP context for AI decisions"""
        mock_framework = Mock()
        mock_framework_class.return_value = mock_framework
        
        service = ERPIntegrationService(erp_config)
        
        # Mock get_erp_metrics
        mock_metrics = ERPMetrics(
            total_revenue=Decimal('10000'),
            total_expenses=Decimal('6000'),
            net_income=Decimal('4000'),
            cash_flow=Decimal('4000'),
            accounts_receivable=Decimal('2000'),
            accounts_payable=Decimal('1000'),
            customer_count=5,
            vendor_count=3,
            outstanding_invoices=10,
            overdue_invoices=2
        )
        
        service.get_erp_metrics = Mock(return_value=mock_metrics)
        
        context = service.get_erp_context_for_ai(ERPProvider.QUICKBOOKS, "summary")
        
        assert context['erp_provider'] == 'quickbooks'
        assert context['total_revenue'] == 10000.0
        assert context['total_expenses'] == 6000.0
        assert context['net_income'] == 4000.0
        assert context['customer_count'] == 5
        assert context['vendor_count'] == 3
        assert context['outstanding_invoices'] == 10
        assert context['overdue_invoices'] == 2
        
    @patch('services.erp_integration.IntegrationFramework')
    def test_get_financial_health_context(self, mock_framework_class, erp_config):
        """Test getting financial health context for AI"""
        mock_framework = Mock()
        mock_framework_class.return_value = mock_framework
        
        service = ERPIntegrationService(erp_config)
        
        # Mock get_erp_metrics
        mock_metrics = ERPMetrics(
            total_revenue=Decimal('10000'),
            total_expenses=Decimal('8000'),
            net_income=Decimal('2000'),
            cash_flow=Decimal('2000'),
            accounts_receivable=Decimal('1000'),
            accounts_payable=Decimal('500'),
            outstanding_invoices=10,
            overdue_invoices=1
        )
        
        service.get_erp_metrics = Mock(return_value=mock_metrics)
        
        context = service.get_erp_context_for_ai(ERPProvider.QUICKBOOKS, "financial_health")
        
        assert context['erp_provider'] == 'quickbooks'
        assert context['revenue_to_expense_ratio'] == 1.25  # 10000/8000
        assert context['overdue_invoice_percentage'] == 10.0  # 1/10 * 100
        assert context['cash_flow_positive'] is True
        assert context['net_profit_margin'] == 20.0  # 2000/10000 * 100
        
    @patch('services.erp_integration.IntegrationFramework')
    def test_get_integration_status(self, mock_framework_class, erp_config):
        """Test getting integration status"""
        mock_framework = Mock()
        mock_framework.list_integrations.return_value = [
            {'name': 'quickbooks', 'enabled': True},
            {'name': 'sap', 'enabled': True}
        ]
        mock_framework_class.return_value = mock_framework
        
        service = ERPIntegrationService(erp_config)
        
        # Mock connector methods to return empty lists (successful test)
        service.quickbooks.get_accounts = Mock(return_value=[])
        service.sap.get_accounts = Mock(return_value=[])
        
        status = service.get_integration_status()
        
        assert 'framework_status' in status
        assert 'connectors' in status
        assert 'quickbooks' in status['connectors']
        assert 'sap' in status['connectors']
        assert status['connectors']['quickbooks']['available'] is True
        assert status['connectors']['sap']['available'] is True
        
    @patch('services.erp_integration.IntegrationFramework')
    def test_shutdown(self, mock_framework_class, erp_config):
        """Test service shutdown"""
        mock_framework = Mock()
        mock_framework_class.return_value = mock_framework
        
        service = ERPIntegrationService(erp_config)
        service.shutdown()
        
        mock_framework.shutdown.assert_called_once()


class TestDataModels:
    """Test ERP data models"""
    
    def test_account_model(self):
        """Test Account data model"""
        account = Account(
            id='1000',
            name='Checking Account',
            account_type='Bank',
            account_number='1000',
            balance=Decimal('50000.00'),
            currency='USD',
            is_active=True
        )
        
        assert account.id == '1000'
        assert account.name == 'Checking Account'
        assert account.account_type == 'Bank'
        assert account.balance == Decimal('50000.00')
        assert account.currency == 'USD'
        assert account.is_active is True
        
    def test_transaction_model(self):
        """Test Transaction data model"""
        transaction = Transaction(
            id='tx_1',
            transaction_type=TransactionType.INVOICE,
            amount=Decimal('1000.00'),
            currency='USD',
            date=datetime.now(),
            description='Test transaction',
            reference_number='INV-001',
            customer_id='cust_1',
            status='Pending'
        )
        
        assert transaction.id == 'tx_1'
        assert transaction.transaction_type == TransactionType.INVOICE
        assert transaction.amount == Decimal('1000.00')
        assert transaction.currency == 'USD'
        assert transaction.reference_number == 'INV-001'
        assert transaction.status == 'Pending'
        
    def test_customer_model(self):
        """Test Customer data model"""
        customer = Customer(
            id='cust_1',
            name='Test Customer',
            email='customer@test.com',
            phone='+1234567890',
            address='123 Test St',
            balance=Decimal('500.00'),
            credit_limit=Decimal('5000.00'),
            is_active=True
        )
        
        assert customer.id == 'cust_1'
        assert customer.name == 'Test Customer'
        assert customer.email == 'customer@test.com'
        assert customer.balance == Decimal('500.00')
        assert customer.credit_limit == Decimal('5000.00')
        assert customer.is_active is True
        
    def test_vendor_model(self):
        """Test Vendor data model"""
        vendor = Vendor(
            id='vendor_1',
            name='Test Vendor',
            email='vendor@test.com',
            phone='+1987654321',
            address='456 Vendor Ave',
            balance=Decimal('1000.00'),
            is_active=True
        )
        
        assert vendor.id == 'vendor_1'
        assert vendor.name == 'Test Vendor'
        assert vendor.email == 'vendor@test.com'
        assert vendor.balance == Decimal('1000.00')
        assert vendor.is_active is True
        
    def test_financial_report_model(self):
        """Test FinancialReport data model"""
        report = FinancialReport(
            report_type='profit_loss',
            period_start=datetime(2024, 1, 1),
            period_end=datetime(2024, 1, 31),
            currency='USD',
            data={'revenue': 10000, 'expenses': 6000},
            generated_at=datetime.now()
        )
        
        assert report.report_type == 'profit_loss'
        assert report.period_start.year == 2024
        assert report.period_end.month == 1
        assert report.currency == 'USD'
        assert report.data['revenue'] == 10000


if __name__ == '__main__':
    pytest.main([__file__])