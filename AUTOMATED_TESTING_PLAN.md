# Automated Testing Plan for EDMS Workflows

**Date:** 2026-01-10  
**Purpose:** Prevent regression issues by implementing comprehensive automated tests  
**Target:** Document Creation, Review, and Approval workflows

---

## 🎯 **Executive Summary**

### **The Three Critical Workflows:**

1. **Document Creation Workflow**
   - Author creates document
   - Uploads file
   - Sets metadata (type, source, etc.)
   - Submits for review

2. **Document Review Workflow**
   - Reviewer receives notification
   - Reviews document content
   - Approves or rejects
   - Provides comments

3. **Document Approval Workflow**
   - Approver receives notification
   - Final approval decision
   - Sets effective date
   - Document becomes effective

---

## 📊 **Current State Analysis**

### **Existing Tests Found:**

#### **E2E Tests (Playwright):**
```
e2e/document_workflow/01_document_lifecycle.spec.ts
tests/03_workflow_testing.spec.js
tests/workflow.spec.js
```

#### **Issues with Current Tests:**
- ❌ Not run automatically before commits
- ❌ May be outdated (last modified Dec 8)
- ❌ Don't cover all edge cases
- ❌ No backend unit tests found
- ❌ No integration tests for API endpoints

---

## 🏗️ **Testing Strategy Overview**

### **Three-Layer Testing Approach:**

```
┌─────────────────────────────────────────────────┐
│  Layer 1: Unit Tests (Backend + Frontend)      │
│  - Test individual functions                    │
│  - Fast, isolated                               │
│  - 80% coverage target                          │
└─────────────────────────────────────────────────┘
           ↓
┌─────────────────────────────────────────────────┐
│  Layer 2: Integration Tests (API)              │
│  - Test API endpoints                           │
│  - Database interactions                        │
│  - 100% critical path coverage                  │
└─────────────────────────────────────────────────┘
           ↓
┌─────────────────────────────────────────────────┐
│  Layer 3: E2E Tests (Playwright)               │
│  - Test complete workflows                      │
│  - Browser automation                           │
│  - User perspective                             │
└─────────────────────────────────────────────────┘
```

---

## 📝 **Part 1 Complete - See remaining parts in subsequent messages**


### **Workflow 2: Document Review Tests**

#### **File:** `backend/apps/workflows/tests/test_review_workflow.py`

**What to test:**
1. ✅ Submit document for review
2. ✅ Only author can submit
3. ✅ Status changes from DRAFT to UNDER_REVIEW
4. ✅ Reviewer receives notification
5. ✅ Reviewer can approve
6. ✅ Reviewer can reject with comments
7. ✅ Non-reviewer cannot approve/reject
8. ✅ Author cannot review their own document

