# 🔧 Migration Fix Script Guide

## 📋 **What the Script Does**

The `fix_migrations_and_test.sh` script automates the entire process:

1. ✅ Checks Docker container status
2. ✅ Detects unapplied model changes
3. ✅ Creates new migrations (with confirmation)
4. ✅ Applies all migrations to database
5. ✅ Verifies schema is up-to-date
6. ✅ Runs complete test suite
7. ✅ Generates detailed test results report

---

## 🚀 **How to Use**

### **Quick Start**
```bash
# Make it executable (already done)
chmod +x fix_migrations_and_test.sh

# Run it
./fix_migrations_and_test.sh
```

### **What Happens**

1. **Container Check** - Verifies backend container is running
2. **Migration Detection** - Shows what needs to be migrated
3. **Confirmation Prompt** - Asks "Do you want to create migrations? [y/N]"
4. **Migration Creation** - Creates migration files automatically
5. **Migration Application** - Applies migrations to database
6. **Test Execution** - Runs all 65+ tests
7. **Results Summary** - Shows pass/fail/error counts

---

## 📊 **Expected Output**

### **Phase 1: Migration Check**
```
[1/7] Checking Docker container...
✓ Container edms_prod_backend is running

[2/7] Checking current migration status...
  → Listing applied migrations...
workflows
 [X] 0001_initial
 [X] 0002_documentstate_documentworkflow
 ...

[3/7] Detecting unapplied model changes...
⚠ Model changes detected that need migrations

Preview of changes:
  Migrations for 'workflows':
    - Add field is_read to workflownotification
  Migrations for 'documents':
    - Alter field status on document
```

### **Phase 2: Migration Creation**
```
Do you want to create and apply these migrations? [y/N]
y

[4/7] Creating migrations...
Creating migrations (answering migration questions automatically)...
Migrations for 'workflows':
  0009_workflownotification_is_read.py
    - Add field is_read to workflownotification
✓ Migrations created
```

### **Phase 3: Migration Application**
```
[5/7] Applying migrations...
  → Running migrate command...
Operations to perform:
  Apply all migrations: workflows, documents, scheduler
Running migrations:
  Applying workflows.0009_workflownotification_is_read... OK
✓ Migrations applied
```

### **Phase 4: Test Results**
```
[7/7] Running tests...

╔══════════════════════════════════════════════════════════════════════════════╗
║                          RUNNING TEST SUITE                                  ║
╚══════════════════════════════════════════════════════════════════════════════╝

Running quick smoke test...
✓ Smoke test completed (tests are running!)

Running full test suite...

apps/workflows/tests/test_versioning_workflow.py::test_create_major_version... FAILED
apps/workflows/tests/test_versioning_workflow.py::test_create_minor_version... FAILED
apps/documents/tests/test_document_dependencies.py::test_add_dependency... PASSED
apps/documents/tests/test_document_dependencies.py::test_circular_dependency... PASSED
...

╔══════════════════════════════════════════════════════════════════════════════╗
║                         TEST RESULTS SUMMARY                                 ║
╚══════════════════════════════════════════════════════════════════════════════╝

✓ Passed:  45
✗ Failed:  15
✗ Errors:  5
Total:     65

Pass Rate: 69%
```

---

## 🎯 **Expected Results**

### **Best Case (All Migrations Needed)**
- ✅ Creates 2-5 new migration files
- ✅ Applies migrations successfully
- ✅ 45-50 tests pass (70%)
- ❌ 15-20 tests fail (30% - need implementation)

### **Good Case (Some Migrations)**
- ✅ Creates 1-2 migration files
- ✅ Applies successfully
- ✅ 40-45 tests pass (65%)
- ❌ 20-25 tests fail (need implementation)

### **Ideal Case (No Migrations Needed)**
- ℹ️ No model changes detected
- ✅ Tests run immediately
- ✅ 45-50 tests pass
- ❌ 15-20 tests fail

---

## ❌ **If Script Fails**

### **Issue 1: Migration Questions Require Manual Input**

**Symptom:**
```
Was scheduledtask.is_running renamed to scheduledtask.completed? [y/N]
```

**Solution:**
Script will automatically try interactive mode. Answer the questions:
- "Was X renamed to Y?" - Check your model and answer honestly
- "Did you delete field Z?" - Answer based on your changes
- "Did you add field A?" - Confirm if you added it

### **Issue 2: Container Not Running**

**Error:**
```
✗ Error: Container edms_prod_backend is not running
```

**Solution:**
```bash
docker-compose up -d backend
./fix_migrations_and_test.sh
```

### **Issue 3: Permission Denied**

**Error:**
```bash
bash: ./fix_migrations_and_test.sh: Permission denied
```

**Solution:**
```bash
chmod +x fix_migrations_and_test.sh
./fix_migrations_and_test.sh
```

---

## 📈 **Understanding Test Results**

### **✅ Tests That Should Pass (45-50 tests)**

