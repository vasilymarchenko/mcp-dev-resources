# Security Guidelines

## Overview
This document provides comprehensive security guidelines for developing secure applications. Following these practices helps prevent common vulnerabilities and ensures robust protection against security threats.

## OWASP Top 10 Security Risks

### 1. Injection Attacks

#### SQL Injection Prevention
```python
# Bad - Vulnerable to SQL injection
query = f"SELECT * FROM users WHERE id = {user_id}"

# Good - Use parameterized queries
query = "SELECT * FROM users WHERE id = ?"
cursor.execute(query, (user_id,))

# Better - Use ORM
user = User.objects.get(id=user_id)
```

#### NoSQL Injection Prevention
```python
# Bad - Vulnerable to NoSQL injection
user = db.users.find_one({"username": username})

# Good - Use proper sanitization
from bson.objectid import ObjectId
user = db.users.find_one({"_id": ObjectId(user_id)})
```

### 2. Authentication & Session Management

#### Password Security
```python
import bcrypt
import secrets

# Password hashing
def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

# Password verification
def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

# Generate secure random tokens
def generate_token() -> str:
    return secrets.token_urlsafe(32)
```

#### Session Security
```python
# Secure session configuration
app.config.update(
    SESSION_COOKIE_SECURE=True,      # HTTPS only
    SESSION_COOKIE_HTTPONLY=True,    # No JavaScript access
    SESSION_COOKIE_SAMESITE='Strict', # CSRF protection
    PERMANENT_SESSION_LIFETIME=timedelta(hours=1)
)
```

### 3. Cross-Site Scripting (XSS) Prevention

#### Output Encoding
```python
from markupsafe import escape
from bleach import clean

# Escape user input for HTML context
def safe_html(user_input: str) -> str:
    return escape(user_input)

# Sanitize HTML content
def sanitize_html(html_content: str) -> str:
    allowed_tags = ['p', 'br', 'strong', 'em']
    return clean(html_content, tags=allowed_tags, strip=True)
```

#### Content Security Policy (CSP)
```python
@app.after_request
def set_csp_header(response):
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: https:;"
    )
    return response
```

### 4. Cross-Site Request Forgery (CSRF) Protection

```python
from flask_wtf.csrf import CSRFProtect

# Enable CSRF protection
csrf = CSRFProtect(app)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')

# CSRF token in forms
@app.route('/transfer', methods=['POST'])
@csrf.protect
def transfer_funds():
    # Process secure form submission
    pass
```

### 5. Security Misconfiguration Prevention

#### Secure Headers
```python
@app.after_request
def set_security_headers(response):
    # Prevent clickjacking
    response.headers['X-Frame-Options'] = 'DENY'
    
    # XSS protection
    response.headers['X-XSS-Protection'] = '1; mode=block'
    
    # Content type sniffing prevention
    response.headers['X-Content-Type-Options'] = 'nosniff'
    
    # HTTPS enforcement
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    
    # Referrer policy
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    
    return response
```

## Input Validation & Sanitization

### Validation Patterns
```python
import re
from typing import Optional

def validate_email(email: str) -> bool:
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def validate_phone(phone: str) -> bool:
    # Remove all non-digits
    digits_only = re.sub(r'\D', '', phone)
    return len(digits_only) >= 10

def sanitize_filename(filename: str) -> str:
    # Remove dangerous characters
    return re.sub(r'[^\w\s-.]', '', filename).strip()

def validate_user_input(data: dict) -> Optional[str]:
    """Validate user input and return error message if invalid"""
    if not data.get('email') or not validate_email(data['email']):
        return "Invalid email format"
    
    if not data.get('name') or len(data['name']) < 2:
        return "Name must be at least 2 characters"
    
    return None
```

### File Upload Security
```python
import os
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB

def allowed_file(filename: str) -> bool:
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def secure_file_upload(file):
    if not file or file.filename == '':
        return None, "No file selected"
    
    if not allowed_file(file.filename):
        return None, "File type not allowed"
    
    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    # Check file size
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)
    
    if file_size > MAX_FILE_SIZE:
        return None, "File too large"
    
    file.save(file_path)
    return file_path, None
```

## Cryptography & Data Protection

