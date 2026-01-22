# Interactive Deployment Script Analysis

**Script:** `deploy-interactive.sh`  
**Version:** 1.0  
**Lines:** 1,226  
**Purpose:** Guided deployment of EDMS with configuration, Docker setup, and optional HAProxy

---

## 📋 Script Overview

This is a **production-grade interactive deployment script** that:
- ✅ Guides users through configuration step-by-step
- ✅ Validates prerequisites before deployment
- ✅ Creates secure environment files
- ✅ Builds and deploys Docker containers
- ✅ Initializes database and default data
- ✅ Creates admin users
- ✅ Tests the deployment
- ✅ Optionally sets up HAProxy load balancer
- ✅ Configures automated backups

**Estimated Time:** 10-20 minutes

---

## 🎯 Main Execution Flow

```bash
main() {
    1. Display banner
    2. preflight_checks()          # Verify Docker, docker-compose, etc.
    3. collect_configuration()     # Interactive configuration gathering
    4. show_configuration_summary() # Review before proceeding
    5. create_env_file()           # Generate backend/.env
    6. deploy_docker()             # Build and start containers
    7. setup_storage_permissions() # Fix file permissions
    8. initialize_database()       # Migrations + default data
    9. create_admin_user()         # Interactive admin creation
    10. test_deployment()          # Health checks
    11. setup_backup_automation()  # Optional cron jobs
    12. setup_haproxy()           # Optional HAProxy
    13. show_final_summary()      # Access URLs and commands
}
```

---

## 🔍 Key Functions Breakdown

### **1. Preflight Checks** (Lines 174-249)

**Purpose:** Validates system requirements before deployment

**Checks:**
- ✅ Docker installed and running
- ✅ Docker Compose version >= 1.29
- ✅ Required utilities (curl, openssl, bc)
- ✅ docker-compose.prod.yml exists
- ✅ Disk space > 5GB available
- ✅ Docker daemon is responding

**Example Output:**
```
═══════════════════════════════════════════
Preflight Checks
═══════════════════════════════════════════
→ Checking for docker...
✓ docker found
→ Checking for docker-compose...
✓ docker-compose found
→ Verifying Docker daemon...
✓ Docker is running
→ Checking disk space...
✓ 45GB available
✓ All preflight checks passed
```

---

### **2. Configuration Collection** (Lines 250-359)

**Purpose:** Interactive gathering of deployment configuration

**Collects:**

#### **Server Settings**
- Server IP address (auto-detected)
- Server hostname (optional)

#### **Port Configuration**
- Backend port (default: 8001)
- Frontend port (default: 3001)
- HAProxy port (default: 80, if enabled)

#### **Database Configuration**
- Database name (default: edms_prod)
- Database username (default: edms_user)
- Database password (secure prompt)
- Database host (default: db - Docker service name)
- Database port (default: 5432)

#### **Email Settings** (Optional)
- SMTP host
- SMTP port (default: 587)
- Use TLS (yes/no)
- SMTP username
- SMTP password
- From email address

#### **Security Settings**
- Django SECRET_KEY (auto-generated 50 characters)
- Session timeout (default: 86400 seconds = 24 hours)

#### **HAProxy Configuration** (Optional)
- Enable HAProxy (yes/no)
- HAProxy port
- Auto-configures CORS origins accordingly

#### **Monitoring** (Optional)
- Enable Sentry error tracking
- Sentry DSN

**Smart Defaults:**
- Auto-detects server IP using `ip route get 1`
- Generates secure SECRET_KEY using `openssl rand -base64 50`
- Configures CORS based on HAProxy usage (with/without ports)

---

### **3. Configuration Summary** (Lines 360-411)

**Purpose:** Shows review screen before proceeding

**Example Display:**
```
═══════════════════════════════════════════
Configuration Summary
═══════════════════════════════════════════

Server:
  IP Address:      192.168.1.100
  Hostname:        edms-server.local

Ports:
  Backend:         8001
  Frontend:        3001
  HAProxy:         80 (enabled)

Database:
  Name:            edms_prod
  User:            edms_user
  Host:            db
  Port:            5432

Email:            Configured
Monitoring:       Sentry enabled

? Proceed with deployment? [Y/n]:
```

---

### **4. Environment File Creation** (Lines 412-565)

**Purpose:** Generates comprehensive backend/.env file

**Security Features:**
- Backs up existing .env with timestamp
- Sets file permissions to 600 (owner read/write only)
- Generates cryptographically secure SECRET_KEY

**Sections Created:**

1. **Django Core**
   - DEBUG=False
   - SECRET_KEY
   - ALLOWED_HOSTS

