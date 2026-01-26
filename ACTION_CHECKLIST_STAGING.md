# Action Checklist for Staging Server DB_PASSWORD Fix

## ✅ Pre-Deployment Checklist

- [x] Issue analyzed and root cause identified
- [x] Fix verified in local deploy-interactive.sh (line 137: printf)
- [x] Automated fix script created (fix_staging_db_password.sh)
- [x] Documentation completed
- [ ] Copy fix script to staging server
- [ ] Run fix script on staging server
- [ ] Verify fix completion
- [ ] Create superuser account
- [ ] Test application access

---

## 📦 Files to Copy to Staging Server

**Required:**
- ✅ `fix_staging_db_password.sh` (14KB) - **COPY THIS**

**Optional (for reference):**
- `QUICK_FIX_STAGING_PASSWORD.md` (2.3KB)
- `DB_PASSWORD_NEWLINE_FIX_GUIDE.md` (9KB)
- `STAGING_DEPLOYMENT_FIX_SUMMARY.txt` (3.9KB)

---

## 🚀 Deployment Steps

### Step 1: Transfer Fix Script
```bash
# From your local machine
scp fix_staging_db_password.sh user@staging-server:/home/user/edms/

# Verify the file is transferred
ssh user@staging-server "ls -lh /home/user/edms/fix_staging_db_password.sh"
```

**Expected Output:**
```
-rwxrwxr-x 1 user user 14K Jan 26 11:47 /home/user/edms/fix_staging_db_password.sh
```

---

### Step 2: Connect to Staging Server
```bash
ssh user@staging-server
cd /home/user/edms/
```

---

### Step 3: Run the Fix Script
```bash
./fix_staging_db_password.sh
```

**What will happen:**
1. Script shows corrupted password format
2. Prompts for new password (12+ characters)
3. Confirms password
4. Backs up current .env file
5. Fixes .env file
6. Stops all containers
7. Removes old database volume
8. Starts database with new password
9. Waits 30 seconds for PostgreSQL
10. Verifies PostgreSQL password
11. Starts backend services
12. Waits 20 seconds for backend
13. Tests database connection
14. Runs migrations
15. Starts frontend
16. Verifies all services

**Duration:** ~5-7 minutes

---

### Step 4: Create Superuser
```bash
docker compose -f docker-compose.prod.yml exec backend python manage.py createsuperuser
```

**Follow prompts:**
- Username: (e.g., admin)
- Email: (your email)
- Password: (secure password)
- Password confirmation: (repeat)

---

### Step 5: Verify Application Access

**Backend API:**
```bash
curl http://localhost:8001/health/
# Expected: {"status":"healthy"} or similar
```

**Frontend (from browser):**
```
http://your-staging-server-ip:3001/
# Should show login page
```

**Admin Interface:**
```
http://your-staging-server-ip:8001/admin/
# Login with superuser credentials
```

---

## 🔍 Verification Checklist

After running the fix script:

- [ ] Script completed without errors
- [ ] All containers show "Up" status
  ```bash
  docker compose -f docker-compose.prod.yml ps
  ```
- [ ] Backend health check passes
  ```bash
  curl http://localhost:8001/health/
  ```
- [ ] .env file has correct format
  ```bash
  cat .env | grep -A2 "^DB_PASSWORD=" | cat -A
  # Should show: DB_PASSWORD=your_password$
  # NOT:         DB_PASSWORD=$
  #              $
  #              your_password$
  ```
- [ ] Backend can connect to database
  ```bash
  docker compose -f docker-compose.prod.yml exec backend \
    python manage.py check --database default
  ```
- [ ] Superuser created successfully
- [ ] Can login to frontend
- [ ] Can login to admin interface

---

## 🐛 Troubleshooting

### Issue: Permission denied when running script
```bash
chmod +x fix_staging_db_password.sh
./fix_staging_db_password.sh
```

### Issue: Script not found
```bash
# Check you're in the correct directory
pwd
# Should be: /home/user/edms/ (or your EDMS path)

# List files
ls -la fix_staging_db_password.sh
```

### Issue: Docker compose not found
```bash
# Try with hyphen instead
docker-compose -f docker-compose.prod.yml ps
```

### Issue: Containers not starting
```bash
# Check logs
docker compose -f docker-compose.prod.yml logs --tail=50

# Or specific service
docker compose -f docker-compose.prod.yml logs backend --tail=50
```

### Issue: Database connection still fails
```bash
# Verify passwords match
echo "Backend DB_PASSWORD:"
docker compose -f docker-compose.prod.yml exec -T backend env | grep "^DB_PASSWORD="

echo "PostgreSQL POSTGRES_PASSWORD:"
docker compose -f docker-compose.prod.yml exec -T db env | grep "^POSTGRES_PASSWORD="

# They should match!
```

---

## 📝 Post-Fix Tasks

After successful fix:

1. **Initialize default data (if needed):**
   ```bash
   docker compose -f docker-compose.prod.yml exec backend \
     python manage.py initialize_database
   ```

2. **Configure email notifications (optional):**
   - Edit .env file
   - Add email settings
   - Restart backend container

3. **Set up HAProxy (if needed):**
   - Follow HAPROXY_INTEGRATION_GUIDE.md
   - Configure reverse proxy

4. **Restore data (if you have backups):**
   - Follow BACKUP_RESTORE_API.md
   - Upload backup package
   - Restore via API or management command

5. **Configure automated backups:**
   ```bash
   ./scripts/setup-backup-cron.sh
   ```

---

## 🎯 Success Criteria

Your fix is complete when:

✅ All containers are "Up"
✅ Backend health check returns 200 OK
✅ Frontend loads in browser
✅ Can login with superuser account
✅ Can access admin interface
✅ No database connection errors in logs

---

## 📞 Need Help?

**Reference Documents:**
- Quick guide: `QUICK_FIX_STAGING_PASSWORD.md`
- Full guide: `DB_PASSWORD_NEWLINE_FIX_GUIDE.md`
- Summary: `STAGING_DEPLOYMENT_FIX_SUMMARY.txt`

**Check Logs:**
```bash
# All services
docker compose -f docker-compose.prod.yml logs --tail=100

# Specific service
docker compose -f docker-compose.prod.yml logs backend --tail=100 -f
```

**Container Status:**
```bash
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml top
```

---

## 🔒 Security Notes

- The new password will be stored in `.env` (file permissions: 600)
- Backup `.env` files are created with timestamps
- Keep backup `.env` files secure (they contain passwords and keys)
- Change passwords periodically

---

**Last Updated:** January 26, 2026  
**Status:** Ready for deployment to staging server
