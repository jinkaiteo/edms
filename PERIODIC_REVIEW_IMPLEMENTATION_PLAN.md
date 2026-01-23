# Periodic Review System - Implementation Plan

**Date:** January 22, 2026  
**Status:** Ready for Implementation  
**Estimated Timeline:** 3 weeks  
**Priority:** HIGH - Critical for FDA compliance

---

## 📋 **Executive Summary**

Implement a periodic review system for EDMS to ensure documents are reviewed regularly (typically annually) for continued accuracy and relevance. This is a **21 CFR Part 11 compliance requirement**.

### **Key Design Decisions:**

✅ **Multi-Stakeholder Notifications** - Author + Reviewer + Approver + Admins all notified (eliminates single point of failure)  
✅ **Dashboard-Based** - Uses dashboard notifications, not email (deploy immediately, no SMTP needed)  
✅ **Manual + Automatic Triggers** - Button in Workflow tab + daily scheduler  
✅ **Uses Existing Version System** - Minor/Major updates use existing "Create Version" workflow  

---

## 🎯 **System Overview**

### **High-Level Flow:**

```
1. Document Approved → Set review date (e.g., 12 months from now)
   ↓
2. Scheduler Checks Daily OR Admin Manually Triggers
   ↓
3. System Creates Review Workflow
   ↓
4. Dashboard Notifications for ALL Stakeholders:
   - Author (original creator)
   - Reviewer (if assigned)
   - Approver (who approved)
   - All Admins (oversight)
   ↓
5. ANY Stakeholder Completes Review (3 outcomes)
   ↓
6. System Takes Action Based on Outcome
```

---

## 📊 **Three Review Outcomes**

### **Outcome 1: Still Valid ✅**
```
Action: None needed
Result: Document stays EFFECTIVE, review date reset to next year
Timeline: Immediate
```

### **Outcome 2: Minor Updates Needed ⚠️**
```
Action: Create MINOR version (v1.0 → v1.1)
Uses: Existing "Create Version" workflow
Result: v1.0 stays EFFECTIVE until v1.1 approved
Timeline: 1-2 weeks
```

### **Outcome 3: Major Updates Needed 🔄**
```
Action: Create MAJOR version (v1.0 → v2.0)
Uses: Existing "Create Version" workflow
Result: v1.0 stays EFFECTIVE until v2.0 approved
Timeline: 2-4 weeks
```

### **Key Insight:**
Both minor and major updates use your **existing version creation system**. No need to build new workflows - just guide users to create appropriate versions.

---

## 🗓️ **Implementation Timeline**

### **Phase 1: Database & Core System (Week 1)**

**Day 1-2: Database Models**
```python
Tasks:
1. Add fields to Document model:
   - last_review_date (DateField)
   - review_frequency_months (IntegerField, default=12)
   - next_review_date (DateField, calculated)

2. Create DocumentReview model:
   - document (FK to Document)
   - review_date (DateField)
   - reviewer (FK to User)
   - outcome (CharField: STILL_VALID, NEEDS_MINOR_UPDATES, NEEDS_MAJOR_UPDATES)
   - comments (TextField)
   - next_review_date (DateField)
   - reviewer_signature (CharField)
   
3. Add document state:
   - UNDER_PERIODIC_REVIEW

4. Create migration files
5. Test migrations
```

**Day 3: Scheduler Task**
```python
Tasks:
1. Create process_periodic_reviews() task in apps/scheduler/tasks.py
   - Finds documents where next_review_date <= today
   - Status = EFFECTIVE
   - No active review workflow
   
2. For each document:
   - Create PERIODIC_REVIEW workflow
   - Change status to UNDER_PERIODIC_REVIEW
   - Create notifications for ALL stakeholders:
     * Author
     * Reviewer (if assigned)
     * Approver
     * All Admins
   - Set 14-day deadline
   - Create audit trail
   
3. Add to celery beat schedule (daily at 6:00 AM)

4. Test scheduler task
```

