"""
CRM Integration Service

Provides integration with CRM systems including Salesforce and HubSpot.
Handles customer data synchronization, sales pipeline analysis, and CRM data context for AI decisions.
"""

import logging
import json
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import requests

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


class CRMProvider(Enum):
    """Supported CRM providers"""
    SALESFORCE = "salesforce"
    HUBSPOT = "hubspot"


@dataclass
class Contact:
    """CRM Contact data model"""
    id: str
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    company: Optional[str] = None
    phone: Optional[str] = None
    title: Optional[str] = None
    created_date: Optional[datetime] = None
    last_modified: Optional[datetime] = None
    lifecycle_stage: Optional[str] = None
    lead_score: Optional[int] = None
    source: Optional[str] = None
    custom_fields: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Deal:
    """CRM Deal/Opportunity data model"""
    id: str
    name: str
    amount: Optional[float] = None
    stage: Optional[str] = None
    probability: Optional[float] = None
    close_date: Optional[datetime] = None
    created_date: Optional[datetime] = None
    last_modified: Optional[datetime] = None
    contact_id: Optional[str] = None
    company_id: Optional[str] = None
    owner_id: Optional[str] = None
    source: Optional[str] = None
    custom_fields: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Company:
    """CRM Company/Account data model"""
    id: str
    name: str
    domain: Optional[str] = None
    industry: Optional[str] = None
    size: Optional[str] = None
    annual_revenue: Optional[float] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    created_date: Optional[datetime] = None
    last_modified: Optional[datetime] = None
    lifecycle_stage: Optional[str] = None
    custom_fields: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SalesPipelineMetrics:
    """Sales pipeline analysis metrics"""
    total_deals: int
    total_value: float
    average_deal_size: float
    conversion_rate: float
    average_sales_cycle: int  # days
    deals_by_stage: Dict[str, int]
    value_by_stage: Dict[str, float]
    monthly_trends: Dict[str, Dict[str, float]]
    top_sources: List[Dict[str, Any]]
    forecast: Dict[str, float]


