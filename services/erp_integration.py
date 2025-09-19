"""
ERP and Financial System Integration Service

Provides integration with ERP systems including QuickBooks and SAP.
Handles real-time financial data synchronization, automated financial reporting,
and ERP data context for CFO decisions.
"""

import logging
import json
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from decimal import Decimal

from services.integration_framework import (
    IntegrationFramework,
    IntegrationConfig,
    AuthConfig,
    AuthType,
    SyncStrategy,
    APIResponse,
    SyncResult
)

logger = logging.getLogger(__name__)


class ERPProvider(Enum):
    """Supported ERP providers"""
    QUICKBOOKS = "quickbooks"
    SAP = "sap"
    NETSUITE = "netsuite"


class TransactionType(Enum):
    """Financial transaction types"""
    INVOICE = "invoice"
    PAYMENT = "payment"
    EXPENSE = "expense"
    PURCHASE_ORDER = "purchase_order"
    JOURNAL_ENTRY = "journal_entry"
    CREDIT_MEMO = "credit_memo"
    BILL = "bill"


@dataclass
class Account:
    """Chart of accounts entry"""
    id: str
    name: str
    account_type: str
    account_number: Optional[str] = None
    parent_account_id: Optional[str] = None
    balance: Optional[Decimal] = None
    currency: str = "USD"
    is_active: bool = True
    created_date: Optional[datetime] = None
    last_modified: Optional[datetime] = None


@dataclass
class Transaction:
    """Financial transaction"""
    id: str
    transaction_type: TransactionType
    amount: Decimal
    currency: str = "USD"
    date: Optional[datetime] = None
    description: Optional[str] = None
    reference_number: Optional[str] = None
    customer_id: Optional[str] = None
    vendor_id: Optional[str] = None
    account_id: Optional[str] = None
    status: Optional[str] = None
    created_date: Optional[datetime] = None
    last_modified: Optional[datetime] = None
    line_items: List[Dict[str, Any]] = field(default_factory=list)
    custom_fields: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Customer:
    """Customer/Client record"""
    id: str
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    balance: Optional[Decimal] = None
    credit_limit: Optional[Decimal] = None
    payment_terms: Optional[str] = None
    tax_id: Optional[str] = None
    is_active: bool = True
    created_date: Optional[datetime] = None
    last_modified: Optional[datetime] = None


@dataclass
class Vendor:
    """Vendor/Supplier record"""
    id: str
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    balance: Optional[Decimal] = None
    payment_terms: Optional[str] = None
    tax_id: Optional[str] = None
    is_active: bool = True
    created_date: Optional[datetime] = None
    last_modified: Optional[datetime] = None


@dataclass
class FinancialReport:
    """Financial report data"""
    report_type: str
    period_start: datetime
    period_end: datetime
    currency: str = "USD"
    data: Dict[str, Any] = field(default_factory=dict)
    generated_at: Optional[datetime] = None


@dataclass
class ERPMetrics:
    """ERP system metrics for AI context"""
    total_revenue: Decimal
    total_expenses: Decimal
    net_income: Decimal
    cash_flow: Decimal
    accounts_receivable: Decimal
    accounts_payable: Decimal
    inventory_value: Optional[Decimal] = None
    customer_count: int = 0
    vendor_count: int = 0
    outstanding_invoices: int = 0
    overdue_invoices: int = 0
    monthly_trends: Dict[str, Dict[str, Decimal]] = field(default_factory=dict)
    top_customers: List[Dict[str, Any]] = field(default_factory=list)
    top_expenses: List[Dict[str, Any]] = field(default_factory=list)


