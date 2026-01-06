# Manual Cleanup and Redeployment Instructions

## Current Status
The staging server is running the WRONG containers (docker-compose.yml development containers).
According to commit 6ace8e5 and STAGING_DEPLOYMENT_SUCCESS_20260102.md, the correct configuration uses **docker-compose.prod.yml** (production containers).

---

## Manual Cleanup Instructions

### Step 1: SSH into Staging Server
```bash
ssh lims@172.28.1.148
```

### Step 2: Stop All Running Containers
```bash
cd ~/edms-staging

# Stop containers using current docker-compose.yml
docker compose down

# If that doesn't work, try:
docker compose -f docker-compose.yml down

# Remove all volumes (CAUTION: This will delete all data)
docker compose down -v

# Or manually stop and remove:
docker stop $(docker ps -a -q)
docker rm $(docker ps -a -q)
```

### Step 3: Clean Up Docker Images (Optional)
```bash
# List all images
docker images

# Remove EDMS-related images
docker rmi edms-staging-backend
docker rmi edms-staging-frontend
docker rmi edms-staging-celery_worker
docker rmi edms-staging-celery_beat

# Or remove all unused images
docker image prune -a
```

### Step 4: Clean Up Volumes (CAUTION: Deletes Data)
```bash
# List volumes
docker volume ls

# Remove specific volumes
docker volume rm edms-staging_postgres_data
docker volume rm edms-staging_redis_data
docker volume rm edms-staging_static_files
docker volume rm edms-staging_media_files

# Or remove all unused volumes
docker volume prune -f
```

### Step 5: Clean Up Networks
```bash
# List networks
docker network ls

# Remove EDMS network
docker network rm edms-staging_edms_network

# Or remove all unused networks
docker network prune -f
```

### Step 6: Clean Deployment Directory
```bash
cd ~/edms-staging

# Remove all deployment files
rm -rf backend frontend infrastructure scripts docs
rm -f docker-compose.yml docker-compose.prod.yml .env
rm -f deploy-interactive.sh *.md *.sh

# Verify directory is clean
ls -la
```

### Step 7: Preserve Backups (Important!)
```bash
# Your backups should be safe in:
ls -lh ~/edms-backups/

# If you want to keep monitoring scripts:
# They are at: ~/check_backup_health.sh, ~/backup_alert.sh, ~/backup_dashboard.sh
```

### Step 8: Remove Cron Jobs
```bash
# View current cron jobs
crontab -l

# Edit and remove backup-related cron jobs
crontab -e
# Delete the lines containing "backup-edms.sh" and "backup_alert.sh"

# Or remove all cron jobs
crontab -r
```

---

## Correct Deployment Configuration

Based on commit **6ace8e5** and **STAGING_DEPLOYMENT_SUCCESS_20260102.md**:

### Correct Docker Compose File
**Use**: `docker-compose.prod.yml`

### Correct Container Names
- `edms_prod_backend`
- `edms_prod_frontend`
- `edms_prod_db`
- `edms_prod_redis`
- `edms_prod_celery_worker`
- `edms_prod_celery_beat`

### Correct Ports
- Frontend: **3001** (not 3000)
- Backend: **8001** (not 8000)
- Database: **5433** (not 5432)

### Correct Database Credentials
- Database: `edms_prod_db`
- User: `edms_prod_user`
- Password: From `.env` file

---

## Redeployment Steps (After Cleanup)

### Step 1: Get Correct Code from Git
```bash
cd ~
# If you have git access:
git clone <repository-url> edms-staging
cd edms-staging
git checkout 6ace8e5

# Or copy the correct deployment package
```

