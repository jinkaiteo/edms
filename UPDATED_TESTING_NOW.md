# 🧪 Manual Testing - UPDATED

## ✅ Service Status (4/4 Core Services)

**Running:**
- ✅ edms_db (PostgreSQL database)
- ✅ edms_redis (Redis cache)
- ✅ edms_backend (Django API)
- ✅ edms_frontend (React UI)

**Not Needed for This Test:**
- ℹ️ Celery Worker (background tasks - not in dev docker-compose)
- ℹ️ Celery Beat (scheduled tasks - not in dev docker-compose)

**Status:** ✅ **All services needed for workflow testing are running!**

---

## 📝 What You Can Test (WITHOUT Celery)

### ✅ Core Workflow (Everything User-Facing)
- User authentication
- Document creation
- Submit for review
- Review documents
- Approve documents
- Status transitions
- Audit trails
- Version history
- User permissions

### ℹ️ What Requires Celery (Test on Staging Later)
- Automatic effective date processing (midnight job)
- Workflow timeout notifications (hourly job)
- Cleanup tasks (6-hour job)

**Bottom Line:** You can complete the entire manual workflow test right now!

---

## 🚀 Start Testing - Step 3: Document Workflow

### Part A: Login as Author (5 min)

1. **Open:** http://localhost:3000

2. **Login:**
   - Username: `author01`
   - Password: `Test123!`

3. **Create Document:**
   - Look for "Create Document" or "New Document" button
   - Fill in:
     - **Title:** "Test SOP - Quality Control"
     - **Document Type:** SOP (or any available type)
     - **Description:** "Testing workflow"
   - Click "Create" or "Save"
   - ✅ **Expected:** Document created in DRAFT status

4. **Submit for Review:**
   - Open the document you created
   - Find "Submit for Review" button
   - Select **Reviewer:** reviewer01
   - Add comment: "Please review this test document"
   - Click "Submit"
   - ✅ **Expected:** Status changes to "Under Review" or "Submitted"

**Checkpoint:** Document is now with reviewer01

---

### Part B: Login as Reviewer (5 min)

1. **Logout** from author01

2. **Login as reviewer01:**
   - Username: `reviewer01`
   - Password: `Test123!`

3. **Find Document:**
   - Go to "My Tasks" or "Documents to Review"
   - ✅ **Expected:** You see the test document

4. **Complete Review:**
   - Open the document
   - Find "Review" or "Complete Review" button
   - Select: **Approve** (not reject)
   - Add comment: "Document reviewed and approved"
   - Click "Complete" or "Submit"
   - ✅ **Expected:** Status changes to "Reviewed"

5. **Route for Approval:**
   - Find "Route for Approval" button
   - Select **Approver:** approver01
   - Add comment: "Ready for approval"
   - Click "Route" or "Submit"
   - ✅ **Expected:** Document sent to approver

**Checkpoint:** Document is now with approver01

---

### Part C: Login as Approver (5 min)

1. **Logout** from reviewer01

2. **Login as approver01:**
   - Username: `approver01`
   - Password: `Test123!`

3. **Find Document:**
   - Go to "My Tasks" or "Documents to Approve"
   - ✅ **Expected:** You see the test document

4. **Approve Document:**
   - Open the document
   - Find "Approve" button
   - Set **Effective Date:** Tomorrow's date
   - Add comment: "Approved for implementation"
   - Click "Approve"
   - ✅ **Expected:** Status changes to "Approved - Pending Effective"

**Checkpoint:** Workflow complete! ✅

---

### Part D: Verify Audit Trail (3 min)

1. **Open the document** (as any user)

2. **Find "History" or "Audit Trail" tab/section**

3. **Verify you see:**
   - ✅ Document created by author01
   - ✅ Submitted for review
   - ✅ Reviewed by reviewer01  
   - ✅ Routed to approver
   - ✅ Approved by approver01
   - ✅ All timestamps
   - ✅ All comments

---

## ✅ Success Criteria

Check these boxes as you complete each:

- [ ] Logged in as author01
- [ ] Created test document
- [ ] Submitted for review
- [ ] Logged in as reviewer01
- [ ] Found document in tasks
- [ ] Completed review
- [ ] Routed for approval
- [ ] Logged in as approver01
- [ ] Found document in tasks
- [ ] Approved document
- [ ] Audit trail shows all actions
- [ ] No errors during workflow

---

## 🎉 When Complete

Tell me:
1. **"All steps passed"** → We deploy to staging!
2. **"Step X failed"** → I'll help you fix it

---

## 📝 Notes

- Effective date processing happens at midnight (Celery job)
- This will work on staging where Celery IS configured
- For now, just verify the workflow completes correctly
- Background automation will be tested on staging

---

**Ready? Start here:** http://localhost:3000

**Login:** author01 / Test123!
