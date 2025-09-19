#!/usr/bin/env python3
"""
AI Executive Suite - Main Application Entry Point

This is the main Flask application that brings together all the services
including document processing, vector database, and AI analysis.
"""

import os
from flask import Flask, render_template, jsonify
from flask_login import LoginManager

# Set development environment if not already set
if not os.getenv('FLASK_ENV'):
    os.environ['FLASK_ENV'] = 'development'
if not os.getenv('DEBUG'):
    os.environ['DEBUG'] = 'true'

def create_app():
    """Create and configure the Flask application"""
    app = Flask(__name__)
    
    # Basic configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['UPLOAD_FOLDER'] = os.getenv('UPLOAD_FOLDER', 'uploads')
    app.config['MAX_CONTENT_LENGTH'] = int(os.getenv('MAX_CONTENT_LENGTH', 50 * 1024 * 1024))  # 50MB
    
    # Database configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///instance/ai_executive_suite.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # MFA configuration
    app.config['MFA_ENCRYPTION_KEY'] = os.getenv('MFA_ENCRYPTION_KEY')
    app.config['APP_NAME'] = os.getenv('APP_NAME', 'AI Executive Suite')
    
    # Email configuration for MFA
    app.config['SMTP_SERVER'] = os.getenv('SMTP_SERVER')
    app.config['SMTP_PORT'] = int(os.getenv('SMTP_PORT', 587))
    app.config['SMTP_USERNAME'] = os.getenv('SMTP_USERNAME')
    app.config['SMTP_PASSWORD'] = os.getenv('SMTP_PASSWORD')
    app.config['FROM_EMAIL'] = os.getenv('FROM_EMAIL')
    
    # SMS configuration for MFA (Twilio)
    app.config['TWILIO_ACCOUNT_SID'] = os.getenv('TWILIO_ACCOUNT_SID')
    app.config['TWILIO_AUTH_TOKEN'] = os.getenv('TWILIO_AUTH_TOKEN')
    app.config['TWILIO_PHONE_NUMBER'] = os.getenv('TWILIO_PHONE_NUMBER')
    
    # Ensure upload directory exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Initialize database
    from models import db
    db.init_app(app)
    
    # Initialize extensions
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login_page'
    
    # Initialize monitoring middleware
    try:
        from utils.request_monitoring import RequestMonitoringMiddleware
        monitoring_middleware = RequestMonitoringMiddleware(app)
        print("✓ Request monitoring middleware initialized")
    except Exception as e:
        print(f"Warning: Could not initialize monitoring middleware: {e}")
    
    @login_manager.user_loader
    def load_user(user_id):
        from models import User
        return User.query.get(int(user_id)) if user_id else None
    
    # Register blueprints
    try:
        from auth import auth_bp
        app.register_blueprint(auth_bp)
        print("✓ Authentication routes registered")
    except Exception as e:
        print(f"Warning: Could not register auth routes: {e}")
    
    try:
        from routes.mfa_routes import mfa_bp
        app.register_blueprint(mfa_bp)
        print("✓ MFA routes registered")
    except Exception as e:
        print(f"Warning: Could not register MFA routes: {e}")
    
    try:
        from routes.document_routes import document_bp
        app.register_blueprint(document_bp)
        print("✓ Document routes registered")
    except Exception as e:
        print(f"Warning: Could not register document routes: {e}")
    
    try:
        from routes.executive_routes import executive_bp
        app.register_blueprint(executive_bp)
        print("✓ Executive routes registered")
    except Exception as e:
        print(f"Warning: Could not register executive routes: {e}")
    
    try:
        from routes.analytics_routes import analytics_bp
        app.register_blueprint(analytics_bp)
        print("✓ Analytics routes registered")
    except Exception as e:
        print(f"Warning: Could not register analytics routes: {e}")
    
    try:
        from routes.collaboration_routes import collaboration_bp
        app.register_blueprint(collaboration_bp)
        print("✓ Collaboration routes registered")
    except Exception as e:
        print(f"Warning: Could not register collaboration routes: {e}")
    
    try:
        from routes.data_protection_routes import data_protection_bp
        app.register_blueprint(data_protection_bp)
        print("✓ Data protection routes registered")
    except Exception as e:
        print(f"Warning: Could not register data protection routes: {e}")
    
    try:
        from routes.compliance_routes import compliance_bp
        app.register_blueprint(compliance_bp)
        print("✓ Compliance routes registered")
    except Exception as e:
        print(f"Warning: Could not register compliance routes: {e}")
    
    try:
        from routes.personality_routes import personality_bp
        app.register_blueprint(personality_bp)
        print("✓ Personality routes registered")
    except Exception as e:
        print(f"Warning: Could not register personality routes: {e}")
    
    try:
        from routes.expertise_routes import expertise_bp
        app.register_blueprint(expertise_bp)
        print("✓ Expertise routes registered")
    except Exception as e:
        print(f"Warning: Could not register expertise routes: {e}")
    
    try:
        from routes.profile_sharing_routes import profile_sharing_bp
        app.register_blueprint(profile_sharing_bp)
        print("✓ Profile sharing routes registered")
    except Exception as e:
        print(f"Warning: Could not register profile sharing routes: {e}")
    
    try:
        from routes.monitoring_routes import monitoring_bp
        app.register_blueprint(monitoring_bp)
        print("✓ Monitoring routes registered")
    except Exception as e:
        print(f"Warning: Could not register monitoring routes: {e}")
    
    try:
        from routes.ai_quality_routes import ai_quality_bp
        app.register_blueprint(ai_quality_bp)
        print("✓ AI quality routes registered")
    except Exception as e:
        print(f"Warning: Could not register AI quality routes: {e}")
    
    try:
        from routes.usage_analytics_routes import usage_analytics_bp
        app.register_blueprint(usage_analytics_bp)
        print("✓ Usage analytics routes registered")
    except Exception as e:
        print(f"Warning: Could not register usage analytics routes: {e}")
    
    try:
        from routes.metrics_routes import metrics_bp
        app.register_blueprint(metrics_bp)
        print("✓ Metrics routes registered")
    except Exception as e:
        print(f"Warning: Could not register metrics routes: {e}")
    
    # Basic routes
    @app.route('/')
    def index():
        """Main dashboard"""
        return render_template('index.html') if os.path.exists('templates/index.html') else jsonify({
            'message': 'AI Executive Suite API',
            'version': '1.0.0',
            'status': 'running',
            'services': {
                'document_processing': 'available',
                'vector_database': 'available',
                'document_analysis': 'available'
            }
        })
    
    @app.route('/upload')
    def upload_page():
        """Document upload page"""
        return render_template('upload_document.html')
    
    @app.route('/mobile-notifications')
    def mobile_notifications():
        """Mobile notification settings page"""
        return render_template('mobile_notifications.html')
    
    @app.route('/personality-config')
    def personality_config():
        """Personality configuration page"""
        return render_template('personality_config.html')
    
    @app.route('/health')
    def health_check():
        """Health check endpoint for production monitoring"""
        from datetime import datetime
        
        try:
            # Check database connectivity
            db.session.execute('SELECT 1')
            db_status = "connected"
        except Exception as e:
            db_status = f"error: {str(e)}"
        
        # Check Redis connectivity if configured
        redis_status = "ok"
        try:
            from services.registry import ServiceRegistry
            registry = ServiceRegistry()
            if hasattr(registry, 'redis_client'):
                registry.redis_client.ping()
        except:
            redis_status = "unavailable"
        
        # Determine overall health
        is_healthy = db_status == "connected"
        status_code = 200 if is_healthy else 503
        
        return jsonify({
            'status': 'healthy' if is_healthy else 'unhealthy',
            'timestamp': datetime.utcnow().isoformat(),
            'database': db_status,
            'redis': redis_status,
            'instance_id': os.getenv('INSTANCE_ID', 'unknown'),
            'services': {
                'document_processing': 'operational',
                'vector_database': 'operational',
                'document_analysis': 'operational'
            }
        }), status_code
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Not found'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({'error': 'Internal server error'}), 500
    
    return app

if __name__ == '__main__':
    app = create_app()
    
    print("🚀 Starting AI Executive Suite...")
    print("📄 Document Processing System: Ready")
    print("🔍 Vector Database: Ready") 
    print("🧠 Document Analysis: Ready")
    print("🌐 Web Interface: http://localhost:5000")
    print("📤 Upload Interface: http://localhost:5000/upload")
    print("🏥 Health Check: http://localhost:5000/health")
    print()
    
    # Run the application
    app.run(
        host=os.getenv('HOST', '0.0.0.0'),
        port=int(os.getenv('PORT', 5000)),
        debug=os.getenv('DEBUG', 'true').lower() == 'true'
    )