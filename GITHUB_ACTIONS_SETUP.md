# GitHub Actions CI/CD Setup Guide

**Step-by-step guide to set up automated deployments with GitHub Actions**

---

## 📋 Prerequisites

Before starting, ensure you have:
- [ ] GitHub repository with admin access
- [ ] SSH access to staging server
- [ ] SSH access to production server
- [ ] SSH keys for deployment

---

## 🚀 Step 1: Prepare SSH Keys

### Generate Deployment Keys

```bash
# Generate staging key
ssh-keygen -t ed25519 -C "github-staging-deploy" -f ~/.ssh/github_staging_key -N ""

# Generate production key
ssh-keygen -t ed25519 -C "github-production-deploy" -f ~/.ssh/github_production_key -N ""
```

### Add Public Keys to Servers

```bash
# Copy staging public key to staging server
ssh-copy-id -i ~/.ssh/github_staging_key.pub user@staging-server.com

# Copy production public key to production server
ssh-copy-id -i ~/.ssh/github_production_key.pub user@production-server.com
```

### Test SSH Access

```bash
# Test staging
ssh -i ~/.ssh/github_staging_key user@staging-server.com "echo 'Staging access OK'"

# Test production
ssh -i ~/.ssh/github_production_key user@production-server.com "echo 'Production access OK'"
```

---

## 🔐 Step 2: Add GitHub Secrets

### Navigate to Repository Secrets

1. Go to your GitHub repository
2. Click **Settings** (top menu)
3. Click **Secrets and variables** → **Actions** (left sidebar)
4. Click **New repository secret**

### Add Required Secrets

Add each of these secrets one by one:

#### Staging Secrets

**1. STAGING_SSH_KEY**
```bash
# Copy the private key content
cat ~/.ssh/github_staging_key

# Then paste the ENTIRE content (including BEGIN/END lines) into GitHub
```
- Name: `STAGING_SSH_KEY`
- Value: Entire private key content
- Click **Add secret**

**2. STAGING_HOST**
- Name: `STAGING_HOST`
- Value: `staging-server.com` (your staging server hostname or IP)
- Click **Add secret**

**3. STAGING_USER**
- Name: `STAGING_USER`
- Value: `deploy` (your SSH username for staging)
- Click **Add secret**

#### Production Secrets

**4. PRODUCTION_SSH_KEY**
```bash
# Copy the private key content
cat ~/.ssh/github_production_key

# Then paste the ENTIRE content into GitHub
```
- Name: `PRODUCTION_SSH_KEY`
- Value: Entire private key content
- Click **Add secret**

**5. PRODUCTION_HOST**
- Name: `PRODUCTION_HOST`
- Value: `production-server.com` (your production server hostname or IP)
- Click **Add secret**

**6. PRODUCTION_USER**
- Name: `PRODUCTION_USER`
- Value: `deploy` (your SSH username for production)
- Click **Add secret**

### Verify Secrets

After adding all secrets, you should see:
- ✓ STAGING_SSH_KEY
- ✓ STAGING_HOST
- ✓ STAGING_USER
- ✓ PRODUCTION_SSH_KEY
- ✓ PRODUCTION_HOST
- ✓ PRODUCTION_USER

---

## 🌍 Step 3: Configure Environments

### Create Staging Environment

1. Go to **Settings** → **Environments**
2. Click **New environment**
3. Name: `staging`
4. Click **Configure environment**
5. (Optional) Add environment secrets specific to staging
6. Click **Save protection rules**

### Create Production Environment

1. Click **New environment**
2. Name: `production`
3. Click **Configure environment**
4. **Enable Required reviewers** (recommended)
   - Check **Required reviewers**
   - Add 1-2 reviewers who must approve production deployments
5. (Optional) **Wait timer**: Add delay before deployment
6. (Optional) **Deployment branches**: Limit to `main` branch only
7. Click **Save protection rules**

---

## 📂 Step 4: Verify Workflow File

The workflow file is already in your repository:
- File: `.github/workflows/deploy.yml`
- Location: Root of repository → `.github/workflows/` directory

### Workflow Overview

```yaml
Triggers:
  - Push to 'main' → Production deployment (with approval)
  - Push to 'develop' → Staging deployment (automatic)
  - Pull requests → Tests only
  - Manual dispatch → Deploy to selected environment

Jobs:
  1. Pre-deployment checks
  2. Build and test
  3. Deploy to staging (auto on develop)
  4. Deploy to production (manual on main)
  5. Post-deployment monitoring
```

### Check Workflow Status

```bash
# If you haven't pushed the workflow yet
git add .github/workflows/deploy.yml
git commit -m "Add GitHub Actions deployment workflow"
git push origin main
```

---

## ✅ Step 5: Enable GitHub Actions

1. Go to **Actions** tab in your repository
2. If prompted, click **I understand my workflows, go ahead and enable them**
3. You should see the **EDMS Deployment Pipeline** workflow

---

## 🧪 Step 6: Test the Setup

### Test 1: Staging Deployment

```bash
# Create or switch to develop branch
git checkout -b develop

# Make a small change (or create test file)
echo "# Test deployment" >> TEST_DEPLOY.md
git add TEST_DEPLOY.md
git commit -m "Test staging deployment"

# Push to develop → triggers staging deployment
git push origin develop
```

**What happens:**
1. GitHub Actions runs pre-deployment checks
2. Runs backend and frontend tests
3. Creates deployment package
4. Automatically deploys to staging
5. Runs post-deployment validation
6. Monitors health for 5 minutes

**Monitor Progress:**
- Go to **Actions** tab
- Click on the running workflow
- Watch each job execute in real-time

### Test 2: Production Deployment (Dry Run)

```bash
# Switch to main branch
git checkout main
git merge develop
git push origin main
```

