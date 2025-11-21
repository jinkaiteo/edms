# Simplified Internal Deployment Guide

## Overview

This guide provides a simplified deployment approach for internal use behind a firewall, removing Nginx complexity and using Django to serve both API and frontend directly.

## Architecture Comparison

### ❌ Original Complex Architecture
```
Internet → Firewall → Nginx (Port 80) → Django API (Port 8000)
                                      → React Static Files
                                      → Media Files
```

### ✅ Simplified Internal Architecture
```
Internal Network → Django + Gunicorn (Port 8000) → Serves API + React + Media
```

## Benefits of Simplified Approach

### 🎯 **For Internal Deployment**
- **Single Port**: Only expose port 8000
- **Simpler Firewall Rules**: One port instead of multiple
- **Easier Monitoring**: Single service to watch
- **Reduced Complexity**: No reverse proxy configuration
- **Faster Deployment**: Fewer moving parts
- **Easier Troubleshooting**: Single service to debug

### 🔧 **Technical Benefits**
- Django's `whitenoise` handles static files efficiently
- Gunicorn provides production-grade WSGI server
- React build served directly from Django
- Single container or process to manage

## Implementation Changes

### 1. Django Configuration

#### settings/production.py
```python
import os
from .base import *

# Serve static files with whitenoise
MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')

# Static files configuration
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# React build files
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'frontend/build/static'),
]

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# React app template
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, 'frontend/build'),
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# Allowed hosts for internal network
ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    '0.0.0.0',
    '10.*',  # Internal network range
    '192.168.*',  # Private network range
    'your-internal-server.local',  # Your internal hostname
]

# Security settings for internal use
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# Internal deployment optimizations
DEBUG = False
ALLOWED_HOSTS = ['*']  # For internal use only
```

#### Main URLs Configuration
```python
# edms/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # API endpoints
    path('api/v1/', include('apps.api.urls')),
    path('api/auth/', include('apps.authentication.urls')),
    
    # Health check
    path('health/', include('apps.monitoring.urls')),
    
    # React app (catch-all)
    path('', TemplateView.as_view(template_name='index.html')),
]

# Serve media files in development/internal use
if settings.DEBUG or settings.INTERNAL_DEPLOYMENT:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Catch-all for React Router
urlpatterns += [
    path('<path:path>', TemplateView.as_view(template_name='index.html')),
]
```

### 2. Container Configuration

#### Simplified Dockerfile
```dockerfile
# Multi-stage build
FROM node:18-alpine AS frontend-build
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci --only=production
COPY frontend/ .
RUN npm run build

FROM python:3.11-slim AS backend
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements/ requirements/
RUN pip install --no-cache-dir -r requirements/production.txt

# Copy backend code
COPY backend/ .

# Copy frontend build
COPY --from=frontend-build /app/frontend/build ./frontend/build

# Collect static files
RUN python manage.py collectstatic --noinput

# Create non-root user
RUN groupadd -r edms && useradd -r -g edms edms
RUN chown -R edms:edms /app
USER edms

# Expose port
EXPOSE 8000

# Start command
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "edms.wsgi:application"]
```

#### Simplified docker-compose.yml with Isolated Network
```yaml
version: '3.8'

services:
  db:
    image: postgres:16
    container_name: edms_db
    environment:
      POSTGRES_DB: edms_db
      POSTGRES_USER: edms_user
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - edms_postgres_data:/var/lib/postgresql/data
    networks:
      - edms_network
    # No external ports exposed - internal communication only
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U edms_user -d edms_db"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: edms_redis
    networks:
      - edms_network
    # No external ports exposed - internal communication only
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 3

  web:
    build: .
    container_name: edms_web
    environment:
      - DEBUG=False
      - DATABASE_URL=postgresql://edms_user:${DB_PASSWORD}@db:5432/edms_db
      - REDIS_URL=redis://redis:6379/0
      - INTERNAL_DEPLOYMENT=True
    volumes:
      - edms_media_volume:/app/media
      - edms_static_volume:/app/staticfiles
      - edms_logs:/app/logs
    ports:
      - "${EDMS_PORT:-8000}:8000"  # Only port exposed to host
    networks:
      - edms_network
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health/"]
      interval: 30s
      timeout: 10s
      retries: 3

  worker:
    build: .
    container_name: edms_worker
    command: celery -A edms worker -l info --concurrency=2
    environment:
      - DATABASE_URL=postgresql://edms_user:${DB_PASSWORD}@db:5432/edms_db
      - REDIS_URL=redis://redis:6379/0
    volumes:
      - edms_media_volume:/app/media
      - edms_logs:/app/logs
    networks:
      - edms_network
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "celery -A edms inspect ping"]
      interval: 60s
      timeout: 10s
      retries: 3

  scheduler:
    build: .
    container_name: edms_scheduler
    command: celery -A edms beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
    environment:
      - DATABASE_URL=postgresql://edms_user:${DB_PASSWORD}@db:5432/edms_db
      - REDIS_URL=redis://redis:6379/0
    volumes:
      - edms_logs:/app/logs
    networks:
      - edms_network
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped

# Dedicated network for EDMS - complete isolation
networks:
  edms_network:
    name: edms_network
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
          gateway: 172.20.0.1

# Prefixed volumes to avoid conflicts
volumes:
  edms_postgres_data:
    name: edms_postgres_data
  edms_media_volume:
    name: edms_media_volume
  edms_static_volume:
    name: edms_static_volume
  edms_logs:
    name: edms_logs
```