**Test Example:**
```python
@pytest.mark.django_db
class TestReviewWorkflow:
    
    def setup_method(self):
        """Setup test data"""
        self.client = APIClient()
        
        # Create users
        self.author = User.objects.create_user(
            username='author01',
            password='test123'
        )
        self.reviewer = User.objects.create_user(
            username='reviewer01',
            password='test123'
        )
        
        # Assign reviewer role
        reviewer_role = Role.objects.get(name='Document Reviewer')
        UserRole.objects.create(
            user=self.reviewer,
            role=reviewer_role,
            is_active=True
        )
        
        # Create document
        self.document = Document.objects.create(
            title='Test Document',
            author=self.author,
            status='DRAFT'
        )
    
    def test_submit_for_review_success(self):
        """Test author can submit document for review"""
        self.client.force_authenticate(user=self.author)
        
        response = self.client.post(
            f'/api/v1/documents/{self.document.id}/submit_for_review/',
            {'reviewer_id': self.reviewer.id}
        )
        
        assert response.status_code == 200
        
        # Verify status changed
        self.document.refresh_from_db()
        assert self.document.status == 'UNDER_REVIEW'
        
        # Verify workflow created
        workflow = self.document.workflows.first()
        assert workflow is not None
        assert workflow.current_state.code == 'UNDER_REVIEW'
    
    def test_non_author_cannot_submit(self):
        """Test only author can submit for review"""
        self.client.force_authenticate(user=self.reviewer)
        
        response = self.client.post(
            f'/api/v1/documents/{self.document.id}/submit_for_review/',
            {'reviewer_id': self.reviewer.id}
        )
        
        assert response.status_code == 403
    
    def test_reviewer_can_approve(self):
        """Test reviewer can approve document"""
        # Submit for review first
        self.document.status = 'UNDER_REVIEW'
        self.document.save()
        
        # Create workflow
        workflow = DocumentWorkflow.objects.create(
            document=self.document,
            initiated_by=self.author
        )
        
        # Reviewer approves
        self.client.force_authenticate(user=self.reviewer)
        
        response = self.client.post(
            f'/api/v1/documents/{self.document.id}/review/',
            {
                'action': 'approve',
                'comment': 'Looks good'
            }
        )
        
        assert response.status_code == 200
        
        # Verify status changed
        self.document.refresh_from_db()
        assert self.document.status == 'REVIEWED'
    
    def test_reviewer_can_reject(self):
        """Test reviewer can reject document"""
        self.document.status = 'UNDER_REVIEW'
        self.document.save()
        
        self.client.force_authenticate(user=self.reviewer)
        
        response = self.client.post(
            f'/api/v1/documents/{self.document.id}/review/',
            {
                'action': 'reject',
                'comment': 'Needs revision'
            }
        )
        
        assert response.status_code == 200
        
        # Verify status changed back to DRAFT
        self.document.refresh_from_db()
        assert self.document.status == 'DRAFT'
    
    def test_author_cannot_review_own_document(self):
        """Test author cannot review their own document"""
        self.document.status = 'UNDER_REVIEW'
        self.document.save()
        
        # Author tries to review their own document
        self.client.force_authenticate(user=self.author)
        
        response = self.client.post(
            f'/api/v1/documents/{self.document.id}/review/',
            {
                'action': 'approve',
                'comment': 'I approve my own work'
            }
        )
        
        assert response.status_code == 403
        assert 'cannot review your own document' in response.data['detail'].lower()
```


## 🔧 **Layer 1: Backend Unit Tests (pytest)**

### **Test Structure:**

```
backend/apps/
├── documents/
│   └── tests/
│       ├── test_models.py
│       ├── test_views.py
│       ├── test_serializers.py
│       └── test_permissions.py
├── workflows/
│   └── tests/
│       ├── test_workflow_models.py
│       ├── test_workflow_transitions.py
│       └── test_workflow_permissions.py
└── users/
    └── tests/
        ├── test_user_models.py
        ├── test_roles.py
        └── test_permissions.py
```

### **Workflow 1: Document Creation Tests**

#### **File:** `backend/apps/documents/tests/test_document_creation.py`

**What to test:**
1. ✅ Create document with all required fields
2. ✅ Author field automatically set to current user
3. ✅ Document type validation
4. ✅ Document source validation
5. ✅ File upload validation
6. ✅ Default status is DRAFT
7. ✅ Version number starts at 1.0
8. ✅ Permissions (only authors can create)

**Test Example:**
```python
import pytest
from django.contrib.auth import get_user_model
from apps.documents.models import Document, DocumentType, DocumentSource
from rest_framework.test import APIClient

User = get_user_model()

@pytest.mark.django_db
class TestDocumentCreation:
    
    def setup_method(self):
        """Setup test data before each test"""
        self.client = APIClient()
        self.author = User.objects.create_user(
            username='author01',
            password='test123'
        )
        self.doc_type = DocumentType.objects.create(
            code='SOP',
            name='Standard Operating Procedure'
        )
        self.doc_source = DocumentSource.objects.create(
            name='Original Digital Draft'
        )
    
    def test_create_document_success(self):
        """Test successful document creation"""
        self.client.force_authenticate(user=self.author)
        
        data = {
            'title': 'Test SOP Document',
            'description': 'Test description',
            'document_type': self.doc_type.id,
            'document_source': self.doc_source.id,
            'author': self.author.id
        }
        
        response = self.client.post('/api/v1/documents/', data)
        
        assert response.status_code == 201
        assert response.data['title'] == 'Test SOP Document'
        assert response.data['author'] == self.author.id
        assert response.data['status'] == 'DRAFT'
        assert response.data['version'] == '1.0'
    
    def test_create_document_missing_author(self):
        """Test document creation fails without author"""
        self.client.force_authenticate(user=self.author)
        
        data = {
            'title': 'Test SOP Document',
            'document_type': self.doc_type.id,
            'document_source': self.doc_source.id,
            # Missing author field
        }
        
        response = self.client.post('/api/v1/documents/', data)
        
        assert response.status_code == 400
        assert 'author' in response.data
    
    def test_create_document_invalid_type(self):
        """Test document creation fails with invalid type"""
        self.client.force_authenticate(user=self.author)
        
        data = {
            'title': 'Test Document',
            'document_type': 9999,  # Non-existent
            'document_source': self.doc_source.id,
            'author': self.author.id
        }
        
        response = self.client.post('/api/v1/documents/', data)
        
        assert response.status_code == 400
    
    def test_create_document_without_authentication(self):
        """Test document creation requires authentication"""
        data = {
            'title': 'Test Document',
            'document_type': self.doc_type.id,
            'document_source': self.doc_source.id
        }
        
        response = self.client.post('/api/v1/documents/', data)
        
        assert response.status_code == 401
```


