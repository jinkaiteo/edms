# EDMS User Guide - Document Workflow Management

## 👋 Welcome to EDMS

This guide will help you understand how to use the Electronic Document Management System (EDMS) to create, review, approve, and manage documents in your organization.

---

## 📖 Table of Contents

1. [Getting Started](#getting-started)
2. [Understanding Your Role](#understanding-your-role)
3. [Document Statuses Explained](#document-statuses-explained)
4. [Common Tasks by Role](#common-tasks-by-role)
5. [Step-by-Step Workflows](#step-by-step-workflows)
6. [Dashboard Overview](#dashboard-overview)
7. [Notifications](#notifications)
8. [Best Practices](#best-practices)
9. [FAQs](#faqs)
10. [Getting Help](#getting-help)

---

## 🚀 Getting Started

### Logging In

1. Open your web browser
2. Navigate to the EDMS URL (provided by your administrator)
3. Enter your **username** and **password**
4. Click **"Login"**

### Your Dashboard

After logging in, you'll see:
- **My Tasks** - Documents requiring your action
- **My Documents** - Documents you've created
- **Document Library** - Approved and effective documents
- **Notifications** - Alerts about your tasks and documents

---

## 👥 Understanding Your Role

EDMS has four main user roles. You may have one or more of these roles:

### 🖊️ **Author**
**What you do**: Create and write documents

**Your responsibilities**:
- ✅ Create new documents
- ✅ Submit documents for review
- ✅ Revise documents when rejected
- ✅ Terminate draft documents if needed

**You can**: Create, edit (drafts only), submit, terminate

---

### 🔍 **Reviewer**
**What you do**: Review documents for technical accuracy and completeness

**Your responsibilities**:
- ✅ Review assigned documents
- ✅ Check for errors, completeness, and accuracy
- ✅ Approve or reject reviews with comments
- ✅ Complete reviews in a timely manner

**You can**: Review, approve/reject reviews, add comments

---

### ✅ **Approver**
**What you do**: Give final approval for documents to become effective

**Your responsibilities**:
- ✅ Approve documents for implementation
- ✅ Set effective dates
- ✅ Reject documents that need more work
- ✅ Schedule documents for obsolescence when needed

**You can**: Approve, reject, set effective dates, schedule obsolescence

---

### 🔧 **Document Administrator**
**What you do**: Manage the entire document system

**Your responsibilities**:
- ✅ All of the above
- ✅ Configure document types and workflows
- ✅ Manage user roles and permissions
- ✅ Override workflows when necessary
- ✅ Generate reports and metrics

**You can**: Everything!

---

## 📊 Document Statuses Explained

Documents go through different statuses as they move through the workflow. Here's what each status means:

### 📝 **DRAFT**
- **What it means**: Document is being written
- **Who can edit**: Author only
- **Who can see**: Author only
- **Next step**: Submit for review

### ⏳ **PENDING REVIEW**
- **What it means**: Waiting for a reviewer to be assigned or to start reviewing
- **Who can edit**: No one
- **Who can see**: Author, assigned reviewer
- **Next step**: Reviewer starts review

### 🔍 **UNDER REVIEW**
- **What it means**: Reviewer is actively reviewing the document
- **Who can edit**: No one
- **Who can see**: Author, reviewer
- **Next step**: Reviewer completes review (approve or reject)

### ✅ **REVIEW COMPLETED**
- **What it means**: Review passed, ready for approval routing
- **Who can edit**: No one
- **Who can see**: Author, reviewer, admin
- **Next step**: Route to approver

### ⏳ **PENDING APPROVAL**
- **What it means**: Waiting for approver to review and approve
- **Who can edit**: No one
- **Who can see**: Author, reviewer, approver
- **Next step**: Approver approves or rejects

### 🕐 **APPROVED PENDING EFFECTIVE**
- **What it means**: Approved but not yet effective (waiting for effective date)
- **Who can edit**: No one
- **Who can see**: Everyone
- **Next step**: Automatically becomes effective on scheduled date

### 🟢 **EFFECTIVE**
- **What it means**: Active and in use! This is the goal!
- **Who can edit**: No one (create new version instead)
- **Who can see**: Everyone
- **Next step**: Use it! Or eventually schedule for obsolescence

### 📅 **SCHEDULED FOR OBSOLESCENCE**
- **What it means**: Document will be retired on a specific date
- **Who can edit**: No one
- **Who can see**: Everyone
- **Next step**: Automatically becomes obsolete on scheduled date

### 🔴 **OBSOLETE**
- **What it means**: Document is no longer in use (retired)
- **Who can edit**: No one
- **Who can see**: Everyone (read-only, for reference)
- **Next step**: None (final state)

### 🔄 **SUPERSEDED**
- **What it means**: Replaced by a newer version
- **Who can edit**: No one
- **Who can see**: Everyone (historical reference)
- **Next step**: None (final state)

### 🚫 **TERMINATED**
- **What it means**: Document was canceled before becoming effective
- **Who can edit**: No one
- **Who can see**: Author (for audit purposes)
- **Next step**: None (final state)

---

## 📋 Common Tasks by Role

### For Authors

#### ✏️ **Creating a New Document**

1. Click **"Create Document"** button
2. Fill in the details:
   - **Title**: Clear, descriptive name
   - **Document Type**: SOP, Policy, Form, etc.
   - **Department**: Your department
   - **Description**: Brief summary
   - **Upload File**: Your document (PDF, DOCX, etc.)
3. Click **"Save as Draft"**
4. Your document is now in **DRAFT** status

#### 📤 **Submitting for Review**

1. Go to **"My Documents"**
2. Find your draft document
3. Click **"View"**
4. Click **"Submit for Review"**
5. Choose a **Reviewer** from the dropdown
6. Add a **Comment** (optional but recommended)
7. Set a **Due Date** (optional)
8. Click **"Submit"**
9. Document status changes to **PENDING REVIEW**
10. Reviewer receives notification

#### 🔄 **Revising a Rejected Document**

1. Check your **Notifications** for rejection notice
2. Go to **"My Documents"**
3. Find the document (status: DRAFT)
4. Read the **rejection comments**
5. Click **"Edit"**
6. Make necessary revisions
7. Upload new file version if needed
8. Save changes
9. Submit for review again

#### 🚫 **Terminating a Draft**

If you need to cancel a document:

1. Go to **"My Documents"**
2. Find the document (must be DRAFT, PENDING_REVIEW, or UNDER_REVIEW)
3. Click **"View"**
4. Click **"Terminate"**
5. Enter **Reason for Termination**
6. Click **"Confirm"**
7. Document status changes to **TERMINATED**

**Note**: You can only terminate documents that haven't been approved yet.

---

### For Reviewers

#### 🔍 **Starting a Review**

1. Check **"My Tasks"** dashboard
2. Find documents in **PENDING REVIEW**
3. Click **"View"** on the document
4. Click **"Start Review"**
5. Status changes to **UNDER REVIEW**
6. Download and review the document

#### ✅ **Approving a Review**

When the document is good:

1. Open the document under review
2. Click **"Complete Review"**
3. Select **"Approve"**
4. Add **Comments** explaining what you checked
5. Click **"Submit"**
6. Status changes to **REVIEW COMPLETED**
7. Document moves to approval routing

#### ❌ **Rejecting a Review**

When the document needs work:

1. Open the document under review
2. Click **"Complete Review"**
3. Select **"Reject"**
4. Add **Detailed Comments** explaining what needs to change
5. Click **"Submit"**
6. Document returns to **DRAFT** status
7. Author receives notification with your comments

**Pro Tip**: Be specific in your comments so the author knows exactly what to fix!

---

### For Approvers

#### ✅ **Approving a Document**

1. Check **"My Tasks"** dashboard
2. Find documents in **PENDING APPROVAL**
3. Click **"View"** on the document
4. Review the document carefully
5. Click **"Approve"**
6. Set the **Effective Date**:
   - **Today**: Document becomes effective immediately
   - **Future Date**: Document becomes effective on that date
7. Add **Approval Comments** (optional but recommended)
8. Click **"Confirm"**

**What happens next**:
- If effective date is today → Status: **EFFECTIVE**
- If effective date is future → Status: **APPROVED PENDING EFFECTIVE**
- On the effective date, the system automatically makes it **EFFECTIVE**

#### ❌ **Rejecting a Document**

If the document needs more work:

1. Open the document
2. Click **"Reject"**
3. Add **Detailed Comments** explaining what needs to change
4. Choose **Reason for Rejection**
5. Click **"Confirm"**
6. Document returns to **DRAFT** status
7. Author receives notification

**Note**: Rejected documents must go through the entire workflow again (review + approval).

#### 📅 **Scheduling Obsolescence**

When a document needs to be retired:

1. Go to **"Document Library"**
2. Find the **EFFECTIVE** document
3. Click **"View"**
4. Click **"Schedule Obsolescence"**
5. Set **Obsolescence Date**
6. Enter **Reason for Obsolescence**
7. Optionally specify **Replacement Document**
8. Click **"Confirm"**
9. Status changes to **SCHEDULED FOR OBSOLESCENCE**
10. On the scheduled date, system makes it **OBSOLETE**

---

## 🔄 Step-by-Step Workflows

### Workflow 1: Creating and Approving a New Document

**Full Process from Start to Finish**

#### **Step 1: Author Creates Document** (Day 1)
- Author logs in
- Clicks "Create Document"
- Fills in details and uploads file
- Saves as **DRAFT**
- Reviews and edits as needed

#### **Step 2: Author Submits for Review** (Day 3)
- Author clicks "Submit for Review"
- Selects reviewer: "John Smith"
- Adds comment: "Please review new SOP for accuracy"
- Sets due date: 5 days from now
- Submits
- Status: **PENDING REVIEW**
- John Smith receives notification

#### **Step 3: Reviewer Reviews Document** (Day 5)
- John logs in and sees notification
- Goes to "My Tasks"
- Opens the document
- Clicks "Start Review"
- Status: **UNDER REVIEW**
- Downloads and reviews the document
- Checks for accuracy and completeness

#### **Step 4: Reviewer Approves Review** (Day 6)
- John clicks "Complete Review"
- Selects "Approve"
- Adds comment: "Reviewed and verified. Ready for approval."
- Submits
- Status: **REVIEW COMPLETED**
- Admin receives notification to route for approval

#### **Step 5: Admin Routes for Approval** (Day 6)
- Admin logs in
- Opens the document
- Clicks "Route for Approval"
- Selects approver: "Jane Doe"
- Adds comment: "Please approve for implementation"
- Submits
- Status: **PENDING APPROVAL**
- Jane Doe receives notification

#### **Step 6: Approver Approves Document** (Day 8)
- Jane logs in and sees notification
- Goes to "My Tasks"
- Opens the document
- Reviews carefully
- Clicks "Approve"
- Sets effective date: "Start of next month" (2026-02-01)
- Adds comment: "Approved for implementation"
- Submits
- Status: **APPROVED PENDING EFFECTIVE**

#### **Step 7: System Activates Document** (2026-02-01)
- Automated scheduler runs at 9:00 AM
- Checks for documents with effective_date = today
- Finds this document
- Changes status to **EFFECTIVE**
- Sends notifications to all stakeholders
- Document is now active and in use! ✅

**Total Time**: ~1 week from creation to activation

---

### Workflow 2: Updating an Effective Document (Up-versioning)

**When you need to change an approved document**

#### **Step 1: Create New Version** (Author or Admin)
- Open the **EFFECTIVE** document (v1.0)
- Click "Create New Version"
- Choose version type:
  - **Major version** (2.0): Significant changes
  - **Minor version** (1.1): Small updates
- Enter "Reason for Change"
- Click "Create"
- New document created in **DRAFT** status (v2.0)
- Old version (v1.0) remains **EFFECTIVE**

#### **Step 2: Edit New Version**
- Edit the new draft version
- Make your changes
- Upload updated file
- Save

#### **Step 3: New Version Goes Through Workflow**
- Submit for review (same as Workflow 1)
- Review process
- Approval process
- Set effective date

#### **Step 4: New Version Becomes Effective**
- On effective date, v2.0 becomes **EFFECTIVE**
- Old version (v1.0) automatically changes to **SUPERSEDED**
- Users are notified of the change
- v2.0 is now the active document

**Important**: The old version is never deleted - it's kept for audit trail!

---

### Workflow 3: Review Rejection and Revision

**When reviewer finds issues**

#### **Review Process**
- Reviewer opens document
- Finds issues: "Section 3.2 is incomplete"
- Clicks "Complete Review"
- Selects "Reject"
- Adds comment: "Section 3.2 needs procedure steps. Please add steps 1-5."
- Submits

#### **What Happens**
- Document returns to **DRAFT** status
- Author receives notification
- Reviewer assignment is cleared

#### **Author Revises**
- Author logs in and sees notification
- Opens the document
- Reads reviewer's comments
- Clicks "Edit"
- Adds missing content to Section 3.2
- Uploads revised file
- Saves changes

#### **Resubmit**
- Author clicks "Submit for Review" again
- Can choose same or different reviewer
- Process starts over from review stage

**Pro Tip**: Address all reviewer comments thoroughly to avoid multiple rejection cycles!

---

## 🎛️ Dashboard Overview

### My Tasks

**What you'll see here**:
- 📝 **My Drafts**: Documents you're writing (DRAFT)
- 🔍 **Pending My Review**: Documents waiting for you to review
- 📋 **Under My Review**: Documents you're currently reviewing
- ✅ **Pending My Approval**: Documents waiting for your approval

**Quick Actions**:
- Click any document to open it
- See due dates highlighted in red if overdue
- Badge counters show number of tasks

### My Documents

**What you'll see here**:
- All documents you've created (any status)
- Filter by status
- Sort by date, title, or status
- Search by document number or title

### Document Library

**What you'll see here**:
- 🟢 **EFFECTIVE** - Active documents
- 🕐 **APPROVED PENDING EFFECTIVE** - Coming soon
- 📅 **SCHEDULED FOR OBSOLESCENCE** - Being retired
- All documents are searchable

**Features**:
- Advanced search and filters
- Download documents
- View document history
- See related documents

### Notifications

**Types of notifications**:
- 📬 **Assignments**: You've been assigned a task
- ⏰ **Reminders**: Task due date approaching
- ✅ **Completions**: Workflow completed
- ❌ **Rejections**: Document rejected
- 📅 **Status Changes**: Document status changed

**Actions**:
- Click to view document
- Mark as read
- Clear notifications

---

## 🔔 Notifications

### When You'll Receive Notifications

#### **As an Author**:
- ✅ Your document is submitted for review (confirmation)
- ✅ Review is completed (approved or rejected)
- ✅ Document is approved
- ✅ Document becomes effective
- ❌ Document is rejected

#### **As a Reviewer**:
- 📬 Document assigned to you for review
- ⏰ Review due date approaching
- ⏰ Review overdue

#### **As an Approver**:
- 📬 Document routed to you for approval
- ⏰ Approval due date approaching
- ⏰ Approval overdue

### Managing Notifications

1. **In-App Notifications**: Bell icon in header
2. **Email Notifications**: Sent to your registered email
3. **Mark as Read**: Click notification to mark as read
4. **Notification Settings**: Configure in your profile

---

## ✨ Best Practices

### For Authors

✅ **Do**:
- Write clear, concise titles
- Fill in all required fields
- Add meaningful descriptions
- Use standard templates when available
- Review your document before submitting
- Choose appropriate reviewers
- Add context in submission comments

❌ **Don't**:
- Leave fields blank unless optional
- Submit incomplete documents
- Skip the review process
- Ignore rejection comments
- Terminate documents without valid reason

### For Reviewers

✅ **Do**:
- Review promptly (before due date)
- Check for completeness and accuracy
- Be specific in your comments
- Suggest improvements
- Approve only when fully satisfied
- Document what you checked

❌ **Don't**:
- Let reviews sit overdue
- Approve without thorough review
- Give vague rejection comments
- Skip sections of the document
- Assume someone else will catch errors

### For Approvers

✅ **Do**:
- Verify all review comments addressed
- Set appropriate effective dates
- Consider implementation impact
- Add approval comments
- Notify stakeholders of major changes
- Understand regulatory implications

❌ **Don't**:
- Approve without careful review
- Set unrealistic effective dates
- Reject without clear explanation
- Skip checking review history
- Approve documents with known issues

### For Everyone

✅ **Do**:
- Check your dashboard daily
- Respond to notifications promptly
- Keep your profile information updated
- Ask questions if unclear
- Follow your organization's procedures
- Maintain document confidentiality

❌ **Don't**:
- Share login credentials
- Ignore overdue tasks
- Make changes outside the system
- Download sensitive documents to unsecure locations
- Bypass required workflow steps

---

## ❓ FAQs

### General Questions

**Q: Can I edit a document after submitting it for review?**  
A: No. Once submitted, the document is locked. If changes are needed, the reviewer must reject it to return it to DRAFT status.

**Q: How long does the approval process take?**  
A: It varies, but typically 1-2 weeks from submission to effectiveness, depending on complexity and due dates.

**Q: Can I see who approved/reviewed a document?**  
A: Yes! Click on the document and look at the "Workflow History" section to see all actions and who performed them.

**Q: What happens if I miss a due date?**  
A: You'll receive overdue notifications. The document won't progress until you complete your task. Your manager may also be notified.

**Q: Can I delete a document?**  
A: No. Documents cannot be deleted for audit trail purposes. You can TERMINATE a draft document, which removes it from active use but keeps it in the system.

---

### Author Questions

**Q: I submitted to the wrong reviewer. Can I change it?**  
A: You cannot change it yourself. Contact your admin or wait for the reviewer to reject it, then resubmit to the correct reviewer.

**Q: Can I create a document without uploading a file?**  
A: No, a document file is required. You must upload at least one file (PDF, DOCX, etc.).

**Q: What's the difference between major and minor versions?**  
A: Major versions (1.0 → 2.0) are for significant changes. Minor versions (1.0 → 1.1) are for small updates or corrections.

**Q: Can I have multiple reviewers?**  
A: Currently, only one reviewer at a time. For multiple reviews, you can resubmit after the first review completes.

---

### Reviewer Questions

**Q: What should I check when reviewing?**  
A: Check for:
- Completeness (all sections filled)
- Accuracy (correct information)
- Clarity (easy to understand)
- Compliance (follows regulations and policies)
- Formatting (consistent, professional)

**Q: Can I edit the document during review?**  
A: No, you cannot edit. You can only approve or reject with comments. If changes are needed, reject it with specific comments.

**Q: What if I don't have expertise in the document area?**  
A: Contact the author or admin to reassign to someone more appropriate.

**Q: How do I handle urgent reviews?**  
A: Check the due date. If it's urgent, prioritize it. If you can't meet the deadline, notify the author and admin immediately.

---

### Approver Questions

**Q: Should I review the document even after it's been reviewed?**  
A: Yes! Approval is the final check. Review it thoroughly, including checking that reviewer comments were addressed.

**Q: What if the effective date needs to change after approval?**  
A: Contact your admin. They can adjust the effective date before it becomes effective.

**Q: Can I unapprove a document?**  
A: No. If an approved document has issues, you can schedule it for obsolescence and create a corrected version.

**Q: What effective date should I choose?**  
A: Consider:
- Implementation readiness (are people trained?)
- Business impact (busy season?)
- Related documents (dependencies?)
- Common practice: Start of month or quarter

---

### Technical Questions

**Q: Which browsers are supported?**  
A: Modern versions of Chrome, Firefox, Edge, and Safari.

**Q: Can I access EDMS on my phone?**  
A: Yes! The interface is mobile-responsive, but a desktop/laptop is recommended for reviewing documents.

**Q: What file formats are supported?**  
A: PDF, DOCX, XLSX, PPTX, TXT, and common image formats.

**Q: Is my data secure?**  
A: Yes! EDMS is compliant with 21 CFR Part 11 and uses encryption, access controls, and audit trails.

**Q: Can I work offline?**  
A: No, EDMS requires an internet connection.

---

## 🆘 Getting Help

### Need Assistance?

#### **Technical Issues**
- **IT Helpdesk**: [Contact your IT support]
- **Email**: [Your support email]
- **Phone**: [Your support phone]

#### **Workflow Questions**
- **Document Administrator**: [Your admin's name/contact]
- **Training Materials**: Check the "Help" section in EDMS
- **User Manual**: This guide!

#### **System Access**
- **Forgot Password**: Click "Forgot Password" on login page
- **Account Locked**: Contact IT Helpdesk
- **Permission Issues**: Contact Document Administrator

### Training Resources

- **New User Training**: [Schedule/Link]
- **Video Tutorials**: [Link to videos]
- **Quick Reference Cards**: [Link to downloadable PDFs]
- **Live Support Hours**: [Your support hours]

---

## 📚 Quick Reference Card

### Document Status Quick Guide

| Status | Meaning | Your Action |
|--------|---------|-------------|
| DRAFT | Being written | Edit, Submit |
| PENDING REVIEW | Waiting for reviewer | Wait |
| UNDER REVIEW | Being reviewed | Wait |
| REVIEW COMPLETED | Review passed | Admin routes |
| PENDING APPROVAL | Waiting for approver | Wait |
| APPROVED PENDING EFFECTIVE | Waiting for date | Wait |
| EFFECTIVE | Active! | Use it! |

### Common Actions by Role

| Role | Common Actions |
|------|----------------|
| **Author** | Create, Submit, Revise, Terminate |
| **Reviewer** | Start Review, Complete Review (Approve/Reject) |
| **Approver** | Approve, Reject, Schedule Obsolescence |
| **Admin** | All actions, Route for Approval, Configure |

### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl/Cmd + N` | Create New Document |
| `Ctrl/Cmd + S` | Save Draft |
| `Ctrl/Cmd + F` | Search Documents |
| `Esc` | Close Modal |

---

## 🎉 Congratulations!

You now know how to use the EDMS system effectively. Remember:

- ✅ Check your dashboard daily
- ✅ Respond to notifications promptly
- ✅ Follow the workflow process
- ✅ Ask questions when unsure
- ✅ Keep documents moving through the system

**Happy Document Managing!** 📄✨

---

**Document Version**: 1.0  
**Last Updated**: January 2026  
**Feedback**: [Your feedback email/link]
