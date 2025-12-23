# HAProxy Integration Guide for EDMS

## Overview

This guide explains how to integrate EDMS with HAProxy as a reverse proxy/load balancer for production deployment.

---

## 🏗️ Architecture with HAProxy

```
Internet / Internal Network
         ↓
    [HAProxy]
    Port 80/443
         ↓
    ┌────┴────┐
    ↓         ↓
[Frontend] [Backend]
Port 3001  Port 8001
    ↓         ↓
[Docker Network]
```

---

## 📋 Benefits of Using HAProxy

1. **Single Entry Point**
   - Users access: `http://edms-server` (no port numbers)
   - HAProxy routes to appropriate service

2. **SSL Termination**
   - HAProxy handles HTTPS
   - Docker containers remain HTTP (simpler)

3. **Load Balancing**
   - Can scale to multiple backend instances
   - Health checks and failover

4. **Clean URLs**
   - No port numbers in URLs
   - Professional appearance

## ℹ️ Requirements

- **HAProxy Version:** 2.0 or higher (2.4+ recommended)
- **Operating System:** Ubuntu 20.04/22.04, Debian 10/11, RHEL 8+
- **Memory:** Minimum 512MB RAM for HAProxy
- **Ports Required:** 80 (HTTP), 443 (HTTPS optional), 8404 (stats)

---

## ⚙️ Configuration

### Step 1: Configure Docker Ports in .env

The ports are now configurable in your `.env` file:

```bash
# Docker Port Configuration
BACKEND_PORT=8001      # HAProxy will route to this
FRONTEND_PORT=3001     # HAProxy will route to this
POSTGRES_PORT=5433     # For direct admin access only
REDIS_PORT=6380        # For direct admin access only
```

**Note:** You can change these ports if needed (e.g., if ports are already in use).

---

### Step 2: Update CORS/CSRF Settings

Since HAProxy will be the entry point, users will access via HAProxy's address:

```bash
# .env configuration
ALLOWED_HOSTS=192.168.1.100,edms-server,localhost

# NO PORT NUMBERS - HAProxy serves on port 80
CORS_ALLOWED_ORIGINS=http://192.168.1.100,http://edms-server
CSRF_TRUSTED_ORIGINS=http://192.168.1.100,http://edms-server
```

---

### Step 3: HAProxy Configuration

Create `/etc/haproxy/haproxy.cfg`:

```haproxy
# ==============================================================================
# HAProxy Configuration for EDMS
# ==============================================================================

global
    log /dev/log local0
    log /dev/log local1 notice
    chroot /var/lib/haproxy
    stats socket /run/haproxy/admin.sock mode 660 level admin
    stats timeout 30s
    user haproxy
    group haproxy
    daemon

    # Security settings
    maxconn 2000
    tune.ssl.default-dh-param 2048

defaults
    log     global
    mode    http
    option  httplog
    option  dontlognull
    
    # Timeout settings
    timeout connect 5000    # 5 seconds to connect to backend
    timeout client  300000  # 5 minutes for client (allows large uploads)
    timeout server  300000  # 5 minutes for server (allows long processing)
    
    # Custom error pages
    errorfile 400 /etc/haproxy/errors/400.http
    errorfile 403 /etc/haproxy/errors/403.http
    errorfile 408 /etc/haproxy/errors/408.http
    errorfile 500 /etc/haproxy/errors/500.http
    errorfile 502 /etc/haproxy/errors/502.http
    errorfile 503 /etc/haproxy/errors/503.http
    errorfile 504 /etc/haproxy/errors/504.http
    
    # Compression for better performance
    compression algo gzip
    compression type text/html text/plain text/css text/javascript application/javascript application/json application/xml

# ==============================================================================
# STATISTICS PAGE (Optional - for monitoring)
# ==============================================================================
listen stats
    bind *:8404
    stats enable
    stats uri /
    stats refresh 30s
    stats admin if TRUE
    # Secure with password:
    stats auth admin:changeme

# ==============================================================================
# FRONTEND - Entry Point
# ==============================================================================
frontend edms_frontend
    bind *:80
    mode http
    
    # Logging
    option httplog
    log global
    
    # Security headers
    http-response set-header X-Frame-Options DENY
    http-response set-header X-Content-Type-Options nosniff
    http-response set-header X-XSS-Protection "1; mode=block"
    
    # Health check endpoint
    acl healthcheck path /health
    use_backend health_check if healthcheck
    
    # Route API requests to backend
    acl is_api path_beg /api/ /admin/ /static/ /media/ /health/
    use_backend backend_servers if is_api
    
    # Route everything else to frontend
    default_backend frontend_servers

# ==============================================================================
# BACKEND SERVERS
# ==============================================================================

# Django Backend
backend backend_servers
    mode http
    balance roundrobin
    option httpchk GET /health/
    http-check expect status 200
    
    # Docker backend container
    server backend1 127.0.0.1:8001 check inter 10s fall 3 rise 2
    
    # Uncomment to add more backend instances for load balancing:
    # server backend2 127.0.0.1:8002 check inter 10s fall 3 rise 2

# React Frontend
backend frontend_servers
    mode http
    balance roundrobin
    option httpchk GET /
    http-check expect status 200
    
    # Docker frontend container
    server frontend1 127.0.0.1:3001 check inter 10s fall 3 rise 2
    
    # Uncomment to add more frontend instances:
    # server frontend2 127.0.0.1:3002 check inter 10s fall 3 rise 2

# Health Check
backend health_check
    mode http
    http-request return status 200 content-type text/plain string "OK"
```

