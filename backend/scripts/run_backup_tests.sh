#!/bin/bash
#
# Run all backup and restoration tests
#

set -e

echo "🧪 Running EDMS Backup & Restoration Test Suite"
echo "================================================"
echo ""

# Run Django unit tests
echo "📝 Running unit tests..."
docker compose exec backend python manage.py test apps.backup.tests.test_workflow_restoration --verbosity=2

echo ""
echo "📝 Running integration tests..."
docker compose exec backend python manage.py test apps.backup.tests.test_complete_restoration_flow --verbosity=2

echo ""
echo "✅ All Django tests completed!"
echo ""

# Run end-to-end test
echo "📝 Running end-to-end restoration test..."
./backend/scripts/test_workflow_restoration.sh

echo ""
echo "🎉 ALL TESTS PASSED!"
