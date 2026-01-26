# Next Steps: Local vs Staging Comparison

## 🎯 Goal
Identify why local works but staging doesn't for scheduler dashboard status updates.

## 📋 Action Required

### Step 1: Run Comparison on LOCAL (Your Machine)

```bash
cd ~/edms
git pull origin main
./compare_local_vs_staging.sh
```

This creates: `edms_diagnostic_<hostname>_<timestamp>.txt`

### Step 2: Run Comparison on STAGING

```bash
# SSH to staging
ssh lims@staging-server-ubuntu-20

cd ~/edms
git pull origin main
./compare_local_vs_staging.sh
```

This creates: `edms_diagnostic_<hostname>_<timestamp>.txt`

### Step 3: Send Me Both Files

Copy the contents of both diagnostic files and share them. I'll analyze:

1. **CELERY_RESULT_BACKEND** - Must be `django-db` in both
2. **Celery result_backend** - Must be `django-db` in both
3. **TaskResult count** - Must be > 0 in both
4. **Beat schedule tasks** - Should have same 9 tasks
5. **Status API output** - Should return same data structure

## 🔍 What I'm Looking For

### Critical Differences

**Local (Working):**
```
Celery result_backend: django-db
TaskResult count: 30+
Status API tasks: 9
Send Test Email: Last run: 3h ago
```

**Staging (Broken):**
```
Celery result_backend: redis://redis:6379/0  ← WRONG!
TaskResult count: 0  ← NO RESULTS!
Status API tasks: 10 (including celery.backend_cleanup)
Send Test Email: Last run: Never run
```

## 📊 Specific Checks

I'll compare these sections:

1. **Section 3: DJANGO SETTINGS**
   - `CELERY_RESULT_BACKEND` value

2. **Section 4: CELERY APP CONFIGURATION**
   - `Result backend` value (this is what Celery actually uses)

3. **Section 5: BEAT SCHEDULE TASKS**
   - Number of tasks
   - Presence of `celery.backend_cleanup` (should not exist after latest fix)

4. **Section 7: DATABASE - TASK RESULTS**
   - Count must be > 0
   - Should have recent executions

5. **Section 8: STATUS API OUTPUT**
   - Tasks should show actual last run times
   - Not "Never run"

6. **Section 11: SETTINGS FILE GREP**
   - Check for duplicate CELERY_RESULT_BACKEND lines
   - Verify only one definition exists

## 🔧 Expected Fixes

Based on comparison, I'll provide:

1. **Exact configuration diff** between local and staging
2. **Specific fix commands** for staging
3. **Verification steps** to confirm fix works

## ⏱️ Timeline

- Step 1+2: 5 minutes (run both scripts)
- Step 3: 2 minutes (copy/paste output)
- Analysis: 5 minutes (I'll identify the issue)
- Fix: 10 minutes (apply targeted fix)

Total: ~20 minutes to resolution

## 📝 Temporary Workaround

While we debug, you can manually trigger tasks and they WILL execute (email sends), but status won't update in dashboard. This is a display issue only, not a functionality issue.

## 🎯 Why This Approach

Instead of SSH access, this diagnostic approach:
- ✅ Captures exact state of both systems
- ✅ Shows configuration as Celery sees it (not just files)
- ✅ Identifies runtime vs configuration issues
- ✅ Provides reproducible diagnostic output
- ✅ Allows systematic comparison

Once you share both diagnostic files, I'll pinpoint the exact difference and provide the targeted fix!
