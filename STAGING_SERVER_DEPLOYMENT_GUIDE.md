# Staging Server Deployment Guide (Updated with HAProxy Details)

## 🎯 Why Staging First? (You're Doing It Right!)

**✅ HIGHLY RECOMMENDED** - This is the professional approach!

### Benefits:
1. ✅ **Test deployment script** without affecting local development
2. ✅ **Verify production configuration** in isolated environment
3. ✅ **Test HAProxy setup** safely before production
4. ✅ **Catch issues early** before real production
5. ✅ **Test data migration** process safely
6. ✅ **Train team** on new environment
7. ✅ **Performance testing** under production settings
8. ✅ **Keep local development** running uninterrupted

### Industry Best Practice:
```
Development (Local) → Staging (Test Server) → Production (Live Server)
      ↓                      ↓                          ↓
   Your laptop         Staging server            Production server
   (coding)            (testing)                 (customers)
```

---

## 📋 Staging Server Requirements

### Minimum Specifications

**Hardware**:
- CPU: 2 cores
- RAM: 4GB
- Disk: 20GB free space
- Network: Static IP or DHCP reservation

**Software**:
- OS: Ubuntu 20.04+ / Debian 11+ / CentOS 8+
- Docker 20.10+
- Docker Compose 2.x+
- Python 3.8+
- SSH access

**Recommended** (matches production):
- CPU: 4 cores
- RAM: 8GB
- Disk: 50GB SSD
- Dedicated server or VM

---

## 🚀 Step-by-Step Deployment to Staging

### Phase 1: Prepare Staging Server (5-10 minutes)

#### 1. Access Staging Server

```bash
# SSH into staging server
ssh user@staging-server-ip

# Or if using key:
ssh -i ~/.ssh/your-key.pem user@staging-server-ip
```

#### 2. Install Prerequisites

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add current user to docker group
sudo usermod -aG docker $USER

# Install Docker Compose
sudo apt install docker-compose-plugin -y

# Install Python3 and pip
sudo apt install python3 python3-pip -y

# Install cryptography package (for key generation)
pip3 install cryptography

# Verify installations
docker --version
docker compose version
python3 --version
```

#### 3. Configure Firewall

```bash
# Allow SSH
sudo ufw allow 22/tcp

# FOR DEPLOYMENT WITHOUT HAPROXY:
sudo ufw allow 8001/tcp  # Backend
sudo ufw allow 3001/tcp  # Frontend

# FOR DEPLOYMENT WITH HAPROXY (Alternative):
# sudo ufw allow 80/tcp    # HAProxy HTTP
# sudo ufw allow 443/tcp   # HAProxy HTTPS (optional)
# sudo ufw allow 8404/tcp  # HAProxy Stats (optional)

# Enable firewall
sudo ufw enable

# Check status
sudo ufw status
```

---

### Phase 2: Transfer Project Files (5 minutes)

#### Option A: Using Git (Recommended)

```bash
# On staging server
cd ~
git clone https://github.com/jinkaiteo/edms.git
cd edms

# Checkout specific branch/commit if needed
git checkout develop  # or specific commit: git checkout 6ace8e5
```

#### Option B: Using rsync (if no git)

```bash
# From your LOCAL machine
rsync -avz --exclude 'node_modules' \
           --exclude '__pycache__' \
           --exclude '*.pyc' \
           --exclude 'backend/edms_*.sqlite3' \
           --exclude '.env' \
           --exclude 'backups/' \
           /path/to/local/edms/ \
           user@staging-server-ip:~/edms/

# Then SSH to staging
ssh user@staging-server-ip
cd ~/edms
```

#### Option C: Using SCP

```bash
# From your LOCAL machine
# Create tarball first
cd /path/to/local
tar --exclude='node_modules' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='backend/edms_*.sqlite3' \
    --exclude='backups/' \
    -czf edms-staging.tar.gz edms/

# Copy to staging
scp edms-staging.tar.gz user@staging-server-ip:~/

# On staging server
ssh user@staging-server-ip
tar -xzf edms-staging.tar.gz
cd edms
```

---

### Phase 3: Verify Files on Staging (2 minutes)

```bash
# On staging server, in project directory
cd ~/edms

