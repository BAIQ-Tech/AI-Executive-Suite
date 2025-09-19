"""
Multi-Factor Authentication Service

Provides TOTP-based 2FA, SMS/email verification, backup codes, and recovery options.
"""

import secrets
import base64
import qrcode
import io
from datetime import datetime, timedelta
from typing import List, Optional, Tuple, Dict
import pyotp
from cryptography.fernet import Fernet
from flask import current_app
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
import requests
import json


class MFAService:
    """Multi-Factor Authentication service for managing 2FA, backup codes, and verification."""
    
    def __init__(self):
        self.encryption_key = self._get_encryption_key()
        self.cipher_suite = Fernet(self.encryption_key)
    
    def _get_encryption_key(self) -> bytes:
        """Get or generate encryption key for sensitive MFA data."""
        key = current_app.config.get('MFA_ENCRYPTION_KEY')
        if not key:
            # Generate a new key - in production, this should be stored securely
            key = Fernet.generate_key()
            current_app.logger.warning("Generated new MFA encryption key - store this securely!")
        
        if isinstance(key, str):
            key = key.encode()
        
        return key
    
    def generate_totp_secret(self, user_id: int, username: str) -> Tuple[str, str]:
        """
        Generate TOTP secret for a user.
        
        Args:
            user_id: User ID
            username: Username for QR code label
            
        Returns:
            Tuple of (secret_key, provisioning_uri)
        """
        # Generate a random secret
        secret = pyotp.random_base32()
        
        # Create TOTP object
        totp = pyotp.TOTP(secret)
        
        # Generate provisioning URI for QR code
        app_name = current_app.config.get('APP_NAME', 'AI Executive Suite')
        provisioning_uri = totp.provisioning_uri(
            name=username,
            issuer_name=app_name
        )
        
        return secret, provisioning_uri
    
    def generate_qr_code(self, provisioning_uri: str) -> str:
        """
        Generate QR code image for TOTP setup.
        
        Args:
            provisioning_uri: TOTP provisioning URI
            
        Returns:
            Base64 encoded QR code image
        """
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(provisioning_uri)
        qr.make(fit=True)
        
        # Create QR code image
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        img_base64 = base64.b64encode(buffer.getvalue()).decode()
        return f"data:image/png;base64,{img_base64}"
    
    def verify_totp_token(self, secret: str, token: str, window: int = 1) -> bool:
        """
        Verify TOTP token.
        
        Args:
            secret: TOTP secret key
            token: 6-digit TOTP token
            window: Time window for verification (default 1 = 30 seconds before/after)
            
        Returns:
            True if token is valid
        """
        try:
            totp = pyotp.TOTP(secret)
            return totp.verify(token, valid_window=window)
        except Exception as e:
            current_app.logger.error(f"TOTP verification error: {e}")
            return False
    
    def generate_backup_codes(self, count: int = 10) -> List[str]:
        """
        Generate backup recovery codes.
        
        Args:
            count: Number of backup codes to generate
            
        Returns:
            List of backup codes
        """
        codes = []
        for _ in range(count):
            # Generate 8-character alphanumeric code
            code = secrets.token_hex(4).upper()
            # Format as XXXX-XXXX for readability
            formatted_code = f"{code[:4]}-{code[4:]}"
            codes.append(formatted_code)
        
        return codes
    
    def encrypt_sensitive_data(self, data: str) -> str:
        """
        Encrypt sensitive MFA data.
        
        Args:
            data: Data to encrypt
            
        Returns:
            Encrypted data as base64 string
        """
        encrypted_data = self.cipher_suite.encrypt(data.encode())
        return base64.b64encode(encrypted_data).decode()
    
    def decrypt_sensitive_data(self, encrypted_data: str) -> str:
        """
        Decrypt sensitive MFA data.
        
        Args:
            encrypted_data: Base64 encoded encrypted data
            
        Returns:
            Decrypted data
        """
        try:
            encrypted_bytes = base64.b64decode(encrypted_data.encode())
            decrypted_data = self.cipher_suite.decrypt(encrypted_bytes)
            return decrypted_data.decode()
        except Exception as e:
            current_app.logger.error(f"Decryption error: {e}")
            raise ValueError("Failed to decrypt data")
    
    def generate_verification_code(self, length: int = 6) -> str:
        """
        Generate numeric verification code for SMS/email.
        
        Args:
            length: Length of verification code
            
        Returns:
            Numeric verification code
        """
        return ''.join([str(secrets.randbelow(10)) for _ in range(length)])
    
    def send_email_verification(self, email: str, code: str, purpose: str = "verification") -> bool:
        """
        Send verification code via email.
        
        Args:
            email: Recipient email address
            code: Verification code
            purpose: Purpose of verification (verification, recovery, etc.)
            
        Returns:
            True if email sent successfully
        """
        try:
            smtp_server = current_app.config.get('SMTP_SERVER')
            smtp_port = current_app.config.get('SMTP_PORT', 587)
            smtp_username = current_app.config.get('SMTP_USERNAME')
            smtp_password = current_app.config.get('SMTP_PASSWORD')
            from_email = current_app.config.get('FROM_EMAIL', smtp_username)
            
            if not all([smtp_server, smtp_username, smtp_password]):
                current_app.logger.error("SMTP configuration missing")
                return False
            
            # Create message
            msg = MimeMultipart()
            msg['From'] = from_email
            msg['To'] = email
            msg['Subject'] = f"AI Executive Suite - {purpose.title()} Code"
            
            # Email body
            body = f"""
            Your {purpose} code is: {code}
            
            This code will expire in 10 minutes.
            
            If you didn't request this code, please ignore this email.
            
            Best regards,
            AI Executive Suite Team
            """
            
            msg.attach(MimeText(body, 'plain'))
            
            # Send email
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.send_message(msg)
            server.quit()
            
            return True
            
        except Exception as e:
            current_app.logger.error(f"Email sending error: {e}")
            return False
    
    def send_sms_verification(self, phone: str, code: str, purpose: str = "verification") -> bool:
        """
        Send verification code via SMS.
        
        Args:
            phone: Phone number
            code: Verification code
            purpose: Purpose of verification
            
        Returns:
            True if SMS sent successfully
        """
        try:
            # Using Twilio as example - replace with your SMS provider
            twilio_sid = current_app.config.get('TWILIO_ACCOUNT_SID')
            twilio_token = current_app.config.get('TWILIO_AUTH_TOKEN')
            twilio_phone = current_app.config.get('TWILIO_PHONE_NUMBER')
            
            if not all([twilio_sid, twilio_token, twilio_phone]):
                current_app.logger.error("Twilio configuration missing")
                return False
            
            # Twilio API endpoint
            url = f"https://api.twilio.com/2010-04-01/Accounts/{twilio_sid}/Messages.json"
            
            # Message data
            data = {
                'From': twilio_phone,
                'To': phone,
                'Body': f"Your AI Executive Suite {purpose} code is: {code}. Valid for 10 minutes."
            }
            
            # Send SMS
            response = requests.post(
                url,
                data=data,
                auth=(twilio_sid, twilio_token)
            )
            
            return response.status_code == 201
            
        except Exception as e:
            current_app.logger.error(f"SMS sending error: {e}")
            return False
    
    def validate_backup_code(self, user_backup_codes: List[str], provided_code: str) -> Tuple[bool, List[str]]:
        """
        Validate backup code and remove it from available codes.
        
        Args:
            user_backup_codes: List of user's backup codes
            provided_code: Code provided by user
            
        Returns:
            Tuple of (is_valid, remaining_codes)
        """
        # Normalize the provided code
        normalized_code = provided_code.upper().replace('-', '').replace(' ', '')
        
        # Check each backup code
        for i, backup_code in enumerate(user_backup_codes):
            normalized_backup = backup_code.upper().replace('-', '').replace(' ', '')
            
            if normalized_code == normalized_backup:
                # Remove the used code
                remaining_codes = user_backup_codes.copy()
                remaining_codes.pop(i)
                return True, remaining_codes
        
        return False, user_backup_codes
    
    def is_rate_limited(self, user_id: int, action: str, max_attempts: int = 5, window_minutes: int = 15) -> bool:
        """
        Check if user is rate limited for MFA actions.
        
        Args:
            user_id: User ID
            action: Action type (totp_verify, sms_send, email_send, etc.)
            max_attempts: Maximum attempts allowed
            window_minutes: Time window in minutes
            
        Returns:
            True if rate limited
        """
        # This would typically use Redis or database to track attempts
        # For now, we'll implement a simple in-memory solution
        # In production, use Redis with expiring keys
        
        from flask import g
        
        if not hasattr(g, 'mfa_attempts'):
            g.mfa_attempts = {}
        
        key = f"{user_id}:{action}"
        now = datetime.utcnow()
        
        if key not in g.mfa_attempts:
            g.mfa_attempts[key] = []
        
        # Clean old attempts
        cutoff = now - timedelta(minutes=window_minutes)
        g.mfa_attempts[key] = [
            attempt for attempt in g.mfa_attempts[key] 
            if attempt > cutoff
        ]
        
        # Check if rate limited
        if len(g.mfa_attempts[key]) >= max_attempts:
            return True
        
        # Record this attempt
        g.mfa_attempts[key].append(now)
        return False
    
    def generate_recovery_token(self, user_id: int) -> str:
        """
        Generate secure recovery token for account recovery.
        
        Args:
            user_id: User ID
            
        Returns:
            Recovery token
        """
        # Create payload with user ID and expiration
        payload = {
            'user_id': user_id,
            'exp': datetime.utcnow() + timedelta(hours=24),  # 24 hour expiry
            'purpose': 'mfa_recovery'
        }
        
        # Generate JWT token
        import jwt
        secret_key = current_app.config.get('SECRET_KEY')
        token = jwt.encode(payload, secret_key, algorithm='HS256')
        
        return token
    
    def verify_recovery_token(self, token: str) -> Optional[int]:
        """
        Verify recovery token and return user ID.
        
        Args:
            token: Recovery token
            
        Returns:
            User ID if valid, None otherwise
        """
        try:
            import jwt
            secret_key = current_app.config.get('SECRET_KEY')
            payload = jwt.decode(token, secret_key, algorithms=['HS256'])
            
            if payload.get('purpose') != 'mfa_recovery':
                return None
            
            return payload.get('user_id')
            
        except jwt.ExpiredSignatureError:
            current_app.logger.warning("Recovery token expired")
            return None
        except jwt.InvalidTokenError:
            current_app.logger.warning("Invalid recovery token")
            return None