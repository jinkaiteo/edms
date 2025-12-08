# 🎯 EDMS Playwright Test Suite

## Overview

This comprehensive Playwright test suite is designed to:
1. **Seed the EDMS system** with realistic test data
2. **Test all major workflow scenarios** to ensure functionality
3. **Populate the application** with users, documents, and workflow states
4. **Validate system functionality** and generate comprehensive reports

## 📋 Test Structure

### Phase 1: User Seeding (`01_seed_users.spec.js`)
- **Creates 10 test users** with various roles:
  - **Authors**: `author01`, `author02` - Can create and manage documents
  - **Reviewers**: `reviewer01`, `reviewer02` - Can review documents for technical accuracy
  - **Approvers**: `approver01`, `approver02` - Can approve documents for publication
  - **Senior Approvers**: `senior01`, `senior02` - Can approve high-level documents
  - **Viewers**: `viewer01`, `viewer02` - Can view published documents
- **Sets up permission groups** and role assignments
- **Configures authentication** for all test scenarios

### Phase 2: Document Creation (`02_create_documents.spec.js`)
- **Creates 6 test documents** using the Tikva Quality Policy template:
  - Quality Policy V1.0 (Policy document)
  - Safety Procedures V1.0 (Procedure document)
  - Training Manual V2.0 (Manual document)
  - Audit Checklist V1.1 (Form document)
  - Emergency Procedures V1.0 (Procedure document)
  - Code of Conduct V3.0 (Policy document)
- **Tests document upload functionality** with real file attachments
- **Validates metadata assignment** and document categorization

### Phase 3: Workflow Testing (`03_workflow_testing.spec.js`)
- **Executes 4 comprehensive workflow scenarios**:

#### Scenario 1: Standard Review and Approval
```
Quality Policy V1.0:
author01 → submit_for_review → reviewer01 → approve_review → 
author01 → route_for_approval → approver01 → approve_document → 
author01 → set_effective_date
```

#### Scenario 2: Review Rejection and Resubmission
```
Safety Procedures V1.0:
author02 → submit_for_review → reviewer02 → reject_review →
author02 → resubmit_for_review → reviewer01 → approve_review →
author02 → route_for_approval → approver02 → approve_document
```

#### Scenario 3: Senior Approval Required
```
Training Manual V2.0:
author01 → submit_for_review → reviewer01 → approve_review →
author01 → route_for_approval → senior01 → approve_document →
author01 → set_effective_date
```

#### Scenario 4: Approval Rejection and Escalation
```
Audit Checklist V1.1:
author02 → submit_for_review → reviewer02 → approve_review →
author02 → route_for_approval → approver01 → reject_approval →
author02 → route_for_approval → senior02 → approve_document
```

### Phase 4: System Validation (`04_validation_and_reporting.spec.js`)
- **Generates comprehensive system reports** with statistics
- **Validates all functionality** is working correctly
- **Creates system backup** of populated data
- **Provides detailed test data summary**

## 🚀 Quick Start

### Prerequisites
```bash
# Ensure EDMS system is running
docker compose up -d

# Verify system accessibility
curl http://localhost:3000  # Frontend
curl http://localhost:8000/health/  # Backend
```

### Run Complete Test Suite
```bash
# Make script executable and run
chmod +x run_edms_tests.sh
./run_edms_tests.sh
```

### Run Individual Test Phases
```bash
# Install Playwright (if needed)
npm install @playwright/test
npx playwright install

# Run specific test phases
npx playwright test tests/01_seed_users.spec.js --headed
npx playwright test tests/02_create_documents.spec.js --headed
npx playwright test tests/03_workflow_testing.spec.js --headed
npx playwright test tests/04_validation_and_reporting.spec.js --headed
```

## 📊 Expected Results

### After Successful Execution:
- **10 Test Users** with proper role assignments and group memberships
- **6 Test Documents** with various types and workflow states
- **4 Completed Workflow Scenarios** demonstrating all major paths
- **System Health Report** with comprehensive statistics
- **Backup Created** for future testing scenarios

### Document Status Distribution:
- **APPROVED_AND_EFFECTIVE**: Quality Policy V1.0, Training Manual V2.0
- **APPROVED**: Safety Procedures V1.0, Audit Checklist V1.1
- **DRAFT**: Emergency Procedures V1.0, Code of Conduct V3.0

### User Credential Summary:
| Username | Password | Role | Groups |
|----------|----------|------|--------|
| author01 | test123 | Author | Document Authors |
| author02 | test123 | Author | Document Authors |
| reviewer01 | test123 | Reviewer | Document Reviewers |
| reviewer02 | test123 | Reviewer | Document Reviewers |
| approver01 | test123 | Approver | Document Approvers |
| approver02 | test123 | Approver | Document Approvers |
| senior01 | test123 | Senior Approver | Senior Document Approvers |
| senior02 | test123 | Senior Approver | Senior Document Approvers |
| viewer01 | test123 | Viewer | - |
| viewer02 | test123 | Viewer | - |

