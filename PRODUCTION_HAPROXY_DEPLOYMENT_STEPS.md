# Production HAProxy Deployment - Step-by-Step Guide

**Target Server:** Production (with SENAITE on HAProxy 7090)  
**Goal:** Add EDMS on HAProxy port 80  
**Estimated Time:** 30-45 minutes  
**Date:** 2026-01-12

---

## 🎯 **What We're Doing**

Adding EDMS to your production server that already has:
- ✅ SENAITE running on HAProxy port 7090 (backends: 8081, 8082)
- ✅ HAProxy already installed and configured

We will:
- ✅ Deploy EDMS containers on ports 8001 (backend) and 3001 (frontend)
- ✅ Update HAProxy config to add EDMS on port 80
- ✅ Keep SENAITE completely unchanged
- ✅ Test both applications work

---

## ⚠️ **CRITICAL: Before You Start**

### **1. Backup Everything**
```bash
# Backup HAProxy config
sudo cp /etc/haproxy/haproxy.cfg /etc/haproxy/haproxy.cfg.backup.$(date +%Y%m%d_%H%M%S)

# Verify backup created
ls -la /etc/haproxy/*.backup*
```

### **2. Verify SENAITE is Working**
```bash
# Test SENAITE access
curl http://localhost:7090

# Or in browser
# http://<production-ip>:7090
```

**DO NOT PROCEED if SENAITE is not working!**

### **3. Check Port Availability**
```bash
# Check if port 80 is available
sudo lsof -i :80

# If something is using port 80, you have two options:
# A. Stop that service
# B. Use port 7091 instead (change in haproxy-production.cfg)
```

### **4. Verify Required Ports are Free**
```bash
# Check EDMS ports
sudo lsof -i :8001  # Should show nothing
sudo lsof -i :3001  # Should show nothing

# If ports are in use, choose different ports
```

---

## 📦 **PHASE 1: Deploy EDMS Application (15 min)**

### **Step 1.1: Prepare Directory**

```bash
# SSH to production server
ssh user@<production-ip>

# Create EDMS directory
sudo mkdir -p /opt/edms
sudo chown $USER:$USER /opt/edms
cd /opt/edms
```

### **Step 1.2: Clone Repository**

```bash
# Clone EDMS repository
git clone https://github.com/jinkaiteo/edms.git .

# Switch to develop branch
git checkout develop

# Verify latest code
git log --oneline -5

# Should show recent commits including:
# - 7826e31 docs: Add HAProxy multi-application configuration guide
```

### **Step 1.3: Run Interactive Deployment**

```bash
# Make script executable
chmod +x deploy-interactive.sh

# Run deployment
./deploy-interactive.sh
```

### **Step 1.4: Answer Deployment Prompts**

**IMPORTANT PORT CONFIGURATION:**

```
? Server IP address: <Press Enter for auto-detect>
? Server hostname: edms-production

? Application title: <Your company name or "EDMS">

? Backend port: 8001      ← CRITICAL: Use 8001
? Frontend port: 3001     ← CRITICAL: Use 3001
? PostgreSQL port: 5432   ← Use default
? Redis port: 6379        ← Use default

? Database name: edms_production
? Database user: edms_prod_user
? Database password: <Strong 12+ character password>

? Redis password: <Enter password or press Enter>

? Django secret key: <Press Enter - auto-generated>
? Debug mode: no
? Allowed hosts: <production-ip>,localhost,127.0.0.1

? Use HAProxy: yes        ← CRITICAL: Say YES
```

**Review configuration and confirm:** `Y`

### **Step 1.5: Wait for Deployment**

Watch for these phases:
1. ✅ Docker containers deployed
2. ✅ Storage permissions configured
3. ✅ Database initialized
4. ✅ Admin user created
5. ✅ Backup automation configured

**Expected time:** 10-15 minutes

### **Step 1.6: Verify EDMS Containers Running**

```bash
cd /opt/edms

# Check container status
docker compose -f docker-compose.prod.yml ps

# Should show 6 containers running:
# - edms_prod_backend (port 8001)
# - edms_prod_frontend (port 3001)
# - edms_prod_db
# - edms_prod_redis
# - edms_prod_celery_worker
# - edms_prod_celery_beat
```

### **Step 1.7: Test EDMS Direct Access (Before HAProxy)**

```bash
# Test backend directly
curl http://localhost:8001/health/
# Expected: {"status":"healthy"}

# Test frontend directly
curl http://localhost:3001
# Expected: HTML content

# If both work, proceed to HAProxy configuration
```

**✅ CHECKPOINT: EDMS containers must be running before proceeding!**

---

## 🔧 **PHASE 2: Update HAProxy Configuration (10 min)**

### **Step 2.1: Download New Config**

```bash
cd /opt/edms

# Pull the prepared HAProxy config
git pull origin develop

# Verify the config file exists
ls -la haproxy-production.cfg
cat haproxy-production.cfg
```

### **Step 2.2: Review Configuration**

