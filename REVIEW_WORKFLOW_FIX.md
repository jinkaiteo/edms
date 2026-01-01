# Review Workflow 500 Error - Fix Documentation

## 🔍 Problem Summary

**Issue:** Document submission for review fails with HTTP 500 Internal Server Error

```
POST http://172.28.1.148:3001/api/v1/workflows/documents/ea462429-29b2-4723-9eb5-fe0e84cabf2e/submit-for-review-enhanced/
[HTTP/1.1 500 Internal Server Error 39ms]
```

**Frontend Error:**
```javascript
💥 Error in submit_for_review: Error: HTTP 500
💥 Error response: undefined
```

**Impact:** Authors cannot submit documents for review, blocking the entire workflow process.

---

## 🎯 Root Cause Analysis

The `submit_for_review_enhanced` endpoint in `backend/apps/workflows/rejection_api_views.py` had **insufficient error handling and logging**, making it impossible to diagnose failures. The likely causes:

1. **Missing DocumentStates or WorkflowTypes** - Database initialization not complete
2. **Reviewer roles not properly assigned** - reviewer01/approver01 have incorrect permissions
3. **Silent exceptions** - Errors were caught but not logged, returning generic 500 errors

---

## ✅ Solution Implemented

### 1. Enhanced Error Handling (`rejection_api_views.py`)

**Added:**
- Comprehensive logging at every step
- Detailed exception tracebacks in responses (for debugging)
- Non-blocking error handling for recommendation system
- Step-by-step logging to pinpoint exact failure point

**Key Changes:**
```python
import traceback
import logging

logger = logging.getLogger(__name__)

# Added logging throughout:
logger.info(f"submit_for_review_enhanced called for document {document_id}")
logger.info(f"Document found: {document.document_number}, Status: {document.status}")
logger.info(f"Reviewer found: {reviewer.username}")

# Non-blocking recommendations (won't fail entire submission):
try:
    recommendations = lifecycle_service.get_assignment_recommendations(document)
except Exception as rec_error:
    logger.warning(f"Error getting recommendations (non-critical): {str(rec_error)}")
    # Continue without recommendations
```

### 2. Debug Script (`scripts/debug-review-workflow.sh`)

Created comprehensive diagnostic script that checks:
- Document existence and current status
- Reviewer user existence and role assignments
- DocumentState and WorkflowType configuration
- Direct test of `submit_for_review` function
- Backend logs for error messages

### 3. Deployment Script (`scripts/deploy-review-fix.sh`)

Automated deployment process:
- Pull latest code
- Restart backend container
- Run debug verification
- Show relevant logs

---

## 🚀 Deployment Instructions

### On Staging Server (172.28.1.148)

```bash
cd /home/lims/edms-staging

# 1. Pull the fix
git pull origin develop

# 2. Deploy using automated script
bash scripts/deploy-review-fix.sh

# Or manually:
docker compose -f docker-compose.prod.yml restart backend
sleep 30
bash scripts/debug-review-workflow.sh
```

---

## 🔧 Verification Steps

### Step 1: Run Debug Script

```bash
bash scripts/debug-review-workflow.sh
```

**Expected Output:**
```
✓ Document found: SOP-2025-0001
  - Status: DRAFT
  - Author: author01
  - Reviewer: reviewer01
  
✓ User found: reviewer01 (Reviewer One)
  - Roles:
    * Document Reviewer (Module: O1, Level: review)
  - Can review documents: True

✓ DocumentStates:
  - DRAFT: Draft
  - PENDING_REVIEW: Pending Review
  - UNDER_REVIEW: Under Review
  ... (more states)

✓ WorkflowTypes:
  - REVIEW: Document Review (Active: True)
  ... (more types)
```

### Step 2: Check Backend Logs

After attempting to submit document from frontend:

```bash
docker compose -f docker-compose.prod.yml logs -f backend | grep "submit_for_review"
```

