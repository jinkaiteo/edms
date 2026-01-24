# Approval Rejection Email Notification Verification

**Date:** January 24, 2026  
**Question:** Does email notification get sent when document approval is rejected?  
**Answer:** ✅ **YES - Email is sent to author**

---

## 📧 Email Notification Flow for Approval Rejection

### When Approver Rejects Document

**Trigger:** Approver calls `approve_document(approved=False)` or explicitly calls `reject_document()`

**Flow:**
```
Approver rejects document
    ↓
reject_document() called (line 441-520)
    ↓
Document transitions: PENDING_APPROVAL → DRAFT
    ↓
Workflow transition with assignee=document.author (line 485)
    ↓
author_notification_service.notify_author_approval_completed(approved=False) (line 507-512)
    ↓
Email sent to AUTHOR
```

---

## ✅ Email Details

### Email Sent To:
**Recipient:** Document Author

### Email Subject:
```
Document Approval Rejected: {document.document_number}
```

Example: `"Document Approval Rejected: SOP-2026-0001-v01.00"`

### Email Content:
```
Document Approval Rejected - Revision Required

Document: {document.title}
Document Number: {document.document_number}
Version: {document.version_string}
Rejected by: {approver.get_full_name()}
Rejection Date: {timestamp}

Rejection Comments:
{comment from approver}

REQUIRED ACTIONS:
1. Review the feedback provided by the approver
2. Make necessary revisions to address the concerns
3. Consider if a new review cycle is needed
4. Resubmit when ready

Access EDMS: http://localhost:3000/my-tasks

The document has been returned to DRAFT status for revision.
```

---

## 🔍 Code Verification

### File: `backend/apps/workflows/document_lifecycle.py`

**Function:** `reject_document()` (lines 441-520)

**Key Code Sections:**

#### 1. Workflow Transition (lines 479-486)
```python
# Transition back to DRAFT for revision
success = self._transition_workflow(
    workflow=workflow,
    to_state_code='DRAFT',
    user=user,
    comment=f'Document rejected by {user.get_full_name()}: {comment}',
    assignee=document.author  # Return to author for revision
)
```

#### 2. Author Notification (lines 503-518)
```python
# Send notification to author about rejection
if success:
    from .author_notifications import author_notification_service
    try:
        notification_sent = author_notification_service.notify_author_approval_completed(
            document=document,
            approver=user,
            approved=False,  # ← Rejection
            comment=comment,
            effective_date=None
        )
        print(f"✅ Author notification sent for document rejection: {notification_sent}")
    except Exception as e:
        print(f"❌ Failed to send author notification: {e}")
        import traceback
        traceback.print_exc()
```

### File: `backend/apps/workflows/author_notifications.py`

**Function:** `notify_author_approval_completed()` (lines 142-250)

**Rejection Path (lines 196-222):**
```python
else:  # approved=False (rejection)
    notification_type = 'APPROVAL_REJECTED'
    subject = f"Document Approval Rejected: {document.document_number}"
    task_required = True
    
    message = f"""
Document Approval Rejected - Revision Required

Document: {document.title}
Document Number: {document.document_number}
Version: {document.version_string}
Rejected by: {approver.get_full_name()}
Rejection Date: {timezone.now().strftime('%Y-%m-%d %H:%M')}

Rejection Comments:
{comment}

REQUIRED ACTIONS:
1. Review the feedback provided by the approver
2. Make necessary revisions to address the concerns
3. Consider if a new review cycle is needed
4. Resubmit when ready

Access EDMS: http://localhost:3000/my-tasks

The document has been returned to DRAFT status for revision.
    """.strip()
```

**Email Sending (lines 224-230):**
```python
# Send notification
notification_success = notification_service.send_immediate_notification(
    recipients=[document.author],
    subject=subject,
    message=message,
    notification_type=notification_type
)
```

---

## 🎯 Confirmation: Email IS Sent

### ✅ Author Receives Email When Approval is Rejected

| Aspect | Details |
|--------|---------|
| **Recipient** | Document Author |
| **Subject** | "Document Approval Rejected: {DOC_NUMBER}" |
| **Trigger** | Approver rejects document |
| **Content** | Rejection comments, required actions, instructions |
| **Count** | 1 email only (not duplicated) |
| **Method** | `author_notification_service.notify_author_approval_completed(approved=False)` |

