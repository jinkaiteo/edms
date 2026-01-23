# Periodic Review System - Quick Reference Guide

**Date:** January 22, 2026  
**Status:** Ready for Implementation  
**Priority:** HIGH - Critical for FDA 21 CFR Part 11 Compliance

---

## 🎯 **What Is Periodic Review?**

A system that ensures all EFFECTIVE documents are reviewed regularly (typically annually) to verify they remain:
- Accurate
- Current
- Relevant
- Compliant with regulations

**Why It's Critical:**
- ✅ FDA 21 CFR Part 11 requirement
- ✅ Prevents use of outdated documents
- ✅ Ensures compliance during audits
- ✅ Maintains document quality

---

## 📋 **How It Works - Simple Overview**

### **The Complete Flow:**

```
Step 1: Document Approved
├─ Approver sets review date (e.g., Jan 22, 2027)
└─ Review frequency (e.g., 12 months)

Step 2: Time Passes
├─ Document is EFFECTIVE and being used
└─ Scheduler monitors review dates daily

Step 3: Review Date Arrives
├─ Scheduler detects document needs review (6 AM daily)
└─ OR Admin manually triggers review from Workflow tab

Step 4: System Takes Action
├─ Document status → UNDER_PERIODIC_REVIEW
├─ Creates review workflow
└─ Notifies ALL stakeholders:
    ├─ Author (created document)
    ├─ Reviewer (if assigned)
    ├─ Approver (who approved it)
    └─ All Admins (oversight)

Step 5: Any Stakeholder Reviews Document
├─ Opens "Periodic Review" page or clicks notification
├─ Reviews document content
└─ Submits one of three outcomes

Step 6: System Processes Outcome
└─ See "Three Review Outcomes" below

Step 7: Cycle Repeats
└─ Next review scheduled (e.g., Jan 22, 2028)
```

---

## ⚖️ **Three Review Outcomes**

### **Outcome 1: Still Valid ✅**

**When to Use:**
- Document is accurate and current
- No changes needed
- Can continue as-is

**What Happens:**
```
Reviewer clicks "Still Valid"
↓
Document: UNDER_PERIODIC_REVIEW → EFFECTIVE (immediately)
Review date: Reset to next year (e.g., 2028-01-22)
Notifications: All stakeholders informed "Review completed"
Timeline: Instant
Result: Done! Document continues as v1.0
```

---

### **Outcome 2: Minor Updates Needed ⚠️**

**When to Use:**
- Typos or grammar errors
- Contact information changed
- Small clarifications needed
- Can be fixed in same version

**What Happens:**
```
Reviewer clicks "Minor Updates Needed"
↓
Document: UNDER_PERIODIC_REVIEW → EFFECTIVE (stays active!)
Notification sent to AUTHOR:
  "Create minor version v1.1 recommended"
  [Create Minor Version v1.1] ← Button opens existing modal
↓
Author clicks button
↓
CreateVersionModal opens (pre-filled):
  - Version Type: Minor (v1.1) ← Pre-selected
  - Reason: "Periodic review corrections"
  - Summary: Reviewer's comments ← Pre-filled
↓
Author creates v1.1 (DRAFT)
  - v1.0 stays EFFECTIVE (no disruption!)
  - Author makes corrections to v1.1
↓
Author submits v1.1 for approval
↓
v1.1 goes through normal workflow:
  DRAFT → PENDING_REVIEW → REVIEWED → APPROVED → EFFECTIVE
↓
v1.1 becomes EFFECTIVE
  - v1.0 → SUPERSEDED
  - Next review: 2028-02-01 (12 months from v1.1 effective date)
↓
Timeline: 1-2 weeks
Result: v1.0 → v1.1 (clean version history)
```

**Key Points:**
- ✅ Uses existing "Create Version" workflow
- ✅ v1.0 stays EFFECTIVE (no disruption)
- ✅ Pre-fills modal with review comments
- ✅ Clean version progression: v1.0 → v1.1

---

### **Outcome 3: Major Updates Needed 🔄**

**When to Use:**
- Regulatory requirements changed
- Process significantly changed
- Multiple sections need rewriting
- Better to create new major version

