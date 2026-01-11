# EDMS Production Deployment Package

**Package**: edms-production-20260106-170206  
**Created**: Tue Jan  6 05:02:06 PM +08 2026  
**Version**: 2.0

## 📦 Package Contents

This package contains everything needed to deploy EDMS in a production environment:

- ✅ Complete backend application (Django)
- ✅ Complete frontend application (React)
- ✅ Docker infrastructure files
- ✅ Production-ready configurations
- ✅ Interactive deployment script
- ✅ Comprehensive documentation

## 🚀 Quick Start

### Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+
- Linux server (Ubuntu 20.04+ or similar)
- Minimum 2GB RAM, 20GB disk space

### Deployment Steps

1. **Copy package to production server**
   ```bash
   scp -r edms-production-20260106-170206 user@server:/opt/
   ```

2. **SSH to server and navigate to package**
   ```bash
   ssh user@server
   cd /opt/edms-production-20260106-170206
   ```

3. **Run interactive deployment**
   ```bash
   chmod +x deploy-interactive.sh
   ./deploy-interactive.sh
   ```

4. **Follow the prompts** to configure:
   - Server IP address
   - Domain name (optional)
   - Database credentials
   - Django secret key
   - Admin credentials

5. **Access the application**
   - Default: http://your-server-ip

## 📋 Manual Deployment

If you prefer manual deployment:

```bash
# 1. Copy .env.example to .env
cp backend/.env.example backend/.env

# 2. Edit .env with your configuration
nano backend/.env

# 3. Build and start containers
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d

# 4. Run migrations
docker compose exec backend python manage.py migrate

# 5. Create superuser
docker compose exec backend python manage.py createsuperuser

# 6. Collect static files
docker compose exec backend python manage.py collectstatic --noinput
```

## 📚 Documentation

Detailed guides are available in the `docs/` directory:

- **DEPLOYMENT_QUICK_START.md** - Step-by-step deployment guide
- **PRODUCTION_DEPLOYMENT_READINESS.md** - Pre-deployment checklist
- **DOCKER_NETWORKING_EXPLAINED.md** - Network configuration guide
- **HAPROXY_INTEGRATION_GUIDE.md** - Load balancer setup

## 🔧 Configuration

### Environment Variables

Key configuration in `backend/.env`:

```bash
# Django
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=your-domain.com,your-ip

# Database
POSTGRES_DB=edms_production
POSTGRES_USER=edms
POSTGRES_PASSWORD=secure-password

# Application
SITE_URL=http://your-domain.com
```

### Docker Compose

- **docker-compose.yml** - Development configuration
- **docker-compose.prod.yml** - Production configuration (recommended)

## 🔍 Verification

After deployment, verify the system:

```bash
# Check container status
docker compose ps

# View logs
docker compose logs -f

# Test health endpoint
curl http://localhost:8000/health/

# Access admin interface
# http://your-server/admin/
```

## 🛠️ Maintenance

### Backup

```bash
./scripts/backup-system.sh
```

### Updates

```bash
# Pull latest images
docker compose pull

# Restart services
docker compose up -d
```

### Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f backend
```

## 📊 Package Statistics

- **Total Files**: 376
- **Backend Files**: 256
- **Frontend Files**: 99
- **Infrastructure Files**: 10
- **Scripts**: 3
- **Documentation**: 8
- **Package Size**: 6.7M

## 🆘 Support

For issues or questions:
1. Check the documentation in `docs/`
2. Review logs: `docker compose logs`
3. Consult PRODUCTION_DEPLOYMENT_READINESS.md

## 🔒 Security Notes

- Change default SECRET_KEY before deployment
- Use strong database passwords
- Configure firewall rules appropriately
- Keep Docker and system packages updated
- Regular backups are essential

## 📝 License

See LICENSE file for details.
