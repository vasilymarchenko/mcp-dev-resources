# API Design Principles

## Overview
This document outlines comprehensive principles for designing RESTful APIs that are intuitive, consistent, and maintainable. Following these guidelines ensures your APIs are developer-friendly and scalable.

## Core REST Principles

### 1. Resource-Oriented Design
- Use nouns for resource names, not verbs
- Resources represent entities, not actions
- Use hierarchical URLs to show relationships

```
Good:
GET /users/123/orders
POST /users/123/orders

Bad:
GET /getUser/123
POST /createUserOrder/123
```

### 2. HTTP Methods (Verbs)
- **GET**: Retrieve resources (idempotent, safe)
- **POST**: Create new resources
- **PUT**: Update/replace entire resource (idempotent)
- **PATCH**: Partial update of resource
- **DELETE**: Remove resources (idempotent)

### 3. HTTP Status Codes
Use appropriate status codes to communicate results:

#### Success (2xx)
- **200 OK**: Standard success response
- **201 Created**: Resource successfully created
- **202 Accepted**: Request accepted for processing
- **204 No Content**: Success with no response body

#### Client Error (4xx)
- **400 Bad Request**: Invalid request format
- **401 Unauthorized**: Authentication required
- **403 Forbidden**: Access denied
- **404 Not Found**: Resource doesn't exist
- **409 Conflict**: Resource conflict
- **422 Unprocessable Entity**: Validation errors

#### Server Error (5xx)
- **500 Internal Server Error**: Generic server error
- **502 Bad Gateway**: Upstream service error
- **503 Service Unavailable**: Temporary unavailability

## URL Structure & Naming

### Resource Naming Conventions
- Use lowercase letters
- Use hyphens for multi-word resources
- Use plural nouns for collections
- Be consistent across the API

```
Good:
/api/v1/user-profiles
/api/v1/order-items

Bad:
/api/v1/UserProfiles
/api/v1/user_profiles
/api/v1/orderitem
```

### Hierarchical Relationships
```
/users                    # All users
/users/123               # Specific user
/users/123/orders        # Orders for user 123
/users/123/orders/456    # Specific order for user 123
```

### Query Parameters
Use query parameters for:
- Filtering: `?status=active&type=premium`
- Sorting: `?sort=created_at&order=desc`
- Pagination: `?page=2&limit=50`
- Field selection: `?fields=id,name,email`

## Request/Response Design

### Request Structure
```json
{
  "data": {
    "type": "user",
    "attributes": {
      "name": "John Doe",
      "email": "john@example.com"
    }
  }
}
```

### Response Structure
```json
{
  "data": {
    "id": "123",
    "type": "user",
    "attributes": {
      "name": "John Doe",
      "email": "john@example.com",
      "created_at": "2023-01-15T10:30:00Z"
    },
    "relationships": {
      "orders": {
        "links": {
          "related": "/users/123/orders"
        }
      }
    }
  },
  "meta": {
    "version": "1.0",
    "timestamp": "2023-01-15T10:30:00Z"
  }
}
```

### Error Response Format
```json
{
  "errors": [
    {
      "id": "validation_error",
      "status": "422",
      "code": "INVALID_EMAIL",
      "title": "Invalid email format",
      "detail": "The email address 'invalid-email' is not a valid format",
      "source": {
        "pointer": "/data/attributes/email"
      }
    }
  ]
}
```

## Versioning Strategy

### URL Versioning (Recommended)
```
/api/v1/users
/api/v2/users
```

### Header Versioning
```
Accept: application/vnd.api+json;version=1
API-Version: 1
```

### Versioning Best Practices
- Version only when breaking changes are introduced
- Maintain backward compatibility when possible
- Provide migration guides for version upgrades
- Deprecate old versions gradually

## Pagination

### Offset-based Pagination
```
GET /users?page=2&limit=50

Response:
{
  "data": [...],
  "pagination": {
    "current_page": 2,
    "per_page": 50,
    "total_pages": 10,
    "total_count": 500
  }
}
```

### Cursor-based Pagination (for large datasets)
```
GET /users?cursor=eyJpZCI6MTIz&limit=50

Response:
{
  "data": [...],
  "pagination": {
    "next_cursor": "eyJpZCI6MTc4",
    "has_more": true
  }
}
```

