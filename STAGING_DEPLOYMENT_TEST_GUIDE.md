# Staging Deployment Test Guide

## 🎯 Purpose

Test the deployment of new features on staging server before promoting to production.

---

## 📦 What's Being Deployed

### **Changes on Main Branch:**

1. **File Upload Size Limit Fix** (Commit: 1cc5075)
   - Nginx: 1MB → 100MB
   - Django: 50MB → 100MB
   - Fixes 413 errors

2. **New Document Types** (Commits: 1b2f43d, 7d2ea10)
   - Protocol (PRO) - 10 year retention
   - Report (RPT) - 7 year retention
   - Memo (MEM) - 3 year retention
   - Total: 6 → 9 document types

---

## 🚀 Staging Deployment Steps

### **Prerequisites**
- SSH access to staging: `172.28.1.148`
- Staging is on port 3001 (frontend) and 8001 (backend)

---

### **Step 1: SSH to Staging**

```bash
ssh lims@172.28.1.148
```

---

### **Step 2: Navigate to Staging Project**

```bash
cd /home/lims/edms-staging
pwd
# Should show: /home/lims/edms-staging
```

---

### **Step 3: Check Current Status**

```bash
# Check current branch
git branch
# Should show: * develop or * main

# Check current commit
git log -1 --oneline

# Check running containers
docker compose -f docker-compose.prod.yml ps
```

---

### **Step 4: Pull Latest from Main**

```bash
# Fetch latest
git fetch origin

# Switch to main (if not already)
git checkout main

# Pull latest changes
git pull origin main

# Verify you got the changes
git log -5 --oneline
```

**Should show:**
```
7d2ea10 feat: Add Memo (MEM) document type
558f75f Merge develop: Add Protocol and Report document types
1b2f43d feat: Add Protocol (PRO) and Report (RPT) document types
27c45f4 Merge branch 'develop'
ba129e0 chore: Add automated deployment script for file upload fix
```

---

### **Step 5: Verify File Changes**

```bash
# Check nginx config has 100MB limit
grep "client_max_body_size" frontend/nginx.conf
# Should show: client_max_body_size 100M;

# Check Django settings
grep "100 \* 1024 \* 1024" backend/edms/settings/base.py
# Should show three lines with 100MB limits

# Check document types
cat backend/apps/documents/management/commands/create_default_document_types.py | grep -E "PRO|RPT|MEM" | grep code
# Should show PRO, RPT, and MEM entries
```

---

### **Step 6: Stop Services** ⏸️

```bash
docker compose -f docker-compose.prod.yml stop frontend backend

# Verify stopped
docker compose -f docker-compose.prod.yml ps
```

**⚠️ Downtime starts here**

---

### **Step 7: Rebuild Frontend** 🔨

```bash
docker compose -f docker-compose.prod.yml build --no-cache frontend
```

**Takes ~2-3 minutes**

---

### **Step 8: Rebuild Backend** 🔨

```bash
docker compose -f docker-compose.prod.yml build --no-cache backend
```

**Takes ~1-2 minutes**

---

### **Step 9: Start Services** ▶️

```bash
docker compose -f docker-compose.prod.yml up -d

# Wait for services to start
sleep 30
```

**⚠️ Downtime ends here**

---

### **Step 10: Verify Deployment** ✅

```bash
# Check all containers
docker compose -f docker-compose.prod.yml ps
# All should show "Up" status

# Verify nginx config in container
docker compose -f docker-compose.prod.yml exec frontend cat /etc/nginx/conf.d/default.conf | grep "client_max_body_size"
# Should show: client_max_body_size 100M;

# Test frontend
curl http://localhost:3001/
# Should return HTML

# Test backend health
curl http://localhost:8001/health/
# Should return: {"status":"healthy"}
```

---

### **Step 11: Add New Document Types** ⭐

```bash
# Run the management command
docker compose -f docker-compose.prod.yml exec backend python manage.py create_default_document_types
```

**Expected output:**
```
Creating default EDMS document types...
  - Exists: POL - Policy
  - Exists: SOP - Standard Operating Procedure
  - Exists: WI - Work Instruction
  - Exists: MAN - Manual
  - Exists: FRM - Form
  - Exists: REC - Record
  ✓ Created: PRO - Protocol
  ✓ Created: RPT - Report
  ✓ Created: MEM - Memo

Completed! Created: 3, Updated: 0, Unchanged: 6
```

