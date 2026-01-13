# Git Workflow - Proper Branch Strategy for Production

## 🎯 You're Right - We Should NOT Deploy from Develop to Production!

**Current situation**: Deploying from `develop` branch to production  
**Problem**: `develop` branch may have untested/unstable code  
**Solution**: Use proper Git branching strategy with `main/master` for production

---

## 📋 Proper Git Workflow

### Standard Branch Strategy:

```
main/master    →  Production-ready code (stable, tested)
    ↑
develop        →  Integration branch (tested features)
    ↑
feature/*      →  New features (work in progress)
hotfix/*       →  Emergency fixes for production
release/*      →  Release preparation
```

### Deployment Strategy:

| Environment | Branch | Purpose |
|-------------|--------|---------|
| **Development** | `develop` or `feature/*` | Active development |
| **Staging** | `develop` | Testing integrated features |
| **Production** | `main` or `master` | Stable, production-ready code |

---

## 🚀 What We Should Do

### Option 1: Create Main Branch and Deploy from It (Recommended)

This is the proper approach for production deployments.

#### Step 1: Check Current Branch Status

```bash
# Check if main/master branch exists
git branch -a | grep -E "main|master"
```

#### Step 2: Create Main Branch (if it doesn't exist)

```bash
# If no main branch exists, create it from develop
git checkout develop
git pull origin develop

# Create main branch
git checkout -b main

# Push to GitHub
git push -u origin main
```

#### Step 3: Set Main as Default Branch on GitHub

1. Go to: `https://github.com/jinkaiteo/edms/settings/branches`
2. Change default branch from `develop` to `main`
3. This makes `main` the production branch

#### Step 4: Update Production to Use Main Branch

```bash
# SSH to production server
ssh lims@172.28.1.149

# Navigate to production
cd /home/lims/edms-production

# Switch to main branch
git fetch origin
git checkout main
git pull origin main

# Verify you're on main
git branch
git log -3 --oneline

# Rebuild and restart (to ensure using main branch code)
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml build --no-cache
docker compose -f docker-compose.prod.yml up -d
```

---

### Option 2: Use Existing Master Branch

If your repository already has a `master` branch:

```bash
# Merge develop into master
git checkout master
git pull origin master
git merge develop
git push origin master

# Then update production server
ssh lims@172.28.1.149
cd /home/lims/edms-production
git fetch origin
git checkout master
git pull origin master
docker compose -f docker-compose.prod.yml restart
```

---

### Option 3: Use Tags/Releases for Production

Most professional approach - use version tags:

```bash
# Create a release tag from develop
git checkout develop
git pull origin develop

# Tag the release
git tag -a v1.0.0 -m "Release version 1.0.0 - Frontend authentication fix"
git push origin v1.0.0

# On production server, checkout the tag
ssh lims@172.28.1.149
cd /home/lims/edms-production
git fetch --tags
git checkout v1.0.0
docker compose -f docker-compose.prod.yml restart
```

---

## 📊 Recommended Git Workflow Going Forward

### For New Features:

```bash
# 1. Create feature branch from develop
git checkout develop
git pull origin develop
git checkout -b feature/new-feature-name

# 2. Make changes and commit
git add .
git commit -m "feat: Add new feature"

# 3. Push to GitHub
git push origin feature/new-feature-name

# 4. Create Pull Request to develop (via GitHub)

# 5. After review and merge, test on staging
# Staging pulls from develop

# 6. When ready for production, merge develop → main
git checkout main
git pull origin main
git merge develop
git push origin main

# 7. Production pulls from main
```

---

## 🎯 Immediate Action Plan

### Step 1: Create Proper Branch Structure

```bash
# On your local machine
cd /path/to/edms

# Ensure develop is up to date
git checkout develop
git pull origin develop

# Create main branch from current develop (since it's working)
git checkout -b main
git push -u origin main

# Verify branches
git branch -a
```

### Step 2: Update Production Server

```bash
# SSH to production
ssh lims@172.28.1.149

# Switch production to main branch
cd /home/lims/edms-production
git fetch origin
git branch -a  # Should now see origin/main
git checkout main
git pull origin main

# Verify correct branch
git branch
# Should show: * main

# Restart to ensure using correct code
docker compose -f docker-compose.prod.yml restart
```

### Step 3: Update Staging Server (Keep on Develop)

