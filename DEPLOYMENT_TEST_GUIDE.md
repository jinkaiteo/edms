# 🚀 EDMS Deployment Testing Guide

## Overview

This guide walks you through testing the deployment locally before pushing to staging and production servers.

## Pre-Deployment Checklist

### ✅ Code Changes Completed
- [x] Core workflow bug fixed (`_get_active_workflow()`)
- [x] Database schema aligned (ScheduledTask, WorkflowNotification)
- [x] API endpoints configured (`/workflow/` endpoint)
- [x] Test files updated (UUID usage, endpoint patterns)
- [x] Missing modules created (`scheduler/tasks.py`)
- [x] Migrations created and tested

### ✅ Files Modified
1. `backend/apps/workflows/document_lifecycle.py` - Core fix
2. `backend/apps/scheduler/models.py` - Schema alignment
3. `backend/apps/documents/workflow_integration.py` - API actions
4. `backend/apps/api/v1/urls.py` - Endpoint routing
5. `backend/apps/workflows/migrations/0009_*.py` - New migration
6. `backend/apps/workflows/migrations/0010_*.py` - New migration
7. `backend/apps/scheduler/tasks.py` - New module
8. Test files - Updated patterns

## Deployment Testing Process

### Stage 1: Local Testing (YOU ARE HERE)

**Purpose:** Verify all changes work with fresh deployment

**Steps:**

1. **Run Automated Local Deployment Test**
   ```bash
   ./test_local_deployment.sh
   ```

   This script will:
   - ✅ Stop existing containers
   - ✅ Backup current database
   - ✅ Start fresh database
   - ✅ Build and start all services
   - ✅ Apply all migrations
   - ✅ Create admin user
   - ✅ Initialize system defaults
   - ✅ Run health checks
   - ✅ Test core workflow

2. **Manual Testing Checklist**
   
   Once the script completes, test manually:
   
   **Basic Access:**
   - [ ] Frontend loads: http://localhost:3000
   - [ ] Backend API responds: http://localhost:8000/api/v1/
   - [ ] Admin panel works: http://localhost:8000/admin
   - [ ] Login with admin/admin123
   
   **User Management:**
   - [ ] Create test users (author, reviewer, approver)
   - [ ] Assign roles
   - [ ] Test permissions
   
   **Document Workflow:**
   - [ ] Create new document
   - [ ] Submit for review
   - [ ] Review and approve
   - [ ] Check status transitions
   - [ ] Verify effective date handling
   
   **Advanced Features:**
   - [ ] Document versioning
   - [ ] Audit trail visible
   - [ ] Notifications working
   - [ ] Document search/filter
   
   **Background Tasks:**
   - [ ] Celery worker running
   - [ ] Celery beat running
   - [ ] Scheduled tasks in admin

3. **Check Logs for Errors**
   ```bash
   # Backend logs
   docker compose logs backend --tail 100
   
   # Celery worker logs
   docker compose logs celery_worker --tail 50
   
   # Celery beat logs
   docker compose logs celery_beat --tail 50
   
   # Frontend logs
   docker compose logs frontend --tail 50
   ```

4. **Run Specific Tests**
   ```bash
   # Test core workflow
   docker exec edms_backend python3 -m pytest \
     apps/workflows/tests/test_review_workflow.py::TestSubmitForReview \
     -v
   
   # Test versioning
   docker exec edms_backend python3 -m pytest \
     apps/workflows/tests/test_versioning_workflow.py \
     -v -k "test_old_version_superseded"
   ```

### Stage 2: Staging Server Testing

**Purpose:** Verify deployment on staging environment

**Prerequisites:**
- [ ] Local testing passed
- [ ] Code committed to repository
- [ ] Staging server accessible

**Steps:**

1. **Deploy to Staging**
   ```bash
   # Use existing staging deployment script
   ./deploy-staging-complete.sh
   
   # Or use automated script
   ./deploy-staging-automated.sh
   ```