**IMPORTANT:** Review the config to ensure it matches your setup:

```bash
# Check SENAITE section (should match your existing config)
grep -A 10 "senaite_frontend" haproxy-production.cfg

# Check EDMS section (should use ports 8001 and 3001)
grep -A 10 "edms_backend" haproxy-production.cfg
```

### **Step 2.3: Copy Config to HAProxy**

```bash
# Copy to HAProxy directory
sudo cp haproxy-production.cfg /etc/haproxy/haproxy.cfg

# Verify file permissions
ls -la /etc/haproxy/haproxy.cfg
```

### **Step 2.4: Validate Configuration**

```bash
# CRITICAL: Test configuration syntax
sudo haproxy -c -f /etc/haproxy/haproxy.cfg
```

**Expected output:**
```
Configuration file is valid
```

**If you see errors:**
- Check the error message carefully
- Common issues:
  - Typos in server addresses
  - Wrong port numbers
  - Missing files (like error pages)
- Fix errors before proceeding

### **Step 2.5: Reload HAProxy**

```bash
# Reload HAProxy (zero downtime!)
sudo systemctl reload haproxy

# NOT restart - reload is safer!

# Check status
sudo systemctl status haproxy
```

**Expected:** `active (running)` in green

**If HAProxy failed to reload:**
```bash
# Check logs
sudo journalctl -u haproxy -n 50

# Restore backup if needed
sudo cp /etc/haproxy/haproxy.cfg.backup.* /etc/haproxy/haproxy.cfg
sudo systemctl reload haproxy
```

---

## ✅ **PHASE 3: Verification & Testing (15 min)**

### **Step 3.1: Verify SENAITE Still Works (CRITICAL!)**

```bash
# Test SENAITE via command line
curl http://localhost:7090
```

**In browser:**
```
http://<production-ip>:7090
```

**✅ MUST WORK!** If SENAITE is broken, rollback immediately:
```bash
sudo cp /etc/haproxy/haproxy.cfg.backup.* /etc/haproxy/haproxy.cfg
sudo systemctl reload haproxy
```

### **Step 3.2: Test EDMS via HAProxy**

```bash
# Test EDMS backend health
curl http://localhost:80/health
# Expected: {"status":"healthy"}

# Test EDMS API
curl http://localhost:80/api/v1/
# Expected: JSON response

# Test EDMS frontend
curl http://localhost:80/
# Expected: HTML content
```

### **Step 3.3: Check HAProxy Stats**

```bash
# View stats in terminal
curl http://localhost:8404/stats

# Or in browser
# http://<production-ip>:8404/stats
# Username: admin
# Password: admin_changeme
```

**Verify in stats page:**
- ✅ `senaite_frontend`: OPEN (green)
- ✅ `senaite_backend` servers: UP (green)
- ✅ `edms_frontend`: OPEN (green)
- ✅ `edms_backend` server: UP (green)
- ✅ `edms_frontend_backend` server: UP (green)

**If any backend shows DOWN:**
```bash
# Check the specific container
docker compose -f /opt/edms/docker-compose.prod.yml ps

# Check backend health directly
curl http://localhost:8001/health/
curl http://localhost:3001

# Check HAProxy logs
sudo journalctl -u haproxy -n 50
```

### **Step 3.4: Browser Testing - SENAITE**

**URL:** `http://<production-ip>:7090`

**Actions:**
1. Login to SENAITE
2. Navigate around
3. Verify all functionality works
4. **MUST work exactly as before!**

### **Step 3.5: Browser Testing - EDMS**

**URL:** `http://<production-ip>:80`

**OR** `http://<production-ip>` (port 80 is default)

**Actions:**
1. ✅ Login page loads (with your custom title)
2. ✅ Login with admin credentials
3. ✅ Dashboard loads
4. ✅ Navigate to My Tasks
5. ✅ Click "Create Document" button
6. ✅ Create test document
7. ✅ Upload test file
8. ✅ Submit document
9. ✅ Verify document appears in list

**Check browser console (F12):**
- ✅ No errors in console
- ✅ All API calls succeed
- ✅ No CORS errors

### **Step 3.6: Test EDMS Workflow**

1. Open test document
2. Submit for review
3. Verify status changes
4. No errors should appear

---

## 📊 **PHASE 4: Final Configuration (5 min)**

### **Step 4.1: Update Firewall (if applicable)**

```bash
# Allow port 80 from internal network
sudo ufw allow from <internal-network-subnet> to any port 80

# Example for 192.168.1.0/24 network:
sudo ufw allow from 192.168.1.0/24 to any port 80

# Or allow from anywhere (if appropriate)
sudo ufw allow 80/tcp

# Check firewall status
sudo ufw status
```

### **Step 4.2: Set HAProxy Admin Password**

```bash
# Change default stats password
sudo nano /etc/haproxy/haproxy.cfg

# Find this line:
# stats auth admin:admin_changeme

# Change to:
# stats auth admin:YourSecurePassword123!

# Save and reload
sudo systemctl reload haproxy
```

