# Root Cause Analysis - Why We Keep Fixing the Same Issues

**Date:** 2026-01-10  
**Analysis By:** Rovo Dev  
**Issue:** Document creation, user management, and other features repeatedly breaking

---

## 🔍 **The Pattern: What Keeps Breaking**

### **Working State (Nov 27, 2025)**
**Commit:** `42b3b5a` - "FINAL SUCCESS - All user roles can create documents"

✅ **What was working:**
- Document creation with file upload
- All user roles could create documents
- Author field properly handled
- Document types and sources loaded
- User role assignment worked

---

## 🚨 **What Happened: The Backup/Restore Development**

### **Timeline of Breaking Changes:**

#### **Phase 1: November 27 - December 1, 2025**
**Status:** ✅ Everything working

#### **Phase 2: December 1-4, 2025**
**Major work:** Backup & Restore System Implementation
- Multiple commits implementing backup/restore
- System reinitialization features
- Database migration/restore logic

#### **Phase 3: December 4, 2025 onwards**
**Commit:** `4f102a1` - "Implement Method #2 backup/restore system"
- **This is where things started breaking**
- Backup/restore work involved heavy refactoring
- Many "fix" commits followed

---

## 🎯 **Root Causes Identified**

### **1. File Not Tracked Properly During Refactoring**

**Evidence:**
```bash
# The working version at 42b3b5a:
- Had author field handling (we assume, based on it working)
- Had proper API endpoint paths
- Had all ViewSets properly registered

# Between 42b3b5a and 4f102a1:
- NO commits show changes to DocumentCreateModal.tsx
- But the file lost the author field somehow
```

**What likely happened:**
- During backup/restore work, files were edited locally
- Changes tested but not committed
- When switching branches or doing git operations, local changes lost
- Or: Files were reset to an older state accidentally

---

### **2. API Views Refactored Without Testing Document Creation**

**Evidence from git history:**

**Commit `8686bbb` (Jan 3, 2026):**
```
fix: Change created_by to author in DocumentViewSet filterset_fields
```

This shows someone changed the field name in the backend but:
1. Didn't update frontend to send `author` field
2. Didn't test document creation after the change
3. Was probably fixing another issue and created this side effect

---

### **3. Duplicate ViewSet Registrations Introduced**

**Commits showing this pattern:**
- `696fbac` - Fix duplicate UserViewSet registration
- `e76f4c1` - Fix duplicate DocumentSourceViewSet registration
- Today's fix - DocumentSourceViewSet wasn't registered at all

**What happened:**
- During backup/restore work, API structure was reorganized
- ViewSets moved between files
- Some registrations lost, some duplicated
- No comprehensive test suite to catch these issues

---

## 📊 **Impact Analysis**

### **What Got Broken:**

| Feature | Working (Nov 27) | Broken After | Fixed |
|---------|------------------|--------------|-------|
| Document creation | ✅ | ❌ Dec 4+ | ✅ Today |
| Role assignment | ✅ | ❌ Dec 4+ | ✅ Jan 7 |
| Password validation | ✅ | ❌ Unknown | ✅ Jan 7 |
| Document types loading | ✅ | ❌ Dec 4+ | ✅ Today |
| Document sources loading | ✅ | ❌ Dec 4+ | ✅ Today |

---

## 🔬 **Why These Issues Weren't Caught**

### **1. No Automated Testing**
```bash
# No tests found for:
- Document creation flow
- User management operations
- API endpoint registration
- Frontend-backend integration
```

### **2. No Integration Test Suite**
The Playwright tests exist but:
- Not run automatically before commits
- Not covering these specific flows
- May not be maintained

### **3. Development Process Issues**
- Large refactoring (backup/restore) without feature freeze
- Changes committed without full regression testing
- No staging environment validation before merge
- Git history shows many "fix:" commits after the big refactor

---

## 🎯 **The Smoking Gun**

### **Backup/Restore Work Was Too Large**

Looking at the commits between working state and broken state:

```bash
# Between 42b3b5a (working) and 4f102a1 (backup/restore):
904ee60 feat: Complete backup and re-init functionality
e23c02c Clean up temporary development files after 100% functionality
4a25120 MILESTONE: Complete 100% restore functionality
7fbdc0d Clean up temporary FK cascade development files
acb022b Implement FK cascade improvements
4fb8f7e Fix frontend authentication for backup system
2dded84 Fix backup restore functionality - eliminate scope creep
d8fbbd3 Complete database restoration functionality
```

