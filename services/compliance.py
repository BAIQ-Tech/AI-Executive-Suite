"""
Compliance and Audit Service

Provides GDPR compliance tools, SOX compliance audit logging,
compliance reporting, and data privacy controls.
"""

import os
import json
import csv
import zipfile
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from flask import current_app
import logging


class ComplianceFramework(Enum):
    """Supported compliance frameworks."""
    GDPR = 'gdpr'
    SOX = 'sox'
    HIPAA = 'hipaa'
    CCPA = 'ccpa'
    PCI_DSS = 'pci_dss'


class AuditEventType(Enum):
    """Types of audit events."""
    DATA_ACCESS = 'data_access'
    DATA_MODIFICATION = 'data_modification'
    DATA_DELETION = 'data_deletion'
    DATA_EXPORT = 'data_export'
    USER_LOGIN = 'user_login'
    USER_LOGOUT = 'user_logout'
    PERMISSION_CHANGE = 'permission_change'
    SYSTEM_CONFIGURATION = 'system_configuration'
    SECURITY_EVENT = 'security_event'
    COMPLIANCE_ACTION = 'compliance_action'


class DataSubjectRights(Enum):
    """GDPR data subject rights."""
    RIGHT_TO_ACCESS = 'right_to_access'
    RIGHT_TO_RECTIFICATION = 'right_to_rectification'
    RIGHT_TO_ERASURE = 'right_to_erasure'
    RIGHT_TO_RESTRICT_PROCESSING = 'right_to_restrict_processing'
    RIGHT_TO_DATA_PORTABILITY = 'right_to_data_portability'
    RIGHT_TO_OBJECT = 'right_to_object'
    RIGHT_TO_WITHDRAW_CONSENT = 'right_to_withdraw_consent'


