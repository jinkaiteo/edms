# 🧪 EDMS User Acceptance Testing (UAT) Scenarios

**Document Version**: 1.0  
**Test Date**: November 2025  
**Purpose**: Validate EDMS workflow system meets business requirements  
**Compliance**: 21 CFR Part 11 validation requirements

---

## 🎯 **UAT OVERVIEW**

### **Test Objectives**
- ✅ Validate complete document lifecycle workflows
- ✅ Verify role-based access control and permissions
- ✅ Confirm regulatory compliance (21 CFR Part 11, ALCOA)
- ✅ Test user interface usability and accessibility
- ✅ Validate error handling and system reliability

### **Test Environment**
- **System**: EDMS Docker containerized deployment
- **Database**: PostgreSQL 18 with sample data
- **Users**: 5 test accounts with different roles
- **Browser**: Chrome/Firefox/Edge compatibility testing

---

## 👥 **TEST USERS & CREDENTIALS**

### **Primary Test Users**
```
🔐 admin / test123          - System Administrator
📝 author / test123         - Document Author  
👀 reviewer / test123       - Document Reviewer
✅ approver / test123       - Document Approver
🏢 docadmin / test123       - Document Administrator
```

### **User Role Matrix**
| User | Create | Upload | Review | Approve | Admin | Workflow Config |
|------|--------|--------|--------|---------|-------|-----------------|
| admin | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| author | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| reviewer | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ |
| approver | ❌ | ❌ | ✅ | ✅ | ❌ | ❌ |
| docadmin | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

---

## 📋 **UAT TEST SCENARIOS**

## **SCENARIO 1: Complete Document Workflow (Primary Path)**

### **Test Case 1.1: Document Creation and Upload**
**User**: author  
**Objective**: Create and upload a new document for review

**Test Steps**:
1. Login as `author` with password `test123`
2. Navigate to Document Management → Upload Document
3. Fill out document information:
   - **Title**: "UAT Test SOP - Document Management"
   - **Document Type**: "Standard Operating Procedure"
   - **Description**: "Test SOP for UAT validation process"
   - **File**: Upload sample .docx file (provided)
4. Select **reviewer** as document reviewer
5. Select **approver** as document approver
6. Click "Upload Document"

**Expected Results**:
- ✅ Document uploaded successfully
- ✅ Document number auto-generated (format: SOP-YYYY-NNNN)
- ✅ Document status shows "DRAFT"
- ✅ Reviewer and approver assigned correctly
- ✅ Author receives confirmation message

**Acceptance Criteria**:
- [ ] Document appears in author's "My Documents" 
- [ ] File is accessible for download
- [ ] Metadata properly saved
- [ ] Audit log entry created

---

### **Test Case 1.2: Submit Document for Review**
**User**: author (continuing from 1.1)  
**Objective**: Submit document to reviewer

**Test Steps**:
1. Navigate to "My Documents"
2. Find the uploaded test document
3. Click "Actions" → "Submit for Review"
4. Add comment: "Ready for initial review - UAT testing"
5. Confirm submission

**Expected Results**:
- ✅ Document status changes to "PENDING_REVIEW"
- ✅ Reviewer receives task assignment
- ✅ Author can see status update
- ✅ Workflow transition logged

**Acceptance Criteria**:
- [ ] Document no longer editable by author
- [ ] Reviewer sees new task in "My Tasks"
- [ ] Email notification sent (if configured)
- [ ] Audit trail updated

---

### **Test Case 1.3: Document Review Process**
**User**: reviewer  
**Objective**: Review assigned document

**Test Steps**:
1. **Login as reviewer**
2. Navigate to "My Tasks" 
3. Verify test document appears in pending tasks
4. Click on document title to open
5. Download document for review
6. **Scenario A - Approve Review**:
   - Click "Approve Review"
   - Add comment: "Document reviewed and approved for final approval"
   - Submit approval
7. **Scenario B - Reject Review** (alternate path):
   - Click "Reject Review" 
   - Add comment: "Please revise section 3.2 for clarity"
   - Submit rejection

**Expected Results (Scenario A)**:
- ✅ Document status changes to "REVIEWED"
- ✅ Document moves to approver's task list
- ✅ Reviewer task marked complete
- ✅ Author notified of review completion

**Expected Results (Scenario B)**:
- ✅ Document status returns to "DRAFT"
- ✅ Document returns to author for revision
- ✅ Rejection reason visible to author
- ✅ Reviewer task marked complete

**Acceptance Criteria**:
- [ ] Task disappears from reviewer's queue
- [ ] Appropriate workflow transition
- [ ] Comments preserved in audit trail
- [ ] Notifications sent to relevant parties

---

