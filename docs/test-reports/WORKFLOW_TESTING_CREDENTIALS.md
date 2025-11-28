# EDMS Workflow Testing Credentials & Instructions

**System Status**: ✅ **READY FOR WORKFLOW TESTING**  
**Date**: November 22, 2025

## 🎯 WORKFLOW TEST USERS

### **Production-Ready Test Accounts**

| Username | Password | Role | Email | Purpose |
|----------|----------|------|-------|---------|
| **author** | `AuthorPass2024!` | Document Author | author@edms-project.com | Create and edit documents |
| **reviewer** | `ReviewPass2024!` | Document Reviewer | reviewer@edms-project.com | Review documents for approval |
| **approver** | `ApprovePass2024!` | Document Approver | approver@edms-project.com | Approve documents for effectiveness |
| **docadmin** | `EDMSAdmin2024!` | Document Admin | docadmin@edms-project.com | Full document management admin |
| **admin** | `admin123` | System Administrator | admin@edms.local | System administration |

### **Additional Test Users**

| Username | Password | Role | Purpose |
|----------|----------|------|---------|
| **viewer** | `ViewerPass2024!` | Document Viewer | Read-only access to documents |
| **placeholderadmin** | `PlaceholderAdmin2024!` | Placeholder Admin | Manage document templates |

## 🔐 ROLE PERMISSIONS HIERARCHY

```
read → write → review → approve → admin
```

### **Permission Levels**
- **read**: View documents and audit trails
- **write**: Create, edit documents + read permissions  
- **review**: Review documents for approval + write permissions
- **approve**: Approve documents for effectiveness + review permissions
- **admin**: Full module administration + approve permissions

## 📋 COMPLETE WORKFLOW TESTING SCENARIO

### **Test Document Lifecycle: DRAFT → EFFECTIVE**

#### **Step 1: Document Creation (Author)**
- **Login as**: `author` / `AuthorPass2024!`
- **Create new document**: Title, Description, Document Type
- **Initial State**: DRAFT
- **Action**: Submit for review

#### **Step 2: Document Review (Reviewer)**  
- **Login as**: `reviewer` / `ReviewPass2024!`
- **Review document**: Add comments, validate content
- **States**: DRAFT → PENDING_REVIEW → UNDER_REVIEW
- **Actions**: Approve for next step OR Reject back to author

#### **Step 3: Document Approval (Approver)**
- **Login as**: `approver` / `ApprovePass2024!`
- **Final approval**: Validate for regulatory compliance
- **States**: REVIEW_COMPLETED → PENDING_APPROVAL → UNDER_APPROVAL
- **Actions**: Approve OR Reject

#### **Step 4: Document Effectiveness (Approver)**
- **Set effective date**: When document becomes active
- **Final State**: APPROVED → EFFECTIVE
- **Result**: Document live in production

## 🏛️ 21 CFR PART 11 COMPLIANCE FEATURES

### **Audit Trail Verification**
- ✅ **Every action recorded** with user attribution
- ✅ **Tamper-proof timestamps** for all transitions
- ✅ **Complete workflow history** maintained
- ✅ **Electronic signature** support through user authentication
- ✅ **Role-based access control** enforced

### **ALCOA Principles Testing**
- **Attributable**: Each workflow step linked to authenticated user
- **Legible**: Clear transition history with comments
- **Contemporaneous**: Real-time workflow timestamping
- **Original**: Immutable workflow transition records
- **Accurate**: Proper state validation and business rules

## 🌐 API ACCESS FOR TESTING

### **Base URL**: `http://localhost:8000`

### **Key Endpoints**
- **Authentication**: `/api/v1/auth/login/`
- **Documents**: `/api/v1/documents/`
- **Workflows**: `/api/v1/workflows/`
- **Audit**: `/api/v1/audit/`
- **Users**: `/api/v1/users/`
- **Health**: `/health/`

### **Frontend Access**: `http://localhost:3000`

## 🔧 SYSTEM VERIFICATION CHECKLIST

### **Before Testing**
- [ ] All Docker containers running (6 containers)
- [ ] PostgreSQL database accessible
- [ ] Celery worker and beat scheduler active
- [ ] Frontend React app loading
- [ ] All test users can login successfully

### **During Testing**
- [ ] Document creation works (author)
- [ ] Workflow transitions function (reviewer → approver)
- [ ] Audit trails being recorded
- [ ] Email notifications (if configured)
- [ ] Role-based permissions enforced

### **After Testing**
- [ ] All workflow states recorded in database
- [ ] Audit trail complete and tamper-proof
- [ ] Document status matches workflow state
- [ ] User actions properly attributed

## 🚀 CRITICAL TESTING AREAS

### **1. Multi-User Workflow**
Test simultaneous workflows with different users to verify:
- Role separation and permissions
- Concurrent document processing
- Audit trail integrity

### **2. Compliance Features**
- Electronic signature workflows
- Audit trail immutability
- User authentication and authorization
- Data integrity validation

### **3. Error Scenarios**
- Invalid state transitions
- Unauthorized user actions
- Network connectivity issues
- Database consistency

### **4. Performance Testing**
- Workflow transition speed
- Database query performance
- Concurrent user handling
- File upload/download performance

## 📊 SUCCESS CRITERIA

### **Workflow Testing Passes If**:
- ✅ Complete document lifecycle (DRAFT → EFFECTIVE) works
- ✅ All user roles function with proper permissions
- ✅ Audit trail records every action with attribution
- ✅ State transitions are atomic and consistent
- ✅ Electronic signatures are properly validated
- ✅ Performance meets requirements (<2 second transitions)

---

**System Status**: The EDMS is **PRODUCTION-READY** for comprehensive workflow testing with full 21 CFR Part 11 compliance.