**What happens:**
1. Runs all checks and tests
2. Creates deployment package
3. **Waits for manual approval** (if reviewers configured)
4. After approval, deploys to production
5. Runs validation and monitoring
6. Rolls back automatically if issues detected

**Approve Deployment:**
1. Go to **Actions** tab
2. Click on the running workflow
3. Click **Review deployments** button
4. Select **production** environment
5. Click **Approve and deploy**

---

## 📊 Step 7: Verify Deployment

### Check Staging Deployment

```bash
# SSH to staging server
ssh user@staging-server.com

# Check deployment
cd /opt/edms-production-*
ls -la

# Run health check
./scripts/health-check.sh
```

### Check Workflow Artifacts

1. Go to **Actions** tab
2. Click on completed workflow
3. Scroll down to **Artifacts** section
4. Download:
   - Deployment package
   - Pre-deployment report
   - Post-deployment report
   - Health report (HTML)

---

## 🔄 Step 8: Regular Usage

### Deploy to Staging

```bash
# Work on develop branch
git checkout develop

# Make changes
git add .
git commit -m "Feature: Add new functionality"
git push origin develop

# Automatic deployment to staging starts
```

### Deploy to Production

```bash
# Merge to main
git checkout main
git merge develop
git push origin main

# Go to GitHub Actions
# Approve deployment when ready
```

### Manual Deployment

1. Go to **Actions** tab
2. Select **EDMS Deployment Pipeline**
3. Click **Run workflow** (top right)
4. Select branch and environment
5. Click **Run workflow**

---

## 🔍 Monitoring & Troubleshooting

### View Deployment Logs

1. **Actions** tab → Click workflow run
2. Click on any job (e.g., "Deploy to Production")
3. View real-time logs

### Check Health Reports

1. **Actions** tab → Completed workflow
2. **Artifacts** section
3. Download `production-health-report.html`
4. Open in browser

### Common Issues

#### SSH Connection Fails

**Symptom:** "Permission denied (publickey)"

**Solution:**
```bash
# Verify key format
ssh-keygen -y -f ~/.ssh/github_staging_key

# Test manually
ssh -i ~/.ssh/github_staging_key -v user@staging-server.com

# Check secret is correct format
# Must include:
# -----BEGIN OPENSSH PRIVATE KEY-----
# ...
# -----END OPENSSH PRIVATE KEY-----
```

#### Workflow Doesn't Trigger

**Check:**
- Is workflow file in `.github/workflows/` directory?
- Is Actions enabled in repository settings?
- Are you pushing to correct branch (develop/main)?
- Check workflow syntax: Actions → Workflow → 3 dots → View workflow file

#### Deployment Fails

**Check logs:**
1. Actions → Failed workflow
2. Click red X on failed job
3. Expand failed step
4. Review error message

**Common fixes:**
- Verify server is accessible
- Check SSH keys are correct
- Ensure Docker is running on server
- Verify environment variables

---

## 📋 Quick Reference

### Secrets Required

| Secret Name | Value Example | Purpose |
|-------------|---------------|---------|
| STAGING_SSH_KEY | `-----BEGIN OPENSSH...` | SSH private key for staging |
| STAGING_HOST | `staging.example.com` | Staging server hostname |
| STAGING_USER | `deploy` | SSH username for staging |
| PRODUCTION_SSH_KEY | `-----BEGIN OPENSSH...` | SSH private key for production |
| PRODUCTION_HOST | `prod.example.com` | Production server hostname |
| PRODUCTION_USER | `deploy` | SSH username for production |

### Branch → Environment Mapping

| Branch | Environment | Deployment |
|--------|-------------|------------|
| `develop` | Staging | Automatic |
| `main` | Production | Manual approval |
| Pull Request | None | Tests only |

### Workflow Commands

```bash
# Trigger staging deployment
git push origin develop

# Trigger production deployment
git push origin main
# Then approve in Actions UI

# Manual deployment
# Actions → Run workflow → Select environment
```

---

## 🎯 Verification Checklist

After setup, verify:

- [ ] All 6 secrets added to GitHub
- [ ] Staging environment created
- [ ] Production environment created with reviewers
- [ ] Workflow file exists (`.github/workflows/deploy.yml`)
- [ ] Actions enabled in repository
- [ ] SSH access to servers works
- [ ] Test deployment to staging succeeded
- [ ] Artifacts generated (packages, reports)
- [ ] Health checks passed
- [ ] Can access deployed application

---

## 🚀 You're Ready!

Your GitHub Actions CI/CD is now set up! 

### What Happens Now

**On every push to develop:**
- ✅ Automated tests run
- ✅ Package is created
- ✅ Deploys to staging automatically
- ✅ Health monitoring for 5 minutes
- ✅ Rollback if issues detected

**On every push to main:**
- ✅ All checks and tests run
- ✅ Waits for manual approval
- ✅ Deploys to production after approval
- ✅ Extended monitoring and validation
- ✅ Automatic rollback on failure

---

## 📞 Need Help?

### Documentation
- GitHub Actions docs: https://docs.github.com/actions
- Workflow syntax: https://docs.github.com/actions/reference
- Secrets: https://docs.github.com/actions/security-guides

### Project Documentation
- `CI_CD_INTEGRATION_GUIDE.md` - Complete CI/CD guide
- `AUTOMATION_SCRIPTS_GUIDE.md` - Automation scripts
- `DEPLOYMENT_QUICK_REFERENCE.md` - Quick commands

### Troubleshooting
- Check Actions logs for errors
- Test SSH connections manually
- Verify secrets are correctly formatted
- Review deployment reports in artifacts

---

**Setup Date**: December 24, 2024  
**Status**: Ready for Production ✅