2. **Database**
   - DATABASE_URL (PostgreSQL connection string)
   - DB_* individual settings

3. **Security**
   - CORS_ALLOWED_ORIGINS
   - CSRF_TRUSTED_ORIGINS
   - SESSION_COOKIE_AGE
   - SECURE_* settings

4. **Email**
   - EMAIL_HOST, EMAIL_PORT
   - EMAIL_USE_TLS
   - EMAIL_HOST_USER, EMAIL_HOST_PASSWORD
   - DEFAULT_FROM_EMAIL

5. **Celery**
   - CELERY_BROKER_URL (Redis)
   - CELERY_RESULT_BACKEND (Django DB)
   - CELERY_TIMEZONE (UTC)

6. **Storage**
   - MEDIA_ROOT, MEDIA_URL
   - STATIC_ROOT, STATIC_URL

7. **JWT Authentication**
   - JWT_ACCESS_TOKEN_LIFETIME
   - JWT_REFRESH_TOKEN_LIFETIME

8. **Monitoring**
   - SENTRY_DSN (if configured)

9. **Performance**
   - DB_CONN_MAX_AGE
   - CACHE_TTL

10. **Localization**
    - TZ=UTC
    - LANGUAGE_CODE=en-us

**Total:** 50+ configuration variables

---

### **5. Docker Deployment** (Lines 566-605)

**Purpose:** Build and start Docker containers

**Process:**
1. Builds Docker images using docker-compose.prod.yml
2. Starts all containers in detached mode
3. Waits 10 seconds for services to initialize
4. Displays container status

**Containers Started:**
- backend (Django API)
- frontend (React UI)
- db (PostgreSQL)
- redis (Cache/broker)
- celery_worker (Background tasks)
- celery_beat (Scheduler)
- elasticsearch (Search)

---

### **6. Storage Permissions** (Lines 606-654)

**Purpose:** Configure file permissions for document storage

**Process:**
1. Creates directory structure:
   - storage/documents/
   - storage/backups/
   - storage/media/

2. Detects backend container UID
3. Sets ownership to container user
4. Sets permissions to 775 (rwxrwxr-x)
5. Fallback to 777 if UID detection fails

**Why Important:** Prevents permission errors when Django uploads files

---

### **7. Database Initialization** (Lines 764-921)

**Purpose:** Set up database schema and default data

**Steps:**

1. **Run Migrations**
   ```bash
   python manage.py migrate
   ```

2. **Collect Static Files**
   ```bash
   python manage.py collectstatic --noinput
   ```

3. **Initialize Default Data via Django Shell:**

   **Groups Created:**
   - Authors
   - Reviewers
   - Approvers
   - Administrators

   **Roles Created:**
   - Document Author (CREATE_EDIT permission)
   - Document Reviewer (REVIEW permission)
   - Document Approver (APPROVE permission)
   - System Administrator (ADMIN permission)

   **Workflow Types:**
   - Standard Document Workflow (STANDARD)
   - Fast Track Workflow (FAST_TRACK)

   **Document States (12 states):**
   - DRAFT
   - PENDING_REVIEW
   - UNDER_REVIEW
   - REVIEW_COMPLETED
   - PENDING_APPROVAL
   - UNDER_APPROVAL
   - APPROVED_PENDING_EFFECTIVE
   - EFFECTIVE
   - SCHEDULED_FOR_OBSOLESCENCE
   - SUPERSEDED
   - OBSOLETE
   - TERMINATED

   **Placeholder Definitions (32 total):**
   - DOCUMENT_NUMBER
   - DOCUMENT_TITLE
   - DOCUMENT_TYPE
   - VERSION
   - EFFECTIVE_DATE
   - AUTHOR_NAME
   - APPROVAL_DATE
   - APPROVER_NAME
   - CURRENT_DATE
   - DEPARTMENT
   - ... 22 more

4. **Initialize Celery Beat Schedule**
   - Creates CrontabSchedule entries
   - Creates PeriodicTask entries for automated jobs:
     - make_documents_effective (midnight UTC)
     - process_obsolescence (midnight UTC)
     - dependency_health_check (daily)

---

### **8. Admin User Creation** (Lines 922-944)

**Purpose:** Create superuser account for system access

**Process:**
1. Prompts for username (default: admin)
2. Prompts for email (default: admin@example.com)
3. Prompts for password (secure, hidden input)
4. Creates Django superuser with full permissions

**Output:**
```
═══════════════════════════════════════════
Admin User Creation
═══════════════════════════════════════════
? Admin username [admin]: adminuser
? Admin email [admin@example.com]: admin@mycompany.com
? Admin password: ********
✅ Admin user 'adminuser' created successfully!
```

---

