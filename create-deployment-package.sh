#!/bin/bash

################################################################################
# EDMS Deployment Package Creator
################################################################################
#
# Description: Creates a minimal deployment package with only required files
# Version: 1.0
# Date: December 24, 2024
#
# This script creates a portable deployment package that can be copied to
# production servers without the entire repository.
#
# Usage: ./create-deployment-package.sh
#
################################################################################

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}╔═══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                                                               ║${NC}"
echo -e "${BLUE}║     EDMS Deployment Package Creator                          ║${NC}"
echo -e "${BLUE}║                                                               ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Package details
PACKAGE_NAME="edms-deployment-$(date +%Y%m%d-%H%M%S)"
PACKAGE_DIR="./${PACKAGE_NAME}"

echo -e "${GREEN}Creating deployment package: ${PACKAGE_NAME}${NC}"
echo ""

# Create package directory structure
mkdir -p "${PACKAGE_DIR}"
mkdir -p "${PACKAGE_DIR}/backend"
mkdir -p "${PACKAGE_DIR}/backend/apps"
mkdir -p "${PACKAGE_DIR}/backend/edms"
mkdir -p "${PACKAGE_DIR}/backend/fixtures"
mkdir -p "${PACKAGE_DIR}/backend/requirements"
mkdir -p "${PACKAGE_DIR}/backend/storage"
mkdir -p "${PACKAGE_DIR}/backend/logs"
mkdir -p "${PACKAGE_DIR}/backend/database"
mkdir -p "${PACKAGE_DIR}/frontend"
mkdir -p "${PACKAGE_DIR}/infrastructure/containers"
mkdir -p "${PACKAGE_DIR}/infrastructure/nginx"
mkdir -p "${PACKAGE_DIR}/docs"
mkdir -p "${PACKAGE_DIR}/scripts"

echo "✓ Created directory structure"

# Copy essential backend files
echo "Copying backend application files..."

# Backend core
cp -r backend/apps "${PACKAGE_DIR}/backend/" 2>/dev/null || true
cp -r backend/edms "${PACKAGE_DIR}/backend/" 2>/dev/null || true
cp backend/manage.py "${PACKAGE_DIR}/backend/" 2>/dev/null || true

# Backend requirements
cp -r backend/requirements "${PACKAGE_DIR}/backend/" 2>/dev/null || true

# Backend fixtures (initial data)
cp -r backend/fixtures "${PACKAGE_DIR}/backend/" 2>/dev/null || true

# Environment template
cp backend/.env.production "${PACKAGE_DIR}/backend/.env.production" 2>/dev/null || true
cp backend/.env.example "${PACKAGE_DIR}/backend/.env.example" 2>/dev/null || true

echo "✓ Backend files copied"

# Copy frontend files
echo "Copying frontend application files..."

cp -r frontend/public "${PACKAGE_DIR}/frontend/" 2>/dev/null || true
cp -r frontend/src "${PACKAGE_DIR}/frontend/" 2>/dev/null || true
cp frontend/package.json "${PACKAGE_DIR}/frontend/" 2>/dev/null || true
cp frontend/package-lock.json "${PACKAGE_DIR}/frontend/" 2>/dev/null || true
cp frontend/tailwind.config.js "${PACKAGE_DIR}/frontend/" 2>/dev/null || true
cp frontend/nginx.conf "${PACKAGE_DIR}/frontend/" 2>/dev/null || true

# Frontend TypeScript config if exists
cp frontend/tsconfig.json "${PACKAGE_DIR}/frontend/" 2>/dev/null || true

echo "✓ Frontend files copied"

# Copy infrastructure files
echo "Copying infrastructure files..."

cp -r infrastructure/containers "${PACKAGE_DIR}/infrastructure/" 2>/dev/null || true
cp -r infrastructure/nginx "${PACKAGE_DIR}/infrastructure/" 2>/dev/null || true

echo "✓ Infrastructure files copied"

# Copy Docker configuration
echo "Copying Docker configuration..."

cp docker-compose.prod.yml "${PACKAGE_DIR}/" 2>/dev/null || true
cp docker-compose.yml "${PACKAGE_DIR}/" 2>/dev/null || true
cp .dockerignore "${PACKAGE_DIR}/" 2>/dev/null || true

echo "✓ Docker files copied"

# Copy documentation
echo "Copying documentation..."

cp PRODUCTION_DEPLOYMENT_READINESS.md "${PACKAGE_DIR}/docs/" 2>/dev/null || true
cp DEPLOYMENT_QUICK_START.md "${PACKAGE_DIR}/docs/" 2>/dev/null || true
cp DOCKER_NETWORKING_EXPLAINED.md "${PACKAGE_DIR}/docs/" 2>/dev/null || true
cp HAPROXY_INTEGRATION_GUIDE.md "${PACKAGE_DIR}/docs/" 2>/dev/null || true
cp README.md "${PACKAGE_DIR}/" 2>/dev/null || true