# Check critical files
ls -la deploy-interactive.sh
ls -la docker-compose.prod.yml
ls -la scripts/create-test-users.sh
ls -la scripts/initialize-workflow-defaults.sh
ls -la scripts/fix-reviewer-approver-roles.sh

# Make deployment script executable
chmod +x deploy-interactive.sh

# Verify DB_HOST fix is present (CRITICAL!)
grep "DB_HOST=db" deploy-interactive.sh
```

**Expected output**: Should show line 456 with `DB_HOST=db`

**If not present**, apply the fix:
```bash
sed -i 's/DB_HOST=postgres/DB_HOST=db/g' deploy-interactive.sh
grep "DB_HOST=db" deploy-interactive.sh  # Verify fix applied
```

---

### Phase 4: Run Deployment Script (15-20 minutes)

```bash
# On staging server
cd ~/edms

# Run deployment script
./deploy-interactive.sh
```

#### Recommended Configuration for Staging

When prompted, use these values:

```yaml
═══════════════════════════════════════════════════════════════
  Pre-flight Checks
═══════════════════════════════════════════════════════════════
# Script will automatically check Docker, disk space, etc.
# All should pass ✓

═══════════════════════════════════════════════════════════════
  Configuration Collection
═══════════════════════════════════════════════════════════════

Server Configuration:
  ? Server IP address [auto-detected]: <press Enter>
  ? Server hostname (optional) [edms-server]: edms-staging

Docker Port Configuration:
  ? Backend port [8001]: <press Enter>
  ? Frontend port [3001]: <press Enter>
  ? PostgreSQL port [5433]: <press Enter>
  ? Redis port [6380]: <press Enter>

Database Configuration:
  ? Database name [edms_production]: edms_staging
  ? Database user [edms_prod_user]: edms_staging_user
  ? Database password: <create-strong-password-12+-chars>
  ? Confirm password: <same-password>

Security Configuration:
  # SECRET_KEY and EDMS_MASTER_KEY generated automatically
  ? Session timeout (seconds) [3600]: <press Enter>

HAProxy Configuration:
  ? Will you be using HAProxy? [Y/n]: n  ⭐ RECOMMEND: NO for staging
  
  # Why NO for staging?
  # - Simpler setup for initial testing
  # - Direct access to services
  # - Easier debugging
  # - Can add later if needed

Optional: Monitoring
  ? Enable Sentry error tracking? [y/N]: n

═══════════════════════════════════════════════════════════════
  Configuration Summary
═══════════════════════════════════════════════════════════════
# Review all settings
# Verify ports, IPs, etc.

? Proceed with deployment? [Y/n]: y

═══════════════════════════════════════════════════════════════
  Environment File Creation
═══════════════════════════════════════════════════════════════
# .env file created with chmod 600

═══════════════════════════════════════════════════════════════
  Docker Deployment
═══════════════════════════════════════════════════════════════
# Building images (3-5 minutes)
# Starting containers

═══════════════════════════════════════════════════════════════
  Database Initialization
═══════════════════════════════════════════════════════════════
# Migrations
# Static files
# Default roles (7 roles)
# Default groups (6 groups)
# Test users (admin, author01, reviewer01, approver01)
# Document types (6 types)
# Document sources (3 sources)
# Workflow defaults
# Role assignments

═══════════════════════════════════════════════════════════════
  Admin User Creation
═══════════════════════════════════════════════════════════════
? Create admin user now? [Y/n]: y
  Username: admin
  Email address: admin@staging.local
  Password: <strong-admin-password>
  Password (again): <same-password>

═══════════════════════════════════════════════════════════════
  System Testing
═══════════════════════════════════════════════════════════════
# Health checks
# Container logs check

═══════════════════════════════════════════════════════════════
  HAProxy Setup
═══════════════════════════════════════════════════════════════
# Skipped (since we chose 'n')

═══════════════════════════════════════════════════════════════
  Deployment Complete! 🎉
