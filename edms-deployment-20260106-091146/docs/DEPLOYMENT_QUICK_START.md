# EDMS Production Deployment - Quick Start Guide

**For Internal Network Deployment - HTTP Only**

---

## 📋 Pre-Deployment Checklist

Before you begin, gather this information:

- [ ] **Server Internal IP Address:** `_________________`
- [ ] **Server Hostname (optional):** `_________________`
- [ ] **Database Password (generate strong):** `_________________`
- [ ] **Admin User Email:** `_________________`

---

## 🚀 Step-by-Step Deployment (1-2 Days)

### Day 1: Configuration (2-3 hours)

#### Step 1: Prepare Environment File

```bash
# Navigate to backend directory
cd /path/to/edms/backend

# Copy the production environment template
cp .env.production .env

# Edit with your values
nano .env
```

#### Step 2: Update Required Values

Replace these placeholders in `.env`:

```bash
# Replace <YOUR-INTERNAL-IP> with server IP (e.g., 192.168.1.100 or 10.0.0.50)
ALLOWED_HOSTS=192.168.1.100,edms-server,localhost

# Replace <CHANGE-ME-USE-STRONG-PASSWORD> with strong password
# Generate with: openssl rand -base64 32
DB_PASSWORD=XyZ123AbC456DeF789...

# Replace frontend URLs
CORS_ALLOWED_ORIGINS=http://192.168.1.100:3000
CSRF_TRUSTED_ORIGINS=http://192.168.1.100:3000
```

#### Step 3: Verify Configuration

```bash
# Check .env file syntax
cat .env | grep -v "^#" | grep -v "^$"

# Ensure no <PLACEHOLDERS> remain
cat .env | grep "<YOUR"
# Should return nothing if all replaced
```

#### Step 4: Secure the File

```bash
# Set proper permissions
chmod 600 .env

# Verify it's not in git
git status .env
# Should show "nothing to commit" or not listed
```

---

### Day 2: Deployment (4-6 hours)

#### Step 1: Build Docker Images

```bash
# From project root
cd /path/to/edms

# Build production images
docker compose -f docker-compose.prod.yml build

# Expected time: 10-15 minutes
```

#### Step 2: Start Services

```bash
# Start all services
docker compose -f docker-compose.prod.yml up -d

# Verify all containers running
docker compose ps

# Expected output:
# backend    running
# frontend   running
# postgres   running
# redis      running
# celery     running
```

#### Step 3: Initialize Database

```bash
# Run migrations
docker compose exec backend python manage.py migrate

# Expected output: "Applying migrations... OK"

# Collect static files
docker compose exec backend python manage.py collectstatic --noinput

# Expected output: "X static files copied"
```

#### Step 4: Create Admin User

```bash
# Create superuser
docker compose exec backend python manage.py createsuperuser

# You'll be prompted for:
# - Username: admin (or your choice)
# - Email: admin@yourcompany.com
# - Password: (choose strong password)
```

#### Step 5: Verify Deployment

```bash
# Test backend health
curl http://YOUR-INTERNAL-IP:8000/health/

# Expected: {"status": "healthy"}

# Test frontend
curl http://YOUR-INTERNAL-IP:3000/

# Expected: HTML content

# Check logs
docker compose logs backend | tail -20
docker compose logs frontend | tail -20
```

---

## ✅ Day 2 Evening: Basic Testing

### Test 1: Login

1. Open browser: `http://YOUR-INTERNAL-IP:3000`
2. Login with superuser credentials
3. ✅ Should see dashboard

### Test 2: Upload Document

1. Click "Documents" → "Create Document"
2. Fill in details and upload a file
3. ✅ Document should appear in list

### Test 3: Workflow

1. Create a document
2. Click "Submit for Review"
3. ✅ Status should change to "Pending Review"

### Test 4: Notifications

1. Check notification bell (top right)
2. ✅ Should see in-app notifications

---

## 🛠️ Day 3: User Setup & UAT

### Morning: User Management

#### Clean Up Test Users

