# Production Deployment Guide - Internal Network

**Date:** 2026-01-12  
**Target:** Internal Network Deployment  
**SSL:** Not required (internal use)  
**Estimated Time:** 1-2 hours

---

## ✅ **Pre-Deployment Checklist**

Before starting, verify:

- [ ] Production server is ready (Linux, Docker, Docker Compose installed)
- [ ] You have SSH access to production server
- [ ] Production server IP address is known
- [ ] You have decided on admin credentials
- [ ] You have decided on application title (or use default "EDMS")
- [ ] Database credentials are prepared (12+ character password)
- [ ] Staging deployment was successful (verified working)
- [ ] You have reviewed `PRODUCTION_READINESS_ASSESSMENT.md`

---

## 🎯 **What Will Be Deployed**

### **Included Features:**
✅ All core functionality (documents, workflows, users)  
✅ Automatic storage permissions setup  
✅ Automated backup system (daily/weekly/monthly)  
✅ Backup/restore scripts (100% tested)  
✅ Customizable app title  
✅ All UI improvements  
✅ All bug fixes and warnings resolved  

### **Latest Commits Being Deployed:**
- `4c1cb78` - Customizable application title
- `52bcd89` - Production frontend Dockerfile fix
- `0f1f752` - Workflow notification & staticfiles warnings fixed
- `7057a16` - Better button layout
- `c7ed922` - Last refresh timestamp
- `29a3232` - Create Document button only on My Tasks
- `363f96a` - Backup scripts read .env credentials
- `62ccf45` - Restore handles volume mounts correctly
- `197b597` - Automated backup setup
- `3a3d3d2` - Storage permissions auto-setup

---

## 🚀 **Deployment Steps**

### **Step 1: Prepare Production Server**

SSH into your production server:

```bash
ssh user@<production-server-ip>
```

Create the EDMS directory:

```bash
# Create directory
sudo mkdir -p /opt/edms
sudo chown $USER:$USER /opt/edms
cd /opt/edms
```

---

### **Step 2: Clone Repository**

```bash
# Clone from GitHub
git clone https://github.com/jinkaiteo/edms.git .

# Switch to develop branch (or main if that's your production branch)
git checkout develop

# Verify latest code
git log --oneline -5

# Should show recent commits including:
# - 4c1cb78 feat: Add customizable application title
# - 52bcd89 fix: Add REACT_APP_TITLE to production frontend Dockerfile
# - 0f1f752 fix: Resolve workflow notification and staticfiles warnings
```

---

### **Step 3: Run Interactive Deployment**

```bash
cd /opt/edms

# Make script executable
chmod +x deploy-interactive.sh

# Run interactive deployment
./deploy-interactive.sh
```

---

### **Step 4: Answer Configuration Prompts**

#### **Pre-flight Checks** (Automatic)
The script will check Docker, Python, Git - all should pass.

#### **Server Configuration**
```
? Server IP address [auto-detected]: <Press Enter or type production IP>
? Server hostname: edms-production
```

#### **Application Branding** (NEW!)
```
? Application title [EDMS]: <Type your company name or press Enter>
```
Examples:
- `TIKVA EDMS`
- `Quality Management System`
- `Document Control`
- Or just press Enter for `EDMS`

#### **Port Configuration**
For internal production, use standard ports:
```
? Backend port [8000]: 8000
? Frontend port [3000]: 3000
? PostgreSQL port [5432]: 5432
? Redis port [6379]: 6379
```

**Note:** These ports are only accessible within your internal network.

#### **Database Configuration**
```
? Database name: edms_production
? Database user: edms_prod_user
? Database password: <enter strong 12+ character password>
? Confirm password: <re-enter password>
```

**Important:** Save this password securely!

#### **Redis Configuration**
```
? Redis password: <enter password or press Enter for none>
```

#### **Django Configuration**
```
? Django secret key: <Press Enter - auto-generated>
? Debug mode [yes/no]: no
? Allowed hosts: <production-ip>,localhost,127.0.0.1,<hostname if any>
```

Examples for allowed hosts:
- `192.168.1.100,localhost,127.0.0.1`
- `10.0.0.50,localhost,127.0.0.1,edms.company.local`

