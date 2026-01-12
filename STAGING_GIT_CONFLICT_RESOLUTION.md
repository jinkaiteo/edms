# Staging Server - Git Conflict Resolution Guide

**Issue:** Cannot pull latest changes because local modifications exist  
**File:** `deploy-interactive.sh`  
**Error:** "Your local changes would be overwritten by merge"

---

## 🔍 Quick Diagnosis

Run this on the **staging server** to see what changed:

```bash
cd ~/edms

# Check current status
git status

# See what changed in deploy-interactive.sh
git diff deploy-interactive.sh
```

---

## ✅ Solution Options (Choose ONE)

### **Option 1: Preserve Staging Changes** (Recommended if you made intentional edits)

If you made custom changes on staging that you want to keep:

```bash
cd ~/edms

# Step 1: Save your changes
git stash save "Staging server modifications before update"

# Step 2: Pull latest code
git pull origin develop

# Step 3: Review what you stashed
git stash show -p

# Step 4: Decide if you need to reapply
# If yes:
git stash pop
# Then manually resolve any conflicts

# If no (new version is better):
git stash drop
```

---

### **Option 2: Discard Staging Changes** (Recommended if changes were accidental/testing)

If the staging changes were just testing or you want to use the new version:

```bash
cd ~/edms

# Step 1: See what will be discarded
git diff deploy-interactive.sh

# Step 2: Backup the current file (safety)
cp deploy-interactive.sh deploy-interactive.sh.staging-backup

# Step 3: Discard local changes
git checkout -- deploy-interactive.sh

# Step 4: Pull latest code
git pull origin develop

# Step 5: Verify you have latest version
git log --oneline -3
# Should show:
# 197b597 feat: Add automated backup setup to deployment script
# 3a3d3d2 fix: Add storage permissions setup to deployment script
```

---

### **Option 3: Compare and Merge Manually** (For advanced users)

If you want to carefully merge specific changes:

```bash
cd ~/edms

# Step 1: See exactly what differs
git diff deploy-interactive.sh > /tmp/staging-changes.diff

# Step 2: View the diff
cat /tmp/staging-changes.diff

# Step 3: Save your version
cp deploy-interactive.sh deploy-interactive.sh.old

# Step 4: Get new version
git checkout -- deploy-interactive.sh
git pull origin develop

# Step 5: Manually apply specific changes from your old version
vimdiff deploy-interactive.sh.old deploy-interactive.sh
# OR
diff -u deploy-interactive.sh.old deploy-interactive.sh
```

---

## 🎯 Recommended Workflow for Most Users

**I recommend Option 2** (discard staging changes) because:
- ✅ Latest version has critical fixes (storage permissions + backup automation)
- ✅ Safe backup is created before discarding
- ✅ Cleanest state for testing the new deployment script
- ✅ You can always review the backup file if needed

### Quick Commands:

```bash
# On staging server
cd ~/edms

# Backup current version
cp deploy-interactive.sh deploy-interactive.sh.staging-backup-$(date +%Y%m%d)

# Discard local changes
git checkout -- deploy-interactive.sh

# Pull latest
git pull origin develop

# Verify success
git log --oneline -5
git status

# Should show:
# On branch develop
# Your branch is up to date with 'origin/develop'.
# nothing to commit, working tree clean
```

---

## ✅ Verification After Resolution

```bash
# 1. Check you're on latest commit
git log --oneline -1
# Should show: 197b597 feat: Add automated backup setup to deployment script

# 2. Verify script has new functions
grep -A 5 "setup_backup_automation" deploy-interactive.sh
grep -A 5 "setup_storage_permissions" deploy-interactive.sh

# 3. Check script is executable
ls -la deploy-interactive.sh
# Should show: -rwxr-xr-x

# 4. Make executable if needed
chmod +x deploy-interactive.sh
```

---

## 🔄 Now Proceed with Reset

Once Git conflict is resolved, continue with the staging reset:

```bash
cd ~/edms

# Follow STAGING_SERVER_RESET_GUIDE.md from Step 1
# Starting with complete system teardown...

docker compose -f docker-compose.prod.yml down -v
# ... continue with reset guide
```

---

## 🚨 If You See Different Files Modified

If `git status` shows other files modified:

```bash
# See all modified files
git status

# Option A: Discard ALL changes (clean slate)
git reset --hard origin/develop

# Option B: Stash ALL changes
git stash save "All staging modifications $(date +%Y%m%d-%H%M%S)"

# Then pull
git pull origin develop
```

---

## 📝 What Caused This?

**Common reasons for staging server modifications:**

1. **Testing/debugging**: Edited script directly on server
2. **Manual fixes**: Applied hotfixes during troubleshooting
3. **Accidental edits**: File opened and saved unintentionally
4. **Previous deployment**: Script modified during earlier deployment

**Prevention for future:**
- ✅ Never edit files directly on staging server
- ✅ All changes should go through Git workflow (local → commit → push → pull)
- ✅ Use `.env` files for server-specific configuration, not script edits
- ✅ Document any urgent hotfixes and commit them properly

---

## 💡 Pro Tip: Check What Changed

Before discarding, see exactly what differs:

```bash
# On staging server
cd ~/edms

# Show line-by-line differences
git diff deploy-interactive.sh | more

# Count how many lines changed
git diff --stat deploy-interactive.sh

# If changes are minor (1-5 lines), probably safe to discard
# If changes are major (50+ lines), review carefully before discarding
```

---

## 🆘 Troubleshooting

### Issue: "git checkout -- file" doesn't work

```bash
# Force discard with reset
git reset --hard HEAD

# Then pull
git pull origin develop
```

### Issue: Still getting merge conflicts after stash

```bash
# Abort any in-progress merge
git merge --abort

# Clean everything
git reset --hard origin/develop

# Verify clean
git status
```

### Issue: Want to compare your version with new version

```bash
# Save your version
cp deploy-interactive.sh /tmp/my-version.sh

# Get new version
git checkout -- deploy-interactive.sh
git pull origin develop

# Compare side-by-side
diff -y /tmp/my-version.sh deploy-interactive.sh | less
```

---

## 📋 Quick Decision Matrix

| Situation | Recommended Action |
|-----------|-------------------|
| Testing the new deployment features | **Option 2** - Discard changes |
| Made important custom modifications | **Option 1** - Stash and review |
| Unsure what changed | **Option 1** - Stash (safe) |
| Want fresh start | **Option 2** - Discard changes |
| Need to merge specific lines | **Option 3** - Manual merge |

---

## ✅ After Resolution Checklist

- [ ] Git conflict resolved
- [ ] `git status` shows "working tree clean"
- [ ] Latest commit is `197b597` (backup automation)
- [ ] Script is executable (`chmod +x`)
- [ ] Ready to proceed with STAGING_SERVER_RESET_GUIDE.md

---

**Next Step:** Once Git is clean, open `STAGING_SERVER_RESET_GUIDE.md` and start from Step 1.

**Questions?** Run `git status` on staging and share the output for specific guidance.
