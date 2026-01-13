# HAProxy Staging Test Plan

**Date:** 2026-01-12  
**Purpose:** Test HAProxy setup on staging before production deployment  
**Server:** 172.25.222.103 (Staging)  
**Estimated Time:** 1-2 hours

---

## 🎯 **Objective**

Verify that HAProxy works correctly on staging server to provide:
- ✅ Single entry point on port 80
- ✅ Clean URLs (no port numbers)
- ✅ Proper routing (frontend and backend)
- ✅ Health checks working
- ✅ All functionality intact

---

## 📋 **Pre-Test Checklist**

- [ ] Staging server is accessible via SSH
- [ ] Current staging deployment is working (port 3001, 8001)
- [ ] HAProxy is not currently running
- [ ] Port 80 is available (no nginx or apache)

---

## 🔍 **Current Staging Status Check**

Run these commands on staging server to check current state:

```bash
# Check if services are running
docker compose -f docker-compose.prod.yml ps

# Check current access
curl http://localhost:3001  # Frontend should respond
curl http://localhost:8001/health/  # Backend should respond

# Check if HAProxy is installed
which haproxy
haproxy -v

# Check if HAProxy is running
sudo systemctl status haproxy

# Check if port 80 is in use
sudo lsof -i :80
```

---

## ⚙️ **HAProxy Installation & Configuration**

### **Step 1: Install HAProxy (if not installed)**

```bash
# Update package list
sudo apt update

# Install HAProxy
sudo apt install -y haproxy

# Verify installation
haproxy -v
# Should show: HAProxy version 2.x.x or higher
```

### **Step 2: Backup Current Configuration**

```bash
# Backup existing HAProxy config
sudo cp /etc/haproxy/haproxy.cfg /etc/haproxy/haproxy.cfg.backup

# Check if backup exists
ls -la /etc/haproxy/haproxy.cfg.backup
```

### **Step 3: Deploy HAProxy Configuration**

```bash
cd ~/edms

# Copy our HAProxy config to system location
sudo cp infrastructure/haproxy/haproxy.cfg /etc/haproxy/haproxy.cfg

# Verify config syntax
sudo haproxy -c -f /etc/haproxy/haproxy.cfg

# Should show: Configuration file is valid
```

### **Step 4: Update Docker Ports (if needed)**

Your docker-compose.prod.yml should already have the correct ports:
- Backend: 8001 (mapped to host)
- Frontend: 3001 (mapped to host)

```bash
# Verify ports in docker-compose
grep "ports:" docker-compose.prod.yml -A 1

# Should show:
# Backend: 8001:8000
# Frontend: 3001:80
```

### **Step 5: Start HAProxy**

```bash
# Enable HAProxy to start on boot
sudo systemctl enable haproxy

# Start HAProxy
sudo systemctl start haproxy

# Check status
sudo systemctl status haproxy
# Should show: active (running)

# Check if port 80 is listening
sudo ss -tlnp | grep :80
# Should show HAProxy listening on port 80
```

---

## ✅ **Testing Phase 1: HAProxy Health**

### **Test 1.1: HAProxy is Running**

```bash
sudo systemctl status haproxy
```

**Expected:** `active (running)` in green

### **Test 1.2: Port 80 Listening**

```bash
curl http://localhost:80
```

**Expected:** Should return HTML (frontend page) or redirect

### **Test 1.3: HAProxy Stats Page**

```bash
curl http://localhost:8404/stats
```

**Expected:** HTML page with statistics

**Or in browser:** `http://172.25.222.103:8404/stats`
- Username: `admin`
- Password: `admin_changeme`

**Should show:**
- Frontend: http_frontend (UP)
- Backend backend_django: django1 (UP)
- Backend frontend_react: react1 (UP)

### **Test 1.4: HAProxy Health Endpoint**

```bash
curl http://localhost:80/haproxy-health
```

**Expected:** `HAProxy Healthy`

---

## ✅ **Testing Phase 2: Backend Routing**

### **Test 2.1: Backend Health Check**

```bash
curl http://localhost:80/health
```

**Expected:** `{"status":"healthy"}`

### **Test 2.2: API Endpoint**

```bash
curl http://localhost:80/api/v1/
```

**Expected:** JSON response with API root

### **Test 2.3: Admin Panel**

```bash
curl -I http://localhost:80/admin/
```

**Expected:** HTTP 302 (redirect to login) or HTTP 200

### **Test 2.4: Static Files**

```bash
curl -I http://localhost:80/static/admin/css/base.css
```

**Expected:** HTTP 200 OK

---

## ✅ **Testing Phase 3: Frontend Routing**

