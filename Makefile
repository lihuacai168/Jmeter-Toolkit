.PHONY: help install dev test lint format clean build up down logs shell

# Default target
help:
	@echo "Available commands:"
	@echo "  install     Install dependencies"
	@echo "  dev         Run development server"
	@echo "  test        Run tests"
	@echo "  lint        Run linting"
	@echo "  format      Format code"
	@echo "  clean       Clean up"
	@echo "  build       Build Docker image"
	@echo "  up          Start services with docker-compose"
	@echo "  down        Stop services"
	@echo "  logs        View logs"
	@echo "  shell       Open shell in container"

# Install dependencies
install:
	pip install -r requirements.txt

# Development server
dev:
	uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Run tests
test:
	pytest tests/ -v --cov=. --cov-report=html

# Lint code
lint:
	flake8 --max-line-length=100 --exclude=venv,__pycache__,.git .
	mypy . --ignore-missing-imports

# Format code
format:
	black . --line-length=100
	isort . --profile black

# Clean up
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .coverage htmlcov/ .pytest_cache/

# Docker operations
build:
	docker-compose build

up:
	docker-compose up -d

down:
	docker-compose down

logs:
	docker-compose logs -f

shell:
	docker-compose exec app /bin/bash

# Database operations
migrate:
	alembic upgrade head

migrate-create:
	alembic revision --autogenerate -m "$(message)"

# Development setup
setup-dev:
	cp .env.example .env
	pip install -r requirements.txt
	docker-compose up -d postgres redis
	sleep 10
	python -c "from database import Base, engine; Base.metadata.create_all(bind=engine)"

# Production deployment
deploy:
	docker-compose -f docker-compose.yml up -d --build

# Monitoring
monitor:
	@echo "Application: http://localhost:8000"
	@echo "Health check: http://localhost:8000/health"
	@echo "Metrics: http://localhost:8000/metrics"
	@echo "API docs: http://localhost:8000/docs"
	@echo "Flower (Celery): http://localhost:5555"