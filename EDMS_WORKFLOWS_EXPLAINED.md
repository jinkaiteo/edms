# EDMS Workflows - Comprehensive Explanation

## 📋 Overview

The EDMS (Electronic Document Management System) implements a sophisticated workflow engine designed for pharmaceutical and regulated industries, compliant with 21 CFR Part 11 requirements. The system uses a **Simple Workflow Architecture** that manages the complete document lifecycle from creation to obsolescence.

---

## 🎯 Core Workflow Concepts

### 1. **Workflow Architecture**

The EDMS uses a **state-based workflow system** where:
- **Documents** have statuses that represent their lifecycle position
- **Workflows** track the progression through various states
- **Transitions** are the actions that move documents between states
- **Roles** determine who can perform specific actions

### 2. **Key Components**

| Component | Purpose |
|-----------|---------|
| **Document States** | Define valid statuses (DRAFT, PENDING_REVIEW, EFFECTIVE, etc.) |
| **Document Workflow** | Tracks active workflow for each document |
| **Workflow Transitions** | Records all state changes (audit trail) |
| **Workflow Notifications** | Alerts users about tasks and changes |
| **Document Lifecycle Service** | Business logic for workflow operations |

---

## 📊 Document Status Flow

### Complete Document Lifecycle

```
┌──────────┐
│  DRAFT   │ ← Document created by Author
└────┬─────┘
     │ submit_for_review()
     ▼
┌────────────────┐
│ PENDING_REVIEW │ ← Waiting for Reviewer assignment
└───────┬────────┘
        │ start_review()
        ▼
┌─────────────┐
│ UNDER_REVIEW│ ← Reviewer actively reviewing
└──────┬──────┘
       │ complete_review()
       ▼
┌─────────────────┐
│ REVIEW_COMPLETED│ ← Review passed
└────────┬────────┘
         │ route_for_approval()
         ▼
┌──────────────────┐
│ PENDING_APPROVAL │ ← Waiting for Approver action
└────────┬─────────┘
         │ approve_document()
         ▼
┌──────────────────────────┐
│APPROVED_PENDING_EFFECTIVE│ ← Approved, waiting for effective date
└────────┬─────────────────┘
         │ (automated scheduler)
         ▼
┌───────────┐
│ EFFECTIVE │ ← Active, in use (final state)
└─────┬─────┘
      │
      ├─→ SUPERSEDED (when new version approved)
      │
      └─→ SCHEDULED_FOR_OBSOLESCENCE → OBSOLETE

Alternative paths:
• DRAFT/PENDING_REVIEW/UNDER_REVIEW → TERMINATED (by Author)
• PENDING_APPROVAL → REJECTED → back to DRAFT (by Approver)
```

---

## 🔄 Main Workflows

### **1. Review Workflow (Primary)**

**Purpose**: Take a document from draft through review and approval to effectiveness.

**Flow**: `DRAFT → PENDING_REVIEW → UNDER_REVIEW → REVIEW_COMPLETED → PENDING_APPROVAL → APPROVED_PENDING_EFFECTIVE → EFFECTIVE`

**Key Steps**:

#### Step 1: Submit for Review
- **Who**: Document Author
- **From**: DRAFT
- **To**: PENDING_REVIEW
- **Action**: `submit_for_review(document, reviewer_id, comment)`
- **What happens**:
  - Assigns reviewer to document
  - Creates workflow instance
  - Sends notification to reviewer
  - Document becomes read-only for author

#### Step 2: Start Review
- **Who**: Assigned Reviewer
- **From**: PENDING_REVIEW
- **To**: UNDER_REVIEW
- **Action**: `start_review(document, reviewer)`
- **What happens**:
  - Marks review as in-progress
  - Logs start time for tracking

#### Step 3: Complete Review
- **Who**: Reviewer
- **From**: UNDER_REVIEW
- **To**: REVIEW_COMPLETED (if approved) or DRAFT (if rejected)
- **Action**: `complete_review(document, reviewer, approved=True/False, comment)`
- **What happens**:
  - If approved: Routes to pending approval
  - If rejected: Returns to author for revision
  - Records review comments
  - Sends notifications

#### Step 4: Route for Approval
- **Who**: System (after review completed) or Admin
- **From**: REVIEW_COMPLETED
- **To**: PENDING_APPROVAL
- **Action**: `route_for_approval(document, approver_id)`
- **What happens**:
  - Assigns approver
  - Sends notification to approver
  - Document ready for final approval

#### Step 5: Approve Document
- **Who**: Assigned Approver
- **From**: PENDING_APPROVAL
- **To**: APPROVED_PENDING_EFFECTIVE or EFFECTIVE
- **Action**: `approve_document(document, approver, effective_date, comment)`
- **What happens**:
  - Sets approval date
  - If effective_date is today: status = EFFECTIVE
  - If effective_date is future: status = APPROVED_PENDING_EFFECTIVE
  - Completes workflow
  - Sends notifications

#### Step 6: Automatic Activation (Scheduled)
- **Who**: System (Celery scheduler)
- **From**: APPROVED_PENDING_EFFECTIVE
- **To**: EFFECTIVE
- **Action**: Automated daily task `activate_pending_documents()`
- **What happens**:
  - Runs daily at configured time
  - Activates documents where effective_date ≤ today
  - Updates status to EFFECTIVE
  - Sends effectiveness notifications

---

