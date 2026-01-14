---
title: "EDMS Quick Reference Guide"
subtitle: "Electronic Document Management System"
author: "EDMS Team"
date: "January 2026"
version: "1.0"
geometry: "margin=0.75in"
fontsize: "10pt"
papersize: "letter"
---

\newpage

# EDMS Quick Reference Guide

**Version 1.0 | January 2026**

---

## Document Workflow

### Standard Approval Flow

```
DRAFT
  ↓ (Author submits)
PENDING REVIEW
  ↓ (Reviewer starts)
UNDER REVIEW
  ↓ (Reviewer approves)
REVIEW COMPLETED
  ↓ (Admin routes)
PENDING APPROVAL
  ↓ (Approver approves)
APPROVED PENDING EFFECTIVE
  ↓ (Scheduler activates)
EFFECTIVE ✓
```

---

## User Roles & Permissions

| Role | Permissions |
|------|-------------|
| **Author** | Create, Edit drafts, Submit for review, Terminate drafts |
| **Reviewer** | Start review, Complete review (approve/reject), Add comments |
| **Approver** | Approve documents, Set effective dates, Reject, Schedule obsolescence |
| **Admin** | All permissions, Route for approval, Configure system |

---

## Document Statuses

| Status | Symbol | Meaning | Who Can Act |
|--------|--------|---------|-------------|
| DRAFT | 📝 | Being written | Author |
| PENDING REVIEW | ⏳ | Awaiting reviewer | Reviewer |
| UNDER REVIEW | 🔍 | Being reviewed | Reviewer |
| REVIEW COMPLETED | ✅ | Review passed | Admin |
| PENDING APPROVAL | ⏳ | Awaiting approver | Approver |
| APPROVED PENDING EFFECTIVE | 🕐 | Waiting for date | System |
| EFFECTIVE | 🟢 | Active & in use | Everyone (read) |
| SCHEDULED FOR OBSOLESCENCE | 📅 | Being retired | Everyone (read) |
| OBSOLETE | 🔴 | Retired | Everyone (archived) |
| SUPERSEDED | 🔄 | Replaced by new version | Everyone (history) |
| TERMINATED | 🚫 | Cancelled | Author (audit) |

---

## Common Tasks

### For Authors

**Create Document**
1. Click "Create Document"
2. Fill in required fields
3. Upload file
4. Click "Save as Draft"

**Submit for Review**
1. Open draft document
2. Click "Submit for Review"
3. Select reviewer
4. Add comment (optional)
5. Click "Submit"

**Revise Rejected Document**
1. Open document (status: DRAFT)
2. Read rejection comments
3. Click "Edit"
4. Make corrections
5. Save and resubmit

---

### For Reviewers

**Review Document**
1. Go to "My Tasks"
2. Open document
3. Click "Start Review"
4. Download and review
5. Click "Complete Review"
6. Select "Approve" or "Reject"
7. Add detailed comments
8. Click "Submit"

**What to Check**
- ☑ Completeness (all sections filled)
- ☑ Accuracy (correct information)
- ☑ Clarity (easy to understand)
- ☑ Compliance (follows policies)
- ☑ Formatting (consistent style)

---

### For Approvers

**Approve Document**
1. Go to "My Tasks"
2. Open document
3. Review thoroughly
4. Click "Approve"
5. Set effective date:
   - Today = immediate
   - Future = scheduled
6. Add approval comment
7. Click "Confirm"

**Reject Document**
1. Open document
2. Click "Reject"
3. Add detailed comments
4. Select reason
5. Click "Confirm"

---

## Navigation

### Dashboard Sections

**My Tasks**
- My Drafts (documents you're writing)
- Pending My Review (assigned to you)
- Under My Review (you're reviewing)
- Pending My Approval (awaiting your approval)

**My Documents**
- All documents you created
- Filter by status
- Search by title/number

**Document Library**
- All approved/effective documents
- Advanced search
- Download files

**Notifications**
- Task assignments
- Due date reminders
- Status changes
- Workflow completions

---

## Best Practices

### DO ✓

- Check dashboard daily
- Respond to notifications promptly
- Add meaningful comments
- Review documents thoroughly
- Meet due dates
- Ask questions when unsure
- Keep login credentials secure

### DON'T ✗

- Ignore overdue tasks
- Approve without reviewing
- Give vague rejection comments
- Skip required fields
- Share passwords
- Bypass workflow steps
- Delete or modify files outside system

---

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl/Cmd + N` | Create New Document |
| `Ctrl/Cmd + S` | Save Draft |
| `Ctrl/Cmd + F` | Search Documents |
| `Esc` | Close Modal/Dialog |

---

## Important Notes

### Editing Rules
- ✓ DRAFT status = Can edit
- ✗ All other statuses = Cannot edit
- Create new version to modify EFFECTIVE documents

### Effective Dates
- **Today**: Document becomes effective immediately
- **Future**: Status changes to APPROVED PENDING EFFECTIVE
- **Automatic**: System activates on scheduled date at 9 AM

### Rejection Impact
- Document returns to DRAFT
- Must go through workflow again
- All rejection comments visible to author

### Version Control
- Major version: 1.0 → 2.0 (significant changes)
- Minor version: 1.0 → 1.1 (small updates)
- Old version becomes SUPERSEDED when new version effective
- All versions retained for audit trail

---

## Getting Help

### Technical Support
**IT Helpdesk**
- Email: [your-support-email]
- Phone: [your-support-phone]
- Hours: [your-support-hours]

### Workflow Questions
**Document Administrator**
- Name: [admin-name]
- Email: [admin-email]
- Office: [admin-location]

### Training Resources
- User Guide: Full documentation available in system
- Video Tutorials: [training-link]
- Live Training: Schedule with admin

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Cannot log in | Use "Forgot Password" or contact IT |
| Document won't submit | Check all required fields completed |
| Can't find document | Use search or check filters |
| Notification not received | Check spam folder, verify email in profile |
| Due date passed | Complete task ASAP, notify admin |
| Wrong reviewer assigned | Contact admin to reassign |

---

## Compliance Reminders

### 21 CFR Part 11 Requirements

**Electronic Signatures**
- Your approval = electronic signature
- Cannot be denied or revoked
- Legally binding

**Audit Trail**
- All actions logged
- Cannot be deleted or modified
- Includes: who, what, when, where, why

**Access Control**
- Use only your own account
- Log out when done
- Report suspicious activity

**Data Integrity**
- Don't modify files outside system
- File checksums verify integrity
- Report any file corruption

---

## Quick Reference URLs

| Resource | URL |
|----------|-----|
| EDMS Login | [your-edms-url] |
| User Guide | [your-docs-url]/EDMS_USER_GUIDE.pdf |
| Training Videos | [your-training-url] |
| Support Portal | [your-support-url] |
| IT Helpdesk | [your-helpdesk-url] |

---

## Document Information

**Document Title**: EDMS Quick Reference Guide  
**Version**: 1.0  
**Effective Date**: January 2026  
**Review Date**: January 2027  
**Owner**: EDMS Team  
**Classification**: Internal Use  

---

**Keep this guide handy for quick reference!**

**For detailed instructions, see the complete EDMS User Guide.**

---

*This document is controlled and maintained by the EDMS Team. Print date: \today*