```bash
# List all users
docker compose exec backend python manage.py shell -c "
from apps.users.models import User
for u in User.objects.all():
    print(f'{u.username} - {u.email} - Superuser: {u.is_superuser}')
"

# Remove test users (if needed)
docker compose exec backend python manage.py shell -c "
from apps.users.models import User
User.objects.filter(username__in=['testuser', 'reviewer01', 'approver01']).delete()
"
```

#### Create Production Users

Use the web interface:
1. Login as admin
2. Go to "Administration" → "User Management"
3. Create users for your team:
   - Authors (can create documents)
   - Reviewers (can review documents)
   - Approvers (can approve documents)
   - Viewers (read-only)

### Afternoon: User Acceptance Testing

Have actual users test:
- [ ] Login/Logout
- [ ] Create document
- [ ] Upload files
- [ ] Submit for review
- [ ] Review process
- [ ] Approval process
- [ ] Search/filter documents
- [ ] View notifications

---

## 📊 Post-Deployment Monitoring

### Check Application Health

```bash
# View logs
docker compose logs -f backend

# Check resource usage
docker stats

# Verify backups working (when configured)
docker compose exec backend python manage.py create_backup
```

### Monitor for 24 Hours

- Check logs every few hours
- Monitor user feedback
- Note any errors or issues
- Document any questions

---

## 🔧 Common Issues & Solutions

### Issue 1: Cannot connect to server

**Solution:**
```bash
# Check firewall allows port 3000
sudo ufw status
sudo ufw allow 3000/tcp

# Check services running
docker compose ps
```

### Issue 2: Database connection error

**Solution:**
```bash
# Check database password in .env matches docker-compose.prod.yml
cat backend/.env | grep DB_PASSWORD
cat docker-compose.prod.yml | grep DB_PASSWORD

# Restart services
docker compose -f docker-compose.prod.yml restart
```

### Issue 3: 403 Forbidden or CSRF errors

**Solution:**
```bash
# Verify CORS settings in .env match frontend URL
cat backend/.env | grep CORS_ALLOWED_ORIGINS

# Should match: http://YOUR-IP:3000
# Restart backend if changed
docker compose restart backend
```

### Issue 4: Static files not loading

**Solution:**
```bash
# Re-collect static files
docker compose exec backend python manage.py collectstatic --noinput

# Restart frontend
docker compose restart frontend
```

---

## 📈 Next Steps (Week 2 - Optional)

### Performance Optimization

```bash
# Enable query logging to identify slow queries
# Add to .env:
# DB_LOG_QUERIES=True

# Monitor performance
docker stats --no-stream
```

### Backup Automation

```bash
# Add to crontab:
0 2 * * * cd /path/to/edms && docker compose exec -T backend python manage.py create_backup >> /var/log/edms/backup.log 2>&1
```

### User Training

- Create user guide document
- Schedule training sessions
- Set up support channel (Slack, Teams, etc.)

### Plan Phase 2 Enhancements

- Email notifications (if needed)
- HTTPS setup (if external access needed)
- Additional features based on user feedback

---

## 📞 Support

### Logs Location

- Backend logs: `docker compose logs backend`
- Frontend logs: `docker compose logs frontend`
- Database logs: `docker compose logs postgres`

### Health Checks

- Backend: `http://YOUR-IP:8000/health/`
- Frontend: `http://YOUR-IP:3000/`
- Admin Panel: `http://YOUR-IP:8000/admin/`

### Useful Commands

```bash
# Restart all services
docker compose -f docker-compose.prod.yml restart

# View real-time logs
docker compose logs -f

# Database backup
docker compose exec backend python manage.py create_backup

# Check disk space
df -h
```

---

## ✅ Deployment Complete!

Once you complete Day 3 UAT successfully:

- [ ] System is live and operational
- [ ] Users can access and use the system
- [ ] Admin has access to all controls
- [ ] Basic workflows tested and working
- [ ] Monitoring in place

**Congratulations! Your EDMS is now in production!** 🎉

---

**Quick Reference:**

- **Frontend:** `http://YOUR-IP:3000`
- **Backend API:** `http://YOUR-IP:8000/api/`
- **Admin Panel:** `http://YOUR-IP:8000/admin/`
- **Health Check:** `http://YOUR-IP:8000/health/`

**Support:** Refer to `PRODUCTION_DEPLOYMENT_READINESS.md` for detailed information.