### **Test 3.1: Frontend Home**

```bash
curl http://localhost:80/
```

**Expected:** HTML with React app

### **Test 3.2: Frontend Routes**

```bash
curl -I http://localhost:80/login
curl -I http://localhost:80/documents
```

**Expected:** HTTP 200 OK (React handles routing)

---

## ✅ **Testing Phase 4: Browser Testing**

### **Test 4.1: Access Frontend via Port 80**

**From any computer on network:**
```
http://172.25.222.103
```

**Expected:**
- ✅ Login page loads
- ✅ No port number needed!
- ✅ Custom app title appears

### **Test 4.2: Login**

**Action:**
- Username: `admin`
- Password: [your admin password]

**Expected:**
- ✅ Login successful
- ✅ Dashboard loads
- ✅ Navigation works

### **Test 4.3: Document Creation**

**Action:**
1. Navigate to My Tasks
2. Click "Create Document"
3. Fill in details
4. Upload file
5. Submit

**Expected:**
- ✅ Document created successfully
- ✅ File uploaded without errors
- ✅ No console errors (F12)

### **Test 4.4: API Calls**

**Action:**
- Open browser console (F12)
- Navigate around the app
- Check Network tab

**Expected:**
- ✅ All API calls go to `/api/v1/...` (not `localhost:8001`)
- ✅ No CORS errors
- ✅ All requests return 200 OK (or expected status)

### **Test 4.5: Admin Panel Access**

**URL:**
```
http://172.25.222.103/admin/
```

**Expected:**
- ✅ Admin login page loads
- ✅ Can login
- ✅ Admin panel functions normally
- ✅ Static files load (styling works)

---

## ✅ **Testing Phase 5: Performance & Load**

### **Test 5.1: Concurrent Users**

**Action:**
- Open 3-5 browser tabs/windows
- Login with different users (or same user)
- Navigate simultaneously

**Expected:**
- ✅ All tabs responsive
- ✅ No timeouts
- ✅ No connection errors

### **Test 5.2: Large File Upload**

**Action:**
- Upload a large document (5-10 MB)

**Expected:**
- ✅ Upload completes successfully
- ✅ No timeout errors
- ✅ HAProxy doesn't block large uploads

### **Test 5.3: HAProxy Logs**

```bash
sudo tail -f /var/log/haproxy.log
```

**Or:**
```bash
sudo journalctl -u haproxy -f
```

**Expected:**
- ✅ Shows incoming requests
- ✅ Backend selections logged
- ✅ No error messages

---

## ✅ **Testing Phase 6: Backup & Restore**

### **Test 6.1: Backup Still Works**

```bash
cd ~/edms
./scripts/backup-hybrid.sh
```

**Expected:**
- ✅ Backup completes successfully
- ✅ No connection issues
- ✅ Backup file created

### **Test 6.2: Access via Port 8001 Still Works**

```bash
curl http://localhost:8001/health/
```

**Expected:**
- ✅ Direct access still works
- ✅ HAProxy doesn't block direct access

---

## 📊 **Test Results Checklist**

After completing all tests, verify:

### **HAProxy Status:**
- [ ] HAProxy is running (`systemctl status haproxy`)
- [ ] Port 80 is listening
- [ ] HAProxy stats page accessible
- [ ] Both backends showing UP in stats

### **Routing:**
- [ ] Frontend accessible via port 80
- [ ] Backend API accessible via port 80
- [ ] Admin panel accessible via port 80
- [ ] Static files served correctly
- [ ] Health checks passing

### **Functionality:**
- [ ] Can login via port 80
- [ ] Can create documents
- [ ] Can upload files
- [ ] Workflow functions work
- [ ] No browser console errors

### **Performance:**
- [ ] Multiple concurrent users work
- [ ] Large file uploads work
- [ ] No timeout errors
- [ ] Response times acceptable (<2 seconds)

### **Integration:**
- [ ] Backup system still works
- [ ] Direct port access (3001, 8001) still works
- [ ] Cron jobs still running
- [ ] No new errors in logs

---

## 🐛 **Troubleshooting**

### **Issue 1: HAProxy Won't Start**

**Symptom:** `systemctl start haproxy` fails

**Check:**
```bash
# Check config syntax
sudo haproxy -c -f /etc/haproxy/haproxy.cfg

# Check logs
sudo journalctl -u haproxy -n 50

# Check if port 80 is in use
sudo lsof -i :80
```

**Solution:**
- Fix configuration syntax errors
- Kill process using port 80
- Check file permissions

---

### **Issue 2: Backend Shows DOWN**

**Symptom:** Stats page shows backend_django or frontend_react as DOWN

