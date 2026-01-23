# Periodic Review System - Complete Design

**Date:** January 22, 2026  
**Status:** Design Phase  
**Purpose:** Comprehensive explanation of how periodic review will work in EDMS

---

## 🎯 **Overview**

The Periodic Review System ensures that all EFFECTIVE documents are reviewed periodically (typically annually) to verify they remain current, accurate, and applicable. This is a **21 CFR Part 11 compliance requirement**.

---

## 📋 **High-Level Flow**

```
┌─────────────────────────────────────────────────────────────────┐
│                    PERIODIC REVIEW LIFECYCLE                     │
└─────────────────────────────────────────────────────────────────┘

1. Document Approved → Set Review Date (12 months from now)
   ↓
2. Scheduler Checks Daily → Document overdue for review?
   ↓
3. Scheduler Triggers Review Workflow
   ↓
4. Email Notification → Reviewer notified
   ↓
5. Reviewer Reviews Document
   ↓
6. Outcome Decision:
   ├─ Still Valid → Re-approve (resets review date)
   ├─ Needs Minor Updates → Edit & Re-approve
   └─ Needs Major Updates → Create new version
   ↓
7. Document Returns to EFFECTIVE → Cycle repeats
```

---

## 🔄 **Detailed Step-by-Step Flow**

### **Step 1: Setting the Initial Review Date**

**When:** Document approval workflow completes  
**Who:** Approver  
**What Happens:**

```
User Journey:
┌──────────────────────────────────────┐
│ Approver clicks "Approve Document"   │
└──────────────┬───────────────────────┘
               ↓
┌──────────────────────────────────────┐
│ Approval Modal Opens:                │
│  [x] Set Effective Date: [2026-01-22]│
│  [x] Set Review Date: [2027-01-22]   │  ← NEW FIELD
│  [ ] Review Frequency: [12] months   │  ← NEW FIELD
│  [ ] Comments: [____________]        │
│  [Cancel]  [Approve]                 │
└──────────────┬───────────────────────┘
               ↓
┌──────────────────────────────────────┐
│ System Calculates:                   │
│  - effective_date = 2026-01-22       │
│  - review_date = 2027-01-22          │
│  - review_frequency_months = 12      │
│  - next_review_date = 2027-01-22     │
└──────────────────────────────────────┘
```

**Backend Logic:**
```python
def approve_document(document, approver, effective_date, review_date):
    """
    Approve document and set periodic review schedule
    """
    # Set approval data
    document.status = 'APPROVED_PENDING_EFFECTIVE'
    document.effective_date = effective_date
    document.approver = approver
    document.approval_date = timezone.now().date()
    
    # NEW: Set periodic review data
    document.review_date = review_date
    document.review_frequency_months = 12  # Default
    document.next_review_date = review_date
    document.last_review_date = None  # First time
    
    document.save()
    
    # Create audit trail
    AuditTrail.objects.create(
        action='DOCUMENT_APPROVED',
        details={
            'effective_date': str(effective_date),
            'review_date': str(review_date),  # NEW
            'review_frequency': 12
        }
    )
```

**Frontend Changes:**
```typescript
// ApproverInterface.tsx - Add review date fields
<div className="space-y-4">
  <div>
    <label>Effective Date</label>
    <input type="date" value={effectiveDate} />
  </div>
  
  {/* NEW: Review Date */}
  <div>
    <label>Periodic Review Date</label>
    <input 
      type="date" 
      value={reviewDate}
      min={effectiveDate}  // Must be after effective date
    />
    <p className="text-xs text-gray-500">
      Date when this document should be reviewed for continued relevance
    </p>
  </div>
  
  {/* NEW: Review Frequency */}
  <div>
    <label>Review Frequency</label>
    <select value={reviewFrequency}>
      <option value="6">Every 6 months</option>
      <option value="12" selected>Annually (12 months)</option>
      <option value="24">Every 2 years</option>
      <option value="36">Every 3 years</option>
    </select>
  </div>
</div>
```

