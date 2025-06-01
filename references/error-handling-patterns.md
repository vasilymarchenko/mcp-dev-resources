# Error Handling Patterns

## Overview
This document provides comprehensive patterns and strategies for implementing robust error handling in applications. Proper error handling improves reliability, debugging, and user experience.

## Error Handling Principles

### 1. Fail Fast
Detect and report errors as early as possible to prevent cascading failures.

```python
def process_user_data(user_data):
    # Validate inputs immediately
    if not user_data:
        raise ValueError("User data cannot be None or empty")
    
    if not isinstance(user_data, dict):
        raise TypeError(f"Expected dict, got {type(user_data)}")
    
    required_fields = ['email', 'name']
    missing_fields = [field for field in required_fields if field not in user_data]
    if missing_fields:
        raise ValueError(f"Missing required fields: {missing_fields}")
    
    # Continue processing...
```

### 2. Error Recovery
When possible, implement recovery mechanisms instead of failing completely.

```python
import time
from typing import Optional, Callable, Any

def retry_with_backoff(
    func: Callable,
    max_retries: int = 3,
    base_delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: tuple = (Exception,)
) -> Any:
    """Retry function with exponential backoff"""
    
    for attempt in range(max_retries + 1):
        try:
            return func()
        except exceptions as e:
            if attempt == max_retries:
                raise e
            
            delay = base_delay * (backoff_factor ** attempt)
            logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay}s...")
            time.sleep(delay)

# Usage
def unreliable_api_call():
    response = requests.get("https://api.example.com/data", timeout=5)
    response.raise_for_status()
    return response.json()

try:
    data = retry_with_backoff(
        unreliable_api_call,
        max_retries=3,
        exceptions=(requests.RequestException,)
    )
except requests.RequestException as e:
    logger.error(f"API call failed after retries: {e}")
    # Fallback to cached data or default behavior
```

### 3. Graceful Degradation
Provide alternative functionality when primary features fail.

```python
class WeatherService:
    def __init__(self):
        self.primary_api = "https://api.weather.com"
        self.fallback_api = "https://backup-weather.com"
        self.cache = {}
    
    def get_weather(self, location: str) -> dict:
        """Get weather with fallback strategies"""
        
        # Try primary API
        try:
            return self._fetch_from_api(self.primary_api, location)
        except APIException as e:
            logger.warning(f"Primary API failed: {e}")
        
        # Try fallback API
        try:
            return self._fetch_from_api(self.fallback_api, location)
        except APIException as e:
            logger.warning(f"Fallback API failed: {e}")
        
        # Try cache
        cached_data = self.cache.get(location)
        if cached_data:
            logger.info(f"Returning cached data for {location}")
            cached_data['source'] = 'cache'
            return cached_data
        
        # Return minimal default data
        logger.error(f"All weather sources failed for {location}")
        return {
            'location': location,
            'temperature': 'N/A',
            'condition': 'Data unavailable',
            'source': 'default'
        }
```

## Exception Hierarchy Design

### Custom Exception Classes
```python
class ApplicationError(Exception):
    """Base exception for application-specific errors"""
    
    def __init__(self, message: str, error_code: str = None, details: dict = None):
        super().__init__(message)
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        self.timestamp = datetime.utcnow()

class ValidationError(ApplicationError):
    """Raised when input validation fails"""
    pass

class AuthenticationError(ApplicationError):
    """Raised when authentication fails"""
    pass

class AuthorizationError(ApplicationError):
    """Raised when user lacks required permissions"""
    pass

class ResourceNotFoundError(ApplicationError):
    """Raised when requested resource doesn't exist"""
    pass

class ExternalServiceError(ApplicationError):
    """Raised when external service calls fail"""
    
    def __init__(self, message: str, service_name: str, status_code: int = None, **kwargs):
        super().__init__(message, **kwargs)
        self.service_name = service_name
        self.status_code = status_code

class DatabaseError(ApplicationError):
    """Raised when database operations fail"""
    pass

# Usage examples
def validate_user_input(data):
    if not data.get('email'):
        raise ValidationError(
            "Email is required",
            error_code="MISSING_EMAIL",
            details={'field': 'email'}
        )
    
    if '@' not in data['email']:
        raise ValidationError(
            "Invalid email format",
            error_code="INVALID_EMAIL",
            details={'field': 'email', 'value': data['email']}
        )

def authenticate_user(username, password):
    user = User.get_by_username(username)
    if not user:
        raise AuthenticationError(
            "Invalid credentials",
            error_code="INVALID_CREDENTIALS"
        )
    
    if not user.check_password(password):
        raise AuthenticationError(
            "Invalid credentials",
            error_code="INVALID_CREDENTIALS"
        )
    
    if not user.is_active:
        raise AuthenticationError(
            "Account is disabled",
            error_code="ACCOUNT_DISABLED",
            details={'user_id': user.id}
        )
```

