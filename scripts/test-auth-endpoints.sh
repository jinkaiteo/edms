#!/bin/bash
#
# Test authentication endpoints
#

echo "Testing Backend Authentication Endpoints"
echo "========================================"
echo ""

# Test various auth endpoint variations
echo "1. Testing /api/v1/auth/token/ (expected endpoint):"
curl -X POST http://localhost:8001/api/v1/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"test123"}' \
  -w "\nHTTP Status: %{http_code}\n\n"

echo "2. Testing /api/auth/token/:"
curl -X POST http://localhost:8001/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"test123"}' \
  -w "\nHTTP Status: %{http_code}\n\n"

echo "3. Testing /auth/token/:"
curl -X POST http://localhost:8001/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"test123"}' \
  -w "\nHTTP Status: %{http_code}\n\n"

echo "4. Testing /api/v1/auth/login/:"
curl -X POST http://localhost:8001/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"test123"}' \
  -w "\nHTTP Status: %{http_code}\n\n"

echo "5. Listing Django URLs:"
docker compose -f docker-compose.prod.yml exec backend python manage.py show_urls 2>/dev/null | grep -i auth | head -20 || \
docker compose -f docker-compose.prod.yml exec backend python manage.py shell -c "from django.urls import get_resolver; print('\n'.join(str(p.pattern) for p in get_resolver().url_patterns))" 2>/dev/null | grep -i auth

echo ""
echo "6. Testing through HAProxy:"
curl -X POST http://localhost/api/v1/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"test123"}' \
  -w "\nHTTP Status: %{http_code}\n\n"