### **Workflow 3: Document Approval Tests**

#### **File:** `backend/apps/workflows/tests/test_approval_workflow.py`

**What to test:**
1. ✅ Submit reviewed document for approval
2. ✅ Only reviewers/authors can submit for approval
3. ✅ Status changes to APPROVED
4. ✅ Approver receives notification
5. ✅ Approver can approve with effective date
6. ✅ Approver can reject
7. ✅ Non-approver cannot approve
8. ✅ Document becomes EFFECTIVE on effective date

**Test Example:**
```python
@pytest.mark.django_db
class TestApprovalWorkflow:
    
    def setup_method(self):
        """Setup test data"""
        self.client = APIClient()
        
        # Create users
        self.author = User.objects.create_user(username='author01', password='test123')
        self.reviewer = User.objects.create_user(username='reviewer01', password='test123')
        self.approver = User.objects.create_user(username='approver01', password='test123')
        
        # Assign roles
        approver_role = Role.objects.get(name='Document Approver')
        UserRole.objects.create(user=self.approver, role=approver_role, is_active=True)
        
        # Create reviewed document
        self.document = Document.objects.create(
            title='Test Document',
            author=self.author,
            status='REVIEWED'
        )
    
    def test_approver_can_approve_document(self):
        """Test approver can approve document and set effective date"""
        self.client.force_authenticate(user=self.approver)
        
        from datetime import date, timedelta
        effective_date = date.today() + timedelta(days=7)
        
        response = self.client.post(
            f'/api/v1/documents/{self.document.id}/approve/',
            {
                'action': 'approve',
                'effective_date': effective_date.isoformat(),
                'comment': 'Approved for implementation'
            }
        )
        
        assert response.status_code == 200
        
        # Verify status changed
        self.document.refresh_from_db()
        assert self.document.status == 'APPROVED_PENDING_EFFECTIVE'
        assert self.document.effective_date == effective_date
    
    def test_approver_can_reject_document(self):
        """Test approver can reject document"""
        self.client.force_authenticate(user=self.approver)
        
        response = self.client.post(
            f'/api/v1/documents/{self.document.id}/approve/',
            {
                'action': 'reject',
                'comment': 'Does not meet requirements'
            }
        )
        
        assert response.status_code == 200
        
        # Verify status changed back to DRAFT
        self.document.refresh_from_db()
        assert self.document.status == 'DRAFT'
    
    def test_non_approver_cannot_approve(self):
        """Test non-approver cannot approve document"""
        self.client.force_authenticate(user=self.reviewer)
        
        response = self.client.post(
            f'/api/v1/documents/{self.document.id}/approve/',
            {'action': 'approve'}
        )
        
        assert response.status_code == 403
    
    def test_document_becomes_effective_on_date(self):
        """Test document automatically becomes effective on effective date"""
        from datetime import date
        
        # Approve with today as effective date
        self.document.status = 'APPROVED_PENDING_EFFECTIVE'
        self.document.effective_date = date.today()
        self.document.save()
        
        # Run scheduler task
        from apps.scheduler.tasks import activate_pending_documents
        activate_pending_documents()
        
        # Verify document is now effective
        self.document.refresh_from_db()
        assert self.document.status == 'EFFECTIVE'
```

---

## 🔧 **Layer 2: API Integration Tests**

### **Purpose:**
Test complete API endpoints with database interactions, ensuring frontend-backend contract is maintained.

#### **File:** `backend/apps/api/tests/test_document_api_integration.py`

