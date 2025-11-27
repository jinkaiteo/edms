# EDMS Quick Login Credentials - UPDATED

## 🔑 STANDARDIZED PASSWORD: `TestUser2024!`

**ALL USERS NOW USE THE SAME PASSWORD FOR TESTING CONVENIENCE**

### Available Test Users

| Username | Role | Email | Password | Capabilities |
|----------|------|--------|----------|--------------|
| `admin` | System Admin | admin@edms.local | `TestUser2024!` | All permissions + Superuser |
| `author` | Document Author | author@edms-project.com | `TestUser2024!` | Create & edit documents |
| `reviewer` | Document Reviewer | reviewer@edms-project.com | `TestUser2024!` | Review documents |
| `approver` | Document Approver | approver@edms-project.com | `TestUser2024!` | Approve documents |
| `docadmin` | Document Administrator | docadmin@edms-project.com | `TestUser2024!` | Document management |
| `placeholderadmin` | Placeholder Admin | placeholderadmin@edms-project.com | `TestUser2024!` | Write + Placeholder Admin |
| `testuser` | Test User | test@edms.local | `TestUser2024!` | Review documents |

## 🧪 Quick Testing Workflow

### Complete Workflow Test:
1. **Login as `author`** → Create document → Submit for review
2. **Login as `reviewer`** → Review and approve document  
3. **Login as `author`** → Route document for approval
4. **Login as `approver`** → Approve and set effective date

### Alternative Testing Combinations:
- **Author**: `placeholderadmin` (has write permission)
- **Reviewer**: `testuser` (alternative reviewer)
- **Approver**: `approver` (only dedicated approver)

## ✅ Authentication Fixed Issues:
- ✅ Backend import error resolved (`date` import added)
- ✅ All user passwords standardized to `TestUser2024!`
- ✅ API authentication working (JWT tokens generated)
- ✅ CORS configured properly for localhost:3000 → localhost:8000

## 🚀 Ready for Testing!

The system is now ready for comprehensive workflow testing. You can login with any of the above usernames using the password `TestUser2024!`.

**Next Steps:**
1. Try logging in as `author` with password `TestUser2024!`
2. Test document creation and workflow progression
3. Switch between users to test complete workflow cycle