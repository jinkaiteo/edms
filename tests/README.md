# 🎯 EDMS Playwright Test Suite

## Overview
Comprehensive Playwright test automation framework for the Enterprise Document Management System (EDMS). The test suite provides both legacy compatibility and enhanced testing capabilities with improved reliability, validation, and reporting.

## 📁 Test Structure

### Core Test Files (Legacy)
- `01_seed_users.spec.js` - User creation and role assignment
- `02_create_documents.spec.js` - Document management testing  
- `03_workflow_testing.spec.js` - Basic workflow scenarios
- `04_validation_and_reporting.spec.js` - System validation
- `workflow.spec.js` - Comprehensive E2E workflow testing
- `api_seed_users.spec.js` - API-based user seeding
- `author02-user-creation.spec.js` - Focused user creation testing

### Enhanced Test Suite (`tests/enhanced/`)
- `01_enhanced_user_seeding.spec.js` - Advanced user management with validation
- `02_enhanced_workflow_testing.spec.js` - Comprehensive workflow scenarios with API validation
- `03_enhanced_validation_testing.spec.js` - System health, security, and performance testing

### Helper Modules (`tests/helpers/`)
- `page-objects.js` - Page Object Models for UI interactions
- `test-utils.js` - Common utilities and validation helpers
- `test-data.js` - Centralized test data and configuration

## 🚀 Quick Start

### Prerequisites
```bash
# Ensure EDMS system is running
docker compose up -d

# Install Playwright (if not already installed)
npm install -g @playwright/test
playwright install
```

### Running Tests

#### Enhanced Test Suite (Recommended)
```bash
# Complete enhanced test suite
./run_enhanced_tests.sh

# Quick core functionality test
./run_enhanced_tests.sh fast

# Validation and security tests only
./run_enhanced_tests.sh validation

# Workflow testing only
./run_enhanced_tests.sh workflows

# Cross-browser compatibility
./run_enhanced_tests.sh cross-browser
```

#### Legacy Test Suite
```bash
# Complete legacy test suite
./run_edms_tests.sh

# Individual legacy tests
npm run test:seed-users
npm run test:create-docs
npm run test:workflows
npm run test:validate
```

#### Individual Enhanced Tests
```bash
# Enhanced user seeding
npm run test:enhanced-users

# Enhanced workflow testing
npm run test:enhanced-workflows

# System validation
npm run test:enhanced-validation
```

#### Specialized Testing
```bash
# API validation only
npm run test:api-validation

# Security testing only
npm run test:security

# Performance testing only
npm run test:performance

# Cross-browser testing
npm run test:cross-browser
```

## 🎛️ Configuration

### Playwright Configuration (`playwright.config.js`)
- **Browser Support**: Chromium, Firefox, WebKit
- **Test Directory**: `./tests`
- **Timeouts**: Action (10s), Navigation (30s)
- **Debugging**: Screenshots on failure, video recording, trace collection
- **Parallel Execution**: Disabled for data integrity

### Test Configuration (`tests/helpers/test-data.js`)
- **Base URLs**: Frontend (localhost:3000), Backend (localhost:8000)
- **Test Users**: 10 users across different roles
- **Test Documents**: 5 different document types
- **Workflow Scenarios**: 4 comprehensive workflow paths
- **Validation Rules**: Input validation and business logic rules

## 🧪 Test Coverage

### ✅ User Management
- User creation with role assignment
- Group membership validation
- Permission testing
- Error handling for invalid inputs
- API-level user verification

### ✅ Document Management
- Document creation across multiple types
- File upload validation
- Document state management
- CRUD operation testing
- API response validation

### ✅ Workflow Testing
- Complete document lifecycle scenarios:
  - Standard Review and Approval
  - Review Rejection and Resubmission
  - Senior Approval Escalation
  - Approval Rejection and Executive Escalation
- State transition validation
- Role-based workflow permissions
- Reviewer/Approver assignment testing

### ✅ System Validation
- Health check validation
- API endpoint testing
- Cross-browser compatibility
- Security and permission validation
- Performance metrics collection
- Error handling and recovery testing
- Data integrity validation

## 📊 Test Data

