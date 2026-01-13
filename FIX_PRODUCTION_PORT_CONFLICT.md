# Fix Production Port Conflict - Port 5433 Already in Use

## 🔴 Problem

Production deployment failed with:
```
Error: failed to bind host port for 0.0.0.0:5433:172.20.0.2:5432/tcp: address already in use
```

**Cause**: Port 5433 is already in use on the production server (likely by staging or another PostgreSQL instance)

---

## 🔍 Diagnose the Issue

### Step 1: Check What's Using Port 5433

```bash
# SSH to production server
ssh lims@172.28.1.149  # or your production server IP

# Check what's using port 5433
sudo lsof -i :5433

# Or use netstat
sudo netstat -tlnp | grep 5433

# Or use ss
sudo ss -tlnp | grep 5433
```

**Possible outputs:**

**Scenario A: Staging Docker container**
```
COMMAND    PID   USER   FD   TYPE DEVICE SIZE/OFF NODE NAME
docker-pr  1234  root   4u   IPv4  12345      0t0  TCP *:5433 (LISTEN)
```

**Scenario B: PostgreSQL service**
```
COMMAND    PID      USER   FD   TYPE DEVICE SIZE/OFF NODE NAME
postgres   1234  postgres   5u   IPv4  12345      0t0  TCP *:5433 (LISTEN)
```

---

## ✅ Solution Options

### Option 1: Change Production Ports (Recommended)

Production and staging should use **different ports** to avoid conflicts.

#### Suggested Port Mapping:
| Service | Staging | Production |
|---------|---------|------------|
| Frontend | 3001 | 3002 |
| Backend | 8001 | 8002 |
| Database | 5433 | 5434 |
| Redis | 6380 | 6381 |

#### Update Production Ports:

```bash
# On production server
cd /home/lims/edms-production  # or your production path

# Edit docker-compose.prod.yml
nano docker-compose.prod.yml
```

**Change these port mappings:**

```yaml
services:
  db:
    ports:
      - "5434:5432"  # Changed from 5433 to 5434
  
  redis:
    ports:
      - "6381:6379"  # Changed from 6380 to 6381
  
  backend:
    ports:
      - "8002:8000"  # Changed from 8001 to 8002
    environment:
      - DB_PORT=5432  # Internal port stays same
      - DB_HOST=db
  
  frontend:
    ports:
      - "3002:80"     # Changed from 3001 to 3002
```

**Then deploy:**
```bash
docker compose -f docker-compose.prod.yml up -d
```

---

### Option 2: Stop Staging to Deploy Production

If you only need one environment at a time:

```bash
# SSH to server
ssh lims@172.28.1.149

# Stop staging containers
cd /home/lims/edms-staging
docker compose -f docker-compose.prod.yml down

# Now deploy production
cd /home/lims/edms-production
docker compose -f docker-compose.prod.yml up -d
```

**Note**: This stops staging completely.

---

### Option 3: Use Internal-Only Database Ports

If you don't need external database access, remove port exposure:

```yaml
services:
  db:
    # Remove the ports section entirely
    # ports:
    #   - "5433:5432"
    
    # Containers can still access via internal network
```

**Backend connects using internal hostname:**
```yaml
backend:
  environment:
    - DB_HOST=db  # Uses internal Docker network
    - DB_PORT=5432  # Internal port, not exposed to host
```

---

## 🚀 Quick Fix for Production Deployment

### Step 1: Create Production-Specific Compose File

```bash
# On production server
cd /home/lims/edms-production

# Copy and modify
cp docker-compose.prod.yml docker-compose.prod-custom.yml
nano docker-compose.prod-custom.yml
```

### Step 2: Update Ports in docker-compose.prod-custom.yml

```yaml
version: '3.8'

services:
  db:
    image: postgres:18
    container_name: edms_prod_db
    environment:
      POSTGRES_DB: edms_prod
      POSTGRES_USER: edms_user
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_prod_data:/var/lib/postgresql/data
    ports:
      - "5434:5432"  # ← Changed from 5433
    networks:
      - edms_prod_network

  redis:
    image: redis:7-alpine
    container_name: edms_prod_redis
    ports:
      - "6381:6379"  # ← Changed from 6380
    networks:
      - edms_prod_network

  backend:
    build:
      context: ./backend
      dockerfile: ../infrastructure/containers/Dockerfile.backend.prod
    container_name: edms_prod_backend
    ports:
      - "8002:8000"  # ← Changed from 8001
    environment:
      - DB_HOST=db
      - DB_PORT=5432  # Internal port
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis
    networks:
      - edms_prod_network

  frontend:
    build:
      context: ./frontend
      dockerfile: ../infrastructure/containers/Dockerfile.frontend.prod
    container_name: edms_prod_frontend
    ports:
      - "3002:80"  # ← Changed from 3001
    depends_on:
      - backend
    networks:
      - edms_prod_network

volumes:
  postgres_prod_data:

networks:
  edms_prod_network:
    driver: bridge
```

