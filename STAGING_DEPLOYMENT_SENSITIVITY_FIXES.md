# Staging Deployment: Sensitivity Label Fixes & UI Improvements

## 📋 Summary
This deployment includes critical bug fixes for the sensitivity label system and UI improvements for document viewing.

## 🎯 Changes Included

### 1. **Sensitivity Label Approval Integration** ✅
- **Fixed**: Sensitivity label selector now appears in approval workflow
- **Files Modified**:
  - `frontend/src/components/workflows/UnifiedWorkflowInterface.tsx` - Added SensitivityLabelSelector component
  - `frontend/src/components/workflows/ApproverInterface.tsx` - Added sensitivity fields to Document interface
  - `backend/apps/documents/workflow_integration.py` - Pass sensitivity_label to workflow service
  - `backend/apps/workflows/services.py` - Accept sensitivity parameters
  - `backend/apps/workflows/document_lifecycle.py` - Fixed audit trail logging

### 2. **Audit Trail Fixes** ✅
- **Fixed**: AuditTrail creation now uses correct field names
- **Changes**: Updated to use `content_type`, `object_id`, `metadata` instead of `document`, `details`
- **Affects**: Both approval and up-versioning workflows

### 3. **SUPERSEDED/OBSOLETE Document Access** ✅
- **Fixed**: Users can now view and download historical documents
- **Files Modified**:
  - `backend/apps/documents/views.py` - Allow downloads for SUPERSEDED, SCHEDULED_FOR_OBSOLESCENCE, OBSOLETE
  - `frontend/src/components/documents/DocumentViewer.tsx` - Show View PDF button for historical statuses
  - `frontend/src/components/documents/DownloadActionMenu.tsx` - Enable downloads for historical statuses
- **Watermarks**: Gray watermarks automatically applied to superseded/obsolete documents

### 4. **Document Detail Header UI Cleanup** ✅
- **Improved**: Reorganized header layout for better readability
- **Changes**: 
  - Title now prominently displayed (2xl font, standalone)
  - Metadata and badges on separate rows
  - Action buttons properly separated with "Back" button on right
- **File**: `frontend/src/components/documents/DocumentViewer.tsx`

### 5. **Backend Serializer Fixes** ✅
- **Fixed**: `sensitivity_set_by_display` field now handles null values
- **Files**: `backend/apps/documents/serializers.py`
- **Prevents**: 500 errors when viewing documents without sensitivity classification

## 🗃️ Database Changes
- ❌ **No new migrations** - All changes are code-only
- ✅ Existing sensitivity label migrations already applied

## 📦 Deployment Steps

### Pre-Deployment Checklist
```bash
# 1. Verify local changes
git status

# 2. Check no uncommitted migrations
docker compose exec backend python manage.py makemigrations --check --dry-run

# 3. Run tests (if available)
# docker compose exec backend python manage.py test
```

### Deploy to Staging
```bash
# Option 1: Use interactive deployment script (RECOMMENDED)
./deploy-interactive.sh

# Option 2: Manual deployment
git add -A
git commit -m "fix: Sensitivity label approval integration and UI improvements"
git push origin develop

# Then on staging server:
cd /path/to/edms
git pull origin develop
docker compose build backend frontend
docker compose restart backend frontend

# Wait for services to start (30-60 seconds)
docker compose logs -f backend frontend
```

## 🧪 Testing Checklist

### 1. Sensitivity Label Approval
- [ ] Login as approver (approver01)
- [ ] Navigate to "My Tasks"
- [ ] Click on a PENDING_APPROVAL document
- [ ] Click "Start Approval Process"
- [ ] Select "Approve Document"
- [ ] **VERIFY**: Sensitivity Label Selector appears
- [ ] Select a sensitivity level (e.g., CONFIDENTIAL)
- [ ] Fill in required fields and submit
- [ ] **VERIFY**: Document approved successfully with sensitivity label

### 2. Up-Versioning with Sensitivity Inheritance
- [ ] Open an EFFECTIVE document with sensitivity label
- [ ] Click "Create New Version"
- [ ] **VERIFY**: New version inherits parent's sensitivity label
- [ ] Complete workflow to approval
- [ ] **VERIFY**: Approver sees inherited sensitivity with option to change

### 3. Historical Document Access
- [ ] Navigate to document library
- [ ] Find a SUPERSEDED document (RPT-2026-0004-v01.00)
- [ ] Click to view document detail
- [ ] **VERIFY**: View PDF and Download buttons visible
- [ ] Download PDF
- [ ] **VERIFY**: Gray "SUPERSEDED" watermark appears on PDF

### 4. UI Improvements
- [ ] Open any document detail page
- [ ] **VERIFY**: Title is large and prominent
- [ ] **VERIFY**: Status and sensitivity badges on separate row
- [ ] **VERIFY**: Action buttons have proper spacing
- [ ] **VERIFY**: "Back" button on the right side

## 🔄 Rollback Plan
If issues occur:

```bash
# Quick rollback (revert code changes)
cd /path/to/edms
git log --oneline -5  # Find commit hash before changes
git checkout <previous-commit-hash>
docker compose restart backend frontend

# OR rebuild from previous version
docker compose down
git reset --hard HEAD~1
docker compose build
docker compose up -d
```

## 📊 Expected Results

### Before Fix
- ❌ No sensitivity selector during approval
- ❌ 500 errors on document detail pages
- ❌ Cannot view SUPERSEDED documents
- ❌ Cluttered document header

### After Fix
- ✅ Sensitivity selector visible during approval
- ✅ All documents load without errors
- ✅ Historical documents accessible with watermarks
- ✅ Clean, readable document header layout

## 🚨 Known Issues
None - all fixes tested locally

## 📞 Support
If issues arise during deployment:
1. Check backend logs: `docker compose logs backend --tail=100`
2. Check frontend logs: `docker compose logs frontend --tail=100`
3. Verify database: `docker compose exec backend python manage.py showmigrations`
4. Test API: `curl http://localhost:8000/api/v1/documents/documents/`

## ✅ Deployment Sign-Off
- **Developer**: [Your Name]
- **Date**: 2026-02-06
- **Tested Locally**: ✅ Yes
- **Code Review**: Pending
- **Ready for Staging**: ✅ Yes
