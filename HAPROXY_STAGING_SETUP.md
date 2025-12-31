# HAProxy Setup Guide for Staging Server

## 🎯 Overview

This guide will help you set up HAProxy on your staging server (`172.28.1.148`) to provide:
- Single entry point on port 80
- Load balancing (future multiple backend instances)
- SSL termination (optional)
- Health checks and failover

---

## 📋 Current Staging Server Status

**Server IP:** `172.28.1.148`

**Current Ports:**
- Backend: `8001` (http://172.28.1.148:8001)
- Frontend: `3001` (http://172.28.1.148:3001)
- Nginx: `80` (http://172.28.1.148:80)
- Database: `5433` (internal only)
- Redis: `6380` (internal only)

**After HAProxy Setup:**
- HAProxy: `80` → Routes to backend/frontend
- HAProxy Stats: `8404` → Monitoring dashboard

---

## 🚀 Quick Setup Options

### Option 1: HAProxy on Host (Recommended for Staging)
Install HAProxy directly on the Ubuntu host, outside Docker.

### Option 2: HAProxy in Docker
Add HAProxy as another container in docker-compose.

---

## 📦 Option 1: HAProxy on Host (Recommended)

### Step 1: Install HAProxy

```bash
# On staging server (172.28.1.148)
sudo apt update
sudo apt install -y haproxy

# Verify installation
haproxy -v
# Should show: HAProxy version 2.x.x
```

### Step 2: Configure HAProxy

Create HAProxy configuration file:

```bash
# Backup original config
sudo cp /etc/haproxy/haproxy.cfg /etc/haproxy/haproxy.cfg.backup

# Create new configuration
sudo nano /etc/haproxy/haproxy.cfg
```

**HAProxy Configuration for Staging:**

```haproxy
#---------------------------------------------------------------------
# Global settings
#---------------------------------------------------------------------
global
    log /dev/log local0
    log /dev/log local1 notice
    chroot /var/lib/haproxy
    stats socket /run/haproxy/admin.sock mode 660 level admin
    stats timeout 30s
    user haproxy
    group haproxy
    daemon

    # Default SSL material locations
    ca-base /etc/ssl/certs
    crt-base /etc/ssl/private

    # Security hardening
    ssl-default-bind-ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256
    ssl-default-bind-options ssl-min-ver TLSv1.2 no-tls-tickets

#---------------------------------------------------------------------
# Common defaults
#---------------------------------------------------------------------
defaults
    log     global
    mode    http
    option  httplog
    option  dontlognull
    option  http-server-close
    option  forwardfor except 127.0.0.0/8
    option  redispatch
    retries 3
    timeout connect 5000ms
    timeout client  50000ms
    timeout server  50000ms
    errorfile 400 /etc/haproxy/errors/400.http
    errorfile 403 /etc/haproxy/errors/403.http
    errorfile 408 /etc/haproxy/errors/408.http
    errorfile 500 /etc/haproxy/errors/500.http
    errorfile 502 /etc/haproxy/errors/502.http
    errorfile 503 /etc/haproxy/errors/503.http
    errorfile 504 /etc/haproxy/errors/504.http

#---------------------------------------------------------------------
# HAProxy Statistics Dashboard
#---------------------------------------------------------------------
frontend stats
    bind *:8404
    stats enable
    stats uri /stats
    stats refresh 30s
    stats show-legends
    stats show-node
    stats admin if TRUE

#---------------------------------------------------------------------
# Frontend - Main Entry Point
#---------------------------------------------------------------------
frontend edms_frontend
    bind *:80
    mode http
    
    # Request logging
    log-format "%ci:%cp [%tr] %ft %b/%s %TR/%Tw/%Tc/%Tr/%Ta %ST %B %CC %CS %tsc %ac/%fc/%bc/%sc/%rc %sq/%bq %hr %hs %{+Q}r"
    
    # ACLs for routing
    acl is_api path_beg /api/
    acl is_admin path_beg /admin/
    acl is_health path /health/
    acl is_static path_beg /static/
    acl is_media path_beg /media/
    
    # Route API, admin, and health to backend
    use_backend edms_backend if is_api or is_admin or is_health or is_static or is_media
    
    # Route everything else to frontend (React app)
    default_backend edms_ui

#---------------------------------------------------------------------
# Backend - Django API Server
#---------------------------------------------------------------------
backend edms_backend
    mode http
    balance roundrobin
    
    # Health check
    option httpchk GET /health/
    http-check expect status 200
    
    # Backend server
    server backend1 127.0.0.1:8001 check inter 5s fall 3 rise 2
    
    # Timeout settings for API
    timeout server 120s
    
    # Error handling
    http-request set-header X-Forwarded-Proto http if !{ ssl_fc }
    http-response set-header X-Backend-Server %s

#---------------------------------------------------------------------
# Backend - React Frontend UI
#---------------------------------------------------------------------
backend edms_ui
    mode http
    balance roundrobin
    
    # Health check
    option httpchk GET /
    http-check expect status 200
    
    # Frontend server
    server frontend1 127.0.0.1:3001 check inter 10s fall 3 rise 2
    
    # Error handling
    http-request set-header X-Forwarded-Proto http if !{ ssl_fc }
    http-response set-header X-Frontend-Server %s
```

### Step 3: Validate Configuration

```bash
# Test configuration for syntax errors
sudo haproxy -c -f /etc/haproxy/haproxy.cfg

# Should show: Configuration file is valid
```

### Step 4: Start HAProxy

```bash
# Enable HAProxy to start on boot
sudo systemctl enable haproxy

# Start HAProxy
sudo systemctl start haproxy

# Check status
sudo systemctl status haproxy

# Should show: Active: active (running)
```

### Step 5: Update Docker Services

Since HAProxy will now use port 80, we need to update Nginx or disable it:

```bash
cd /home/lims/edms-staging

# Option A: Stop Nginx (HAProxy replaces it)
docker compose -f docker-compose.prod.yml stop nginx

# Option B: Change Nginx port in docker-compose.prod.yml
# Edit docker-compose.prod.yml to change Nginx ports from 80:80 to 8080:80
```

### Step 6: Update ALLOWED_HOSTS and CORS

Update `.env` file to allow HAProxy:

```bash
cd /home/lims/edms-staging
nano .env
```

Update these lines:
```bash
ALLOWED_HOSTS=edms-server,172.28.1.148,localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://172.28.1.148
```

Restart backend:
```bash
docker compose -f docker-compose.prod.yml restart backend
```

### Step 7: Verify Setup

```bash
# 1. Check HAProxy is running
sudo systemctl status haproxy

# 2. View HAProxy stats dashboard
# Open in browser: http://172.28.1.148:8404/stats

# 3. Test API through HAProxy
curl http://172.28.1.148/health/

# Should return: {"status": "healthy", ...}

# 4. Test frontend through HAProxy
curl -I http://172.28.1.148/

# Should return: HTTP/1.1 200 OK

# 5. Check HAProxy logs
sudo tail -f /var/log/haproxy.log
```

---

## 🐳 Option 2: HAProxy in Docker

If you prefer HAProxy in Docker, add this to your `docker-compose.prod.yml`:

```yaml
  haproxy:
    image: haproxy:2.8-alpine
    container_name: edms_prod_haproxy
    volumes:
      - ./infrastructure/haproxy/haproxy.cfg:/usr/local/etc/haproxy/haproxy.cfg:ro
    ports:
      - "80:80"
      - "8404:8404"  # Stats page
    depends_on:
      - backend
      - frontend
    networks:
      - edms_prod_network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "haproxy", "-c", "-f", "/usr/local/etc/haproxy/haproxy.cfg"]
      interval: 30s
      timeout: 10s
      retries: 3
```

Create `infrastructure/haproxy/haproxy.cfg` with the configuration above (adjust backend/frontend addresses to use Docker service names).

---

## 🔧 Troubleshooting

### HAProxy won't start - Port 80 in use

```bash
# Check what's using port 80
sudo lsof -i :80

# If Nginx Docker container is using it:
docker compose -f docker-compose.prod.yml stop nginx
```

### Backend/Frontend not reachable

```bash
# Check HAProxy logs
sudo journalctl -u haproxy -f

# Check if backend/frontend ports are accessible
curl http://127.0.0.1:8001/health/
curl http://127.0.0.1:3001/
```

### Health checks failing

```bash
# View HAProxy stats
# Browser: http://172.28.1.148:8404/stats
# Look for red/orange servers

# Check backend health
docker compose -f docker-compose.prod.yml logs backend | tail -50
```

---

## 📊 Monitoring

### HAProxy Statistics Dashboard

Access at: `http://172.28.1.148:8404/stats`

**Key Metrics:**
- **Session rate** - Requests per second
- **Backend status** - Green (UP) or Red (DOWN)
- **Queue** - Requests waiting for backend
- **Response time** - Server response latency

### Useful HAProxy Commands

```bash
# View active connections
echo "show stat" | sudo socat stdio /run/haproxy/admin.sock

# View current sessions
echo "show sess" | sudo socat stdio /run/haproxy/admin.sock

# Reload configuration without downtime
sudo systemctl reload haproxy

# Check HAProxy version and build options
haproxy -vv
```

---

## 🔒 Security Hardening (Optional)

### Rate Limiting

Add to `frontend edms_frontend`:
```haproxy
    # Rate limiting - 100 requests per 10 seconds
    stick-table type ip size 100k expire 30s store http_req_rate(10s)
    http-request track-sc0 src
    http-request deny deny_status 429 if { sc_http_req_rate(0) gt 100 }
```

### IP Whitelisting

```haproxy
    # Allow only specific IPs
    acl allowed_ips src 172.28.0.0/16 10.0.0.0/8
    http-request deny if !allowed_ips
```

### Basic Authentication for Stats

```haproxy
frontend stats
    bind *:8404
    stats enable
    stats uri /stats
    stats realm HAProxy\ Statistics
    stats auth admin:your_secure_password_here
```

---

## 🎯 Next Steps After HAProxy Setup

1. **SSL/TLS Certificate** (optional for staging)
   - Use Let's Encrypt for free SSL
   - Update HAProxy to listen on port 443
   
2. **Log Aggregation**
   - Send HAProxy logs to centralized logging (ELK, Splunk, etc.)
   
3. **Alerting**
   - Set up alerts for backend down events
   
4. **Load Testing**
   - Test HAProxy with load testing tools (Apache Bench, wrk, etc.)

---

## 📝 Summary

**With HAProxy configured, your staging server will:**
- ✅ Single entry point on port 80
- ✅ Automatic routing: `/api/*` → Backend, `/*` → Frontend
- ✅ Health checks with automatic failover
- ✅ Real-time monitoring dashboard
- ✅ Request/response logging
- ✅ Ready for multiple backend instances (scalability)

**Architecture After HAProxy:**
```
Internet
    ↓
HAProxy (Port 80)
    ├── /api/* → Backend (Port 8001)
    ├── /admin/* → Backend (Port 8001)
    ├── /health/ → Backend (Port 8001)
    └── /* → Frontend (Port 3001)
```

---

## 🆘 Need Help?

- View full HAProxy documentation: `HAPROXY_INTEGRATION_GUIDE.md`
- Check HAProxy official docs: https://www.haproxy.org/
- View logs: `sudo journalctl -u haproxy -f`
- Stats dashboard: `http://172.28.1.148:8404/stats`
