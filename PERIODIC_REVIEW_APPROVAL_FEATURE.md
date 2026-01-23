# Periodic Review Configuration in Approval Process

**Date**: January 22, 2026  
**Status**: ✅ **Implemented**

---

## 🎯 **Feature Summary**

Added periodic review configuration to the document approval process, allowing approvers to set review intervals or mark documents as not requiring periodic review.

---

## 💡 **Business Need**

**Problem**: 
- No way to configure periodic review schedule during approval
- Documents approved without review dates
- Manual configuration needed after approval

**Solution**:
- Add review period configuration to approval modal
- Allow approvers to set review interval or disable reviews
- Automatically calculate next_review_date from effective_date

---

## ✅ **Implementation**

### **Frontend Changes** (`UnifiedWorkflowInterface.tsx`)

**1. New State Variables**:
```typescript
const [reviewPeriodMonths, setReviewPeriodMonths] = useState<number>(12);
const [requiresReview, setRequiresReview] = useState<boolean>(true);
```

**2. New UI Section** (appears when approving):
```
📅 Effective Date
  [date picker]

🔄 Periodic Review Required
  [toggle switch: ON/OFF]
  
  When ON:
    Review Interval
    [dropdown: 6/12/18/24/36 months]
    
    Next review due: [calculated date]
```

**3. Options**:
- **6 months** - Quarterly/Semi-annual
- **12 months** - Annual (default)
- **18 months** - Every 1.5 years
- **24 months** - Biennial
- **36 months** - Every 3 years
- **Off** - No periodic review required

**4. API Integration**:
```typescript
const requestBody: any = {
  action: 'approve_document',
  approved: true,
  comment: comment,
  effective_date: effectiveDate,
  review_period_months: requiresReview ? reviewPeriodMonths : null
};
```

---

### **Backend Changes**

**1. Document Lifecycle Service** (`document_lifecycle.py`)

Updated `approve_document()` signature:
```python
def approve_document(self, document: Document, user: User, 
                    effective_date: date, comment: str = '', approved: bool = True,
                    review_period_months: int = None) -> bool:
```

**Review Date Calculation**:
```python
if review_period_months is not None and review_period_months > 0:
    document.review_period_months = review_period_months
    from dateutil.relativedelta import relativedelta
    document.next_review_date = effective_date + relativedelta(months=review_period_months)
else:
    # No periodic review required
    document.review_period_months = None
    document.next_review_date = None
```

**2. Views** (`views.py`)

Updated workflow action handler to pass review_period_months:
```python
success = lifecycle.approve_document(
    document=document,
    user=request.user,
    effective_date=effective_date,
    comment=comment,
    approved=True,
    review_period_months=request.data.get("review_period_months")
)
```

---

## 🎨 **User Experience**

### **Approval Flow with Review Configuration**

```
1. Approver opens approval modal
   ↓
2. Sees expanded form:
   - Effective Date (required)
   - Periodic Review toggle (default: ON)
   - Review Interval dropdown (default: 12 months)
   ↓
3. Approver can:
   - Keep default (annual review)
   - Change interval (6/18/24/36 months)
   - Turn off reviews (for reference docs)
   ↓
4. System shows calculated next review date
   ↓
5. Approver approves document
   ↓
6. Backend saves:
   - effective_date
   - review_period_months (or null)
   - next_review_date (or null)
```

---

## 📊 **Examples**

### **Example 1: Standard SOP (Annual Review)**

```
Approval Input:
- Effective Date: 2026-01-22
- Periodic Review: ON
- Interval: 12 months

Result:
- effective_date: 2026-01-22
- review_period_months: 12
- next_review_date: 2027-01-22
```

### **Example 2: High-Risk Document (6 Month Review)**

```
Approval Input:
- Effective Date: 2026-01-22
- Periodic Review: ON
- Interval: 6 months

Result:
- effective_date: 2026-01-22
- review_period_months: 6
- next_review_date: 2026-07-22
```

### **Example 3: Reference Document (No Review)**

```
Approval Input:
- Effective Date: 2026-01-22
- Periodic Review: OFF

Result:
- effective_date: 2026-01-22
- review_period_months: null
- next_review_date: null
```

---

## ✅ **Benefits**

### **1. Streamlined Process**
- ✅ Review schedule set during approval (single step)
- ✅ No post-approval configuration needed
- ✅ Approver decides if review required

