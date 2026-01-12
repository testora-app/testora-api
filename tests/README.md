# Testora API - Comprehensive E2E Test Suite

## Overview
This directory contains comprehensive end-to-end (e2e) tests for the Testora Flask API application covering **ALL 95 active routes**.

## Test Coverage Summary

### ✅ Complete Route Coverage: 95/95 (100%)

| Module | Routes | Tests | Test File |
|--------|--------|-------|-----------|
| Main Routes | 4 | 27 | `test_main_routes.py` |
| App Admin | 20 | 49 | `test_app_admin_routes.py` |
| School | 1 | 10 | `test_school_routes.py` |
| Notifications | 5 | 30 | `test_notifications_routes.py` |
| Staff | 10 | 47 | `test_staff_routes.py` |
| Student | 17 | 40+ | `test_student_routes.py` |
| Subscriptions | 10 | 35+ | `test_subscriptions_routes.py` |
| Test/Questions | 9 | 30+ | `test_test_routes.py` |
| Analytics | 25 | 50+ | `test_analytics_routes.py` |
| **TOTAL** | **95** | **318+** | **9 files** |

## Test Infrastructure

### Fixtures (conftest.py)
Comprehensive fixtures providing:
- **App & Database**: SQLite in-memory database with automatic setup/teardown
- **Authentication**: Token fixtures for all user types (admin, school_admin, staff, student)
- **Test Data**: Pre-populated fixtures for users, schools, subjects, topics, questions, tests, notifications, billing
- **Mocked Services**: External services (Mailer, Pusher, Paystack) are mocked
- **Utility Fixtures**: JSON content types, headers, etc.

### Test Coverage Areas
Each route is tested for:
- ✅ **Happy Path**: Valid requests with expected successful responses
- ✅ **Authentication**: Valid/invalid/expired/missing tokens
- ✅ **Authorization**: Wrong user type attempting access
- ✅ **Input Validation**: Missing fields, invalid formats, empty values
- ✅ **Edge Cases**: Boundary conditions, nonexistent IDs, duplicate data
- ✅ **Error Responses**: Proper 400, 401, 403, 404 status codes
- ✅ **Business Logic**: Data integrity, state management

## Installation

```bash
# Install test dependencies
pip install pytest pytest-cov

# Or install from requirements.txt
pip install -r requirements.txt
```

## Running Tests

### Run All Tests
```bash
pytest tests/
```

### Run Specific Test File
```bash
pytest tests/test_main_routes.py
pytest tests/test_staff_routes.py
pytest tests/test_analytics_routes.py
```

### Run Specific Test Class
```bash
pytest tests/test_main_routes.py::TestContactUsRoute
pytest tests/test_staff_routes.py::TestStaffAuthentication
```

### Run Specific Test
```bash
pytest tests/test_main_routes.py::TestContactUsRoute::test_post_contact_us_with_valid_data
```

### Run with Verbose Output
```bash
pytest -v tests/
```

### Run with Coverage Report
```bash
# Generate coverage report
pytest --cov=app tests/

# Generate HTML coverage report
pytest --cov=app --cov-report=html tests/

# View coverage report
open htmlcov/index.html
```

### Run Tests Matching Pattern
```bash
# Run all authentication tests
pytest -k "authenticate" tests/

# Run all validation tests
pytest -k "validation" tests/

# Run all tests for a specific route
pytest -k "contact_us" tests/
```

### Run Tests with Output
```bash
# Show print statements
pytest -s tests/

# Show test output and disable warnings
pytest -s -W ignore tests/
```

## Test File Structure

### Main Routes (test_main_routes.py)
- `GET /` - Health check
- `POST /contact-us/` - Contact form
- `POST /account/reset-password/` - Password reset
- `POST /account/change-password/` - Password change

### App Admin Routes (test_app_admin_routes.py)
- Admin management (create, authenticate)
- Curriculum management
- Subject CRUD operations
- Theme CRUD operations
- Topic CRUD operations

### School Routes (test_school_routes.py)
- School listing (admin only)

### Notifications Routes (test_notifications_routes.py)
- Notification retrieval
- Mark notifications as read
- Device ID registration
- Test notifications

### Staff Routes (test_staff_routes.py)
- School admin registration
- Staff registration
- Staff authentication
- Staff approval/unapproval
- Staff management (list, details, edit)
- Dashboard analytics

### Student Routes (test_student_routes.py)
- Student registration
- Student authentication
- Student approval/unapproval
- Student management
- Batch management
- Subject levels
- Student dashboard analytics

### Subscriptions Routes (test_subscriptions_routes.py)
- Billing history (CRUD)
- Subscription creation
- Payment initiation
- Payment confirmation
- Paystack webhooks
- Billing process

### Test/Question Routes (test_test_routes.py)
- Question CRUD operations
- Question flagging
- Test creation
- Test submission/marking
- Subject performance

### Analytics Routes (test_analytics_routes.py)
- School/staff analytics (9 endpoints)
- Student-specific analytics (6 endpoints)
- New student dashboard (5 endpoints)
- Legacy analytics (5 endpoints)

## Continuous Integration

### GitHub Actions Example
```yaml
name: Run Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-cov
    
    - name: Run tests with coverage
      run: |
        pytest --cov=app tests/
    
    - name: Upload coverage reports
      uses: codecov/codecov-action@v3
```

## Troubleshooting

### Common Issues

**Issue**: Tests failing with database errors
```bash
# Solution: Ensure clean test database
pytest tests/ --tb=short
```

**Issue**: Import errors
```bash
# Solution: Install all dependencies
pip install -r requirements.txt
```

**Issue**: Fixtures not found
```bash
# Solution: Ensure conftest.py is in tests directory
ls tests/conftest.py
```

**Issue**: Mock services not working
```bash
# Solution: Check that external services are properly mocked in conftest.py
pytest tests/ -v --tb=short
```

## Best Practices

### Writing New Tests
1. Follow existing test patterns
2. Use descriptive test names: `test_<method>_<endpoint>_<scenario>`
3. Include docstrings explaining what each test validates
4. Use appropriate fixtures from conftest.py
5. Test both success and failure cases
6. Verify response status codes and data structure

### Example Test Structure
```python
def test_post_endpoint_with_valid_data(self, client, auth_headers):
    """Test POST /endpoint/ creates resource with valid data."""
    payload = {
        "data": {
            "field": "value"
        }
    }
    
    response = client.post(
        '/endpoint/',
        data=json.dumps(payload),
        content_type='application/json',
        headers=auth_headers
    )
    
    assert response.status_code == 201
    data = json.loads(response.data)
    assert data['data']['field'] == 'value'
```

## Maintenance

### Adding New Routes
1. Identify the new route and its module
2. Add fixtures for any new models in `conftest.py`
3. Create tests in the appropriate test file
4. Ensure coverage for all scenarios
5. Update this README with new route counts

### Updating Existing Tests
1. Maintain existing test patterns
2. Update fixtures if models change
3. Ensure backward compatibility
4. Run full test suite after changes

## Documentation

For more information about the API routes, see:
- API Documentation: [Link to API docs]
- Route Discovery: See individual test files for route details
- Flask APIFlask Documentation: https://apiflask.com/

## Contributing

When adding new tests:
1. Follow the existing structure and naming conventions
2. Ensure comprehensive coverage (happy path, auth, validation, edge cases)
3. Use appropriate fixtures and mocks
4. Add clear docstrings
5. Run tests locally before committing
6. Update this README if adding new test files

## License

[Your License Here]
