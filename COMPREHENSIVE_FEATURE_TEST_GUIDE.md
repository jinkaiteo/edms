# 🧪 Comprehensive Feature Test Guide

## Testing All New Features - Step by Step

**URL:** http://localhost:3000  
**Module:** Admin → Backup Management

---

## 🎯 Test Checklist Overview

- [ ] Phase 1: Quick Wins (2 tests)
- [ ] Phase 2: Configuration CRUD (5 tests)
- [ ] Phase 3: Search & Filter (4 tests)
- [ ] Integration Tests (3 tests)

**Total Tests:** 14

---

## 📋 PHASE 1: Quick Wins Tests

### Test 1.1: Restore Tab - Redundancy Removed ✅

**What Changed:** Removed duplicate "Restore from Backup Job" dropdown

**Steps:**
1. Navigate to: Admin → Backup Management → **Restore** tab
2. Observe the page layout

**Expected Results:**
- ✅ See ONE upload package card (centered)
- ✅ See blue info box below with text: "To restore from an existing backup job, go to the Backup Jobs tab..."
- ❌ NO dropdown selector visible
- ✅ Professional centered layout

**Pass Criteria:** Only upload interface visible, no dropdown

---

### Test 1.2: Run Now on All Configurations ✅

**What Changed:** "Run Now" button now appears on ALL enabled configs

**Steps:**
1. Navigate to: Admin → Backup Management → **Configurations** tab
2. Scroll through configuration cards
3. Count how many have "Run Now" buttons

**Expected Results:**
- ✅ ALL enabled configurations show "▶ Run Now" button (blue)
- ✅ Disabled configurations don't show button
- ✅ Hovering shows tooltip with config name
- ✅ Button has play icon (▶)

**Pass Criteria:** Run Now appears on all enabled configs (should be 11/11)

---

## 📋 PHASE 2: Configuration CRUD Tests

### Test 2.1: Create Configuration ✅

**Steps:**
1. Go to: **Configurations** tab
2. Click green "➕ Create Configuration" button (top right)
3. Fill in form:
   - Name: `test_hourly_backup`
   - Description: `Test hourly database backup`
   - Type: `DATABASE`
   - Frequency: `HOURLY`
   - Schedule Time: `03:00`
   - Retention Days: `7`
   - Max Backups: `24`
   - Storage Path: `/opt/edms/backups`
   - ☑ Enable Compression
   - ☐ Enable Encryption
   - ☑ Enable Configuration
4. Click "Create Configuration" (green button)

**Expected Results:**
- ✅ Modal closes
- ✅ Success toast: "Configuration created"
- ✅ New config appears in grid
- ✅ Page refreshes automatically
- ✅ New config shows "Enabled" badge

**Pass Criteria:** New configuration visible in grid

---

### Test 2.2: Edit Configuration ✅

**Steps:**
1. Find the config you just created: `test_hourly_backup`
2. Click yellow "✏️ Edit" button
3. Modal opens with pre-filled values
4. Change:
   - Retention Days: `7` → `14`
   - Description: Add " - EDITED"
5. Click "Update Configuration" (yellow button)

**Expected Results:**
- ✅ Modal closes
- ✅ Success toast: "Configuration updated"
- ✅ Changes reflected in card
- ✅ Description shows " - EDITED"
- ✅ Card refreshes

**Pass Criteria:** Changes visible on configuration card

---

### Test 2.3: Disable/Enable Configuration ✅

**Steps:**
1. Find `test_hourly_backup` config
2. Note it shows "Enabled" badge and orange "⏸️ Disable" button
3. Click "⏸️ Disable" button
4. Wait for response
5. Observe changes
6. Click "▶️ Enable" button

**Expected Results:**

**After Disable:**
- ✅ Success toast: "Configuration disabled"
- ✅ Badge changes to "Disabled"
- ✅ Button changes to green "▶️ Enable"
- ✅ "Run Now" button disappears

**After Enable:**
- ✅ Success toast: "Configuration enabled"
- ✅ Badge changes to "Enabled"
- ✅ Button changes to orange "⏸️ Disable"
- ✅ "Run Now" button reappears

**Pass Criteria:** Toggle works both directions

---

### Test 2.4: Delete Configuration ✅

**Steps:**
1. Find `test_hourly_backup` config
2. Click red "🗑️ Delete" button
3. Confirmation modal appears
4. Read the warning
5. Verify config details shown
6. Click "Delete Configuration" (red button)

**Expected Results:**
- ✅ Confirmation modal displays
- ✅ Shows config name and description
- ✅ Shows warning about permanent deletion
- ✅ Has Cancel and Delete buttons
- ✅ After delete: Success toast
- ✅ Config removed from grid
- ✅ Grid refreshes

