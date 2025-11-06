# ACE Connection Logger - Test Suite Documentation

## Overview

This test suite provides comprehensive coverage for the ACE Connection Logger, ensuring reliability, correctness, and production-readiness.

## Test Structure

```
tests/
├── __init__.py              # Test package initialization
├── conftest.py              # Pytest fixtures and configuration
├── test_ping.py             # Unit tests for ping functionality
├── test_database.py         # Unit tests for database operations
├── test_statistics.py       # Unit tests for statistics calculations
├── test_config.py           # Unit tests for configuration loading
├── test_cleanup.py          # Integration tests for cleanup job
├── test_integration.py      # End-to-end and edge case tests
└── README.md                # This file
```

## Test Categories

### Unit Tests

#### Ping Functionality (`test_ping.py`)
- Successful pings with various latencies
- Failed pings (timeouts, unreachable hosts)
- Partial success scenarios with packet loss
- Host validation (IPv4, IPv6, domains)
- Ping count variations
- Timeout settings
- Network error handling
- Latency calculation accuracy
- DNS resolution
- Concurrent ping execution

#### Database Operations (`test_database.py`)
- Schema creation and validation
- CRUD operations (Create, Read, Update, Delete)
- Query performance with indexes
- Data integrity constraints
- Transaction handling (commit/rollback)
- Bulk insert performance
- Concurrent access
- NULL value handling
- Database size management
- Backup feasibility

#### Statistics Calculations (`test_statistics.py`)
- Success rate calculations (0%, partial, 100%)
- Latency statistics (min, max, average)
- Aggregated statistics across hosts
- Time-based statistics (hourly, daily)
- Percentile calculations (50th, 90th, 95th, 99th)
- Moving averages
- Standard deviation and jitter
- Uptime/downtime calculations
- Trend analysis
- Reliability scoring

#### Configuration (`test_config.py`)
- Valid configuration loading
- Required field validation
- Invalid configuration handling
- Default configuration generation
- Host format validation
- Range validation (ping count, timeout, retention)
- Environment variable overrides
- Configuration reloading
- Unicode support
- Path expansion

### Integration Tests

#### Cleanup Job (`test_cleanup.py`)
- Removal of records older than retention period
- Preservation of recent records
- Mixed-age record handling
- Various retention periods (1, 7, 30, 90, 365 days)
- Empty database handling
- Transaction rollback on errors
- Database vacuum after cleanup
- Performance with large datasets
- Database integrity maintenance
- Concurrent read operations during cleanup

#### End-to-End Workflows (`test_integration.py`)
- Complete monitoring cycle (ping → database → statistics)
- Multiple host monitoring
- Error recovery from failed pings
- Database connection resilience
- Concurrent read/write operations
- Statistics calculation on real data
- Cleanup integration with monitoring

#### Edge Cases and Failure Modes (`test_integration.py`)
- Empty host list
- Invalid host addresses
- Network timeouts
- Permission denied errors
- Database locked errors
- Extreme latency values (very high, zero, negative)
- Packet loss edge cases
- Timestamp edge cases (past, future)
- Database corruption detection
- Very long host names
- Unicode in host names
- Rapid succession pings
- Long-running monitoring simulation
- System clock changes
- Config changes during runtime
- Memory leak prevention

## Running Tests

### Run All Tests
```bash
pytest
```

### Run Specific Test Categories
```bash
# Unit tests only
pytest -m unit

# Integration tests only
pytest -m integration

# Specific component tests
pytest -m ping
pytest -m database
pytest -m stats
pytest -m config
pytest -m cleanup
```

### Run with Coverage
```bash
# Generate coverage report
pytest --cov=ace_connection_logger --cov-report=html

# View coverage report
open htmlcov/index.html
```

### Run Specific Test File
```bash
pytest tests/test_ping.py
pytest tests/test_database.py
pytest tests/test_statistics.py
pytest tests/test_config.py
pytest tests/test_cleanup.py
pytest tests/test_integration.py
```

### Run Specific Test Function
```bash
pytest tests/test_ping.py::TestPingFunctionality::test_successful_ping
pytest tests/test_database.py::TestDatabaseOperations::test_schema_creation
```

### Run Tests in Parallel
```bash
# Run tests across multiple CPU cores for faster execution
pytest -n auto
```

### Run with Verbose Output
```bash
pytest -v
pytest -vv  # Extra verbose
```

### Run Slow Tests Only
```bash
pytest -m slow
```

### Skip Slow Tests
```bash
pytest -m "not slow"
```

### Run with Output Capture Disabled
```bash
pytest -s
```

## Test Fixtures

### Database Fixtures
- `temp_db`: Temporary SQLite database file
- `db_connection`: Database connection with schema initialized
- `populated_db`: Database pre-populated with sample data

### Data Fixtures
- `sample_ping_data`: Recent ping result data
- `old_ping_data`: Ping results older than 90 days

### Mock Fixtures
- `mock_ping_response`: Successful ping response
- `mock_failed_ping_response`: Failed ping response
- `mock_partial_ping_response`: Partial success ping response
- `mock_streamlit`: Mocked Streamlit components

