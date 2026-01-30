# Manual QA Testing Checklist

**Purpose:** Systematic manual testing of all EDMS features  
**Date:** 2026-01-30  
**Tester:** ___________________  

---

## 🎯 Test Session Information

**Environment:** ☐ Local  ☐ Staging  ☐ Production  
**Browser:** ___________________  
**OS:** ___________________  
**Git Commit:** ___________________  

---

## ✅ Pre-Test Setup

- [ ] Database has test data
- [ ] Test users created (author, reviewer, approver, admin)
- [ ] Sample documents available
- [ ] Services running (backend, frontend, database)
- [ ] Browser cache cleared

---

## 1️⃣ Authentication & User Management

### Login/Logout
- [ ] Can login with valid credentials
- [ ] Cannot login with invalid credentials
- [ ] Error message shows for wrong password
- [ ] Can logout successfully
- [ ] Logged out redirects to login page

### User Creation
- [ ] Can create new user with all fields
- [ ] Email validation works
- [ ] Username uniqueness enforced
- [ ] Password requirements enforced
- [ ] User appears in user list

### ⭐ NEW: Superuser Management
- [ ] **Superuser badge** shows in user list for superusers
- [ ] Can click "Manage Roles" on any user
- [ ] **Superuser Status section** appears at TOP of modal
- [ ] Shows "⭐ Superuser" or "Regular User" correctly
- [ ] Purple gradient background visible
- [ ] **Grant Superuser button** (purple) appears for regular users
- [ ] **Revoke Superuser button** (red) appears for superusers
- [ ] Clicking "Grant Superuser" prompts for reason
- [ ] After granting, status updates to "⭐ Superuser"
- [ ] **Cannot revoke last superuser** (error message appears)
- [ ] Can revoke when 2+ superusers exist
- [ ] Regular users don't see grant/revoke buttons (if not admin)

**Notes:**
```


```

---

## 2️⃣ Document Management

### Document Creation
- [ ] Can create new document
- [ ] All document types available
- [ ] Required fields enforced
- [ ] Document appears in list
- [ ] Document number generated correctly

### File Upload
- [ ] Can upload DOCX file
- [ ] Can upload PDF file
- [ ] Large files upload (>10MB)
- [ ] Invalid file types rejected
- [ ] Upload progress shows
- [ ] File appears in document

### Document Viewing
- [ ] Document details display correctly
- [ ] File information shows
- [ ] Metadata accurate
- [ ] Dependencies section visible
- [ ] ⭐ **NEW: View PDF button** appears for EFFECTIVE documents
- [ ] ⭐ **NEW: View PDF button** does NOT appear for DRAFT documents

### ⭐ NEW: PDF Viewer
- [ ] **"📄 View PDF" button** visible (blue/indigo, next to Download)
- [ ] Button disabled while loading
- [ ] Loading spinner appears when clicked
- [ ] **Fullscreen PDF viewer** opens
- [ ] **Header shows**:
  - [ ] Document title
  - [ ] Document number
  - [ ] Download button
  - [ ] Close button (X)
- [ ] **PDF displays correctly** in iframe
- [ ] Can **zoom in/out** (native browser controls)
- [ ] Can **navigate pages** (native browser controls)
- [ ] **Download button** in header works
- [ ] **Close button** exits viewer and cleans up
- [ ] **Error handling**: Shows message if PDF fails to load
- [ ] Works on different screen sizes

**Notes:**
```


```

---

## 3️⃣ Document Dependencies

### Adding Dependencies
- [ ] Can add dependency
- [ ] Dependency validation works
- [ ] Cannot add circular dependencies
- [ ] Dependencies appear in list
- [ ] Can mark dependencies as critical

### ⭐ NEW: Dependency Visualization
- [ ] **"Dependencies" tab** shows in document viewer
- [ ] **"View Graph" button** visible
- [ ] **"View Tree" button** visible
- [ ] Can toggle between graph and tree views

### Graph View
- [ ] **Graph renders** with nodes and edges
- [ ] **Current document** highlighted (blue)
- [ ] **Dependencies** on LEFT side
- [ ] **Dependents** on RIGHT side
- [ ] **Arrows point correctly**:
  - [ ] Dependencies: arrows point FROM dependency TO current doc
  - [ ] Dependents: arrows point FROM current doc TO dependent
- [ ] Can **drag nodes** to rearrange
- [ ] Can **zoom** in/out
- [ ] Can **pan** the graph
- [ ] Nodes show document numbers
- [ ] Click node navigates to document (if implemented)

### Tree View
- [ ] **Tree structure** displays correctly
- [ ] **Dependencies** section shows
- [ ] **Dependents** section shows
- [ ] Hierarchy clear (parent-child)
- [ ] Can expand/collapse sections

**Notes:**
```


```

---

## 4️⃣ Document Workflows

