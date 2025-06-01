# Logging Configuration

## Overview
This document provides comprehensive guidance on configuring and implementing structured logging for applications. Proper logging is essential for debugging, monitoring, and maintaining applications in production.

## Logging Fundamentals

### Log Levels
- **DEBUG**: Detailed diagnostic information (development only)
- **INFO**: General application flow information
- **WARNING**: Something unexpected happened, but application continues
- **ERROR**: Application error occurred, functionality affected
- **CRITICAL**: Serious error occurred, application may stop

### Structured Logging Principles
- Use consistent log formats
- Include contextual information
- Make logs searchable and filterable
- Avoid logging sensitive information
- Use appropriate log levels

## Python Logging Configuration

### Basic Logging Setup
```python
import logging
import sys
from datetime import datetime
from pythonjsonlogger import jsonlogger

def setup_logging(
    level: str = "INFO",
    format_type: str = "json",
    log_file: str = None
) -> logging.Logger:
    """Configure application logging"""
    
    # Create logger
    logger = logging.getLogger("app")
    logger.setLevel(getattr(logging, level.upper()))
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Create formatters
    if format_type == "json":
        formatter = jsonlogger.JsonFormatter(
            '%(asctime)s %(name)s %(levelname)s %(message)s',
            rename_fields={
                'asctime': 'timestamp',
                'name': 'logger',
                'levelname': 'level'
            }
        )
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (optional)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

# Initialize logger
logger = setup_logging(level="INFO", format_type="json")
```

### Advanced Configuration with YAML
```yaml
# logging_config.yaml
version: 1
disable_existing_loggers: false

formatters:
  standard:
    format: '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
  
  json:
    class: pythonjsonlogger.jsonlogger.JsonFormatter
    format: '%(asctime)s %(name)s %(levelname)s %(message)s'
  
  detailed:
    format: '%(asctime)s - %(name)s - %(levelname)s - %(module)s - %(funcName)s - %(lineno)d - %(message)s'

handlers:
  console:
    class: logging.StreamHandler
    level: INFO
    formatter: json
    stream: ext://sys.stdout
  
  file:
    class: logging.handlers.RotatingFileHandler
    level: DEBUG
    formatter: detailed
    filename: app.log
    maxBytes: 10485760  # 10MB
    backupCount: 5
  
  error_file:
    class: logging.FileHandler
    level: ERROR
    formatter: json
    filename: error.log

loggers:
  app:
    level: DEBUG
    handlers: [console, file, error_file]
    propagate: false
  
  sqlalchemy.engine:
    level: WARNING
    handlers: [console]
    propagate: false

root:
  level: WARNING
  handlers: [console]
```

```python
import yaml
import logging.config

def load_logging_config(config_path: str = "logging_config.yaml"):
    """Load logging configuration from YAML file"""
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    logging.config.dictConfig(config)
    return logging.getLogger("app")

# Usage
logger = load_logging_config()
```

## Contextual Logging

### Context Managers for Request Tracing
```python
import uuid
import threading
from contextlib import contextmanager
from typing import Dict, Any, Optional

class LogContext:
    """Thread-local storage for logging context"""
    
    def __init__(self):
        self._storage = threading.local()
    
    def set_context(self, **kwargs):
        """Set logging context for current thread"""
        if not hasattr(self._storage, 'context'):
            self._storage.context = {}
        self._storage.context.update(kwargs)
    
    def get_context(self) -> Dict[str, Any]:
        """Get current logging context"""
        return getattr(self._storage, 'context', {})
    
    def clear_context(self):
        """Clear logging context"""
        if hasattr(self._storage, 'context'):
            self._storage.context.clear()

# Global context instance
log_context = LogContext()

class ContextualLogger:
    """Logger that automatically includes context"""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
    
    def _log_with_context(self, level: int, message: str, **kwargs):
        """Add context to log message"""
        context = log_context.get_context()
        extra = {
            'context': context,
            **kwargs
        }
        self.logger.log(level, message, extra=extra)
    
    def debug(self, message: str, **kwargs):
        self._log_with_context(logging.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs):
        self._log_with_context(logging.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        self._log_with_context(logging.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs):
        self._log_with_context(logging.ERROR, message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        self._log_with_context(logging.CRITICAL, message, **kwargs)

@contextmanager
def request_context(request_id: str = None, user_id: str = None, **kwargs):
    """Context manager for request-scoped logging"""
    if request_id is None:
        request_id = str(uuid.uuid4())
    
    log_context.set_context(
        request_id=request_id,
        user_id=user_id,
        **kwargs
    )
    
    try:
        yield request_id
    finally:
        log_context.clear_context()

# Usage
logger = ContextualLogger(__name__)

def handle_user_request(user_id: str, action: str):
    with request_context(user_id=user_id, action=action) as request_id:
        logger.info(f"Processing {action} for user")
        
        try:
            # Business logic here
            result = process_action(action)
            logger.info("Action completed successfully", result=result)
            return result
        except Exception as e:
            logger.error(f"Action failed: {e}", error_type=type(e).__name__)
            raise
```

