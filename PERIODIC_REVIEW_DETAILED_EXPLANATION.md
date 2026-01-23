# Periodic Review System - Detailed Explanation

**Date:** January 22, 2026  
**Focus:** Implementation details, workflow cases, and UI design

---

## 🎯 What is Periodic Review?

Periodic Review is a **regulatory compliance requirement** for document management systems, especially in FDA-regulated industries (pharmaceuticals, medical devices, etc.).

### Regulatory Background

**21 CFR Part 11** and **GxP guidelines** require:
- Documents must be reviewed periodically (typically annually)
- Review verifies document remains current and accurate
- Review history must be maintained for audit trail
- Reviews must be completed by authorized personnel

### Business Need

Without periodic review:
- ❌ Documents become outdated without detection
- ❌ Regulatory non-compliance
- ❌ Audit findings during inspections
- ❌ No systematic verification process

With periodic review:
- ✅ Systematic document freshness verification
- ✅ Regulatory compliance maintained
- ✅ Complete audit trail
- ✅ Automated reminders and tracking

---

## 📊 System Architecture Overview

### High-Level Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    PERIODIC REVIEW LIFECYCLE                     │
└─────────────────────────────────────────────────────────────────┘

1. DOCUMENT BECOMES EFFECTIVE
   └─> next_review_date set to: effective_date + 12 months
   
2. SCHEDULER MONITORS DAILY (9 AM)
   └─> Checks: next_review_date <= today
   
3. REVIEW BECOMES DUE
   └─> Creates PERIODIC_REVIEW workflow
   └─> Sends notifications to stakeholders
   
4. USER COMPLETES REVIEW
   └─> Chooses outcome: CONFIRMED / UPDATED / UPVERSIONED
   
5. SYSTEM UPDATES
   └─> Records review in audit trail (DocumentReview)
   └─> Updates document: last_review_date, next_review_date
   └─> Terminates workflow
   
6. CYCLE REPEATS
   └─> Next review scheduled automatically
```

### Database Design

```
┌──────────────────────────────┐
│ Document (extended)          │
├──────────────────────────────┤
│ id                           │
│ document_number              │
│ status                       │
│ ...existing fields...        │
│ ┌─────────────────────────┐  │
│ │ NEW PERIODIC REVIEW     │  │
│ │ review_period_months    │  │ ← Default: 12 (annual)
│ │ last_review_date        │  │ ← When last reviewed
│ │ next_review_date        │  │ ← When next review due
│ │ last_reviewed_by_id     │  │ ← Who reviewed
│ └─────────────────────────┘  │
└──────────────────────────────┘
         │
         │ One-to-Many
         ▼
┌──────────────────────────────┐
│ DocumentReview (new)         │
├──────────────────────────────┤
│ id                           │
│ uuid                         │
│ document_id                  │ ← FK to Document
│ reviewed_by_id               │ ← FK to User
│ review_date                  │ ← Date completed
│ outcome                      │ ← CONFIRMED/UPDATED/UPVERSIONED
│ comments                     │ ← Reviewer notes
│ next_review_date             │ ← Next scheduled review
│ new_version_id               │ ← FK to new Document (if upversioned)
│ workflow_id                  │ ← FK to DocumentWorkflow
│ metadata                     │ ← JSON for extensibility
└──────────────────────────────┘
```

---

## 🔄 The Three Workflow Cases

### Case 1: CONFIRMED (No Changes Needed)

**When to use:**
- Document content is still accurate
- No updates required
- References are still valid
- No regulatory changes affecting the document

**What happens:**

```
User Reviews Document
    │
    ├─> Clicks "Complete Review"
    ├─> Selects outcome: "CONFIRMED"
    ├─> Adds comments: "Reviewed - all content current"
    ├─> Submits
    │
System Actions:
    │
    ├─> Creates DocumentReview record
    │   • outcome = "CONFIRMED"
    │   • review_date = today
    │   • next_review_date = today + 12 months
    │
    ├─> Updates Document
    │   • last_review_date = today
    │   • next_review_date = today + 12 months
    │   • last_reviewed_by = current_user
    │   • Status remains: EFFECTIVE (no change)
    │
    ├─> Terminates workflow
    │   • PERIODIC_REVIEW workflow → is_terminated = True
    │
    └─> Audit Trail Created
        • Action: "Periodic review completed - confirmed"
        • All fields logged for compliance
```

**UI Flow:**
```
Document Viewer Page
    │
    ├─> [Periodic Review Due] badge visible
    │
    ├─> User clicks "Complete Review" button
    │
    ▼