**You should see:**
```
submit_for_review_enhanced called for document ea462429-29b2-4723-9eb5-fe0e84cabf2e
User: author01, Data: {'reviewer_id': 3, 'comment': '', 'acknowledge_warnings': False}
Document found: SOP-2025-0001, Status: DRAFT
Reviewer found: reviewer01 (Reviewer One)
Getting assignment recommendations...
Assigning reviewer reviewer01 to document
Document saved with reviewer assignment
Calling lifecycle_service.submit_for_review...
🔍 submit_for_review called for SOP-2025-0001
   Document status: DRAFT
   User: author01
   Reviewer assigned: reviewer01
🔄 Transitioning workflow from DRAFT to PENDING_REVIEW...
✅ Document status after transition: PENDING_REVIEW
submit_for_review returned: True
Document status after submit: PENDING_REVIEW
```

### Step 3: Test from Frontend

1. Login as **author01** (password: test123)
2. Navigate to "My Documents"
3. Find a DRAFT document
4. Click "Submit for Review"
5. Select **reviewer01** from dropdown
6. Click "Submit"

**Expected Result:**
- ✅ Success message: "Document submitted for review successfully"
- ✅ Document status changes to "Pending Review"
- ✅ Reviewer receives notification (if notifications configured)

---

## 🐛 Troubleshooting

### Issue: Still getting 500 error after fix

**Check 1: DocumentStates not initialized**
```bash
docker compose -f docker-compose.prod.yml exec backend python manage.py shell
>>> from apps.workflows.models import DocumentState
>>> DocumentState.objects.count()
```

If returns `0`, run:
```bash
docker compose -f docker-compose.prod.yml exec backend python manage.py migrate
```

**Check 2: Reviewer has no roles**
```bash
bash scripts/fix-reviewer-approver-roles.sh
```

**Check 3: Backend logs show specific error**
```bash
docker compose -f docker-compose.prod.yml logs --tail=50 backend
```

Look for the actual exception and traceback.

---

## 📋 Related Issues and Fixes

### 1. Reviewer/Approver Role Assignments

**Issue:** reviewer01 and approver01 have incorrect roles on staging

**Fix:**
```bash
bash scripts/fix-reviewer-approver-roles.sh
```

### 2. Missing System Defaults

**Issue:** DocumentStates, WorkflowTypes, or Roles not initialized

**Fix:**
```bash
docker compose -f docker-compose.prod.yml exec backend python manage.py migrate
docker compose -f docker-compose.prod.yml exec backend python manage.py create_default_roles
docker compose -f docker-compose.prod.yml exec backend python manage.py create_default_groups
```

---

## 🎯 Testing Checklist

After deploying the fix, verify:

- [ ] Debug script runs without errors
- [ ] Document exists in database with DRAFT status
- [ ] Reviewer user exists with correct roles (O1/review permission)
- [ ] DocumentStates exist (at least 10+ states)
- [ ] WorkflowTypes exist (at least REVIEW type)
- [ ] Backend logs show detailed step-by-step execution
- [ ] Frontend can submit document successfully
- [ ] Document transitions to PENDING_REVIEW status
- [ ] No 500 errors in backend logs

---

## 📝 Changes Made

### Files Modified:
1. `backend/apps/workflows/rejection_api_views.py` - Enhanced error handling and logging
2. `scripts/debug-review-workflow.sh` - New diagnostic script
3. `scripts/deploy-review-fix.sh` - New deployment script

### Backup:
Original file backed up to: `backend/apps/workflows/rejection_api_views.py.backup`

---

## 🔄 Rollback Instructions

If the fix causes issues:

```bash
cd /home/lims/edms-staging
mv backend/apps/workflows/rejection_api_views.py.backup backend/apps/workflows/rejection_api_views.py
docker compose -f docker-compose.prod.yml restart backend
```

---

## 📚 References

- Original error in frontend console
- `backend/apps/workflows/document_lifecycle.py` - Core workflow logic
- `backend/apps/workflows/models.py` - DocumentWorkflow, DocumentState models
- Git commit: `c5a7194` - Fix reviewer/approver role assignments

---

## ✅ Success Criteria

The fix is successful when:

1. ✅ Backend logs show detailed execution flow
2. ✅ Any errors show specific exception messages and tracebacks
3. ✅ Frontend receives proper error messages (not undefined)
4. ✅ Documents can be successfully submitted for review
5. ✅ No generic 500 errors without explanation

---

**Date:** 2026-01-01  
**Server:** 172.28.1.148 (staging)  
**Status:** Ready for deployment