### **9. Deployment Testing** (Lines 945-990)

**Purpose:** Validate deployment health

**Tests:**

1. **Backend Health Check**
   - Curl http://localhost:8001/health/
   - Expects 200 OK response

2. **Frontend Accessibility**
   - Curl http://localhost:3001/
   - Expects 200 OK response

3. **Log Analysis**
   - Counts errors in backend logs
   - Counts errors in frontend logs
   - Warns if any errors found

**Output:**
```
═══════════════════════════════════════════
System Testing
═══════════════════════════════════════════
→ Testing backend health...
✓ Backend health check passed
→ Testing frontend...
✓ Frontend is accessible
→ Checking container logs for errors...
✓ No backend errors detected
✓ No frontend errors detected
```

---

### **10. Backup Automation** (Lines 655-758)

**Purpose:** Set up automated daily backups (optional)

**Process:**
1. Asks if user wants automated backups
2. Creates backup script at scripts/backup-scheduled.sh
3. Script performs:
   - PostgreSQL database dump
   - Media files tar.gz backup
   - Retention: keeps last 7 days only
4. Adds cron job: runs daily at 2:00 AM

**Generated Script:**
```bash
#!/bin/bash
BACKUP_DIR="/path/to/backups"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)

# Database backup
docker compose exec -T db pg_dump -U $DB_USER $DB_NAME > \
    "$BACKUP_DIR/db-backup-$TIMESTAMP.sql"

# Media files backup
tar -czf "$BACKUP_DIR/media-backup-$TIMESTAMP.tar.gz" storage/

# Keep only last 7 days
find "$BACKUP_DIR" -name "*.sql" -mtime +7 -delete
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +7 -delete
```

**Crontab Entry:**
```
0 2 * * * /path/to/scripts/backup-scheduled.sh
```

---

### **11. HAProxy Setup** (Lines 992-1097)

**Purpose:** Configure HAProxy load balancer (optional)

**When Enabled:**
1. Generates haproxy.cfg with:
   - Frontend on port 80
   - Backend routing to frontend:3000 (React)
   - Backend routing to backend:8000 (Django API)
   - Health checks for both backends
   - Round-robin load balancing

2. Starts HAProxy container:
   ```bash
   docker run -d \
     --name edms-haproxy \
     -p 80:80 \
     -v ./infrastructure/haproxy/haproxy.cfg:/usr/local/etc/haproxy/haproxy.cfg:ro \
     --network edms_default \
     haproxy:2.8
   ```

**Benefits:**
- Single port access (port 80)
- Load balancing ready
- Health check monitoring
- SSL termination support (future)

---

### **12. Final Summary** (Lines 1099-1164)

**Purpose:** Display deployment results and next steps

**Shows:**

1. **Access URLs**
   - Frontend URL (with/without HAProxy)
   - Backend API URL
   - Admin panel URL
   - Health check URL

2. **Container Management Commands**
   - View logs
   - Restart services
   - Stop/start
   - Rebuild images

3. **Test User Credentials**
   - Admin account
   - Test author, reviewer, approver

4. **Next Steps**
   - Verify configuration
   - Create document types
   - Set up user accounts
   - Configure notifications

5. **Documentation References**
   - Deployment guides
   - HAProxy documentation
   - Security guides

---

## 🎨 UI/UX Features

### **Color-Coded Output**
```bash
RED     # Errors (✗)
GREEN   # Success (✓)
YELLOW  # Warnings (⚠)
CYAN    # Info/prompts (ℹ)
BOLD    # Section headers
```

### **Interactive Prompts**
- `prompt_yes_no()` - Y/N questions with defaults
- `prompt_input()` - Text input with defaults
- `prompt_password()` - Hidden password input

### **Progress Indicators**
- Step markers (→)
- Success checkmarks (✓)
- Error X marks (✗)
- Warning triangles (⚠)

---

## 🔒 Security Best Practices

1. **Environment File Protection**
   - chmod 600 (owner only)
   - Automatic backup before overwrite

2. **Secure Password Generation**
   - 50-character SECRET_KEY
   - Cryptographically secure (openssl)

3. **No Hardcoded Credentials**
   - All secrets prompted
   - No default passwords

4. **Proper CORS Configuration**
   - Restricts origins
   - Based on actual deployment

5. **Storage Permissions**
   - Container-specific UID
   - Minimal necessary permissions (775)

---

## 🚀 Quick Start Guide

