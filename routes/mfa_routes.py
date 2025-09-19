"""
Multi-Factor Authentication Routes

Provides API endpoints for MFA setup, verification, and management.
"""

from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from services.mfa import MFAService
from models import db, MFAMethod, MFABackupCode, MFAVerificationAttempt, PendingMFAVerification, MFARecoveryToken
import secrets

mfa_bp = Blueprint('mfa', __name__, url_prefix='/api/mfa')

# Initialize MFA service
mfa_service = MFAService()


@mfa_bp.route('/status')
@login_required
def get_mfa_status():
    """Get user's MFA status and available methods."""
    try:
        mfa_methods = current_user.get_enabled_mfa_methods()
        backup_codes_count = len(current_user.get_unused_backup_codes())
        
        return jsonify({
            'success': True,
            'mfa_enabled': current_user.has_mfa_enabled(),
            'methods': [method.to_dict() for method in mfa_methods],
            'backup_codes_count': backup_codes_count,
            'available_methods': ['totp', 'sms', 'email']
        })
        
    except Exception as e:
        current_app.logger.error(f"MFA status error: {e}")
        return jsonify({'error': 'Failed to get MFA status'}), 500


@mfa_bp.route('/totp/setup', methods=['POST'])
@login_required
def setup_totp():
    """Setup TOTP (Time-based One-Time Password) authentication."""
    try:
        # Check if TOTP is already enabled
        existing_totp = current_user.get_mfa_method('totp')
        if existing_totp and existing_totp.is_enabled:
            return jsonify({'error': 'TOTP is already enabled'}), 400
        
        # Generate TOTP secret and QR code
        secret, provisioning_uri = mfa_service.generate_totp_secret(
            current_user.id, 
            current_user.username
        )
        qr_code = mfa_service.generate_qr_code(provisioning_uri)
        
        # Encrypt and store the secret
        encrypted_secret = mfa_service.encrypt_sensitive_data(secret)
        
        # Create or update TOTP method
        if existing_totp:
            existing_totp.totp_secret = encrypted_secret
            existing_totp.is_verified = False
        else:
            totp_method = MFAMethod(
                user_id=current_user.id,
                method_type='totp',
                totp_secret=encrypted_secret
            )
            db.session.add(totp_method)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'secret': secret,  # Only return for initial setup
            'qr_code': qr_code,
            'message': 'TOTP setup initiated. Please verify with your authenticator app.'
        })
        
    except Exception as e:
        current_app.logger.error(f"TOTP setup error: {e}")
        return jsonify({'error': 'Failed to setup TOTP'}), 500


@mfa_bp.route('/totp/verify', methods=['POST'])
@login_required
def verify_totp_setup():
    """Verify TOTP setup with a token from authenticator app."""
    try:
        data = request.json
        token = data.get('token', '').strip()
        
        if not token or len(token) != 6:
            return jsonify({'error': 'Invalid token format'}), 400
        
        # Get TOTP method
        totp_method = current_user.get_mfa_method('totp')
        if not totp_method or not totp_method.totp_secret:
            return jsonify({'error': 'TOTP not set up'}), 400
        
        # Rate limiting
        if mfa_service.is_rate_limited(current_user.id, 'totp_verify'):
            return jsonify({'error': 'Too many attempts. Please try again later.'}), 429
        
        # Decrypt secret and verify token
        secret = mfa_service.decrypt_sensitive_data(totp_method.totp_secret)
        is_valid = mfa_service.verify_totp_token(secret, token)
        
        # Log attempt
        attempt = MFAVerificationAttempt(
            user_id=current_user.id,
            method_type='totp',
            ip_address=request.remote_addr,
            success=is_valid,
            failure_reason=None if is_valid else 'invalid_token',
            user_agent=request.headers.get('User-Agent')
        )
        db.session.add(attempt)
        
        if is_valid:
            # Enable TOTP
            totp_method.is_verified = True
            totp_method.is_enabled = True
            totp_method.last_used = datetime.utcnow()
            
            # Generate backup codes
            backup_codes = mfa_service.generate_backup_codes()
            for code in backup_codes:
                backup_code = MFABackupCode(current_user.id, code)
                db.session.add(backup_code)
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'TOTP enabled successfully',
                'backup_codes': backup_codes
            })
        else:
            db.session.commit()
            return jsonify({'error': 'Invalid token'}), 400
            
    except Exception as e:
        current_app.logger.error(f"TOTP verification error: {e}")
        return jsonify({'error': 'Failed to verify TOTP'}), 500


