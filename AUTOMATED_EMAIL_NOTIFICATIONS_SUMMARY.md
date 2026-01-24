# Automated Email Notifications - Complete Summary

**Date:** January 24, 2026  
**Question:** Check if email notifications are sent for obsolescence, upversion, document effective, etc.

---

## 📧 **Email Notifications Summary**

### ✅ **Emails That ARE Sent Automatically**

| Event | Trigger | Recipient | Subject | Status |
|-------|---------|-----------|---------|--------|
| **Submit for Review** | Author submits | Reviewer | "New Task Assigned: REVIEW" | ✅ Sent |
| **Review Approved** | Reviewer approves | Author | "Review Approved: [DOC] - Action Required" | ✅ Sent |
| **Review Rejected** | Reviewer rejects | Author | "Review Rejected: [DOC] - Revision Required" | ✅ Sent |
| **Route for Approval** | Author routes | Approver | "New Task Assigned: APPROVE" | ✅ Sent |
| **Document Approved** | Approver approves | Author | "Document Approved: [DOC]" | ✅ Sent |
| **Approval Rejected** | Approver rejects | Author | "Document Approval Rejected: [DOC]" | ✅ Sent |
| **Document Effective** | Scheduled date arrives | Author | "Document Now Effective: [DOC]" | ✅ Sent |
| **Document Obsolete** | Scheduled date arrives | Author | "Document Now Obsolete: [DOC]" | ✅ Sent |
| **Workflow Timeout** | Task overdue | Current Assignee | "Overdue Workflow: [DOC]" | ✅ Sent |

---

### ❌ **Emails That Are NOT Sent (No Implementation)**

| Event | Reason | Would Recipients Be |
|-------|--------|---------------------|
| **Document Scheduled for Obsolescence** | Not implemented | Author, stakeholders |
| **Upversion Started** | Not implemented | Author |
| **Document Superseded** | Not implemented | Users of old document |
| **Scheduled for Effective Date** | Not implemented | Author |
| **Periodic Review Due** | Partial implementation | Document owner |

---

## 🔍 **Detailed Analysis**

### 1. ✅ **Document Becomes Effective - EMAIL IS SENT**

**Trigger:** Scheduler task runs daily and document's `effective_date` arrives

**Code Location:**
- Service: `backend/apps/scheduler/services/automation.py` (lines 136-140)
- Email Function: `backend/apps/scheduler/notification_service.py` (lines 42-68)

**How it works:**
1. Celery Beat runs `process_document_effective_dates` task daily
2. Checks documents with status `APPROVED_PENDING_EFFECTIVE` where `effective_date <= today`
3. Updates document status to `EFFECTIVE`
4. Calls `notification_service.send_document_effective_notification(document)`
5. Sends email to document author

**Email Content:**
```
Subject: Document Now Effective: SOP-2026-0001-v01.00

Document: SOP-2026-0001-v01.00 - [Title]
Status: EFFECTIVE as of 2026-01-24
Author: John Smith

This document is now effective and available for use.
```

**Recipient:** Document Author only

**Schedule:** Runs automatically via Celery Beat (daily check)

---

### 2. ✅ **Document Becomes Obsolete - EMAIL IS SENT**

**Trigger:** Scheduler task runs daily and document's `obsolescence_date` arrives

**Code Location:**
- Service: `backend/apps/scheduler/services/automation.py` (lines 234-238)
- Email Function: `backend/apps/scheduler/notification_service.py` (lines 70-96)

**How it works:**
1. Celery Beat runs `process_document_obsoletion_dates` task daily
2. Checks documents with status `SCHEDULED_FOR_OBSOLESCENCE` where `obsolescence_date <= today`
3. Updates document status to `OBSOLETE`
4. Calls `notification_service.send_document_obsolete_notification(document)`
5. Sends email to document author

**Email Content:**
```
Subject: Document Now Obsolete: SOP-2026-0001-v01.00

Document: SOP-2026-0001-v01.00 - [Title]
Status: OBSOLETE as of 2026-01-24
Reason: [Obsolescence reason or 'Scheduled obsolescence']

This document is no longer valid for use.
```

**Recipient:** Document Author only

**Schedule:** Runs automatically via Celery Beat (daily check)

---

### 3. ❌ **Document Scheduled for Obsolescence - NO EMAIL**