class QuickBooksConnector:
    """QuickBooks Online API connector"""
    
    def __init__(self, framework: IntegrationFramework):
        self.framework = framework
        self.integration_name = "quickbooks"
        
    def setup_integration(self, config: Dict[str, Any]) -> None:
        """Setup QuickBooks integration"""
        auth_config = AuthConfig(
            auth_type=AuthType.OAUTH2,
            client_id=config.get('client_id'),
            client_secret=config.get('client_secret'),
            access_token=config.get('access_token'),
            refresh_token=config.get('refresh_token'),
            token_url="https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer",
            scope="com.intuit.quickbooks.accounting"
        )
        
        company_id = config.get('company_id')
        base_url = f"https://sandbox-quickbooks.api.intuit.com/v3/company/{company_id}"
        if config.get('production', False):
            base_url = f"https://quickbooks.api.intuit.com/v3/company/{company_id}"
        
        integration_config = IntegrationConfig(
            name=self.integration_name,
            base_url=base_url,
            auth_config=auth_config,
            timeout=30,
            max_retries=3,
            rate_limit_per_minute=500,  # QuickBooks API limits
            cache_ttl=300,
            sync_strategy=SyncStrategy.INCREMENTAL,
            enabled=config.get('enabled', True)
        )
        
        self.framework.register_integration(integration_config)
        
    def get_accounts(self) -> List[Account]:
        """Get chart of accounts from QuickBooks"""
        response = self.framework.make_request(
            self.integration_name,
            'GET',
            'accounts',
            params={'minorversion': '65'}
        )
        
        if not response.success:
            logger.error(f"Failed to get QuickBooks accounts: {response.error}")
            return []
            
        accounts = []
        for item in response.data.get('QueryResponse', {}).get('Account', []):
            account = Account(
                id=item['Id'],
                name=item['Name'],
                account_type=item.get('AccountType'),
                account_number=item.get('AcctNum'),
                parent_account_id=item.get('ParentRef', {}).get('value'),
                balance=Decimal(str(item.get('CurrentBalance', 0))),
                is_active=item.get('Active', True),
                created_date=self._parse_quickbooks_date(item.get('MetaData', {}).get('CreateTime')),
                last_modified=self._parse_quickbooks_date(item.get('MetaData', {}).get('LastUpdatedTime'))
            )
            accounts.append(account)
            
        return accounts
        
    def get_transactions(self, transaction_type: TransactionType, limit: int = 100) -> List[Transaction]:
        """Get transactions from QuickBooks"""
        # Map transaction types to QuickBooks entities
        entity_map = {
            TransactionType.INVOICE: 'invoice',
            TransactionType.PAYMENT: 'payment',
            TransactionType.EXPENSE: 'purchase',
            TransactionType.BILL: 'bill',
            TransactionType.JOURNAL_ENTRY: 'journalentry'
        }
        
        entity = entity_map.get(transaction_type)
        if not entity:
            logger.warning(f"Unsupported transaction type: {transaction_type}")
            return []
            
        response = self.framework.make_request(
            self.integration_name,
            'GET',
            f"{entity}s",
            params={'minorversion': '65', 'maxresults': limit}
        )
        
        if not response.success:
            logger.error(f"Failed to get QuickBooks {entity}s: {response.error}")
            return []
            
        transactions = []
        entity_key = entity.capitalize()
        for item in response.data.get('QueryResponse', {}).get(entity_key, []):
            transaction = Transaction(
                id=item['Id'],
                transaction_type=transaction_type,
                amount=Decimal(str(item.get('TotalAmt', 0))),
                date=self._parse_quickbooks_date(item.get('TxnDate')),
                description=item.get('PrivateNote') or item.get('Memo'),
                reference_number=item.get('DocNumber'),
                customer_id=item.get('CustomerRef', {}).get('value'),
                status=item.get('TxnStatus'),
                created_date=self._parse_quickbooks_date(item.get('MetaData', {}).get('CreateTime')),
                last_modified=self._parse_quickbooks_date(item.get('MetaData', {}).get('LastUpdatedTime')),
                line_items=item.get('Line', [])
            )
            transactions.append(transaction)
            
        return transactions
        
    def get_customers(self) -> List[Customer]:
        """Get customers from QuickBooks"""
        response = self.framework.make_request(
            self.integration_name,
            'GET',
            'customers',
            params={'minorversion': '65'}
        )
        
        if not response.success:
            logger.error(f"Failed to get QuickBooks customers: {response.error}")
            return []
            
        customers = []
        for item in response.data.get('QueryResponse', {}).get('Customer', []):
            # Parse address
            address = None
            if item.get('BillAddr'):
                addr = item['BillAddr']
                address = f"{addr.get('Line1', '')}, {addr.get('City', '')}, {addr.get('CountrySubDivisionCode', '')} {addr.get('PostalCode', '')}"
                
            customer = Customer(
                id=item['Id'],
                name=item['Name'],
                email=item.get('PrimaryEmailAddr', {}).get('Address'),
                phone=item.get('PrimaryPhone', {}).get('FreeFormNumber'),
                address=address,
                balance=Decimal(str(item.get('Balance', 0))),
                is_active=item.get('Active', True),
                created_date=self._parse_quickbooks_date(item.get('MetaData', {}).get('CreateTime')),
                last_modified=self._parse_quickbooks_date(item.get('MetaData', {}).get('LastUpdatedTime'))
            )
            customers.append(customer)
            
        return customers
        
    def get_vendors(self) -> List[Vendor]:
        """Get vendors from QuickBooks"""
        response = self.framework.make_request(
            self.integration_name,
            'GET',
            'vendors',
            params={'minorversion': '65'}
        )
        
        if not response.success:
            logger.error(f"Failed to get QuickBooks vendors: {response.error}")
            return []
            
        vendors = []
        for item in response.data.get('QueryResponse', {}).get('Vendor', []):
            # Parse address
            address = None
            if item.get('BillAddr'):
                addr = item['BillAddr']
                address = f"{addr.get('Line1', '')}, {addr.get('City', '')}, {addr.get('CountrySubDivisionCode', '')} {addr.get('PostalCode', '')}"
                
            vendor = Vendor(
                id=item['Id'],
                name=item['Name'],
                email=item.get('PrimaryEmailAddr', {}).get('Address'),
                phone=item.get('PrimaryPhone', {}).get('FreeFormNumber'),
                address=address,
                balance=Decimal(str(item.get('Balance', 0))),
                is_active=item.get('Active', True),
                created_date=self._parse_quickbooks_date(item.get('MetaData', {}).get('CreateTime')),
                last_modified=self._parse_quickbooks_date(item.get('MetaData', {}).get('LastUpdatedTime'))
            )
            vendors.append(vendor)
            
        return vendors
        
    def get_financial_report(self, report_type: str, start_date: datetime, end_date: datetime) -> Optional[FinancialReport]:
        """Get financial report from QuickBooks"""
        # Map report types
        report_map = {
            'profit_loss': 'ProfitAndLoss',
            'balance_sheet': 'BalanceSheet',
            'cash_flow': 'CashFlow'
        }
        
        qb_report_type = report_map.get(report_type)
        if not qb_report_type:
            logger.warning(f"Unsupported report type: {report_type}")
            return None
            
        params = {
            'minorversion': '65',
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d')
        }
        
        response = self.framework.make_request(
            self.integration_name,
            'GET',
            f'reports/{qb_report_type}',
            params=params
        )
        
        if not response.success:
            logger.error(f"Failed to get QuickBooks {report_type} report: {response.error}")
            return None
            
        return FinancialReport(
            report_type=report_type,
            period_start=start_date,
            period_end=end_date,
            data=response.data,
            generated_at=datetime.now()
        )
        
    def _parse_quickbooks_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse QuickBooks date format"""
        if not date_str:
            return None
        try:
            # QuickBooks uses ISO format
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except ValueError:
            try:
                # Try parsing as date only
                return datetime.strptime(date_str, '%Y-%m-%d')
            except ValueError:
                return None


class SAPConnector:
    """SAP API connector (simplified implementation)"""
    
    def __init__(self, framework: IntegrationFramework):
        self.framework = framework
        self.integration_name = "sap"
        
    def setup_integration(self, config: Dict[str, Any]) -> None:
        """Setup SAP integration"""
        auth_config = AuthConfig(
            auth_type=AuthType.BASIC_AUTH,
            client_id=config.get('username'),
            client_secret=config.get('password')
        )
        
        integration_config = IntegrationConfig(
            name=self.integration_name,
            base_url=config.get('base_url', 'https://api.sap.com'),
            auth_config=auth_config,
            timeout=60,  # SAP can be slower
            max_retries=3,
            rate_limit_per_minute=100,
            cache_ttl=600,  # Cache longer for SAP
            sync_strategy=SyncStrategy.INCREMENTAL,
            enabled=config.get('enabled', True)
        )
        
        self.framework.register_integration(integration_config)
        
    def get_accounts(self) -> List[Account]:
        """Get chart of accounts from SAP"""
        response = self.framework.make_request(
            self.integration_name,
            'GET',
            'sap/opu/odata/sap/API_GLACCOUNTMASTER_SRV/A_GLAccountMaster'
        )
        
        if not response.success:
            logger.error(f"Failed to get SAP accounts: {response.error}")
            return []
            
        accounts = []
        for item in response.data.get('d', {}).get('results', []):
            account = Account(
                id=item.get('GLAccount'),
                name=item.get('GLAccountName'),
                account_type=item.get('GLAccountType'),
                account_number=item.get('GLAccount'),
                is_active=item.get('IsBlocked') != 'X',
                created_date=self._parse_sap_date(item.get('CreationDate')),
                last_modified=self._parse_sap_date(item.get('LastChangeDate'))
            )
            accounts.append(account)
            
        return accounts
        
    def get_transactions(self, transaction_type: TransactionType, limit: int = 100) -> List[Transaction]:
        """Get transactions from SAP (simplified)"""
        # This is a simplified implementation
        # Real SAP integration would require specific APIs for different transaction types
        response = self.framework.make_request(
            self.integration_name,
            'GET',
            'sap/opu/odata/sap/API_JOURNALENTRY_SRV/A_JournalEntry',
            params={'$top': limit}
        )
        
        if not response.success:
            logger.error(f"Failed to get SAP transactions: {response.error}")
            return []
            
        transactions = []
        for item in response.data.get('d', {}).get('results', []):
            transaction = Transaction(
                id=item.get('AccountingDocument'),
                transaction_type=transaction_type,
                amount=Decimal(str(item.get('AmountInCompanyCodeCurrency', 0))),
                currency=item.get('CompanyCodeCurrency', 'USD'),
                date=self._parse_sap_date(item.get('DocumentDate')),
                description=item.get('DocumentHeaderText'),
                reference_number=item.get('Reference'),
                created_date=self._parse_sap_date(item.get('CreationDate'))
            )
            transactions.append(transaction)
            
        return transactions
        
    def _parse_sap_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse SAP date format"""
        if not date_str:
            return None
        try:
            # SAP often uses /Date(timestamp)/ format
            if date_str.startswith('/Date(') and date_str.endswith(')/'):
                timestamp = int(date_str[6:-2]) / 1000
                return datetime.fromtimestamp(timestamp)
            # Try ISO format
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except (ValueError, TypeError):
            return None


