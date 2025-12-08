# Manual User Creation Test Guide

## 🎯 Purpose
Test user creation functionality and password unmasking feature through the EDMS frontend interface.

## 📋 Prerequisites
- EDMS backend and frontend running (Docker containers up)
- Admin credentials: `admin` / `test123`

## 🔍 Test Scenarios

### 1. Password Unmasking Feature Test
1. **Open browser** to http://localhost:3000
2. **Login as admin** with credentials above
3. **Navigate**: Admin → User Management
4. **Click**: "Create User" button
5. **Test password field**:
   - Enter password in "Password" field
   - ✅ **Verify**: Field shows dots (••••••••) by default
   - 👁️ **Click**: Eye icon next to password field
   - ✅ **Verify**: Password now shows as plain text
   - 👁️ **Click**: Eye icon again  
   - ✅ **Verify**: Password returns to masked (••••••••)
6. **Test confirm password field** (repeat above)

### 2. User Creation Tests

#### Test User 1: Basic Author
```
Username: test_author_manual
Email: test.author@edms-test.local
First Name: Test
Last Name: Author
Department: Engineering
Position: Technical Writer
Password: ManualTest123!
Groups: [Select "Authors" if available]
```

#### Test User 2: Reviewer Role  
```
Username: test_reviewer_manual
Email: test.reviewer@edms-test.local
First Name: Test
Last Name: Reviewer
Department: Quality
Position: QA Specialist  
Password: ManualTest123!
Groups: [Select "Reviewers" if available]
```

#### Test User 3: Multi-Role User
```
Username: test_multi_manual
Email: test.multi@edms-test.local
First Name: Test
Last Name: MultiRole
Department: Operations
Position: Senior Specialist
Password: ManualTest123!
Groups: [Select multiple if available]
```

## ✅ Verification Steps

### After Each User Creation:
1. **Success Check**: Look for success message or modal closing
2. **List Verification**: 
   - Refresh page or check user list
   - ✅ **Verify**: New user appears in table
   - ✅ **Verify**: Correct name, email, department shown
3. **Login Test**:
   - Logout from admin
   - Login with new user credentials
   - ✅ **Verify**: Can access dashboard
   - Logout and return to admin

### Password Unmasking Verification:
- ✅ **Default state**: Both password fields masked
- ✅ **Toggle works**: Eye icon shows/hides passwords
- ✅ **Independent**: Each field can be toggled separately
- ✅ **Visual feedback**: Icon changes appropriately

## 🚨 Error Testing

### Test Invalid Scenarios:
1. **Duplicate Username**: Try creating user with existing username
   - ✅ **Verify**: Error message appears
2. **Password Mismatch**: Enter different passwords in confirmation
   - ✅ **Verify**: Validation error shown
3. **Missing Required Fields**: Leave required fields empty
   - ✅ **Verify**: Form validation prevents submission

## 📊 Results Recording

### Record Results:
```
✅ Password unmasking works correctly
✅ User 1 (test_author_manual) created successfully
✅ User 2 (test_reviewer_manual) created successfully  
✅ User 3 (test_multi_manual) created successfully
✅ All users can login
✅ Error handling works for invalid inputs
```

## 🧹 Cleanup (Optional)
If you want to remove test users after testing:
1. Login as admin
2. Go to User Management
3. Delete the test users created above

## 📝 Manual Test Report Template

```
EDMS User Creation Manual Test Report
===================================

Date: [DATE]
Tester: [NAME]
Environment: Docker Local Development

Password Unmasking Feature:
- Default masked state: [PASS/FAIL]
- Eye icon toggle: [PASS/FAIL]
- Confirm field toggle: [PASS/FAIL]
- Icon visual feedback: [PASS/FAIL]

User Creation Tests:
- test_author_manual: [PASS/FAIL] - [NOTES]
- test_reviewer_manual: [PASS/FAIL] - [NOTES]
- test_multi_manual: [PASS/FAIL] - [NOTES]

Login Verification:
- New users can login: [PASS/FAIL]
- Correct dashboard access: [PASS/FAIL]

Error Handling:
- Duplicate username error: [PASS/FAIL]
- Password mismatch validation: [PASS/FAIL]
- Required field validation: [PASS/FAIL]

Overall Result: [PASS/FAIL]
Issues Found: [LIST ANY ISSUES]
```

## 🔧 Troubleshooting

If frontend doesn't load properly:
```bash
# Restart frontend container
docker compose restart frontend

# Check logs
docker compose logs frontend

# Verify backend is accessible
curl http://localhost:8000/api/v1/health/
```

This manual testing approach will verify both the password unmasking feature and user creation functionality while we resolve the Playwright automation issues.