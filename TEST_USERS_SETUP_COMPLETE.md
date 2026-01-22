# Test Users Setup - Complete

**Date:** January 22, 2026  
**Status:** ✅ All test users created and configured

---

## 👥 **Test Users Created**

### **1. Admin User (Superuser)**
```
Username: admin
Password: admin123
Email:    admin@edms.local
Role:     Superuser (full system access)
```

### **2. Document Author**
```
Username: author01
Password: test123
Email:    author01@edms.com
Name:     Author One
Role:     Document Author (O1/write)
```
**Permissions:**
- Create new documents
- Edit draft documents
- Submit documents for review

### **3. Document Reviewer**
```
Username: reviewer01
Password: test123
Email:    reviewer01@edms.com
Name:     Reviewer User
Role:     Document Reviewer (O1/review)
```
**Permissions:**
- Review submitted documents
- Request changes
- Approve for final approval

### **4. Document Approver**
```
Username: approver01
Password: test123
Email:    approver01@edms.com
Name:     Approver User
Role:     Document Approver (O1/approve)
```
**Permissions:**
- Final document approval
- Set effective dates
- Reject documents back to author

### **5. System User (Automated)**
```
Username: edms_system
Email:    system@edms.local
Name:     EDMS System Service
Role:     System automation (scheduler tasks)
```

---

## 🔧 **How They Were Created**

### **Method Used:**
```bash
# Step 1: Create users
bash scripts/create-test-users.sh

# Step 2: Assign roles
bash scripts/fix-reviewer-approver-roles.sh
```

### **What the Scripts Do:**

**create-test-users.sh:**
- Creates 4 users (admin + 3 test users)
- Sets passwords
- Configures basic user attributes

**fix-reviewer-approver-roles.sh:**
- Assigns UserRole records
- Configures permission levels
- Sets up workflow permissions

---

## 📋 **Interactive Deployment Script Integration**

The test users are created automatically when running `./deploy-interactive.sh`:

**Sequence in deployment:**
1. ✅ Database migrations
2. ✅ Collect static files
3. ✅ Create default roles (7 roles)
4. ✅ Create Django groups (6 groups)
5. ✅ **Create test users** ← Lines 811-819
6. ✅ Create document types
7. ✅ Create document sources
8. ✅ Initialize placeholders
9. ✅ Initialize workflows
10. ✅ **Assign roles to test users** ← Lines 862-869
11. ✅ Initialize scheduler

---

## 🚀 **Quick Test Access**

### **Frontend Login:**
```
URL: http://localhost:3000/login

Test with:
- author01   / test123
- reviewer01 / test123
- approver01 / test123
```

### **Admin Panel:**
```
URL: http://localhost:8000/admin

Login with:
- admin / admin123
```

### **API Access:**
```bash
# Get auth token for author01
curl -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "author01", "password": "test123"}'
```

---

## 🔍 **Verify Users**

### **Check All Users:**
```bash
docker compose exec backend python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
for user in User.objects.all().order_by('username'):
    print(f'{user.username} - {user.email}')
"
```

### **Check User Roles:**
```bash
docker compose exec backend python manage.py shell -c "
from apps.users.models import UserRole
for ur in UserRole.objects.filter(is_active=True).select_related('user', 'role'):
    print(f'{ur.user.username}: {ur.role.name}')
"
```

### **Check User Groups:**
```bash
docker compose exec backend python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
for user in User.objects.all():
    groups = ', '.join([g.name for g in user.groups.all()])
    print(f'{user.username}: {groups or \"(no groups)\"}')
"
```

---

## 🔐 **Password Reset (if needed)**

### **Reset Password via Django Shell:**
```bash
docker compose exec backend python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
user = User.objects.get(username='author01')
user.set_password('newpassword123')
user.save()
print('Password updated')
"
```

### **Reset Password via Management Command:**
```bash
docker compose exec backend python manage.py changepassword author01
```

---

## 📊 **Typical Workflow Test**

### **Complete Document Workflow:**

1. **Author01 creates document:**
   - Login as `author01`
   - Create new SOP document
   - Fill metadata and upload file
   - Submit for review

2. **Reviewer01 reviews:**
   - Login as `reviewer01`
   - Open document from "My Tasks"
   - Review content
   - Approve or request changes

3. **Approver01 approves:**
   - Login as `approver01`
   - Open document from "My Tasks"
   - Final approval
   - Set effective date

4. **System processes:**
   - Scheduler activates document on effective date
   - Document status: DRAFT → REVIEW → APPROVED → EFFECTIVE

---

## 🎯 **Role-Based Access Summary**

| Feature | Author01 | Reviewer01 | Approver01 | Admin |
|---------|----------|------------|------------|-------|
| Create documents | ✅ | ❌ | ❌ | ✅ |
| Edit own drafts | ✅ | ❌ | ❌ | ✅ |
| Submit for review | ✅ | ❌ | ❌ | ✅ |
| Review documents | ❌ | ✅ | ❌ | ✅ |
| Request changes | ❌ | ✅ | ❌ | ✅ |
| Approve documents | ❌ | ❌ | ✅ | ✅ |
| Set effective dates | ❌ | ❌ | ✅ | ✅ |
| Admin panel access | ❌ | ❌ | ❌ | ✅ |
| User management | ❌ | ❌ | ❌ | ✅ |

---

## 📝 **Adding More Test Users**

### **Manual Creation:**
```bash
docker compose exec backend python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()

user = User.objects.create_user(
    username='author02',
    email='author02@edms.com',
    password='test123',
    first_name='Author',
    last_name='Two'
)
print(f'Created: {user.username}')
"
```

### **Assign Role:**
```bash
docker compose exec backend python manage.py shell -c "
from django.contrib.auth import get_user_model
from apps.users.models import UserRole, Role

User = get_user_model()
user = User.objects.get(username='author02')
role = Role.objects.get(name='Document Author')

UserRole.objects.create(
    user=user,
    role=role,
    is_active=True
)
print(f'Role assigned: {user.username} -> {role.name}')
"
```

---

## ✅ **Status**

**Users Created:** 5 total
- ✅ admin (superuser)
- ✅ author01 (Document Author)
- ✅ reviewer01 (Document Reviewer)
- ✅ approver01 (Document Approver)
- ✅ edms_system (System user)

**Roles Assigned:** ✅ Complete
**Ready for Testing:** ✅ Yes
**Login URL:** http://localhost:3000

---

**All test users are ready to use!**
