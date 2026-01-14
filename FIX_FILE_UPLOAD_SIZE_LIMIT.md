# Fix: 413 Request Entity Too Large - File Upload Size Limit

## 🔴 Problem

When uploading documents from a remote instance, you're getting:
```
POST http://10.30.105.202:3001/api/v1/documents/documents/ 413 (Request Entity Too Large)
```

## 🔍 Root Cause

The **frontend nginx container** doesn't have `client_max_body_size` configured in `frontend/nginx.conf`, which defaults to **1MB** in nginx.

**Current Configuration:**
- ❌ `frontend/nginx.conf` - No `client_max_body_size` (defaults to 1MB)
- ✅ `backend/edms/settings/base.py` - 50MB limit configured
- ✅ `infrastructure/nginx/nginx.prod.conf` - 100MB configured (but not used by production)

**Your setup:**
```
User → Frontend Nginx (1MB limit ❌) → Backend Django (50MB limit ✅)
```

The request never reaches Django because nginx rejects it first!

---

## ✅ Solution

Add `client_max_body_size` to the nginx configuration used by the production frontend container.

---

## 🔧 Fix Implementation

### Option 1: Update `frontend/nginx.conf` (Recommended)

This file is used by the production Docker container.

**File:** `frontend/nginx.conf`

**Add this line** inside the `server` block (around line 6):

```nginx
server {
    listen 80;
    server_name localhost;
    root /usr/share/nginx/html;
    index index.html;

    # ✅ ADD THIS: Increase file upload size limit to 100MB
    client_max_body_size 100M;

    # Handle React Router (SPA)
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Proxy API requests to internal backend
    location /api/ {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # ✅ ADD THIS: Also needed for proxy location
        client_max_body_size 100M;
        
        # Increase timeouts for large file uploads
        proxy_read_timeout 300s;
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        
        # CORS headers
        add_header Access-Control-Allow-Origin * always;
        add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS" always;
        add_header Access-Control-Allow-Headers "Authorization, Content-Type" always;
        
        # Handle preflight requests
        if ($request_method = 'OPTIONS') {
            add_header Access-Control-Allow-Origin * always;
            add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS" always;
            add_header Access-Control-Allow-Headers "Authorization, Content-Type" always;
            add_header Content-Length 0;
            add_header Content-Type text/plain;
            return 204;
        }
    }

    # ... rest of config
}
```

---

### Option 2: Create `infrastructure/nginx/frontend.conf`

If the production Dockerfile uses this file (line 52 of `Dockerfile.frontend.prod`):

**File:** `infrastructure/nginx/frontend.conf`

```nginx
server {
    listen 80;
    server_name localhost;
    root /usr/share/nginx/html;
    index index.html;

    # File upload size limit - 100MB for document uploads
    client_max_body_size 100M;

    # Handle React Router (SPA)
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Proxy API requests to backend
    location /api/ {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # File upload size limit for API requests
        client_max_body_size 100M;
        
        # Timeouts for large file uploads
        proxy_read_timeout 300s;
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        
        # Buffer settings
        proxy_buffering off;
        proxy_request_buffering off;
        
        # CORS headers
        add_header Access-Control-Allow-Origin * always;
        add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS" always;
        add_header Access-Control-Allow-Headers "Authorization, Content-Type" always;
        
        if ($request_method = 'OPTIONS') {
            add_header Access-Control-Allow-Origin * always;
            add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS" always;
            add_header Access-Control-Allow-Headers "Authorization, Content-Type" always;
            add_header Content-Length 0;
            add_header Content-Type text/plain;
            return 204;
        }
    }

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;

    # Static files caching
    location ~* \.(css|js|jpg|jpeg|png|gif|ico|svg)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

---

## 🚀 Deployment Steps

### For Production Server (10.30.105.202:3001)

**Step 1: Update the nginx configuration**

```bash
# SSH to production server
ssh lims@10.30.105.202

# Navigate to project
cd /home/lims/edms-production

# Edit nginx config
nano frontend/nginx.conf

# Add the client_max_body_size lines as shown above
# Save and exit (Ctrl+X, Y, Enter)
```

**Step 2: Rebuild and restart the frontend container**

```bash
# Stop frontend
docker compose -f docker-compose.prod.yml stop frontend

# Rebuild with new nginx config
docker compose -f docker-compose.prod.yml build --no-cache frontend

# Start frontend
docker compose -f docker-compose.prod.yml up -d frontend