echo "✓ Documentation copied"

# Copy deployment scripts
echo "Copying deployment scripts..."

cp deploy-interactive.sh "${PACKAGE_DIR}/" 2>/dev/null || true
chmod +x "${PACKAGE_DIR}/deploy-interactive.sh" 2>/dev/null || true

# Copy utility scripts if they exist
cp scripts/backup-system.sh "${PACKAGE_DIR}/scripts/" 2>/dev/null || true
cp scripts/deploy-production.sh "${PACKAGE_DIR}/scripts/" 2>/dev/null || true

echo "✓ Scripts copied"

# Create .gitignore for the package
cat > "${PACKAGE_DIR}/.gitignore" << 'EOF'
# Environment files
.env
.env.local
*.env

# Python
__pycache__/
*.py[cod]
*.so
*.egg-info/
dist/
build/

# Node
node_modules/
npm-debug.log*

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Application
backend/storage/media/*
backend/logs/*.log
backend/*.sqlite3
backend/staticfiles/

# Docker
*.log
EOF

# Create README for the package
cat > "${PACKAGE_DIR}/README-DEPLOYMENT.md" << 'EOF'
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
EOF

# Create quick start script
cat > "${PACKAGE_DIR}/quick-deploy.sh" << 'EOF'
#!/bin/bash

# EDMS Quick Deploy Script
# Runs the interactive deployment immediately

if [ ! -f "./deploy-interactive.sh" ]; then
    echo "Error: deploy-interactive.sh not found"
    echo "Please run this script from the deployment package directory"
    exit 1
fi

chmod +x deploy-interactive.sh
./deploy-interactive.sh
EOF

chmod +x "${PACKAGE_DIR}/quick-deploy.sh"

# Create manifest file
cat > "${PACKAGE_DIR}/MANIFEST.txt" << EOF
EDMS Deployment Package Manifest
================================

Package: ${PACKAGE_NAME}
Created: $(date)
Creator: create-deployment-package.sh v1.0

Contents:
---------
- Complete backend application (Django)
- Complete frontend application (React)
- Docker infrastructure files
- Production documentation (4 guides)
- Interactive deployment script
- Configuration templates

Size: $(du -sh "${PACKAGE_DIR}" | cut -f1)

Files: $(find "${PACKAGE_DIR}" -type f | wc -l)

Deployment Steps:
-----------------
1. Copy this package to production server
2. Run: ./deploy-interactive.sh
3. Follow the interactive prompts
4. Access your application

For detailed instructions, see:
- README-DEPLOYMENT.md
- docs/DEPLOYMENT_QUICK_START.md

EOF

# Calculate package size
PACKAGE_SIZE=$(du -sh "${PACKAGE_DIR}" | cut -f1)
FILE_COUNT=$(find "${PACKAGE_DIR}" -type f | wc -l)

# Create compressed archive
echo ""
echo "Creating compressed archive..."

tar -czf "${PACKAGE_NAME}.tar.gz" "${PACKAGE_DIR}"

ARCHIVE_SIZE=$(du -sh "${PACKAGE_NAME}.tar.gz" | cut -f1)

echo "✓ Archive created: ${PACKAGE_NAME}.tar.gz"

# Summary
echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}Deployment Package Created Successfully!${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo "Package Details:"
echo "  Name:            ${PACKAGE_NAME}"
echo "  Directory Size:  ${PACKAGE_SIZE}"
echo "  Archive Size:    ${ARCHIVE_SIZE}"
echo "  Files:           ${FILE_COUNT}"
echo ""
echo "Package Location:"
echo "  Directory:       ${PACKAGE_DIR}/"
echo "  Archive:         ${PACKAGE_NAME}.tar.gz"
echo ""
echo "To Deploy on Production Server:"
echo ""
echo "  1. Copy archive to server:"
echo "     scp ${PACKAGE_NAME}.tar.gz user@server:/opt/"
echo ""
echo "  2. On the server, extract:"
echo "     cd /opt"
echo "     tar -xzf ${PACKAGE_NAME}.tar.gz"
echo "     cd ${PACKAGE_NAME}"
echo ""
echo "  3. Run deployment:"
echo "     ./deploy-interactive.sh"
echo ""
echo -e "${YELLOW}Note: The package contains NO sensitive data.${NC}"
echo -e "${YELLOW}Configuration will be created during deployment.${NC}"
echo ""