**Pass Criteria:** Configuration deleted and removed from display

---

### Test 2.5: Cancel Operations ✅

**Steps:**
1. Click "Create Configuration"
2. Fill in some fields
3. Click "Cancel"
4. Click "Create Configuration" again
5. Verify form is blank

**Repeat for Edit:**
1. Click "Edit" on any config
2. Change some values
3. Click "Cancel"
4. Click "Edit" again
5. Verify original values preserved

**Expected Results:**
- ✅ Cancel closes modal without saving
- ✅ No toast notification
- ✅ No changes made
- ✅ Form resets properly
- ✅ Original data preserved

**Pass Criteria:** Cancel buttons work correctly

---

## 📋 PHASE 3: Search & Filter Tests

### Test 3.1: Real-time Search ✅

**Steps:**
1. Go to: **Backup Jobs** tab
2. Note total number of jobs displayed
3. Find the search box at top (🔍 Search by job name...)
4. Type: `daily`
5. Observe results change
6. Clear search box
7. Try searching: `full`
8. Try searching: `completed`

**Expected Results:**
- ✅ Results filter instantly (no submit button)
- ✅ Results count appears: "Showing X of Y jobs"
- ✅ "Clear Filters" button appears (red)
- ✅ Only matching jobs displayed
- ✅ Search is case-insensitive
- ✅ Searches job name, type, status, config name
- ✅ Clearing search shows all jobs again

**Pass Criteria:** Search filters results in real-time

---

### Test 3.2: Status Filter ✅

**Steps:**
1. In **Backup Jobs** tab
2. Find status dropdown (says "All Status")
3. Click dropdown
4. Select "✅ Completed"
5. Observe results
6. Change to "❌ Failed" (if any)
7. Change to "🔄 Running" (if any)
8. Change back to "All Status"

**Expected Results:**
- ✅ Dropdown shows 6 options with icons
- ✅ Selecting filters jobs by status
- ✅ Results count updates
- ✅ "Clear Filters" button appears
- ✅ Works in combination with search
- ✅ Changing back to "All" shows all jobs

**Pass Criteria:** Status filter works correctly

---

### Test 3.3: Combined Search + Filter ✅

**Steps:**
1. Type in search: `backup`
2. Select status: `✅ Completed`
3. Observe results (should show only completed backups with "backup" in name)
4. Note the results count
5. Click "Clear Filters" button

**Expected Results:**
- ✅ Both filters apply simultaneously
- ✅ Results meet BOTH criteria
- ✅ Results count shows filtered number
- ✅ "Clear Filters" clears both at once
- ✅ All jobs reappear after clear

**Pass Criteria:** Multiple filters work together

---

### Test 3.4: Job Details Modal ✅

**Steps:**
1. Find any **COMPLETED** backup job
2. Hover over the row (should see cursor change)
3. Click anywhere on the row
4. Modal opens

**In Modal, verify all sections:**

**A. Basic Information (gray)**
- [ ] Job Name displayed
- [ ] Job ID (UUID) displayed
- [ ] Configuration name shown
- [ ] Status badge with correct color

**B. Backup Details (blue)**
- [ ] Backup Type shown
- [ ] File Size in MB
- [ ] Backup Path shown
- [ ] Checksum (first 16 chars) shown

**C. Timing (green)**
- [ ] Started date/time
- [ ] Completed date/time
- [ ] Duration in seconds

**D. Action Buttons**
- [ ] "📥 Download" button (blue)
- [ ] "✓ Verify" button (green)
- [ ] "🔄 Restore" button (purple)
- [ ] "Close" button (gray)

**Test Actions:**
1. Click "📥 Download" - file should download
2. Click "✓ Verify" - checksum notification appears
3. Click "🔄 Restore" - restore modal opens
4. Close restore modal
5. Click "Close" or X - details modal closes

**Expected Results:**
- ✅ Modal displays all sections
- ✅ All data formatted correctly
- ✅ Colors match status/section
- ✅ Action buttons work
- ✅ Close buttons work
- ✅ Responsive design (try resizing window)

**Pass Criteria:** All information displays, all buttons work

---

## 📋 INTEGRATION TESTS

### Integration Test 1: Complete Backup Workflow ✅

**Scenario:** Create config → Run backup → Find it → View details → Download

**Steps:**
1. **Configurations tab:** Create new config `integration_test`
2. Click "▶ Run Now" on it
3. Confirm in modal
4. **Backup Jobs tab:** Wait for job to appear
5. Search for `integration`
6. Click the job row
7. View details in modal
8. Click "Download" button

