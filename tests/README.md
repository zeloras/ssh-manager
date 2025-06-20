# SSH Profile Manager Test Suite

This directory contains a comprehensive test suite for the SSH Profile Manager project, providing thorough coverage of all components including CLI, GUI, and core functionality.

## 📋 Test Structure

```
tests/
├── __init__.py                 # Test package initialization
├── conftest.py                 # Shared fixtures and configuration
├── test_ssh_profile.py         # SSHProfile class unit tests
├── test_ssh_manager.py         # SSHManager class unit tests
├── test_cli.py                 # Command-line interface tests
├── test_integration.py         # Integration and end-to-end tests
├── data/                       # Test data files
│   ├── sample_profiles.json    # Sample profile configurations
│   └── corrupted_profiles.json # Corrupted data for error testing
└── fixtures/                   # Test fixtures (auto-generated)
```

## 🧪 Test Categories

### Unit Tests
- **test_ssh_profile.py**: Tests for the `SSHProfile` class
  - Profile creation and initialization
  - Data serialization/deserialization
  - SSH command generation
  - Edge cases and validation

- **test_ssh_manager.py**: Tests for the `SSHManager` class
  - Profile management (CRUD operations)
  - File I/O operations
  - Search functionality
  - Statistics and reporting

### Integration Tests
- **test_integration.py**: End-to-end workflow testing
  - Complete profile lifecycle
  - File system integration
  - CLI-to-manager integration
  - Data persistence and consistency

### CLI Tests
- **test_cli.py**: Command-line interface testing
  - Argument parsing
  - Command execution
  - Error handling
  - Output formatting

## 🚀 Running Tests

### Quick Start
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=ssh_manager --cov=ssh_gui --cov-report=html

# Run specific test categories
pytest tests/test_ssh_profile.py  # Unit tests only
pytest tests/test_integration.py  # Integration tests only
```

### Using the Test Runner
```bash
# Comprehensive test runner
python run_tests.py

# Quick tests (unit + lint)
python run_tests.py --fast

# Full test suite
python run_tests.py --full

# CI/CD pipeline tests
python run_tests.py --ci
```

### Using Make Commands
```bash
make test           # Run all tests
make test-unit      # Unit tests only
make test-coverage  # Tests with coverage
make test-performance  # Performance tests
```

### Using Tox (Multiple Python Versions)
```bash
tox                 # Test on all Python versions
tox -e py311        # Test on Python 3.11 only
tox -e lint         # Run linting only
tox -e coverage     # Coverage testing
```

## 📊 Test Coverage

Our test suite maintains **85%+ code coverage** across all modules:

- **ssh_manager.py**: 90%+ coverage
- **ssh_gui.py**: 85%+ coverage
- **Integration scenarios**: 95%+ coverage

### Coverage Reports
```bash
# Generate HTML coverage report
pytest --cov=ssh_manager --cov=ssh_gui --cov-report=html

# View coverage report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

## 🔍 Test Markers

Tests are organized using pytest markers:

```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Run CLI-specific tests
pytest -m cli

# Run GUI-specific tests
pytest -m gui

# Skip slow tests
pytest -m "not slow"

# Run only performance tests
pytest -m slow --benchmark-only
```

Available markers:
- `unit`: Unit tests
- `integration`: Integration tests
- `cli`: Command line interface tests
- `gui`: GUI interface tests
- `slow`: Slow running tests
- `network`: Tests requiring network access

## 🛠️ Test Fixtures

Common test fixtures are defined in `conftest.py`:

### Temporary Files
- `temp_dir`: Temporary directory for test files
- `temp_config_file`: Temporary configuration file
- `temp_ssh_dir`: Mock SSH directory structure

### Sample Data
- `sample_profile_data`: Sample profile dictionary
- `sample_profile`: Sample SSHProfile instance
- `multiple_profiles_data`: Multiple profiles for testing
- `populated_config_file`: Pre-populated configuration file

### Managers
- `empty_ssh_manager`: Fresh SSHManager instance
- `populated_ssh_manager`: SSHManager with sample profiles

### Mocks
- `mock_subprocess`: Mocked subprocess for SSH execution
- `mock_datetime`: Fixed datetime for consistent timestamps
- `mock_home_dir`: Mocked home directory

## 📝 Writing New Tests

### Test Organization
```python
class TestFeatureName:
    """Test class for specific feature."""
    
    def test_basic_functionality(self):
        """Test basic functionality."""
        pass
    
    def test_edge_cases(self):
        """Test edge cases and error conditions."""
        pass
    
    def test_error_handling(self):
        """Test error handling."""
        pass
```

### Using Fixtures
```python
def test_with_fixtures(self, empty_ssh_manager, sample_profile):
    """Example test using fixtures."""
    empty_ssh_manager.add_profile_from_dict(sample_profile.to_dict())
    assert len(empty_ssh_manager.profiles) == 1
```

