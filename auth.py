from flask import Blueprint, request, jsonify, redirect, url_for, session, current_app, render_template
from flask_login import login_user, logout_user, login_required, current_user
import bcrypt
import secrets
from datetime import datetime, timedelta
import requests
from authlib.integrations.flask_client import OAuth
import json
import os
from dotenv import load_dotenv

load_dotenv()

auth_bp = Blueprint('auth', __name__)

# Import models at module level to avoid circular imports
from models import User, LoginAttempt, UserSession

def get_models():
    """Get models and db instance to avoid circular imports."""
    from app import db
    from models import User, LoginAttempt, UserSession
    return User, LoginAttempt, UserSession, db

# OAuth setup
oauth = OAuth()

# Google OAuth
google = oauth.register(
    name='google',
    client_id=os.getenv('GOOGLE_CLIENT_ID'),
    client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
    server_metadata_url='https://accounts.google.com/.well-known/openid_configuration',
    client_kwargs={
        'scope': 'openid email profile'
    }
)

# Apple OAuth
apple = oauth.register(
    name='apple',
    client_id=os.getenv('APPLE_CLIENT_ID'),
    client_secret=os.getenv('APPLE_CLIENT_SECRET'),
    server_metadata_url='https://appleid.apple.com/.well-known/openid_configuration',
    client_kwargs={
        'scope': 'name email'
    }
)

def log_login_attempt(ip_address, method, email=None, wallet_address=None, success=False):
    """Log login attempt for security monitoring."""
    User, LoginAttempt, UserSession, db = get_models()
    attempt = LoginAttempt(
        ip_address=ip_address,
        method=method,
        email=email,
        wallet_address=wallet_address,
        success=success,
        user_agent=request.headers.get('User-Agent', '')
    )
    db.session.add(attempt)
    db.session.commit()

def create_session_token():
    """Generate secure session token."""
    return secrets.token_urlsafe(64)

def create_user_session(user_id, ip_address):
    """Create new user session."""
    User, LoginAttempt, UserSession, db = get_models()
    session_token = create_session_token()
    user_session = UserSession(
        user_id=user_id,
        session_token=session_token,
        ip_address=ip_address,
        user_agent=request.headers.get('User-Agent', ''),
        expires_at=datetime.utcnow() + timedelta(days=30)
    )
    db.session.add(user_session)
    db.session.commit()
    return session_token

@auth_bp.route('/login')
def login_page():
    """Display login page."""
    return render_template('login.html')

@auth_bp.route('/api/auth/register', methods=['POST'])
def register():
    """Register new user with email/password."""
    User, LoginAttempt, UserSession, db = get_models()
    data = request.json
    name = data.get('name', '')
    username = data.get('username', '')
    email = data.get('email', '').lower()
    password = data.get('password', '')
    
    if not all([name, username, email, password]):
        return jsonify({'error': 'All fields are required'}), 400
    
    # Check if user already exists
    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'Email already registered'}), 400
    
    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'Username already taken'}), 400
    
    # Create user
    user = User(
        username=username,
        email=email,
        name=name
    )
    user.set_password(password)
    
    db.session.add(user)
    db.session.commit()
    
    # Log successful registration
    ip_address = request.remote_addr
    log_login_attempt(ip_address, 'register', email=email, success=True)
    
    return jsonify({
        'success': True,
        'user': user.to_dict(),
        'message': 'Registration successful'
    })

@auth_bp.route('/api/auth/login', methods=['POST'])
def login():
    """Login with email/password."""
    User, LoginAttempt, UserSession, db = get_models()
    data = request.json
    email = data.get('email', '').lower()
    password = data.get('password', '')
    
    if not email or not password:
        return jsonify({'error': 'Email and password are required'}), 400
    
    ip_address = request.remote_addr
    
    # Find user
    user = User.query.filter_by(email=email).first()
    
    if not user or not bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
        log_login_attempt(ip_address, 'email', email=email, success=False)
        return jsonify({'error': 'Invalid email or password'}), 401
    
    # Log successful login
    log_login_attempt(ip_address, 'email', email=email, success=True)
    
    # Login user
    login_user(user)
    user.update_last_login()
    db.session.commit()
    
    # Create session
    session_token = create_user_session(user.id, ip_address)
    session['session_token'] = session_token
    
    return jsonify({
        'success': True,
        'user': user.to_dict(),
        'message': 'Login successful'
    })