### Decorators for Automatic Logging
```python
import time
from functools import wraps
from typing import Callable, Any

def log_function_calls(
    log_entry: bool = True,
    log_exit: bool = True,
    log_duration: bool = True,
    log_args: bool = False,
    log_result: bool = False,
    exclude_args: list = None
):
    """Decorator to automatically log function calls"""
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            logger = ContextualLogger(func.__module__)
            func_name = f"{func.__module__}.{func.__name__}"
            
            # Prepare log data
            log_data = {"function": func_name}
            
            if log_args:
                # Filter out excluded arguments
                filtered_args = args
                filtered_kwargs = kwargs
                
                if exclude_args:
                    filtered_kwargs = {
                        k: v for k, v in kwargs.items() 
                        if k not in exclude_args
                    }
                
                log_data.update({
                    "args": filtered_args,
                    "kwargs": filtered_kwargs
                })
            
            # Log function entry
            if log_entry:
                logger.debug("Function called", **log_data)
            
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                
                # Log successful exit
                if log_exit:
                    exit_data = log_data.copy()
                    if log_duration:
                        exit_data["duration"] = time.time() - start_time
                    if log_result:
                        exit_data["result"] = result
                    
                    logger.debug("Function completed", **exit_data)
                
                return result
                
            except Exception as e:
                # Log error exit
                error_data = log_data.copy()
                error_data.update({
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "duration": time.time() - start_time
                })
                
                logger.error("Function failed", **error_data)
                raise
        
        return wrapper
    return decorator

# Usage examples
@log_function_calls(log_args=True, log_result=True, exclude_args=['password'])
def authenticate_user(username: str, password: str) -> dict:
    # Authentication logic
    return {"user_id": 123, "username": username}

@log_function_calls(log_duration=True)
def expensive_operation(data: list) -> int:
    # Expensive computation
    time.sleep(1)
    return len(data)
```

## Application-Specific Logging

### Database Query Logging
```python
from sqlalchemy import event
from sqlalchemy.engine import Engine
import time

class DatabaseLogger:
    """Logger for database operations"""
    
    def __init__(self):
        self.logger = ContextualLogger("database")
        self.slow_query_threshold = 1.0  # seconds
    
    def setup_query_logging(self):
        """Setup SQLAlchemy event listeners for query logging"""
        
        @event.listens_for(Engine, "before_cursor_execute")
        def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            context._query_start_time = time.time()
            context._query_statement = statement
            context._query_parameters = parameters
        
        @event.listens_for(Engine, "after_cursor_execute")
        def receive_after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            total_time = time.time() - context._query_start_time
            
            log_data = {
                "query_time": total_time,
                "query": statement[:200] + "..." if len(statement) > 200 else statement,
                "parameter_count": len(parameters) if parameters else 0
            }
            
            if total_time > self.slow_query_threshold:
                self.logger.warning("Slow database query detected", **log_data)
            else:
                self.logger.debug("Database query executed", **log_data)

# Initialize database logging
db_logger = DatabaseLogger()
db_logger.setup_query_logging()
```

### API Request/Response Logging
```python
from flask import Flask, request, g
import time
import json

class APILogger:
    """Logger for API requests and responses"""
    
    def __init__(self, app: Flask = None):
        self.logger = ContextualLogger("api")
        if app:
            self.init_app(app)
    
    def init_app(self, app: Flask):
        """Initialize API logging for Flask app"""
        app.before_request(self._before_request)
        app.after_request(self._after_request)
        app.teardown_appcontext(self._teardown_request)
    
    def _before_request(self):
        """Log request start"""
        g.start_time = time.time()
        g.request_id = str(uuid.uuid4())
        
        # Set request context
        log_context.set_context(
            request_id=g.request_id,
            method=request.method,
            path=request.path,
            user_agent=request.headers.get('User-Agent'),
            ip_address=request.remote_addr
        )
        
        # Log request details
        request_data = {
            "method": request.method,
            "path": request.path,
            "args": dict(request.args),
            "content_length": request.content_length
        }
        
        # Log request body for POST/PUT/PATCH (be careful with sensitive data)
        if request.method in ['POST', 'PUT', 'PATCH'] and request.is_json:
            try:
                request_data["body"] = request.get_json()
            except:
                request_data["body"] = "Unable to parse JSON"
        
        self.logger.info("API request started", **request_data)
    
    def _after_request(self, response):
        """Log request completion"""
        duration = time.time() - g.start_time
        
        response_data = {
            "status_code": response.status_code,
            "duration": duration,
            "content_length": response.content_length
        }
        
        # Determine log level based on status code
        if response.status_code >= 500:
            self.logger.error("API request completed with server error", **response_data)
        elif response.status_code >= 400:
            self.logger.warning("API request completed with client error", **response_data)
        else:
            self.logger.info("API request completed successfully", **response_data)
        
        return response
    
    def _teardown_request(self, exception):
        """Log unhandled exceptions"""
        if exception:
            self.logger.error(
                "Unhandled exception in request",
                exception=str(exception),
                exception_type=type(exception).__name__
            )

# Usage with Flask
app = Flask(__name__)
api_logger = APILogger(app)
```

