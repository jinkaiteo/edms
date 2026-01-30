# Production Deployment Guide - EDMS v1.3.0

**Version:** 1.3.0  
**Release Date:** 2026-01-30  
**Commit:** 03cd7a1  
**Deployment Date:** To be scheduled  

---

## 📋 Pre-Deployment Checklist

### ✅ Prerequisites
- [ ] Staging deployment tested successfully
- [ ] Release notes reviewed and approved
- [ ] Backup of current production database completed
- [ ] Downtime window scheduled (if required)
- [ ] Rollback plan reviewed
- [ ] Team notified of deployment

### ✅ System Requirements
- [ ] Docker Engine installed and running
- [ ] Docker Compose available
- [ ] Sufficient disk space (minimum 10GB free)
- [ ] Network connectivity to GitHub
- [ ] Production `.env` file configured correctly

---

## 🎯 Deployment Summary

### Changes in This Release
- ✅ Interactive dependency graph visualization (frontend only)
- ✅ Auto-copy dependencies on upversion (backend logic)
- ✅ Bug fixes for arrow directions and dependency copying
- ✅ New npm package: `@xyflow/react@12.10.0`

### Impact Assessment
- **Database Changes:** None (no migrations)
- **Environment Variables:** None (no new variables)
- **System Dependencies:** None (no new system packages)
- **Downtime Required:** Minimal (2-3 minutes for service restart)
- **Rollback Difficulty:** Easy (git checkout previous commit)

---

## 🚀 Deployment Steps

### Step 1: Pre-Deployment Backup ⚠️

**CRITICAL: Always backup before deployment!**

```bash
# SSH to production server
ssh user@production-server

# Navigate to project directory
cd /path/to/edms

# Run backup script
./scripts/backup-hybrid.sh

# Verify backup was created
ls -lh backups/ | tail -1

# Expected output: backup_YYYYMMDD_HHMMSS.tar.gz (~several MB)
```

**Save backup file path for potential rollback!**

---

### Step 2: Pull Latest Code

```bash
# Ensure you're on main branch
git branch

# Should show: * main

# Fetch latest changes
git fetch origin main

# Check what will be pulled
git log HEAD..origin/main --oneline

# Should show:
# 03cd7a1 docs: Add release notes for v1.3.0
# ad94bb6 Merge feature/dependency-graph-visualization into main
# 74d479d docs: Add deployment analysis for dependency graph feature
# 5cc8e04 fix: Auto-copy dependencies when upversioning documents
# e079d89 feat: Add interactive dependency graph visualization

# Pull the changes
git pull origin main
```

---

### Step 3: Review Changes

```bash
# Review what changed since last deployment
git diff 5cae7d4..HEAD --stat

# Should show:
# - 10 files changed
# - New components added
# - Package.json updated
```

---

### Step 4: Deploy Using Interactive Script

**Option A: Interactive Deployment (Recommended)**

```bash
# Use the interactive deployment script
./deploy-interactive.sh

# Follow the prompts:
# 1. Confirm environment (production)
# 2. Review configuration
# 3. Confirm deployment
# 4. Wait for completion (10-15 minutes)
```

The script will:
1. ✅ Validate configuration
2. ✅ Build Docker images (includes npm install for new package)
3. ✅ Stop existing containers gracefully
4. ✅ Start new containers
5. ✅ Run health checks
6. ✅ Verify services are running

**Option B: Manual Deployment**

```bash
# Build images with new code
docker compose -f docker-compose.prod.yml build

# Stop existing services
docker compose -f docker-compose.prod.yml down

# Start services with new images
docker compose -f docker-compose.prod.yml up -d

# Check service status
docker compose -f docker-compose.prod.yml ps
```

---

### Step 5: Post-Deployment Verification

#### 5.1 Health Checks

```bash
# Check all services are running
docker compose -f docker-compose.prod.yml ps

# Expected: All services "Up" and healthy

# Check backend logs
docker compose -f docker-compose.prod.yml logs backend --tail=50

# Should see: "Application startup complete"

# Check frontend logs
docker compose -f docker-compose.prod.yml logs frontend --tail=50

# Should see: Nginx started successfully
```