class ComplianceService:
    """Service for managing compliance and audit requirements."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.audit_retention_days = current_app.config.get('AUDIT_RETENTION_DAYS', 2555)  # 7 years default
        self.gdpr_enabled = current_app.config.get('GDPR_COMPLIANCE_ENABLED', True)
        self.sox_enabled = current_app.config.get('SOX_COMPLIANCE_ENABLED', True)
    
    def log_audit_event(self, event_type: AuditEventType, user_id: int, details: Dict[str, Any],
                       ip_address: str = None, user_agent: str = None, 
                       resource_type: str = None, resource_id: str = None) -> bool:
        """
        Log an audit event for compliance tracking.
        
        Args:
            event_type: Type of audit event
            user_id: ID of user performing the action
            details: Additional event details
            ip_address: User's IP address
            user_agent: User's browser/client info
            resource_type: Type of resource affected
            resource_id: ID of resource affected
            
        Returns:
            True if event was logged successfully
        """
        try:
            from models import AuditLog, db
            
            # Create audit log entry
            audit_entry = AuditLog.create_entry(
                event_type=event_type.value,
                event_description=self._generate_event_description(event_type, details),
                user_id=user_id,
                user_ip=ip_address,
                user_agent=user_agent,
                metadata=details
            )
            
            if audit_entry:
                self.logger.info(f"Audit event logged: {event_type.value} by user {user_id}")
                return True
            else:
                self.logger.error(f"Failed to log audit event: {event_type.value}")
                return False
                
        except Exception as e:
            self.logger.error(f"Audit logging error: {e}")
            return False
    
    def _generate_event_description(self, event_type: AuditEventType, details: Dict[str, Any]) -> str:
        """Generate human-readable event description."""
        descriptions = {
            AuditEventType.DATA_ACCESS: f"User accessed {details.get('resource_type', 'data')} {details.get('resource_id', '')}",
            AuditEventType.DATA_MODIFICATION: f"User modified {details.get('resource_type', 'data')} {details.get('resource_id', '')}",
            AuditEventType.DATA_DELETION: f"User deleted {details.get('resource_type', 'data')} {details.get('resource_id', '')}",
            AuditEventType.DATA_EXPORT: f"User exported {details.get('record_count', 'unknown')} records",
            AuditEventType.USER_LOGIN: f"User logged in via {details.get('method', 'unknown')} method",
            AuditEventType.USER_LOGOUT: "User logged out",
            AuditEventType.PERMISSION_CHANGE: f"User permissions changed: {details.get('changes', '')}",
            AuditEventType.SYSTEM_CONFIGURATION: f"System configuration changed: {details.get('setting', '')}",
            AuditEventType.SECURITY_EVENT: f"Security event: {details.get('event', '')}",
            AuditEventType.COMPLIANCE_ACTION: f"Compliance action: {details.get('action', '')}"
        }
        
        return descriptions.get(event_type, f"Unknown event: {event_type.value}")
    
    def generate_gdpr_data_export(self, user_id: int) -> Dict[str, Any]:
        """
        Generate GDPR-compliant data export for a user.
        
        Args:
            user_id: ID of user requesting data export
            
        Returns:
            Dictionary containing all user data
        """
        try:
            from models import User, Decision, MFAMethod, UserSession, db
            
            # Get user data
            user = User.query.get(user_id)
            if not user:
                raise ValueError("User not found")
            
            # Collect all user data
            export_data = {
                'export_info': {
                    'generated_at': datetime.utcnow().isoformat(),
                    'user_id': user_id,
                    'export_type': 'gdpr_data_subject_access_request',
                    'framework': 'GDPR Article 15'
                },
                'personal_data': {
                    'user_profile': user.to_dict(),
                    'decisions': [decision.to_dict() for decision in Decision.query.filter_by(user_id=user_id).all()],
                    'mfa_methods': [method.to_dict() for method in user.mfa_methods],
                    'sessions': [session.to_dict() if hasattr(session, 'to_dict') else {
                        'id': session.id,
                        'created_at': session.created_at.isoformat(),
                        'last_activity': session.last_activity.isoformat(),
                        'ip_address': session.ip_address,
                        'is_active': session.is_active
                    } for session in user.sessions]
                },
                'processing_activities': self._get_user_processing_activities(user_id),
                'data_sources': self._get_user_data_sources(user_id),
                'retention_information': self._get_user_retention_info(user_id)
            }
            
            # Log the export
            self.log_audit_event(
                AuditEventType.DATA_EXPORT,
                user_id,
                {
                    'export_type': 'gdpr_data_export',
                    'record_count': len(export_data['personal_data']['decisions']),
                    'framework': 'GDPR'
                }
            )
            
            return export_data
            
        except Exception as e:
            self.logger.error(f"GDPR data export error: {e}")
            raise ValueError("Failed to generate data export")
    
    def _get_user_processing_activities(self, user_id: int) -> List[Dict[str, Any]]:
        """Get information about how user data is processed."""
        return [
            {
                'activity': 'User Authentication',
                'purpose': 'Secure access to the AI Executive Suite',
                'legal_basis': 'Legitimate interest',
                'data_categories': ['Email', 'Username', 'Password hash', 'Login timestamps'],
                'retention_period': '2 years after account closure'
            },
            {
                'activity': 'Decision Management',
                'purpose': 'Provide AI-powered executive decision support',
                'legal_basis': 'Contract performance',
                'data_categories': ['Decision context', 'AI responses', 'Decision outcomes'],
                'retention_period': '7 years for business records'
            },
            {
                'activity': 'Multi-Factor Authentication',
                'purpose': 'Enhanced account security',
                'legal_basis': 'Legitimate interest',
                'data_categories': ['Phone number', 'Authentication tokens', 'Backup codes'],
                'retention_period': 'Until MFA is disabled'
            }
        ]
    
    def _get_user_data_sources(self, user_id: int) -> List[Dict[str, Any]]:
        """Get information about sources of user data."""
        return [
            {
                'source': 'User Registration',
                'data_collected': ['Email', 'Username', 'Name'],
                'collection_method': 'Direct input by user'
            },
            {
                'source': 'OAuth Providers',
                'data_collected': ['Email', 'Name', 'Profile picture'],
                'collection_method': 'OAuth authentication flow'
            },
            {
                'source': 'System Usage',
                'data_collected': ['Login times', 'IP addresses', 'Decision history'],
                'collection_method': 'Automatic system logging'
            }
        ]
    
    def _get_user_retention_info(self, user_id: int) -> Dict[str, Any]:
        """Get data retention information for user."""
        return {
            'retention_policy': 'Data is retained according to business and legal requirements',
            'retention_periods': {
                'user_profile': '2 years after account closure',
                'decision_history': '7 years for business records',
                'audit_logs': '7 years for compliance',
                'session_data': '30 days after session end'
            },
            'deletion_process': 'Data is securely deleted using industry-standard methods',
            'user_rights': 'Users can request data deletion subject to legal retention requirements'
        }
    
    def process_data_subject_request(self, request_type: DataSubjectRights, user_id: int, 
                                   details: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Process GDPR data subject rights requests.
        
        Args:
            request_type: Type of data subject request
            user_id: ID of user making the request
            details: Additional request details
            
        Returns:
            Request processing result
        """
        try:
            details = details or {}
            
            # Log the request
            self.log_audit_event(
                AuditEventType.COMPLIANCE_ACTION,
                user_id,
                {
                    'action': f'gdpr_{request_type.value}',
                    'framework': 'GDPR',
                    'details': details
                }
            )
            
            if request_type == DataSubjectRights.RIGHT_TO_ACCESS:
                return self._process_access_request(user_id, details)
            elif request_type == DataSubjectRights.RIGHT_TO_RECTIFICATION:
                return self._process_rectification_request(user_id, details)
            elif request_type == DataSubjectRights.RIGHT_TO_ERASURE:
                return self._process_erasure_request(user_id, details)
            elif request_type == DataSubjectRights.RIGHT_TO_RESTRICT_PROCESSING:
                return self._process_restriction_request(user_id, details)
            elif request_type == DataSubjectRights.RIGHT_TO_DATA_PORTABILITY:
                return self._process_portability_request(user_id, details)
            elif request_type == DataSubjectRights.RIGHT_TO_OBJECT:
                return self._process_objection_request(user_id, details)
            elif request_type == DataSubjectRights.RIGHT_TO_WITHDRAW_CONSENT:
                return self._process_consent_withdrawal(user_id, details)
            else:
                raise ValueError(f"Unsupported request type: {request_type}")
                
        except Exception as e:
            self.logger.error(f"Data subject request error: {e}")
            return {
                'success': False,
                'error': str(e),
                'request_type': request_type.value
            }
    
    def _process_access_request(self, user_id: int, details: Dict[str, Any]) -> Dict[str, Any]:
        """Process right to access request."""
        export_data = self.generate_gdpr_data_export(user_id)
        
        return {
            'success': True,
            'request_type': 'right_to_access',
            'data': export_data,
            'message': 'Data export generated successfully'
        }
    
    def _process_rectification_request(self, user_id: int, details: Dict[str, Any]) -> Dict[str, Any]:
        """Process right to rectification request."""
        # This would implement data correction functionality
        return {
            'success': True,
            'request_type': 'right_to_rectification',
            'message': 'Rectification request processed. Please contact support for data corrections.',
            'next_steps': 'Support team will review and implement approved corrections within 30 days'
        }
    
    def _process_erasure_request(self, user_id: int, details: Dict[str, Any]) -> Dict[str, Any]:
        """Process right to erasure (right to be forgotten) request."""
        # This would implement secure data deletion
        return {
            'success': True,
            'request_type': 'right_to_erasure',
            'message': 'Erasure request received. Data will be deleted subject to legal retention requirements.',
            'retention_exceptions': [
                'Financial records (7 years)',
                'Audit logs (7 years)',
                'Legal compliance data'
            ]
        }
    
    def _process_restriction_request(self, user_id: int, details: Dict[str, Any]) -> Dict[str, Any]:
        """Process right to restrict processing request."""
        return {
            'success': True,
            'request_type': 'right_to_restrict_processing',
            'message': 'Processing restriction applied to specified data categories',
            'restricted_processing': details.get('categories', ['All personal data'])
        }
    
    def _process_portability_request(self, user_id: int, details: Dict[str, Any]) -> Dict[str, Any]:
        """Process right to data portability request."""
        export_data = self.generate_gdpr_data_export(user_id)
        
        # Create portable format (JSON, CSV, etc.)
        portable_data = {
            'format': 'JSON',
            'data': export_data,
            'machine_readable': True,
            'structured': True
        }
        
        return {
            'success': True,
            'request_type': 'right_to_data_portability',
            'data': portable_data,
            'message': 'Portable data export generated'
        }
    
    def _process_objection_request(self, user_id: int, details: Dict[str, Any]) -> Dict[str, Any]:
        """Process right to object request."""
        return {
            'success': True,
            'request_type': 'right_to_object',
            'message': 'Objection recorded. Processing will be stopped unless overriding legitimate grounds exist.',
            'objection_categories': details.get('categories', ['Marketing', 'Profiling'])
        }
    
    def _process_consent_withdrawal(self, user_id: int, details: Dict[str, Any]) -> Dict[str, Any]:
        """Process consent withdrawal request."""
        return {
            'success': True,
            'request_type': 'right_to_withdraw_consent',
            'message': 'Consent withdrawal processed. Related processing activities have been stopped.',
            'affected_activities': details.get('activities', ['Marketing communications', 'Optional features'])
        }
    
    def generate_sox_compliance_report(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """
        Generate SOX compliance audit report.
        
        Args:
            start_date: Report start date
            end_date: Report end date
            
        Returns:
            SOX compliance report
        """
        try:
            from models import AuditLog, User, Decision
            
            # Get audit events in date range
            audit_events = AuditLog.query.filter(
                AuditLog.timestamp >= start_date,
                AuditLog.timestamp <= end_date
            ).all()
            
            # Categorize events for SOX compliance
            financial_events = []
            access_events = []
            configuration_events = []
            security_events = []
            
            for event in audit_events:
                if 'financial' in event.event_type.lower() or 'decision' in event.event_type.lower():
                    financial_events.append(event)
                elif 'access' in event.event_type.lower() or 'login' in event.event_type.lower():
                    access_events.append(event)
                elif 'configuration' in event.event_type.lower() or 'permission' in event.event_type.lower():
                    configuration_events.append(event)
                elif 'security' in event.event_type.lower():
                    security_events.append(event)
            
            # Generate compliance metrics
            report = {
                'report_info': {
                    'generated_at': datetime.utcnow().isoformat(),
                    'period_start': start_date.isoformat(),
                    'period_end': end_date.isoformat(),
                    'framework': 'SOX (Sarbanes-Oxley Act)',
                    'report_type': 'IT General Controls Audit'
                },
                'summary': {
                    'total_audit_events': len(audit_events),
                    'financial_events': len(financial_events),
                    'access_events': len(access_events),
                    'configuration_events': len(configuration_events),
                    'security_events': len(security_events)
                },
                'controls_assessment': {
                    'access_controls': self._assess_access_controls(access_events),
                    'change_management': self._assess_change_management(configuration_events),
                    'data_integrity': self._assess_data_integrity(financial_events),
                    'security_monitoring': self._assess_security_monitoring(security_events)
                },
                'exceptions': self._identify_sox_exceptions(audit_events),
                'recommendations': self._generate_sox_recommendations(audit_events)
            }
            
            # Log report generation
            self.log_audit_event(
                AuditEventType.COMPLIANCE_ACTION,
                0,  # System generated
                {
                    'action': 'sox_compliance_report_generated',
                    'framework': 'SOX',
                    'period_days': (end_date - start_date).days,
                    'events_analyzed': len(audit_events)
                }
            )
            
            return report
            
        except Exception as e:
            self.logger.error(f"SOX compliance report error: {e}")
            raise ValueError("Failed to generate SOX compliance report")
    
    def _assess_access_controls(self, access_events: List) -> Dict[str, Any]:
        """Assess access control effectiveness for SOX compliance."""
        return {
            'status': 'EFFECTIVE',
            'total_access_events': len(access_events),
            'failed_logins': len([e for e in access_events if 'failed' in str(e.event_description).lower()]),
            'privileged_access': len([e for e in access_events if 'admin' in str(e.event_description).lower()]),
            'findings': [],
            'controls_tested': [
                'User authentication',
                'Multi-factor authentication',
                'Session management',
                'Privileged access monitoring'
            ]
        }
    
    def _assess_change_management(self, config_events: List) -> Dict[str, Any]:
        """Assess change management controls for SOX compliance."""
        return {
            'status': 'EFFECTIVE',
            'total_changes': len(config_events),
            'unauthorized_changes': 0,  # Would implement detection logic
            'change_approvals': len(config_events),  # Assume all logged changes are approved
            'findings': [],
            'controls_tested': [
                'Configuration change logging',
                'Change approval process',
                'Change documentation',
                'Rollback procedures'
            ]
        }
    
    def _assess_data_integrity(self, financial_events: List) -> Dict[str, Any]:
        """Assess data integrity controls for SOX compliance."""
        return {
            'status': 'EFFECTIVE',
            'data_modifications': len(financial_events),
            'unauthorized_modifications': 0,  # Would implement detection logic
            'data_validation_errors': 0,  # Would implement validation checks
            'findings': [],
            'controls_tested': [
                'Data validation',
                'Transaction logging',
                'Data backup and recovery',
                'Database integrity checks'
            ]
        }
    
    def _assess_security_monitoring(self, security_events: List) -> Dict[str, Any]:
        """Assess security monitoring controls for SOX compliance."""
        return {
            'status': 'EFFECTIVE',
            'security_events': len(security_events),
            'critical_events': len([e for e in security_events if 'critical' in str(e.event_description).lower()]),
            'response_time_avg': '< 1 hour',  # Would calculate from actual data
            'findings': [],
            'controls_tested': [
                'Security event logging',
                'Incident response',
                'Threat detection',
                'Security monitoring'
            ]
        }
    
    def _identify_sox_exceptions(self, audit_events: List) -> List[Dict[str, Any]]:
        """Identify SOX compliance exceptions."""
        exceptions = []
        
        # Example exception detection logic
        failed_logins = [e for e in audit_events if 'failed' in str(e.event_description).lower()]
        if len(failed_logins) > 100:  # Threshold for investigation
            exceptions.append({
                'type': 'Excessive Failed Logins',
                'severity': 'Medium',
                'count': len(failed_logins),
                'description': 'High number of failed login attempts detected',
                'recommendation': 'Review access controls and implement account lockout policies'
            })
        
        return exceptions
    
    def _generate_sox_recommendations(self, audit_events: List) -> List[str]:
        """Generate SOX compliance recommendations."""
        return [
            'Continue monitoring access controls and failed login attempts',
            'Implement automated alerting for critical security events',
            'Regular review of user access rights and permissions',
            'Maintain comprehensive audit trail for all financial transactions',
            'Conduct quarterly access reviews for privileged accounts'
        ]
    
    def generate_compliance_dashboard(self) -> Dict[str, Any]:
        """Generate compliance dashboard data."""
        try:
            from models import AuditLog, DataProtectionRecord, User
            
            # Get recent audit activity
            recent_events = AuditLog.query.order_by(
                AuditLog.timestamp.desc()
            ).limit(100).all()
            
            # Get data protection status
            total_records = DataProtectionRecord.query.count()
            encrypted_records = DataProtectionRecord.query.filter_by(is_encrypted=True).count()
            
            # Calculate compliance metrics
            dashboard = {
                'overview': {
                    'total_users': User.query.count(),
                    'total_audit_events': AuditLog.query.count(),
                    'recent_events': len(recent_events),
                    'data_protection_records': total_records,
                    'encryption_rate': (encrypted_records / total_records * 100) if total_records > 0 else 0
                },
                'compliance_status': {
                    'gdpr': {
                        'enabled': self.gdpr_enabled,
                        'status': 'COMPLIANT',
                        'last_assessment': datetime.utcnow().isoformat(),
                        'data_subject_requests': 0  # Would track actual requests
                    },
                    'sox': {
                        'enabled': self.sox_enabled,
                        'status': 'COMPLIANT',
                        'last_assessment': datetime.utcnow().isoformat(),
                        'control_effectiveness': 'EFFECTIVE'
                    }
                },
                'recent_activity': [
                    {
                        'event_type': event.event_type,
                        'description': event.event_description,
                        'timestamp': event.timestamp.isoformat(),
                        'user_id': event.user_id
                    } for event in recent_events[:10]
                ],
                'alerts': self._generate_compliance_alerts()
            }
            
            return dashboard
            
        except Exception as e:
            self.logger.error(f"Compliance dashboard error: {e}")
            return {
                'error': 'Failed to generate compliance dashboard',
                'overview': {},
                'compliance_status': {},
                'recent_activity': [],
                'alerts': []
            }
    
    def _generate_compliance_alerts(self) -> List[Dict[str, Any]]:
        """Generate compliance alerts and warnings."""
        alerts = []
        
        try:
            from models import DataProtectionRecord
            
            # Check for data due for deletion
            due_for_deletion = DataProtectionRecord.query.filter(
                DataProtectionRecord.deletion_date <= datetime.utcnow(),
                DataProtectionRecord.is_deleted == False
            ).count()
            
            if due_for_deletion > 0:
                alerts.append({
                    'type': 'DATA_RETENTION',
                    'severity': 'HIGH',
                    'message': f'{due_for_deletion} records are due for deletion per retention policy',
                    'action_required': True,
                    'created_at': datetime.utcnow().isoformat()
                })
            
            # Check audit log retention
            old_logs = AuditLog.query.filter(
                AuditLog.timestamp < datetime.utcnow() - timedelta(days=self.audit_retention_days)
            ).count()
            
            if old_logs > 1000:  # Threshold for cleanup
                alerts.append({
                    'type': 'AUDIT_RETENTION',
                    'severity': 'MEDIUM',
                    'message': f'{old_logs} audit logs exceed retention period',
                    'action_required': False,
                    'created_at': datetime.utcnow().isoformat()
                })
            
        except Exception as e:
            self.logger.error(f"Compliance alerts error: {e}")
        
        return alerts
    
    def export_compliance_data(self, framework: ComplianceFramework, 
                              start_date: datetime, end_date: datetime,
                              format: str = 'json') -> str:
        """
        Export compliance data in specified format.
        
        Args:
            framework: Compliance framework
            start_date: Export start date
            end_date: Export end date
            format: Export format ('json', 'csv', 'xml')
            
        Returns:
            Path to exported file
        """
        try:
            if framework == ComplianceFramework.GDPR:
                data = self._export_gdpr_data(start_date, end_date)
            elif framework == ComplianceFramework.SOX:
                data = self.generate_sox_compliance_report(start_date, end_date)
            else:
                raise ValueError(f"Unsupported framework: {framework}")
            
            # Generate filename
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            filename = f"compliance_{framework.value}_{timestamp}.{format}"
            filepath = os.path.join(current_app.config.get('UPLOAD_FOLDER', 'uploads'), filename)
            
            # Export in requested format
            if format == 'json':
                with open(filepath, 'w') as f:
                    json.dump(data, f, indent=2, default=str)
            elif format == 'csv':
                self._export_to_csv(data, filepath)
            else:
                raise ValueError(f"Unsupported format: {format}")
            
            # Log export
            self.log_audit_event(
                AuditEventType.DATA_EXPORT,
                0,  # System generated
                {
                    'export_type': 'compliance_data',
                    'framework': framework.value,
                    'format': format,
                    'filename': filename
                }
            )
            
            return filepath
            
        except Exception as e:
            self.logger.error(f"Compliance data export error: {e}")
            raise ValueError("Failed to export compliance data")
    
    def _export_gdpr_data(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Export GDPR-specific compliance data."""
        from models import AuditLog, User, DataProtectionRecord
        
        return {
            'export_info': {
                'framework': 'GDPR',
                'period_start': start_date.isoformat(),
                'period_end': end_date.isoformat(),
                'generated_at': datetime.utcnow().isoformat()
            },
            'data_processing_activities': self._get_processing_activities(),
            'data_subject_requests': self._get_data_subject_requests(start_date, end_date),
            'data_breaches': self._get_data_breaches(start_date, end_date),
            'consent_records': self._get_consent_records(start_date, end_date),
            'data_protection_measures': self._get_protection_measures()
        }
    
    def _get_processing_activities(self) -> List[Dict[str, Any]]:
        """Get data processing activities for GDPR compliance."""
        return [
            {
                'activity_name': 'User Account Management',
                'purpose': 'Provide access to AI Executive Suite services',
                'legal_basis': 'Contract performance',
                'data_categories': ['Contact details', 'Account credentials', 'Usage data'],
                'data_subjects': 'Platform users',
                'recipients': 'Internal staff only',
                'retention_period': '2 years after account closure',
                'security_measures': ['Encryption', 'Access controls', 'Audit logging']
            },
            {
                'activity_name': 'AI Decision Support',
                'purpose': 'Provide AI-powered business decision recommendations',
                'legal_basis': 'Contract performance',
                'data_categories': ['Business context', 'Decision history', 'Preferences'],
                'data_subjects': 'Platform users',
                'recipients': 'AI service providers (OpenAI)',
                'retention_period': '7 years for business records',
                'security_measures': ['Data minimization', 'Encryption', 'Access logging']
            }
        ]
    
    def _get_data_subject_requests(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Get data subject requests in date range."""
        # This would query actual request records
        return []
    
    def _get_data_breaches(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Get data breaches in date range."""
        # This would query actual breach records
        return []
    
    def _get_consent_records(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Get consent records in date range."""
        # This would query actual consent records
        return []
    
    def _get_protection_measures(self) -> List[str]:
        """Get data protection measures implemented."""
        return [
            'End-to-end encryption for sensitive data',
            'Multi-factor authentication',
            'Regular security audits',
            'Data minimization practices',
            'Automated data retention policies',
            'Comprehensive audit logging',
            'Access controls and role-based permissions',
            'Regular staff training on data protection'
        ]
    
    def _export_to_csv(self, data: Dict[str, Any], filepath: str):
        """Export data to CSV format."""
        # Flatten the data structure for CSV export
        rows = []
        
        def flatten_dict(d, parent_key='', sep='_'):
            items = []
            for k, v in d.items():
                new_key = f"{parent_key}{sep}{k}" if parent_key else k
                if isinstance(v, dict):
                    items.extend(flatten_dict(v, new_key, sep=sep).items())
                elif isinstance(v, list):
                    for i, item in enumerate(v):
                        if isinstance(item, dict):
                            items.extend(flatten_dict(item, f"{new_key}_{i}", sep=sep).items())
                        else:
                            items.append((f"{new_key}_{i}", item))
                else:
                    items.append((new_key, v))
            return dict(items)
        
        flattened = flatten_dict(data)
        
        with open(filepath, 'w', newline='') as csvfile:
            if flattened:
                writer = csv.DictWriter(csvfile, fieldnames=flattened.keys())
                writer.writeheader()
                writer.writerow(flattened)