═══════════════════════════════════════════════════════════════
```

---

### Phase 5: Post-Deployment Verification (5 minutes)

#### 1. Check Container Status

```bash
docker compose -f docker-compose.prod.yml ps
```

**Expected**: All containers "Up" and healthy
```
NAME                        STATUS              PORTS
edms_prod_backend           Up About a minute   0.0.0.0:8001->8000/tcp
edms_prod_frontend          Up About a minute   0.0.0.0:3001->80/tcp
edms_prod_db                Up About a minute   0.0.0.0:5433->5432/tcp
edms_prod_redis             Up About a minute   0.0.0.0:6380->6379/tcp
edms_prod_celery_worker     Up About a minute
edms_prod_celery_beat       Up About a minute
```

#### 2. Check Container Logs

```bash
# Backend logs
docker compose -f docker-compose.prod.yml logs backend | tail -50

# Look for successful startup
# Should see: "Booting worker" or "Listening at: http://0.0.0.0:8000"

# Frontend logs
docker compose -f docker-compose.prod.yml logs frontend | tail -20

# Check for errors
docker compose -f docker-compose.prod.yml logs | grep -i "error" | tail -20
```

#### 3. Test Backend Health

```bash
curl http://localhost:8001/health/
```

**Expected**: 
```json
{"status": "healthy", "timestamp": "...", ...}
```

#### 4. Test Frontend (from staging server)

```bash
curl -I http://localhost:3001/
```

**Expected**: `HTTP/1.1 200 OK`

#### 5. Test from Your Local Machine

```bash
# From your LOCAL computer
curl http://staging-server-ip:3001/
curl http://staging-server-ip:8001/health/
```

Both should return successfully.

#### 6. Access Web Interface

Open browser on your local machine:
```
http://staging-server-ip:3001
```

**Login with**:
- Username: `admin`
- Password: [your admin password]

**Or test users**:
- `author01` / `author01pass`
- `reviewer01` / `reviewer01pass`
- `approver01` / `approver01pass`

---

## 🎯 HAProxy Decision Guide

### When to Use HAProxy

#### ✅ **Use HAProxy if:**
- You want production-like setup
- Single port access desired (port 80/443)
- Professional URLs without ports
- Testing load balancing
- Need SSL/TLS termination
- Staging closely mirrors production

#### ❌ **Skip HAProxy if:**
- First time deploying
- Want simpler debugging
- Direct service access preferred
- Less infrastructure complexity
- Quick testing focus

---

## 🔧 Option: Adding HAProxy After Initial Deployment

If you deployed WITHOUT HAProxy and want to add it later:

### 1. Install HAProxy

```bash
sudo apt update
sudo apt install haproxy -y
```

### 2. Generate Configuration

The deployment script already created a template at `/tmp/edms-haproxy.cfg`.

If not present, create it:

```bash
sudo nano /etc/haproxy/haproxy.cfg
```

**Basic configuration**:
```
global
    log /dev/log local0
    maxconn 2000
    user haproxy
    group haproxy
    daemon

defaults
    log     global
    mode    http
    option  httplog
    timeout connect 5000
    timeout client  300000
    timeout server  300000

listen stats
    bind *:8404
    stats enable
    stats uri /
    stats refresh 30s

frontend edms_frontend
    bind *:80
    
    acl is_api path_beg /api/ /admin/ /static/ /media/ /health/
    use_backend backend_servers if is_api
    default_backend frontend_servers

backend backend_servers
    option httpchk GET /health/
    server backend1 127.0.0.1:8001 check inter 10s

backend frontend_servers
    option httpchk GET /
    server frontend1 127.0.0.1:3001 check inter 10s
```

### 3. Update Environment Variables

```bash
# Edit .env file
nano backend/.env

# Update these lines:
CORS_ALLOWED_ORIGINS=http://staging-server-ip
CSRF_TRUSTED_ORIGINS=http://staging-server-ip
# Remove :3001 from the URLs
```

### 4. Restart Services

```bash
# Restart backend to load new CORS settings
docker compose -f docker-compose.prod.yml restart backend

# Enable and start HAProxy
sudo systemctl enable haproxy
sudo systemctl start haproxy

# Check HAProxy status
sudo systemctl status haproxy
```

### 5. Update Firewall

```bash
# Allow HAProxy port
sudo ufw allow 80/tcp

