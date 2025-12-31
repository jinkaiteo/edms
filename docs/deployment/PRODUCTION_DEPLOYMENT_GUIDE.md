# 🚀 EDMS Production Deployment Guide

## Overview
This guide provides step-by-step instructions for deploying the standardized EDMS workflow system to a production Docker environment.

## 🛠️ Prerequisites

### System Requirements
- Docker 20.10+ installed and running
- Docker Compose v2.0+ or docker-compose 1.29+
- Minimum 4GB RAM, 20GB disk space
- Ubuntu 20.04+ or equivalent Linux distribution

### Network Requirements
- Ports 80, 443 (if using SSL), 3001, 8001, 5433, 6380 available
- Internet connectivity for pulling base images

## 🔧 Pre-Deployment Setup

### 1. Clone Repository and Navigate
```bash
git clone <repository-url>
cd edms
```

### 2. Create Production Environment File
```bash
cp .env.production .env.prod
```

### 3. Configure Production Environment
Edit `.env.prod` with your production values:

```bash
# Critical settings to customize
DB_PASSWORD=your_very_secure_database_password_123!
REDIS_PASSWORD=your_very_secure_redis_password_456!
SECRET_KEY=your_django_secret_key_must_be_50_chars_minimum_789!

# Encryption Master Key (REQUIRED for document encryption/backup)
# Generate with: python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
EDMS_MASTER_KEY=your_generated_master_key_here

# Domain settings
ALLOWED_HOSTS=localhost,127.0.0.1,your-production-domain.com
CORS_ALLOWED_ORIGINS=https://your-production-domain.com

# Email settings (optional but recommended)
EMAIL_HOST=smtp.your-email-provider.com
EMAIL_HOST_USER=noreply@your-domain.com
EMAIL_HOST_PASSWORD=your-email-password
```

**⚠️ CRITICAL: EDMS_MASTER_KEY**
- This key is **required** for the encryption service and backup/restore system
- Generate it once and store it securely - never regenerate after initial deployment
- Without this key, you cannot decrypt encrypted documents or restore backups
- Use a password manager or secure secrets vault to store this key

### 4. Create Required Directories
```bash
mkdir -p logs/{db,redis,nginx}
mkdir -p storage/{media,documents}
mkdir -p backups
```

## 🚀 Deployment Process

### Option 1: Automated Deployment (Recommended)
```bash
# Run the automated deployment script
./scripts/deploy-production.sh
```

### Option 2: Manual Deployment
```bash
# Build images
docker build -f infrastructure/containers/Dockerfile.backend.prod --target production -t edms-backend:production ./backend
docker build -f infrastructure/containers/Dockerfile.frontend.prod --target production -t edms-frontend:production ./frontend

# Deploy services
docker-compose -f docker-compose.prod.yml --env-file .env.prod up -d

# Wait for services to start
sleep 60

# Run health checks
curl http://localhost:8001/health/
curl http://localhost:3001/health
```

## 🧪 Testing Production Deployment

### Automated Testing
```bash
# Run comprehensive production tests
./scripts/test-production-workflow.sh
```

### Manual Testing

#### 1. Service Health Checks
```bash
# Backend health
curl http://localhost:8001/health/

# Frontend health  
curl http://localhost:3001/health

# Database connectivity
docker-compose -f docker-compose.prod.yml exec db pg_isready -U edms_prod_user
```

#### 2. Authentication Test
```bash
# Test login endpoint
curl -X POST http://localhost:8001/api/v1/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "author", "password": "AuthorPass2024!"}'
```

#### 3. Workflow System Test
```bash
# Get authentication token
TOKEN=$(curl -s -X POST http://localhost:8001/api/v1/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "author", "password": "AuthorPass2024!"}' | \
  python3 -c "import sys, json; print(json.load(sys.stdin)['access'])")

# Test workflow endpoints
curl -H "Authorization: Bearer $TOKEN" http://localhost:8001/api/v1/workflows/my-tasks/
```

## 📊 Service URLs

| Service | URL | Description |
|---------|-----|-------------|
| **Frontend** | http://localhost:3001 | Main application interface |
| **Backend API** | http://localhost:8001 | REST API and admin |
| **API Documentation** | http://localhost:8001/api/docs/ | Swagger API docs |
| **Database** | localhost:5433 | PostgreSQL database |
| **Redis** | localhost:6380 | Cache and message broker |

## 🔐 Default Credentials

### Test Users (Change in Production)
| Username | Password | Role |
|----------|----------|------|
| `admin` | `admin123` | System Administrator |
| `author` | `AuthorPass2024!` | Document Author |
| `reviewer` | `ReviewPass2024!` | Document Reviewer |
| `approver` | `ApprovePass2024!` | Document Approver |
| `docadmin` | `EDMSAdmin2024!` | Document Administrator |

