# HAProxy Setup in Deploy-Interactive.sh

## ✅ YES - HAProxy Setup is Included!

The `deploy-interactive.sh` script includes comprehensive HAProxy configuration and setup.

---

## 📋 What HAProxy Features Are Included

### 1. **Interactive Configuration** (Lines 312-332)

During deployment, you'll be asked:

```
? Will you be using HAProxy? [Y/n]: 
```

If you answer **yes**:
- Asks for HAProxy port (default: 80)
- Configures CORS origins without port numbers
- Sets up proper routing

If you answer **no**:
- Uses direct access with ports
- CORS configured for direct access

---

### 2. **Automatic HAProxy Installation** (Lines 760-861)

The script can install HAProxy automatically:

```bash
? Install HAProxy now? [Y/n]:
```

**What it does**:
- ✅ Installs HAProxy via apt/yum (based on your OS)
- ✅ Generates complete HAProxy configuration file
- ✅ Creates config at `/tmp/edms-haproxy.cfg`
- ✅ Provides manual installation instructions
- ✅ References detailed documentation

---

### 3. **Generated HAProxy Configuration** (Lines 791-843)

The script generates a complete HAProxy config with:

#### **Global Settings**:
- Logging configuration
- Max connections: 2000
- Daemon mode

#### **Compression**:
- gzip compression enabled
- Compresses: HTML, CSS, JS, JSON

#### **Stats Dashboard**:
- Accessible at port 8404
- URL: `http://your-server:8404`
- 30-second refresh
- Admin interface

#### **Frontend (Port 80)**:
- Listens on all interfaces (*:80)
- HTTP logging enabled
- Smart routing:
  - `/api/*` → Backend
  - `/admin/*` → Backend
  - `/static/*` → Backend
  - `/media/*` → Backend
  - `/health/*` → Backend
  - Everything else → Frontend

#### **Backend Servers**:
- **backend_servers**: Django backend on port 8001
  - Health check: `/health/`
  - Check interval: 10 seconds
  - Expects HTTP 200
  
- **frontend_servers**: React frontend on port 3001
  - Health check: `/`
  - Check interval: 10 seconds
  - Expects HTTP 200

---

## 🔧 How HAProxy Integration Works

### During Deployment:

**Step 1: Configuration Collection**
```
▶ HAProxy Configuration

? Will you be using HAProxy? [Y/n]: y
? HAProxy port (usually 80 or 443) [80]: 80
```

**Step 2: CORS Configuration**
If HAProxy enabled:
- CORS Origins: `http://your-server-ip` (no port!)
- CSRF Origins: Same as CORS

If HAProxy disabled:
- CORS Origins: `http://your-server-ip:3001` (with port!)

**Step 3: HAProxy Setup** (at end of deployment)
```
▶ HAProxy Setup

HAProxy configuration will be set up.
Refer to HAPROXY_INTEGRATION_GUIDE.md for detailed instructions.

? Install HAProxy now? [Y/n]: y
```

---

## 📊 What You Get

### Option A: HAProxy Enabled

**User Access**:
```
http://your-server-ip/           → Frontend (React)
http://your-server-ip/api/       → Backend (Django API)
http://your-server-ip/admin/     → Backend (Django Admin)
http://your-server-ip:8404       → HAProxy Stats
```

**Direct Access** (still works for admin/debugging):
```
http://your-server-ip:3001       → Frontend directly
http://your-server-ip:8001       → Backend directly
```

**Architecture**:
```
User Browser
     ↓
  Port 80 (HAProxy)
     ↓
     ├─→ /api/*     → Backend :8001
     ├─→ /admin/*   → Backend :8001
     └─→ /*         → Frontend :3001
```

---

### Option B: HAProxy Disabled

**User Access**:
```
http://your-server-ip:3001       → Frontend
http://your-server-ip:8001/api/  → Backend API
http://your-server-ip:8001/admin/ → Backend Admin
```

**Architecture**:
```
User Browser
     ↓
     ├─→ Port 3001  → Frontend
     └─→ Port 8001  → Backend
```

---

## 📁 Files Generated

When HAProxy is enabled, the script generates:

**1. `/tmp/edms-haproxy.cfg`** - Complete HAProxy configuration

**Contents**:
- Global settings (logging, maxconn, daemon)
- Defaults (timeouts, compression)
- Stats dashboard (port 8404)
- Frontend routing (port 80)
- Backend health checks

**2. Updated `.env` file** with:
```bash
CORS_ALLOWED_ORIGINS=http://your-server-ip  # No ports!
CSRF_TRUSTED_ORIGINS=http://your-server-ip  # No ports!
```

---

## 🚀 Manual Installation Steps (provided by script)

After HAProxy config is generated, the script tells you:

```bash
HAProxy configuration generated at: /tmp/edms-haproxy.cfg

Please review and install manually:
  sudo cp /tmp/edms-haproxy.cfg /etc/haproxy/haproxy.cfg
  sudo systemctl restart haproxy

For detailed setup, see: HAPROXY_INTEGRATION_GUIDE.md
```