@mfa_bp.route('/sms/setup', methods=['POST'])
@login_required
def setup_sms():
    """Setup SMS-based MFA."""
    try:
        data = request.json
        phone_number = data.get('phone_number', '').strip()
        
        if not phone_number:
            return jsonify({'error': 'Phone number is required'}), 400
        
        # Basic phone number validation
        if not phone_number.startswith('+') or len(phone_number) < 10:
            return jsonify({'error': 'Invalid phone number format. Use international format (+1234567890)'}), 400
        
        # Rate limiting
        if mfa_service.is_rate_limited(current_user.id, 'sms_setup'):
            return jsonify({'error': 'Too many SMS requests. Please try again later.'}), 429
        
        # Generate verification code
        verification_code = mfa_service.generate_verification_code()
        
        # Send SMS
        sms_sent = mfa_service.send_sms_verification(phone_number, verification_code, 'setup')
        
        if not sms_sent:
            return jsonify({'error': 'Failed to send SMS. Please check your phone number.'}), 500
        
        # Store pending verification
        expires_at = datetime.utcnow() + timedelta(minutes=10)
        pending = PendingMFAVerification(
            user_id=current_user.id,
            method_type='sms',
            code=verification_code,
            contact_info=phone_number,
            expires_at=expires_at
        )
        db.session.add(pending)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Verification code sent to {phone_number[-4:]}',
            'masked_phone': phone_number[-4:]
        })
        
    except Exception as e:
        current_app.logger.error(f"SMS setup error: {e}")
        return jsonify({'error': 'Failed to setup SMS MFA'}), 500


@mfa_bp.route('/sms/verify', methods=['POST'])
@login_required
def verify_sms_setup():
    """Verify SMS setup with verification code."""
    try:
        data = request.json
        code = data.get('code', '').strip()
        
        if not code or len(code) != 6:
            return jsonify({'error': 'Invalid code format'}), 400
        
        # Get pending verification
        pending = PendingMFAVerification.query.filter_by(
            user_id=current_user.id,
            method_type='sms'
        ).order_by(PendingMFAVerification.created_at.desc()).first()
        
        if not pending or pending.is_expired():
            return jsonify({'error': 'Verification code expired or not found'}), 400
        
        if pending.is_max_attempts_reached():
            return jsonify({'error': 'Maximum verification attempts reached'}), 400
        
        # Verify code
        is_valid = pending.verify_code(code)
        pending.increment_attempts()
        
        # Log attempt
        attempt = MFAVerificationAttempt(
            user_id=current_user.id,
            method_type='sms',
            ip_address=request.remote_addr,
            success=is_valid,
            failure_reason=None if is_valid else 'invalid_code',
            user_agent=request.headers.get('User-Agent')
        )
        db.session.add(attempt)
        
        if is_valid:
            # Create or update SMS method
            sms_method = current_user.get_mfa_method('sms')
            if sms_method:
                sms_method.phone_number = pending.contact_info
                sms_method.is_verified = True
                sms_method.is_enabled = True
            else:
                sms_method = MFAMethod(
                    user_id=current_user.id,
                    method_type='sms',
                    phone_number=pending.contact_info,
                    is_verified=True,
                    is_enabled=True
                )
                db.session.add(sms_method)
            
            # Remove pending verification
            db.session.delete(pending)
            
            # Generate backup codes if this is the first MFA method
            if not current_user.has_mfa_enabled():
                backup_codes = mfa_service.generate_backup_codes()
                for backup_code in backup_codes:
                    backup_code_obj = MFABackupCode(current_user.id, backup_code)
                    db.session.add(backup_code_obj)
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'SMS MFA enabled successfully'
            })
        else:
            db.session.commit()
            return jsonify({'error': 'Invalid verification code'}), 400
            
    except Exception as e:
        current_app.logger.error(f"SMS verification error: {e}")
        return jsonify({'error': 'Failed to verify SMS'}), 500


