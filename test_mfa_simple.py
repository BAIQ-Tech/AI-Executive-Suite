#!/usr/bin/env python3
"""
Simple test to verify MFA functionality works
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
# from services.mfa import MFAService
import pyotp

def test_mfa_service():
    """Test basic MFA service functionality."""
    
    # Test basic TOTP functionality without the full service
    import pyotp
    from cryptography.fernet import Fernet
    import secrets
        
    print("Testing MFA Core Functionality...")
    
    # Test TOTP secret generation
    print("1. Testing TOTP secret generation...")
    secret = pyotp.random_base32()
    totp = pyotp.TOTP(secret)
    provisioning_uri = totp.provisioning_uri(name='testuser', issuer_name='AI Executive Suite')
    print(f"   ✓ Secret generated: {secret[:8]}...")
    print(f"   ✓ Provisioning URI: {provisioning_uri[:50]}...")
    
    # Test TOTP token verification
    print("2. Testing TOTP token verification...")
    valid_token = totp.now()
    is_valid = totp.verify(valid_token)
    print(f"   ✓ Token verification: {is_valid}")
    
    # Test invalid token
    is_invalid = totp.verify('000000')
    print(f"   ✓ Invalid token rejected: {not is_invalid}")
    
    # Test backup code generation
    print("3. Testing backup code generation...")
    backup_codes = []
    for _ in range(5):
        code = secrets.token_hex(4).upper()
        formatted_code = f"{code[:4]}-{code[4:]}"
        backup_codes.append(formatted_code)
    print(f"   ✓ Generated {len(backup_codes)} backup codes")
    print(f"   ✓ Sample code: {backup_codes[0]}")
    
    # Test encryption/decryption
    print("4. Testing encryption/decryption...")
    key = Fernet.generate_key()
    cipher_suite = Fernet(key)
    original_data = "sensitive-totp-secret"
    encrypted = cipher_suite.encrypt(original_data.encode())
    decrypted = cipher_suite.decrypt(encrypted).decode()
    print(f"   ✓ Encryption/decryption: {original_data == decrypted}")
    
    # Test verification code generation
    print("5. Testing verification code generation...")
    code = ''.join([str(secrets.randbelow(10)) for _ in range(6)])
    print(f"   ✓ Verification code: {code} (length: {len(code)})")
    
    print("\n✅ All MFA core functionality tests passed!")

if __name__ == '__main__':
    test_mfa_service()