### Security Event Logging
```python
class SecurityLogger:
    """Specialized logger for security events"""
    
    def __init__(self):
        self.logger = ContextualLogger("security")
    
    def log_authentication_attempt(self, username: str, success: bool, 
                                 ip_address: str, user_agent: str = None):
        """Log authentication attempts"""
        event_data = {
            "event_type": "authentication_attempt",
            "username": username,
            "success": success,
            "ip_address": ip_address,
            "user_agent": user_agent
        }
        
        if success:
            self.logger.info("User authentication successful", **event_data)
        else:
            self.logger.warning("User authentication failed", **event_data)
    
    def log_authorization_failure(self, user_id: str, resource: str, 
                                action: str, ip_address: str):
        """Log authorization failures"""
        event_data = {
            "event_type": "authorization_failure",
            "user_id": user_id,
            "resource": resource,
            "action": action,
            "ip_address": ip_address
        }
        
        self.logger.warning("Authorization denied", **event_data)
    
    def log_suspicious_activity(self, activity_type: str, details: dict, 
                              severity: str = "medium"):
        """Log suspicious security activity"""
        event_data = {
            "event_type": "suspicious_activity",
            "activity_type": activity_type,
            "severity": severity,
            "details": details
        }
        
        if severity == "high":
            self.logger.critical("High severity suspicious activity detected", **event_data)
        else:
            self.logger.warning("Suspicious activity detected", **event_data)
    
    def log_data_access(self, user_id: str, resource_type: str, 
                       resource_id: str, action: str):
        """Log access to sensitive data"""
        event_data = {
            "event_type": "data_access",
            "user_id": user_id,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "action": action
        }
        
        self.logger.info("Sensitive data accessed", **event_data)

# Global security logger
security_logger = SecurityLogger()
```

## Performance and Monitoring Logging

### Performance Metrics Logging
```python
import psutil
import gc
from typing import Dict

class PerformanceLogger:
    """Logger for performance metrics"""
    
    def __init__(self):
        self.logger = ContextualLogger("performance")
    
    def log_system_metrics(self):
        """Log current system performance metrics"""
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        metrics = {
            "metric_type": "system_performance",
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "memory_available": memory.available,
            "disk_percent": disk.percent,
            "disk_free": disk.free
        }
        
        self.logger.info("System performance metrics", **metrics)
    
    def log_memory_usage(self, operation: str = None):
        """Log current memory usage"""
        process = psutil.Process()
        memory_info = process.memory_info()
        
        metrics = {
            "metric_type": "memory_usage",
            "operation": operation,
            "rss": memory_info.rss,
            "vms": memory_info.vms,
            "gc_count": len(gc.get_objects())
        }
        
        self.logger.debug("Memory usage", **metrics)
    
    def log_request_metrics(self, endpoint: str, method: str, 
                          duration: float, status_code: int):
        """Log HTTP request performance metrics"""
        metrics = {
            "metric_type": "request_performance",
            "endpoint": endpoint,
            "method": method,
            "duration": duration,
            "status_code": status_code
        }
        
        # Log slow requests as warnings
        if duration > 2.0:  # 2 seconds threshold
            self.logger.warning("Slow request detected", **metrics)
        else:
            self.logger.info("Request performance", **metrics)

# Performance monitoring decorator
def monitor_performance(operation_name: str = None):
    """Decorator to monitor function performance"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            perf_logger = PerformanceLogger()
            op_name = operation_name or f"{func.__module__}.{func.__name__}"
            
            # Log memory before
            perf_logger.log_memory_usage(f"{op_name}_start")
            
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                # Log performance metrics
                perf_logger.logger.info(
                    "Operation completed",
                    operation=op_name,
                    duration=duration,
                    success=True
                )
                
                return result
            except Exception as e:
                duration = time.time() - start_time
                perf_logger.logger.error(
                    "Operation failed",
                    operation=op_name,
                    duration=duration,
                    success=False,
                    error=str(e)
                )
                raise
            finally:
                # Log memory after
                perf_logger.log_memory_usage(f"{op_name}_end")
        
        return wrapper
    return decorator

# Usage
@monitor_performance("data_processing")
def process_large_dataset(data):
    # Processing logic
    time.sleep(2)
    return len(data)
```

