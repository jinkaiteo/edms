# PostgreSQL Setup Instructions for EDMS

## Current Status
✅ **PostgreSQL installed**: psql command available  
✅ **psycopg2 installed**: Python PostgreSQL driver ready  
❗ **Database setup needed**: Need to create database and user  

## Manual Setup Required

Since the automated setup requires admin permissions, please run these commands manually:

### 1. Start PostgreSQL Service (if needed)
```bash
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

### 2. Create Database and User
```bash
# Switch to postgres user and run psql
sudo -u postgres psql

# In the PostgreSQL prompt, run:
CREATE DATABASE edms_workflow;
CREATE USER edms_user WITH PASSWORD 'edms_password';
GRANT ALL PRIVILEGES ON DATABASE edms_workflow TO edms_user;

# Connect to the database and grant schema permissions
\c edms_workflow
GRANT ALL ON SCHEMA public TO edms_user;

# Exit psql
\q
```

### 3. Test Connection
```bash
PGPASSWORD='edms_password' psql -h localhost -U edms_user -d edms_workflow -c "SELECT version();"
```

## Alternative: Use Existing SQLite for Now

If PostgreSQL setup is complex, we can:
1. **Continue with SQLite** for immediate workflow testing
2. **Switch to PostgreSQL later** when ready for production

The workflow functionality will work the same with both databases.

## What Should We Do?

**Option A**: Complete PostgreSQL setup manually (recommended for production-like testing)  
**Option B**: Continue with SQLite for immediate workflow testing  
**Option C**: Use Docker (requires Docker installation)  

Which would you prefer?