# Staging HAProxy Test Deployment

**Server:** 172.25.222.103 (Staging)  
**Purpose:** Test HAProxy multi-app setup before production  
**Estimated Time:** 45-60 minutes  
**Date:** 2026-01-12

---

## 🎯 **What We're Testing**

Simulate the production setup on staging:
- ✅ Test HAProxy with EDMS
- ✅ Verify configuration works
- ✅ Identify any issues before production
- ✅ Practice the deployment procedure

**Staging Test Setup:**
```
HAProxy Port 80 → EDMS Backend (8001) + Frontend (3001)
```

**Note:** We won't deploy SENAITE on staging - we'll just test the EDMS portion of the HAProxy config.

---

## 📋 **Pre-Test Checklist**

- [ ] Staging server accessible (172.25.222.103)
- [ ] Current EDMS deployment working (ports 3001, 8001)
- [ ] SSH access configured
- [ ] Ready to make changes

---

## 🚀 **TEST PHASE 1: Current State Check (5 min)**

### **Step 1.1: Verify Current EDMS Works**

```bash
# SSH to staging
ssh lims@172.25.222.103

# Check current containers
cd ~/edms
docker compose -f docker-compose.prod.yml ps

# Should show 6 containers running

# Test current access
curl http://localhost:3001  # Frontend
curl http://localhost:8001/health/  # Backend

# Both should work
```

### **Step 1.2: Check HAProxy Status**

```bash
# Check if HAProxy is installed
which haproxy
haproxy -v

# Check if HAProxy is running
sudo systemctl status haproxy

# Check current config
sudo cat /etc/haproxy/haproxy.cfg 2>/dev/null || echo "No HAProxy config found"
```

### **Step 1.3: Check Port 80 Availability**

```bash
# Check what's using port 80
sudo lsof -i :80

# If nothing, you're good!
# If something is using it, we'll need to stop it
```

---

## 🔧 **TEST PHASE 2: Install/Configure HAProxy (15 min)**

### **Step 2.1: Install HAProxy (if not installed)**

```bash
# Update package list
sudo apt update

# Install HAProxy
sudo apt install -y haproxy

# Verify installation
haproxy -v

# Expected: HAProxy version 2.x.x
```

### **Step 2.2: Backup Any Existing Config**

```bash
# Backup if config exists
if [ -f /etc/haproxy/haproxy.cfg ]; then
    sudo cp /etc/haproxy/haproxy.cfg /etc/haproxy/haproxy.cfg.backup.$(date +%Y%m%d_%H%M%S)
    echo "✅ Backup created"
else
    echo "ℹ No existing config to backup"
fi
```

### **Step 2.3: Create Staging HAProxy Config**

```bash
cd ~/edms

# Create staging-specific config (without SENAITE section)
cat << 'EOF' | sudo tee /etc/haproxy/haproxy.cfg
global
        log /dev/log    local0
        log /dev/log    local1 notice
        chroot /var/lib/haproxy
        stats socket /run/haproxy/admin.sock mode 660 level admin expose-fd listeners
        stats timeout 30s
        user haproxy
        group haproxy
        daemon

        ca-base /etc/ssl/certs
        crt-base /etc/ssl/private

        ssl-default-bind-ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384
        ssl-default-bind-ciphersuites TLS_AES_128_GCM_SHA256:TLS_AES_256_GCM_SHA384:TLS_CHACHA20_POLY1305_SHA256
        ssl-default-bind-options ssl-min-ver TLSv1.2 no-tls-tickets

defaults
        log     global
        mode    http
        option  httplog
        option  dontlognull
        timeout connect 5000
        timeout client  50000
        timeout server  50000
        errorfile 400 /etc/haproxy/errors/400.http
        errorfile 403 /etc/haproxy/errors/403.http
        errorfile 408 /etc/haproxy/errors/408.http
        errorfile 500 /etc/haproxy/errors/500.http
        errorfile 502 /etc/haproxy/errors/502.http
        errorfile 503 /etc/haproxy/errors/503.http
        errorfile 504 /etc/haproxy/errors/504.http

# ==============================================================================
# EDMS APPLICATION - Port 80
# ==============================================================================

frontend edms_frontend
        bind *:80
        mode http
        
        option httplog
        
        # ACL to identify backend vs frontend requests
        acl is_api path_beg /api/
        acl is_admin path_beg /admin/
        acl is_static path_beg /static/
        acl is_media path_beg /media/
        acl is_health path /health
        acl is_health_slash path /health/
        acl is_haproxy_health path /haproxy-health
        
        # Special health check endpoint
        use_backend haproxy_health_backend if is_haproxy_health
        
        # Route backend requests
        use_backend edms_backend if is_api or is_admin or is_static or is_media or is_health or is_health_slash
        
        # Everything else goes to frontend
        default_backend edms_frontend_backend

backend edms_backend
        mode http
        balance roundrobin
        
        # Health check with trailing slash
        option httpchk GET /health/ HTTP/1.1\r\nHost:\ localhost
        http-check expect status 200
        
        # Backend server
        server edms1 127.0.0.1:8001 check inter 5s fall 3 rise 2
        
        timeout server 60s

backend edms_frontend_backend
        mode http
        balance roundrobin
        
        # Frontend server
        server react1 127.0.0.1:3001 check inter 5s fall 3 rise 2

backend haproxy_health_backend
        mode http
        errorfile 503 /etc/haproxy/errors/200.http

# ==============================================================================
# HAPROXY STATISTICS
# ==============================================================================

listen stats
        bind *:8404
        mode http
        stats enable
        stats uri /stats
        stats refresh 30s
        stats realm HAProxy\ Statistics
        stats auth admin:staging_test
        stats admin if TRUE
        stats show-desc EDMS Staging Load Balancer
EOF

echo "✅ HAProxy config created"
```