Review Modal Opens
    │
    ├─> Shows document details (title, number, version)
    ├─> Shows last review date
    ├─> Radio buttons for outcome:
    │   ○ Confirmed - No changes needed ✓ SELECTED
    │   ○ Updated - Minor changes applied
    │   ○ Up-versioned - Major changes required
    │
    ├─> Comments textarea: "Verified all content is current..."
    │
    ├─> Next review date picker: [Jan 22, 2027] (auto-calculated)
    │
    ├─> [Cancel] [Complete Review] buttons
    │
    └─> User clicks "Complete Review"
        └─> Success: "Review completed successfully. Next review: Jan 22, 2027"
```

**Result:**
- ✅ Document status: EFFECTIVE (unchanged)
- ✅ Review recorded in audit trail
- ✅ Next review scheduled
- ✅ No new version created
- ⏰ Next review due: 1 year from today

---

### Case 2: UPDATED (Minor Changes Applied)

**When to use:**
- Document needs minor corrections
- Typos, formatting fixes
- Updated contact information
- Small clarifications
- **No workflow approval needed** (author can make changes directly)

**What happens:**

```
User Reviews Document
    │
    ├─> Identifies minor issues
    ├─> Downloads document
    ├─> Makes minor edits (typos, formatting)
    ├─> Uploads updated file (SAME version number)
    │
    ├─> Clicks "Complete Review"
    ├─> Selects outcome: "UPDATED"
    ├─> Adds comments: "Fixed 3 typos on page 5, updated contact email"
    ├─> Submits
    │
System Actions:
    │
    ├─> Creates DocumentReview record
    │   • outcome = "UPDATED"
    │   • review_date = today
    │   • next_review_date = today + 12 months
    │
    ├─> Updates Document
    │   • last_review_date = today
    │   • next_review_date = today + 12 months
    │   • File replaced with updated version
    │   • File checksum updated (SHA-256)
    │   • Version number: UNCHANGED (still v01.00)
    │   • Status remains: EFFECTIVE
    │
    ├─> Creates version history entry
    │   • Action: "Minor update during periodic review"
    │   • Previous checksum saved
    │   • New checksum recorded
    │
    ├─> Terminates workflow
    │
    └─> Audit Trail Created
        • All changes logged
        • Old/new checksums recorded
```

**UI Flow:**
```
Document Viewer Page
    │
    ├─> [Periodic Review Due] badge visible
    │
    ├─> User clicks "Complete Review" button
    │
    ▼
Review Modal Opens
    │
    ├─> Radio buttons for outcome:
    │   ○ Confirmed - No changes needed
    │   ○ Updated - Minor changes applied ✓ SELECTED
    │   ○ Up-versioned - Major changes required
    │
    ├─> "Updated" selected → Shows file upload section:
    │   ┌────────────────────────────────────┐
    │   │ Upload Updated File (Optional)     │
    │   │ [Choose File] or drag here         │
    │   │                                    │
    │   │ ℹ️  Minor changes only:            │
    │   │  • Typos, formatting               │
    │   │  • No content changes              │
    │   │  • Same version number             │
    │   └────────────────────────────────────┘
    │
    ├─> Comments textarea: "Fixed typos on page 5, updated email address"
    │
    ├─> [Cancel] [Complete Review] buttons
    │
    └─> User clicks "Complete Review"
        └─> Success: "Review completed. Minor updates applied."
```

**Result:**
- ✅ Document status: EFFECTIVE (unchanged)
- ✅ Same version number (v01.00)
- ✅ Updated file with new checksum
- ✅ Version history entry created
- ✅ Review recorded in audit trail
- ⏰ Next review due: 1 year from today

**Important Notes:**
- ⚠️ "UPDATED" is for **non-substantive changes only**
- ⚠️ Substantive changes require going through full approval workflow (use UPVERSIONED)
- ⚠️ Some organizations may require all changes to go through approval (configure based on SOP)

---

### Case 3: UPVERSIONED (Major Changes Required)

**When to use:**
- Substantive content changes needed
- Regulatory requirement changes
- Process improvements
- New safety information
- Anything requiring **full review and approval workflow**

**What happens:**

```
User Reviews Document
    │
    ├─> Identifies need for major changes
    ├─> Clicks "Complete Review"
    ├─> Selects outcome: "UPVERSIONED"
    ├─> Adds comments: "Regulatory requirements changed - need to update section 4"
    ├─> Submits
    │
System Actions (Part 1 - Record Review):
    │
    ├─> Creates DocumentReview record
    │   • outcome = "UPVERSIONED"
    │   • review_date = today
    │   • next_review_date = today + 12 months (for old version)
    │   • new_version_id = NULL (will be set later)
    │
    ├─> Updates OLD Document
    │   • last_review_date = today
    │   • Status remains: EFFECTIVE
    │   • next_review_date = today + 12 months
    │       (Old version continues to be tracked)
    │
    ├─> Terminates periodic review workflow
    │
    └─> Audit Trail: "Periodic review completed - upversioning required"