---

### **Step 12: Verify Document Types**

```bash
# Enter Django shell
docker compose -f docker-compose.prod.yml exec backend python manage.py shell
```

**In Django shell:**
```python
from apps.documents.models import DocumentType

# Check total count
print(f"Total document types: {DocumentType.objects.filter(is_active=True).count()}")
# Should show: Total document types: 9

# List all types
for dt in DocumentType.objects.filter(is_active=True).order_by('code'):
    print(f"{dt.code}: {dt.name} ({dt.retention_years} years)")

# Exit shell
exit()
```

**Expected output:**
```
FRM: Form (3 years)
MAN: Manual (5 years)
MEM: Memo (3 years)
POL: Policy (7 years)
PRO: Protocol (10 years)
REC: Record (7 years)
RPT: Report (7 years)
SOP: Standard Operating Procedure (5 years)
WI: Work Instruction (5 years)
```

---

### **Step 13: Check Logs**

```bash
# Check for any errors in logs
docker compose -f docker-compose.prod.yml logs --tail=30 frontend
docker compose -f docker-compose.prod.yml logs --tail=30 backend
```

Look for:
- ✅ No error messages
- ✅ "Application startup complete" type messages
- ✅ No "client_max_body_size" warnings

---

## 🧪 Browser Testing

### **Test 1: Frontend Access**

From your workstation:

```bash
# Test from command line
curl http://172.28.1.148:3001/

# Open browser (INCOGNITO MODE!)
http://172.28.1.148:3001
```

**Should:**
- ✅ Load EDMS login page
- ✅ No console errors
- ✅ Styling loads correctly

---

### **Test 2: Login and Navigation**

1. Login with credentials
2. Navigate through the app
3. Check all main sections load

---

### **Test 3: Document Creation with New Types** ⭐

1. Click **"Create Document"**
2. Check **Document Type** dropdown
3. **Should show all 9 types:**
   - Form
   - Manual
   - **Memo** ⭐ (NEW)
   - Policy
   - **Protocol** ⭐ (NEW)
   - Record
   - **Report** ⭐ (NEW)
   - Standard Operating Procedure
   - Work Instruction

---

### **Test 4: File Upload Size** ⭐

1. Create a new document (any type)
2. Try uploading a **5MB file**
3. **Should upload successfully!** ✅ (Previously failed with 413)

---

### **Test 5: Create Each New Document Type**

#### **Test 5a: Create Protocol**
1. Create Document → Type: Protocol
2. Fill in details
3. Upload file
4. Save
5. **Verify:**
   - ✅ Document number: PRO-2026-XXXX-v01.00
   - ✅ Status: DRAFT
   - ✅ Approval required: Yes
   - ✅ Review required: Yes

#### **Test 5b: Create Report**
1. Create Document → Type: Report
2. Fill in details
3. Upload file
4. Save
5. **Verify:**
   - ✅ Document number: RPT-2026-XXXX-v01.00
   - ✅ Status: DRAFT
   - ✅ Approval required: Yes
   - ✅ Review required: Yes

#### **Test 5c: Create Memo**
1. Create Document → Type: Memo
2. Fill in details
3. Upload file
4. Save
5. **Verify:**
   - ✅ Document number: MEM-2026-XXXX-v01.00
   - ✅ Status: DRAFT
   - ✅ Approval required: No (should skip workflow)
   - ✅ Review required: No (should skip workflow)

---

### **Test 6: Large File Upload**

1. Create any document type
2. Upload a **50MB file**
3. **Should upload successfully!** ✅
4. Verify document shows correct file size

---

### **Test 7: Workflow Testing**

Test that new document types follow correct workflows:

**Protocol (should require approval):**
1. Create Protocol document
2. Submit for Review
3. **Should show review workflow** ✅

**Report (should require approval):**
1. Create Report document
2. Submit for Review
3. **Should show review workflow** ✅

**Memo (should NOT require approval):**
1. Create Memo document
2. **Should NOT show "Submit for Review" button** ✅
3. Memo stays in DRAFT or goes directly to EFFECTIVE

---

## ✅ Success Criteria

