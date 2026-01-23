# Periodic Review Outcomes - Detailed Explanation

**Date:** January 22, 2026  
**Purpose:** Explain what happens when reviewer selects each outcome option

---

## 🎯 **Three Possible Outcomes**

When a stakeholder completes a periodic review, they choose one of three outcomes:

```
1. ✅ Still Valid - No changes needed
2. ⚠️  Minor Updates Needed - Small corrections required
3. 🔄 Major Updates Needed - Significant revision required
```

Let's explore each in detail...

---

## ✅ **Outcome 1: "Still Valid - No Changes Needed"**

### **Use Case:**
- Document content is still accurate
- No regulatory changes
- No process changes
- Document can continue as-is

### **What Happens:**

```
Step 1: Reviewer submits review
┌────────────────────────────────────┐
│ Review Outcome:                    │
│ ⦿ Still valid - No changes needed │  ← Selected
│ ○ Minor updates needed             │
│ ○ Major updates needed             │
│                                    │
│ Comments: [Document reviewed and   │
│            remains current]        │
│                                    │
│ Next Review Date: [2028-01-22]    │
│                                    │
│ [Submit Review]                    │
└────────────────────────────────────┘

Step 2: System processes immediately
├─ Document status: UNDER_PERIODIC_REVIEW → EFFECTIVE
├─ last_review_date: Updated to today (2027-01-22)
├─ next_review_date: Updated to 2028-01-22
├─ Workflow: Terminated (is_terminated=True)
└─ DocumentReview record: Created

Step 3: Notifications sent
├─ Author: "Your document was reviewed and approved"
├─ Approver: "Document remains effective"
└─ Admin: "Periodic review completed successfully"

Result: ✅ DONE - Document continues as EFFECTIVE
```

### **Timeline:**
```
2027-01-22: Review submitted → Document immediately EFFECTIVE
2028-01-22: Next automatic review scheduled
```

**Code Flow:**
```python
def handle_still_valid_outcome(document, reviewer, comments, next_review_date):
    # 1. Create review record
    DocumentReview.objects.create(
        document=document,
        reviewer=reviewer,
        outcome='STILL_VALID',
        comments=comments,
        next_review_date=next_review_date
    )
    
    # 2. Update document
    document.status = 'EFFECTIVE'
    document.last_review_date = timezone.now().date()
    document.next_review_date = next_review_date
    document.save()
    
    # 3. Terminate workflow
    workflow.is_terminated = True
    workflow.completed_at = timezone.now()
    workflow.save()
    
    # 4. Notify stakeholders
    notify_stakeholders(document, 'REVIEW_APPROVED')
    
    # 5. Audit trail
    AuditTrail.objects.create(
        action='PERIODIC_REVIEW_COMPLETED',
        details={'outcome': 'STILL_VALID'}
    )
```

---

## ⚠️ **Outcome 2: "Minor Updates Needed"**

### **Use Case:**
- Typos or grammar corrections
- Updated contact information
- Minor clarifications
- Small procedural adjustments
- Same version can be corrected

### **What Happens:**

