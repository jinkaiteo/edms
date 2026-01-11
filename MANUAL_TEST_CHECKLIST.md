# 🧪 Manual Testing Checklist - Local Deployment

## ✅ Services Running

Run these checks:

```bash
# Check all services
docker compose ps

# Should see 6 services running:
# - edms_db
# - edms_redis  
# - edms_backend
# - edms_frontend
# - edms_celery_worker
# - edms_celery_beat
```

## 📝 Manual Testing Steps

### 1. Access Frontend (5 min)
- [ ] Open http://localhost:3000
- [ ] Page loads without errors
- [ ] Login page visible
- [ ] Can navigate UI

### 2. Admin Panel (5 min)
- [ ] Open http://localhost:8000/admin
- [ ] Login with admin/admin123
- [ ] Can access Users section
- [ ] Can access Documents section
- [ ] Can access Workflows section

### 3. Create Test Users (10 min)

In admin panel, create 3 users:

**Author (author01)**
- Username: author01
- Password: Test123!
- Email: author@test.com
- Groups: Authors
- [ ] User created successfully

**Reviewer (reviewer01)**
- Username: reviewer01
- Password: Test123!
- Email: reviewer@test.com
- Groups: Reviewers
- [ ] User created successfully

**Approver (approver01)**
- Username: approver01
- Password: Test123!
- Email: approver@test.com  
- Groups: Approvers
- [ ] User created successfully

### 4. Test Document Workflow (20 min)

**As Author:**
- [ ] Login as author01
- [ ] Create new document
  - Title: "Test SOP - Quality Procedure"
  - Document Type: SOP
  - Status: DRAFT
- [ ] Document created successfully
- [ ] Submit document for review
  - Select reviewer01
  - Add comment
- [ ] Document status changed to "Under Review"

**As Reviewer:**
- [ ] Logout and login as reviewer01
- [ ] See document in "My Tasks"
- [ ] Open document for review
- [ ] Approve review
  - Add review comment
- [ ] Document status changed to "Reviewed"
- [ ] Route to approver01

**As Approver:**
- [ ] Logout and login as approver01
- [ ] See document in "My Tasks"
- [ ] Open document for approval
- [ ] Approve document
  - Set effective date (tomorrow)
  - Add approval comment
- [ ] Document status changed to "Approved - Pending Effective"

### 5. Check Audit Trail (5 min)
- [ ] Open document
- [ ] View version history
- [ ] See all workflow actions logged
- [ ] Timestamps recorded
- [ ] User actions visible

### 6. Background Tasks (5 min)
```bash
# Check Celery logs
docker compose logs celery_worker --tail 50
docker compose logs celery_beat --tail 50

# Should see:
# - Worker started
# - Beat scheduler running
# - No critical errors
```

- [ ] Celery worker running
- [ ] Celery beat running
- [ ] No error messages in logs

### 7. Check Backend Logs (5 min)
```bash
docker compose logs backend --tail 100
```

- [ ] No critical errors
- [ ] API requests logging
- [ ] Workflow actions logging

## ✅ Success Criteria

All checks must pass:
- [ ] All 6 services running
- [ ] Frontend accessible
- [ ] Admin panel accessible
- [ ] Users can be created
- [ ] Document workflow completes
- [ ] Audit trail records actions
- [ ] Background tasks running
- [ ] No critical errors in logs

## 🚨 If Any Test Fails

1. Check logs:
   ```bash
   docker compose logs backend
   docker compose logs frontend
   ```

2. Restart services:
   ```bash
   docker compose restart backend frontend
   ```

3. Check database:
   ```bash
   docker compose exec backend python3 manage.py dbshell
   ```

## 📊 Estimated Time

- **Quick check (services only):** 5 minutes
- **Full manual testing:** 50-60 minutes
- **With troubleshooting:** 90 minutes

## ✅ After All Tests Pass

You're ready for:
1. **Staging deployment** - Same tests on staging server
2. **Production deployment** - With confidence!

---

**Current Status:** Services running, ready for manual testing

**Next:** Complete this checklist, then proceed to staging
