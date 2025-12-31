# HAProxy Deployment Options

## 🤔 Do You Need to Commit & Pull?

**Short Answer:** You have **two options** - both work!

---

## ✅ **Option 1: Direct Deployment (Faster)**

Deploy directly **without** committing to GitHub.

### Files Status:
All HAProxy files are currently **untracked** (not in git):
```
?? infrastructure/haproxy/haproxy.cfg
?? scripts/setup-haproxy-staging.sh
?? scripts/update-docker-for-haproxy.sh
?? scripts/verify-haproxy-setup.sh
```

### How to Deploy:

**On your local machine:**
```bash
# Copy files directly to staging server
scp -r infrastructure/haproxy lims@172.28.1.148:/home/lims/edms-staging/infrastructure/
scp scripts/setup-haproxy-staging.sh lims@172.28.1.148:/home/lims/edms-staging/scripts/
scp scripts/update-docker-for-haproxy.sh lims@172.28.1.148:/home/lims/edms-staging/scripts/
scp scripts/verify-haproxy-setup.sh lims@172.28.1.148:/home/lims/edms-staging/scripts/
```

**Or use rsync (recommended):**
```bash
rsync -avz --progress \
  infrastructure/haproxy \
  scripts/setup-haproxy-staging.sh \
  scripts/update-docker-for-haproxy.sh \
  scripts/verify-haproxy-setup.sh \
  lims@172.28.1.148:/home/lims/edms-staging/
```

**Then on staging server:**
```bash
ssh lims@172.28.1.148
cd /home/lims/edms-staging

# Make scripts executable
chmod +x scripts/setup-haproxy-staging.sh
chmod +x scripts/update-docker-for-haproxy.sh
chmod +x scripts/verify-haproxy-setup.sh

# Run setup
sudo bash scripts/setup-haproxy-staging.sh
bash scripts/update-docker-for-haproxy.sh
bash scripts/verify-haproxy-setup.sh
```

**Pros:**
- ⚡ Faster (no git operations)
- 🔧 Test immediately
- 🔄 Easy to iterate if changes needed

**Cons:**
- 📝 Not version controlled (yet)
- 👥 Team doesn't have access (yet)

---

## ✅ **Option 2: Git Commit & Pull (Recommended for Production)**

Commit to GitHub first, then pull on staging server.

### How to Deploy:

**On your local machine:**
```bash
# Stage HAProxy files
git add infrastructure/haproxy/
git add scripts/setup-haproxy-staging.sh
git add scripts/update-docker-for-haproxy.sh
git add scripts/verify-haproxy-setup.sh

# Also add documentation
git add HAPROXY_PRODUCTION_SETUP_GUIDE.md
git add QUICK_START_HAPROXY.md

# Commit
git commit -m "feat: Add HAProxy production setup for staging server

- Add HAProxy configuration for single port 80 entry point
- Add automated installation script (setup-haproxy-staging.sh)
- Add Docker configuration update script (update-docker-for-haproxy.sh)
- Add verification script (verify-haproxy-setup.sh)
- Fix login issue by changing REACT_APP_API_URL to relative path
- Add comprehensive setup documentation

Fixes login issue on staging server (172.28.1.148)
"

# Push to GitHub
git push origin main  # or your branch name
```

**On staging server:**
```bash
ssh lims@172.28.1.148
cd /home/lims/edms-staging

# Pull latest changes
git pull origin main  # or your branch name

# Make scripts executable (if needed)
chmod +x scripts/setup-haproxy-staging.sh
chmod +x scripts/update-docker-for-haproxy.sh
chmod +x scripts/verify-haproxy-setup.sh

# Run setup
sudo bash scripts/setup-haproxy-staging.sh
bash scripts/update-docker-for-haproxy.sh
bash scripts/verify-haproxy-setup.sh
```

**Pros:**
- 📝 Version controlled (audit trail)
- 👥 Team has access to changes
- 🔄 Easy to rollback if needed
- 📚 Documentation included

**Cons:**
- ⏱️ Takes a bit longer
- 🌐 Requires GitHub access

---

## 🎯 **My Recommendation**

### **For Testing/Validation:**
Use **Option 1** (Direct Deployment)
- Test the scripts quickly
- Verify everything works
- Make adjustments if needed

