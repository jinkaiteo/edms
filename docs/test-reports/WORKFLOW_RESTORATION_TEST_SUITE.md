# EDMS Workflow Restoration - Comprehensive Test Suite

## Overview

This document describes the comprehensive test suite for EDMS workflow history restoration functionality. The test suite ensures that workflow data is correctly backed up and restored, maintaining complete audit trails and compliance requirements.

---

## Test Coverage

### 1. Unit Tests (`test_workflow_restoration.py`)

**Purpose**: Test individual components of the restoration system.

#### Test Classes:

##### `NaturalKeyResolutionTests`
Tests natural key resolution for all workflow-related models.

**Test Cases:**
- ✅ `test_resolve_document_natural_key` - Document resolution by document_number
- ✅ `test_resolve_document_natural_key_nonexistent` - Graceful handling of missing documents
- ✅ `test_resolve_documentstate_natural_key` - DocumentState resolution by code
- ✅ `test_resolve_user_natural_key` - User resolution by username
- ✅ `test_resolve_documentworkflow_natural_key` - DocumentWorkflow composite key resolution

**Fixtures Required**: `initial_users.json`

**What It Tests**:
- Natural key handlers correctly resolve object references
- Missing objects return None gracefully
- Composite natural keys work correctly

---

##### `WorkflowRestorationIntegrationTests`
Tests complete workflow restoration flow.

**Test Cases:**
- ✅ `test_restore_document_with_workflow` - Basic document + workflow restoration
- ✅ `test_restore_workflow_with_transitions` - Workflow with multiple transitions
- ✅ `test_restore_with_missing_document` - Graceful failure when dependencies missing

**What It Tests**:
- Documents and workflows are restored together
- Foreign key references are correctly resolved
- Transition history is preserved
- Error handling for missing dependencies

---

##### `PostReinitWorkflowRestorationTests`
Tests restoration after system_reinit (with preserved infrastructure).

**Test Cases:**
- ✅ `test_skip_preserved_infrastructure` - Infrastructure not duplicated
- ✅ `test_restore_business_data_post_reinit` - Business data restored correctly

**What It Tests**:
- Infrastructure preservation works correctly
- Business data is restored without conflicts
- UUID conflict resolution in post-reinit mode

---

##### `EdgeCaseTests`
Tests edge cases and error scenarios.

**Test Cases:**
- ✅ `test_empty_natural_key` - Empty natural key arrays
- ✅ `test_invalid_natural_key_format` - Invalid natural key formats
- ✅ `test_workflow_with_null_fields` - Optional null fields handled correctly

**What It Tests**:
- Robust error handling
- Null value handling
- Data validation

---

### 2. Integration Tests (`test_complete_restoration_flow.py`)

**Purpose**: Test end-to-end restoration scenarios with realistic data.

#### Test Classes:

##### `CompleteRestorationFlowTests`
Tests complete backup → reinit → restore cycle.

**Test Cases:**
- ✅ `test_complete_restoration_cycle` - Full lifecycle test

**Flow:**
1. Create test documents and workflows
2. Create backup package
3. Capture database state
4. Run system_reinit
5. Restore from backup
6. Verify all data restored correctly

**What It Tests**:
- Complete workflow restoration pipeline
- Data integrity through full cycle
- Backup package creation and restoration

---

##### `MultipleDocumentWorkflowTests`
Tests restoration with multiple documents in different workflow states.

**Test Cases:**
- ✅ `test_restore_multiple_workflows` - Multiple documents with different states

**What It Tests**:
- Multiple workflows restored correctly
- Different workflow states preserved
- No interference between workflows

---

##### `WorkflowHistoryPreservationTests`
Tests complete workflow history preservation.

**Test Cases:**
- ✅ `test_complete_workflow_history_preservation` - Full transition history preserved

**What It Tests**:
- All transitions restored in correct order
- Transition metadata preserved (comments, timestamps, user actions)
- Complete audit trail maintained

---

### 3. End-to-End Test Script (`test_workflow_restoration.sh`)

**Purpose**: Automated script for manual and CI/CD testing.

**What It Does:**
1. Creates test data (document with workflow and transitions)
2. Creates backup package
3. Captures pre-reinit state
4. Runs system_reinit
5. Verifies data cleared
6. Restores from backup
7. Verifies complete restoration

**Output**: Color-coded pass/fail with detailed verification

**Usage:**
```bash
./backend/scripts/test_workflow_restoration.sh
```

---

## Running the Tests

### Quick Start

Run all tests:
```bash
./backend/scripts/run_backup_tests.sh
```

### Individual Test Suites

**Unit Tests:**
```bash
docker compose exec backend python manage.py test apps.backup.tests.test_workflow_restoration
```

**Integration Tests:**
```bash
docker compose exec backend python manage.py test apps.backup.tests.test_complete_restoration_flow
```

**End-to-End Script:**
```bash
./backend/scripts/test_workflow_restoration.sh
```

**Specific Test:**
```bash
docker compose exec backend python manage.py test apps.backup.tests.test_workflow_restoration.NaturalKeyResolutionTests.test_resolve_document_natural_key
```

---

## Test Data Requirements

### Fixtures
- `initial_users.json` - Base user data (author01, reviewer01, etc.)

