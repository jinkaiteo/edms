# DB_PASSWORD Newline Corruption - Complete Fix Guide

## Issue Summary

**Error:** `psycopg2.OperationalError: connection to server at "db" (172.20.0.3), port 5432 failed: fe_sendauth: no password supplied`

**Root Cause:** The `deploy-interactive.sh` script had a bug in the `prompt_password()` function (prior to commit `715d85a`) that caused passwords to be written to the `.env` file with newlines, resulting in this format:

```bash
DB_PASSWORD=

actual_password_here
```

This causes Django/psycopg2 to read an empty string for `DB_PASSWORD` (stops at first newline), while PostgreSQL initializes with the actual password, causing authentication failures.

## Technical Details

### The Bug (Fixed in commit 715d85a)

**Before (Buggy Code - Line 136):**
```bash
prompt_password() {
    ...
    if [ "$password" = "$password_confirm" ]; then
        # Remove any newlines from password
        echo "$password" | tr -d '\n'  # BUG: echo adds newline before tr removes it
        break
    fi
}
```

**Problem:** 
- `echo "$password"` outputs the password with a trailing newline
- The newline goes to stdout first, then `tr -d '\n'` processes it
- But the command substitution `DB_PASSWORD=$(prompt_password ...)` captures output with newline intact
- Result: `.env` file gets created with password on separate line

**After (Fixed Code - Line 137):**
```bash
prompt_password() {
    ...
    if [ "$password" = "$password_confirm" ]; then
        # Return password without newlines
        printf '%s' "$password"  # FIX: printf '%s' doesn't add newline
        break
    fi
}
```

**Solution:**
- `printf '%s'` outputs exactly what's given without adding newlines
- Clean, simple, and reliable

## How to Verify If You Have This Issue

### Method 1: Visual Inspection with cat -A

```bash
cd /path/to/edms/project
cat .env | grep -A3 "^DB_PASSWORD" | cat -A
```

**Corrupted output looks like:**
```
DB_PASSWORD=$
$
password1234$
DB_HOST=db$
```

**Correct output looks like:**
```
DB_PASSWORD=password1234$
DB_HOST=db$
```

### Method 2: Check Password Length

```bash
DB_PASS=$(grep "^DB_PASSWORD=" .env | cut -d'=' -f2)
if [ -z "$DB_PASS" ]; then
    echo "CORRUPTED: DB_PASSWORD is empty"
else
    echo "OK: DB_PASSWORD has ${#DB_PASS} characters"
fi
```

### Method 3: Check Container Environment

```bash
docker compose -f docker-compose.prod.yml exec -T backend env | grep "^DB_PASSWORD="
```

If this shows `DB_PASSWORD=` with no value, the container has the corrupted password.

## Fix Options

### Option 1: Use the Automated Fix Script (Recommended)

**On your staging server:**

```bash
# 1. Copy the fix script to your server
scp fix_staging_db_password.sh user@staging-server:/path/to/edms/

# 2. SSH to the server
ssh user@staging-server

# 3. Navigate to project directory
cd /path/to/edms

# 4. Run the fix script
./fix_staging_db_password.sh
```

**What the script does:**
1. ✅ Diagnoses the corruption issue
2. ✅ Prompts for a new valid password
3. ✅ Backs up existing `.env` file
4. ✅ Fixes the `.env` file with correct password format
5. ✅ Recreates the PostgreSQL database with new password
6. ✅ Restarts all services
7. ✅ Runs migrations
8. ✅ Verifies the fix

### Option 2: Manual Fix

**Step 1: Stop all containers**
```bash
docker compose -f docker-compose.prod.yml down
```

**Step 2: Backup .env**
```bash
cp .env .env.backup.$(date +%Y%m%d-%H%M%S)
```

**Step 3: Fix .env file**
```bash
# Replace with your actual password (minimum 12 characters)
NEW_PASSWORD="your_secure_password_here"

# Fix the DB_PASSWORD line
sed -i "s|^DB_PASSWORD=.*|DB_PASSWORD=$NEW_PASSWORD|" .env

# Verify the fix
cat .env | grep "^DB_PASSWORD=" | cat -A
# Should show: DB_PASSWORD=your_secure_password_here$
```

**Step 4: Remove old database volume**
```bash
docker volume rm edms_postgres_prod_data
```

**Step 5: Start database**
```bash
docker compose -f docker-compose.prod.yml up -d db redis

# Wait for PostgreSQL to initialize
sleep 30
```

**Step 6: Start backend and run migrations**
```bash
docker compose -f docker-compose.prod.yml up -d backend celery_worker celery_beat

# Wait for backend to start
sleep 20

# Test database connection
docker compose -f docker-compose.prod.yml exec backend python manage.py check --database default

# Run migrations
docker compose -f docker-compose.prod.yml exec backend python manage.py migrate
```