### Step 2: Create .env File
```bash
cd ~/edms-staging
cat > .env << 'ENVFILE'
# Django Settings
DJANGO_ENV=production
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=172.28.1.148,localhost

# Database
DB_NAME=edms_prod_db
DB_USER=edms_prod_user
DB_PASSWORD=SecurePassword123!@#
POSTGRES_PORT=5433

# Redis
REDIS_PASSWORD=SecureRedisPassword123
REDIS_PORT=6380

# Backend/Frontend Ports
BACKEND_PORT=8001
FRONTEND_PORT=3001

# Celery
CELERY_BROKER_URL=redis://:SecureRedisPassword123@redis:6379/0
CELERY_RESULT_BACKEND=redis://:SecureRedisPassword123@redis:6379/0

# CORS
CORS_ALLOWED_ORIGINS=http://172.28.1.148:3001,http://localhost:3001

# Time Zone
DISPLAY_TIMEZONE=Asia/Singapore
ENVFILE
```

### Step 3: Build and Start Production Containers
```bash
cd ~/edms-staging

# Build production containers
docker compose -f docker-compose.prod.yml build

# Start containers
docker compose -f docker-compose.prod.yml up -d

# Wait for containers to start
sleep 30

# Check status
docker compose -f docker-compose.prod.yml ps
```

### Step 4: Initialize Database
```bash
cd ~/edms-staging

# Run migrations
docker compose -f docker-compose.prod.yml exec backend python manage.py migrate

# Initialize defaults
docker compose -f docker-compose.prod.yml exec backend python manage.py initialize_groups
docker compose -f docker-compose.prod.yml exec backend python manage.py initialize_roles
docker compose -f docker-compose.prod.yml exec backend python manage.py initialize_workflow_defaults
docker compose -f docker-compose.prod.yml exec backend python manage.py setup_scheduled_tasks

# Create admin user
docker compose -f docker-compose.prod.yml exec backend python manage.py shell << 'PYEOF'
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@edms-staging.local', 'AdminPassword123!@#')
    print('Admin created')
PYEOF
```

### Step 5: Configure Backup System
```bash
cd ~/edms-staging

# Update cron job for production containers
crontab -e

# Add this line:
0 2 * * * export POSTGRES_CONTAINER='edms_prod_db' POSTGRES_USER='edms_prod_user' POSTGRES_DB='edms_prod_db' && /home/lims/edms-staging/scripts/backup-edms.sh && find $HOME/edms-backups -maxdepth 1 -type d -name 'backup_*' -mtime +14 -exec rm -rf {} \; >> /home/lims/edms-backups/backup.log 2>&1
```

### Step 6: Verify Deployment
```bash
# Check containers
docker compose -f docker-compose.prod.yml ps

# Test frontend
curl http://172.28.1.148:3001/

# Test backend
curl http://172.28.1.148:8001/health/

# Test login
curl -X POST http://172.28.1.148:8001/api/v1/auth/token/ \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"AdminPassword123!@#"}'
```

---

## Verification Checklist

After redeployment, verify:

- [ ] Containers using `docker-compose.prod.yml`
- [ ] Container names start with `edms_prod_`
- [ ] Frontend accessible on port **3001**
- [ ] Backend accessible on port **8001**
- [ ] Login page shows **username in top-right** after login
- [ ] Dashboard accessible
- [ ] No console errors
- [ ] Documents page works
- [ ] Administration page accessible
- [ ] Backup cron job configured for production containers

---

## Access Information (After Correct Deployment)

- **Frontend**: http://172.28.1.148:3001
- **Backend**: http://172.28.1.148:8001
- **Admin Username**: admin
- **Admin Password**: AdminPassword123!@#

---

## Quick Reference Commands

### Check what's running:
```bash
docker ps
docker compose -f docker-compose.prod.yml ps
```

### View logs:
```bash
docker compose -f docker-compose.prod.yml logs backend
docker compose -f docker-compose.prod.yml logs frontend
```

### Restart services:
```bash
docker compose -f docker-compose.prod.yml restart backend frontend
```

### Complete cleanup:
```bash
docker compose down -v
docker system prune -a --volumes -f
```

---

## Important Notes

1. **Use `docker-compose.prod.yml`** - Not `docker-compose.yml`
2. **Port 3001 for frontend** - Not 3000
3. **Port 8001 for backend** - Not 8000
4. **Container names have `_prod_`** - e.g., `edms_prod_backend`
5. **Backup your data first** - Before running cleanup commands
6. **Preserve ~/edms-backups/** - Don't delete existing backups