---

### **Step 2: Scheduler Monitors Review Dates**

**When:** Daily at 6:00 AM  
**Who:** Automated system (Celery Beat)  
**What Happens:**

```python
@shared_task(name='apps.scheduler.tasks.process_periodic_reviews')
def process_periodic_reviews():
    """
    Check for documents that need periodic review
    Runs daily at 6:00 AM
    """
    from apps.documents.models import Document
    from apps.workflows.models import DocumentWorkflow, WorkflowType
    from apps.workflows.models import WorkflowNotification
    from django.utils import timezone
    
    today = timezone.now().date()
    
    # Find documents needing review
    documents_for_review = Document.objects.filter(
        status='EFFECTIVE',
        next_review_date__lte=today,
        is_active=True
    )
    
    review_count = 0
    
    for document in documents_for_review:
        # Check if already under review
        existing_review = DocumentWorkflow.objects.filter(
            document=document,
            workflow_type__code='PERIODIC_REVIEW',
            is_terminated=False
        ).exists()
        
        if existing_review:
            continue  # Skip, already in review
        
        # Create periodic review workflow
        workflow_type = WorkflowType.objects.get(code='PERIODIC_REVIEW')
        workflow = DocumentWorkflow.objects.create(
            document=document,
            workflow_type=workflow_type,
            initiated_by=User.objects.get(username='edms_system'),
            due_date=today + timedelta(days=14)  # 2 weeks to complete
        )
        
        # Update document status
        document.status = 'UNDER_PERIODIC_REVIEW'
        document.save()
        
        # Create notification for reviewer
        reviewer = document.reviewer or document.author
        WorkflowNotification.objects.create(
            workflow=workflow,
            recipient=reviewer,
            notification_type='EMAIL',
            subject=f'Periodic Review Required: {document.document_number}',
            message=f'Document "{document.title}" is due for periodic review.',
            metadata={
                'document_number': document.document_number,
                'title': document.title,
                'last_review_date': str(document.last_review_date) if document.last_review_date else 'Never',
                'due_date': str(workflow.due_date)
            }
        )
        
        review_count += 1
        
        # Create audit trail
        AuditTrail.objects.create(
            user=User.objects.get(username='edms_system'),
            action='PERIODIC_REVIEW_INITIATED',
            object_type='Document',
            object_id=document.id,
            details={
                'document_number': document.document_number,
                'reviewer': reviewer.username,
                'due_date': str(workflow.due_date)
            }
        )
    
    return {
        'documents_processed': review_count,
        'status': 'completed'
    }
```

**Scheduler Configuration:**
```python
# backend/edms/celery.py
app.conf.beat_schedule = {
    # ... existing tasks
    
    'process-periodic-reviews': {
        'task': 'apps.scheduler.tasks.process_periodic_reviews',
        'schedule': crontab(hour=6, minute=0),  # Daily at 6 AM
        'options': {'priority': 8}  # High priority
    },
}
```

**What the Scheduler Does:**
1. ✅ Runs daily at 6:00 AM
2. ✅ Finds documents where `next_review_date <= today`
3. ✅ Creates PERIODIC_REVIEW workflow
4. ✅ Changes document status to `UNDER_PERIODIC_REVIEW`
5. ✅ Sends email notification to reviewer
6. ✅ Creates audit trail entry
7. ✅ Sets 2-week deadline for review completion

---

### **Step 3: Email Notification Sent**

**When:** Immediately after scheduler triggers review  
**Who:** System sends to reviewer  
**What Happens:**

