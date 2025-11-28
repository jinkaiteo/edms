# 📊 UAT Sample Test Data & Scripts

**Purpose**: Pre-configured test data and scripts for UAT execution  
**Environment**: EDMS Test Environment  
**Created**: November 2025

---

## 👥 **TEST USER ACCOUNTS**

### **User Account Setup Script**
```bash
# Execute in Docker container to create UAT users
docker compose exec backend python manage.py shell -c "
from apps.users.models import User, Role, UserRole

# Create UAT test users if they don't exist
users_data = [
    {'username': 'uat_author', 'email': 'uat.author@company.com', 'first_name': 'John', 'last_name': 'Author'},
    {'username': 'uat_reviewer', 'email': 'uat.reviewer@company.com', 'first_name': 'Jane', 'last_name': 'Reviewer'},
    {'username': 'uat_approver', 'email': 'uat.approver@company.com', 'first_name': 'Mike', 'last_name': 'Approver'},
    {'username': 'uat_admin', 'email': 'uat.admin@company.com', 'first_name': 'Sarah', 'last_name': 'Admin'},
]

for user_data in users_data:
    user, created = User.objects.get_or_create(
        username=user_data['username'],
        defaults={
            'email': user_data['email'],
            'first_name': user_data['first_name'],
            'last_name': user_data['last_name'],
            'is_active': True,
            'is_staff': True
        }
    )
    user.set_password('UAT2025!')
    user.save()
    print(f'UAT User created: {user.username} / UAT2025!')
"
```

---

## 📄 **SAMPLE DOCUMENTS FOR TESTING**

### **Document Templates**

#### **1. Standard Operating Procedure Template**
```
Document Title: UAT Test SOP - Quality Control Procedures
Document Number: [Auto-generated]
Document Type: Standard Operating Procedure
Version: 1.0

Content Overview:
- Purpose and Scope
- Responsibilities
- Procedure Steps
- Quality Checkpoints
- Approval Requirements

File: sample_sop.docx (provided separately)
```

#### **2. Work Instruction Template**
```
Document Title: UAT Test WI - Equipment Calibration
Document Number: [Auto-generated]
Document Type: Work Instruction
Version: 1.0

Content Overview:
- Equipment list
- Calibration frequency
- Step-by-step procedures
- Documentation requirements

File: sample_work_instruction.docx
```

#### **3. Policy Document Template**
```
Document Title: UAT Test Policy - Document Control
Document Number: [Auto-generated]
Document Type: Policy
Version: 1.0

Content Overview:
- Policy statement
- Applicability
- Responsibilities
- Implementation guidelines

File: sample_policy.docx
```

---

## 🧪 **TEST DATA SCENARIOS**

### **Scenario 1 Test Data: New Document Creation**
```json
{
  "test_documents": [
    {
      "title": "UAT-001: Chemical Storage Procedures",
      "type": "Standard Operating Procedure",
      "description": "Detailed procedures for safe chemical storage in laboratory environments",
      "author": "uat_author",
      "reviewer": "uat_reviewer", 
      "approver": "uat_approver",
      "expected_workflow": "REVIEW → APPROVAL → EFFECTIVE"
    },
    {
      "title": "UAT-002: Quality Assurance Manual",
      "type": "Manual",
      "description": "Comprehensive QA manual for manufacturing processes",
      "author": "uat_author",
      "reviewer": "uat_reviewer",
      "approver": "uat_approver", 
      "expected_workflow": "REVIEW → APPROVAL → EFFECTIVE"
    }
  ]
}
```

### **Scenario 2 Test Data: Version Control**
```json
{
  "version_control_test": {
    "base_document": "UAT-001: Chemical Storage Procedures v1.0",
    "new_version": {
      "version": "1.1",
      "changes": "Added section on hazardous waste disposal",
      "reason": "Updated per new EPA regulations",
      "change_impact": "Minor revision - training update required"
    }
  }
}
```

### **Scenario 3 Test Data: Document Obsolescence**
```json
{
  "obsolescence_test": {
    "document": "UAT-003: Legacy Equipment Manual",
    "reason": "Equipment decommissioned - replaced with automated system",
    "dependencies": [],
    "obsolete_date": "2025-12-31",
    "replacement_document": "UAT-004: Automated System Manual"
  }
}
```

---

## 🔧 **UAT ENVIRONMENT SETUP SCRIPTS**

### **Database Setup for UAT**
```bash
#!/bin/bash
# UAT Environment Setup Script

echo "Setting up UAT test environment..."

# 1. Create test database backup
docker compose exec backend python manage.py dumpdata --natural-foreign --natural-primary > uat_backup.json

# 2. Create UAT test data
docker compose exec backend python manage.py shell -c "
from apps.documents.models import DocumentType, DocumentSource

# Ensure document types exist
doc_types = [
    ('SOP', 'Standard Operating Procedure', 'SOPs for operational processes'),
    ('WI', 'Work Instruction', 'Detailed work instructions'),
    ('POL', 'Policy', 'Company policies and guidelines'),
    ('MAN', 'Manual', 'Comprehensive procedure manuals'),
    ('FORM', 'Form', 'Templates and forms'),
    ('REC', 'Record', 'Quality and compliance records')
]

for code, name, desc in doc_types:
    DocumentType.objects.get_or_create(
        code=code,
        defaults={'name': name, 'description': desc}
    )

print('UAT document types configured')
"

echo "UAT environment ready for testing"
```

