# Docker Networking Architecture - EDMS

## Why Do We Need Internal IP in ALLOWED_HOSTS?

**Short Answer:** You need the **host server's IP** (not Docker internal IPs) because users will access the application from their browsers using that IP.

---

## 🏗️ Network Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│  Physical Server (e.g., 192.168.1.100)                          │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Docker Network: edms_prod_network                       │   │
│  │  Subnet: 172.20.0.0/16 (internal Docker network)        │   │
│  │                                                           │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │   │
│  │  │  PostgreSQL  │  │   Backend    │  │   Frontend   │  │   │
│  │  │  (postgres)  │  │   (Django)   │  │   (React)    │  │   │
│  │  │              │  │              │  │              │  │   │
│  │  │  Internal:   │  │  Internal:   │  │  Internal:   │  │   │
│  │  │  172.20.0.2  │  │  172.20.0.3  │  │  172.20.0.4  │  │   │
│  │  │              │  │              │  │              │  │   │
│  │  │  No external │  │  Port mapped │  │  Port mapped │  │   │
│  │  │  port        │  │  8001:8000   │  │  3001:80     │  │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘  │   │
│  │                                                           │   │
│  └─────────────────────────────────────────────────────────┘   │
│         ↑                    ↑                    ↑              │
│         │                    │                    │              │
│         │              Port Mapping                              │
│         │                    │                    │              │
│  Not exposed          8001 → 8000            3001 → 80          │
│                              │                    │              │
└─────────────────────────────────────────────────────────────────┘
                               ↓                    ↓
                    http://192.168.1.100:8001  http://192.168.1.100:3001
                               ↑                    ↑
                               │                    │
                    ┌──────────┴────────────────────┴──────────┐
                    │  User Browser (Other Computer)           │
                    │  IP: 192.168.1.50                        │
                    │                                           │
                    │  Accesses: http://192.168.1.100:3001    │
                    └───────────────────────────────────────────┘
```

---

## 🔍 Understanding the Network Layers

### Layer 1: Docker Internal Network (172.20.0.0/16)

**Purpose:** Containers communicate with each other

```yaml
networks:
  edms_prod_network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
```

**Container Internal IPs (Examples):**
- PostgreSQL: `172.20.0.2:5432`
- Backend: `172.20.0.3:8000`
- Frontend: `172.20.0.4:80`
- Redis: `172.20.0.5:6379`

**Communication within Docker:**
```python
# Backend connects to PostgreSQL using service name:
DB_HOST=postgres  # Docker resolves to 172.20.0.2
DB_PORT=5432

# Backend connects to Redis:
REDIS_URL=redis://redis:6379  # Docker resolves to 172.20.0.5
```

---

### Layer 2: Port Mapping to Host

**Purpose:** Expose services to the host machine and network

```yaml
# Backend port mapping:
ports:
  - "8001:8000"  # Host:Container
  
# Frontend port mapping:
ports:
  - "3001:80"    # Host:Container
```

**What this means:**
- Request to `192.168.1.100:8001` → forwards to → Container `172.20.0.3:8000`
- Request to `192.168.1.100:3001` → forwards to → Container `172.20.0.4:80`

---

### Layer 3: Network Access (Users)

**Purpose:** Users access the application from their computers

**User access flow:**
1. User opens browser on computer (IP: `192.168.1.50`)
2. Types: `http://192.168.1.100:3001`
3. Request hits server at `192.168.1.100` port `3001`
4. Docker forwards to frontend container port `80`
5. Frontend serves the React app

---

## 🎯 Why ALLOWED_HOSTS Needs Host IP

### Django Security Check

Django's `ALLOWED_HOSTS` checks the `Host` header in HTTP requests:

```python
# When user accesses: http://192.168.1.100:3001
# HTTP Request Header contains:
Host: 192.168.1.100:3001
```

**Django checks:**
```python
if request_host not in ALLOWED_HOSTS:
    raise DisallowedHost("Invalid HTTP_HOST header")
```

**Therefore you need:**
```bash
ALLOWED_HOSTS=192.168.1.100,edms-server,localhost
```

---

## 📝 Common Misunderstandings

### ❌ Misconception 1: Use Docker Internal IPs

```bash
# WRONG - This won't work!
ALLOWED_HOSTS=172.20.0.3,172.20.0.4
```

**Why wrong:** Users never see or use these IPs. These are only for container-to-container communication.

### ❌ Misconception 2: Only localhost is needed

```bash
# INSUFFICIENT - This only works on the server itself!
ALLOWED_HOSTS=localhost,127.0.0.1
```

**Why insufficient:** Users on other computers can't access with localhost.

### ✅ Correct Configuration

```bash
# CORRECT - Covers all access methods
ALLOWED_HOSTS=192.168.1.100,edms-server,localhost,127.0.0.1
```

- `192.168.1.100` - Network users access via IP
- `edms-server` - Network users access via hostname
- `localhost` - Server admin accesses locally
- `127.0.0.1` - Server admin accesses locally

---

## 🌐 Access Scenarios

### Scenario 1: User on Different Computer

