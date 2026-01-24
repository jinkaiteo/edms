# Email Notification Flow Analysis - Review/Approval Workflow

**Date:** January 24, 2026  
**Issue:** Incorrect email subjects and recipients in review/approval workflow  
**Status:** ⚠️ **ISSUES IDENTIFIED - FIX REQUIRED**

---

## 🔍 Problem Summary

Based on user observation:
1. **When author submits document for review:** Reviewer receives email ✅ CORRECT
2. **When reviewer approves document:** Reviewer receives ANOTHER email ❌ WRONG
3. **Author notification:** Does receive email ✅ CORRECT

**Issue:** The reviewer is receiving an incorrect "New Task Assigned" email after completing the review, when the task should go back to the author to route for approval.

---

## 📊 Current Email Notification Flow

### Step 1: Author Submits for Review
```
Author → submit_for_review() → Reviewer
```

**What happens:**
1. Document transitions: `DRAFT` → `PENDING_REVIEW`
2. `_transition_workflow()` is called with `assignee=document.reviewer`
3. `_create_workflow_task_for_assignee()` creates task for reviewer
4. `_send_task_notification_simple()` sends email to reviewer

**Email sent to:** ✅ Reviewer (CORRECT)  
**Email subject:** `"New Task Assigned: REVIEW"`  
**Email purpose:** Notify reviewer they have a review task

---

### Step 2: Reviewer Completes Review (Approved)
```
Reviewer → complete_review(approved=True) → Author
```

**What happens:**
1. Document transitions: `UNDER_REVIEW` → `REVIEW_COMPLETED`
2. `_transition_workflow()` is called with `assignee=document.author` (line 257)
3. ❌ **PROBLEM:** `_create_workflow_task_for_assignee()` creates task for author
4. ❌ **PROBLEM:** BUT the task_type_map has `'REVIEW_COMPLETED': 'REVIEW'` (line 1625)
5. ❌ **PROBLEM:** So it sends email with subject `"New Task Assigned: REVIEW"` to author

**Additionally:**
6. `author_notification_service.notify_author_review_completed()` sends CORRECT email to author
   - Subject: `"Review Approved: {doc_number} - Action Required"`
   - Message: Explains need to route for approval

**Result:**
- ✅ Author receives CORRECT notification about review approval
- ❌ BUT ALSO receives INCORRECT "New Task Assigned: REVIEW" email
- ❌ This creates confusion - two emails with different messages

**Current behavior:**
```
Email 1 to Author: "New Task Assigned: REVIEW" (WRONG - sounds like review task)
Email 2 to Author: "Review Approved: SOP-2026-0001 - Action Required" (CORRECT)
```

---

### Step 3: Author Routes for Approval
```
Author → route_for_approval() → Approver
```

**What happens:**
1. Document transitions: `REVIEW_COMPLETED` → `PENDING_APPROVAL`
2. `_transition_workflow()` is called with `assignee=approver`
3. `_create_workflow_task_for_assignee()` creates task for approver
4. Task type determined from map: `'PENDING_APPROVAL': 'APPROVE'` ✅
5. `_send_task_notification_simple()` sends email to approver

**Email sent to:** ✅ Approver (CORRECT)  
**Email subject:** `"New Task Assigned: APPROVE"`  
**Email purpose:** Notify approver they have an approval task

---

### Step 4: Approver Approves Document
```
Approver → approve_document() → Author (notification only)
```

**What happens:**
1. Document transitions: `PENDING_APPROVAL` → `APPROVED_PENDING_EFFECTIVE` or `EFFECTIVE`
2. No assignee set (approval is final step)
3. ✅ NO task creation
4. ✅ NO incorrect email sent
5. Author receives notification via `author_notification_service.notify_author_approval_completed()`
   - Subject: `"Document Approved: {doc_number}"`

**Email sent to:** ✅ Author only (CORRECT)  
**Email subject:** `"Document Approved: SOP-2026-0001"`  
**No duplicate/incorrect emails** ✅

---

## 🐛 Root Cause Analysis

### Issue 1: Incorrect Task Type for REVIEW_COMPLETED State

**Location:** `backend/apps/workflows/document_lifecycle.py` line 1622-1627

```python
task_type_map = {
    'PENDING_REVIEW': 'REVIEW',
    'PENDING_APPROVAL': 'APPROVE', 
    'REVIEW_COMPLETED': 'REVIEW'  # ❌ WRONG - This is routing task, not review
}
```

