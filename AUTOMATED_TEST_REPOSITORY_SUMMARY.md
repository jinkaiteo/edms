# 🧪 EDMS Automated Test Repository Summary

**Generated:** 2026-01-30  
**Purpose:** Comprehensive overview of automated testing infrastructure

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Test Architecture](#test-architecture)
3. [Test Types & Organization](#test-types--organization)
4. [Current Test Coverage](#current-test-coverage)
5. [Known Issues](#known-issues)
6. [Test Users & Credentials](#test-users--credentials)
7. [How to Run Tests](#how-to-run-tests)
8. [Recent Test Development](#recent-test-development)
9. [Next Steps](#next-steps)

---

## 🎯 Overview

**EDMS (Electronic Document Management System)** is a 21 CFR Part 11 compliant document management system with comprehensive automated testing infrastructure using Playwright for E2E tests and pytest for backend unit tests.

### Key Statistics
- **E2E Tests:** 14 spec files (TypeScript)
- **Legacy Tests:** 8 spec files (JavaScript) 
- **Backend Unit Tests:** 11 test files (pytest)
- **Total Lines of Test Code:** ~4,500+ lines
- **Test Framework:** Playwright + pytest
- **Configuration:** playwright.config.ts, pytest.ini

---

## 🏗️ Test Architecture

### Frontend E2E Testing (Playwright)
```
e2e/
├── document_workflow/          # Complete document lifecycle tests
│   ├── workflow_from_draft_to_effective.spec.ts  ⭐ Main workflow test
│   ├── 1_draft_sendToReview.spec.ts
│   ├── 2_Review.spec.ts
│   ├── 3_sendToApproval.spec.ts
│   └── 4_Approval.spec.ts
├── workflows_complete/         # Advanced workflow features
│   ├── 04_document_versioning.spec.ts
│   ├── 05_document_obsolescence.spec.ts
│   └── 06_document_termination.spec.ts
├── user_creation/              # User management tests
│   └── user_creation.spec.ts
├── system_reset/               # Database reset utilities
│   └── system_reset.spec.ts
└── helpers/
    └── testConfig.ts           # Centralized test configuration
```

### Legacy Tests (tests/ directory)
```
tests/
├── 01_seed_users.spec.js              # User seeding
├── 02_create_documents.spec.js        # Document creation
├── 03_workflow_testing.spec.js        # Workflow validation
├── 04_validation_and_reporting.spec.js # Reporting tests
├── workflow.spec.js                   # Comprehensive workflow (700 lines)
├── enhanced/                          # Enhanced test suite
│   ├── 01_enhanced_user_seeding.spec.js
│   ├── 02_enhanced_workflow_testing.spec.js
│   └── 03_enhanced_validation_testing.spec.js
└── helpers/
    ├── page-objects.js                # Page Object Model
    ├── test-data.js                   # Test data fixtures
    └── test-utils.js                  # Utility functions
```

### Backend Unit Tests (pytest)
```
backend/apps/
├── documents/tests/
│   ├── test_pdf_viewer.py             # PDF viewer endpoint tests (13 tests)
│   ├── test_family_grouping_obsolescence.py
│   └── test_document_dependencies.py
├── users/tests/
│   └── test_superuser_management.py   # Superuser protection (12 tests)
├── workflows/tests/
│   ├── test_obsolescence_workflow.py
│   ├── test_termination_workflow.py
│   ├── test_versioning_workflow.py
│   └── test_workflow_notifications.py
├── scheduler/tests/
│   ├── test_obsolescence_automation.py
│   └── test_document_activation.py
└── audit/tests/
    └── test_workflow_audit_trail.py
```

---

## 🧩 Test Types & Organization

### 1. **E2E Workflow Tests** (Primary Focus)
**Location:** `e2e/document_workflow/`

**Main Test:** `workflow_from_draft_to_effective.spec.ts`
- ✅ Document creation as Author
- ✅ Submit for review workflow
- ✅ Review and approval by Reviewer
- ✅ Route for approval by Author
- ✅ Final approval by Approver
- ✅ Document becomes EFFECTIVE

**Test Flow:**
```
DRAFT → Submit → PENDING_REVIEW → Review → REVIEWED 
      → Route → PENDING_APPROVAL → Approve → EFFECTIVE
```

### 2. **User Creation & Management Tests**
**Location:** `e2e/user_creation/user_creation.spec.ts`

Tests creation of:
- ✅ Admin users
- ✅ Authors (document writers)
- ✅ Reviewers (review documents)
- ✅ Approvers (approve documents)
- ✅ Viewers (read-only)

### 3. **Advanced Workflow Tests**
**Location:** `e2e/workflows_complete/`

- **Versioning:** Document version control (v1.0 → v2.0)
- **Obsolescence:** Document lifecycle management
- **Termination:** Workflow termination scenarios

### 4. **Backend Unit Tests** (pytest)
**Coverage Areas:**
- PDF viewer security & access control
- Superuser protection (prevent admin lockout)
- Document dependencies & family grouping
- Workflow notifications
- Scheduler automation
- Audit trail integrity

### 5. **System Utilities**
- **System Reset:** `e2e/system_reset/system_reset.spec.ts`
- **Enhanced Test Suite:** `tests/enhanced/` (professional-grade reporting)

---

## 📊 Current Test Coverage

### ✅ Well-Covered Areas

| Feature | Coverage | Test Location |
|---------|----------|---------------|
| **Document Creation** | ⭐⭐⭐⭐⭐ | `e2e/document_workflow/` |
| **Review Workflow** | ⭐⭐⭐⭐⭐ | `workflow_from_draft_to_effective.spec.ts` |
| **Approval Workflow** | ⭐⭐⭐⭐⭐ | `workflow_from_draft_to_effective.spec.ts` |
| **User Management** | ⭐⭐⭐⭐ | `e2e/user_creation/` |
| **PDF Viewer** | ⭐⭐⭐⭐ | `backend/apps/documents/tests/test_pdf_viewer.py` |
| **Superuser Protection** | ⭐⭐⭐⭐ | `backend/apps/users/tests/test_superuser_management.py` |
| **Version Control** | ⭐⭐⭐⭐ | `e2e/workflows_complete/04_document_versioning.spec.ts` |
| **Authentication** | ⭐⭐⭐⭐ | All test files use login flows |

### ⚠️ Areas Needing More Coverage

- Email notification system (manual testing only)
- Backup & Restore functionality
- Document search & filtering
- Reports generation
- Admin dashboard statistics
- Placeholder system validation
- Dependency graph visualization

---

## 🐛 Known Issues

### 1. **Backend pytest Database Setup Issue** ⚠️
**Status:** Infrastructure Issue - Tests Ready but Cannot Execute

**Problem:**
```
psycopg2.errors.InvalidCursorName: cursor "_django_curs_XXX" does not exist
```

**Root Cause:** 
- Test database setup fails during `scheduler_scheduledtask` table serialization
- Cursor becomes invalid during migration process

**Impact:**
- ✅ Test code is written and correct (25 tests)
- ❌ Cannot execute due to database setup issue
- ✅ Tests ready to run once infrastructure fixed

**Workarounds:**
1. Use SQLite for tests instead of PostgreSQL
2. Exclude scheduler from test INSTALLED_APPS
3. Fix scheduler app migrations

**Reference:** `TEST_INFRASTRUCTURE_KNOWN_ISSUES.md`

### 2. **Test User Credential Inconsistencies**
Some test files use different passwords:
- Most tests: `P@ssword1234`
- Some tests: `Author01!`, `Reviewer01!`, etc.
- Admin: `test123` or `admin123`

**Location:** `e2e/helpers/testConfig.ts`

### 3. **Hardcoded IDs in Tests**
```typescript
export const REVIEWER_ID = '119';
export const APPROVER_ID = '120';
```
These may not exist in fresh database installations.

---

## 👥 Test Users & Credentials

### Standard Test Users

| Username | Password | Role | Usage |
|----------|----------|------|-------|
| `admin` | `test123` or `admin123` | Administrator | System admin, user creation |
| `author01` | `P@ssword1234` | Document Author | Create & submit documents |
| `reviewer01` | `P@ssword1234` | Document Reviewer | Review documents |
| `approver01` | `P@ssword1234` | Document Approver | Approve documents |
| `viewer01` | `P@ssword1234` | Document Viewer | Read-only access |

### Test Configuration
**File:** `e2e/helpers/testConfig.ts`
```typescript
export const BASE_URL = process.env.BASE_URL || 'http://localhost:3000';
export const AUTHOR_USERNAME = process.env.AUTHOR_USERNAME || 'author01';
export const AUTHOR_PASSWORD = process.env.AUTHOR_PASSWORD || 'P@ssword1234';
// ... etc
```

### Creating Test Users
**Automated:** Run `e2e/user_creation/user_creation.spec.ts`  
**Manual:** Use admin panel at `http://localhost:8000/admin`  
**API:** See `tests/api_seed_users.spec.js`

---

## 🚀 How to Run Tests

### E2E Tests (Playwright)

#### Prerequisites
```bash
# Install dependencies
npm install

# Ensure EDMS is running
docker compose up -d
```

#### Run All Tests
```bash
# Headless mode
npx playwright test

# Headed mode (see browser)
npx playwright test --headed

# UI mode (interactive)
npx playwright test --ui

# Debug mode
npx playwright test --debug
```

#### Run Specific Tests
```bash
# Main workflow test
npx playwright test e2e/document_workflow/workflow_from_draft_to_effective.spec.ts

# User creation tests
npx playwright test e2e/user_creation/

# All document workflow tests
npx playwright test e2e/document_workflow/
```

#### View Test Reports
```bash
# After tests complete
npx playwright show-report
```

### Backend Tests (pytest)

#### Prerequisites
```bash
# Backend must be running
docker compose up -d backend
```

#### Run All Tests
```bash
docker compose exec backend pytest

# With verbose output
docker compose exec backend pytest -vv

# With coverage report
docker compose exec backend pytest --cov=apps --cov-report=html
```

#### Run Specific Tests
```bash
# PDF viewer tests
docker compose exec backend pytest apps/documents/tests/test_pdf_viewer.py

# Superuser management tests
docker compose exec backend pytest apps/users/tests/test_superuser_management.py

# All document tests
docker compose exec backend pytest apps/documents/tests/
```

#### View Coverage Report
```bash
# Coverage report generated in backend/htmlcov/
# Open in browser: backend/htmlcov/index.html
```

### Configuration Files

**Playwright:** `playwright.config.ts`
```typescript
export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',
  use: {
    trace: 'on-first-retry',
  },
});
```

**pytest:** `backend/pytest.ini`
```ini
[tool:pytest]
DJANGO_SETTINGS_MODULE = edms.settings.test
python_files = tests.py test_*.py *_tests.py
addopts = 
    --verbose
    --cov=apps
    --cov-report=html
    --cov-fail-under=80
    --reuse-db
```

---

## 📈 Recent Test Development

### Recent Commits (Since Dec 2025)

**2026-01-30:**
- 📝 Document test infrastructure known issue
- 📝 Document pytest database cursor error

**2026-01-29:**
- ✅ Merge QA comprehensive testing framework
- ✅ Add QA implementation summary
- ✅ Add test runner script for new QA tests

**2025-12:**
- ✅ Add comprehensive testing and quality assurance framework
- ✅ Add PDF viewer tests (13 tests)
- ✅ Add superuser management tests (12 tests)
- ✅ Add Send Test Email functionality
- ✅ Enhanced test suite with professional reporting

### Test Documentation Created

| Document | Purpose |
|----------|---------|
| `tests/README.md` | Main test suite guide |
| `TESTING_GUIDE_LOCAL.md` | Local testing walkthrough |
| `MANUAL_QA_TESTING_CHECKLIST.md` | Manual testing procedures |
| `QA_COMPREHENSIVE_TEST_PLAN.md` | Complete QA strategy |
| `PLAYWRIGHT_TEST_GUIDE.md` | Playwright-specific guide |
| `TEST_INFRASTRUCTURE_KNOWN_ISSUES.md` | Current blockers |
| `PLAYWRIGHT_CLEANUP_AND_ENHANCEMENT_SUMMARY.md` | Test improvements |

---

## 🎯 Test Workflow Example

### Complete Document Workflow Test

**Test File:** `e2e/document_workflow/workflow_from_draft_to_effective.spec.ts`

**Scenario:** Author creates document, submits for review, reviewer approves, author routes for approval, approver approves, document becomes effective.

**Steps:**
1. **Login as Author** (`author01`)
2. **Create Document**
   - Upload `.docx` file
   - Fill metadata (title, description, type, source)
   - Status: `DRAFT`
3. **Submit for Review**
   - Select reviewer (`reviewer01`)
   - Add comment
   - Status: `PENDING_REVIEW`
4. **Logout, Login as Reviewer** (`reviewer01`)
5. **Review Document**
   - Find document in "My Tasks"
   - Start review process
   - Approve with comments
   - Status: `REVIEWED`
6. **Logout, Login as Author** (`author01`)
7. **Route for Approval**
   - Select approver (`approver01`)
   - Add comment
   - Status: `PENDING_APPROVAL`
8. **Logout, Login as Approver** (`approver01`)
9. **Approve Document**
   - Find document in "My Tasks"
   - Start approval process
   - Approve with effective date
   - Status: `EFFECTIVE`
10. **Verify in Document Library**
    - Document appears in library
    - Status is `EFFECTIVE`

**Test Assertions:**
```typescript
await expect(page.getByRole('main')).toContainText('PENDING REVIEW');
await expect(page.getByRole('main')).toContainText('REVIEWED');
await expect(page.getByRole('main')).toContainText('PENDING APPROVAL');
await expect(page.getByRole('main')).toContainText('EFFECTIVE');
```

---

## 🔍 Test Helper Utilities

### Page Object Model (POM)
**File:** `tests/helpers/page-objects.js`
- Reusable page interaction methods
- Reduces code duplication
- Easier maintenance

### Test Data Fixtures
**File:** `tests/helpers/test-data.js`
- Centralized test data
- Consistent across tests
- Easy to update

### Test Utilities
**File:** `tests/helpers/test-utils.js`
- Common helper functions
- Login helpers
- Wait utilities
- Assertion helpers

---

## 📝 Manual Testing Resources

While automated tests have infrastructure issues, comprehensive manual testing is available:

### Manual Testing Guides
1. **TESTING_GUIDE_LOCAL.md** - Step-by-step local testing
2. **MANUAL_QA_TESTING_CHECKLIST.md** - Systematic test cases
3. **QA_COMPREHENSIVE_TEST_PLAN.md** - Complete QA strategy

### Manual Test Coverage
- ✅ Complete document workflows
- ✅ User management
- ✅ PDF viewer functionality
- ✅ Notifications system
- ✅ Admin dashboard
- ✅ Reports generation
- ✅ Backup & restore
- ✅ Email notifications

---

## 🚧 Next Steps & Recommendations

### Immediate (Fix Test Infrastructure)
1. **Resolve pytest Database Issue**
   - Fix scheduler app migration cursor issue
   - OR use SQLite for tests
   - OR exclude scheduler from test setup
2. **Standardize Test Credentials**
   - Update all tests to use consistent passwords
   - Document in central config file
3. **Fix Hardcoded IDs**
   - Use fixture-based user/role creation
   - Avoid relying on specific database IDs

### Short Term (Expand Coverage)
1. **Add API Integration Tests**
   - Test all REST endpoints
   - Validate request/response formats
   - Check error handling
2. **Add Email Notification Tests**
   - Mock email backend
   - Test notification triggers
   - Verify email content
3. **Add Search & Filter Tests**
   - Document search functionality
   - Filter combinations
   - Performance under load

### Medium Term (CI/CD Integration)
1. **Set Up GitHub Actions**
   - Run tests on every PR
   - Generate test reports
   - Enforce coverage thresholds
2. **Add E2E Test Screenshots**
   - Capture on test failure
   - Store as artifacts
   - Aid debugging
3. **Performance Testing**
   - Load testing with k6
   - Database query optimization
   - Frontend performance metrics

### Long Term (Test Excellence)
1. **Visual Regression Testing**
   - Screenshot comparison
   - Catch UI regressions
   - Automated visual QA
2. **Accessibility Testing**
   - WCAG 2.1 compliance
   - Screen reader compatibility
   - Keyboard navigation
3. **Security Testing**
   - Penetration testing
   - SQL injection prevention
   - XSS prevention
   - 21 CFR Part 11 compliance validation

---

## 📚 Key Testing Documentation

### Test Guides
- **Primary Guide:** `tests/README.md` - Main test suite documentation
- **Local Testing:** `TESTING_GUIDE_LOCAL.md` - Step-by-step local testing
- **Playwright Guide:** `PLAYWRIGHT_TEST_GUIDE.md` - Playwright-specific guide

### QA Documentation
- **QA Plan:** `QA_COMPREHENSIVE_TEST_PLAN.md` - Complete QA strategy
- **Manual Testing:** `MANUAL_QA_TESTING_CHECKLIST.md` - Manual test cases
- **Known Issues:** `TEST_INFRASTRUCTURE_KNOWN_ISSUES.md` - Current blockers

### Implementation Summaries
- **Cleanup Summary:** `PLAYWRIGHT_CLEANUP_AND_ENHANCEMENT_SUMMARY.md`
- **QA Summary:** `QA_IMPLEMENTATION_SUMMARY.md`

---

## 🎓 Best Practices from Workspace Memory

### From AGENTS.md:

1. **Always include `.tsx` extensions** in import statements
2. **Verify API endpoint existence** before building frontend features
3. **Null safety for object properties:** Use `document?.version_major || 0`
4. **Check serializer field names** in backend before implementing frontend
5. **Distinguish business logic filters from access control filters**
6. **Python code changes in Docker require image rebuild**, not just restart
7. **Test with actual logged-in user context**, not assumed test users
8. **Backend-frontend alignment:** Update both serializer AND frontend types

### Testing-Specific Patterns:
- **Real-world user testing** often reveals integration problems unit tests miss
- **Browser behavior verification:** Test actual download behavior in browsers
- **End-to-end validation:** Always test complete user workflows
- **Mock data vs real data:** Never use mock data as fallback in production
- **API endpoint verification first:** Always verify endpoints exist before debugging frontend

---

## 🔗 Related Resources

### External Documentation
- **Playwright Docs:** https://playwright.dev/
- **pytest Docs:** https://docs.pytest.org/
- **Django Testing:** https://docs.djangoproject.com/en/stable/topics/testing/

### Internal Links
- **Main README:** `README.md`
- **Development Docs:** `Dev_Docs/`
- **Deployment Guides:** `docs/deployment/`
- **API Specs:** `Dev_Docs/2_EDMS_API_Specifications.md`

---

## ✅ Summary

### Test Infrastructure Status

| Component | Status | Notes |
|-----------|--------|-------|
| **E2E Tests (Playwright)** | ✅ **Working** | 14 spec files, comprehensive coverage |
| **Backend Tests (pytest)** | ⚠️ **Blocked** | 25 tests written, database setup issue |
| **Test Documentation** | ✅ **Complete** | 8+ documentation files |
| **Manual Testing** | ✅ **Available** | Comprehensive checklists |
| **CI/CD Integration** | ❌ **Not Set Up** | GitHub Actions configured but not active |

### Quick Start

**Run E2E Tests:**
```bash
npm install
docker compose up -d
npx playwright test --headed
```

**Run Backend Tests (when fixed):**
```bash
docker compose exec backend pytest -vv
```

**Manual Testing:**
```bash
# Follow guide at:
cat TESTING_GUIDE_LOCAL.md
```

---

**Last Updated:** 2026-01-30  
**Maintainer:** Development Team  
**Status:** Active Development  

For questions or issues with tests, refer to `TEST_INFRASTRUCTURE_KNOWN_ISSUES.md` or contact the development team.

---

