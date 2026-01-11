# ✅ READY TO TEST - Quick Start Guide

## Current System Status

**Services:** ✅ Running (backend + frontend)  
**Authentication:** ✅ Fixed and working  
**Test Documents:** ✅ 2 available  
**Workflows:** ✅ Ready to test  

---

## Quick Test Commands

### 1. Check Services
```bash
docker compose ps
```

### 2. Access the Application
- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **Admin Panel:** http://localhost:8000/admin

### 3. Test Login
```bash
# Test users
Username: admin / Password: admin123
Username: author01 / Password: Author01!
Username: reviewer01 / Password: Reviewer01!
Username: approver01 / Password: Approver01!
```

### 4. Available Documents for Testing
```
POL-2026-0002-v01.00 - Shell Test - Status: DRAFT
POL-2026-0001-v01.00 - Test - Status: DRAFT
```

---

## Workflow Testing Checklist

### ✅ What You Can Test Now

1. **Document Review Workflow**
   - [ ] Submit document for review (as author)
   - [ ] Review document (as reviewer01)
   - [ ] Approve review
   - [ ] Check notification updates

2. **Document Approval Workflow**
   - [ ] Route for approval (after review)
   - [ ] Approve document (as approver01)
   - [ ] Check status changes
   - [ ] Verify effective date scheduling

3. **Document Transitions**
   - [ ] Effective date activation (scheduled)
   - [ ] Obsolescence workflow
   - [ ] Document termination

4. **Notification System**
   - [ ] HTTP polling (every 30-60s)
   - [ ] Badge updates
   - [ ] Task list updates
   - [ ] My Tasks page

5. **Version History**
   - [ ] View document history
   - [ ] Download previous versions
   - [ ] PDF generation

---

## ❌ What's NOT Working (Document It!)

- **Document Creation via UI** - Known issue, documented in KNOWN_ISSUES.md
- **E2E tests requiring new documents** - Will fail, skip for now

---

## If You Need More Test Documents

### Option 1: Django Shell (Quick)
```bash
docker compose exec backend python manage.py shell

from apps.documents.models import Document, DocumentType, DocumentSource
from apps.users.models import User

Document.objects.create(
    title="Test Document 3",
    description="Additional test document",
    author=User.objects.get(username='author01'),
    document_type=DocumentType.objects.get(id=13),
    document_source=DocumentSource.objects.get(id=8),
    priority='normal',
    requires_training=False,
    is_controlled=True
)
```

### Option 2: Django Admin Panel
1. Go to http://localhost:8000/admin
2. Login as admin / admin123
3. Navigate to Documents → Add document
4. Fill in form and save

---

## Testing Priority

**High Priority (Test First):**
1. Authentication - ✅ Already fixed
2. Document review workflow
3. Document approval workflow
4. Notifications

**Medium Priority:**
5. Effective date transitions
6. Version history
7. PDF downloads

**Low Priority (Known Issues):**
8. Document creation via UI - Skip for now
9. E2E tests requiring new docs - Skip for now

---

## 🎯 Your Original Question

> "we are in the process of testing the workflow. there is an error when creating document"

**Answer:** 
- ✅ The AUTH error is FIXED (can get user ID)
- ⚠️ Document creation has a DIFFERENT issue (FK serialization)
- ✅ You CAN test workflows with the 2 existing documents
- 🚀 Continue testing - come back to creation later!

---

**Ready to test workflows! Start with document review → approval flow.**