### 3. Deployment Script

#### deploy-internal.sh
```bash
#!/bin/bash

set -e

echo "🚀 Starting EDMS Internal Deployment..."

# Configuration
EDMS_PORT=${EDMS_PORT:-8000}
EDMS_ENV=${EDMS_ENV:-production}
DB_PASSWORD=${DB_PASSWORD:-$(openssl rand -base64 32)}

# Create environment file
cat > .env << EOF
DB_PASSWORD=${DB_PASSWORD}
SECRET_KEY=$(openssl rand -base64 50)
EDMS_PORT=${EDMS_PORT}
ENVIRONMENT=${EDMS_ENV}
INTERNAL_DEPLOYMENT=true
EOF

# Build and start services
echo "📦 Building containers..."
docker-compose build --no-cache

echo "🗄️ Starting database..."
docker-compose up -d db redis

echo "⏳ Waiting for database..."
sleep 10

echo "🔧 Running migrations..."
docker-compose run --rm web python manage.py migrate

echo "👤 Creating superuser..."
docker-compose run --rm web python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@internal.local', 'admin123')
    print('Superuser created: admin/admin123')
"

echo "📚 Collecting static files..."
docker-compose run --rm web python manage.py collectstatic --noinput

echo "🚀 Starting EDMS application..."
docker-compose up -d

echo "✅ EDMS deployed successfully!"
echo ""
echo "🔗 Access EDMS at: http://localhost:${EDMS_PORT}"
echo "👤 Admin login: admin / admin123"
echo "📊 Health check: http://localhost:${EDMS_PORT}/health/"
echo ""
echo "🔧 Management commands:"
echo "  docker-compose logs web     # View application logs"
echo "  docker-compose exec web python manage.py shell  # Django shell"
echo "  docker-compose down        # Stop all services"
```

## Network Isolation & Multi-App Deployment

### 🔒 Complete Container Isolation

The EDMS deployment uses a **dedicated Docker network** to ensure complete isolation from other applications on your server:

#### Network Architecture
```
Host Server
├── edms_network (172.20.0.0/16) - ISOLATED
│   ├── edms_db (172.20.0.2)
│   ├── edms_redis (172.20.0.3)
│   ├── edms_web (172.20.0.4)
│   ├── edms_worker (172.20.0.5)
│   └── edms_scheduler (172.20.0.6)
├── app2_network (172.21.0.0/16) - ISOLATED
└── app3_network (172.22.0.0/16) - ISOLATED
```

#### Key Isolation Benefits
- ✅ **No port conflicts** - Database/Redis not exposed to host
- ✅ **No name conflicts** - All containers prefixed with `edms_`
- ✅ **No volume conflicts** - All volumes prefixed with `edms_`
- ✅ **Separate IP space** - Uses 172.20.0.0/16 subnet
- ✅ **Internal communication** - Containers talk via service names

### 🌐 Multi-Application Port Strategy

#### Recommended Port Allocation
```bash
# Main applications
EDMS:           Port 8000
App2 (CRM):     Port 8001  
App3 (ERP):     Port 8002
Monitoring:     Port 3000
Database Admin: Port 8080

# Internal services (not exposed)
PostgreSQL:     5432 (internal only)
Redis:          6379 (internal only)
```

#### Environment Variables for Port Management
```bash
# .env file for each app
EDMS_PORT=8000
CRM_PORT=8001
ERP_PORT=8002
```

### 🔧 Multi-App Docker Compose Management

#### Directory Structure
```
/opt/applications/
├── edms/
│   ├── docker-compose.yml
│   ├── .env
│   └── ...
├── crm/
│   ├── docker-compose.yml
│   ├── .env
│   └── ...
└── erp/
    ├── docker-compose.yml
    ├── .env
    └── ...
```

