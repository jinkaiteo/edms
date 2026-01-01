# EDMS Staging Server - Complete Deployment Documentation

## 🎯 Overview

This document details the complete deployment process for the EDMS staging server, including all fixes and configurations required for a fully functional system.

---

## 📋 Deployment Timeline (January 1, 2026)

### **Issues Encountered and Fixed:**

1. ✅ **Storage Permission Issues**
   - Problem: Permission denied on `/app/storage/documents` and `/app/storage/media`
   - Solution: Set 777 permissions on storage directories

2. ✅ **HAProxy Port Conflicts**
   - Problem: Nginx container trying to bind port 80 while HAProxy is running
   - Solution: Removed port 80:80 binding from nginx container in docker-compose

3. ✅ **Session ID Database Constraints**
   - Problem: `session_id` columns didn't allow NULL in `document_access_logs` and `audit_trail`
   - Solution: Added `null=True` to models and created migrations

4. ✅ **Role Permission Configuration**
   - Problem: Roles didn't have correct `module` and `permission_level` values
   - Solution: Roles already configured with O1/write for Document Author

5. ✅ **User Role Assignment**
   - Problem: author01 didn't have Document Author role assigned
   - Solution: Created UserRole assignment linking user to role

---

## 🏗️ Final Architecture

```
Internet (port 80)
    ↓
HAProxy (systemd service on host)
    ↓
    ├─ Frontend Container (localhost:3001)
    │  └─ React App served by nginx
    │
    └─ Backend Container (localhost:8001)
       └─ Django + Gunicorn

Docker Containers:
- frontend (nginx serving React build)
- backend (Django + Gunicorn)
- db (PostgreSQL)
- redis (Redis)
- celery_worker
- celery_beat
- nginx (no port binding, HAProxy handles routing)
```

---

## 📦 System Configuration

### **Storage Structure:**
```
storage/
├── documents/          # 777 permissions
├── media/             # 777 permissions
│   └── certificates/
├── backups/           # 755 permissions
└── temp/              # 777 permissions

logs/
├── backend/
├── db/
├── redis/
└── nginx/
```

### **Database Tables Fixed:**
- `document_access_logs.session_id` → NULL allowed
- `audit_trail.session_id` → NULL allowed

### **Role Configuration:**
```
Document Admin:     O1/admin
Document Author:    O1/write  (required for document creation)
Document Reviewer:  O1/review
Document Approver:  O1/approve
Document Viewer:    O1/read
User Admin:         S1/admin
Placeholder Admin:  S6/admin
```

### **Test Users:**
```
admin:      superuser, password: test123
author01:   Document Author role, password: test123
reviewer01: Document Reviewer role, password: test123
approver01: Document Approver role, password: test123
```

---

## 🔧 Manual Deployment Steps (Reference)

### **Phase 1: Initial Setup**

```bash
cd /home/lims/edms-staging

# 1. Pull latest code
git pull origin develop

# 2. Create environment file
bash scripts/setup-staging-env.sh 172.28.1.148

# 3. Configure for HAProxy
bash scripts/configure-for-haproxy.sh

# 4. Setup HAProxy on host
sudo bash scripts/setup-haproxy-staging.sh

# 5. Fix storage permissions
sudo bash scripts/fix-storage-permissions.sh
```

### **Phase 2: Deploy Application**

```bash
# 6. Stop existing containers
docker compose -f docker-compose.prod.yml down

# 7. Build and start containers
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d

# Wait for services
sleep 30
```

### **Phase 3: Database Setup**

```bash
# 8. Run migrations (includes session_id fixes)
docker compose -f docker-compose.prod.yml exec backend python manage.py migrate

# 9. Initialize system defaults
docker compose -f docker-compose.prod.yml exec backend python manage.py create_default_roles
docker compose -f docker-compose.prod.yml exec backend python manage.py create_default_groups
docker compose -f docker-compose.prod.yml exec backend python manage.py create_default_document_types
docker compose -f docker-compose.prod.yml exec backend python manage.py create_default_document_sources
```

### **Phase 4: User Setup**

```bash
# 10. Create admin user
docker compose -f docker-compose.prod.yml exec backend python manage.py shell << 'PYTHON'
from apps.users.models import User
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser(
        username='admin',
        email='admin@edms-project.com',
        password='test123',
        first_name='System',
        last_name='Administrator'
    )
PYTHON

# 11. Create test users (author01, reviewer01, approver01)
# Run deploy-staging-complete.sh user creation section

# 12. Assign roles to users
bash scripts/assign-author-role.sh
```

### **Phase 5: Verification**

