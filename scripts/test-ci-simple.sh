#!/bin/bash

# Simplified CI integration test script
set -e

echo "🧪 Starting Simplified CI Integration Tests..."

# Function to cleanup
cleanup() {
    echo "🧹 Cleaning up..."
    docker-compose -f docker-compose.ci.yml down -v --remove-orphans 2>/dev/null || true
}

# Trap cleanup on exit
trap cleanup EXIT

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

# Check pytest availability
echo "🔍 Checking pytest availability..."
if ! docker-compose -f $COMPOSE_FILE exec -T ci-app python -m pytest --version > /dev/null 2>&1; then
    echo "❌ pytest not available in container"
    echo "📋 Available Python packages:"
    docker-compose -f $COMPOSE_FILE exec -T ci-app pip list | grep -i pytest || echo "No pytest packages found"
    exit 1
fi

# Run core API tests
echo "🧪 Running core API tests..."
docker-compose -f $COMPOSE_FILE exec -T ci-app python -m pytest tests/test_execute_api.py -v --tb=short

echo "✅ Simplified CI integration tests completed successfully!"
