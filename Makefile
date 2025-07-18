# Makefile for Make It Heavy Testing
# Provides convenient commands for running tests with various configurations

.PHONY: help test test-unit test-integration test-e2e test-coverage test-parallel test-watch test-mutation clean install-test-deps

# Default target
help:
	@echo "Make It Heavy Test Suite Commands:"
	@echo ""
	@echo "Setup:"
	@echo "  install-test-deps    Install testing dependencies"
	@echo ""
	@echo "Test Execution:"
	@echo "  test                 Run all tests"
	@echo "  test-unit            Run unit tests only"
	@echo "  test-integration     Run integration tests only"
	@echo "  test-e2e             Run end-to-end tests only"
	@echo "  test-fast            Run fast tests (unit + some integration)"
	@echo "  test-slow            Run slow tests (e2e + performance)"
	@echo ""
	@echo "Coverage & Reports:"
	@echo "  test-coverage        Run tests with coverage report"
	@echo "  coverage-html        Generate HTML coverage report"
	@echo "  coverage-report      Show coverage report in terminal"
	@echo ""
	@echo "Parallel & Performance:"
	@echo "  test-parallel        Run tests in parallel"
	@echo "  test-parallel-fast   Run fast tests in parallel"
	@echo ""
	@echo "Continuous Testing:"
	@echo "  test-watch           Run tests in watch mode"
	@echo "  test-watch-unit      Watch unit tests only"
	@echo ""
	@echo "Quality & Mutation:"
	@echo "  test-mutation        Run mutation testing"
	@echo "  test-quality         Run quality checks + tests"
	@echo ""
	@echo "Cleanup:"
	@echo "  clean                Clean test artifacts"

# Install testing dependencies
install-test-deps:
	pip install -r requirements-test.txt

# Basic test commands
test:
	pytest

test-unit:
	pytest tests/unit/ -v

test-integration:
	pytest tests/integration/ -v

test-e2e:
	pytest tests/e2e/ -v

test-fast:
	pytest -m "not slow" -v

test-slow:
	pytest -m "slow" -v

# Coverage commands
test-coverage:
	pytest --cov=. --cov-report=html --cov-report=term-missing

coverage-html:
	pytest --cov=. --cov-report=html
	@echo "HTML coverage report generated in htmlcov/"

coverage-report:
	pytest --cov=. --cov-report=term-missing --cov-report=term

# Parallel execution
test-parallel:
	pytest -n auto

test-parallel-fast:
	pytest -n auto -m "not slow"

test-parallel-unit:
	pytest tests/unit/ -n auto

test-parallel-integration:
	pytest tests/integration/ -n auto

# Watch mode
test-watch:
	ptw --runner "pytest --tb=short"

test-watch-unit:
	ptw tests/unit/ --runner "pytest --tb=short"

test-watch-fast:
	ptw --runner "pytest -m 'not slow' --tb=short"

# Mutation testing
test-mutation:
	mutmut run --paths-to-mutate=agent.py,orchestrator.py,utils.py
	mutmut results

# Quality checks
test-quality: test-coverage
	@echo "Running additional quality checks..."
	pytest --tb=short --maxfail=5

# Specific test categories
test-api:
	pytest -m "api" -v

test-mock:
	pytest -m "mock" -v

test-smoke:
	pytest -m "smoke" -v

# Performance testing
test-performance:
	pytest -m "slow" --tb=short

# Debugging
test-debug:
	pytest -v -s --tb=long --maxfail=1

test-debug-unit:
	pytest tests/unit/ -v -s --tb=long --maxfail=1

# Clean up
clean:
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf *.coverage
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -type d -exec rm -rf {} +

# Reporting
test-html-report:
	pytest --html=reports/test_report.html --self-contained-html

# CI/CD friendly commands
ci-test:
	pytest --tb=short --maxfail=10 --durations=10

ci-test-with-coverage:
	pytest --cov=. --cov-report=xml --cov-report=term --tb=short

# Development workflow
dev-test: clean test-fast

dev-test-watch: clean test-watch-fast

# Full test suite (for releases)
full-test: clean test-coverage test-mutation

# Quick smoke test
smoke: test-smoke test-parallel-unit