```
Step 1: Reviewer submits review
┌────────────────────────────────────┐
│ Review Outcome:                    │
│ ○ Still valid - No changes needed │
│ ⦿ Minor updates needed             │  ← Selected
│ ○ Major updates needed             │
│                                    │
│ Comments: [Please correct the      │
│            email address on page 3 │
│            and fix typo in step 5] │
│                                    │
│ [Submit Review]                    │
└────────────────────────────────────┘

Step 2: System processes
├─ Document status: UNDER_PERIODIC_REVIEW → DRAFT
├─ Workflow: Terminated (review complete)
├─ DocumentReview record: Created with comments
└─ Document returned to author for edits

Step 3: Notifications sent to AUTHOR
┌────────────────────────────────────────────────┐
│ 📧 Periodic Review - Minor Updates Required   │
├────────────────────────────────────────────────┤
│ Your document SOP-2026-0001 v1.0 has been     │
│ reviewed and requires minor corrections.       │
│                                                │
│ Reviewer Comments:                             │
│ "Please correct the email address on page 3   │
│  and fix typo in step 5"                      │
│                                                │
│ What to do:                                    │
│ 1. Edit the document                           │
│ 2. Make the requested corrections             │
│ 3. Re-submit for approval                     │
│                                                │
│ [Edit Document]                                │
└────────────────────────────────────────────────┘

Step 4: Author makes corrections
├─ Opens document in edit mode
├─ Makes the corrections
├─ Document remains as v1.0 (same version)
└─ Submits for approval

Step 5: Normal approval workflow
┌─────────────────────────────────────────┐
│ Regular Document Approval Workflow      │
├─────────────────────────────────────────┤
│ DRAFT → PENDING_REVIEW → UNDER_REVIEW  │
│       → REVIEWED → PENDING_APPROVAL     │
│       → APPROVED_PENDING_EFFECTIVE      │
│       → EFFECTIVE                       │
└─────────────────────────────────────────┘

Step 6: Document becomes EFFECTIVE again
├─ Same version: v1.0 (just corrected)
├─ New effective_date: 2027-02-01
├─ New review_date: 2028-02-01
└─ Cycle continues
```

### **Timeline:**
```
2027-01-22: Review submitted → Document status: DRAFT
2027-01-23: Author makes corrections
2027-01-24: Submits for approval
2027-01-25: Reviewer approves (fast-track)
2027-01-26: Approver approves → EFFECTIVE
2028-01-26: Next periodic review
```

### **Important Notes:**

✅ **Same Version Number**
- Document remains v1.0
- No version increment needed
- Just corrections to existing content

✅ **Full Approval Workflow Required**
- Even though minor changes, still needs review/approval
- Ensures corrections are verified
- Maintains audit trail

✅ **Author Responsible**
- Author must make the changes
- Can't delegate to someone else
- If author unavailable, admin can reassign document

**Code Flow:**
```python
def handle_minor_updates_outcome(document, reviewer, comments):
    # 1. Create review record
    DocumentReview.objects.create(
        document=document,
        reviewer=reviewer,
        outcome='NEEDS_MINOR_UPDATES',
        comments=comments
    )
    
    # 2. Return document to DRAFT
    document.status = 'DRAFT'
    document.save()
    
    # 3. Terminate review workflow
    workflow.is_terminated = True
    workflow.save()
    
    # 4. Notify AUTHOR
    WorkflowNotification.objects.create(
        recipient=document.author,
        subject=f'Minor Updates Required: {document.document_number}',
        message=f'Reviewer has requested minor corrections.\n\nComments: {comments}',
        metadata={
            'action_required': 'EDIT_DOCUMENT',
            'reviewer_comments': comments
        }
    )
    
    # 5. Audit trail
    AuditTrail.objects.create(
        action='PERIODIC_REVIEW_MINOR_UPDATES_REQUESTED',
        details={
            'reviewer': reviewer.username,
            'comments': comments
        }
    )
```

---

## 🔄 **Outcome 3: "Major Updates Needed"**

### **Use Case:**
- Significant content changes
- New regulatory requirements
- Process completely changed
- Major sections need rewriting
- Better to create NEW VERSION

### **What Happens:**