### **Step 4.3: Document Access URLs**

Create a reference file:

```bash
cat > /opt/edms/ACCESS_URLS.txt << EOF
=== PRODUCTION ACCESS URLS ===
Date: $(date)

SENAITE:
  URL: http://<production-ip>:7090
  Backend Ports: 8081, 8082
  Status: Unchanged

EDMS:
  URL: http://<production-ip>:80
  OR:  http://<production-ip>
  Backend Port: 8001
  Frontend Port: 3001
  Admin: http://<production-ip>:80/admin/

HAProxy Stats:
  URL: http://<production-ip>:8404/stats
  Username: admin
  Password: [Your secure password]

Admin Credentials:
  EDMS Username: admin
  EDMS Password: [Document securely]
  Database: edms_production
  Database User: edms_prod_user
  Database Password: [Document securely]
EOF

# Set secure permissions
chmod 600 /opt/edms/ACCESS_URLS.txt

# View
cat /opt/edms/ACCESS_URLS.txt
```

---

## 🎉 **SUCCESS CHECKLIST**

Mark each item as you verify:

### **SENAITE (Must be unchanged):**
- [ ] Accessible via port 7090
- [ ] Login works
- [ ] All functionality works
- [ ] No errors or slowdowns
- [ ] HAProxy stats shows backends UP

### **EDMS (New):**
- [ ] Accessible via port 80 (no port number needed!)
- [ ] Login page shows custom title
- [ ] Login works with admin credentials
- [ ] Dashboard loads
- [ ] Can create documents
- [ ] Can upload files
- [ ] Workflows function correctly
- [ ] No browser console errors
- [ ] HAProxy stats shows backends UP

### **HAProxy:**
- [ ] Service running (`systemctl status haproxy`)
- [ ] No errors in logs (`journalctl -u haproxy`)
- [ ] Stats page accessible
- [ ] All backends show UP
- [ ] Stats password changed from default

### **System:**
- [ ] All Docker containers healthy
- [ ] Backup cron jobs installed
- [ ] Access URLs documented
- [ ] Credentials documented securely
- [ ] Firewall configured (if applicable)

---

## 🚨 **ROLLBACK PROCEDURE**

If anything goes wrong:

### **Emergency Rollback:**

```bash
# 1. Restore HAProxy config
sudo cp /etc/haproxy/haproxy.cfg.backup.* /etc/haproxy/haproxy.cfg

# 2. Reload HAProxy
sudo systemctl reload haproxy

# 3. Verify SENAITE works
curl http://localhost:7090

# 4. Stop EDMS containers (optional)
cd /opt/edms
docker compose -f docker-compose.prod.yml down
```

### **Complete Rollback:**

```bash
# Remove EDMS completely
cd /opt/edms
docker compose -f docker-compose.prod.yml down -v

# Remove EDMS directory
sudo rm -rf /opt/edms

# Restore original HAProxy config
sudo cp /etc/haproxy/haproxy.cfg.backup.* /etc/haproxy/haproxy.cfg
sudo systemctl reload haproxy
```

---

## 📊 **Post-Deployment Monitoring**

### **First 24 Hours:**

```bash
# Monitor HAProxy logs
sudo journalctl -u haproxy -f

# Monitor Docker containers
docker compose -f /opt/edms/docker-compose.prod.yml ps

# Check HAProxy stats regularly
# http://<production-ip>:8404/stats
```

### **Watch for:**
- Memory usage
- CPU usage
- Error rates in HAProxy stats
- Backend health status
- Response times

---

## 📞 **Troubleshooting Quick Reference**

| Issue | Check | Solution |
|-------|-------|----------|
| SENAITE broken | Logs, config | Rollback immediately |
| EDMS backend DOWN | Port 8001, health check | Check container, restart |
| Port 80 won't bind | `lsof -i :80` | Stop conflicting service |
| 502 Bad Gateway | Backend status | Check EDMS containers |
| 504 Gateway Timeout | Backend health | Increase timeout, check backend |
| Stats page 401 | Password | Check username/password |

---

## ✅ **Deployment Complete!**

**You now have:**
- ✅ SENAITE on port 7090 (unchanged)
- ✅ EDMS on port 80 (new)
- ✅ Single HAProxy managing both
- ✅ Monitoring via stats page
- ✅ Automated backups configured

**Access URLs:**
- SENAITE: `http://<production-ip>:7090`
- EDMS: `http://<production-ip>`
- Stats: `http://<production-ip>:8404/stats`

**Next Steps:**
1. Announce EDMS to users
2. Create user accounts
3. Import existing documents (if applicable)
4. Monitor performance for first week
5. Schedule quarterly review

---

**🎊 Congratulations on your multi-application HAProxy deployment!** 🚀

---

**Deployment Date:** [Fill in]  
**Deployed By:** [Fill in]  
**SENAITE Status:** Unchanged ✅  
**EDMS Status:** Live on Port 80 ✅
