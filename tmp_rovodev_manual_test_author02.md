# Manual Test: Create Author02 with Document Author Role

## 🎯 Purpose
Test the new role selection functionality by creating `author02` user with Document Author role assignment during user creation.

## 📋 Prerequisites
- EDMS running: Frontend (localhost:3000) + Backend (localhost:8000)
- Admin credentials: `admin` / `test123`

## 🔧 Test Steps

### Step 1: Access User Management
1. **Open browser** → http://localhost:3000
2. **Login as admin**:
   - Username: `admin`
   - Password: `test123`
3. **Navigate**: Admin → User Management
4. **Click**: "Create User" button

### Step 2: Fill User Details
```
Username: author02
Email: author02@edms-test.local  
First Name: Author
Last Name: Two
Department: Engineering
Position: Technical Writer
Password: Author02Test123!
Confirm Password: Author02Test123!
```

### Step 3: ✅ NEW FEATURE - Role Selection
1. **Scroll down** to "Assign Roles" section
2. **Verify** you can see all available roles:
   - ☐ Document Admin (admin)
   - ☐ Document Approver (approve)  
   - ☐ Document Viewer (read)
   - ☐ Document Reviewer (review)
   - ☐ Document Author (write) ← **Check this one**
   - ☐ User Admin (admin)
   - ☐ Placeholder Admin (admin)

3. **✅ Check the "Document Author (write)" checkbox**
4. **Verify** checkbox shows as checked/selected

### Step 4: Create User
1. **Click**: "Create User" button
2. **Wait** for success message or modal to close
3. **Verify**: No error messages appear

### Step 5: Verify User Creation
1. **Check user list** for new user:
   - Look for: `Author Two` or `author02`
   - **✅ VERIFY**: User appears in the list
   
2. **Check role assignment**:
   - Look for blue badge: **"Document Author (write)"**
   - **✅ VERIFY**: Role badge is visible next to user name

### Step 6: Test Login & Permissions
1. **Logout** from admin account
2. **Login as author02**:
   - Username: `author02`
   - Password: `Author02Test123!`
3. **✅ VERIFY**: Login successful, reaches dashboard
4. **Check author permissions**: Look for document creation options

## 🔍 Expected Results

### ✅ SUCCESS Indicators:
- **User created** without errors
- **"Document Author (write)" badge** visible in user list
- **author02 can login** successfully
- **Role assignment** happened during creation (not after)

### ❌ FAILURE Indicators:
- Error messages during creation
- No role badge shown
- Login fails for new user
- Role section missing or broken

## 🐛 Troubleshooting

### If Role Selection Not Visible:
```bash
# Check if roles are loaded
curl http://localhost:8000/api/v1/users/roles/
```

### If User Creation Fails:
- Check browser console for errors
- Verify all required fields filled
- Try creating without role first

### If Role Not Assigned:
- Check user list after refresh
- Look in "Manage Roles" for the user
- Verify backend role assignment API

## 📊 Test Results Template

```
Manual Test Results: author02 Creation with Role Selection
=========================================================

Date: [DATE]
Tester: [NAME]

✅ Step 1 - Access user management: [PASS/FAIL]
✅ Step 2 - Fill user details: [PASS/FAIL]  
✅ Step 3 - Role selection UI visible: [PASS/FAIL]
✅ Step 3 - Document Author role selectable: [PASS/FAIL]
✅ Step 4 - User creation successful: [PASS/FAIL]
✅ Step 5 - User appears in list: [PASS/FAIL]
✅ Step 5 - Role badge visible: [PASS/FAIL]
✅ Step 6 - Login as author02 works: [PASS/FAIL]

Overall Result: [PASS/FAIL]

Notes:
- Role selection UI: [Description]
- Performance: [Fast/Slow]
- Any issues: [List any problems]
```

## 🎉 Success Confirmation

**If all steps pass, you have successfully:**
1. ✅ **Verified the role selection feature works**
2. ✅ **Created author02 with Document Author role**
3. ✅ **Confirmed roles are assigned during user creation**
4. ✅ **Validated the complete user creation workflow**

This resolves the original issue where author01 had no role assigned - the new interface allows role assignment during creation instead of requiring a separate step afterward.

## 🔄 Next Steps
- Test with multiple role selections
- Verify other role types work  
- Test role modification after creation
- Document any UI improvements needed