**What Happens:**
```
Reviewer clicks "Major Updates Needed"
↓
Document: UNDER_PERIODIC_REVIEW → EFFECTIVE (stays active!)
Notification sent to AUTHOR:
  "Create major version v2.0 recommended"
  [Create Major Version v2.0] ← Button opens existing modal
↓
Author clicks button
↓
CreateVersionModal opens (pre-filled):
  - Version Type: Major (v2.0) ← Pre-selected
  - Reason: "Periodic review major updates"
  - Summary: Reviewer's recommendations ← Pre-filled
↓
Author creates v2.0 (DRAFT)
  - v1.0 stays EFFECTIVE (operations continue!)
  - Author works on v2.0 at their pace
  - Can take weeks if needed
↓
Author submits v2.0 for approval
↓
v2.0 goes through normal workflow:
  DRAFT → PENDING_REVIEW → REVIEWED → APPROVED → EFFECTIVE
↓
v2.0 becomes EFFECTIVE
  - v1.0 → SUPERSEDED
  - Next review: 2028-03-15 (12 months from v2.0 effective date)
↓
Timeline: 2-4 weeks
Result: v1.0 → v2.0 (major version change)
```

**Key Points:**
- ✅ Uses existing "Create Version" workflow
- ✅ v1.0 stays EFFECTIVE (no disruption)
- ✅ Author has time to make major changes
- ✅ Clean version progression: v1.0 → v2.0

---

## 🎨 **User Interface**

### **1. Setting Review Date (Approval)**

When approving a document, approver sees:

```
┌────────────────────────────────────┐
│ Approve Document                   │
├────────────────────────────────────┤
│                                    │
│ Effective Date:                    │
│ [2026-01-22]                       │
│                                    │
│ Review Date: ← NEW                 │
│ [2027-01-22]                       │
│                                    │
│ Review Frequency: ← NEW            │
│ [12] months (Annually)             │
│                                    │
│ [Cancel] [Approve]                 │
└────────────────────────────────────┘
```

---

### **2. Navigation with New Page**

```
┌─────────────────────────────────────────────────┐
│ Navigation Bar                                   │
├─────────────────────────────────────────────────┤
│ [Document Library] [My Documents] [My Tasks]   │
│ [Periodic Review (3)] ← NEW with badge count   │
└─────────────────────────────────────────────────┘
```

---

### **3. Periodic Review Page**

```
┌──────────────────────────────────────────────────────┐
│ 🔄 Periodic Review Dashboard                        │
├──────────────────────────────────────────────────────┤
│                                                      │
│ Documents Requiring Review (3)                       │
│                                                      │
│ ┌────────────────────────────────────────────────┐ │
│ │ ⚠️ SOP-2026-0001 v1.0                          │ │
│ │ Standard Operating Procedure for QC            │ │
│ │                                                │ │
│ │ 📅 Due: Jan 29, 2026 (5 days remaining)       │ │
│ │ 👥 Stakeholders: author01, reviewer01,        │ │
│ │                  approver01, admin            │ │
│ │ 📊 Status: Pending Review                      │ │
│ │                                                │ │
│ │ [View Document] [Start Review]                 │ │
│ └────────────────────────────────────────────────┘ │
│                                                      │
│ ┌────────────────────────────────────────────────┐ │
│ │ ⚠️ POL-2026-0003 v2.0                          │ │
│ │ Safety Policy                                  │ │
│ │ 📅 Due: Feb 05, 2026 (13 days remaining)      │ │
│ │ ...                                            │ │
│ └────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────┘
```

---

### **4. Workflow Tab with Manual Trigger**

```
┌──────────────────────────────────────────────────┐
│ Document Detail - Workflow Tab                   │
├──────────────────────────────────────────────────┤
│                                                  │
│ Current Status: EFFECTIVE                        │
│ Effective Date: Jan 22, 2025                     │
│                                                  │
│ Periodic Review Information:                     │
│ Last Reviewed: Never                             │
│ Next Review Due: Jan 22, 2027 (365 days)        │
│ Review Frequency: Annually (12 months)           │
│ Stakeholders: author01, reviewer01, approver01  │
│                                                  │
│ Available Actions:                               │
│ ┌──────────────────────────────────────────┐   │
│ │ [📝 Edit Document]                        │   │
│ │ [🔄 Create New Version]                   │   │
│ │ [🔄 Initiate Periodic Review] ← NEW      │   │
│ │ [🗑️ Mark Obsolete]                       │   │
│ └──────────────────────────────────────────┘   │
└──────────────────────────────────────────────────┘
```

---

### **5. Review Submission Modal**

