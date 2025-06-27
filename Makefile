# JMeter Toolkit Development Makefile

.PHONY: help install install-dev setup-hooks lint format test test-cov clean build docker-build docker-test security docs

# Default target
help:
	@echo "JMeter Toolkit Development Commands:"
	@echo ""
	@echo "Setup:"
	@echo "  install          Install production dependencies"
	@echo "  install-dev      Install development dependencies"
	@echo "  setup-hooks      Setup pre-commit hooks"
	@echo ""
	@echo "Code Quality:"
	@echo "  lint             Run all linters (flake8, mypy, bandit)"
	@echo "  format           Format code with black and isort"
	@echo "  format-check     Check code formatting without changes"
	@echo ""
	@echo "Testing:"
	@echo "  test             Run tests with pytest"
	@echo "  test-cov         Run tests with coverage report"
	@echo "  test-fast        Run tests in parallel (faster)"
	@echo ""
	@echo "Security:"
	@echo "  security         Run security checks (bandit, safety, pip-audit)"
	@echo ""
	@echo "Docker:"
	@echo "  docker-build     Build Docker image"
	@echo "  docker-test      Test Docker image"
	@echo "  docker-ci        Build and test CI Docker image"
	@echo ""
	@echo "Maintenance:"
	@echo "  clean            Clean temporary files and caches"
	@echo "  docs             Build documentation"
	@echo "  update-deps      Update dependencies"

# Installation
install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements-dev.txt

setup-hooks:
	pre-commit install
	pre-commit install --hook-type commit-msg
	@echo "✅ Pre-commit hooks installed!"
	@echo "To test hooks: make format && git add . && git commit -m 'test commit'"

# Code quality
lint:
	@echo "🔍 Running flake8..."
	flake8 .
	@echo "🔍 Running mypy..."
	mypy . --ignore-missing-imports
	@echo "🔍 Running bandit..."
	bandit -r . -f json -o bandit-report.json || true
	@echo "✅ Linting complete!"

format:
	@echo "🎨 Formatting with black..."
	black . --line-length 127
	@echo "📦 Sorting imports with isort..."
	isort . --profile black --line-length 127
	@echo "🧹 Removing unused imports..."
	autoflake --in-place --remove-all-unused-imports --remove-unused-variables --recursive .
	@echo "✅ Formatting complete!"

format-check:
	@echo "🔍 Checking black formatting..."
	black . --line-length 127 --check --diff
	@echo "🔍 Checking isort..."
	isort . --profile black --line-length 127 --check-only --diff
	@echo "✅ Format check complete!"

# Testing
test:
	@echo "🧪 Running tests..."
	pytest tests/ -v

test-cov:
	@echo "🧪 Running tests with coverage..."
	pytest tests/ -v --cov=. --cov-report=html --cov-report=term-missing

test-fast:
	@echo "🧪 Running tests in parallel..."
	pytest tests/ -v -n auto

# Security
security:
	@echo "🔒 Running security checks..."
	bandit -r . -f json -o bandit-report.json
	safety check
	pip-audit
	@echo "✅ Security checks complete!"

# Docker
docker-build:
	@echo "🐳 Building Docker image..."
	docker build -t jmeter-toolkit:latest .

docker-test:
	@echo "🐳 Testing Docker image..."
	docker run --rm -d --name test-container -p 8000:8000 jmeter-toolkit:latest
	sleep 10
	curl -f http://localhost:8000/health || (docker stop test-container && exit 1)
	docker stop test-container
	@echo "✅ Docker test complete!"

docker-ci:
	@echo "🐳 Building CI Docker image..."
	docker build -f Dockerfile.ci -t jmeter-toolkit:ci-test .
	docker run --rm -d --name ci-test-container -p 8001:8000 jmeter-toolkit:ci-test
	sleep 10
	HTTP_STATUS=$$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/health); \
	if [ "$$HTTP_STATUS" != "200" ] && [ "$$HTTP_STATUS" != "503" ]; then \
		echo "❌ CI Docker test failed with status: $$HTTP_STATUS"; \
		docker stop ci-test-container; \
		exit 1; \
	fi; \
	echo "✅ CI Docker test passed with status: $$HTTP_STATUS"
	docker stop ci-test-container

# Documentation
docs:
	@echo "📚 Building documentation..."
	mkdocs build
	@echo "✅ Documentation built in site/"

# Maintenance
clean:
	@echo "🧹 Cleaning temporary files..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type f -name ".coverage" -delete
	find . -type d -name "htmlcov" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type f -name "bandit-report.json" -delete
	rm -rf build/ dist/ site/
	@echo "✅ Cleanup complete!"

update-deps:
	@echo "🔄 Updating dependencies..."
	pre-commit autoupdate
	pip list --outdated
	@echo "✅ Check for outdated packages above"

# CI/CD simulation
ci-local:
	@echo "🚀 Running full CI pipeline locally..."
	make clean
	make format-check
	make lint
	make test-cov
	make security
	make docker-ci
	@echo "✅ Local CI pipeline complete!"

# Quick development setup
dev-setup: install-dev setup-hooks
	@echo "🎉 Development environment setup complete!"
	@echo ""
	@echo "Next steps:"
	@echo "1. Run 'make format' to format your code"
	@echo "2. Run 'make test' to run tests"
	@echo "3. Start developing - pre-commit hooks will run automatically!"

# Pre-commit hook simulation
pre-commit-all:
	@echo "🔧 Running all pre-commit hooks..."
	pre-commit run --all-files