**What happens:**
When an approver schedules a document for obsolescence using `obsolete_document_directly()`:
1. Document status changes to `SCHEDULED_FOR_OBSOLESCENCE`
2. Obsolescence date is set
3. **NO email is sent at this time**
4. Email will be sent later when the obsolescence date arrives (see #2 above)

**Code Location:**
- Function: `backend/apps/workflows/document_lifecycle.py` (lines 801-900)
- **No email notification call in this function**

**Gap:** Author is NOT notified when obsolescence is scheduled, only when it actually becomes obsolete.

**Recommendation:** Could add email notification when obsolescence is scheduled:
```python
# After scheduling (around line 870)
if success:
    # Send notification about scheduled obsolescence
    subject = f"Document Scheduled for Obsolescence: {document.document_number}"
    message = f"""
    Your document has been scheduled for obsolescence.
    
    Document: {document.document_number}
    Scheduled Date: {obsolescence_date}
    Reason: {reason}
    Scheduled by: {user.get_full_name()}
    
    You will receive another notification when the document becomes obsolete.
    """
    # Send email...
```

---

### 4. ❌ **Upversion Started - NO EMAIL**

**What happens:**
When creating a new version via `start_upversion_workflow()`:
1. New document created with higher version
2. Old document linked via `supersedes` field
3. New document goes through normal workflow (draft → review → approval)
4. **NO specific "upversion started" email**

**Code Location:**
- Function: `backend/apps/workflows/document_lifecycle.py` (lines 581-698)
- **No email notification call in this function**

**Current Behavior:**
- Author receives normal workflow emails (review, approval, etc.) for the new version
- No special notification about upversion process starting

**Note:** Not critical since author initiates the upversion and receives all normal workflow emails.

---

### 5. ❌ **Document Superseded - NO EMAIL**

**What happens:**
When new document becomes effective and supersedes old version:
1. Old document status changes to `SUPERSEDED`
2. Old document's `obsolete_date` is set
3. **NO email sent to users of old document**

**Code Location:**
- Function: `backend/apps/workflows/document_lifecycle.py` (lines 697-724)
- **No email notification call in this function**

**Gap:** Users who reference or use the old document are not notified it's been superseded.

**Recommendation:** Could notify:
- Author of old document
- Users who have the old document in their workflows
- Users who have bookmarked/favorited the old document

---

### 6. ✅ **Workflow Timeout - EMAIL IS SENT**

**Trigger:** Task is overdue (scheduler checks periodically)

**Code Location:**
- Email Function: `backend/apps/scheduler/notification_service.py` (lines 98-124)

**How it works:**
1. Scheduler task checks workflows for overdue tasks
2. Calls `send_workflow_timeout_notification(workflow, days_overdue)`
3. Sends email to current assignee

**Email Content:**
```
Subject: Overdue Workflow: SOP-2026-0001-v01.00

Document: SOP-2026-0001-v01.00 - [Title]
Workflow Type: REVIEW
Current State: PENDING_REVIEW
Days Overdue: 5

Please complete this workflow task immediately.
```

**Recipient:** Current workflow assignee (reviewer or approver)

---

### 7. ⚠️ **Periodic Review Due - PARTIAL**

**Status:** Mentioned in code but not fully implemented for email notifications

**Code Location:**
- Service: `backend/apps/scheduler/services/periodic_review_service.py`
- References upversion requirements but no email sending observed

**Current Implementation:** Tracks periodic reviews, marks documents as needing review, but **no email notification sent**

**Gap:** Document owners are not notified when periodic review is due.

---

## 📊 **Email Notification Implementation Status**

### **Workflow Events** (User-Initiated Actions)
| Event | Implementation | Email? |
|-------|----------------|--------|
| Submit for Review | ✅ Complete | ✅ Yes |
| Start Review | ⚠️ No email needed | ❌ No |
| Complete Review (Approve) | ✅ Complete | ✅ Yes |
| Complete Review (Reject) | ✅ Complete | ✅ Yes |
| Route for Approval | ✅ Complete | ✅ Yes |
| Approve Document | ✅ Complete | ✅ Yes |
| Reject Document | ✅ Complete | ✅ Yes |

### **Scheduled/Automated Events** (System-Initiated)
| Event | Implementation | Email? |
|-------|----------------|--------|
| Document Becomes Effective | ✅ Complete | ✅ Yes |
| Document Becomes Obsolete | ✅ Complete | ✅ Yes |
| Workflow Timeout | ✅ Complete | ✅ Yes |
| **Schedule for Obsolescence** | ⚠️ No email | ❌ No |
| **Document Superseded** | ⚠️ No email | ❌ No |
| **Periodic Review Due** | ⚠️ Partial | ❌ No |
| **Upversion Started** | ⚠️ No specific email | ❌ No |

---

## 🎯 **Missing Email Notifications (Gaps)**

### Gap 1: Schedule for Obsolescence
**What:** When document is scheduled for future obsolescence
**Who should get email:** Document author
**Current:** No email sent
**Impact:** Author not aware document will become obsolete

### Gap 2: Document Superseded
**What:** When old version is superseded by new version
**Who should get email:** Users of old document, stakeholders
**Current:** No email sent
**Impact:** Users may continue using old version without knowing new one exists

### Gap 3: Periodic Review Due
**What:** When document requires periodic review
**Who should get email:** Document owner, designated reviewers
**Current:** System tracks it but no email notification
**Impact:** Reviews may be missed

### Gap 4: Scheduled for Effective Date
**What:** When document is approved and scheduled to become effective
**Who should get email:** Document author
**Current:** No email sent (but gets email when it becomes effective)
**Impact:** Minor - author already knows from approval email

---

## 🔧 **Recommendations**

### Priority 1: Add "Scheduled for Obsolescence" Notification
```python
def obsolete_document_directly(self, document: Document, user: User, 
                              reason: str, obsolescence_date) -> bool:
    # ... existing code ...
    
    if success:
        # NEW: Send notification about scheduled obsolescence
        from ..scheduler.notification_service import notification_service
        subject = f"Document Scheduled for Obsolescence: {document.document_number}"
        message = f"""
Document Scheduled for Obsolescence

Document: {document.document_number} - {document.title}
Scheduled Date: {obsolescence_date}
Reason: {reason}
Scheduled by: {user.get_full_name()}

Your document will become obsolete on {obsolescence_date}.
You will receive another notification when the document becomes obsolete.

Please ensure any dependent processes are updated before this date.
        """
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [document.author.email],
            fail_silently=True
        )
```

### Priority 2: Add "Document Superseded" Notification
Notify users when old document is superseded by new version.

### Priority 3: Add "Periodic Review Due" Notification  
Integrate with existing periodic review system to send reminder emails.

---

## 📝 **Summary Answer to Your Question**

**Q: Check if email notification will be sent when document approval is scheduled for obsolescence, upversion, etc?**

**A: Mixed - Some events send emails, others don't:**

### ✅ **YES - Emails ARE Sent:**
1. **Document Becomes Effective** (when scheduled effective date arrives)
2. **Document Becomes Obsolete** (when scheduled obsolescence date arrives)
3. **Workflow Timeout** (when tasks are overdue)
4. All user-initiated workflow actions (review, approval, rejection)

### ❌ **NO - Emails Are NOT Sent:**
1. **When Obsolescence is Scheduled** (only sent when it actually becomes obsolete later)
2. **When Document is Superseded** (no notification to users of old version)
3. **When Upversion is Started** (normal workflow emails are sent instead)
4. **When Periodic Review is Due** (tracked but no email)
5. **When Scheduled for Effective Date** (only sent when it becomes effective)

---

## 🧪 **How to Test**

### Test 1: Document Becomes Effective
```bash
1. Approve document with future effective date (e.g., tomorrow)
2. Wait for scheduler task to run (or run manually)
3. Check author's email for "Document Now Effective: [DOC]"
```

### Test 2: Document Becomes Obsolete
```bash
1. Schedule document for obsolescence with future date
2. Wait for scheduler task to run
3. Check author's email for "Document Now Obsolete: [DOC]"
4. Note: Author did NOT receive email when obsolescence was scheduled
```

### Test 3: Schedule for Obsolescence (Gap)
```bash
1. Schedule document for obsolescence
2. Check author's email - NO EMAIL RECEIVED
3. This is a gap - no notification when scheduling happens
```

---

## 🔗 **Code References**

### Email Notification Functions
- `send_document_effective_notification()` - `backend/apps/scheduler/notification_service.py:42-68`
- `send_document_obsolete_notification()` - `backend/apps/scheduler/notification_service.py:70-96`
- `send_workflow_timeout_notification()` - `backend/apps/scheduler/notification_service.py:98-124`

### Scheduler Tasks That Trigger Emails
- `process_document_effective_dates()` - `backend/apps/scheduler/services/automation.py:88-155`
- `process_document_obsoletion_dates()` - `backend/apps/scheduler/services/automation.py:157-249`
- `check_workflow_timeouts()` - `backend/apps/scheduler/tasks.py`

### Document Lifecycle Functions (No Emails)
- `start_obsolete_workflow()` - `backend/apps/workflows/document_lifecycle.py:727-799` (❌ No email)
- `obsolete_document_directly()` - `backend/apps/workflows/document_lifecycle.py:801-900` (❌ No email)
- `start_upversion_workflow()` - `backend/apps/workflows/document_lifecycle.py:581-698` (❌ No specific email)
- `_supersede_old_version()` - `backend/apps/workflows/document_lifecycle.py:697-724` (❌ No email)

---

**Report Generated:** January 24, 2026  
**Status:** Complete analysis with gaps identified  
**Recommendation:** Implement missing notifications as Priority 1, 2, 3 above
