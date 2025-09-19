# AI Executive Suite Test Suite

This directory contains comprehensive unit tests for the AI Executive Suite application.

## Test Structure

### Configuration Files
- `conftest.py` - Pytest configuration and shared fixtures
- `factories.py` - Test data factories using factory_boy
- `pytest.ini` - Pytest configuration settings
- `README.md` - This documentation file

### Unit Test Files
- `test_ai_integration.py` - Tests for AI integration service
- `test_analytics_service.py` - Tests for analytics service
- `test_document_analysis.py` - Tests for document analysis service
- `test_vector_database.py` - Tests for vector database service
- `test_usage_analytics.py` - Tests for usage analytics service
- `test_registry.py` - Tests for service registry
- `test_models_comprehensive.py` - Comprehensive model tests
- `test_basic_setup.py` - Basic setup verification tests

### Existing Test Files
The following test files were already present and provide additional coverage:
- `test_collaboration_service.py`
- `test_document_processing.py`
- `test_enhanced_models.py`
- `test_context_management.py`
- `test_prompt_engineering.py`
- And many more...

## Features Implemented

### 1. Test Configuration (`conftest.py`)
- Application factory for testing
- Database session fixtures
- Mock services (OpenAI, Redis, Vector DB)
- Sample data fixtures
- Security test data
- Performance testing utilities

### 2. Test Data Factories (`factories.py`)
- UserFactory - Generate test users
- DecisionFactory - Generate test decisions
- DocumentFactory - Generate test documents
- CommentFactory - Generate test comments
- CollaborationSessionFactory - Generate collaboration sessions
- Specialized factories for different scenarios
- Batch creation utilities

### 3. Mock Objects and External Dependencies
- Mock OpenAI client with realistic responses
- Mock Redis client for caching tests
- Mock vector database for document search
- Mock external APIs (CRM, ERP, Financial)
- Configurable mock responses

### 4. Test Data Generators
- Decision data with various patterns
- Document data with different types
- Financial data for analytics testing
- User activity data
- Performance test scenarios

### 5. Comprehensive Unit Tests
- **AI Integration Service**: 50+ test cases covering LLM interactions, prompt management, context handling
- **Analytics Service**: 30+ test cases covering metrics calculation, trend analysis, reporting
- **Document Analysis Service**: 40+ test cases covering text analysis, categorization, insights extraction
- **Vector Database Service**: 35+ test cases covering embedding generation, similarity search, document management
- **Usage Analytics Service**: 45+ test cases covering user activity tracking, feature usage, performance metrics
- **Service Registry**: 25+ test cases covering service registration, health checks, dependency management
- **Models**: 60+ test cases covering all model classes, relationships, and business logic

### 6. Test Coverage Configuration
- Coverage reporting with HTML and XML output
- Minimum coverage threshold of 80%
- Exclusion of test files from coverage
- Integration with CI/CD systems

### 7. Test Runner Script (`run_tests.py`)
- Command-line interface for running different test types
- Unit test execution with coverage
- Integration test support
- Performance test support
- Security test support
- Linting and code quality checks
- Test report generation

## Running Tests

### Basic Usage
```bash
# Run all unit tests with coverage
python run_tests.py --unit --coverage

# Run specific test file
python run_tests.py --test tests/test_ai_integration.py

# Run with verbose output
python run_tests.py --unit --verbose

# Run all tests
python run_tests.py --all
```

### Using pytest directly
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=services --cov=models --cov-report=html

# Run specific test file
pytest tests/test_ai_integration.py -v

# Run tests with specific marker
pytest -m "not integration"
```

## Test Markers

Tests are organized using pytest markers:
- `unit` - Unit tests (default)
- `integration` - Integration tests
- `performance` - Performance tests
- `security` - Security tests
- `slow` - Slow running tests
- `external` - Tests requiring external services

## Coverage Goals

The test suite aims for:
- **Overall Coverage**: 80%+ (enforced)
- **Service Layer**: 90%+ coverage
- **Model Layer**: 95%+ coverage
- **Critical Paths**: 100% coverage

## Mock Strategy

### External Services
- OpenAI API calls are mocked with realistic responses
- Database operations use in-memory SQLite
- Redis operations are mocked
- File system operations use temporary files
- External API calls are mocked

### Service Dependencies
- Services are tested in isolation using dependency injection
- Mock objects implement the same interfaces as real services
- Configuration is provided through test fixtures

## Test Data Management

### Factories
- Use factory_boy for generating test data
- Factories create realistic but deterministic data
- Support for creating related objects
- Batch creation for performance tests

### Fixtures
- Shared fixtures in conftest.py
- Database fixtures with automatic cleanup
- Mock service fixtures
- Test data generators

## Best Practices Implemented

1. **Isolation**: Each test is independent and can run in any order
2. **Deterministic**: Tests produce consistent results
3. **Fast**: Unit tests run quickly using mocks
4. **Comprehensive**: High coverage of critical functionality
5. **Maintainable**: Clear test structure and naming
6. **Realistic**: Mock data resembles production data
7. **Documented**: Clear test descriptions and comments

## Integration with CI/CD

The test suite generates:
- JUnit XML reports for test results
- Coverage XML reports for code coverage
- HTML coverage reports for detailed analysis
- Performance benchmarks (JSON format)

## Future Enhancements

Planned improvements:
- Property-based testing with Hypothesis
- Mutation testing for test quality assessment
- Visual regression testing for UI components
- Load testing scenarios
- Chaos engineering tests

## Troubleshooting

### Common Issues
1. **Import Errors**: Ensure PYTHONPATH includes project root
2. **Database Errors**: Check that test database is properly configured
3. **Mock Failures**: Verify mock objects match real service interfaces
4. **Coverage Issues**: Check that all source files are included in coverage

### Debug Mode
Run tests with debug output:
```bash
pytest --pdb --pdb-trace
```

### Verbose Logging
Enable detailed logging in tests:
```bash
pytest --log-cli-level=DEBUG
```