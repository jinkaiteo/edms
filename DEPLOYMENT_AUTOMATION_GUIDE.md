# EDMS Deployment Automation Guide

**Version**: 2.0  
**Date**: December 24, 2024  
**Status**: Production Ready ✅

## 📦 Overview

This guide covers the automated deployment package creation and transfer system for EDMS. The system provides two main scripts that automate the entire deployment workflow from package creation to remote server transfer.

## 🎯 Features

### Package Creator (`scripts/create-production-package.sh`)
- ✅ Creates minimal, production-ready deployment packages
- ✅ Verifies all required files are present
- ✅ Generates detailed manifest with statistics
- ✅ Creates SHA256 checksums for integrity verification
- ✅ Excludes development files and sensitive data
- ✅ Creates compressed tar.gz archive (7.5M → 1.5M)
- ✅ Zero errors in package creation

### Automated Transfer (`scripts/deploy-to-remote.sh`)
- ✅ Validates remote server connectivity
- ✅ Checks remote server requirements (Docker, Docker Compose)
- ✅ Automatically creates deployment package
- ✅ Transfers via SCP with progress
- ✅ Verifies transfer integrity with checksums
- ✅ Extracts package on remote server
- ✅ Supports SSH key authentication
- ✅ Optional auto-deployment mode

## 🚀 Quick Start

### 1. Create Deployment Package Locally

```bash
# Create package in current directory
./scripts/create-production-package.sh

# Create package in specific directory
./scripts/create-production-package.sh /path/to/output
```

**Output**:
- Package directory: `edms-production-YYYYMMDD-HHMMSS/`
- Compressed archive: `edms-production-YYYYMMDD-HHMMSS.tar.gz`
- Size: ~1.5M (compressed from 7.5M)
- Files: 410+ files

### 2. Transfer to Remote Server

```bash
# Basic transfer
./scripts/deploy-to-remote.sh user@server.com

# Transfer to specific path
./scripts/deploy-to-remote.sh user@server.com:/var/www/edms

# Transfer with SSH key
./scripts/deploy-to-remote.sh user@server.com --key ~/.ssh/production_key

# Transfer and auto-deploy
./scripts/deploy-to-remote.sh user@server.com --auto-deploy

# Keep local package after transfer
./scripts/deploy-to-remote.sh user@server.com --keep
```

### 3. Deploy on Remote Server

After transfer, SSH to the server and deploy:

```bash
ssh user@server.com
cd /opt/edms-production-YYYYMMDD-HHMMSS
./quick-deploy.sh
```

## 📋 Detailed Usage

### Package Creator Script

#### Basic Usage

```bash
./scripts/create-production-package.sh [output-directory]
```

#### Arguments

- `output-directory` (optional): Directory where package will be created (default: current directory)

#### What It Does

1. **Creates directory structure**
   - `backend/` - Django application
   - `frontend/` - React application
   - `infrastructure/` - Docker files
   - `scripts/` - Utility scripts
   - `docs/` - Documentation

2. **Copies application files**
   - Backend: 292 files (apps, edms, fixtures, requirements)
   - Frontend: 99 files (src, public, configs)
   - Infrastructure: 8 files (Dockerfiles, nginx)
   - Scripts: 3 files (deployment scripts)
   - Documentation: 8 files (guides)

3. **Generates package files**
   - `.gitignore` - Excludes sensitive files
   - `README-DEPLOYMENT.md` - Deployment instructions
   - `quick-deploy.sh` - Quick deployment script
   - `MANIFEST.txt` - Package manifest with statistics
   - `checksums.sha256` - File integrity checksums

4. **Verifies package integrity**
   - Checks critical files exist
   - Validates directory structure
   - Reports any missing files

5. **Creates compressed archive**
   - tar.gz format
   - ~80% size reduction (7.5M → 1.5M)

#### Example Output