**What to test:**
1. ✅ All API endpoints exist (404 prevention)
2. ✅ Response format matches frontend expectations
3. ✅ Pagination works correctly
4. ✅ Filtering works correctly
5. ✅ Serializer field names match frontend
6. ✅ ViewSet actions registered correctly

**Test Example:**
```python
@pytest.mark.django_db
class TestDocumentAPIIntegration:
    
    def test_document_types_endpoint_exists(self):
        """Test /api/v1/document-types/ endpoint exists"""
        client = APIClient()
        response = client.get('/api/v1/document-types/')
        
        assert response.status_code in [200, 401]  # Not 404!
    
    def test_document_sources_endpoint_exists(self):
        """Test /api/v1/document-sources/ endpoint exists"""
        client = APIClient()
        response = client.get('/api/v1/document-sources/')
        
        assert response.status_code in [200, 401]  # Not 404!
    
    def test_user_assign_role_endpoint_exists(self):
        """Test /api/v1/users/{id}/assign_role/ endpoint exists"""
        client = APIClient()
        user = User.objects.create_user(username='test', password='test')
        
        response = client.post(f'/api/v1/users/{user.id}/assign_role/', {})
        
        assert response.status_code in [400, 401, 403]  # Not 404!
    
    def test_document_response_format(self):
        """Test document API returns expected field names"""
        client = APIClient()
        author = User.objects.create_user(username='author', password='test')
        client.force_authenticate(user=author)
        
        doc = Document.objects.create(
            title='Test',
            author=author
        )
        
        response = client.get(f'/api/v1/documents/{doc.id}/')
        
        assert response.status_code == 200
        
        # Verify frontend-expected fields exist
        required_fields = ['id', 'title', 'author', 'status', 'document_type', 'document_source']
        for field in required_fields:
            assert field in response.data, f"Missing field: {field}"
```

---

## 🌐 **Layer 3: End-to-End Tests (Playwright)**

### **Purpose:**
Test complete workflows from user perspective, ensuring UI, API, and database work together.

#### **File:** `e2e/workflows/complete_document_workflow.spec.ts`

**What to test:**
1. ✅ Complete document lifecycle (create → review → approve → effective)
2. ✅ All three user roles (author, reviewer, approver)
3. ✅ Browser UI interactions
4. ✅ Error messages displayed correctly
5. ✅ Success notifications shown

