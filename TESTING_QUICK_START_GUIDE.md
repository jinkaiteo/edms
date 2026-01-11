# 🚀 EDMS Testing Quick Start Guide

## 📊 **Current Test Status**

### **Test Files Summary**
- **Total Backend Test Files**: 13 (5 new + 8 existing)
- **Total E2E Test Files**: 16 (3 new + 13 existing)
- **Total Test Code**: ~3,116 lines of backend tests + ~1,348 lines of E2E tests

---

## ✅ **What Was Created**

### **New Backend Unit Tests (8 files, ~1,793 lines)**

1. **`backend/apps/workflows/tests/test_versioning_workflow.py`** (376 lines)
   - 15 comprehensive versioning tests
   
2. **`backend/apps/workflows/tests/test_obsolescence_workflow.py`** (181 lines)
   - 8 obsolescence workflow tests
   
3. **`backend/apps/workflows/tests/test_termination_workflow.py`** (235 lines)
   - 9 termination workflow tests
   
4. **`backend/apps/documents/tests/test_document_dependencies.py`** (306 lines)
   - 14 dependency management tests
   
5. **`backend/apps/scheduler/tests/test_document_activation.py`** (213 lines)
   - 8 scheduler activation tests
   
6. **`backend/apps/scheduler/tests/test_obsolescence_automation.py`** (113 lines)
   - 3 scheduler obsolescence tests
   
7. **`backend/apps/workflows/tests/test_workflow_notifications.py`** (125 lines)
   - 6 notification tests (placeholders)
   
8. **`backend/apps/audit/tests/test_workflow_audit_trail.py`** (244 lines)
   - 10 audit trail tests

### **New E2E Tests (3 files, ~496 lines)**

9. **`e2e/workflows_complete/04_document_versioning.spec.ts`** (167 lines)
   - 4 versioning E2E scenarios
   
10. **`e2e/workflows_complete/05_document_obsolescence.spec.ts`** (135 lines)
    - 3 obsolescence E2E scenarios
    
11. **`e2e/workflows_complete/06_document_termination.spec.ts`** (194 lines)
    - 4 termination E2E scenarios

---

## 🎯 **How to Run Tests**

### **Option 1: Run All New Tests Together**

```bash
# Backend tests - all new workflow tests
cd backend
pytest apps/workflows/tests/test_versioning_workflow.py \
       apps/workflows/tests/test_obsolescence_workflow.py \
       apps/workflows/tests/test_termination_workflow.py \
       apps/documents/tests/test_document_dependencies.py \
       apps/scheduler/tests/ \
       apps/workflows/tests/test_workflow_notifications.py \
       apps/audit/tests/test_workflow_audit_trail.py \
       -v --tb=short

# E2E tests - all new workflow tests
npx playwright test e2e/workflows_complete/04_document_versioning.spec.ts \
                    e2e/workflows_complete/05_document_obsolescence.spec.ts \
                    e2e/workflows_complete/06_document_termination.spec.ts
```

### **Option 2: Run by Category**

#### **Document Versioning**
```bash
# Backend
pytest apps/workflows/tests/test_versioning_workflow.py -v

# E2E
npx playwright test e2e/workflows_complete/04_document_versioning.spec.ts
```

#### **Document Obsolescence**
```bash
# Backend
pytest apps/workflows/tests/test_obsolescence_workflow.py -v

# E2E
npx playwright test e2e/workflows_complete/05_document_obsolescence.spec.ts
```

#### **Document Termination**
```bash
# Backend
pytest apps/workflows/tests/test_termination_workflow.py -v

# E2E
npx playwright test e2e/workflows_complete/06_document_termination.spec.ts
```

#### **Document Dependencies**
```bash
pytest apps/documents/tests/test_document_dependencies.py -v
```

#### **Scheduler Automation**
```bash
pytest apps/scheduler/tests/test_document_activation.py -v
pytest apps/scheduler/tests/test_obsolescence_automation.py -v
```

#### **Audit Trail**
```bash
pytest apps/audit/tests/test_workflow_audit_trail.py -v
```

### **Option 3: Run Complete Test Suite**

```bash
# All backend tests with coverage
cd backend
pytest --cov=apps --cov-report=html --cov-report=term-missing

# All E2E tests
npx playwright test
```

---

## 🔍 **Expected Results**

### **Tests That Should Pass Immediately:**
✅ **Document Dependencies** - Uses existing Document model
✅ **Audit Trail** (most tests) - Uses existing audit infrastructure
✅ **Termination** (if `Document.terminate_document()` exists)

