"""
Data Protection and Encryption Routes

Provides API endpoints for managing data encryption, classification, and retention.
"""

from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from services.data_encryption import DataEncryptionService, DataClassification, RetentionPolicy
from models import db, DataProtectionRecord, EncryptedField, DataRetentionJob
import json

data_protection_bp = Blueprint('data_protection', __name__, url_prefix='/api/data-protection')

# Initialize data encryption service
encryption_service = DataEncryptionService()


@data_protection_bp.route('/status')
@login_required
def get_protection_status():
    """Get overall data protection status."""
    try:
        # Get protection records summary
        total_records = DataProtectionRecord.query.count()
        encrypted_records = DataProtectionRecord.query.filter_by(is_encrypted=True).count()
        
        # Classification breakdown
        classification_counts = {}
        for classification in DataClassification:
            count = DataProtectionRecord.query.filter_by(classification=classification.value).count()
            classification_counts[classification.value] = count
        
        # Retention policy breakdown
        retention_counts = {}
        for policy in RetentionPolicy:
            count = DataProtectionRecord.query.filter_by(retention_policy=policy.value).count()
            retention_counts[policy.value] = count
        
        # Items due for deletion
        due_for_deletion = DataProtectionRecord.query.filter(
            DataProtectionRecord.deletion_date <= datetime.utcnow(),
            DataProtectionRecord.is_deleted == False
        ).count()
        
        return jsonify({
            'success': True,
            'total_records': total_records,
            'encrypted_records': encrypted_records,
            'encryption_percentage': (encrypted_records / total_records * 100) if total_records > 0 else 0,
            'classification_breakdown': classification_counts,
            'retention_breakdown': retention_counts,
            'due_for_deletion': due_for_deletion
        })
        
    except Exception as e:
        current_app.logger.error(f"Protection status error: {e}")
        return jsonify({'error': 'Failed to get protection status'}), 500


