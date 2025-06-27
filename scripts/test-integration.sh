#!/bin/bash

# Integration test script using Docker Compose
set -e

echo "🧪 Starting Integration Tests..."

# Function to cleanup
cleanup() {
    echo "🧹 Cleaning up..."
    docker-compose -f docker-compose.test.yml down -v --remove-orphans 2>/dev/null || true
    docker-compose -f docker-compose.ci.yml down -v --remove-orphans 2>/dev/null || true
}

# Trap cleanup on exit
trap cleanup EXIT

# Test environment selection
TEST_ENV=${1:-test}

if [ "$TEST_ENV" = "ci" ]; then
    COMPOSE_FILE="docker-compose.ci.yml"
    APP_URL="http://localhost:8002"
    TEST_SERVER_URL="http://localhost:3001"
    echo "🚀 Using CI environment"
elif [ "$TEST_ENV" = "prod" ]; then
    COMPOSE_FILE="docker-compose.yml"
    APP_URL="http://localhost:8000"
    TEST_SERVER_URL="http://localhost:3000"
    echo "🚀 Using Production environment"
else
    COMPOSE_FILE="docker-compose.test.yml"
    APP_URL="http://localhost:8001"
    TEST_SERVER_URL="http://localhost:3000"
    echo "🚀 Using Test environment"
fi

echo "📋 Configuration:"
echo "   Compose file: $COMPOSE_FILE"
echo "   App URL: $APP_URL"
echo "   Test Server URL: $TEST_SERVER_URL"

# Start services
echo "🐳 Starting Docker Compose services..."
docker-compose -f $COMPOSE_FILE up -d --build

# Wait for services to be healthy
echo "⏳ Waiting for services to be healthy..."
max_attempts=60
attempt=0

while [ $attempt -lt $max_attempts ]; do
    if [ "$TEST_ENV" = "prod" ]; then
        # Production environment - check main app only
        if docker-compose -f $COMPOSE_FILE ps | grep -q "healthy"; then
            echo "✅ Services are healthy"
            break
        fi
    else
        # Test/CI environment - check both app and test server
        app_healthy=$(docker-compose -f $COMPOSE_FILE ps | grep "test-app\|ci-app" | grep -c "healthy" || echo "0")
        server_healthy=$(docker-compose -f $COMPOSE_FILE ps | grep "test-server\|ci-test-server" | grep -c "healthy" || echo "0")

        if [ "$app_healthy" -ge "1" ] && [ "$server_healthy" -ge "1" ]; then
            echo "✅ Services are healthy"
            break
        fi
    fi

    attempt=$((attempt + 1))
    echo "   Attempt $attempt/$max_attempts - waiting..."
    sleep 2
done

if [ $attempt -eq $max_attempts ]; then
    echo "❌ Services failed to become healthy"
    echo "📋 Service status:"
    docker-compose -f $COMPOSE_FILE ps
    echo "📋 Service logs:"
    docker-compose -f $COMPOSE_FILE logs
    exit 1
fi

# Additional health checks
echo "🔍 Performing additional health checks..."

# Check app health endpoint
echo "   Checking app health..."
for i in {1..10}; do
    if curl -s -f "$APP_URL/health" > /dev/null; then
        echo "   ✅ App health check passed"
        break
    fi
    if [ $i -eq 10 ]; then
        echo "   ❌ App health check failed"
        exit 1
    fi
    sleep 2
done

# Check test server (if not production)
if [ "$TEST_ENV" != "prod" ]; then
    echo "   Checking test server health..."
    for i in {1..10}; do
        if curl -s -f "$TEST_SERVER_URL/health" > /dev/null; then
            echo "   ✅ Test server health check passed"
            break
        fi
        if [ $i -eq 10 ]; then
            echo "   ❌ Test server health check failed"
            exit 1
        fi
        sleep 2
    done
fi

# Run integration tests
echo "🧪 Running integration tests..."

if [ "$TEST_ENV" = "prod" ]; then
    # Production environment - run basic API tests
    echo "   Running production integration tests..."
    docker-compose -f $COMPOSE_FILE exec -T app pytest tests/test_api.py -v
else
    # Test/CI environment - run full integration tests
    echo "   Running full integration tests..."
    docker-compose -f $COMPOSE_FILE exec -T test-app pytest tests/test_integration_execute.py -v -s

    # Run additional API tests
    echo "   Running API tests in containerized environment..."
    docker-compose -f $COMPOSE_FILE exec -T test-app pytest tests/test_execute_api.py -v
fi

echo "✅ Integration tests completed successfully!"

# Optional: Run performance tests
if [ "$2" = "--with-performance" ]; then
    echo "🚀 Running performance tests..."
    if [ "$TEST_ENV" = "prod" ]; then
        docker-compose -f $COMPOSE_FILE exec -T app pytest tests/test_performance_execute.py -v -m performance
    else
        docker-compose -f $COMPOSE_FILE exec -T test-app pytest tests/test_performance_execute.py -v -m performance
    fi
fi

echo "🎉 All tests completed successfully!"