```
Step 1: Reviewer submits review
┌────────────────────────────────────────────────┐
│ Review Outcome:                                │
│ ○ Still valid - No changes needed             │
│ ○ Minor updates needed                         │
│ ⦿ Major updates needed                         │  ← Selected
│                                                │
│ Comments: [New FDA regulation 21 CFR 820.30   │
│            requires additional validation      │
│            steps. Sections 3, 5, and 7 need   │
│            substantial revision. Recommend     │
│            creating v2.0]                      │
│                                                │
│ [Submit Review]                                │
└────────────────────────────────────────────────┘

Step 2: System processes
├─ Document status: UNDER_PERIODIC_REVIEW → EFFECTIVE ✅
├─ Current version (v1.0) REMAINS EFFECTIVE
├─ Workflow: Terminated (review complete)
├─ DocumentReview record: Created with recommendations
└─ Document stays active until replaced

Step 3: Notifications sent
├─ To AUTHOR:
│   ┌────────────────────────────────────────────┐
│   │ 📧 Major Updates Recommended               │
│   ├────────────────────────────────────────────┤
│   │ Your document SOP-2026-0001 v1.0 requires │
│   │ significant updates.                       │
│   │                                            │
│   │ Reviewer Recommendations:                  │
│   │ "New FDA regulation requires additional    │
│   │  validation steps..."                      │
│   │                                            │
│   │ Action Required:                           │
│   │ Please create a NEW VERSION (v2.0) with   │
│   │ the necessary updates.                     │
│   │                                            │
│   │ Current version v1.0 will remain EFFECTIVE│
│   │ until v2.0 is approved.                   │
│   │                                            │
│   │ [Create New Version]                       │
│   └────────────────────────────────────────────┘
│
└─ To ADMIN:
    "Major review completed - new version recommended"

Step 4: Current version stays active
├─ v1.0 status: EFFECTIVE (not changed)
├─ v1.0 continues to be used in operations
├─ Users can still reference v1.0
├─ v1.0 appears in Document Library
└─ No disruption to operations

Step 5: Author creates NEW version v2.0
┌─────────────────────────────────────────────┐
│ Author clicks "Create New Version"          │
├─────────────────────────────────────────────┤
│ System creates:                             │
│ - New document: SOP-2026-0001 v2.0          │
│ - Status: DRAFT                             │
│ - Supersedes: v1.0                          │
│ - Content: Copied from v1.0                 │
└─────────────────────────────────────────────┘

Step 6: Author works on v2.0
├─ v1.0 remains EFFECTIVE (people still use it)
├─ v2.0 is DRAFT (author makes major changes)
├─ No rush - can take days or weeks
└─ Operations continue with v1.0

Step 7: v2.0 goes through normal workflow
┌─────────────────────────────────────────────┐
│ v2.0 Workflow:                              │
│ DRAFT → PENDING_REVIEW → UNDER_REVIEW      │
│       → REVIEWED → PENDING_APPROVAL         │
│       → APPROVED_PENDING_EFFECTIVE          │
└─────────────────────────────────────────────┘

Step 8: v2.0 becomes EFFECTIVE
├─ v2.0 status: EFFECTIVE ✅
├─ v1.0 status: SUPERSEDED (automatically)
└─ v1.0 moves to version history

Step 9: Final state
├─ Document Library shows: v2.0 (EFFECTIVE)
├─ Version History shows: v1.0 (SUPERSEDED)
└─ Next review for v2.0: 2028-03-15 (12 months)
```

### **Timeline:**
```
2027-01-22: Review submitted → v1.0 remains EFFECTIVE
2027-01-23: Author starts v2.0 (DRAFT)
2027-02-15: Author completes v2.0 → Submit for review
2027-02-20: v2.0 reviewed
2027-02-22: v2.0 approved
2027-03-01: v2.0 EFFECTIVE, v1.0 SUPERSEDED
2028-03-01: Next review for v2.0
```

### **Important Notes:**

✅ **No Disruption**
- v1.0 stays EFFECTIVE until v2.0 ready
- Operations continue normally
- No gap in coverage

✅ **Clean Version History**
- v2.0 is a true new version
- Supersession relationship maintained
- Audit trail preserved

✅ **Author Control**
- Author decides timeline for v2.0
- Can coordinate with operations
- Can phase in new version

