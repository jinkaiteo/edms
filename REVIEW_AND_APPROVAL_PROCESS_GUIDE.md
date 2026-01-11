# EDMS Review and Approval Process - Complete Guide

**Based on:** Repository documentation and implementation  
**Date:** 2026-01-10  
**System:** EDMS - Electronic Document Management System

---

## 📋 **Table of Contents**

1. [Overview](#overview)
2. [Document States](#document-states)
3. [User Roles](#user-roles)
4. [Complete Workflow Process](#complete-workflow-process)
5. [Step-by-Step Guide](#step-by-step-guide)
6. [Rejection Paths](#rejection-paths)
7. [Compliance Requirements](#compliance-requirements)
8. [Examples](#examples)

---

## 🎯 **Overview**

The EDMS uses a **simple, linear workflow** designed for regulated industries (pharmaceutical, medical device, food & beverage) that require 21 CFR Part 11 compliance.

### **Core Principle:**
> "Every document must go through review and approval before becoming effective"

### **Key Compliance Features:**
- ✅ No self-review (author cannot review their own document)
- ✅ Clear separation of duties (Author → Reviewer → Approver)
- ✅ Audit trail for all actions
- ✅ Comments required for rejections
- ✅ Scheduled effective dates

---

## 📊 **Document States**

The system uses **7 primary document states** (based on `Simplified_Workflow_Architecture.md`):

```
┌─────────────────────────────────────────────────────────────────┐
│                    DOCUMENT LIFECYCLE STATES                    │
└─────────────────────────────────────────────────────────────────┘

1. DRAFT                          ← Initial state, author working
2. UNDER_REVIEW                   ← Submitted to reviewer
3. REVIEWED                       ← Reviewer approved
4. APPROVED_PENDING_EFFECTIVE     ← Approver approved, waiting for date
5. EFFECTIVE                      ← Currently active document
6. OBSOLETE                       ← Superseded or retired
7. SCHEDULED_FOR_OBSOLESCENCE     ← Will become obsolete on date
```

---

## 👥 **User Roles**

### **Three Primary Roles:**

| Role | Permissions | Responsibilities |
|------|------------|------------------|
| **Author** | Create, Edit (DRAFT only), Submit for Review | Create documents, revise after rejection |
| **Reviewer** | Review documents, Approve/Reject | Technical review, quality check |
| **Approver** | Final Approve/Reject, Set Effective Date | Final authorization, regulatory approval |

### **Role Restrictions:**
- ❌ **Author CANNOT review their own documents** (compliance requirement)
- ❌ **Reviewer CANNOT give final approval** (approver-only function)
- ❌ **Non-approver CANNOT set effective dates**

---

## 🔄 **Complete Workflow Process**

### **Visual Workflow Diagram:**

```
┌──────────────────────────────────────────────────────────────────────────┐
│                   EDMS DOCUMENT REVIEW & APPROVAL WORKFLOW               │
└──────────────────────────────────────────────────────────────────────────┘

   START
     │
     ▼
  ┌──────┐
  │DRAFT │  ← Author creates document
  └──┬───┘
     │ (1) Author clicks "Submit for Review"
     │     Selects reviewer
     ▼
┌──────────────┐
│UNDER_REVIEW  │  ← Reviewer receives notification
└──────┬───────┘
       │
       ├─────(2a) Reviewer APPROVES ─────────┐
       │          Adds review comments        │
       │                                      ▼
       │                               ┌──────────┐
       │                               │ REVIEWED │
       │                               └────┬─────┘
       │                                    │
       │                                    │ (3) Route for Approval
       │                                    │     Selects approver
       │                                    ▼
       │                          ┌──────────────────────┐
       │                          │ AWAITING APPROVAL    │
       │                          └──────────┬───────────┘
       │                                     │
       │                                     ├─(4a) Approver APPROVES
       │                                     │     Sets effective date
       │                                     │     Adds approval comments
       │                                     ▼
       │                          ┌───────────────────────────┐
       │                          │APPROVED_PENDING_EFFECTIVE │
       │                          └──────────┬────────────────┘
       │                                     │
       │                                     │ (5) Scheduler runs daily
       │                                     │     Checks effective_date
       │                                     ▼
       │                               ┌──────────┐
       │                               │EFFECTIVE │ ← Document is active
       │                               └──────────┘
       │
       │
       └─────(2b) Reviewer REJECTS ──────┐
               Adds rejection comments    │
                                         │
       ┌─────(4b) Approver REJECTS ─────┤
       │     Adds rejection reason       │
       │                                 │
       │                                 ▼
       │                            ┌──────┐
       └────────────────────────────►DRAFT │ ← Back to author for revision
                                    └──────┘
                                        │
                                        │ Author revises
                                        │ Can resubmit
                                        └──► (Back to step 1)
```

---

## 📝 **Step-by-Step Guide**

### **STEP 1: Author Creates Document**

**Actions:**
1. Login as Author (e.g., `author01`)
2. Navigate to **Documents** page
3. Click **"Create Document"** button
4. Fill in document details:
   - Title (required)
   - Description (required)
   - Document Type (SOP, POL, WI, etc.)
   - Document Source (Original Digital Draft, etc.)
   - Upload file (DOCX, PDF, etc.)
5. Click **"Create"** button

**Result:**
- Document created in **DRAFT** status
- Author is document owner
- Only author can edit at this stage

**Technical Details:**
- API: `POST /api/v1/documents/`
- Required fields: `title`, `description`, `document_type`, `document_source`, `author`, `file`
- **Regression note:** Author field now automatically included (fixed 2026-01-10)

---

### **STEP 2: Author Submits for Review**

**Actions:**
1. Open the document in DRAFT status
2. Click **"Submit for Review"** button
3. Select a **Reviewer** from dropdown
4. (Optional) Add comments for reviewer
5. Click **"Submit"** button

**Result:**
- Document status changes: **DRAFT → UNDER_REVIEW**
- Reviewer receives notification
- Document locked from editing (read-only)
- Workflow created in database

**Technical Details:**
- API: `POST /api/v1/documents/{id}/submit_for_review/`
- Parameters: `reviewer_id`, `comment` (optional)
- Creates `DocumentWorkflow` record
- Sends notification to reviewer

**Business Rules:**
- ✅ Only document author can submit for review
- ❌ Cannot submit already-reviewed documents
- ❌ Cannot submit if already under review

---

### **STEP 3: Reviewer Reviews Document**

**Actions:**
1. Login as Reviewer (e.g., `reviewer01`)
2. Navigate to **"My Tasks"** or **"Documents"**
3. Open document in **UNDER_REVIEW** status
4. Review document content:
   - Download and read file
   - Check for accuracy
   - Verify completeness
5. Choose action:
   - **Option A: APPROVE** → Continue to Step 3A
   - **Option B: REJECT** → Continue to Step 3B

---

#### **STEP 3A: Reviewer APPROVES**

**Actions:**
1. Click **"Approve"** button
2. Add review comments (recommended):
   - "Document reviewed and approved"
   - "All sections verified"
   - Technical notes
3. Click **"Confirm"** button

**Result:**
- Document status changes: **UNDER_REVIEW → REVIEWED**
- Document ready for final approval
- Author and approver notified
- Review comments recorded in audit trail

**Technical Details:**
- API: `POST /api/v1/documents/{id}/review/`
- Parameters: `action: 'approve'`, `comment`
- Updates workflow state
- Creates audit trail entry

---

#### **STEP 3B: Reviewer REJECTS**

**Actions:**
1. Click **"Reject"** button
2. **Add rejection comments (REQUIRED):**
   - Explain what needs to be fixed
   - Reference specific sections
   - Provide clear guidance for author
   Example:
   ```
   Document needs revision:
   1. Section 3.2 has incorrect procedure steps
   2. Missing safety warnings in section 4
   3. References need updating
   ```
3. Click **"Confirm"** button

**Result:**
- Document status changes: **UNDER_REVIEW → DRAFT**
- Document returns to author for revision
- Author receives notification with comments
- Author can revise and resubmit

**Technical Details:**
- API: `POST /api/v1/documents/{id}/review/`
- Parameters: `action: 'reject'`, `comment` (required)
- Workflow returns to initial state
- Rejection recorded in history

---

### **STEP 4: Route for Approval**

**Actions:**
1. After reviewer approval (status = REVIEWED)
2. Author or Reviewer clicks **"Route for Approval"**
3. Select an **Approver** from dropdown
4. (Optional) Add comments
5. Click **"Submit"** button

**Result:**
- Document routed to approver's task list
- Approver receives notification
- Document awaits final approval

**Technical Details:**
- API: `POST /api/v1/documents/{id}/route_for_approval/`
- Parameters: `approver_id`, `comment` (optional)
- Updates workflow to approval stage

---

### **STEP 5: Approver Final Decision**

**Actions:**
1. Login as Approver (e.g., `approver01`)
2. Navigate to **"My Tasks"**
3. Open document ready for approval
4. Review document:
   - Download and read file
   - Review previous comments
   - Verify regulatory compliance
5. Choose action:
   - **Option A: APPROVE** → Continue to Step 5A
   - **Option B: REJECT** → Continue to Step 5B

---

#### **STEP 5A: Approver APPROVES**

**Actions:**
1. Click **"Approve"** button
2. **Set Effective Date (REQUIRED):**
   - Today = Immediate activation
   - Future date = Scheduled activation
   Example:
   ```
   Effective Date: 2026-01-17 (7 days from now)
   ```
3. Add approval comments:
   - "Final approval granted"
   - "Document meets all requirements"
   - Regulatory references
4. Click **"Confirm"** button

**Result:**
- Document status changes: **REVIEWED → APPROVED_PENDING_EFFECTIVE**
- Document enters activation queue
- Scheduled for automatic activation on effective date
- All stakeholders notified

**Technical Details:**
- API: `POST /api/v1/documents/{id}/approve/`
- Parameters: `action: 'approve'`, `effective_date`, `comment`
- Effective date stored in `document.effective_date`
- Scheduler task monitors for activation

**Business Rules:**
- ✅ Effective date must be today or future (not past)
- ✅ Approver can set immediate or scheduled activation
- ❌ Only users with Approver role can approve

---

#### **STEP 5B: Approver REJECTS**

**Actions:**
1. Click **"Reject"** button
2. **Add detailed rejection reason (REQUIRED):**
   - Explain regulatory concerns
   - Reference specific requirements
   - Provide clear direction
   Example:
   ```
   Document does not meet compliance requirements:
   - Missing required FDA references
   - Procedure not aligned with 21 CFR Part 11
   - Requires management review
   - Needs complete revision of section 5
   ```
3. Click **"Confirm"** button

**Result:**
- Document status changes: **REVIEWED → DRAFT**
- Document returns to author (bypasses review)
- Author receives detailed feedback
- Must be revised and go through full workflow again

**Technical Details:**
- API: `POST /api/v1/documents/{id}/approve/`
- Parameters: `action: 'reject'`, `comment` (required)
- Workflow resets to initial state
- Approver rejection is final (returns to DRAFT, not UNDER_REVIEW)

---

### **STEP 6: Automatic Activation**

**Process:**
- **Scheduler runs daily** (Celery Beat task)
- Checks all documents with status = `APPROVED_PENDING_EFFECTIVE`
- For each document:
  - If `effective_date` = today or past
  - Change status: **APPROVED_PENDING_EFFECTIVE → EFFECTIVE**
  - Send notifications
  - Document is now officially active

**Technical Details:**
- Task: `apps.scheduler.tasks.activate_pending_documents()`
- Runs: Daily at configured time
- Updates: `document.status = 'EFFECTIVE'`
- Logs: Audit trail entry created

**Result:**
- Document is **EFFECTIVE** and officially active
- Users can access effective document
- Supersedes any previous versions
- Workflow complete ✓

---

## 🔄 **Rejection Paths**

### **Rejection Scenarios:**

```
┌────────────────────────────────────────────────────────────┐
│                    REJECTION WORKFLOWS                     │
└────────────────────────────────────────────────────────────┘

Scenario 1: Rejection at Review Stage
   UNDER_REVIEW ──(Reviewer Rejects)──► DRAFT
                                         │
                                         ├─ Author revises
                                         └─ Can resubmit

Scenario 2: Rejection at Approval Stage
   REVIEWED ──(Approver Rejects)──► DRAFT
                                     │
                                     ├─ Author revises
                                     └─ Must go through full workflow again

Scenario 3: Multiple Rejections (Iterative Improvement)
   DRAFT → UNDER_REVIEW → (Reject) → DRAFT
        → UNDER_REVIEW → (Reject) → DRAFT
        → UNDER_REVIEW → REVIEWED → APPROVED → EFFECTIVE
   
   ✓ System supports unlimited rejection cycles
   ✓ All feedback captured in history
   ✓ Quality improves with each iteration
```

### **Rejection Requirements:**

| Requirement | Description | Compliance |
|------------|-------------|------------|
| **Comments Required** | Rejector must provide detailed reason | 21 CFR Part 11 |
| **Return to DRAFT** | Document always returns to DRAFT status | Business Rule |
| **Author Notification** | Author notified with full feedback | Process |
| **Audit Trail** | All rejections logged permanently | Compliance |
| **Resubmission Allowed** | Unlimited revise/resubmit cycles | Quality |

---

## ✅ **Compliance Requirements**

### **21 CFR Part 11 Alignment:**

1. **No Self-Review:**
   - ❌ Author CANNOT review their own document
   - ✅ System enforces role separation
   - ✅ Compliance tested in automated tests

2. **Electronic Signatures:**
   - ✅ Each approval is an electronic signature
   - ✅ User credentials + comment = signature
   - ✅ Audit trail maintains signature records

3. **Audit Trail:**
   - ✅ All workflow actions logged
   - ✅ Who did what, when
   - ✅ Comments preserved
   - ✅ Cannot be modified or deleted

4. **Access Control:**
   - ✅ Role-based permissions
   - ✅ Only authorized users can approve
   - ✅ System enforces segregation of duties

---

## 📚 **Examples**

### **Example 1: Successful Approval (Happy Path)**

```
User: author01
Document: SOP-001 "Equipment Cleaning Procedure"

Timeline:
Day 1, 09:00 - author01 creates document, uploads SOP-001.docx
Day 1, 09:30 - author01 submits for review, assigns to reviewer01
Day 1, 14:00 - reviewer01 reviews and approves
              Comment: "Procedure steps verified, safety warnings adequate"
Day 1, 14:15 - reviewer01 routes to approver01
Day 2, 10:00 - approver01 reviews
Day 2, 10:30 - approver01 approves with effective date = Day 9
              Comment: "Approved for implementation per FDA guidelines"
Day 9, 00:05 - Scheduler activates document automatically
              Status: EFFECTIVE

Result: Document active and available to all users
```

---

### **Example 2: Rejection at Review Stage**

```
User: author02
Document: POL-042 "Data Integrity Policy"

Timeline:
Day 1 - author02 creates and submits for review
Day 2 - reviewer02 rejects
        Comment: "Section 4 missing ALCOA+ principles,
                  References to 21 CFR Part 11 needed,
                  Management approval signature missing"
        Status: DRAFT (returned to author)

Day 3 - author02 revises document:
        - Adds ALCOA+ section
        - Includes regulatory references
        - Adds signature block
        
Day 3 - author02 resubmits for review
Day 4 - reviewer02 approves
        Comment: "All issues addressed, ready for approval"
        
Day 5 - approver02 approves
        Effective Date: Day 12
        
Day 12 - Document becomes EFFECTIVE

Result: Iterative improvement led to compliant document
```

---

### **Example 3: Rejection at Approval Stage**

```
User: author03
Document: WI-088 "Calibration Work Instruction"

Timeline:
Day 1 - author03 creates and submits
Day 2 - reviewer03 approves
Day 3 - approver03 reviews and finds major regulatory issue
Day 3 - approver03 rejects
        Comment: "Calibration intervals do not meet FDA requirements.
                  Must reference equipment manufacturer specs.
                  Requires complete rewrite of section 3.
                  Quality manager review needed before resubmission."
        Status: DRAFT (returned to author, bypasses review)

Day 5 - author03 revises (consults quality manager)
Day 6 - author03 resubmits → Full workflow restarts
Day 7 - reviewer03 re-reviews
Day 7 - reviewer03 approves
Day 8 - approver03 re-reviews
Day 8 - approver03 approves (now compliant)
        Effective Date: Day 15
Day 15 - Document becomes EFFECTIVE

Result: Approver's rejection prevented non-compliant document activation
```

---

## 🎯 **Summary**

### **Complete Workflow Steps:**

1. ✅ **Author Creates** → DRAFT
2. ✅ **Author Submits** → UNDER_REVIEW
3. ✅ **Reviewer Approves** → REVIEWED
4. ✅ **Route to Approver** → Awaiting Approval
5. ✅ **Approver Approves + Effective Date** → APPROVED_PENDING_EFFECTIVE
6. ✅ **Scheduler Activates** → EFFECTIVE

### **Key Principles:**

- 📝 **Clear roles** - Author, Reviewer, Approver
- 🔒 **Compliance** - No self-review, audit trail
- 🔄 **Flexible** - Unlimited reject/resubmit cycles
- ⏰ **Scheduled** - Control when documents become effective
- ✅ **Traceable** - Complete history of all actions

---

## 📞 **References**

**Documentation Sources:**
- `Dev_Docs/Simplified_Workflow_Architecture.md` - Architecture overview
- `Dev_Docs/Workflow_Implementation_Status.md` - Implementation details
- `Dev_Docs/10_Workflow_Action_Buttons_Documentation.md` - UI actions
- `Dev_Docs/3_Enhanced_Simple_Workflow_Setup.md` - Setup guide
- `backend/apps/workflows/models.py` - Data models
- `backend/apps/documents/models.py` - Document states

**Automated Tests:**
- `backend/apps/workflows/tests/test_review_workflow.py` - Review tests
- `backend/apps/workflows/tests/test_approval_workflow.py` - Approval tests
- `e2e/workflows_complete/01_complete_workflow_happy_path.spec.ts` - E2E tests

---

**Document Status:** ✅ Complete  
**Last Updated:** 2026-01-10  
**Based on:** EDMS v1.0 implementation