### **Tests That May Need Implementation:**

#### **1. Document Versioning** ⚠️
**Required**: `lifecycle_service.start_version_workflow()`

If missing, implement in `backend/apps/workflows/document_lifecycle.py`:
```python
def start_version_workflow(self, existing_document, user, new_version_data):
    """Create new document version"""
    if existing_document.status != 'EFFECTIVE':
        return {'success': False, 'error': 'Only EFFECTIVE documents can be versioned'}
    
    version_type = new_version_data.get('version_type', 'major')
    
    # Create new document
    new_doc = Document.objects.create(
        title=new_version_data.get('title', existing_document.title),
        description=existing_document.description,
        document_type=existing_document.document_type,
        document_source=existing_document.document_source,
        author=user,
        status='DRAFT',
        version_major=existing_document.version_major + 1 if version_type == 'major' else existing_document.version_major,
        version_minor=0 if version_type == 'major' else existing_document.version_minor + 1,
        reason_for_change=new_version_data.get('reason_for_change', ''),
        supersedes=existing_document
    )
    
    return {'success': True, 'new_document': new_doc}
```

#### **2. Document Obsolescence** ⚠️
**Required**: `lifecycle_service.start_obsolete_workflow()`

If missing, implement:
```python
def start_obsolete_workflow(self, document, user, reason, target_date=None):
    """Mark document for obsolescence"""
    if document.status != 'EFFECTIVE':
        return None
    
    if not target_date:
        target_date = date.today()
    
    document.status = 'SCHEDULED_FOR_OBSOLESCENCE'
    document.obsolescence_date = target_date
    document.obsolescence_reason = reason
    document.obsoleted_by = user
    document.save()
    
    return DocumentWorkflow.objects.create(
        document=document,
        workflow_type='OBSOLESCENCE',
        initiated_by=user
    )
```

#### **3. Scheduler Tasks** ⚠️
**Required**: `apps/scheduler/automated_tasks.py`

If missing, create:
```python
from celery import shared_task
from datetime import date
from apps.documents.models import Document

@shared_task
def activate_pending_documents():
    """Activate documents that have reached their effective date"""
    today = date.today()
    
    documents = Document.objects.filter(
        status='APPROVED_PENDING_EFFECTIVE',
        effective_date__lte=today
    )
    
    count = 0
    for doc in documents:
        doc.status = 'EFFECTIVE'
        doc.save()
        count += 1
    
    return f"Activated {count} documents"

@shared_task
def process_scheduled_obsolescence():
    """Mark documents obsolete that have reached obsolescence date"""
    today = date.today()
    
    documents = Document.objects.filter(
        status='SCHEDULED_FOR_OBSOLESCENCE',
        obsolescence_date__lte=today
    )
    
    count = 0
    for doc in documents:
        doc.status = 'OBSOLETE'
        doc.save()
        count += 1
    
    return f"Marked {count} documents obsolete"
```

---

## 🐛 **Troubleshooting**

### **Issue: Tests fail with "No module named 'apps'"**
```bash
# Solution: Run from backend directory
cd backend
pytest apps/workflows/tests/test_versioning_workflow.py -v
```

### **Issue: "fixture 'db' not found"**
```bash
# Solution: Install pytest-django
pip install pytest-django
```

### **Issue: E2E tests can't connect to localhost:3001**
```bash
# Solution: Start the application first
docker-compose up -d

# Or update baseURL in playwright.config.ts
```

### **Issue: "LifecycleService has no attribute 'start_version_workflow'"**
```bash
# Solution: Implement the missing method (see above)
# Or skip those tests for now:
pytest -k "not version" apps/workflows/tests/
```

---

## 📊 **Test Coverage Report**

### **Generate Coverage Report**
```bash
cd backend
pytest --cov=apps \
       --cov-report=html \
       --cov-report=term-missing \
       --cov-fail-under=80

# View HTML report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

### **Coverage by Module**
```bash
# Specific module coverage
pytest --cov=apps.workflows --cov-report=term

pytest --cov=apps.documents --cov-report=term

pytest --cov=apps.scheduler --cov-report=term
```

---

## 🎨 **Test Output Examples**

### **Successful Test Run**
```
================================ test session starts ================================
collected 15 items