### Test Users
- **Authors**: author01, author02 (Document Authors group)
- **Reviewers**: reviewer01, reviewer02 (Document Reviewers group)
- **Approvers**: approver01, approver02 (Document Approvers group)
- **Senior Approvers**: senior01, senior02 (Senior Document Approvers group)
- **Viewers**: viewer01, viewer02 (No special groups)

All test users use password: `test123`

### Test Documents
- Quality Management System Policy V2.0 (POL)
- Workplace Safety Procedures V1.5 (PROC)
- Employee Training and Development Manual V3.0 (MAN)
- Internal Audit Checklist and Guidelines V2.1 (FORM)
- Document Control Procedures V1.0 (PROC)

## 🔧 Debugging

### Screenshots and Videos
- Automatic screenshots on test failure
- Video recording for failed tests
- Debug screenshots at key workflow steps
- Files saved to `test-results/`

### Trace Collection
- Playwright traces collected on retry
- View traces: `npx playwright show-trace trace.zip`

### Debug Mode
```bash
# Debug mode (step-by-step execution)
npm run test:debug

# UI mode (interactive testing)
npm run test:ui

# Headed mode (visible browser)
npm run test:headed
```

### Logging
- Detailed console logging for each test step
- API response validation logging
- Performance metrics logging
- Error state capture and reporting

## 📈 Reports

### HTML Reports
```bash
# View test results
npx playwright show-report
```

### Console Reports
- Real-time test execution progress
- Pass/fail status for each test
- Performance metrics
- Error summaries

### Test Artifacts
- **Location**: `test-results/` and `playwright-report/`
- **Contents**: Screenshots, videos, traces, debug logs
- **Format**: HTML, JSON, images, videos

## 🎯 Best Practices

### Page Object Pattern
Tests use Page Object Models for:
- Centralized selector management
- Reusable UI interactions
- Improved test maintenance
- Consistent error handling

### Test Data Management
- Centralized test data in `test-data.js`
- Environment-specific configuration
- Validation rules for input data
- API endpoint definitions

### Error Handling
- Graceful failure handling
- Comprehensive error logging
- Debug screenshot capture
- Retry mechanisms with backoff

### Validation Strategy
- Multi-level validation (UI + API)
- State verification after actions
- Data integrity checks
- Performance monitoring

## 🚨 Troubleshooting

### Common Issues

#### Modal Detection Timeout
```javascript
// If modal selectors timeout, update in page-objects.js
this.modalSelectors = [
  '[data-testid="submit-review-modal"]',
  '[role="dialog"]',
  '.modal-dialog',
  // Add your specific modal selectors
];
```

#### Authentication Issues
- Verify admin credentials in `test-data.js`
- Check if CSRF tokens are required
- Validate session persistence

#### Test Data Conflicts
- Use unique test data per run
- Implement cleanup procedures
- Check for existing test users/documents

#### Performance Issues
- Adjust timeouts in `playwright.config.js`
- Check system resources
- Monitor network latency

### Getting Help

1. **Check test logs** in console output
2. **Review screenshots** in `test-results/`
3. **Examine HTML report** with `npx playwright show-report`
4. **Run individual tests** for isolation debugging
5. **Use debug mode** for step-by-step execution

## 📋 Test Execution Checklist

### Before Running Tests
- ✅ EDMS system is running (`docker compose up -d`)
- ✅ Frontend accessible at http://localhost:3000
- ✅ Backend accessible at http://localhost:8000
- ✅ Playwright browsers installed (`playwright install`)
- ✅ Test data directory exists (`test_doc/`)

### After Running Tests
- ✅ Review HTML test report
- ✅ Check for any failed tests
- ✅ Validate test data was created correctly
- ✅ Clean up test artifacts if needed
- ✅ Document any issues found

## 🎉 Success Metrics

A successful test run should show:
- **User Creation**: 10 test users created with appropriate roles
- **Document Management**: Documents created and managed successfully
- **Workflow Testing**: All workflow scenarios completed
- **System Validation**: All health checks passed
- **Security Testing**: Permission controls validated
- **Performance**: Response times within acceptable limits

---

**The enhanced test suite provides comprehensive validation of EDMS functionality with professional-grade testing infrastructure and reporting.**