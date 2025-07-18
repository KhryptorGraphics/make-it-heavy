# Make It Heavy Test Suite

Comprehensive testing framework for the Make It Heavy multi-agent AI system.

## Overview

This test suite provides complete coverage of the Make It Heavy codebase with:
- **Unit Tests**: Individual component testing with mocking
- **Integration Tests**: Component interaction and workflow testing  
- **End-to-End Tests**: Complete user scenario testing
- **Coverage Analysis**: Code coverage reporting and enforcement
- **Parallel Execution**: Fast test execution with pytest-xdist
- **Mutation Testing**: Test quality verification with mutmut
- **Continuous Testing**: Watch mode for development

## Quick Start

### Install Test Dependencies
```bash
pip install -r requirements-test.txt
```

### Run All Tests
```bash
pytest
# or
make test
```

### Run Specific Test Types
```bash
# Unit tests only
pytest tests/unit/
make test-unit

# Integration tests
pytest tests/integration/
make test-integration

# End-to-end tests
pytest tests/e2e/
make test-e2e
```

### Coverage Analysis
```bash
# Generate coverage report
pytest --cov=. --cov-report=html
make test-coverage

# View HTML report
open htmlcov/index.html
```

## Test Organization

```
tests/
├── conftest.py              # Global test configuration
├── fixtures/                # Test data and fixtures
│   └── sample_data.py       # Sample data for tests
├── unit/                    # Unit tests
│   ├── test_agent.py        # Agent class tests
│   ├── test_orchestrator.py # Orchestrator tests
│   ├── test_tools.py        # Tool system tests
│   └── test_utils.py        # Utility function tests
├── integration/             # Integration tests
│   └── test_agent_orchestrator_integration.py
└── e2e/                     # End-to-end tests
    └── test_complete_workflows.py
```

## Test Categories

### Unit Tests (`tests/unit/`)
- **Scope**: Individual functions and classes
- **Dependencies**: Heavily mocked
- **Speed**: Fast (~1-5s total)
- **Coverage**: High (90%+ target)

Example:
```python
def test_agent_initialization(temp_config_file, mock_ui_manager):
    agent = OpenRouterAgent(
        config_path=temp_config_file,
        ui_manager=mock_ui_manager
    )
    assert agent.agent_id is not None
```

### Integration Tests (`tests/integration/`)
- **Scope**: Component interactions
- **Dependencies**: Real classes, mocked external services
- **Speed**: Medium (~10-30s total)
- **Coverage**: Component boundaries

Example:
```python
@pytest.mark.integration
def test_agent_orchestrator_workflow(temp_config_file):
    orchestrator = TaskOrchestrator(config_path=temp_config_file)
    result = orchestrator.orchestrate("Test query")
    assert result is not None
```

### End-to-End Tests (`tests/e2e/`)
- **Scope**: Complete user workflows
- **Dependencies**: Full system integration
- **Speed**: Slow (~30s-2min total)
- **Coverage**: Critical user paths

Example:
```python
@pytest.mark.e2e
def test_complete_user_workflow(test_config):
    cli = EnhancedMakeItHeavyCLI()
    # Test complete workflow from user input to output
```

## Advanced Testing Features

### Parallel Execution
```bash
# Run tests in parallel (auto-detect CPU cores)
pytest -n auto

# Run with specific number of workers
pytest -n 4

# Parallel unit tests only
make test-parallel-unit
```

### Watch Mode (Continuous Testing)
```bash
# Watch all files
python scripts/test_runner.py --watch

# Watch unit tests only
python scripts/test_runner.py --watch --watch-type unit

# Using pytest-watch
ptw tests/unit/
```

### Mutation Testing
```bash
# Run mutation testing
python scripts/test_runner.py --mutation

# Or using mutmut directly
mutmut run --paths-to-mutate agent.py,orchestrator.py
mutmut results
```

### Coverage Targets
- **Statements**: 80%+ (enforced)
- **Branches**: 75%+
- **Functions**: 90%+
- **Lines**: 80%+

### Test Markers
```bash
# Run fast tests only
pytest -m "not slow"

# Run integration tests
pytest -m integration

# Run API tests (with real API calls)
pytest -m api

# Run smoke tests
pytest -m smoke
```

## Configuration

### pytest.ini
```ini
[tool:pytest]
testpaths = tests
addopts = 
    --verbose
    --cov=.
    --cov-report=html
    --cov-fail-under=80
```