apps/workflows/tests/test_versioning_workflow.py::TestDocumentVersioning::test_create_major_version_from_effective_document PASSED [  6%]
apps/workflows/tests/test_versioning_workflow.py::TestDocumentVersioning::test_create_minor_version_from_effective_document PASSED [ 13%]
apps/workflows/tests/test_versioning_workflow.py::TestDocumentVersioning::test_cannot_version_non_effective_document PASSED [ 20%]
...

================================ 15 passed in 2.34s =================================
```

### **Test Failure Example**
```
FAILED apps/workflows/tests/test_versioning_workflow.py::TestDocumentVersioning::test_create_major_version_from_effective_document

AttributeError: 'DocumentLifecycleService' object has no attribute 'start_version_workflow'
```
**Fix**: Implement the missing method in `document_lifecycle.py`

---

## 🔧 **Customizing Tests**

### **Run Specific Test Method**
```bash
pytest apps/workflows/tests/test_versioning_workflow.py::TestDocumentVersioning::test_create_major_version_from_effective_document -v
```

### **Run Tests Matching Pattern**
```bash
# All tests with "version" in name
pytest -k "version" -v

# All tests with "obsolete" in name
pytest -k "obsolete" -v

# All tests except notifications
pytest -k "not notification" -v
```

### **Run Tests with Different Verbosity**
```bash
# Quiet (only show failures)
pytest -q

# Verbose (show each test)
pytest -v

# Very verbose (show each test + output)
pytest -vv
```

### **Run Tests with Debugging**
```bash
# Stop on first failure
pytest -x

# Drop into debugger on failure
pytest --pdb

# Show local variables on failure
pytest -l
```

---

## 📈 **Performance Testing**

### **Test Execution Time**
```bash
# Show slowest tests
pytest --durations=10

# Show all test durations
pytest --durations=0
```

### **Parallel Execution**
```bash
# Install pytest-xdist
pip install pytest-xdist

# Run tests in parallel
pytest -n auto
```

---

## 🎯 **CI/CD Integration**

### **GitHub Actions Example**
Add to `.github/workflows/test.yml`:

```yaml
- name: Run New Workflow Tests
  run: |
    cd backend
    pytest apps/workflows/tests/test_versioning_workflow.py \
           apps/workflows/tests/test_obsolescence_workflow.py \
           apps/workflows/tests/test_termination_workflow.py \
           apps/documents/tests/test_document_dependencies.py \
           apps/scheduler/tests/ \
           apps/audit/tests/ \
           --cov=apps \
           --cov-report=xml \
           --cov-fail-under=80

- name: Upload Coverage
  uses: codecov/codecov-action@v3
  with:
    file: ./backend/coverage.xml
```

---

## 📚 **Additional Resources**

### **Test Documentation**
- `TEST_SUITE_SUMMARY.md` - Complete test suite overview
- `AUTOMATED_TESTING_PLAN.md` - Original testing plan
- `tests/README.md` - E2E test documentation

### **Workflow Documentation**
- `REVIEW_AND_APPROVAL_PROCESS_GUIDE.md` - Workflow explanation
- `CURRENT_WORKFLOW_ARCHITECTURE_2025.md` - System architecture

### **API Documentation**
- `API_ARCHITECTURE_DOCUMENTATION.md` - API reference

---

## ✅ **Verification Checklist**

Before finalizing, verify:

- [ ] All test files are in correct directories
- [ ] All `__init__.py` files exist in test directories
- [ ] Tests can import required modules
- [ ] Database migrations are up to date
- [ ] Test users exist in database
- [ ] Document types and sources exist
- [ ] Services implement required methods
- [ ] Scheduler tasks are registered in Celery

---

## 🎉 **Success Metrics**

**Target Coverage**: 80%+

**Expected Results After Implementation**:
- ✅ 100+ test scenarios passing
- ✅ All workflow paths tested
- ✅ 85%+ code coverage
- ✅ Zero critical bugs in workflows
- ✅ Full compliance audit trail

---

## 🆘 **Getting Help**

### **Test Issues**
1. Check test output for specific error
2. Verify required methods exist
3. Check database state
4. Review implementation examples above

### **Implementation Questions**
1. Review existing workflow tests for patterns
2. Check `document_lifecycle.py` for similar methods
3. Consult workflow documentation

### **CI/CD Issues**
1. Verify GitHub Actions workflow file
2. Check test environment variables
3. Review CI logs for specific errors

---

**Ready to test! Run the commands above to verify your EDMS workflows are working correctly.** 🚀
