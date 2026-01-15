# Docker Volume Permissions Management Guide

## Problem
When Docker containers run as root and create files in volume-mounted directories, those files are owned by root on the host system, making them difficult to manage.

## Current Situation
- Frontend container runs as **root** inside Docker
- Build files in `frontend/build/` are owned by **root** on host
- Local user (jinkaiteo, UID 1000) cannot delete or modify these files

## Solutions

### Option 1: Clean Build Files via Docker (Recommended for Development)

Use Docker to manage build artifacts since the container created them:

```bash
# Clean build directory via Docker
docker compose exec frontend rm -rf /app/build

# Build inside container
docker compose exec frontend npm run build

# Deploy the built files (if needed)
docker compose exec frontend npm run deploy
```

### Option 2: Use Docker Compose Override for Development

Create `docker-compose.override.yml` to fix permissions after build:

```yaml
# docker-compose.override.yml
services:
  frontend:
    # Add post-build command to fix permissions
    command: >
      sh -c "npm start && 
             if [ -d /app/build ]; then 
               chown -R 1000:1000 /app/build 2>/dev/null || true; 
             fi"
```

### Option 3: Helper Script for Permission Management

Create a helper script `scripts/fix-frontend-permissions.sh`:

```bash
#!/bin/bash
# Fix frontend build directory permissions

echo "Fixing frontend build directory permissions..."
docker compose exec frontend chown -R 1000:1000 /app/build 2>/dev/null || true
echo "✅ Permissions fixed!"
```

Make it executable:
```bash
chmod +x scripts/fix-frontend-permissions.sh
```

### Option 4: Production-Ready Solution (Recommended for Production)

Update `infrastructure/containers/Dockerfile.frontend`:

```dockerfile
FROM node:18-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Production stage
FROM nginx:alpine
COPY --from=builder /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

This uses multi-stage build - build artifacts never touch the host filesystem.

## Current Quick Fix

For immediate use, you have two options:

### Quick Fix A: Use Docker to Clean
```bash
# Remove build files via Docker
docker compose exec frontend rm -rf /app/build

# Rebuild
docker compose exec frontend npm run build
```

### Quick Fix B: Use sudo (Not Recommended)
```bash
# Only if you need to clean manually
sudo rm -rf frontend/build
npm run build  # Build on host
```

## Best Practice Recommendations

### For Development:
1. Keep Dockerfile as is (running as root is fine for dev)
2. Use `docker compose exec frontend` for all build operations
3. Never build directly on host to avoid mixing permissions

### For Production:
1. Use multi-stage Docker builds
2. Run containers as non-root users
3. Don't use volume mounts for build artifacts
4. Use nginx or similar to serve static files

## Current Status

✅ **Auth fixes applied** - Page refresh no longer logs out users
✅ **Route conflict resolved** - `/administration` route doesn't conflict with backend
✅ **Docker build working** - Container can successfully build the frontend
⚠️ **Permission issue** - Build files owned by root (expected in development)

## Next Steps

Choose your preferred solution above based on your workflow:
- **Development**: Use Option 1 (Docker exec commands)
- **Production**: Use Option 4 (Multi-stage builds)
- **Convenience**: Create helper script (Option 3)