### Configuration Fixtures
- `temp_config_file`: Valid temporary configuration file
- `invalid_config_file`: Invalid configuration for negative testing

### Utility Fixtures
- `reset_environment`: Resets environment variables between tests
- `capture_logs`: Enhanced log capturing

## Test Markers

Configure test execution with markers:

- `@pytest.mark.unit`: Unit tests for individual components
- `@pytest.mark.integration`: Integration tests for component interactions
- `@pytest.mark.slow`: Tests that take significant time
- `@pytest.mark.network`: Tests requiring network access
- `@pytest.mark.database`: Database-related tests
- `@pytest.mark.cleanup`: Cleanup job tests
- `@pytest.mark.config`: Configuration tests
- `@pytest.mark.ping`: Ping functionality tests
- `@pytest.mark.stats`: Statistics calculation tests
- `@pytest.mark.dashboard`: Dashboard component tests

## Coverage Goals

- **Target Coverage**: 80% minimum
- **Critical Components**: 90%+ coverage
  - Database operations
  - Ping functionality
  - Statistics calculations
  - Configuration loading

## Continuous Integration

### GitHub Actions Example
```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.13'

    - name: Install dependencies
      run: |
        pip install uv
        uv sync --group dev

    - name: Run tests
      run: |
        pytest --cov --cov-report=xml

    - name: Upload coverage
      uses: codecov/codecov-action@v3
```

## Test Best Practices

### 1. Test Independence
- Each test should be independent and not rely on other tests
- Use fixtures to set up test data
- Clean up after tests complete

### 2. Descriptive Test Names
- Test names should clearly describe what is being tested
- Use `test_<scenario>_<expected_result>` format

### 3. Arrange-Act-Assert Pattern
```python
def test_example():
    # Arrange: Set up test data
    input_data = prepare_test_data()

    # Act: Execute the code being tested
    result = function_under_test(input_data)

    # Assert: Verify the results
    assert result == expected_value
```

### 4. Parametrized Tests
Use `@pytest.mark.parametrize` for testing multiple scenarios:
```python
@pytest.mark.parametrize("input,expected", [
    (10, 100),
    (5, 50),
    (0, 0),
])
def test_calculation(input, expected):
    assert calculate(input) == expected
```

### 5. Mock External Dependencies
- Mock network calls to avoid flaky tests
- Mock file system operations for consistency
- Use fixtures for reusable mocks

### 6. Test Edge Cases
- Empty inputs
- Null/None values
- Boundary conditions
- Error conditions
- Maximum/minimum values

## Troubleshooting

### Tests Fail Due to Database Locks
- Increase timeout in conftest.py
- Ensure proper cleanup of database connections
- Use separate database files for concurrent tests

### Tests Fail Due to Timing Issues
- Use `@pytest.mark.slow` for time-sensitive tests
- Increase timeouts where appropriate
- Avoid relying on exact timing

### Coverage Not Reaching Target
- Identify uncovered code with `pytest --cov --cov-report=term-missing`
- Add tests for error paths
- Test edge cases and boundary conditions

### Flaky Tests
- Remove dependencies on external services
- Mock time-dependent operations
- Ensure test independence
- Use proper fixtures for setup/teardown

## Adding New Tests

When adding new functionality:

1. **Write tests first** (TDD approach recommended)
2. **Choose appropriate test category** (unit vs integration)
3. **Add descriptive markers** for easy filtering
4. **Update this documentation** if adding new test files
5. **Ensure tests are independent** and can run in any order
6. **Mock external dependencies** (network, file system)
7. **Add parametrized tests** for multiple scenarios
8. **Test edge cases** and error conditions

## Performance Testing

For performance-critical components:

```bash
# Run with timing information
pytest --durations=10

# Profile test execution
pytest --profile

# Run only slow tests to identify bottlenecks
pytest -m slow --durations=0
```

## Test Data

Test data is generated using fixtures in `conftest.py`. To add new test data:

1. Create a fixture in `conftest.py`
2. Document the fixture's purpose
3. Use the fixture in your tests
4. Ensure proper cleanup

## Validation Checklist

Before marking testing complete:

- [ ] All test files created
- [ ] All critical paths covered
- [ ] Edge cases tested
- [ ] Error handling validated
- [ ] Mock strategies implemented
- [ ] Integration tests passing
- [ ] Coverage target met (80%+)
- [ ] No flaky tests
- [ ] Tests run in CI/CD
- [ ] Documentation updated

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Pytest Fixtures](https://docs.pytest.org/en/stable/fixture.html)
- [Pytest Parametrization](https://docs.pytest.org/en/stable/parametrize.html)
- [Pytest Coverage](https://pytest-cov.readthedocs.io/)
- [Python unittest.mock](https://docs.python.org/3/library/unittest.mock.html)

## Support

For questions or issues with tests:
1. Check this documentation
2. Review existing test examples
3. Consult pytest documentation
4. Open an issue on the project repository