System Actions (Part 2 - Create New Version):
    │
    ├─> Calls existing upversion logic
    │   (Same as manual "Create New Version" button)
    │
    ├─> Creates NEW Document
    │   • document_number: SOP-2025-0001-v02.00 (incremented)
    │   • status: DRAFT
    │   • supersedes: points to v01.00
    │   • All metadata copied
    │   • Dependencies SMART-COPIED (to latest effective versions)
    │   • review_period_months: 12 (inherited)
    │   • next_review_date: NULL (will be set when approved)
    │
    ├─> Links new version to DocumentReview
    │   • DocumentReview.new_version_id = new_document.id
    │
    ├─> Creates APPROVAL WORKFLOW for new version
    │   • Type: REVIEW (standard approval workflow)
    │   • State: DRAFT
    │   • Assigned to: original document author
    │
    └─> Sends notifications
        • Author: "New version created from periodic review"
        • Reviewer: "New version pending your review"
        • Approver: "New version will need approval"

When New Version Approved and Becomes EFFECTIVE:
    │
    ├─> New version (v02.00)
    │   • status: EFFECTIVE
    │   • effective_date: today (or future date)
    │   • next_review_date: effective_date + 12 months
    │
    ├─> Old version (v01.00)
    │   • status: SUPERSEDED
    │   • superseded_by: v02.00
    │   • obsolete_date: today
    │   • Still tracked for periodic review (continues existing schedule)
    │
    └─> Both versions now tracked independently
```

**UI Flow:**
```
Document Viewer Page (for v01.00)
    │
    ├─> [Periodic Review Due] badge visible
    │
    ├─> User clicks "Complete Review" button
    │
    ▼
Review Modal Opens
    │
    ├─> Radio buttons for outcome:
    │   ○ Confirmed - No changes needed
    │   ○ Updated - Minor changes applied
    │   ○ Up-versioned - Major changes required ✓ SELECTED
    │
    ├─> "Up-versioned" selected → Shows warning:
    │   ┌────────────────────────────────────────────┐
    │   │ ⚠️  Major Changes Workflow                 │
    │   │                                            │
    │   │ This will:                                 │
    │   │ 1. Create new version v02.00 (DRAFT)       │
    │   │ 2. Start approval workflow                 │
    │   │ 3. Require review and approval             │
    │   │ 4. Current version stays EFFECTIVE until   │
    │   │    new version approved                    │
    │   │                                            │
    │   │ Reason for upversion (required):           │
    │   │ [Regulatory requirements updated]          │
    │   │                                            │
    │   │ Change summary (required):                 │
    │   │ [FDA guidance changed - need to update     │
    │   │  risk assessment section]                  │
    │   └────────────────────────────────────────────┘
    │
    ├─> Version increment radio:
    │   ○ Major increment (v02.00) ✓ SELECTED
    │   ○ Minor increment (v01.01)
    │
    ├─> [Cancel] [Create New Version] buttons
    │
    └─> User clicks "Create New Version"
        │
        ▼
    Success Modal:
        │
        ├─> "✅ Review completed and new version created"
        │
        ├─> "New version: SOP-2025-0001-v02.00 (DRAFT)"
        │
        ├─> "Next steps:"
        │   1. Author will modify v02.00
        │   2. Submit for review
        │   3. Reviewer reviews
        │   4. Approver approves
        │   5. v02.00 becomes EFFECTIVE
        │   6. v01.00 becomes SUPERSEDED
        │
        └─> [View New Version] [Close] buttons
```

**Result:**
- ✅ Old version (v01.00): EFFECTIVE → will become SUPERSEDED when v02.00 approved
- ✅ New version (v02.00): DRAFT → goes through full approval workflow
- ✅ Review recorded in audit trail
- ✅ DocumentReview links old and new versions
- ⏰ Old version next review: 1 year from today (continues to be tracked)
- ⏰ New version next review: Set when it becomes EFFECTIVE

---

## 🎨 Frontend UI Design (Detailed)

### 1. Navigation Integration

**Main Navigation Menu:**
```
┌─────────────────────────────────────────┐
│ EDMS - Electronic Document Management  │
├─────────────────────────────────────────┤
│ 🏠 Dashboard                            │
│ 📄 Documents                            │
│   ├─ Document Library                   │
│   ├─ My Documents                       │
│   ├─ Recent                             │
│   └─ 🆕 Periodic Reviews [3] ← NEW     │
│ ✓ My Tasks                              │
│ 📊 Reports                              │
│ ⚙️ Admin                                │
└─────────────────────────────────────────┘
```

**Badge Logic:**
```typescript
// Show count of documents under periodic review where user is stakeholder
const periodicReviewCount = documents.filter(doc => 
  doc.status === 'EFFECTIVE' && 
  doc.hasActivePeriodicReview &&
  (doc.author === currentUser || 
   doc.reviewer === currentUser || 
   doc.approver === currentUser)
).length;
```

### 2. Periodic Reviews Page

**Route:** `/documents?filter=periodic_review`

**Layout:**
```
┌───────────────────────────────────────────────────────────────┐
│ Periodic Reviews                                    [Refresh] │
├───────────────────────────────────────────────────────────────┤
│                                                               │
│ 📋 Documents Requiring Periodic Review                       │
│                                                               │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ SOP-2025-0001-v01.00 - Quality Management System    🔴 │ │
│ │ Type: SOP  │  Status: EFFECTIVE  │  Due: 3 days overdue │ │
│ │ Last Review: Jan 22, 2025  │  Next Review: Jan 22, 2026  │ │
│ │ [View Document]  [Complete Review]                       │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                               │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ POL-2025-0005-v02.00 - Data Integrity Policy        🟡 │ │
│ │ Type: POLICY  │  Status: EFFECTIVE  │  Due: in 7 days   │ │
│ │ Last Review: Feb 15, 2025  │  Next Review: Feb 15, 2026  │ │
│ │ [View Document]  [Complete Review]                       │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                               │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ WI-2025-0023-v01.00 - Calibration Procedure         🟢 │ │
│ │ Type: WORK INSTRUCTION  │  Status: EFFECTIVE  │  Due: 30d│ │
│ │ Last Review: Mar 1, 2025  │  Next Review: Mar 1, 2026    │ │
│ │ [View Document]  [Complete Review]                       │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                               │
│ Showing 3 of 3 documents                                     │
└───────────────────────────────────────────────────────────────┘

