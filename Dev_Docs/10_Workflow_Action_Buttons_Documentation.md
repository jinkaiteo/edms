# EDMS Workflow Action Buttons Documentation

## Overview

This document provides comprehensive documentation for all workflow action buttons available in the Document Management page's workflow tab. These buttons implement the role-based workflow system as defined in the EDMS specifications.

## Document Location

**File**: `frontend/src/components/documents/DocumentViewer.tsx`  
**Function**: `getAvailableActions()`  
**UI Location**: Document Management → Select Document → Workflow Tab → Available Actions Section

## Action Buttons Inventory

### 1. 📤 Submit for Review (Step 2)

**Purpose**: Initiates the review workflow by allowing document author to select a reviewer and submit the document for review.

- **Label**: "📤 Submit for Review (Step 2)"
- **Color**: Blue (`bg-blue-600`)
- **Description**: "Select reviewer and route document for review"
- **Action Key**: `submit_for_review`
- **Modal Triggered**: `SubmitForReviewModal`

**Visibility Conditions**:
```javascript
document.status.toLowerCase() === 'draft' && hasWritePermission
```

**Permission Logic**:
- User has write permission (`user.permissions.includes('write')`) OR
- User is staff (`user.is_staff`) OR  
- User is document author (`document.author === user.id`)

**EDMS Reference**: Lines 113-115 in EDMS_details.txt

---

### 2. 📋 Start Review Process

**Purpose**: Opens the reviewer interface for assigned reviewers to begin the document review process.

- **Label**: "📋 Start Review Process"
- **Color**: Blue (`bg-blue-600`)
- **Description**: "Download document and provide review comments"
- **Action Key**: `open_reviewer_interface`
- **Component Triggered**: `ReviewerInterface`

**Visibility Conditions**:
```javascript
document.status.toLowerCase() === 'pending_review' && hasReviewPermission
```

**Permission Logic**:
- User has review permission (`user.permissions.includes('review')`) OR
- User is staff (`user.is_staff`) OR
- User is assigned reviewer (`document.reviewer === user.id`)

**EDMS Reference**: Lines 116-119 in EDMS_details.txt

---

### 3. 👀 View Review Status

**Purpose**: Allows document authors to monitor review progress when they don't have reviewer permissions.

- **Label**: "👀 View Review Status"
- **Color**: Gray (`bg-gray-600`)
- **Description**: "Monitor review progress"
- **Action Key**: `view_review_status`

**Visibility Conditions**:
```javascript
document.status.toLowerCase() === 'pending_review' && isDocumentAuthor && !hasReviewPermission
```

**Permission Logic**:
- User is document author AND
- User does NOT have review permissions

---

### 4. 📋 Continue Review

**Purpose**: Allows assigned reviewers to continue an in-progress review.

- **Label**: "📋 Continue Review"
- **Color**: Blue (`bg-blue-600`)
- **Description**: "Complete document review process"
- **Action Key**: `open_reviewer_interface`
- **Component Triggered**: `ReviewerInterface`

**Visibility Conditions**:
```javascript
document.status.toLowerCase() === 'under_review' && hasReviewPermission && isAssignedReviewer
```

**Permission Logic**:
- User has review permission AND
- User is the assigned reviewer for this document

---

### 5. ✅ Route for Approval

**Purpose**: After review completion, allows authors to select an approver and route the document for approval.

- **Label**: "✅ Route for Approval"
- **Color**: Green (`bg-green-600`)
- **Description**: "Select approver and route for approval"
- **Action Key**: `route_for_approval`

**Visibility Conditions**:
```javascript
['review_completed', 'reviewed'].includes(document.status.toLowerCase()) && hasWritePermission && isDocumentAuthor
```

**Permission Logic**:
- User has write permission AND
- User is document author

**EDMS Reference**: Line 120 in EDMS_details.txt

---

### 6. ✅ Start Approval Process

**Purpose**: Opens approval interface for assigned approvers to approve or reject the document.

- **Label**: "✅ Start Approval Process"
- **Color**: Green (`bg-green-600`)
- **Description**: "Review and approve/reject document"
- **Action Key**: `open_approver_interface`

