# PostgreSQL Docker Setup for EDMS Workflow Testing

## Current Situation

✅ **Docker configuration exists**: Complete `docker-compose.yml` with PostgreSQL 18  
❌ **Docker not installed**: Need to install Docker first  
🎯 **Goal**: Set up PostgreSQL in Docker for proper workflow testing  

## Option 1: Quick PostgreSQL Setup (Recommended for Testing)

### Install PostgreSQL Directly (No Docker Required)
This is faster for immediate testing:

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install postgresql postgresql-contrib

# Start PostgreSQL service
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create database and user for EDMS
sudo -u postgres psql
CREATE DATABASE edms_workflow;
CREATE USER edms_user WITH PASSWORD 'edms_password';
GRANT ALL PRIVILEGES ON DATABASE edms_workflow TO edms_user;
\q
```

## Option 2: Full Docker Setup (Production-like)

### Install Docker and Docker Compose
```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker

# Install Docker Compose
sudo apt install docker-compose

# Verify installation
docker --version
docker-compose --version
```

### Start PostgreSQL Container
```bash
# Start only PostgreSQL (not full stack)
docker-compose up -d db

# Or start PostgreSQL + Redis for caching
docker-compose up -d db redis
```

## Recommended Approach for Immediate Testing

**Use Option 1 (Direct PostgreSQL)** because:
- ✅ Faster to set up (5 minutes vs 20 minutes)
- ✅ No Docker learning curve
- ✅ Same production database (PostgreSQL 18)
- ✅ Can test workflow immediately

**Switch to Docker later** when ready for full production setup.

## Next Steps After PostgreSQL Setup

1. **Update environment file**
2. **Install psycopg2** (PostgreSQL Python driver)  
3. **Run database migrations**
4. **Migrate workflow data**
5. **Test with PostgreSQL**

Would you like me to proceed with Option 1 (direct PostgreSQL) for immediate testing?