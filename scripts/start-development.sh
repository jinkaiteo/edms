#!/bin/bash
#
# EDMS Development Environment Startup Script
# 
# This script initializes and starts the EDMS development environment
# with all necessary services and dependencies.

set -e

echo "🚀 Starting EDMS Development Environment"
echo "======================================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose is not installed. Please install it and try again."
    exit 1
fi

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p logs storage/documents storage/media storage/backups

# Copy environment file if it doesn't exist
if [ ! -f backend/.env ]; then
    echo "📋 Creating environment file..."
    cp backend/.env.example backend/.env
    echo "⚠️  Please edit backend/.env with your configuration"
fi

# Initialize flag
INIT=false
if [ "$1" = "--init" ] || [ "$1" = "-i" ]; then
    INIT=true
fi

# Start services
echo "🐳 Starting Docker services..."
docker-compose up -d db redis

# Wait for database to be ready
echo "⏳ Waiting for database to be ready..."
sleep 10

if [ "$INIT" = true ]; then
    echo "🔧 Initializing database..."
    
    # Build and run migrations
    docker-compose build backend
    docker-compose run --rm backend python manage.py migrate
    
    # Create superuser (interactive)
    echo "👤 Creating superuser..."
    docker-compose run --rm backend python manage.py createsuperuser
    
    # Load initial data
    echo "📊 Loading initial data..."
    docker-compose run --rm backend python manage.py loaddata initial_roles
fi

# Start all services
echo "🚀 Starting all services..."
docker-compose up -d

# Install frontend dependencies if needed
if [ ! -d "frontend/node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    cd frontend && npm install && cd ..
fi

echo ""
echo "✅ EDMS Development Environment is ready!"
echo ""
echo "🌐 Services:"
echo "   Frontend: http://localhost:3000"
echo "   Backend:  http://localhost:8000"
echo "   Admin:    http://localhost:8000/admin"
echo "   API Docs: http://localhost:8000/api/v1/docs/"
echo ""
echo "📊 Monitoring:"
echo "   Logs:     docker-compose logs -f [service]"
echo "   Status:   docker-compose ps"
echo ""
echo "⚠️  Note: If this is your first run, use --init flag to initialize the database"
echo ""

# Show running containers
docker-compose ps