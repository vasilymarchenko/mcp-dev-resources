# Code Review Checklist

## Overview
This comprehensive checklist ensures consistent, high-quality code reviews that improve code maintainability, security, and performance. Use this guide for both self-review and peer review processes.

## Pre-Review Preparation
- [ ] Code compiles without warnings
- [ ] All tests pass locally
- [ ] Code follows project style guidelines
- [ ] Documentation is updated
- [ ] Self-review completed

## Code Quality & Style

### Readability
- [ ] Code is self-documenting with clear variable/function names
- [ ] Complex logic has explanatory comments
- [ ] Functions are focused and do one thing well
- [ ] Code follows consistent formatting
- [ ] No commented-out code (unless temporarily needed)

### Structure & Design
- [ ] Functions are appropriately sized (< 20-30 lines ideally)
- [ ] Classes have single responsibility
- [ ] Code follows SOLID principles
- [ ] Appropriate design patterns are used
- [ ] No code duplication (DRY principle)
- [ ] Dependencies are properly injected

### Error Handling
- [ ] Appropriate exception handling
- [ ] Error messages are descriptive and actionable
- [ ] Resources are properly cleaned up (try/finally, context managers)
- [ ] Edge cases are handled
- [ ] Input validation is performed

## Security Review

### Input Validation
- [ ] All user inputs are validated and sanitized
- [ ] SQL injection prevention (parameterized queries)
- [ ] XSS prevention (output encoding)
- [ ] Path traversal protection
- [ ] File upload restrictions

### Authentication & Authorization
- [ ] Proper authentication checks
- [ ] Authorization at appropriate levels
- [ ] Session management is secure
- [ ] Password handling follows best practices
- [ ] Sensitive data is not logged

### Data Protection
- [ ] Sensitive data is encrypted at rest
- [ ] HTTPS used for data transmission
- [ ] API keys/secrets not hardcoded
- [ ] Personal data handling complies with regulations
- [ ] Audit logging for sensitive operations

## Performance Review

### Efficiency
- [ ] No unnecessary database queries (N+1 problem)
- [ ] Appropriate data structures chosen
- [ ] Caching implemented where beneficial
- [ ] Async operations used appropriately
- [ ] Resource usage is reasonable

### Scalability
- [ ] Code handles increased load gracefully
- [ ] Database queries are optimized
- [ ] Memory usage is controlled
- [ ] No potential memory leaks
- [ ] Pagination implemented for large datasets

## Testing

### Test Coverage
- [ ] New code has appropriate test coverage
- [ ] Tests cover edge cases and error scenarios
- [ ] Integration tests for complex interactions
- [ ] Tests are maintainable and fast
- [ ] Mocks are used appropriately

### Test Quality
- [ ] Tests are independent and deterministic
- [ ] Test names are descriptive
- [ ] Tests follow AAA pattern (Arrange, Act, Assert)
- [ ] No test duplication
- [ ] Tests fail for the right reasons

## Documentation

### Code Documentation
- [ ] Public APIs are documented
- [ ] Complex algorithms are explained
- [ ] Configuration options are documented
- [ ] Examples provided where helpful
- [ ] Documentation is up-to-date

### Change Documentation
- [ ] PR description explains the changes
- [ ] Breaking changes are highlighted
- [ ] Migration instructions provided if needed
- [ ] Related issues are referenced
- [ ] Screenshots for UI changes

## Architecture & Maintainability

### Dependencies
- [ ] New dependencies are justified
- [ ] Dependencies are up-to-date and secure
- [ ] Circular dependencies are avoided
- [ ] Interfaces are properly defined
- [ ] Coupling is minimized

### Configuration
- [ ] Configuration is externalized
- [ ] Default values are sensible
- [ ] Environment-specific configs are separate
- [ ] Configuration validation is implemented
- [ ] Secrets are managed securely

## Specific Technology Checks

### Database
- [ ] Migrations are reversible
- [ ] Indexes are appropriate
- [ ] Foreign key constraints are used
- [ ] Connection pooling is configured
- [ ] Transactions are used correctly

### API Design
- [ ] RESTful conventions followed
- [ ] Consistent response formats
- [ ] Appropriate HTTP status codes
- [ ] Rate limiting considered
- [ ] Versioning strategy implemented

### Frontend (if applicable)
- [ ] Accessibility standards met
- [ ] Performance optimized (bundle size, loading)
- [ ] Browser compatibility considered
- [ ] Responsive design implemented
- [ ] Error states handled gracefully

## Review Process

### Reviewer Guidelines
- [ ] Provide constructive feedback
- [ ] Explain reasoning behind suggestions
- [ ] Prioritize feedback (must-fix vs. suggestions)
- [ ] Check out and test complex changes
- [ ] Acknowledge good practices

### Author Guidelines
- [ ] Respond to all feedback
- [ ] Ask for clarification when needed
- [ ] Make requested changes promptly
- [ ] Test changes after addressing feedback
- [ ] Thank reviewers for their time

## Common Issues to Watch For

### Logic Issues
- [ ] Off-by-one errors
- [ ] Race conditions in concurrent code
- [ ] Null pointer exceptions
- [ ] Integer overflow/underflow
- [ ] Infinite loops or recursion

### Anti-Patterns
- [ ] God objects/functions
- [ ] Tight coupling
- [ ] Magic numbers/strings
- [ ] Premature optimization
- [ ] Copy-paste programming

## Final Checklist
- [ ] All automated checks pass
- [ ] Performance impact is acceptable
- [ ] Security implications are considered
- [ ] Backward compatibility is maintained
- [ ] Deployment considerations are addressed
- [ ] Monitoring/alerting is updated if needed

## Severity Levels
- **Critical**: Security issues, data corruption risks
- **Major**: Functionality broken, performance issues
- **Minor**: Style issues, small improvements
- **Suggestion**: Nice-to-have improvements

Remember: The goal is to maintain high code quality while fostering a collaborative learning environment.