## Error Context and Logging

### Contextual Error Information
```python
import traceback
import sys
from contextlib import contextmanager

class ErrorContext:
    """Capture and manage error context"""
    
    def __init__(self):
        self.context_stack = []
    
    @contextmanager
    def operation(self, operation_name: str, **context):
        """Add operation context"""
        self.context_stack.append({
            'operation': operation_name,
            'timestamp': datetime.utcnow(),
            **context
        })
        try:
            yield
        finally:
            self.context_stack.pop()
    
    def get_context(self) -> dict:
        """Get current error context"""
        return {
            'context_stack': self.context_stack.copy(),
            'thread_id': threading.get_ident(),
            'process_id': os.getpid()
        }

# Global error context
error_context = ErrorContext()

def handle_user_registration(user_data):
    with error_context.operation('user_registration', user_id=user_data.get('id')):
        try:
            with error_context.operation('validation'):
                validate_user_input(user_data)
            
            with error_context.operation('database_save'):
                user = User.create(user_data)
            
            with error_context.operation('send_welcome_email', user_id=user.id):
                send_welcome_email(user.email)
            
            return user
            
        except Exception as e:
            # Enhanced error logging with context
            context = error_context.get_context()
            logger.error(
                f"User registration failed: {e}",
                extra={
                    'error_type': type(e).__name__,
                    'error_context': context,
                    'user_data': sanitize_sensitive_data(user_data)
                }
            )
            raise
```

### Structured Error Logging
```python
import json
import logging
from datetime import datetime

class StructuredLogger:
    def __init__(self, name):
        self.logger = logging.getLogger(name)
        
        # Configure structured logging
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
    
    def log_error(self, error: Exception, context: dict = None, user_id: str = None):
        """Log error with structured data"""
        error_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'error_type': type(error).__name__,
            'error_message': str(error),
            'error_code': getattr(error, 'error_code', None),
            'traceback': traceback.format_exc(),
            'context': context or {},
            'user_id': user_id
        }
        
        # Add custom error details if available
        if hasattr(error, 'details'):
            error_data['error_details'] = error.details
        
        self.logger.error(json.dumps(error_data, indent=2))
    
    def log_performance_issue(self, operation: str, duration: float, threshold: float):
        """Log performance issues"""
        if duration > threshold:
            perf_data = {
                'timestamp': datetime.utcnow().isoformat(),
                'type': 'performance_issue',
                'operation': operation,
                'duration': duration,
                'threshold': threshold,
                'exceeded_by': duration - threshold
            }
            self.logger.warning(json.dumps(perf_data, indent=2))

logger = StructuredLogger(__name__)
```

## API Error Responses

