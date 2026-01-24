# System Settings Tab - Implementation Status

**Date:** January 24, 2026  
**Current Status:** ⚠️ **MOSTLY NOT IMPLEMENTED**

---

## 📊 Implementation Status

| Tab | Status | Backend | Frontend | Notes |
|-----|--------|---------|----------|-------|
| **Notifications** | ✅ **WORKING** | ✅ Real | ✅ Real | Shows SSH config guide |
| **General** | ❌ Mock Only | ❌ No API | ❌ Mock Data | Company name, file size, etc. |
| **Security** | ❌ Mock Only | ❌ No API | ❌ Mock Data | Session timeout, password policy |
| **Features** | ❌ Mock Only | ❌ No API | ❌ Mock Data | Feature toggles |
| **Appearance** | ❌ Mock Only | ❌ No API | ❌ Mock Data | Theme colors |

---

## ✅ What's Actually Working

### **Notifications Tab ONLY**
- **Purpose:** Shows SSH instructions for email configuration
- **Implementation:** Static content (no API needed)
- **Working:** 100% functional
- **Content:**
  - 5-step guide to configure email via SSH
  - SMTP settings explanation
  - Gmail/Office365 app password links
  - Backend restart instructions

---

## ❌ What's NOT Implemented

### 1. **General Settings Tab**
**Status:** Mock data only

**Mock Settings (not functional):**
- Company Name
- Maximum File Size (MB)
- Backup Retention (days)

**Backend Status:**
- ✅ Model exists: `apps.settings.models.SystemConfiguration`
- ❌ No API endpoints
- ❌ No data in database (0 records)
- ❌ No way to save changes

**Frontend Status:**
- Shows mock data with hardcoded values
- Save button shows alert: "Settings save functionality will be implemented"
- Changes don't persist

---

### 2. **Security Settings Tab**
**Status:** Mock data only

**Mock Settings (not functional):**
- Session Timeout (minutes)
- Password Policy settings
- Authentication settings

**Backend Status:**
- ❌ No API endpoints
- ❌ No functionality

**Frontend Status:**
- Shows mock data
- No actual security configuration

---

### 3. **Features Tab**
**Status:** Mock data only

**Mock Features (not functional):**
- Enable Document Versioning
- Enable Workflow Automation
- Enable Audit Trail
- Enable Backup System
- Enable Email Notifications

**Backend Status:**
- ❌ No feature toggle system
- ❌ Features are always enabled (hardcoded)

**Frontend Status:**
- Shows mock toggles
- Changes don't actually enable/disable features

---

### 4. **Appearance Tab**
**Status:** Mock data only

**Mock Settings (not functional):**
- Primary Theme Color
- UI customization

**Backend Status:**
- ❌ No theming system
- ❌ No API endpoints

**Frontend Status:**
- Shows color picker (doesn't work)
- No actual theme changes

---

## 📝 Evidence from Code

### Frontend (SystemSettings.tsx)
```tsx
// Line 14: Mock settings data
const mockSettings: SystemConfiguration[] = [
  // Hardcoded mock data for 6 settings
];

// Line 146: Mock feature toggles
const mockFeatures: FeatureToggle[] = [
  // Hardcoded mock data for 5 features
];

// Line 242-248: Simulates API call with timeout
React.useEffect(() => {
  setTimeout(() => {
    setSettings(mockSettings);  // Using mock data
    setFeatures(mockFeatures);  // Using mock data
    setLoading(false);
  }, 800);
}, []);

// Line 267: Save functionality not implemented
const handleSaveChanges = useCallback(() => {
  // TODO: Implement save functionality
  alert('Settings save functionality will be implemented...');
  setHasChanges(false);
}, []);
```

### Backend
```bash
$ docker compose exec backend python manage.py shell -c "
from apps.settings.models import SystemConfiguration
configs = SystemConfiguration.objects.all()
print(f'Records: {configs.count()}')
"

Result: SystemConfiguration records: 0
```

**No API endpoints exist for:**
- GET /api/v1/settings/
- PUT /api/v1/settings/{id}/
- POST /api/v1/settings/

---

## 💡 Recommendation

### Option 1: Remove Non-Working Tabs (Recommended)
**Keep only what works:**
- ✅ Keep "Notifications" tab (fully functional)
- ❌ Hide "General" tab (not implemented)
- ❌ Hide "Security" tab (not implemented)
- ❌ Hide "Features" tab (not implemented)
- ❌ Hide "Appearance" tab (not implemented)

**Benefit:** No confusion for users trying to change settings that don't work

---

### Option 2: Add "Coming Soon" Indicators
Keep all tabs but add clear indicators:
```tsx
<div className="p-4 bg-yellow-50 border border-yellow-200 rounded">
  ⚠️ This tab is under development. Settings displayed are for preview only 
  and cannot be saved yet.
</div>
```

**Benefit:** Shows future capabilities without misleading users

---

### Option 3: Implement the Backend (Future Work)
Full implementation would require:

1. **Backend API Development:**
   - Settings CRUD endpoints
   - Feature toggle system
   - Validation logic
   - Permission checks

2. **Database Migration:**
   - Seed default settings
   - Populate SystemConfiguration table

3. **Frontend Integration:**
   - Replace mock data with API calls
   - Implement save functionality
   - Add error handling

**Estimated Effort:** 2-3 weeks of development

---

## 🎯 Current Best Use

**The Settings page is currently useful ONLY for:**
- ✅ **Notifications tab** - Email configuration SSH guide
- ❌ **Nothing else** - All other tabs are non-functional mock-ups

**User Experience:**
- Users can view mock settings
- Users can click toggles and change values
- Users click "Save Changes"
- Alert appears: "Settings save functionality will be implemented..."
- **Nothing actually changes in the system**

---

## 📋 Action Items

### Immediate (Recommended)
1. **Hide non-working tabs** or add "Coming Soon" badges
2. **Update navigation** to only show Notifications tab
3. **Document** that only email config is available
4. **Remove "Save Changes" button** from non-working tabs

### Future (If implementing)
1. Build Settings API backend
2. Create database seed data
3. Implement save functionality
4. Add permission checks
5. Test all settings actually work

---

## ✅ Summary

**Working:** 1 tab (Notifications - email config guide)  
**Not Working:** 4 tabs (General, Security, Features, Appearance)  
**Total Functionality:** ~20% implemented  

**Recommendation:** Hide the non-working tabs or add clear "Not Implemented" warnings to avoid user confusion.

---

**Would you like me to:**
1. Hide the non-working tabs?
2. Add "Coming Soon" indicators?
3. Keep as-is with documentation?
4. Something else?

