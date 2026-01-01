# 🚀 Quick Deploy: Review Workflow Fix

## Problem
**HTTP 500 error** when submitting documents for review with no error details.

## Solution
Enhanced error handling + comprehensive logging to diagnose and fix the issue.

---

## 📋 Deploy on Staging Server (172.28.1.148)

### Step 1: Pull the Fix
```bash
ssh lims@172.28.1.148
cd /home/lims/edms-staging
git pull origin develop
```

### Step 2: Deploy (Choose one method)

**Option A: Automated Deployment (Recommended)**
```bash
bash scripts/deploy-review-fix.sh
```

**Option B: Manual Deployment**
```bash
# Restart backend
docker compose -f docker-compose.prod.yml restart backend

# Wait for startup
sleep 30

# Run diagnostics
bash scripts/debug-review-workflow.sh
```

### Step 3: Monitor Backend Logs
```bash
# In a separate terminal, watch logs in real-time
docker compose -f docker-compose.prod.yml logs -f backend | grep -E "submit_for_review|ERROR|Exception"
```

### Step 4: Test from Frontend
1. Login as **author01** (password: test123)
2. Go to "My Documents"
3. Find a DRAFT document
4. Click "Submit for Review"
5. Select **reviewer01**
6. Click "Submit"

---

## 🔍 Expected Results

### In Frontend:
✅ Success message: "Document submitted for review successfully"  
✅ Document status changes to "Pending Review"

### In Backend Logs:
```
submit_for_review_enhanced called for document ea462429...
Document found: SOP-2025-0001, Status: DRAFT
Reviewer found: reviewer01 (Reviewer One)
Assigning reviewer reviewer01 to document
Calling lifecycle_service.submit_for_review...
🔍 submit_for_review called for SOP-2025-0001
🔄 Transitioning workflow from DRAFT to PENDING_REVIEW...
✅ Document status after transition: PENDING_REVIEW
```

---

## 🐛 If Still Getting Errors

### Error 1: "No active roles" for reviewer01
```bash
bash scripts/fix-reviewer-approver-roles.sh
```

### Error 2: "No DocumentStates found"
```bash
docker compose -f docker-compose.prod.yml exec backend python manage.py migrate
```

### Error 3: Specific exception in logs
Check backend logs for the actual error:
```bash
docker compose -f docker-compose.prod.yml logs --tail=100 backend
```

The enhanced logging will show exactly what's failing.

---

## 📊 What Changed

### Enhanced Error Handling
- ✅ Detailed logging at every step
- ✅ Full exception tracebacks in responses
- ✅ Non-blocking recommendation system
- ✅ Specific error messages instead of generic 500

### New Diagnostic Tools
- ✅ `scripts/debug-review-workflow.sh` - Full system diagnostics
- ✅ `scripts/deploy-review-fix.sh` - Automated deployment
- ✅ `REVIEW_WORKFLOW_FIX.md` - Complete documentation

---

## 📞 Need Help?

**Check the detailed guide:** `REVIEW_WORKFLOW_FIX.md`

**Common Issues:**
1. Reviewer has no roles → Run `fix-reviewer-approver-roles.sh`
2. Missing database states → Run migrations
3. Document in wrong state → Check with debug script

**Get diagnostics:**
```bash
bash scripts/debug-review-workflow.sh
```

---

## ✅ Commit Info

**Commit:** `bbc3b0e`  
**Branch:** `develop`  
**Date:** 2026-01-01  
**Status:** Ready to deploy
