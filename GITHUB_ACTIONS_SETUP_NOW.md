# GitHub Actions Setup - Step by Step

**Follow these steps exactly to set up GitHub Actions with staging + production**

---

## 📋 What You Need

- [ ] Access to staging server (SSH)
- [ ] Access to production server (SSH)
- [ ] GitHub repository admin access
- [ ] 10 minutes of time

---

## 🔑 STEP 1: Generate SSH Keys (2 minutes)

Open your terminal and run these commands:

### Generate Staging Key
```bash
ssh-keygen -t ed25519 -C "github-staging-deploy" -f ~/.ssh/github_staging_key -N ""
```

**Output:** You should see:
```
Your identification has been saved in ~/.ssh/github_staging_key
Your public key has been saved in ~/.ssh/github_staging_key.pub
```

### Generate Production Key
```bash
ssh-keygen -t ed25519 -C "github-production-deploy" -f ~/.ssh/github_production_key -N ""
```

**Output:** You should see:
```
Your identification has been saved in ~/.ssh/github_production_key
Your public key has been saved in ~/.ssh/github_production_key.pub
```

✅ **Check:** You should now have 4 files:
```bash
ls -la ~/.ssh/github_*
# Should show:
# github_staging_key
# github_staging_key.pub
# github_production_key
# github_production_key.pub
```

---

## 🌐 STEP 2: Add Keys to Servers (3 minutes)

### Add Staging Key to Staging Server

Replace `user@staging-server.com` with your actual staging server details:

```bash
ssh-copy-id -i ~/.ssh/github_staging_key.pub user@staging-server.com
```

**You'll be asked for your password.** Enter it.

**Output:** You should see:
```
Number of key(s) added: 1
```

**Test the connection:**
```bash
ssh -i ~/.ssh/github_staging_key user@staging-server.com "echo 'Staging connection OK'"
```

**Expected output:** `Staging connection OK`

### Add Production Key to Production Server

Replace `user@production-server.com` with your actual production server details:

```bash
ssh-copy-id -i ~/.ssh/github_production_key.pub user@production-server.com
```

**You'll be asked for your password.** Enter it.

**Test the connection:**
```bash
ssh -i ~/.ssh/github_production_key user@production-server.com "echo 'Production connection OK'"
```

**Expected output:** `Production connection OK`

✅ **Check:** Both connections should work without password

---

## 🔐 STEP 3: Get Private Keys for GitHub (1 minute)

### Get Staging Private Key

```bash
cat ~/.ssh/github_staging_key
```

**Copy the ENTIRE output** including the BEGIN and END lines. It looks like:
```
-----BEGIN OPENSSH PRIVATE KEY-----
b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAAAMwAAAAtzc2gtZW
... (many more lines) ...
-----END OPENSSH PRIVATE KEY-----
```

**Save this somewhere temporarily** - you'll need it in the next step.

### Get Production Private Key

```bash
cat ~/.ssh/github_production_key
```

**Copy the ENTIRE output** including the BEGIN and END lines.

**Save this somewhere temporarily** - you'll need it in the next step.

✅ **Check:** You have both private keys copied

---

## 🔒 STEP 4: Add Secrets to GitHub (3 minutes)

### Navigate to GitHub Secrets

1. Go to your GitHub repository
2. Click **Settings** (top menu bar)
3. Click **Secrets and variables** (left sidebar)
4. Click **Actions**
5. Click **New repository secret** button

### Add Secret 1: STAGING_SSH_KEY

- Click **New repository secret**
- Name: `STAGING_SSH_KEY`
- Value: **Paste the ENTIRE staging private key** you copied earlier
- Click **Add secret**

### Add Secret 2: STAGING_HOST

- Click **New repository secret**
- Name: `STAGING_HOST`
- Value: `staging-server.com` (your staging server hostname or IP address)
- Click **Add secret**

### Add Secret 3: STAGING_USER

- Click **New repository secret**
- Name: `STAGING_USER`
- Value: `deploy` (the SSH username you use to connect to staging)
- Click **Add secret**

### Add Secret 4: PRODUCTION_SSH_KEY

- Click **New repository secret**
- Name: `PRODUCTION_SSH_KEY`
- Value: **Paste the ENTIRE production private key** you copied earlier
- Click **Add secret**

### Add Secret 5: PRODUCTION_HOST

- Click **New repository secret**
- Name: `PRODUCTION_HOST`
- Value: `production-server.com` (your production server hostname or IP)
- Click **Add secret**

### Add Secret 6: PRODUCTION_USER

- Click **New repository secret**
- Name: `PRODUCTION_USER`
- Value: `deploy` (the SSH username you use to connect to production)
- Click **Add secret**

✅ **Check:** You should see 6 secrets in the list:
- STAGING_SSH_KEY
- STAGING_HOST
- STAGING_USER
- PRODUCTION_SSH_KEY
- PRODUCTION_HOST
- PRODUCTION_USER

---

## 🌍 STEP 5: Create Environments (2 minutes)

### Navigate to Environments

1. Still in **Settings**
2. Click **Environments** (left sidebar)
3. Click **New environment**

### Create Staging Environment

1. Name: `staging`
2. Click **Configure environment**
3. **Don't add any protection rules** (staging should auto-deploy)
4. Click outside the modal to save