#### **HAProxy Configuration**
```
? Use HAProxy reverse proxy [yes/no]: no
```
(Not needed for internal network)

#### **Review Configuration Summary**
The script shows all your settings. Review carefully!

```
? Proceed with deployment? [Y/n]: Y
```

---

### **Step 5: Watch Deployment Progress**

The script will automatically:

1. **Deploy Docker Containers** (3-5 min)
   - Build backend, frontend, database, redis, celery
   - 6 containers total

2. **Setup Storage Permissions** (10 sec)
   - Auto-detect container UID (usually 995)
   - Set ownership and permissions
   - ✅ No manual intervention needed!

3. **Initialize Database** (30-60 sec)
   - Run migrations
   - Create default groups, roles, workflow types
   - Setup document types and sources

4. **Create Admin User**
   ```
   ? Admin username: admin
   ? Admin email: admin@company.com
   ? Admin password: <12+ characters>
   ? Confirm password: <re-enter>
   ```

5. **Setup Automated Backups** (1-2 min)
   ```
   ? Set up automated backups now? [Y/n]: Y
   ```
   - Installs 3 cron jobs (daily/weekly/monthly)
   - Runs test backup
   - Shows schedule and location

6. **Test Deployment** (30 sec)
   - Backend health check
   - Frontend accessibility
   - Database connection

---

### **Step 6: Verify Deployment**

After deployment completes, verify everything is working:

#### **A. Check Container Status**
```bash
cd /opt/edms
docker compose -f docker-compose.prod.yml ps

# All should show "Up (healthy)":
# - edms_prod_backend
# - edms_prod_frontend
# - edms_prod_db
# - edms_prod_redis
# - edms_prod_celery_worker
# - edms_prod_celery_beat
```

#### **B. Check Backup System**
```bash
# Verify cron jobs
crontab -l | grep backup-hybrid.sh

# Should show 3 lines:
# 0 2 * * * ... (daily at 2 AM)
# 0 3 * * 0 ... (weekly at 3 AM Sunday)
# 0 4 1 * * ... (monthly at 4 AM on 1st)

# Verify test backup created
ls -lh backups/
# Should show at least 1 backup file
```

#### **C. Check Storage Permissions**
```bash
ls -la storage/

# Should show:
# drwxrwxr-x 2 995 995 ... documents/
# drwxrwxr-x 2 995 995 ... media/
```

#### **D. Test Backend Health**
```bash
curl http://localhost:8000/health/

# Should return: {"status":"healthy"}
```

#### **E. Test Frontend**
```bash
curl -I http://localhost:3000

# Should return: HTTP/1.1 200 OK
```

---

### **Step 7: Browser Testing**

#### **A. Access Frontend**

From any computer on your internal network:
```
http://<production-server-ip>:3000
```

Example: `http://192.168.1.100:3000`

#### **B. Login**
- Username: `admin`
- Password: (what you entered during deployment)

#### **C. Verify Custom Title**
- Login page should show your custom title
- Sidebar should show your custom title
- When collapsed, shows first letter of title

#### **D. Create Test Document**
1. Navigate to **My Tasks**
2. Click **"📝 Create Document"** button (should only appear here!)
3. Fill in document details
4. Upload a test file
5. Submit

**Expected Results:**
- ✅ Document created successfully
- ✅ File uploaded without permission errors
- ✅ Document appears in list
- ✅ Refresh timestamp updates when you click Refresh

#### **E. Test Workflow**
1. Open the test document
2. Click **"Submit for Review"**
3. Verify status changes to **"Under Review"**
4. No errors should appear

---

## 🔒 **Post-Deployment Security (Internal Network)**

### **Recommended Actions:**

#### **1. Firewall Configuration**
Since this is internal, block external access:

```bash
# Allow only internal network (example: 192.168.1.0/24)
sudo ufw allow from 192.168.1.0/24 to any port 3000
sudo ufw allow from 192.168.1.0/24 to any port 8000

# Block external access
sudo ufw deny 3000
sudo ufw deny 8000

# Enable firewall
sudo ufw enable
```

#### **2. Restrict Database/Redis Ports**
Already configured in docker-compose.prod.yml:
- Database and Redis are NOT exposed to host
- Only accessible within Docker network
- ✅ Good security practice

