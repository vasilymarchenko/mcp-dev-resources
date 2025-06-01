# Unit Testing Guidelines

## Overview
This document provides comprehensive guidelines for writing effective unit tests using pytest and other testing frameworks. Following these practices will ensure your tests are reliable, maintainable, and provide good coverage.

## Core Principles

### 1. Test Structure (AAA Pattern)
- **Arrange**: Set up test data and dependencies
- **Act**: Execute the code under test
- **Assert**: Verify the expected outcomes

### 2. Test Naming Convention
- Use descriptive names that explain what is being tested
- Format: `test_should_[expected_behavior]_when_[condition]`
- Example: `test_should_return_user_when_valid_id_provided`

### 3. Test Independence
- Each test should be independent and not rely on other tests
- Use fixtures for shared setup code
- Clean up after each test to avoid side effects

## Pytest Best Practices

### Fixtures
```python
@pytest.fixture
def sample_user():
    return User(id=1, name="John Doe", email="john@example.com")

@pytest.fixture
def database_session():
    # Setup
    session = create_test_session()
    yield session
    # Teardown
    session.close()
```

### Parameterized Tests
```python
@pytest.mark.parametrize("input,expected", [
    (1, 2),
    (2, 4),
    (3, 6),
])
def test_double_function(input, expected):
    assert double(input) == expected
```

### Mocking with unittest.mock
```python
from unittest.mock import Mock, patch

@patch('module.external_service')
def test_service_call(mock_service):
    mock_service.return_value = {"status": "success"}
    result = my_function()
    assert result["status"] == "success"
    mock_service.assert_called_once()
```

## Test Categories

### 1. Unit Tests
- Test individual functions/methods in isolation
- Mock external dependencies
- Fast execution (< 100ms per test)

### 2. Integration Tests
- Test interaction between components
- Use real databases/services in test environment
- Slower but more comprehensive

### 3. Property-Based Tests
```python
from hypothesis import given, strategies as st

@given(st.integers())
def test_absolute_value_is_positive(x):
    assert abs(x) >= 0
```

## Coverage Guidelines
- Aim for 80-90% code coverage
- Focus on critical business logic
- Don't chase 100% coverage at the expense of test quality
- Use `pytest-cov` for coverage reporting

## Common Patterns

### Testing Exceptions
```python
def test_should_raise_error_when_invalid_input():
    with pytest.raises(ValueError, match="Invalid input"):
        process_data(None)
```

### Testing Async Code
```python
@pytest.mark.asyncio
async def test_async_function():
    result = await async_operation()
    assert result is not None
```

### Database Testing
```python
@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = SessionLocal()
    yield session
    session.close()
```

## CI/CD Integration
- Run tests on every commit
- Use parallel test execution for faster feedback
- Generate test reports and coverage metrics
- Fail builds on test failures or coverage drops

## Tools and Libraries
- **pytest**: Primary testing framework
- **pytest-cov**: Coverage reporting
- **pytest-xdist**: Parallel test execution
- **factory-boy**: Test data generation
- **freezegun**: Time/date mocking
- **responses**: HTTP request mocking

## Anti-Patterns to Avoid
- Testing implementation details instead of behavior
- Overly complex test setup
- Tests that depend on external services
- Flaky tests that pass/fail inconsistently
- Testing getters/setters without logic
- One assertion per test (too rigid)

## Test Organization
```
tests/
├── unit/
│   ├── test_models.py
│   ├── test_services.py
│   └── test_utils.py
├── integration/
│   ├── test_api.py
│   └── test_database.py
├── fixtures/
│   └── conftest.py
└── data/
    └── test_data.json
```
