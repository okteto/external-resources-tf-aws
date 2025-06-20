# Testing Guide

This document describes how to run unit tests for the Oktaco Shop microservices application.

## Overview

The application consists of three microservices, each with comprehensive unit tests:

1. **Menu Service** (Node.js/Express) - Handles order placement
2. **Kitchen Service** (Go/Gin) - Processes orders from SQS queue
3. **Check Service** (Python/FastAPI) - Handles billing and receipts

## Running Tests with Okteto

### Run All Unit Tests
```bash
okteto test
```

### Run Individual Service Tests
```bash
# Menu service unit tests
okteto test menu-unit

# Kitchen service unit tests  
okteto test kitchen-unit

# Check service unit tests
okteto test check-unit

# End-to-end tests
okteto test e2e
```

## Test Coverage

Each service includes comprehensive test coverage:

### Menu Service Tests
- ✅ Health check endpoint
- ✅ Order placement via SQS
- ✅ Template rendering
- ✅ Error handling for SQS failures
- ✅ Static file serving
- ✅ Environment configuration

### Kitchen Service Tests
- ✅ Order creation and management
- ✅ Item ready marking
- ✅ Order completion detection
- ✅ REST API endpoints
- ✅ JSON serialization/deserialization
- ✅ Error handling for invalid data

### Check Service Tests
- ✅ Health check endpoint
- ✅ Check creation with price calculation
- ✅ Receipt generation and S3 upload
- ✅ CRUD operations for checks
- ✅ Error handling for missing resources
- ✅ Full workflow integration tests


## Continuous Integration

The tests are designed to run in CI/CD pipelines and include:

- **Caching** - Dependencies and build artifacts are cached for faster runs
- **Coverage Reports** - Detailed coverage information for all services
- **Artifacts** - Test results and coverage reports are preserved
- **Parallel Execution** - Tests can run independently and in parallel

## Test Environment

Unit tests use mocked external dependencies:

- **AWS SQS** - Mocked for menu service order placement
- **AWS S3** - Mocked for check service receipt storage
- **HTTP Clients** - Mocked for inter-service communication

This ensures tests are:
- Fast and reliable
- Independent of external services
- Suitable for CI/CD environments
- Deterministic and repeatable

The End to End test validates functionality without mocks.

## Adding New Tests

When adding new functionality:

1. **Write tests first** (TDD approach recommended)
2. **Mock external dependencies** (AWS services, HTTP calls)
3. **Test both success and error cases**
4. **Include integration tests** for complete workflows
5. **Update this documentation** if adding new test categories

## Troubleshooting

### Common Issues

**Okteto test command not found:**
```bash
# Ensure you're in the workspace root directory
cd /workspace
okteto validate  # Verify manifest is valid
```