**Code Flow:**
```python
def handle_major_updates_outcome(document, reviewer, comments, next_review_date):
    # 1. Create review record
    DocumentReview.objects.create(
        document=document,
        reviewer=reviewer,
        outcome='NEEDS_MAJOR_UPDATES',
        comments=comments,
        next_review_date=next_review_date
    )
    
    # 2. Document REMAINS EFFECTIVE
    document.status = 'EFFECTIVE'  # ← Key difference!
    document.last_review_date = timezone.now().date()
    document.next_review_date = next_review_date  # Still set next review
    document.save()
    
    # 3. Terminate workflow
    workflow.is_terminated = True
    workflow.save()
    
    # 4. Notify AUTHOR with recommendation
    WorkflowNotification.objects.create(
        recipient=document.author,
        subject=f'Major Updates Recommended: {document.document_number}',
        message=f'''
            Your document requires significant updates.
            
            Reviewer Recommendations:
            {comments}
            
            Action Required:
            Please create a NEW VERSION to incorporate these changes.
            Current version will remain effective until the new version is approved.
        ''',
        metadata={
            'action_recommended': 'CREATE_NEW_VERSION',
            'current_version_status': 'REMAINS_EFFECTIVE',
            'reviewer_comments': comments
        }
    )
    
    # 5. Notify ADMIN (oversight)
    notify_admins(document, 'MAJOR_UPDATES_RECOMMENDED')
    
    # 6. Audit trail
    AuditTrail.objects.create(
        action='PERIODIC_REVIEW_MAJOR_UPDATES_RECOMMENDED',
        details={
            'reviewer': reviewer.username,
            'comments': comments,
            'current_version_remains_effective': True
        }
    )
```

---

## 📊 **Comparison Matrix**

| Aspect | Still Valid | Minor Updates | Major Updates |
|--------|-------------|---------------|---------------|
| **Document Status** | EFFECTIVE | DRAFT | EFFECTIVE |
| **Version Number** | v1.0 (same) | v1.0 (same) | v1.0 → v2.0 |
| **Immediate Action** | None | Author edits | Author creates v2.0 |
| **Workflow Needed** | No | Yes (re-approve) | Yes (new version) |
| **Disruption** | None | Brief (few days) | None |
| **Timeline** | Instant | 1-2 weeks | 2-4 weeks |
| **Use Case** | Content OK | Small fixes | Major changes |

---

## 🎯 **Decision Guide for Reviewers**

### **Choose "Still Valid" if:**
- ✅ Content is accurate and current
- ✅ No changes to regulations or processes
- ✅ Document can continue as-is
- ✅ Just confirming it's still good

### **Choose "Minor Updates" if:**
- ⚠️ Typos or grammar issues
- ⚠️ Contact information changed
- ⚠️ Small clarifications needed
- ⚠️ Can fix without changing version

### **Choose "Major Updates" if:**
- 🔄 Regulatory requirements changed
- 🔄 Process significantly changed
- 🔄 Multiple sections need rewriting
- 🔄 Better to create new version

---

## 📋 **What Author Sees After Each Outcome**

### **After "Still Valid":**
```
┌────────────────────────────────────────┐
│ ✅ Periodic Review Completed           │
├────────────────────────────────────────┤
│ Your document SOP-2026-0001 v1.0 has  │
│ been reviewed and approved.            │
│                                        │
│ Status: EFFECTIVE                      │
│ Next Review: Jan 22, 2028              │
│                                        │
│ No action required.                    │
└────────────────────────────────────────┘
```

### **After "Minor Updates":**
```
┌────────────────────────────────────────┐
│ ⚠️ Corrections Required                │
├────────────────────────────────────────┤
│ Your document SOP-2026-0001 v1.0      │
│ requires minor corrections.            │
│                                        │
│ Status: DRAFT                          │
│                                        │
│ Reviewer Comments:                     │
│ "Please correct email on page 3..."   │
│                                        │
│ [Edit Document] ← Action button       │
└────────────────────────────────────────┘
```

### **After "Major Updates":**
```
┌────────────────────────────────────────┐
│ 🔄 New Version Recommended             │
├────────────────────────────────────────┤
│ Your document SOP-2026-0001 v1.0      │
│ requires significant updates.          │
│                                        │
│ Current Status: EFFECTIVE              │
│ (continues until v2.0 is ready)        │
│                                        │
│ Reviewer Recommendations:              │
│ "New FDA regulation requires..."       │
│                                        │
│ [Create New Version] ← Action button  │
└────────────────────────────────────────┘
```

---

## ✅ **Summary**

### **Key Differences:**

**Minor Updates:**
- Same version, quick fix
- Returns to DRAFT
- Must re-approve
- Fast turnaround (days)

**Major Updates:**
- New version needed
- Current version stays active
- No disruption
- Longer timeline (weeks)

**Philosophy:**
- Minor = "Fix this version"
- Major = "Create next version"

---

**Any questions about the three outcomes?** 🎯
