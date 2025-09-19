"""
Logging Infrastructure

Centralized logging setup for the AI Executive Suite with
structured logging, performance tracking, and monitoring integration.
"""

import logging
import logging.handlers
import os
import sys
import json
from datetime import datetime
from typing import Dict, Any, Optional
from functools import wraps
import time

from config.settings import config


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured JSON"""
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add extra fields if present
        if hasattr(record, 'user_id'):
            log_data['user_id'] = record.user_id
        if hasattr(record, 'request_id'):
            log_data['request_id'] = record.request_id
        if hasattr(record, 'execution_time'):
            log_data['execution_time'] = record.execution_time
        if hasattr(record, 'service'):
            log_data['service'] = record.service
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_data)


class PerformanceLogger:
    """Logger for performance metrics and monitoring"""
    
    def __init__(self):
        self.logger = logging.getLogger('performance')
        
    def log_request_time(self, endpoint: str, method: str, duration: float, status_code: int):
        """Log HTTP request performance"""
        self.logger.info(
            f"Request completed",
            extra={
                'endpoint': endpoint,
                'method': method,
                'duration': duration,
                'status_code': status_code,
                'metric_type': 'http_request'
            }
        )
    
    def log_ai_response_time(self, executive_type: str, duration: float, token_count: int):
        """Log AI response performance"""
        self.logger.info(
            f"AI response generated",
            extra={
                'executive_type': executive_type,
                'duration': duration,
                'token_count': token_count,
                'metric_type': 'ai_response'
            }
        )
    
    def log_database_query(self, query_type: str, duration: float, rows_affected: int):
        """Log database query performance"""
        self.logger.info(
            f"Database query executed",
            extra={
                'query_type': query_type,
                'duration': duration,
                'rows_affected': rows_affected,
                'metric_type': 'database_query'
            }
        )


def setup_logging() -> None:
    """Setup application logging configuration"""
    
    # Create logs directory if it doesn't exist
    log_dir = os.path.dirname(config.logging.file_path)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, config.logging.level.upper()))
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, config.logging.level.upper()))
    
    if config.debug:
        # Use simple format for development
        console_formatter = logging.Formatter(config.logging.format)
    else:
        # Use structured format for production
        console_formatter = StructuredFormatter()
    
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # File handler with rotation
    if config.logging.file_path:
        file_handler = logging.handlers.RotatingFileHandler(
            config.logging.file_path,
            maxBytes=config.logging.max_file_size,
            backupCount=config.logging.backup_count
        )
        file_handler.setLevel(getattr(logging, config.logging.level.upper()))
        file_handler.setFormatter(StructuredFormatter())
        root_logger.addHandler(file_handler)
    
    # Configure specific loggers
    
    # Suppress noisy third-party loggers
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('werkzeug').setLevel(logging.WARNING)
    
    # Set service loggers
    logging.getLogger('services').setLevel(logging.INFO)
    logging.getLogger('performance').setLevel(logging.INFO)
    logging.getLogger('security').setLevel(logging.INFO)
    
    logging.info("Logging system initialized")


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


def log_performance(func_name: Optional[str] = None):
    """
    Decorator to log function performance
    
    Args:
        func_name: Optional custom function name for logging
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            logger = get_logger(func.__module__)
            
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                
                logger.info(
                    f"Function executed successfully",
                    extra={
                        'function': func_name or func.__name__,
                        'execution_time': execution_time,
                        'metric_type': 'function_performance'
                    }
                )
                
                return result
                
            except Exception as e:
                execution_time = time.time() - start_time
                
                logger.error(
                    f"Function execution failed",
                    extra={
                        'function': func_name or func.__name__,
                        'execution_time': execution_time,
                        'error': str(e),
                        'metric_type': 'function_error'
                    },
                    exc_info=True
                )
                raise
                
        return wrapper
    return decorator


def log_user_action(action: str, user_id: str, details: Dict[str, Any] = None):
    """
    Log user actions for audit trail
    
    Args:
        action: Action performed
        user_id: ID of the user
        details: Additional action details
    """
    logger = get_logger('audit')
    logger.info(
        f"User action: {action}",
        extra={
            'user_id': user_id,
            'action': action,
            'details': details or {},
            'metric_type': 'user_action'
        }
    )


def log_security_event(event_type: str, details: Dict[str, Any], severity: str = 'INFO'):
    """
    Log security-related events
    
    Args:
        event_type: Type of security event
        details: Event details
        severity: Event severity (INFO, WARNING, ERROR, CRITICAL)
    """
    logger = get_logger('security')
    log_method = getattr(logger, severity.lower())
    
    log_method(
        f"Security event: {event_type}",
        extra={
            'event_type': event_type,
            'details': details,
            'severity': severity,
            'metric_type': 'security_event'
        }
    )


# Global performance logger instance
performance_logger = PerformanceLogger()