### **2. Flexibility**
- ✅ Multiple review intervals supported
- ✅ Can disable reviews for reference docs
- ✅ Visual feedback (calculated date shown)

### **3. Compliance**
- ✅ Ensures critical documents reviewed regularly
- ✅ Review dates tracked from approval
- ✅ Scheduler can monitor and notify

### **4. User Experience**
- ✅ Intuitive toggle switch
- ✅ Clear dropdown options
- ✅ Immediate feedback on next review date
- ✅ Smart defaults (annual review)

---

## 🧪 **Testing**

### **Test Cases**

**1. Approve with Default Review**
- [ ] Toggle ON, 12 months selected
- [ ] Approve document
- [ ] Verify next_review_date set to +12 months
- [ ] Verify review_period_months = 12

**2. Approve with Custom Interval**
- [ ] Select 6 months
- [ ] Verify calculated date updates
- [ ] Approve document
- [ ] Verify next_review_date set to +6 months

**3. Approve without Review**
- [ ] Toggle OFF
- [ ] Info message shows
- [ ] Approve document
- [ ] Verify next_review_date = null
- [ ] Verify review_period_months = null

**4. Date Calculation**
- [ ] Effective date: 2026-01-31
- [ ] Interval: 12 months
- [ ] Next review: 2027-01-31 (handles month-end correctly)

**5. Toggle Interaction**
- [ ] Toggle ON → dropdown appears
- [ ] Toggle OFF → dropdown hides
- [ ] Toggle ON again → previous selection restored

---

## 🔄 **Integration with Scheduler**

The scheduler will:
1. Check `next_review_date` field daily
2. Find documents where `next_review_date <= today`
3. Send notifications to stakeholders
4. Create periodic review workflow

Documents with `next_review_date = null` are skipped.

---

## 📝 **Database Fields Used**

| Field | Type | Purpose |
|-------|------|---------|
| `review_period_months` | Integer (nullable) | Review interval in months |
| `next_review_date` | Date (nullable) | When next review due |
| `last_review_date` | Date (nullable) | When last reviewed |
| `last_reviewed_by` | ForeignKey (nullable) | Who reviewed last |

---

## 🎯 **Future Enhancements**

### **Potential Improvements**

1. **Document Type Defaults**:
   - Set default review periods per document type
   - Critical SOPs: 6 months
   - Standard SOPs: 12 months
   - Reference: No review

2. **Risk-Based Review**:
   - High risk: 6 months
   - Medium risk: 12 months
   - Low risk: 24 months

3. **Custom Intervals**:
   - Allow custom month input
   - Validate range (1-60 months)

4. **Review Reminders**:
   - Email 30 days before due
   - Email on due date
   - Email 7 days overdue

5. **Bulk Configuration**:
   - Set review periods for multiple documents
   - Template-based configuration

---

## 📊 **Files Modified**

```
Frontend (1 file):
✓ frontend/src/components/workflows/UnifiedWorkflowInterface.tsx
  - Added review period state
  - Added UI section with toggle and dropdown
  - Added API integration

Backend (2 files):
✓ backend/apps/workflows/document_lifecycle.py
  - Added review_period_months parameter
  - Added date calculation logic

✓ backend/apps/documents/views.py
  - Pass review_period_months to lifecycle service
```

**Lines Added**: ~80 lines  
**Complexity**: Low  
**Breaking Changes**: None (backward compatible)

---

## ✅ **Deployment Status**

- ✅ Frontend implemented
- ✅ Backend implemented
- ✅ Backend restarted
- ✅ Ready for testing
- ⏳ Awaiting manual validation

---

## 🧪 **Test Now**

### **Testing Instructions**:

1. **Refresh Browser** (F5)
2. **Open Document**: TEST-2026-9999
3. **Click**: "✅ Start Approval Process"
4. **Verify**: New section appears:
   - "🔄 Periodic Review Required" toggle
   - "Review Interval" dropdown
   - Calculated next review date
5. **Test**: 
   - Toggle ON/OFF
   - Select different intervals
   - Approve document
6. **Verify**: Document approved with review_period_months set

---

**Status**: ✅ **Ready for Testing**

**Approver Login**:
- URL: http://localhost:3000
- Username: approver01
- Password: TestPass123!

**Test Document**: TEST-2026-9999 (PENDING_APPROVAL)

🎉 **Periodic review configuration is now part of the approval process!**