# Optional: Stats dashboard
sudo ufw allow 8404/tcp
```

### 6. Test HAProxy

```bash
# From local machine
curl http://staging-server-ip/            # Frontend
curl http://staging-server-ip/api/        # Backend
curl http://staging-server-ip:8404        # Stats dashboard
```

---

## 📊 Access URLs Reference

### Without HAProxy (Recommended for Staging)

```
Frontend:    http://staging-server-ip:3001
Backend API: http://staging-server-ip:8001/api/
Admin Panel: http://staging-server-ip:8001/admin/
Health:      http://staging-server-ip:8001/health/
```

### With HAProxy

```
Frontend:    http://staging-server-ip/
Backend API: http://staging-server-ip/api/
Admin Panel: http://staging-server-ip/admin/
Health:      http://staging-server-ip/health/
Stats:       http://staging-server-ip:8404
```

---

## 📋 Functional Testing Checklist

### Critical Features to Test (30+ minutes)

#### **Authentication** ✅
- [ ] Login with admin
- [ ] Login with author01
- [ ] Login with reviewer01
- [ ] Login with approver01
- [ ] Logout
- [ ] Invalid credentials rejected

#### **Document Management** ✅
- [ ] Create new document
- [ ] Upload document file (DOCX, PDF)
- [ ] Edit document metadata
- [ ] View document details
- [ ] Search documents
- [ ] Delete document (if permitted)

#### **Workflow** ✅
- [ ] Submit document for review (as author01)
- [ ] Review document (as reviewer01)
- [ ] Approve document (as approver01)
- [ ] Check status transitions
- [ ] View workflow history

#### **User Management** (as admin) ✅
- [ ] Create new user
- [ ] Assign roles
- [ ] Edit user permissions
- [ ] Deactivate user
- [ ] View user list

#### **Reports** ✅
- [ ] Generate document report
- [ ] Check audit trail
- [ ] View system logs

#### **Backup System** ✅
```bash
# On staging server
./scripts/backup-hybrid.sh

# Verify backup created
ls -lh backups/

# Test restore (optional, creates test backup)
# WARNING: This will overwrite current data!
# Only do this if you want to test restore process
# ./scripts/restore-hybrid.sh backups/backup_YYYYMMDD_HHMMSS.tar.gz
```

---

## 🔧 Troubleshooting Common Issues

### Issue 1: "Cannot connect to Docker daemon"

```bash
# Solution
sudo systemctl start docker
sudo usermod -aG docker $USER
# Log out and back in
```

### Issue 2: "Port already in use"

```bash
# Check what's using the port
sudo lsof -i :8001

# Option 1: Kill the process
sudo kill -9 <PID>