@mfa_bp.route('/email/setup', methods=['POST'])
@login_required
def setup_email():
    """Setup email-based MFA."""
    try:
        data = request.json
        email_address = data.get('email_address', '').strip().lower()
        
        # Use current user's email if not provided
        if not email_address:
            email_address = current_user.email
        
        if not email_address or '@' not in email_address:
            return jsonify({'error': 'Valid email address is required'}), 400
        
        # Rate limiting
        if mfa_service.is_rate_limited(current_user.id, 'email_setup'):
            return jsonify({'error': 'Too many email requests. Please try again later.'}), 429
        
        # Generate verification code
        verification_code = mfa_service.generate_verification_code()
        
        # Send email
        email_sent = mfa_service.send_email_verification(email_address, verification_code, 'setup')
        
        if not email_sent:
            return jsonify({'error': 'Failed to send email. Please check your email address.'}), 500
        
        # Store pending verification
        expires_at = datetime.utcnow() + timedelta(minutes=10)
        pending = PendingMFAVerification(
            user_id=current_user.id,
            method_type='email',
            code=verification_code,
            contact_info=email_address,
            expires_at=expires_at
        )
        db.session.add(pending)
        db.session.commit()
        
        # Mask email for response
        masked_email = mfa_service._mask_email(email_address) if hasattr(mfa_service, '_mask_email') else email_address
        
        return jsonify({
            'success': True,
            'message': f'Verification code sent to {masked_email}',
            'masked_email': masked_email
        })
        
    except Exception as e:
        current_app.logger.error(f"Email setup error: {e}")
        return jsonify({'error': 'Failed to setup email MFA'}), 500


@mfa_bp.route('/email/verify', methods=['POST'])
@login_required
def verify_email_setup():
    """Verify email setup with verification code."""
    try:
        data = request.json
        code = data.get('code', '').strip()
        
        if not code or len(code) != 6:
            return jsonify({'error': 'Invalid code format'}), 400
        
        # Get pending verification
        pending = PendingMFAVerification.query.filter_by(
            user_id=current_user.id,
            method_type='email'
        ).order_by(PendingMFAVerification.created_at.desc()).first()
        
        if not pending or pending.is_expired():
            return jsonify({'error': 'Verification code expired or not found'}), 400
        
        if pending.is_max_attempts_reached():
            return jsonify({'error': 'Maximum verification attempts reached'}), 400
        
        # Verify code
        is_valid = pending.verify_code(code)
        pending.increment_attempts()
        
        # Log attempt
        attempt = MFAVerificationAttempt(
            user_id=current_user.id,
            method_type='email',
            ip_address=request.remote_addr,
            success=is_valid,
            failure_reason=None if is_valid else 'invalid_code',
            user_agent=request.headers.get('User-Agent')
        )
        db.session.add(attempt)
        
        if is_valid:
            # Create or update email method
            email_method = current_user.get_mfa_method('email')
            if email_method:
                email_method.email_address = pending.contact_info
                email_method.is_verified = True
                email_method.is_enabled = True
            else:
                email_method = MFAMethod(
                    user_id=current_user.id,
                    method_type='email',
                    email_address=pending.contact_info,
                    is_verified=True,
                    is_enabled=True
                )
                db.session.add(email_method)
            
            # Remove pending verification
            db.session.delete(pending)
            
            # Generate backup codes if this is the first MFA method
            if not current_user.has_mfa_enabled():
                backup_codes = mfa_service.generate_backup_codes()
                for backup_code in backup_codes:
                    backup_code_obj = MFABackupCode(current_user.id, backup_code)
                    db.session.add(backup_code_obj)
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Email MFA enabled successfully'
            })
        else:
            db.session.commit()
            return jsonify({'error': 'Invalid verification code'}), 400
            
    except Exception as e:
        current_app.logger.error(f"Email verification error: {e}")
        return jsonify({'error': 'Failed to verify email'}), 500


@mfa_bp.route('/backup-codes')
@login_required
def get_backup_codes():
    """Get user's backup codes (only show count for security)."""
    try:
        unused_codes = current_user.get_unused_backup_codes()
        
        return jsonify({
            'success': True,
            'backup_codes_count': len(unused_codes),
            'total_codes': len(current_user.backup_codes)
        })
        
    except Exception as e:
        current_app.logger.error(f"Backup codes error: {e}")
        return jsonify({'error': 'Failed to get backup codes'}), 500


