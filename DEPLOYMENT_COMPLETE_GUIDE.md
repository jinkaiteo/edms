# EDMS Deployment Complete Guide

## 📋 Table of Contents

1. [Overview](#overview)
2. [Deployment Architecture](#deployment-architecture)
3. [Deployment Methods](#deployment-methods)
4. [Staging Deployment (Internal Network)](#staging-deployment-internal-network)
5. [Production Deployment](#production-deployment)
6. [Advanced Options](#advanced-options)
7. [Troubleshooting](#troubleshooting)

---

## Overview

### What You've Built

Your CI/CD pipeline automatically:
- ✅ Validates every code change
- ✅ Runs tests
- ✅ Builds production packages
- ✅ Creates deployment artifacts
- ✅ Handles internal network constraints

### Deployment Artifacts

Each successful workflow run creates:
```
deployment-package artifact:
  ├── edms-production-YYYYMMDD-HHMMSS.tar.gz (1.5MB)
  │   ├── 410 files ready for deployment
  │   ├── SHA256 checksums for verification
  │   └── All deployment scripts included
  └── Retention: 7 days
```

---

## Deployment Architecture

### System Components

```
EDMS Application Stack:
├── Frontend (React + TypeScript)
│   ├── Nginx web server
│   ├── Port 3000 (or 80/443 in production)
│   └── Static build artifacts
│
├── Backend (Django + DRF)
│   ├── Gunicorn WSGI server
│   ├── Port 8000
│   └── Python 3.11 runtime
│
├── Database (PostgreSQL)
│   ├── Port 5432
│   └── Persistent data volume
│
├── Cache (Redis)
│   ├── Port 6379
│   └── Session and cache storage
│
├── Task Queue (Celery Worker)
│   └── Background job processing
│
└── Scheduler (Celery Beat)
    └── Scheduled task execution
```

### Docker Architecture

```yaml
# 6 Docker containers:
edms_frontend       # React application
edms_backend        # Django API
edms_db            # PostgreSQL database
edms_redis         # Redis cache
edms_celery_worker # Task processor
edms_celery_beat   # Task scheduler
```

---

## Deployment Methods

### Method 1: Automated via GitHub Actions ⭐ (Production Only)

**When to use:**
- Production deployments
- Server is publicly accessible
- Want fully automated deployment

**How it works:**
```bash
git checkout main
git merge develop
git push origin main

# GitHub Actions automatically:
# 1. Runs all tests
# 2. Builds application
# 3. Creates deployment package
# 4. SSHs to production server
# 5. Deploys via Docker Compose
# 6. Runs health checks
# 7. Creates GitHub release
```

**Requirements:**
- Production server publicly accessible
- SSH access configured
- GitHub secrets configured:
  - PRODUCTION_SSH_KEY
  - PRODUCTION_HOST
  - PRODUCTION_USER

---

### Method 2: Manual Download and Deploy ⭐ (Staging - Internal Network)

**When to use:**
- Staging server on internal network
- Cannot be reached from GitHub Actions
- Need manual control over deployment

**Step-by-Step Process:**

#### Step 1: Download Deployment Package

```bash
# Option A: From GitHub Actions UI
1. Go to: https://github.com/jinkaiteo/edms/actions
2. Click on the latest successful workflow run
3. Scroll to "Artifacts" section
4. Download "deployment-package" artifact
5. Save to your local machine

# Option B: Using GitHub CLI
gh run list --limit 1
gh run download <run-id> --name deployment-package
```

#### Step 2: Transfer to Internal Network Machine

```bash
# If you're already on internal network machine:
# (Package downloaded directly there)

# If you need to transfer:
scp edms-production-*.tar.gz user@internal-machine:/tmp/
```

#### Step 3: Extract Package

```bash
# On the machine with internal network access
cd /tmp  # or your preferred location
tar -xzf edms-production-*.tar.gz
cd edms-production-*/
```

#### Step 4: Deploy to Staging Server

```bash
# Option A: Automated deployment script
./scripts/deploy-to-remote.sh user@staging-server-ip

# Option B: Interactive deployment (recommended first time)
./deploy-interactive.sh
# Follow the prompts:
# - Remote host: user@staging-server-ip
# - Remote path: /opt/edms
# - SSH key: path to your SSH key
# - Verify checksum: yes

# Option C: Manual deployment
# (See detailed steps below)
```

---

### Method 3: Local Package Creation and Deploy

**When to use:**
- You have the repository cloned on internal network
- Want to deploy latest code directly
- Testing changes before committing

**Process:**

```bash
# From your repository on internal network machine
cd /path/to/edms

# Create deployment package
./scripts/create-production-package.sh

# Package created: edms-production-YYYYMMDD-HHMMSS.tar.gz

# Deploy to staging
./scripts/deploy-to-remote.sh user@staging-server-ip

# Or use interactive mode
./deploy-interactive.sh
```

---

## Staging Deployment (Internal Network)

### Complete Walkthrough

#### Prerequisites

1. **Staging Server Ready:**
   ```bash
   # Server must have:
   - Ubuntu 20.04+ (or similar Linux)
   - Docker 20.10+
   - Docker Compose 2.0+
   - SSH access enabled
   - Minimum 4GB RAM
   - Minimum 20GB disk space
   ```

2. **SSH Access Configured:**
   ```bash
   # From your deployment machine:
   ssh user@staging-server-ip
   # Should connect without password (using SSH key)
   
   # If not, add your SSH key:
   ssh-copy-id -i ~/.ssh/id_rsa user@staging-server-ip
   ```

3. **Docker Installed on Server:**
   ```bash
   # Check if Docker is installed:
   ssh user@staging-server-ip 'docker --version'
   ssh user@staging-server-ip 'docker compose version'
   
   # If not installed, see: DOCKER_INSTALLATION.md
   ```

#### Deployment Steps

**Step 1: Download and Extract Package**

```bash
# Download from GitHub Actions
# (as described in Method 2 above)

# Extract
tar -xzf edms-production-20251227-*.tar.gz
cd edms-production-20251227-*/
```

**Step 2: Review Configuration**

```bash
# Check what will be deployed
cat MANIFEST.txt | head -20

# Verify checksums
cat checksums.sha256 | head -10

# Review deployment script
less scripts/deploy-to-remote.sh
```

**Step 3: Run Deployment**

```bash
# Using automated script (recommended)
./scripts/deploy-to-remote.sh user@staging-server-ip \
  --key ~/.ssh/id_rsa \
  --path /opt/edms \
  --verbose

# Script will:
# ✓ Validate remote connection
# ✓ Transfer package via SCP
# ✓ Extract on remote server
# ✓ Stop existing containers (if any)
# ✓ Pull/build Docker images
# ✓ Start new containers
# ✓ Run health checks
```

**Step 4: Monitor Deployment**

```bash
# Watch the deployment output:
# You'll see progress indicators like:
Configuration:
  Remote Host:    user@staging-server-ip
  Remote Path:    /opt/edms
  SSH Port:       22

ℹ Validating remote connection...
✓ Remote host is accessible
ℹ Creating deployment directory...
✓ Directory created: /opt/edms-production-20251227-103733
ℹ Transferring package...
  → Uploading edms-production-20251227-103733.tar.gz
✓ Package transferred successfully
ℹ Extracting package on remote host...
✓ Package extracted
ℹ Stopping existing containers...
✓ Containers stopped
ℹ Starting new deployment...
✓ Docker Compose started successfully
ℹ Running health checks...
✓ All services healthy

Deployment Summary:
  Status:     SUCCESS
  Time:       2m 34s
  Services:   6/6 running
  Location:   /opt/edms-production-20251227-103733
```

**Step 5: Verify Deployment**

```bash
# SSH to the server and check
ssh user@staging-server-ip

# Check Docker containers
cd /opt/edms-production-*/
docker compose ps

# Should show:
NAME                   STATUS
edms_backend           Up 2 minutes
edms_frontend          Up 2 minutes
edms_db                Up 2 minutes
edms_redis             Up 2 minutes
edms_celery_worker     Up 2 minutes
edms_celery_beat       Up 2 minutes

# Check logs
docker compose logs --tail=50 backend
docker compose logs --tail=50 frontend

# Test the application
curl http://localhost:3000  # Frontend
curl http://localhost:8000/api/v1/health/  # Backend API
```

**Step 6: Access the Application**

```bash
# From internal network:
# Frontend: http://staging-server-ip:3000
# Backend API: http://staging-server-ip:8000
# Admin: http://staging-server-ip:8000/admin

# Login credentials (default):
Username: admin
Password: admin123  # Change this!
```

---

## Production Deployment

### Automated Deployment (GitHub Actions)

**Prerequisites:**

1. **Production Server Setup:**
   ```bash
   # Must be publicly accessible
   # Must have Docker and Docker Compose
   # Must allow SSH from GitHub Actions IPs
   ```

2. **GitHub Secrets Configured:**
   ```
   Go to: https://github.com/jinkaiteo/edms/settings/secrets/actions
   
   Add:
   - PRODUCTION_SSH_KEY: Full private key
   - PRODUCTION_HOST: prod.example.com or IP
   - PRODUCTION_USER: deploy or ubuntu
   ```

3. **GitHub Environment Created:**
   ```
   Go to: Settings → Environments
   Create: "production" environment
   
   Optional but recommended:
   - Add required reviewers
   - Add deployment protection rules
   ```

**Deployment Process:**

```bash
# 1. Ensure all changes tested in staging
# 2. Merge to main branch
git checkout main
git pull origin main
git merge develop

# 3. Review changes
git log --oneline -5
git diff develop

# 4. Push to trigger deployment
git push origin main

# 5. Monitor in GitHub Actions
# Go to: https://github.com/jinkaiteo/edms/actions
# Watch the deployment progress

# 6. Workflow will:
#    ✓ Run all tests
#    ✓ Build application
#    ✓ Create backup on production
#    ✓ Deploy new version
#    ✓ Run health checks
#    ✓ Monitor for 5 minutes
#    ✓ Create GitHub release
#    ✓ Rollback if any failure
```

**Production Deployment Timeline:**

```
00:00 - 03:00  Pre-deployment checks
03:00 - 10:00  Build and test
10:00 - 12:00  Create production backup
12:00 - 15:00  Deploy to production
15:00 - 16:00  Post-deployment validation
16:00 - 21:00  Health monitoring (5 min)
21:00          Create GitHub release
```

---

### Manual Production Deployment

**When to use:**
- First-time production deployment
- Need manual control
- Testing deployment process

**Process:**

```bash
# 1. Create production package locally
./scripts/create-production-package.sh

# 2. Transfer to production server
scp edms-production-*.tar.gz user@prod-server:/tmp/

# 3. SSH to production server
ssh user@prod-server

# 4. Create backup of existing deployment
cd /opt/edms-current
./scripts/backup-system.sh

# 5. Extract new package
cd /tmp
tar -xzf edms-production-*.tar.gz
cd edms-production-*/

# 6. Review deployment
cat MANIFEST.txt
cat README-DEPLOYMENT.md

# 7. Deploy
./deploy-interactive.sh

# 8. Verify
docker compose ps
docker compose logs

# 9. Test application
curl http://localhost:3000
curl http://localhost:8000/api/v1/health/

# 10. If successful, update symlink
cd /opt
rm edms-current
ln -s edms-production-20251227-* edms-current
```

---

## Advanced Options

### Self-Hosted GitHub Actions Runner

**Purpose:** Enable automated deployment to internal network staging server

**Setup Steps:**

```bash
# 1. On internal network machine (has access to staging)
cd ~
mkdir actions-runner && cd actions-runner

# 2. Download GitHub Actions runner
# Go to: https://github.com/jinkaiteo/edms/settings/actions/runners/new
# Follow the download and installation instructions

# 3. Configure runner
./config.sh --url https://github.com/jinkaiteo/edms --token <TOKEN>

# 4. Install as a service
sudo ./svc.sh install
sudo ./svc.sh start

# 5. Verify
./svc.sh status

# 6. Update workflow to use self-hosted runner
# In .github/workflows/deploy.yml:
# Change: runs-on: ubuntu-latest
# To:     runs-on: self-hosted
```

**Benefits:**
- ✅ Fully automated staging deployment
- ✅ No manual download/transfer needed
- ✅ Complete CI/CD for both environments

**Considerations:**
- ❌ Requires dedicated machine on internal network
- ❌ Need to maintain runner updates
- ❌ Security considerations (runner has GitHub access)

---

### Blue-Green Deployment

**Purpose:** Zero-downtime deployments

**Setup:**

```bash
# Deploy to "green" while "blue" is running
./scripts/deploy-to-remote.sh user@server \
  --path /opt/edms-green \
  --no-auto-start

# Test green deployment
ssh user@server 'cd /opt/edms-green && docker compose up -d'
# Test at http://server:3001 (different port)

# If successful, switch traffic
# Update load balancer or nginx to point to green
# Stop blue deployment
```

---

### Rolling Deployment

**Purpose:** Gradual rollout across multiple servers

```bash
# Deploy to 20% of servers
for server in server1; do
  ./scripts/deploy-to-remote.sh user@$server
done

# Monitor for issues

# Deploy to 50% more
for server in server2 server3; do
  ./scripts/deploy-to-remote.sh user@$server
done

# Deploy to remaining 30%
for server in server4 server5; do
  ./scripts/deploy-to-remote.sh user@$server
done
```

---

## Troubleshooting

### Common Issues and Solutions

#### Issue 1: SSH Connection Failed

**Symptoms:**
```
✗ Cannot connect to user@host
✗ Please check:
  - SSH service is running on remote host
  - Port 22 is accessible
```

**Solutions:**
```bash
# Test SSH manually
ssh -v user@host

# Check if port 22 is open
nc -zv host 22

# Try different port
ssh -p 2222 user@host

# Check firewall
# On server:
sudo ufw status
sudo ufw allow 22/tcp

# Test with specific key
ssh -i ~/.ssh/specific_key user@host
```

#### Issue 2: Docker Not Installed on Server

**Symptoms:**
```
bash: docker: command not found
```

**Solution:**
```bash
# SSH to server
ssh user@server

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add user to docker group
sudo usermod -aG docker $USER

# Re-login
exit
ssh user@server

# Verify
docker --version
docker compose version
```

#### Issue 3: Port Already in Use

**Symptoms:**
```
Error: bind: address already in use
```

**Solution:**
```bash
# Check what's using the port
ssh user@server 'sudo netstat -tlnp | grep :8000'

# Option A: Stop conflicting service
ssh user@server 'sudo systemctl stop <service>'

# Option B: Use different ports
# Edit docker-compose.prod.yml:
# Change "3000:3000" to "3001:3000"
```

#### Issue 4: Insufficient Disk Space

**Symptoms:**
```
Error: no space left on device
```

**Solution:**
```bash
# Check disk space
ssh user@server 'df -h'

# Clean up old Docker images
ssh user@server 'docker system prune -a --volumes -f'

# Remove old deployments
ssh user@server 'rm -rf /opt/edms-production-older-dates/'

# Check again
ssh user@server 'df -h'
```

#### Issue 5: Services Not Starting

**Symptoms:**
```
✗ Health check failed
Container edms_backend exited with code 1
```

**Solution:**
```bash
# SSH to server
ssh user@server
cd /opt/edms-production-*/

# Check logs
docker compose logs backend
docker compose logs frontend

# Check environment variables
cat backend/.env

# Restart specific service
docker compose restart backend

# Full restart
docker compose down
docker compose up -d

# Check status
docker compose ps
```

---

## Deployment Checklist

### Pre-Deployment

```
□ All tests passing in develop branch
□ Changes reviewed and approved
□ Database migrations tested
□ Backup of current deployment exists
□ Deployment window scheduled
□ Stakeholders notified
□ Rollback plan documented
```

### During Deployment

```
□ Monitor deployment logs
□ Watch Docker container status
□ Check application health endpoints
□ Verify database connectivity
□ Test critical user workflows
□ Monitor error rates
□ Check performance metrics
```

### Post-Deployment

```
□ All services running
□ Health checks passing
□ User login working
□ Document upload/download working
□ Workflow actions functional
□ Backup system operational
□ Monitoring alerts configured
□ Documentation updated
□ Team notified of completion
```

---

## Best Practices

### Security

1. **SSH Keys:**
   - Use separate keys for staging and production
   - Rotate keys periodically
   - Never commit keys to repository

2. **Secrets Management:**
   - All secrets in GitHub Secrets
   - Never in code or configuration files
   - Rotate database passwords regularly

3. **Server Access:**
   - Limit SSH access to specific IPs
   - Use fail2ban for brute force protection
   - Enable UFW firewall

### Reliability

1. **Backups:**
   - Automated daily backups
   - Test restore procedures monthly
   - Keep 30 days of backups

2. **Monitoring:**
   - Set up health check alerts
   - Monitor disk space
   - Track error rates
   - Log aggregation

3. **Rollback:**
   - Test rollback procedure
   - Keep last 3 deployments
   - Document rollback steps

### Performance

1. **Docker:**
   - Use production Dockerfiles
   - Optimize image sizes
   - Clean up old images

2. **Database:**
   - Regular VACUUM operations
   - Index optimization
   - Connection pooling configured

3. **Caching:**
   - Redis cache properly configured
   - Static files served by nginx
   - Enable gzip compression

---

## Quick Reference Commands

### Deployment

```bash
# Download and deploy to staging
# 1. Download artifact from GitHub Actions
# 2. Extract and deploy
tar -xzf edms-production-*.tar.gz
cd edms-production-*/
./scripts/deploy-to-remote.sh user@staging-ip

# Create local package and deploy
./scripts/create-production-package.sh
./scripts/deploy-to-remote.sh user@server-ip

# Interactive deployment
./deploy-interactive.sh

# Deploy to production (automated)
git checkout main && git merge develop && git push origin main
```

### Monitoring

```bash
# Check container status
ssh user@server 'cd /opt/edms-production-* && docker compose ps'

# View logs
ssh user@server 'cd /opt/edms-production-* && docker compose logs -f'

# Health check
ssh user@server 'cd /opt/edms-production-* && ./scripts/health-check.sh'

# Check disk space
ssh user@server 'df -h'

# Check memory
ssh user@server 'free -h'
```

### Maintenance

```bash
# Restart services
ssh user@server 'cd /opt/edms-production-* && docker compose restart'

# Full restart
ssh user@server 'cd /opt/edms-production-* && docker compose down && docker compose up -d'

# Update single service
ssh user@server 'cd /opt/edms-production-* && docker compose up -d --no-deps backend'

# Clean up
ssh user@server 'docker system prune -a -f'

# Create backup
ssh user@server 'cd /opt/edms-production-* && ./scripts/backup-system.sh'
```

---

## Support

For issues or questions:
1. Check troubleshooting section above
2. Review workflow logs in GitHub Actions
3. Check Docker logs on the server
4. Review deployment documentation

---

**Created:** 2025-12-27  
**Version:** 1.0  
**Status:** Complete and tested