### **Test Case 1.4: Final Document Approval**
**User**: approver  
**Objective**: Approve or reject reviewed document

**Test Steps**:
1. **Login as approver**
2. Navigate to "My Tasks"
3. Verify reviewed document appears
4. Download document for final review
5. **Scenario A - Approve Document**:
   - Click "Approve Document"
   - Set effective date (today + 1 day)
   - Add comment: "Final approval granted - ready for production"
   - Submit approval
6. **Scenario B - Reject Document** (alternate path):
   - Click "Reject Document"
   - Add comment: "Requires additional safety warnings"
   - Submit rejection

**Expected Results (Scenario A)**:
- ✅ Document status changes to "APPROVED_PENDING_EFFECTIVE" 
- ✅ Effective date set correctly
- ✅ Document queued for automatic activation
- ✅ All participants notified

**Expected Results (Scenario B)**:
- ✅ Document returns to "DRAFT" status
- ✅ Author notified of rejection with reasons
- ✅ Document available for revision

**Acceptance Criteria**:
- [ ] Final status properly set
- [ ] Effective date handling correct
- [ ] Complete audit trail maintained
- [ ] All stakeholders notified

---

### **Test Case 1.5: Document Becomes Effective**
**User**: admin  
**Objective**: Verify automatic document activation

**Test Steps**:
1. **Login as admin**
2. Navigate to Documents → All Documents
3. Find the approved test document
4. Verify status shows "APPROVED_PENDING_EFFECTIVE"
5. **Simulate scheduler** (or wait for effective date):
   - Navigate to Admin → System Tasks
   - Run "Update Document Status" task
6. Refresh and check document status

**Expected Results**:
- ✅ Document status changes to "EFFECTIVE"
- ✅ Document appears in published documents
- ✅ Effective date recorded correctly
- ✅ Digital signature applied (if configured)

**Acceptance Criteria**:
- [ ] Document searchable by all users
- [ ] Version history preserved
- [ ] Audit trail complete
- [ ] Document immutable in effective state

---

## **SCENARIO 2: Document Version Control**

### **Test Case 2.1: Up-versioning Effective Document**
**User**: author  
**Objective**: Create new version of effective document

**Test Steps**:
1. **Login as author**
2. Navigate to Documents → All Documents
3. Find effective test document from Scenario 1
4. Click "Actions" → "Create New Version"
5. Upload revised document file
6. Add version change reason: "Updated safety procedures per new regulations"
7. Submit for review workflow

**Expected Results**:
- ✅ New version created (version 1.1 or 2.0)
- ✅ Previous version remains effective
- ✅ New version enters review workflow
- ✅ Version relationships maintained

**Acceptance Criteria**:
- [ ] Version numbering correct
- [ ] Original document still effective
- [ ] New version in draft/review status
- [ ] Version history linked

---

### **Test Case 2.2: Version Superseding Process**
**User**: Various users  
**Objective**: Complete new version and supersede old version

**Test Steps**:
1. Complete review/approval workflow for new version
2. Set effective date for new version
3. Verify old version status changes to "SUPERSEDED"
4. Check version relationships and dependencies

**Expected Results**:
- ✅ New version becomes effective
- ✅ Old version marked as superseded
- ✅ Users see current effective version
- ✅ Historical versions accessible

**Acceptance Criteria**:
- [ ] Only current version active
- [ ] Version history preserved
- [ ] Search returns current version
- [ ] Superseded version read-only

---

## **SCENARIO 3: Document Obsolescence**

### **Test Case 3.1: Obsolete Document Workflow**
**User**: author  
**Objective**: Mark effective document as obsolete

**Test Steps**:
1. **Login as author**
2. Find effective document to obsolete
3. Click "Actions" → "Mark Obsolete"
4. Enter obsolescence reason: "Process no longer used - replaced by automated system"
5. Submit for approval
6. **As approver**: Approve obsolescence with future effective date

**Expected Results**:
- ✅ Document enters obsolescence workflow
- ✅ Approver must confirm obsolescence
- ✅ Obsolescence date set
- ✅ Document marked obsolete on effective date

**Acceptance Criteria**:
- [ ] Document removed from active use
- [ ] Still accessible for historical reference
- [ ] Audit trail maintained
- [ ] Dependencies checked

---

## **SCENARIO 4: Role-Based Access Control**

### **Test Case 4.1: Permission Boundaries**
**User**: reviewer  
**Objective**: Verify role-based restrictions

**Test Steps**:
1. **Login as reviewer**
2. Attempt to access Admin Dashboard
3. Try to upload new document
4. Attempt to approve documents (should only review)
5. Try to modify workflow configuration

**Expected Results**:
- ❌ Admin Dashboard access denied
- ❌ Document upload not available
- ❌ Approval actions not visible
- ❌ Workflow configuration restricted