@data_protection_bp.route('/classify', methods=['POST'])
@login_required
def classify_data():
    """Classify data and get recommended protection level."""
    try:
        data = request.json
        text_data = data.get('data', '')
        context = data.get('context', {})
        
        if not text_data:
            return jsonify({'error': 'Data is required'}), 400
        
        # Classify the data
        classification = encryption_service.classify_data(text_data, context)
        retention_policy = encryption_service.get_retention_policy(
            classification, 
            context.get('data_type')
        )
        
        # Create protection metadata
        metadata = encryption_service.create_data_protection_metadata(text_data, context)
        
        return jsonify({
            'success': True,
            'classification': classification.value,
            'retention_policy': retention_policy.value,
            'metadata': metadata,
            'recommendations': {
                'should_encrypt': classification in [DataClassification.CONFIDENTIAL, DataClassification.RESTRICTED],
                'encryption_strength': 'high' if classification == DataClassification.RESTRICTED else 'standard',
                'access_logging': classification != DataClassification.PUBLIC
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Data classification error: {e}")
        return jsonify({'error': 'Failed to classify data'}), 500


@data_protection_bp.route('/encrypt', methods=['POST'])
@login_required
def encrypt_data():
    """Encrypt sensitive data."""
    try:
        data = request.json
        text_data = data.get('data', '')
        classification_str = data.get('classification', 'confidential')
        context = data.get('context', {})
        
        if not text_data:
            return jsonify({'error': 'Data is required'}), 400
        
        # Parse classification
        try:
            classification = DataClassification(classification_str)
        except ValueError:
            classification = DataClassification.CONFIDENTIAL
        
        # Encrypt the data
        encrypted_data = encryption_service.encrypt_field(text_data, classification)
        
        # Create hash for searchability
        data_hash, salt = encryption_service.hash_data(text_data)
        
        # Create protection record if requested
        if context.get('create_record', True):
            data_type = context.get('data_type', 'general')
            data_id = context.get('data_id', 'unknown')
            
            retention_policy = encryption_service.get_retention_policy(classification, data_type)
            deletion_date = encryption_service.calculate_retention_date(retention_policy)
            
            protection_record = DataProtectionRecord(
                data_type=data_type,
                data_id=data_id,
                classification=classification.value,
                retention_policy=retention_policy.value,
                is_encrypted=True,
                encryption_algorithm='Fernet',
                data_hash=data_hash,
                hash_salt=salt,
                deletion_date=deletion_date
            )
            
            db.session.add(protection_record)
            db.session.commit()
        
        return jsonify({
            'success': True,
            'encrypted_data': encrypted_data,
            'data_hash': data_hash,
            'classification': classification.value,
            'message': 'Data encrypted successfully'
        })
        
    except Exception as e:
        current_app.logger.error(f"Data encryption error: {e}")
        return jsonify({'error': 'Failed to encrypt data'}), 500


@data_protection_bp.route('/decrypt', methods=['POST'])
@login_required
def decrypt_data():
    """Decrypt encrypted data."""
    try:
        data = request.json
        encrypted_data = data.get('encrypted_data', '')
        classification_str = data.get('classification', 'confidential')
        record_id = data.get('record_id')
        
        if not encrypted_data:
            return jsonify({'error': 'Encrypted data is required'}), 400
        
        # Parse classification
        try:
            classification = DataClassification(classification_str)
        except ValueError:
            classification = DataClassification.CONFIDENTIAL
        
        # Update access tracking if record ID provided
        if record_id:
            protection_record = DataProtectionRecord.query.get(record_id)
            if protection_record:
                protection_record.update_access()
                db.session.commit()
        
        # Decrypt the data
        decrypted_data = encryption_service.decrypt_field(encrypted_data, classification)
        
        return jsonify({
            'success': True,
            'decrypted_data': decrypted_data,
            'message': 'Data decrypted successfully'
        })
        
    except Exception as e:
        current_app.logger.error(f"Data decryption error: {e}")
        return jsonify({'error': 'Failed to decrypt data'}), 500


@data_protection_bp.route('/records')
@login_required
def get_protection_records():
    """Get data protection records with filtering."""
    try:
        # Query parameters
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        classification = request.args.get('classification')
        retention_policy = request.args.get('retention_policy')
        data_type = request.args.get('data_type')
        due_for_deletion = request.args.get('due_for_deletion', type=bool)
        
        # Build query
        query = DataProtectionRecord.query.filter_by(is_deleted=False)
        
        if classification:
            query = query.filter_by(classification=classification)
        
        if retention_policy:
            query = query.filter_by(retention_policy=retention_policy)
        
        if data_type:
            query = query.filter_by(data_type=data_type)
        
        if due_for_deletion:
            query = query.filter(DataProtectionRecord.deletion_date <= datetime.utcnow())
        
        # Paginate results
        records = query.order_by(DataProtectionRecord.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'success': True,
            'records': [record.to_dict() for record in records.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': records.total,
                'pages': records.pages,
                'has_next': records.has_next,
                'has_prev': records.has_prev
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Protection records error: {e}")
        return jsonify({'error': 'Failed to get protection records'}), 500


@data_protection_bp.route('/records/<int:record_id>')
@login_required
def get_protection_record(record_id):
    """Get specific protection record details."""
    try:
        record = DataProtectionRecord.query.get_or_404(record_id)
        
        # Update access tracking
        record.update_access()
        db.session.commit()
        
        # Check retention compliance
        compliance = encryption_service.check_retention_compliance({
            'deletion_date': record.deletion_date.isoformat() if record.deletion_date else None
        })
        
        record_dict = record.to_dict()
        record_dict['compliance'] = compliance
        
        return jsonify({
            'success': True,
            'record': record_dict
        })
        
    except Exception as e:
        current_app.logger.error(f"Protection record error: {e}")
        return jsonify({'error': 'Failed to get protection record'}), 500


@data_protection_bp.route('/retention/check', methods=['POST'])
@login_required
def check_retention_compliance():
    """Check retention compliance and identify items for deletion."""
    try:
        # Create retention check job
        job = DataRetentionJob(
            job_type='retention_check',
            status='running'
        )
        job.start_job()
        db.session.add(job)
        db.session.commit()
        
        # Get records due for deletion
        due_records = DataProtectionRecord.query.filter(
            DataProtectionRecord.deletion_date <= datetime.utcnow(),
            DataProtectionRecord.is_deleted == False
        ).all()
        
        items_processed = 0
        items_due = 0
        compliance_report = []
        
        for record in due_records:
            items_processed += 1
            
            compliance = encryption_service.check_retention_compliance({
                'deletion_date': record.deletion_date.isoformat() if record.deletion_date else None
            })
            
            if compliance['should_delete']:
                items_due += 1
                compliance_report.append({
                    'record_id': record.id,
                    'data_type': record.data_type,
                    'data_id': record.data_id,
                    'classification': record.classification,
                    'compliance': compliance
                })
        
        # Complete job
        job.complete_job(items_processed=items_processed, items_deleted=0, items_failed=0)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'job_id': job.id,
            'items_processed': items_processed,
            'items_due_for_deletion': items_due,
            'compliance_report': compliance_report
        })
        
    except Exception as e:
        current_app.logger.error(f"Retention check error: {e}")
        return jsonify({'error': 'Failed to check retention compliance'}), 500


@data_protection_bp.route('/retention/delete', methods=['POST'])
@login_required
def execute_retention_deletion():
    """Execute retention-based data deletion."""
    try:
        data = request.json
        record_ids = data.get('record_ids', [])
        confirm_deletion = data.get('confirm', False)
        
        if not confirm_deletion:
            return jsonify({'error': 'Deletion must be confirmed'}), 400
        
        if not record_ids:
            return jsonify({'error': 'No records specified for deletion'}), 400
        
        # Create deletion job
        job = DataRetentionJob(
            job_type='secure_delete',
            status='running'
        )
        job.start_job()
        db.session.add(job)
        db.session.commit()
        
        items_processed = 0
        items_deleted = 0
        items_failed = 0
        
        for record_id in record_ids:
            items_processed += 1
            
            try:
                record = DataProtectionRecord.query.get(record_id)
                if record and not record.is_deleted:
                    # Check if deletion is due
                    if record.is_due_for_deletion():
                        # Perform secure deletion
                        success = encryption_service.secure_delete_data(record.data_id, record.data_type)
                        
                        if success:
                            record.mark_deleted('retention_policy')
                            items_deleted += 1
                        else:
                            items_failed += 1
                    else:
                        items_failed += 1
                else:
                    items_failed += 1
                    
            except Exception as e:
                current_app.logger.error(f"Failed to delete record {record_id}: {e}")
                items_failed += 1
        
        # Complete job
        job.complete_job(items_processed=items_processed, items_deleted=items_deleted, items_failed=items_failed)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'job_id': job.id,
            'items_processed': items_processed,
            'items_deleted': items_deleted,
            'items_failed': items_failed,
            'message': f'Deleted {items_deleted} items successfully'
        })
        
    except Exception as e:
        current_app.logger.error(f"Retention deletion error: {e}")
        return jsonify({'error': 'Failed to execute retention deletion'}), 500


@data_protection_bp.route('/jobs')
@login_required
def get_retention_jobs():
    """Get data retention job history."""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        job_type = request.args.get('job_type')
        status = request.args.get('status')
        
        # Build query
        query = DataRetentionJob.query
        
        if job_type:
            query = query.filter_by(job_type=job_type)
        
        if status:
            query = query.filter_by(status=status)
        
        # Paginate results
        jobs = query.order_by(DataRetentionJob.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'success': True,
            'jobs': [job.to_dict() for job in jobs.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': jobs.total,
                'pages': jobs.pages,
                'has_next': jobs.has_next,
                'has_prev': jobs.has_prev
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Retention jobs error: {e}")
        return jsonify({'error': 'Failed to get retention jobs'}), 500


@data_protection_bp.route('/report')
@login_required
def generate_protection_report():
    """Generate comprehensive data protection report."""
    try:
        # Get all protection records
        records = DataProtectionRecord.query.filter_by(is_deleted=False).all()
        
        # Convert to format expected by report generator
        data_items = []
        for record in records:
            data_items.append({
                'metadata': {
                    'classification': record.classification,
                    'retention_policy': record.retention_policy,
                    'deletion_date': record.deletion_date.isoformat() if record.deletion_date else None,
                    'encryption_used': record.is_encrypted
                }
            })
        
        # Generate report
        report = encryption_service.generate_data_protection_report(data_items)
        
        # Add additional statistics
        report['recent_jobs'] = DataRetentionJob.query.order_by(
            DataRetentionJob.created_at.desc()
        ).limit(5).all()
        
        report['recent_jobs'] = [job.to_dict() for job in report['recent_jobs']]
        
        return jsonify({
            'success': True,
            'report': report
        })
        
    except Exception as e:
        current_app.logger.error(f"Protection report error: {e}")
        return jsonify({'error': 'Failed to generate protection report'}), 500


@data_protection_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def manage_protection_settings():
    """Get or update data protection settings."""
    if request.method == 'GET':
        try:
            # Get current settings (would be stored in database or config)
            settings = {
                'auto_classification': True,
                'encryption_by_default': True,
                'retention_check_frequency': 'daily',
                'auto_deletion_enabled': False,
                'notification_settings': {
                    'retention_warnings': True,
                    'deletion_confirmations': True,
                    'compliance_reports': True
                },
                'classification_rules': {
                    'email_patterns': ['@company.com'],
                    'phone_patterns': [r'\d{3}-\d{3}-\d{4}'],
                    'ssn_patterns': [r'\d{3}-\d{2}-\d{4}']
                }
            }
            
            return jsonify({
                'success': True,
                'settings': settings
            })
            
        except Exception as e:
            current_app.logger.error(f"Get protection settings error: {e}")
            return jsonify({'error': 'Failed to get protection settings'}), 500
    
    else:  # POST
        try:
            settings = request.json
            
            # Validate and save settings (would be stored in database)
            # For now, just return success
            
            return jsonify({
                'success': True,
                'message': 'Protection settings updated successfully'
            })
            
        except Exception as e:
            current_app.logger.error(f"Update protection settings error: {e}")
            return jsonify({'error': 'Failed to update protection settings'}), 500