**Email Template:**
```html
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: #2563eb; color: white; padding: 20px; }
        .content { background: #f9fafb; padding: 20px; }
        .button { background: #2563eb; color: white; padding: 12px 24px; 
                  text-decoration: none; border-radius: 6px; display: inline-block; }
        .warning { background: #fef3c7; padding: 12px; border-left: 4px solid #f59e0b; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>📋 Periodic Review Required</h2>
        </div>
        
        <div class="content">
            <p>Hello {{ reviewer_name }},</p>
            
            <p>The following document is due for periodic review:</p>
            
            <div style="background: white; padding: 15px; margin: 20px 0;">
                <strong>Document:</strong> {{ document_number }}<br>
                <strong>Title:</strong> {{ title }}<br>
                <strong>Current Version:</strong> v{{ version }}<br>
                <strong>Effective Since:</strong> {{ effective_date }}<br>
                <strong>Last Reviewed:</strong> {{ last_review_date or 'Never' }}<br>
            </div>
            
            <div class="warning">
                ⚠️ <strong>Due Date:</strong> {{ due_date }}<br>
                Please complete this review within 2 weeks.
            </div>
            
            <p><strong>What you need to do:</strong></p>
            <ol>
                <li>Review the current document content</li>
                <li>Verify accuracy and relevance</li>
                <li>Check if any updates are needed</li>
                <li>Submit review outcome</li>
            </ol>
            
            <p style="margin-top: 30px;">
                <a href="{{ edms_url }}/documents/{{ document_uuid }}/review" class="button">
                    Review Document Now
                </a>
            </p>
            
            <p style="color: #6b7280; font-size: 14px; margin-top: 30px;">
                This is an automated notification from EDMS.<br>
                If you have questions, contact your document administrator.
            </p>
        </div>
    </div>
</body>
</html>
```

**Email Sending Implementation:**
```python
# backend/apps/workflows/tasks.py
@shared_task(name='apps.workflows.tasks.send_email_notification')
def send_email_notification(notification_id):
    """
    Send email notification for workflow events
    """
    from django.core.mail import EmailMessage
    from django.template.loader import render_to_string
    from django.conf import settings
    
    notification = WorkflowNotification.objects.get(id=notification_id)
    
    try:
        # Prepare context
        context = {
            'recipient_name': notification.recipient.get_full_name(),
            'document_number': notification.workflow.document.document_number,
            'title': notification.workflow.document.title,
            'version': notification.workflow.document.version_string,
            'effective_date': notification.workflow.document.effective_date,
            'last_review_date': notification.workflow.document.last_review_date,
            'due_date': notification.workflow.due_date,
            'edms_url': settings.FRONTEND_URL,
            'document_uuid': notification.workflow.document.uuid,
        }
        
        # Render HTML email
        html_content = render_to_string('emails/periodic_review.html', context)
        
        # Send email
        email = EmailMessage(
            subject=notification.subject,
            body=html_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[notification.recipient.email]
        )
        email.content_subtype = 'html'
        email.send()
        
        # Update notification status
        notification.status = 'SENT'
        notification.sent_at = timezone.now()
        notification.save()
        
        return {'status': 'sent', 'notification_id': notification_id}
        
    except Exception as e:
        notification.status = 'FAILED'
        notification.error_message = str(e)
        notification.save()
        raise
```

---

### **Step 4: Reviewer Accesses Document**

**When:** Reviewer clicks link in email or goes to "My Tasks"  
**Who:** Reviewer  
**What Happens:**

**Frontend Display:**
```typescript
// My Tasks View
┌─────────────────────────────────────────────────┐
│ 📋 My Tasks                                     │
├─────────────────────────────────────────────────┤
│                                                 │
│ 🔄 PERIODIC REVIEW                              │
│ ┌─────────────────────────────────────────┐   │
│ │ SOP-2026-0001 v1.0                       │   │
│ │ Standard Operating Procedure for QC      │   │
│ │                                          │   │
│ │ 📅 Due: January 29, 2026 (5 days left)  │   │
│ │ 👤 Assigned to: You                      │   │
│ │ ⏰ Initiated: January 15, 2026           │   │
│ │                                          │   │
│ │ [View Document] [Start Review]           │   │
│ └─────────────────────────────────────────┘   │
│                                                 │
└─────────────────────────────────────────────────┘
```

