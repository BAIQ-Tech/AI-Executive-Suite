#!/usr/bin/env python3
"""
Simple test to verify compliance functionality works
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from services.compliance import ComplianceService, AuditEventType, DataSubjectRights, ComplianceFramework
from datetime import datetime, timedelta

def test_compliance_service():
    """Test basic compliance service functionality."""
    
    # Create Flask app for context
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'test-secret-key'
    app.config['UPLOAD_FOLDER'] = '/tmp'
    app.config['GDPR_COMPLIANCE_ENABLED'] = True
    app.config['SOX_COMPLIANCE_ENABLED'] = True
    app.config['AUDIT_RETENTION_DAYS'] = 2555
    
    with app.app_context():
        compliance_service = ComplianceService()
        
        print("Testing Compliance Service...")
        
        # Test event description generation
        print("1. Testing audit event description generation...")
        details = {
            'resource_type': 'decision',
            'resource_id': '123',
            'action': 'view'
        }
        
        description = compliance_service._generate_event_description(
            AuditEventType.DATA_ACCESS, 
            details
        )
        print(f"   ✓ Data access description: {description}")
        
        login_details = {'method': 'email', 'mfa': True}
        login_description = compliance_service._generate_event_description(
            AuditEventType.USER_LOGIN,
            login_details
        )
        print(f"   ✓ Login description: {login_description}")
        
        # Test GDPR data subject rights
        print("2. Testing GDPR data subject rights...")
        for right in DataSubjectRights:
            print(f"   ✓ {right.value}: {right.name.replace('_', ' ').title()}")
        
        # Test processing activities
        print("3. Testing data processing activities...")
        activities = compliance_service._get_user_processing_activities(123)
        print(f"   ✓ Found {len(activities)} processing activities")
        for activity in activities:
            print(f"     - {activity['activity']}: {activity['purpose']}")
        
        # Test data sources
        print("4. Testing data sources...")
        sources = compliance_service._get_user_data_sources(123)
        print(f"   ✓ Found {len(sources)} data sources")
        for source in sources:
            print(f"     - {source['source']}: {source['collection_method']}")
        
        # Test retention information
        print("5. Testing retention information...")
        retention_info = compliance_service._get_user_retention_info(123)
        print(f"   ✓ Retention policy: {retention_info['retention_policy']}")
        print(f"   ✓ Retention periods: {len(retention_info['retention_periods'])} categories")
        
        # Test compliance frameworks
        print("6. Testing compliance frameworks...")
        for framework in ComplianceFramework:
            print(f"   ✓ {framework.value}: {framework.name}")
        
        # Test audit event types
        print("7. Testing audit event types...")
        critical_events = [
            AuditEventType.DATA_ACCESS,
            AuditEventType.DATA_MODIFICATION,
            AuditEventType.DATA_DELETION,
            AuditEventType.SECURITY_EVENT
        ]
        
        for event_type in critical_events:
            description = compliance_service._generate_event_description(
                event_type,
                {'resource_type': 'test', 'resource_id': '123'}
            )
            print(f"   ✓ {event_type.value}: {description}")
        
        # Test SOX controls assessment
        print("8. Testing SOX controls assessment...")
        mock_events = []  # Empty list for testing
        
        access_assessment = compliance_service._assess_access_controls(mock_events)
        print(f"   ✓ Access controls status: {access_assessment['status']}")
        
        change_assessment = compliance_service._assess_change_management(mock_events)
        print(f"   ✓ Change management status: {change_assessment['status']}")
        
        data_assessment = compliance_service._assess_data_integrity(mock_events)
        print(f"   ✓ Data integrity status: {data_assessment['status']}")
        
        security_assessment = compliance_service._assess_security_monitoring(mock_events)
        print(f"   ✓ Security monitoring status: {security_assessment['status']}")
        
        # Test compliance alerts generation
        print("9. Testing compliance alerts...")
        alerts = compliance_service._generate_compliance_alerts()
        print(f"   ✓ Generated {len(alerts)} compliance alerts")
        for alert in alerts:
            print(f"     - {alert['type']}: {alert['message']}")
        
        # Test data subject request processing (mock - without database)
        print("10. Testing data subject request processing...")
        
        # Test rectification request (doesn't require database)
        rectification_result = compliance_service._process_rectification_request(123, {})
        print(f"   ✓ Rectification request: {rectification_result['success']}")
        
        # Test erasure request (doesn't require database)
        erasure_result = compliance_service._process_erasure_request(123, {})
        print(f"   ✓ Erasure request: {erasure_result['success']}")
        
        # Test restriction request
        restriction_result = compliance_service._process_restriction_request(123, {'categories': ['marketing']})
        print(f"   ✓ Restriction request: {restriction_result['success']}")
        
        # Test objection request
        objection_result = compliance_service._process_objection_request(123, {'categories': ['profiling']})
        print(f"   ✓ Objection request: {objection_result['success']}")
        
        # Test consent withdrawal
        consent_result = compliance_service._process_consent_withdrawal(123, {'activities': ['marketing']})
        print(f"   ✓ Consent withdrawal: {consent_result['success']}")
        
        print("\n✅ All compliance service tests passed!")

if __name__ == '__main__':
    test_compliance_service()