**Day 4-5: Manual Trigger API**
```python
Tasks:
1. Create API endpoint: POST /documents/{uuid}/initiate-periodic-review/
   
2. Validation:
   - Document must be EFFECTIVE
   - User must be stakeholder (author/reviewer/approver/admin)
   - No existing active review workflow
   
3. Logic:
   - Create PERIODIC_REVIEW workflow
   - Update document status
   - Create notifications for all stakeholders
   - Return stakeholder list
   
4. Test API endpoint
```

**Deliverables:**
- ✅ Database migrations
- ✅ DocumentReview model
- ✅ Scheduler task (daily at 6 AM)
- ✅ Manual trigger API endpoint
- ✅ Multi-stakeholder notification logic

---

### **Phase 2: Dashboard & Navigation (Week 2)**

**Day 1-2: Backend Filter**
```python
Tasks:
1. Add 'periodic_review' filter to DocumentViewSet.get_queryset()
   
2. Filter logic:
   - Status = UNDER_PERIODIC_REVIEW
   - Has active PERIODIC_REVIEW workflow
   - User is stakeholder (author/reviewer/approver) OR admin
   - Order by next_review_date
   
3. Return with workflow metadata (due date, stakeholders)

4. Test filter with different users
```

**Day 3-4: Frontend Navigation**
```typescript
Tasks:
1. Add "Periodic Review" navigation item
   - Route: /documents?filter=periodic_review
   - Icon: 🔄
   - Badge: Show count of pending reviews
   
2. Create badge count API or compute client-side

3. Add to main navigation bar (same level as My Tasks)

4. Test navigation and filtering
```

**Day 5: My Tasks Integration**
```typescript
Tasks:
1. Update My Tasks view to show periodic reviews separately

2. Add "Periodic Reviews" section showing:
   - Document number and title
   - Due date
   - Days remaining
   - Stakeholders
   
3. Link to review action

4. Test integration
```

**Deliverables:**
- ✅ Backend periodic_review filter
- ✅ "Periodic Review" page with badge count
- ✅ My Tasks integration
- ✅ Document list showing pending reviews

---

### **Phase 3: Workflow Tab & Manual Trigger (Week 2)**

**Day 1-2: Workflow Tab Button**
```typescript
Tasks:
1. Add "Initiate Periodic Review" button to Workflow tab
   
2. Show button only if:
   - Document status = EFFECTIVE
   - No active periodic review
   - User is stakeholder (author/reviewer/approver/admin)
   
3. Confirmation modal:
   - Explain what will happen
   - Show stakeholders who will be notified
   - Set 14-day deadline
   
4. API call handler with error handling

5. Success notification showing stakeholder list

6. Test button visibility and functionality
```

**Day 3: Review Information Display**
```typescript
Tasks:
1. Add review information section to Workflow tab:
   - Last review date (or "Never")
   - Review frequency (e.g., "Annually")
   - Next review due date
   - Days until review
   - Stakeholder list
   
2. Show visual indicator if review overdue (red warning)

3. Test display with different document states
```

**Deliverables:**
- ✅ Manual trigger button in Workflow tab
- ✅ Review information display
- ✅ Confirmation modal
- ✅ Integration with backend API

---

### **Phase 4: Review Completion UI (Week 3)**

**Day 1-2: Review Submission Modal**
```typescript
Tasks:
1. Create PeriodicReviewModal component:
   - Document information display
   - Three outcome radio buttons:
     * Still Valid
     * Minor Updates Needed
     * Major Updates Needed
   - Comments field (required)
   - Next review date picker (pre-filled with +12 months)
   - Electronic signature field
   - Checkbox: "I certify this review is accurate"
   
2. Field validation

3. Submit handler
```

