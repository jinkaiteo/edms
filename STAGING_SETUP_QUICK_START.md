# Quick Start: GitHub Actions with Staging Server

**Now that you have a staging server, use the full workflow!**

---

## ✅ What You Have

You already have the **complete GitHub Actions workflow** configured with staging support:
- File: `.github/workflows/deploy.yml` ✅ Already in your repo!

---

## 🚀 Quick Setup (5 Steps)

### Step 1: Generate SSH Keys (2 keys)

```bash
# Staging key
ssh-keygen -t ed25519 -C "github-staging" -f ~/.ssh/github_staging_key -N ""

# Production key
ssh-keygen -t ed25519 -C "github-production" -f ~/.ssh/github_production_key -N ""
```

### Step 2: Add Keys to Servers

```bash
# Add to staging
ssh-copy-id -i ~/.ssh/github_staging_key.pub user@staging-server.com

# Add to production
ssh-copy-id -i ~/.ssh/github_production_key.pub user@production-server.com

# Test connections
ssh -i ~/.ssh/github_staging_key user@staging-server.com "echo 'Staging OK'"
ssh -i ~/.ssh/github_production_key user@production-server.com "echo 'Production OK'"
```

### Step 3: Add GitHub Secrets (6 total)

Go to: **Repository → Settings → Secrets and variables → Actions**

**Staging Secrets (3):**
```bash
# Get staging private key
cat ~/.ssh/github_staging_key
```
- Name: `STAGING_SSH_KEY`, Value: (entire key output)
- Name: `STAGING_HOST`, Value: `staging-server.com`
- Name: `STAGING_USER`, Value: `deploy` (your username)

**Production Secrets (3):**
```bash
# Get production private key
cat ~/.ssh/github_production_key
```
- Name: `PRODUCTION_SSH_KEY`, Value: (entire key output)
- Name: `PRODUCTION_HOST`, Value: `production-server.com`
- Name: `PRODUCTION_USER`, Value: `deploy` (your username)

### Step 4: Create Environments (2)

Go to: **Repository → Settings → Environments**

**Create "staging":**
- Click "New environment"
- Name: `staging`
- No protection rules needed
- Click "Configure environment" → Save

**Create "production":**
- Click "New environment"
- Name: `production`
- ✅ Enable "Required reviewers"
- Add yourself or team members (1-2 people)
- Click "Save protection rules"

### Step 5: Remove Production-Only Workflow

```bash
# Backup the production-only workflow
mv .github/workflows/deploy-production-only.yml \
   .github/workflows/deploy-production-only.yml.backup

# The main deploy.yml already supports staging!
```

---

## 🎯 How It Works

### Automatic Staging Deployment
```bash
# Push to develop branch
git checkout -b develop
git push origin develop

# GitHub Actions will:
# 1. Run tests
# 2. Create package
# 3. Deploy to staging automatically
# 4. Run health checks
# 5. Monitor for 5 minutes
```

### Manual Production Deployment
```bash
# After testing on staging, merge to main
git checkout main
git merge develop
git push origin main

# GitHub Actions will:
# 1. Run all tests
# 2. Create package
# 3. ⏸️  Wait for your approval
# 4. Deploy to production after approval
# 5. Extended monitoring and validation
```

---

## 📊 Workflow Overview

```
┌─────────────────────────────────────────────────────────┐
│                                                         │
│  Feature Branch                                         │
│       ↓                                                 │
│  Push to develop                                        │
│       ↓                                                 │
│  ┌─────────────────────────────────────┐               │
│  │  Staging Deployment (Automatic)     │               │
│  │  - Tests run                        │               │
│  │  - Deploy to staging                │               │
│  │  - Health checks                    │               │
│  └─────────────────────────────────────┘               │
│       ↓                                                 │
│  Test on staging server                                │
│       ↓                                                 │
│  Merge to main                                          │
│       ↓                                                 │
│  ┌─────────────────────────────────────┐               │
│  │  Production Deployment (Manual)     │               │
│  │  - All tests run                    │               │
│  │  - Manual approval required         │               │
│  │  - Deploy to production             │               │
│  │  - Extended validation              │               │
│  └─────────────────────────────────────┘               │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## ✅ Verification

After setup, verify:
- [ ] 6 secrets added to GitHub
- [ ] 2 environments created (staging, production)
- [ ] SSH connections tested to both servers
- [ ] deploy.yml is the active workflow
- [ ] deploy-production-only.yml is removed/disabled

Test:
```bash
git push origin develop
# Check Actions tab - should deploy to staging
```

---

## 🎓 Alternative: Use Interactive Wizard

Instead of manual setup, use the wizard:
```bash
./scripts/setup-github-actions.sh
```

This will:
- Generate both keys
- Add keys to both servers
- Test both connections
- Show you all 6 secrets
- Guide you through environment setup

---

## 📚 Full Documentation

- **GITHUB_ACTIONS_SETUP.md** - Complete step-by-step guide
- **CI_CD_INTEGRATION_GUIDE.md** - All platforms
- **.github/SETUP_INSTRUCTIONS.md** - Quick reference

---

## 🎉 Benefits

With staging, you get:
✅ Test in production-like environment  
✅ Catch bugs before production  
✅ QA validation opportunity  
✅ Lower production risk  
✅ Automatic staging deployments  
✅ Manual production approval  
✅ Complete CI/CD pipeline  

---

**Ready?** Run the wizard:
```bash
./scripts/setup-github-actions.sh
```

Or follow the steps above for manual setup!