### **Step 2.4: Validate Configuration**

```bash
# Test configuration syntax
sudo haproxy -c -f /etc/haproxy/haproxy.cfg

# Expected: "Configuration file is valid"
```

**If you get errors:**
- Check the error message
- Common issues: typos, wrong ports
- Fix and validate again

### **Step 2.5: Start HAProxy**

```bash
# Enable HAProxy to start on boot
sudo systemctl enable haproxy

# Start HAProxy
sudo systemctl start haproxy

# Check status
sudo systemctl status haproxy

# Should show: active (running) in green
```

### **Step 2.6: Verify Port 80 is Listening**

```bash
# Check if HAProxy is listening on port 80
sudo ss -tlnp | grep :80

# Should show HAProxy listening on port 80

# Test basic access
curl http://localhost:80

# Should return HTML (even if it's an error, it means HAProxy responded)
```

---

## ✅ **TEST PHASE 3: Verification (15 min)**

### **Test 3.1: HAProxy Health**

```bash
# Test HAProxy stats page
curl http://localhost:8404/stats

# Or in browser:
# http://172.25.222.103:8404/stats
# Username: admin
# Password: staging_test
```

**In stats page, verify:**
- ✅ `edms_frontend`: OPEN (green)
- ✅ `edms_backend` edms1: UP (green)
- ✅ `edms_frontend_backend` react1: UP (green)

**If any backend shows DOWN:**
```bash
# Check container
docker compose -f docker-compose.prod.yml ps

# Check direct access
curl http://localhost:8001/health/
curl http://localhost:3001

# Check HAProxy logs
sudo journalctl -u haproxy -n 50
```

### **Test 3.2: Backend Routing**

```bash
# Test backend health via HAProxy
curl http://localhost:80/health
# Expected: {"status":"healthy"}

# Test API endpoint
curl http://localhost:80/api/v1/
# Expected: JSON response

# Test admin panel
curl -I http://localhost:80/admin/
# Expected: HTTP 302 or 200

# Test static files
curl -I http://localhost:80/static/admin/css/base.css
# Expected: HTTP 200
```

### **Test 3.3: Frontend Routing**

```bash
# Test frontend home
curl http://localhost:80/
# Expected: HTML with React app

# Test frontend route
curl -I http://localhost:80/login
# Expected: HTTP 200
```

### **Test 3.4: Direct Access Still Works**

```bash
# Verify direct access still works (important!)
curl http://localhost:8001/health/
curl http://localhost:3001

# Both should still work
```

---

## 🌐 **TEST PHASE 4: Browser Testing (20 min)**

### **Test 4.1: Access via Port 80**

**From your computer:**
```
http://172.25.222.103
```

**Expected:**
- ✅ Login page loads
- ✅ No port number needed!
- ✅ Custom app title appears ("TIKVA EDMS")

### **Test 4.2: Full User Workflow**

1. **Login**
   - Username: `admin`
   - Password: [your staging admin password]
   - ✅ Should login successfully

2. **Navigate Dashboard**
   - ✅ Dashboard loads
   - ✅ Sidebar shows custom title
   - ✅ Navigation works

3. **Create Document**
   - Navigate to My Tasks
   - Click "📝 Create Document"
   - Fill in details
   - Upload file
   - Submit
   - ✅ Document created successfully

4. **Test Workflow**
   - Open document
   - Submit for Review
   - ✅ Status changes
   - ✅ No errors

5. **Test Admin Panel**
   - Access: `http://172.25.222.103/admin/`
   - ✅ Admin panel loads
   - ✅ Styling works (static files loaded)
   - ✅ Can view users, documents

### **Test 4.3: Check Browser Console**

**Open browser console (F12):**
- ✅ No errors in console
- ✅ All API calls succeed
- ✅ No CORS errors
- ✅ Network tab shows requests to `/api/v1/...`

### **Test 4.4: Test Performance**

