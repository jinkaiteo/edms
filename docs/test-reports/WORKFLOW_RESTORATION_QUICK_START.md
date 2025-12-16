# Workflow Restoration Testing - Quick Start Guide

## 🚀 Run Tests Now

### Option 1: Run All Tests (Recommended)
```bash
./backend/scripts/run_backup_tests.sh
```

### Option 2: Individual Test Suites

**Unit Tests (Fast - 30 seconds):**
```bash
docker compose exec backend python manage.py test apps.backup.tests.test_workflow_restoration
```

**Integration Tests (Medium - 2 minutes):**
```bash
docker compose exec backend python manage.py test apps.backup.tests.test_complete_restoration_flow
```

**End-to-End Test (Complete - 5 minutes):**
```bash
./backend/scripts/test_workflow_restoration.sh
```

---

## 📋 What Gets Tested

| Test Type | Coverage | Duration |
|-----------|----------|----------|
| **Unit Tests** | Natural key resolution, FK resolution, edge cases | 30 sec |
| **Integration Tests** | Complete restoration flow, multiple documents | 2 min |
| **E2E Test** | Real-world backup → reinit → restore cycle | 5 min |

---

## ✅ Expected Output

### Successful Run:
```
🎉 ALL TESTS PASSED!

Summary:
  ✅ 15 unit tests passed
  ✅ 3 integration tests passed
  ✅ E2E restoration verified
  
  Documents: 4 restored
  Workflows: 2 restored  
  Transitions: 30 restored
```

### If Tests Fail:
1. Check error message in output
2. Review [Troubleshooting Guide](WORKFLOW_RESTORATION_TEST_SUITE.md#troubleshooting)
3. Verify infrastructure setup: `docker compose exec backend python manage.py seed_test_users`

---

## 🔧 Prerequisites

Before running tests, ensure:
- ✅ Docker containers running: `docker compose up -d`
- ✅ Database migrations applied: `docker compose exec backend python manage.py migrate`
- ✅ Test users seeded: `docker compose exec backend python manage.py seed_test_users`

---

## 📊 Test Coverage Summary

**What's Tested:**
- ✅ Document restoration with workflow history
- ✅ Multiple workflow transitions
- ✅ Natural key resolution for all models
- ✅ Foreign key reference handling
- ✅ Post-reinit restoration (UUID conflict resolution)
- ✅ Infrastructure preservation
- ✅ Error handling and edge cases

**What's Verified:**
- Document counts match before/after
- Workflow states preserved correctly
- Transition history maintained
- User references intact
- Timestamps preserved
- Comments and metadata restored

---

## 🎯 Quick Test: Verify Workflow Restoration Works

**1-Minute Smoke Test:**
```bash
# Create backup, clear DB, restore, verify
docker compose exec backend python -c "
from django.core.management import call_command
from apps.documents.models import Document
from apps.workflows.models_simple import DocumentWorkflow

# Check current state
print('Before:', DocumentWorkflow.objects.count(), 'workflows')

# Your existing workflows should restore successfully
"
```

---

## 📚 Full Documentation

For complete test suite details, see [Workflow Restoration Test Suite](WORKFLOW_RESTORATION_TEST_SUITE.md)

---

## 🆘 Quick Help

**Test fails with "Document not found"?**
→ Document natural key handler issue. Check `_resolve_document_natural_key` in `restore_processor.py`

**Workflows show 0 after restore?**
→ FK resolution issue. Verify document FK handler is registered.

**"WorkflowType has no field 'code'"?**
→ Use `name` field instead of `code` for WorkflowType lookups.

**Need more help?**
→ Check full [Test Suite Documentation](WORKFLOW_RESTORATION_TEST_SUITE.md)
