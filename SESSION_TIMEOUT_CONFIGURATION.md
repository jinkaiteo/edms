# EDMS Session Timeout Configuration

## ⏱️ Current Configuration

### **Session Timeouts by Environment:**

| Environment | Timeout | Setting | File |
|-------------|---------|---------|------|
| **Development** | 8 hours | `SESSION_COOKIE_AGE = 28800` | `settings/base.py` |
| **Staging** | 8 hours | Inherits from base.py | `settings/base.py` |
| **Production** | **1 hour** | `SESSION_COOKIE_AGE = 3600` | `settings/production.py` |

---

## 🔍 How Session Timeout Works

### **Session Lifecycle:**

1. **User logs in** → Session cookie created
2. **User is active** → Session remains valid
3. **User is inactive** → Session expires after timeout period
4. **Session expired** → User must log in again

### **Activity = Any Request:**
- Loading pages
- Creating documents
- Submitting forms
- API calls
- Clicking buttons

### **Key Behavior:**

**`SESSION_SAVE_EVERY_REQUEST = True`**
- ✅ Every user action resets the timeout timer
- ✅ Active users stay logged in indefinitely
- ❌ Inactive users are logged out after timeout

---

## 📋 Real-World Examples

### **Production (1-hour timeout):**

**Scenario 1: Active User**
```
9:00 AM - Login
9:30 AM - Create document (timer resets to 10:30 AM)
10:00 AM - Review document (timer resets to 11:00 AM)
10:30 AM - Upload file (timer resets to 11:30 AM)
11:00 AM - Approve document (timer resets to 12:00 PM)
...continues all day while active...
```
**Result:** ✅ Stays logged in all day with continuous activity

**Scenario 2: Inactive User**
```
9:00 AM - Login
9:30 AM - Start working on document
10:30 AM - Go to lunch (no activity)
11:30 AM - Session expires (1 hour of inactivity)
11:45 AM - Return and try to save → Redirected to login
```
**Result:** ❌ Must log in again after 1 hour of inactivity

---

### **Staging/Development (8-hour timeout):**

**Scenario: Developer Testing**
```
9:00 AM - Login
12:00 PM - Last activity before lunch
5:00 PM - Return (still logged in - only 5 hours passed)
6:00 PM - Still logged in (within 8-hour window)
```
**Result:** ✅ Can leave and return within 8 hours without re-login

---

## 🎯 Recommended Timeout Values

### **By Industry/Use Case:**

| Use Case | Recommended | Reasoning |
|----------|-------------|-----------|
| **Pharmaceutical (21 CFR Part 11)** | 1-2 hours | Regulatory compliance, security |
| **Healthcare (HIPAA)** | 15-30 minutes | Patient data protection |
| **General Office** | 4-8 hours | Convenience vs security balance |
| **High Security** | 15-60 minutes | Strict security requirements |
| **Development/Testing** | 8-24 hours | Developer convenience |

**Your Current Setup:**
- ✅ Production: 1 hour (Good for regulated environment)
- ✅ Staging: 8 hours (Good for testing)

---

## ⚙️ Changing Session Timeout

### **Option 1: Increase Production Timeout (2 hours)**

**When to use:** If 1 hour is too short for normal workflow

**Edit:** `backend/edms/settings/production.py` (line 113)

**Change from:**
```python
SESSION_COOKIE_AGE = 3600  # 1 hour for production
```

**Change to:**
```python
SESSION_COOKIE_AGE = 7200  # 2 hours for production
```

---

### **Option 2: Increase to 4 hours**

**When to use:** For longer work sessions, less frequent logins

**Change to:**
```python
SESSION_COOKIE_AGE = 14400  # 4 hours for production
```

---

### **Option 3: Match Staging (8 hours)**

**When to use:** If you want same experience as staging

**Change to:**
```python
SESSION_COOKIE_AGE = 28800  # 8 hours for production
```

---

### **Option 4: Regulatory Compliance (30 minutes)**

**When to use:** For strict compliance requirements

**Change to:**
```python
SESSION_COOKIE_AGE = 1800  # 30 minutes for production
```

---

## 🔒 Security vs Convenience Trade-off

### **Shorter Timeout (15-60 minutes):**

**Pros:**
- ✅ Better security
- ✅ Reduces risk if user walks away
- ✅ Meets strict compliance requirements
- ✅ Auto-logout on shared computers

**Cons:**
- ❌ More frequent logins
- ❌ Interrupts long workflows
- ❌ User frustration
- ❌ May lose unsaved work

---

### **Longer Timeout (4-8 hours):**

**Pros:**
- ✅ Better user experience
- ✅ Fewer interruptions
- ✅ Supports long workflows
- ✅ Less login friction

**Cons:**
- ❌ Security risk if user walks away
- ❌ May not meet strict compliance
- ❌ Higher risk on shared computers
- ❌ Session hijacking risk

---

## 💡 Best Practice Recommendations

### **For Your EDMS (Pharmaceutical):**

**Recommended Configuration:**
```python
# Production - Balanced for pharmaceutical environment
SESSION_COOKIE_AGE = 7200  # 2 hours

# Staging - Convenient for testing
SESSION_COOKIE_AGE = 28800  # 8 hours (keep as is)

# Development - Maximum convenience
SESSION_COOKIE_AGE = 28800  # 8 hours (keep as is)
```