**Day 2-3: Backend Review Completion**
```python
Tasks:
1. Create API endpoint: POST /documents/{uuid}/complete-periodic-review/
   
2. Request body:
   {
     "outcome": "STILL_VALID|NEEDS_MINOR_UPDATES|NEEDS_MAJOR_UPDATES",
     "comments": "...",
     "next_review_date": "2028-01-22",
     "reviewer_signature": "John Doe"
   }
   
3. Outcome handling:
   
   STILL_VALID:
   - Document status → EFFECTIVE
   - Update last_review_date, next_review_date
   - Terminate workflow
   - Notify all stakeholders: "Review completed"
   
   NEEDS_MINOR_UPDATES:
   - Document status → EFFECTIVE (stays active!)
   - Update review dates
   - Terminate workflow
   - Notify AUTHOR: "Create minor version recommended"
   - Include button to open CreateVersionModal (pre-filled)
   
   NEEDS_MAJOR_UPDATES:
   - Document status → EFFECTIVE (stays active!)
   - Update review dates
   - Terminate workflow
   - Notify AUTHOR: "Create major version recommended"
   - Include button to open CreateVersionModal (pre-filled)
   
4. Create DocumentReview record for all outcomes

5. Create audit trail

6. Test all three outcomes
```

**Day 4: Integration with Version Creation**
```typescript
Tasks:
1. Update CreateNewVersionModal to accept pre-filled values:
   - isMajor (boolean) - pre-select version type
   - preFilledReason (string)
   - preFilledSummary (string)
   
2. Update notification component to show "Create Version" button
   when metadata.action_recommended = 'CREATE_MINOR_VERSION' or 'CREATE_MAJOR_VERSION'
   
3. Button handler opens CreateVersionModal with:
   - Minor/Major pre-selected based on review outcome
   - Reason: "Periodic review corrections/updates"
   - Summary: Pre-filled with reviewer comments
   
4. Test version creation from periodic review notification
```

**Day 5: Testing & Polish**
```
Tasks:
1. End-to-end testing:
   - Complete review → Still Valid
   - Complete review → Minor Updates → Create v1.1
   - Complete review → Major Updates → Create v2.0
   
2. Test multi-stakeholder scenarios:
   - Author completes review
   - Reviewer completes review
   - Approver completes review
   - Admin completes review
   
3. Test edge cases:
   - Multiple stakeholders
   - User on leave (others can complete)
   - Overdue reviews
   - Manual trigger vs automatic trigger
   
4. UI polish and error handling

5. Documentation updates
```

**Deliverables:**
- ✅ Review submission modal
- ✅ Backend review completion API
- ✅ All three outcome handlers
- ✅ Integration with version creation
- ✅ Complete end-to-end testing
- ✅ Documentation

---

## 🗂️ **Database Schema**

### **Document Model (Enhanced)**
```python
class Document(models.Model):
    # ... existing fields ...
    
    # EXISTING (currently unused)
    review_date = models.DateField(null=True, blank=True)
    
    # NEW FIELDS
    last_review_date = models.DateField(
        null=True, 
        blank=True,
        help_text="Date of most recent periodic review"
    )
    
    review_frequency_months = models.IntegerField(
        default=12,
        help_text="Review frequency in months (12 = annually)"
    )
    
    next_review_date = models.DateField(
        null=True,
        blank=True,
        help_text="Calculated date when next review is due"
    )
```

### **NEW: DocumentReview Model**
```python
class DocumentReview(models.Model):
    """Track periodic review history for compliance"""
    
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
        help_text="When next review should occur"
    )
    
    reviewer_signature = models.CharField(
        max_length=255,
        help_text="Electronic signature (typed name)"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-review_date']
```

### **NEW: Workflow State**
```python
# Add to document states
UNDER_PERIODIC_REVIEW = 'UNDER_PERIODIC_REVIEW'
```

### **NEW: Workflow Type**
```python
# Add via data migration or initialization script
WorkflowType.objects.create(
    code='PERIODIC_REVIEW',
    name='Periodic Review',
    description='Regular review of effective documents to ensure continued relevance'
)
```

