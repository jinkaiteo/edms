# Comprehensive QA & Testing Plan - EDMS

**Created:** 2026-01-30  
**Version:** 1.0  
**Purpose:** Ensure quality, reliability, and correctness of all EDMS features  

---

## 📊 Current Test Coverage Analysis

### Existing Tests:

**Backend (Python/Django):**
- ✅ ~2,147 lines of test code
- ✅ 5 test directories in apps
- ✅ Tests for:
  - Document dependencies
  - Family grouping & obsolescence
  - Workflow transitions
  - Workflow notifications
  - Scheduler automation
  - Audit trail
  - Termination & versioning workflows

**Frontend (E2E/Integration):**
- ✅ Playwright tests in `e2e/` and `tests/`
- ✅ Tests for:
  - User creation
  - Document workflows
  - System reset
  - Document creation

**Configuration:**
- ✅ pytest configured with coverage reporting
- ✅ Target: 80% code coverage
- ✅ Database reuse for speed

---

## 🎯 QA Strategy

### Three-Layer Testing Approach:

1. **Unit Tests** (Backend) - Test individual functions
2. **Integration Tests** (API) - Test API endpoints
3. **E2E Tests** (Full Stack) - Test user workflows

---

## 🔍 Gap Analysis: What's NOT Tested Yet

### Recently Added Features (Need Tests):

1. **PDF Viewer** ❌
   - View PDF button appears correctly
   - PDF loads and displays
   - Access control (only approved docs)
   - Blob URL creation and cleanup
   - Error handling

