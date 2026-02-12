# Sensitivity Label System - Rollback Plan

## Overview

This document provides step-by-step procedures for rolling back the sensitivity label system in case of critical issues during or after deployment.

---

## When to Rollback

Consider rollback if:
- ❌ Migration fails and cannot be fixed
- ❌ Critical application errors after deployment
- ❌ Data integrity issues detected
- ❌ Performance degradation (>50% slower)
- ❌ Blocking bugs affecting document workflows
- ❌ Security vulnerabilities discovered

**DO NOT rollback for:**
- ✅ Minor UI issues (can be fixed with hotfix)
- ✅ Training-related issues
- ✅ User confusion (address with documentation)
- ✅ Non-critical bugs

---

## Rollback Levels

### Level 1: Disable Watermarks Only (Least Impact)
### Level 2: Revert Frontend Changes (Moderate Impact)
### Level 3: Revert Backend Code Changes (High Impact)
### Level 4: Revert Database Migration (Highest Impact)

---

## Level 1: Disable Watermarks Only

**When to use:** Watermark rendering causing performance issues or visual problems

**Impact:** Low - Documents still have sensitivity labels, just no watermarks on PDFs

**Time:** 2 minutes

**Steps:**

```bash
# 1. Disable watermarks in settings
docker-compose exec -T backend python manage.py shell << 'PYEOF'
from django.conf import settings

# Option A: Edit settings.py directly
# Add to settings/base.py or settings/production.py:
# OFFICIAL_PDF_CONFIG = {'PDF_WATERMARK': False}

print("Add to settings.py:")
print("OFFICIAL_PDF_CONFIG = {'PDF_WATERMARK': False}")
PYEOF

# 2. Restart backend
docker-compose restart backend

# 3. Verify watermarks disabled
docker-compose exec -T backend python manage.py shell << 'PYEOF'
from django.conf import settings
config = getattr(settings, 'OFFICIAL_PDF_CONFIG', {})
print(f"Watermarks enabled: {config.get('PDF_WATERMARK', True)}")
PYEOF
```

**Verification:**
- [ ] Backend restarted successfully
- [ ] PDFs download without watermarks
- [ ] Application still functional

**Restore:**
```bash
# Re-enable watermarks
# Edit settings.py: OFFICIAL_PDF_CONFIG = {'PDF_WATERMARK': True}
docker-compose restart backend
```

---

## Level 2: Revert Frontend Changes

**When to use:** Frontend sensitivity UI causing issues, but backend is stable

**Impact:** Medium - Users cannot select sensitivity during approval, but existing labels preserved

**Time:** 10 minutes

**Steps:**

```bash
# 1. Checkout previous frontend commit
cd frontend

# Find commit before sensitivity changes
git log --oneline -20

# Revert to previous commit (replace COMMIT_HASH)
git checkout <COMMIT_HASH> src/components/workflows/ApproverInterface.tsx
git checkout <COMMIT_HASH> src/components/workflows/UnifiedWorkflowInterface.tsx

# 2. Remove new components (if causing issues)
git rm src/components/common/SensitivityBadge.tsx
git rm src/components/workflows/SensitivityLabelSelector.tsx

# 3. Rebuild frontend
npm run build

# 4. Restart frontend container
cd ..
docker-compose restart frontend

# 5. Verify
# - Frontend loads without errors
# - Approval workflow works (without sensitivity selector)
```

**Verification:**
- [ ] Frontend builds successfully
- [ ] No JavaScript errors in browser console
- [ ] Approval workflow functional
- [ ] Document list displays correctly

**Note:** Backend still has sensitivity labels, but frontend doesn't show/edit them

**Restore:**
```bash
cd frontend
git checkout develop  # or your main branch
npm run build
cd ..
docker-compose restart frontend
```

---

## Level 3: Revert Backend Code Changes

**When to use:** Backend code causing critical errors, but database is stable

**Impact:** High - Sensitivity features disabled, but data preserved

**Time:** 15 minutes

**Steps:**

