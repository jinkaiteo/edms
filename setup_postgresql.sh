#!/bin/bash

# PostgreSQL Setup Script for EDMS Workflow Testing
# This script sets up PostgreSQL directly (no Docker required)

echo "🚀 Setting up PostgreSQL for EDMS Workflow Testing"
echo "================================================="

# Check if running with sudo
if [ "$EUID" -eq 0 ]; then
    echo "❌ Please do not run this script as root"
    echo "   Run: ./setup_postgresql.sh"
    exit 1
fi

# Function to check command success
check_success() {
    if [ $? -eq 0 ]; then
        echo "   ✅ $1"
    else
        echo "   ❌ $1 failed"
        exit 1
    fi
}

# Update package list
echo ""
echo "📦 Updating package list..."
sudo apt update
check_success "Package list updated"

# Install PostgreSQL
echo ""
echo "🗄️ Installing PostgreSQL..."
sudo apt install -y postgresql postgresql-contrib postgresql-client
check_success "PostgreSQL installed"

# Start and enable PostgreSQL
echo ""
echo "🔄 Starting PostgreSQL service..."
sudo systemctl start postgresql
check_success "PostgreSQL started"

sudo systemctl enable postgresql
check_success "PostgreSQL enabled for auto-start"

# Check PostgreSQL status
echo ""
echo "📊 PostgreSQL status:"
sudo systemctl status postgresql --no-pager -l

# Create database and user
echo ""
echo "🔧 Setting up EDMS database and user..."

# Create the database setup SQL
cat > /tmp/edms_setup.sql << EOF
-- Create database
CREATE DATABASE edms_workflow;

-- Create user
CREATE USER edms_user WITH PASSWORD 'edms_password';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE edms_workflow TO edms_user;

-- Grant schema permissions
\c edms_workflow
GRANT ALL ON SCHEMA public TO edms_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO edms_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO edms_user;

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Show created database and user
\l edms_workflow
\du edms_user
EOF

# Execute the setup SQL
sudo -u postgres psql -f /tmp/edms_setup.sql
check_success "Database and user created"

# Clean up temp file
rm /tmp/edms_setup.sql

# Test connection
echo ""
echo "🧪 Testing database connection..."
PGPASSWORD='edms_password' psql -h localhost -U edms_user -d edms_workflow -c "SELECT version();"
check_success "Database connection test"

# Install Python PostgreSQL adapter
echo ""
echo "🐍 Installing Python PostgreSQL adapter..."
cd backend
source venv/bin/activate
pip install psycopg2-binary
check_success "psycopg2 installed"

# Create environment file
echo ""
echo "📝 Creating environment configuration..."
cat > .env << EOF
# PostgreSQL Database Configuration
DB_NAME=edms_workflow
DB_USER=edms_user
DB_PASSWORD=edms_password
DB_HOST=localhost
DB_PORT=5432

# Other settings
SECRET_KEY=workflow-dev-secret-key-for-testing
DEBUG=True
EOF
check_success "Environment file created"

echo ""
echo "🎉 PostgreSQL setup complete!"
echo ""
echo "📋 Connection Details:"
echo "   Database: edms_workflow"
echo "   User: edms_user"
echo "   Password: edms_password" 
echo "   Host: localhost"
echo "   Port: 5432"
echo ""
echo "🔄 Next steps:"
echo "   1. Run: cd backend && python manage.py migrate"
echo "   2. Run: python prepare_workflow_testing.py"
echo "   3. Start backend: python manage.py runserver 8002"
echo ""
echo "✅ Ready for PostgreSQL workflow testing!"