### **Reset UAT Environment Script**
```bash
#!/bin/bash
# Reset UAT environment between test sessions

echo "Resetting UAT environment..."

# Clear test documents
docker compose exec backend python manage.py shell -c "
from apps.documents.models import Document
from apps.workflows.models import DocumentWorkflow, WorkflowTask

# Delete UAT test documents (keeping system data)
test_docs = Document.objects.filter(document_number__startswith='UAT-')
print(f'Removing {test_docs.count()} UAT test documents')
test_docs.delete()

# Clean up orphaned workflows
orphaned_workflows = DocumentWorkflow.objects.filter(document__isnull=True)
orphaned_workflows.delete()

# Clean up orphaned tasks
orphaned_tasks = WorkflowTask.objects.filter(workflow_instance__isnull=True)
orphaned_tasks.delete()

print('UAT environment reset complete')
"

echo "UAT environment reset complete"
```

---

## 📋 **UAT TEST EXECUTION CHECKLISTS**

### **Pre-Test Setup Checklist**
- [ ] UAT test environment accessible
- [ ] Test user accounts created and verified
- [ ] Sample documents prepared and accessible
- [ ] Database backup created
- [ ] Test scenarios printed/accessible
- [ ] Stakeholders notified of test schedule
- [ ] Recording/documentation tools ready

### **Test Session Checklist**
- [ ] All testers logged in successfully
- [ ] Baseline performance metrics recorded
- [ ] Test data loaded correctly
- [ ] Network connectivity verified
- [ ] Browser compatibility confirmed
- [ ] Screen recording started (if required)

### **Post-Test Checklist**
- [ ] All test results documented
- [ ] Issues logged with severity ratings
- [ ] Performance metrics recorded
- [ ] User feedback collected
- [ ] Test environment reset for next session
- [ ] Stakeholder summary prepared

---

## 📊 **UAT METRICS COLLECTION**

### **Performance Benchmarks**
```javascript
// Performance testing script
const performanceTests = {
  login: {
    expected: '< 2 seconds',
    metric: 'time_to_dashboard'
  },
  documentUpload: {
    expected: '< 30 seconds for 10MB file',
    metric: 'upload_completion_time'
  },
  workflowTransition: {
    expected: '< 3 seconds',
    metric: 'state_change_time'
  },
  searchResponse: {
    expected: '< 2 seconds',
    metric: 'search_result_time'
  },
  pageLoad: {
    expected: '< 3 seconds',
    metric: 'dom_content_loaded'
  }
};
```

### **User Experience Metrics**
```
Usability Metrics to Track:
- Task completion rate
- Time to complete workflows  
- Number of clicks to complete tasks
- User error rate
- Help/support requests
- User satisfaction ratings
```

---

## 🎯 **UAT SUCCESS CRITERIA**

### **Functional Acceptance Criteria**
- ✅ **100% of critical workflows** must complete successfully
- ✅ **95% of test scenarios** must pass without major issues
- ✅ **All user roles** must be able to perform assigned functions
- ✅ **Zero data loss** during normal operations
- ✅ **Complete audit trail** for all workflow actions

### **Performance Acceptance Criteria**  
- ✅ **Page load times** < 3 seconds for 95% of requests
- ✅ **Document uploads** complete within expected timeframes
- ✅ **System availability** > 99% during test period
- ✅ **Concurrent user support** for 10+ simultaneous users
- ✅ **Mobile responsiveness** on tablets and smartphones

### **Compliance Acceptance Criteria**
- ✅ **21 CFR Part 11** compliance verified by quality team
- ✅ **ALCOA principles** demonstrated in audit trails
- ✅ **Role-based access control** functioning correctly
- ✅ **Electronic signatures** legally compliant
- ✅ **Data integrity** maintained throughout workflows

---

## 📞 **UAT SUPPORT CONTACTS**

### **Technical Support**
- **IT Helpdesk**: ext. 1234
- **System Administrator**: admin@company.com
- **EDMS Development Team**: edms-dev@company.com

### **Business Support**
- **Quality Manager**: quality@company.com  
- **Compliance Officer**: compliance@company.com
- **Training Coordinator**: training@company.com

### **Escalation Contacts**
- **Project Manager**: pm@company.com
- **IT Director**: it-director@company.com
- **Quality Director**: qd@company.com

---

**Document Control**:
- **Version**: 1.0
- **Last Updated**: November 2025
- **Next Review**: Post-UAT completion
- **Owner**: EDMS UAT Team