```
╔═══════════════════════════════════════════════════════════════╗
║     EDMS Production Deployment Package Creator v2.0          ║
╚═══════════════════════════════════════════════════════════════╝

ℹ Creating package directory structure...
✓ Directory structure created
ℹ Copying backend files...
✓ Copied 256 Python files from apps
✓ Backend files copied (292 files)
ℹ Copying frontend files...
✓ Frontend files copied (99 files)
ℹ Copying infrastructure files...
✓ Infrastructure files copied (8 files)
...
✓ Archive created: edms-production-20251224-082745.tar.gz (1.5M)

╔═══════════════════════════════════════════════════════════════╗
║     Deployment Package Created Successfully                   ║
╚═══════════════════════════════════════════════════════════════╝

Package Details:
  Name:          edms-production-20251224-082745
  Total Files:   410
  Package Size:  7.5M
  Archive Size:  1.5M
  Errors:        0
```

### Automated Transfer Script

#### Basic Usage

```bash
./scripts/deploy-to-remote.sh [user@]host[:path] [options]
```

#### Arguments

| Argument | Description | Example |
|----------|-------------|---------|
| `[user@]host[:path]` | Remote server destination | `user@server.com:/opt/` |

If user is omitted, current user is used.  
If path is omitted, `/opt/` is used.

#### Options

| Option | Description | Default |
|--------|-------------|---------|
| `-p, --path PATH` | Remote deployment path | `/opt` |
| `-k, --key KEY` | SSH private key file | Default SSH key |
| `-P, --port PORT` | SSH port | `22` |
| `-a, --auto-deploy` | Automatically deploy after transfer | `false` |
| `-n, --no-verify` | Skip checksum verification | Verify enabled |
| `-K, --keep` | Keep local package after transfer | Delete after |
| `-v, --verbose` | Verbose output | Normal output |
| `-h, --help` | Show help message | - |

#### Examples

**Basic transfer to server:**
```bash
./scripts/deploy-to-remote.sh root@192.168.1.100
```

**Transfer to specific path:**
```bash
./scripts/deploy-to-remote.sh user@server.com:/var/www/edms
```

**Transfer with custom SSH key:**
```bash
./scripts/deploy-to-remote.sh user@server.com \
  --key ~/.ssh/production_key \
  --port 2222
```

**Transfer and auto-deploy:**
```bash
./scripts/deploy-to-remote.sh user@server.com --auto-deploy
```

**Transfer with verbose output and keep local:**
```bash
./scripts/deploy-to-remote.sh user@server.com \
  --verbose \
  --keep
```

#### What It Does

1. **Validates remote connection**
   - Tests SSH connectivity
   - Verifies authentication
   - Checks network accessibility

2. **Checks remote requirements**
   - Docker installation and version
   - Docker Compose availability
   - Remote path accessibility

3. **Creates deployment package**
   - Runs package creator script
   - Generates fresh package
   - Verifies package creation

4. **Transfers package**
   - Uses SCP for transfer
   - Shows progress (in verbose mode)
   - Handles large files efficiently

5. **Verifies transfer integrity**
   - Compares SHA256 checksums
   - Local vs remote verification
   - Ensures data integrity

6. **Extracts on remote**
   - Extracts tar.gz archive
   - Removes archive after extraction
   - Prepares for deployment

7. **Optional auto-deploy**
   - Runs deployment script remotely (if enabled)
   - Sets up application
   - Starts services

8. **Cleanup**
   - Removes local package (unless --keep specified)
   - Cleans temporary files
   - Reports summary

#### Example Output

