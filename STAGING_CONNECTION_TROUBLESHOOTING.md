# Staging Server Connection Troubleshooting

## 🔴 Issue: SSL_ERROR_RX_RECORD_TOO_LONG

### Error Message:
```
An error occurred during a connection to 172.25.222.103:3001.
SSL received a record that exceeded the maximum permissible length.
Error code: SSL_ERROR_RX_RECORD_TOO_LONG
```

---

## ✅ SOLUTION: Use HTTP, Not HTTPS

### The Problem:
Your browser is trying to access the staging server using **HTTPS** (secure), but the server is configured for **HTTP** (non-secure).

Since you deployed **without HAProxy** and **without SSL certificates**, the server only speaks HTTP on ports 3001 and 8001.

---

## 🎯 Correct URLs to Use

### ✅ Use These URLs (HTTP):

```
Frontend:     http://172.25.222.103:3001
Backend API:  http://172.25.222.103:8001/api/
Admin Panel:  http://172.25.222.103:8001/admin/
Health Check: http://172.25.222.103:8001/health/
```

**Notice**: All start with `http://` NOT `https://`

---

## 🔍 Why This Happens

### Common Causes:

1. **Browser Auto-Upgraded to HTTPS**
   - Modern browsers (Chrome, Firefox) automatically try HTTPS first
   - If you previously accessed a site with HTTPS, browser remembers

2. **HSTS (HTTP Strict Transport Security)**
   - Browser may have cached HTTPS requirement
   - Need to clear browser cache/HSTS cache

3. **Typed "https://" Manually**
   - Easy to type https:// out of habit
   - Must explicitly use http://

---

## 🛠️ Detailed Troubleshooting

### Step 1: Use Correct URL

In your browser address bar, type:
```
http://172.25.222.103:3001
```

**Important**: Make sure it's `http://` not `https://`

---

### Step 2: If Browser Still Redirects to HTTPS

#### Option A: Clear Browser HSTS Cache

**Chrome**:
```
1. Go to: chrome://net-internals/#hsts
2. In "Delete domain security policies"
3. Enter: 172.25.222.103
4. Click "Delete"
5. Try http://172.25.222.103:3001 again
```

**Firefox**:
```
1. Go to: about:preferences#privacy
2. Cookies and Site Data → Manage Data
3. Search for: 172.25.222.103
4. Remove
5. Try http://172.25.222.103:3001 again
```

**Safari**:
```
1. Safari → Preferences → Privacy
2. Manage Website Data
3. Find and remove 172.25.222.103
4. Try http://172.25.222.103:3001 again
```

#### Option B: Use Incognito/Private Window

```
Chrome: Ctrl+Shift+N (Windows) / Cmd+Shift+N (Mac)
Firefox: Ctrl+Shift+P (Windows) / Cmd+Shift+P (Mac)
Safari: Cmd+Shift+N (Mac)
```

Then access: `http://172.25.222.103:3001`

---

### Step 3: Verify Server is Listening

**On staging server**, check if services are listening:

```bash
# Check if frontend is listening on 3001
sudo netstat -tulpn | grep 3001

# Expected output:
tcp6  0  0 :::3001  :::*  LISTEN  12345/docker-proxy

# Check if backend is listening on 8001
sudo netstat -tulpn | grep 8001

# Expected output:
tcp6  0  0 :::8001  :::*  LISTEN  12346/docker-proxy
```

---

### Step 4: Test from Staging Server First

**On staging server**, test locally:

```bash
# Test frontend
curl -I http://localhost:3001/

# Expected: HTTP/1.1 200 OK

# Test backend
curl http://localhost:8001/health/

# Expected: {"status": "healthy", ...}
```

If these work, the services are running correctly.

---

### Step 5: Check Firewall

**On staging server**:

```bash
# Check if firewall is blocking
sudo ufw status

# Should show:
3001/tcp         ALLOW       Anywhere
8001/tcp         ALLOW       Anywhere
```

If not allowed:
```bash
sudo ufw allow 3001/tcp
sudo ufw allow 8001/tcp
```

---

### Step 6: Test Connection from Your Machine

**From your local computer** (not staging server):

```bash
# Test if port is reachable
telnet 172.25.222.103 3001

# Should connect (Ctrl+C to exit)

# Or use curl
curl -v http://172.25.222.103:3001/

# Should return HTML or data
```

---

## 🚨 Common Issues & Solutions