**Step 7: Start frontend**
```bash
docker compose -f docker-compose.prod.yml up -d frontend
```

**Step 8: Verify all services**
```bash
docker compose -f docker-compose.prod.yml ps
```

## Prevention: Ensure You Have the Fixed Script

### Check if your script has the fix

```bash
grep -n "printf '%s' \"\$password\"" deploy-interactive.sh
```

**If you see output like:** `137:            printf '%s' "$password"`
- ✅ Your script has the fix

**If you see nothing:**
- ❌ Your script needs to be updated

### Update to the fixed version

```bash
# Check current commit
git log --oneline -1

# Pull latest changes
git pull origin main

# Verify the fix is present
git log --oneline --all | grep "715d85a"
# Should show: 715d85a fix: Remove newline from password prompt (DB_PASSWORD corruption)

# Verify the fix in the file
grep -A2 "Return password without newlines" deploy-interactive.sh
# Should show:
#   # Return password without newlines
#   printf '%s' "$password"
```

## Related Fixes

This issue was part of a series of authentication fixes:

1. **Commit `93ff43f`:** Remove Redis password requirement (causing auth errors)
2. **Commit `aaf88dd`:** Add env_file to PostgreSQL service (database auth failure)
3. **Commit `715d85a`:** Fix password prompt newline bug ⭐ (this issue)
4. **Commit `9dedef9`:** Add comprehensive DB password fix script

## Verification After Fix

### 1. Check .env file format
```bash
cat .env | grep -A2 "^DB_PASSWORD=" | cat -A
```
Should show password on same line with no blank lines.

### 2. Test backend database connection
```bash
docker compose -f docker-compose.prod.yml exec backend python manage.py check --database default
```
Should succeed with no errors.

### 3. Test backend health endpoint
```bash
BACKEND_PORT=$(grep "^BACKEND_PORT=" .env | cut -d'=' -f2)
curl http://localhost:${BACKEND_PORT:-8001}/health/
```
Should return `{"status":"healthy"}` or similar.

### 4. Check all containers are running
```bash
docker compose -f docker-compose.prod.yml ps
```
All services should show "Up" status.

## Post-Fix Next Steps

After fixing the database password issue:

1. **Create superuser account:**
   ```bash
   docker compose -f docker-compose.prod.yml exec backend python manage.py createsuperuser
   ```

2. **Initialize default data (if needed):**
   ```bash
   docker compose -f docker-compose.prod.yml exec backend python manage.py initialize_database
   ```

3. **Access the application:**
   - Backend API: `http://your-server-ip:8001/`
   - Frontend: `http://your-server-ip:3001/`
   - Or via HAProxy: `http://your-server-ip/` (if configured)

## Email Integration Note

After fixing the database password, you may want to configure email notifications. The deployment script also had a similar issue with email configuration that was fixed in commit `fe3f6d1`.

See: `EMAIL_NOTIFICATION_DEPLOYMENT_FIX.md` for details.

## Troubleshooting

### Issue: Script still creates corrupted passwords

**Check:** Is your `deploy-interactive.sh` up to date?
```bash
git log --oneline --all | grep "715d85a"
```

**Solution:** Pull the latest version with the fix.

### Issue: Database volume won't delete

**Error:** `Error response from daemon: volume is in use`

**Solution:**
```bash
# Stop all containers first
docker compose -f docker-compose.prod.yml down

# Then remove volume
docker volume rm edms_postgres_prod_data

# If still fails, remove all stopped containers
docker container prune -f
docker volume rm edms_postgres_prod_data
```

### Issue: Backend still can't connect after fix

**Check:** Does backend container have correct password?
```bash
docker compose -f docker-compose.prod.yml exec backend env | grep "^DB_PASSWORD="
```

**Check:** Does PostgreSQL have correct password?
```bash
docker compose -f docker-compose.prod.yml exec db env | grep "^POSTGRES_PASSWORD="
```

**Solution:** If they don't match, the containers need to be recreated:
```bash
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml up -d --force-recreate
```

## References

- **Fix Commit:** `715d85a` - Remove newline from password prompt
- **Related Script:** `fix_db_password_issue.sh` - Original diagnostic script
- **New Script:** `fix_staging_db_password.sh` - Complete automated fix
- **Email Fix:** `EMAIL_NOTIFICATION_DEPLOYMENT_FIX.md` - Related email configuration fix

## Summary

The DB_PASSWORD newline corruption bug was caused by using `echo "$password" | tr -d '\n'` instead of `printf '%s' "$password"` in the password prompt function. This bug has been fixed in commit `715d85a`, but any `.env` files created before this fix will need to be manually corrected or regenerated using the provided scripts.

---
**Last Updated:** January 26, 2026
**Status:** ✅ Fixed in main branch (commit 715d85a)