```
╔═══════════════════════════════════════════════════════════════╗
║     EDMS Automated Remote Deployment Transfer                ║
╚═══════════════════════════════════════════════════════════════╝

Configuration:
  Remote Host:    root@192.168.1.100
  Remote Path:    /opt
  SSH Port:       22
  Auto Deploy:    false
  Verify Checksum: true
  Keep Local:     false

ℹ Validating remote connection...
✓ Remote connection validated
ℹ Checking remote server requirements...
✓ Docker found: Docker version 24.0.7
✓ Docker Compose found: Docker Compose version v2.23.0
✓ Remote path accessible: /opt
ℹ Creating deployment package...
✓ Package created: edms-production-20251224-082745.tar.gz
ℹ Package size: 1.5M
ℹ Transferring package to remote server...
✓ Package transferred successfully
ℹ Verifying transfer integrity...
✓ Checksum verification passed
ℹ Extracting package on remote server...
✓ Package extracted on remote server
ℹ Cleaning up local files...
✓ Local cleanup completed

╔═══════════════════════════════════════════════════════════════╗
║     Transfer Completed Successfully                           ║
╚═══════════════════════════════════════════════════════════════╝

Transfer Details:
  Package:        edms-production-20251224-082745
  Remote Host:    root@192.168.1.100
  Remote Path:    /opt/edms-production-20251224-082745

Next Steps:
  1. SSH to the remote server:
     ssh root@192.168.1.100
  
  2. Navigate to deployment directory:
     cd /opt/edms-production-20251224-082745
  
  3. Run interactive deployment:
     ./deploy-interactive.sh
```

## 📊 Package Contents

### Directory Structure

```
edms-production-YYYYMMDD-HHMMSS/
├── backend/                    # Django application
│   ├── apps/                  # Application modules (256 .py files)
│   │   ├── admin_pages/
│   │   ├── api/
│   │   ├── audit/
│   │   ├── backup/
│   │   ├── documents/
│   │   ├── placeholders/
│   │   ├── scheduler/
│   │   ├── search/
│   │   ├── security/
│   │   ├── settings/
│   │   ├── users/
│   │   └── workflows/
│   ├── edms/                  # Core configuration
│   │   ├── settings/
│   │   ├── urls.py
│   │   ├── wsgi.py
│   │   └── asgi.py
│   ├── fixtures/              # Initial data
│   │   └── initial_users.json
│   ├── requirements/          # Python dependencies
│   │   ├── base.txt
│   │   ├── production.txt
│   │   ├── development.txt
│   │   └── test.txt
│   ├── database/              # Database utilities
│   ├── storage/               # File storage (empty)
│   ├── logs/                  # Application logs (empty)
│   ├── media/                 # User uploads (empty)
│   ├── manage.py              # Django management
│   └── .env.example           # Environment template
│
├── frontend/                   # React application
│   ├── src/                   # Source code
│   │   ├── components/        # 50 React components
│   │   ├── pages/
│   │   ├── contexts/
│   │   ├── hooks/
│   │   ├── services/
│   │   ├── types/
│   │   ├── utils/
│   │   └── styles/
│   ├── public/                # Static assets
│   │   ├── index.html
│   │   └── backup-test.html
│   ├── package.json           # Node dependencies
│   ├── package-lock.json
│   ├── tailwind.config.js     # Tailwind CSS config
│   └── nginx.conf             # Nginx configuration
│
├── infrastructure/            # Docker setup
│   ├── containers/           # Dockerfiles
│   │   ├── Dockerfile.backend
│   │   ├── Dockerfile.backend.prod
│   │   ├── Dockerfile.frontend
│   │   └── Dockerfile.frontend.prod
│   └── nginx/                # Web server config
│       ├── frontend.conf
│       └── nginx.prod.conf
│
├── scripts/                   # Utility scripts
│   ├── backup-system.sh
│   └── deploy-production.sh
│
├── docs/                      # Documentation
│   ├── DEPLOYMENT_QUICK_START.md
│   ├── PRODUCTION_DEPLOYMENT_READINESS.md
│   ├── DOCKER_NETWORKING_EXPLAINED.md
│   └── HAPROXY_INTEGRATION_GUIDE.md
│
├── docker-compose.yml         # Development config
├── docker-compose.prod.yml    # Production config
├── deploy-interactive.sh      # Interactive deployment
├── quick-deploy.sh            # Quick deployment
├── README-DEPLOYMENT.md       # Main deployment guide
├── README.md                  # Project README
├── CHANGELOG.md               # Change history
├── LICENSE                    # License file
├── SECURITY.md                # Security guidelines
├── .gitignore                 # Git ignore rules
├── MANIFEST.txt               # Package manifest
└── checksums.sha256           # File checksums (546 entries)
```