Status Indicators:
🔴 Overdue (red)
🟡 Due soon (<14 days, yellow/orange)
🟢 Upcoming (>14 days, green)
```


### 3. Document Viewer - Review Section

**Enhanced Document Viewer Page:**
```
┌───────────────────────────────────────────────────────────────┐
│ SOP-2025-0001-v01.00 - Quality Management System             │
├───────────────────────────────────────────────────────────────┤
│                                                               │
│ ⚠️  PERIODIC REVIEW DUE                                       │
│ This document is due for periodic review (Due: Jan 22, 2026) │
│ [Complete Review Now]                                         │
│                                                               │
├───────────────────────────────────────────────────────────────┤
│ Document Details │ Version History │ Dependencies │ Review History│
├───────────────────────────────────────────────────────────────┤
│                                                               │
│ Basic Information:                                            │
│ • Document Number: SOP-2025-0001-v01.00                      │
│ • Title: Quality Management System                           │
│ • Status: EFFECTIVE                                          │
│ • Effective Date: Jan 22, 2025                               │
│                                                               │
│ Review Information:                                           │
│ • Review Period: Annual (12 months)                          │
│ • Last Review: Jan 22, 2025 by John Doe                      │
│ • Next Review: Jan 22, 2026                                  │
│ • Days Until Due: -3 (OVERDUE)                               │
│                                                               │
│ [Download PDF] [View Online] [Complete Review]               │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