### Coverage Configuration
```ini
[coverage:run]
source = .
omit = 
    tests/*
    .venv/*
    
[coverage:report]
exclude_lines =
    pragma: no cover
    def __repr__
```

## Fixtures and Test Data

### Global Fixtures (`conftest.py`)
- `test_config`: Standard test configuration
- `temp_config_file`: Temporary config file
- `mock_openai_client`: Mocked OpenAI client
- `mock_ui_manager`: Mocked UI manager
- `sample_user_input`: Standard test input

### Sample Data (`fixtures/sample_data.py`)
- User inputs for various scenarios
- API response examples
- Tool execution results
- Error scenarios
- Performance test data

Example usage:
```python
def test_agent_with_sample_data(sample_user_input, mock_openai_client):
    agent = OpenRouterAgent()
    result = agent.run(sample_user_input)
    assert result is not None
```

## CI/CD Integration

### GitHub Actions (`.github/workflows/tests.yml`)
- Tests on Python 3.8, 3.9, 3.10, 3.11
- Unit, integration, and e2e test phases
- Coverage reporting to Codecov
- Parallel execution for speed
- Mutation testing on main branch

### Local CI Simulation
```bash
# Run CI-style tests
python scripts/test_runner.py --ci

# Quality checks
make test-quality
```

## Development Workflow

### TDD (Test-Driven Development)
```bash
# 1. Write failing test
pytest tests/unit/test_new_feature.py::test_new_function -v

# 2. Implement minimum code to pass
# ... implement feature ...

# 3. Run tests and refactor
pytest tests/unit/test_new_feature.py -v
```

### Pre-commit Testing
```bash
# Quick smoke test before committing
make smoke

# Full test suite before pushing
make full-test
```

### Debugging Tests
```bash
# Run with detailed output
pytest -v -s --tb=long

# Debug specific test
pytest tests/unit/test_agent.py::test_specific_function -v -s --pdb
```

## Test Commands Reference

### Make Commands
```bash
make test                 # Run all tests
make test-unit           # Unit tests only
make test-integration    # Integration tests only
make test-e2e           # End-to-end tests only
make test-coverage      # Coverage analysis
make test-parallel      # Parallel execution
make test-watch         # Watch mode
make test-mutation      # Mutation testing
make clean             # Clean test artifacts
```

### Python Script Commands
```bash
# Advanced test runner
python scripts/test_runner.py --help
python scripts/test_runner.py --unit --parallel
python scripts/test_runner.py --watch --watch-type fast
python scripts/test_runner.py --mutation
python scripts/test_runner.py --ci
```

### Direct pytest Commands
```bash
pytest                          # All tests
pytest tests/unit/             # Unit tests
pytest -k "test_agent"         # Tests matching pattern
pytest --cov=agent.py          # Coverage for specific file
pytest -x                      # Stop on first failure
pytest --lf                    # Last failed tests only
pytest --ff                    # Failed first
```

## Performance Benchmarks

### Target Execution Times
- **Unit Tests**: <10 seconds total
- **Integration Tests**: <30 seconds total
- **E2E Tests**: <2 minutes total
- **Full Suite**: <5 minutes total

### Optimization Tips
- Use `pytest -n auto` for parallel execution
- Run unit tests during development
- Use `pytest -x` to stop on first failure
- Cache fixtures with appropriate scope
- Mock external dependencies in unit tests

## Troubleshooting

### Common Issues
1. **Import Errors**: Ensure all dependencies installed
2. **Slow Tests**: Use parallel execution (`-n auto`)
3. **Flaky Tests**: Check for race conditions or timing issues
4. **Coverage Issues**: Verify all code paths are tested

### Debug Commands
```bash
# Collect tests without running
pytest --collect-only

# Show test dependency tree
pytest --fixtures

# Verbose output with timing
pytest -v --durations=10
```

## Contributing

### Adding New Tests
1. Choose appropriate test type (unit/integration/e2e)
2. Use existing fixtures when possible
3. Follow naming conventions (`test_*.py`)
4. Add appropriate markers
5. Ensure coverage targets are met

### Test Guidelines
- One assertion per test when possible
- Use descriptive test names
- Mock external dependencies
- Test both success and failure cases
- Include performance tests for critical paths

## Resources

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-cov Coverage](https://pytest-cov.readthedocs.io/)
- [mutmut Mutation Testing](https://mutmut.readthedocs.io/)
- [pytest-xdist Parallel Testing](https://pytest-xdist.readthedocs.io/)