### **Deployment Success:**
- ✅ All containers running (Up status)
- ✅ Nginx config shows 100M limit
- ✅ Frontend accessible
- ✅ Backend healthy
- ✅ No errors in logs

### **Document Types Success:**
- ✅ 9 document types total
- ✅ Protocol (PRO) appears in dropdown
- ✅ Report (RPT) appears in dropdown
- ✅ Memo (MEM) appears in dropdown
- ✅ Can create documents with new types
- ✅ Document numbering works (PRO-*, RPT-*, MEM-*)

### **File Upload Success:**
- ✅ Can upload 5MB files
- ✅ Can upload 50MB files
- ✅ No 413 errors
- ✅ Files appear correctly in documents

### **Workflow Success:**
- ✅ Protocol requires approval
- ✅ Report requires approval
- ✅ Memo does NOT require approval

---

## 🔧 Troubleshooting

### Issue: Containers won't start

```bash
# Check logs
docker compose -f docker-compose.prod.yml logs

# Try rebuilding with no cache
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml build --no-cache
docker compose -f docker-compose.prod.yml up -d
```

### Issue: Document types not showing

```bash
# Re-run the command
docker compose -f docker-compose.prod.yml exec backend python manage.py create_default_document_types

# Verify in database
docker compose -f docker-compose.prod.yml exec backend python manage.py shell
from apps.documents.models import DocumentType
DocumentType.objects.filter(is_active=True).count()
```

### Issue: Still getting 413 errors

```bash
# Verify nginx config in running container
docker compose -f docker-compose.prod.yml exec frontend cat /etc/nginx/conf.d/default.conf | grep client_max_body_size

# If not showing 100M, rebuild frontend
docker compose -f docker-compose.prod.yml build --no-cache frontend
docker compose -f docker-compose.prod.yml restart frontend
```

### Issue: Browser shows old interface

**Solution:** Clear browser cache or use incognito mode
- Hard reload: `Ctrl+Shift+R` (Windows/Linux) or `Cmd+Shift+R` (Mac)

---

## 📊 Testing Checklist

### **Deployment Tests:**
- [ ] SSH to staging successful
- [ ] Git pull completed
- [ ] Containers rebuilt
- [ ] All services started
- [ ] Nginx config updated
- [ ] Document types command ran successfully

### **Browser Tests:**
- [ ] Frontend loads (incognito mode)
- [ ] Login successful
- [ ] Dashboard accessible
- [ ] Create document modal opens

### **Document Type Tests:**
- [ ] 9 types in dropdown
- [ ] Protocol (PRO) visible
- [ ] Report (RPT) visible
- [ ] Memo (MEM) visible
- [ ] Can create Protocol
- [ ] Can create Report
- [ ] Can create Memo
- [ ] Numbering correct (PRO-*, RPT-*, MEM-*)

### **File Upload Tests:**
- [ ] 1MB file uploads
- [ ] 5MB file uploads
- [ ] 50MB file uploads
- [ ] No 413 errors

### **Workflow Tests:**
- [ ] Protocol requires approval
- [ ] Report requires approval
- [ ] Memo skips approval

---

## 🎯 After Successful Testing

Once staging tests pass:

1. **Document results** (note any issues)
2. **Create backup** of production
3. **Schedule production deployment**
4. **Notify users** of upcoming changes
5. **Deploy to production** using same steps

---

## 📝 Test Results Template

```
STAGING DEPLOYMENT TEST - [DATE]

Deployment:
✅/❌ Git pull successful
✅/❌ Containers rebuilt
✅/❌ Services started
✅/❌ Document types added

File Upload:
✅/❌ 5MB upload
✅/❌ 50MB upload
✅/❌ No 413 errors

Document Types:
✅/❌ Protocol (PRO) - [PRO-2026-XXXX-v01.00]
✅/❌ Report (RPT) - [RPT-2026-XXXX-v01.00]
✅/❌ Memo (MEM) - [MEM-2026-XXXX-v01.00]

Workflows:
✅/❌ Protocol requires approval
✅/❌ Report requires approval
✅/❌ Memo skips approval

Issues Found:
[List any issues]

Ready for Production: YES/NO
```

---

**Ready to test on staging!** 🚀

Follow the steps above and let me know the results!
