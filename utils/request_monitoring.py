"""
Request monitoring middleware for Flask application.
Tracks request metrics and integrates with monitoring service.
"""

import time
import logging
from functools import wraps
from flask import request, g
from services.monitoring import monitoring_service

logger = logging.getLogger(__name__)

class RequestMonitoringMiddleware:
    """Middleware to monitor Flask requests."""
    
    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize the middleware with Flask app."""
        app.before_request(self.before_request)
        app.after_request(self.after_request)
        app.teardown_appcontext(self.teardown_request)
        
        # Start monitoring service
        monitoring_service.start_monitoring()
        
        logger.info("Request monitoring middleware initialized")
    
    def before_request(self):
        """Called before each request."""
        g.start_time = time.time()
        g.request_start = time.time()
    
    def after_request(self, response):
        """Called after each request."""
        if hasattr(g, 'start_time'):
            response_time = time.time() - g.start_time
            is_error = response.status_code >= 400
            
            # Record request metrics
            monitoring_service.record_request(response_time, is_error)
            
            # Log slow requests
            if response_time > 2.0:
                logger.warning(
                    f"Slow request: {request.method} {request.path} "
                    f"took {response_time:.2f}s"
                )
        
        return response
    
    def teardown_request(self, exception):
        """Called when request context is torn down."""
        if exception:
            logger.error(f"Request exception: {str(exception)}")

def monitor_ai_api_call(func):
    """Decorator to monitor AI API calls."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            response_time = time.time() - start_time
            monitoring_service.record_ai_api_call(response_time)
            return result
        except Exception as e:
            response_time = time.time() - start_time
            monitoring_service.record_ai_api_call(response_time)
            logger.error(f"AI API call failed: {str(e)}")
            raise
    return wrapper

def monitor_db_query(func):
    """Decorator to monitor database queries."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            query_time = time.time() - start_time
            monitoring_service.record_db_query(query_time)
            return result
        except Exception as e:
            query_time = time.time() - start_time
            monitoring_service.record_db_query(query_time)
            logger.error(f"Database query failed: {str(e)}")
            raise
    return wrapper