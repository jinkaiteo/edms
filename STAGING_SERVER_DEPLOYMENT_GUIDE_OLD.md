# Staging Server Deployment Guide

## 🎯 Why Staging First? (You're Doing It Right!)

**✅ HIGHLY RECOMMENDED** - This is the professional approach!

### Benefits:
1. ✅ **Test deployment script** without affecting local development
2. ✅ **Verify production configuration** in isolated environment
3. ✅ **Catch issues early** before real production
4. ✅ **Test data migration** process safely
5. ✅ **Train team** on new environment
6. ✅ **Performance testing** under production settings
7. ✅ **Keep local development** running uninterrupted

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

#### 3. Configure Firewall (if needed)

```bash
# Allow SSH
sudo ufw allow 22/tcp

# Allow application ports (adjust as needed)
sudo ufw allow 8001/tcp  # Backend
sudo ufw allow 3001/tcp  # Frontend

# Optional: HAProxy
# sudo ufw allow 80/tcp
# sudo ufw allow 443/tcp

# Enable firewall
sudo ufw enable
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
git checkout develop  # or specific commit
```

#### Option B: Using rsync (if no git)

```bash
# From your LOCAL machine
rsync -avz --exclude 'node_modules' \
           --exclude '__pycache__' \
           --exclude '*.pyc' \
           --exclude 'backend/edms_*.sqlite3' \
           --exclude '.env' \
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

# Verify DB_HOST fix is present
grep "DB_HOST=db" deploy-interactive.sh
```

**Expected output**: Should show line with `DB_HOST=db`

---

### Phase 4: Run Deployment Script (15-20 minutes)

```bash
# On staging server
cd ~/edms

# Run deployment script
./deploy-interactive.sh
```

#### Sample Configuration for Staging

When prompted, use these values:

```yaml
Server Configuration:
  IP Address: [staging-server-ip] (auto-detected)
  Hostname: edms-staging

Docker Ports:
  Backend: 8001 (default)
  Frontend: 3001 (default)
  PostgreSQL: 5433 (default)
  Redis: 6380 (default)

Database Configuration:
  Name: edms_staging (or edms_production)
  User: edms_staging_user
  Password: [strong-password-12+-chars]

Session Configuration:
  Timeout: 3600 (1 hour)

HAProxy:
  Setup: n (not needed for staging)

Sentry:
  DSN: [leave empty or use staging DSN]

Admin User:
  Create: y
  Username: admin
  Email: admin@staging.local
  Password: [strong-admin-password]
```

---

### Phase 5: Post-Deployment Verification (5 minutes)

#### 1. Check Container Status

```bash
docker compose -f docker-compose.prod.yml ps
```

**Expected**: All containers "Up" and healthy

#### 2. Check Container Logs

```bash
# Backend logs
docker compose -f docker-compose.prod.yml logs backend | tail -50

# Frontend logs
docker compose -f docker-compose.prod.yml logs frontend | tail -20

# Check for errors
docker compose -f docker-compose.prod.yml logs | grep -i "error" | tail -20
```

#### 3. Test Backend Health

```bash
curl http://localhost:8001/health/
```

**Expected**: `{"status": "healthy", ...}`

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

#### 6. Access Web Interface

Open browser on your local machine:
```
http://staging-server-ip:3001
```

Try logging in with:
- Username: `admin`
- Password: [your admin password]

Or test users:
- `author01` / `author01pass`
- `reviewer01` / `reviewer01pass`
- `approver01` / `approver01pass`

---

### Phase 6: Functional Testing (30+ minutes)

#### Critical Features to Test

**Authentication**:
- [ ] Login with admin
- [ ] Login with test users
- [ ] Logout
- [ ] Password reset (if configured)

**Document Management**:
- [ ] Create new document
- [ ] Upload document file
- [ ] Edit document metadata
- [ ] Delete document
- [ ] Search documents

**Workflow**:
- [ ] Submit document for review
- [ ] Review document (as reviewer01)
- [ ] Approve document (as approver01)
- [ ] Check status changes

**User Management** (as admin):
- [ ] Create new user
- [ ] Assign roles
- [ ] Edit user permissions
- [ ] Deactivate user

**Reports**:
- [ ] Generate document report
- [ ] Check audit trail
- [ ] View system logs

**Backup System**:
```bash
# On staging server
./scripts/backup-hybrid.sh

# Verify backup created
ls -lh backups/

# Test restore (to verify it works)
./scripts/restore-hybrid.sh backups/backup_latest.tar.gz
```

---

## 📊 Staging vs Production Differences

### What Should Be SAME:
- ✅ Docker configuration (docker-compose.prod.yml)
- ✅ Deployment process (deploy-interactive.sh)
- ✅ Security settings (DEBUG=False, secrets)
- ✅ Container setup and health checks

### What Can Be DIFFERENT:
- 📍 Server IP address
- 📍 Domain name (staging.yourdomain.com vs yourdomain.com)
- 📍 Database size (smaller test data)
- 📍 SSL certificates (can use self-signed)
- 📍 Email settings (can use console backend)
- 📍 Monitoring/logging (less verbose)

---

## 🔧 Staging-Specific Configuration

### Create Staging .env Overrides

If you need staging-specific settings, create `.env.staging`:

