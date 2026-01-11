# EDMS Deployment Package

This is a minimal deployment package containing only the files needed to deploy EDMS to production.

## Package Contents

```
edms-deployment/
├── backend/                   # Django backend application
│   ├── apps/                  # All Django apps
│   ├── edms/                  # Django project settings
│   ├── requirements/          # Python dependencies
│   ├── fixtures/              # Initial data
│   ├── .env.production        # Environment template
│   └── manage.py             # Django management
├── frontend/                  # React frontend application
│   ├── src/                   # React source code
│   ├── public/               # Static files
│   └── package.json          # Node dependencies
├── infrastructure/           # Docker and infrastructure
│   ├── containers/           # Dockerfiles
│   └── nginx/               # Nginx configs
├── docs/                     # Documentation
│   ├── PRODUCTION_DEPLOYMENT_READINESS.md
│   ├── DEPLOYMENT_QUICK_START.md
│   ├── DOCKER_NETWORKING_EXPLAINED.md
│   └── HAPROXY_INTEGRATION_GUIDE.md
├── docker-compose.prod.yml   # Production Docker config
├── deploy-interactive.sh     # Interactive deployment script
└── README-DEPLOYMENT.md      # This file
```

## Quick Start

### 1. Copy Package to Server

```bash
# On your local machine
scp -r edms-deployment-YYYYMMDD-HHMMSS/ user@server:/opt/

# On the server
cd /opt/edms-deployment-YYYYMMDD-HHMMSS/
```

### 2. Run Interactive Deployment

```bash
chmod +x deploy-interactive.sh
./deploy-interactive.sh
```

The script will guide you through:
- Environment configuration
- Docker deployment
- Database initialization
- Admin user creation
- HAProxy setup (optional)

### 3. Access Your Application

After deployment completes, access at:
- Frontend: http://YOUR-SERVER-IP:3001 (or port 80 with HAProxy)
- Admin: http://YOUR-SERVER-IP:8001/admin/

## Manual Deployment

If you prefer manual deployment, see:
- `docs/DEPLOYMENT_QUICK_START.md` - Step-by-step guide
- `docs/PRODUCTION_DEPLOYMENT_READINESS.md` - Complete production guide

## Requirements

- Docker 20.10+
- Docker Compose 2.0+
- 10GB+ available disk space
- 4GB+ RAM recommended

## Support

Refer to documentation in the `docs/` directory for detailed guides on:
- Production deployment
- Docker networking
- HAProxy integration
- Troubleshooting

## Package Information

- Created: $(date)
- Version: 1.0
- Deployment Type: Internal Network (HTTP, No Email)
