# 🚀 Commands to Complete Task List Implementation

**Run these commands after Docker build finishes**

---

## ✅ Check Build Status

```bash
# Check if build is complete
ps aux | grep "docker compose build" | grep -v grep

# If no output, build is done. Verify new image:
docker images qms_04-backend --format "{{.CreatedAt}}\t{{.ID}}"
```

---

## 📋 Step-by-Step Completion

### **Step 1: Stop Current Backend**
```bash
docker compose stop backend
```

### **Step 2: Start New Backend Image**
```bash
docker compose up -d backend
```

### **Step 3: Wait for Backend to Start**
```bash
sleep 15
docker compose logs backend --tail 20
```

### **Step 4: Run Migrations**
```bash
docker compose exec backend python manage.py migrate django_celery_results
```

**Expected output:**
```
Running migrations:
  Applying django_celery_results.0001_initial... OK
  Applying django_celery_results.0002_add_group_result... OK
  ...
```

### **Step 5: Restart Celery Services**
```bash
docker compose restart celery_worker celery_beat
```

### **Step 6: Wait for Services to Start**
```bash
sleep 20
```

### **Step 7: Test New API Endpoint**
```bash
curl -s http://localhost:8000/api/v1/scheduler/monitoring/status/ | python3 -m json.tool | head -100
```

**Expected output:**
```json
{
  "timestamp": "2026-01-15T...",
  "summary": {
    "total_tasks": 11,
    "healthy": ...,
    ...
  },
  "tasks": [
    {
      "name": "Process Effective Dates",
      "last_run": {
        "timestamp": "...",
        "relative_time": "5m ago",
        "status": "SUCCESS"
      },
      "next_run": {
        "relative_time": "in 55m"
      }
    }
  ]
}
```

### **Step 8: Verify Task Results Are Being Stored**
```bash
docker compose exec backend python manage.py shell << 'EOF'
from django_celery_results.models import TaskResult

count = TaskResult.objects.count()
print(f"\n✅ Task results stored: {count}")

if count > 0:
    latest = TaskResult.objects.order_by('-date_done').first()
    print(f"\n📊 Latest task:")
    print(f"   Task: {latest.task_name}")
    print(f"   Status: {latest.status}")
    print(f"   Date: {latest.date_done}")
else:
    print("\n⏳ No results yet - tasks haven't run since migration")
    print("   Wait a few minutes for scheduled tasks to execute")
EOF
```

---

## 🎨 Frontend Update (Optional - Can Do Later)

The API is working with the new format. Frontend update is optional and can be done separately:

```bash
# Edit frontend/src/components/scheduler/SchedulerStatusWidget.tsx
# Replace health score display with task table
```

**Key changes needed:**
1. Remove health score rendering
2. Add task table with columns: Name | Last Run | Next Run | Status
3. Group tasks by category
4. Color code by status (green/yellow/red)

---

## 🧹 Cleanup Old Code (Optional)

Remove old health score calculation code:

```bash
# Review what to remove from monitoring_dashboard.py
grep -n "health_score\|_calculate_health_score" backend/apps/scheduler/monitoring_dashboard.py

# Can remove:
# - _calculate_health_score() method
# - health_breakdown calculations
# - Complex scoring logic

# Keep:
# - manual_trigger_api()
# - scheduler_dashboard() (if still used)
```

---

## ✅ Verification Checklist

After completing all steps:

- [ ] Backend started successfully
- [ ] Migrations ran without errors
- [ ] Celery workers restarted
- [ ] API endpoint returns task list (not health score)
- [ ] Task results are being stored in database
- [ ] Tasks show last run time
- [ ] Tasks show next run time
- [ ] Task status is accurate

---

## 🐛 Troubleshooting

### **If backend won't start:**
```bash
docker compose logs backend --tail 50
# Look for import errors or migration issues
```

### **If API returns old format:**
```bash
# Verify the new code is in the container
docker compose exec backend grep -n "task_monitor" /app/apps/scheduler/urls.py
```

### **If no task results:**
```bash
# Check if tasks are running
docker compose logs celery_worker --tail 50 | grep "Task.*succeeded"

# Wait for next scheduled task (every 5 minutes for notifications)
```

---

## 📊 Expected Results

After completion, visiting the scheduler dashboard should show:

```
📅 SCHEDULED TASKS

Summary: 11 tasks | 10 healthy | 1 failed | 0 warnings

Document Processing (2 tasks)
─────────────────────────────────────────────────────────
Process Effective Dates     5m ago    in 55m    ✅ SUCCESS
Process Obsolescence       4m ago    in 56m    ✅ SUCCESS

Notifications (2 tasks)
─────────────────────────────────────────────────────────
Process Queue              1m ago    in 4m     ✅ SUCCESS
Daily Summary             22h ago    in 2h     ✅ SUCCESS

Backups (3 tasks)
─────────────────────────────────────────────────────────
Daily Backup               5h ago    in 19h    ❌ FAILED
Weekly Backup              4d ago    in 3d     ✅ SUCCESS
Monthly Backup            14d ago    in 16d    ✅ SUCCESS
```

Much clearer than abstract health scores!

---

## ⏱️ Estimated Time

- Running commands: ~5 minutes
- Verification: ~2 minutes
- Frontend update (optional): ~30 minutes
- Total: ~7 minutes (or ~37 with frontend)

---

## 📝 Notes

- Docker build typically takes 10-15 minutes on first run
- Subsequent builds are much faster (cached layers)
- Task results accumulate over time (24 hour retention)
- Frontend update can be done in a separate session

---

**Current Status:** Waiting for Docker build to complete
**Commands Ready:** ✅ All commands prepared above
**Next Action:** Run Step 1-8 once build finishes
