# Fix Production Backup/Restore Issue

**Issue:** Backup/restore works on staging/local but fails on production  
**Root Cause:** Scripts default to `docker-compose.yml` (dev) but production uses `docker-compose.prod.yml`  
**Date:** 2026-01-30  

---

## 🔍 Root Cause Analysis

### Why It Fails on Production:

**Scripts default behavior:**
```bash
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.yml}"  # ← Falls back to dev file!
```

**Local/Staging (works):**
- Uses `docker-compose.yml`
- Ports: 8000 (backend), 3000 (frontend)
- Scripts connect correctly ✅

**Production (fails):**
- Uses `docker-compose.prod.yml`
- Ports: 8001 (backend), 3001 (frontend)
- Scripts try to use `docker-compose.yml` which doesn't match running containers ❌

---

## ✅ Solution 1: Quick Fix (Add COMPOSE_FILE to .env)

**On production server:**

```bash
cd /path/to/edms

# Check if COMPOSE_FILE is set
grep COMPOSE_FILE .env

# If missing, add it
echo "COMPOSE_FILE=docker-compose.prod.yml" >> .env

# Verify
cat .env | grep COMPOSE_FILE
# Should show: COMPOSE_FILE=docker-compose.prod.yml

# Test backup
./scripts/backup-hybrid.sh

# Should now work! ✅
```

---

## ✅ Solution 2: Use Auto-Detecting Scripts (Recommended)

**Better approach - works everywhere automatically!**

```bash
cd /path/to/edms

# Pull latest code (includes fixed scripts)
git pull origin main

# Use the new auto-detecting scripts
./scripts/backup-hybrid-fixed.sh

# Or for restore
./scripts/restore-hybrid-fixed.sh backups/backup_YYYYMMDD_HHMMSS.tar.gz
```

**Benefits:**
- ✅ Auto-detects which docker-compose file to use
- ✅ Works on dev, staging, and production without changes
- ✅ Safer default (uses prod file if unsure)
- ✅ Shows which file it detected

---

## 🧪 Test the Fix

### Test Backup:

```bash
cd /path/to/edms

# Using fixed script
./scripts/backup-hybrid-fixed.sh

# Should see:
# ✅ Auto-detected: docker-compose.prod.yml
# [timestamp] Backing up database...
# [timestamp] ✅ Database backup complete: 500K
# [timestamp] Backing up media files...
# [timestamp] ✅ Media files backup complete: 2.5M
# [timestamp] Backup completed successfully!

# Verify backup created
ls -lh backups/ | tail -3
```

### Test Restore:

```bash
# Find a recent backup
BACKUP=$(ls -t backups/backup_*.tar.gz | head -1)
echo "Testing with: $BACKUP"

# Test restore (will ask for confirmation)
./scripts/restore-hybrid-fixed.sh "$BACKUP"

# Type: yes

# Should see:
# ✅ Auto-detected: docker-compose.prod.yml
# [timestamp] Extracting backup archive...
# [timestamp] ✅ Archive extracted
# [timestamp] Restoring database...
# [timestamp] ✅ Database restored
# [timestamp] Restoring media files...
# [timestamp] ✅ Media files restored
# [timestamp] Restore Completed Successfully!
```

---

## 📋 Comparison: Original vs Fixed Scripts

### Original Scripts:

**Pros:**
- Simple
- Works if COMPOSE_FILE is set

**Cons:**
- ❌ Defaults to dev file
- ❌ Fails silently if wrong file
- ❌ Requires manual .env configuration

### Fixed Scripts:

**Pros:**
- ✅ Auto-detects correct file
- ✅ Works everywhere without config
- ✅ Shows which file detected
- ✅ Safer default (prod file)
- ✅ Graceful fallback

**Cons:**
- Slightly more complex logic

---

## 🎯 Recommended Approach

### For Production:

**Option A: Use Fixed Scripts (Recommended)**
```bash
# Replace old scripts with new ones
cd /path/to/edms
cp scripts/backup-hybrid-fixed.sh scripts/backup-hybrid.sh
cp scripts/restore-hybrid-fixed.sh scripts/restore-hybrid.sh

# Or just use the -fixed versions directly
./scripts/backup-hybrid-fixed.sh
```

