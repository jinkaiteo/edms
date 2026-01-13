# HAProxy Configuration for Multiple Applications

**Scenario:** SENAITE already running on ports 8081/8082, accessed via HAProxy port 7090  
**Goal:** Add EDMS on ports 8001/8002, accessed via HAProxy port 80 (or another port)  
**Approach:** Share HAProxy instance, separate frontends for each app

---

## 🎯 **Configuration Strategy**

### **Current Setup:**
```
Users → HAProxy Port 7090 → SENAITE (ports 8081, 8082)
```

### **Target Setup:**
```
Users → HAProxy Port 7090 → SENAITE (ports 8081, 8082)
Users → HAProxy Port 80   → EDMS (ports 8001, 8002)
```

**OR if port 80 is restricted:**
```
Users → HAProxy Port 7090 → SENAITE (ports 8081, 8082)
Users → HAProxy Port 7091 → EDMS (ports 8001, 8002)
```

---

## 📝 **Updated HAProxy Configuration**

### **Option A: EDMS on Port 80 (Recommended)**

This gives EDMS the standard HTTP port while keeping SENAITE on 7090.

```haproxy
global
        log /dev/log    local0
        log /dev/log    local1 notice
        chroot /var/lib/haproxy
        stats socket /run/haproxy/admin.sock mode 660 level admin
        stats timeout 30s
        user haproxy
        group haproxy
        daemon

        # Default SSL material locations
        ca-base /etc/ssl/certs
        crt-base /etc/ssl/private

        # Modern cipher suite
        ssl-default-bind-ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384
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
# SENAITE APPLICATION (Existing - Port 7090)
# ==============================================================================

frontend senaite_frontend
        bind *:7090
        mode http
        default_backend senaite_backend

backend senaite_backend
        mode http
        balance leastconn
        server server1 127.0.0.1:8081 check
        server server2 127.0.0.1:8082 check

# ==============================================================================
# EDMS APPLICATION (New - Port 80)
# ==============================================================================

frontend edms_frontend
        bind *:80
        mode http
        
        # ACL to route requests
        acl is_api path_beg /api/
        acl is_admin path_beg /admin/
        acl is_static path_beg /static/
        acl is_media path_beg /media/
        acl is_health path /health
        acl is_haproxy_health path /haproxy-health
        
        # Special health check endpoint
        use_backend haproxy_health_backend if is_haproxy_health
        
        # Route backend requests
        use_backend edms_backend if is_api or is_admin or is_static or is_media or is_health
        
        # Default to frontend
        default_backend edms_frontend_backend

backend edms_backend
        mode http
        balance roundrobin
        
        # Health check with trailing slash (Django requires it)
        option httpchk GET /health/ HTTP/1.1\r\nHost:\ localhost
        
        # Backend servers (your EDMS containers)
        server edms1 127.0.0.1:8001 check inter 5s fall 3 rise 2
        server edms2 127.0.0.1:8002 check inter 5s fall 3 rise 2

backend edms_frontend_backend
        mode http
        balance roundrobin
        
        # Frontend servers (React app)
        server react1 127.0.0.1:3001 check inter 5s fall 3 rise 2
        server react2 127.0.0.1:3002 check inter 5s fall 3 rise 2

backend haproxy_health_backend
        mode http
        server health_check 127.0.0.1:8888 check disabled

# ==============================================================================
# HAPROXY STATISTICS PAGE
# ==============================================================================

listen stats
        bind *:8404
        mode http
        stats enable
        stats uri /stats
        stats refresh 30s
        stats auth admin:admin_changeme
        stats admin if TRUE
```

---

### **Option B: EDMS on Port 7091 (Alternative)**

If port 80 is restricted or you want both apps on similar ports:

```haproxy
# Just change this line in the edms_frontend section:
frontend edms_frontend
        bind *:7091  # Changed from 80 to 7091
        mode http
        # ... rest stays the same
```

**Access URLs:**
- SENAITE: `http://<server-ip>:7090`
- EDMS: `http://<server-ip>:7091`

---

## 🔧 **Setup Instructions**

### **Step 1: Backup Current Configuration**

```bash
# SSH to production server
ssh user@<production-ip>

# Backup existing HAProxy config
sudo cp /etc/haproxy/haproxy.cfg /etc/haproxy/haproxy.cfg.backup.$(date +%Y%m%d)

# Verify backup
ls -la /etc/haproxy/haproxy.cfg.backup.*
```

---

### **Step 2: Deploy EDMS Containers**

Before updating HAProxy, deploy EDMS:

```bash
cd /opt/edms

# Run interactive deployment
# IMPORTANT: Use these ports:
# - Backend: 8001, 8002
# - Frontend: 3001, 3002

./deploy-interactive.sh
```

**During prompts:**
```
? Backend port: 8001
? Frontend port: 3001
? Use HAProxy: yes
```

This will deploy the first instance. For the second instance (optional load balancing):

```bash
# Option 1: Deploy second instance manually
# Update docker-compose.prod.yml to use ports 8002 and 3002

# Option 2: Start with single instance
# You can use just one backend (8001) and one frontend (3001)
```

---

### **Step 3: Update HAProxy Configuration**

```bash
# Create new HAProxy config
sudo nano /etc/haproxy/haproxy.cfg

# Paste the updated configuration (from Option A or B above)
# Save and exit (Ctrl+X, Y, Enter)
```

---