#### 5.2 API Health Check

```bash
# Test backend API
curl -f http://production-domain/api/v1/health/

# Expected: {"status": "healthy"}
```

#### 5.3 Frontend Health Check

```bash
# Test frontend loads
curl -f http://production-domain/

# Expected: HTML response with React app
```

---

### Step 6: Feature Testing

**Critical: Test new features immediately after deployment**

#### Test 1: Dependency Graph Visualization

1. **Login to application**
   - URL: `http://production-domain/`
   - Use admin credentials

2. **Navigate to a document with dependencies**
   - Go to Document Management
   - Open any document that has dependencies (e.g., TEST-WIN-001)

3. **Open Dependencies Tab**
   - Click "Dependencies" tab in document viewer

4. **Test Graph View**
   - Click "View Graph" button
   - ✅ Verify graph renders with nodes and edges
   - ✅ Verify current document is blue, others are gray
   - ✅ Verify arrows point correctly:
     - Left side (dependencies): arrows FROM dependency TO current doc
     - Right side (dependents): arrows FROM current doc TO dependent
   - ✅ Test drag and drop functionality
   - ✅ Test zoom and pan

5. **Test Tree View**
   - Click "View Tree" button
   - ✅ Verify tree structure displays correctly
   - ✅ Verify hierarchy is clear

#### Test 2: Dependency Copying on Upversion

1. **Select a document with dependencies**
   - Find a document that has dependencies (e.g., TEST-WIN-001 v1.0)

2. **Create New Version**
   - Click "Create New Version" action
   - Fill in version details
   - Submit

3. **Verify Dependencies Copied**
   - Open the new version (should be in DRAFT status)
   - Click "Dependencies" tab
   - ✅ Verify dependencies are present
   - ✅ Check descriptions show "Auto-copied from v1.0"
   - ✅ Verify dependencies point to latest EFFECTIVE versions

#### Test 3: Backward Compatibility

1. **Document List**
   - ✅ Document list loads correctly
   - ✅ Filters work as expected
   - ✅ Search functions normally

2. **Document Viewer**
   - ✅ Document details display properly
   - ✅ All tabs work (Details, History, Workflows, etc.)
   - ✅ Actions are available as expected

3. **Workflows**
   - ✅ Submit for review works
   - ✅ Approval workflow functions
   - ✅ Email notifications sent (if configured)

---

## ⏱️ Expected Timeline

| Phase | Duration | Description |
|-------|----------|-------------|
| Pre-deployment backup | 2-5 min | Backup database and media files |
| Code pull | 1 min | Pull latest from GitHub |
| Docker build | 5-8 min | Build images with new npm package |
| Service restart | 2-3 min | Stop old, start new containers |
| Health checks | 1-2 min | Verify services are healthy |
| Feature testing | 5-10 min | Test new features work correctly |
| **Total** | **16-29 min** | **Full deployment with testing** |

**Downtime:** 2-3 minutes (during service restart only)

---

## 🔄 Rollback Procedure

If issues arise during or after deployment:

### Quick Rollback (5 minutes)

```bash
# 1. Checkout previous stable version
git checkout 5cae7d4

# 2. Rebuild with old code
docker compose -f docker-compose.prod.yml build

# 3. Restart services
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml up -d

# 4. Verify rollback
docker compose -f docker-compose.prod.yml ps
curl -f http://production-domain/api/v1/health/
```

### Full Rollback with Database Restore (10-15 minutes)

```bash
# 1. Restore from backup created in Step 1
./scripts/restore-hybrid.sh backups/backup_YYYYMMDD_HHMMSS.tar.gz

# 2. Follow Quick Rollback steps above
```

---

## 📊 Monitoring After Deployment

### First 30 Minutes

Monitor these metrics closely:

1. **Docker Container Health**
   ```bash
   watch -n 10 'docker compose -f docker-compose.prod.yml ps'
   ```

2. **Backend Logs**
   ```bash
   docker compose -f docker-compose.prod.yml logs -f backend | grep -i error
   ```

3. **Frontend Logs**
   ```bash
   docker compose -f docker-compose.prod.yml logs -f frontend | grep -i error
   ```

