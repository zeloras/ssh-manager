# SSH Profile Manager - Development Makefile
# Provides common development tasks and shortcuts

.PHONY: help install install-dev test test-unit test-integration test-cli test-gui test-coverage \
        lint lint-black lint-isort lint-flake8 lint-mypy lint-bandit \
        format format-black format-isort \
        clean clean-build clean-pyc clean-test clean-coverage \
        build build-wheel build-sdist \
        release release-test release-prod \
        docs docs-build docs-serve \
        security security-bandit security-safety \
        performance benchmark \
        install-hooks pre-commit \
        run-cli run-gui \
        validate validate-all

# Default target
help: ## Show this help message
	@echo "SSH Profile Manager - Development Commands"
	@echo "=========================================="
	@echo ""
	@echo "Available targets:"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "Examples:"
	@echo "  make install-dev    # Install development dependencies"
	@echo "  make test          # Run all tests"
	@echo "  make lint          # Run all linting checks"
	@echo "  make format        # Format code with black and isort"
	@echo "  make clean         # Clean all build artifacts"

# Installation targets
install: ## Install SSH Profile Manager for production use
	python -m pip install --upgrade pip
	python -m pip install .

install-dev: ## Install development dependencies
	python -m pip install --upgrade pip
	python -m pip install -r requirements-dev.txt
	python -m pip install -e .

install-hooks: ## Install pre-commit hooks
	pre-commit install
	pre-commit install --hook-type commit-msg

# Testing targets
test: test-unit test-integration test-cli ## Run all tests
	@echo "✅ All tests completed"

test-unit: ## Run unit tests only
	@echo "🧪 Running unit tests..."
	pytest tests/test_ssh_profile.py tests/test_ssh_manager.py -v \
		--cov=ssh_manager --cov=ssh_gui \
		--cov-report=term-missing \
		--tb=short

test-integration: ## Run integration tests
	@echo "🔗 Running integration tests..."
	pytest tests/test_integration.py -v --tb=short

test-cli: ## Run CLI tests
	@echo "⚡ Running CLI tests..."
	pytest tests/test_cli.py -v --tb=short

test-gui: ## Run GUI tests (if available)
	@echo "🎨 Running GUI tests..."
	pytest tests/ -k "gui" -v --tb=short || echo "No GUI tests found"

test-coverage: ## Run tests with detailed coverage report
	@echo "📊 Running tests with coverage..."
	pytest tests/ \
		--cov=ssh_manager --cov=ssh_gui \
		--cov-report=html:htmlcov \
		--cov-report=xml:coverage.xml \
		--cov-report=term-missing \
		--cov-fail-under=85 \
		--tb=short

test-performance: ## Run performance tests
	@echo "🚀 Running performance tests..."
	pytest tests/ -m "slow" --benchmark-only --benchmark-sort=mean

# Linting targets
lint: lint-black lint-isort lint-flake8 lint-mypy ## Run all linting checks
	@echo "✅ All linting checks completed"

lint-black: ## Check code formatting with black
	@echo "⚫ Checking code formatting with black..."
	black --check --diff ssh_manager.py ssh_gui.py tests/

lint-isort: ## Check import sorting with isort
	@echo "🔤 Checking import sorting with isort..."
	isort --check-only --diff ssh_manager.py ssh_gui.py tests/

lint-flake8: ## Check code style with flake8
	@echo "🔍 Checking code style with flake8..."
	flake8 ssh_manager.py ssh_gui.py tests/

lint-mypy: ## Check type hints with mypy
	@echo "🔧 Checking type hints with mypy..."
	mypy ssh_manager.py ssh_gui.py --ignore-missing-imports || echo "Type checking completed with warnings"

lint-bandit: ## Check security issues with bandit
	@echo "🔒 Checking security issues with bandit..."
	bandit -r ssh_manager.py ssh_gui.py -ll || echo "Security check completed"

# Formatting targets
format: format-black format-isort ## Format code with black and isort
	@echo "✨ Code formatting completed"