#### **3. Backup Important Files**
```bash
# Backup .env file (contains passwords)
cp /opt/edms/.env /opt/edms/.env.backup
chmod 600 /opt/edms/.env.backup

# Store backup securely (not on same server)
# Consider copying to:
# - Network storage
# - USB drive
# - Password manager
```

---

## 📊 **Monitoring & Maintenance**

### **Daily:**
- [ ] Check that all 6 containers are healthy
  ```bash
  cd /opt/edms && docker compose -f docker-compose.prod.yml ps
  ```

### **Weekly:**
- [ ] Verify backups are being created
  ```bash
  ls -lh /opt/edms/backups/
  ```
- [ ] Check logs for errors
  ```bash
  docker compose -f docker-compose.prod.yml logs --tail=100 | grep ERROR
  ```

### **Monthly:**
- [ ] Test backup restoration (on staging, not production!)
- [ ] Review disk space usage
  ```bash
  df -h
  du -sh /opt/edms/storage/
  ```
- [ ] Check for system updates
  ```bash
  sudo apt update && sudo apt list --upgradable
  ```

### **Quarterly:**
- [ ] Review user accounts (deactivate inactive users)
- [ ] Review document retention (if policy created)
- [ ] Check system performance
- [ ] Review audit logs

---

## 🔄 **Backup & Restore Procedures**

### **Manual Backup**
```bash
cd /opt/edms
./scripts/backup-hybrid.sh

# Backup created in: backups/backup_YYYYMMDD_HHMMSS.tar.gz
```

### **Manual Restore**
```bash
cd /opt/edms
./scripts/restore-hybrid.sh backups/backup_YYYYMMDD_HHMMSS.tar.gz

# Answer 'yes' to confirmation prompt
# Restore completes in ~15 seconds
```

### **Automated Backups**
Already configured! Running:
- **Daily:** 2:00 AM every day
- **Weekly:** 3:00 AM every Sunday
- **Monthly:** 4:00 AM on the 1st of each month

### **Off-Site Backup (Recommended)**

Add this to cron for off-site copies:

```bash
# Edit cron
crontab -e

# Add after backup jobs:
# Copy backups to network storage daily at 5 AM
0 5 * * * rsync -avz /opt/edms/backups/ /mnt/network-storage/edms-backups/

# Or copy to another server
0 5 * * * scp /opt/edms/backups/backup_$(date +\%Y\%m\%d)*.tar.gz backup-server:/backups/edms/
```

---

## 📝 **User Management**

### **Create Additional Users**

Option 1: Via Admin Panel
1. Login as admin
2. Navigate to `http://<server-ip>:8000/admin/`
3. Click **Users** → **Add User**
4. Fill in details, assign roles
5. Save

Option 2: Via Command Line
```bash
cd /opt/edms
docker compose -f docker-compose.prod.yml exec backend python manage.py shell

# In Python shell:
from django.contrib.auth import get_user_model
User = get_user_model()

user = User.objects.create_user(
    username='john.doe',
    email='john.doe@company.com',
    password='SecurePassword123!',
    first_name='John',
    last_name='Doe'
)
print(f"Created user: {user.username}")
exit()
```

### **Assign Roles**
Use the seeding script or admin panel:
```bash
docker compose -f docker-compose.prod.yml exec backend python manage.py seed_test_users
```

Or assign manually in admin panel.

---

## 🆘 **Troubleshooting**

### **Issue: Container Not Starting**
```bash
# Check logs
docker compose -f docker-compose.prod.yml logs <service-name>

# Example:
docker compose -f docker-compose.prod.yml logs backend --tail=50
```

### **Issue: Cannot Access Frontend**
```bash
# Verify container is running
docker compose -f docker-compose.prod.yml ps frontend

# Check if port is accessible
curl http://localhost:3000

# Check firewall
sudo ufw status
```

### **Issue: Database Connection Error**
```bash
# Verify database is running
docker compose -f docker-compose.prod.yml ps db

# Test connection
docker compose -f docker-compose.prod.yml exec db psql -U edms_prod_user -d edms_production -c "SELECT 1;"
```

### **Issue: Backup Failed**
```bash
# Check backup logs
cat /opt/edms/logs/backup.log

# Verify .env has correct credentials
grep -E "DB_NAME|DB_USER" /opt/edms/.env

# Test manual backup
cd /opt/edms && ./scripts/backup-hybrid.sh
```

