#!/bin/bash
# Test script for periodic review migrations

echo "🧪 Testing Periodic Review Migrations..."
echo ""

# Check if backend container is running
if ! docker compose ps backend | grep -q "Up"; then
    echo "❌ Backend container not running. Please start with: docker compose up -d"
    exit 1
fi

echo "1️⃣ Checking current migration status..."
docker compose exec -T backend python manage.py showmigrations documents workflows 2>&1 | tail -20

echo ""
echo "2️⃣ Running makemigrations to detect new migrations..."
docker compose exec -T backend python manage.py makemigrations --dry-run 2>&1 | head -30

echo ""
echo "3️⃣ Checking migration plan..."
echo "--- Documents app ---"
docker compose exec -T backend python manage.py migrate documents --plan 2>&1 | tail -15
echo ""
echo "--- Workflows app ---"
docker compose exec -T backend python manage.py migrate workflows --plan 2>&1 | tail -15

echo ""
echo "✅ Migration test complete. Review output above."
echo ""
echo "To apply migrations for real, run:"
echo "  docker compose exec backend python manage.py migrate"
echo ""
echo "To test the API endpoints, run:"
echo "  ./test_periodic_review_api.sh"