**Check:**
```bash
# Verify containers are running
docker compose -f docker-compose.prod.yml ps

# Check if ports are accessible
curl http://localhost:3001
curl http://localhost:8001/health/

# Check HAProxy logs
sudo journalctl -u haproxy -f
```

**Solution:**
```bash
# Fix health check path (must have trailing slash)
# In haproxy.cfg, line 93 should be:
option httpchk GET /health/ HTTP/1.1\\r\\nHost:\\ localhost

# Restart HAProxy after fix
sudo systemctl restart haproxy
```

---

### **Issue 3: Frontend Loads but API Calls Fail**

**Symptom:** Login page loads but login fails with network error

**Check:**
```bash
# Test API directly
curl http://localhost:80/api/v1/

# Check backend logs
docker compose -f docker-compose.prod.yml logs backend --tail=50

# Check HAProxy routing
curl -v http://localhost:80/api/v1/
```

**Solution:**
- Verify `REACT_APP_API_URL=/api/v1` in .env
- Rebuild frontend if env var was changed
- Check CORS settings in Django

---

### **Issue 4: Static Files Not Loading**

**Symptom:** Admin panel has no styling

**Check:**
```bash
# Test static file access
curl -I http://localhost:80/static/admin/css/base.css

# Check if Django serves static files
docker compose -f docker-compose.prod.yml exec backend ls -la /app/staticfiles/
```

**Solution:**
```bash
# Collect static files
docker compose -f docker-compose.prod.yml exec backend python manage.py collectstatic --noinput

# Restart backend
docker compose -f docker-compose.prod.yml restart backend
```

---

## 📝 **Test Results Template**

Document your test results:

```
=== HAPROXY STAGING TEST RESULTS ===
Date: 2026-01-12
Tester: [Your Name]
Server: 172.25.222.103

PRE-TEST STATUS:
- Staging working: YES/NO
- HAProxy installed: YES/NO
- Port 80 available: YES/NO

HAPROXY SETUP:
- Installation: SUCCESS/FAILED
- Configuration: SUCCESS/FAILED
- Service start: SUCCESS/FAILED
- Port 80 listening: YES/NO

ROUTING TESTS:
- Backend health: PASS/FAIL
- API endpoint: PASS/FAIL
- Admin panel: PASS/FAIL
- Static files: PASS/FAIL
- Frontend home: PASS/FAIL

BROWSER TESTS:
- Port 80 access: PASS/FAIL
- Login: PASS/FAIL
- Document creation: PASS/FAIL
- File upload: PASS/FAIL
- Admin panel: PASS/FAIL

PERFORMANCE:
- Concurrent users: PASS/FAIL
- Large uploads: PASS/FAIL
- Response times: ACCEPTABLE/SLOW

INTEGRATION:
- Backup system: WORKING/BROKEN
- Direct access: WORKING/BROKEN
- Cron jobs: WORKING/BROKEN

OVERALL RESULT: PASS/FAIL

ISSUES FOUND:
[List any issues encountered]

RECOMMENDATIONS:
[Any recommendations before production]
```

---

## 🎯 **Success Criteria**

HAProxy test is successful when:

1. ✅ All tests pass
2. ✅ Frontend accessible via port 80
3. ✅ Backend API working via port 80
4. ✅ No functionality broken
5. ✅ Performance acceptable
6. ✅ No new errors in logs

---

## 🚀 **Next Steps After Successful Test**

### **If All Tests Pass:**

1. **Document Configuration**
   - [ ] Note HAProxy version
   - [ ] Save haproxy.cfg
   - [ ] Document any customizations

2. **Update Deployment Guide**
   - [ ] Add HAProxy steps to production guide
   - [ ] Document firewall rules (port 80)
   - [ ] Update access URLs

3. **Deploy to Production**
   - [ ] Install HAProxy on production
   - [ ] Copy tested configuration
   - [ ] Follow same setup steps
   - [ ] Test production access

### **If Tests Fail:**

1. **Troubleshoot Issues**
   - Review error logs
   - Check configuration
   - Test each component

2. **Decide:**
   - Fix HAProxy issues and retest
   - Or deploy production without HAProxy
   - Or get help with specific issues

---

## 📞 **Support**

**If you encounter issues during testing:**

1. Check HAProxy logs: `sudo journalctl -u haproxy -f`
2. Check Docker logs: `docker compose -f docker-compose.prod.yml logs -f`
3. Review troubleshooting section above
4. Refer to `DEPLOYMENT_WITH_HAPROXY_GUIDE.md`

---

**Ready to start testing? Let me know when you want to begin!** 🧪