### **After Successful Test:**
Use **Option 2** (Git Commit & Pull)
- Commit the working solution
- Document the changes
- Share with team

---

## 📋 **Files to Commit (When Ready)**

### Essential Files:
```
infrastructure/haproxy/haproxy.cfg          # HAProxy configuration
scripts/setup-haproxy-staging.sh            # Installation script
scripts/update-docker-for-haproxy.sh        # Docker update script
scripts/verify-haproxy-setup.sh             # Verification script
```

### Documentation:
```
HAPROXY_PRODUCTION_SETUP_GUIDE.md          # Full guide
QUICK_START_HAPROXY.md                      # Quick reference
```

### Optional (Clean Up Later):
```
tmp_rovodev_architecture_explanation.md     # Temporary analysis
STAGING_LOGIN_ISSUE_ANALYSIS.md             # Temporary analysis
README_HAPROXY_SETUP.txt                    # Summary file
```

---

## 🚀 **Quick Start Commands**

### Option 1: Direct SCP
```bash
# From your local machine
scp -r infrastructure/haproxy scripts/setup-haproxy-staging.sh \
  scripts/update-docker-for-haproxy.sh scripts/verify-haproxy-setup.sh \
  lims@172.28.1.148:/home/lims/edms-staging/

# On staging server
ssh lims@172.28.1.148
cd /home/lims/edms-staging
chmod +x scripts/*.sh
sudo bash scripts/setup-haproxy-staging.sh
```

### Option 2: Git Method
```bash
# From your local machine
git add infrastructure/haproxy/ scripts/*haproxy*.sh *.md
git commit -m "feat: Add HAProxy production setup"
git push

# On staging server
ssh lims@172.28.1.148
cd /home/lims/edms-staging
git pull
sudo bash scripts/setup-haproxy-staging.sh
```

---

## ⚠️ **Important Notes**

### 1. Scripts Will Modify Files
The update script will modify:
- `docker-compose.prod.yml` (changes REACT_APP_API_URL)
- `.env` (adds/updates ALLOWED_HOSTS, CORS_ALLOWED_ORIGINS)

**Backups are created automatically** in `backups/haproxy_migration_TIMESTAMP/`

### 2. HAProxy Installation
The setup script will:
- Install HAProxy system package (needs sudo)
- Create `/etc/haproxy/haproxy.cfg`
- Configure firewall (if UFW is active)
- Start HAProxy as a system service

### 3. Docker Rebuild Required
The update script will:
- Rebuild frontend container (new REACT_APP_API_URL)
- Restart all services (brief downtime ~30 seconds)

---

## 🔄 **Rollback Plan**

If something goes wrong:

### Rollback HAProxy:
```bash
# Stop HAProxy
sudo systemctl stop haproxy

# Restore from backup (created by script)
sudo cp /etc/haproxy/haproxy.cfg.backup.TIMESTAMP /etc/haproxy/haproxy.cfg

# Or disable HAProxy
sudo systemctl disable haproxy
```

### Rollback Docker:
```bash
# Restore from backup
cp backups/haproxy_migration_TIMESTAMP/docker-compose.prod.yml .
cp backups/haproxy_migration_TIMESTAMP/.env .

# Rebuild and restart
docker compose -f docker-compose.prod.yml build frontend
docker compose -f docker-compose.prod.yml restart
```

---

## 📞 **Decision Helper**

**Choose Option 1 (Direct) if:**
- ✅ You want to test immediately
- ✅ You might need to make adjustments
- ✅ This is your first time deploying HAProxy
- ✅ You're the only one working on this

**Choose Option 2 (Git) if:**
- ✅ You've already tested and it works
- ✅ You want version control
- ✅ Team needs access to changes
- ✅ This is final production deployment

---

## ✨ **Best Practice (Hybrid Approach)**

1. **First:** Use Option 1 to test on staging
2. **Verify:** Run verification script
3. **Test:** Confirm login works at http://172.28.1.148
4. **Then:** Commit to git (Option 2)
5. **Document:** Note the working configuration
6. **Share:** Team can replicate on other environments

---

**My Recommendation:** Start with **Option 1** (direct copy) to test quickly, then commit to git once you confirm everything works!