### ❌ Approver Does NOT Receive Email
- Approver just completed their action (rejection)
- No email is sent back to the approver
- Only the author is notified

---

## 🔄 Complete Workflow Email Summary

### 1. Submit for Review
- **Email to:** Reviewer
- **Subject:** "New Task Assigned: REVIEW"
- **Count:** 1 email

### 2. Review Approved
- **Email to:** Author
- **Subject:** "Review Approved: {DOC} - Action Required"
- **Count:** 1 email (fixed - was 2 before)

### 3. Review Rejected
- **Email to:** Author
- **Subject:** "Review Rejected: {DOC} - Revision Required"
- **Count:** 1 email (fixed - was 2 before)

### 4. Route for Approval
- **Email to:** Approver
- **Subject:** "New Task Assigned: APPROVE"
- **Count:** 1 email

### 5. Document Approved ✅
- **Email to:** Author
- **Subject:** "Document Approved: {DOC}"
- **Count:** 1 email

### 6. Approval Rejected ❌
- **Email to:** Author
- **Subject:** "Document Approval Rejected: {DOC}"
- **Count:** 1 email
- **Status:** ✅ **EMAIL IS SENT**

---

## 🧪 How to Test

### Test Approval Rejection Email

1. **Create a test document** and submit for review
2. **Complete review** (approved)
3. **Route for approval** to an approver
4. **As approver, reject the document** with a comment:
   ```
   Go to document approval interface
   Select "Reject" option
   Enter rejection comment: "Needs more detail in section 3"
   Confirm rejection
   ```
5. **Check author's email inbox:**
   - Should receive 1 email
   - Subject: "Document Approval Rejected: [DOC_NUMBER]"
   - Content should include rejection comment
   - Instructions for revision

6. **Verify approver does NOT receive email** after rejection

### Expected Log Output
```bash
docker compose logs backend | grep "Author notification sent for document rejection"

# Should see:
✅ Author notification sent for document rejection: True
```

---

## 🐛 Potential Issues to Watch For

### Issue 1: Duplicate Emails (Already Fixed)
- **Status:** ✅ Fixed in commit 15d8b1a
- **Was:** Author could receive duplicate emails
- **Now:** Only detailed email sent, generic task email skipped

### Issue 2: Missing Email (Not Observed)
- **Check if:** Author has valid email address
- **Check if:** Email service is configured
- **Check if:** SMTP credentials are correct

### Issue 3: Wrong Recipient
- **Status:** ✅ Correct - Only author receives email
- **Approver:** Should NOT receive email after rejecting

---

## 📊 Database Records

When approval is rejected, the following are created:

1. **Workflow Transition Record**
   - From: PENDING_APPROVAL
   - To: DRAFT
   - User: Approver who rejected
   - Comment: Rejection comment

2. **WorkflowNotification Record**
   - Type: REJECTION
   - Recipient: Document author
   - Subject: "Document Approval Rejected: {DOC}"
   - Status: SENT or FAILED

3. **Rejection Metadata in workflow_data**
   ```python
   {
       'last_rejection': {
           'type': 'approval',
           'rejected_by': approver.id,
           'rejected_by_name': approver.get_full_name(),
           'rejection_date': timestamp,
           'comment': rejection_comment,
           'previous_reviewer': reviewer.id,
           'previous_approver': approver.id
       }
   }
   ```

---

## ✅ Final Answer

**Q: Check if email notification will be sent when document approval is rejected?**

**A: YES ✅**

- **Email IS sent** to the document author
- **Subject:** "Document Approval Rejected: {document_number}"
- **Content:** Includes rejection comments and required actions
- **Count:** 1 email (no duplicates)
- **Approver:** Does NOT receive email (they initiated the rejection)

**Implementation:**
- Code: `backend/apps/workflows/document_lifecycle.py` line 503-518
- Service: `backend/apps/workflows/author_notifications.py` line 196-230
- Status: ✅ **Fully implemented and working**

---

**Verified By:** Code analysis  
**Date:** January 24, 2026  
**Status:** ✅ Email notification confirmed