### Standardized Error Format
```python
from flask import Flask, jsonify
from werkzeug.exceptions import HTTPException

app = Flask(__name__)

class APIErrorResponse:
    """Standardized API error response format"""
    
    def __init__(self, 
                 error_code: str,
                 message: str,
                 status_code: int = 400,
                 details: dict = None,
                 request_id: str = None):
        self.error_code = error_code
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        self.request_id = request_id or generate_request_id()
        self.timestamp = datetime.utcnow().isoformat()
    
    def to_dict(self):
        return {
            'error': {
                'code': self.error_code,
                'message': self.message,
                'details': self.details,
                'request_id': self.request_id,
                'timestamp': self.timestamp
            }
        }
    
    def to_response(self):
        return jsonify(self.to_dict()), self.status_code

# Global error handlers
@app.errorhandler(ValidationError)
def handle_validation_error(error):
    response = APIErrorResponse(
        error_code=error.error_code,
        message=str(error),
        status_code=400,
        details=error.details
    )
    return response.to_response()

@app.errorhandler(AuthenticationError)
def handle_authentication_error(error):
    response = APIErrorResponse(
        error_code=error.error_code,
        message="Authentication failed",
        status_code=401
    )
    return response.to_response()

@app.errorhandler(AuthorizationError)
def handle_authorization_error(error):
    response = APIErrorResponse(
        error_code=error.error_code,
        message="Access denied",
        status_code=403
    )
    return response.to_response()

@app.errorhandler(ResourceNotFoundError)
def handle_not_found_error(error):
    response = APIErrorResponse(
        error_code=error.error_code,
        message=str(error),
        status_code=404
    )
    return response.to_response()

@app.errorhandler(500)
def handle_internal_error(error):
    logger.error(f"Internal server error: {error}")
    response = APIErrorResponse(
        error_code="INTERNAL_ERROR",
        message="An internal error occurred",
        status_code=500
    )
    return response.to_response()
```

## Circuit Breaker Pattern

### Circuit Breaker Implementation
```python
import time
from enum import Enum
from typing import Callable, Any

class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, requests blocked
    HALF_OPEN = "half_open"  # Testing if service recovered

class CircuitBreaker:
    """Implements circuit breaker pattern for external service calls"""
    
    def __init__(self,
                 failure_threshold: int = 5,
                 recovery_timeout: int = 60,
                 expected_exception: type = Exception):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection"""
        
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
            else:
                raise CircuitBreakerOpenError("Circuit breaker is open")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
            
        except self.expected_exception as e:
            self._on_failure()
            raise e
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset"""
        return (time.time() - self.last_failure_time) >= self.recovery_timeout
    
    def _on_success(self):
        """Handle successful call"""
        self.failure_count = 0
        self.state = CircuitState.CLOSED
    
    def _on_failure(self):
        """Handle failed call"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN

class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open"""
    pass

# Usage example
class ExternalAPIClient:
    def __init__(self):
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=3,
            recovery_timeout=30,
            expected_exception=requests.RequestException
        )
    
    def fetch_data(self, endpoint: str) -> dict:
        """Fetch data with circuit breaker protection"""
        def api_call():
            response = requests.get(endpoint, timeout=5)
            response.raise_for_status()
            return response.json()
        
        try:
            return self.circuit_breaker.call(api_call)
        except CircuitBreakerOpenError:
            logger.warning(f"Circuit breaker open for {endpoint}")
            return self._get_fallback_data()
        except requests.RequestException as e:
            logger.error(f"API call failed: {e}")
            return self._get_fallback_data()
    
    def _get_fallback_data(self) -> dict:
        """Return fallback data when API is unavailable"""
        return {'status': 'unavailable', 'data': None}
```

## Database Error Handling

### Database Transaction Patterns
```python
from contextlib import contextmanager
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker

@contextmanager
def database_transaction(session_factory: sessionmaker):
    """Database transaction context manager with proper error handling"""
    session = session_factory()
    try:
        yield session
        session.commit()
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Database transaction failed: {e}")
        raise DatabaseError(f"Database operation failed: {e}") from e
    except Exception as e:
        session.rollback()
        logger.error(f"Unexpected error in database transaction: {e}")
        raise
    finally:
        session.close()

# Usage
def create_user_with_profile(user_data: dict, profile_data: dict):
    """Create user and profile in a transaction"""
    with database_transaction(SessionLocal) as db:
        try:
            # Create user
            user = User(**user_data)
            db.add(user)
            db.flush()  # Get user ID without committing
            
            # Create profile
            profile_data['user_id'] = user.id
            profile = UserProfile(**profile_data)
            db.add(profile)
            
            # Transaction will be committed by context manager
            return user
            
        except ValidationError:
            # Re-raise validation errors without wrapping
            raise
        except Exception as e:
            # Log and wrap unexpected errors
            logger.error(f"Failed to create user with profile: {e}")
            raise DatabaseError("User creation failed") from e
```