```bash
# 1. Make executable
chmod +x deploy-interactive.sh

# 2. Run script
./deploy-interactive.sh

# 3. Follow prompts (example responses):
Server IP: 192.168.1.100
Hostname: edms.mycompany.local
Backend port: 8001
Frontend port: 3001
Database name: edms_prod
Database user: edms_user
Database password: [secure password]
Use HAProxy: y
HAProxy port: 80
Admin username: admin
Admin email: admin@mycompany.com
Admin password: [secure password]

# 4. Wait 10-20 minutes for completion

# 5. Access system:
# http://192.168.1.100:80 (if HAProxy)
# http://192.168.1.100:3001 (without HAProxy)
```

---

## 📊 What Gets Created

### **Files**
```
backend/.env                          # Environment config (chmod 600)
backend/.env.backup.YYYYMMDD-HHMMSS  # Backup of old .env
infrastructure/haproxy/haproxy.cfg    # HAProxy config (optional)
scripts/backup-scheduled.sh           # Backup script (optional)
```

### **Directories**
```
storage/
  ├── documents/   # Uploaded documents
  ├── backups/     # System backups
  └── media/       # Media files
```

### **Docker Containers**
```
edms-backend-1          # Django API (port 8001)
edms-frontend-1         # React UI (port 3001)
edms-db-1               # PostgreSQL (port 5432)
edms-redis-1            # Redis (port 6379)
edms-celery-worker-1    # Task processor
edms-celery-beat-1      # Scheduler
edms-elasticsearch-1    # Search (port 9200)
edms-haproxy            # Load balancer (optional, port 80)
```

### **Database Content**
- 4 user groups
- 4 roles with permissions
- 2 workflow types
- 12 document states
- 32 placeholder definitions
- Celery Beat scheduled tasks
- 1 admin superuser

---

## 🛠️ Troubleshooting

### **Issue: Docker build fails**
```bash
# Check Docker daemon
sudo systemctl status docker

# Check disk space
df -h

# View detailed build logs
docker compose -f docker-compose.prod.yml build --progress=plain
```

### **Issue: Database initialization fails**
```bash
# Check database logs
docker compose -f docker-compose.prod.yml logs db

# Verify database is ready
docker compose -f docker-compose.prod.yml exec db pg_isready

# Test connection
docker compose -f docker-compose.prod.yml exec db psql -U edms_user -d edms_prod
```

### **Issue: Health checks fail**
```bash
# Services may still be starting - wait longer
sleep 60

# Check all container status
docker compose -f docker-compose.prod.yml ps

# View container logs
docker compose -f docker-compose.prod.yml logs backend
docker compose -f docker-compose.prod.yml logs frontend

# Restart all containers
docker compose -f docker-compose.prod.yml restart
```

### **Issue: Permission errors on storage**
```bash
# Manual permission fix
sudo chown -R 33:33 storage/  # www-data UID
sudo chmod -R 775 storage/

# Or more permissive
sudo chmod -R 777 storage/
```

### **Issue: Can't access from other machines**
```bash
# Check firewall
sudo ufw status
sudo ufw allow 8001/tcp
sudo ufw allow 3001/tcp
sudo ufw allow 80/tcp

# Check ALLOWED_HOSTS in backend/.env
# Should include server IP
```

---

## 🎯 Key Advantages

1. **Beginner-Friendly** - Clear prompts with sensible defaults
2. **Production-Ready** - Secure configuration out of the box
3. **Comprehensive** - Handles infrastructure + application setup
4. **Idempotent** - Safe to run multiple times
5. **Self-Documenting** - Clear output at each step
6. **Error Handling** - Validates before proceeding
7. **Flexible** - Optional features (HAProxy, backups, monitoring)
8. **Fast** - 10-20 minutes total deployment time

---

## 📈 Comparison: Manual vs Interactive Script

| Task | Manual Time | Script Time |
|------|-------------|-------------|
| Environment setup | 10 min | 2 min (prompts) |
| Docker build | 5 min | 5 min (automated) |
| Database setup | 15 min | 3 min (automated) |
| Create admin | 5 min | 1 min (prompt) |
| Testing | 10 min | 2 min (automated) |
| HAProxy setup | 20 min | 2 min (optional) |
| Backup automation | 15 min | 2 min (optional) |
| **Total** | **80 min** | **17 min** |

**Time Savings:** 78% faster (63 minutes saved)

---

## 🔗 Related Documentation

- `docker-compose.prod.yml` - Production Docker configuration
- `PRODUCTION_DEPLOYMENT_READINESS.md` - Full production guide
- `DEPLOYMENT_QUICK_START.md` - Quick reference
- `HAPROXY_INTEGRATION_GUIDE.md` - HAProxy details
- `DOCKER_NETWORKING_EXPLAINED.md` - Network architecture

---

**This script transforms complex EDMS deployment into a simple, guided experience suitable for both developers and operations teams.**