**Document View with Review Banner:**
```typescript
┌──────────────────────────────────────────────────┐
│ ⚠️  PERIODIC REVIEW REQUIRED                     │
│ This document is due for periodic review.        │
│ Last reviewed: Never                             │
│ Review due: January 29, 2026                     │
│ [Start Review]                                   │
└──────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────┐
│ SOP-2026-0001 v1.0                               │
│ Standard Operating Procedure for Quality Control │
│                                                  │
│ Status: UNDER_PERIODIC_REVIEW                    │
│ Effective Date: January 22, 2025                 │
│ Review Frequency: Annually                       │
│                                                  │
│ [Document Content...]                            │
└──────────────────────────────────────────────────┘
```

---

### **Step 5: Reviewer Submits Review**

**When:** Reviewer completes review  
**Who:** Reviewer  
**What Happens:**

**Review Modal:**
```typescript
┌──────────────────────────────────────────────────────┐
│ 📋 Periodic Review - SOP-2026-0001                   │
├──────────────────────────────────────────────────────┤
│                                                      │
│ Review Outcome:                                      │
│ ○ Document is still valid - No changes needed       │
│ ○ Minor corrections needed - Update and re-approve  │
│ ○ Significant updates needed - Create new version   │
│                                                      │
│ Review Comments:                                     │
│ ┌──────────────────────────────────────────────┐   │
│ │ [Comments explaining review outcome...]      │   │
│ │                                              │   │
│ │                                              │   │
│ └──────────────────────────────────────────────┘   │
│                                                      │
│ Next Review Date:                                    │
│ [2028-01-22] (12 months from today)                 │
│                                                      │
│ Reviewer Signature:                                  │
│ ┌──────────────────────────────────────────────┐   │
│ │ [Type your full name to sign]                │   │
│ └──────────────────────────────────────────────┘   │
│                                                      │
│ ☑ I certify that I have reviewed this document     │
│   and my assessment is accurate                     │
│                                                      │
│ [Cancel]  [Submit Review]                           │
└──────────────────────────────────────────────────────┘
```

**Backend Processing:**
```python
def complete_periodic_review(document, reviewer, outcome, comments, next_review_date):
    """
    Process periodic review completion
    """
    from apps.documents.models import DocumentReview
    
    # Create review record
    review = DocumentReview.objects.create(
        document=document,
        review_date=timezone.now().date(),
        reviewer=reviewer,
        outcome=outcome,
        comments=comments,
        next_review_date=next_review_date
    )
    
    # Update document based on outcome
    if outcome == 'STILL_VALID':
        # Document approved as-is
        document.status = 'EFFECTIVE'
        document.last_review_date = timezone.now().date()
        document.next_review_date = next_review_date
        document.save()
        
        # Terminate workflow
        workflow = DocumentWorkflow.objects.get(
            document=document,
            workflow_type__code='PERIODIC_REVIEW',
            is_terminated=False
        )
        workflow.is_terminated = True
        workflow.completed_at = timezone.now()
        workflow.save()
        
        # Send notification to document owner
        WorkflowNotification.objects.create(
            workflow=workflow,
            recipient=document.author,
            notification_type='EMAIL',
            subject=f'Periodic Review Completed: {document.document_number}',
            message=f'Your document has been reviewed and remains valid.'
        )
        
    elif outcome == 'NEEDS_MINOR_UPDATES':
        # Return to author for minor edits
        document.status = 'DRAFT'
        document.save()
        
        # Create notification for author
        WorkflowNotification.objects.create(
            workflow=workflow,
            recipient=document.author,
            notification_type='EMAIL',
            subject=f'Review Completed - Updates Needed: {document.document_number}',
            message=f'Reviewer has requested minor updates. Comments: {comments}'
        )
        
    elif outcome == 'NEEDS_MAJOR_UPDATES':
        # Document remains effective, but author should create new version
        document.status = 'EFFECTIVE'
        document.last_review_date = timezone.now().date()
        document.next_review_date = next_review_date
        document.save()
        
        # Create notification suggesting new version
        WorkflowNotification.objects.create(
            workflow=workflow,
            recipient=document.author,
            notification_type='EMAIL',
            subject=f'Review Completed - New Version Recommended: {document.document_number}',
            message=f'Reviewer recommends creating a new version. Current version remains effective.'
        )
    
    # Create audit trail
    AuditTrail.objects.create(
        user=reviewer,
        action='PERIODIC_REVIEW_COMPLETED',
        object_type='Document',
        object_id=document.id,
        details={
            'outcome': outcome,
            'comments': comments,
            'next_review_date': str(next_review_date)
        }
    )
    
    return review
```

