"""
Test Suite for Compliance and Audit System

Tests GDPR compliance, SOX audit logging, compliance reporting, and data privacy controls.
"""

import pytest
import os
import sys
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask
from models import db, User, AuditLog, DataProtectionRecord
from services.compliance import ComplianceService, ComplianceFramework, AuditEventType, DataSubjectRights


@pytest.fixture
def app():
    """Create test Flask application."""
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'test-secret-key'
    app.config['UPLOAD_FOLDER'] = '/tmp'
    app.config['GDPR_COMPLIANCE_ENABLED'] = True
    app.config['SOX_COMPLIANCE_ENABLED'] = True
    app.config['AUDIT_RETENTION_DAYS'] = 2555
    app.config['WTF_CSRF_ENABLED'] = False
    
    db.init_app(app)
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def test_user(app):
    """Create test user."""
    with app.app_context():
        user = User(
            username='testuser',
            email='test@example.com',
            name='Test User'
        )
        user.set_password('testpassword')
        db.session.add(user)
        db.session.commit()
        return user


@pytest.fixture
def compliance_service(app):
    """Create compliance service instance."""
    with app.app_context():
        return ComplianceService()


class TestComplianceService:
    """Test compliance service functionality."""
    
    def test_audit_event_logging(self, app, compliance_service, test_user):
        """Test audit event logging."""
        with app.app_context():
            # Log an audit event
            success = compliance_service.log_audit_event(
                event_type=AuditEventType.DATA_ACCESS,
                user_id=test_user.id,
                details={'resource_type': 'decision', 'resource_id': '123'},
                ip_address='192.168.1.1',
                user_agent='Test Browser'
            )
            
            assert success is True
            
            # Verify event was logged
            audit_log = AuditLog.query.first()
            assert audit_log is not None
            assert audit_log.event_type == 'data_access'
            assert audit_log.user_id == test_user.id
    
    def test_gdpr_data_export(self, app, compliance_service, test_user):
        """Test GDPR data export generation."""
        with app.app_context():
            # Generate data export
            export_data = compliance_service.generate_gdpr_data_export(test_user.id)
            
            assert 'export_info' in export_data
            assert 'personal_data' in export_data
            assert 'processing_activities' in export_data
            assert export_data['export_info']['user_id'] == test_user.id
            assert export_data['export_info']['framework'] == 'GDPR Article 15'
            
            # Verify user data is included
            assert 'user_profile' in export_data['personal_data']
            assert export_data['personal_data']['user_profile']['email'] == test_user.email
    
    def test_data_subject_rights_processing(self, app, compliance_service, test_user):
        """Test processing of GDPR data subject rights requests."""
        with app.app_context():
            # Test right to access
            result = compliance_service.process_data_subject_request(
                DataSubjectRights.RIGHT_TO_ACCESS,
                test_user.id
            )
            
            assert result['success'] is True
            assert result['request_type'] == 'right_to_access'
            assert 'data' in result
            
            # Test right to erasure
            result = compliance_service.process_data_subject_request(
                DataSubjectRights.RIGHT_TO_ERASURE,
                test_user.id
            )
            
            assert result['success'] is True
            assert result['request_type'] == 'right_to_erasure'
            assert 'retention_exceptions' in result
    
    def test_sox_compliance_report(self, app, compliance_service, test_user):
        """Test SOX compliance report generation."""
        with app.app_context():
            # Create some audit events
            events = [
                AuditEventType.DATA_ACCESS,
                AuditEventType.DATA_MODIFICATION,
                AuditEventType.USER_LOGIN,
                AuditEventType.SECURITY_EVENT
            ]
            
            for event_type in events:
                compliance_service.log_audit_event(
                    event_type=event_type,
                    user_id=test_user.id,
                    details={'test': 'data'},
                    ip_address='192.168.1.1'
                )
            
            # Generate SOX report
            start_date = datetime.utcnow() - timedelta(days=30)
            end_date = datetime.utcnow()
            
            report = compliance_service.generate_sox_compliance_report(start_date, end_date)
            
            assert 'report_info' in report
            assert 'summary' in report
            assert 'controls_assessment' in report
            assert report['report_info']['framework'] == 'SOX (Sarbanes-Oxley Act)'
            assert report['summary']['total_audit_events'] >= len(events)
    
    def test_compliance_dashboard(self, app, compliance_service, test_user):
        """Test compliance dashboard generation."""
        with app.app_context():
            # Create some test data
            compliance_service.log_audit_event(
                AuditEventType.DATA_ACCESS,
                test_user.id,
                {'test': 'data'}
            )
            
            # Generate dashboard
            dashboard = compliance_service.generate_compliance_dashboard()
            
            assert 'overview' in dashboard
            assert 'compliance_status' in dashboard
            assert 'recent_activity' in dashboard
            assert 'alerts' in dashboard
            
            # Check overview data
            assert dashboard['overview']['total_users'] >= 1
            assert dashboard['overview']['total_audit_events'] >= 1
            
            # Check compliance status
            assert 'gdpr' in dashboard['compliance_status']
            assert 'sox' in dashboard['compliance_status']
    
    def test_compliance_alerts(self, app, compliance_service):
        """Test compliance alert generation."""
        with app.app_context():
            # Create a data protection record due for deletion
            past_date = datetime.utcnow() - timedelta(days=1)
            record = DataProtectionRecord(
                data_type='test_data',
                data_id='test_123',
                classification='internal',
                retention_policy='short_term',
                deletion_date=past_date
            )
            db.session.add(record)
            db.session.commit()
            
            # Generate dashboard (which includes alerts)
            dashboard = compliance_service.generate_compliance_dashboard()
            
            # Check for retention alert
            alerts = dashboard['alerts']
            retention_alerts = [a for a in alerts if a['type'] == 'DATA_RETENTION']
            assert len(retention_alerts) > 0
            assert retention_alerts[0]['severity'] == 'HIGH'
    
    def test_compliance_data_export(self, app, compliance_service, test_user):
        """Test compliance data export functionality."""
        with app.app_context():
            # Create some audit events
            compliance_service.log_audit_event(
                AuditEventType.DATA_ACCESS,
                test_user.id,
                {'test': 'data'}
            )
            
            start_date = datetime.utcnow() - timedelta(days=1)
            end_date = datetime.utcnow()
            
            # Test GDPR export
            filepath = compliance_service.export_compliance_data(
                ComplianceFramework.GDPR,
                start_date,
                end_date,
                'json'
            )
            
            assert os.path.exists(filepath)
            assert filepath.endswith('.json')
            
            # Clean up
            os.remove(filepath)
    
    def test_event_description_generation(self, compliance_service):
        """Test audit event description generation."""
        details = {
            'resource_type': 'decision',
            'resource_id': '123'
        }
        
        description = compliance_service._generate_event_description(
            AuditEventType.DATA_ACCESS,
            details
        )
        
        assert 'decision' in description
        assert '123' in description
        
        # Test login event
        login_details = {'method': 'email'}
        description = compliance_service._generate_event_description(
            AuditEventType.USER_LOGIN,
            login_details
        )
        
        assert 'logged in' in description
        assert 'email' in description


