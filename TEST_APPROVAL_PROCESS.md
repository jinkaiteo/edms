# Testing Approval Process

**Date**: January 22, 2026  
**Test Document**: TEST-2026-9999

---

## 🎯 **Test Setup Complete**

A test document has been created and set to **PENDING_APPROVAL** status for testing the approval workflow.

### **Test Document Details**

```
Document Number:  TEST-2026-9999
Title:           Test Document for Approval Process
Status:          PENDING_APPROVAL
UUID:            969aa190-0b32-403f-8d58-2a09bc6b6aaa

Assigned Roles:
- Author:   author01
- Reviewer: reviewer01
- Approver: approver01 (← YOU WILL TEST AS THIS USER)
```

---

## 🧪 **Testing Steps**

### **Step 1: Login as Approver**

1. Open browser to: **http://localhost:3000**
2. Login with:
   - **Username**: `approver01`
   - **Password**: `TestPass123!`

### **Step 2: Find the Document**

1. Navigate to **Documents** section
2. Look for document **TEST-2026-9999**
3. Status should show **PENDING_APPROVAL**
4. Click on the document to open it

### **Step 3: Test Approval Interface**

1. You should see an action button: **"✅ Start Approval Process"**
2. Click the button
3. Verify the approval modal opens with:
   - Document details
   - Effective date selector
   - Comments field
   - Approve/Reject buttons

### **Step 4: Test Approval**

**Option A: Approve the Document**
1. Select an effective date (today or future)
2. Enter approval comments
3. Click **"Approve"** button
4. Verify:
   - Success message appears
   - Document status changes to EFFECTIVE (if today) or APPROVED_PENDING_EFFECTIVE (if future)
   - Document list refreshes

**Option B: Reject the Document**
1. Click **"Reject"** button
2. Enter rejection reason
3. Click **"Confirm Rejection"**
4. Verify:
   - Document returns to DRAFT
   - Reviewer and Approver assignments cleared
   - Author receives notification

---

## ✅ **What to Test**

### **Approval Modal Tests**

- [ ] Modal opens when clicking "Start Approval Process"
- [ ] Document information displays correctly
- [ ] Effective date picker works
- [ ] Comments field accepts input
- [ ] Approve button enabled when date selected
- [ ] Reject button works
- [ ] Modal closes properly

### **Approval Success Tests**

- [ ] Document transitions to correct status
- [ ] Effective date saved correctly
- [ ] Approval date recorded
- [ ] Success notification shows
- [ ] Document list refreshes
- [ ] No console errors

### **Rejection Tests**

- [ ] Rejection modal opens
- [ ] Reason field required
- [ ] Document returns to DRAFT
- [ ] Assignments cleared
- [ ] Success notification shows

### **Edge Cases**

- [ ] Past effective date (should be immediate EFFECTIVE)
- [ ] Future effective date (should be APPROVED_PENDING_EFFECTIVE)
- [ ] Today's date (should be EFFECTIVE)
- [ ] Empty comments (should be allowed or required?)
- [ ] Cancel button works
- [ ] Close (X) button works

---

## 🐛 **Known Issues**

### **Workflow State Issue**

During CLI testing, discovered:
- `REVIEWED` state doesn't exist in DocumentState table
- WorkflowTask import error (model may have been removed)
- Manual status change used as workaround

### **To Investigate**

1. Check if `REVIEWED` state needs to be added to DocumentState
2. Verify WorkflowTask model status
3. Confirm workflow transitions match available states

---

## 📊 **Expected Results**

### **After Approval (Effective Today)**

```
Status: EFFECTIVE
Effective Date: 2026-01-22
Approval Date: 2026-01-22 HH:MM:SS
Approved By: approver01
```

### **After Approval (Future Date)**

```
Status: APPROVED_PENDING_EFFECTIVE
Effective Date: [selected future date]
Approval Date: 2026-01-22 HH:MM:SS
Approved By: approver01

Note: Scheduler will activate on effective date
```

### **After Rejection**

```
Status: DRAFT
Reviewer: None (cleared)
Approver: None (cleared)
Author: author01 (unchanged)
```

---

## 🔍 **Things to Observe**

### **UI Elements**

- Action button appears for approver01 only
- Button label: "✅ Start Approval Process"
- Button color: Green
- Modal design and layout
- Form validation
- Error handling
- Success messages

### **Backend Behavior**

- API calls succeed
- Status transitions correctly
- Dates saved properly
- Workflow completed
- Notifications sent (check logs)

### **Browser Console**

- Check for JavaScript errors
- Verify API responses
- Monitor network requests
- Check state updates

---

## 📝 **Report Findings**

After testing, report:

1. **What worked?**
   - List successful features

2. **What didn't work?**
   - List bugs found
   - Include error messages
   - Note console errors

3. **UX Observations**
   - Is it intuitive?
   - Any confusing elements?
   - Suggestions for improvement

4. **Performance**
   - Response times
   - Loading states
   - Any lag or delays

---

## 🔧 **Cleanup**

After testing, delete the test document:

```bash
docker compose exec backend python manage.py shell << 'EOF'
from apps.documents.models import Document

doc = Document.objects.filter(document_number='TEST-2026-9999').first()
if doc:
    doc.delete()
    print("✅ Test document deleted")
EOF
```

---

## 🎯 **Success Criteria**

The approval process test is successful if:

✅ Approver can open approval interface  
✅ Effective date can be selected  
✅ Approval saves correctly  
✅ Document transitions to correct status  
✅ No console errors  
✅ UI is intuitive and clear  
✅ Success messages appear  
✅ Document list updates  

---

**Ready to test! Open your browser and login as approver01** 🚀