### Issue 1: Connection Timeout

**Symptom**: Browser just keeps loading

**Causes**:
- Firewall blocking connections
- Wrong IP address
- Server not running

**Solutions**:
```bash
# On staging server
sudo ufw allow 3001/tcp
sudo ufw allow 8001/tcp

# Check containers running
docker compose -f docker-compose.prod.yml ps

# Check logs
docker compose -f docker-compose.prod.yml logs frontend
```

---

### Issue 2: Connection Refused

**Symptom**: "Connection refused" error

**Causes**:
- Containers not running
- Services crashed
- Wrong port

**Solutions**:
```bash
# On staging server
# Restart containers
docker compose -f docker-compose.prod.yml restart

# Check status
docker compose -f docker-compose.prod.yml ps

# All should show "Up"
```

---

### Issue 3: 502 Bad Gateway (if using HAProxy)

**Symptom**: "502 Bad Gateway" error

**Cause**: HAProxy can't reach backend services

**Solutions**:
```bash
# Check HAProxy status
sudo systemctl status haproxy

# Check HAProxy logs
sudo tail -f /var/log/haproxy.log

# Restart HAProxy
sudo systemctl restart haproxy
```

---

## 📊 Quick Diagnostic Commands

### On Staging Server:

```bash
# Check all services
docker compose -f docker-compose.prod.yml ps

# Check frontend logs
docker compose -f docker-compose.prod.yml logs frontend | tail -50

# Check backend logs
docker compose -f docker-compose.prod.yml logs backend | tail -50

# Check what ports are listening
sudo netstat -tulpn | grep -E "3001|8001"

# Check firewall
sudo ufw status numbered

# Test locally
curl http://localhost:3001/
curl http://localhost:8001/health/
```

### From Your Local Machine:

```bash
# Test connectivity
ping 172.25.222.103

# Test port reachability
nc -zv 172.25.222.103 3001
nc -zv 172.25.222.103 8001

# Test HTTP
curl -v http://172.25.222.103:3001/
curl -v http://172.25.222.103:8001/health/
```

---

## ✅ Expected Behavior

### When Everything Works:

**Frontend** (`http://172.25.222.103:3001`):
```
Should show: EDMS login page or main application
```

**Backend Health** (`http://172.25.222.103:8001/health/`):
```json
{
  "status": "healthy",
  "timestamp": "2026-01-12T...",
  "database": "connected",
  "redis": "connected"
}
```

**Backend Admin** (`http://172.25.222.103:8001/admin/`):
```
Should show: Django administration login page
```

---

## 🔐 About HTTPS / SSL

### Why No HTTPS?

Your current staging deployment:
- ✅ Uses HTTP (port 80/3001/8001)
- ❌ Does NOT use HTTPS (port 443)
- ❌ No SSL certificates configured

**This is NORMAL for staging!**

### When to Add HTTPS:

**For Production**, you should add HTTPS:
1. Get SSL certificate (Let's Encrypt free)
2. Configure HAProxy with SSL termination
3. Use ports 80 → 443 redirect
4. Then access via `https://yourdomain.com`

**For Staging**, HTTP is fine:
- Internal testing only
- Faster setup
- No certificate management
- Can add HTTPS later if needed

---

## 🎯 Next Steps

### 1. Try Correct URL

```
http://172.25.222.103:3001
```

### 2. If Still Issues, Run Diagnostics

**On staging server**:
```bash
cd ~/edms
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs | tail -100
sudo ufw status
```

**From local machine**:
```bash
ping 172.25.222.103
curl -v http://172.25.222.103:3001/
```

### 3. Report Results

Let me know:
- Did `http://` work? (not `https://`)
- What do you see in browser?
- Output of diagnostic commands

---

## 📋 Success Checklist

- [ ] Using `http://` (not `https://`)
- [ ] All containers running on staging server
- [ ] Firewall allows ports 3001 and 8001
- [ ] Can curl from staging server locally
- [ ] Can ping staging server from local machine
- [ ] Can telnet to ports 3001/8001 from local machine
- [ ] Browser cleared HSTS cache (if needed)
- [ ] Using correct IP: 172.25.222.103

---

## 🎉 TL;DR - Quick Fix

**Use this URL in your browser**:
```
http://172.25.222.103:3001
```

**NOT**:
```
https://172.25.222.103:3001  ❌
```

**That's it!** The "s" in "https" is causing the SSL error.

