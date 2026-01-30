# Fix Production Port Configuration Issue

**Issue:** Production might be using wrong docker-compose file with incorrect ports  
**Date:** 2026-01-30  
**Severity:** Medium (affects accessibility)  

---

## 🔍 Problem Identification

### Port Mismatch Detected

**Expected Configuration (.env file):**
- `BACKEND_PORT=8001`
- `FRONTEND_PORT=3001`
- `DB_PORT=5432`

**Possible Issue:**
Production server might be using `docker-compose.yml` (development) instead of `docker-compose.prod.yml` (production).

### Differences Between Compose Files

**docker-compose.yml (Development):**
```yaml
backend:
  ports:
    - "8000:8000"  # ❌ Hardcoded, ignores .env
    
frontend:
  ports:
    - "3000:3000"  # ❌ Hardcoded, ignores .env
```

**docker-compose.prod.yml (Production):**
```yaml
backend:
  ports:
    - "${BACKEND_PORT:-8001}:8000"  # ✅ Reads from .env
    
frontend:
  ports:
    - "${FRONTEND_PORT:-3001}:80"   # ✅ Reads from .env
```

---

## 🔍 Step 1: Diagnose Current Setup

### On Production Server, Run:

```bash
cd /path/to/edms

# Check which containers are running
docker ps --format "table {{.Names}}\t{{.Ports}}"

# Expected output if using wrong file:
# NAME                    PORTS
# edms-backend-1         0.0.0.0:8000->8000/tcp  ❌ Wrong!
# edms-frontend-1        0.0.0.0:3000->3000/tcp  ❌ Wrong!

# Expected output if using correct file:
# NAME                    PORTS
# edms-backend-1         0.0.0.0:8001->8000/tcp  ✅ Correct!
# edms-frontend-1        0.0.0.0:3001->80/tcp    ✅ Correct!
```

### Or Use Diagnostic Script:

```bash
# Copy to production server
scp CHECK_PRODUCTION_PORTS.sh user@production-server:/tmp/

# Run on server
ssh user@production-server
cd /path/to/edms
bash /tmp/CHECK_PRODUCTION_PORTS.sh
```

---

## 🔧 Step 2: Fix the Configuration

### If Using Wrong Compose File:

```bash
# On production server
cd /path/to/edms

# Stop current containers
docker compose down

# Verify .env file has correct ports
cat .env | grep -E "BACKEND_PORT|FRONTEND_PORT|DB_PORT"

# Expected output:
# BACKEND_PORT=8001
# FRONTEND_PORT=3001
# DB_PORT=5432

# Start with correct compose file
docker compose -f docker-compose.prod.yml up -d

# Verify ports are correct now
docker ps --format "table {{.Names}}\t{{.Ports}}"
```

---

## ✅ Step 3: Update Deployment Process

### Update Existing Scripts

If you have deployment scripts that don't specify `-f docker-compose.prod.yml`, update them:

**Bad (uses default docker-compose.yml):**
```bash
docker compose up -d
docker compose restart backend
```

**Good (uses production compose file):**
```bash
docker compose -f docker-compose.prod.yml up -d
docker compose -f docker-compose.prod.yml restart backend
```

### Set Default Compose File (Optional)

Create/update `.env` to include:
```bash
echo "COMPOSE_FILE=docker-compose.prod.yml" >> .env
```

Then you can use commands without `-f`:
```bash
docker compose up -d  # Automatically uses docker-compose.prod.yml
```

---

## 🎯 Recommended Approach

### Permanent Fix for Production

**Option 1: Use COMPOSE_FILE Environment Variable**

```bash
# On production server, add to .env:
echo "COMPOSE_FILE=docker-compose.prod.yml" >> .env

# Now all commands automatically use prod file:
docker compose up -d
docker compose restart backend
docker compose ps
```

**Option 2: Create Production Alias**

```bash
# Add to ~/.bashrc or ~/.bash_aliases on production server:
alias dc-prod='docker compose -f docker-compose.prod.yml'

# Usage:
dc-prod up -d
dc-prod restart backend
dc-prod ps
```

**Option 3: Always Specify in Scripts (Current Approach)**

Continue using `-f docker-compose.prod.yml` in all commands and scripts.

---

## 📋 Migration Steps (If Currently Using Wrong File)

### Complete Migration Process:

```bash
# 1. Backup current state
cd /path/to/edms
./scripts/backup-hybrid.sh

# 2. Note current port configuration
docker ps --format "table {{.Names}}\t{{.Ports}}" > /tmp/old_ports.txt

# 3. Stop services
docker compose down

# 4. Verify .env has correct ports
cat .env | grep PORT

# 5. Start with production compose file
docker compose -f docker-compose.prod.yml up -d

# 6. Verify new ports
docker ps --format "table {{.Names}}\t{{.Ports}}"

# 7. Update any HAProxy or nginx configs if they point to old ports
# (If using HAProxy, update backend servers from :8000 to :8001, :3000 to :3001)

# 8. Test application access
curl http://localhost:8001/api/v1/health/  # Backend
curl http://localhost:3001/                # Frontend

# 9. If everything works, update COMPOSE_FILE in .env for future
echo "COMPOSE_FILE=docker-compose.prod.yml" >> .env
```

---

## 🔍 Verification Checklist

After fixing, verify:

- [ ] Backend accessible on port 8001 (not 8000)
- [ ] Frontend accessible on port 3001 (not 3000)
- [ ] Database accessible on port 5432
- [ ] Health check passes: `curl http://localhost:8001/api/v1/health/`
- [ ] Frontend loads: `curl http://localhost:3001/`
- [ ] Login works through frontend
- [ ] Document list loads
- [ ] All features functional

---

## ⚠️ Impact Analysis

### If Production is Using Wrong Ports:

**Potential Issues:**
1. HAProxy might be routing to wrong ports (if configured)
2. External services might be connecting to wrong ports
3. Firewall rules might need updating
4. Backup scripts might be connecting to wrong database port

**Things That Still Work:**
- Application functions normally (just on different ports)
- All data is intact
- No data loss risk

**Things to Update After Port Change:**
1. HAProxy configuration (if used)
2. Nginx reverse proxy (if used)
3. Firewall rules
4. Monitoring scripts
5. Backup scripts (database connection)
6. External integrations

---

## 🔄 Update HAProxy Configuration (If Using)

If you're using HAProxy, update backend server addresses:

```bash
# Edit HAProxy config
sudo nano /etc/haproxy/haproxy.cfg

# Change from:
backend backend_servers
    server backend1 127.0.0.1:8000 check

backend frontend_servers
    server frontend1 127.0.0.1:3000 check

# To:
backend backend_servers
    server backend1 127.0.0.1:8001 check

backend frontend_servers
    server frontend1 127.0.0.1:3001 check

# Reload HAProxy
sudo systemctl reload haproxy
```

---

## 🚀 Quick Fix Commands (Copy-Paste Ready)

### If Production Uses Wrong Ports, Run This:

```bash
#!/bin/bash
# Quick fix for production port configuration

cd /path/to/edms  # Adjust path

echo "🔍 Current configuration:"
docker ps --format "table {{.Names}}\t{{.Ports}}"

echo ""
echo "🛑 Stopping services..."
docker compose down

echo ""
echo "✅ Starting with production config..."
docker compose -f docker-compose.prod.yml up -d

echo ""
echo "⏳ Waiting for services to start..."
sleep 10

echo ""
echo "🔍 New configuration:"
docker ps --format "table {{.Names}}\t{{.Ports}}"

echo ""
echo "✅ Testing services..."
curl -f http://localhost:8001/api/v1/health/ && echo "✅ Backend healthy"
curl -f http://localhost:3001/ && echo "✅ Frontend accessible"

echo ""
echo "📝 Setting default compose file..."
echo "COMPOSE_FILE=docker-compose.prod.yml" >> .env

echo ""
echo "✅ COMPLETE! Services now running on correct ports."
echo "   Backend: http://localhost:8001"
echo "   Frontend: http://localhost:3001"
```

---

## 📚 Updated Deployment Scripts

### All Fixed Scripts Now Use Correct Compose File:

1. ✅ `deploy-interactive.sh` - Already uses `docker-compose.prod.yml`
2. ✅ `DEPLOY_HOTFIX_NOW.sh` - Fixed to use `docker-compose.prod.yml`
3. ✅ `DEPLOY_COMPLETE_SUPERUSER_FEATURE.md` - Specifies correct compose file

### Future Deployments:

Always use:
```bash
docker compose -f docker-compose.prod.yml [command]
```

Or set `COMPOSE_FILE=docker-compose.prod.yml` in `.env`.

---

## 🎯 Recommendation

**Best Practice for Production:**

1. **Add to production .env file:**
   ```bash
   COMPOSE_FILE=docker-compose.prod.yml
   ```

2. **Verify all scripts use production compose file**

3. **Document in deployment guides**

4. **Add to production deployment checklist**

---

## 📞 Troubleshooting

### Issue: Services won't start on new ports

**Cause:** Ports might be in use by old containers

**Solution:**
```bash
# Stop all containers
docker compose down
docker ps -a | grep edms | awk '{print $1}' | xargs docker rm -f

# Start fresh
docker compose -f docker-compose.prod.yml up -d
```

### Issue: HAProxy returns 503 after port change

**Cause:** HAProxy still pointing to old ports

**Solution:**
```bash
# Update haproxy.cfg backend servers to new ports
sudo nano /etc/haproxy/haproxy.cfg
sudo systemctl reload haproxy
```

### Issue: Can't connect to database

**Cause:** Database port changed

**Solution:**
```bash
# Check database is on correct port
docker ps | grep postgres
# Should show: 0.0.0.0:5432->5432/tcp

# Update any external tools connecting to database
```

---

## ✅ Post-Fix Checklist

After fixing port configuration:

- [ ] Services running on correct ports (8001, 3001)
- [ ] Health check passes
- [ ] Frontend loads
- [ ] Login works
- [ ] All features functional
- [ ] HAProxy updated (if used)
- [ ] Firewall rules updated (if needed)
- [ ] Monitoring scripts updated (if any)
- [ ] Backup scripts work correctly
- [ ] `COMPOSE_FILE` set in `.env` for future
- [ ] Deployment scripts use correct compose file
- [ ] Team notified of port changes

---

**Next Steps:**
1. Run diagnostic script to confirm current state
2. If using wrong ports, follow migration steps
3. Update `.env` with `COMPOSE_FILE=docker-compose.prod.yml`
4. Re-deploy with correct configuration

---

*Created: 2026-01-30*  
*Status: Diagnostic & Fix Guide Ready*