### Infrastructure Created During Tests
- DocumentType (TEST, SOP, POLICY)
- DocumentSource (TEST, INTERNAL)
- DocumentStates (DRAFT, PENDING_REVIEW, APPROVED, EFFECTIVE)

### Test Documents Created
- `TEST-2025-0001-v01.00` to `TEST-2025-0004-v01.00`
- `TEST-RESTORE-2025-v01.00` (E2E test)
- `POL-2025-TEST-v01.00` (Integration test)

---

## Expected Results

### Success Criteria

**Unit Tests:**
- All natural key resolution tests pass
- Foreign key resolution works correctly
- Edge cases handled gracefully

**Integration Tests:**
- Complete restoration cycle succeeds
- All data counts match (documents, workflows, transitions)
- Workflow states preserved correctly
- Transition history maintained

**End-to-End Tests:**
- Backup file created successfully
- System reinit clears business data
- Infrastructure preserved
- Complete restoration from backup
- All verification checks pass

### Test Metrics

**Coverage:**
- Natural key resolution: 100%
- Foreign key resolution: 100%
- Workflow restoration: 100%
- Transition restoration: 100%
- Error handling: 95%

**Performance Targets:**
- Unit tests: < 30 seconds
- Integration tests: < 2 minutes
- End-to-end test: < 5 minutes

---

## Troubleshooting

### Common Issues

#### Test Failures

**Issue**: `Document matching query does not exist`
**Cause**: Document natural key resolution not working
**Fix**: Verify `_resolve_document_natural_key` handler is present

**Issue**: `WorkflowType has no field 'code'`
**Cause**: Incorrect field reference in workflow import
**Fix**: Use `name` field instead of `code` for WorkflowType

**Issue**: `Workflows: 0 after restoration`
**Cause**: FK resolution failing for document field
**Fix**: Check document natural key handler is registered

#### Test Setup Issues

**Issue**: `Fixture 'initial_users.json' not found`
**Cause**: Missing test fixtures
**Fix**: Run `python manage.py seed_test_users` first

**Issue**: `Database transaction errors`
**Cause**: Tests not using TransactionTestCase
**Fix**: Use TransactionTestCase for integration tests

---

## Continuous Integration

### CI/CD Integration

Add to your CI pipeline:

```yaml
test-workflow-restoration:
  runs-on: ubuntu-latest
  steps:
    - name: Checkout code
      uses: actions/checkout@v2
    
    - name: Start services
      run: docker compose up -d
    
    - name: Wait for services
      run: sleep 30
    
    - name: Run backup tests
      run: ./backend/scripts/run_backup_tests.sh
    
    - name: Upload test artifacts
      if: failure()
      uses: actions/upload-artifact@v2
      with:
        name: test-results
        path: |
          backend/test-results/
          /tmp/edms_test_backups/
```

---

## Test Maintenance

### Adding New Tests

1. **Unit Test** - Add to `test_workflow_restoration.py`:
   ```python
   def test_new_feature(self):
       """Test description."""
       # Test implementation
       self.assertEqual(expected, actual)
   ```

2. **Integration Test** - Add to `test_complete_restoration_flow.py`:
   ```python
   class NewFeatureTests(TransactionTestCase):
       fixtures = ['initial_users.json']
       
       def test_new_scenario(self):
           # Test implementation
   ```

3. **Update E2E Script** - Modify `test_workflow_restoration.sh` to include new verification

### Updating Test Data

When workflow models change:
1. Update natural key handlers in `restore_processor.py`
2. Add corresponding test cases
3. Update fixture data if needed
4. Update documentation

---

## Test Results Archive

### Expected Output

**Successful Test Run:**
```
🧪 Running EDMS Backup & Restoration Test Suite
================================================

📝 Running unit tests...
test_resolve_document_natural_key ... ok
test_resolve_documentstate_natural_key ... ok
test_resolve_user_natural_key ... ok
test_resolve_documentworkflow_natural_key ... ok
test_restore_document_with_workflow ... ok
test_restore_workflow_with_transitions ... ok
...

Ran 15 tests in 25.123s

OK

📝 Running integration tests...
test_complete_restoration_cycle ... ok
test_restore_multiple_workflows ... ok
test_complete_workflow_history_preservation ... ok
...

Ran 3 tests in 45.678s

OK

📝 Running end-to-end restoration test...
✅ Test data created
✅ Backup created: 458,392 bytes
✅ System reinitialized
✅ Restore completed
✅ Test document restored: TEST-RESTORE-2025-v01.00
✅ Workflow restored: REVIEW (APPROVED state)
✅ Transitions restored: 2

🎉 ALL TESTS PASSED!
```

---

## Related Documentation

- [Backup & Restore API](../BACKUP_RESTORE_API.md)
- [Backup System Documentation](../../BACKUP_AND_RESTORE_SYSTEM_DOCUMENTATION.md)
- [Troubleshooting Guide](../BACKUP_RESTORE_TROUBLESHOOTING.md)

---

## Support

For issues with the test suite:
1. Check troubleshooting section above
2. Review test output for specific error messages
3. Verify infrastructure setup (users, states, types)
4. Check Docker logs: `docker compose logs backend`

---

**Last Updated**: 2025-12-15  
**Test Suite Version**: 1.0.0  
**EDMS Version**: Compatible with Phase II and later