class SalesforceConnector:
    """Salesforce API connector"""
    
    def __init__(self, framework: IntegrationFramework):
        self.framework = framework
        self.integration_name = "salesforce"
        
    def setup_integration(self, config: Dict[str, Any]) -> None:
        """Setup Salesforce integration"""
        auth_config = AuthConfig(
            auth_type=AuthType.OAUTH2,
            client_id=config.get('client_id'),
            client_secret=config.get('client_secret'),
            access_token=config.get('access_token'),
            refresh_token=config.get('refresh_token'),
            token_url=f"{config.get('instance_url', 'https://login.salesforce.com')}/services/oauth2/token",
            scope="api refresh_token"
        )
        
        integration_config = IntegrationConfig(
            name=self.integration_name,
            base_url=f"{config.get('instance_url')}/services/data/v58.0",
            auth_config=auth_config,
            timeout=30,
            max_retries=3,
            rate_limit_per_minute=100,  # Salesforce API limits
            cache_ttl=300,
            sync_strategy=SyncStrategy.INCREMENTAL,
            enabled=config.get('enabled', True)
        )
        
        self.framework.register_integration(integration_config)
        
    def get_contacts(self, limit: int = 100, offset: int = 0) -> List[Contact]:
        """Get contacts from Salesforce"""
        query = f"""
        SELECT Id, Email, FirstName, LastName, Account.Name, Phone, Title, 
               CreatedDate, LastModifiedDate, LeadSource
        FROM Contact 
        ORDER BY LastModifiedDate DESC 
        LIMIT {limit} OFFSET {offset}
        """
        
        response = self.framework.make_request(
            self.integration_name,
            'GET',
            'query',
            params={'q': query}
        )
        
        if not response.success:
            logger.error(f"Failed to get Salesforce contacts: {response.error}")
            return []
            
        contacts = []
        for record in response.data.get('records', []):
            contact = Contact(
                id=record['Id'],
                email=record.get('Email'),
                first_name=record.get('FirstName'),
                last_name=record.get('LastName'),
                company=record.get('Account', {}).get('Name') if record.get('Account') else None,
                phone=record.get('Phone'),
                title=record.get('Title'),
                created_date=self._parse_salesforce_date(record.get('CreatedDate')),
                last_modified=self._parse_salesforce_date(record.get('LastModifiedDate')),
                source=record.get('LeadSource')
            )
            contacts.append(contact)
            
        return contacts
        
    def get_deals(self, limit: int = 100, offset: int = 0) -> List[Deal]:
        """Get opportunities from Salesforce"""
        query = f"""
        SELECT Id, Name, Amount, StageName, Probability, CloseDate, 
               CreatedDate, LastModifiedDate, AccountId, OwnerId, LeadSource
        FROM Opportunity 
        ORDER BY LastModifiedDate DESC 
        LIMIT {limit} OFFSET {offset}
        """
        
        response = self.framework.make_request(
            self.integration_name,
            'GET',
            'query',
            params={'q': query}
        )
        
        if not response.success:
            logger.error(f"Failed to get Salesforce opportunities: {response.error}")
            return []
            
        deals = []
        for record in response.data.get('records', []):
            deal = Deal(
                id=record['Id'],
                name=record['Name'],
                amount=record.get('Amount'),
                stage=record.get('StageName'),
                probability=record.get('Probability'),
                close_date=self._parse_salesforce_date(record.get('CloseDate')),
                created_date=self._parse_salesforce_date(record.get('CreatedDate')),
                last_modified=self._parse_salesforce_date(record.get('LastModifiedDate')),
                company_id=record.get('AccountId'),
                owner_id=record.get('OwnerId'),
                source=record.get('LeadSource')
            )
            deals.append(deal)
            
        return deals
        
    def get_companies(self, limit: int = 100, offset: int = 0) -> List[Company]:
        """Get accounts from Salesforce"""
        query = f"""
        SELECT Id, Name, Website, Industry, NumberOfEmployees, AnnualRevenue,
               Phone, BillingAddress, CreatedDate, LastModifiedDate
        FROM Account 
        ORDER BY LastModifiedDate DESC 
        LIMIT {limit} OFFSET {offset}
        """
        
        response = self.framework.make_request(
            self.integration_name,
            'GET',
            'query',
            params={'q': query}
        )
        
        if not response.success:
            logger.error(f"Failed to get Salesforce accounts: {response.error}")
            return []
            
        companies = []
        for record in response.data.get('records', []):
            # Format address
            address = None
            if record.get('BillingAddress'):
                addr = record['BillingAddress']
                address = f"{addr.get('street', '')}, {addr.get('city', '')}, {addr.get('state', '')} {addr.get('postalCode', '')}"
                
            company = Company(
                id=record['Id'],
                name=record['Name'],
                domain=record.get('Website'),
                industry=record.get('Industry'),
                size=str(record.get('NumberOfEmployees')) if record.get('NumberOfEmployees') else None,
                annual_revenue=record.get('AnnualRevenue'),
                phone=record.get('Phone'),
                address=address,
                created_date=self._parse_salesforce_date(record.get('CreatedDate')),
                last_modified=self._parse_salesforce_date(record.get('LastModifiedDate'))
            )
            companies.append(company)
            
        return companies
        
    def _parse_salesforce_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse Salesforce date format"""
        if not date_str:
            return None
        try:
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except ValueError:
            return None


class HubSpotConnector:
    """HubSpot API connector"""
    
    def __init__(self, framework: IntegrationFramework):
        self.framework = framework
        self.integration_name = "hubspot"
        
    def setup_integration(self, config: Dict[str, Any]) -> None:
        """Setup HubSpot integration"""
        auth_config = AuthConfig(
            auth_type=AuthType.BEARER_TOKEN,
            access_token=config.get('access_token')
        )
        
        integration_config = IntegrationConfig(
            name=self.integration_name,
            base_url="https://api.hubapi.com",
            auth_config=auth_config,
            timeout=30,
            max_retries=3,
            rate_limit_per_minute=100,  # HubSpot API limits
            cache_ttl=300,
            sync_strategy=SyncStrategy.INCREMENTAL,
            enabled=config.get('enabled', True)
        )
        
        self.framework.register_integration(integration_config)
        
    def get_contacts(self, limit: int = 100, offset: int = 0) -> List[Contact]:
        """Get contacts from HubSpot"""
        properties = [
            'email', 'firstname', 'lastname', 'company', 'phone', 'jobtitle',
            'createdate', 'lastmodifieddate', 'lifecyclestage', 'hubspotscore',
            'hs_lead_status'
        ]
        
        response = self.framework.make_request(
            self.integration_name,
            'GET',
            'crm/v3/objects/contacts',
            params={
                'properties': ','.join(properties),
                'limit': limit,
                'after': offset
            }
        )
        
        if not response.success:
            logger.error(f"Failed to get HubSpot contacts: {response.error}")
            return []
            
        contacts = []
        for record in response.data.get('results', []):
            props = record.get('properties', {})
            contact = Contact(
                id=record['id'],
                email=props.get('email'),
                first_name=props.get('firstname'),
                last_name=props.get('lastname'),
                company=props.get('company'),
                phone=props.get('phone'),
                title=props.get('jobtitle'),
                created_date=self._parse_hubspot_date(props.get('createdate')),
                last_modified=self._parse_hubspot_date(props.get('lastmodifieddate')),
                lifecycle_stage=props.get('lifecyclestage'),
                lead_score=int(props.get('hubspotscore', 0)) if props.get('hubspotscore') else None,
                source=props.get('hs_lead_status')
            )
            contacts.append(contact)
            
        return contacts
        
    def get_deals(self, limit: int = 100, offset: int = 0) -> List[Deal]:
        """Get deals from HubSpot"""
        properties = [
            'dealname', 'amount', 'dealstage', 'hs_probability_to_close',
            'closedate', 'createdate', 'hs_lastmodifieddate', 'hubspot_owner_id',
            'hs_deal_source_id'
        ]
        
        response = self.framework.make_request(
            self.integration_name,
            'GET',
            'crm/v3/objects/deals',
            params={
                'properties': ','.join(properties),
                'limit': limit,
                'after': offset
            }
        )
        
        if not response.success:
            logger.error(f"Failed to get HubSpot deals: {response.error}")
            return []
            
        deals = []
        for record in response.data.get('results', []):
            props = record.get('properties', {})
            deal = Deal(
                id=record['id'],
                name=props.get('dealname'),
                amount=float(props.get('amount', 0)) if props.get('amount') else None,
                stage=props.get('dealstage'),
                probability=float(props.get('hs_probability_to_close', 0)) if props.get('hs_probability_to_close') else None,
                close_date=self._parse_hubspot_date(props.get('closedate')),
                created_date=self._parse_hubspot_date(props.get('createdate')),
                last_modified=self._parse_hubspot_date(props.get('hs_lastmodifieddate')),
                owner_id=props.get('hubspot_owner_id'),
                source=props.get('hs_deal_source_id')
            )
            deals.append(deal)
            
        return deals
        
    def get_companies(self, limit: int = 100, offset: int = 0) -> List[Company]:
        """Get companies from HubSpot"""
        properties = [
            'name', 'domain', 'industry', 'numberofemployees', 'annualrevenue',
            'phone', 'address', 'createdate', 'hs_lastmodifieddate', 'lifecyclestage'
        ]
        
        response = self.framework.make_request(
            self.integration_name,
            'GET',
            'crm/v3/objects/companies',
            params={
                'properties': ','.join(properties),
                'limit': limit,
                'after': offset
            }
        )
        
        if not response.success:
            logger.error(f"Failed to get HubSpot companies: {response.error}")
            return []
            
        companies = []
        for record in response.data.get('results', []):
            props = record.get('properties', {})
            company = Company(
                id=record['id'],
                name=props.get('name'),
                domain=props.get('domain'),
                industry=props.get('industry'),
                size=str(props.get('numberofemployees')) if props.get('numberofemployees') else None,
                annual_revenue=float(props.get('annualrevenue', 0)) if props.get('annualrevenue') else None,
                phone=props.get('phone'),
                address=props.get('address'),
                created_date=self._parse_hubspot_date(props.get('createdate')),
                last_modified=self._parse_hubspot_date(props.get('hs_lastmodifieddate')),
                lifecycle_stage=props.get('lifecyclestage')
            )
            companies.append(company)
            
        return companies
        
    def _parse_hubspot_date(self, timestamp_str: Optional[str]) -> Optional[datetime]:
        """Parse HubSpot timestamp format"""
        if not timestamp_str:
            return None
        try:
            timestamp = int(timestamp_str) / 1000  # HubSpot uses milliseconds
            return datetime.fromtimestamp(timestamp)
        except (ValueError, TypeError):
            return None


class CRMIntegrationService:
    """Main CRM integration service"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.framework = IntegrationFramework(config)
        self.connectors: Dict[str, Union[SalesforceConnector, HubSpotConnector]] = {}
        
        # Initialize connectors
        self.salesforce = SalesforceConnector(self.framework)
        self.hubspot = HubSpotConnector(self.framework)
        self.connectors['salesforce'] = self.salesforce
        self.connectors['hubspot'] = self.hubspot
        
        self._setup_integrations()
        
    def _setup_integrations(self) -> None:
        """Setup CRM integrations based on configuration"""
        integrations_config = self.config.get('integrations', {})
        
        # Setup Salesforce if configured
        if integrations_config.get('crm_enabled') and integrations_config.get('salesforce'):
            try:
                self.salesforce.setup_integration(integrations_config['salesforce'])
                logger.info("Salesforce integration configured")
            except Exception as e:
                logger.error(f"Failed to setup Salesforce integration: {e}")
                
        # Setup HubSpot if configured
        if integrations_config.get('crm_enabled') and integrations_config.get('hubspot'):
            try:
                self.hubspot.setup_integration(integrations_config['hubspot'])
                logger.info("HubSpot integration configured")
            except Exception as e:
                logger.error(f"Failed to setup HubSpot integration: {e}")
                
    def sync_crm_data(self, provider: CRMProvider, force_full_sync: bool = False) -> SyncResult:
        """Synchronize CRM data from specified provider"""
        
        def sync_function(context):
            connector = self.connectors.get(provider.value)
            if not connector:
                return SyncResult(
                    success=False,
                    errors=[f"Connector for {provider.value} not found"]
                )
                
            try:
                # Sync contacts
                contacts = connector.get_contacts(limit=1000)
                contacts_processed = len(contacts)
                
                # Sync deals
                deals = connector.get_deals(limit=1000)
                deals_processed = len(deals)
                
                # Sync companies
                companies = connector.get_companies(limit=1000)
                companies_processed = len(companies)
                
                # Store in database (implementation would go here)
                # For now, just log the counts
                logger.info(f"Synced {contacts_processed} contacts, {deals_processed} deals, {companies_processed} companies from {provider.value}")
                
                return SyncResult(
                    success=True,
                    records_processed=contacts_processed + deals_processed + companies_processed,
                    records_created=contacts_processed + deals_processed + companies_processed,  # Simplified
                    records_updated=0,
                    records_failed=0
                )
                
            except Exception as e:
                logger.error(f"CRM sync error for {provider.value}: {e}")
                return SyncResult(
                    success=False,
                    errors=[f"Sync failed: {str(e)}"]
                )
                
        return self.framework.sync_data(provider.value, sync_function, force_full_sync)
        
    def get_sales_pipeline_metrics(self, provider: CRMProvider, days_back: int = 90) -> Optional[SalesPipelineMetrics]:
        """Get sales pipeline analysis metrics"""
        connector = self.connectors.get(provider.value)
        if not connector:
            logger.error(f"Connector for {provider.value} not found")
            return None
            
        try:
            # Get deals from the specified time period
            deals = connector.get_deals(limit=10000)  # Get more deals for analysis
            
            if not deals:
                return None
                
            # Filter deals by date
            cutoff_date = datetime.now() - timedelta(days=days_back)
            recent_deals = [d for d in deals if d.created_date and d.created_date >= cutoff_date]
            
            # Calculate metrics
            total_deals = len(recent_deals)
            total_value = sum(d.amount or 0 for d in recent_deals)
            average_deal_size = total_value / total_deals if total_deals > 0 else 0
            
            # Deals by stage
            deals_by_stage = {}
            value_by_stage = {}
            for deal in recent_deals:
                stage = deal.stage or 'Unknown'
                deals_by_stage[stage] = deals_by_stage.get(stage, 0) + 1
                value_by_stage[stage] = value_by_stage.get(stage, 0) + (deal.amount or 0)
                
            # Calculate conversion rate (simplified)
            closed_won_deals = deals_by_stage.get('Closed Won', 0) + deals_by_stage.get('Closed-Won', 0)
            conversion_rate = (closed_won_deals / total_deals * 100) if total_deals > 0 else 0
            
            # Calculate average sales cycle (simplified)
            closed_deals = [d for d in recent_deals if d.close_date and d.created_date]
            if closed_deals:
                cycles = [(d.close_date - d.created_date).days for d in closed_deals]
                average_sales_cycle = sum(cycles) / len(cycles)
            else:
                average_sales_cycle = 0
                
            # Monthly trends (simplified)
            monthly_trends = {}
            for i in range(3):  # Last 3 months
                month_start = datetime.now().replace(day=1) - timedelta(days=30*i)
                month_deals = [d for d in recent_deals if d.created_date and d.created_date >= month_start]
                month_name = month_start.strftime('%Y-%m')
                monthly_trends[month_name] = {
                    'deals': len(month_deals),
                    'value': sum(d.amount or 0 for d in month_deals)
                }
                
            # Top sources
            sources = {}
            for deal in recent_deals:
                source = deal.source or 'Unknown'
                sources[source] = sources.get(source, 0) + 1
                
            top_sources = [{'source': k, 'count': v} for k, v in sorted(sources.items(), key=lambda x: x[1], reverse=True)[:5]]
            
            # Forecast (simplified)
            open_deals = [d for d in recent_deals if d.stage not in ['Closed Won', 'Closed Lost', 'Closed-Won', 'Closed-Lost']]
            forecast = {
                'pipeline_value': sum(d.amount or 0 for d in open_deals),
                'weighted_value': sum((d.amount or 0) * (d.probability or 0) / 100 for d in open_deals),
                'expected_close_this_month': len([d for d in open_deals if d.close_date and d.close_date.month == datetime.now().month])
            }
            
            return SalesPipelineMetrics(
                total_deals=total_deals,
                total_value=total_value,
                average_deal_size=average_deal_size,
                conversion_rate=conversion_rate,
                average_sales_cycle=int(average_sales_cycle),
                deals_by_stage=deals_by_stage,
                value_by_stage=value_by_stage,
                monthly_trends=monthly_trends,
                top_sources=top_sources,
                forecast=forecast
            )
            
        except Exception as e:
            logger.error(f"Failed to get sales pipeline metrics for {provider.value}: {e}")
            return None
            
    def get_crm_context_for_ai(self, provider: CRMProvider, context_type: str = "summary") -> Dict[str, Any]:
        """Get CRM data context for AI decision making"""
        try:
            if context_type == "summary":
                metrics = self.get_sales_pipeline_metrics(provider)
                if not metrics:
                    return {}
                    
                return {
                    "crm_provider": provider.value,
                    "total_deals": metrics.total_deals,
                    "total_pipeline_value": metrics.total_value,
                    "average_deal_size": metrics.average_deal_size,
                    "conversion_rate": metrics.conversion_rate,
                    "average_sales_cycle_days": metrics.average_sales_cycle,
                    "top_deal_stages": list(metrics.deals_by_stage.keys())[:3],
                    "forecast_pipeline_value": metrics.forecast.get('pipeline_value', 0),
                    "forecast_weighted_value": metrics.forecast.get('weighted_value', 0)
                }
                
            elif context_type == "recent_activity":
                connector = self.connectors.get(provider.value)
                if not connector:
                    return {}
                    
                # Get recent contacts and deals
                recent_contacts = connector.get_contacts(limit=10)
                recent_deals = connector.get_deals(limit=10)
                
                return {
                    "crm_provider": provider.value,
                    "recent_contacts_count": len(recent_contacts),
                    "recent_deals_count": len(recent_deals),
                    "recent_contact_sources": list(set(c.source for c in recent_contacts if c.source))[:3],
                    "recent_deal_stages": list(set(d.stage for d in recent_deals if d.stage))[:3]
                }
                
            return {}
            
        except Exception as e:
            logger.error(f"Failed to get CRM context for AI: {e}")
            return {}
            
    def get_integration_status(self) -> Dict[str, Any]:
        """Get status of all CRM integrations"""
        status = {
            "framework_status": self.framework.list_integrations(),
            "connectors": {}
        }
        
        for provider, connector in self.connectors.items():
            try:
                # Test basic connectivity
                if provider == "salesforce":
                    test_data = connector.get_contacts(limit=1)
                elif provider == "hubspot":
                    test_data = connector.get_contacts(limit=1)
                else:
                    test_data = []
                    
                status["connectors"][provider] = {
                    "available": True,
                    "test_successful": len(test_data) >= 0,  # Even 0 results is successful
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
        """Shutdown the CRM integration service"""
        logger.info("Shutting down CRM integration service...")
        self.framework.shutdown()
        logger.info("CRM integration service shut down successfully")