2. **Superuser Management** ❌
   - Grant superuser action
   - Revoke superuser action
   - Protection (can't revoke last superuser)
   - UI buttons appear correctly
   - Access control

3. **Dependency Graph Visualization** ❌
   - Graph view renders
   - Tree view renders
   - Arrow directions correct
   - Toggle between views works
   - Performance with large graphs

4. **Modal Responsiveness** ❌
   - Modals fit on screen
   - Scroll works in modals
   - Max-height constraints applied

5. **Header Z-Index Fix** ❌
   - Modals dim header
   - Dropdowns still work

6. **Auto-Copy Dependencies** ❌
   - Dependencies copied on upversion
   - Smart resolution to latest effective
   - Error handling

---

## 📋 Comprehensive Test Plan

### Phase 1: Critical Path Testing (Priority 1)

**Goal:** Ensure core business workflows work flawlessly

#### 1.1 Document Lifecycle
- [ ] Create document (all types)
- [ ] Upload file (DOCX, PDF, various sizes)
- [ ] Submit for review
- [ ] Review document
- [ ] Approve document
- [ ] Set effective date
- [ ] Document becomes effective
- [ ] Download official PDF
- [ ] **NEW:** View PDF in-app
- [ ] Create new version
- [ ] **NEW:** Dependencies auto-copied
- [ ] Mark obsolete
- [ ] Terminate document

#### 1.2 User Management
- [ ] Create user
- [ ] Assign roles
- [ ] **NEW:** Grant superuser
- [ ] **NEW:** Revoke superuser (with protection)
- [ ] **NEW:** Can't revoke last superuser
- [ ] Deactivate user
- [ ] Login/logout
- [ ] Password change

#### 1.3 Dependency Management
- [ ] Add dependency
- [ ] Remove dependency
- [ ] **NEW:** View dependency graph
- [ ] **NEW:** View dependency tree
- [ ] **NEW:** Toggle between views
- [ ] Circular dependency detection
- [ ] Dependency validation

---

### Phase 2: Integration Testing (Priority 2)

**Goal:** Ensure components work together correctly

#### 2.1 Workflow Integration
- [ ] Document → Review → Approval flow
- [ ] Email notifications sent
- [ ] Task creation
- [ ] Workflow history tracked
- [ ] Audit trail created
- [ ] Status updates correctly

#### 2.2 Scheduler Integration
- [ ] Document activation on effective date
- [ ] Obsolescence automation
- [ ] Periodic review scheduling
- [ ] Email reminders

#### 2.3 Backup & Restore
- [ ] **NEW:** Auto-detect compose file
- [ ] Create backup (database + files)
- [ ] Restore from backup
- [ ] Data integrity after restore
- [ ] Permissions preserved

---

### Phase 3: UI/UX Testing (Priority 2)

**Goal:** Ensure excellent user experience

#### 3.1 Visual Testing
- [ ] **NEW:** Modals fit on screen (all sizes)
- [ ] **NEW:** Header dims when modal opens
- [ ] **NEW:** PDF viewer displays correctly
- [ ] Buttons styled consistently
- [ ] Loading states show
- [ ] Error messages clear

#### 3.2 Responsive Testing
- [ ] Desktop (1920x1080)
- [ ] Laptop (1366x768)
- [ ] Tablet (768x1024)
- [ ] Mobile (375x667)

#### 3.3 Browser Compatibility
- [ ] Chrome/Chromium
- [ ] Firefox
- [ ] Edge
- [ ] Safari

---

### Phase 4: Security Testing (Priority 1)

**Goal:** Ensure system is secure

#### 4.1 Authentication
- [ ] Login required for all pages
- [ ] JWT tokens expire correctly
- [ ] Refresh tokens work
- [ ] Logout clears tokens
- [ ] **NEW:** PDF viewer requires auth

#### 4.2 Authorization
- [ ] Role-based access control
- [ ] **NEW:** Only superusers can grant/revoke superuser
- [ ] Document access control
- [ ] Workflow action permissions
- [ ] API endpoint permissions

#### 4.3 Data Protection
- [ ] SQL injection prevention
- [ ] XSS prevention
- [ ] CSRF protection
- [ ] File upload validation
- [ ] **NEW:** PDF blob URLs are temporary

---

### Phase 5: Performance Testing (Priority 3)

**Goal:** Ensure system performs well under load

#### 5.1 Load Testing
- [ ] 10 concurrent users
- [ ] 50 concurrent users
- [ ] 100 concurrent users
- [ ] Response times acceptable

#### 5.2 Data Volume Testing
- [ ] 1,000 documents
- [ ] 10,000 documents
- [ ] Large file uploads (50MB+)
- [ ] **NEW:** Large dependency graphs (100+ nodes)

#### 5.3 Frontend Performance
- [ ] Page load time < 2s
- [ ] Bundle size reasonable
- [ ] **NEW:** PDF viewer loads quickly
- [ ] No memory leaks

---

### Phase 6: Edge Cases & Error Handling (Priority 2)

**Goal:** System handles errors gracefully

#### 6.1 Data Edge Cases
- [ ] Empty fields
- [ ] Special characters in filenames
- [ ] Very long text inputs
- [ ] Duplicate document numbers
- [ ] Invalid file types

#### 6.2 Workflow Edge Cases
- [ ] Reviewer = Approver
- [ ] Self-review attempts
- [ ] Workflow interruption
- [ ] Concurrent edits
- [ ] **NEW:** Upversion with circular dependencies

#### 6.3 Network Edge Cases
- [ ] Slow connection
- [ ] Connection timeout
- [ ] API errors (500, 503)
- [ ] **NEW:** PDF download fails

---

## 🧪 Automated Test Scripts

### Backend Tests (pytest)

**Run all tests:**
```bash
cd backend
docker compose exec backend pytest
```

**Run with coverage:**
```bash
docker compose exec backend pytest --cov=apps --cov-report=html
```

**Run specific test:**
```bash
docker compose exec backend pytest apps/documents/tests/test_document_dependencies.py
```

### Frontend Tests (Playwright)

**Run all E2E tests:**
```bash
npm run test:e2e
```

**Run specific test:**
```bash
npx playwright test tests/01_seed_users.spec.js
```

**Run in headed mode (see browser):**
```bash
npx playwright test --headed
```

---

## ✅ Manual Testing Checklist

### Daily Smoke Test (10 minutes)

Quick verification that core features work:

- [ ] **Login** - Can login as different users
- [ ] **Document List** - Documents load correctly
- [ ] **Create Document** - Can create new document
- [ ] **Upload File** - File uploads successfully
- [ ] **Submit for Review** - Workflow starts
- [ ] **View PDF** - **NEW:** PDF viewer opens
- [ ] **Download** - Files download correctly
- [ ] **Logout** - Can logout successfully

### Weekly Regression Test (30 minutes)

More thorough testing of all features:

**Documents:**
- [ ] Create, edit, delete document
- [ ] Upload different file types
- [ ] Add/remove dependencies
- [ ] **NEW:** View dependency graph
- [ ] Version history displays

**Workflows:**
- [ ] Submit → Review → Approve → Effective
- [ ] Rejection workflow
- [ ] **NEW:** Create new version (dependencies copied)
- [ ] Mark obsolete
- [ ] Terminate

**Users:**
- [ ] Create user with roles
- [ ] Edit user details
- [ ] **NEW:** Grant/revoke superuser
- [ ] Deactivate user

**Admin:**
- [ ] System settings
- [ ] Backup creation
- [ ] **NEW:** Backup auto-detection
- [ ] Scheduler tasks running

---

## 🐛 Bug Tracking & Triage

### Bug Severity Levels:

**Critical (P0):**
- System crash
- Data loss
- Security vulnerability
- Unable to login
- **NEW:** Can't revoke last superuser (prevents lockout)

**High (P1):**
- Major feature broken
- Workflow can't complete
- Data corruption
- **NEW:** PDF viewer doesn't work

**Medium (P2):**
- Minor feature issue
- Workaround available
- UI glitch
- **NEW:** Modal doesn't fit on screen

**Low (P3):**
- Cosmetic issue
- Enhancement request
- Documentation error
- **NEW:** PDF zoom not optimal

### Bug Report Template:

```markdown
**Title:** Brief description

**Severity:** P0/P1/P2/P3

**Steps to Reproduce:**
1. Step one
2. Step two
3. Step three

**Expected Result:**
What should happen

**Actual Result:**
What actually happens

**Environment:**
- Browser: Chrome 120
- OS: Windows 11
- Server: Production/Staging/Local

**Screenshots:**
[Attach if applicable]

**Logs:**
[Paste relevant logs]
```

---

## 📊 Test Coverage Goals

### Current Coverage:
- Backend: Unknown (need to run pytest --cov)
- Frontend: No coverage configured

### Target Coverage:
- Backend: 80% (already configured in pytest.ini)
- Frontend: 70% (need to add jest/vitest)
- E2E: 100% of critical paths

### Areas Needing Coverage:

**Backend:**
- [ ] PDF generation
- [ ] Dependency resolution
- [ ] Superuser management actions
- [ ] Scheduler tasks
- [ ] Backup/restore logic

**Frontend:**
- [ ] PDFViewerSimple component
- [ ] Dependency graph rendering
- [ ] Superuser management UI
- [ ] Modal responsiveness
- [ ] Authentication handling

---

## 🔄 Continuous Testing Strategy

### Pre-Commit:
- Run linters (eslint, pylint)
- Run unit tests for changed files
- Check code coverage

### Pre-Push:
- Run all unit tests
- Run integration tests
- Check overall coverage

### CI/CD Pipeline:
- Run full test suite
- Generate coverage reports
- Deploy only if tests pass

---

## 📝 Test Documentation

### For Each Test:
- Clear test name
- Purpose/goal
- Prerequisites
- Steps
- Expected result
- Cleanup

### Example:
```python
def test_pdf_viewer_requires_authentication():
    """
    Test that PDF viewer endpoint requires authentication.
    
    Prerequisites:
    - Document with status EFFECTIVE exists
    
    Steps:
    1. Attempt to access PDF endpoint without auth token
    2. Verify 401 Unauthorized response
    
    Expected:
    - Endpoint returns 401
    - No PDF data returned
    
    Cleanup:
    - None needed
    """
    response = client.get(f'/documents/{doc.uuid}/download/official/')
    assert response.status_code == 401
```

---

## 🎯 QA Checklist for New Features

**Before merging any new feature:**

- [ ] Unit tests written (backend)
- [ ] Integration tests written (API)
- [ ] E2E tests written (if user-facing)
- [ ] Manual testing completed
- [ ] Edge cases identified and tested
- [ ] Error handling tested
- [ ] Performance tested (if applicable)
- [ ] Security reviewed
- [ ] Documentation updated
- [ ] Code reviewed by peer
- [ ] All tests passing
- [ ] Coverage meets threshold

---

## 📋 Testing Priority Matrix

| Feature | Priority | Tests Needed | Status |
|---------|----------|--------------|--------|
| Document CRUD | P0 | Unit + E2E | ✅ Exists |
| Workflow | P0 | Unit + E2E | ✅ Exists |
| User Auth | P0 | Unit + E2E | ✅ Exists |
| PDF Viewer | P1 | Unit + E2E | ❌ **Missing** |
| Superuser Mgmt | P1 | Unit + E2E | ❌ **Missing** |
| Dependency Graph | P2 | Unit + E2E | ❌ **Missing** |
| Auto-copy Deps | P1 | Unit | ❌ **Missing** |
| Backup/Restore | P1 | Integration | ⚠️ Partial |
| Scheduler | P1 | Unit | ✅ Exists |
| Modal UI | P3 | E2E | ❌ **Missing** |

---

## 🚀 Implementation Plan

### Week 1: High Priority Tests
- [ ] PDF viewer tests (backend + frontend)
- [ ] Superuser management tests
- [ ] Auto-copy dependencies tests
- [ ] Update existing tests for compatibility

### Week 2: Medium Priority Tests
- [ ] Dependency graph visualization tests
- [ ] Enhanced backup/restore tests
- [ ] UI/UX tests for recent changes
- [ ] Browser compatibility tests

### Week 3: Coverage & Reporting
- [ ] Achieve 80% backend coverage
- [ ] Set up frontend coverage (jest/vitest)
- [ ] Generate coverage reports
- [ ] Document test results

### Week 4: Automation & CI/CD
- [ ] Set up GitHub Actions
- [ ] Automated test runs on PR
- [ ] Coverage reports on PR
- [ ] Deployment gating on tests

---

## 📚 Resources

### Testing Tools:
- **pytest** - Backend unit tests
- **pytest-django** - Django integration
- **Playwright** - E2E tests
- **jest/vitest** - Frontend unit tests (to add)
- **coverage.py** - Python coverage
- **istanbul/c8** - JavaScript coverage (to add)

### Documentation:
- [pytest docs](https://docs.pytest.org/)
- [Playwright docs](https://playwright.dev/)
- [Django testing](https://docs.djangoproject.com/en/stable/topics/testing/)

---

## ✅ Success Metrics

**Quality Goals:**
- [ ] 80%+ code coverage (backend)
- [ ] 70%+ code coverage (frontend)
- [ ] 100% critical path coverage
- [ ] < 5 P0/P1 bugs in production
- [ ] All E2E tests passing

**Process Goals:**
- [ ] All PRs have tests
- [ ] Tests run automatically on push
- [ ] Coverage reports generated
- [ ] Bug fix time < 24h (P0/P1)

---

**This QA plan ensures the EDMS system is robust, reliable, and production-ready!**

---

*Created: 2026-01-30*  
*Status: Ready to Implement*  
*Next: Begin Week 1 High Priority Tests*
