# Pytest Fixtures Examples

"""
Comprehensive examples of pytest fixtures for different testing scenarios.
This file demonstrates various fixture patterns including database setup,
API mocking, file system operations, and test data generation.
"""

import pytest
import tempfile
import shutil
import json
import sqlite3
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from typing import Dict, List, Any, Generator
import requests_mock
import fakeredis

# =============================================================================
# Basic Fixtures
# =============================================================================

@pytest.fixture
def sample_user() -> Dict[str, Any]:
    """Fixture providing a sample user for testing."""
    return {
        "id": 1,
        "username": "testuser",
        "email": "test@example.com",
        "first_name": "Test",
        "last_name": "User",
        "is_active": True,
        "created_at": "2023-01-15T10:30:00Z"
    }

@pytest.fixture
def sample_users() -> List[Dict[str, Any]]:
    """Fixture providing multiple sample users."""
    return [
        {
            "id": 1,
            "username": "alice",
            "email": "alice@example.com",
            "first_name": "Alice",
            "last_name": "Smith",
            "is_active": True
        },
        {
            "id": 2,
            "username": "bob",
            "email": "bob@example.com",
            "first_name": "Bob",
            "last_name": "Johnson",
            "is_active": True
        },
        {
            "id": 3,
            "username": "charlie",
            "email": "charlie@example.com",
            "first_name": "Charlie",
            "last_name": "Brown",
            "is_active": False
        }
    ]

# =============================================================================
# Database Fixtures
# =============================================================================

@pytest.fixture
def in_memory_db() -> Generator[sqlite3.Connection, None, None]:
    """Fixture providing an in-memory SQLite database."""
    conn = sqlite3.connect(":memory:")
    
    # Create tables
    conn.execute("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            first_name TEXT,
            last_name TEXT,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.execute("""
        CREATE TABLE posts (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            content TEXT,
            user_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)
    
    conn.commit()
    yield conn
    conn.close()

@pytest.fixture
def populated_db(in_memory_db: sqlite3.Connection, sample_users: List[Dict]) -> sqlite3.Connection:
    """Fixture providing a database populated with sample data."""
    cursor = in_memory_db.cursor()
    
    # Insert sample users
    for user in sample_users:
        cursor.execute("""
            INSERT INTO users (id, username, email, first_name, last_name, is_active)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            user["id"], user["username"], user["email"],
            user["first_name"], user["last_name"], user["is_active"]
        ))
    
    # Insert sample posts
    posts = [
        (1, "First Post", "Content of first post", 1),
        (2, "Second Post", "Content of second post", 1),
        (3, "Third Post", "Content of third post", 2),
    ]
    
    cursor.executemany("""
        INSERT INTO posts (id, title, content, user_id)
        VALUES (?, ?, ?, ?)
    """, posts)
    
    in_memory_db.commit()
    return in_memory_db

@pytest.fixture
def database_session():
    """Fixture for SQLAlchemy database session (example pattern)."""
    # This would be adapted to your actual SQLAlchemy setup
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    
    # Create test database engine
    engine = create_engine("sqlite:///:memory:")
    
    # Create tables (assuming you have a Base.metadata)
    # Base.metadata.create_all(engine)
    
    # Create session
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    try:
        yield session
    finally:
        session.close()

# =============================================================================
# File System Fixtures
# =============================================================================

@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Fixture providing a temporary directory."""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    shutil.rmtree(temp_dir)

@pytest.fixture
def sample_json_file(temp_dir: Path) -> Path:
    """Fixture creating a sample JSON file."""
    data = {
        "users": [
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"}
        ],
        "metadata": {
            "version": "1.0",
            "created": "2023-01-15"
        }
    }
    
    file_path = temp_dir / "sample_data.json"
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)
    
    return file_path

@pytest.fixture
def sample_csv_file(temp_dir: Path) -> Path:
    """Fixture creating a sample CSV file."""
    csv_content = """id,name,email,age