---

## 🚀 Deployment Steps

### 1. Update .env File

```bash
# Edit backend/.env
nano backend/.env

# Set these values:
BACKEND_PORT=8001
FRONTEND_PORT=3001
ALLOWED_HOSTS=192.168.1.100,edms-server
CORS_ALLOWED_ORIGINS=http://192.168.1.100,http://edms-server
CSRF_TRUSTED_ORIGINS=http://192.168.1.100,http://edms-server
```

### 2. Start Docker Containers

```bash
# Build and start
docker compose -f docker-compose.prod.yml up -d

# Verify containers are running
docker compose ps

# Check exposed ports
docker compose ps | grep -E "PORT|edms_prod"
```

### 3. Install and Configure HAProxy

```bash
# Install HAProxy
sudo apt update
sudo apt install haproxy -y

# Verify HAProxy version (should be 2.0 or higher)
haproxy -v
# Expected: HAProxy version 2.x.x or higher

# Create backup directory for configs
sudo mkdir -p /etc/haproxy/backups

# Backup original config with timestamp
sudo cp /etc/haproxy/haproxy.cfg /etc/haproxy/backups/haproxy.cfg.original.$(date +%Y%m%d-%H%M%S)

# Copy your config
sudo cp haproxy.cfg /etc/haproxy/haproxy.cfg

# Validate configuration (IMPORTANT - catches syntax errors)
sudo haproxy -c -f /etc/haproxy/haproxy.cfg
# Expected: Configuration file is valid

# Start HAProxy
sudo systemctl restart haproxy
sudo systemctl enable haproxy

# Check status
sudo systemctl status haproxy
```

### 4. Test Configuration

```bash
# Test backend through HAProxy
curl -I http://localhost/health/
# Should return: HTTP/1.1 200 OK

# Test frontend through HAProxy
curl -I http://localhost/
# Should return: HTTP/1.1 200 OK

# Test API through HAProxy
curl http://localhost/api/v1/documents/
# Should return: JSON response or 401 (auth required)

# Check HAProxy stats page
curl http://localhost:8404
# Or open in browser: http://192.168.1.100:8404
```

### 5. Configure Firewall

```bash
# Allow HAProxy ports
sudo ufw allow 80/tcp
sudo ufw allow 8404/tcp  # Stats page (optional)

# Block direct access to Docker ports (optional for security)
# This forces all traffic through HAProxy
sudo ufw deny 8001/tcp
sudo ufw deny 3001/tcp

# Verify rules
sudo ufw status
```

---

## 🔍 Access URLs

### Before HAProxy (Direct Docker Access):
- Frontend: `http://192.168.1.100:3001`
- Backend: `http://192.168.1.100:8001`

### After HAProxy:
- **Application:** `http://192.168.1.100` or `http://edms-server`
- **HAProxy Stats:** `http://192.168.1.100:8404`

---

## 📊 Port Mapping Summary

| Component | Internal (Docker) | External (Host) | HAProxy Routes To | User Access |
|-----------|------------------|-----------------|-------------------|-------------|
| Frontend | 80 | 3001 | Yes | Via HAProxy:80 |
| Backend | 8000 | 8001 | Yes | Via HAProxy:80 |
| PostgreSQL | 5432 | 5433 | No | Direct admin only |
| Redis | 6379 | 6380 | No | Direct admin only |
| HAProxy | - | 80 | - | Main entry point |