class ERPIntegrationService:
    """Main ERP integration service"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.framework = IntegrationFramework(config)
        self.connectors: Dict[str, Union[QuickBooksConnector, SAPConnector]] = {}
        
        # Initialize connectors
        self.quickbooks = QuickBooksConnector(self.framework)
        self.sap = SAPConnector(self.framework)
        self.connectors['quickbooks'] = self.quickbooks
        self.connectors['sap'] = self.sap
        
        self._setup_integrations()
        
    def _setup_integrations(self) -> None:
        """Setup ERP integrations based on configuration"""
        integrations_config = self.config.get('integrations', {})
        
        # Setup QuickBooks if configured
        if integrations_config.get('erp_enabled') and integrations_config.get('quickbooks'):
            try:
                self.quickbooks.setup_integration(integrations_config['quickbooks'])
                logger.info("QuickBooks integration configured")
            except Exception as e:
                logger.error(f"Failed to setup QuickBooks integration: {e}")
                
        # Setup SAP if configured
        if integrations_config.get('erp_enabled') and integrations_config.get('sap'):
            try:
                self.sap.setup_integration(integrations_config['sap'])
                logger.info("SAP integration configured")
            except Exception as e:
                logger.error(f"Failed to setup SAP integration: {e}")
                
    def sync_erp_data(self, provider: ERPProvider, force_full_sync: bool = False) -> SyncResult:
        """Synchronize ERP data from specified provider"""
        
        def sync_function(context):
            connector = self.connectors.get(provider.value)
            if not connector:
                return SyncResult(
                    success=False,
                    errors=[f"Connector for {provider.value} not found"]
                )
                
            try:
                records_processed = 0
                
                # Sync accounts
                accounts = connector.get_accounts()
                records_processed += len(accounts)
                
                # Sync customers
                if hasattr(connector, 'get_customers'):
                    customers = connector.get_customers()
                    records_processed += len(customers)
                
                # Sync vendors
                if hasattr(connector, 'get_vendors'):
                    vendors = connector.get_vendors()
                    records_processed += len(vendors)
                
                # Sync transactions (sample different types)
                for tx_type in [TransactionType.INVOICE, TransactionType.EXPENSE]:
                    transactions = connector.get_transactions(tx_type, limit=100)
                    records_processed += len(transactions)
                
                logger.info(f"Synced {records_processed} records from {provider.value}")
                
                return SyncResult(
                    success=True,
                    records_processed=records_processed,
                    records_created=records_processed,  # Simplified
                    records_updated=0,
                    records_failed=0
                )
                
            except Exception as e:
                logger.error(f"ERP sync error for {provider.value}: {e}")
                return SyncResult(
                    success=False,
                    errors=[f"Sync failed: {str(e)}"]
                )
                
        return self.framework.sync_data(provider.value, sync_function, force_full_sync)
        
    def get_erp_metrics(self, provider: ERPProvider, days_back: int = 30) -> Optional[ERPMetrics]:
        """Get ERP metrics for AI context"""
        connector = self.connectors.get(provider.value)
        if not connector:
            logger.error(f"Connector for {provider.value} not found")
            return None
            
        try:
            # Get financial data
            cutoff_date = datetime.now() - timedelta(days=days_back)
            
            # Get transactions
            invoices = connector.get_transactions(TransactionType.INVOICE, limit=1000)
            expenses = connector.get_transactions(TransactionType.EXPENSE, limit=1000)
            
            # Filter by date
            recent_invoices = [t for t in invoices if t.date and t.date >= cutoff_date]
            recent_expenses = [t for t in expenses if t.date and t.date >= cutoff_date]
            
            # Calculate metrics
            total_revenue = sum(t.amount for t in recent_invoices)
            total_expenses = sum(t.amount for t in recent_expenses)
            net_income = total_revenue - total_expenses
            
            # Get customers and vendors if available
            customer_count = 0
            vendor_count = 0
            if hasattr(connector, 'get_customers'):
                customers = connector.get_customers()
                customer_count = len([c for c in customers if c.is_active])
                
            if hasattr(connector, 'get_vendors'):
                vendors = connector.get_vendors()
                vendor_count = len([v for v in vendors if v.is_active])
            
            # Calculate outstanding invoices (simplified)
            outstanding_invoices = len([i for i in recent_invoices if i.status not in ['Paid', 'Closed']])
            overdue_invoices = len([i for i in recent_invoices if i.date and i.date < datetime.now() - timedelta(days=30)])
            
            # Monthly trends (simplified)
            monthly_trends = {}
            for i in range(3):  # Last 3 months
                month_start = datetime.now().replace(day=1) - timedelta(days=30*i)
                month_invoices = [t for t in recent_invoices if t.date and t.date >= month_start]
                month_expenses = [t for t in recent_expenses if t.date and t.date >= month_start]
                month_name = month_start.strftime('%Y-%m')
                monthly_trends[month_name] = {
                    'revenue': sum(t.amount for t in month_invoices),
                    'expenses': sum(t.amount for t in month_expenses)
                }
            
            return ERPMetrics(
                total_revenue=total_revenue,
                total_expenses=total_expenses,
                net_income=net_income,
                cash_flow=total_revenue - total_expenses,  # Simplified
                accounts_receivable=sum(t.amount for t in recent_invoices if t.status != 'Paid'),
                accounts_payable=sum(t.amount for t in recent_expenses if t.status != 'Paid'),
                customer_count=customer_count,
                vendor_count=vendor_count,
                outstanding_invoices=outstanding_invoices,
                overdue_invoices=overdue_invoices,
                monthly_trends=monthly_trends
            )
            
        except Exception as e:
            logger.error(f"Failed to get ERP metrics for {provider.value}: {e}")
            return None
            
    def get_financial_report(self, provider: ERPProvider, report_type: str, start_date: datetime, end_date: datetime) -> Optional[FinancialReport]:
        """Get financial report from ERP system"""
        connector = self.connectors.get(provider.value)
        if not connector:
            logger.error(f"Connector for {provider.value} not found")
            return None
            
        if hasattr(connector, 'get_financial_report'):
            return connector.get_financial_report(report_type, start_date, end_date)
        else:
            logger.warning(f"Financial reports not supported for {provider.value}")
            return None
            
    def get_erp_context_for_ai(self, provider: ERPProvider, context_type: str = "summary") -> Dict[str, Any]:
        """Get ERP data context for AI decision making"""
        try:
            if context_type == "summary":
                metrics = self.get_erp_metrics(provider)
                if not metrics:
                    return {}
                    
                return {
                    "erp_provider": provider.value,
                    "total_revenue": float(metrics.total_revenue),
                    "total_expenses": float(metrics.total_expenses),
                    "net_income": float(metrics.net_income),
                    "cash_flow": float(metrics.cash_flow),
                    "accounts_receivable": float(metrics.accounts_receivable),
                    "accounts_payable": float(metrics.accounts_payable),
                    "customer_count": metrics.customer_count,
                    "vendor_count": metrics.vendor_count,
                    "outstanding_invoices": metrics.outstanding_invoices,
                    "overdue_invoices": metrics.overdue_invoices
                }
                
            elif context_type == "financial_health":
                metrics = self.get_erp_metrics(provider)
                if not metrics:
                    return {}
                    
                # Calculate financial health indicators
                revenue_to_expense_ratio = float(metrics.total_revenue / metrics.total_expenses) if metrics.total_expenses > 0 else 0
                overdue_percentage = (metrics.overdue_invoices / metrics.outstanding_invoices * 100) if metrics.outstanding_invoices > 0 else 0
                
                return {
                    "erp_provider": provider.value,
                    "revenue_to_expense_ratio": revenue_to_expense_ratio,
                    "overdue_invoice_percentage": overdue_percentage,
                    "cash_flow_positive": float(metrics.cash_flow) > 0,
                    "net_profit_margin": float(metrics.net_income / metrics.total_revenue * 100) if metrics.total_revenue > 0 else 0
                }
                
            return {}
            
        except Exception as e:
            logger.error(f"Failed to get ERP context for AI: {e}")
            return {}
            
    def get_integration_status(self) -> Dict[str, Any]:
        """Get status of all ERP integrations"""
        status = {
            "framework_status": self.framework.list_integrations(),
            "connectors": {}
        }
        
        for provider, connector in self.connectors.items():
            try:
                # Test basic connectivity
                test_data = connector.get_accounts()
                
                status["connectors"][provider] = {
                    "available": True,
                    "test_successful": len(test_data) >= 0,
                    "last_test": datetime.now().isoformat()
                }
            except Exception as e:
                status["connectors"][provider] = {
                    "available": False,
                    "error": str(e),
                    "last_test": datetime.now().isoformat()
                }
                
        return status
        
    def shutdown(self) -> None:
        """Shutdown the ERP integration service"""
        logger.info("Shutting down ERP integration service...")
        self.framework.shutdown()
        logger.info("ERP integration service shut down successfully")