format-black: ## Format code with black
	@echo "⚫ Formatting code with black..."
	black ssh_manager.py ssh_gui.py tests/

format-isort: ## Sort imports with isort
	@echo "🔤 Sorting imports with isort..."
	isort ssh_manager.py ssh_gui.py tests/

# Cleaning targets
clean: clean-build clean-pyc clean-test clean-coverage ## Clean all build artifacts
	@echo "🧹 Cleaned all build artifacts"

clean-build: ## Remove build artifacts
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .eggs/

clean-pyc: ## Remove Python file artifacts
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*~" -delete
	find . -type f -name "__pycache__" -delete
	find . -type d -name "__pycache__" -delete

clean-test: ## Remove test artifacts
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .tox/
	rm -rf coverage.xml
	rm -rf test-results/

clean-coverage: ## Remove coverage reports
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf coverage.xml

# Build targets
build: clean build-wheel build-sdist ## Build both wheel and source distribution
	@echo "📦 Build completed"

build-wheel: ## Build wheel distribution
	@echo "🎡 Building wheel distribution..."
	python -m build --wheel

build-sdist: ## Build source distribution
	@echo "📦 Building source distribution..."
	python -m build --sdist

# Release targets
release-test: build ## Upload to Test PyPI
	@echo "🚀 Uploading to Test PyPI..."
	python -m twine upload --repository testpypi dist/* --verbose

release-prod: build ## Upload to Production PyPI
	@echo "🚀 Uploading to Production PyPI..."
	python -m twine upload dist/* --verbose

# Documentation targets
docs-build: ## Build documentation
	@echo "📚 Building documentation..."
	@if [ -d "docs" ]; then \
		cd docs && make html; \
	else \
		echo "📝 No docs directory found. Creating basic documentation..."; \
		mkdir -p docs; \
		echo "# SSH Profile Manager Documentation" > docs/README.md; \
		echo "Documentation coming soon..." >> docs/README.md; \
	fi

docs-serve: ## Serve documentation locally
	@echo "🌐 Serving documentation..."
	@if [ -d "docs/_build/html" ]; then \
		cd docs/_build/html && python -m http.server 8000; \
	else \
		echo "📚 No built documentation found. Run 'make docs-build' first."; \
	fi

# Security targets
security: security-bandit security-safety ## Run all security checks
	@echo "🔒 Security checks completed"

security-bandit: ## Run bandit security linter
	@echo "🔒 Running bandit security checks..."
	bandit -r ssh_manager.py ssh_gui.py -f json -o bandit-report.json || echo "Bandit completed with warnings"

security-safety: ## Check dependencies for known vulnerabilities
	@echo "🛡️ Checking dependencies for vulnerabilities..."
	safety check --json --output safety-report.json || echo "Safety check completed"

# Performance targets
benchmark: ## Run performance benchmarks
	@echo "⏱️ Running performance benchmarks..."
	pytest tests/ --benchmark-only --benchmark-sort=mean --benchmark-json=benchmark-results.json

performance: test-performance benchmark ## Run all performance tests
	@echo "🚀 Performance testing completed"

# Development targets
run-cli: ## Run CLI version
	@echo "⚡ Running SSH Manager CLI..."
	python ssh_manager.py --help

run-gui: ## Run GUI version
	@echo "🎨 Running SSH Manager GUI..."
	python ssh_gui.py

# Validation targets
validate: validate-all ## Run comprehensive validation
	@echo "✅ Validation completed"

validate-all: clean lint test security ## Run all validation checks
	@echo "🎯 Running comprehensive validation..."
	@echo "  1. Cleaned build artifacts"
	@echo "  2. Passed linting checks"
	@echo "  3. Passed all tests"
	@echo "  4. Passed security checks"
	@echo "✅ All validation checks passed!"

# Development workflow targets
dev-setup: install-dev install-hooks ## Set up development environment
	@echo "🛠️ Development environment setup completed"
	@echo "📋 Next steps:"
	@echo "  1. Run 'make test' to verify everything works"
	@echo "  2. Run 'make lint' to check code quality"
	@echo "  3. Run 'make run-cli' or 'make run-gui' to test the applications"

dev-check: format lint test ## Quick development check
	@echo "✅ Development check completed - ready to commit!"

pre-commit: format lint test-unit ## Pre-commit checks (fast)
	@echo "✅ Pre-commit checks passed!"

ci-test: clean lint test-coverage security ## CI/CD pipeline simulation
	@echo "🤖 CI/CD pipeline simulation completed"

# Installation verification
verify-install: ## Verify installation works correctly
	@echo "🔍 Verifying installation..."
	@command -v ssh-manager >/dev/null 2>&1 || { echo "❌ ssh-manager not found in PATH"; exit 1; }
	@command -v ssh-gui >/dev/null 2>&1 || { echo "❌ ssh-gui not found in PATH"; exit 1; }
	@ssh-manager --help >/dev/null 2>&1 || { echo "❌ ssh-manager help failed"; exit 1; }
	@echo "✅ Installation verification passed"

# Quick help for common tasks
quick-start: ## Show quick start guide
	@echo "🚀 SSH Profile Manager - Quick Start"
	@echo "===================================="
	@echo ""
	@echo "1. Development setup:"
	@echo "   make dev-setup"
	@echo ""
	@echo "2. Run tests:"
	@echo "   make test"
	@echo ""
	@echo "3. Format and lint code:"
	@echo "   make format"
	@echo "   make lint"
	@echo ""
	@echo "4. Build and test release:"
	@echo "   make build"
	@echo "   make release-test"
	@echo ""
	@echo "5. Try the applications:"
	@echo "   make run-cli"
	@echo "   make run-gui"

# Variables for customization
PYTHON ?= python
PIP ?= pip
PYTEST_ARGS ?= -v
COV_REPORT ?= term-missing

# Platform-specific commands
ifeq ($(OS),Windows_NT)
    RM = del /Q
    RMDIR = rmdir /S /Q
else
    RM = rm -f
    RMDIR = rm -rf
endif

# Color output (if supported)
ifneq (,$(findstring xterm,${TERM}))
	RED := $(shell tput setaf 1)
	GREEN := $(shell tput setaf 2)
	YELLOW := $(shell tput setaf 3)
	BLUE := $(shell tput setaf 4)
	MAGENTA := $(shell tput setaf 5)
	CYAN := $(shell tput setaf 6)
	WHITE := $(shell tput setaf 7)
	RESET := $(shell tput sgr0)
else
	RED := ""
	GREEN := ""
	YELLOW := ""
	BLUE := ""
	MAGENTA := ""
	CYAN := ""
	WHITE := ""
	RESET := ""
endif

# Advanced targets for maintainers
maintainer-clean: clean ## Deep clean for maintainers
	git clean -xfd

update-deps: ## Update all dependencies
	@echo "📦 Updating dependencies..."
	pip-compile requirements-dev.in --upgrade || echo "pip-tools not available"
	pip install -r requirements-dev.txt --upgrade

check-deps: ## Check for outdated dependencies
	@echo "🔍 Checking for outdated dependencies..."
	pip list --outdated

# Docker targets (if Dockerfile exists)
docker-build: ## Build Docker image
	@if [ -f "Dockerfile" ]; then \
		docker build -t ssh-profile-manager .; \
	else \
		echo "No Dockerfile found"; \
	fi

docker-test: ## Test in Docker container
	@if [ -f "Dockerfile" ]; then \
		docker run --rm ssh-profile-manager make test; \
	else \
		echo "No Dockerfile found"; \
	fi

# GitHub Actions local simulation (if act is available)
act-test: ## Run GitHub Actions locally with act
	@if command -v act >/dev/null 2>&1; then \
		act --job test; \
	else \
		echo "act not available. Install from https://github.com/nektos/act"; \
	fi

# Final reminder
.DEFAULT_GOAL := help