```bash
# On staging server
cat > backend/.env.staging << 'ENVEOF'
# Staging-specific overrides
ENVIRONMENT=staging
ALLOWED_HOSTS=staging-server-ip,staging.yourdomain.com,localhost

# Less restrictive CORS for testing
CORS_ALLOWED_ORIGINS=http://staging-server-ip:3001,http://localhost:3001

# Console email backend (don't send real emails)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend

# More verbose logging for debugging
LOG_LEVEL=INFO

# Shorter session for testing
SESSION_COOKIE_AGE=1800

# Staging database
DB_NAME=edms_staging
ENVEOF
```

Then source it:
```bash
# Backend container will read .env by default
# No changes needed if using deploy-interactive.sh
```

---

## 🔄 Iteration and Testing Cycle

### Making Changes and Redeploying

```bash
# On staging server

# 1. Pull latest changes (if using git)
git pull origin develop

# 2. Rebuild containers
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d

# 3. Check logs
docker compose -f docker-compose.prod.yml logs -f

# 4. Test changes
curl http://localhost:8001/health/
```

### Reset Staging (Clean Slate)

```bash
# Stop and remove everything
docker compose -f docker-compose.prod.yml down -v

# Remove all data (CAUTION!)
sudo rm -rf storage/*
sudo rm -rf logs/*
sudo rm -rf backend/.env

# Redeploy from scratch
./deploy-interactive.sh
```

---

## 📋 Staging Deployment Checklist

### Before Deployment
- [ ] Staging server provisioned
- [ ] Docker and Docker Compose installed
- [ ] Firewall configured
- [ ] Project files transferred
- [ ] deploy-interactive.sh is executable
- [ ] DB_HOST fix verified (`grep "DB_HOST=db"`)

### During Deployment
- [ ] Script runs without errors
- [ ] All containers start successfully
- [ ] Health checks pass
- [ ] No errors in logs

### After Deployment
- [ ] All 6 containers running
- [ ] Backend health endpoint responds
- [ ] Frontend loads in browser
- [ ] Can login with admin
- [ ] Can login with test users
- [ ] Database migrations completed
- [ ] Test users and roles created
- [ ] Backup system works

### Functional Testing
- [ ] Create document works
- [ ] Upload file works
- [ ] Workflow submission works
- [ ] Review/approval works
- [ ] User management works
- [ ] Reports generate correctly
- [ ] Backup/restore tested

### Performance Testing
- [ ] Page load times acceptable
- [ ] API response times < 500ms
- [ ] Database queries optimized
- [ ] No memory leaks (check `docker stats`)

---

## 🚨 Common Staging Issues

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

# Kill the process or choose different port
# When running deploy-interactive.sh, use different ports
```

### Issue 3: "Permission denied" on files

```bash
# Fix permissions
sudo chown -R $USER:$USER ~/edms
chmod +x deploy-interactive.sh
```

### Issue 4: Containers crash immediately

```bash
# Check logs
docker compose -f docker-compose.prod.yml logs backend

# Common causes:
# - Missing .env variables
# - Database connection failed
# - Port conflicts
```

### Issue 5: Can't access from local machine

```bash
# Check firewall on staging server
sudo ufw status

# Allow the ports
sudo ufw allow 3001/tcp
sudo ufw allow 8001/tcp
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
```

### Application Logs

```bash
# Tail all logs
docker compose -f docker-compose.prod.yml logs -f

# Specific service
docker compose -f docker-compose.prod.yml logs -f backend

# Search for errors
docker compose -f docker-compose.prod.yml logs | grep -i error
```

---

## 🎯 When Staging is Ready for Production

### Sign-Off Checklist

- [ ] All functional tests passed
- [ ] Performance is acceptable
- [ ] No critical errors in logs
- [ ] Backup/restore process verified
- [ ] User acceptance testing completed
- [ ] Security review passed
- [ ] Documentation updated
- [ ] Team trained on new system

### Migration Path to Production

```bash
# 1. On production server, follow same steps:
ssh user@production-server
cd ~
git clone https://github.com/jinkaiteo/edms.git
cd edms

# 2. Run deployment (use production values)
./deploy-interactive.sh

# 3. Migrate data (if needed)
# Copy backup from old system
scp old-server:~/edms/backups/latest.tar.gz .
./scripts/restore-hybrid.sh latest.tar.gz

# 4. Final verification
curl http://localhost:8001/health/
```

---

## 📄 Documentation to Update

After successful staging deployment:

1. **Document staging URL** for team
2. **Update testing procedures**
3. **Record staging credentials** (securely!)
4. **Note any staging-specific configs**
5. **Create production deployment checklist** based on staging experience

---

## 🎊 Quick Reference

### Staging Server Commands

```bash
# Access staging
ssh user@staging-server-ip

# Check status
cd ~/edms
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
```

### Access URLs

```
Frontend:    http://staging-server-ip:3001
Backend API: http://staging-server-ip:8001/api/
Admin Panel: http://staging-server-ip:8001/admin/
Health:      http://staging-server-ip:8001/health/
```

---

## ✅ Success Criteria

Your staging deployment is successful when:

1. ✅ All containers running and healthy
2. ✅ Web interface accessible from your laptop
3. ✅ Can login and use all features
4. ✅ No critical errors in logs
5. ✅ Backup/restore works
6. ✅ Performance is acceptable
7. ✅ Team can access for testing

---

**You're following industry best practices! This is the right approach!** 🎉

**Next steps**: 
1. Set up staging server
2. Deploy using these instructions
3. Test thoroughly
4. Report any issues you find
5. When confident, deploy to production

Need help with any of these steps? Let me know! 🚀