---

## 🔒 Security Best Practices

### 1. Block Direct Docker Port Access

```bash
# After HAProxy is working, block direct access:
sudo iptables -A INPUT -p tcp --dport 8001 ! -s 127.0.0.1 -j DROP
sudo iptables -A INPUT -p tcp --dport 3001 ! -s 127.0.0.1 -j DROP

# Save iptables rules
sudo netfilter-persistent save
```

### 2. Secure HAProxy Stats Page

```haproxy
# In haproxy.cfg:
listen stats
    bind *:8404
    stats enable
    stats uri /
    stats refresh 30s
    
    # Require authentication
    stats auth admin:STRONG-PASSWORD-HERE
    
    # Limit to local network only
    acl local_net src 192.168.1.0/24
    http-request deny unless local_net
```

### 3. Enable Rate Limiting

```haproxy
# Add to frontend section:
frontend edms_frontend
    # ... existing config ...
    
    # Rate limiting (100 requests per 10 seconds per IP)
    stick-table type ip size 100k expire 30s store http_req_rate(10s)
    http-request track-sc0 src
    http-request deny if { sc_http_req_rate(0) gt 100 }
```

---

## 🔄 Load Balancing (Optional)

To add multiple backend/frontend instances:

### 1. Create Additional Docker Services

```yaml
# In docker-compose.prod.yml, duplicate services:

backend2:
  # ... same as backend but different container_name ...
  ports:
    - "8002:8000"

backend3:
  ports:
    - "8003:8000"
```

### 2. Update HAProxy

```haproxy
backend backend_servers
    # ... existing config ...
    server backend1 127.0.0.1:8001 check
    server backend2 127.0.0.1:8002 check
    server backend3 127.0.0.1:8003 check
```

---

## 🛠️ Troubleshooting

### Issue 1: HAProxy Shows 503 Service Unavailable

```bash
# Check backend health
curl http://localhost:8001/health/
curl http://localhost:3001/

# Check HAProxy logs
sudo tail -f /var/log/haproxy.log

# Check backend status in stats page
http://192.168.1.100:8404
```

### Issue 2: CORS Errors After Adding HAProxy

```bash
# Verify CORS settings in .env don't include port numbers
cat backend/.env | grep CORS_ALLOWED_ORIGINS
# Should be: http://192.168.1.100 (no :3001)

# Restart backend
docker compose restart backend
```

### Issue 3: Can't Access HAProxy Stats

```bash
# Check HAProxy is listening
sudo netstat -tlnp | grep 8404

# Check firewall
sudo ufw status | grep 8404

# Test locally first
curl http://localhost:8404
```

### Issue 4: Backend Health Check Failing

```bash
# Test backend health directly
curl -v http://localhost:8001/health/

# Check backend logs
docker compose logs backend | grep health

# Verify health check endpoint exists
docker compose exec backend python manage.py shell -c "
from django.urls import resolve
print(resolve('/health/'))
"
```

### Issue 5: Need to Update HAProxy Config Without Downtime

```bash
# Method 1: Graceful reload (zero downtime)
# Edit configuration
sudo nano /etc/haproxy/haproxy.cfg

# Validate new configuration
sudo haproxy -c -f /etc/haproxy/haproxy.cfg

# Graceful reload - doesn't drop existing connections
sudo systemctl reload haproxy

# Method 2: For major changes requiring restart
sudo systemctl restart haproxy

# Check if reload was successful
sudo systemctl status haproxy
```

### Issue 6: Large File Upload Timeouts

```bash
# If uploads >100MB are timing out, already configured with 5-minute timeouts
# If you need longer, edit /etc/haproxy/haproxy.cfg:

# In defaults section, increase timeouts:
timeout client  600000  # 10 minutes
timeout server  600000  # 10 minutes

# Reload HAProxy
sudo systemctl reload haproxy
```

---

## 📈 Monitoring

### Configure Log Rotation

Prevent log files from growing too large:

```bash
# Create logrotate configuration
sudo tee /etc/logrotate.d/haproxy << 'EOF'
/var/log/haproxy.log {
    daily
    rotate 14
    missingok
    notifempty
    compress
    delaycompress
    postrotate
        /usr/bin/systemctl reload rsyslog > /dev/null 2>&1 || true
    endscript
}
EOF

# Test logrotate configuration
sudo logrotate -d /etc/logrotate.d/haproxy

# Force rotation (for testing)
sudo logrotate -f /etc/logrotate.d/haproxy
```

