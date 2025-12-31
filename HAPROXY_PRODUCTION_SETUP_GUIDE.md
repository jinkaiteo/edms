# HAProxy Production Setup Guide for EDMS Staging Server

## 🎯 Overview

This guide will help you set up HAProxy as a reverse proxy for your EDMS application on the staging server (`172.28.1.148`). HAProxy will provide a single entry point on port 80, routing traffic to your frontend and backend containers.

---

## 📋 Prerequisites

- Ubuntu/Debian server with sudo access
- Docker and Docker Compose installed
- EDMS repository cloned to `/home/lims/edms-staging` (or your preferred location)
- Ports 80, 443, and 8404 available (not blocked by firewall)

---

## 🏗️ Architecture Before and After

### Current Architecture (With Login Issue)
```
User Browser
    ↓
http://172.28.1.148:3001 (Frontend)
    ↓
Try to call: http://localhost:8001/api/v1 ❌
    ↓
Fails (localhost = user's computer, not server)
```

### New Architecture (With HAProxy)
```
User Browser
    ↓
http://172.28.1.148 (port 80) → HAProxy
    ↓
    ├─ / (frontend requests) → Frontend Container (3001)
    │                                 ↓
    │                          Nginx proxies /api/ → Backend (8000 internal)
    │
    └─ /api/ (API requests) → Backend Container (8001)
```

**Benefits:**
- ✅ Single entry point on standard port 80
- ✅ Clean URLs for users
- ✅ Backend not directly exposed
- ✅ Easy to add SSL/HTTPS later
- ✅ Load balancing ready
- ✅ Production-grade architecture

---

## 🚀 Installation Steps

### Step 1: Prepare Your Server

SSH into your staging server:

```bash
ssh lims@172.28.1.148
cd /home/lims/edms-staging
```

### Step 2: Install HAProxy

Run the automated installation script:

```bash
sudo bash scripts/setup-haproxy-staging.sh
```

**What this script does:**
1. Installs HAProxy (latest version from Ubuntu repos)
2. Backs up any existing HAProxy configuration
3. Installs the EDMS HAProxy configuration
4. Validates the configuration
5. Configures firewall rules (if UFW is active)
6. Enables and starts HAProxy service
7. Verifies HAProxy is running correctly

**Expected output:**
```
================================================
HAProxy Setup for Staging Server
================================================
✅ HAProxy installed successfully
✅ Configuration is valid
✅ HAProxy is running
✅ HAProxy listening on port 80
```

### Step 3: Update Docker Configuration

Run the Docker update script:

```bash
bash scripts/update-docker-for-haproxy.sh
```

**What this script does:**
1. Backs up current `docker-compose.prod.yml` and `.env`
2. Updates `REACT_APP_API_URL` from `http://localhost:8001/api/v1` to `/api/v1`
3. Updates `.env` with correct `ALLOWED_HOSTS` and `CORS_ALLOWED_ORIGINS`
4. Rebuilds frontend container with new configuration
5. Restarts all Docker services
6. Verifies services are healthy

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

### Step 4: Verify Setup

Run the verification script:

```bash
bash scripts/verify-haproxy-setup.sh
```

**What this script checks:**
1. HAProxy service status
2. Port bindings (80, 8404)
3. Docker container status
4. Direct container health checks
5. HAProxy routing functionality
6. External access from staging IP
7. Configuration correctness
8. API authentication endpoint
9. HAProxy stats page
10. Security headers

**Expected output:**
```
================================================
Verification Summary
================================================
Tests Passed: 25
Tests Failed: 0

✅ All tests passed! HAProxy setup is working correctly.
```

### Step 5: Create Initial Users

If you haven't already created users:

```bash
# Option 1: Create superuser interactively
docker compose -f docker-compose.prod.yml exec backend python manage.py createsuperuser

# Option 2: Load fixture users
docker compose -f docker-compose.prod.yml exec backend python manage.py loaddata backend/fixtures/initial_users.json
```

**Test users from fixture:**
- Username: `admin` / Password: `admin123`
- Username: `author01` / Password: `author123`
- Username: `reviewer01` / Password: `reviewer123`

### Step 6: Test Login

Open your browser and navigate to:

```
http://172.28.1.148
```

Try logging in with one of the test users. Login should now work correctly!

---

## 🔍 Access Points

After successful setup:

| Service | URL | Notes |
|---------|-----|-------|
| **Main Application** | `http://172.28.1.148` | Clean URL on port 80 |
| **API Endpoints** | `http://172.28.1.148/api/v1/` | Routed through HAProxy |
| **Django Admin** | `http://172.28.1.148/admin/` | Backend admin interface |
| **HAProxy Stats** | `http://172.28.1.148:8404/stats` | Username: `admin` / Password: `admin_changeme` |

