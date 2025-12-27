# GitHub Actions Setup - Quick Start

**5-minute setup guide for GitHub Actions CI/CD**

---

## 🚀 Quick Setup (Copy & Paste)

### 1. Generate SSH Keys

```bash
# Generate staging key
ssh-keygen -t ed25519 -C "github-staging" -f ~/.ssh/github_staging_key -N ""

# Generate production key
ssh-keygen -t ed25519 -C "github-production" -f ~/.ssh/github_production_key -N ""
```

### 2. Add Keys to Servers

```bash
# Add to staging
ssh-copy-id -i ~/.ssh/github_staging_key.pub user@staging-server.com

# Add to production
ssh-copy-id -i ~/.ssh/github_production_key.pub user@production-server.com
```

### 3. Copy Private Keys for GitHub

```bash
# Staging key (copy entire output)
cat ~/.ssh/github_staging_key

# Production key (copy entire output)
cat ~/.ssh/github_production_key
```

### 4. Add to GitHub Secrets

Go to: **Repository → Settings → Secrets and variables → Actions**

Add these 6 secrets:

| Name | Value | How to Get |
|------|-------|------------|
| `STAGING_SSH_KEY` | Entire private key | Output from step 3 |
| `STAGING_HOST` | `staging.example.com` | Your staging server |
| `STAGING_USER` | `deploy` | Your SSH username |
| `PRODUCTION_SSH_KEY` | Entire private key | Output from step 3 |
| `PRODUCTION_HOST` | `prod.example.com` | Your production server |
| `PRODUCTION_USER` | `deploy` | Your SSH username |

### 5. Create Environments

Go to: **Repository → Settings → Environments**

**Create two environments:**

1. **staging** (no protection needed)
2. **production** (add required reviewers)

### 6. Test Deployment

```bash
# Deploy to staging
git checkout -b develop
git push origin develop

# Watch progress
# Go to: Actions tab → View workflow
```

---

## ✅ Verification

After setup, verify:
- [ ] 6 secrets added
- [ ] 2 environments created
- [ ] Workflow appears in Actions tab
- [ ] Test deployment to staging works

---

## 📚 Full Documentation

- **GITHUB_ACTIONS_SETUP.md** - Detailed step-by-step guide
- **CI_CD_INTEGRATION_GUIDE.md** - Complete CI/CD documentation

---

## 🆘 Need Help?

Run the interactive setup wizard:
```bash
./scripts/setup-github-actions.sh
```

Or check: **GITHUB_ACTIONS_SETUP.md** for detailed instructions.