**Review History Tab (NEW):**
```
┌───────────────────────────────────────────────────────────────┐
│ Review History                                                │
├───────────────────────────────────────────────────────────────┤
│                                                               │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Review #3 - Jan 22, 2025                                │ │
│ │ Reviewed by: John Doe (Document Approver)               │ │
│ │ Outcome: ✅ CONFIRMED - No changes needed                │ │
│ │ Comments: "Reviewed all sections. Content remains       │ │
│ │           current and accurate per latest regulations." │ │
│ │ Next Review: Jan 22, 2026                                │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                               │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Review #2 - Jan 22, 2024                                │ │
│ │ Reviewed by: Jane Smith (Document Reviewer)             │ │
│ │ Outcome: 📝 UPDATED - Minor changes applied              │ │
│ │ Comments: "Updated contact information in section 2.    │ │
│ │           Fixed formatting issues on page 7."           │ │
│ │ Next Review: Jan 22, 2025                                │ │
│ │ File Checksum: abc123... → def456...                     │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                               │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Review #1 - Jan 22, 2023                                │ │
│ │ Reviewed by: John Doe (Document Approver)               │ │
│ │ Outcome: 🔄 UPVERSIONED - Major changes required         │ │
│ │ Comments: "Regulatory requirements changed. Created     │ │
│ │           version 2.0 to incorporate new FDA guidance." │ │
│ │ New Version: SOP-2025-0001-v02.00 (became EFFECTIVE)    │ │
│ │ Next Review: Jan 22, 2024                                │ │
│ │ [View v02.00]                                            │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

### 4. Periodic Review Modal (Main UI Component)

**Modal Design - Step 1 (Outcome Selection):**
```
┌─────────────────────────────────────────────────────────────┐
│ Complete Periodic Review                              [✕]   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ Document: SOP-2025-0001-v01.00                              │
│ Title: Quality Management System                            │
│ Last Review: Jan 22, 2025 by John Doe                       │
│ Review Due: Jan 22, 2026 (3 days overdue)                   │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│ Step 1: Select Review Outcome                               │
│                                                             │
│ ┌─────────────────────────────────────────────────────────┐│
│ │ ○ Confirmed - No changes needed                         ││
│ │   Document remains accurate and current                 ││
│ └─────────────────────────────────────────────────────────┘│
│                                                             │
│ ┌─────────────────────────────────────────────────────────┐│
│ │ ○ Updated - Minor changes applied                       ││
│ │   Non-substantive edits (typos, formatting, contact info)││
│ └─────────────────────────────────────────────────────────┘│
│                                                             │
│ ┌─────────────────────────────────────────────────────────┐│
│ │ ○ Up-versioned - Major changes required                 ││
│ │   Substantive changes requiring full approval workflow  ││
│ └─────────────────────────────────────────────────────────┘│
│                                                             │
│                                     [Cancel] [Next Step →] │
└─────────────────────────────────────────────────────────────┘
```

**Modal - CONFIRMED Path:**
```
┌─────────────────────────────────────────────────────────────┐
│ Complete Periodic Review - Confirmed                  [✕]   │
├─────────────────────────────────────────────────────────────┤
│ Outcome: ✅ CONFIRMED - No changes needed                    │
│                                                             │
│ Review Comments (required):                                 │
│ ┌─────────────────────────────────────────────────────────┐│
│ │ Reviewed all sections of the document. All content     ││
│ │ remains current and accurate. No changes required per   ││
│ │ current regulatory requirements.                        ││
│ │                                                         ││
│ │ Verified:                                               ││
│ │ - References are current                                ││
│ │ - Process descriptions accurate                         ││
│ │ - Regulatory compliance maintained                      ││
│ └─────────────────────────────────────────────────────────┘│
│                                                             │
│ Next Review Schedule:                                       │
│ ┌─────────────────────────────────────────────────────────┐│
│ │ Review Period: [12 months ▼]  (Annual review)          ││
│ │ Next Review Date: Jan 22, 2027 (Auto-calculated)       ││
│ └─────────────────────────────────────────────────────────┘│
│                                                             │
│ ℹ️  The document will remain EFFECTIVE. Review history     │
│    will be updated and audit trail created.                │
│                                                             │
│                                [← Back] [Complete Review]  │
└─────────────────────────────────────────────────────────────┘
```

**Modal - UPDATED Path:**
```
┌─────────────────────────────────────────────────────────────┐
│ Complete Periodic Review - Updated                    [✕]   │
├─────────────────────────────────────────────────────────────┤
│ Outcome: 📝 UPDATED - Minor changes applied                  │
│                                                             │
│ ⚠️  Minor Changes Only                                      │
│ This option is for non-substantive changes:                │
│ • Typos and formatting corrections                          │
│ • Updated contact information                               │
│ • Small clarifications                                      │
│                                                             │
│ For substantive changes, use "Up-versioned" instead.        │
│                                                             │
│ Upload Updated File (optional):                             │
│ ┌─────────────────────────────────────────────────────────┐│
│ │ [Choose File] or drag and drop                          ││
│ │                                                         ││
│ │ Current file: SOP-2025-0001-v01.00.docx                 ││
│ │ Checksum: abc123def456...                               ││
│ │                                                         ││
│ │ 📎 No file selected                                     ││
│ └─────────────────────────────────────────────────────────┘│
│                                                             │
│ Review Comments (required):                                 │
│ ┌─────────────────────────────────────────────────────────┐│
│ │ Fixed 3 typos on page 5, section 2.3.                  ││
│ │ Updated contact email address in footer.                ││
│ │ Corrected formatting of table on page 12.               ││
│ └─────────────────────────────────────────────────────────┘│
│                                                             │
│ Next Review Schedule:                                       │
│ │ Review Period: [12 months ▼]                             │
│ │ Next Review Date: Jan 22, 2027                           │
│                                                             │
│ ℹ️  Version number will remain v01.00. File will be        │
│    replaced and new checksum recorded.                     │
│                                                             │
│                                [← Back] [Complete Review]  │
└─────────────────────────────────────────────────────────────┘
```

**Modal - UPVERSIONED Path:**
```
┌─────────────────────────────────────────────────────────────┐
│ Complete Periodic Review - Up-version Required        [✕]   │
├─────────────────────────────────────────────────────────────┤
│ Outcome: 🔄 UPVERSIONED - Major changes required             │
│                                                             │
│ ⚠️  Major Changes - Approval Workflow                       │
│ This will create a new version requiring full approval:     │
│                                                             │
│ Process:                                                    │
│ 1. New version v02.00 created (DRAFT)                       │
│ 2. Author modifies the document                             │
│ 3. Submit for review                                        │
│ 4. Reviewer reviews                                         │
│ 5. Approver approves with effective date                    │
│ 6. v02.00 becomes EFFECTIVE                                 │
│ 7. v01.00 becomes SUPERSEDED                                │
│                                                             │
│ Current version (v01.00) remains EFFECTIVE until new        │
│ version is approved.                                        │
│                                                             │
│ Version Increment:                                          │
│ ┌─────────────────────────────────────────────────────────┐│
│ │ ● Major increment: v02.00 (Recommended for major changes)││
│ │ ○ Minor increment: v01.01 (For small substantive changes)││
│ └─────────────────────────────────────────────────────────┘│
│                                                             │
│ Reason for Upversion (required):                            │
│ ┌─────────────────────────────────────────────────────────┐│
│ │ FDA guidance updated - ICH Q9(R1) released              ││
│ └─────────────────────────────────────────────────────────┘│
│                                                             │
│ Change Summary (required):                                  │
│ ┌─────────────────────────────────────────────────────────┐│
│ │ Need to update risk assessment section to align with   ││
│ │ new FDA guidance on quality risk management. Will add   ││
│ │ new section on emerging risks and update decision trees.││
│ └─────────────────────────────────────────────────────────┘│
│                                                             │
│ Next Review Schedule (for current version):                 │
│ │ Review Period: [12 months ▼]                             │
│ │ Next Review Date: Jan 22, 2027                           │
│                                                             │
│                           [← Back] [Create New Version]    │
└─────────────────────────────────────────────────────────────┘
```

**Success Modal (After UPVERSIONED):**
```
┌─────────────────────────────────────────────────────────────┐
│ Periodic Review Complete - New Version Created        [✕]   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│              ✅ Review Completed Successfully                │
│                                                             │
│ Original Version:                                           │
│ • SOP-2025-0001-v01.00                                      │
│ • Status: EFFECTIVE (unchanged)                             │
│ • Next Review: Jan 22, 2027                                 │
│                                                             │
│ New Version Created:                                        │
│ • SOP-2025-0001-v02.00                                      │
│ • Status: DRAFT                                             │
│ • Assigned to: John Doe (Author)                            │
│                                                             │
│ Next Steps:                                                 │
│ 1. Author will modify v02.00 with required changes          │
│ 2. Submit for review                                        │
│ 3. Reviewer reviews                                         │
│ 4. Approver approves                                        │
│ 5. v02.00 becomes EFFECTIVE                                 │
│ 6. v01.00 becomes SUPERSEDED                                │
│                                                             │
│ Notifications sent to:                                      │
│ ✉️  John Doe (Author) - New version assigned                │
│ ✉️  Jane Smith (Reviewer) - Future review notification      │
│ ✉️  Bob Johnson (Approver) - Future approval notification   │
│                                                             │
│                    [View v02.00] [Stay on v01.00] [Close]  │
└─────────────────────────────────────────────────────────────┘
```

### 5. My Tasks Integration

**My Tasks Page - Periodic Review Section:**
```
┌───────────────────────────────────────────────────────────────┐
│ My Tasks                                          [Filters ▼]│
├───────────────────────────────────────────────────────────────┤
│                                                               │
│ 📋 Periodic Reviews (3) ────────────────────────────────── ▼ │
│                                                               │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ 🔴 SOP-2025-0001 Quality Management System              │ │
│ │ Status: EFFECTIVE │ Due: 3 days overdue │ Priority: HIGH│ │
│ │ [Complete Review]                                        │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                               │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ 🟡 POL-2025-0005 Data Integrity Policy                  │ │
│ │ Status: EFFECTIVE │ Due: in 7 days │ Priority: MEDIUM   │ │
│ │ [Complete Review]                                        │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                               │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ 🟢 WI-2025-0023 Calibration Procedure                   │ │
│ │ Status: EFFECTIVE │ Due: in 30 days │ Priority: LOW     │ │
│ │ [Complete Review]                                        │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                               │
│ 📝 Pending My Review (2) ─────────────────────────────────▼ │
│                                                               │
│ ... existing review tasks ...                                │
│                                                               │
│ ✅ Pending My Approval (1) ───────────────────────────────▼ │
│                                                               │
│ ... existing approval tasks ...                              │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

