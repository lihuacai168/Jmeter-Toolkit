#!/bin/bash

# Simplified CI integration test script
set -e

echo "🧪 Starting Simplified CI Integration Tests..."

# Note: Cleanup is handled by CI workflow to allow coverage extraction
# Function to cleanup (disabled - handled by CI workflow)
cleanup() {
    echo "ℹ️  Cleanup will be handled by CI workflow after coverage extraction"
}

# Trap cleanup on exit (disabled - CI workflow handles cleanup)
# trap cleanup EXIT

COMPOSE_FILE="docker-compose.ci.yml"
APP_URL="http://localhost:8002"

echo "📋 Configuration:"
echo "   Compose file: $COMPOSE_FILE"
echo "   App URL: $APP_URL"

# Start only essential services (skip test server and postgres for CI)
echo "🐳 Starting essential Docker Compose services..."
docker-compose -f $COMPOSE_FILE up -d --build ci-redis ci-app

# Wait for essential services to be healthy
echo "⏳ Waiting for essential services to be healthy..."
max_attempts=10
attempt=0

while [ $attempt -lt $max_attempts ]; do
    # Check if ci-app service is healthy
    if docker-compose -f $COMPOSE_FILE ps | grep "ci-app" | grep -q "healthy"; then
        echo "✅ Essential services are healthy"
        break
    fi

    attempt=$((attempt + 1))
    echo "   Attempt $attempt/$max_attempts - waiting..."
    sleep 10
done

if [ $attempt -eq $max_attempts ]; then
    echo "❌ Essential services failed to become healthy"
    echo "📋 Service status:"
    docker-compose -f $COMPOSE_FILE ps
    echo "📋 App logs:"
    docker-compose -f $COMPOSE_FILE logs ci-app
    exit 1
fi

# Health check app endpoint
echo "🔍 Performing app health check..."
for i in {1..5}; do
    if curl -s -f "$APP_URL/health" > /dev/null; then
        echo "   ✅ App health check passed"
        break
    fi
    if [ $i -eq 5 ]; then
        HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$APP_URL/health" || echo "000")
        echo "   ❌ App health check failed (status: $HTTP_STATUS)"
        exit 1
    fi
    sleep 5
done

# Check pytest availability with detailed debugging
echo "🔍 Checking pytest availability..."
echo "📋 Debugging Python environment in container..."

# Check Python version and path
echo "🔍 Python environment details:"
docker-compose -f $COMPOSE_FILE exec -T ci-app python --version
docker-compose -f $COMPOSE_FILE exec -T ci-app which python
docker-compose -f $COMPOSE_FILE exec -T ci-app echo "PATH: $PATH"

# Check virtual environment
echo "🔍 Virtual environment status:"
docker-compose -f $COMPOSE_FILE exec -T ci-app ls -la /app/.venv/bin/ | head -10 || echo "❌ .venv/bin not found"

# List all installed packages
echo "🔍 All installed packages:"
docker-compose -f $COMPOSE_FILE exec -T ci-app uv pip list

# Specifically check for pytest packages
echo "🔍 Pytest-related packages:"
docker-compose -f $COMPOSE_FILE exec -T ci-app uv pip list | grep -i pytest || echo "❌ No pytest packages found"

# Try to import pytest directly
echo "🔍 Testing pytest import:"
if docker-compose -f $COMPOSE_FILE exec -T ci-app python -c "import pytest; print(f'✅ pytest version: {pytest.__version__}')"; then
    echo "✅ pytest import successful"
else
    echo "❌ pytest import failed"
fi

# Check pytest command availability
echo "🔍 Testing pytest command:"
if docker-compose -f $COMPOSE_FILE exec -T ci-app python -m pytest --version; then
    echo "✅ pytest command available"
else
    echo "❌ pytest command failed"
    echo "🔍 Attempting to install pytest manually..."
    docker-compose -f $COMPOSE_FILE exec -T ci-app uv pip install pytest
    if docker-compose -f $COMPOSE_FILE exec -T ci-app python -m pytest --version; then
        echo "✅ pytest manually installed and working"
    else
        echo "❌ Manual pytest installation failed"
        exit 1
    fi
fi

# Run comprehensive test suite with coverage (unit tests + integration tests)
echo "🧪 Running comprehensive test suite with coverage..."
echo "   📋 Test coverage includes:"
echo "      • Unit tests: ~47 test functions"
echo "      • Integration tests: test_execute_api.py (19 tests)"
echo "      • Total coverage from all test files except test_integration_execute.py"

# Run all tests except the full integration tests (which require more complex setup)
docker-compose -f $COMPOSE_FILE exec -T ci-app python -m pytest tests/ -v \
  --cov=. \
  --cov-report=xml \
  --cov-report=term-missing \
  --tb=short \
  --ignore=tests/test_integration_execute.py \
  --ignore=tests/test_performance_execute.py

echo "✅ Simplified CI integration tests completed successfully!"
