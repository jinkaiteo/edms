# Staging Server Shutdown and Redeployment Guide

## Safe Shutdown of Existing Deployment

Follow these steps to safely shut down the current deployment on the staging server before redeploying from GitHub.

### Step 1: Backup Critical Data

```bash
cd /home/lims/edms-production-20251229-092231

# 1. Backup the .env file (contains passwords and keys)
cp .env .env.backup.$(date +%Y%m%d-%H%M%S)

# 2. Backup database (if needed)
docker compose -f docker-compose.prod.yml exec db pg_dump -U edms_prod_user edms_prod_db > database_backup_$(date +%Y%m%d-%H%M%S).sql

# 3. Backup uploaded documents/storage (if any)
tar -czf storage_backup_$(date +%Y%m%d-%H%M%S).tar.gz storage/ 2>/dev/null || echo "No storage directory"

# 4. Save environment variables for reference
docker compose -f docker-compose.prod.yml exec backend env > environment_backup_$(date +%Y%m%d-%H%M%S).txt
```

### Step 2: Graceful Shutdown

```bash
cd /home/lims/edms-production-20251229-092231

# Stop all services gracefully
docker compose -f docker-compose.prod.yml down

# Verify all containers are stopped
docker compose -f docker-compose.prod.yml ps
```

### Step 3: Optional - Remove Volumes (Clean Slate)

⚠️ **WARNING: This will delete all data in the database!** Only do this if:
- You have a backup
- This is a fresh staging environment
- You want to start completely fresh

```bash
# DESTRUCTIVE: Remove all volumes and data
docker compose -f docker-compose.prod.yml down -v

# Or keep volumes but just stop containers (recommended)
docker compose -f docker-compose.prod.yml down
```

### Step 4: Archive Old Deployment

```bash
cd /home/lims

# Rename old deployment for backup
mv edms-production-20251229-092231 edms-production-20251229-092231.OLD.$(date +%Y%m%d-%H%M%S)

# Or if you want to remove it completely (not recommended until new deployment works)
# rm -rf edms-production-20251229-092231
```

---

## Complete Redeployment from GitHub

### Step 1: Clone Fresh Code

```bash
cd /home/lims

# Clone from GitHub (replace with your actual repo URL)
git clone -b develop https://github.com/your-org/edms.git edms-production-latest

# Or if you already have a local clone, update it
# cd edms-local-repo
# git pull origin develop
# cd /home/lims
# cp -r edms-local-repo edms-production-latest

cd edms-production-latest
```

### Step 2: Create Environment Configuration

```bash
# Copy from backup if you made one
cp /home/lims/edms-production-20251229-092231.OLD.*/env.backup.* .env

# OR create fresh .env file
cat > .env << 'EOF'
# Database Configuration
DB_NAME=edms_prod_db
DB_USER=edms_prod_user
DB_PASSWORD=your_secure_db_password_here

# Django Secret Key (50+ characters)
SECRET_KEY=your_django_secret_key_here

# Encryption Master Key (CRITICAL - must be same as before if restoring data)
EDMS_MASTER_KEY=Jq38TwbkHKSdNKhZV1l3RHOGHXjhfn22chlnVidkoVw=

# Redis Password
REDIS_PASSWORD=your_redis_password_here

# Network Configuration
ALLOWED_HOSTS=localhost,127.0.0.1,your-staging-ip-or-domain
CORS_ALLOWED_ORIGINS=http://localhost:3001,http://your-staging-ip:3001

# Optional: Email Configuration
# EMAIL_HOST=smtp.gmail.com
# EMAIL_PORT=587
# EMAIL_HOST_USER=your_email@gmail.com
# EMAIL_HOST_PASSWORD=your_app_password
EOF
```

### Step 3: Verify Configuration

```bash
# Check that docker-compose.prod.yml has EDMS_MASTER_KEY
grep -A 2 "EDMS_MASTER_KEY" docker-compose.prod.yml

# Should show:
#       - EDMS_MASTER_KEY=${EDMS_MASTER_KEY:-generate_a_secure_master_key_here}

# Verify .env has all required variables
cat .env | grep -E "^[A-Z_]+=" | sort
```

### Step 4: Deploy

```bash
cd /home/lims/edms-production-latest

# Build and start services
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d

# Watch logs as services start
docker compose -f docker-compose.prod.yml logs -f
# Press Ctrl+C to stop watching logs
```