## Authentication & Authorization

### Authentication Methods
- **API Keys**: Simple, suitable for server-to-server
- **JWT Tokens**: Stateless, good for distributed systems
- **OAuth 2.0**: Industry standard for user authorization

### Security Headers
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
API-Key: your-api-key-here
X-API-Version: 1
```

### Authorization Patterns
```json
{
  "data": {
    "id": "123",
    "type": "document",
    "attributes": {...},
    "meta": {
      "permissions": ["read", "update"]
    }
  }
}
```

## Content Negotiation

### Request Headers
```
Content-Type: application/json
Accept: application/json
Accept-Language: en-US,en;q=0.9
```

### Response Headers
```
Content-Type: application/json; charset=utf-8
Content-Language: en-US
ETag: "33a64df551425fcc55e4d42a148795d9f25f89d4"
```

## Rate Limiting

### Rate Limit Headers
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1640995200
Retry-After: 3600
```

### Rate Limiting Strategies
- **Fixed Window**: Simple, but can cause thundering herd
- **Sliding Window**: More accurate, computationally expensive
- **Token Bucket**: Allows bursts, good for APIs with varying load

## Caching

### Cache Control Headers
```
Cache-Control: public, max-age=3600
ETag: "686897696a7c876b7e"
Last-Modified: Wed, 15 Jan 2023 10:30:00 GMT
```

### Conditional Requests
```
If-None-Match: "686897696a7c876b7e"
If-Modified-Since: Wed, 15 Jan 2023 10:30:00 GMT
```

## Documentation Best Practices

### API Documentation Should Include
- **Authentication**: How to authenticate requests
- **Rate Limits**: Request limits and policies
- **Error Codes**: Comprehensive error reference
- **Examples**: Request/response examples for each endpoint
- **SDKs**: Client libraries and code samples
- **Changelog**: Version history and breaking changes

### OpenAPI/Swagger Specification
```yaml
openapi: 3.0.0
info:
  title: User API
  version: 1.0.0
paths:
  /users:
    get:
      summary: List users
      parameters:
        - name: page
          in: query
          schema:
            type: integer
            default: 1
      responses:
        '200':
          description: Successful response
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/UserList'
```

## Testing APIs

### Test Categories
- **Unit Tests**: Individual endpoint logic
- **Integration Tests**: Full request/response cycle
- **Contract Tests**: API specification compliance
- **Load Tests**: Performance under load

### Test Data Management
```python
# Use factories for consistent test data
class UserFactory:
    @staticmethod
    def create(name="John Doe", email="john@example.com"):
        return {
            "name": name,
            "email": email,
            "created_at": datetime.utcnow().isoformat()
        }
```

## Monitoring & Observability

### Key Metrics
- **Response Time**: P50, P90, P99 percentiles
- **Error Rate**: 4xx and 5xx response rates
- **Throughput**: Requests per second
- **Availability**: Uptime percentage

### Logging
```json
{
  "timestamp": "2023-01-15T10:30:00Z",
  "level": "INFO",
  "request_id": "req_123456",
  "method": "GET",
  "path": "/api/v1/users/123",
  "status_code": 200,
  "response_time_ms": 150,
  "user_id": "user_789"
}
```

## Common Anti-Patterns to Avoid

- **Chatty APIs**: Requiring multiple requests for simple operations
- **Over-fetching**: Returning more data than needed
- **Under-fetching**: Requiring additional requests for related data
- **Inconsistent Naming**: Mixed conventions across endpoints
- **Ignoring HTTP Semantics**: Misusing HTTP methods and status codes
- **No Versioning Strategy**: Breaking changes without version management
- **Poor Error Messages**: Vague or unhelpful error responses

## API Design Checklist

- [ ] Consistent naming conventions
- [ ] Appropriate HTTP methods and status codes
- [ ] Comprehensive error handling
- [ ] Authentication and authorization
- [ ] Rate limiting implemented
- [ ] Caching strategy defined
- [ ] Documentation complete
- [ ] Versioning strategy in place
- [ ] Monitoring and logging configured
- [ ] Performance testing completed

Remember: Good API design is about creating an interface that is intuitive, consistent, and provides a great developer experience.