# Option 2: Use different ports during deployment
# When prompted, use: 8002, 3002, etc.
```

### Issue 3: "Permission denied" on scripts

```bash
# Fix permissions
sudo chown -R $USER:$USER ~/edms
chmod +x deploy-interactive.sh
chmod +x scripts/*.sh
```

### Issue 4: Containers crash immediately

```bash
# Check logs
docker compose -f docker-compose.prod.yml logs backend

# Common causes:
# - Missing .env variables → Re-run deployment
# - Database connection failed → Check DB_HOST=db
# - Port conflicts → Use different ports
```

### Issue 5: Can't access from local machine

```bash
# On staging server, check firewall
sudo ufw status

# Allow the ports
sudo ufw allow 3001/tcp
sudo ufw allow 8001/tcp

# Check if services are listening
sudo netstat -tulpn | grep -E "3001|8001"
```

### Issue 6: Backend health check fails

```bash
# Wait a bit longer (backend may still be starting)
sleep 30
curl http://localhost:8001/health/

# Check backend logs
docker compose -f docker-compose.prod.yml logs backend | tail -50

# Look for:
# - Database connection errors
# - Missing migrations
# - Import errors
```

### Issue 7: Frontend shows white page

```bash
# Check frontend logs
docker compose -f docker-compose.prod.yml logs frontend

# Check if frontend can reach backend
docker compose -f docker-compose.prod.yml exec frontend ping backend

# Verify environment variables
docker compose -f docker-compose.prod.yml exec frontend env | grep API
```

---

## 📊 Monitoring Staging Server

### Resource Usage

```bash
# Check Docker resource usage
docker stats

# Check disk space
df -h

# Check memory
free -h

# Check CPU
top

# Check Docker volumes
docker volume ls
```

### Application Logs

```bash
# Tail all logs
docker compose -f docker-compose.prod.yml logs -f

# Specific service
docker compose -f docker-compose.prod.yml logs -f backend

# Last 100 lines
docker compose -f docker-compose.prod.yml logs --tail=100

# Search for errors
docker compose -f docker-compose.prod.yml logs | grep -i error | tail -50
```

### Health Checks

```bash
# Backend health
curl http://localhost:8001/health/ | python3 -m json.tool

# Database connection
docker compose -f docker-compose.prod.yml exec backend python manage.py dbshell

# Redis connection
docker compose -f docker-compose.prod.yml exec redis redis-cli ping
```

---

## 🔄 Iteration and Testing Cycle

### Making Changes and Redeploying

```bash
# On staging server

# 1. Pull latest changes (if using git)
cd ~/edms
git pull origin develop

# 2. Stop containers
docker compose -f docker-compose.prod.yml down

# 3. Rebuild (if code changed)
docker compose -f docker-compose.prod.yml build

# 4. Start containers
docker compose -f docker-compose.prod.yml up -d

# 5. Check status
docker compose -f docker-compose.prod.yml ps

# 6. Check logs
docker compose -f docker-compose.prod.yml logs -f
```

### Reset Staging (Clean Slate)

```bash
# CAUTION: This deletes ALL data!

# Stop and remove everything
docker compose -f docker-compose.prod.yml down -v

# Remove data directories
sudo rm -rf storage/*
sudo rm -rf logs/*
sudo rm -rf backend/.env
sudo rm -rf backups/*

# Redeploy from scratch
./deploy-interactive.sh
```

---

## 📋 Deployment Success Checklist

### Pre-Deployment ✅
- [ ] Staging server provisioned
- [ ] Docker and Docker Compose installed (20.10+, 2.x+)
- [ ] Python3 and cryptography installed
- [ ] Firewall configured (ports 3001, 8001)
- [ ] Project files transferred
- [ ] deploy-interactive.sh is executable
- [ ] DB_HOST=db verified

### During Deployment ✅
- [ ] Script runs without errors
- [ ] All containers start successfully
- [ ] Database migrations complete
- [ ] Default data created (roles, groups, types, sources)
- [ ] Test users created
- [ ] Admin user created
- [ ] Health checks pass
- [ ] No critical errors in logs

### Post-Deployment ✅
- [ ] All 6 containers running
- [ ] Backend health endpoint responds (200 OK)
- [ ] Frontend loads in browser
- [ ] Can login with admin
- [ ] Can login with test users
- [ ] Test users have correct roles
- [ ] Admin panel accessible

### Functional Testing ✅
- [ ] Create document works
- [ ] Upload file works
- [ ] Workflow submission works
- [ ] Review/approval works
- [ ] User management works
- [ ] Reports generate correctly
- [ ] Backup script works
- [ ] Search functionality works
- [ ] Document download works

### Performance ✅
- [ ] Page load times < 3 seconds
- [ ] API response times < 500ms
- [ ] No memory leaks (`docker stats` stable)
- [ ] Database queries optimized
- [ ] No N+1 query issues

---

## 🎯 When Staging is Ready for Production

### Sign-Off Checklist

- [ ] All functional tests passed
- [ ] Performance is acceptable
- [ ] No critical errors in logs
- [ ] Backup/restore process verified
- [ ] User acceptance testing completed
- [ ] Security review passed (if required)
- [ ] Documentation updated
- [ ] Team trained on new system
- [ ] Rollback plan documented
- [ ] Production server ready

### Migration Path to Production

Once staging is verified, deploy to production using the same process:

```bash
# 1. On production server
ssh user@production-server
cd ~
git clone https://github.com/jinkaiteo/edms.git
cd edms

# 2. Run deployment with PRODUCTION values
./deploy-interactive.sh

# Configuration for PRODUCTION:
# - Use production IP/domain
# - Strong passwords (20+ chars)
# - Enable HAProxy (port 80/443)
# - Enable Sentry (if available)
# - Shorter session timeout (if needed)

# 3. Migrate data (if needed from old system)
# Copy backup from old system
scp old-server:~/edms/backups/latest.tar.gz backups/
./scripts/restore-hybrid.sh backups/latest.tar.gz

# 4. Final verification
curl http://localhost:8001/health/
curl http://localhost:3001/

# 5. Configure HAProxy/SSL (if enabled)
# See HAPROXY_INTEGRATION_GUIDE.md

# 6. Update DNS (if using domain)
# Point domain to production server

# 7. Final smoke tests
# - Login works
# - Create document works
# - Workflow works
# - Backups work
```

---

## 📄 Documentation to Update

After successful staging deployment:

1. **Document staging URL** for team:
   ```
   Staging Frontend: http://staging-ip:3001
   Staging Admin: http://staging-ip:8001/admin
   Test Credentials: See internal wiki
   ```

2. **Update testing procedures**:
   - Add staging as required step
   - Document test scenarios
   - Create test data guidelines

3. **Record configuration** (securely):
   - Staging server IP
   - Admin credentials
   - Database credentials
   - Test user accounts

4. **Note any issues found**:
   - Create issue tracker entries
   - Document workarounds
   - Plan fixes before production

5. **Update production checklist** based on staging experience:
   - Add extra verification steps
   - Document timing estimates
   - Note any surprises

---

## 🎊 Quick Reference

### Staging Server Commands

```bash
# Access staging
ssh user@staging-server-ip

# Project directory
cd ~/edms

# Check status
docker compose -f docker-compose.prod.yml ps

# View logs
docker compose -f docker-compose.prod.yml logs -f backend

# Restart services
docker compose -f docker-compose.prod.yml restart

# Stop all
docker compose -f docker-compose.prod.yml down

# Full reset
docker compose -f docker-compose.prod.yml down -v
./deploy-interactive.sh

# Create backup
./scripts/backup-hybrid.sh

# Check cron jobs (if configured)
crontab -l
```

### Access URLs (Without HAProxy)

```
Frontend:    http://staging-server-ip:3001
Backend API: http://staging-server-ip:8001/api/
Admin Panel: http://staging-server-ip:8001/admin/
Health:      http://staging-server-ip:8001/health/
```

### Test User Credentials

```
admin       / [your-admin-password]
author01    / author01pass
reviewer01  / reviewer01pass
approver01  / approver01pass
```

---

## ✅ Success Criteria

Your staging deployment is successful when:

1. ✅ All containers running and healthy
2. ✅ Web interface accessible from your laptop
3. ✅ Can login with admin and test users
4. ✅ Can create and upload documents
5. ✅ Workflow submission and approval works
6. ✅ No critical errors in logs
7. ✅ Backup/restore tested successfully
8. ✅ Performance is acceptable
9. ✅ Team can access for testing
10. ✅ All functional tests pass

---

## 🎯 Recommended Staging Workflow

### Day 1: Initial Deployment
1. Set up staging server
2. Run deployment script (WITHOUT HAProxy)
3. Verify all services start
4. Quick smoke tests

### Day 2: Functional Testing
1. Complete functional test checklist
2. Test all user roles
3. Test workflows end-to-end
4. Document any issues

### Day 3: Performance & Edge Cases
1. Performance testing
2. Test error scenarios
3. Test backup/restore
4. Load testing (if applicable)

### Day 4: Team UAT
1. Team access testing
2. User acceptance testing
3. Collect feedback
4. Document findings

### Day 5: Production Prep
1. Fix any issues found
2. Update documentation
3. Plan production deployment
4. Create production checklist

---

**You're following industry best practices! This is the right approach!** 🎉

**Ready to deploy to staging?** The guide is complete and ready to use! 🚀

---

**Summary of Updates**:
- ✅ HAProxy decision guide added
- ✅ HAProxy post-deployment setup included
- ✅ Access URLs for both scenarios
- ✅ Firewall rules for both scenarios
- ✅ Recommended configuration (NO HAProxy for staging)
- ✅ Complete HAProxy integration steps
- ✅ Enhanced troubleshooting section
- ✅ 5-day staging workflow guide

**Total**: 1,089 lines of comprehensive staging deployment guidance!