### Step 3: Deploy with Custom Compose File

```bash
# Stop any existing production containers
docker compose -f docker-compose.prod.yml down

# Start with new ports
docker compose -f docker-compose.prod-custom.yml up -d

# Check status
docker compose -f docker-compose.prod-custom.yml ps
```

### Step 4: Test Production

```bash
# Test frontend
curl http://localhost:3002/

# Test backend
curl http://localhost:8002/health/

# Test from your machine (replace with actual production IP)
curl http://172.28.1.149:3002/
```

---

## 🔧 Interactive Script Fix

If you're using the interactive deployment script, modify it to use different ports for production:

### Update deploy-interactive.sh

```bash
nano deploy-interactive.sh
```

Find the port configuration section and update defaults:

```bash
# Around line 250-260
collect_configuration() {
    # ...
    
    if [ "$DEPLOY_TYPE" = "production" ]; then
        FRONTEND_PORT=${FRONTEND_PORT:-3002}  # Changed from 3001
        BACKEND_PORT=${BACKEND_PORT:-8002}    # Changed from 8001
        DB_PORT=${DB_PORT:-5434}              # Changed from 5433
        REDIS_PORT=${REDIS_PORT:-6381}        # Changed from 6380
    else
        FRONTEND_PORT=${FRONTEND_PORT:-3001}
        BACKEND_PORT=${BACKEND_PORT:-8001}
        DB_PORT=${DB_PORT:-5433}
        REDIS_PORT=${REDIS_PORT:-6380}
    fi
}
```

---

## 🎯 Recommended Solution

**For production server, use different ports:**

```bash
# 1. Edit docker-compose.prod.yml on production server
cd /home/lims/edms-production
nano docker-compose.prod.yml

# 2. Change ports:
#    Database: 5433 → 5434
#    Redis: 6380 → 6381
#    Backend: 8001 → 8002
#    Frontend: 3001 → 3002

# 3. Deploy
docker compose -f docker-compose.prod.yml up -d

# 4. Test
curl http://localhost:3002/
curl http://localhost:8002/health/
```

---

## 📋 Port Conflict Prevention Checklist

**Before deploying multiple environments:**

- [ ] Plan port allocation for each environment
- [ ] Document port mappings
- [ ] Check for port conflicts: `sudo lsof -i :PORT`
- [ ] Update docker-compose files with unique ports
- [ ] Update firewall rules if needed
- [ ] Test each environment independently

**Standard Port Allocation:**

| Environment | Frontend | Backend | Database | Redis |
|-------------|----------|---------|----------|-------|
| Development | 3000 | 8000 | 5432 | 6379 |
| Staging | 3001 | 8001 | 5433 | 6380 |
| Production | 3002 | 8002 | 5434 | 6381 |

---

## 🔍 Additional Diagnostics

### Check All Docker Containers

```bash
# See all running containers
docker ps -a

# Check if staging is running
docker ps | grep edms_staging

# Check port bindings
docker ps --format "table {{.Names}}\t{{.Ports}}"
```

### Check All Listening Ports

```bash
# See all services listening on ports
sudo netstat -tlnp | grep -E ':(3001|3002|5433|5434|6380|6381|8001|8002)'
```

---

## 🚀 Quick Command Sequence

```bash
# On production server
cd /home/lims/edms-production

# Edit compose file
nano docker-compose.prod.yml
# Change: 5433→5434, 6380→6381, 8001→8002, 3001→3002

# Deploy with new ports
docker compose -f docker-compose.prod.yml up -d

# Verify
docker compose -f docker-compose.prod.yml ps
curl http://localhost:3002/
```

---

## ✅ After Fixing

**Production will be accessible at:**
- Frontend: `http://YOUR_PROD_IP:3002`
- Backend API: `http://YOUR_PROD_IP:8002/api/v1`
- Health check: `http://YOUR_PROD_IP:8002/health/`

**Staging remains at:**
- Frontend: `http://172.28.1.148:3001`
- Backend API: `http://172.28.1.148:8001/api/v1`

---

## 📞 Need Help?

**If you need to:**
1. Check what's on port 5433: `sudo lsof -i :5433`
2. Stop staging: `docker compose down` in staging directory
3. Change production ports: Edit `docker-compose.prod.yml`
4. Kill process on port: `sudo kill -9 PID`

Let me know which solution you'd like to use! 🚀