### Step 5: Initialize Database (Fresh Deployment Only)

```bash
# Run database migrations
docker compose -f docker-compose.prod.yml exec backend python manage.py migrate

# Create superuser
docker compose -f docker-compose.prod.yml exec backend python manage.py createsuperuser

# Load initial data/fixtures if needed
docker compose -f docker-compose.prod.yml exec backend python manage.py loaddata fixtures/initial_users.json
```

### Step 6: Restore Data (If From Backup)

```bash
# If you backed up the database, restore it
cat /home/lims/edms-production-20251229-092231.OLD.*/database_backup_*.sql | \
  docker compose -f docker-compose.prod.yml exec -T db psql -U edms_prod_user edms_prod_db

# If you backed up storage, restore it
tar -xzf /home/lims/edms-production-20251229-092231.OLD.*/storage_backup_*.tar.gz
```

### Step 7: Verify Deployment

```bash
# Check all services are healthy
docker compose -f docker-compose.prod.yml ps

# Expected output:
# NAME                STATUS
# edms_prod_backend   Up (healthy)
# edms_prod_db        Up (healthy)
# edms_prod_redis     Up (healthy)

# Test backend health
curl http://localhost:8001/health/
# Should return: {"status": "healthy", ...}

# Verify EDMS_MASTER_KEY is loaded
docker compose -f docker-compose.prod.yml exec backend env | grep EDMS_MASTER_KEY
# Should show: EDMS_MASTER_KEY=Jq38Tw...

# Check backend logs for errors
docker compose -f docker-compose.prod.yml logs backend | tail -50
```

---

## Quick Reference Commands

```bash
# Check service status
docker compose -f docker-compose.prod.yml ps

# View logs
docker compose -f docker-compose.prod.yml logs backend
docker compose -f docker-compose.prod.yml logs -f  # Follow logs

# Restart a service
docker compose -f docker-compose.prod.yml restart backend

# Stop all services
docker compose -f docker-compose.prod.yml down

# Stop and remove volumes (data loss!)
docker compose -f docker-compose.prod.yml down -v

# Rebuild and restart
docker compose -f docker-compose.prod.yml build backend
docker compose -f docker-compose.prod.yml up -d backend

# Execute commands in container
docker compose -f docker-compose.prod.yml exec backend python manage.py migrate
docker compose -f docker-compose.prod.yml exec backend bash
docker compose -f docker-compose.prod.yml exec db psql -U edms_prod_user edms_prod_db
```

---

## Troubleshooting

### Backend Still Unhealthy After Redeployment

1. **Check environment variable is loaded:**
   ```bash
   docker compose -f docker-compose.prod.yml exec backend env | grep EDMS_MASTER_KEY
   ```
   If empty, check `.env` file and recreate container:
   ```bash
   docker compose -f docker-compose.prod.yml up -d --force-recreate backend
   ```

2. **Check logs for specific errors:**
   ```bash
   docker compose -f docker-compose.prod.yml logs backend | tail -100
   ```

3. **Verify database connection:**
   ```bash
   docker compose -f docker-compose.prod.yml exec backend python manage.py check --database default
   ```

### Port Already in Use

```bash
# Find what's using the port
sudo lsof -i :8001

# Stop old containers
docker ps -a | grep edms
docker stop <container-id>
docker rm <container-id>
```

### Permission Issues

```bash
cd /home/lims/edms-production-latest

# Fix storage permissions
sudo chown -R 1000:1000 storage/
sudo chmod -R 755 storage/

# Fix logs permissions
sudo chown -R 1000:1000 logs/
sudo chmod -R 755 logs/
```

---

## Rollback to Old Deployment

If the new deployment fails and you need to go back:

```bash
cd /home/lims

# Stop new deployment
cd edms-production-latest
docker compose -f docker-compose.prod.yml down

# Restore old deployment
cd /home/lims
mv edms-production-20251229-092231.OLD.* edms-production-20251229-092231
cd edms-production-20251229-092231

# Start old deployment
docker compose -f docker-compose.prod.yml up -d
```

---

## Clean Up After Successful Deployment

Once new deployment is verified working:

```bash
# Remove old deployment directory
rm -rf /home/lims/edms-production-20251229-092231.OLD.*

# Clean up old Docker images
docker image prune -a

# Clean up old volumes (if you created new ones)
docker volume prune
```
