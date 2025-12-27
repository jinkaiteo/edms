# EDMS CI/CD Setup Checklist

**Quick reference for setting up CI/CD integration**

---

## ✅ GitHub Actions Setup

### Prerequisites
- [ ] GitHub repository created
- [ ] Admin access to repository

### Steps
1. [ ] **Add Repository Secrets** (Settings → Secrets)
   - [ ] `STAGING_SSH_KEY` - SSH private key
   - [ ] `STAGING_HOST` - Server hostname/IP
   - [ ] `STAGING_USER` - SSH username
   - [ ] `PRODUCTION_SSH_KEY` - SSH private key
   - [ ] `PRODUCTION_HOST` - Server hostname/IP
   - [ ] `PRODUCTION_USER` - SSH username

2. [ ] **Create Environments** (Settings → Environments)
   - [ ] Create `staging` environment
   - [ ] Create `production` environment
   - [ ] Add reviewers for production (recommended)

3. [ ] **Enable Actions** (Actions tab)
   - [ ] Enable workflows

4. [ ] **Push Workflow File**
   - [ ] File already in `.github/workflows/deploy.yml`
   - [ ] Push to repository

5. [ ] **Test**
   - [ ] Push to `develop` branch → deploys to staging
   - [ ] Push to `main` branch → deploys to production (with approval)

---

## ✅ GitLab CI Setup

### Prerequisites
- [ ] GitLab repository created
- [ ] Maintainer access to project

### Steps
1. [ ] **Add CI/CD Variables** (Settings → CI/CD → Variables)
   - [ ] `STAGING_SSH_KEY` - SSH private key (protected, masked)
   - [ ] `STAGING_HOST` - Server hostname
   - [ ] `STAGING_USER` - SSH username
   - [ ] `PRODUCTION_SSH_KEY` - SSH private key (protected, masked)
   - [ ] `PRODUCTION_HOST` - Server hostname
   - [ ] `PRODUCTION_USER` - SSH username

2. [ ] **Configure Runners** (Settings → CI/CD → Runners)
   - [ ] Enable shared runners, or
   - [ ] Configure specific runners

3. [ ] **Push Pipeline File**
   - [ ] File already in `.gitlab-ci.yml`
   - [ ] Push to repository

4. [ ] **Configure Environments** (optional)
   - [ ] Settings → CI/CD → Environments
   - [ ] Add protection rules

5. [ ] **Test**
   - [ ] Push to `develop` → auto deploys to staging
   - [ ] Push to `main` → manual deploy to production

---

## ✅ Jenkins Setup

### Prerequisites
- [ ] Jenkins server installed
- [ ] Required plugins installed:
  - [ ] Pipeline
  - [ ] Docker Pipeline
  - [ ] SSH Agent
  - [ ] Credentials Binding

### Steps
1. [ ] **Add Credentials** (Manage Jenkins → Manage Credentials)
   - [ ] `staging-ssh-key` - SSH Username with private key
   - [ ] `staging-host` - Secret text
   - [ ] `staging-user` - Secret text
   - [ ] `production-ssh-key` - SSH Username with private key
   - [ ] `production-host` - Secret text
   - [ ] `production-user` - Secret text

2. [ ] **Create Pipeline Job**
   - [ ] New Item → Pipeline
   - [ ] Pipeline definition: Pipeline script from SCM
   - [ ] SCM: Git
   - [ ] Repository URL: your-repo-url
   - [ ] Script Path: `Jenkinsfile`

3. [ ] **Configure Triggers** (optional)
   - [ ] GitHub webhook, or
   - [ ] Poll SCM

4. [ ] **Test**
   - [ ] Build with Parameters
   - [ ] Select deployment environment
   - [ ] Run pipeline

---

## ✅ Docker-Based CI Setup

### Prerequisites
- [ ] Docker installed
- [ ] Docker Compose installed

### Steps
1. [ ] **Build CI Runner Image**
   ```bash
   docker-compose -f docker-compose.ci.yml build ci-runner
   ```

2. [ ] **Set Environment Variables**
   ```bash
   export DEPLOY_HOST=your-server.com
   export DEPLOY_USER=deploy-user
   export SSH_KEY=~/.ssh/id_rsa
   ```

3. [ ] **Test Pipeline**
   ```bash
   ./scripts/ci-pipeline.sh validate
   ./scripts/ci-pipeline.sh test
   ```

4. [ ] **Full Deployment**
   ```bash
   ./scripts/ci-pipeline.sh all
   ```

---

## 🔑 SSH Key Setup

### For All Platforms
1. [ ] **Generate deployment key**
   ```bash
   ssh-keygen -t ed25519 -C "ci-deployment" -f ~/.ssh/ci_deploy_key
   ```

2. [ ] **Add public key to servers**
   ```bash
   ssh-copy-id -i ~/.ssh/ci_deploy_key.pub user@staging-server
   ssh-copy-id -i ~/.ssh/ci_deploy_key.pub user@production-server
   ```

3. [ ] **Add private key to CI/CD**
   - [ ] Copy content: `cat ~/.ssh/ci_deploy_key`
   - [ ] Add to CI/CD secrets/variables

4. [ ] **Test connection**
   ```bash
   ssh -i ~/.ssh/ci_deploy_key user@server "echo OK"
   ```

---

## 🧪 Testing Checklist

### Before Going Live
- [ ] **Local testing works**
  ```bash
  ./scripts/pre-deploy-check.sh .
  ./scripts/health-check.sh
  ```

- [ ] **Staging deployment works**
  - [ ] Push to develop branch
  - [ ] Pipeline runs successfully
  - [ ] Application is accessible
  - [ ] Health checks pass

- [ ] **Rollback works**
  ```bash
  ssh user@staging
  cd /opt/edms-production-*
  ./scripts/rollback.sh --list
  ./scripts/rollback.sh --previous --dry-run
  ```

- [ ] **Production deployment works** (test environment)
  - [ ] Manual approval process
  - [ ] Post-deployment validation
  - [ ] Health monitoring

---

## 📊 Verification

### After Setup
- [ ] Pipeline runs automatically on push
- [ ] All stages complete successfully
- [ ] Artifacts are generated and stored
- [ ] Health reports are accessible
- [ ] Rollback tested and working
- [ ] Notifications configured (if applicable)

---

## 🚨 Troubleshooting

### If Pipeline Fails

**SSH Connection Issues:**
```bash
# Test SSH manually
ssh -v -i ~/.ssh/key user@host

# Check key format
ssh-keygen -y -f ~/.ssh/key
```

**Package Creation Issues:**
```bash
# Check locally
./scripts/create-production-package.sh
ls -lh edms-production-*.tar.gz
```

**Health Check Issues:**
```bash
# Test on server
ssh user@server
cd /opt/edms-production-*
./scripts/health-check.sh --verbose
```

---

## 📚 Quick Reference

### Key Files
- `.github/workflows/deploy.yml` - GitHub Actions
- `.gitlab-ci.yml` - GitLab CI
- `Jenkinsfile` - Jenkins Pipeline
- `docker-compose.ci.yml` - Docker CI services
- `scripts/ci-pipeline.sh` - Universal pipeline

### Documentation
- `CI_CD_INTEGRATION_GUIDE.md` - Complete guide
- `AUTOMATION_SCRIPTS_GUIDE.md` - Scripts documentation

---

**Ready to deploy?** Follow your platform's checklist above! ✅