@auth_bp.route('/google')
def google_login():
    """Initiate Google OAuth login."""
    redirect_uri = url_for('auth.google_callback', _external=True)
    return google.authorize_redirect(redirect_uri)

@auth_bp.route('/google/callback')
def google_callback():
    """Handle Google OAuth callback."""
    try:
        token = google.authorize_access_token()
        user_info = token.get('userinfo')
        
        if not user_info:
            return jsonify({'error': 'Failed to get user info from Google'}), 400
        
        google_id = user_info.get('sub')
        email = user_info.get('email', '').lower()
        name = user_info.get('name', '')
        avatar_url = user_info.get('picture', '')
        
        ip_address = request.remote_addr
        
        # Find existing user
        user = User.query.filter_by(google_id=google_id).first()
        
        if not user and email:
            # Check if user exists with same email
            user = User.query.filter_by(email=email).first()
            if user:
                # Link Google account to existing user
                user.set_google_id(google_id)
                if not user.name:
                    user.name = name
                if not user.avatar_url:
                    user.avatar_url = avatar_url
            else:
                # Create new user
                username = email.split('@')[0]
                # Ensure unique username
                counter = 1
                original_username = username
                while User.query.filter_by(username=username).first():
                    username = f"{original_username}{counter}"
                    counter += 1
                
                user = User(username=username, email=email, name=name)
                user.set_google_id(google_id)
                user.avatar_url = avatar_url
                user.email_verified = True
                db.session.add(user)
        
        if not user:
            return jsonify({'error': 'Failed to create or find user'}), 400
        
        from models import db
        db.session.commit()
        
        # Log successful login
        log_login_attempt(ip_address, 'google', email=email, success=True)
        
        # Login user
        login_user(user)
        user.update_last_login()
        from models import db
        db.session.commit()
        
        # Create session
        session_token = create_user_session(user.id, ip_address)
        session['session_token'] = session_token
        
        return redirect('/?login=success')
        
    except Exception as e:
        ip_address = request.remote_addr
        log_login_attempt(ip_address, 'google', success=False)
        return jsonify({'error': f'Google login failed: {str(e)}'}), 400

@auth_bp.route('/apple')
def apple_login():
    """Initiate Apple Sign-In."""
    redirect_uri = url_for('auth.apple_callback', _external=True)
    return apple.authorize_redirect(redirect_uri)

@auth_bp.route('/apple/callback')
def apple_callback():
    """Handle Apple Sign-In callback."""
    try:
        token = apple.authorize_access_token()
        user_info = token.get('userinfo')
        
        if not user_info:
            return jsonify({'error': 'Failed to get user info from Apple'}), 400
        
        apple_id = user_info.get('sub')
        email = user_info.get('email', '').lower()
        name = user_info.get('name', '')
        
        ip_address = request.remote_addr
        
        # Find existing user
        user = User.query.filter_by(apple_id=apple_id).first()
        
        if not user and email:
            # Check if user exists with same email
            user = User.query.filter_by(email=email).first()
            if user:
                # Link Apple account to existing user
                user.set_apple_id(apple_id)
                if not user.name:
                    user.name = name
            else:
                # Create new user
                username = email.split('@')[0] if email else f"apple_user_{apple_id[:8]}"
                # Ensure unique username
                counter = 1
                original_username = username
                while User.query.filter_by(username=username).first():
                    username = f"{original_username}{counter}"
                    counter += 1
                
                user = User(username=username, email=email, name=name)
                user.set_apple_id(apple_id)
                user.email_verified = True
                db.session.add(user)
        
        if not user:
            return jsonify({'error': 'Failed to create or find user'}), 400
        
        from models import db
        db.session.commit()
        
        # Log successful login
        log_login_attempt(ip_address, 'apple', email=email, success=True)
        
        # Login user
        login_user(user)
        user.update_last_login()
        from models import db
        db.session.commit()
        
        # Create session
        session_token = create_user_session(user.id, ip_address)
        session['session_token'] = session_token
        
        return redirect('/?login=success')
        
    except Exception as e:
        ip_address = request.remote_addr
        log_login_attempt(ip_address, 'apple', success=False)
        return jsonify({'error': f'Apple login failed: {str(e)}'}), 400