### Submit for Review
- [ ] Can submit document for review
- [ ] Status changes to "UNDER_REVIEW"
- [ ] Reviewer assigned
- [ ] Notification sent (if enabled)
- [ ] Action buttons update

### Review Document
- [ ] Reviewer can see document
- [ ] Can approve review
- [ ] Can reject review
- [ ] Comments captured
- [ ] Status updates correctly

### Approve Document
- [ ] Approver can see document
- [ ] Can approve document
- [ ] Can reject document
- [ ] Effective date can be set
- [ ] Status updates to approved

### ⭐ NEW: Create New Version (Upversion)
- [ ] "Create New Version" button visible
- [ ] Modal opens with form
- [ ] Can enter reason for change
- [ ] Can select reviewer/approver
- [ ] New version created successfully
- [ ] **Dependencies auto-copied** from original version
- [ ] Go to new version and verify dependencies present
- [ ] **Dependencies resolved to latest EFFECTIVE** versions
- [ ] Dependency description shows "Auto-copied from v1.0"

**Notes:**
```


```

---

## 5️⃣ UI/UX Features

### ⭐ NEW: Modal Responsiveness
- [ ] All modals fit on screen (no overflow)
- [ ] Can scroll within modal if content is long
- [ ] Modals work on small screens (1366x768)
- [ ] Modals work on large screens (1920x1080)
- [ ] Test these modals specifically:
  - [ ] Create New Version modal
  - [ ] User Management modals
  - [ ] Role Management modal
  - [ ] Document creation modal

### ⭐ NEW: Header Z-Index
- [ ] When modal opens, **header is dimmed**
- [ ] Modal overlay covers entire screen
- [ ] **Dropdown menus** (profile, notifications) still work
- [ ] After closing modal, header returns to normal
- [ ] Test with:
  - [ ] PDF viewer
  - [ ] User management modal
  - [ ] Create new version modal

**Notes:**
```


```

---

## 6️⃣ System Administration

### Backup & Restore
- [ ] Can create backup
- [ ] Backup file created in backups/ folder
- [ ] Backup has reasonable size
- [ ] ⭐ **NEW: Auto-detects correct docker-compose file**
- [ ] Backup script shows which compose file detected
- [ ] Can restore from backup
- [ ] Data intact after restore
- [ ] Files intact after restore

### Scheduler Tasks
- [ ] Scheduler tab shows tasks
- [ ] Can see task schedules
- [ ] Can manually trigger tasks
- [ ] Task execution logs visible
- [ ] Tasks run automatically

**Notes:**
```


```

---

## 7️⃣ Cross-Browser Testing

### Chrome
- [ ] All features work
- [ ] PDF viewer works
- [ ] No console errors
- [ ] UI renders correctly

### Firefox
- [ ] All features work
- [ ] PDF viewer works
- [ ] No console errors
- [ ] UI renders correctly

### Edge
- [ ] All features work
- [ ] PDF viewer works
- [ ] No console errors
- [ ] UI renders correctly

### Safari (if available)
- [ ] All features work
- [ ] PDF viewer works
- [ ] No console errors
- [ ] UI renders correctly

**Notes:**
```


```

---

## 8️⃣ Mobile/Tablet Testing

### Tablet (768x1024)
- [ ] Layout responsive
- [ ] All buttons accessible
- [ ] Modals fit on screen
- [ ] PDF viewer usable
- [ ] No horizontal scrolling

### Mobile (375x667)
- [ ] Layout responsive
- [ ] Navigation works
- [ ] Can use core features
- [ ] Text readable
- [ ] Buttons tappable

**Notes:**
```


```

---

## 🐛 Bugs Found

### Bug #1
**Severity:** ☐ Critical  ☐ High  ☐ Medium  ☐ Low  
**Description:**
```


```
**Steps to Reproduce:**
1. 
2. 
3. 

**Expected:**
**Actual:**

---

### Bug #2
**Severity:** ☐ Critical  ☐ High  ☐ Medium  ☐ Low  
**Description:**
```


```
**Steps to Reproduce:**
1. 
2. 
3. 

**Expected:**
**Actual:**

---

## ✅ Test Summary

**Total Tests:** _____ / _____  
**Passed:** _____  
**Failed:** _____  
**Blocked:** _____  

**Overall Status:** ☐ Pass  ☐ Pass with Minor Issues  ☐ Fail  

**Critical Issues:** _____  
**High Issues:** _____  
**Medium Issues:** _____  
**Low Issues:** _____  

---

## 📝 Additional Notes

```




```

---

## ✍️ Sign-Off

**Tester:** ___________________  
**Date:** ___________________  
**Time Spent:** ___________________  

**Recommendation:**
☐ Ready for Production  
☐ Ready with Known Issues  
☐ Not Ready - Fix Issues First  

---

*This checklist covers all major EDMS features including recently added PDF viewer, superuser management, dependency visualization, and UI improvements.*
