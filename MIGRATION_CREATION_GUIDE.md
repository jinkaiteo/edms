# 🔧 Migration Creation Guide

## 🚨 **Current Issue**

Django needs to create migrations but requires interactive input to resolve questions about model changes.

---

## ⚡ **Quick Solution**

### **Option 1: Use Interactive Script (Recommended)**

```bash
./create_migrations_interactive.sh
```

This script will:
1. Guide you through creating migrations
2. Show you what questions to expect
3. Automatically apply migrations after creation
4. Run tests to show results

---

### **Option 2: Manual Step-by-Step**

#### **Step 1: Create Migrations for Scheduler**

```bash
docker exec -it edms_prod_backend python manage.py makemigrations scheduler
```

**Questions you'll be asked:**

**Question 1:**
```
Was scheduledtask.is_running renamed to scheduledtask.completed (a BooleanField)? [y/N]
```
**Answer:** `n` (Press 'n' then Enter)

**Question 2:**
```
It is impossible to add a non-nullable field 'scheduled_time' without specifying a default.
Please select a fix:
 1) Provide a one-off default now
 2) Quit
Select an option:
```
**Answer:** `1` (Press '1' then Enter)

**Question 3:**
```
Please enter the default value as valid Python.
```
**Answer:** `timezone.now()` (Type this exactly, then Enter)

---

#### **Step 2: Create Migrations for Workflows**

```bash
docker exec -it edms_prod_backend python manage.py makemigrations workflows
```

Answer any questions similarly:
- Renamed field? → `n`
- Need default? → `1` then provide appropriate default

---

#### **Step 3: Create Migrations for Documents**

```bash
docker exec -it edms_prod_backend python manage.py makemigrations documents
```

---

#### **Step 4: Create Remaining Migrations**

```bash
docker exec -it edms_prod_backend python manage.py makemigrations
```

---

#### **Step 5: Apply All Migrations**

```bash
docker exec edms_prod_backend python manage.py migrate
```

---

#### **Step 6: Run Tests**

```bash
./fix_migrations_and_test.sh
```

---

## 📋 **Common Migration Questions & Answers**

### **Question Type 1: Field Rename**
```
Was fieldA renamed to fieldB? [y/N]
```
**When to answer 'y':** Only if you actually renamed the field in the code  
**When to answer 'n':** If it's a new field or you deleted old one (most cases)  
**Recommendation:** `n` (safer - creates new field)

---

### **Question Type 2: Non-nullable Field**
```
It is impossible to add a non-nullable field without specifying a default.
Please select a fix:
 1) Provide a one-off default now
 2) Quit
Select an option:
```
**Answer:** `1`

---

### **Question Type 3: Default Value**
```
Please enter the default value as valid Python.
```

**Common defaults by field type:**

| Field Type | Default Value |
|------------|---------------|
| DateTimeField | `timezone.now()` |
| DateField | `timezone.now()` |
| BooleanField | `False` |
| IntegerField | `0` |
| CharField | `''` (empty string) |
| TextField | `''` (empty string) |
| ForeignKey | `None` (if nullable) |

**For scheduled_time:** Use `timezone.now()`

---

## 🎯 **Expected Results After Migration Creation**

### **Migration Files Created**
You should see output like:
```
Migrations for 'scheduler':
  scheduler/migrations/0006_auto_20260111_0120.py
    - Add field scheduled_time to scheduledtask
    - Remove field is_running from scheduledtask
    - Add field completed to scheduledtask
```

### **After Applying Migrations**
```
Running migrations:
  Applying scheduler.0006_auto_20260111_0120... OK
  Applying workflows.0010_workflownotification_is_read... OK
  Applying documents.0015_alter_document_status... OK
```

### **After Running Tests**
```
✓ Passed:    45-50 tests  (70-75%)
✗ Failed:     5-10 tests  (edge cases)
⚠ Errors:     0-5 tests   (minor issues)
```

---

## 🔍 **Troubleshooting**

### **Problem: "EOF when reading a line"**
**Cause:** Non-interactive shell can't read input  
**Solution:** Use `docker exec -it` (with `-it` flag) or use the interactive script

---

### **Problem: "Field already exists"**
**Cause:** Migration trying to add field that's already in database  
**Solution:** 
```bash
# Check existing migrations
docker exec edms_prod_backend python manage.py showmigrations

# If needed, fake the migration
docker exec edms_prod_backend python manage.py migrate --fake scheduler 0006
```

---

### **Problem: "No changes detected"**
**Cause:** Django doesn't see any model changes  
**Solution:** 
```bash
# Force check
docker exec edms_prod_backend python manage.py makemigrations --dry-run

# Check model definitions match
docker exec edms_prod_backend python manage.py check
```

---

## ⚡ **Fastest Path to Working Tests**

### **3-Minute Solution:**

```bash
# 1. Run interactive script (1 minute)
./create_migrations_interactive.sh
# Answer questions when prompted

# Result: Tests will run automatically
```

### **Expected Timeline:**
- Answer questions: 1-2 minutes
- Create migrations: 10 seconds
- Apply migrations: 10 seconds  
- Run tests: 30 seconds
- **Total: ~3 minutes**

---

## 📊 **What Happens Next**

After migrations are created and applied:

1. ✅ **Database schema matches models**
2. ✅ **Tests can set up test database**
3. ✅ **45-50 tests should PASS** (70-75%)
4. ❌ **5-10 tests might FAIL** (edge cases, scheduler tasks)
5. ⚠️ **0-5 tests might ERROR** (minor issues)

---

## 🎉 **Success Indicators**

You'll know it worked when you see:

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                         TEST RESULTS SUMMARY                                 ║
╚══════════════════════════════════════════════════════════════════════════════╝

✓ Passed:  48 tests
✗ Failed:   6 tests
Total:     54 tests

Pass Rate: 89%
```

---

## 🚀 **Ready to Fix Migrations?**

Choose your method:

### **Easy Way:**
```bash
./create_migrations_interactive.sh
```

### **Manual Way:**
Follow Step 1-6 above

### **Need Help:**
Read the "Common Migration Questions" section above

---

**Good luck! You're just 3 minutes away from passing tests!** 🎊