**Why 2 hours for production?**
- ✅ Balances security and usability
- ✅ Sufficient for most workflows
- ✅ Acceptable for regulatory compliance
- ✅ Active users stay logged in
- ✅ Inactive users log out reasonably fast

---

## 🚀 Implementation

### **To Change Production Timeout:**

**Step 1: Edit production.py**
```bash
# On your local machine
nano backend/edms/settings/production.py

# Change line 113
SESSION_COOKIE_AGE = 7200  # 2 hours for production
```

**Step 2: Commit and push**
```bash
git add backend/edms/settings/production.py
git commit -m "config: Increase production session timeout to 2 hours"
git push origin develop
```

**Step 3: Merge to main**
```bash
git checkout main
git merge develop
git push origin main
```

**Step 4: Deploy to production**
```bash
# On production server
cd /home/lims/edms-production
git pull origin main

# Rebuild backend (settings are in the image)
docker compose -f docker-compose.prod.yml stop backend
docker compose -f docker-compose.prod.yml build --no-cache backend
docker compose -f docker-compose.prod.yml up -d backend
```

**Step 5: Verify**
```bash
# Check new setting is applied
docker compose -f docker-compose.prod.yml exec backend python manage.py shell

# In shell:
from django.conf import settings
print(f"Session timeout: {settings.SESSION_COOKIE_AGE} seconds")
print(f"Hours: {settings.SESSION_COOKIE_AGE / 3600}")
exit()
```

---

## 🧪 Testing Session Timeout

### **Test 1: Active Session**
1. Login to EDMS
2. Work continuously (create docs, navigate, etc.)
3. Continue for 2+ hours
4. **Expected:** Still logged in ✅

### **Test 2: Inactive Session**
1. Login to EDMS
2. Open a page
3. Leave browser idle for timeout duration + 5 minutes
4. Try to click something
5. **Expected:** Redirected to login ❌

### **Test 3: Timer Reset**
1. Login to EDMS
2. Wait 50 minutes (10 min before timeout)
3. Click something (resets timer)
4. Wait another 50 minutes
5. **Expected:** Still logged in ✅

---

## 📊 Monitoring Session Duration

### **Check Active Sessions:**

```python
# Django shell
from django.contrib.sessions.models import Session
from django.utils import timezone

# Count active sessions
Session.objects.filter(expire_date__gte=timezone.now()).count()

# List session expiry times
for session in Session.objects.filter(expire_date__gte=timezone.now()):
    print(f"Expires: {session.expire_date}")
```

---

## 🔔 User Notifications

### **Consider Implementing:**

**Warning Before Expiry (Optional Enhancement):**
- Show popup 5 minutes before timeout
- "Your session will expire in 5 minutes"
- Button to extend session
- Better user experience

**Frontend Implementation Idea:**
```javascript
// frontend/src/utils/sessionMonitor.ts
const SESSION_TIMEOUT = 2 * 60 * 60 * 1000; // 2 hours
const WARNING_TIME = 5 * 60 * 1000; // 5 minutes before

// Show warning at SESSION_TIMEOUT - WARNING_TIME
// Extend session with any user activity
```

---

## 📝 Session Configuration Summary

### **Current Settings:**

```python
# Session Storage
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'  # Redis
SESSION_CACHE_ALIAS = 'default'

# Timeout
SESSION_COOKIE_AGE = 3600  # 1 hour (production)
SESSION_SAVE_EVERY_REQUEST = True  # Reset on activity

# Security
SESSION_COOKIE_HTTPONLY = True  # Prevent JS access
SESSION_COOKIE_SECURE = False  # Set to True with HTTPS
SESSION_COOKIE_SAMESITE = 'Lax'  # CSRF protection

# Storage Location
# Sessions stored in Redis (fast, scalable)
# Automatically cleaned up when expired
```

---

## ⚡ Quick Reference

### **Common Timeout Values:**

| Minutes | Seconds | Use Case |
|---------|---------|----------|
| 15 | 900 | High security |
| 30 | 1,800 | HIPAA compliance |
| 60 | 3,600 | **Current production** |
| 120 | 7,200 | Recommended for EDMS |
| 240 | 14,400 | Extended workflows |
| 480 | 28,800 | **Current staging** |

---

## 🎯 Recommendation

**For your pharmaceutical EDMS:**

**Production:** Increase to **2 hours (7200 seconds)**
- Balances security and usability
- Sufficient for most document workflows
- Still meets regulatory requirements
- Reduces user login friction

**Keep Staging/Development at 8 hours**
- Convenient for testing
- Won't affect production users

---

## 📞 Questions to Consider

Before changing timeout, ask:

1. **What's the typical workflow duration?**
   - Creating documents
   - Review cycles
   - Approval processes

2. **What do regulatory requirements specify?**
   - 21 CFR Part 11 guidelines
   - Company security policy
   - Industry standards

3. **What do users prefer?**
   - Survey users
   - Check support tickets
   - Monitor login frequency

4. **How secure is the environment?**
   - Shared workstations?
   - Private offices?
   - Remote access?

---

## ✅ Summary

**Current:**
- Production: 1 hour
- Staging: 8 hours
- Active users stay logged in
- Inactive users log out

**Recommendation:**
- Increase production to 2 hours
- Provides better UX without compromising security
- Still compliant with regulatory requirements

**To implement:**
1. Edit `production.py` line 113
2. Change to `SESSION_COOKIE_AGE = 7200`
3. Commit and deploy

---

**Need help implementing this change?** Let me know! 🚀