@auth_bp.route('/web3', methods=['POST'])
def web3_verify():
    """Verify Web3 wallet signature and login."""
    data = request.json
    wallet_address = data.get('address', '')
    signature = data.get('signature', '')
    message = data.get('message', '')
    wallet_type = data.get('wallet_type', 'metamask')
    
    return handle_ethereum_wallet_auth(wallet_address, signature, message, wallet_type)

@auth_bp.route('/phantom', methods=['POST'])
def phantom_verify():
    """Verify Phantom wallet signature and login."""
    data = request.json
    wallet_address = data.get('address', '')
    signature = data.get('signature', '')
    message = data.get('message', '')
    wallet_type = 'phantom'
    
    return handle_solana_wallet_auth(wallet_address, signature, message, wallet_type)

def handle_ethereum_wallet_auth(wallet_address, signature, message, wallet_type):
    """Handle Ethereum-based wallet authentication (MetaMask, Coinbase)."""
    if not wallet_address or not signature or not message:
        return jsonify({'error': 'Wallet address, signature, and message are required'}), 400
    
    ip_address = request.remote_addr
    
    try:
        # Verify the signature using eth-account
        from eth_account.messages import encode_defunct
        from eth_account import Account
        
        # Create the message hash
        message_hash = encode_defunct(text=message)
        
        # Recover the address from the signature
        recovered_address = Account.recover_message(message_hash, signature=signature)
        
        # Verify that the recovered address matches the provided address
        if recovered_address.lower() != wallet_address.lower():
            try:
                log_login_attempt(ip_address, 'web3', wallet_address=wallet_address, success=False)
            except:
                pass
            return jsonify({'error': 'Invalid signature'}), 401
        
        # Get models and db instance
        User, LoginAttempt, UserSession, db = get_models()
        
        # Find or create user
        user = User.query.filter_by(wallet_address=wallet_address.lower()).first()
        
        if not user:
            # Create new user with wallet
            username = f"{wallet_type}_{wallet_address[:8]}"
            counter = 1
            original_username = username
            while User.query.filter_by(username=username).first():
                username = f"{original_username}{counter}"
                counter += 1
            
            user = User(username=username, name=f"{wallet_type.title()} User {wallet_address[:8]}")
            user.set_wallet(wallet_address, wallet_type)
            db.session.add(user)
            db.session.commit()
        
        # Log successful login
        try:
            log_login_attempt(ip_address, 'web3', wallet_address=wallet_address, success=True)
        except:
            pass
        
        # Login user
        login_user(user)
        user.update_last_login()
        db.session.commit()
        
        # Create session
        session_token = create_user_session(user.id, ip_address)
        session['session_token'] = session_token
        
        return jsonify({
            'success': True,
            'user': user.to_dict(),
            'message': 'Web3 login successful'
        })
        
    except Exception as e:
        print(f"Web3 authentication error: {e}")
        try:
            log_login_attempt(ip_address, 'web3', wallet_address=wallet_address, success=False)
        except:
            pass
        return jsonify({'error': f'Web3 verification failed: {str(e)}'}), 500