**Problem:** When document is in `REVIEW_COMPLETED` state and assigned to author, the task type is set to `'REVIEW'`, which creates email with subject `"New Task Assigned: REVIEW"`.

**What it should be:** The task type should be `'ROUTE_FOR_APPROVAL'` or `'SELECT_APPROVER'` to accurately reflect what the author needs to do.

### Issue 2: Duplicate Email Sending

**Location:** `backend/apps/workflows/document_lifecycle.py` lines 252-308

```python
# Line 252-258: Transition creates task and sends email
success = self._transition_workflow(
    workflow=workflow,
    to_state_code='REVIEW_COMPLETED',
    user=user,
    comment=comment,
    assignee=document.author  # This triggers task creation + email
)

# Lines 293-307: ALSO sends author notification
if success:
    from .author_notifications import author_notification_service
    try:
        notification_sent = author_notification_service.notify_author_review_completed(
            document=document,
            reviewer=user,
            approved=approved,
            comment=comment
        )  # This sends ANOTHER email
```

**Problem:** Two separate email notifications are sent to the author:
1. Generic task assignment email from `_transition_workflow` → `_create_workflow_task_for_assignee` → `_send_task_notification_simple`
2. Detailed review completion email from `author_notification_service.notify_author_review_completed`

**Result:** Author receives TWO emails when review is completed.

---

## ✅ Correct Behavior (What Should Happen)

### When Review is Approved

**Email sent to:** Author ONLY  
**Number of emails:** 1 (not 2)  
**Subject:** `"Review Approved: SOP-2026-0001-v01.00 - Action Required"`  
**Content:** 
- Review approved by [Reviewer Name]
- Next action: Route for approval
- Instructions for selecting approver

**NO email should be sent to:** Reviewer (they just completed their task)

### When Review is Rejected

**Email sent to:** Author ONLY  
**Number of emails:** 1  
**Subject:** `"Review Rejected: SOP-2026-0001-v01.00 - Revision Required"`  
**Content:**
- Review rejected by [Reviewer Name]
- Review comments
- Instructions for revision

---

## 🔧 Proposed Fixes

### Fix 1: Update Task Type Map

**File:** `backend/apps/workflows/document_lifecycle.py` line 1622-1627

**Change:**
```python
# BEFORE
task_type_map = {
    'PENDING_REVIEW': 'REVIEW',
    'PENDING_APPROVAL': 'APPROVE', 
    'REVIEW_COMPLETED': 'REVIEW'  # ❌ WRONG
}

# AFTER
task_type_map = {
    'PENDING_REVIEW': 'REVIEW',
    'PENDING_APPROVAL': 'APPROVE', 
    'REVIEW_COMPLETED': 'ROUTE_FOR_APPROVAL'  # ✅ CORRECT
}
```

**Impact:** Changes email subject from `"New Task Assigned: REVIEW"` to `"New Task Assigned: ROUTE_FOR_APPROVAL"`.

**Better but still problematic:** Author will still receive TWO emails - one generic task email and one detailed review completion email.

---

### Fix 2: Disable Automatic Task Email for REVIEW_COMPLETED (RECOMMENDED)

**File:** `backend/apps/workflows/document_lifecycle.py`

**Option A: Skip task creation for REVIEW_COMPLETED state**

Add condition to skip task creation when transitioning to REVIEW_COMPLETED:

```python
def _transition_workflow(...):
    # ... existing code ...
    
    # Only create task and send notification for certain states
    if assignee and to_state.code not in ['REVIEW_COMPLETED', 'DRAFT']:
        transaction.on_commit(lambda: self._create_workflow_task_safe(...))
```

**Option B: Skip email notification for REVIEW_COMPLETED**

Modify `_send_task_notification_simple` to skip email for certain task types:

```python
def _send_task_notification_simple(self, task, assigned_by: User, assignee: User):
    # Skip notification for REVIEW_COMPLETED - author notification service handles this
    if task.task_data.get('action_required') == 'REVIEW_COMPLETED':
        print(f"⏭️ Skipping task notification - author notification service handles this")
        return
    
    # ... rest of function ...
```

**Impact:** Author receives ONLY the detailed review completion email from `author_notification_service`, not the generic task email.

---

### Fix 3: Improve Email Subject for Review Completion Task (Alternative)

If we decide to keep both emails, at least make the task email subject clearer:

**File:** `backend/apps/workflows/document_lifecycle.py` line 1531

```python
# BEFORE
subject = f"New Task Assigned: {task_type}"

# AFTER
if task_type == 'ROUTE_FOR_APPROVAL':
    subject = f"Action Required: Route Document for Approval - {task_data.get('document_number', 'Unknown')}"
else:
    subject = f"New Task Assigned: {task_type}"
```

**Impact:** More descriptive subject, but author still receives two emails.

---

## 📋 Recommended Solution

**Implement Fix 2 Option B** - Skip automatic task email for REVIEW_COMPLETED state

**Reasoning:**
1. ✅ Eliminates duplicate emails
2. ✅ Author notification service sends comprehensive, context-rich email
3. ✅ No confusion for users
4. ✅ Maintains task creation for tracking (if needed)
5. ✅ Minimal code changes
6. ✅ No breaking changes to workflow logic

**Implementation:**

```python
def _send_task_notification_simple(self, task, assigned_by: User, assignee: User):
    """Send simple email notification without database storage to avoid transaction issues."""
    try:
        # Skip notification for states handled by author notification service
        task_data = getattr(task, 'task_data', {})
        action_required = task_data.get('action_required', '')
        
        # REVIEW_COMPLETED state: author_notification_service sends detailed email
        # No need for generic task email
        if action_required == 'REVIEW_COMPLETED':
            print(f"⏭️ Skipping generic task notification for {action_required} - handled by author notification service")
            return
        
        # DRAFT state (rejection): author_notification_service sends detailed email
        if action_required == 'DRAFT':
            print(f"⏭️ Skipping generic task notification for rejection - handled by author notification service")
            return
        
        # ... rest of existing function for PENDING_REVIEW and PENDING_APPROVAL states ...
```

---

## 🧪 Testing Plan

### Test Case 1: Submit for Review
**Steps:**
1. Author submits document for review
2. Check reviewer's email

**Expected:**
- ✅ Reviewer receives 1 email
- ✅ Subject: "New Task Assigned: REVIEW"
- ❌ Author receives NO email

### Test Case 2: Complete Review (Approved)
**Steps:**
1. Reviewer approves document
2. Check author's email
3. Check reviewer's email

**Expected:**
- ✅ Author receives 1 email (not 2)
- ✅ Subject: "Review Approved: SOP-2026-0001-v01.00 - Action Required"
- ✅ Content explains need to route for approval
- ❌ Reviewer receives NO email

### Test Case 3: Complete Review (Rejected)
**Steps:**
1. Reviewer rejects document
2. Check author's email
3. Check reviewer's email

**Expected:**
- ✅ Author receives 1 email (not 2)
- ✅ Subject: "Review Rejected: SOP-2026-0001-v01.00 - Revision Required"
- ✅ Content includes review comments
- ❌ Reviewer receives NO email

### Test Case 4: Route for Approval
**Steps:**
1. Author routes document for approval
2. Check approver's email
3. Check author's email

**Expected:**
- ✅ Approver receives 1 email
- ✅ Subject: "New Task Assigned: APPROVE"
- ❌ Author receives NO email (they just initiated this action)

### Test Case 5: Approve Document
**Steps:**
1. Approver approves document
2. Check author's email
3. Check approver's email

**Expected:**
- ✅ Author receives 1 email
- ✅ Subject: "Document Approved: SOP-2026-0001-v01.00"
- ❌ Approver receives NO email

---

## 📊 Summary

### Current Issues
1. ❌ Author receives TWO emails when review is completed (one generic, one detailed)
2. ❌ Generic task email has misleading subject "New Task Assigned: REVIEW" (should indicate routing task)
3. ⚠️ Reviewer does NOT receive incorrect email (user's observation was about author's duplicate emails)

### After Fix
1. ✅ Author receives ONE detailed email when review is completed
2. ✅ Email subject clearly indicates action required
3. ✅ No duplicate or confusing emails
4. ✅ All recipients receive appropriate notifications only

---

## 🎯 Action Items

1. ✅ Implement Fix 2 Option B in `document_lifecycle.py`
2. ✅ Test all 5 test cases above
3. ✅ Update documentation
4. ✅ Deploy to staging for user testing
5. ✅ Collect user feedback

---

**Prepared By:** Rovo Dev  
**Analysis Date:** January 24, 2026  
**Ready for Implementation:** ✅ Yes
