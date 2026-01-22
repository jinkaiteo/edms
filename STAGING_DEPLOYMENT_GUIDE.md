# Staging Server Deployment Guide - Scheduler Timeout Fix

**Date:** January 16, 2026  
**Commit:** `79d75df` - fix(scheduler): Replace synchronous task execution with fire-and-forget pattern  
**Status:** Ready for deployment

---

## Pre-Deployment Checklist

Before deploying to staging, verify:

- ✅ Changes committed and pushed to GitHub
- ✅ Commit hash: `79d75df`
- ✅ Branch: `main`
- ✅ Files changed: 2 (monitoring_dashboard.py, TaskListWidget.tsx)
- ✅ Local testing: Passed (85ms response time)

---

## Deployment Steps for Staging Server

### Step 1: SSH to Staging Server

```bash
ssh user@your-staging-server
# Replace with your actual staging server credentials
```

### Step 2: Navigate to Project Directory

```bash
cd /home/edms/edms
# Or wherever your EDMS project is located
```

### Step 3: Verify Current Status

```bash
# Check current branch
git branch

# Check current commit
git log --oneline -1

# Check running services
docker compose ps
```

### Step 4: Pull Latest Changes

```bash
# Fetch latest changes from GitHub
git fetch origin

# Pull changes (will include commit 79d75df)
git pull origin main

# Verify the fix was pulled
git log --oneline -1
# Should show: 79d75df fix(scheduler): Replace synchronous task execution...
```

### Step 5: Rebuild Containers

```bash
# Stop all services
docker compose down

# Rebuild backend and frontend with new code
docker compose build backend frontend

# Start all services
docker compose up -d

# Wait for services to initialize (20 seconds)
sleep 20
```

### Step 6: Verify Deployment

```bash
# Check all services are running
docker compose ps

# Expected output:
# NAME                 STATUS
# edms_backend         Up
# edms_frontend        Up
# edms_celery_worker   Up
# edms_celery_beat     Up
# edms_db              Up
# edms_redis           Up

# Check backend logs for errors
docker logs edms_backend --tail=50

# Check celery worker is ready
docker logs edms_celery_worker --tail=20
```

### Step 7: Test the Fix

```bash
# Test manual trigger via API
curl -X POST http://localhost:8000/api/v1/scheduler/monitoring/manual-trigger/ \
  -H "Content-Type: application/json" \
  -d '{"task_name": "perform_system_health_check"}'

# Expected response (instant, <100ms):
# {
#   "success": true,
#   "task_id": "abc-123-...",
#   "status": "queued",
#   "message": "Task queued successfully..."
# }
```

### Step 8: Verify Task Execution

```bash
# Check backend logs for task queuing
docker logs edms_backend --tail=50 | grep "queued successfully"

# Check celery worker logs for task execution
docker logs edms_celery_worker --tail=50 | grep "succeeded"
```

---

## Complete Deployment Script (Copy-Paste)

```bash
#!/bin/bash
# Quick deployment script for staging server

set -e

echo "=========================================="
echo "  Deploying Scheduler Timeout Fix"
echo "  Commit: 79d75df"
echo "=========================================="
echo ""

# Navigate to project
cd /home/edms/edms || cd ~/edms || { echo "Project directory not found"; exit 1; }

# Pull latest changes
echo "📥 Pulling latest changes..."
git fetch origin
git pull origin main

# Verify commit
CURRENT_COMMIT=$(git log --oneline -1)
echo "✅ Current commit: $CURRENT_COMMIT"

# Stop services
echo ""
echo "🛑 Stopping services..."
docker compose down

# Rebuild containers
echo ""
echo "🔨 Rebuilding containers..."
docker compose build backend frontend

# Start services
echo ""
echo "🚀 Starting services..."
docker compose up -d

# Wait for initialization
echo ""
echo "⏳ Waiting for services to initialize (20 seconds)..."
sleep 20

# Check status
echo ""
echo "🔍 Checking service status..."
docker compose ps

# Test the fix
echo ""
echo "🧪 Testing manual trigger..."
RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/scheduler/monitoring/manual-trigger/ \
  -H "Content-Type: application/json" \
  -d '{"task_name": "perform_system_health_check"}')

if echo "$RESPONSE" | grep -q '"success": true'; then
  echo "✅ Test PASSED - Manual trigger working!"
  echo "Response: $RESPONSE" | head -c 200
else
  echo "❌ Test FAILED - Check logs"
  echo "Response: $RESPONSE"
fi

echo ""
echo "=========================================="
echo "  Deployment Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Open admin dashboard and test manual trigger"
echo "2. Verify no timeout errors occur"
echo "3. Monitor logs for any issues"
echo ""
echo "Monitoring commands:"
echo "  docker logs edms_backend --tail=100 -f"
echo "  docker logs edms_celery_worker --tail=100 -f"
```

---

## Alternative: Interactive Deployment Script

If you already have the interactive deployment script:

```bash
# Use the existing deploy-interactive.sh script
./deploy-interactive.sh

# When prompted:
# - Select "Update existing deployment"
# - Confirm rebuild of backend and frontend
# - Test manually after deployment
```

---

## Testing Checklist (After Deployment)

### 1. UI Testing

1. **Open Admin Dashboard:**
   - URL: `http://your-staging-server/admin/dashboard`
   - Or: `http://your-staging-server:3000/admin/dashboard`

2. **Navigate to Scheduled Tasks:**
   - Find "Scheduled Tasks" widget
   - Click to expand