### **2. Up-versioning Workflow**

**Purpose**: Create new versions of effective documents.

**Flow**: `EFFECTIVE (v1.0) → [Create Version] → DRAFT (v2.0) → [Review Workflow] → EFFECTIVE (v2.0) → Old version becomes SUPERSEDED`

**Key Steps**:

#### Step 1: Create New Version
- **Who**: Author or Admin
- **From**: Document must be EFFECTIVE
- **Action**: `create_new_version(document, major_increment=True/False, reason)`
- **What happens**:
  - Copies document metadata
  - Increments version (major: 2.0, minor: 1.1)
  - New document starts in DRAFT
  - Links to previous version via `supersedes` field
  - Old version remains EFFECTIVE until new version approved

#### Step 2: New Version Workflow
- New version goes through complete Review Workflow
- Independent approval process

#### Step 3: Supersession (Automatic)
- **When**: New version reaches EFFECTIVE status
- **What happens**:
  - Old version status changes to SUPERSEDED
  - Old version workflow marked completed
  - System maintains link between versions
  - Both versions retained for audit trail

---

### **3. Obsolescence Workflow**

**Purpose**: Retire documents that are no longer needed.

**Flow**: `EFFECTIVE → SCHEDULED_FOR_OBSOLESCENCE → OBSOLETE`

**Key Steps**:

#### Step 1: Schedule Obsolescence
- **Who**: Approver or Admin
- **From**: EFFECTIVE
- **To**: SCHEDULED_FOR_OBSOLESCENCE
- **Action**: `schedule_obsolescence(document, obsolescence_date, reason, obsoleted_by)`
- **What happens**:
  - Sets future obsolescence date
  - Records reason for obsolescence
  - Document remains accessible until obsolescence date
  - Notifications sent to stakeholders

#### Step 2: Execute Obsolescence (Automated)
- **Who**: System (Celery scheduler)
- **From**: SCHEDULED_FOR_OBSOLESCENCE
- **To**: OBSOLETE
- **Action**: Automated daily task `process_scheduled_obsolescence()`
- **What happens**:
  - Runs daily
  - Makes documents obsolete when date reached
  - Updates status to OBSOLETE
  - Workflow marked as completed
  - Document moved to archives (still readable for compliance)

---

### **4. Termination Workflow**

**Purpose**: Cancel documents before they become effective (author can withdraw).

**Flow**: `DRAFT/PENDING_REVIEW/UNDER_REVIEW → TERMINATED`

**Key Steps**:

#### Terminate Document
- **Who**: Document Author only
- **From**: DRAFT, PENDING_REVIEW, or UNDER_REVIEW
- **To**: TERMINATED
- **Action**: `terminate_document(document, author, reason)`
- **What happens**:
  - Marks document as terminated
  - Cancels all pending workflow tasks
  - Records termination reason
  - Document becomes inactive
  - Cannot be reactivated (for audit trail)
  - Sends notifications to assigned reviewer/approver

**Important**: Only authors can terminate, and only before document becomes effective.

---

## 👥 Role-Based Access Control

### Roles and Permissions

| Role | Permissions |
|------|-------------|
| **Author** | Create documents, submit for review, terminate before effective |
| **Reviewer** | Review documents, approve/reject reviews, add comments |
| **Approver** | Approve documents, reject back to draft, set effective dates |
| **Document Admin** | All permissions, can override workflows, system configuration |

### Permission Checks

The system enforces permissions at multiple levels:

1. **Model Level**: `document.can_edit(user)`, `document.can_approve(user)`
2. **View Level**: Permission classes check roles before allowing actions
3. **Frontend**: Buttons hidden/disabled based on user permissions
4. **API**: Each endpoint validates user has required role

---

## 📨 Notification System

### Notification Types

| Type | Triggered When | Recipients |
|------|----------------|------------|
| **ASSIGNMENT** | Document assigned for review/approval | Assigned user |
| **REMINDER** | Task overdue or approaching due date | Assigned user |
| **COMPLETION** | Workflow completed | Document author, stakeholders |
| **REJECTION** | Document rejected | Document author |
| **EFFECTIVENESS** | Document becomes effective | All stakeholders |
| **OBSOLESCENCE** | Document scheduled for/becomes obsolete | All stakeholders |

### Notification Channels

- **In-app notifications**: Dashboard notifications panel
- **Email**: (configured via SMTP settings)
- **Audit trail**: All notifications logged for compliance

---

## 🤖 Automated Tasks (Scheduler)

The system uses **Celery Beat** for scheduled automation:

### Daily Tasks

1. **`activate_pending_documents()`** - 9:00 AM daily
   - Activates documents where `effective_date ≤ today`
   - Status: `APPROVED_PENDING_EFFECTIVE` → `EFFECTIVE`

2. **`process_scheduled_obsolescence()`** - 9:00 AM daily
   - Obsoletes documents where `obsolescence_date ≤ today`
   - Status: `SCHEDULED_FOR_OBSOLESCENCE` → `OBSOLETE`

3. **`send_workflow_reminders()`** - 9:00 AM daily
   - Sends reminders for overdue tasks
   - Notifies assignees of pending actions

4. **`cleanup_workflow_tasks()`** - Weekly
   - Removes orphaned workflow data
   - Ensures data consistency

---

This is Part 1 of the explanation. Would you like me to continue with Part 2 covering the technical implementation details, API endpoints, and frontend integration?
