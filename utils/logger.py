import logging
import logging.handlers
import os
import sys
from datetime import datetime
from flask import request, g
import json


class RequestIdFilter(logging.Filter):
    """Add request ID to log records for tracing."""
    def filter(self, record):
        try:
            record.request_id = getattr(g, 'request_id', 'N/A')
        except RuntimeError:
            # Outside of request context
            record.request_id = 'N/A'
        return True


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""
    def format(self, record):
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'request_id': getattr(record, 'request_id', 'N/A'),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        # Add extra fields if present
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 
                          'filename', 'module', 'exc_info', 'exc_text', 'stack_info', 
                          'lineno', 'funcName', 'created', 'msecs', 'relativeCreated', 
                          'thread', 'threadName', 'processName', 'process', 'message', 
                          'asctime', 'request_id']:
                log_data[key] = value
        
        return json.dumps(log_data)


def setup_logging(app):
    """Setup comprehensive logging for the application."""
    
    # Create logs directory if it doesn't exist
    log_dir = os.path.join(os.path.dirname(__file__), '..', 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Remove existing handlers
    root_logger.handlers.clear()
    
    # Console handler with colored output
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        '[%(asctime)s] [%(levelname)s] [%(request_id)s] %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    console_handler.addFilter(RequestIdFilter())
    root_logger.addHandler(console_handler)
    
    # File handler for general logs
    general_log = os.path.join(log_dir, 'general.log')
    file_handler = logging.handlers.RotatingFileHandler(
        general_log,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.INFO)
    file_formatter = logging.Formatter(
        '[%(asctime)s] [%(levelname)s] [%(request_id)s] %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    file_handler.addFilter(RequestIdFilter())
    root_logger.addHandler(file_handler)
    
    # File handler for error logs
    error_log = os.path.join(log_dir, 'error.log')
    error_handler = logging.handlers.RotatingFileHandler(
        error_log,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(file_formatter)
    error_handler.addFilter(RequestIdFilter())
    root_logger.addHandler(error_handler)
    
    # JSON file handler for structured logging (useful for log aggregation)
    json_log = os.path.join(log_dir, 'structured.log')
    json_handler = logging.handlers.RotatingFileHandler(
        json_log,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    json_handler.setLevel(logging.INFO)
    json_handler.setFormatter(JSONFormatter())
    json_handler.addFilter(RequestIdFilter())
    root_logger.addHandler(json_handler)
    
    # Set specific log levels for different loggers
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
    logging.getLogger('sqlalchemy.pool').setLevel(logging.WARNING)
    logging.getLogger('werkzeug').setLevel(logging.INFO)
    
    # Add request logging middleware
    @app.before_request
    def log_request_info():
        import uuid
        g.request_id = str(uuid.uuid4())[:8]
        g.start_time = datetime.utcnow()
        
        # Log request details
        app.logger.info(
            'Request started',
            extra={
                'method': request.method,
                'path': request.path,
                'remote_addr': request.remote_addr,
                'user_agent': request.headers.get('User-Agent'),
                'content_type': request.content_type
            }
        )
    
    @app.after_request
    def log_response_info(response):
        if hasattr(g, 'start_time'):
            duration = (datetime.utcnow() - g.start_time).total_seconds() * 1000

            # Safely get response size, handle direct passthrough mode
            response_size = 0
            try:
                response_size = len(response.get_data())
            except (RuntimeError, TypeError):
                # Response is in direct passthrough mode or cannot be measured
                response_size = 0

            app.logger.info(
                'Request completed',
                extra={
                    'method': request.method,
                    'path': request.path,
                    'status_code': response.status_code,
                    'duration_ms': round(duration, 2),
                    'response_size': response_size
                }
            )

        # Add request ID to response headers
        response.headers['X-Request-ID'] = getattr(g, 'request_id', 'N/A')
        return response
    
    @app.errorhandler(Exception)
    def log_exception(error):
        app.logger.error(
            'Unhandled exception',
            exc_info=True,
            extra={
                'method': request.method if request else 'N/A',
                'path': request.path if request else 'N/A',
                'error_type': type(error).__name__
            }
        )
        return error
    
    app.logger.info('Logging system initialized successfully')


def get_logger(name):
    """Get a logger instance with the given name."""
    return logging.getLogger(name)


# Performance monitoring decorator
def monitor_performance(logger_name='app.performance'):
    """Decorator to monitor function performance."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            logger = logging.getLogger(logger_name)
            start_time = datetime.utcnow()
            
            try:
                result = func(*args, **kwargs)
                duration = (datetime.utcnow() - start_time).total_seconds() * 1000
                
                logger.info(
                    f'{func.__name__} completed successfully',
                    extra={
                        'function': func.__name__,
                        'duration_ms': round(duration, 2),
                        'status': 'success'
                    }
                )
                
                return result
            except Exception as e:
                duration = (datetime.utcnow() - start_time).total_seconds() * 1000
                
                logger.error(
                    f'{func.__name__} failed',
                    exc_info=True,
                    extra={
                        'function': func.__name__,
                        'duration_ms': round(duration, 2),
                        'status': 'error',
                        'error_type': type(e).__name__
                    }
                )
                
                raise
        
        return wrapper
    return decorator


# Database query monitoring
def log_db_query(query, params=None, duration_ms=None):
    """Log database query performance."""
    logger = logging.getLogger('app.database')
    
    logger.debug(
        'Database query executed',
        extra={
            'query': query[:500],  # Truncate long queries
            'params': str(params)[:200] if params else None,
            'duration_ms': duration_ms,
            'query_length': len(query)
        }
    )


# Security event logging
def log_security_event(event_type, details=None, severity='info'):
    """Log security-related events."""
    logger = logging.getLogger('app.security')
    
    log_func = {
        'info': logger.info,
        'warning': logger.warning,
        'error': logger.error,
        'critical': logger.critical
    }.get(severity, logger.info)
    
    log_func(
        f'Security event: {event_type}',
        extra={
            'event_type': event_type,
            'details': details,
            'severity': severity,
            'ip_address': request.remote_addr if request else 'N/A',
            'user_agent': request.headers.get('User-Agent') if request else 'N/A'
        }
    )