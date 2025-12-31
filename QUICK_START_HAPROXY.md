# HAProxy Setup - Quick Start Guide

## 🚀 TL;DR - Three Commands to Fix Login

```bash
# 1. Install HAProxy
sudo bash scripts/setup-haproxy-staging.sh

# 2. Update Docker configuration
bash scripts/update-docker-for-haproxy.sh

# 3. Verify everything works
bash scripts/verify-haproxy-setup.sh
```

Then access your application at: **http://172.28.1.148**

---

## 📋 What Each Script Does

### Script 1: `setup-haproxy-staging.sh`
- Installs HAProxy
- Configures routing rules
- Sets up firewall
- Starts HAProxy service

**Time:** ~2 minutes

### Script 2: `update-docker-for-haproxy.sh`
- Updates `REACT_APP_API_URL` to `/api/v1`
- Configures backend CORS settings
- Rebuilds frontend container
- Restarts all services

**Time:** ~3-5 minutes

### Script 3: `verify-haproxy-setup.sh`
- Runs 25+ verification tests
- Checks all services are healthy
- Validates routing is working
- Shows access URLs

**Time:** ~30 seconds

---

## ✅ Success Indicators

After running all three scripts, you should see:

```
✅ HAProxy is running
✅ Docker containers are up
✅ Backend is healthy
✅ Frontend is healthy
✅ HAProxy routing correctly
✅ External access working
✅ Login endpoint accessible

Tests Passed: 25
Tests Failed: 0
```

---

## 🌐 Access URLs

| What | URL |
|------|-----|
| **Main App** | http://172.28.1.148 |
| **API** | http://172.28.1.148/api/v1/ |
| **Admin** | http://172.28.1.148/admin/ |
| **HAProxy Stats** | http://172.28.1.148:8404/stats |

---

## 🔑 Default Credentials

**HAProxy Stats:**
- Username: `admin`
- Password: `admin_changeme` (Change this!)

**Test Users (if loaded from fixtures):**
- `admin` / `admin123`
- `author01` / `author123`
- `reviewer01` / `reviewer123`

---

## 🐛 If Something Goes Wrong

Run verification to see what failed:
```bash
bash scripts/verify-haproxy-setup.sh
```

Common fixes:
```bash
# HAProxy not running
sudo systemctl start haproxy

# Docker containers not running
docker compose -f docker-compose.prod.yml up -d

# Frontend still using localhost
docker compose -f docker-compose.prod.yml build frontend
docker compose -f docker-compose.prod.yml up -d frontend
```

---

## 📖 Full Documentation

For detailed information, see: **HAPROXY_PRODUCTION_SETUP_GUIDE.md**

---

**Ready?** Run the three commands above and your login issue will be fixed! 🎉
