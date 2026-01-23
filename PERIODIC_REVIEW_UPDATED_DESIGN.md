# Periodic Review System - Updated Design (v2)

**Date:** January 22, 2026  
**Status:** Design Phase - Incorporating User Feedback  
**Changes:** Multi-stakeholder notifications, Dashboard-based notifications, Manual trigger button

---

## 🎯 **Updated Flow with Your Suggestions**

```
┌─────────────────────────────────────────────────────────────────┐
│                  UPDATED PERIODIC REVIEW FLOW                    │
└─────────────────────────────────────────────────────────────────┘

1. Document Approved → Set Review Date (12 months from now)
   ↓
2. Scheduler Checks Daily OR Admin Manually Triggers Review
   ↓
3. System Creates Review Workflow
   ↓
4. Dashboard Notifications Created for:
   - Author (original creator)
   - Reviewer (if assigned)
   - Approver (who approved document)
   - All Admins (oversight)
   ↓
5. ANY of these users can complete the review
   ↓
6. Review submitted → Document status updated
   ↓
7. All stakeholders notified of completion
```

---

## 📋 **Change 1: Multi-Stakeholder Notifications**

### **Who Gets Notified:**

| Stakeholder | Why Notified | Can Complete Review? |
|-------------|--------------|---------------------|
| **Author** | Created the document | ✅ Yes |
| **Reviewer** | Reviewed originally | ✅ Yes |
| **Approver** | Approved originally | ✅ Yes |
| **Admins** | System oversight | ✅ Yes |

### **Updated Notification Logic:**

```python
def create_periodic_review_notifications(workflow, document):
    """
    Create dashboard notifications for all stakeholders
    """
    from apps.workflows.models import WorkflowNotification
    from django.contrib.auth import get_user_model
    
    User = get_user_model()
    recipients = []
    
    # 1. Author (original creator)
    if document.author:
        recipients.append(document.author)
    
    # 2. Reviewer (if assigned)
    if document.reviewer and document.reviewer not in recipients:
        recipients.append(document.reviewer)
    
    # 3. Approver (who approved it)
    if document.approver and document.approver not in recipients:
        recipients.append(document.approver)
    
    # 4. All admins (oversight)
    admins = User.objects.filter(
        Q(is_superuser=True) | 
        Q(groups__name='Document Admins')
    ).distinct()
    
    for admin in admins:
        if admin not in recipients:
            recipients.append(admin)
    
    # Create notification for each stakeholder
    for recipient in recipients:
        WorkflowNotification.objects.create(
            workflow=workflow,
            recipient=recipient,
            notification_type='DASHBOARD',  # Changed from EMAIL
            subject=f'Periodic Review Required: {document.document_number}',
            message=f'Document "{document.title}" is due for periodic review. '
                   f'Any stakeholder can complete this review.',
            metadata={
                'document_number': document.document_number,
                'title': document.title,
                'due_date': str(workflow.due_date),
                'last_review_date': str(document.last_review_date) if document.last_review_date else 'Never',
                'stakeholders': [u.username for u in recipients]
            }
        )
    
    return recipients
```

### **Benefits:**

✅ **No Single Point of Failure**
- If reviewer is on leave, author or approver can handle it
- If staff member leaves, others are already aware

✅ **Distributed Responsibility**
- Multiple people accountable
- Faster response time
- Reduces bottlenecks

✅ **Admin Oversight Built-In**
- Admins automatically aware of all pending reviews
- Can escalate if needed
- Can complete review if staff unavailable

---

## 📋 **Change 2: Dashboard-Based Notifications**

### **New: "Periodic Review" Page**

**Location:** Main navigation, same level as "My Tasks"

```
┌─────────────────────────────────────────────────────┐
│ Navigation Bar                                       │
├─────────────────────────────────────────────────────┤
│ [Document Library] [My Documents] [My Tasks]        │
│ [Periodic Review] ← NEW                              │
└─────────────────────────────────────────────────────┘
```

**Page Layout:**