```
User Computer: 192.168.1.50
Server: 192.168.1.100

User types: http://192.168.1.100:3001
Django sees Host header: 192.168.1.100:3001
✅ ALLOWED_HOSTS must contain: 192.168.1.100
```

### Scenario 2: User Uses Hostname

```
User Computer: 192.168.1.50
Server hostname: edms-server

User types: http://edms-server:3001
Django sees Host header: edms-server:3001
✅ ALLOWED_HOSTS must contain: edms-server
```

### Scenario 3: Testing on Server Itself

```
On the server, admin types: http://localhost:3001
Django sees Host header: localhost:3001
✅ ALLOWED_HOSTS must contain: localhost
```

---

## 🔧 Simplified .env Configuration

Based on this understanding, here's what you actually need:

### Option A: Access by IP Only (Simplest)

```bash
# If users will access by IP only
ALLOWED_HOSTS=192.168.1.100,localhost,127.0.0.1

CORS_ALLOWED_ORIGINS=http://192.168.1.100:3001
CSRF_TRUSTED_ORIGINS=http://192.168.1.100:3001
```

### Option B: With Hostname (Recommended)

```bash
# If server has a hostname in DNS
ALLOWED_HOSTS=192.168.1.100,edms-server,localhost,127.0.0.1

CORS_ALLOWED_ORIGINS=http://192.168.1.100:3001,http://edms-server:3001
CSRF_TRUSTED_ORIGINS=http://192.168.1.100:3001,http://edms-server:3001
```

### Option C: Development (All Access)

```bash
# For testing/development - allows any host
ALLOWED_HOSTS=*
# WARNING: Don't use in production!
```

---

## 📊 Port Summary

| Service | Container Internal | Host Port | User Access URL |
|---------|-------------------|-----------|-----------------|
| Backend API | `172.20.0.3:8000` | `8001` | `http://192.168.1.100:8001` |
| Frontend | `172.20.0.4:80` | `3001` | `http://192.168.1.100:3001` |
| PostgreSQL | `172.20.0.2:5432` | `5433` | Not accessed by users |
| Redis | `172.20.0.5:6379` | `6380` | Not accessed by users |

**Why different ports for production?**
```yaml
# Development uses standard ports:
backend: 8000:8000
frontend: 3000:3000

# Production uses different ports to avoid conflicts:
backend: 8001:8000
frontend: 3001:80
```

---

## 🎯 What You Actually Need to Know

### For Deployment - Just Two Values:

1. **Find your server's IP:**
   ```bash
   # On the server, run:
   ip addr show | grep "inet " | grep -v 127.0.0.1
   # Example output: 192.168.1.100
   ```

2. **Update .env with that IP:**
   ```bash
   ALLOWED_HOSTS=192.168.1.100,localhost
   CORS_ALLOWED_ORIGINS=http://192.168.1.100:3001
   CSRF_TRUSTED_ORIGINS=http://192.168.1.100:3001
   ```

**That's it!** Docker handles all the internal networking automatically.

---

## 🔄 Complete Request Flow Example

```
1. User types in browser:
   http://192.168.1.100:3001

2. Request hits server network interface:
   192.168.1.100:3001

3. Docker port mapping forwards to:
   Container 172.20.0.4:80 (frontend)

4. Frontend serves React app

5. React app makes API call:
   http://192.168.1.100:8001/api/v1/documents/

6. Request hits server:
   192.168.1.100:8001

7. Docker forwards to:
   Container 172.20.0.3:8000 (backend)

8. Django checks:
   - Host header = "192.168.1.100:8001"
   - Is "192.168.1.100" in ALLOWED_HOSTS? ✅ Yes
   - Request processed

9. Django needs database:
   - Connects to: postgres:5432
   - Docker resolves to: 172.20.0.2:5432
   - No ALLOWED_HOSTS check (internal communication)

10. Response sent back through same path
```

---

## ✅ Revised Quick Setup

### You DON'T need to worry about:
- ❌ Docker internal IPs (172.20.x.x)
- ❌ Container service names (postgres, redis, backend)
- ❌ Docker networking configuration
- ❌ Port mapping details

### You ONLY need to know:
- ✅ Your server's IP on the network (e.g., 192.168.1.100)
- ✅ Users will access via: `http://YOUR-SERVER-IP:3001`
- ✅ Put that IP in ALLOWED_HOSTS and CORS settings

---

## 🔒 Security Note

**Internal Docker Network (172.20.0.0/16):**
- ✅ Isolated from external network
- ✅ PostgreSQL and Redis not exposed externally
- ✅ Only backend (8001) and frontend (3001) are accessible

**This is secure because:**
- Database has no external port mapping
- Redis has no external port mapping
- Only application interfaces are exposed
- Firewall can control access to ports 8001 and 3001

---

## 📝 Summary

**The server's internal IP in .env is NOT about Docker networking.**

**It's about:** Where users' browsers will send HTTP requests to access the application.

**Docker handles:** All the internal container-to-container networking automatically using service names.

**You configure:** The public-facing access points (ALLOWED_HOSTS, CORS) based on how users will reach your server.

---

**Bottom line:** Just put your server's IP address (the one users type in their browsers) in ALLOWED_HOSTS, and Docker takes care of the rest! 🎯
