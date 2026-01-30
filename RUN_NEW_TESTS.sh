#!/bin/bash
# Run new tests for PDF viewer and superuser management

echo "=========================================="
echo "EDMS QA - Running New Feature Tests"
echo "=========================================="
echo ""

cd /home/jinkaiteo/Documents/QMS/QMS_04

echo "📦 Rebuilding backend container with new tests..."
docker compose build backend

echo ""
echo "🧪 Running PDF Viewer Tests..."
docker compose exec backend pytest apps/documents/tests/test_pdf_viewer.py -v

echo ""
echo "🧪 Running Superuser Management Tests..."
docker compose exec backend pytest apps/users/tests/test_superuser_management.py -v

echo ""
echo "📊 Running All Tests with Coverage..."
docker compose exec backend pytest --cov=apps --cov-report=term-missing

echo ""
echo "✅ Testing complete!"
echo ""
