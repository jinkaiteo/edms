# 🧪 Manual Testing - IN PROGRESS

## ✅ Completed Steps

### Step 1: Services Verified ✅
- All 6 services running
- Backend health: OK
- Frontend accessible
- Admin panel accessible

### Step 2: Test Users Created ✅
Three test users are ready:

**Author Account:**
- Username: `author01`
- Password: `Test123!`
- Role: Author (can create documents)

**Reviewer Account:**
- Username: `reviewer01`  
- Password: `Test123!`
- Role: Reviewer (can review documents)

**Approver Account:**
- Username: `approver01`
- Password: `Test123!`
- Role: Approver (can approve documents)

---

## 📝 Next: Test Document Workflow

### Step 3: Login as Author and Create Document

1. **Open Frontend:** http://localhost:3000

2. **Login as author01:**
   - Username: `author01`
   - Password: `Test123!`

3. **Create New Document:**
   - Click "Create Document" or "+" button
   - Fill in details:
     - **Title:** "Test SOP - Quality Control Procedure"
     - **Document Number:** (auto-generated or enter "SOP-001")
     - **Document Type:** SOP or Standard
     - **Description:** "Test document for workflow validation"
   - Click "Save" or "Create"
   - **Expected:** Document created in DRAFT status

4. **Submit for Review:**
   - Open the document you just created
   - Find "Submit for Review" button
   - Select **Reviewer:** reviewer01
   - Add comment: "Please review this test document"
   - Click "Submit"
   - **Expected:** Status changes to "Under Review" or "Submitted for Review"

**✅ Checkpoint:** Document is now with reviewer01

---

### Step 4: Login as Reviewer and Review Document

1. **Logout** from author01 account

2. **Login as reviewer01:**
   - Username: `reviewer01`
   - Password: `Test123!`

3. **Find Document to Review:**
   - Go to "My Tasks" or "Documents for Review"
   - You should see the test document
   - **Expected:** Document appears in reviewer's queue

4. **Review the Document:**
   - Open the document
   - Review the content
   - Find "Complete Review" or "Review" button
   - Select: **Approve Review** (not reject)
   - Add comment: "Document reviewed and approved"
   - Click "Complete Review"
   - **Expected:** Status changes to "Reviewed"

5. **Route for Approval:**
   - Find "Route for Approval" button
   - Select **Approver:** approver01
   - Add comment: "Routing to approver for final approval"
   - Click "Route"
   - **Expected:** Document sent to approver

**✅ Checkpoint:** Document is now with approver01

---

### Step 5: Login as Approver and Approve Document

1. **Logout** from reviewer01 account

2. **Login as approver01:**
   - Username: `approver01`
   - Password: `Test123!`

3. **Find Document to Approve:**
   - Go to "My Tasks" or "Documents for Approval"
   - You should see the test document
   - **Expected:** Document appears in approver's queue

4. **Approve the Document:**
   - Open the document
   - Find "Approve" button
   - Set **Effective Date:** Tomorrow's date
   - Add comment: "Document approved for implementation"
   - Click "Approve"
   - **Expected:** Status changes to "Approved - Pending Effective" or similar

**✅ Checkpoint:** Document approved, waiting for effective date

---

### Step 6: Verify Audit Trail

1. **While logged in as any user, open the document**

2. **Find "History" or "Audit Trail" section**

3. **Verify you can see:**
   - ✅ Document created by author01
   - ✅ Submitted for review with comment
   - ✅ Reviewed by reviewer01 with comment
   - ✅ Routed for approval
   - ✅ Approved by approver01 with comment
   - ✅ All timestamps recorded
   - ✅ All user actions logged

**Expected:** Complete history of all workflow actions

---

### Step 7: Check Background Tasks

Open terminal and run:

```bash
# Check Celery worker
docker compose logs celery_worker --tail 50

# Check Celery beat
docker compose logs celery_beat --tail 50

# Expected output:
# - Worker: "celery@hostname ready"
# - Beat: "Scheduler: Sending due task"
# - No ERROR messages
```

---

### Step 8: Check Backend Logs

```bash
# Check for errors
docker compose logs backend --tail 100 | grep -i error

# If no output or only non-critical errors, all good!
```

---

## ✅ Success Criteria

All of these should be TRUE:

- [ ] Can login as all 3 users (author, reviewer, approver)
- [ ] Can create document as author
- [ ] Can submit document for review
- [ ] Document appears in reviewer's tasks
- [ ] Can complete review as reviewer
- [ ] Can route to approver
- [ ] Document appears in approver's tasks
- [ ] Can approve document with effective date
- [ ] Audit trail shows all actions
- [ ] No critical errors in logs
- [ ] Celery worker/beat running

---

## 🎉 When All Tests Pass

You're ready for **STAGING DEPLOYMENT**!

Run:
```bash
./deploy-staging-complete.sh
```

---

## 🚨 If Something Doesn't Work

**Check logs:**
```bash
docker compose logs backend -f
```

**Restart services:**
```bash
docker compose restart backend frontend
```

**Ask for help:** Let me know what step failed and what error you see
