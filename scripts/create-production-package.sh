#!/bin/bash

################################################################################
# EDMS Production Deployment Package Creator
################################################################################
#
# Description: Creates a complete, verified deployment package for production
# Version: 2.0
# Date: December 24, 2024
#
# Features:
# - Creates minimal, production-ready deployment package
# - Verifies all required files are present
# - Generates detailed manifest
# - Creates checksums for verification
# - Excludes development files and sensitive data
#
# Usage: ./scripts/create-production-package.sh [output-dir]
#
################################################################################

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
OUTPUT_BASE="${1:-${REPO_ROOT}}"

# Package details
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
PACKAGE_NAME="edms-production-${TIMESTAMP}"
PACKAGE_DIR="${OUTPUT_BASE}/${PACKAGE_NAME}"
MANIFEST_FILE="${PACKAGE_DIR}/MANIFEST.txt"
CHECKSUM_FILE="${PACKAGE_DIR}/checksums.sha256"

# Statistics
declare -A FILE_COUNTS
TOTAL_SIZE=0
ERRORS=0

################################################################################
# Functions
################################################################################

print_header() {
    echo -e "${BLUE}╔═══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║                                                               ║${NC}"
    echo -e "${BLUE}║     EDMS Production Deployment Package Creator v2.0          ║${NC}"
    echo -e "${BLUE}║                                                               ║${NC}"
    echo -e "${BLUE}╚═══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

log_info() {
    echo -e "${CYAN}ℹ${NC} $1"
}

log_success() {
    echo -e "${GREEN}✓${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

log_error() {
    echo -e "${RED}✗${NC} $1"
    ERRORS=$((ERRORS + 1))
}

create_directory_structure() {
    log_info "Creating package directory structure..."
    
    # Main directories
    mkdir -p "${PACKAGE_DIR}"/{backend,frontend,infrastructure,scripts,docs}
    
    # Backend subdirectories
    mkdir -p "${PACKAGE_DIR}/backend"/{apps,edms,fixtures,requirements,database,storage,logs,media}
    
    # Frontend subdirectories
    mkdir -p "${PACKAGE_DIR}/frontend"/{src,public}
    
    # Infrastructure subdirectories
    mkdir -p "${PACKAGE_DIR}/infrastructure"/{containers,nginx}
    
    log_success "Directory structure created"
}

copy_backend_files() {
    log_info "Copying backend files..."
    
    cd "${REPO_ROOT}"
    
    # Core backend files
    if [ -f "backend/manage.py" ]; then
        cp backend/manage.py "${PACKAGE_DIR}/backend/"
        FILE_COUNTS[backend]=$((${FILE_COUNTS[backend]:-0} + 1))
    else
        log_error "Missing backend/manage.py"
    fi
    
    # Copy entire apps directory
    if [ -d "backend/apps" ]; then
        cp -r backend/apps/* "${PACKAGE_DIR}/backend/apps/"
        local count=$(find backend/apps -type f -name "*.py" | wc -l)
        FILE_COUNTS[backend]=$((${FILE_COUNTS[backend]:-0} + count))
        log_success "Copied ${count} Python files from apps"
    else
        log_error "Missing backend/apps directory"
    fi
    
    # Copy edms configuration
    if [ -d "backend/edms" ]; then
        cp -r backend/edms/* "${PACKAGE_DIR}/backend/edms/"
        local count=$(find backend/edms -type f | wc -l)
        FILE_COUNTS[backend]=$((${FILE_COUNTS[backend]:-0} + count))
    else
        log_error "Missing backend/edms directory"
    fi
    
    # Copy fixtures
    if [ -d "backend/fixtures" ]; then
        cp -r backend/fixtures/* "${PACKAGE_DIR}/backend/fixtures/" 2>/dev/null || true
        local count=$(find backend/fixtures -type f 2>/dev/null | wc -l)
        FILE_COUNTS[backend]=$((${FILE_COUNTS[backend]:-0} + count))
    fi
    
    # Copy requirements
    if [ -d "backend/requirements" ]; then
        cp -r backend/requirements/* "${PACKAGE_DIR}/backend/requirements/"
        local count=$(find backend/requirements -type f | wc -l)
        FILE_COUNTS[backend]=$((${FILE_COUNTS[backend]:-0} + count))
    else
        log_error "Missing backend/requirements directory"
    fi
    
    # Copy database directory structure
    if [ -d "backend/database" ]; then
        cp -r backend/database/*.py "${PACKAGE_DIR}/backend/database/" 2>/dev/null || true
        cp -r backend/database/__init__.py "${PACKAGE_DIR}/backend/database/" 2>/dev/null || true
    fi
    
    # Copy .env.example
    if [ -f "backend/.env.example" ]; then
        cp backend/.env.example "${PACKAGE_DIR}/backend/"
        FILE_COUNTS[backend]=$((${FILE_COUNTS[backend]:-0} + 1))
    else
        log_warning "Missing backend/.env.example"
    fi
    
    log_success "Backend files copied (${FILE_COUNTS[backend]:-0} files)"
}

copy_frontend_files() {
    log_info "Copying frontend files..."
    
    cd "${REPO_ROOT}"
    
    # Copy package files
    if [ -f "frontend/package.json" ]; then
        cp frontend/package.json "${PACKAGE_DIR}/frontend/"
        FILE_COUNTS[frontend]=$((${FILE_COUNTS[frontend]:-0} + 1))
    else
        log_error "Missing frontend/package.json"
    fi
    
    if [ -f "frontend/package-lock.json" ]; then
        cp frontend/package-lock.json "${PACKAGE_DIR}/frontend/"
        FILE_COUNTS[frontend]=$((${FILE_COUNTS[frontend]:-0} + 1))
    fi
    
    # Copy configuration files
    for file in tailwind.config.js nginx.conf; do
        if [ -f "frontend/${file}" ]; then
            cp "frontend/${file}" "${PACKAGE_DIR}/frontend/"
            FILE_COUNTS[frontend]=$((${FILE_COUNTS[frontend]:-0} + 1))
        fi
    done
    
    # Copy source files
    if [ -d "frontend/src" ]; then
        cp -r frontend/src/* "${PACKAGE_DIR}/frontend/src/"
        local count=$(find frontend/src -type f | wc -l)
        FILE_COUNTS[frontend]=$((${FILE_COUNTS[frontend]:-0} + count))
    else
        log_error "Missing frontend/src directory"
    fi
    
    # Copy public files
    if [ -d "frontend/public" ]; then
        cp -r frontend/public/* "${PACKAGE_DIR}/frontend/public/" 2>/dev/null || true
        local count=$(find frontend/public -type f 2>/dev/null | wc -l)
        FILE_COUNTS[frontend]=$((${FILE_COUNTS[frontend]:-0} + count))
    fi
    
    log_success "Frontend files copied (${FILE_COUNTS[frontend]:-0} files)"
}

copy_infrastructure_files() {
    log_info "Copying infrastructure files..."
    
    cd "${REPO_ROOT}"
    
    # Copy Dockerfiles
    if [ -d "infrastructure/containers" ]; then
        cp infrastructure/containers/Dockerfile.* "${PACKAGE_DIR}/infrastructure/containers/" 2>/dev/null || true
        local count=$(find infrastructure/containers -type f | wc -l)
        FILE_COUNTS[infrastructure]=$((${FILE_COUNTS[infrastructure]:-0} + count))
    else
        log_error "Missing infrastructure/containers directory"
    fi
    
    # Copy nginx configuration
    if [ -d "infrastructure/nginx" ]; then
        cp infrastructure/nginx/*.conf "${PACKAGE_DIR}/infrastructure/nginx/" 2>/dev/null || true
        local count=$(find infrastructure/nginx -type f | wc -l)
        FILE_COUNTS[infrastructure]=$((${FILE_COUNTS[infrastructure]:-0} + count))
    fi
    
    # Copy docker-compose files
    for file in docker-compose.yml docker-compose.prod.yml; do
        if [ -f "${file}" ]; then
            cp "${file}" "${PACKAGE_DIR}/"
            FILE_COUNTS[infrastructure]=$((${FILE_COUNTS[infrastructure]:-0} + 1))
        else
            log_error "Missing ${file}"
        fi
    done
    
    # Copy .dockerignore
    if [ -f ".dockerignore" ]; then
        cp .dockerignore "${PACKAGE_DIR}/"
        FILE_COUNTS[infrastructure]=$((${FILE_COUNTS[infrastructure]:-0} + 1))
    fi
    
    log_success "Infrastructure files copied (${FILE_COUNTS[infrastructure]:-0} files)"
}

copy_scripts() {
    log_info "Copying deployment scripts..."
    
    cd "${REPO_ROOT}"
    
    # Copy main deployment scripts
    for script in deploy-interactive.sh; do
        if [ -f "${script}" ]; then
            cp "${script}" "${PACKAGE_DIR}/"
            chmod +x "${PACKAGE_DIR}/${script}"
            FILE_COUNTS[scripts]=$((${FILE_COUNTS[scripts]:-0} + 1))
        else
            log_warning "Missing ${script}"
        fi
    done
    
    # Copy utility scripts
    if [ -d "scripts" ]; then
        for script in backup-system.sh deploy-production.sh; do
            if [ -f "scripts/${script}" ]; then
                cp "scripts/${script}" "${PACKAGE_DIR}/scripts/"
                chmod +x "${PACKAGE_DIR}/scripts/${script}"
                FILE_COUNTS[scripts]=$((${FILE_COUNTS[scripts]:-0} + 1))
            fi
        done
    fi
    
    log_success "Scripts copied (${FILE_COUNTS[scripts]:-0} files)"
}

copy_documentation() {
    log_info "Copying documentation..."
    
    cd "${REPO_ROOT}"
    
    # Copy root documentation
    for doc in README.md CHANGELOG.md LICENSE SECURITY.md; do
        if [ -f "${doc}" ]; then
            cp "${doc}" "${PACKAGE_DIR}/"
            FILE_COUNTS[docs]=$((${FILE_COUNTS[docs]:-0} + 1))
        fi
    done
    
    # Copy deployment docs
    for doc in PRODUCTION_DEPLOYMENT_READINESS.md DEPLOYMENT_QUICK_START.md \
               DOCKER_NETWORKING_EXPLAINED.md HAPROXY_INTEGRATION_GUIDE.md; do
        if [ -f "${doc}" ]; then
            cp "${doc}" "${PACKAGE_DIR}/docs/"
            FILE_COUNTS[docs]=$((${FILE_COUNTS[docs]:-0} + 1))
        fi
    done
    
    # Copy docs directory if exists
    if [ -d "docs/deployment" ]; then
        cp -r docs/deployment/*.md "${PACKAGE_DIR}/docs/" 2>/dev/null || true
    fi
    
    log_success "Documentation copied (${FILE_COUNTS[docs]:-0} files)"
}

create_gitignore() {
    log_info "Creating .gitignore..."
    
    cat > "${PACKAGE_DIR}/.gitignore" << 'EOF'
# Environment files
.env
.env.local
.env.production
*.env

# Python
__pycache__/
*.py[cod]
*.so
*.egg-info/
dist/
build/
*.sqlite3

# Node
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*
build/

# Docker
*.log

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Application data
backend/media/*
backend/storage/*
backend/logs/*
!backend/media/.gitkeep
!backend/storage/.gitkeep
!backend/logs/.gitkeep
EOF
    
    log_success ".gitignore created"
}

create_readme() {
    log_info "Creating README-DEPLOYMENT.md..."
    
    cat > "${PACKAGE_DIR}/README-DEPLOYMENT.md" << EOF
# EDMS Production Deployment Package

**Package**: ${PACKAGE_NAME}  
**Created**: $(date)  
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
   \`\`\`bash
   scp -r ${PACKAGE_NAME} user@server:/opt/
   \`\`\`

2. **SSH to server and navigate to package**
   \`\`\`bash
   ssh user@server
   cd /opt/${PACKAGE_NAME}
   \`\`\`

3. **Run interactive deployment**
   \`\`\`bash
   chmod +x deploy-interactive.sh
   ./deploy-interactive.sh
   \`\`\`

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

\`\`\`bash
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
\`\`\`

## 📚 Documentation

Detailed guides are available in the \`docs/\` directory:

- **DEPLOYMENT_QUICK_START.md** - Step-by-step deployment guide
- **PRODUCTION_DEPLOYMENT_READINESS.md** - Pre-deployment checklist
- **DOCKER_NETWORKING_EXPLAINED.md** - Network configuration guide
- **HAPROXY_INTEGRATION_GUIDE.md** - Load balancer setup

## 🔧 Configuration

### Environment Variables

Key configuration in \`backend/.env\`:

\`\`\`bash
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
\`\`\`

### Docker Compose

- **docker-compose.yml** - Development configuration
- **docker-compose.prod.yml** - Production configuration (recommended)

## 🔍 Verification

After deployment, verify the system:

\`\`\`bash
# Check container status
docker compose ps

# View logs
docker compose logs -f

# Test health endpoint
curl http://localhost:8000/health/

# Access admin interface
# http://your-server/admin/
\`\`\`

## 🛠️ Maintenance

### Backup

\`\`\`bash
./scripts/backup-system.sh
\`\`\`

### Updates

\`\`\`bash
# Pull latest images
docker compose pull

# Restart services
docker compose up -d
\`\`\`

### Logs

\`\`\`bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f backend
\`\`\`

## 📊 Package Statistics

$(generate_package_stats)

## 🆘 Support

For issues or questions:
1. Check the documentation in \`docs/\`
2. Review logs: \`docker compose logs\`
3. Consult PRODUCTION_DEPLOYMENT_READINESS.md

## 🔒 Security Notes

- Change default SECRET_KEY before deployment
- Use strong database passwords
- Configure firewall rules appropriately
- Keep Docker and system packages updated
- Regular backups are essential

## 📝 License

See LICENSE file for details.
EOF
    
    log_success "README-DEPLOYMENT.md created"
}

generate_package_stats() {
    local total_files=0
    for count in "${FILE_COUNTS[@]}"; do
        total_files=$((total_files + count))
    done
    
    local package_size=$(du -sh "${PACKAGE_DIR}" 2>/dev/null | cut -f1)
    
    cat << EOF
- **Total Files**: ${total_files}
- **Backend Files**: ${FILE_COUNTS[backend]:-0}
- **Frontend Files**: ${FILE_COUNTS[frontend]:-0}
- **Infrastructure Files**: ${FILE_COUNTS[infrastructure]:-0}
- **Scripts**: ${FILE_COUNTS[scripts]:-0}
- **Documentation**: ${FILE_COUNTS[docs]:-0}
- **Package Size**: ${package_size}
EOF
}

create_quick_deploy_script() {
    log_info "Creating quick-deploy.sh..."
    
    cat > "${PACKAGE_DIR}/quick-deploy.sh" << 'EOF'
#!/bin/bash

################################################################################
# EDMS Quick Deploy Script
################################################################################

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}Starting EDMS Quick Deployment...${NC}"
echo ""

# Check if deploy-interactive.sh exists
if [ ! -f "./deploy-interactive.sh" ]; then
    echo -e "${RED}Error: deploy-interactive.sh not found${NC}"
    echo "Please run this script from the deployment package directory"
    exit 1
fi

# Make executable
chmod +x deploy-interactive.sh

# Run deployment
./deploy-interactive.sh

echo ""
echo -e "${GREEN}Quick deployment completed!${NC}"
EOF
    
    chmod +x "${PACKAGE_DIR}/quick-deploy.sh"
    log_success "quick-deploy.sh created"
}

create_manifest() {
    log_info "Generating manifest..."
    
    local total_files=0
    for count in "${FILE_COUNTS[@]}"; do
        total_files=$((total_files + count))
    done
    
    local package_size=$(du -sh "${PACKAGE_DIR}" 2>/dev/null | cut -f1)
    
    cat > "${MANIFEST_FILE}" << EOF
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║     EDMS Production Deployment Package Manifest              ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝

Package Information
===================
Name:        ${PACKAGE_NAME}
Created:     $(date)
Creator:     create-production-package.sh v2.0
Size:        ${package_size}
Total Files: ${total_files}

File Breakdown
==============
Backend Files:        ${FILE_COUNTS[backend]:-0}
Frontend Files:       ${FILE_COUNTS[frontend]:-0}
Infrastructure Files: ${FILE_COUNTS[infrastructure]:-0}
Scripts:              ${FILE_COUNTS[scripts]:-0}
Documentation:        ${FILE_COUNTS[docs]:-0}

Package Structure
=================
${PACKAGE_NAME}/
├── backend/              # Django application
│   ├── apps/            # Application modules
│   ├── edms/            # Core configuration
│   ├── fixtures/        # Initial data
│   └── requirements/    # Python dependencies
├── frontend/            # React application
│   ├── src/            # Source code
│   └── public/         # Static assets
├── infrastructure/      # Docker setup
│   ├── containers/     # Dockerfiles
│   └── nginx/          # Web server config
├── scripts/            # Utility scripts
├── docs/               # Documentation
├── docker-compose.yml  # Development config
├── docker-compose.prod.yml  # Production config
├── deploy-interactive.sh    # Interactive setup
└── quick-deploy.sh     # Quick deployment

Deployment Instructions
=======================
1. Copy this package to your production server
2. Run: ./deploy-interactive.sh
3. Follow the interactive prompts
4. Access your application at the configured URL

Quick Deploy
============
For fastest deployment:
  ./quick-deploy.sh

Manual Deploy
=============
For manual configuration:
  1. cp backend/.env.example backend/.env
  2. Edit backend/.env with your settings
  3. docker compose -f docker-compose.prod.yml up -d

Documentation
=============
- README-DEPLOYMENT.md           # Main deployment guide
- docs/DEPLOYMENT_QUICK_START.md # Quick start guide
- docs/PRODUCTION_DEPLOYMENT_READINESS.md  # Checklist
- docs/DOCKER_NETWORKING_EXPLAINED.md      # Network setup
- docs/HAPROXY_INTEGRATION_GUIDE.md        # Load balancer

Verification
============
After deployment, verify with:
  docker compose ps                    # Check containers
  docker compose logs -f               # View logs
  curl http://localhost:8000/health/   # Test backend

Support
=======
For deployment issues, check:
  1. Container logs: docker compose logs
  2. Environment configuration: backend/.env
  3. Documentation in docs/ directory

Package Integrity
=================
Checksums generated: checksums.sha256
Verify with: sha256sum -c checksums.sha256

Errors During Creation
======================
Errors: ${ERRORS}
$([ ${ERRORS} -gt 0 ] && echo "⚠ Some files may be missing. Review the output above.")

Created by EDMS Production Package Creator v2.0
EOF
    
    log_success "Manifest generated: ${MANIFEST_FILE}"
}

create_checksums() {
    log_info "Generating checksums..."
    
    cd "${PACKAGE_DIR}"
    find . -type f ! -name "checksums.sha256" -exec sha256sum {} \; > "${CHECKSUM_FILE}"
    
    local checksum_count=$(wc -l < "${CHECKSUM_FILE}")
    log_success "Checksums generated for ${checksum_count} files"
}

verify_package() {
    log_info "Verifying package integrity..."
    
    local issues=0
    
    # Check critical files
    local critical_files=(
        "backend/manage.py"
        "backend/requirements/production.txt"
        "frontend/package.json"
        "docker-compose.prod.yml"
        "deploy-interactive.sh"
    )
    
    for file in "${critical_files[@]}"; do
        if [ ! -f "${PACKAGE_DIR}/${file}" ]; then
            log_error "Missing critical file: ${file}"
            issues=$((issues + 1))
        fi
    done
    
    # Check critical directories
    local critical_dirs=(
        "backend/apps"
        "backend/edms"
        "frontend/src"
        "infrastructure/containers"
    )
    
    for dir in "${critical_dirs[@]}"; do
        if [ ! -d "${PACKAGE_DIR}/${dir}" ]; then
            log_error "Missing critical directory: ${dir}"
            issues=$((issues + 1))
        fi
    done
    
    if [ ${issues} -eq 0 ]; then
        log_success "Package verification passed"
        return 0
    else
        log_error "Package verification failed with ${issues} issues"
        return 1
    fi
}

create_archive() {
    log_info "Creating compressed archive..."
    
    cd "${OUTPUT_BASE}"
    tar -czf "${PACKAGE_NAME}.tar.gz" "${PACKAGE_NAME}"
    
    local archive_size=$(du -sh "${PACKAGE_NAME}.tar.gz" 2>/dev/null | cut -f1)
    log_success "Archive created: ${PACKAGE_NAME}.tar.gz (${archive_size})"
}

print_summary() {
    echo ""
    echo -e "${GREEN}╔═══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                                                               ║${NC}"
    echo -e "${GREEN}║     Deployment Package Created Successfully                   ║${NC}"
    echo -e "${GREEN}║                                                               ║${NC}"
    echo -e "${GREEN}╚═══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    
    local total_files=0
    for count in "${FILE_COUNTS[@]}"; do
        total_files=$((total_files + count))
    done
    
    local package_size=$(du -sh "${PACKAGE_DIR}" 2>/dev/null | cut -f1)
    local archive_size=$(du -sh "${PACKAGE_NAME}.tar.gz" 2>/dev/null | cut -f1)
    
    echo -e "${CYAN}Package Details:${NC}"
    echo "  Name:          ${PACKAGE_NAME}"
    echo "  Location:      ${PACKAGE_DIR}"
    echo "  Archive:       ${PACKAGE_NAME}.tar.gz"
    echo "  Total Files:   ${total_files}"
    echo "  Package Size:  ${package_size}"
    echo "  Archive Size:  ${archive_size}"
    echo "  Errors:        ${ERRORS}"
    echo ""
    
    echo -e "${CYAN}File Breakdown:${NC}"
    echo "  Backend:        ${FILE_COUNTS[backend]:-0} files"
    echo "  Frontend:       ${FILE_COUNTS[frontend]:-0} files"
    echo "  Infrastructure: ${FILE_COUNTS[infrastructure]:-0} files"
    echo "  Scripts:        ${FILE_COUNTS[scripts]:-0} files"
    echo "  Documentation:  ${FILE_COUNTS[docs]:-0} files"
    echo ""
    
    echo -e "${CYAN}Next Steps:${NC}"
    echo "  1. Transfer to server:"
    echo "     ${YELLOW}scp ${PACKAGE_NAME}.tar.gz user@server:/opt/${NC}"
    echo ""
    echo "  2. Extract on server:"
    echo "     ${YELLOW}tar -xzf ${PACKAGE_NAME}.tar.gz${NC}"
    echo ""
    echo "  3. Deploy:"
    echo "     ${YELLOW}cd ${PACKAGE_NAME} && ./quick-deploy.sh${NC}"
    echo ""
    echo "  Or use the automated transfer script:"
    echo "     ${YELLOW}./scripts/deploy-to-remote.sh user@server:/opt/${NC}"
    echo ""
    
    if [ ${ERRORS} -gt 0 ]; then
        echo -e "${YELLOW}⚠ Warning: ${ERRORS} errors occurred during package creation${NC}"
        echo "  Review the output above for details"
        echo ""
    fi
}

################################################################################
# Main Execution
################################################################################

main() {
    cd "${REPO_ROOT}"
    
    print_header
    
    # Create package
    create_directory_structure
    copy_backend_files
    copy_frontend_files
    copy_infrastructure_files
    copy_scripts
    copy_documentation
    
    # Generate package files
    create_gitignore
    create_readme
    create_quick_deploy_script
    create_manifest
    create_checksums
    
    # Verify and package
    if verify_package; then
        create_archive
        print_summary
        exit 0
    else
        log_error "Package creation completed with errors"
        print_summary
        exit 1
    fi
}

# Run main function
main "$@"
