# Deployment Data Strategy: Fresh vs Update

**Understanding how your deployment handles data**

---

## 🎯 Quick Answer

**By default, deployments PRESERVE data** (update existing system).

For a **fresh/reinit deployment**, you need to explicitly reset the database.

---

## 📊 Deployment Types

### 1. Update Deployment (Default)
**What it does:**
- ✅ Updates application code
- ✅ Runs database migrations
- ✅ **Preserves all existing data**
- ✅ Keeps users, documents, settings
- ✅ Updates to new version

**When to use:**
- Normal deployments
- Production updates
- Feature releases
- Bug fixes

**Data status:** All preserved

### 2. Fresh Deployment (Reinit)
**What it does:**
- ✅ Installs application code
- ✅ Creates fresh database
- ✅ **No existing data**
- ✅ Clean slate
- ✅ Empty tables

**When to use:**
- First-time installation
- Staging server reset
- Testing fresh install
- Development environment

**Data status:** Empty/fresh

---

## 🔄 Current Deployment Behavior

### What Happens Automatically

```bash
# When you deploy via CI/CD or scripts:

1. Create new deployment directory
   /opt/edms-production-20241224-140000/

2. Extract package

3. Start Docker containers
   - Uses existing volumes if present
   - Creates new volumes if first time

4. Run migrations
   python manage.py migrate
   
   This UPDATES schema, does NOT reset data

5. Restart services

Result: Code updated, data preserved
```

### First Deployment vs Subsequent

**First Deployment (New Server):**
```
- No database volume exists
- Creates new volume
- Runs migrations (creates schema)
- Database is empty
- Need to create superuser
- Fresh state
```

**Subsequent Deployments:**
```
- Database volume exists
- Reuses existing volume
- Runs migrations (updates schema)
- Data is preserved
- Users still exist
- Update state
```

---

## 💾 Data Persistence

### What Gets Preserved

| Data Type | Preserved? | Location |
|-----------|------------|----------|
| **Database** | ✅ Yes | Docker volume (persistent) |
| **Users** | ✅ Yes | Database |
| **Documents** | ✅ Yes | Database + media files |
| **Settings** | ✅ Yes | Database |
| **Media files** | ✅ Yes | `backend/media/` (mounted) |
| **Application code** | ❌ No | Replaced with new version |
| **Dependencies** | ❌ No | Updated with new package |

### Docker Volumes (Persistent Storage)

```bash
# View current volumes
docker volume ls

# Typical output:
# edms_postgres_data    (database - persistent)
# edms_redis_data       (cache - can be reset)
# edms_media_files      (uploads - persistent)

# These survive container restarts and updates
```

---

## 🔧 How to Control Deployment Type

### Option 1: Keep Data (Default - Recommended)

Just deploy normally:
```bash
# Via CI/CD
git push origin main

# Or manually
./scripts/deploy-to-remote.sh user@server
```

Everything is preserved.

### Option 2: Fresh Install on Staging

Reset staging before deployment:
```bash
# SSH to staging
ssh user@staging-server

# Stop and remove everything
cd /opt/edms-current
docker compose down -v  # -v removes volumes

# Clear media
rm -rf backend/media/*
rm -rf backend/storage/*

# Now deploy (will be fresh)
```

### Option 3: Fresh Install on New Server

First deployment is automatically fresh:
```bash
# Just deploy to new server
./scripts/deploy-to-remote.sh user@new-server

# Database will be empty
# Need to create superuser:
ssh user@new-server
cd /opt/edms-production-*
docker compose exec backend python manage.py createsuperuser
```

### Option 4: Partial Reset (Specific Data)

```bash
# SSH to server
ssh user@server

# Enter Django shell
docker compose exec backend python manage.py shell

# Delete specific data
>>> from apps.documents.models import Document
>>> Document.objects.all().delete()

# Or reset specific app
docker compose exec backend python manage.py migrate documents zero
docker compose exec backend python manage.py migrate documents
```

---

## 🎯 Recommendations by Environment

### Development
```
Strategy: Fresh deploys OK
Frequency: As needed
Data: Not important
Command: docker compose down -v; deploy
```

### Staging
```
Strategy: Fresh for major testing, update for iterative
Frequency: Daily/weekly fresh reset
Data: Test data only
Command: Reset weekly, test fresh install
```

### Production
```
Strategy: ALWAYS update, NEVER reinit
Frequency: On releases
Data: Critical - must preserve
Command: Normal deployment only
Safety: Automatic backup before deploy
```

---

## 🛡️ Safety Features

### Automatic Backups

The deployment scripts include automatic backup:

```yaml
# In GitHub Actions workflow:
- name: Create backup before deployment
  run: |
    ssh user@server \
      'cd /opt/edms-current && ./scripts/backup-system.sh'
```

Before each production deployment:
1. ✅ Backup created
2. ✅ Database exported
3. ✅ Media files backed up
4. ✅ Can restore if needed

### Rollback Capability

If deployment fails:
```bash
# Automatic rollback in CI/CD
# Or manual:
./scripts/rollback.sh --previous --backup-first
```

This returns to previous version with all data intact.

---

## 📋 Pre-Deployment Checklist

### For Production (Update)
- [ ] Backup exists
- [ ] Migrations tested on staging
- [ ] No breaking schema changes
- [ ] Users notified (if needed)
- [ ] Rollback plan ready

### For Staging (Fresh)
- [ ] Confirm OK to lose data
- [ ] Test data preparation ready
- [ ] Superuser credentials ready
- [ ] Fixtures available (if needed)

### For First Deployment (Fresh)
- [ ] Server prepared
- [ ] Docker installed
- [ ] Secrets configured
- [ ] Superuser creation planned
- [ ] Initial data plan

---

## 🔍 How to Verify Current State

### Check if Data Exists

```bash
# SSH to server
ssh user@server

# Check database
docker volume ls | grep postgres
# If exists: May have data

# Check data
docker compose exec backend python manage.py shell
>>> from django.contrib.auth import get_user_model
>>> User = get_user_model()
>>> print(User.objects.count())

# If count > 0: Has data
# If 0 or error: Fresh database
```

### Check Deployment History

```bash
# On server
ls -la /opt/ | grep edms-production

# Shows all deployed versions
# Multiple versions = update deployments
# Single version = first deployment
```

---

## 💡 Common Scenarios

### Scenario 1: First Time Production Deployment

```
Status: Fresh server, no data
Result: Fresh deployment
Action: 
  1. Deploy package
  2. Create superuser
  3. Load fixtures (if any)
  4. Start using

Data: Empty, need to populate
```

### Scenario 2: Update Existing Production

```
Status: Running system with users/data
Result: Update deployment
Action:
  1. Backup automatically created
  2. Deploy new version
  3. Migrations run
  4. Service restarts

Data: All preserved
```

### Scenario 3: Reset Staging for Testing

```
Status: Want fresh staging for testing
Result: Fresh deployment
Action:
  1. docker compose down -v
  2. Deploy package
  3. Create test users
  4. Load test data

Data: Fresh, controlled test data
```

### Scenario 4: Disaster Recovery

```
Status: Production failed, need restore
Result: Restore from backup
Action:
  1. Rollback to previous version
  2. Or restore from backup
  3. Verify data integrity
  4. Resume operations

Data: Restored from backup
```

---

## 🎓 Best Practices

### Production
1. ✅ Always backup before deployment
2. ✅ Never reinit production
3. ✅ Test migrations on staging first
4. ✅ Have rollback plan
5. ✅ Monitor after deployment

### Staging
1. ✅ Reset weekly for fresh testing
2. ✅ Test migrations before production
3. ✅ Use realistic test data
4. ✅ Test both fresh and update scenarios

### Development
1. ✅ Reinit freely
2. ✅ Test migrations often
3. ✅ Use fixtures for quick setup
4. ✅ Keep development data separate

---

## 🚀 Quick Commands

### Deploy (Preserve Data)
```bash
# Normal deployment - data preserved
git push origin main
```

### Deploy Fresh (Staging Only)
```bash
# Reset staging first
ssh staging "cd /opt/edms-current && docker compose down -v"

# Then deploy
git push origin develop
```

### Create Superuser After Fresh Deploy
```bash
ssh user@server
cd /opt/edms-production-*
docker compose exec backend python manage.py createsuperuser
```

### Load Initial Data
```bash
# If you have fixtures
docker compose exec backend python manage.py loaddata initial_users
docker compose exec backend python manage.py loaddata initial_settings
```

---

## ✅ Summary

| Aspect | Default Behavior |
|--------|------------------|
| **Deployment Type** | Update (preserve data) |
| **Database** | Preserved across deploys |
| **Users** | Preserved |
| **Documents** | Preserved |
| **Code** | Updated to new version |
| **For Fresh Install** | Manual reset required |
| **Safety** | Automatic backup before production deploy |
| **Rollback** | Available if needed |

**Bottom Line**: Your deployments will UPDATE existing installations and preserve data. For a fresh start, you need to explicitly reset the database.

---

**Need help?** Check:
- `scripts/rollback.sh --help` - Rollback options
- `scripts/health-check.sh` - Check current state
- `BACKUP_RESTORE_SYSTEM_DOCUMENTATION.md` - Backup/restore details