---

## 🎨 **UI Components**

### **1. Approval Modal (Enhanced)**
```
When approving document, show:

┌────────────────────────────────────┐
│ Approve Document                   │
├────────────────────────────────────┤
│ Effective Date: [2026-01-22]      │
│ Review Date: [2027-01-22]          │  ← NEW
│ Review Frequency: [12] months      │  ← NEW
│                                    │
│ [Cancel] [Approve]                 │
└────────────────────────────────────┘
```

### **2. Navigation Bar (Enhanced)**
```
┌─────────────────────────────────────────────────┐
│ [Document Library] [My Documents] [My Tasks]   │
│ [Periodic Review (3)] ← NEW with badge         │
└─────────────────────────────────────────────────┘
```

### **3. Periodic Review Page**
```
┌──────────────────────────────────────────────────┐
│ 🔄 Periodic Review Dashboard                    │
├──────────────────────────────────────────────────┤
│ Documents Requiring Review (3)                   │
│                                                  │
│ ┌──────────────────────────────────────────┐   │
│ │ ⚠️ SOP-2026-0001 v1.0                    │   │
│ │ Quality Control Procedure                │   │
│ │ 📅 Due: Jan 29, 2026 (5 days)           │   │
│ │ 👥 Stakeholders: author01, reviewer01,  │   │
│ │                  approver01, admin       │   │
│ │ [View] [Start Review]                    │   │
│ └──────────────────────────────────────────┘   │
└──────────────────────────────────────────────────┘
```

### **4. Workflow Tab (Enhanced)**
```
┌──────────────────────────────────────────────────┐
│ Workflow Tab                                     │
├──────────────────────────────────────────────────┤
│ Current Status: EFFECTIVE                        │
│ Next Review Due: Jan 22, 2027 (365 days)        │
│                                                  │
│ Available Actions:                               │
│ [📝 Edit Document]                               │
│ [🔄 Create New Version]                          │
│ [🔄 Initiate Periodic Review] ← NEW             │
│ [🗑️ Mark Obsolete]                              │
│                                                  │
│ Review Information:                              │
│ Last Reviewed: Never                             │
│ Review Frequency: Annually                       │
│ Stakeholders: author01, reviewer01, approver01  │
└──────────────────────────────────────────────────┘
```

### **5. Review Submission Modal**
```
┌──────────────────────────────────────────────────┐
│ 📋 Complete Periodic Review                     │
├──────────────────────────────────────────────────┤
│ Document: SOP-2026-0001 v1.0                    │
│ Title: Quality Control Procedure                │
│                                                  │
│ Review Outcome: *                                │
│ ○ Still Valid - No changes needed               │
│ ○ Minor Updates Needed - Create v1.1            │
│ ○ Major Updates Needed - Create v2.0            │
│                                                  │
│ Comments: *                                      │
│ ┌────────────────────────────────────────┐     │
│ │                                        │     │
│ └────────────────────────────────────────┘     │
│                                                  │
│ Next Review Date:                                │
│ [2028-01-22] (12 months)                        │
│                                                  │
│ Electronic Signature: *                          │
│ [Type your full name]                            │
│                                                  │
│ ☑ I certify this review is accurate             │
│                                                  │
│ [Cancel] [Submit Review]                         │
└──────────────────────────────────────────────────┘
```

### **6. Notification (Minor/Major Updates)**
```
┌──────────────────────────────────────────────────┐
│ ⚠️ Minor Updates Required                        │
├──────────────────────────────────────────────────┤
│ SOP-2026-0001 v1.0 requires corrections         │
│                                                  │
│ Reviewer Comments:                               │
│ "Please correct email on page 3 and fix typo"   │
│                                                  │
│ Current Version Status: EFFECTIVE                │
│ (continues until v1.1 is ready)                  │
│                                                  │
│ [Create Minor Version v1.1] ← Pre-filled modal  │
└──────────────────────────────────────────────────┘
```

