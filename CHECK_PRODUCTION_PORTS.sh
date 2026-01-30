#!/bin/bash
# Check which docker-compose file and ports are being used on production

echo "=========================================="
echo "PRODUCTION PORT CONFIGURATION CHECK"
echo "=========================================="
echo ""

echo "1. Checking .env file:"
echo "----------------------"
if [ -f .env ]; then
    echo "✅ .env file exists"
    grep -E "BACKEND_PORT|FRONTEND_PORT|DB_PORT" .env
else
    echo "❌ .env file not found!"
fi
echo ""

echo "2. Checking running containers:"
echo "--------------------------------"
docker compose ps 2>/dev/null || docker-compose ps 2>/dev/null || echo "No containers running"
echo ""

echo "3. Checking port bindings:"
echo "--------------------------"
docker ps --format "table {{.Names}}\t{{.Ports}}" | grep -E "backend|frontend|db"
echo ""

echo "4. Which docker-compose.yml is active:"
echo "---------------------------------------"
if docker compose -f docker-compose.prod.yml ps >/dev/null 2>&1; then
    echo "✅ Using docker-compose.prod.yml"
    echo "   Backend should be on port: ${BACKEND_PORT:-8001}"
    echo "   Frontend should be on port: ${FRONTEND_PORT:-3001}"
elif docker compose ps >/dev/null 2>&1; then
    echo "⚠️  Using default docker-compose.yml"
    echo "   Backend is on port: 8000 (hardcoded)"
    echo "   Frontend is on port: 3000 (hardcoded)"
fi
echo ""

echo "5. Recommendation:"
echo "------------------"
echo "Production should use: docker-compose.prod.yml"
echo "Command: docker compose -f docker-compose.prod.yml up -d"
