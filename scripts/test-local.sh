#!/bin/bash

# Local integration test script
set -e

echo "🧪 Running Local Integration Tests..."

# Function to cleanup
cleanup() {
    echo "🧹 Cleaning up..."
    docker-compose -f docker-compose.test.yml down -v --remove-orphans 2>/dev/null || true
}

# Trap cleanup on exit
trap cleanup EXIT

echo "🐳 Starting test environment with Docker Compose..."
docker-compose -f docker-compose.test.yml up -d --build

echo "⏳ Waiting for services to be healthy..."
max_attempts=5
attempt=0

while [ $attempt -lt $max_attempts ]; do
    app_healthy=$(docker-compose -f docker-compose.test.yml ps | grep "test-app" | grep -c "healthy" 2>/dev/null || echo "0")
    server_healthy=$(docker-compose -f docker-compose.test.yml ps | grep "test-server" | grep -c "healthy" 2>/dev/null || echo "0")

    if [ "${app_healthy:-0}" -ge "1" ] && [ "${server_healthy:-0}" -ge "1" ]; then
        echo "✅ Services are healthy"
        break
    fi

    attempt=$((attempt + 1))
    echo "   Attempt $attempt/$max_attempts - waiting..."
    sleep 2
done

if [ $attempt -eq $max_attempts ]; then
    echo "❌ Services failed to become healthy"
    echo "📋 Service status:"
    docker-compose -f docker-compose.test.yml ps
    echo "📋 Service logs:"
    docker-compose -f docker-compose.test.yml logs
    exit 1
fi

# Health checks
echo "🔍 Performing health checks..."

echo "   Checking app health..."
for i in {1..10}; do
    if curl -s -f "http://localhost:8001/health" > /dev/null; then
        echo "   ✅ App health check passed"
        break
    fi
    if [ $i -eq 10 ]; then
        echo "   ❌ App health check failed"
        exit 1
    fi
    sleep 2
done

echo "   Checking test server health..."
for i in {1..10}; do
    if curl -s -f "http://localhost:3000/health" > /dev/null; then
        echo "   ✅ Test server health check passed"
        break
    fi
    if [ $i -eq 10 ]; then
        echo "   ❌ Test server health check failed"
        exit 1
    fi
    sleep 2
done

# Run integration tests
echo "🧪 Running integration tests..."
export TEST_SERVER_URL="http://localhost:3000"
export API_BASE_URL="http://localhost:8001"

# Run tests outside container (requires local pytest)
if command -v pytest &> /dev/null; then
    echo "   Running tests with local pytest..."
    TEST_SERVER_URL="http://localhost:3000" pytest tests/test_integration_execute.py -v -s
else
    echo "   Running tests inside container..."
    docker-compose -f docker-compose.test.yml exec -T test-app pytest tests/test_integration_execute.py -v -s
fi

echo "✅ Local integration tests completed successfully!"