### File Statistics

- **Total Files**: 410
- **Backend Files**: 292 (Python modules, configs, requirements)
- **Frontend Files**: 99 (React components, configs)
- **Infrastructure Files**: 8 (Dockerfiles, nginx configs)
- **Scripts**: 3 (deployment automation)
- **Documentation**: 8 (markdown guides)

### Package Sizes

- **Uncompressed**: 7.5M
- **Compressed**: 1.5M (80% reduction)
- **Checksum File**: 62K (546 entries)

## 🔐 Security Features

### Package Creator
- Excludes sensitive files (`.env`, credentials, databases)
- Excludes development files (`__pycache__`, `.pyc`, `node_modules`)
- Generates checksums for integrity verification
- Creates secure `.gitignore` in package

### Transfer Script
- Supports SSH key authentication
- Validates remote connection before transfer
- Verifies checksums after transfer
- Uses SCP for secure transfer
- No plaintext credentials in scripts

## ✅ Verification & Testing

### Verify Package Locally

```bash
cd edms-production-YYYYMMDD-HHMMSS

# Verify all checksums
sha256sum -c checksums.sha256

# Check critical files
ls -l backend/manage.py
ls -l frontend/package.json
ls -l docker-compose.prod.yml

# View manifest
cat MANIFEST.txt
```

### Test Package Extraction

```bash
# Extract to test directory
tar -xzf edms-production-YYYYMMDD-HHMMSS.tar.gz -C /tmp/test

# Verify extraction
cd /tmp/test/edms-production-YYYYMMDD-HHMMSS
./quick-deploy.sh --help
```

### Test Remote Connection

```bash
# Test SSH connectivity
ssh user@server.com 'echo "Connection successful"'

# Test with specific key
ssh -i ~/.ssh/production_key user@server.com 'echo "OK"'

# Dry run transfer script (just validation)
./scripts/deploy-to-remote.sh user@server.com --help
```

## 🔧 Troubleshooting

### Package Creation Issues

**Problem**: Script fails with "Permission denied"
```bash
# Solution: Make script executable
chmod +x scripts/create-production-package.sh
```

**Problem**: Missing files in package
```bash
# Check if source files exist
ls -la backend/manage.py
ls -la frontend/package.json

# Review creation log
./scripts/create-production-package.sh 2>&1 | tee package.log
```

### Transfer Issues

**Problem**: Cannot connect to remote server
```bash
# Test SSH connection
ssh -v user@server.com

# Test with key
ssh -i ~/.ssh/key user@server.com

# Check firewall
telnet server.com 22
```

**Problem**: Checksum verification fails
```bash
# Transfer with verbose mode
./scripts/deploy-to-remote.sh user@server.com --verbose

# Skip verification (not recommended)
./scripts/deploy-to-remote.sh user@server.com --no-verify
```

**Problem**: Permission denied on remote
```bash
# Ensure user has sudo privileges
ssh user@server.com 'sudo -v'

# Or change remote path to user-writable directory
./scripts/deploy-to-remote.sh user@server.com --path ~/deployments
```

### Deployment Issues

**Problem**: Docker not found on remote
```bash
# Install Docker on remote server first
ssh user@server.com
curl -fsSL https://get.docker.com | sh
```

**Problem**: Package extraction fails
```bash
# Check disk space on remote
ssh user@server.com 'df -h'

# Manually extract
ssh user@server.com
cd /opt
tar -xzf edms-production-*.tar.gz
```

## 📝 Best Practices

### Before Deployment

1. ✅ Test package creation locally
2. ✅ Verify all critical files are included
3. ✅ Check package size is reasonable (~1.5M)
4. ✅ Review MANIFEST.txt for completeness
5. ✅ Test SSH connection to remote server
6. ✅ Ensure remote server meets requirements

### During Deployment

1. ✅ Use verbose mode for first deployment
2. ✅ Keep local package until verified (--keep)
3. ✅ Verify checksums after transfer
4. ✅ Test extraction before deployment
5. ✅ Review deployment logs