---

## 🔧 **API Endpoints**

### **New Endpoints to Create:**

```
1. POST /api/v1/documents/{uuid}/initiate-periodic-review/
   Purpose: Manually trigger periodic review
   Auth: Stakeholder or admin
   Response: { workflow_id, stakeholders[], due_date }

2. POST /api/v1/documents/{uuid}/complete-periodic-review/
   Purpose: Submit review outcome
   Auth: Stakeholder or admin
   Body: { outcome, comments, next_review_date, reviewer_signature }
   Response: { status, message, recommended_action }

3. GET /api/v1/documents/?filter=periodic_review
   Purpose: List documents needing periodic review
   Auth: Any authenticated user (filtered by stakeholder)
   Response: Paginated document list with workflow data
```

### **Modified Endpoints:**

```
1. POST /api/v1/documents/{uuid}/approve/
   Add fields: review_date, review_frequency_months
   
2. GET /api/v1/documents/{uuid}/
   Include: last_review_date, next_review_date, review_frequency_months
```

---

## 🔔 **Notification Strategy**

### **Dashboard Notifications (Phase 1)**

All notifications appear in:
1. ✅ "Periodic Review" page (dedicated)
2. ✅ "My Tasks" section
3. ✅ Navigation badge count
4. ✅ In-app notification center

### **Email Notifications (Phase 2 - Future)**

Can be added later when SMTP is configured:
- Review due reminder (7 days before)
- Review overdue alert (1 day after)
- Review completed confirmation
- New version recommended

---

## 📊 **Scheduler Configuration**

### **Add to celery.py:**

```python
app.conf.beat_schedule = {
    # ... existing tasks ...
    
    'process-periodic-reviews': {
        'task': 'apps.scheduler.tasks.process_periodic_reviews',
        'schedule': crontab(hour=6, minute=0),  # Daily at 6:00 AM
        'options': {'priority': 8}  # High priority
    },
}
```

### **Task Registration:**

```python
# apps/scheduler/tasks.py

@shared_task(name='apps.scheduler.tasks.process_periodic_reviews')
def process_periodic_reviews():
    """
    Check for documents that need periodic review.
    Runs daily at 6:00 AM.
    """
    # Implementation in Phase 1
```

---

## ✅ **Testing Checklist**

### **Unit Tests:**
- [ ] DocumentReview model creation
- [ ] Review date calculation
- [ ] Stakeholder identification logic
- [ ] Each outcome handler

### **Integration Tests:**
- [ ] Scheduler task execution
- [ ] Manual trigger API
- [ ] Review completion API
- [ ] Notification creation
- [ ] Version creation integration

### **End-to-End Tests:**
- [ ] Complete flow: Approval → Review due → Complete review (Still Valid)
- [ ] Complete flow: Review → Minor Updates → Create v1.1 → Approve
- [ ] Complete flow: Review → Major Updates → Create v2.0 → Approve
- [ ] Multi-stakeholder: Different users completing reviews
- [ ] Edge cases: Overdue reviews, manual trigger, staff changes

### **User Acceptance Tests:**
- [ ] Admin can manually trigger review
- [ ] Any stakeholder can complete review
- [ ] Review completion creates appropriate version
- [ ] Notifications appear correctly
- [ ] Badge counts update
- [ ] Version history is clean

---

## 📝 **Documentation to Create**

### **User Documentation:**
1. ✅ How to set review dates when approving documents
2. ✅ How to complete periodic reviews
3. ✅ Understanding review outcomes
4. ✅ How to find documents needing review

### **Admin Documentation:**
1. ✅ How to manually trigger reviews
2. ✅ How to monitor overdue reviews
3. ✅ How to handle staff turnover
4. ✅ Compliance reporting

