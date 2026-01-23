# Test Approval Process with Periodic Review Configuration

**Date**: January 22, 2026  
**Test Document**: TEST-2026-9998

---

## ✅ **Test Document Created**

A fresh test document has been created in **PENDING_APPROVAL** status specifically for testing the new periodic review configuration feature.

### **Document Details**

```
Document Number:  TEST-2026-9998
Title:           Test Approval with Periodic Review Configuration
Status:          PENDING_APPROVAL
UUID:            [generated]

Assigned Roles:
- Author:   author01
- Reviewer: reviewer01
- Approver: approver01 ← TEST AS THIS USER
```

---

## 🧪 **Testing Instructions**

### **Step 1: Login**

1. Open browser: **http://localhost:3000**
2. Login with:
   - Username: `approver01`
   - Password: `TestPass123!`

### **Step 2: Find Document**

1. Navigate to **Documents** section
2. Look for: **TEST-2026-9998**
3. Status should show: **PENDING_APPROVAL**
4. Click to open the document

### **Step 3: Start Approval**

1. Click button: **"✅ Start Approval Process"**
2. Approval modal should open

### **Step 4: NEW FEATURE - Check Periodic Review Section**

You should now see a **NEW blue section**:

```
🔄 Periodic Review Required
  [Toggle Switch: ON] ←─── NEW!
  
  Review Interval          ←─── NEW!
  [Dropdown: Annual (12 months)]
  
  Document will require periodic review for regulatory compliance.
  Next review due: January 22, 2027  ←─── NEW! (Auto-calculated)
```

---

## 📋 **Test Cases**

### **Test 1: Approve with Default Review (Annual)**

**Steps:**
1. Leave toggle **ON**
2. Keep interval at **Annual (12 months)**
3. Select effective date: **Today**
4. Enter comments: "Approved with annual review"
5. Click **"Approve"**

**Expected Result:**
- ✅ Document status → **EFFECTIVE**
- ✅ `review_period_months` = 12
- ✅ `next_review_date` = January 22, 2027
- ✅ Success message appears

**Verification:**
```bash
# Check in database
docker compose exec backend python manage.py shell << 'EOF'
from apps.documents.models import Document
doc = Document.objects.filter(document_number='TEST-2026-9998').first()
print(f"Status: {doc.status}")
print(f"Review period: {doc.review_period_months} months")
print(f"Next review: {doc.next_review_date}")
EOF
```

---

### **Test 2: Approve with 6 Month Review**

**Steps:**
1. Refresh page / create another test doc
2. Open approval modal
3. Toggle **ON**
4. Select interval: **Every 6 months**
5. Watch the "Next review due" date update
6. Effective date: **Today**
7. Comments: "High-risk document, 6-month review"
8. Click **"Approve"**

**Expected Result:**
- ✅ Document status → **EFFECTIVE**
- ✅ `review_period_months` = 6
- ✅ `next_review_date` = July 22, 2026
- ✅ Calculated date was accurate

---

### **Test 3: Approve with No Periodic Review**

**Steps:**
1. Open approval modal
2. Toggle **OFF**
3. Info message should appear:
   > "ℹ️ No periodic review will be scheduled. This is typically used for reference documents or documents with indefinite validity."
4. Effective date: **Today**
5. Comments: "Reference document, no review needed"
6. Click **"Approve"**

**Expected Result:**
- ✅ Document status → **EFFECTIVE**
- ✅ `review_period_months` = null
- ✅ `next_review_date` = null
- ✅ No review will be scheduled

---

### **Test 4: Toggle Interaction**

**Steps:**
1. Open approval modal
2. Toggle **ON** → Dropdown appears
3. Select **Biennial (24 months)**
4. Note calculated date
5. Toggle **OFF** → Dropdown hides, info message shows
6. Toggle **ON** again → Dropdown reappears
7. Verify previous selection (24 months) is restored

**Expected Result:**
- ✅ Toggle shows/hides dropdown
- ✅ Selection persists when toggling back ON
- ✅ Calculated date updates in real-time

---

### **Test 5: Future Effective Date**

**Steps:**
1. Open approval modal
2. Toggle **ON**, select **12 months**
3. Effective date: **February 1, 2026** (future)
4. Note calculated next review: **February 1, 2027**
5. Click **"Approve"**

**Expected Result:**
- ✅ Document status → **APPROVED_PENDING_EFFECTIVE**
- ✅ `effective_date` = 2026-02-01
- ✅ `next_review_date` = 2027-02-01 (from effective date, not today)

---

## 🔍 **What to Check**

### **Visual Elements**

- [ ] Blue bordered section appears
- [ ] Toggle switch works smoothly
- [ ] Toggle is ON by default
- [ ] Dropdown appears/disappears correctly
- [ ] Dropdown has 5 options (6, 12, 18, 24, 36 months)
- [ ] Default selection is 12 months (Annual)
- [ ] Calculated date displays and updates
- [ ] Help text is clear and readable

### **Functionality**

- [ ] Toggle affects dropdown visibility
- [ ] Selection persists when toggling
- [ ] Calculated date updates when interval changes
- [ ] Calculated date updates when effective date changes
- [ ] Approve button still works
- [ ] API call includes `review_period_months`
- [ ] Backend saves values correctly

### **Edge Cases**

- [ ] Toggle OFF → approve → values null
- [ ] Toggle ON → select 36 months → long-term review works
- [ ] Effective date in past → review calculated from effective date
- [ ] Effective date far future → review calculated correctly
- [ ] Cancel modal → reopen → defaults restored

---

## 🐛 **Report Issues**

If you find issues, please note:

1. **What did you do?**
   - Exact steps taken

2. **What did you expect?**
   - Expected behavior

3. **What happened?**
   - Actual behavior
   - Error messages
   - Console errors

4. **Screenshots**
   - UI appearance
   - Console logs
   - Network requests

---

## 🧹 **Cleanup**

After testing, delete the test document:

```bash
docker compose exec backend python manage.py shell << 'EOF'
from apps.documents.models import Document
doc = Document.objects.filter(document_number='TEST-2026-9998').first()
if doc:
    doc.delete()
    print("✅ Test document deleted")
EOF
```

---

## ✅ **Success Criteria**

The feature is successful if:

1. ✅ New section appears in approval modal
2. ✅ Toggle works correctly (ON/OFF)
3. ✅ Dropdown shows 5 interval options
4. ✅ Calculated next review date is accurate
5. ✅ Approval saves review_period_months correctly
6. ✅ Approval saves next_review_date correctly
7. ✅ Toggle OFF results in null values
8. ✅ UI is intuitive and clear
9. ✅ No console errors
10. ✅ No API errors

---

**Ready to test!** 🚀

**Login**: http://localhost:3000  
**Username**: approver01  
**Password**: TestPass123!  
**Document**: TEST-2026-9998