**Option B: Add COMPOSE_FILE to .env**
```bash
echo "COMPOSE_FILE=docker-compose.prod.yml" >> .env
# Then use original scripts
./scripts/backup-hybrid.sh
```

### For All Environments:

**Best Practice:**
1. Add `COMPOSE_FILE=docker-compose.prod.yml` to production `.env`
2. Add `COMPOSE_FILE=docker-compose.yml` to development `.env` (optional)
3. Use auto-detecting scripts for maximum compatibility

---

## 🔧 Update Cron Jobs (If Automated Backups)

If you have automated backups via cron, update them:

```bash
# Edit crontab
crontab -e

# Old (may fail on production):
0 2 * * * cd /path/to/edms && ./scripts/backup-hybrid.sh

# New (works everywhere):
0 2 * * * cd /path/to/edms && ./scripts/backup-hybrid-fixed.sh

# Or with explicit .env:
0 2 * * * cd /path/to/edms && COMPOSE_FILE=docker-compose.prod.yml ./scripts/backup-hybrid.sh
```

---

## 📊 Verification Checklist

After fixing:

- [ ] COMPOSE_FILE set in production .env (or using fixed scripts)
- [ ] Backup script runs successfully
- [ ] Backup file created in `backups/` directory
- [ ] Backup file has reasonable size (not 0 bytes)
- [ ] Restore script can extract backup
- [ ] Restore script connects to correct containers
- [ ] Database restore completes
- [ ] Media files restore completes
- [ ] Services restart successfully
- [ ] Restored data accessible in application

---

## 🚨 Troubleshooting

### Issue: "Error: service 'db' not found"

**Cause:** Script using wrong docker-compose file

**Solution:**
```bash
# Check which containers are running
docker ps --format "table {{.Names}}\t{{.Image}}"

# Check which compose file they're using
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.yml ps

# Use the one that shows running containers
# Or add to .env:
echo "COMPOSE_FILE=docker-compose.prod.yml" >> .env
```

### Issue: "Error: database connection refused"

**Cause:** Port mismatch or containers not running

**Solution:**
```bash
# Check container status
docker compose -f docker-compose.prod.yml ps db

# Check database port
docker compose -f docker-compose.prod.yml port db 5432

# Check logs
docker compose -f docker-compose.prod.yml logs db --tail=50

# Restart database if needed
docker compose -f docker-compose.prod.yml restart db
```

### Issue: Script works but backup is tiny (< 1MB)

**Cause:** Connected to empty database or wrong instance

**Solution:**
```bash
# Verify database has data
docker compose -f docker-compose.prod.yml exec db psql -U edms_user -d edms_db -c "SELECT COUNT(*) FROM auth_user;"

# Check database name matches
grep DB_NAME .env

# Check script is using correct compose file
./scripts/backup-hybrid-fixed.sh | head -10
# Look for: "Compose file: docker-compose.prod.yml"
```

---

## 📚 Related Documentation

- **CLEAN_DEPLOYMENT_GUIDE.md** - Complete fresh deployment
- **FIX_PRODUCTION_PORTS.md** - Port configuration issues
- **PRODUCTION_DEPLOYMENT_CHECKLIST.md** - Full deployment guide

---

## ✅ Quick Test Commands

```bash
# Test which compose file is active
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.yml ps

# Test backup with explicit compose file
COMPOSE_FILE=docker-compose.prod.yml ./scripts/backup-hybrid.sh

# Test backup with fixed script (auto-detects)
./scripts/backup-hybrid-fixed.sh

# Check what's in .env
cat .env | grep COMPOSE_FILE

# Verify backup worked
ls -lh backups/ | tail -5
```

---

## 🎯 Summary

**Problem:** Scripts defaulted to dev compose file on production  
**Impact:** Backup/restore failed on production but worked elsewhere  
**Solution:** Either set COMPOSE_FILE in .env OR use auto-detecting scripts  
**Recommendation:** Use fixed scripts for maximum compatibility  

**Time to Fix:** 2-5 minutes  
**Complexity:** Low  
**Risk:** None (scripts are read-only until restore)  

---

*Created: 2026-01-30*  
*Status: Fix Available and Tested*
