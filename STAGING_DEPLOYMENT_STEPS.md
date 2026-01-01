# Staging Server Deployment Steps

## ✅ Git Push Complete!

All HAProxy files have been pushed to GitHub (develop branch).

---

## 🚀 **Now Run These Commands on Staging Server**

### Step 1: SSH to Staging Server

```bash
ssh lims@172.28.1.148
```

### Step 2: Navigate to Project Directory

```bash
cd /home/lims/edms-staging
```

### Step 3: Pull Latest Changes from GitHub

```bash
# Check current branch
git branch

# If not on develop, switch to it
git checkout develop

# Pull latest changes
git pull origin develop
```

**Expected output:**
```
remote: Enumerating objects...
remote: Counting objects: 100% (XX/XX), done.
Updating 1643a9f..341168b
Fast-forward
 DEPLOYMENT_OPTIONS_HAPROXY.md           | 288 ++++++++++++++++++
 HAPROXY_PRODUCTION_SETUP_GUIDE.md       | 850 ++++++++++++++++++++++++++++++++++++++++++++++
 QUICK_START_HAPROXY.md                  | 85 +++++
 infrastructure/haproxy/haproxy.cfg      | 157 +++++++++
 scripts/setup-haproxy-staging.sh        | 220 ++++++++++++
 scripts/update-docker-for-haproxy.sh    | 300 ++++++++++++++++
 scripts/verify-haproxy-setup.sh         | 250 ++++++++++++++
 7 files changed, 2150 insertions(+)
```

### Step 4: Verify Files Were Pulled

```bash
# Check HAProxy config exists
ls -lh infrastructure/haproxy/haproxy.cfg

# Check scripts exist
ls -lh scripts/*haproxy*.sh

# Check documentation
ls -lh HAPROXY*.md QUICK_START*.md
```

### Step 5: Make Scripts Executable

```bash
chmod +x scripts/setup-haproxy-staging.sh
chmod +x scripts/update-docker-for-haproxy.sh
chmod +x scripts/verify-haproxy-setup.sh
```

### Step 6: Install HAProxy

```bash
sudo bash scripts/setup-haproxy-staging.sh
```

**What this does:**
- Installs HAProxy package
- Copies configuration to `/etc/haproxy/haproxy.cfg`
- Validates configuration
- Configures firewall (if UFW is active)
- Starts HAProxy service

**Expected output:**
```
================================================
HAProxy Setup for Staging Server
================================================
✅ HAProxy installed successfully
✅ Configuration is valid
✅ HAProxy is running
✅ HAProxy listening on port 80
✅ HAProxy stats page available on port 8404
```

### Step 7: Update Docker Configuration

```bash
bash scripts/update-docker-for-haproxy.sh
```

**What this does:**
- Backs up current configuration
- Updates `REACT_APP_API_URL` to `/api/v1`
- Updates `.env` with correct settings
- Rebuilds frontend container
- Restarts all services

**Expected output:**
```
================================================
Configuration Complete!
================================================
✅ Frontend container rebuilt successfully
✅ All services started
✅ Backend is healthy
✅ Frontend is healthy
✅ HAProxy is routing correctly
```

### Step 8: Verify Setup

```bash
bash scripts/verify-haproxy-setup.sh
```

**What this does:**
- Runs 25+ verification tests
- Checks all services are healthy
- Validates routing is working
- Shows access URLs

**Expected output:**
```
================================================
Verification Summary
================================================
Tests Passed: 25
Tests Failed: 0

✅ All tests passed! HAProxy setup is working correctly.
```

---

## 🌐 **Test Your Application**

Open your browser and go to:

```
http://172.28.1.148
```

Try logging in with test credentials:
- Username: `admin`
- Password: `admin123`

**Login should now work!** ✅

---

## 📊 **Access Points After Deployment**

| Service | URL | Credentials |
|---------|-----|-------------|
| **Main Application** | http://172.28.1.148 | Your user accounts |
| **API Endpoints** | http://172.28.1.148/api/v1/ | - |
| **Django Admin** | http://172.28.1.148/admin/ | Superuser credentials |
| **HAProxy Stats** | http://172.28.1.148:8404/stats | admin / admin_changeme |

---

## 🛠️ **Useful Commands**

### Check Service Status

```bash
# HAProxy status
sudo systemctl status haproxy

# Docker containers status
docker compose -f docker-compose.prod.yml ps

# View logs
docker compose -f docker-compose.prod.yml logs -f
```

### Quick Health Checks

```bash
# Test HAProxy
curl http://localhost/haproxy-health

# Test backend
curl http://localhost/health

# Test API
curl http://localhost/api/v1/
```

---

## 🐛 **If Something Goes Wrong**

### HAProxy not starting?

```bash
# Check HAProxy logs
sudo journalctl -u haproxy -n 50

# Validate configuration
sudo haproxy -c -f /etc/haproxy/haproxy.cfg

# Restart HAProxy
sudo systemctl restart haproxy
```

### Docker containers not running?

```bash
# Check container logs
docker compose -f docker-compose.prod.yml logs backend frontend

# Restart containers
docker compose -f docker-compose.prod.yml restart

# Or full rebuild
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml up -d
```

### Login still not working?

```bash
# Verify frontend is using correct API URL
docker compose -f docker-compose.prod.yml exec frontend env | grep REACT_APP_API_URL

# Should show: REACT_APP_API_URL=/api/v1

# If not, rebuild frontend
docker compose -f docker-compose.prod.yml build frontend
docker compose -f docker-compose.prod.yml up -d frontend
```

---

## 📋 **Checklist**

Use this checklist as you go:

- [ ] SSH to staging server
- [ ] Navigate to project directory
- [ ] Pull latest changes from GitHub
- [ ] Verify files were downloaded
- [ ] Make scripts executable
- [ ] Run HAProxy installation script
- [ ] Run Docker update script
- [ ] Run verification script
- [ ] Test login in browser
- [ ] Verify all services accessible

---

## 🎉 **Success Indicators**

You'll know everything is working when:

1. ✅ All three scripts complete without errors
2. ✅ Verification shows "Tests Passed: 25, Tests Failed: 0"
3. ✅ You can access http://172.28.1.148 (no port number)
4. ✅ Login works successfully
5. ✅ HAProxy stats page loads at http://172.28.1.148:8404/stats

---

## 📞 **Need Help?**

Reference these documentation files:
- **Full Guide:** `HAPROXY_PRODUCTION_SETUP_GUIDE.md`
- **Quick Start:** `QUICK_START_HAPROXY.md`
- **Deployment Options:** `DEPLOYMENT_OPTIONS_HAPROXY.md`

---

**Ready to deploy?** Copy these commands and run them on your staging server! 🚀