1. **Open multiple tabs**
   - Open 3-5 browser tabs
   - Navigate in all tabs simultaneously
   - ✅ All responsive
   - ✅ No timeouts

2. **Large file upload**
   - Upload a 5-10 MB file
   - ✅ Upload completes
   - ✅ No timeout errors

---

## 📊 **TEST PHASE 5: Integration Tests (10 min)**

### **Test 5.1: Backup System**

```bash
cd ~/edms

# Run backup
./scripts/backup-hybrid.sh

# Should complete successfully
ls -lh backups/

# Backup should be created
```

### **Test 5.2: Cron Jobs**

```bash
# Check cron jobs still exist
crontab -l | grep backup-hybrid.sh

# Should show 3 lines
```

### **Test 5.3: Container Health**

```bash
# Check all containers
docker compose -f docker-compose.prod.yml ps

# All should be healthy
```

---

## 📝 **Test Results Documentation**

Document your findings:

```bash
cat > ~/edms/STAGING_HAPROXY_TEST_RESULTS.txt << EOF
=== STAGING HAPROXY TEST RESULTS ===
Date: $(date)
Tester: $(whoami)
Server: 172.25.222.103

HAPROXY SETUP:
- Installation: SUCCESS/FAILED
- Configuration: SUCCESS/FAILED  
- Service start: SUCCESS/FAILED
- Port 80 listening: YES/NO

BACKEND ROUTING:
- Health endpoint (/health): PASS/FAIL
- API endpoint (/api/v1/): PASS/FAIL
- Admin panel (/admin/): PASS/FAIL
- Static files: PASS/FAIL

FRONTEND ROUTING:
- Home page (/): PASS/FAIL
- React routing: PASS/FAIL

BROWSER TESTING:
- Port 80 access: PASS/FAIL
- Login: PASS/FAIL
- Document creation: PASS/FAIL
- File upload: PASS/FAIL
- Workflow: PASS/FAIL
- Admin panel: PASS/FAIL
- Console errors: YES/NO
- Performance: GOOD/SLOW

INTEGRATION:
- Backup system: WORKING/BROKEN
- Cron jobs: ACTIVE/MISSING
- Direct access (8001/3001): WORKING/BROKEN

HAPROXY STATS:
- Stats page accessible: YES/NO
- Backend status: UP/DOWN
- Frontend status: UP/DOWN

ISSUES FOUND:
[List any issues here]

OVERALL RESULT: PASS/FAIL

READY FOR PRODUCTION: YES/NO

NOTES:
[Additional observations]
EOF

cat ~/edms/STAGING_HAPROXY_TEST_RESULTS.txt
```

---

## ✅ **Success Criteria**

Test is successful when:

- [ ] HAProxy installed and running
- [ ] Port 80 accessible
- [ ] All backend routes work (/health, /api/, /admin/, /static/)
- [ ] Frontend accessible via port 80
- [ ] Login works
- [ ] Document creation works
- [ ] File upload works
- [ ] Workflows function
- [ ] Admin panel works
- [ ] No console errors
- [ ] Performance acceptable
- [ ] Backup system still works
- [ ] Direct access still works (8001, 3001)
- [ ] HAProxy stats shows backends UP

---

## 🔄 **Rollback (if needed)**

If test fails and you want to revert:

```bash
# Stop HAProxy
sudo systemctl stop haproxy
sudo systemctl disable haproxy

# Restore backup config (if any)
if [ -f /etc/haproxy/haproxy.cfg.backup.* ]; then
    sudo cp /etc/haproxy/haproxy.cfg.backup.* /etc/haproxy/haproxy.cfg
fi

# Verify direct access still works
curl http://localhost:3001
curl http://localhost:8001/health/
```

---

## 🎯 **After Successful Test**

Once all tests pass:

1. **Document results** - Fill in test results template
2. **Note any issues** - Document problems and solutions
3. **Review with team** - Share findings
4. **Update production guide** - Add any lessons learned
5. **Schedule production deployment** - You're ready!

---

## 📞 **Next Steps**

### **If Test PASSED ✅**
1. Document test results
2. Review production deployment guide
3. Schedule production deployment
4. Follow same procedure on production

### **If Test FAILED ❌**
1. Document errors
2. Troubleshoot issues
3. Fix problems
4. Re-test on staging
5. Don't proceed to production until staging works

---

## 🚀 **Ready to Test?**

**Start testing now with:**

```bash
# SSH to staging
ssh lims@172.25.222.103

# Follow this guide step by step
cd ~/edms
cat STAGING_HAPROXY_TEST_DEPLOYMENT.md
```

**Time required:** 45-60 minutes  
**Risk:** Low (staging environment)  
**Rollback:** Easy (stop HAProxy)

---

**Good luck with your staging test!** 🧪

**Let me know how it goes and if you encounter any issues!**