---

## ✅ Benefits of HAProxy Integration

### 1. **Single Port Access**
- Users only need port 80 (or 443 for HTTPS)
- No confusing port numbers (:3001, :8001)
- Professional URL structure

### 2. **Automatic Routing**
- Frontend and backend on same domain
- No CORS complications
- Clean URLs for users

### 3. **Load Balancing Ready**
- Can add multiple backend servers easily
- Round-robin distribution
- Automatic health checks

### 4. **Health Monitoring**
- Built-in health checks every 10 seconds
- Automatic failover (if multiple backends)
- Stats dashboard on port 8404

### 5. **Compression**
- Automatic gzip compression
- Faster page loads
- Reduced bandwidth

---

## ⚠️ Important Notes

### HAProxy Installation is Semi-Automatic

**The script does**:
- ✅ Install HAProxy package
- ✅ Generate configuration file
- ✅ Configure CORS/CSRF correctly
- ✅ Provide installation instructions

**You must manually**:
- ⚠️ Copy config to `/etc/haproxy/haproxy.cfg`
- ⚠️ Restart HAProxy service
- ⚠️ Configure firewall if needed

**Why?** 
- Modifying `/etc/haproxy/` requires sudo
- Script runs as regular user
- Gives you chance to review config first

---

## 🎯 Recommended Approach for Staging

### Option 1: Enable HAProxy (Recommended for Production-like Test)

```
? Will you be using HAProxy? [Y/n]: y
? HAProxy port (usually 80 or 443) [80]: 80
? Install HAProxy now? [Y/n]: y
```

**Then manually**:
```bash
sudo cp /tmp/edms-haproxy.cfg /etc/haproxy/haproxy.cfg
sudo systemctl enable haproxy
sudo systemctl start haproxy

# Allow port 80 in firewall
sudo ufw allow 80/tcp
```

**Access**: `http://staging-server-ip/`

---

### Option 2: Disable HAProxy (Simpler for Initial Testing)

```
? Will you be using HAProxy? [Y/n]: n
```

**Access**: 
- Frontend: `http://staging-server-ip:3001`
- Backend: `http://staging-server-ip:8001`

**Can add HAProxy later** without redeploying!

---

## 🔧 Adding HAProxy After Deployment

If you initially deployed without HAProxy, you can add it later:

### 1. Install HAProxy

```bash
sudo apt install haproxy -y
```

### 2. Create Configuration

```bash
# Use the generated config from /tmp/edms-haproxy.cfg
# Or create new one based on template
sudo nano /etc/haproxy/haproxy.cfg
```

### 3. Update .env File

```bash
# Edit backend/.env
CORS_ALLOWED_ORIGINS=http://staging-server-ip
CSRF_TRUSTED_ORIGINS=http://staging-server-ip
```

### 4. Restart Services

```bash
# Restart backend to apply new CORS settings
docker compose -f docker-compose.prod.yml restart backend

# Start HAProxy
sudo systemctl restart haproxy
```

---

## 📊 Quick Comparison

| Feature | Without HAProxy | With HAProxy |
|---------|----------------|--------------|
| **Frontend URL** | `http://ip:3001` | `http://ip/` |
| **Backend API** | `http://ip:8001/api/` | `http://ip/api/` |
| **Admin** | `http://ip:8001/admin/` | `http://ip/admin/` |
| **Ports Needed** | 3001, 8001 | 80 (or 443) |
| **CORS Setup** | With ports | Without ports |
| **Professional Look** | ⚠️ Technical | ✅ Clean |
| **Setup Complexity** | ✅ Simple | ⚠️ More steps |

---

## 🎯 Recommendation for Your Staging Deployment

### **Start WITHOUT HAProxy**

**Reasons**:
1. ✅ Simpler initial testing
2. ✅ Fewer moving parts
3. ✅ Easier to debug
4. ✅ Can add later

**During deployment, choose**:
```
? Will you be using HAProxy? [Y/n]: n
```

**Test everything works first**, then add HAProxy if desired.

---

### **Add HAProxy Later** (if desired)

Once you verify everything works:
1. Install HAProxy
2. Copy generated config
3. Update CORS settings
4. Restart services
5. Test with HAProxy

This way you test both configurations!

---

## 📚 Additional Resources

The script references:
- `HAPROXY_INTEGRATION_GUIDE.md` - Detailed HAProxy setup
- Generated config at `/tmp/edms-haproxy.cfg`
- Stats dashboard at `http://ip:8404`

---

## ✅ Summary

**HAProxy setup in deploy-interactive.sh**:

✅ **Included**: Interactive prompts during configuration  
✅ **Included**: Automatic HAProxy installation  
✅ **Included**: Complete config generation  
✅ **Included**: CORS/CSRF auto-configuration  
✅ **Included**: Health checks and monitoring  
✅ **Included**: Stats dashboard  
⚠️ **Manual**: Final config copy and service restart  

**Recommendation**: Start without HAProxy for staging, add later if needed.