## Monitoring and Alerting

### Error Rate Monitoring
```python
import time
from collections import defaultdict, deque

class ErrorMonitor:
    """Monitor error rates and trigger alerts"""
    
    def __init__(self, window_size: int = 300):  # 5 minutes
        self.window_size = window_size
        self.error_counts = defaultdict(deque)
        self.total_counts = defaultdict(deque)
    
    def record_request(self, operation: str, success: bool):
        """Record request outcome"""
        current_time = time.time()
        
        # Clean old entries
        self._clean_old_entries(operation, current_time)
        
        # Record new entry
        self.total_counts[operation].append(current_time)
        if not success:
            self.error_counts[operation].append(current_time)
        
        # Check if alert threshold exceeded
        self._check_alert_threshold(operation)
    
    def _clean_old_entries(self, operation: str, current_time: float):
        """Remove entries outside the time window"""
        cutoff_time = current_time - self.window_size
        
        while (self.error_counts[operation] and 
               self.error_counts[operation][0] < cutoff_time):
            self.error_counts[operation].popleft()
        
        while (self.total_counts[operation] and 
               self.total_counts[operation][0] < cutoff_time):
            self.total_counts[operation].popleft()
    
    def get_error_rate(self, operation: str) -> float:
        """Get current error rate for operation"""
        total = len(self.total_counts[operation])
        errors = len(self.error_counts[operation])
        
        return errors / total if total > 0 else 0.0
    
    def _check_alert_threshold(self, operation: str):
        """Check if error rate exceeds alert threshold"""
        error_rate = self.get_error_rate(operation)
        total_requests = len(self.total_counts[operation])
        
        # Alert if error rate > 10% and at least 10 requests
        if error_rate > 0.1 and total_requests >= 10:
            self._send_alert(operation, error_rate, total_requests)
    
    def _send_alert(self, operation: str, error_rate: float, total_requests: int):
        """Send alert for high error rate"""
        logger.critical(
            f"HIGH ERROR RATE ALERT: {operation} - "
            f"Rate: {error_rate:.2%}, "
            f"Requests: {total_requests} in last {self.window_size}s"
        )
        
        # Send to external alerting system
        # self.alert_service.send_alert(...)

# Global error monitor
error_monitor = ErrorMonitor()

# Decorator to monitor function calls
def monitor_errors(operation_name: str = None):
    def decorator(func):
        nonlocal operation_name
        if operation_name is None:
            operation_name = f"{func.__module__}.{func.__name__}"
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                error_monitor.record_request(operation_name, success=True)
                return result
            except Exception as e:
                error_monitor.record_request(operation_name, success=False)
                raise
        return wrapper
    return decorator

# Usage
@monitor_errors("user_service.create_user")
def create_user(user_data):
    # User creation logic
    pass
```

## Error Handling Best Practices

### 1. Validation Patterns
```python
from typing import List, Optional
from dataclasses import dataclass

@dataclass
class ValidationResult:
    is_valid: bool
    errors: List[str]
    
    def add_error(self, error: str):
        self.errors.append(error)
        self.is_valid = False

def validate_user_registration(data: dict) -> ValidationResult:
    """Comprehensive validation with detailed error reporting"""
    result = ValidationResult(is_valid=True, errors=[])
    
    # Required fields validation
    required_fields = ['email', 'username', 'password']
    for field in required_fields:
        if not data.get(field):
            result.add_error(f"{field} is required")
    
    # Email format validation
    if data.get('email') and '@' not in data['email']:
        result.add_error("Invalid email format")
    
    # Password strength validation
    password = data.get('password', '')
    if len(password) < 8:
        result.add_error("Password must be at least 8 characters")
    if not any(c.isupper() for c in password):
        result.add_error("Password must contain uppercase letter")
    if not any(c.isdigit() for c in password):
        result.add_error("Password must contain a digit")
    
    # Username uniqueness validation
    if data.get('username') and User.exists(username=data['username']):
        result.add_error("Username already exists")
    
    return result
```