**Visibility Conditions**:
```javascript
document.status.toLowerCase() === 'pending_approval' && hasApprovalPermission && isAssignedApprover
```

**Permission Logic**:
- User has approval permission AND
- User is the assigned approver for this document

**EDMS Reference**: Lines 121-124 in EDMS_details.txt

---

### 7. 📅 Set Effective Date

**Purpose**: After approval, allows approvers to set when the document becomes effective.

- **Label**: "📅 Set Effective Date"
- **Color**: Green (`bg-green-600`)
- **Description**: "Set when document becomes effective"
- **Action Key**: `set_effective_date`

**Visibility Conditions**:
```javascript
document.status.toLowerCase() === 'approved' && hasApprovalPermission && isAssignedApprover
```

**Permission Logic**:
- User has approval permission AND
- User is the assigned approver for this document

**EDMS Reference**: Line 125 in EDMS_details.txt

---

### 8. 📝 Create New Version

**Purpose**: Initiates up-versioning workflow for effective documents.

- **Label**: "📝 Create New Version"
- **Color**: Blue (`bg-blue-600`)
- **Description**: "Start up-versioning workflow"
- **Action Key**: `create_revision`

**Visibility Conditions**:
```javascript
document.status.toLowerCase() === 'effective' && hasWritePermission
```

**Permission Logic**:
- User has write permission

**EDMS Reference**: Lines 129-135 in EDMS_details.txt

---

### 9. 🗑️ Mark Obsolete

**Purpose**: Initiates obsolescence workflow for effective documents that have no dependencies.

- **Label**: "🗑️ Mark Obsolete"
- **Color**: Red (`bg-red-600`)
- **Description**: "Start obsolescence workflow"
- **Action Key**: `initiate_obsolescence`

**Visibility Conditions**:
```javascript
document.status.toLowerCase() === 'effective' && hasWritePermission && !hasDocumentDependencies()
```

**Permission Logic**:
- User has write permission AND
- Document has no dependencies

**EDMS Reference**: Lines 137-153 in EDMS_details.txt

---

## Permission System

### Core Permission Calculation

```javascript
const isDocumentAuthor = document.author === user.id;
const isAssignedReviewer = document.reviewer === user.id;
const isAssignedApprover = document.approver === user.id;
const hasWritePermission = user.permissions?.includes('write') || user.is_staff || isDocumentAuthor;
const hasReviewPermission = user.permissions?.includes('review') || user.is_staff || isAssignedReviewer;
const hasApprovalPermission = user.permissions?.includes('approve') || user.is_staff || isAssignedApprover;
```

### Permission Hierarchy

1. **Staff Users** (`user.is_staff = true`)
   - Automatically receive ALL permissions
   - Can perform any action on any document

2. **Document Authors**
   - Automatically receive write permission for their documents
   - Can submit for review, route for approval, create versions

3. **Assigned Reviewers** 
   - Automatically receive review permission for assigned documents
   - Can start and complete review processes

4. **Assigned Approvers**
   - Automatically receive approval permission for assigned documents
   - Can approve/reject and set effective dates

5. **Explicit Permissions**
   - Users can be granted explicit `write`, `review`, or `approve` permissions
   - These permissions apply across all documents (not document-specific)

### Global Requirements

All action buttons require:
- `document` exists (not null)
- `workflowStatus` exists (not null)
- `authenticated = true`
- `user` exists (not null)

## Document Status Flow

The action buttons follow the EDMS document lifecycle:

```
DRAFT → PENDING_REVIEW → UNDER_REVIEW → REVIEWED → PENDING_APPROVAL → APPROVED → EFFECTIVE
                                                                                    ↓
                                                                               (NEW VERSION)
                                                                                    ↓
                                                                               (OBSOLETE)
```

### Status-Based Button Availability

| Document Status | Available Actions |
|-----------------|------------------|
| `DRAFT` | Submit for Review |
| `PENDING_REVIEW` | Start Review Process, View Review Status |
| `UNDER_REVIEW` | Continue Review |
| `REVIEW_COMPLETED`/`REVIEWED` | Route for Approval |
| `PENDING_APPROVAL` | Start Approval Process |
| `APPROVED` | Set Effective Date |
| `EFFECTIVE` | Create New Version, Mark Obsolete |

