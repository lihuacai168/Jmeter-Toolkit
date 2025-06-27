# Integration Testing Guide

This document describes the integration testing setup for the JMeter Toolkit project.

## Overview

The project includes comprehensive integration tests that run in containerized environments using Docker Compose. This ensures tests run in environments that closely match production.

## Test Environments

### 1. Test Environment (`docker-compose.test.yml`)
- **Purpose**: Development and local testing
- **App URL**: http://localhost:8001
- **Test Server URL**: http://localhost:3000
- **Database**: PostgreSQL on port 5433
- **Redis**: Redis on port 6380

### 2. CI Environment (`docker-compose.ci.yml`)
- **Purpose**: Continuous Integration testing
- **App URL**: http://localhost:8002
- **Test Server URL**: http://localhost:3001
- **Database**: PostgreSQL on port 5434
- **Redis**: Redis on port 6381

### 3. Production Environment (`docker-compose.yml`)
- **Purpose**: Production-like integration testing
- **App URL**: http://localhost:8000
- **Database**: PostgreSQL on port 5432
- **Redis**: Redis on port 6379

## Running Integration Tests

### Local Development
```bash
# Run test environment
./scripts/test-local.sh

# Or manually
docker-compose -f docker-compose.test.yml up -d --build
TEST_SERVER_URL="http://localhost:3000" pytest tests/test_integration_execute.py -v
```

### Full Integration Test Suite
```bash
# Test environment
./scripts/test-integration.sh test

# CI environment  
./scripts/test-integration.sh ci

# Production environment
./scripts/test-integration.sh prod

# With performance tests
./scripts/test-integration.sh test --with-performance
```

## Test Components

### Integration Test Files
- `tests/test_integration_execute.py` - Main integration tests for execute APIs
- `test_examples/test_server.py` - FastAPI test server for JMeter targets
- `test_examples/sample_test.jmx` - Real JMeter test plan

### Test Scenarios
1. **Real JMX Execution**: Upload and execute actual JMX files against test server
2. **Upload-and-Execute Workflow**: Combined upload/execute operations
3. **End-to-End Workflow**: Complete API workflow testing
4. **File Management**: Upload, list, and download operations
5. **Task Management**: Task creation, status checking, and listing

## Docker Compose Services

### Application Services
- **test-app/ci-app**: Main JMeter Toolkit application
- **test-postgres/ci-postgres**: PostgreSQL database
- **test-redis/ci-redis**: Redis cache/message broker

### Test Infrastructure
- **test-server/ci-test-server**: FastAPI test server that serves as JMeter target
- **Health checks**: All services include health checks for reliability

## Environment Variables

### Test Configuration
- `ENVIRONMENT=testing`
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `TEST_SERVER_URL`: Test server endpoint for integration tests

### CI/CD Integration

The integration tests are automatically run in GitHub Actions:

1. **Unit Test Phase**: Integration tests are skipped
2. **Integration Test Phase**: 
   - CI environment tests with `docker-compose.ci.yml`
   - Production environment tests with `docker-compose.yml`
   - Automatic cleanup and resource management

## Troubleshooting

### Common Issues

1. **Services not healthy**: Check Docker logs
   ```bash
   docker-compose -f docker-compose.test.yml logs
   ```

2. **Port conflicts**: Ensure ports are available
   ```bash
   netstat -an | grep :8001
   ```

3. **Test server not reachable**: Verify test server is running
   ```bash
   curl http://localhost:3000/health
   ```

### Debugging

1. **Check service status**:
   ```bash
   docker-compose -f docker-compose.test.yml ps
   ```

2. **View service logs**:
   ```bash
   docker-compose -f docker-compose.test.yml logs test-app
   docker-compose -f docker-compose.test.yml logs test-server
   ```

3. **Run tests manually**:
   ```bash
   docker-compose -f docker-compose.test.yml exec test-app pytest tests/test_integration_execute.py -v -s
   ```

## Best Practices

1. **Always cleanup**: Use scripts that include cleanup on exit
2. **Health checks**: Wait for services to be healthy before running tests
3. **Isolation**: Each test environment uses separate ports and databases
4. **Resource limits**: Test environments use tmpfs for databases to improve speed
5. **Timeouts**: Include reasonable timeouts for service startup and health checks

## Performance Considerations

- Test databases use tmpfs for faster I/O
- Separate Redis instances prevent data conflicts
- Health checks ensure services are ready before testing
- Automatic cleanup prevents resource leaks