**Acceptance Criteria**:
- [ ] Appropriate error messages
- [ ] UI elements hidden for unauthorized actions
- [ ] Access attempts logged
- [ ] No system errors or crashes

---

### **Test Case 4.2: Cross-User Document Access**
**User**: Various  
**Objective**: Verify document visibility rules

**Test Steps**:
1. Create document as **author**
2. **As reviewer**: Verify can only see assigned documents
3. **As different author**: Verify cannot see other's drafts
4. **As admin**: Verify can see all documents

**Expected Results**:
- ✅ Users see only authorized documents
- ✅ Drafts private to authors
- ✅ Active workflows visible to participants
- ✅ Admin has full visibility

**Acceptance Criteria**:
- [ ] Document lists filtered correctly
- [ ] No unauthorized access possible
- [ ] Search respects permissions
- [ ] Audit log tracks access

---

## **SCENARIO 5: System Administration**

### **Test Case 5.1: User Management**
**User**: admin  
**Objective**: Manage user accounts and roles

**Test Steps**:
1. **Login as admin**
2. Navigate to Admin → User Management
3. **Create new test user**:
   - Username: `testuser1`
   - Email: `testuser1@company.com`
   - Role: Document Reviewer
4. **Modify existing user**:
   - Change reviewer to approver role
   - Deactivate user account
5. **Reset user password**

**Expected Results**:
- ✅ New user created successfully
- ✅ Role changes take effect immediately
- ✅ Deactivated users cannot login
- ✅ Password reset works

**Acceptance Criteria**:
- [ ] User changes logged in audit trail
- [ ] Role permissions updated correctly
- [ ] Security maintained throughout
- [ ] No system disruptions

---

### **Test Case 5.2: Workflow Configuration**
**User**: admin  
**Objective**: Configure workflow settings

**Test Steps**:
1. Navigate to Admin → Workflow Configuration
2. **Modify workflow timeouts**:
   - Change review timeout from 30 to 14 days
   - Change approval timeout from 14 to 7 days
3. **Activate/deactivate workflow types**
4. **Test configuration changes** with new document

**Expected Results**:
- ✅ Timeout changes take effect for new workflows
- ✅ Deactivated workflows not available
- ✅ Configuration saved permanently
- ✅ No impact on existing workflows

**Acceptance Criteria**:
- [ ] Changes apply to new workflows only
- [ ] Configuration persisted correctly
- [ ] UI reflects current settings
- [ ] Admin actions logged

---

## **SCENARIO 6: Audit Trail and Compliance**

### **Test Case 6.1: Audit Trail Verification**
**User**: admin  
**Objective**: Verify complete audit trail

**Test Steps**:
1. **Login as admin**
2. Navigate to Admin → Audit Trail
3. **Filter audit logs** for test document from Scenario 1
4. Verify all workflow transitions logged
5. **Check log details**:
   - User attribution
   - Timestamps
   - IP addresses
   - Comments/reasons
6. **Export audit report** for compliance

**Expected Results**:
- ✅ Every workflow action logged
- ✅ Complete user attribution
- ✅ Accurate timestamps
- ✅ No missing audit entries
- ✅ Export functionality works

**Acceptance Criteria**:
- [ ] 21 CFR Part 11 compliance verified
- [ ] ALCOA principles met
- [ ] Audit logs tamper-proof
- [ ] Export format suitable for regulators

---

### **Test Case 6.2: Electronic Signature Validation**
**User**: Various  
**Objective**: Verify electronic signature compliance

**Test Steps**:
1. Complete document approval workflow
2. Download final approved document
3. **Verify electronic signature elements**:
   - Digital signature present
   - Signer identification
   - Signature timestamp
   - Document integrity seal
4. **Test signature validation**

**Expected Results**:
- ✅ Electronic signatures applied
- ✅ Signer identification clear
- ✅ Timestamps accurate
- ✅ Document integrity maintained

**Acceptance Criteria**:
- [ ] Signatures legally compliant
- [ ] Non-repudiation achieved
- [ ] Document tampering detectable
- [ ] Signature validation works

---

## **SCENARIO 7: Error Handling and Recovery**

### **Test Case 7.1: Network Interruption Handling**
**User**: author  
**Objective**: Test system resilience

**Test Steps**:
1. Start document upload process
2. **Simulate network interruption**:
   - Disconnect network during upload
   - Reconnect after 30 seconds
3. Complete upload process
4. Verify document integrity

**Expected Results**:
- ✅ System handles interruption gracefully
- ✅ Upload can be resumed or restarted
- ✅ No data corruption
- ✅ Appropriate error messages

