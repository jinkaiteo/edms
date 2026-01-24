#!/bin/bash
echo "=== Checking Email Configuration ==="
echo ""
echo "1. .env file EMAIL settings:"
grep -E "^EMAIL_|^DEFAULT_FROM_EMAIL" backend/.env 2>/dev/null || grep -E "^EMAIL_|^DEFAULT_FROM_EMAIL" .env 2>/dev/null
echo ""
echo "2. Running backend container EMAIL environment:"
docker compose exec -T backend env | grep -E "^EMAIL_|^DEFAULT_FROM_EMAIL" | sort
echo ""
echo "=== End Check ==="