2. **Run Same Manual Tests**
   - Repeat all manual tests from Stage 1
   - Test with realistic data volumes
   - Test with multiple concurrent users
   - Monitor performance

3. **Staging Acceptance Criteria**
   - [ ] All services start successfully
   - [ ] Migrations apply without errors
   - [ ] User can complete full document workflow
   - [ ] No critical errors in logs
   - [ ] Performance acceptable (< 2s page loads)
   - [ ] Background tasks running

### Stage 3: Production Deployment

**Purpose:** Deploy to production with confidence

**Prerequisites:**
- [ ] Staging testing passed
- [ ] Stakeholder approval
- [ ] Backup plan ready
- [ ] Rollback plan documented

**Steps:**

1. **Pre-Deployment**
   ```bash
   # Backup production database
   ./scripts/backup-edms.sh
   
   # Verify backup
   ls -lh backups/
   ```

2. **Deploy to Production**
   ```bash
   # Use production deployment script
   ./scripts/deploy-production.sh
   
   # Or interactive deployment
   ./deploy-interactive.sh
   ```

3. **Post-Deployment Verification**
   - [ ] All services running
   - [ ] Migrations applied
   - [ ] Test with production data
   - [ ] Monitor logs for 1 hour
   - [ ] Check scheduled tasks executing

4. **Rollback Plan (if needed)**
   ```bash
   # Stop services
   docker compose down
   
   # Restore database backup
   docker compose up -d db
   psql -h localhost -U edms_user edms_db < backup_file.sql
   
   # Start previous version
   git checkout <previous-commit>
   docker compose up -d
   ```

## Quick Reference Commands

### Local Testing
```bash
# Start fresh test
./test_local_deployment.sh

# Check service status
docker compose ps

# View logs
docker compose logs -f backend

# Access services
open http://localhost:3000        # Frontend
open http://localhost:8000/admin  # Admin
```

### Staging Testing
```bash
# SSH to staging
ssh user@staging-server

# Check deployment
cd /path/to/edms
docker compose ps
docker compose logs backend --tail 100
```

### Production
```bash
# SSH to production
ssh user@production-server

# Deploy
cd /path/to/edms
./scripts/deploy-production.sh

# Monitor
docker compose logs -f backend
```

## Troubleshooting

### Issue: Migrations Fail
```bash
# Check migration status
docker exec edms_backend python3 manage.py showmigrations

# Apply specific migration
docker exec edms_backend python3 manage.py migrate workflows 0009

# Fake if needed (use carefully!)
docker exec edms_backend python3 manage.py migrate workflows 0009 --fake
```

### Issue: Services Won't Start
```bash
# Check for port conflicts
netstat -tulpn | grep -E "3000|8000|5432"

# Rebuild containers
docker compose down
docker compose build --no-cache
docker compose up -d
```

### Issue: Database Connection Errors
```bash
# Check database logs
docker compose logs db

# Test connection
docker exec edms_backend python3 manage.py dbshell

# Restart database
docker compose restart db
```

## Success Criteria Summary

### Local ✅
- [ ] Fresh deployment works
- [ ] Core workflows functional
- [ ] No critical errors

### Staging ✅
- [ ] Production-like environment works
- [ ] Performance acceptable
- [ ] Concurrent users supported

### Production ✅
- [ ] Live deployment successful
- [ ] Users can work normally
- [ ] Monitoring shows healthy system

## Timeline

- **Local Testing:** 1-2 hours
- **Staging Testing:** 2-4 hours (includes soak testing)
- **Production Deployment:** 1-2 hours (with monitoring)

**Total:** 4-8 hours for complete deployment cycle

## Contact & Support

If issues arise:
1. Check logs first
2. Refer to troubleshooting section
3. Review commit history for recent changes
4. Check AGENTS.md for known issues

---

**Current Status:** Ready for Stage 1 (Local Testing)

**Next Action:** Run `./test_local_deployment.sh`