class TestComplianceModels:
    """Test compliance-related database models."""
    
    def test_audit_log_creation(self, app, test_user):
        """Test AuditLog model creation."""
        with app.app_context():
            audit_log = AuditLog.create_entry(
                event_type='test_event',
                event_description='Test event description',
                user_id=test_user.id,
                user_ip='192.168.1.1',
                user_agent='Test Browser',
                metadata={'test': 'data'}
            )
            
            assert audit_log is not None
            assert audit_log.event_type == 'test_event'
            assert audit_log.user_id == test_user.id
            assert audit_log.user_ip == '192.168.1.1'
    
    def test_data_protection_record_compliance(self, app):
        """Test DataProtectionRecord compliance features."""
        with app.app_context():
            # Create record due for deletion
            past_date = datetime.utcnow() - timedelta(days=1)
            record = DataProtectionRecord(
                data_type='user_data',
                data_id='user_123',
                classification='confidential',
                retention_policy='short_term',
                deletion_date=past_date
            )
            
            db.session.add(record)
            db.session.commit()
            
            # Test compliance checking
            assert record.is_due_for_deletion() is True
            assert record.days_until_deletion() < 0  # Overdue
            
            # Test deletion tracking
            record.mark_deleted('compliance_requirement')
            assert record.is_deleted is True
            assert record.deletion_reason == 'compliance_requirement'