**Priority Calculation:**
```typescript
function calculateReviewPriority(document: Document): 'HIGH' | 'MEDIUM' | 'LOW' {
  const daysUntilDue = calculateDaysUntilDue(document.next_review_date);
  
  if (daysUntilDue < 0) return 'HIGH';      // Overdue
  if (daysUntilDue <= 7) return 'HIGH';     // Due within 1 week
  if (daysUntilDue <= 14) return 'MEDIUM';  // Due within 2 weeks
  return 'LOW';                              // Due later
}
```

### 6. Admin Dashboard - Periodic Review Metrics

**Admin Dashboard - New Widget:**
```
┌───────────────────────────────────────────────────────────────┐
│ Admin Dashboard                                               │
├───────────────────────────────────────────────────────────────┤
│                                                               │
│ Periodic Review Status                       [View Details →]│
│ ┌─────────────────────────────────────────────────────────┐ │
│ │                                                         │ │
│ │  Overdue Reviews: 5 🔴                                  │ │
│ │  Due This Week: 12 🟡                                   │ │
│ │  Due This Month: 28 🟢                                  │ │
│ │  Upcoming: 156 ⚪                                        │ │
│ │                                                         │ │
│ │  Compliance Rate: 94.2% (Last 30 days)                 │ │
│ │                                                         │ │
│ │  Recent Reviews:                                        │ │
│ │  • 3 confirmed today                                    │ │
│ │  • 1 updated yesterday                                  │ │
│ │  • 2 upversioned this week                              │ │
│ │                                                         │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

---

## 🔗 Integration with Existing Systems

### 1. Workflow System Integration

**How Periodic Review Interacts with Existing Workflows:**

```
Existing Workflow System:
├─ REVIEW workflow (author → reviewer → approver)
├─ UPVERSIONING (creating new versions)
├─ OBSOLESCENCE (marking documents obsolete)
│
└─ 🆕 PERIODIC_REVIEW workflow (NEW)
    │
    ├─ Uses SAME DocumentWorkflow model
    │  • workflow_type = 'PERIODIC_REVIEW'
    │  • current_state = 'UNDER_PERIODIC_REVIEW'
    │  • Works alongside existing workflows
    │
    ├─ If outcome = UPVERSIONED:
    │  └─> Triggers existing upversioning logic
    │      └─> Creates new REVIEW workflow for new version
    │
    └─ If outcome = CONFIRMED or UPDATED:
       └─> Terminates PERIODIC_REVIEW workflow
           └─> No additional workflows needed