### HAProxy Logs

```bash
# Watch real-time logs
sudo tail -f /var/log/haproxy.log

# Filter for errors
sudo tail -f /var/log/haproxy.log | grep -i error

# Count requests per minute
sudo tail -f /var/log/haproxy.log | pv -l -i 60 > /dev/null

# View log file size
ls -lh /var/log/haproxy.log
```

### Stats Page Metrics

Access: `http://192.168.1.100:8404`

**Key Metrics to Monitor:**
- **Sessions:** Current active connections
- **Queue:** Requests waiting (should be 0)
- **Status:** Should show green (UP)
- **Checks:** Health check status
- **Response Time:** Average response times

---

## 🎯 Production Checklist

### Pre-Deployment
- [ ] HAProxy version 2.0+ verified
- [ ] Docker containers running with configurable ports
- [ ] `.env` file updated with correct ports and CORS
- [ ] Backup of original HAProxy config created

### Installation
- [ ] HAProxy installed
- [ ] Configuration file validated (`haproxy -c`)
- [ ] HAProxy service enabled and running
- [ ] Log rotation configured

### Configuration
- [ ] Health checks passing (check stats page)
- [ ] Timeouts set appropriately (5 min for uploads)
- [ ] Compression enabled for text/html/css/js
- [ ] Firewall configured (allow 80, block direct Docker ports)
- [ ] HAProxy stats page secured with password

### Testing
- [ ] Tested access through HAProxy (not direct ports)
- [ ] Backend health check working (`/health/`)
- [ ] Frontend loading correctly
- [ ] API calls routing properly
- [ ] CORS working correctly (no console errors)
- [ ] Large file upload tested (if applicable)

### Security
- [ ] Direct Docker ports blocked via firewall
- [ ] Rate limiting configured
- [ ] Stats page authentication enabled
- [ ] SSL certificate ready (if using HTTPS)

### Monitoring
- [ ] Stats page accessible and monitored
- [ ] Logs being written and rotated
- [ ] Health checks monitored
- [ ] Alert system configured (optional)

### Documentation
- [ ] Team trained on HAProxy basics
- [ ] Troubleshooting guide accessible
- [ ] Backup/restore procedure documented
- [ ] Contact information for support

---

## 🔐 HTTPS Configuration (Optional)

To add SSL/TLS:

### 1. Obtain Certificate

```bash
# Using Let's Encrypt:
sudo apt install certbot
sudo certbot certonly --standalone -d edms-server.yourcompany.com

# Certificate will be at:
# /etc/letsencrypt/live/edms-server.yourcompany.com/fullchain.pem
# /etc/letsencrypt/live/edms-server.yourcompany.com/privkey.pem
```

### 2. Combine Certificate for HAProxy

```bash
# HAProxy needs cert + key in one file
sudo cat /etc/letsencrypt/live/edms-server.yourcompany.com/fullchain.pem \
         /etc/letsencrypt/live/edms-server.yourcompany.com/privkey.pem \
         > /etc/haproxy/certs/edms.pem

# Secure the certificate
sudo chmod 600 /etc/haproxy/certs/edms.pem
```

### 3. Update HAProxy Config

```haproxy
frontend edms_frontend
    # Add HTTPS binding
    bind *:80
    bind *:443 ssl crt /etc/haproxy/certs/edms.pem
    
    # Redirect HTTP to HTTPS
    redirect scheme https code 301 if !{ ssl_fc }
    
    # ... rest of config ...
```

### 4. Update Django Settings

```bash
# In .env:
CORS_ALLOWED_ORIGINS=https://edms-server.yourcompany.com
CSRF_TRUSTED_ORIGINS=https://edms-server.yourcompany.com

# In production.py (uncomment these):
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
```

---

## 📝 Summary

**With HAProxy:**
- ✅ Clean URLs (no port numbers)
- ✅ Single entry point (port 80)
- ✅ Load balancing ready
- ✅ Health checks and monitoring
- ✅ Professional production setup
- ✅ Configurable Docker ports via .env

**User Experience:**
- Before: `http://192.168.1.100:3001`
- After: `http://edms-server` or `http://192.168.1.100`

Much cleaner! 🎉

---

**Next Steps:**
1. Update `.env` with your ports and CORS settings
2. Deploy Docker containers
3. Install and configure HAProxy
4. Test and monitor
5. (Optional) Add SSL for HTTPS
