#!/bin/bash
set -e

echo "=== Email Configuration Root Cause Analysis ==="
echo ""

echo "1. Checking .env file EMAIL settings:"
echo "-----------------------------------"
if [ -f ".env" ]; then
    grep -E "^EMAIL_|^DEFAULT_FROM_EMAIL" .env
    echo ""
    echo "Line numbers:"
    grep -n -E "^EMAIL_|^DEFAULT_FROM_EMAIL" .env
else
    echo "❌ .env file not found"
fi

echo ""
echo "2. Checking backend/.env EMAIL settings:"
echo "-----------------------------------"
if [ -f "backend/.env" ]; then
    grep -E "^EMAIL_|^DEFAULT_FROM_EMAIL" backend/.env
    echo ""
    echo "Line numbers:"
    grep -n -E "^EMAIL_|^DEFAULT_FROM_EMAIL" backend/.env
else
    echo "❌ backend/.env file not found"
fi

echo ""
echo "3. Checking which .env file Docker uses:"
echo "-----------------------------------"
if [ -f "docker-compose.prod.yml" ]; then
    echo "Checking docker-compose.prod.yml for env_file:"
    grep -A2 "env_file:" docker-compose.prod.yml || echo "No env_file directives found"
fi

echo ""
echo "4. Checking running backend container environment:"
echo "-----------------------------------"
docker compose -f docker-compose.prod.yml exec -T backend env | grep -E "^EMAIL_|^DEFAULT_FROM_EMAIL" | sort || echo "❌ Backend not running or no EMAIL vars"

echo ""
echo "5. Checking if .env is being read at all:"
echo "-----------------------------------"
docker compose -f docker-compose.prod.yml exec -T backend python manage.py shell -c "
from django.conf import settings
import os

print('EMAIL_BACKEND:', settings.EMAIL_BACKEND)
print('EMAIL_HOST:', settings.EMAIL_HOST)
print('EMAIL_PORT:', settings.EMAIL_PORT)
print('EMAIL_USE_TLS:', settings.EMAIL_USE_TLS)
print('EMAIL_HOST_USER:', settings.EMAIL_HOST_USER)
print('DEFAULT_FROM_EMAIL:', settings.DEFAULT_FROM_EMAIL)
print('')
print('Environment variable EMAIL_HOST:', os.getenv('EMAIL_HOST', 'NOT SET'))
print('Environment variable EMAIL_PORT:', os.getenv('EMAIL_PORT', 'NOT SET'))
" 2>/dev/null || echo "❌ Cannot query Django settings"

echo ""
echo "=== Analysis Complete ==="