```bash
# 1. Backup current state
git stash save "sensitivity-label-backup"

# 2. Revert code changes
git log --oneline --all -30 | grep -i sensitivity

# Find commits to revert
git revert <COMMIT_HASH>  # Revert each sensitivity-related commit

# OR checkout specific files
git checkout <PREVIOUS_COMMIT> backend/apps/documents/annotation_processor.py
git checkout <PREVIOUS_COMMIT> backend/apps/documents/services/pdf_generator.py
git checkout <PREVIOUS_COMMIT> backend/apps/workflows/document_lifecycle.py
git checkout <PREVIOUS_COMMIT> backend/apps/workflows/views.py
git checkout <PREVIOUS_COMMIT> backend/apps/documents/serializers.py

# 3. Remove new files
rm backend/apps/documents/sensitivity_labels.py
rm backend/apps/documents/watermark_processor.py
rm backend/apps/documents/access_control.py

# 4. Restart backend
docker-compose restart backend

# 5. Verify
docker-compose exec backend python manage.py check
```

**Verification:**
- [ ] Backend starts without errors
- [ ] Django check passes
- [ ] Document workflows functional
- [ ] No import errors

**Important:** Database still has sensitivity columns, but they're not used

**Restore:**
```bash
git stash pop  # Restore backed up changes
# OR
git checkout develop
docker-compose restart backend
```

---

## Level 4: Revert Database Migration (Full Rollback)

**When to use:** Database corruption, data integrity issues, or complete rollback needed

**Impact:** Critical - All sensitivity data will be lost

**Time:** 30 minutes

**Prerequisites:**
- Database backup exists
- Confirmed decision to rollback
- Maintenance window scheduled

**Steps:**

### Option A: Rollback Migration (Preferred)

```bash
# 1. Find migration number
docker-compose exec -T backend python manage.py showmigrations documents

# Output will show:
# documents
#  [X] 0001_initial
#  [X] 0002_add_sensitivity_labels  ← Target to rollback

# 2. Rollback to previous migration
docker-compose exec -T backend python manage.py migrate documents 0001_initial

# This will:
# - Remove sensitivity_* columns
# - Remove indexes
# - Preserve all other document data

# 3. Remove migration file
rm backend/apps/documents/migrations/0002_add_sensitivity_labels.py

# 4. Restart services
docker-compose restart backend

# 5. Verify
docker-compose exec -T backend python manage.py shell << 'PYEOF'
from django.db import connection
cursor = connection.cursor()
cursor.execute("""
    SELECT column_name 
    FROM information_schema.columns 
    WHERE table_name='documents_document' 
    AND column_name LIKE 'sensitivity%';
""")
columns = cursor.fetchall()
print(f"Sensitivity columns remaining: {len(columns)}")
if len(columns) == 0:
    print("✓ Migration rolled back successfully")
else:
    print("✗ Some sensitivity columns remain")
PYEOF
```

### Option B: Restore from Backup (If migration rollback fails)

```bash
# 1. Stop services
docker-compose down

# 2. Restore database from backup
# Find your backup file: backup_before_sensitivity_YYYYMMDD_HHMMSS.json

# 3. Start database only
docker-compose up -d db
sleep 5

# 4. Restore data
docker-compose run --rm backend python manage.py flush --noinput
docker-compose run --rm backend python manage.py loaddata backup_before_sensitivity_YYYYMMDD_HHMMSS.json

# 5. Start all services
docker-compose up -d

# 6. Verify
docker-compose exec backend python manage.py check
```

**Verification:**
- [ ] Migration rolled back
- [ ] No sensitivity columns in database
- [ ] Document data intact
- [ ] Application functional

**Data Loss:**
- ❌ All sensitivity labels lost
- ❌ Sensitivity change history lost
- ✅ All documents preserved
- ✅ All workflows preserved

---

## Emergency Rollback (Complete System)

**When to use:** Complete system failure, data corruption

**Time:** 45 minutes

**Steps:**