## Log Aggregation and Analysis

### Structured Logging for ELK Stack
```python
class ELKLogger:
    """Logger optimized for ELK Stack (Elasticsearch, Logstash, Kibana)"""
    
    def __init__(self, service_name: str, environment: str):
        self.service_name = service_name
        self.environment = environment
        self.logger = self._setup_logger()
    
    def _setup_logger(self):
        """Setup logger with ELK-optimized format"""
        logger = logging.getLogger(f"{self.service_name}.elk")
        
        # Custom formatter for ELK
        formatter = jsonlogger.JsonFormatter(
            '%(asctime)s %(name)s %(levelname)s %(message)s',
            rename_fields={
                'asctime': '@timestamp',
                'name': 'logger_name',
                'levelname': 'level'
            }
        )
        
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        
        return logger
    
    def log_event(self, event_type: str, message: str, **fields):
        """Log structured event for ELK analysis"""
        log_data = {
            'service': self.service_name,
            'environment': self.environment,
            'event_type': event_type,
            'message': message,
            **fields
        }
        
        # Add correlation ID if available
        context = log_context.get_context()
        if 'request_id' in context:
            log_data['correlation_id'] = context['request_id']
        
        self.logger.info("", extra=log_data)
    
    def log_metric(self, metric_name: str, value: float, unit: str = None, **tags):
        """Log metrics for monitoring dashboards"""
        metric_data = {
            'metric_name': metric_name,
            'metric_value': value,
            'metric_unit': unit,
            'metric_tags': tags,
            'service': self.service_name,
            'environment': self.environment
        }
        
        self.logger.info("metric", extra=metric_data)
    
    def log_business_event(self, event: str, entity_type: str, 
                          entity_id: str, **properties):
        """Log business events for analytics"""
        business_data = {
            'business_event': event,
            'entity_type': entity_type,
            'entity_id': entity_id,
            'properties': properties,
            'service': self.service_name,
            'environment': self.environment
        }
        
        self.logger.info("business_event", extra=business_data)

# Usage
elk_logger = ELKLogger("user-service", "production")

# Log various event types
elk_logger.log_event("user_registration", "New user registered", 
                    user_id="12345", email="user@example.com")

elk_logger.log_metric("response_time", 0.234, "seconds", 
                     endpoint="/api/users", method="GET")

elk_logger.log_business_event("purchase_completed", "order", "order-123",
                             amount=99.99, currency="USD", items_count=3)
```

## Testing and Validation

### Log Testing Utilities
```python
import logging
from unittest.mock import Mock
from contextlib import contextmanager

class LogCapture:
    """Utility for capturing and testing log messages"""
    
    def __init__(self, logger_name: str, level: int = logging.INFO):
        self.logger_name = logger_name
        self.level = level
        self.records = []
    
    def __enter__(self):
        # Create mock handler
        self.handler = Mock()
        self.handler.handle = self._handle_record
        
        # Add to logger
        logger = logging.getLogger(self.logger_name)
        logger.addHandler(self.handler)
        logger.setLevel(self.level)
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Remove handler
        logger = logging.getLogger(self.logger_name)
        logger.removeHandler(self.handler)
    
    def _handle_record(self, record):
        """Handle log record"""
        self.records.append(record)
    
    def assert_log_count(self, count: int):
        """Assert number of log records"""
        assert len(self.records) == count, f"Expected {count} logs, got {len(self.records)}"
    
    def assert_log_message(self, message: str, level: int = None):
        """Assert log message exists"""
        for record in self.records:
            if message in record.getMessage():
                if level is None or record.levelno == level:
                    return
        
        raise AssertionError(f"Log message '{message}' not found")
    
    def get_log_data(self, index: int = -1) -> dict:
        """Get log data from record"""
        record = self.records[index]
        return getattr(record, '__dict__', {})

# Test example
def test_user_creation_logging():
    """Test that user creation is properly logged"""
    
    with LogCapture("app.user_service") as log_capture:
        # Execute function that should log
        create_user({"email": "test@example.com", "name": "Test User"})
        
        # Verify logging
        log_capture.assert_log_count(2)  # Start and completion logs
        log_capture.assert_log_message("User creation started")
        log_capture.assert_log_message("User created successfully")
        
        # Check log data
        completion_log = log_capture.get_log_data(-1)
        assert completion_log.get('user_email') == "test@example.com"
```

