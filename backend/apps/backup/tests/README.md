# Backup & Restore Test Suite

## Overview

Comprehensive test suite for EDMS backup and restoration functionality, with focus on workflow history preservation.

## Test Files

- **`test_workflow_restoration.py`** - Unit tests for natural key resolution and workflow restoration
- **`test_complete_restoration_flow.py`** - Integration tests for end-to-end restoration scenarios

## Quick Start

Run all tests:
```bash
# From project root
./backend/scripts/run_backup_tests.sh

# Or run individually
docker compose exec backend python manage.py test apps.backup.tests
```

## Test Structure

### Unit Tests (`test_workflow_restoration.py`)

**Classes:**
- `NaturalKeyResolutionTests` - Tests natural key handlers
- `WorkflowRestorationIntegrationTests` - Tests workflow restoration
- `PostReinitWorkflowRestorationTests` - Tests post-reinit scenarios
- `EdgeCaseTests` - Tests error handling

**Coverage:**
- Natural key resolution for all models
- Foreign key reference handling
- UUID conflict resolution
- Error scenarios

### Integration Tests (`test_complete_restoration_flow.py`)

**Classes:**
- `CompleteRestorationFlowTests` - Full backup → restore cycle
- `MultipleDocumentWorkflowTests` - Multiple document scenarios
- `WorkflowHistoryPreservationTests` - Transition history preservation

**Coverage:**
- End-to-end restoration flow
- Multiple workflow states
- Complete audit trail preservation

## Running Specific Tests

**Single test class:**
```bash
docker compose exec backend python manage.py test apps.backup.tests.test_workflow_restoration.NaturalKeyResolutionTests
```

**Single test method:**
```bash
docker compose exec backend python manage.py test apps.backup.tests.test_workflow_restoration.NaturalKeyResolutionTests.test_resolve_document_natural_key
```

**With verbose output:**
```bash
docker compose exec backend python manage.py test apps.backup.tests --verbosity=2
```

## Requirements

- Docker environment running
- Database migrations applied
- Test fixtures: `initial_users.json`

## Expected Results

All tests should pass with output similar to:
```
Ran 18 tests in 55.123s

OK
```

## Documentation

Full documentation: [docs/test-reports/WORKFLOW_RESTORATION_TEST_SUITE.md](../../../docs/test-reports/WORKFLOW_RESTORATION_TEST_SUITE.md)

## Troubleshooting

**Tests fail with fixture errors:**
```bash
docker compose exec backend python manage.py seed_test_users
```

**Database issues:**
```bash
docker compose exec backend python manage.py migrate
```

**Clear test data:**
```bash
docker compose exec backend python manage.py flush --no-input
docker compose exec backend python manage.py migrate
```