3. **Test Manual Trigger:**
   - Expand any category (e.g., "Document Processing")
   - Click "▶️ Run Now" on any task
   - **Expected:** Instant success message (<1 second)
   - **NOT Expected:** 30-second wait or timeout error

4. **Verify Success Message:**
   ```
   ✅ Task queued successfully!
   
   Task: process-document-effective-dates
   Task ID: abc-123-def-456
   Status: queued
   
   The task is now running in the background.
   The dashboard will update automatically when it completes.
   ```

5. **Wait for Auto-Refresh:**
   - Dashboard auto-refreshes after 2 seconds
   - Task status should update to "SUCCESS"

### 2. API Testing

```bash
# SSH to staging server
ssh user@staging-server

# Test API endpoint
time curl -X POST http://localhost:8000/api/v1/scheduler/monitoring/manual-trigger/ \
  -H "Content-Type: application/json" \
  -d '{"task_name": "perform_system_health_check"}'

# Expected: Response in <1 second with success: true
```

### 3. Log Verification

```bash
# Check backend logs
docker logs edms_backend --tail=50 | grep -E "queued successfully|ERROR"

# Check celery worker logs
docker logs edms_celery_worker --tail=50 | grep "succeeded"

# Check for any errors
docker logs edms_backend --tail=100 | grep ERROR
```

---

## Rollback Plan (If Needed)

If issues occur on staging:

### Option 1: Git Rollback

```bash
# SSH to staging server
ssh user@staging-server

# Navigate to project
cd /home/edms/edms

# Revert to previous commit
git log --oneline -5  # Find previous commit hash
git reset --hard 8b0bef2  # Replace with actual previous commit

# Rebuild and restart
docker compose down
docker compose build backend frontend
docker compose up -d
```

### Option 2: Revert Specific Files

```bash
# Revert just the changed files
git checkout 8b0bef2 -- backend/apps/scheduler/monitoring_dashboard.py
git checkout 8b0bef2 -- frontend/src/components/scheduler/TaskListWidget.tsx

# Rebuild
docker compose restart backend frontend
```

---

## Expected Results

### Performance Metrics

| Metric | Before | After | Status |
|--------|--------|-------|--------|
| Response Time | 30+ seconds | <100ms | ✅ 300x faster |
| Timeout Errors | Always | None | ✅ Fixed |
| User Feedback | Delayed | Instant | ✅ Improved |

### Health Indicators

After deployment, verify:
- ✅ All 6 containers running
- ✅ Backend responds to requests
- ✅ Celery worker processing tasks
- ✅ Manual trigger responds instantly
- ✅ No timeout errors in browser console
- ✅ Tasks execute successfully

---

## Troubleshooting

### Issue: Git pull fails

```bash
# Stash any local changes
git stash

# Pull again
git pull origin main

# If you need local changes back
git stash pop
```

### Issue: Container build fails

```bash
# Clean up old containers and images
docker compose down -v
docker system prune -a

# Rebuild from scratch
docker compose build --no-cache backend frontend
docker compose up -d
```

### Issue: Services won't start

```bash
# Check logs for errors
docker logs edms_backend
docker logs edms_frontend

# Check port conflicts
netstat -tulpn | grep -E "3000|8000"

# Restart specific service
docker compose restart backend
```

### Issue: Manual trigger still times out

```bash
# Verify code was pulled
cd /home/edms/edms
git log --oneline -1
# Should show: 79d75df

# Check if containers were rebuilt
docker images | grep qms_04
# Check image creation time (should be recent)

# Force rebuild
docker compose build --no-cache backend frontend
docker compose restart backend frontend
```

---

## Monitoring After Deployment

### First 30 Minutes

```bash
# Watch backend logs
docker logs edms_backend --tail=100 -f

# Watch celery worker
docker logs edms_celery_worker --tail=100 -f

# Monitor for errors
watch -n 5 'docker logs edms_backend --tail=20 | grep ERROR'
```

### First 24 Hours

- Monitor task execution success rate
- Check for any timeout errors
- Verify scheduled tasks continue to work
- Collect user feedback on manual trigger feature

---

## Success Criteria

Deployment is successful when:

- ✅ All services running (6 containers)
- ✅ Manual trigger responds in <1 second
- ✅ No timeout errors in browser console
- ✅ Tasks execute successfully in background
- ✅ Dashboard auto-refreshes after 2 seconds
- ✅ Scheduled tasks continue to work normally

---

## Support

If you encounter issues:

1. **Check deployment logs:**
   - Backend: `docker logs edms_backend --tail=100`
   - Worker: `docker logs edms_celery_worker --tail=100`

2. **Verify git commit:**
   ```bash
   git log --oneline -1
   # Should show: 79d75df fix(scheduler)...
   ```

3. **Check container rebuild:**
   ```bash
   docker images | grep qms_04-backend
   docker images | grep qms_04-frontend
   # Check creation time is recent
   ```

4. **Test API directly:**
   ```bash
   curl -X POST http://localhost:8000/api/v1/scheduler/monitoring/manual-trigger/ \
     -H "Content-Type: application/json" \
     -d '{"task_name": "perform_system_health_check"}'
   ```

---

**Deployment Status:** Ready  
**Risk Level:** Low (only affects manual trigger feature)  
**Estimated Deployment Time:** 5-10 minutes  
**Estimated Downtime:** 2-3 minutes (during container rebuild)

---

**Good luck with the deployment! 🚀**