```

**Workflow State Additions:**
```python
# backend/apps/workflows/models_simple.py

WORKFLOW_STATES = [
    # Existing states
    ('DRAFT', 'Draft'),
    ('PENDING_REVIEW', 'Pending Review'),
    ('UNDER_REVIEW', 'Under Review'),
    # ... existing states ...
    
    # NEW state for periodic review
    ('UNDER_PERIODIC_REVIEW', 'Under Periodic Review'),
]

WORKFLOW_TYPES = [
    # Existing types
    ('REVIEW', 'Review Workflow'),
    
    # NEW type for periodic review
    ('PERIODIC_REVIEW', 'Periodic Review'),
]
```

### 2. Notification System Integration

**Notification Types:**
```python
# backend/apps/notifications/models.py

NOTIFICATION_TYPES = [
    # Existing types
    ('DOCUMENT_SUBMITTED', 'Document Submitted for Review'),
    ('REVIEW_ASSIGNED', 'Review Assigned'),
    # ... existing types ...
    
    # NEW types for periodic review
    ('PERIODIC_REVIEW_DUE', 'Periodic Review Due'),
    ('PERIODIC_REVIEW_OVERDUE', 'Periodic Review Overdue'),
    ('PERIODIC_REVIEW_COMPLETED', 'Periodic Review Completed'),
]
```

**When notifications are sent:**
1. **Review Due:** Daily at 9 AM for documents with next_review_date <= today
2. **Review Overdue:** Daily for documents past due date (escalation)
3. **Review Completed:** Immediately after review completion (to all stakeholders)

### 3. Audit Trail Integration

**Audit Events:**
```python
# All periodic review actions logged to audit trail

AUDIT_ACTIONS = [
    'PERIODIC_REVIEW_INITIATED',       # Manual or automatic
    'PERIODIC_REVIEW_COMPLETED_CONFIRMED',
    'PERIODIC_REVIEW_COMPLETED_UPDATED',
    'PERIODIC_REVIEW_COMPLETED_UPVERSIONED',
    'PERIODIC_REVIEW_OVERDUE',         # When becomes overdue
]
```

**Audit Trail Entry Example:**
```json
{
  "action": "PERIODIC_REVIEW_COMPLETED_CONFIRMED",
  "user": "john.doe",
  "timestamp": "2026-01-22T10:30:00Z",
  "document": "SOP-2025-0001-v01.00",
  "details": {
    "outcome": "CONFIRMED",
    "comments": "Reviewed all sections...",
    "previous_review_date": "2025-01-22",
    "next_review_date": "2027-01-22",
    "review_uuid": "abc-123-def-456"
  },
  "ip_address": "192.168.1.100",
  "metadata": {
    "workflow_id": 456,
    "review_id": 789
  }
}
```

---

## 🚀 Future Enhancements (Phase 2+)

### Phase 2: Enhanced Features

1. **Review Checklist:**
   - Configurable checklist items
   - Must complete all items before review
   - Different checklists per document type

2. **Email Notifications:**
   - Email alerts for due reviews
   - Weekly digest of upcoming reviews
   - Escalation emails for overdue reviews

3. **Advanced Scheduling:**
   - Different review periods per document type
   - Risk-based review frequency
   - Configurable reminder schedules

4. **Bulk Review Operations:**
   - Review multiple documents at once
   - Bulk confirm for unchanged documents
   - Batch processing for admins

5. **Review Analytics:**
   - Compliance reports
   - Review completion trends
   - User performance metrics

### Phase 3: Advanced Compliance

1. **Risk-Based Review Periods:**
   - Critical documents: 6 months
   - Standard documents: 12 months
   - Low-risk documents: 24 months

2. **Training Integration:**
   - Mark reviewers as requiring training
   - Block review if training expired
   - Track training completion

3. **Electronic Signatures:**
   - Require e-signature for review completion
   - PIN verification
   - Multi-factor authentication

4. **Delegation:**
   - Temporary delegation during absence
   - Backup reviewers
   - Authority matrix integration

---

## 📊 Database Queries & Performance

### Common Queries

**Find documents due for review:**
```sql
SELECT d.*
FROM documents d
WHERE d.status = 'EFFECTIVE'
  AND d.is_active = TRUE
  AND d.next_review_date <= CURRENT_DATE
  AND NOT EXISTS (
    SELECT 1 FROM document_workflows dw
    WHERE dw.document_id = d.id
      AND dw.workflow_type = 'PERIODIC_REVIEW'
      AND dw.is_terminated = FALSE
  )
