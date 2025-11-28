# Docker Architecture Migration Guide

## 🚨 **CRITICAL SECURITY ISSUE IDENTIFIED**

**Current Setup:** All services exposed externally (INSECURE)
**Intended Setup:** Only frontend exposed externally (SECURE)

## 📊 **Current vs Intended Architecture**

### ❌ **CURRENT (INSECURE)**
```
Internet → Port 3000 → Frontend ✓
Internet → Port 8000 → Backend  ❌ SECURITY RISK
Internet → Port 5432 → Database ❌ CRITICAL RISK  
Internet → Port 6379 → Redis    ❌ SECURITY RISK
```

### ✅ **INTENDED (SECURE)**
```
Internet → Port 3000 → Frontend → Internal Network → Backend
                                                   → Database
                                                   → Redis
```

## 🔧 **Migration Steps**

### Step 1: Stop Current Containers
```bash
docker-compose down
```

### Step 2: Backup Current Configuration
```bash
cp docker-compose.yml docker-compose.yml.backup
```

### Step 3: Use Secure Configuration
```bash
cp docker-compose-secure.yml docker-compose.yml
```

### Step 4: Update Frontend API Configuration
The frontend currently uses `http://localhost:8000` but should use `http://backend:8000` for internal communication.

**Update these files:**
- `frontend/src/setupProxy.js` - Remove or update proxy
- Any direct API calls to `localhost:8000` → use relative paths `/api/v1/`

### Step 5: Start Secure Stack
```bash
docker-compose up -d
```

## 🛡️ **Security Benefits After Migration**

### **1. Network Isolation**
- ✅ Backend only accessible from within Docker network
- ✅ Database only accessible from backend containers
- ✅ Redis only accessible from backend/worker containers
- ✅ No direct external access to internal services

### **2. Single Entry Point**
- ✅ All external traffic goes through frontend (port 3000)
- ✅ Frontend handles authentication before API calls
- ✅ Nginx reverse proxy provides additional security

### **3. Production Ready**
- ✅ Nginx serves static files efficiently
- ✅ Security headers automatically added
- ✅ CORS properly configured
- ✅ Rate limiting possible
- ✅ SSL termination ready

## 🔍 **Verification Commands**

After migration, verify security:

```bash
# Should show ONLY frontend port exposed
docker ps --format "table {{.Names}}\t{{.Ports}}"

# Should show secure network
docker network inspect edms_network

# Test external access (should work)
curl http://localhost:3000

# Test internal access (should fail)
curl http://localhost:8000  # Should be refused
curl http://localhost:5432  # Should be refused
curl http://localhost:6379  # Should be refused
```

## 🚨 **IMMEDIATE RISKS OF CURRENT SETUP**

### **Critical (Database Exposed)**
- **Direct database access** from internet
- **No authentication** required for PostgreSQL
- **Full data access** possible from outside

### **High (Backend API Exposed)**
- **Bypass frontend authentication** by calling API directly
- **Direct API manipulation** possible
- **Internal system structure** exposed

### **Medium (Redis Exposed)**
- **Session hijacking** possible
- **Cache poisoning** attacks
- **Memory dump** access

## 📋 **Post-Migration Checklist**

- [ ] Only port 3000 exposed externally
- [ ] Backend accessible only via internal network
- [ ] Database accessible only from backend
- [ ] Redis accessible only from backend/workers
- [ ] Frontend loads correctly on port 3000
- [ ] API calls work through nginx proxy
- [ ] Authentication flow works end-to-end
- [ ] File uploads/downloads work
- [ ] Workflow notifications function

## 🎯 **Expected Final State**

```
EXTERNAL ACCESS:
✅ http://localhost:3000 → EDMS Application

INTERNAL ONLY:
🔒 backend:8000     → Django API (not externally accessible)
🔒 db:5432          → PostgreSQL (not externally accessible)  
🔒 redis:6379       → Redis (not externally accessible)
🔒 Internal network → Container communication only
```

This migration will transform the current **development-style** exposed setup into a **production-ready** secure architecture.