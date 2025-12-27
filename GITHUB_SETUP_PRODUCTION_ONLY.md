# GitHub Actions Setup - Production Only (No Staging)

**Quick setup for production deployment without staging server**

---

## 🚀 Quick Setup (3 Steps)

### Step 1: Generate SSH Key

```bash
# Generate production deployment key
ssh-keygen -t ed25519 -C "github-production-deploy" -f ~/.ssh/github_production_key -N ""

# Add public key to your production server
ssh-copy-id -i ~/.ssh/github_production_key.pub user@your-server.com

# Test connection
ssh -i ~/.ssh/github_production_key user@your-server.com "echo 'Connection OK'"
```

### Step 2: Add GitHub Secrets

Go to: **Repository → Settings → Secrets and variables → Actions → New repository secret**

Add these **3 secrets**:

#### 1. PRODUCTION_SSH_KEY
```bash
# Copy the entire private key
cat ~/.ssh/github_production_key
```
- Name: `PRODUCTION_SSH_KEY`
- Value: Paste entire key output (including BEGIN/END lines)

#### 2. PRODUCTION_HOST
- Name: `PRODUCTION_HOST`
- Value: `your-server.com` (your server hostname or IP)

#### 3. PRODUCTION_USER
- Name: `PRODUCTION_USER`
- Value: `deploy` (your SSH username)

### Step 3: Choose Workflow File

You have **2 options**:

#### Option A: Production Only (Recommended for you)
```bash
# Use the simplified workflow
# File: .github/workflows/deploy-production-only.yml

# This workflow:
# - Deploys only to production
# - Requires manual approval
# - Runs tests before deployment
# - Automatic rollback on failure
```

**To use this:**
```bash
# Rename or disable the staging workflow
mv .github/workflows/deploy.yml .github/workflows/deploy-with-staging.yml.disabled

# Rename the production-only workflow
mv .github/workflows/deploy-production-only.yml .github/workflows/deploy.yml
```

#### Option B: Use Original (Test with PR)
```bash
# Keep .github/workflows/deploy.yml
# Test with pull requests (no staging deployment)
# Deploy to production from main branch
```

---

## 🌍 Step 4: Configure Environment

Create **production** environment with approval:

1. Go to **Settings → Environments**
2. Click **New environment**
3. Name: `production`
4. Click **Configure environment**
5. **Enable Required reviewers**
   - Check **Required reviewers**
   - Add yourself or team members (1-2 people)
6. **Optional**: Add deployment branches → Limit to `main` only
7. Click **Save protection rules**

---

## ✅ Step 5: Test Deployment

```bash
# Make a test change
echo "# Test deployment" >> TEST.md
git add TEST.md
git commit -m "Test: GitHub Actions deployment"

# Push to main (triggers production deployment)
git push origin main

# Go to Actions tab to approve deployment
# Repository → Actions → Click on running workflow
# Click "Review deployments" → Select "production" → Approve
```

---

## 📋 Simplified Workflow

### What Happens on Push to Main:

1. **Pre-Deployment Checks** (automatic)
   - Package creation
   - Integrity verification
   - Pre-deployment validation

2. **Tests** (automatic)
   - Backend tests
   - Frontend tests

3. **Deploy to Production** (waits for approval)
   - ⏸️ **Manual approval required**
   - Creates backup
   - Deploys to server
   - Post-deployment validation
   - Health checks

4. **Monitoring** (automatic)
   - 5-minute health monitoring
   - Generate reports
   - Alert on failure

5. **Auto-Rollback** (if deployment fails)
   - Rollback to previous version
   - Verify rollback
   - Alert team

---

## 🔄 Alternative: Use Pull Requests for Testing

If you want to test before deploying:

```bash
# Create feature branch
git checkout -b feature/new-feature

# Make changes and commit
git add .
git commit -m "Add new feature"

# Push and create PR
git push origin feature/new-feature

# On GitHub: Create Pull Request to main
# This will run tests WITHOUT deploying
# Merge PR when tests pass → triggers production deployment
```