ORDER BY d.next_review_date ASC;
```

**Get review history for document:**
```sql
SELECT dr.*, u.username, u.first_name, u.last_name,
       dv.document_number as new_version_number
FROM document_reviews dr
JOIN users u ON dr.reviewed_by_id = u.id
LEFT JOIN documents dv ON dr.new_version_id = dv.id
WHERE dr.document_id = ?
ORDER BY dr.review_date DESC;
```

**Compliance report (last 30 days):**
```sql
-- Reviews completed on time vs overdue
SELECT 
  COUNT(*) as total_reviews,
  SUM(CASE WHEN dr.review_date <= d.next_review_date THEN 1 ELSE 0 END) as on_time,
  SUM(CASE WHEN dr.review_date > d.next_review_date THEN 1 ELSE 0 END) as overdue,
  ROUND(100.0 * SUM(CASE WHEN dr.review_date <= d.next_review_date THEN 1 ELSE 0 END) / COUNT(*), 2) as compliance_rate
FROM document_reviews dr
JOIN documents d ON dr.document_id = d.id
WHERE dr.review_date >= CURRENT_DATE - INTERVAL '30 days';
```

### Performance Optimization

**Indexes:**
```sql
-- Already added in migration
CREATE INDEX idx_documents_next_review_date ON documents(next_review_date);
CREATE INDEX idx_documents_status_active ON documents(status, is_active);
CREATE INDEX idx_document_reviews_document_date ON document_reviews(document_id, review_date);
```

**Caching Strategy:**
- Cache count of pending reviews per user (5-minute TTL)
- Cache compliance metrics (1-hour TTL)
- Real-time for individual review operations

---

## 🎓 Summary of Implementation

### Backend (✅ COMPLETE)

**Models:**
- ✅ Document model extended with 4 review fields
- ✅ DocumentReview model for audit trail
- ✅ Migrations ready

**Services:**
- ✅ PeriodicReviewService with all business logic
- ✅ Daily monitoring scheduler task
- ✅ Workflow and notification creation

**APIs:**
- ✅ 3 REST endpoints (initiate, complete, history)
- ✅ Document filter endpoint
- ✅ Authorization and validation

### Frontend (📋 PLANNED)

**Components to Create:**
1. PeriodicReviewModal (main component)
2. PeriodicReviewList (page for filter=periodic_review)
3. ReviewHistoryTab (in DocumentViewer)
4. PeriodicReviewBadge (navigation menu)
5. MyTasksPeriodicReviewSection (My Tasks integration)

**Estimated Implementation Time:**
- PeriodicReviewModal: 2-3 hours
- PeriodicReviewList: 1-2 hours
- ReviewHistoryTab: 1 hour
- Integration: 1 hour
- **Total: 5-7 hours**

### Testing (🧪 TO DO)

**Unit Tests:**
- Service layer tests
- Model validation tests
- API endpoint tests

**Integration Tests:**
- End-to-end workflow tests
- Scheduler task tests
- Notification tests

**E2E Tests (Playwright):**
- Complete review flow (all 3 outcomes)
- Overdue review handling
- Admin oversight

---

## 🎯 Next Action Items

**For Immediate Deployment:**
1. ✅ Apply migrations
2. ✅ Test API endpoints manually
3. ✅ Run scheduler task once to verify
4. ⏳ Implement frontend components
5. ⏳ Test complete user journey
6. ⏳ Set initial next_review_date for existing EFFECTIVE docs

**After Frontend Complete:**
1. Update deployment documentation
2. Create user training materials
3. Configure email notifications (optional)
4. Set up monitoring alerts for overdue reviews

---

**End of Detailed Explanation**