### Create Production Environment

1. Click **New environment** again
2. Name: `production`
3. Click **Configure environment**
4. ✅ Check **Required reviewers**
5. In the search box, type your GitHub username
6. Select yourself (or team members who should approve)
7. **Optional:** Add "Wait timer" if you want a delay
8. **Optional:** Check "Deployment branches" and select "Selected branches" → add `main`
9. Click **Save protection rules**

✅ **Check:** You should see 2 environments:
- staging (no protection)
- production (with reviewers)

---

## ✅ STEP 6: Enable GitHub Actions (30 seconds)

1. Go to the **Actions** tab (top of repository)
2. If you see "Get started with GitHub Actions", click **I understand my workflows, go ahead and enable them**
3. You should see **EDMS Deployment Pipeline** workflow

✅ **Check:** Actions tab is accessible and shows workflows

---

## 🧪 STEP 7: Test Deployment (5 minutes)

### Test Staging Deployment

1. Make sure you have a `develop` branch:
   ```bash
   git checkout -b develop
   git push origin develop
   ```

2. Go to **Actions** tab in GitHub

3. You should see a workflow running

4. Click on it to watch progress

5. It will:
   - Run pre-deployment checks
   - Run tests
   - Create package
   - Deploy to staging automatically
   - Run health checks

**Expected:** Green checkmarks for all steps

### Test Production Deployment (Approval Flow)

1. Merge develop to main:
   ```bash
   git checkout main
   git merge develop
   git push origin main
   ```

2. Go to **Actions** tab

3. Workflow will run and pause at "Deploy to Production"

4. You'll see **Review deployments** button

5. Click it, select **production**, click **Approve and deploy**

6. Deployment will complete

**Expected:** Successful deployment with all checks passing

---

## ✅ Verification Checklist

After setup, verify:

- [ ] 6 secrets added to GitHub
- [ ] 2 environments created (staging with no protection, production with reviewers)
- [ ] Actions enabled
- [ ] Workflow file exists (`.github/workflows/deploy.yml`)
- [ ] SSH connections work to both servers
- [ ] Test deployment to staging succeeded
- [ ] Can see workflow in Actions tab

---

## 📊 What Happens After Setup

### When you push to `develop` branch:
```
1. Pre-deployment checks run
2. Backend tests run
3. Frontend tests run
4. Package created
5. ✅ Automatically deploys to STAGING
6. Post-deployment validation
7. 5-minute health monitoring
8. Artifacts saved (reports, packages)
```

### When you push to `main` branch:
```
1. Pre-deployment checks run
2. Backend tests run
3. Frontend tests run
4. Package created
5. ⏸️  WAITS for your approval
6. You click "Review deployments" → "Approve"
7. ✅ Deploys to PRODUCTION
8. Post-deployment validation
9. Extended monitoring
10. Automatic rollback if failure
11. Artifacts saved
```

---

## 🆘 Troubleshooting

### SSH Connection Fails

**Problem:** `Permission denied (publickey)`

**Solution:**
```bash
# Verify key exists
ls -la ~/.ssh/github_staging_key

# Test connection manually
ssh -i ~/.ssh/github_staging_key -v user@server

# Check key format
ssh-keygen -y -f ~/.ssh/github_staging_key
```

### Secret is Wrong Format

**Problem:** Workflow fails with SSH errors

**Solution:**
- Make sure you copied the ENTIRE private key
- Must include `-----BEGIN OPENSSH PRIVATE KEY-----`
- Must include `-----END OPENSSH PRIVATE KEY-----`
- No extra spaces or characters

### Workflow Doesn't Trigger

**Problem:** Push doesn't start workflow

**Check:**
- Is Actions enabled?
- Is workflow file in `.github/workflows/deploy.yml`?
- Are you pushing to `develop` or `main` branch?
- Check Actions tab for error messages

### Can't Approve Deployment

**Problem:** No "Review deployments" button

**Check:**
- Production environment exists
- You're added as required reviewer
- Workflow reached "Deploy to Production" step
- You're logged into GitHub

---

## 🎉 Success!

When setup is complete, you'll have:

✅ Automated deployments to staging on push to `develop`  
✅ Manual approval deployments to production on push to `main`  
✅ Automatic testing before deployment  
✅ Health monitoring after deployment  
✅ Automatic rollback on failure  
✅ Reports and artifacts saved  

---

## 📞 Need Help?

### Commands Reference

```bash
# Check SSH keys exist
ls -la ~/.ssh/github_*

# Test staging connection
ssh -i ~/.ssh/github_staging_key user@staging "echo OK"

# Test production connection
ssh -i ~/.ssh/github_production_key user@production "echo OK"

# View private key (for GitHub secret)
cat ~/.ssh/github_staging_key
cat ~/.ssh/github_production_key
```

### Documentation

- This guide (step-by-step)
- `GITHUB_ACTIONS_SETUP.md` (detailed explanations)
- `CI_CD_INTEGRATION_GUIDE.md` (complete CI/CD guide)
- `.github/SETUP_INSTRUCTIONS.md` (quick reference)

---

## ✨ You're All Set!

After completing these steps:
- Push to `develop` → deploys to staging automatically
- Push to `main` → waits for approval → deploys to production

**Happy deploying! 🚀**