```typescript
// New route: /documents?filter=periodic_review

┌────────────────────────────────────────────────────────┐
│ 🔄 Periodic Review Dashboard                          │
├────────────────────────────────────────────────────────┤
│                                                        │
│ Documents Requiring Periodic Review (3)               │
│                                                        │
│ ┌────────────────────────────────────────────────┐   │
│ │ ⚠️ SOP-2026-0001 v1.0                          │   │
│ │ Standard Operating Procedure for QC            │   │
│ │                                                │   │
│ │ 📅 Due: Jan 29, 2026 (5 days)                 │   │
│ │ 👥 Stakeholders: author01, reviewer01,        │   │
│ │                  approver01, admin            │   │
│ │ 📊 Status: Pending Review                      │   │
│ │                                                │   │
│ │ [View Document] [Start Review]                 │   │
│ └────────────────────────────────────────────────┘   │
│                                                        │
│ ┌────────────────────────────────────────────────┐   │
│ │ ⚠️ POL-2026-0003 v2.0                          │   │
│ │ Safety Policy                                  │   │
│ │                                                │   │
│ │ 📅 Due: Feb 05, 2026 (13 days)                │   │
│ │ 👥 Stakeholders: author02, reviewer01, admin  │   │
│ │ 📊 Status: Pending Review                      │   │
│ │                                                │   │
│ │ [View Document] [Start Review]                 │   │
│ └────────────────────────────────────────────────┘   │
│                                                        │
└────────────────────────────────────────────────────────┘
```

### **Backend Filter Implementation:**

```python
# backend/apps/documents/views.py - DocumentViewSet

def get_queryset(self):
    queryset = super().get_queryset()
    filter_type = self.request.query_params.get('filter')
    
    # ... existing filters ...
    
    elif filter_type == 'periodic_review':
        # Show documents under periodic review where user is a stakeholder
        user = self.request.user
        
        # Get workflows for periodic review
        from apps.workflows.models import DocumentWorkflow
        review_workflows = DocumentWorkflow.objects.filter(
            workflow_type__code='PERIODIC_REVIEW',
            is_terminated=False
        )
        
        # Get document IDs
        review_doc_ids = review_workflows.values_list('document_id', flat=True)
        
        # Filter documents
        queryset = queryset.filter(
            id__in=review_doc_ids,
            status='UNDER_PERIODIC_REVIEW'
        )
        
        # Filter by stakeholder (author, reviewer, approver, or admin)
        if not self.is_admin(user):
            queryset = queryset.filter(
                Q(author=user) |
                Q(reviewer=user) |
                Q(approver=user)
            )
        # Admins see all pending reviews
        
        queryset = queryset.order_by('next_review_date')
```

### **Frontend Navigation Update:**

```typescript
// frontend/src/components/Navigation.tsx

const navigationItems = [
  { name: 'Document Library', path: '/documents?filter=library' },
  { name: 'My Documents', path: '/documents?filter=my_documents' },
  { name: 'My Tasks', path: '/documents?filter=my_tasks' },
  { 
    name: 'Periodic Review', 
    path: '/documents?filter=periodic_review',
    badge: pendingReviewCount,  // Show count badge
    icon: '🔄'
  },
  // ... other items
];
```

### **Dashboard Notification Badge:**

```typescript
// Show notification count in navigation
┌─────────────────────────────────────┐
│ [Periodic Review (3)] ← Badge count │
└─────────────────────────────────────┘
```

### **Integration with My Tasks:**

```typescript
// My Tasks also shows periodic reviews

┌──────────────────────────────────────┐
│ 📋 My Tasks                          │
├──────────────────────────────────────┤
│                                      │
│ PENDING REVIEWS (2)                  │
│ ┌──────────────────────────────┐   │
│ │ Review: POL-2026-0001         │   │
│ │ Due: 5 days                   │   │
│ └──────────────────────────────┘   │
│                                      │
│ PERIODIC REVIEWS (3)  ← NEW SECTION │
│ ┌──────────────────────────────┐   │
│ │ Review: SOP-2026-0001         │   │
│ │ Due: 5 days                   │   │
│ └──────────────────────────────┘   │
│                                      │
└──────────────────────────────────────┘
```

---

## 📋 **Change 3: Manual Trigger Button in Workflow Tab**

### **New Button Location:**

```typescript
// Document Detail View - Workflow Tab

┌──────────────────────────────────────────────────────┐
│ SOP-2026-0001 v1.0                                   │
├──────────────────────────────────────────────────────┤
│ [Details] [Content] [Version History] [Workflow] ←  │
└──────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────┐
│ Workflow Tab                                         │
├──────────────────────────────────────────────────────┤
│                                                      │
│ Current Status: EFFECTIVE                            │
│ Effective Date: Jan 22, 2025                         │
│ Next Review Due: Jan 22, 2027 (365 days)            │
│                                                      │
│ Available Actions:                                   │
│ ┌──────────────────────────────────────────────┐   │
│ │ [📝 Edit Document]                            │   │
│ │ [🔄 Create New Version]                       │   │
│ │ [🔄 Initiate Periodic Review] ← NEW BUTTON   │   │
│ │ [🗑️ Mark Obsolete]                           │   │
│ └──────────────────────────────────────────────┘   │
│                                                      │
│ Review Information:                                  │
│ Last Reviewed: Never                                 │
│ Review Frequency: Annually (12 months)               │
│ Stakeholders: author01, reviewer01, approver01      │
│                                                      │
└──────────────────────────────────────────────────────┘
```