**Expected Results:**
- ✅ Config created successfully
- ✅ Backup triggered
- ✅ Job appears in Backup Jobs
- ✅ Search finds it
- ✅ Details modal shows complete info
- ✅ Download works

**Pass Criteria:** Complete end-to-end flow works

---

### Integration Test 2: Filter → Details → Action ✅

**Scenario:** Filter completed jobs → View details → Verify backup

**Steps:**
1. **Backup Jobs tab**
2. Select status: `✅ Completed`
3. Results show only completed
4. Click first completed job
5. Modal opens with details
6. Click "✓ Verify" button
7. Check notification

**Expected Results:**
- ✅ Filter shows only completed jobs
- ✅ Modal opens for selected job
- ✅ Verify button available (job is completed)
- ✅ Verification runs
- ✅ Success notification appears with checksum

**Pass Criteria:** Full flow from filter to action works

---

### Integration Test 3: Configuration Management Cycle ✅

**Scenario:** Create → Edit → Disable → Enable → Delete

**Steps:**
1. Create config: `lifecycle_test`
2. Edit: Change retention to 30 days
3. Disable the config
4. Enable the config
5. Delete the config

**Expected Results:**
- ✅ Each operation succeeds
- ✅ Success notifications for each
- ✅ UI updates after each step
- ✅ Final deletion removes config
- ✅ No errors throughout

**Pass Criteria:** Complete CRUD cycle completes successfully

---

## 🎯 Empty State Tests

### Test: Empty Search Results ✅

**Steps:**
1. Search for: `nonexistentbackup12345`

**Expected:**
- ✅ Shows: "No jobs match your search criteria. Try adjusting your filters."
- ✅ Results count: "Showing 0 of X jobs"
- ✅ "Clear Filters" button visible

---

### Test: No Configurations ✅

**Steps:**
1. If you deleted all test configs, check Configurations tab

**Expected:**
- ✅ If empty: appropriate message
- ✅ "Create Configuration" button still visible
- ✅ No error messages

---

## 🐛 Error Handling Tests

### Test: Invalid Configuration Data ✅

**Steps:**
1. Create configuration
2. Leave Name blank
3. Try to submit

**Expected:**
- ✅ "Create Configuration" button is DISABLED
- ✅ Cannot submit without required fields

---

### Test: Network Error Simulation ✅

**Steps:**
1. Open browser DevTools (F12)
2. Go to Network tab
3. Enable "Offline" mode
4. Try to create a configuration
5. Check console for error messages

**Expected:**
- ✅ Error notification appears
- ✅ User-friendly error message
- ✅ No crash or blank screen

---

## 📊 Test Results Template

### Test Session Info
- **Date:** _______________
- **Tester:** _______________
- **Browser:** _______________
- **Environment:** Development / Production

### Results Summary

| Test | Status | Notes |
|------|--------|-------|
| 1.1 Restore Tab | ✅ ❌ | |
| 1.2 Run Now All | ✅ ❌ | |
| 2.1 Create Config | ✅ ❌ | |
| 2.2 Edit Config | ✅ ❌ | |
| 2.3 Toggle Config | ✅ ❌ | |
| 2.4 Delete Config | ✅ ❌ | |
| 2.5 Cancel Actions | ✅ ❌ | |
| 3.1 Search | ✅ ❌ | |
| 3.2 Status Filter | ✅ ❌ | |
| 3.3 Combined Filters | ✅ ❌ | |
| 3.4 Job Details | ✅ ❌ | |
| I.1 Complete Workflow | ✅ ❌ | |
| I.2 Filter→Action | ✅ ❌ | |
| I.3 Config Cycle | ✅ ❌ | |

**Total Passed:** _____ / 14  
**Total Failed:** _____

---

## 🚨 Issues Found

### Issue Template
```
Issue #: ___
Test: _______________
Description: _______________
Steps to Reproduce:
1. 
2. 
3. 

Expected: _______________
Actual: _______________
Severity: Critical / High / Medium / Low
Screenshot: _______________
```

---

## ✅ Sign-Off

**All tests passed:** ✅ / ❌  
**Ready for production:** ✅ / ❌  
**Additional notes:**
_______________________________
_______________________________

**Tester Signature:** _______________  
**Date:** _______________

---

## 🎯 Quick Test Commands

### Open Application
```
http://localhost:3000
```

### Check Backend Logs
```bash
docker compose logs backend | tail -50
```

### Check Frontend Logs
```bash
docker compose logs frontend | tail -50
```

### Restart Services if Needed
```bash
docker compose restart frontend backend
```

---

**Ready to test! Start with Phase 1 tests and work through sequentially.** 🚀