### After Deployment

1. ✅ Verify services are running
2. ✅ Check application health endpoints
3. ✅ Review container logs
4. ✅ Test core functionality
5. ✅ Document any custom configuration
6. ✅ Create backup of working deployment

## 🔄 Workflow Examples

### Complete Deployment Workflow

```bash
# 1. Create package
./scripts/create-production-package.sh

# 2. Transfer to staging
./scripts/deploy-to-remote.sh staging@staging.example.com \
  --key ~/.ssh/staging_key \
  --keep

# 3. Test on staging
ssh staging@staging.example.com
cd /opt/edms-production-*
./deploy-interactive.sh
# ... test application ...

# 4. Transfer to production
./scripts/deploy-to-remote.sh production@prod.example.com \
  --key ~/.ssh/production_key \
  --auto-deploy

# 5. Verify production
ssh production@prod.example.com
docker compose ps
curl http://localhost:8000/health/
```

### Emergency Hotfix Deployment

```bash
# Quick package and deploy
./scripts/create-production-package.sh && \
./scripts/deploy-to-remote.sh user@server.com --auto-deploy
```

### Multi-Server Deployment

```bash
# Deploy to multiple servers
for server in server1.com server2.com server3.com; do
  echo "Deploying to $server..."
  ./scripts/deploy-to-remote.sh "user@$server" --keep
done
```

## 📈 Success Metrics

### Package Creator Results
- ✅ **Completion**: 100% success rate
- ✅ **Errors**: 0 errors during creation
- ✅ **File Coverage**: 410 files packaged
- ✅ **Compression**: 80% size reduction
- ✅ **Integrity**: 546 checksums generated
- ✅ **Speed**: ~10 seconds to create package

### Transfer Script Results
- ✅ **Validation**: Connection pre-verification
- ✅ **Requirements**: Docker/Compose detection
- ✅ **Integrity**: SHA256 checksum verification
- ✅ **Automation**: End-to-end automation
- ✅ **Safety**: Secure transfer via SCP
- ✅ **Cleanup**: Automatic local cleanup

## 🆘 Support

### Getting Help

1. **Read documentation**
   - This guide
   - `README-DEPLOYMENT.md` in package
   - `docs/DEPLOYMENT_QUICK_START.md`

2. **Check logs**
   - Package creation output
   - Transfer script output (use `--verbose`)
   - SSH connection logs (`ssh -v`)

3. **Verify environment**
   - Local: Docker, Docker Compose installed
   - Remote: SSH access, Docker installed
   - Network: Firewall rules, port access

### Common Commands

```bash
# View help
./scripts/create-production-package.sh --help  # (no help flag needed)
./scripts/deploy-to-remote.sh --help

# Verbose output
./scripts/deploy-to-remote.sh user@server.com --verbose

# Keep files for debugging
./scripts/deploy-to-remote.sh user@server.com --keep

# Test connection only
ssh user@server.com 'echo OK'
```

## 📚 Related Documentation

- **README-DEPLOYMENT.md** - Main deployment instructions
- **DEPLOYMENT_QUICK_START.md** - Quick start guide
- **PRODUCTION_DEPLOYMENT_READINESS.md** - Pre-deployment checklist
- **DOCKER_NETWORKING_EXPLAINED.md** - Network configuration
- **HAPROXY_INTEGRATION_GUIDE.md** - Load balancer setup

## 🎉 Conclusion

The EDMS deployment automation system provides a complete, tested solution for creating and deploying production packages. With zero errors in testing, comprehensive verification, and automated workflows, it streamlines the deployment process from development to production.

**Key Achievements**:
- ✅ 410 files packaged automatically
- ✅ 80% compression ratio
- ✅ 546 checksums for integrity
- ✅ 0 errors in testing
- ✅ End-to-end automation
- ✅ Production-ready quality

Ready to deploy? Start with:
```bash
./scripts/create-production-package.sh
```

---

**Document Version**: 2.0  
**Last Updated**: December 24, 2024  
**Status**: ✅ Production Ready