1,Alice Smith,alice@example.com,25
2,Bob Johnson,bob@example.com,30
3,Charlie Brown,charlie@example.com,35"""
    
    file_path = temp_dir / "users.csv"
    with open(file_path, 'w') as f:
        f.write(csv_content)
    
    return file_path

@pytest.fixture
def sample_config_file(temp_dir: Path) -> Path:
    """Fixture creating a sample configuration file."""
    config = {
        "database": {
            "host": "localhost",
            "port": 5432,
            "name": "testdb"
        },
        "api": {
            "base_url": "https://api.example.com",
            "timeout": 30
        },
        "logging": {
            "level": "INFO",
            "format": "json"
        }
    }
    
    file_path = temp_dir / "config.json"
    with open(file_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    return file_path

# =============================================================================
# API and HTTP Fixtures
# =============================================================================

@pytest.fixture
def mock_requests():
    """Fixture for mocking HTTP requests."""
    with requests_mock.Mocker() as m:
        # Setup common mock responses
        m.get('https://api.example.com/users', json=[
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"}
        ])
        
        m.get('https://api.example.com/users/1', json={
            "id": 1,
            "name": "Alice",
            "email": "alice@example.com"
        })
        
        m.post('https://api.example.com/users', json={
            "id": 3,
            "name": "New User",
            "email": "new@example.com"
        }, status_code=201)
        
        m.get('https://api.example.com/error', status_code=500)
        
        yield m

@pytest.fixture
def api_client():
    """Fixture providing a mock API client."""
    client = Mock()
    
    # Mock successful responses
    client.get_user.return_value = {
        "id": 1,
        "username": "testuser",
        "email": "test@example.com"
    }
    
    client.create_user.return_value = {
        "id": 2,
        "username": "newuser",
        "email": "new@example.com"
    }
    
    client.list_users.return_value = [
        {"id": 1, "username": "user1"},
        {"id": 2, "username": "user2"}
    ]
    
    return client

@pytest.fixture
def flask_app():
    """Fixture providing a Flask app for testing."""
    from flask import Flask
    
    app = Flask(__name__)
    app.config['TESTING'] = True
    
    @app.route('/health')
    def health():
        return {"status": "healthy"}
    
    @app.route('/users/<int:user_id>')
    def get_user(user_id):
        return {"id": user_id, "name": f"User {user_id}"}
    
    with app.test_client() as client:
        with app.app_context():
            yield client

# =============================================================================
# Cache and Redis Fixtures
# =============================================================================

@pytest.fixture
def redis_client():
    """Fixture providing a fake Redis client for testing."""
    fake_redis = fakeredis.FakeStrictRedis()
    
    # Pre-populate with test data
    fake_redis.set("user:1", json.dumps({"id": 1, "name": "Alice"}))
    fake_redis.set("user:2", json.dumps({"id": 2, "name": "Bob"}))
    fake_redis.hset("user_cache", "count", 2)
    
    yield fake_redis
    fake_redis.flushall()

@pytest.fixture
def cache_service(redis_client):
    """Fixture providing a cache service with Redis backend."""
    class MockCacheService:
        def __init__(self, redis_client):
            self.redis = redis_client
        
        def get(self, key: str) -> Any:
            value = self.redis.get(key)
            return json.loads(value) if value else None
        
        def set(self, key: str, value: Any, ttl: int = 3600):
            self.redis.setex(key, ttl, json.dumps(value))
        
        def delete(self, key: str):
            self.redis.delete(key)
        
        def exists(self, key: str) -> bool:
            return self.redis.exists(key)
    
    return MockCacheService(redis_client)

# =============================================================================
# Authentication and Security Fixtures
# =============================================================================

@pytest.fixture
def auth_token() -> str:
    """Fixture providing a mock authentication token."""
    return "mock_jwt_token_for_testing"

@pytest.fixture
def authenticated_user() -> Dict[str, Any]:
    """Fixture providing an authenticated user context."""
    return {
        "user_id": 1,
        "username": "testuser",
        "email": "test@example.com",
        "roles": ["user"],
        "permissions": ["read", "write"]
    }

@pytest.fixture
def admin_user() -> Dict[str, Any]:
    """Fixture providing an admin user context."""
    return {
        "user_id": 999,
        "username": "admin",
        "email": "admin@example.com",
        "roles": ["admin"],
        "permissions": ["read", "write", "delete", "admin"]
    }

@pytest.fixture
def auth_headers(auth_token: str) -> Dict[str, str]:
    """Fixture providing authentication headers."""
    return {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }

# =============================================================================
# Time and Date Fixtures
# =============================================================================

@pytest.fixture
def fixed_datetime():
    """Fixture providing a fixed datetime for consistent testing."""
    fixed_time = datetime(2023, 1, 15, 10, 30, 0)
    
    with patch('datetime.datetime') as mock_datetime:
        mock_datetime.now.return_value = fixed_time
        mock_datetime.utcnow.return_value = fixed_time
        mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
        yield fixed_time

@pytest.fixture
def time_machine():
    """Fixture providing time manipulation utilities."""
    class TimeMachine:
        def __init__(self):
            self.current_time = datetime.now()
            self.patcher = None
        
        def set_time(self, new_time: datetime):
            if self.patcher:
                self.patcher.stop()
            
            self.current_time = new_time
            self.patcher = patch('datetime.datetime')
            mock_datetime = self.patcher.start()
            mock_datetime.now.return_value = new_time
            mock_datetime.utcnow.return_value = new_time
            mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
        
        def advance_time(self, **kwargs):
            self.current_time += timedelta(**kwargs)
            self.set_time(self.current_time)
        
        def stop(self):
            if self.patcher:
                self.patcher.stop()
    
    machine = TimeMachine()
    yield machine
    machine.stop()

# =============================================================================
# Environment and Configuration Fixtures
# =============================================================================

@pytest.fixture
def mock_env_vars():
    """Fixture for mocking environment variables."""
    env_vars = {
        "DATABASE_URL": "sqlite:///:memory:",
        "SECRET_KEY": "test-secret-key",
        "DEBUG": "True",
        "ENVIRONMENT": "testing"
    }
    
    with patch.dict('os.environ', env_vars):
        yield env_vars

@pytest.fixture
def app_config():
    """Fixture providing application configuration."""
    return {
        "database": {
            "url": "sqlite:///:memory:",
            "pool_size": 5
        },
        "cache": {
            "type": "redis",
            "url": "redis://localhost:6379/0"
        },
        "logging": {
            "level": "DEBUG",
            "format": "json"
        },
        "features": {
            "email_notifications": True,
            "user_registration": True,
            "payment_processing": False
        }
    }

# =============================================================================
# Factory Fixtures
# =============================================================================

@pytest.fixture
def user_factory():
    """Fixture providing a user factory for generating test users."""
    class UserFactory:
        def __init__(self):
            self.counter = 0
        
        def create(self, **overrides) -> Dict[str, Any]:
            self.counter += 1
            user = {
                "id": self.counter,
                "username": f"user{self.counter}",
                "email": f"user{self.counter}@example.com",
                "first_name": f"User",
                "last_name": f"{self.counter}",
                "is_active": True,
                "created_at": datetime.now().isoformat()
            }
            user.update(overrides)
            return user
        
        def create_batch(self, count: int, **overrides) -> List[Dict[str, Any]]:
            return [self.create(**overrides) for _ in range(count)]
    
    return UserFactory()

@pytest.fixture
def order_factory():
    """Fixture providing an order factory for e-commerce testing."""
    class OrderFactory:
        def __init__(self):
            self.counter = 0
        
        def create(self, **overrides) -> Dict[str, Any]:
            self.counter += 1
            order = {
                "id": self.counter,
                "user_id": 1,
                "status": "pending",
                "total_amount": 99.99,
                "currency": "USD",
                "items": [
                    {
                        "id": 1,
                        "name": "Test Product",
                        "quantity": 1,
                        "price": 99.99
                    }
                ],
                "shipping_address": {
                    "street": "123 Test St",
                    "city": "Test City",
                    "state": "TS",
                    "zip_code": "12345"
                },
                "created_at": datetime.now().isoformat()
            }
            order.update(overrides)
            return order
    
    return OrderFactory()

# =============================================================================
# Async Testing Fixtures
# =============================================================================

@pytest.fixture
async def async_client():
    """Fixture providing an async HTTP client for testing."""
    import aiohttp
    
    async with aiohttp.ClientSession() as session:
        yield session

@pytest.fixture
def mock_async_service():
    """Fixture providing a mock async service."""
    service = Mock()
    
    async def mock_fetch_data(url):
        if "error" in url:
            raise aiohttp.ClientError("Connection failed")
        return {"data": "test_data", "url": url}
    
    service.fetch_data = mock_fetch_data
    return service

# =============================================================================
# Integration Test Fixtures
# =============================================================================

@pytest.fixture(scope="session")
def docker_postgres():
    """Fixture providing a PostgreSQL database in Docker for integration tests."""
    import subprocess
    import time
    import psycopg2
    
    # Start PostgreSQL container
    container_name = "pytest_postgres"
    subprocess.run([
        "docker", "run", "-d",
        "--name", container_name,
        "-e", "POSTGRES_PASSWORD=testpass",
        "-e", "POSTGRES_DB=testdb",
        "-p", "5433:5432",
        "postgres:13"
    ])
    
    # Wait for database to be ready
    for _ in range(30):
        try:
            conn = psycopg2.connect(
                host="localhost",
                port=5433,
                database="testdb",
                user="postgres",
                password="testpass"
            )
            conn.close()
            break
        except psycopg2.OperationalError:
            time.sleep(1)
    
    yield {
        "host": "localhost",
        "port": 5433,
        "database": "testdb",
        "user": "postgres",
        "password": "testpass"
    }
    
    # Cleanup
    subprocess.run(["docker", "stop", container_name])
    subprocess.run(["docker", "rm", container_name])

# =============================================================================
# Parametrized Fixtures
# =============================================================================

@pytest.fixture(params=["sqlite", "postgres", "mysql"])
def database_type(request):
    """Parametrized fixture for testing with different database types."""
    return request.param

@pytest.fixture(params=[
    {"role": "user", "permissions": ["read"]},
    {"role": "admin", "permissions": ["read", "write", "delete"]},
    {"role": "guest", "permissions": []}
])
def user_with_role(request):
    """Parametrized fixture for testing with different user roles."""
    return request.param

# =============================================================================
# Cleanup and Teardown Fixtures
# =============================================================================

@pytest.fixture
def cleanup_files():
    """Fixture that provides file cleanup functionality."""
    created_files = []
    
    def register_file(filepath):
        created_files.append(Path(filepath))
    
    yield register_file
    
    # Cleanup
    for filepath in created_files:
        if filepath.exists():
            if filepath.is_file():
                filepath.unlink()
            elif filepath.is_dir():
                shutil.rmtree(filepath)

@pytest.fixture(autouse=True)
def reset_singletons():
    """Auto-use fixture to reset singleton instances between tests."""
    # Reset any singleton instances here
    # Example:
    # SometonClass._instance = None
    yield
    # Additional cleanup if needed

# =============================================================================
# Performance Testing Fixtures
# =============================================================================

@pytest.fixture
def performance_monitor():
    """Fixture for monitoring test performance."""
    import time
    import psutil
    
    class PerformanceMonitor:
        def __init__(self):
            self.start_time = None
            self.start_memory = None
        
        def start(self):
            self.start_time = time.time()
            self.start_memory = psutil.Process().memory_info().rss
        
        def stop(self):
            end_time = time.time()
            end_memory = psutil.Process().memory_info().rss
            
            return {
                "duration": end_time - self.start_time,
                "memory_delta": end_memory - self.start_memory
            }
    
    return PerformanceMonitor()

# =============================================================================
# Example Usage in Tests
# =============================================================================

def test_user_creation_with_fixtures(sample_user, populated_db):
    """Example test using multiple fixtures."""
    cursor = populated_db.cursor()
    
    # Test user creation
    cursor.execute("SELECT COUNT(*) FROM users")
    initial_count = cursor.fetchone()[0]
    
    # Insert new user
    cursor.execute("""
        INSERT INTO users (username, email, first_name, last_name)
        VALUES (?, ?, ?, ?)
    """, (
        sample_user["username"],
        sample_user["email"],
        sample_user["first_name"],
        sample_user["last_name"]
    ))
    
    # Verify insertion
    cursor.execute("SELECT COUNT(*) FROM users")
    final_count = cursor.fetchone()[0]
    
    assert final_count == initial_count + 1

def test_api_integration_with_mocks(mock_requests, api_client):
    """Example test using API mocks."""
    # Test with requests_mock
    import requests
    response = requests.get('https://api.example.com/users')
    assert response.status_code == 200
    assert len(response.json()) == 2
    
    # Test with mock client
    user = api_client.get_user(1)
    assert user["id"] == 1
    assert user["username"] == "testuser"

def test_file_operations_with_temp_dir(temp_dir, sample_json_file):
    """Example test using file system fixtures."""
    # Read the sample file
    with open(sample_json_file, 'r') as f:
        data = json.load(f)
    
    assert "users" in data
    assert len(data["users"]) == 2
    
    # Create a new file in temp directory
    new_file = temp_dir / "output.txt"
    new_file.write_text("Test output")
    
    assert new_file.exists()
    assert new_file.read_text() == "Test output"