@mfa_bp.route('/backup-codes/regenerate', methods=['POST'])
@login_required
def regenerate_backup_codes():
    """Regenerate backup codes."""
    try:
        if not current_user.has_mfa_enabled():
            return jsonify({'error': 'MFA must be enabled to generate backup codes'}), 400
        
        # Mark all existing backup codes as used
        for backup_code in current_user.backup_codes:
            backup_code.mark_used()
        
        # Generate new backup codes
        new_codes = mfa_service.generate_backup_codes()
        for code in new_codes:
            backup_code = MFABackupCode(current_user.id, code)
            db.session.add(backup_code)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'backup_codes': new_codes,
            'message': 'New backup codes generated. Save them securely!'
        })
        
    except Exception as e:
        current_app.logger.error(f"Backup codes regeneration error: {e}")
        return jsonify({'error': 'Failed to regenerate backup codes'}), 500


@mfa_bp.route('/disable/<method_type>', methods=['POST'])
@login_required
def disable_mfa_method(method_type):
    """Disable a specific MFA method."""
    try:
        if method_type not in ['totp', 'sms', 'email']:
            return jsonify({'error': 'Invalid MFA method'}), 400
        
        # Get MFA method
        mfa_method = current_user.get_mfa_method(method_type)
        if not mfa_method:
            return jsonify({'error': 'MFA method not found'}), 404
        
        # Disable the method
        mfa_method.is_enabled = False
        
        # If this was the last enabled method, disable all backup codes
        remaining_methods = [m for m in current_user.mfa_methods if m.is_enabled and m.id != mfa_method.id]
        if not remaining_methods:
            for backup_code in current_user.backup_codes:
                backup_code.mark_used()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'{method_type.upper()} MFA disabled successfully'
        })
        
    except Exception as e:
        current_app.logger.error(f"MFA disable error: {e}")
        return jsonify({'error': 'Failed to disable MFA method'}), 500


@mfa_bp.route('/recovery/request', methods=['POST'])
@login_required
def request_recovery():
    """Request MFA recovery token."""
    try:
        # Generate recovery token
        recovery_token = mfa_service.generate_recovery_token(current_user.id)
        
        # Store recovery token in database
        expires_at = datetime.utcnow() + timedelta(hours=24)
        recovery_token_obj = MFARecoveryToken(
            user_id=current_user.id,
            token=recovery_token,
            ip_address=request.remote_addr,
            expires_at=expires_at
        )
        db.session.add(recovery_token_obj)
        db.session.commit()
        
        # Send recovery token via email
        if current_user.email:
            email_sent = mfa_service.send_email_verification(
                current_user.email, 
                recovery_token, 
                'recovery'
            )
            
            if email_sent:
                return jsonify({
                    'success': True,
                    'message': 'Recovery token sent to your email address'
                })
        
        return jsonify({
            'success': True,
            'recovery_token': recovery_token,
            'message': 'Recovery token generated. Save it securely!'
        })
        
    except Exception as e:
        current_app.logger.error(f"MFA recovery request error: {e}")
        return jsonify({'error': 'Failed to request recovery'}), 500


@mfa_bp.route('/attempts')
@login_required
def get_mfa_attempts():
    """Get recent MFA verification attempts for security monitoring."""
    try:
        attempts = MFAVerificationAttempt.query.filter_by(
            user_id=current_user.id
        ).order_by(MFAVerificationAttempt.timestamp.desc()).limit(20).all()
        
        attempts_data = []
        for attempt in attempts:
            attempts_data.append({
                'method_type': attempt.method_type,
                'success': attempt.success,
                'failure_reason': attempt.failure_reason,
                'ip_address': attempt.ip_address,
                'timestamp': attempt.timestamp.isoformat()
            })
        
        return jsonify({
            'success': True,
            'attempts': attempts_data
        })
        
    except Exception as e:
        current_app.logger.error(f"MFA attempts error: {e}")
        return jsonify({'error': 'Failed to get MFA attempts'}), 500