---

## 📊 Comparison: With vs Without Staging

### Without Staging (Your Setup)

**Workflow:**
```
Feature Branch → PR (tests only) → Main → Production
```

**Pros:**
- ✅ Simpler setup
- ✅ Fewer servers to maintain
- ✅ Lower costs
- ✅ Direct to production

**Safety Measures:**
- ✅ Comprehensive tests before deployment
- ✅ Manual approval required
- ✅ Automatic backup
- ✅ Automatic rollback
- ✅ Post-deployment validation

### With Staging (Optional Future)

**Workflow:**
```
Feature Branch → Develop → Staging → Main → Production
```

**Pros:**
- ✅ Test in production-like environment
- ✅ QA validation on staging
- ✅ Lower risk

---

## 🛡️ Safety Without Staging

Your setup is still safe because:

1. **Pre-Deployment Validation**
   - 14 checks before deployment
   - Package integrity verification
   - System requirements check

2. **Automated Testing**
   - Backend unit tests
   - Frontend unit tests
   - Run on every push

3. **Manual Approval**
   - Required for production
   - 1-2 reviewers must approve
   - Time to review changes

4. **Automatic Backup**
   - Created before deployment
   - Can restore if needed

5. **Post-Deployment Validation**
   - 17 automated tests
   - Health checks
   - Immediate rollback if issues

6. **Monitoring**
   - 5-minute continuous monitoring
   - HTML reports
   - Alert on failure

---

## 🎯 Recommended Workflow

For production-only setup, use this workflow:

```bash
# Day-to-day development
git checkout -b feature/my-feature
# ... make changes ...
git commit -m "Implement feature"
git push origin feature/my-feature

# Create PR on GitHub (tests run, no deployment)
# Get code review
# Merge PR when approved

# Deployment happens automatically:
# 1. Tests run again
# 2. Package created
# 3. Waits for your approval
# 4. You approve in GitHub Actions
# 5. Deploys to production
# 6. Validates deployment
# 7. Monitors for 5 minutes
```

---

## 🆘 Troubleshooting

### "No staging server" Errors

If you see staging-related errors:
```bash
# Use the production-only workflow
mv .github/workflows/deploy.yml .github/workflows/deploy-staging.yml.disabled
mv .github/workflows/deploy-production-only.yml .github/workflows/deploy.yml
git add .github/workflows/
git commit -m "Use production-only workflow"
git push origin main
```

### SSH Connection Issues

```bash
# Test manually
ssh -i ~/.ssh/github_production_key user@your-server.com

# Check key format
ssh-keygen -y -f ~/.ssh/github_production_key

# Verify key is added to server
ssh user@your-server.com "cat ~/.ssh/authorized_keys"
```

---

## ✅ Verification Checklist

- [ ] SSH key generated
- [ ] Public key added to production server
- [ ] SSH connection tested
- [ ] 3 secrets added to GitHub (not 6)
- [ ] Production environment created
- [ ] Required reviewers configured
- [ ] Using production-only workflow
- [ ] Test deployment successful

---

## 📚 Documentation

- **This file**: Production-only setup
- **GITHUB_ACTIONS_SETUP.md**: Full setup with staging
- **CI_CD_INTEGRATION_GUIDE.md**: All platforms
- **scripts/setup-github-actions.sh**: Interactive wizard (will skip staging)

---

## 🚀 Quick Commands

```bash
# Generate key
ssh-keygen -t ed25519 -f ~/.ssh/github_production_key

# Add to server
ssh-copy-id -i ~/.ssh/github_production_key.pub user@server

# Get private key for GitHub
cat ~/.ssh/github_production_key

# Test deployment
git push origin main
# Then approve in Actions tab
```

---

**Setup Time**: ~3 minutes  
**Servers Required**: 1 (production only)  
**Secrets Required**: 3 (not 6)  
**Status**: ✅ Ready to use