```
┌──────────────────────────────────────────────────────┐
│ 📋 Complete Periodic Review                         │
├──────────────────────────────────────────────────────┤
│                                                      │
│ Document: SOP-2026-0001 v1.0                        │
│ Title: Standard Operating Procedure for QC          │
│ Effective Since: Jan 22, 2025                        │
│                                                      │
│ Review Outcome: *                                    │
│ ○ Still Valid - No changes needed                   │
│ ○ Minor Updates Needed - Create v1.1                │
│ ○ Major Updates Needed - Create v2.0                │
│                                                      │
│ Comments: *                                          │
│ ┌────────────────────────────────────────────────┐ │
│ │ [Document reviewed and found to be current.    │ │
│ │  All procedures are still accurate.]           │ │
│ └────────────────────────────────────────────────┘ │
│                                                      │
│ Next Review Date:                                    │
│ [2028-01-22] (12 months from today)                 │
│                                                      │
│ Electronic Signature: *                              │
│ [Type your full name to sign]                       │
│                                                      │
│ ☑ I certify that I have reviewed this document     │
│   and my assessment is accurate                     │
│                                                      │
│ [Cancel]  [Submit Review]                           │
└──────────────────────────────────────────────────────┘
```

---

### **6. Notification for Updates Needed**

```
┌──────────────────────────────────────────────────────┐
│ ⚠️ Minor Updates Required                            │
├──────────────────────────────────────────────────────┤
│                                                      │
│ Your document SOP-2026-0001 v1.0 requires minor     │
│ corrections based on periodic review.                │
│                                                      │
│ Current Status: EFFECTIVE (continues until v1.1     │
│                            is ready)                 │
│                                                      │
│ Reviewer Comments:                                   │
│ "Please correct the email address on page 3 and     │
│  fix the typo in step 5."                           │
│                                                      │
│ Recommended Action:                                  │
│ Create a minor version (v1.1) with the requested    │
│ corrections.                                         │
│                                                      │
│ [Create Minor Version v1.1]                         │
│ ↑ Opens existing version modal (pre-filled)         │
│                                                      │
└──────────────────────────────────────────────────────┘
```

---

## 🔔 **Multi-Stakeholder Notifications**

### **Who Gets Notified:**

When a document needs review, **ALL** of these people are notified:

| Stakeholder | Why Notified | Can Complete Review? |
|-------------|--------------|---------------------|
| **Author** | Created the document | ✅ Yes |
| **Reviewer** | Reviewed originally | ✅ Yes |
| **Approver** | Approved originally | ✅ Yes |
| **All Admins** | System oversight | ✅ Yes |

### **Benefits:**

✅ **No Single Point of Failure**
- If reviewer is on leave, author or approver can handle it
- If staff member leaves, others are already aware

✅ **Faster Response**
- Multiple people can act
- Reduces bottlenecks

✅ **Built-in Oversight**
- Admins automatically aware
- Can escalate if needed

✅ **Flexible Responsibility**
- ANY stakeholder can complete the review
- Distributed accountability

---

## ⚙️ **Technical Implementation**

### **Database Schema**

**Document Model (Enhanced):**
```python
class Document(models.Model):
    # ... existing fields ...
    
    # NEW FIELDS:
    last_review_date = models.DateField(null=True, blank=True)
    review_frequency_months = models.IntegerField(default=12)
    next_review_date = models.DateField(null=True, blank=True)
```

**NEW DocumentReview Model:**
```python
class DocumentReview(models.Model):
    document = ForeignKey(Document)
    review_date = DateField(auto_now_add=True)
    reviewer = ForeignKey(User)
    outcome = CharField(choices=[
        'STILL_VALID',
        'NEEDS_MINOR_UPDATES',
        'NEEDS_MAJOR_UPDATES'
    ])
    comments = TextField()
    next_review_date = DateField()
    reviewer_signature = CharField(max_length=255)
```

**NEW Document State:**
```
UNDER_PERIODIC_REVIEW
```

**NEW Workflow Type:**
```
PERIODIC_REVIEW
```

---

### **Scheduler Task**

**New Task:** `process_periodic_reviews`

**Schedule:** Daily at 6:00 AM

**What It Does:**
```python
1. Find documents where:
   - status = EFFECTIVE
   - next_review_date <= today
   - No active review workflow

2. For each document:
   - Create PERIODIC_REVIEW workflow
   - Change status to UNDER_PERIODIC_REVIEW
   - Create notifications for:
     * Author
     * Reviewer (if assigned)
     * Approver
     * All Admins
   - Set 14-day deadline
   - Create audit trail
```

