#!/bin/bash
# Quick Production Deployment for EDMS
# Simplified version for immediate testing

set -e

echo "🚀 Starting EDMS Production Deployment"
echo "======================================"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date '+%H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
    exit 1
}

# Check requirements
log "Checking requirements..."
if ! command -v docker &> /dev/null; then
    error "Docker is not installed"
fi

if ! docker info &> /dev/null; then
    error "Docker is not running"
fi

# Check environment file
if [[ ! -f ".env.prod" ]]; then
    error "Production environment file .env.prod not found"
fi

log "✓ Requirements check passed"

# Stop development containers if running
log "Stopping development containers..."
docker-compose down 2>/dev/null || true

# Build production images
log "Building production backend image..."
docker build -f infrastructure/containers/Dockerfile.backend \
    -t edms-backend:production ./backend || error "Backend build failed"

log "Building production frontend image..."
docker build -f infrastructure/containers/Dockerfile.frontend \
    -t edms-frontend:production ./frontend || error "Frontend build failed"

# Start production services
log "Starting production services..."
docker-compose -f docker-compose.prod.yml --env-file .env.prod up -d

# Wait for services
log "Waiting for services to start..."
sleep 30

# Check service health
log "Checking service health..."

# Database
if docker-compose -f docker-compose.prod.yml --env-file .env.prod exec -T db pg_isready -U edms_prod_user; then
    log "✓ Database is healthy"
else
    error "Database health check failed"
fi

# Redis
if docker-compose -f docker-compose.prod.yml --env-file .env.prod exec -T redis redis-cli -a EDMSProdRedis2024! ping | grep -q PONG; then
    log "✓ Redis is healthy"
else
    warn "Redis health check failed, but continuing..."
fi

# Backend (wait a bit longer)
log "Waiting for backend to fully start..."
sleep 20

if curl -f -s http://localhost:8001/health/ > /dev/null; then
    log "✓ Backend is healthy"
else
    warn "Backend health check failed, checking logs..."
    docker-compose -f docker-compose.prod.yml logs backend | tail -10
fi

# Frontend
if curl -f -s http://localhost:3001/health > /dev/null; then
    log "✓ Frontend is healthy"
else
    warn "Frontend health check failed"
fi

log "Production services started!"

echo
echo "🎯 Service URLs:"
echo "  Frontend:  http://localhost:3001"
echo "  Backend:   http://localhost:8001"
echo "  API Docs:  http://localhost:8001/api/docs/"
echo
echo "🧪 Next steps:"
echo "  Run tests: ./scripts/test-production-workflow.sh"
echo "  View logs: docker-compose -f docker-compose.prod.yml logs -f"
echo "  Stop:      docker-compose -f docker-compose.prod.yml down"

log "Production deployment completed!"