class TestComplianceIntegration:
    """Test compliance system integration scenarios."""
    
    def test_complete_gdpr_workflow(self, app, compliance_service, test_user):
        """Test complete GDPR compliance workflow."""
        with app.app_context():
            # 1. Log some user activities
            activities = [
                (AuditEventType.USER_LOGIN, {'method': 'email'}),
                (AuditEventType.DATA_ACCESS, {'resource_type': 'decision', 'resource_id': '123'}),
                (AuditEventType.DATA_MODIFICATION, {'resource_type': 'profile', 'changes': 'name'})
            ]
            
            for event_type, details in activities:
                compliance_service.log_audit_event(
                    event_type=event_type,
                    user_id=test_user.id,
                    details=details,
                    ip_address='192.168.1.1'
                )
            
            # 2. User requests data export (Right to Access)
            export_result = compliance_service.process_data_subject_request(
                DataSubjectRights.RIGHT_TO_ACCESS,
                test_user.id
            )
            
            assert export_result['success'] is True
            assert 'data' in export_result
            
            # 3. Verify audit trail includes the request
            audit_logs = AuditLog.query.filter_by(user_id=test_user.id).all()
            compliance_logs = [log for log in audit_logs if 'gdpr' in log.event_description.lower()]
            assert len(compliance_logs) > 0
            
            # 4. User requests data deletion (Right to Erasure)
            erasure_result = compliance_service.process_data_subject_request(
                DataSubjectRights.RIGHT_TO_ERASURE,
                test_user.id
            )
            
            assert erasure_result['success'] is True
            assert 'retention_exceptions' in erasure_result
    
    def test_sox_audit_trail_workflow(self, app, compliance_service, test_user):
        """Test SOX audit trail workflow."""
        with app.app_context():
            # 1. Simulate financial decision activities
            financial_activities = [
                (AuditEventType.DATA_ACCESS, {'resource_type': 'financial_decision', 'resource_id': 'fd_123'}),
                (AuditEventType.DATA_MODIFICATION, {'resource_type': 'budget', 'amount': 10000}),
                (AuditEventType.SYSTEM_CONFIGURATION, {'setting': 'financial_approval_limit', 'value': 50000})
            ]
            
            for event_type, details in financial_activities:
                compliance_service.log_audit_event(
                    event_type=event_type,
                    user_id=test_user.id,
                    details=details,
                    ip_address='192.168.1.1'
                )
            
            # 2. Generate SOX compliance report
            start_date = datetime.utcnow() - timedelta(days=1)
            end_date = datetime.utcnow()
            
            report = compliance_service.generate_sox_compliance_report(start_date, end_date)
            
            # 3. Verify report contains required SOX elements
            assert report['report_info']['framework'] == 'SOX (Sarbanes-Oxley Act)'
            assert 'controls_assessment' in report
            assert 'access_controls' in report['controls_assessment']
            assert 'change_management' in report['controls_assessment']
            assert 'data_integrity' in report['controls_assessment']
            
            # 4. Verify audit events are categorized correctly
            assert report['summary']['total_audit_events'] >= len(financial_activities)
    
    def test_data_retention_compliance_workflow(self, app, compliance_service):
        """Test data retention compliance workflow."""
        with app.app_context():
            # 1. Create records with different retention periods
            records = [
                # Record due for deletion
                DataProtectionRecord(
                    data_type='session_data',
                    data_id='session_123',
                    classification='internal',
                    retention_policy='short_term',
                    deletion_date=datetime.utcnow() - timedelta(days=1)
                ),
                # Record not due for deletion
                DataProtectionRecord(
                    data_type='user_data',
                    data_id='user_456',
                    classification='confidential',
                    retention_policy='medium_term',
                    deletion_date=datetime.utcnow() + timedelta(days=30)
                )
            ]
            
            db.session.add_all(records)
            db.session.commit()
            
            # 2. Generate compliance dashboard
            dashboard = compliance_service.generate_compliance_dashboard()
            
            # 3. Verify retention alerts are generated
            alerts = dashboard['alerts']
            retention_alerts = [a for a in alerts if a['type'] == 'DATA_RETENTION']
            assert len(retention_alerts) > 0
            
            # 4. Verify due records are identified
            due_record = records[0]
            assert due_record.is_due_for_deletion() is True
            
            not_due_record = records[1]
            assert not_due_record.is_due_for_deletion() is False


if __name__ == '__main__':
    pytest.main([__file__, '-v'])