⚠️ **Security Notice**: Change all default passwords immediately in production!

## 🏥 Health Monitoring

### Service Status
```bash
# Check all services
docker-compose -f docker-compose.prod.yml ps

# View service logs
docker-compose -f docker-compose.prod.yml logs -f backend
docker-compose -f docker-compose.prod.yml logs -f frontend
```

### Performance Monitoring
```bash
# Container resource usage
docker stats

# Database performance
docker-compose -f docker-compose.prod.yml exec db \
  psql -U edms_prod_user -d edms_prod_db -c "SELECT * FROM pg_stat_activity;"
```

## 🔧 Management Commands

### Start/Stop Services
```bash
# Start all services
docker-compose -f docker-compose.prod.yml up -d

# Stop all services
docker-compose -f docker-compose.prod.yml down

# Restart specific service
docker-compose -f docker-compose.prod.yml restart backend
```

### Database Operations
```bash
# Django shell access
docker-compose -f docker-compose.prod.yml exec backend python manage.py shell

# Run migrations
docker-compose -f docker-compose.prod.yml exec backend python manage.py migrate

# Create superuser
docker-compose -f docker-compose.prod.yml exec backend python manage.py createsuperuser
```

### Backup Operations
```bash
# Database backup
docker-compose -f docker-compose.prod.yml exec db \
  pg_dump -U edms_prod_user edms_prod_db > backup_$(date +%Y%m%d).sql

# Storage backup
tar -czf storage_backup_$(date +%Y%m%d).tar.gz storage/
```

## 🚨 Troubleshooting

### Common Issues

#### 1. Services Not Starting
```bash
# Check logs for errors
docker-compose -f docker-compose.prod.yml logs backend
docker-compose -f docker-compose.prod.yml logs db

# Verify environment file
cat .env.prod | grep -E "PASSWORD|SECRET_KEY"
```

#### 2. Database Connection Issues
```bash
# Test database connectivity
docker-compose -f docker-compose.prod.yml exec db \
  psql -U edms_prod_user -d edms_prod_db -c "SELECT 1;"

# Reset database if needed
docker-compose -f docker-compose.prod.yml down -v
docker-compose -f docker-compose.prod.yml up -d db
```

#### 3. Frontend Not Loading
```bash
# Check nginx logs
docker-compose -f docker-compose.prod.yml logs nginx

# Verify frontend build
docker-compose -f docker-compose.prod.yml exec frontend ls -la /usr/share/nginx/html/
```

#### 4. Workflow Operations Failing
```bash
# Check backend logs
docker-compose -f docker-compose.prod.yml logs backend | grep -i error

# Test workflow service directly
docker-compose -f docker-compose.prod.yml exec backend python manage.py shell -c "
from apps.workflows.services import get_simple_workflow_service
service = get_simple_workflow_service()
print('Workflow service loaded successfully')
"
```

## 📋 Post-Deployment Checklist

### ✅ Security Checklist
- [ ] Changed all default passwords
- [ ] Configured proper ALLOWED_HOSTS
- [ ] Set up CORS origins correctly
- [ ] Configured secure SECRET_KEY
- [ ] Set up SSL certificates (if applicable)
- [ ] Configured firewall rules
- [ ] Set up backup procedures

### ✅ Functionality Checklist
- [ ] User authentication working
- [ ] Document creation/upload working
- [ ] Workflow state transitions working
- [ ] Email notifications working (if configured)
- [ ] Audit trail logging functional
- [ ] Frontend-backend communication working

### ✅ Monitoring Checklist
- [ ] Health check endpoints responding
- [ ] Log files being created
- [ ] Database performance acceptable
- [ ] Redis cache working
- [ ] Backup procedures tested

## 🆘 Support

### Logs Location
- Backend: `logs/gunicorn_*.log`, `logs/edms.log`
- Database: `logs/db/postgresql-*.log`
- Nginx: `logs/nginx/access.log`, `logs/nginx/error.log`
- Redis: `logs/redis/`

### Key Files
- **Configuration**: `.env.prod`
- **Compose**: `docker-compose.prod.yml`
- **Deployment Script**: `scripts/deploy-production.sh`
- **Test Script**: `scripts/test-production-workflow.sh`

---

## 🎯 Next Steps

After successful deployment:

1. **Configure SSL/HTTPS** for production security
2. **Set up automated backups** with cron jobs
3. **Configure monitoring** with log aggregation
4. **Set up CI/CD pipelines** for updates
5. **Train users** on the new workflow system

**The standardized workflow system is now ready for production use!** 🎉