**Test Example:**
```typescript
import { test, expect } from '@playwright/test';

test.describe('Complete Document Workflow', () => {
  
  test('Full workflow: Create → Review → Approve → Effective', async ({ page, browser }) => {
    
    // === PART 1: Author Creates Document ===
    await page.goto('http://localhost:3001');
    await page.fill('[name="username"]', 'author01');
    await page.fill('[name="password"]', 'test123');
    await page.click('button[type="submit"]');
    
    // Navigate to documents
    await page.click('text=Documents');
    await page.click('button:has-text("Create Document")');
    
    // Fill form
    await page.fill('[name="title"]', 'Test SOP-001');
    await page.fill('[name="description"]', 'Test workflow document');
    await page.selectOption('[name="document_type"]', { label: 'SOP' });
    await page.selectOption('[name="document_source"]', { label: 'Original Digital Draft' });
    
    // Upload file
    const fileInput = await page.locator('input[type="file"]');
    await fileInput.setInputFiles('test_doc/test_document.docx');
    
    // Submit
    await page.click('button:has-text("Create")');
    
    // Verify success
    await expect(page.locator('text=Document created successfully')).toBeVisible();
    
    // Get document ID from URL or response
    const documentId = await page.evaluate(() => {
      return document.querySelector('[data-document-id]')?.getAttribute('data-document-id');
    });
    
    // === PART 2: Author Submits for Review ===
    await page.click(`button:has-text("Submit for Review")`);
    await page.selectOption('[name="reviewer"]', { label: 'reviewer01' });
    await page.click('button:has-text("Submit")');
    
    await expect(page.locator('text=Submitted for review')).toBeVisible();
    
    // Logout
    await page.click('button:has-text("Logout")');
    
    // === PART 3: Reviewer Reviews Document ===
    // Login as reviewer
    await page.fill('[name="username"]', 'reviewer01');
    await page.fill('[name="password"]', 'test123');
    await page.click('button[type="submit"]');
    
    // Go to My Tasks
    await page.click('text=My Tasks');
    
    // Find document in review queue
    await page.click(`text=Test SOP-001`);
    
    // Review
    await page.click('button:has-text("Approve")');
    await page.fill('[name="comment"]', 'Document reviewed and approved');
    await page.click('button:has-text("Confirm")');
    
    await expect(page.locator('text=Document approved')).toBeVisible();
    
    // Logout
    await page.click('button:has-text("Logout")');
    
    // === PART 4: Approver Approves Document ===
    // Login as approver
    await page.fill('[name="username"]', 'approver01');
    await page.fill('[name="password"]', 'test123');
    await page.click('button[type="submit"]');
    
    // Go to My Tasks
    await page.click('text=My Tasks');
    
    // Find document in approval queue
    await page.click(`text=Test SOP-001`);
    
    // Approve with effective date
    await page.click('button:has-text("Approve")');
    
    // Set effective date (7 days from now)
    const futureDate = new Date();
    futureDate.setDate(futureDate.getDate() + 7);
    await page.fill('[name="effective_date"]', futureDate.toISOString().split('T')[0]);
    
    await page.fill('[name="comment"]', 'Final approval granted');
    await page.click('button:has-text("Confirm")');
    
    await expect(page.locator('text=Document approved')).toBeVisible();
    
    // Verify document status is APPROVED_PENDING_EFFECTIVE
    await page.click('text=Documents');
    await page.click(`text=Test SOP-001`);
    
    await expect(page.locator('text=APPROVED_PENDING_EFFECTIVE')).toBeVisible();
  });
  
  test('Reject document at review stage', async ({ page }) => {
    // Setup: Create document and submit for review
    // ... (similar setup as above)
    
    // Login as reviewer
    await page.goto('http://localhost:3001');
    await page.fill('[name="username"]', 'reviewer01');
    await page.fill('[name="password"]', 'test123');
    await page.click('button[type="submit"]');
    
    // Review and reject
    await page.click('text=My Tasks');
    await page.click('text=Test Document');
    await page.click('button:has-text("Reject")');
    await page.fill('[name="comment"]', 'Needs revision - incorrect procedure');
    await page.click('button:has-text("Confirm")');
    
    // Verify rejection
    await expect(page.locator('text=Document rejected')).toBeVisible();
    
    // Verify document back in DRAFT status
    await page.click('text=Documents');
    await expect(page.locator('text=DRAFT')).toBeVisible();
  });
});
```


---

## 🚀 **Implementation Plan**

### **Phase 1: Backend Unit Tests (Week 1)**

**Days 1-2: Setup Testing Infrastructure**
```bash
# Install dependencies
pip install pytest pytest-django pytest-cov factory-boy

# Create pytest.ini configuration
# backend/pytest.ini
[pytest]
DJANGO_SETTINGS_MODULE = edms.settings.test
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = --verbose --cov=apps --cov-report=html --cov-report=term
testpaths = apps
```

**Days 3-4: Write Document Creation Tests**
- Create `apps/documents/tests/test_document_creation.py`
- 10-15 test cases covering all scenarios
- Target: 80% coverage of document creation

**Days 5-7: Write Workflow Tests**
- Create `apps/workflows/tests/test_review_workflow.py`
- Create `apps/workflows/tests/test_approval_workflow.py`
- 20-25 test cases covering complete workflows
- Target: 90% coverage of workflow operations

**Deliverable:** 35+ backend unit tests, 85% code coverage

---

### **Phase 2: API Integration Tests (Week 2)**

**Days 1-2: Endpoint Existence Tests**
```python
# Create apps/api/tests/test_endpoints_exist.py

CRITICAL_ENDPOINTS = [
    '/api/v1/documents/',
    '/api/v1/document-types/',
    '/api/v1/document-sources/',
    '/api/v1/users/',
    '/api/v1/users/{id}/assign_role/',
    '/api/v1/users/{id}/remove_role/',
]

@pytest.mark.django_db
class TestCriticalEndpointsExist:
    def test_all_endpoints_exist(self):
        """Ensure no 404 errors on critical endpoints"""
        client = APIClient()
        for endpoint in CRITICAL_ENDPOINTS:
            response = client.get(endpoint)
            assert response.status_code != 404, f"404 Not Found: {endpoint}"
```

**Days 3-5: Response Format Tests**
- Test serializer output matches frontend expectations
- Test pagination format
- Test error response format
- 15-20 integration tests

**Deliverable:** 20+ API integration tests

---

### **Phase 3: E2E Tests Enhancement (Week 3)**