---

## 📊 **Database Schema Changes**

### **Enhanced Document Model:**
```python
class Document(models.Model):
    # ... existing fields ...
    
    # EXISTING (not being used)
    review_date = models.DateField(null=True, blank=True)
    
    # NEW FIELDS
    last_review_date = models.DateField(
        null=True, 
        blank=True,
        help_text="Date of the most recent periodic review"
    )
    
    review_frequency_months = models.IntegerField(
        default=12,
        help_text="How often this document should be reviewed (in months)"
    )
    
    next_review_date = models.DateField(
        null=True,
        blank=True,
        help_text="Calculated date when next review is due"
    )
```

### **NEW: DocumentReview Model:**
```python
class DocumentReview(models.Model):
    """
    Track periodic review history for compliance
    """
    OUTCOME_CHOICES = [
        ('STILL_VALID', 'Document is still valid'),
        ('NEEDS_MINOR_UPDATES', 'Minor updates needed'),
        ('NEEDS_MAJOR_UPDATES', 'Major updates needed'),
    ]
    
    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    
    review_date = models.DateField(auto_now_add=True)
    
    reviewer = models.ForeignKey(
        User,
        on_delete=models.PROTECT
    )
    
    outcome = models.CharField(
        max_length=30,
        choices=OUTCOME_CHOICES
    )
    
    comments = models.TextField(
        help_text="Reviewer's comments and findings"
    )
    
    next_review_date = models.DateField(
        help_text="When the next review should occur"
    )
    
    reviewer_signature = models.CharField(
        max_length=255,
        help_text="Electronic signature (typed name)"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-review_date']
    
    def __str__(self):
        return f"{self.document.document_number} - Review on {self.review_date}"
```

### **NEW Workflow State:**
```python
# Add to DocumentState model or workflow configuration
UNDER_PERIODIC_REVIEW = 'UNDER_PERIODIC_REVIEW'
```

---

## 🎯 **User Roles & Permissions**

### **Who Does What:**

| Role | Responsibility | Actions |
|------|---------------|---------|
| **System** | Trigger reviews | Schedule review workflows |
| **Reviewer** | Conduct review | Assess document, submit outcome |
| **Author** | Update if needed | Make minor corrections |
| **Approver** | Re-approve | Approve updated document |
| **Admin** | Monitor | View overdue reviews, escalate |

---

## 📈 **Reporting & Compliance**

### **Reports Generated:**

**1. Upcoming Reviews Report**
```
Documents Due for Review (Next 30 Days)
========================================
SOP-2026-0001 | QC Procedure    | Due: Jan 29, 2026 | Reviewer: John Doe
POL-2026-0003 | Safety Policy   | Due: Feb 05, 2026 | Reviewer: Jane Smith
WI-2026-0012  | Lab Work Inst.  | Due: Feb 12, 2026 | Reviewer: Bob Johnson
```

**2. Overdue Reviews Report**
```
Overdue Periodic Reviews
========================
SOP-2025-0005 | OVERDUE by 15 days | Last Review: Jan 2024 | Reviewer: John Doe
POL-2025-0002 | OVERDUE by 8 days  | Last Review: Dec 2024 | Reviewer: Jane Smith
```