```bash
# 13. Verify services are running
docker compose -f docker-compose.prod.yml ps

# 14. Check backend health
curl http://localhost:8001/health/

# 15. Check HAProxy
sudo systemctl status haproxy

# 16. Test frontend
curl http://172.28.1.148/
```

---

## 🚨 Critical Fixes Applied

### **1. Storage Permissions Fix**

**Script:** `scripts/fix-storage-permissions.sh`

Sets 777 permissions on:
- `storage/documents` - For direct file writes by serializer
- `storage/media` - For Django default_storage
- `storage/temp` - For temporary processing

**Why 777?**
- Docker container runs as specific UID
- Needs write access to create subdirectories dynamically
- Safe for development/staging environments

### **2. Session ID Null Constraint Fix**

**Migrations:**
- `documents/migrations/0008_alter_documentaccesslog_session_id.py`
- `audit/migrations/0008_alter_audittrail_session_id.py`

**Problem:**
- REST API token authentication doesn't create Django sessions
- `request.session.session_key` returns `None`
- Audit logging tried to save `NULL` to NOT NULL columns

**Solution:**
- Added `null=True` to both `session_id` fields
- Allows audit logging for API requests

### **3. Role Permission Configuration**

**Requirement:**
Document creation permission check requires:
```python
user.user_roles.filter(
    role__module='O1',  # Document Management module
    role__permission_level__in=['write', 'admin'],
    is_active=True
).exists()
```

**Configuration:**
- Document Author: `module='O1'`, `permission_level='write'`
- Must be assigned via UserRole junction table

### **4. HAProxy Configuration**

**Changes to docker-compose.prod.yml:**
```yaml
nginx:
  ports: []  # Removed "80:80" and "443:443"
```

**Why:**
- HAProxy runs on host port 80
- Routes traffic to containers on localhost:3001 and localhost:8001
- Nginx container doesn't need external port binding

---

## 📊 Deployment Time Breakdown

| Phase | Duration | Description |
|-------|----------|-------------|
| Setup | 2 min | Environment, HAProxy config, storage |
| Build | 4-5 min | Docker image builds |
| Deploy | 30 sec | Container startup |
| Migrations | 30 sec | Database schema updates |
| Initialization | 2 min | Roles, groups, types, sources |
| User Setup | 1 min | Admin and test user creation |
| **Total** | **~10 min** | **Complete deployment** |

---

## 🧪 Verification Checklist

### **Infrastructure:**
- [ ] HAProxy running: `sudo systemctl status haproxy`
- [ ] All containers running: `docker compose -f docker-compose.prod.yml ps`
- [ ] Backend healthy: `curl http://localhost:8001/health/`
- [ ] Frontend accessible: `curl http://172.28.1.148/`

### **Database:**
- [ ] Migrations applied: Check for `0008_alter_*_session_id` in both `documents` and `audit`
- [ ] Roles exist: 7 roles in database
- [ ] Groups exist: 6 Django groups
- [ ] Document types exist: 6 types (POL, SOP, WI, MAN, FRM, REC)
- [ ] Document sources exist: 3 sources

### **Permissions:**
- [ ] Storage permissions: `ls -la storage/` shows 777 on documents/media
- [ ] author01 has Document Author role
- [ ] Document Author role has module='O1', permission_level='write'

### **Functionality:**
- [ ] Can login with admin/test123
- [ ] Can login with author01/test123
- [ ] Can create document with file upload as author01
- [ ] Document appears in library
- [ ] File is saved to storage/documents/

---

## 🔄 Redeployment Process

For subsequent deployments (code updates):

```bash
cd /home/lims/edms-staging

# 1. Pull latest code
git pull origin develop

# 2. Rebuild if code changed
docker compose -f docker-compose.prod.yml build backend frontend

# 3. Restart services
docker compose -f docker-compose.prod.yml up -d

# 4. Run new migrations (if any)
docker compose -f docker-compose.prod.yml exec backend python manage.py migrate

# 5. Verify health
curl http://localhost:8001/health/
```

**No need to:**
- Recreate HAProxy configuration (persistent)
- Reset storage permissions (persistent)
- Reinitialize system defaults (preserved in database)
- Recreate users (preserved in database)

---

## 🆘 Troubleshooting Guide

### **Issue: Permission denied on file upload**

**Check:**
```bash
ls -ld storage/documents storage/media
# Should show: drwxrwxrwx (777)
```

**Fix:**
```bash
sudo bash scripts/fix-storage-permissions.sh
```

### **Issue: 403 Insufficient permissions to create documents**