### Encryption
```python
from cryptography.fernet import Fernet
import base64
import os

class DataEncryption:
    def __init__(self):
        self.key = self._get_or_create_key()
        self.cipher = Fernet(self.key)
    
    def _get_or_create_key(self) -> bytes:
        key = os.environ.get('ENCRYPTION_KEY')
        if not key:
            key = Fernet.generate_key()
            # Store this key securely!
            print(f"Generated new key: {key.decode()}")
        return key.encode() if isinstance(key, str) else key
    
    def encrypt(self, data: str) -> str:
        encrypted_data = self.cipher.encrypt(data.encode())
        return base64.urlsafe_b64encode(encrypted_data).decode()
    
    def decrypt(self, encrypted_data: str) -> str:
        decoded_data = base64.urlsafe_b64decode(encrypted_data.encode())
        decrypted_data = self.cipher.decrypt(decoded_data)
        return decrypted_data.decode()
```

### Secure Random Generation
```python
import secrets
import string

def generate_secure_password(length: int = 12) -> str:
    """Generate a cryptographically secure password"""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def generate_secure_token() -> str:
    """Generate a secure random token for API keys, session tokens, etc."""
    return secrets.token_urlsafe(32)

def generate_otp() -> str:
    """Generate a 6-digit OTP"""
    return ''.join(secrets.choice(string.digits) for _ in range(6))
```

## API Security

### Authentication & Authorization
```python
import jwt
from functools import wraps
from datetime import datetime, timedelta

def generate_jwt_token(user_id: int, role: str) -> str:
    payload = {
        'user_id': user_id,
        'role': role,
        'exp': datetime.utcnow() + timedelta(hours=24),
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, app.config['JWT_SECRET'], algorithm='HS256')

def verify_jwt_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, app.config['JWT_SECRET'], algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        raise ValueError("Token has expired")
    except jwt.InvalidTokenError:
        raise ValueError("Invalid token")

def require_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return {'error': 'No token provided'}, 401
        
        try:
            # Remove 'Bearer ' prefix
            token = token.split(' ')[1] if token.startswith('Bearer ') else token
            payload = verify_jwt_token(token)
            request.current_user = payload
        except ValueError as e:
            return {'error': str(e)}, 401
        
        return f(*args, **kwargs)
    return decorated_function

def require_role(required_role: str):
    def decorator(f):
        @wraps(f)
        @require_auth
        def decorated_function(*args, **kwargs):
            if request.current_user.get('role') != required_role:
                return {'error': 'Insufficient permissions'}, 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator
```

### Rate Limiting
```python
from collections import defaultdict
from time import time

class RateLimiter:
    def __init__(self, max_requests: int = 100, window_seconds: int = 3600):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = defaultdict(list)
    
    def is_allowed(self, client_id: str) -> bool:
        now = time()
        window_start = now - self.window_seconds
        
        # Clean old requests
        self.requests[client_id] = [
            req_time for req_time in self.requests[client_id]
            if req_time > window_start
        ]
        
        # Check if limit exceeded
        if len(self.requests[client_id]) >= self.max_requests:
            return False
        
        # Add current request
        self.requests[client_id].append(now)
        return True

rate_limiter = RateLimiter(max_requests=100, window_seconds=3600)

@app.before_request
def check_rate_limit():
    client_ip = request.remote_addr
    if not rate_limiter.is_allowed(client_ip):
        return {'error': 'Rate limit exceeded'}, 429
```

## Database Security

### Secure Database Practices
```python
import os
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

# Secure database connection
def create_secure_db_connection():
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        raise ValueError("DATABASE_URL environment variable not set")
    
    # Use connection pooling
    engine = create_engine(
        db_url,
        poolclass=QueuePool,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,  # Validate connections
        echo=False  # Don't log SQL in production
    )
    return engine

# Secure data access patterns
class SecureUserRepository:
    def __init__(self, db_session):
        self.db = db_session
    
    def get_user_by_id(self, user_id: int, requesting_user_id: int):
        # Authorization check
        if user_id != requesting_user_id and not self.is_admin(requesting_user_id):
            raise PermissionError("Access denied")
        
        return self.db.query(User).filter(User.id == user_id).first()
    
    def is_admin(self, user_id: int) -> bool:
        user = self.db.query(User).filter(User.id == user_id).first()
        return user and user.role == 'admin'
```

## Logging & Monitoring