**Acceptance Criteria**:
- [ ] User data not lost
- [ ] Clear error messaging
- [ ] Recovery process intuitive
- [ ] System stability maintained

---

### **Test Case 7.2: Concurrent User Operations**
**User**: Multiple users  
**Objective**: Test multi-user scenarios

**Test Steps**:
1. **Simultaneous login** of 5 different users
2. **Concurrent document operations**:
   - User 1: Upload document
   - User 2: Review different document
   - User 3: Approve different document
   - User 4: Search documents
   - User 5: Configure workflows
3. Verify no conflicts or data corruption

**Expected Results**:
- ✅ All users can work simultaneously
- ✅ No data conflicts
- ✅ Performance remains acceptable
- ✅ Each user sees correct data

**Acceptance Criteria**:
- [ ] Multi-user operations successful
- [ ] Data integrity maintained
- [ ] Performance acceptable (<3 seconds)
- [ ] No system errors

---

## **SCENARIO 8: Mobile and Accessibility Testing**

### **Test Case 8.1: Mobile Device Compatibility**
**User**: reviewer  
**Objective**: Test mobile accessibility

**Test Steps**:
1. Access EDMS on mobile device (smartphone/tablet)
2. **Login and navigate** to My Tasks
3. **Review document** on mobile device:
   - View document details
   - Download document
   - Approve/reject review
4. Test touch interface responsiveness

**Expected Results**:
- ✅ Mobile interface responsive
- ✅ All functions accessible
- ✅ Touch interface works correctly
- ✅ Text readable without zooming

**Acceptance Criteria**:
- [ ] Mobile-friendly interface
- [ ] All workflows accessible
- [ ] Performance acceptable
- [ ] Usability maintained

---

### **Test Case 8.2: Accessibility Compliance**
**User**: Various  
**Objective**: Verify WCAG 2.1 compliance

**Test Steps**:
1. **Screen reader testing**:
   - Navigate using screen reader
   - Complete workflow operations
2. **Keyboard navigation**:
   - Navigate without mouse
   - Complete all actions via keyboard
3. **Visual accessibility**:
   - Test high contrast mode
   - Verify color blind accessibility
4. **Alternative format testing**

**Expected Results**:
- ✅ Screen reader compatible
- ✅ Full keyboard navigation
- ✅ High contrast support
- ✅ Color-blind friendly

**Acceptance Criteria**:
- [ ] WCAG 2.1 AA compliance
- [ ] Government accessibility standards met
- [ ] Inclusive design verified
- [ ] Alternative access methods work

---

## 📊 **UAT COMPLETION CRITERIA**

### **Pass/Fail Criteria**
Each test scenario must achieve:
- ✅ **Functionality**: All steps complete successfully
- ✅ **Usability**: Intuitive user experience
- ✅ **Performance**: Response times <3 seconds
- ✅ **Reliability**: No system crashes or data loss
- ✅ **Compliance**: 21 CFR Part 11 requirements met

### **UAT Sign-off Requirements**
- [ ] **Business Users**: All scenarios passed by user representatives
- [ ] **IT Manager**: Technical requirements validated
- [ ] **Compliance Officer**: Regulatory requirements verified
- [ ] **QA Manager**: Test procedures and results approved

---

## 📋 **UAT EXECUTION CHECKLIST**

### **Pre-Testing Setup**
- [ ] Test environment prepared and validated
- [ ] Test data created and verified
- [ ] User accounts configured correctly
- [ ] Testing schedule coordinated with stakeholders

### **During Testing**
- [ ] All test scenarios executed
- [ ] Results documented for each test case
- [ ] Issues logged with severity and priority
- [ ] Stakeholder feedback collected

### **Post-Testing Activities**
- [ ] Test results compiled and analyzed
- [ ] Issues prioritized for resolution
- [ ] UAT report prepared for management
- [ ] Production deployment recommendation made

---

## 🎯 **EXPECTED OUTCOMES**

### **Successful UAT Completion**
Upon successful completion of all test scenarios:
- ✅ **Business Confidence**: Users comfortable with system
- ✅ **Regulatory Readiness**: Compliance requirements validated
- ✅ **Production Approval**: System ready for live deployment
- ✅ **Training Needs**: User training requirements identified

### **UAT Documentation Deliverables**
1. **Test Execution Report**: Detailed results for each scenario
2. **Issue Log**: All defects found with resolution status
3. **User Feedback Summary**: Business user satisfaction assessment
4. **Compliance Validation**: 21 CFR Part 11 compliance verification
5. **Production Readiness Certification**: Final deployment approval

---

**Document Control**:  
- **Version**: 1.0  
- **Prepared by**: EDMS Development Team  
- **Approved by**: [To be completed during UAT]  
- **Next Review**: Post-UAT completion