**Days 1-2: Update Existing Tests**
- Review existing Playwright tests
- Update outdated tests
- Fix broken test scenarios

**Days 3-5: Add Missing Scenarios**
- Complete workflow with file upload
- Rejection scenarios at each stage
- Permission denial scenarios
- Edge cases (concurrent edits, etc.)

**Deliverable:** 10+ E2E test scenarios covering all workflows

---

### **Phase 4: CI/CD Integration (Week 4)**

**Days 1-2: GitHub Actions Setup**

Create `.github/workflows/test.yml`:
```yaml
name: EDMS Test Suite

on:
  push:
    branches: [ develop, main ]
  pull_request:
    branches: [ develop, main ]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:18
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r backend/requirements/test.txt
      
      - name: Run Backend Tests
        run: |
          cd backend
          pytest --cov --cov-report=xml
      
      - name: Upload Coverage
        uses: codecov/codecov-action@v3
  
  frontend-tests:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Node
        uses: actions/setup-node@v3
        with:
          node-version: '18'
      
      - name: Install dependencies
        run: |
          cd frontend
          npm ci
      
      - name: Run Frontend Tests
        run: |
          cd frontend
          npm test
  
  e2e-tests:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Start Docker Services
        run: |
          docker-compose up -d
          sleep 30
      
      - name: Run E2E Tests
        run: |
          npx playwright test
      
      - name: Upload Test Results
        if: failure()
        uses: actions/upload-artifact@v3
        with:
          name: playwright-report
          path: playwright-report/
```

**Days 3-4: Pre-commit Hooks**

Create `.pre-commit-config.yaml`:
```yaml
repos:
  - repo: local
    hooks:
      - id: pytest-check
        name: pytest-check
        entry: bash -c 'cd backend && pytest apps/documents/tests/test_document_creation.py -v'
        language: system
        pass_filenames: false
        always_run: true
      
      - id: eslint
        name: eslint
        entry: bash -c 'cd frontend && npm run lint'
        language: system
        pass_filenames: false
        always_run: true
```

**Day 5: Documentation**
- Update README with testing instructions
- Create TESTING.md guide
- Document test conventions

**Deliverable:** Automated CI/CD pipeline

---

## 📊 **Test Coverage Targets**

### **By Component:**

| Component | Unit Tests | Integration Tests | E2E Tests | Target Coverage |
|-----------|-----------|------------------|-----------|----------------|
| Document Creation | 15 | 5 | 3 | 90% |
| Review Workflow | 12 | 4 | 3 | 85% |
| Approval Workflow | 12 | 4 | 3 | 85% |
| User Management | 10 | 3 | 2 | 80% |
| API Endpoints | 5 | 15 | 0 | 100% existence |
| **TOTAL** | **54** | **31** | **11** | **85% overall** |

---

## 🛠️ **Tools and Technologies**

### **Backend Testing:**
- **pytest** - Test framework
- **pytest-django** - Django integration
- **factory-boy** - Test data factories
- **pytest-cov** - Coverage reports
- **faker** - Fake data generation

### **Frontend Testing:**
- **Jest** - Unit test framework
- **React Testing Library** - Component tests
- **Playwright** - E2E tests
- **TypeScript** - Type safety

### **CI/CD:**
- **GitHub Actions** - Automation
- **Docker** - Environment consistency
- **codecov** - Coverage tracking
- **pre-commit** - Git hooks

---

## ✅ **Success Criteria**

### **Tests Must:**
1. ✅ Run in under 5 minutes (total)
2. ✅ Pass 100% before any merge
3. ✅ Cover all three workflows completely
4. ✅ Catch the issues we fixed today (regression)
5. ✅ Be maintainable (clear, documented)
6. ✅ Run automatically on every commit
7. ✅ Provide clear failure messages

### **Code Coverage:**
- ✅ Overall: 85%+
- ✅ Critical paths: 95%+
- ✅ New code: 90%+

---

## 🔒 **Preventing Future Regressions**

### **The Tests Will Catch:**

1. **Document Creation Issues:**
   - ✅ Missing author field → `test_create_document_missing_author` FAILS
   - ✅ Wrong API paths → `test_endpoints_exist` FAILS
   - ✅ ViewSet not registered → `test_document_types_endpoint_exists` FAILS

2. **User Management Issues:**
   - ✅ Duplicate ViewSets → `test_user_assign_role_endpoint_exists` FAILS
   - ✅ Permission errors → `test_non_approver_cannot_approve` FAILS