### **Issue: Permission Denied on File Upload**
```bash
# Check storage permissions
ls -la /opt/edms/storage/

# Fix if needed
docker compose -f docker-compose.prod.yml exec backend chown -R 995:995 /app/storage
docker compose -f docker-compose.prod.yml restart backend
```

---

## 🔄 **Update/Upgrade Procedures**

### **Minor Updates (Bug Fixes)**
```bash
cd /opt/edms

# Backup first!
./scripts/backup-hybrid.sh

# Pull latest code
git pull origin develop

# Restart services
docker compose -f docker-compose.prod.yml restart backend frontend

# Verify
docker compose -f docker-compose.prod.yml ps
```

### **Major Updates (New Features)**
```bash
cd /opt/edms

# Full backup
./scripts/backup-hybrid.sh

# Pull latest code
git pull origin develop

# Rebuild containers
docker compose -f docker-compose.prod.yml build

# Restart with new images
docker compose -f docker-compose.prod.yml up -d

# Run migrations if needed
docker compose -f docker-compose.prod.yml exec backend python manage.py migrate

# Verify
docker compose -f docker-compose.prod.yml ps
```

---

## 📞 **Support & Documentation**

### **Documentation Files:**
- `PRODUCTION_READINESS_ASSESSMENT.md` - Complete readiness report
- `COMPLIANCE_QUICK_CHECK_REPORT.md` - Compliance assessment
- `BACKUP_RESTORE_TESTING_GUIDE.md` - Comprehensive backup testing
- `STAGING_FRESH_DEPLOYMENT_GUIDE.md` - Deployment procedures
- `RECORD_RETENTION_POLICY_GUIDE.md` - Retention policy creation

### **Log Files:**
```bash
# Application logs
tail -f /opt/edms/logs/edms.log

# Backup logs
tail -f /opt/edms/logs/backup.log

# Container logs
docker compose -f docker-compose.prod.yml logs -f
```

### **Useful Commands:**
```bash
# Check system status
cd /opt/edms && docker compose -f docker-compose.prod.yml ps

# Restart all services
cd /opt/edms && docker compose -f docker-compose.prod.yml restart

# Stop all services
cd /opt/edms && docker compose -f docker-compose.prod.yml down

# Start all services
cd /opt/edms && docker compose -f docker-compose.prod.yml up -d

# View logs
cd /opt/edms && docker compose -f docker-compose.prod.yml logs -f backend
```

---

## ✅ **Deployment Success Checklist**

After deployment, verify:

### **System:**
- [ ] All 6 containers running and healthy
- [ ] Storage permissions: 995:995 with 775
- [ ] 3 backup cron jobs installed
- [ ] Test backup file created
- [ ] Backend health endpoint responds
- [ ] Frontend accessible from internal network

### **Functionality:**
- [ ] Can login with admin credentials
- [ ] Custom app title appears correctly
- [ ] Can create new document
- [ ] Can upload file successfully
- [ ] Can submit document for review
- [ ] Workflow progresses correctly
- [ ] Refresh button shows timestamp

### **Security:**
- [ ] Firewall configured (internal network only)
- [ ] .env file backed up securely
- [ ] Database not accessible from external network
- [ ] Redis not accessible from external network

### **Documentation:**
- [ ] Admin credentials documented securely
- [ ] Database credentials documented
- [ ] Server IP documented
- [ ] Access URLs documented for users

---

## 🎊 **Production Deployment Complete!**

**Your EDMS is now live in production!** 🎉

### **Access URLs:**
- **Frontend:** `http://<production-ip>:3000`
- **Admin Panel:** `http://<production-ip>:8000/admin/`
- **API Documentation:** `http://<production-ip>:8000/api/v1/`

### **Next Steps:**
1. ✅ Announce to users
2. ✅ Provide access URL and instructions
3. ✅ Create user accounts
4. ✅ Monitor for first week
5. ✅ Schedule first quarterly review

---

**Congratulations on your production deployment!** 🚀

---

**Deployment Date:** [Fill in]  
**Deployed By:** [Fill in]  
**Production Server:** [Fill in]  
**App Title:** [Fill in]