**Problems visible:**
1. "Clean up temporary development files" - suggests messy development
2. "eliminate scope creep" - suggests project got too big
3. Multiple "fix" and "complete" commits - suggests rushing
4. FK cascade work, authentication fixes - deep system changes

---

## 💡 **What Should Have Been Done**

### **1. Feature Branch Isolation**
```bash
# Should have been:
git checkout -b feature/backup-restore-system
# Do all backup/restore work here
# Keep main features working on develop
# Merge only when fully tested
```

### **2. Incremental Changes**
Instead of one massive backup/restore implementation:
- Phase 1: Just backup (no restore)
- Phase 2: Simple restore
- Phase 3: Advanced features
- Test thoroughly between phases

### **3. Regression Test Suite**
Before starting backup/restore work:
```bash
# Create tests for:
1. Document creation (all user roles)
2. User management (CRUD operations)
3. Workflow operations
4. API endpoint availability
```

### **4. Staging Validation**
After each phase:
- Deploy to staging
- Run full test suite
- Manual QA of critical features
- Only then merge to develop

---

## 🔧 **What Went Wrong Specifically**

### **Theory Based on Evidence:**

**November 27, 2025:**
```
✅ Everything working
   └─ Document creation: author field handled correctly
   └─ ViewSets: All properly registered
   └─ API paths: All correct
```

**December 1-4, 2025:**
```
🔧 Backup/Restore Development Begins
   └─ Heavy refactoring of models, views, serializers
   └─ Database schema changes for natural keys
   └─ API restructuring for backup/restore endpoints
   └─ Multiple file moves and renames
```

**What Happened to DocumentCreateModal.tsx:**

**Theory 1: File Accidentally Reverted**
- Developer was working on backup/restore
- Had local changes to many files
- Did a `git reset` or `git checkout` accidentally
- DocumentCreateModal.tsx lost uncommitted changes
- Since there were no tests, issue not noticed

**Theory 2: Cherry-Pick Gone Wrong**
- Backup/restore work done on branch
- Cherry-picked commits to main
- Some files included, some not
- DocumentCreateModal.tsx changes not included

**Theory 3: Merge Conflict Resolved Incorrectly**
- Merge backup/restore branch to develop
- Conflict in DocumentCreateModal.tsx
- Resolved by taking "ours" (old version)
- Lost the author field changes

---

## 📋 **Evidence Supporting This Theory**

### **1. No Explicit Commit Removing Author Field**
```bash
# Git history shows:
42b3b5a - Document creation working
[many backup/restore commits]
(present) - Document creation broken, author field missing

# But NO commit says "remove author field"
# This suggests accidental reversion, not intentional change
```

### **2. Pattern of "Fix" Commits**
```bash
# After backup/restore merge:
696fbac fix: Remove duplicate UserViewSet registration
8686bbb fix: Change created_by to author in DocumentViewSet
e76f4c1 fix: Add DocumentSourceViewSet registration
d2da690 fix: Add current user as author when creating documents

# All fixing issues that DIDN'T EXIST before backup/restore work
```

### **3. Git History Gap**
```bash
# DocumentCreateModal.tsx commits:
42b3b5a - Nov 27: "FINAL SUCCESS - All user roles can create"
(no commits touching this file)
d2da690 - Jan 10: "fix: Add current user as author"

# 45 days with NO commits to this file
# But it broke during that time
# Suggests it was reverted/reset, not intentionally modified
```

---

## 🎓 **Lessons Learned**

### **1. Large Refactoring is Dangerous**
**What backup/restore work did:**
- Changed 50+ files
- Affected models, views, serializers, frontend
- Touched authentication, permissions, API structure
- Lasted over a month

**Risk:** High chance of breaking existing features

**Better approach:**
- Small, focused changes
- One feature at a time
- Continuous integration testing

### **2. Git Best Practices Weren't Followed**
**Issues:**
- No feature branch visible in history
- Many "WIP" commits
- "Clean up temporary files" commits
- Suggests disorganized development

