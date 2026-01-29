# 🚀 Staging Deployment Instructions - SoD & Badge Refresh

**Branch**: `feature/segregation-of-duties-and-badge-refresh`  
**Target**: Staging Server  
**Status**: ✅ READY FOR DEPLOYMENT  
**Date**: 2026-01-27

---

## ⚠️ Pre-Deployment Checklist

- [ ] Staging server accessible
- [ ] SSH access available
- [ ] Docker & Docker Compose installed
- [ ] ~15-20 minutes available
- [ ] Test users exist (approver01, reviewer01, admin)

---

## 📊 Changes Being Deployed

**Backend (3 files)**:
- SoD enforcement in workflow and models
- Permission fix for document creation

**Frontend (7 files)**:
- Badge refresh on all workflow actions
- Self-assignment prevention in dropdowns
- Button hiding for document authors

**Total**: 10 files, 99 insertions, 11 deletions

---

## 🚀 Deployment Steps

### 1. Connect to Staging Server
```bash
ssh your-staging-server
cd /path/to/edms
```

### 2. Backup Current State (Optional)
```bash
git branch backup-staging-$(date +%Y%m%d-%H%M%S)
git log --oneline -1 > /tmp/pre-deployment-commit.txt
```

### 3. Checkout Feature Branch
```bash
git fetch origin
git checkout feature/segregation-of-duties-and-badge-refresh
git log --oneline -1
# Should show: 9a64042 or similar
```

### 4. Stop Services
```bash
docker compose down
docker compose ps  # Verify stopped
```

### 5. Rebuild Containers
```bash
docker compose build --no-cache backend frontend
# Wait 5-10 minutes for build
```

### 6. Start Services
```bash
docker compose up -d
docker compose ps  # Verify all running
docker compose logs backend frontend | tail -50
```

### 7. Verify Deployment
```bash
curl http://localhost:8000/health/
curl http://localhost:3000/
```

---

## 🧪 Testing Checklist

### Test 1: Badge Refresh on Document Creation
**As**: approver01
1. Note badge count
2. Create new document
3. **Expected**: Badge increases immediately
4. **Console**: `✅ Badge refreshed immediately after document creation`

**Status**: ⬜ PASS / ⬜ FAIL

---

### Test 2: Self-Assignment Prevention
**As**: approver01
1. Create document (you're the author)
2. Click "Route for Approval"
3. **Expected**: You NOT in approver dropdown
4. **Console**: `authorId: 4` (not undefined)

**Status**: ⬜ PASS / ⬜ FAIL

---

### Test 3: Button Hiding for Authors
**As**: approver01 (author)
1. Open your own document in PENDING_APPROVAL
2. **Expected**: NO "Start Approval Process" button
3. **Expected**: Shows "⚠️ Cannot Approve Own Document"

**Status**: ⬜ PASS / ⬜ FAIL

---

### Test 4: Badge Refresh on Review
**As**: reviewer01
1. Note badge count
2. Complete a review
3. **Expected**: Badge decreases immediately

**Status**: ⬜ PASS / ⬜ FAIL

---

### Test 5: Badge Refresh on Approval
**As**: approver01
1. Note badge count
2. Approve someone else's document
3. **Expected**: Badge decreases immediately

**Status**: ⬜ PASS / ⬜ FAIL

---

### Test 6: New Version Creation
**As**: Any user
1. Create new version of EFFECTIVE document
2. **Expected**: Badge increases (new DRAFT)

**Status**: ⬜ PASS / ⬜ FAIL

---

### Test 7: Creation Permissions
**As**: reviewer01 or approver01
1. Create a document
2. **Expected**: Success (no 403 error)

**Status**: ⬜ PASS / ⬜ FAIL

---

## 📊 Test Results Summary

**Overall Status**: ⬜ ALL PASS / ⬜ SOME FAIL

---

## 🔄 Rollback Plan

### If Tests Fail:
```bash
docker compose down
git checkout main
docker compose build backend frontend
docker compose up -d
```

---

## ✅ Success Criteria

- ✅ All 7 tests pass
- ✅ No console errors
- ✅ No 500 errors in logs
- ✅ Badge updates work
- ✅ SoD enforcement works
- ✅ System stable 10+ minutes

---

## 🐛 Troubleshooting

**Services won't start**:
```bash
docker compose logs backend frontend
```

**Badge not updating**:
1. Clear browser cache (Ctrl+Shift+R)
2. Check console for errors
3. Verify backend: `curl http://localhost:8000/health/`

**Self-assignment still works**:
1. Check console shows `authorId: X` (not undefined)
2. Hard refresh browser
3. Verify correct branch: `git branch --show-current`

---

## 📝 Deployment Log

**Deployed By**: _________________  
**Date**: _________________  
**Commit**: 9a64042  
**All Tests Passed**: ⬜ YES / ⬜ NO  
**Ready for Production**: ⬜ YES / ⬜ NO  

**Notes**: _________________________________

---

## 🎯 Next Steps

**If All Pass ✅**:
1. Monitor staging 24-48 hours
2. Get stakeholder approval
3. Create pull request
4. Merge to main
5. Deploy to production

**If Tests Fail ❌**:
1. Rollback to main
2. Document issues
3. Fix in feature branch
4. Re-deploy to staging

---

**Time Required**: 15-20 minutes  
**Risk Level**: LOW (backwards compatible)  
**Rollback**: Easy (switch to main branch)