**Check:**
```bash
docker compose -f docker-compose.prod.yml exec backend python manage.py shell << 'PYTHON'
from apps.users.models import User
author = User.objects.get(username='author01')
has_perm = author.user_roles.filter(
    role__module='O1',
    role__permission_level__in=['write', 'admin'],
    is_active=True
).exists()
print(f"Has permission: {has_perm}")
PYTHON
```

**Fix:**
```bash
bash scripts/assign-author-role.sh
```

### **Issue: 500 Internal Server Error**

**Check backend logs:**
```bash
docker compose -f docker-compose.prod.yml logs backend --tail=100
```

**Common causes:**
1. Session ID constraint → Run migrations
2. File permission → Check storage/documents permissions
3. Missing field → Check backend error for specifics

### **Issue: HAProxy port 80 conflict**

**Check:**
```bash
sudo lsof -i :80
```

**Fix:**
```bash
# Stop conflicting service
sudo systemctl stop nginx  # if standalone nginx is running

# Or configure docker-compose
bash scripts/configure-for-haproxy.sh
```

---

## 📚 Related Scripts

All scripts are in `scripts/` directory:

| Script | Purpose |
|--------|---------|
| `setup-staging-env.sh` | Creates .env.prod with server IP |
| `configure-for-haproxy.sh` | Removes nginx port 80 binding |
| `setup-haproxy-staging.sh` | Installs and configures HAProxy |
| `fix-storage-permissions.sh` | Sets 777 on storage directories |
| `deploy-staging-complete.sh` | Complete automated deployment |
| `assign-author-role.sh` | Assigns Document Author role to author01 |
| `update-role-permissions.sh` | Updates role module/permission_level (not needed if fresh deploy) |

---

## 🎯 Key Learnings

### **Docker File Permissions:**
- Container processes need write access to mounted volumes
- 777 is acceptable for staging; production should use proper UID/GID
- Both `storage/documents` (direct writes) and `storage/media` (Django storage) need write access

### **Django Session Management:**
- REST API token authentication != session-based authentication
- Session ID fields must allow NULL for API requests
- Affects audit logging tables

### **Role-Based Permissions:**
- EDMS uses custom Role model with module codes
- Permission checks look for specific module/permission_level combinations
- Users linked to roles via UserRole junction table
- Must be `is_active=True` to take effect

### **HAProxy vs Docker Networking:**
- HAProxy runs on host, not in Docker
- Containers don't need to expose port 80 when using HAProxy
- HAProxy routes to container ports via localhost

---

## ✅ Success Criteria

A successful deployment is confirmed when:

1. ✅ All 7 Docker containers running
2. ✅ HAProxy active and routing traffic
3. ✅ Frontend accessible at http://172.28.1.148
4. ✅ Backend health check returns 200 OK
5. ✅ Can login with author01/test123
6. ✅ Can create document with file upload
7. ✅ Document appears in library with file attached
8. ✅ File exists in storage/documents/ directory

---

## 📝 Environment Variables

**Required in `.env.prod`:**
```env
DJANGO_SETTINGS_MODULE=edms.settings.production
SECRET_KEY=<random-key>
DEBUG=False
ALLOWED_HOSTS=172.28.1.148,localhost

DB_NAME=edms_prod_db
DB_USER=edms_prod_user
DB_PASSWORD=<password>
DB_HOST=db
DB_PORT=5432

REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/0

CORS_ALLOWED_ORIGINS=http://172.28.1.148,http://172.28.1.148:3001
CSRF_TRUSTED_ORIGINS=http://172.28.1.148,http://172.28.1.148:3001

MEDIA_ROOT=/app/storage/media
```

---

## 🔐 Security Notes

### **For Production:**

1. **Change default passwords:**
   ```bash
   docker compose exec backend python manage.py changepassword admin
   ```

2. **Use proper storage permissions:**
   - Run container with specific UID
   - Use 755 permissions with correct ownership
   - Not 777

3. **Enable HTTPS:**
   - Configure SSL certificates in HAProxy
   - Update CSRF_COOKIE_SECURE and SESSION_COOKIE_SECURE to True

4. **Secure environment variables:**
   - Use secrets management
   - Don't commit .env.prod to git
   - Rotate SECRET_KEY regularly

---

## 📞 Support

For issues or questions:
1. Check backend logs: `docker compose -f docker-compose.prod.yml logs backend`
2. Review this documentation
3. Check related markdown files in repository root
4. Verify all prerequisites are met

---

**Last Updated:** January 1, 2026  
**Tested On:** Ubuntu 20.04, Docker Compose v2.x  
**EDMS Version:** 2.0 (Staging)