## Configuration Best Practices

### Environment-Specific Configuration
```python
import os
from enum import Enum

class LogLevel(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class LoggingConfig:
    """Centralized logging configuration"""
    
    def __init__(self):
        self.environment = os.getenv("ENVIRONMENT", "development")
        self.service_name = os.getenv("SERVICE_NAME", "app")
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        self.log_format = os.getenv("LOG_FORMAT", "json")
        self.enable_file_logging = os.getenv("ENABLE_FILE_LOGGING", "false").lower() == "true"
        self.log_file_path = os.getenv("LOG_FILE_PATH", "app.log")
        self.enable_performance_logging = os.getenv("ENABLE_PERFORMANCE_LOGGING", "false").lower() == "true"
        self.enable_security_logging = os.getenv("ENABLE_SECURITY_LOGGING", "true").lower() == "true"
    
    def get_config(self) -> dict:
        """Get complete logging configuration"""
        return {
            "environment": self.environment,
            "service_name": self.service_name,
            "log_level": self.log_level,
            "log_format": self.log_format,
            "enable_file_logging": self.enable_file_logging,
            "log_file_path": self.log_file_path,
            "enable_performance_logging": self.enable_performance_logging,
            "enable_security_logging": self.enable_security_logging
        }
    
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.environment.lower() == "production"
    
    def should_log_sensitive_data(self) -> bool:
        """Determine if sensitive data should be logged (development only)"""
        return not self.is_production()

# Initialize configuration
logging_config = LoggingConfig()

# Setup loggers based on configuration
def initialize_application_logging():
    """Initialize all application loggers"""
    config = logging_config.get_config()
    
    # Main application logger
    setup_logging(
        level=config["log_level"],
        format_type=config["log_format"],
        log_file=config["log_file_path"] if config["enable_file_logging"] else None
    )
    
    # Performance logger (if enabled)
    if config["enable_performance_logging"]:
        perf_logger = PerformanceLogger()
        # Setup periodic system metrics logging
    
    # Security logger (if enabled)
    if config["enable_security_logging"]:
        security_logger = SecurityLogger()
    
    # Database query logging (development only)
    if not logging_config.is_production():
        db_logger = DatabaseLogger()
        db_logger.setup_query_logging()

# Call during application startup
initialize_application_logging()
```

## Monitoring and Alerting Integration

### Log-Based Alerting
```python
class AlertManager:
    """Manage alerts based on log patterns"""
    
    def __init__(self):
        self.logger = ContextualLogger("alerts")
        self.alert_thresholds = {
            "error_rate": 0.05,  # 5% error rate
            "slow_requests": 10,  # 10 slow requests per minute
            "failed_logins": 20   # 20 failed logins per minute
        }
    
    def check_error_rate(self, error_count: int, total_count: int):
        """Check if error rate exceeds threshold"""
        if total_count > 0:
            error_rate = error_count / total_count
            if error_rate > self.alert_thresholds["error_rate"]:
                self.send_alert(
                    "high_error_rate",
                    f"Error rate {error_rate:.2%} exceeds threshold",
                    severity="high",
                    error_rate=error_rate,
                    error_count=error_count,
                    total_count=total_count
                )
    
    def send_alert(self, alert_type: str, message: str, 
                  severity: str = "medium", **metadata):
        """Send alert to monitoring system"""
        alert_data = {
            "alert_type": alert_type,
            "message": message,
            "severity": severity,
            "timestamp": datetime.utcnow().isoformat(),
            "service": logging_config.service_name,
            "environment": logging_config.environment,
            **metadata
        }
        
        # Log alert (will be picked up by monitoring system)
        self.logger.critical("ALERT", **alert_data)
        
        # Send to external alerting system (Slack, PagerDuty, etc.)
        self._send_external_alert(alert_data)
    
    def _send_external_alert(self, alert_data: dict):
        """Send alert to external system"""
        # Implementation depends on your alerting system
        # e.g., Slack webhook, PagerDuty API, etc.
        pass

alert_manager = AlertManager()
```

Remember: Effective logging is about finding the right balance between too little information (making debugging difficult) and too much information (creating noise and performance issues). Always consider the operational impact of your logging strategy.