### **Button Visibility Logic:**

```typescript
// Show button only if:
const showPeriodicReviewButton = 
  document.status === 'EFFECTIVE' &&  // Document must be effective
  !hasActivePeriodicReview &&          // No ongoing review
  isStakeholder;                       // User is author/reviewer/approver/admin

// isStakeholder check:
const isStakeholder = (
  user.id === document.author ||
  user.id === document.reviewer ||
  user.id === document.approver ||
  user.is_superuser ||
  user.groups.includes('Document Admins')
);
```

### **Button Click Handler:**

```typescript
const handleInitiatePeriodicReview = async () => {
  // Show confirmation modal
  const confirmed = await showConfirmation({
    title: 'Initiate Periodic Review',
    message: `
      Are you sure you want to initiate periodic review for this document?
      
      This will:
      - Change document status to UNDER_PERIODIC_REVIEW
      - Notify all stakeholders (author, reviewer, approver, admins)
      - Set a 14-day deadline for review completion
      
      Any stakeholder can complete the review.
    `,
    confirmText: 'Initiate Review',
    cancelText: 'Cancel'
  });
  
  if (!confirmed) return;
  
  try {
    // Call API
    const response = await api.post(
      `/documents/${document.uuid}/initiate-periodic-review/`
    );
    
    // Success notification
    showNotification({
      type: 'success',
      message: 'Periodic review initiated. All stakeholders have been notified.',
    });
    
    // Refresh document
    refetchDocument();
    
  } catch (error) {
    showNotification({
      type: 'error',
      message: 'Failed to initiate periodic review. Please try again.',
    });
  }
};
```

### **Backend API Endpoint:**

```python
# backend/apps/documents/views.py - DocumentViewSet

@action(detail=True, methods=['post'])
def initiate_periodic_review(self, request, uuid=None):
    """
    Manually initiate periodic review for a document
    """
    document = self.get_object()
    user = request.user
    
    # Validation
    if document.status != 'EFFECTIVE':
        return Response(
            {'error': 'Only EFFECTIVE documents can be reviewed'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Check if user is stakeholder
    is_stakeholder = (
        user == document.author or
        user == document.reviewer or
        user == document.approver or
        user.is_superuser or
        user.groups.filter(name='Document Admins').exists()
    )
    
    if not is_stakeholder:
        return Response(
            {'error': 'Only stakeholders can initiate periodic review'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Check for existing active review
    existing_review = DocumentWorkflow.objects.filter(
        document=document,
        workflow_type__code='PERIODIC_REVIEW',
        is_terminated=False
    ).exists()
    
    if existing_review:
        return Response(
            {'error': 'Document already has an active periodic review'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Create periodic review workflow
    from apps.workflows.models import WorkflowType
    workflow_type = WorkflowType.objects.get(code='PERIODIC_REVIEW')
    
    workflow = DocumentWorkflow.objects.create(
        document=document,
        workflow_type=workflow_type,
        initiated_by=user,
        due_date=timezone.now().date() + timedelta(days=14)
    )
    
    # Update document status
    document.status = 'UNDER_PERIODIC_REVIEW'
    document.save()
    
    # Create notifications for all stakeholders
    recipients = create_periodic_review_notifications(workflow, document)
    
    # Create audit trail
    AuditTrail.objects.create(
        user=user,
        action='PERIODIC_REVIEW_INITIATED_MANUAL',
        object_type='Document',
        object_id=document.id,
        details={
            'initiated_by': user.username,
            'stakeholders': [r.username for r in recipients],
            'due_date': str(workflow.due_date)
        }
    )
    
    return Response({
        'message': 'Periodic review initiated successfully',
        'workflow_id': workflow.id,
        'stakeholders': [r.username for r in recipients],
        'due_date': workflow.due_date
    })
```

### **Benefits of Manual Button:**

✅ **Early Reviews**
- Don't wait for scheduler if document needs early review
- Regulatory changes may require immediate review

✅ **Testing**
- Easy to test review workflow
- No need to manipulate dates

✅ **Admin Control**
- Admin can trigger reviews on demand
- Useful for audits or special circumstances

✅ **UI Consistency**
- Matches existing workflow actions
- Users expect buttons in Workflow tab

---

## 📊 **Updated Implementation Plan**

### **Phase 1: Core System (Week 1)**

**Day 1-2: Database & Models**
```python
# Models to create/update:
1. Document model - add review fields
2. DocumentReview model - track reviews
3. WorkflowType - add PERIODIC_REVIEW type
4. DocumentState - add UNDER_PERIODIC_REVIEW status
```