---

### **API Endpoints**

**New Endpoints:**

```
1. POST /api/v1/documents/{uuid}/initiate-periodic-review/
   - Manually trigger periodic review
   - Auth: Stakeholder or admin
   
2. POST /api/v1/documents/{uuid}/complete-periodic-review/
   - Submit review outcome
   - Body: { outcome, comments, next_review_date, signature }
   
3. GET /api/v1/documents/?filter=periodic_review
   - List documents needing review
   - Filtered by stakeholder
```

**Modified Endpoints:**

```
1. POST /api/v1/documents/{uuid}/approve/
   - Add: review_date, review_frequency_months
   
2. GET /api/v1/documents/{uuid}/
   - Include: last_review_date, next_review_date
```

---

### **Frontend Routes**

**New Routes:**

```
/documents?filter=periodic_review
  - Dedicated periodic review page
  - Shows all documents needing review
  - Badge count in navigation
```

**Modified Components:**

```
1. ApproverInterface.tsx
   - Add review_date and review_frequency fields
   
2. DocumentDetail.tsx - Workflow Tab
   - Add "Initiate Periodic Review" button
   - Show review information section
   
3. Navigation.tsx
   - Add "Periodic Review" menu item with badge
   
4. CreateNewVersionModal.tsx
   - Accept pre-filled values from review
```

---

## 🎯 **Key Design Decisions**

### **1. Multi-Stakeholder Approach** ✅

**Decision:** Notify author + reviewer + approver + admins (not just reviewer)

**Reasoning:**
- Eliminates single point of failure
- Handles staff turnover/leave
- Faster response time
- Built-in admin oversight

---

### **2. Dashboard Notifications** ✅

**Decision:** Use dashboard notifications, NOT email

**Reasoning:**
- Email system not configured yet
- Can deploy immediately
- Users already check dashboard daily
- Email can be added later as enhancement

---

### **3. Manual + Automatic Triggers** ✅

**Decision:** Both scheduler (automatic) AND manual button

**Reasoning:**
- Scheduler ensures no reviews missed
- Manual button for early reviews or testing
- Admin control for special circumstances
- UI consistency (matches existing workflow buttons)

---

### **4. Integration with Existing Version System** ✅

**Decision:** Use existing "Create Version" workflow for updates

**Reasoning:**
- Don't reinvent the wheel
- Users already familiar with it
- Clean version history (v1.0 → v1.1 → v2.0)
- Less code, reuse tested functionality
- No operational disruption

---

## 📊 **Outcome Comparison Matrix**

| Aspect | Still Valid | Minor Updates | Major Updates |
|--------|-------------|---------------|---------------|
| **Action** | None | Create v1.1 | Create v2.0 |
| **Status During** | EFFECTIVE | EFFECTIVE | EFFECTIVE |
| **Disruption** | None | None | None |
| **Timeline** | Instant | 1-2 weeks | 2-4 weeks |
| **Version Change** | None | v1.0 → v1.1 | v1.0 → v2.0 |
| **Workflow** | None | Existing | Existing |
| **Use Case** | No changes | Small fixes | Major changes |

---

## ⏱️ **Timeline & Phases**

### **Phase 1: Core System (Week 1)**
- Database models
- Scheduler task
- Manual trigger API
- Multi-stakeholder notifications

### **Phase 2: Dashboard & Navigation (Week 2)**
- "Periodic Review" page
- Navigation with badge
- My Tasks integration
- Manual trigger button

### **Phase 3: Review UI & Testing (Week 3)**
- Review submission modal
- Outcome handlers
- Version integration
- End-to-end testing

**Total:** 3 weeks

---

## ✅ **Success Criteria**

### **Functional:**
- ✅ Scheduler runs daily, detects overdue reviews
- ✅ Manual trigger button works for stakeholders
- ✅ All stakeholders notified
- ✅ Any stakeholder can complete review
- ✅ Three outcomes work correctly
- ✅ Version creation pre-fills correctly
- ✅ Complete audit trail

### **Non-Functional:**
- ✅ No email dependency
- ✅ No operational disruption
- ✅ Clean version history
- ✅ Multi-stakeholder resilience
- ✅ FDA compliance ready

---

## 🔍 **Example Scenarios**

### **Scenario 1: Happy Path - Still Valid**