```bash
# 1. Stop all services
docker-compose down

# 2. Checkout previous working commit
git log --oneline -50
git checkout <WORKING_COMMIT>

# 3. Restore database
docker-compose up -d db
sleep 10

docker-compose run --rm backend python manage.py flush --noinput
docker-compose run --rm backend python manage.py loaddata backup_before_sensitivity_YYYYMMDD_HHMMSS.json

# 4. Start all services
docker-compose up -d

# 5. Verify entire system
bash scripts/check-backend-health.sh

# 6. Test critical workflows
# - Document creation
# - Document review
# - Document approval
# - Document download
```

---

## Post-Rollback Actions

### Immediate Actions (Within 1 hour)
- [ ] Notify all users of rollback
- [ ] Document reason for rollback
- [ ] Test critical workflows
- [ ] Verify data integrity
- [ ] Check system health

### Short-term Actions (Within 24 hours)
- [ ] Conduct root cause analysis
- [ ] Fix identified issues
- [ ] Update test suite
- [ ] Plan redeployment

### Long-term Actions (Within 1 week)
- [ ] Prepare fixed version
- [ ] Test in staging environment
- [ ] Create detailed deployment plan
- [ ] Schedule new deployment

---

## Rollback Verification Checklist

After any rollback level, verify:

### Application Health
- [ ] Backend starts without errors
- [ ] Frontend loads correctly
- [ ] Database accessible
- [ ] No Python import errors
- [ ] No JavaScript console errors

### Core Functionality
- [ ] Create new document
- [ ] Upload document file
- [ ] Submit for review
- [ ] Review document
- [ ] Approve document
- [ ] Download document
- [ ] Search documents
- [ ] View document list

### Data Integrity
- [ ] All documents still exist
- [ ] Document counts match pre-deployment
- [ ] User accounts intact
- [ ] Workflow history preserved
- [ ] Audit trail complete

### Performance
- [ ] Page load times normal
- [ ] API response times <500ms
- [ ] PDF generation <3 seconds
- [ ] Search responsive

---

## Prevention for Future Deployments

### Before Deployment
- [ ] Test in staging environment
- [ ] Complete regression testing
- [ ] Performance benchmarking
- [ ] Database backup verified
- [ ] Rollback plan reviewed
- [ ] Team trained on rollback

### During Deployment
- [ ] Deploy during maintenance window
- [ ] Monitor logs in real-time
- [ ] Test after each phase
- [ ] Have rollback team ready

### After Deployment
- [ ] Monitor system for 24 hours
- [ ] Gradual user rollout
- [ ] Collect user feedback
- [ ] Performance monitoring
- [ ] Error rate tracking

---

## Contact Information

**Emergency Contacts:**
- Tech Lead: [Contact]
- DevOps Lead: [Contact]
- Database Admin: [Contact]
- QA Lead: [Contact]

**Escalation Path:**
1. Development Team
2. Tech Lead
3. Engineering Manager
4. CTO

---

## Rollback Decision Matrix

| Severity | Examples | Recommended Action | Approval Required |
|----------|----------|-------------------|-------------------|
| **Critical** | System down, data corruption | Level 4 (Full rollback) | CTO |
| **High** | Major feature broken, security issue | Level 3 (Backend revert) | Tech Lead |
| **Medium** | UI issues, minor bugs | Level 2 (Frontend revert) | Dev Lead |
| **Low** | Visual glitches, performance | Level 1 (Disable watermarks) | Dev Team |

---

## Testing After Rollback

Run comprehensive tests after rollback:

```bash
# 1. Backend health check
bash scripts/check-backend-health.sh

# 2. Database integrity check
docker-compose exec backend python manage.py check

# 3. Run automated tests
cd backend
pytest tests/

# 4. Frontend tests
cd frontend
npm test

# 5. End-to-end tests
npx playwright test
```

---

## Lessons Learned Template

After rollback, document:

**What went wrong:**
- [Description of issue]

**Root cause:**
- [Technical root cause]

**Impact:**
- [User impact]
- [Data impact]
- [Business impact]

**Resolution:**
- [What was done]

**Prevention:**
- [How to prevent in future]

**Action items:**
- [ ] Fix issue
- [ ] Update tests
- [ ] Improve deployment process
- [ ] Train team

---

**Document Version:** 1.0  
**Last Updated:** 2026-02-05  
**Next Review:** Before next deployment