# Verify
docker compose -f docker-compose.prod.yml ps frontend
```

**Step 3: Test the fix**

```bash
# Check nginx config inside container
docker compose -f docker-compose.prod.yml exec frontend cat /etc/nginx/conf.d/default.conf | grep client_max_body_size

# Should show: client_max_body_size 100M;
```

---

## 🧪 Testing

### Test 1: Small File (< 1MB)
- Should work (was working before)

### Test 2: Medium File (1-50MB)
- Should now work (was failing before)

### Test 3: Large File (50-100MB)
- Should work after fix

### Test 4: Very Large File (> 100MB)
- Should fail with 413 (expected - exceeds limit)

---

## 📊 Current File Size Limits

| Layer | Limit | Status |
|-------|-------|--------|
| **Frontend Nginx** | 1MB (default) | ❌ Too small - FIXED to 100MB |
| **Backend Django** | 50MB | ✅ Good |
| **Database** | Unlimited | ✅ Good |

### After Fix:

| Layer | Limit | Status |
|-------|-------|--------|
| **Frontend Nginx** | 100MB | ✅ Fixed |
| **Backend Django** | 50MB | ⚠️ Lower than nginx |
| **Database** | Unlimited | ✅ Good |

**Recommendation**: Also increase backend limit to match:

```python
# backend/edms/settings/base.py or production.py

FILE_UPLOAD_MAX_MEMORY_SIZE = 100 * 1024 * 1024  # 100MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 100 * 1024 * 1024  # 100MB
```

---

## 🔧 Alternative: Increase Limits Further

If you need to support larger files:

### For 250MB limit:

```nginx
client_max_body_size 250M;
proxy_read_timeout 600s;
proxy_connect_timeout 600s;
proxy_send_timeout 600s;
```

```python
# Django settings
FILE_UPLOAD_MAX_MEMORY_SIZE = 250 * 1024 * 1024
DATA_UPLOAD_MAX_MEMORY_SIZE = 250 * 1024 * 1024
```

### For 500MB limit:

```nginx
client_max_body_size 500M;
proxy_read_timeout 900s;
```

```python
FILE_UPLOAD_MAX_MEMORY_SIZE = 500 * 1024 * 1024
DATA_UPLOAD_MAX_MEMORY_SIZE = 500 * 1024 * 1024
```

---

## 📝 Why Multiple Limits?

1. **Nginx (Frontend)**: First line of defense - rejects oversized requests early
2. **Django (Backend)**: Application-level validation
3. **Database**: Storage (usually no practical limit for BLOBs)

**Best Practice**: Set nginx limit slightly higher than Django to allow Django to handle validation and show user-friendly errors.

---

## ⚡ Quick Fix Commands

```bash
# On production server
cd /home/lims/edms-production

# Backup original config
cp frontend/nginx.conf frontend/nginx.conf.backup

# Add the line (edit manually or use sed)
sed -i '/listen 80;/a\    client_max_body_size 100M;' frontend/nginx.conf

# Also add to location /api/ block
sed -i '/location \/api\/ {/a\        client_max_body_size 100M;' frontend/nginx.conf

# Rebuild and restart
docker compose -f docker-compose.prod.yml stop frontend
docker compose -f docker-compose.prod.yml build --no-cache frontend
docker compose -f docker-compose.prod.yml up -d frontend

# Verify
docker compose -f docker-compose.prod.yml exec frontend nginx -t
```

---

## 🎯 Summary

**Problem**: 413 error on file uploads > 1MB

**Cause**: Missing `client_max_body_size` in nginx config

**Solution**: Add `client_max_body_size 100M;` to `frontend/nginx.conf`

**Impact**: After fix, files up to 100MB can be uploaded

**Deployment**: Requires frontend container rebuild (~2 minutes)

---

## ✅ Verification Checklist

After applying fix:

- [ ] Edit `frontend/nginx.conf`
- [ ] Add `client_max_body_size 100M;` in server block
- [ ] Add `client_max_body_size 100M;` in location /api/ block
- [ ] Rebuild frontend container
- [ ] Restart frontend container
- [ ] Test upload file < 1MB (should work)
- [ ] Test upload file 5MB (should now work)
- [ ] Test upload file 50MB (should now work)
- [ ] Test upload file > 100MB (should fail with clear error)

---

**Ready to apply the fix?** Let me know if you want me to create the updated config files! 🚀