#### Management Script for Multiple Apps
```bash
#!/bin/bash
# /opt/scripts/app-manager.sh

APPS_DIR="/opt/applications"
APPS=("edms" "crm" "erp")

case "$1" in
    start)
        for app in "${APPS[@]}"; do
            echo "Starting $app..."
            cd "$APPS_DIR/$app"
            docker-compose up -d
        done
        ;;
    stop)
        for app in "${APPS[@]}"; do
            echo "Stopping $app..."
            cd "$APPS_DIR/$app"
            docker-compose down
        done
        ;;
    status)
        for app in "${APPS[@]}"; do
            echo "=== $app Status ==="
            cd "$APPS_DIR/$app"
            docker-compose ps
        done
        ;;
    logs)
        if [ -n "$2" ]; then
            cd "$APPS_DIR/$2"
            docker-compose logs -f
        else
            echo "Usage: $0 logs <app_name>"
        fi
        ;;
esac
```

### 🛡️ Firewall Configuration

#### Simple Firewall Rules
```bash
# Only expose necessary ports
sudo ufw allow 8000/tcp  # EDMS
sudo ufw allow 8001/tcp  # CRM
sudo ufw allow 8002/tcp  # ERP
sudo ufw allow 3000/tcp  # Monitoring

# Or for specific IP ranges
sudo ufw allow from 10.0.0.0/8 to any port 8000
sudo ufw allow from 192.168.0.0/16 to any port 8000

# Block database ports (they should be internal only)
sudo ufw deny 5432/tcp
sudo ufw deny 6379/tcp
```

#### Network Security Check Script
```bash
#!/bin/bash
# security-check.sh

echo "🔍 Checking exposed ports..."
netstat -tlnp | grep -E ':(5432|6379|3306|27017)'

echo "🔍 Checking Docker networks..."
docker network ls | grep -E '(edms|crm|erp)'

echo "🔍 Checking running containers..."
docker ps --format "table {{.Names}}\t{{.Ports}}\t{{.Networks}}"
```

## Monitoring and Health Checks

### Simple Health Check Endpoint
```python
# apps/monitoring/views.py
from django.http import JsonResponse
from django.db import connection
import redis
from django.conf import settings

def health_check(request):
    """Simple health check for internal deployment"""
    status = {
        'status': 'healthy',
        'database': 'unknown',
        'redis': 'unknown',
        'version': '1.0.0'
    }
    
    try:
        # Check database
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        status['database'] = 'healthy'
    except:
        status['database'] = 'unhealthy'
        status['status'] = 'unhealthy'
    
    try:
        # Check Redis
        r = redis.from_url(settings.REDIS_URL)
        r.ping()
        status['redis'] = 'healthy'
    except:
        status['redis'] = 'unhealthy'
        status['status'] = 'unhealthy'
    
    return JsonResponse(status)
```

## Performance Considerations

### Whitenoise Configuration
```python
# Optimized static file serving
WHITENOISE_USE_FINDERS = True
WHITENOISE_AUTOREFRESH = True
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
```

### Gunicorn Optimization
```bash
# For internal deployment
gunicorn --workers 3 --worker-class gevent --worker-connections 1000 --bind 0.0.0.0:8000 edms.wsgi:application
```

## Maintenance Commands

### Backup
```bash
# Simple backup script
docker-compose exec db pg_dump -U edms_user edms_db > backup_$(date +%Y%m%d_%H%M%S).sql
```

### Updates
```bash
# Update EDMS deployment safely
cd /opt/applications/edms
git pull origin main
docker-compose build --no-cache
docker-compose down
docker-compose up -d
```

### Logs and Monitoring
```bash
# View logs for specific services
docker-compose logs -f web
docker-compose logs -f worker
docker-compose logs -f scheduler

# Monitor all EDMS containers
docker stats edms_web edms_worker edms_db edms_redis

# Check network connectivity
docker network inspect edms_network
```

### Container Resource Management
```bash
# Check EDMS resource usage
docker-compose exec web htop
docker-compose exec web df -h

# Cleanup old images and containers
docker system prune --volumes -f
docker image prune -f
```

## Security for Internal Use

Since this is internal deployment behind firewall:

### Relaxed Security Settings
```python
# Internal deployment security
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False  
CSRF_COOKIE_SECURE = False
SECURE_HSTS_SECONDS = 0

# But keep essential security
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
```

### File Upload Security
```python
# Still validate file uploads
FILE_UPLOAD_MAX_MEMORY_SIZE = 100 * 1024 * 1024  # 100MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 100 * 1024 * 1024
ALLOWED_UPLOAD_EXTENSIONS = ['.pdf', '.docx', '.xlsx', '.txt']
```

## Summary

This simplified approach:
- ✅ **Removes Nginx complexity**
- ✅ **Single port (8000) exposure**  
- ✅ **Django serves everything**
- ✅ **Perfect for internal deployment**
- ✅ **Easier to maintain and deploy**
- ✅ **Still production-ready with Gunicorn**

The deployment becomes as simple as:
```bash
git clone https://github.com/jinkaiteo/edms.git
cd edms
bash scripts/deploy-internal.sh
```

Access your EDMS at: `http://your-internal-server:8000`