**3. Review History Report**
```
Document Review History: SOP-2026-0001
=======================================
Review Date     | Reviewer   | Outcome        | Next Review
----------------|------------|----------------|-------------
Jan 22, 2027    | John Doe   | Still Valid    | Jan 22, 2028
Jan 22, 2026    | Jane Smith | Minor Updates  | Jan 22, 2027
Jan 22, 2025    | Initial    | N/A            | Jan 22, 2026
```

---

## 🔔 **Notification Schedule**

### **Email Notifications Sent:**

| Event | Timing | Recipient | Template |
|-------|--------|-----------|----------|
| **Review Due** | Day review triggered | Reviewer | periodic_review_due.html |
| **Review Reminder** | 7 days before due | Reviewer | review_reminder.html |
| **Review Overdue** | 1 day after due | Reviewer + Admin | review_overdue.html |
| **Review Completed** | On completion | Author | review_completed.html |
| **Review Approved** | On approval | Stakeholders | document_reviewed.html |

---

## 🛡️ **Compliance Features**

### **21 CFR Part 11 Requirements Met:**

✅ **Audit Trail**
- All review actions logged
- Reviewer identity captured
- Electronic signatures (typed name)
- Timestamps recorded

✅ **Periodic Review**
- Configurable review frequency
- Automated reminders
- Review history maintained
- Overdue tracking

✅ **Version Control**
- Review tied to specific version
- New versions reset review cycle
- Historical reviews preserved

✅ **Access Control**
- Only authorized reviewers can review
- Role-based permissions
- Admin oversight capability

---

## 📊 **Example Timeline**

### **Year 1: Initial Approval**
```
Jan 22, 2026:  Document SOP-2026-0001 approved
               - Effective Date: Jan 22, 2026
               - Review Date: Jan 22, 2027
               - Status: EFFECTIVE
```

### **Year 2: First Review**
```
Jan 22, 2027:  Scheduler detects review due
               - Status: UNDER_PERIODIC_REVIEW
               - Email sent to reviewer
               
Jan 25, 2027:  Reviewer completes review
               - Outcome: STILL_VALID
               - Next Review: Jan 22, 2028
               - Status: EFFECTIVE
```

### **Year 3: Review with Updates**
```
Jan 22, 2028:  Scheduler detects review due
               - Status: UNDER_PERIODIC_REVIEW
               - Email sent to reviewer
               
Jan 26, 2028:  Reviewer requests minor updates
               - Outcome: NEEDS_MINOR_UPDATES
               - Status: DRAFT
               - Returned to author
               
Jan 28, 2028:  Author makes corrections
               - Re-submits for approval
               
Jan 30, 2028:  Approver approves
               - Next Review: Jan 30, 2029
               - Status: EFFECTIVE
```

---

## 🎯 **Success Metrics**

### **What Success Looks Like:**

✅ **100% of EFFECTIVE documents** have review dates set  
✅ **95%+ compliance rate** - reviews completed on time  
✅ **Automated notifications** - no manual tracking needed  
✅ **Complete audit trail** - FDA inspection ready  
✅ **User adoption** - reviewers use system voluntarily  

---

## 🚀 **Implementation Phases**

### **Phase 1: Core Functionality (Week 1)**
- Database migrations
- Scheduler task
- Basic workflow

### **Phase 2: Email & Notifications (Week 2)**
- SMTP configuration
- Email templates
- Notification system

### **Phase 3: Frontend & UX (Week 3)**
- Review UI
- My Tasks integration
- Reports

### **Phase 4: Testing & Documentation (Week 4)**
- End-to-end testing
- Compliance documentation
- User training

---

## ✅ **Ready to Start?**

This is the complete design for the Periodic Review system. 

**Next steps:**
1. Review this design - any questions or changes?
2. Get your approval
3. Start implementation Phase 1

**Shall we proceed?** 🚀