3. **Workflow Issues:**
   - ✅ Status not changing → `test_submit_for_review_success` FAILS
   - ✅ Wrong user roles → `test_author_cannot_review_own_document` FAILS

### **If Tests Pass:**
- ✅ All endpoints exist (no 404s)
- ✅ All workflows function correctly
- ✅ All permissions enforced
- ✅ All data validated
- ✅ Safe to deploy

---

## 📅 **Timeline Summary**

| Week | Focus | Deliverables |
|------|-------|-------------|
| Week 1 | Backend Unit Tests | 35+ unit tests, 85% coverage |
| Week 2 | API Integration Tests | 20+ integration tests |
| Week 3 | E2E Test Enhancement | 10+ E2E scenarios |
| Week 4 | CI/CD Integration | Automated pipeline + hooks |

**Total Time:** 4 weeks  
**Total Tests:** 65+ automated tests  
**ROI:** Prevents hours of debugging per incident

---

## 💰 **Cost-Benefit Analysis**

### **Investment:**
- **Initial:** 4 weeks of development
- **Maintenance:** 1-2 hours per new feature
- **Running:** Automated, ~5 minutes per commit

### **Returns:**
- **Prevented Issues:** Unlimited (every commit validated)
- **Debugging Time Saved:** 2-4 hours per prevented issue
- **Deployment Confidence:** High
- **User Impact:** Zero (no broken deployments)

### **Break-Even:**
After preventing just 10-15 issues, the test suite pays for itself.

---

## 🎯 **Quick Start (This Week)**

### **Day 1: Start Now**
```bash
# 1. Create test structure
mkdir -p backend/apps/documents/tests
mkdir -p backend/apps/workflows/tests
mkdir -p backend/apps/api/tests

# 2. Install pytest
pip install pytest pytest-django pytest-cov

# 3. Create first test
cat > backend/apps/documents/tests/test_document_creation.py << 'PYTEST'
import pytest
from apps.documents.models import Document

@pytest.mark.django_db
def test_document_creation_requires_author():
    """Regression test for the issue we fixed today"""
    # This test would have caught the missing author field!
    from rest_framework.test import APIClient
    from django.contrib.auth import get_user_model
    
    User = get_user_model()
    client = APIClient()
    author = User.objects.create_user(username='test', password='test')
    client.force_authenticate(user=author)
    
    # Try to create without author field
    response = client.post('/api/v1/documents/', {
        'title': 'Test',
        # Missing 'author' field
    })
    
    # Should fail with 400
    assert response.status_code == 400
    assert 'author' in response.data
PYTEST

# 4. Run it
cd backend
pytest apps/documents/tests/test_document_creation.py -v
```

**Expected Output:**
```
PASSED test_document_creation_requires_author ✓
```

### **Day 2-3: Add More Tests**
Add 5-10 more critical tests covering the issues we fixed.

### **Day 4-5: Set Up CI**
Add GitHub Actions workflow.

---

## 📚 **Resources**

### **Documentation:**
- [pytest Documentation](https://docs.pytest.org/)
- [Playwright Documentation](https://playwright.dev/)
- [Django Testing](https://docs.djangoproject.com/en/4.2/topics/testing/)
- [GitHub Actions](https://docs.github.com/actions)

### **Examples:**
- Existing tests in `tests/` directory
- E2E tests in `e2e/` directory
- This plan document

---

## ✨ **Summary**

### **What We're Building:**
A comprehensive automated test suite that:
1. Catches issues before they reach production
2. Runs automatically on every commit
3. Covers all three critical workflows
4. Prevents the regressions we experienced
5. Takes only 5 minutes to run

### **How It Prevents Issues:**
- **Before commit:** Pre-commit hooks catch obvious errors
- **On push:** GitHub Actions runs full test suite
- **Before merge:** All tests must pass
- **Before deploy:** Final validation on staging

### **Why It's Worth It:**
- **Today's issues:** 4+ hours of debugging
- **With tests:** Would be caught in 5 minutes
- **ROI:** Massive (prevents multiple incidents)

---

**Status:** 📋 **PLAN COMPLETE**  
**Ready to implement:** ✅ YES  
**Estimated time:** 4 weeks  
**Expected impact:** Prevents 90% of regressions  

**Last Updated:** 2026-01-10 21:15 SGT