```bash
# SSH to staging
ssh lims@172.28.1.148

# Verify staging is on develop
cd /home/lims/edms-staging
git branch
# Should show: * develop

# This is correct for staging
```

### Step 4: Update Deployment Scripts

Edit `deploy-interactive.sh` to use correct branches:

```bash
nano deploy-interactive.sh
```

Update the branch selection logic:

```bash
# Around line 250
collect_configuration() {
    # ...
    
    if [ "$DEPLOY_TYPE" = "production" ]; then
        BRANCH=${BRANCH:-main}  # Changed from develop
    elif [ "$DEPLOY_TYPE" = "staging" ]; then
        BRANCH=${BRANCH:-develop}
    else
        BRANCH=${BRANCH:-develop}
    fi
}
```

---

## 📋 Final Branch Configuration

After setup:

| Server | Environment | Branch | Purpose |
|--------|-------------|--------|---------|
| **172.28.1.148** | Staging | `develop` | Test new features |
| **172.28.1.149** | Production | `main` | Stable releases |
| **Local** | Development | `feature/*` or `develop` | Active development |

---

## 🔄 Updated Deployment Workflow

### For Staging (Testing):
```bash
# 1. Merge feature to develop
git checkout develop
git merge feature/my-feature
git push origin develop

# 2. Deploy to staging
ssh lims@172.28.1.148
cd /home/lims/edms-staging
git pull origin develop
docker compose -f docker-compose.prod.yml restart
```

### For Production (Release):
```bash
# 1. Test on staging first
# 2. Merge develop to main
git checkout main
git merge develop
git push origin main

# 3. Deploy to production
ssh lims@172.28.1.149
cd /home/lims/edms-production
git pull origin main
docker compose -f docker-compose.prod.yml restart
```

---

## ✅ Benefits of Proper Branch Strategy

### 1. **Stability**
- Production always runs tested code
- Develop can have experimental features
- Easy rollback if issues occur

### 2. **Safety**
- Accidental commits to develop don't affect production
- Production deploys are intentional (merge to main)
- Clear separation of concerns

### 3. **Traceability**
- Know exactly what version is in production
- Can use tags for version tracking
- Easy to see what changed between deployments

### 4. **Compliance**
- Audit trail of what's in production
- Change control process
- Meets regulatory requirements (21 CFR Part 11)

---

## 🎯 Quick Command Sequence

Execute these now to fix the branch situation:

```bash
# === On Local Machine ===

# Create main branch from develop
git checkout develop
git pull origin develop
git checkout -b main
git push -u origin main

# === On Production Server ===

# Switch to main branch
ssh lims@172.28.1.149
cd /home/lims/edms-production
git fetch origin
git checkout main
git pull origin main
docker compose -f docker-compose.prod.yml restart
exit

# === Verify ===

# Check staging is on develop
ssh lims@172.28.1.148
cd /home/lims/edms-staging
git branch  # Should show: * develop
exit

# Check production is on main
ssh lims@172.28.1.149
cd /home/lims/edms-production
git branch  # Should show: * main
exit
```

---

## 📚 GitHub Repository Settings

### Set Main as Default Branch

1. Go to: `https://github.com/jinkaiteo/edms/settings/branches`
2. Default branch: Change to `main`
3. Save changes

### Branch Protection (Recommended)

Protect the `main` branch:

1. Settings → Branches → Add rule
2. Branch name pattern: `main`
3. Enable:
   - ✅ Require pull request reviews before merging
   - ✅ Require status checks to pass
   - ✅ Include administrators (optional)

This prevents direct pushes to production branch.

---

## 🔍 Verify Current Setup

```bash
# Check what branch each server is using
ssh lims@172.28.1.148 "cd /home/lims/edms-staging && git branch"
ssh lims@172.28.1.149 "cd /home/lims/edms-production && git branch"

# Expected output:
# Staging: * develop
# Production: * main
```

---

## 📝 Summary

**Why this matters:**
- ✅ Production stability - only deploy tested code
- ✅ Safety - experimental features don't affect production
- ✅ Compliance - audit trail and change control
- ✅ Best practice - industry standard workflow

**Current state (incorrect):**
- ❌ Both staging and production using `develop`

**Desired state (correct):**
- ✅ Staging uses `develop` (for testing)
- ✅ Production uses `main` (for stable releases)

**Action needed:**
1. Create `main` branch
2. Update production to use `main`
3. Keep staging on `develop`
4. Update deployment scripts

---

Would you like me to help you execute these changes now? 🚀