4. **Database Connections**
   ```bash
   docker compose -f docker-compose.prod.yml logs db | grep -i "connection"
   ```

### First 24 Hours

Monitor these areas:

- [ ] User login success rate
- [ ] Document viewing errors
- [ ] Dependency graph rendering errors
- [ ] Upversion workflow completion rate
- [ ] Server resource utilization (CPU, memory, disk)
- [ ] Response times for API endpoints

---

## 🐛 Troubleshooting

### Issue: Frontend Not Loading

**Symptoms:** Blank page, 404 errors

**Solution:**
```bash
# Check if frontend container is running
docker compose -f docker-compose.prod.yml ps frontend

# Check frontend logs
docker compose -f docker-compose.prod.yml logs frontend --tail=100

# Rebuild frontend only
docker compose -f docker-compose.prod.yml build frontend
docker compose -f docker-compose.prod.yml up -d frontend
```

### Issue: Dependency Graph Not Rendering

**Symptoms:** Graph shows loading spinner forever, or blank area

**Possible Causes:**
1. New npm package not installed
2. Frontend cache not cleared
3. API endpoint not reachable

**Solution:**
```bash
# Verify npm package installed
docker compose -f docker-compose.prod.yml exec frontend ls node_modules/@xyflow

# Should show: react/

# If missing, rebuild frontend
docker compose -f docker-compose.prod.yml build --no-cache frontend
docker compose -f docker-compose.prod.yml up -d frontend

# Have users clear browser cache (Ctrl+F5)
```

### Issue: Dependencies Not Copied on Upversion

**Symptoms:** New version has no dependencies

**Possible Causes:**
1. Backend code not updated
2. Old Python bytecode cached

**Solution:**
```bash
# Verify backend code updated
docker compose -f docker-compose.prod.yml exec backend grep -n "_copy_dependencies_smart" /app/apps/workflows/document_lifecycle.py

# Should show line numbers where method exists

# If missing, rebuild backend
docker compose -f docker-compose.prod.yml build --no-cache backend
docker compose -f docker-compose.prod.yml up -d backend
```

---

## 📝 Deployment Sign-Off

### Pre-Deployment Approval

- [ ] **Technical Lead:** _________________ Date: _______
- [ ] **QA Lead:** _________________ Date: _______
- [ ] **Project Manager:** _________________ Date: _______

### Post-Deployment Verification

- [ ] **Deployment Completed By:** _________________ Date: _______ Time: _______
- [ ] **Health Checks Passed:** Yes / No
- [ ] **Feature Testing Passed:** Yes / No
- [ ] **Rollback Plan Tested:** Yes / No / N/A
- [ ] **Monitoring Active:** Yes / No

### Issues Encountered During Deployment

_Document any issues, even if resolved:_

```
Issue #1: _________________________________________________
Resolution: _______________________________________________
Time Lost: _______________________________________________

Issue #2: _________________________________________________
Resolution: _______________________________________________
Time Lost: _______________________________________________
```

### Deployment Status

- [ ] ✅ **Successful - No Issues**
- [ ] ⚠️ **Successful - Minor Issues (documented above)**
- [ ] ❌ **Failed - Rolled Back**

---

## 📞 Support Contacts

**During Deployment:**
- **Primary:** Development Team
- **Backup:** System Administrator
- **Emergency:** Project Manager

**After Deployment:**
- **Bug Reports:** Create GitHub Issue
- **Feature Questions:** See Release Notes
- **System Issues:** Contact System Administrator

---

## 📚 Additional Resources

- **Release Notes:** `RELEASE_NOTES_v1.3.0.md`
- **Deployment Analysis:** `DEPLOYMENT_ANALYSIS_DEPENDENCY_GRAPH.md`
- **Backup/Restore Guide:** `docs/BACKUP_RESTORE_API.md`
- **GitHub Commit:** 03cd7a1

---

**Important:** Keep this guide available during deployment. Print or have it open on a second screen.

**Post-Deployment:** Update this document with any lessons learned or additional steps that were required.

---

*Prepared by: Rovo Dev AI Assistant*  
*Last Updated: 2026-01-30*
