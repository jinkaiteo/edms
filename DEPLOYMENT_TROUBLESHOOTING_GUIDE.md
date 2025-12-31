# EDMS Deployment Troubleshooting Guide

## Common Deployment Issues and Solutions

### Issue 1: Backend Unhealthy - Missing EDMS_MASTER_KEY

**Symptom:**
```
django.core.exceptions.ImproperlyConfigured: EDMS_MASTER_KEY must be set in production settings
```

**Cause:** The encryption service requires `EDMS_MASTER_KEY` environment variable for document encryption and backup/restore functionality.

**Solution:**

#### Quick Fix (Staging/Development)
```bash
cd /path/to/deployment

# Generate a secure master key
MASTER_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")

# Create or append to .env file
echo "EDMS_MASTER_KEY=${MASTER_KEY}" >> .env

# Restart backend
docker compose -f docker-compose.prod.yml restart backend

# Verify health
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs backend | tail -50
```

#### Production Fix (Secure)
```bash
# 1. Generate key on secure workstation
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# 2. Store in password manager or secrets vault
# Example output: gAAAAABl... (44 characters)

# 3. Add to .env on production server (use secure method)
# Option A: Manual editing with nano/vim
nano .env
# Add line: EDMS_MASTER_KEY=gAAAAABl...

# Option B: Use secrets management (AWS Secrets Manager, HashiCorp Vault, etc.)

# 4. Restart services
docker compose -f docker-compose.prod.yml restart backend
```

**⚠️ CRITICAL WARNINGS:**
- **Never lose this key** - store multiple secure backups
- **Never regenerate** - you won't be able to decrypt existing data
- **Never commit to git** - keep in .env (which is gitignored)
- **Rotate carefully** - requires re-encrypting all existing data

---

### Issue 2: Backend Still Unhealthy After EDMS_MASTER_KEY Fix

**Diagnostic Steps:**

```bash
# 1. Check if environment variable is loaded
docker compose -f docker-compose.prod.yml exec backend env | grep EDMS_MASTER_KEY

# 2. Check backend logs for new errors
docker compose -f docker-compose.prod.yml logs backend | tail -100

# 3. Check container health
docker compose -f docker-compose.prod.yml ps

# 4. Test health endpoint directly
curl -v http://localhost:8001/health/

# 5. Check database connectivity
docker compose -f docker-compose.prod.yml exec backend python manage.py check --database default
```

**Common Follow-up Issues:**

#### A. Database Migration Needed
```bash
docker compose -f docker-compose.prod.yml exec backend python manage.py migrate
```

#### B. Static Files Not Collected
```bash
docker compose -f docker-compose.prod.yml exec backend python manage.py collectstatic --noinput
```

#### C. Database Connection Issues
```bash
# Check database is up
docker compose -f docker-compose.prod.yml exec db pg_isready

# Verify credentials in .env match docker-compose.prod.yml
cat .env | grep DB_
```

#### D. Missing Dependencies
```bash
# Rebuild container if requirements changed
docker compose -f docker-compose.prod.yml build backend
docker compose -f docker-compose.prod.yml up -d backend
```

---

### Issue 3: Permission Denied Errors

**Solution:**
```bash
# Fix storage permissions
sudo chown -R 1000:1000 storage/
sudo chmod -R 755 storage/

# Fix logs permissions
sudo chown -R 1000:1000 logs/
sudo chmod -R 755 logs/
```

---

### Issue 4: Port Already in Use

**Solution:**
```bash
# Check what's using the port
sudo lsof -i :8001
sudo lsof -i :3001

# Option 1: Stop conflicting service
sudo systemctl stop <service-name>

# Option 2: Change ports in docker-compose.prod.yml
# Edit ports section: "8002:8000" instead of "8001:8000"
```

---

## Health Check Commands

```bash
# Quick health check all services
docker compose -f docker-compose.prod.yml ps

# Detailed backend logs
docker compose -f docker-compose.prod.yml logs backend --tail=100 --follow

# Check all container health
docker compose -f docker-compose.prod.yml ps --format "table {{.Name}}\t{{.Status}}"

# Test API endpoints
curl http://localhost:8001/health/
curl http://localhost:8001/api/v1/auth/profile/

# Database check
docker compose -f docker-compose.prod.yml exec db psql -U edms_prod_user -d edms_prod_db -c "SELECT version();"
```

---

## Required Environment Variables Checklist

```bash
# Required for all deployments
☐ SECRET_KEY              # Django secret (50+ chars)
☐ DB_PASSWORD             # Database password
☐ EDMS_MASTER_KEY         # Encryption key (44 chars)
☐ REDIS_PASSWORD          # Redis password

# Required for external access
☐ ALLOWED_HOSTS           # Comma-separated hostnames/IPs
☐ CORS_ALLOWED_ORIGINS    # Frontend URL(s)

# Optional but recommended
☐ EMAIL_HOST              # SMTP server
☐ EMAIL_HOST_USER         # Email username
☐ EMAIL_HOST_PASSWORD     # Email password
```

---

## Complete Service Restart Procedure

```bash
# Safe restart (no data loss)
docker compose -f docker-compose.prod.yml restart

# Full restart (rebuilds if needed)
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml up -d

# Nuclear option (removes volumes - DATA LOSS!)
docker compose -f docker-compose.prod.yml down -v
docker compose -f docker-compose.prod.yml up -d
```

---

## Contact & Support

If issues persist after trying these solutions:

1. **Collect diagnostic information:**
   ```bash
   docker compose -f docker-compose.prod.yml logs > deployment_logs.txt
   docker compose -f docker-compose.prod.yml ps > deployment_status.txt
   cat .env | grep -v PASSWORD | grep -v KEY > deployment_config.txt
   ```

2. **Check documentation:**
   - `PRODUCTION_DEPLOYMENT_GUIDE.md`
   - `DEPLOYMENT_QUICK_START.md`
   - `docs/deployment/`

3. **Review recent changes:**
   ```bash
   git log --oneline -10
   git diff HEAD~1 docker-compose.prod.yml
   ```