## 🔧 Configuration

### Test Configuration (`playwright_test_suite.js`)
```javascript
const config = {
  baseURL: 'http://localhost:3000',
  timeout: 30000,
  adminCredentials: { username: 'admin', password: 'test123' },
  testDocumentPath: path.join(__dirname, 'test_doc', 'Tikva Quality Policy_template.docx')
};
```

### Playwright Configuration (`playwright.config.js`)
- **Timeout**: 120 seconds per test
- **Retries**: 1 retry on failure
- **Workers**: 1 (sequential execution for workflow dependencies)
- **Screenshots**: On failure
- **Video**: Retained on failure
- **Trace**: On first retry

## 🐛 Troubleshooting

### Common Issues:

#### 1. System Not Available
```bash
# Check if containers are running
docker compose ps

# Start if needed
docker compose up -d

# Check logs
docker compose logs backend
docker compose logs frontend
```

#### 2. Test Document Missing
```bash
# Verify test document exists
ls -la test_doc/Tikva\ Quality\ Policy_template.docx

# If missing, create a dummy document or adjust path in config
```

#### 3. Authentication Failures
```bash
# Verify admin credentials
docker exec edms_backend python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
admin = User.objects.filter(username='admin').first()
print(f'Admin exists: {admin is not None}')
if admin:
    admin.set_password('test123')
    admin.save()
    print('Admin password reset to test123')
"
```

#### 4. Workflow Failures
- **Check user permissions**: Ensure test users have correct group memberships
- **Verify document states**: Documents must be in correct state for workflow actions
- **Check UI selectors**: Frontend changes may require selector updates

## 📁 File Structure

```
playwright_test_suite.js          # Main configuration and test data
run_edms_tests.sh                  # Test execution script
PLAYWRIGHT_TEST_GUIDE.md           # This guide
tests/
  ├── 01_seed_users.spec.js        # User creation and setup
  ├── 02_create_documents.spec.js  # Document creation testing
  ├── 03_workflow_testing.spec.js  # Workflow scenario execution
  └── 04_validation_and_reporting.spec.js # System validation
test-results/                      # Generated test artifacts
playwright-report/                 # HTML test reports
```

## 🎯 Use Cases

### Development Testing
- **Populate clean system** with realistic test data
- **Test new features** against established workflows
- **Validate UI changes** don't break existing functionality

### Demo Preparation
- **Create realistic demo environment** with sample data
- **Showcase workflow capabilities** with real scenarios
- **Demonstrate user role functionality** across different personas

### Regression Testing
- **Validate system functionality** after updates
- **Ensure workflow integrity** across releases
- **Test user management** and permission systems

### Training Environment Setup
- **Prepare training systems** with sample users and documents
- **Create workflow examples** for user training
- **Generate realistic test scenarios** for practice

## 📈 Extending the Tests

### Adding New Users:
```javascript
// In playwright_test_suite.js, add to testUsers array:
{
  username: 'newuser01',
  email: 'newuser01@edms.test',
  firstName: 'New',
  lastName: 'User',
  role: 'reviewer',
  groups: ['Document Reviewers']
}
```

### Adding New Documents:
```javascript
// In testDocuments array:
{
  title: 'New Document Title',
  description: 'Document description',
  documentType: 'SOP',
  department: 'Quality',
  author: 'author01'
}
```

### Adding New Workflow Scenarios:
```javascript
// In workflowScenarios array:
{
  name: 'Custom Workflow Test',
  document: 'Document Title',
  steps: [
    { action: 'submit_for_review', actor: 'author01', reviewer: 'reviewer01' },
    // ... additional steps
  ]
}
```

## 🎉 Success Indicators

After running the complete test suite, you should have:

- ✅ **Populated User Base**: 10 test users across all roles
- ✅ **Document Library**: 6 documents in various workflow states
- ✅ **Workflow History**: Complete audit trail of all workflow actions
- ✅ **System Validation**: Comprehensive health check passed
- ✅ **Backup Created**: System state preserved for future use

## 📞 Support

For issues with the test suite:
1. **Check system logs**: `docker compose logs`
2. **Review test artifacts**: Screenshots and videos in `test-results/`
3. **Check Playwright report**: `npx playwright show-report`
4. **Verify system health**: Run validation tests individually

---

**The EDMS system is now fully populated and ready for development, testing, and demonstration! 🚀**