# EDMS Deployment Scripts

This directory contains production-ready deployment automation scripts.

## 📦 Available Scripts

### 1. Production Package Creator
**File**: `create-production-package.sh`

Creates a complete, verified deployment package for production.

```bash
./scripts/create-production-package.sh [output-directory]
```

**Features**:
- Creates minimal production package (410+ files)
- Generates SHA256 checksums (546 files)
- Compresses to tar.gz (80% reduction: 7.5M → 1.5M)
- Verifies package integrity
- Zero errors in testing

**Output**:
- `edms-production-YYYYMMDD-HHMMSS/` - Package directory
- `edms-production-YYYYMMDD-HHMMSS.tar.gz` - Compressed archive

---

### 2. Automated Remote Transfer
**File**: `deploy-to-remote.sh`

Automates package creation, transfer, and deployment to remote servers.

```bash
./scripts/deploy-to-remote.sh [user@]host[:path] [options]
```

**Options**:
- `-p, --path PATH` - Remote path (default: /opt)
- `-k, --key KEY` - SSH private key
- `-P, --port PORT` - SSH port (default: 22)
- `-a, --auto-deploy` - Auto deploy after transfer
- `-K, --keep` - Keep local package
- `-v, --verbose` - Verbose output
- `-h, --help` - Show help

**Examples**:
```bash
# Basic transfer
./scripts/deploy-to-remote.sh user@server.com

# With SSH key
./scripts/deploy-to-remote.sh user@server.com --key ~/.ssh/prod_key

# Auto deploy
./scripts/deploy-to-remote.sh user@server.com --auto-deploy
```

---

### 3. Health Check & Monitoring
**File**: `health-check.sh`

Comprehensive health monitoring with continuous watch mode and HTML reporting.

```bash
./scripts/health-check.sh --watch
```

---

### 4. Deployment Rollback
**File**: `rollback.sh`

Safe rollback mechanism with backup creation and verification.

```bash
./scripts/rollback.sh --previous --backup-first
```

---

### 5. Pre-Deployment Verification
**File**: `pre-deploy-check.sh`

Verifies system readiness before deployment.

```bash
./scripts/pre-deploy-check.sh /path/to/package
```

---

### 6. Post-Deployment Validation
**File**: `post-deploy-check.sh`

Validates deployment success and application health.

```bash
./scripts/post-deploy-check.sh
```

---

### 7. Backup System
**File**: `backup-system.sh`

Creates system backups (database, configurations, files).

---

### 8. Production Deployment
**File**: `deploy-production.sh`

Handles production deployment operations.

---

## 🚀 Quick Start

### Complete Deployment Workflow

```bash
# 1. Create package
./scripts/create-production-package.sh

# 2. Transfer to server
./scripts/deploy-to-remote.sh user@server.com

# 3. Deploy on server
ssh user@server.com
cd /opt/edms-production-*
./quick-deploy.sh
```

### One-Line Deployment

```bash
./scripts/deploy-to-remote.sh user@server.com --auto-deploy
```

## 📚 Documentation

Complete documentation available in project root:

- **DEPLOYMENT_AUTOMATION_GUIDE.md** - Complete usage guide (21K)
- **DEPLOYMENT_PACKAGE_SUMMARY.md** - Test results and summary (9.2K)
- **DEPLOYMENT_QUICK_REFERENCE.md** - Quick reference card

## ✅ Testing Status

| Script | Status | Test Results |
|--------|--------|--------------|
| create-production-package.sh | ✅ Tested | 0 errors, 410 files packaged |
| deploy-to-remote.sh | ✅ Tested | All options verified |
| health-check.sh | ✅ Tested | All modes working |
| rollback.sh | ✅ Tested | All options verified |
| pre-deploy-check.sh | ✅ Tested | All checks working |
| post-deploy-check.sh | ✅ Tested | All validations working |

## 🔐 Security

- SSH key authentication supported
- SHA256 checksum verification
- Secure SCP transfer
- No credentials in scripts
- Excludes sensitive files

## 📊 Performance

| Metric | Value |
|--------|-------|
| Package Creation | ~10 seconds |
| Compression Ratio | 80% (7.5M → 1.5M) |
| Files Packaged | 410 |
| Checksums | 546 files |

## 🆘 Support

For issues or questions:

1. Read documentation in project root
2. Run with `--help` flag
3. Use `--verbose` for debugging
4. Check logs and error messages

## 📝 Version

- **Version**: 2.0
- **Date**: December 24, 2024
- **Status**: Production Ready ✅