---

## 🛠️ Useful Commands

### HAProxy Management

```bash
# Check HAProxy status
sudo systemctl status haproxy

# Restart HAProxy
sudo systemctl restart haproxy

# View HAProxy logs
sudo journalctl -u haproxy -f

# Test configuration
sudo haproxy -c -f /etc/haproxy/haproxy.cfg

# Reload configuration (no downtime)
sudo systemctl reload haproxy
```

### Docker Management

```bash
# Check container status
docker compose -f docker-compose.prod.yml ps

# View logs
docker compose -f docker-compose.prod.yml logs -f

# Restart services
docker compose -f docker-compose.prod.yml restart

# Rebuild and restart frontend
docker compose -f docker-compose.prod.yml build frontend
docker compose -f docker-compose.prod.yml up -d frontend
```

### Testing

```bash
# Test HAProxy health
curl http://localhost/haproxy-health

# Test backend API
curl http://localhost/api/v1/

# Test backend health
curl http://localhost/health

# Test login endpoint
curl -X POST http://localhost/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

---

## 🔧 Configuration Files

### HAProxy Configuration

**Location:** `/etc/haproxy/haproxy.cfg`

**Key sections:**

```haproxy
# Frontend - receives all traffic on port 80
frontend http_frontend
    bind *:80
    
    # Route API requests to backend
    acl is_api path_beg /api/
    use_backend backend_django if is_api
    
    # Route everything else to frontend
    default_backend frontend_react

# Backend - Django API (port 8001)
backend backend_django
    server django1 127.0.0.1:8001 check

# Backend - React Frontend (port 3001)
backend frontend_react
    server react1 127.0.0.1:3001 check
```

### Docker Compose Frontend Configuration

**Location:** `docker-compose.prod.yml`

```yaml
frontend:
  environment:
    - REACT_APP_API_URL=/api/v1  # Relative URL
    - NODE_ENV=production
  ports:
    - "3001:80"  # Internal, accessed by HAProxy
```

### Environment Variables

**Location:** `.env`

```bash
# Network Configuration
ALLOWED_HOSTS=172.28.1.148,localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://172.28.1.148,http://localhost

# Port Configuration
BACKEND_PORT=8001
FRONTEND_PORT=3001
```

---

## 🐛 Troubleshooting

### Issue: Cannot access application on port 80

**Check:**
```bash
# Is HAProxy running?
sudo systemctl status haproxy

# Is it listening on port 80?
sudo netstat -tuln | grep :80

# Check firewall
sudo ufw status
```

**Fix:**
```bash
# Start HAProxy
sudo systemctl start haproxy

# Allow port 80 in firewall
sudo ufw allow 80/tcp
```

### Issue: Login still fails

**Check:**
```bash
# Verify frontend is using relative URL
docker compose -f docker-compose.prod.yml exec frontend env | grep REACT_APP_API_URL

# Should show: REACT_APP_API_URL=/api/v1
```

**Fix:**
```bash
# If it shows localhost, rebuild frontend
docker compose -f docker-compose.prod.yml build frontend
docker compose -f docker-compose.prod.yml up -d frontend
```

### Issue: 502 Bad Gateway

**Check:**
```bash
# Are containers running?
docker compose -f docker-compose.prod.yml ps

# Check backend health
curl http://localhost:8001/health

# Check frontend health
curl http://localhost:3001/health
```

**Fix:**
```bash
# Restart containers
docker compose -f docker-compose.prod.yml restart
```

### Issue: HAProxy stats page not accessible

**Check:**
```bash
# Is HAProxy listening on 8404?
sudo netstat -tuln | grep :8404

# Check firewall
sudo ufw status | grep 8404
```

**Fix:**
```bash
# Allow stats port
sudo ufw allow 8404/tcp
sudo systemctl restart haproxy
```

### Issue: CORS errors in browser console

**Check:**
```bash
# Verify CORS settings in .env
grep CORS_ALLOWED_ORIGINS .env

# Should include: http://172.28.1.148
```

**Fix:**
```bash
# Update .env
echo "CORS_ALLOWED_ORIGINS=http://172.28.1.148,http://localhost" >> .env

# Restart backend
docker compose -f docker-compose.prod.yml restart backend
```

---

## 🔒 Security Considerations

### 1. Change HAProxy Stats Password

Edit `/etc/haproxy/haproxy.cfg`:

```haproxy
listen stats
    bind *:8404
    stats auth admin:YOUR_STRONG_PASSWORD_HERE  # Change this!
