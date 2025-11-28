# EDMS Workflow Testing - Comprehensive User Matrix

## 📊 **Available User Combinations for Testing**

Based on the database analysis, here are all available users organized by workflow capability:

### **AUTHORS (Can Create Documents & Submit for Review)**
| Username | ID | Full Name | Email | Password | Additional Roles |
|----------|----|-----------|----- |----------|-----------------|
| `author` | 3 | Document Author | author@edms-project.com | `AuthorPass2024!` | Write only |
| `admin` | 1 | Admin Superuser | admin@edms.local | `EDMSAdmin2024!` | Write + Admin + Superuser |
| `placeholderadmin` | 6 | Placeholder Admin | placeholderadmin@edms-project.com | `PlaceholderAdmin2024!` | Write + Placeholder Admin |

### **REVIEWERS (Can Review Documents)**
| Username | ID | Full Name | Email | Password | Additional Roles |
|----------|----|-----------|----- |----------|-----------------|
| `reviewer` | 4 | Document Reviewer | reviewer@edms-project.com | `ReviewPass2024!` | Review only |
| `approver` | 5 | Document Approver | approver@edms-project.com | `ApprovePass2024!` | Review + Approve |
| `testuser` | 7 | Test User | test@edms.local | `TestUser2024!` | Review only |

### **APPROVERS (Can Approve Documents)**
| Username | ID | Full Name | Email | Password | Additional Roles |
|----------|----|-----------|----- |----------|-----------------|
| `approver` | 5 | Document Approver | approver@edms-project.com | `ApprovePass2024!` | Review + Approve |

### **ADMINS (Can Manage Everything)**
| Username | ID | Full Name | Email | Password | Capabilities |
|----------|----|-----------|----- |----------|-------------|
| `admin` | 1 | Admin Superuser | admin@edms.local | `EDMSAdmin2024!` | All permissions + Superuser |
| `docadmin` | 2 | Document Administrator | docadmin@edms-project.com | `EDMSAdmin2024!` | Document Admin |

## 🧪 **Recommended Testing Scenarios**

### **Scenario 1: Original Team (Already Tested) ✅**
- **Author**: `author` (ID: 3)
- **Reviewer**: `reviewer` (ID: 4)  
- **Approver**: `approver` (ID: 5)
- **Status**: ✅ **FULLY TESTED** - Complete workflow functional

### **Scenario 2: Alternative Team A (Recommended Next)**
- **Author**: `placeholderadmin` (ID: 6) - Has write permission
- **Reviewer**: `testuser` (ID: 7) - Different reviewer
- **Approver**: `approver` (ID: 5) - Same approver (only one available)
- **Purpose**: Test different author/reviewer combination

### **Scenario 3: Admin-Led Team**
- **Author**: `admin` (ID: 1) - Superuser as author
- **Reviewer**: `approver` (ID: 5) - Approver acting as reviewer
- **Approver**: `admin` (ID: 1) - Admin approving their own document
- **Purpose**: Test admin permissions and self-approval

### **Scenario 4: Cross-Role Testing**
- **Author**: `author` (ID: 3) - Original author
- **Reviewer**: `approver` (ID: 5) - Approver acting as reviewer
- **Approver**: `admin` (ID: 1) - Admin as final approver
- **Purpose**: Test users with multiple roles

## 📋 **Complete Workflow Testing Steps**

### **Step 1: Document Creation (Author)**
1. Login as the designated author
2. Go to Document Management → Create New Document
3. Upload file, set title, description, document type
4. Assign reviewer and submit for review
5. **Verify**: Status changes `DRAFT` → `PENDING_REVIEW`

### **Step 2: Review Process (Reviewer)**  
1. Login as the designated reviewer
2. Navigate to the document in Document Management
3. **Verify**: "📋 Start Review Process" button appears
4. Click button, add review comments, approve
5. **Verify**: Status changes `PENDING_REVIEW` → `UNDER_REVIEW` → `REVIEWED`

### **Step 3: Approval Routing (Author)**
1. Login as original author
2. Navigate to the reviewed document
3. **Verify**: "✅ Route for Approval" button appears
4. Select approver from dropdown and route document
5. **Verify**: Status changes `REVIEWED` → `PENDING_APPROVAL`

### **Step 4: Final Approval (Approver)**
1. Login as the designated approver
2. Navigate to the document awaiting approval
3. **Verify**: "✅ Start Approval Process" button appears
4. Approve the document with comments
5. **Verify**: Status changes `PENDING_APPROVAL` → `APPROVED`

### **Step 5: Make Effective (Approver)**
1. **Verify**: "📅 Set Effective Date" button appears
2. Click "Make Effective Immediately"
3. **Verify**: Status changes `APPROVED` → `EFFECTIVE`

## 🎯 **Quick Testing Guide for Scenario 2**

**Test with Alternative Team A:**

1. **Login as `placeholderadmin`** (`PlaceholderAdmin2024!`)
   - Create new document
   - Assign `testuser` as reviewer
   - Submit for review

2. **Login as `testuser`** (`TestUser2024!`)  
   - Review and approve document

3. **Login as `placeholderadmin`** 
   - Route document to `approver`

4. **Login as `approver`** (`ApprovePass2024!`)
   - Approve and make effective

## ✅ **Testing Verification Checklist**

For each scenario, verify:
- ✅ Button visibility for each role
- ✅ Permission enforcement
- ✅ Status transitions
- ✅ Comment recording
- ✅ Error handling

## 🚀 **Recommended Next Steps**

1. **Test Scenario 2** first (most straightforward alternative)
2. **Test Scenario 4** (cross-role functionality)  
3. **Test Scenario 3** (admin edge cases)

This will confirm the workflow is robust across all user combinations before implementing additional workflows!