### **Developer Documentation:**
1. ✅ Database schema changes
2. ✅ API endpoint specifications
3. ✅ Scheduler task implementation
4. ✅ Testing procedures

---

## 🎯 **Success Criteria**

### **Functional Requirements:**
✅ Documents can have review dates set on approval
✅ Scheduler automatically triggers reviews daily
✅ Manual trigger button works for admins
✅ All stakeholders notified (author + reviewer + approver + admins)
✅ Any stakeholder can complete review
✅ Three outcomes handled correctly:
   - Still Valid → Reset review date
   - Minor Updates → Recommend v1.1 creation
   - Major Updates → Recommend v2.0 creation
✅ Version creation pre-fills review comments
✅ Complete audit trail maintained

### **Non-Functional Requirements:**
✅ No email dependency (dashboard only)
✅ No operational disruption (current version stays active)
✅ Clean version history
✅ Reuses existing version system
✅ Multi-stakeholder resilience
✅ FDA compliance ready

### **Performance Requirements:**
✅ Scheduler completes in < 5 minutes
✅ Review submission < 2 seconds
✅ Dashboard loads in < 3 seconds
✅ Handles 1000+ documents efficiently

---

## 🚨 **Known Constraints & Assumptions**

### **Constraints:**
1. Email system not configured → Using dashboard notifications only
2. Must not disrupt operations → Current versions stay EFFECTIVE
3. Must handle staff turnover → Multi-stakeholder approach
4. Must reuse existing code → Integration with version system

### **Assumptions:**
1. Users check dashboard regularly
2. 14-day review completion is acceptable
3. 12-month review frequency is standard (but configurable)
4. Electronic signature (typed name) is sufficient
5. Existing version workflow is well-tested

---

## 📋 **Pre-Implementation Checklist**

Before starting implementation:

- [ ] Review and approve this plan
- [ ] Confirm timeline is acceptable (3 weeks)
- [ ] Confirm design decisions (multi-stakeholder, dashboard, version integration)
- [ ] Identify test documents for UAT
- [ ] Set up development environment
- [ ] Create feature branch: `feature/periodic-review-system`
- [ ] Review existing version creation workflow
- [ ] Verify no conflicting work in progress

---

## 🚀 **Getting Started**

### **To Begin Implementation:**

1. Create feature branch:
   ```bash
   git checkout -b feature/periodic-review-system
   ```

2. Start with Phase 1, Day 1:
   ```
   Task: Add fields to Document model
   File: backend/apps/documents/models.py
   ```

3. Follow implementation plan sequentially

4. Test after each phase

5. Merge to develop after complete testing

---

## 📞 **Questions Before Starting?**

Before implementation begins, confirm:

1. ✅ Is the 3-week timeline acceptable?
2. ✅ Do you approve the multi-stakeholder approach?
3. ✅ Is dashboard notification (no email) acceptable for Phase 1?
4. ✅ Do you approve integration with existing version system?
5. ✅ Any changes to the three review outcomes?
6. ✅ Any changes to review frequency defaults?

---

## 📚 **Related Documentation**

- `PERIODIC_REVIEW_SYSTEM_DESIGN.md` - Complete system design
- `PERIODIC_REVIEW_UPDATED_DESIGN.md` - Design with user feedback
- `PERIODIC_REVIEW_OUTCOMES_DETAILED.md` - Detailed outcome explanations
- `PERIODIC_REVIEW_VERSION_WORKFLOW_INTEGRATION.md` - Version system integration
- `CRITICAL_GAPS_ANALYSIS.md` - Why this is priority #1

---

**Status:** ✅ **READY FOR IMPLEMENTATION**  
**Priority:** 🔴 **HIGH - Critical for Compliance**  
**Estimated Effort:** 3 weeks (one developer)  
**Complexity:** Medium  
**Risk:** Low (reuses existing infrastructure)

---

**To start implementation, create feature branch and begin with Phase 1, Day 1!** 🚀