```

Then reload:
```bash
sudo systemctl reload haproxy
```

### 2. Update Django Secret Keys

Generate new secrets:

```bash
# Generate Django SECRET_KEY
python3 -c "import secrets; print(secrets.token_urlsafe(50))"

# Generate EDMS_MASTER_KEY
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Update in `.env` file and restart:

```bash
docker compose -f docker-compose.prod.yml restart backend
```

### 3. Restrict HAProxy Stats Access (Optional)

To restrict stats page to localhost only:

```haproxy
listen stats
    bind 127.0.0.1:8404  # Only accessible from server
```

Then access via SSH tunnel:
```bash
ssh -L 8404:localhost:8404 lims@172.28.1.148
# Access at http://localhost:8404/stats
```

### 4. Set Up Firewall Rules

```bash
# Allow HTTP
sudo ufw allow 80/tcp

# Allow HTTPS (for future SSL)
sudo ufw allow 443/tcp

# Allow SSH
sudo ufw allow 22/tcp

# Restrict stats page to specific IP (optional)
sudo ufw allow from YOUR_IP_ADDRESS to any port 8404

# Enable firewall
sudo ufw enable
```

---

## 🚀 Next Steps

### 1. SSL/HTTPS Setup

Once you have a domain name and SSL certificate:

1. Edit `/etc/haproxy/haproxy.cfg` and uncomment the HTTPS section
2. Update the certificate path
3. Reload HAProxy

```bash
sudo systemctl reload haproxy
```

### 2. Domain Name Configuration

If you have a domain name (e.g., `edms.example.com`):

1. Point DNS A record to `172.28.1.148`
2. Update `.env`:
   ```bash
   ALLOWED_HOSTS=edms.example.com,172.28.1.148,localhost
   CORS_ALLOWED_ORIGINS=https://edms.example.com,http://172.28.1.148
   ```
3. Update HAProxy server_name if needed
4. Restart services

### 3. Load Balancing

To add more backend instances for load balancing:

1. Update `docker-compose.prod.yml` to create multiple backend containers
2. Update HAProxy configuration to include all backend servers
3. HAProxy will automatically balance load using `roundrobin`

### 4. Monitoring

Consider setting up:
- Log aggregation (ELK stack, Grafana)
- Uptime monitoring (UptimeRobot, Pingdom)
- Performance monitoring (New Relic, DataDog)
- HAProxy stats dashboard customization

---

## 📊 Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    Internet/Network                      │
└───────────────────────┬─────────────────────────────────┘
                        │
                        ▼
              ┌─────────────────┐
              │  HAProxy :80    │ ◄─── Single Entry Point
              │  (Port 80/443)  │
              └────────┬────────┘
                       │
          ┌────────────┴────────────┐
          │                         │
          ▼                         ▼
┌──────────────────┐      ┌──────────────────┐
│  Frontend :3001  │      │  Backend :8001   │
│  (React + Nginx) │      │  (Django + DRF)  │
└────────┬─────────┘      └────────┬─────────┘
         │                         │
         │ /api/ → Backend :8000   │
         └─────────────────────────┘
                  │
                  ▼
         ┌────────────────┐
         │  PostgreSQL    │
         │  Redis         │
         └────────────────┘
```

---

## 📝 Summary

**What we accomplished:**

1. ✅ Installed and configured HAProxy
2. ✅ Updated Docker configuration to use relative API URLs
3. ✅ Set up proper CORS and allowed hosts
4. ✅ Created single entry point on port 80
5. ✅ Enabled HAProxy statistics monitoring
6. ✅ Fixed login issue by using frontend nginx proxy
7. ✅ Created verification and testing scripts
8. ✅ Set up production-grade architecture

**Result:**
- Clean URLs: `http://172.28.1.148` (no ports)
- Working authentication
- Production-ready setup
- Easy to add SSL/HTTPS
- Monitoring capabilities
- Scalable architecture

---

## 📞 Support

If you encounter issues:

1. Run verification script: `bash scripts/verify-haproxy-setup.sh`
2. Check logs:
   - HAProxy: `sudo journalctl -u haproxy -f`
   - Docker: `docker compose -f docker-compose.prod.yml logs -f`
3. Review this guide's troubleshooting section
4. Check HAProxy stats at `http://172.28.1.148:8404/stats`

---

**Last Updated:** 2026-01-01  
**Version:** 1.0  
**Server:** 172.28.1.148 (staging)  
**Status:** Ready for deployment