### Testing Patterns
```python
# Testing file operations
def test_file_operations(self, temp_config_file):
    manager = SSHManager(temp_config_file)
    # Test file operations...

# Testing CLI commands
def test_cli_command(self):
    with patch('sys.argv', ['ssh-manager', 'list']):
        with patch('ssh_manager.SSHManager') as mock_manager:
            main()
            mock_manager.return_value.list_profiles.assert_called_once()

# Testing error conditions
def test_error_handling(self):
    with pytest.raises(ValueError):
        # Code that should raise ValueError
        pass
```

## 🎯 Test Data

### Sample Profiles
The `tests/data/sample_profiles.json` file contains:
- 10 diverse profile configurations
- Different authentication methods
- Various port configurations
- Unicode character support
- Legacy system examples

### Corrupted Data
The `tests/data/corrupted_profiles.json` file contains:
- Invalid JSON syntax
- Missing required fields
- Invalid data types
- Duplicate keys

## 🔧 Configuration

### pytest.ini
Main pytest configuration with:
- Test discovery patterns
- Coverage settings
- Marker definitions
- Warning filters

### .coveragerc
Coverage configuration with:
- Source inclusion/exclusion
- Branch coverage
- Report formatting
- Minimum coverage thresholds

### tox.ini
Multi-environment testing with:
- Python version matrix
- Dependency management
- Environment-specific commands

## 🚦 Continuous Integration

### GitHub Actions
Tests run automatically on:
- Push to main/develop branches
- Pull requests
- Release tags

Test matrix includes:
- Python 3.8, 3.9, 3.10, 3.11, 3.12
- Ubuntu, macOS, Windows
- Various test categories

### Pre-commit Hooks
Automated checks before commits:
- Code formatting (black, isort)
- Linting (flake8, mypy)
- Security (bandit, safety)
- Basic test execution

## 📈 Performance Testing

Performance tests use pytest-benchmark:

```bash
# Run performance tests
pytest -m slow --benchmark-only

# Generate benchmark report
pytest --benchmark-json=benchmark.json
```

Benchmarks cover:
- Profile loading/saving performance
- Search operation speed
- Large dataset handling
- Memory usage patterns

## 🐛 Debugging Tests

### Verbose Output
```bash
pytest -v --tb=long  # Detailed output
pytest -s           # Don't capture stdout
pytest --lf         # Run last failed tests only
pytest --pdb        # Drop into debugger on failure
```

### Test-specific Debugging
```python
import pytest

def test_with_debugging():
    # Set breakpoint
    pytest.set_trace()
    
    # Or use regular debugging
    import pdb; pdb.set_trace()
```

## 📚 Best Practices

### Test Naming
- Use descriptive test names: `test_add_profile_with_custom_port`
- Group related tests in classes: `TestSSHProfileSerialization`
- Use consistent naming patterns

### Test Structure
- **Arrange**: Set up test data and conditions
- **Act**: Execute the code being tested
- **Assert**: Verify the results

### Fixtures
- Use fixtures for common setup
- Keep fixtures focused and reusable
- Use appropriate fixture scopes

### Mocking
- Mock external dependencies (subprocess, file system)
- Use `patch` for temporary mocking
- Mock at the right level (not too deep)

### Error Testing
- Test both success and failure paths
- Use `pytest.raises` for expected exceptions
- Test edge cases and boundary conditions

## 🔍 Troubleshooting

### Common Issues

**Import Errors**
```bash
# Add project root to Python path
export PYTHONPATH=$PWD:$PYTHONPATH
pytest
```

**Fixture Not Found**
- Check `conftest.py` is in the right location
- Verify fixture scope and dependencies

**Coverage Issues**
- Ensure source paths are correct in configuration
- Check file patterns in coverage exclusions

**Performance Test Failures**
- Performance tests may be sensitive to system load
- Run on dedicated hardware for consistent results

### Getting Help

1. Check test output for specific error messages
2. Run tests with `-v` flag for detailed output
3. Use `--tb=long` for full tracebacks
4. Check GitHub Issues for known problems
5. Review test documentation and examples

## 📋 Maintenance

### Adding New Tests
1. Create test file following naming conventions
2. Add appropriate markers
3. Update this README if adding new categories
4. Ensure tests pass in CI/CD pipeline

### Updating Test Data
1. Update `tests/data/` files as needed
2. Regenerate fixtures if data structure changes
3. Update corresponding tests
4. Verify all tests still pass

### Performance Monitoring
- Monitor test execution times
- Update performance baselines as needed
- Optimize slow tests when possible
- Consider parallel test execution for large suites

---

## 🎉 Contributing

When contributing tests:

1. **Follow the existing patterns** in test organization and naming
2. **Add appropriate markers** to categorize tests
3. **Include both positive and negative test cases**
4. **Mock external dependencies** appropriately
5. **Update documentation** for new test categories
6. **Ensure tests pass** in CI/CD pipeline

For questions or issues with the test suite, please:
- Check existing GitHub issues
- Run tests locally with verbose output
- Review test documentation and examples

Happy Testing! 🧪