**Day 3: Scheduler Task**
```python
# Create scheduler task that:
1. Finds documents with next_review_date <= today
2. Creates periodic review workflow
3. Creates notifications for ALL stakeholders (not just reviewer)
4. Updates document status
```

**Day 4-5: Manual Trigger API**
```python
# Create API endpoint:
1. POST /documents/{uuid}/initiate-periodic-review/
2. Validation logic (status, permissions)
3. Create workflow and notifications
4. Return response with stakeholder list
```

### **Phase 2: Dashboard & Navigation (Week 2)**

**Day 1-2: Backend Filter**
```python
# Add periodic_review filter to DocumentViewSet
1. Filter by status=UNDER_PERIODIC_REVIEW
2. Filter by stakeholder (author/reviewer/approver/admin)
3. Order by next_review_date
4. Return with workflow metadata
```

**Day 3-4: Frontend Navigation**
```typescript
# Add new navigation item:
1. "Periodic Review" menu item
2. Badge showing count of pending reviews
3. Route to /documents?filter=periodic_review
4. Document list filtered for reviews
```

**Day 5: My Tasks Integration**
```typescript
# Update My Tasks view:
1. Add "Periodic Reviews" section
2. Show pending reviews separately
3. Link to review action
```

### **Phase 3: Workflow Tab Button (Week 2)**

**Day 1-2: Frontend Button**
```typescript
# Add to Workflow tab:
1. "Initiate Periodic Review" button
2. Visibility logic (status, permissions)
3. Confirmation modal
4. API call handler
5. Success/error notifications
```

**Day 3: Review Information Display**
```typescript
# Show on Workflow tab:
1. Last review date
2. Review frequency
3. Next review due date
4. Stakeholder list
5. Days until review
```

### **Phase 4: Review Completion UI (Week 3)**

**Day 1-3: Review Modal**
```typescript
# Create review submission UI:
1. Review outcome selection
2. Comments field
3. Next review date picker
4. Signature field
5. Submit handler
```

**Day 4-5: Testing & Polish**
```
1. End-to-end testing
2. Multiple stakeholder scenarios
3. UI polish
4. Documentation
```

---

## 🎯 **Updated Success Criteria**

### **Must Have:**

✅ **Multi-Stakeholder Notifications**
- Author, reviewer, approver, and admins all notified
- Any stakeholder can complete review
- No single point of failure

✅ **Dashboard-Based Workflow**
- "Periodic Review" page shows pending reviews
- Badge count in navigation
- Integration with My Tasks
- No dependency on email system

✅ **Manual + Automatic Triggers**
- Scheduler runs daily (automatic)
- Button in Workflow tab (manual)
- Both create same workflow
- Consistent behavior

✅ **Complete Audit Trail**
- Who initiated review (manual vs automatic)
- Who was notified
- Who completed review
- Review outcome and comments

---

## 📋 **Comparison: Original vs Updated**

| Feature | Original Design | Updated Design |
|---------|----------------|----------------|
| **Notifications** | Reviewer only | Author + Reviewer + Approver + Admins |
| **Notification Method** | Email (not ready) | Dashboard + Badge (works now) |
| **Trigger Method** | Scheduler only | Scheduler + Manual button |
| **UI Location** | My Tasks only | Dedicated page + My Tasks |
| **Single Point of Failure** | Yes (reviewer) | No (multiple stakeholders) |
| **Staff Turnover Resilient** | No | Yes |
| **Immediate Deployment** | No (needs SMTP) | Yes (dashboard only) |

---

## ✅ **Your Suggestions Impact**

### **Suggestion 1: Multi-Stakeholder** 
**Impact:** 🎯 **CRITICAL IMPROVEMENT**
- Eliminates biggest risk (single person dependency)
- Makes system production-ready
- Handles real-world scenarios

### **Suggestion 2: Dashboard Notifications**
**Impact:** 🚀 **ENABLES IMMEDIATE DEPLOYMENT**
- Can deploy without SMTP setup
- Consistent with existing UI
- Email becomes Phase 2 enhancement

### **Suggestion 3: Manual Button**
**Impact:** 💡 **BETTER UX & CONSISTENCY**
- Matches existing workflow patterns
- Admin control for edge cases
- Easier testing and development

---

## 🚀 **Ready to Implement?**

The updated design is:
✅ **More robust** (multi-stakeholder)
✅ **Immediately deployable** (no email dependency)
✅ **Better UX** (manual button + dedicated page)
✅ **Production-ready** (handles staff turnover)

**Shall we start with Phase 1 (Database & Models)?**

I can begin implementing right away! 🎯