### 2. Error Recovery Strategies
```python
class ServiceWithFallbacks:
    """Service with multiple fallback strategies"""
    
    def __init__(self):
        self.cache = {}
        self.circuit_breaker = CircuitBreaker()
    
    def get_user_recommendations(self, user_id: str) -> List[dict]:
        """Get recommendations with multiple fallback strategies"""
        
        # Strategy 1: Try ML recommendation service
        try:
            return self.circuit_breaker.call(
                self._get_ml_recommendations, user_id
            )
        except (CircuitBreakerOpenError, ExternalServiceError) as e:
            logger.warning(f"ML service unavailable: {e}")
        
        # Strategy 2: Try collaborative filtering
        try:
            return self._get_collaborative_recommendations(user_id)
        except Exception as e:
            logger.warning(f"Collaborative filtering failed: {e}")
        
        # Strategy 3: Use cached recommendations
        cached = self.cache.get(f"recommendations:{user_id}")
        if cached:
            logger.info(f"Using cached recommendations for user {user_id}")
            return cached
        
        # Strategy 4: Use popular items as fallback
        logger.warning(f"All recommendation strategies failed for user {user_id}")
        return self._get_popular_items()
    
    def _get_ml_recommendations(self, user_id: str) -> List[dict]:
        # ML service call
        pass
    
    def _get_collaborative_recommendations(self, user_id: str) -> List[dict]:
        # Collaborative filtering logic
        pass
    
    def _get_popular_items(self) -> List[dict]:
        # Return generally popular items
        return [{'id': 1, 'title': 'Popular Item', 'type': 'fallback'}]
```

## Testing Error Scenarios

### Error Simulation and Testing
```python
import pytest
from unittest.mock import patch, Mock

class TestErrorHandling:
    """Test error handling scenarios"""
    
    def test_validation_errors(self):
        """Test validation error handling"""
        invalid_data = {'email': 'invalid-email'}
        
        with pytest.raises(ValidationError) as exc_info:
            validate_user_input(invalid_data)
        
        assert exc_info.value.error_code == "INVALID_EMAIL"
        assert "email" in exc_info.value.details
    
    def test_database_error_handling(self):
        """Test database error handling"""
        with patch('app.database.session') as mock_session:
            mock_session.commit.side_effect = SQLAlchemyError("Connection lost")
            
            with pytest.raises(DatabaseError):
                create_user({'email': 'test@example.com'})
            
            mock_session.rollback.assert_called_once()
    
    def test_external_service_fallback(self):
        """Test fallback when external service fails"""
        service = ServiceWithFallbacks()
        
        with patch.object(service, '_get_ml_recommendations') as mock_ml:
            mock_ml.side_effect = ExternalServiceError("Service down")
            
            with patch.object(service, '_get_popular_items') as mock_popular:
                mock_popular.return_value = [{'id': 1, 'title': 'Fallback'}]
                
                result = service.get_user_recommendations('user123')
                
                assert result == [{'id': 1, 'title': 'Fallback'}]
                mock_ml.assert_called_once()
                mock_popular.assert_called_once()
    
    def test_circuit_breaker_behavior(self):
        """Test circuit breaker opening and closing"""
        cb = CircuitBreaker(failure_threshold=2, recovery_timeout=1)
        
        failing_func = Mock(side_effect=Exception("Service error"))
        
        # Trigger failures to open circuit
        for _ in range(2):
            with pytest.raises(Exception):
                cb.call(failing_func)
        
        # Circuit should be open now
        with pytest.raises(CircuitBreakerOpenError):
            cb.call(failing_func)
        
        # Wait for recovery timeout
        time.sleep(1.1)
        
        # Should allow one test call (half-open state)
        working_func = Mock(return_value="success")
        result = cb.call(working_func)
        assert result == "success"
```

Remember: Good error handling is about providing clear information to users while logging detailed information for developers. Always consider the user experience when designing error responses.