1. **Document Dependencies (12 tests)**
   - Add dependency
   - Circular dependency prevention
   - Multiple dependencies
   - Dependency types

2. **Audit Trail (8-10 tests)**
   - Audit entry creation
   - User tracking
   - Timestamp recording

3. **Basic Validations (10-15 tests)**
   - Permission checks
   - Status validation
   - Field validation

4. **Model Operations (10-15 tests)**
   - CRUD operations
   - Model relationships
   - Data integrity

### **❌ Tests That Will Fail (15-20 tests)**

1. **Versioning Workflow (11 tests)** ❌
   - Needs: `lifecycle_service.start_version_workflow()`
   - Error: `AttributeError: 'DocumentLifecycleService' object has no attribute 'start_version_workflow'`

2. **Obsolescence Workflow (8 tests)** ❌
   - Needs: `lifecycle_service.start_obsolete_workflow()`
   - Error: Similar AttributeError

3. **Termination Workflow (7 tests)** ❌
   - Needs: `Document.terminate_document()` method
   - Error: `AttributeError: 'Document' object has no attribute 'terminate_document'`

4. **Scheduler Tests (8 tests)** ❌
   - Needs: `activate_pending_documents()` Celery task
   - Error: `ImportError: cannot import name 'activate_pending_documents'`

---

## 🔍 **Analyzing Failures**

### **After Script Runs:**

```bash
# View detailed report
cat test_results_*.txt

# Run specific failing test with more detail
docker exec edms_prod_backend python -m pytest \
  apps/workflows/tests/test_versioning_workflow.py::TestDocumentVersioning::test_create_major_version_from_effective_document \
  -vv --tb=long

# Check what methods are missing
docker exec edms_prod_backend python manage.py shell << 'EOF'
from apps.workflows.document_lifecycle import get_document_lifecycle_service
service = get_document_lifecycle_service()
print(dir(service))
EOF
```

---

## 🛠️ **Quick Fixes for Common Failures**

### **1. Implement start_version_workflow()**

Add to `backend/apps/workflows/document_lifecycle.py`:

```python
def start_version_workflow(self, existing_document, user, new_version_data):
    """Create new document version"""
    if existing_document.status != 'EFFECTIVE':
        return {'success': False, 'error': 'Only EFFECTIVE documents can be versioned'}
    
    version_type = new_version_data.get('version_type', 'major')
    
    new_doc = Document.objects.create(
        title=new_version_data.get('title', existing_document.title),
        description=existing_document.description,
        document_type=existing_document.document_type,
        document_source=existing_document.document_source,
        author=user,
        status='DRAFT',
        version_major=existing_document.version_major + 1 if version_type == 'major' else existing_document.version_major,
        version_minor=0 if version_type == 'major' else existing_document.version_minor + 1,
        reason_for_change=new_version_data.get('reason_for_change', '')
    )
    
    return {'success': True, 'new_document': new_doc}
```

### **2. Implement start_obsolete_workflow()**

Add to `backend/apps/workflows/document_lifecycle.py`:

```python
def start_obsolete_workflow(self, document, user, reason, target_date=None):
    """Mark document for obsolescence"""
    if document.status != 'EFFECTIVE':
        return None
    
    document.status = 'SCHEDULED_FOR_OBSOLESCENCE'
    document.obsolescence_date = target_date or date.today()
    document.obsolescence_reason = reason
    document.obsoleted_by = user
    document.save()
    
    return document
```

### **3. Implement terminate_document()**

Add to `backend/apps/documents/models.py` in Document class:

```python
def terminate_document(self, terminated_by, reason):
    """Terminate document before it becomes effective"""
    if self.status == 'EFFECTIVE':
        raise ValueError("Cannot terminate effective documents")
    
    if self.author != terminated_by:
        raise ValueError("Only author can terminate document")
    
    self.status = 'TERMINATED'
    self.obsoleted_by = terminated_by
    self.obsolescence_reason = f'TERMINATED: {reason}'
    self.is_active = False
    self.save()
    
    return True
```

---

## 📊 **Success Metrics**

### **Good Result:**
- ✅ Migrations applied successfully
- ✅ 40+ tests passing (60%+)
- ✅ Failures are due to missing implementations (expected)
- ✅ No database errors

### **Excellent Result:**
- ✅ Migrations applied successfully
- ✅ 50+ tests passing (75%+)
- ✅ Only implementation-related failures
- ✅ All infrastructure tests passing

---

## 🎉 **Next Steps After Running**

1. **Review Results** - Check pass/fail counts
2. **Implement Missing Methods** - Use guides above
3. **Re-run Tests** - `./fix_migrations_and_test.sh` again
4. **Iterate Until 80%+** - Keep implementing until pass rate > 80%

---

## 📝 **Files Generated**

- `test_results_YYYYMMDD_HHMMSS.txt` - Full test output
- Migration files in `backend/apps/*/migrations/` (if created)

---

**Ready to run?** Execute: `./fix_migrations_and_test.sh` 🚀