### Security Logging
```python
import logging
from datetime import datetime

# Configure security logger
security_logger = logging.getLogger('security')
security_handler = logging.FileHandler('security.log')
security_formatter = logging.Formatter(
    '%(asctime)s - %(levelname)s - %(message)s'
)
security_handler.setFormatter(security_formatter)
security_logger.addHandler(security_handler)
security_logger.setLevel(logging.INFO)

def log_security_event(event_type: str, user_id: str = None, details: dict = None):
    """Log security-related events"""
    log_entry = {
        'timestamp': datetime.utcnow().isoformat(),
        'event_type': event_type,
        'user_id': user_id,
        'ip_address': request.remote_addr if request else None,
        'user_agent': request.headers.get('User-Agent') if request else None,
        'details': details or {}
    }
    security_logger.info(f"SECURITY_EVENT: {log_entry}")

# Usage examples
@app.route('/login', methods=['POST'])
def login():
    # ... login logic ...
    if login_successful:
        log_security_event('LOGIN_SUCCESS', user_id=user.id)
    else:
        log_security_event('LOGIN_FAILED', details={'username': username})
```

## Environment & Configuration Security

### Secure Configuration Management
```python
import os
from typing import Optional

class SecurityConfig:
    # Required environment variables
    REQUIRED_VARS = [
        'SECRET_KEY',
        'DATABASE_URL',
        'JWT_SECRET'
    ]
    
    def __init__(self):
        self.validate_environment()
    
    def validate_environment(self):
        missing_vars = [var for var in self.REQUIRED_VARS if not os.environ.get(var)]
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {missing_vars}")
    
    @property
    def secret_key(self) -> str:
        return os.environ['SECRET_KEY']
    
    @property
    def database_url(self) -> str:
        return os.environ['DATABASE_URL']
    
    @property
    def jwt_secret(self) -> str:
        return os.environ['JWT_SECRET']
    
    @property
    def debug_mode(self) -> bool:
        return os.environ.get('DEBUG', 'False').lower() == 'true'

# Example .env file (never commit to version control)
"""
SECRET_KEY=your-secret-key-here-make-it-long-and-random
DATABASE_URL=postgresql://user:password@localhost/dbname
JWT_SECRET=another-secret-key-for-jwt-tokens
DEBUG=False
ENCRYPTION_KEY=your-encryption-key-here
"""
```

## Security Testing

### Security Test Examples
```python
import pytest
from unittest.mock import patch

class TestSecurityFeatures:
    def test_sql_injection_prevention(self):
        """Test that SQL injection attacks are prevented"""
        malicious_input = "'; DROP TABLE users; --"
        response = self.client.get(f'/users?search={malicious_input}')
        assert response.status_code != 500
        # Verify database integrity
    
    def test_xss_prevention(self):
        """Test that XSS attacks are prevented"""
        xss_payload = "<script>alert('xss')</script>"
        response = self.client.post('/comments', json={'content': xss_payload})
        assert xss_payload not in response.data.decode()
    
    def test_authentication_required(self):
        """Test that protected endpoints require authentication"""
        response = self.client.get('/protected-resource')
        assert response.status_code == 401
    
    def test_rate_limiting(self):
        """Test that rate limiting works"""
        for _ in range(101):  # Exceed rate limit
            response = self.client.get('/api/endpoint')
        assert response.status_code == 429
    
    def test_password_strength(self):
        """Test password strength requirements"""
        weak_passwords = ['123', 'password', 'abc']
        for password in weak_passwords:
            response = self.client.post('/register', json={
                'username': 'test',
                'password': password
            })
            assert response.status_code == 400
```

## Security Checklist

### Development Phase
- [ ] Input validation on all user inputs
- [ ] Output encoding for all dynamic content
- [ ] Parameterized queries for database access
- [ ] Proper authentication and authorization
- [ ] Secure session management
- [ ] CSRF protection implemented
- [ ] Security headers configured
- [ ] Sensitive data encryption
- [ ] Secure error handling (no information leakage)
- [ ] Rate limiting implemented

### Deployment Phase
- [ ] HTTPS enforced
- [ ] Security headers configured
- [ ] Database access restricted
- [ ] Environment variables secured
- [ ] Logging and monitoring in place
- [ ] Regular security updates
- [ ] Backup and recovery procedures
- [ ] Incident response plan

### Ongoing Maintenance
- [ ] Regular security audits
- [ ] Dependency vulnerability scanning
- [ ] Penetration testing
- [ ] Security training for developers
- [ ] Security patch management
- [ ] Access control reviews

## Common Security Anti-Patterns to Avoid

- **Storing passwords in plain text**
- **Using GET requests for sensitive operations**
- **Trusting user input without validation**
- **Hardcoding secrets in source code**
- **Ignoring security headers**
- **Using outdated dependencies**
- **Insufficient logging of security events**
- **Overprivileged database connections**
- **Missing input sanitization**
- **Weak password policies**

Remember: Security is not a feature, it's a fundamental requirement that must be built into every aspect of your application.