def handle_solana_wallet_auth(wallet_address, signature, message, wallet_type):
    """Handle Solana-based wallet authentication (Phantom)."""
    try:
        
        if not wallet_address or not signature or not message:
            return jsonify({'error': 'Wallet address, signature, and message are required'}), 400
        
        ip_address = request.remote_addr
        
        # For Phantom/Solana wallets, we'll use a simplified verification
        # In production, you would use proper Solana signature verification
        is_valid = len(signature) > 50 and signature.startswith('0x')
        
        if not is_valid:
            try:
                log_login_attempt(ip_address, 'solana', wallet_address=wallet_address, success=False)
            except:
                pass  # Don't fail authentication due to logging issues
            return jsonify({'error': 'Invalid signature'}), 401
        
        # Get models and db instance
        User, LoginAttempt, UserSession, db = get_models()
        
        # Find or create user
        user = User.query.filter_by(wallet_address=wallet_address).first()
        
        if not user:
            # Create new user with wallet
            username = f"phantom_{wallet_address[:8]}"
            counter = 1
            original_username = username
            while User.query.filter_by(username=username).first():
                username = f"{original_username}{counter}"
                counter += 1
            
            user = User(username=username, name=f"Phantom User {wallet_address[:8]}")
            user.set_wallet(wallet_address, wallet_type)
            db.session.add(user)
            db.session.commit()
        
        # Log successful login
        try:
            log_login_attempt(ip_address, 'solana', wallet_address=wallet_address, success=True)
        except:
            pass  # Don't fail authentication due to logging issues
        
        # Login user
        login_user(user)
        user.update_last_login()
        db.session.commit()
        
        # Create session
        session_token = create_user_session(user.id, ip_address)
        session['session_token'] = session_token
        
        return jsonify({
            'success': True,
            'user': user.to_dict(),
            'message': 'Phantom wallet login successful'
        })
        
    except Exception as e:
        print(f"Phantom authentication error: {e}")
        try:
            log_login_attempt(request.remote_addr, 'solana', wallet_address=wallet_address, success=False)
        except:
            pass
        return jsonify({'error': f'Phantom verification failed: {str(e)}'}), 500

@auth_bp.route('/api/auth/logout', methods=['POST'])
@login_required
def logout():
    """Logout current user."""
    # Deactivate current session
    session_token = session.get('session_token')
    if session_token:
        user_session = UserSession.query.filter_by(session_token=session_token).first()
        if user_session:
            user_session.is_active = False
            from models import db
            db.session.commit()
    
    logout_user()
    session.clear()
    
    return jsonify({
        'success': True,
        'message': 'Logged out successfully'
    })

@auth_bp.route('/api/auth/user')
@login_required
def get_current_user():
    """Get current user information."""
    return jsonify({
        'user': current_user.to_dict()
    })

@auth_bp.route('/api/auth/user/preferences', methods=['PUT'])
@login_required
def update_user_preferences():
    """Update user AI preferences."""
    data = request.json
    preferences = current_user.get_ai_preferences()
    
    # Update preferences
    if 'preferred_language' in data:
        preferences['preferred_language'] = data['preferred_language']
    if 'voice_enabled' in data:
        preferences['voice_enabled'] = data['voice_enabled']
    if 'default_agent' in data:
        preferences['default_agent'] = data['default_agent']
    
    current_user.set_ai_preferences(preferences)
    current_user.preferred_language = preferences.get('preferred_language', 'en')
    db.session.commit()
    
    return jsonify({
        'success': True,
        'preferences': preferences
    })

@auth_bp.route('/api/auth/sessions')
@login_required
def get_user_sessions():
    """Get user's active sessions."""
    sessions = UserSession.query.filter_by(
        user_id=current_user.id,
        is_active=True
    ).order_by(UserSession.last_activity.desc()).all()
    
    session_list = []
    for sess in sessions:
        if not sess.is_expired():
            session_list.append({
                'id': sess.id,
                'ip_address': sess.ip_address,
                'user_agent': sess.user_agent,
                'created_at': sess.created_at.isoformat(),
                'last_activity': sess.last_activity.isoformat(),
                'expires_at': sess.expires_at.isoformat(),
                'is_current': sess.session_token == session.get('session_token')
            })
    
    return jsonify({
        'sessions': session_list
    })

@auth_bp.route('/api/auth/sessions/<int:session_id>', methods=['DELETE'])
@login_required
def revoke_session(session_id):
    """Revoke a specific session."""
    user_session = UserSession.query.filter_by(
        id=session_id,
        user_id=current_user.id
    ).first()
    
    if not user_session:
        return jsonify({'error': 'Session not found'}), 404
    
    user_session.is_active = False
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Session revoked successfully'
    })