```
Jan 22, 2026: SOP-2026-0001 approved, review_date = Jan 22, 2027
↓
[365 days pass, document used in operations]
↓
Jan 22, 2027 at 6:00 AM: Scheduler detects review due
↓
Notifications sent to: author01, reviewer01, approver01, admin
↓
Jan 23, 2027: reviewer01 logs in, sees notification
↓
Clicks "Start Review" → Reviews document → Selects "Still Valid"
↓
Document status: UNDER_PERIODIC_REVIEW → EFFECTIVE
Review completed, next review: Jan 22, 2028
↓
Done! Document continues as v1.0
```

---

### **Scenario 2: Minor Updates Path**

```
Jan 22, 2027 at 6:00 AM: Scheduler detects review due
↓
Notifications sent to all stakeholders
↓
Jan 23, 2027: approver01 completes review
Outcome: "Minor Updates Needed"
Comments: "Correct email on page 3, fix typo in step 5"
↓
Document stays EFFECTIVE (v1.0)
Author01 gets notification: "Create minor version v1.1 recommended"
↓
Jan 24, 2027: author01 clicks "Create Minor Version v1.1"
Modal opens pre-filled with reviewer's comments
↓
Author creates v1.1 (DRAFT), makes corrections
↓
Jan 25, 2027: Submits v1.1 for review
↓
Jan 26-28: v1.1 reviewed and approved
↓
Jan 29, 2027: v1.1 becomes EFFECTIVE
v1.0 becomes SUPERSEDED
Next review: Jan 29, 2028
↓
Done! Clean version history: v1.0 → v1.1
```

---

### **Scenario 3: Staff Turnover**

```
Jan 22, 2027: Scheduler triggers review for SOP-2026-0001
Notifications sent to:
  - author01 (on vacation for 2 weeks)
  - reviewer01 (left company last month)
  - approver01 (available!)
  - admin (available!)
↓
Jan 23, 2027: approver01 sees notification
↓
Completes review (outcome: Still Valid)
↓
Review completed successfully!
↓
System resilient: Even with 2 stakeholders unavailable,
review was completed by remaining stakeholders
```

---

## 🚨 **Important Notes**

### **What This System Does:**
✅ Automates periodic review tracking
✅ Notifies multiple stakeholders
✅ Provides clear review workflow
✅ Maintains clean version history
✅ Ensures compliance

### **What This System Does NOT Do:**
❌ Send email notifications (Phase 2 - future)
❌ Automatically edit documents
❌ Replace human review judgment
❌ Automatically create new versions

### **Current Version Strategy:**
When updates are needed (minor or major), the current version **stays EFFECTIVE** until the new version is ready. This ensures:
- ✅ No operational disruption
- ✅ Continuous coverage
- ✅ Time for proper updates
- ✅ Quality assurance

---

## 📚 **Related Documents**

For detailed information, see:

1. **PERIODIC_REVIEW_IMPLEMENTATION_PLAN.md** - Complete day-by-day plan
2. **PERIODIC_REVIEW_SYSTEM_DESIGN.md** - Full technical design
3. **PERIODIC_REVIEW_OUTCOMES_DETAILED.md** - Outcome explanations
4. **PERIODIC_REVIEW_VERSION_WORKFLOW_INTEGRATION.md** - Version system integration
5. **CRITICAL_GAPS_ANALYSIS.md** - Why this is priority #1

---

## 🎯 **Quick Decision Guide for Reviewers**

### **Choose "Still Valid" if:**
- ✅ Content is accurate and current
- ✅ No regulatory changes
- ✅ No process changes
- ✅ Document works as-is

### **Choose "Minor Updates" if:**
- ⚠️ Typos or grammar
- ⚠️ Contact info changes
- ⚠️ Small clarifications
- ⚠️ Can fix without major rewrite

### **Choose "Major Updates" if:**
- 🔄 New regulations
- 🔄 Process significantly changed
- 🔄 Multiple sections need rewriting
- 🔄 Better to create new version

---

## 🚀 **Getting Started**

To implement this system, follow:

**PERIODIC_REVIEW_IMPLEMENTATION_PLAN.md**

Start with Phase 1, Day 1:
```bash
git checkout -b feature/periodic-review-system
# Begin with database model changes
```

---

**Status:** ✅ **DOCUMENTED AND READY**  
**Priority:** 🔴 **HIGH - Compliance Critical**  
**Timeline:** 3 weeks  
**Risk:** Low (reuses existing infrastructure)

---

**This system will make your EDMS FDA audit-ready! 🎯**
