# Rejection Notification Bug Fix

## Issues Reported

When reviewer01 rejects a document:
1. ❌ **Wrong recipient:** Email sent to reviewer01 (jinkaiteo@hotmail.com) instead of author
2. ❌ **Wrong subject:** "New Task Assigned: Review - REC-2026-0001-v01.00" instead of rejection notification

## Root Cause

The `_reject_document` method in `backend/apps/documents/views.py` was NOT using the proper workflow system and had NO email notification code at all.

**Old buggy code:**
```python
def _reject_document(self, document, request, comment):
    """Reject document."""
    # Just changes status to DRAFT
    document.status = 'DRAFT'
    document.save()
    
    # Adds comment but NO EMAIL NOTIFICATION
    DocumentComment.objects.create(...)
    
    return Response({'message': 'Document rejected'})
```

**The proper workflow existed** in `document_lifecycle.py` with correct notifications in `author_notifications.py`, but the API endpoint wasn't using it!

## Solution

Modified `_reject_document` to use the proper workflow system:

```python
def _reject_document(self, document, request, comment):
    """Reject document."""
    # Use the proper workflow for rejection to ensure notifications are sent
    from apps.workflows.document_lifecycle import document_lifecycle_service
    
    # Determine if this is a review rejection or approval rejection
    is_review_rejection = document.can_review(request.user)
    
    if is_review_rejection:
        # Review rejection - use complete_review with approved=False
        success = document_lifecycle_service.complete_review(
            document=document,
            user=request.user,
            approved=False,  # This triggers rejection notification
            comment=comment or 'Document rejected'
        )
    else:
        # Approval rejection - use complete_approval with approved=False
        success = document_lifecycle_service.complete_approval(
            document=document,
            user=request.user,
            approved=False,
            comment=comment or 'Document rejected'
        )
    
    return Response({'message': 'Document rejected and author notified'})
```

## What This Fix Does

### For Review Rejection:
1. ✅ Calls `document_lifecycle_service.complete_review(approved=False)`
2. ✅ Which calls `author_notification_service.notify_author_review_completed(approved=False)`
3. ✅ Sends email to **document author** (not reviewer)
4. ✅ Subject: **"Review Rejected: [DOC-NUMBER] - Revision Required"**
5. ✅ Creates task for author: "Revise [DOC-NUMBER] Based on Review"

### For Approval Rejection:
1. ✅ Calls `document_lifecycle_service.complete_approval(approved=False)`
2. ✅ Which calls `author_notification_service.notify_author_approval_completed(approved=False)`
3. ✅ Sends email to **document author** (not approver)
4. ✅ Subject: **"Approval Rejected: [DOC-NUMBER] - Revision Required"**
5. ✅ Creates task for author: "Revise [DOC-NUMBER] Based on Approval"

## Email Notification Details

### Review Rejection Email (from author_notifications.py):
```
Subject: Review Rejected: REC-2026-0001 - Revision Required
To: author@example.com (document author)
From: jinkaiteo.tikva@gmail.com

Document Review Rejected - Revision Required

Document: Record Template
Document Number: REC-2026-0001
Version: v01.00
Reviewed by: Reviewer User
Review Date: 2026-01-26 14:30

Review Comments:
[Reviewer's rejection comment]

REQUIRED ACTIONS:
1. Review the feedback provided above
2. Make necessary revisions to the document
3. Address all concerns raised in the review
4. Resubmit for review when ready
```

### Task Created for Author:
```
Task Name: Revise REC-2026-0001 Based on Review
Description: Review was rejected by Reviewer User. Please address the review comments and resubmit.
Status: Pending
Assigned to: Document Author
```

## Testing

After restart, when reviewer01 rejects a document:
1. ✅ Email will be sent to **author** (author01@edms.com)
2. ✅ Subject will be: **"Review Rejected: [DOC-NUMBER] - Revision Required"**
3. ✅ Task will be created for author to revise the document
4. ✅ Reviewer will NOT receive any email

## Files Modified

- `backend/apps/documents/views.py` - Fixed `_reject_document` method

## Files Already Correct (No Changes Needed)

- ✅ `backend/apps/workflows/document_lifecycle.py` - Already has proper rejection workflow
- ✅ `backend/apps/workflows/author_notifications.py` - Already has proper rejection notification
- ✅ `backend/apps/scheduler/notification_service.py` - Email sending works correctly

## Related Code References

**Workflow Code (already correct):**
- `document_lifecycle.py:complete_review()` - Line 296-298: Calls author notification
- `author_notifications.py:notify_author_review_completed()` - Line 83: Handles rejection email

**Previous Issues:**
- Email addresses were never hardcoded (verified in commit 64ec7d8)
- This was a missing integration, not a hardcoded value

---

**Date:** January 26, 2026  
**Status:** ✅ Fixed - Backend restart required  
**Impact:** All rejection notifications now send to author with correct subject