### **Step 4: Validate Configuration**

```bash
# Test configuration syntax
sudo haproxy -c -f /etc/haproxy/haproxy.cfg

# Should show: Configuration file is valid
```

**If errors:**
- Check for typos
- Verify indentation
- Check port numbers match your containers

---

### **Step 5: Reload HAProxy**

```bash
# Reload HAProxy (no downtime)
sudo systemctl reload haproxy

# Check status
sudo systemctl status haproxy

# Should show: active (running)
```

---

### **Step 6: Verify SENAITE Still Works**

```bash
# Test SENAITE (make sure we didn't break it!)
curl http://localhost:7090

# Or in browser
# http://<production-ip>:7090
```

**Expected:** SENAITE loads normally ✅

---

### **Step 7: Test EDMS Access**

```bash
# Test EDMS backend
curl http://localhost:80/health
# OR if using port 7091:
curl http://localhost:7091/health

# Expected: {"status":"healthy"}

# Test EDMS frontend
curl http://localhost:80/
# OR:
curl http://localhost:7091/

# Expected: HTML content
```

---

### **Step 8: Browser Testing**

**SENAITE (verify unchanged):**
```
http://<production-ip>:7090
```

**EDMS (new):**
```
http://<production-ip>:80
OR
http://<production-ip>:7091
```

---

## 📊 **Port Allocation Summary**

| Service | HAProxy Port | Container Ports | Purpose |
|---------|-------------|-----------------|---------|
| **SENAITE** | 7090 | 8081, 8082 | Existing LIMS |
| **EDMS** | 80 (or 7091) | 8001, 8002 (backend)<br>3001, 3002 (frontend) | New EDMS |
| **HAProxy Stats** | 8404 | - | Monitoring |

---

## 🎯 **Simplified Option: Single Backend**

If you don't need load balancing yet, start with one container per service:

```haproxy
backend edms_backend
        mode http
        option httpchk GET /health/ HTTP/1.1\r\nHost:\ localhost
        
        # Just one backend server
        server edms1 127.0.0.1:8001 check inter 5s fall 3 rise 2

backend edms_frontend_backend
        mode http
        
        # Just one frontend server
        server react1 127.0.0.1:3001 check inter 5s fall 3 rise 2
```

**Deploy with:**
- Backend port: 8001
- Frontend port: 3001
- No need for 8002 and 3002 yet

---

## 🔍 **Monitoring Both Applications**

### **HAProxy Stats Page**

```
http://<production-ip>:8404/stats
Username: admin
Password: admin_changeme
```

**You'll see:**
- SENAITE frontend and backend status
- EDMS frontend and backend status
- Health check status for all servers
- Request statistics

---

## 🐛 **Troubleshooting**

### **Issue 1: SENAITE Stopped Working**

**Check:**
```bash
# Verify SENAITE backend
curl http://localhost:8081
curl http://localhost:8082

# Check HAProxy routing
sudo journalctl -u haproxy -n 50
```

**Solution:**
```bash
# Restore backup config
sudo cp /etc/haproxy/haproxy.cfg.backup.YYYYMMDD /etc/haproxy/haproxy.cfg
sudo systemctl reload haproxy
```

---

### **Issue 2: EDMS Backend Shows DOWN**

**Check:**
```bash
# Verify EDMS is running
docker compose -f docker-compose.prod.yml ps

# Test direct access
curl http://localhost:8001/health/
# Note the trailing slash!
```

**Solution:**
```bash
# Ensure health check path has trailing slash
option httpchk GET /health/ HTTP/1.1\r\nHost:\ localhost
                           # ^ Important!
```

---

### **Issue 3: Port Conflicts**

**Symptom:** HAProxy won't bind to port 80

**Check:**
```bash
# See what's using port 80
sudo lsof -i :80
```

**Solution:**
- Use port 7091 instead of 80
- Or stop the service using port 80

---

## 📝 **Configuration File Template**

I'll create a ready-to-use configuration file:

```bash
# Save this to: /etc/haproxy/haproxy.cfg

cat << 'EOF' | sudo tee /etc/haproxy/haproxy.cfg
[paste the full configuration from Option A or B above]
EOF

# Validate
sudo haproxy -c -f /etc/haproxy/haproxy.cfg

# Reload
sudo systemctl reload haproxy
```

---

## 🎯 **Recommended Approach**

For your situation, I recommend:

1. **Use Option A (EDMS on port 80)**
   - Gives EDMS the standard HTTP port
   - SENAITE stays on 7090 (unchanged)
   - Most user-friendly

2. **Start with Single Backend**
   - Deploy EDMS with just port 8001 and 3001
   - Add 8002 and 3002 later if needed for load balancing

3. **Test Thoroughly**
   - Verify SENAITE still works
   - Test EDMS functionality
   - Check HAProxy stats page

---

## ✅ **Success Criteria**

Configuration is successful when:

- [ ] SENAITE accessible on port 7090
- [ ] SENAITE functions normally (unchanged)
- [ ] EDMS accessible on port 80 (or 7091)
- [ ] EDMS login works
- [ ] EDMS document creation works
- [ ] HAProxy stats shows all backends UP
- [ ] No errors in HAProxy logs

---

## 📞 **Need Help?**

If you'd like me to:
1. **Generate the exact config** for your setup
2. **Create deployment script** that handles everything
3. **Walk through the setup** step by step

Just let me know! 🚀