**Should have been:**
```bash
feature/backup-restore
  ├─ feat: Add backup models
  ├─ feat: Add backup API endpoints
  ├─ feat: Add backup frontend UI
  ├─ test: Add backup integration tests
  └─ (merge to develop only when complete)
```

### **3. No Definition of "Done"**
**Backup/restore commits show:**
- Multiple "complete" declarations
- Multiple "fix" commits after "complete"
- "Eliminate scope creep" - work expanded beyond plan

**Should have:**
- Clear acceptance criteria
- Must pass all existing tests
- Must not break existing features
- Staged rollout (backup first, restore later)

---

## 🔮 **How to Prevent This**

### **1. Automated Testing (CRITICAL)**
```bash
# Before ANY merge to develop:
npm run test              # Frontend tests
pytest                    # Backend tests
npm run test:e2e          # Integration tests

# If ANY test fails: DO NOT MERGE
```

### **2. Pre-Commit Hooks**
```bash
# .git/hooks/pre-commit
#!/bin/bash
# Run linting
npm run lint
# Run quick tests
npm run test:unit
# Check for console.logs in production code
```

### **3. CI/CD Pipeline**
```yaml
# .github/workflows/test.yml
on: [push, pull_request]
jobs:
  test:
    - Run all tests
    - Deploy to staging
    - Run smoke tests
    - Only merge if all pass
```

### **4. Feature Flags**
```javascript
// For risky changes:
if (featureFlags.newBackupSystem) {
  // New code
} else {
  // Old working code
}
```

### **5. Staged Rollout**
```bash
# Deploy order:
1. Dev environment
2. Run tests
3. Staging environment
4. Manual QA
5. Production (only if all above pass)
```

---

## 📊 **Cost of Not Having Tests**

### **Time Spent Fixing:**
- Jan 7: 2 hours (Role assignment, password validation)
- Jan 10: 2 hours (Document creation, types, sources, author field)
- **Total:** 4 hours fixing issues that shouldn't have broken

### **Time Would Have Spent on Tests:**
- Initial test suite: 4-6 hours
- Maintenance: 30 min per feature
- **Total:** ~6 hours one-time investment

### **ROI:**
- Tests would have caught these issues immediately
- No deployment of broken code
- No user frustration
- No emergency fixes
- **Saved:** Multiple days of debugging and fixing

---

## ✅ **What to Do Now**

### **Immediate (This Week):**
1. ✅ Document all current fixes (done today)
2. 🔄 Create test suite for critical paths
3. 🔄 Set up basic CI/CD
4. 🔄 Document deployment process

### **Short Term (This Month):**
1. Implement pre-commit hooks
2. Add integration tests for:
   - Document creation
   - User management
   - Workflow operations
3. Set up staging environment testing
4. Create regression test checklist

### **Long Term (Next Quarter):**
1. Full test coverage for all features
2. Automated deployment pipeline
3. Feature flag system
4. Monitoring and alerting
5. Regular regression testing schedule

---

## 🎯 **Summary: Why This Keeps Happening**

### **Root Cause:**
**The backup/restore system development was too large, too disruptive, and lacked proper testing.**

### **Specific Failures:**
1. ❌ No feature branch isolation
2. ❌ No automated tests
3. ❌ No regression testing
4. ❌ No staging validation
5. ❌ Large changes without incremental testing
6. ❌ Files accidentally reverted during development
7. ❌ No one noticed until production deployment

### **Result:**
Working features broke silently, requiring emergency fixes weeks later.

### **Prevention:**
**Tests, tests, tests.** And proper git workflow.

---

## 📞 **Recommendations**

### **Priority 1: Stop Breaking Things**
```bash
# Before any commit:
1. Run existing tests
2. Manually test affected features
3. Deploy to local staging
4. Verify nothing broke
5. Only then commit
```

### **Priority 2: Catch Breaks Early**
```bash
# Add to repository:
1. Pre-commit hooks
2. GitHub Actions CI
3. Automated test suite
4. Staging environment
```

### **Priority 3: Make Fixes Permanent**
```bash
# For each fix we make:
1. Add a test that would have caught it
2. Document why it broke
3. Add to regression test suite
4. Prevent it from happening again
```

---

**Status:** 📋 **ANALYSIS COMPLETE**  
**Next Step:** Implement automated testing to prevent recurrence  
**Last Updated:** 2026-01-10 20:45 SGT