## UI Implementation Details

### Button Styling

```javascript
className={`w-full px-4 py-3 text-sm font-medium rounded-md border focus:ring-2 focus:ring-offset-2 text-left ${
  action.color === 'blue' ? 'bg-blue-600 border-blue-600 text-white hover:bg-blue-700 focus:ring-blue-500' :
  action.color === 'green' ? 'bg-green-600 border-green-600 text-white hover:bg-green-700 focus:ring-green-500' :
  action.color === 'yellow' ? 'bg-yellow-600 border-yellow-600 text-white hover:bg-yellow-700 focus:ring-yellow-500' :
  action.color === 'red' ? 'bg-red-600 border-red-600 text-white hover:bg-red-700 focus:ring-red-500' :
  'bg-gray-600 border-gray-600 text-white hover:bg-gray-700 focus:ring-gray-500'
}`}
```

### Empty State

When no actions are available for the current user and document state:

```javascript
{getAvailableActions().length === 0 && (
  <div className="text-center py-6 text-gray-500">
    <svg className="w-8 h-8 mx-auto mb-2 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
    <p className="text-sm">No workflow actions available for your role at this time.</p>
  </div>
)}
```

## Workflow Integration

### Modal Components Triggered

1. **`SubmitForReviewModal`** - Triggered by "Submit for Review" button
   - Allows reviewer selection and comment addition
   - Handles reviewer assignment and workflow state transition

2. **`ReviewerInterface`** - Triggered by review-related buttons  
   - Provides document review functionality
   - Handles review completion and rejection

### Action Handler

```javascript
const handleWorkflowAction = (actionKey: string) => {
  switch (actionKey) {
    case 'submit_for_review':
      setShowSubmitForReviewModal(true);
      return;
    case 'open_reviewer_interface':
      setShowReviewerInterface(true);
      return;
    default:
      if (onWorkflowAction && document) {
        onWorkflowAction(document, actionKey);
      }
  }
};
```

## Security Considerations

1. **Frontend Permission Checks**
   - All button visibility is based on user permissions and document state
   - Provides immediate UI feedback to users

2. **Backend Validation Required**
   - Frontend permission checks are for UX only
   - Backend must validate all workflow actions independently
   - Never trust frontend permission calculations for security

3. **Document Dependencies**
   - "Mark Obsolete" action checks for document dependencies
   - Prevents obsolescence of documents that other documents depend on

## Testing Considerations

### Test Scenarios by Role

1. **Document Author Tests**
   - Can see "Submit for Review" on DRAFT documents they created
   - Can see "Route for Approval" on REVIEWED documents they created
   - Cannot see reviewer/approver specific buttons

2. **Assigned Reviewer Tests**
   - Can see "Start Review Process" on documents assigned to them
   - Cannot see buttons on documents not assigned to them
   - Can see "Continue Review" on in-progress reviews

3. **Assigned Approver Tests**
   - Can see approval buttons only on documents assigned to them
   - Can set effective dates after approval

4. **Staff User Tests**
   - Can see all buttons regardless of assignment
   - Acts as super-user for all workflow actions

### Edge Cases

1. **Unassigned Documents** - Documents without reviewer/approver assignments
2. **Multiple Role Users** - Users with multiple permission types
3. **Document Dependencies** - Testing obsolescence workflow constraints
4. **Permission Changes** - Users gaining/losing permissions during workflow

## Related Documentation

- **EDMS_details.txt** - Original workflow specifications
- **EDMS_details_workflow.txt** - Detailed workflow state definitions
- **DocumentViewer.tsx** - Implementation file
- **SubmitForReviewModal.tsx** - Review submission component
- **ReviewerInterface.tsx** - Review process component

## Change Log

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2024-11-26 | Initial documentation |

---

**Note**: This documentation reflects the current implementation as of the documentation date. For the most up-to-date implementation details, refer to the source code in `frontend/src/components/documents/DocumentViewer.tsx`.