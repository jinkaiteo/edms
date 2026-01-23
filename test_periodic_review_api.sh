#!/bin/bash
# Test script for periodic review API endpoints

echo "🧪 Testing Periodic Review API Endpoints..."
echo ""

# Configuration
BACKEND_URL="http://localhost:8001"
API_BASE="${BACKEND_URL}/api/v1"

# Check if backend is running
if ! curl -s "${BACKEND_URL}/health/" > /dev/null 2>&1; then
    echo "❌ Backend not reachable at ${BACKEND_URL}"
    echo "Please start the backend with: docker compose up -d backend"
    exit 1
fi

echo "✅ Backend is running"
echo ""

# Test 1: Get documents with periodic_review filter
echo "1️⃣ Testing periodic review filter..."
echo "GET ${API_BASE}/documents/?filter=periodic_review"
curl -s "${API_BASE}/documents/?filter=periodic_review" \
  -H "Authorization: Bearer YOUR_TOKEN" | jq -r '.count' 2>/dev/null || echo "No auth token - use browser or set TOKEN"

echo ""
echo ""

# Test 2: Get first EFFECTIVE document (for testing)
echo "2️⃣ Finding an EFFECTIVE document for testing..."
FIRST_DOC_UUID=$(curl -s "${API_BASE}/documents/?status=EFFECTIVE&limit=1" \
  -H "Authorization: Bearer YOUR_TOKEN" 2>/dev/null | jq -r '.results[0].uuid' 2>/dev/null)

if [ "$FIRST_DOC_UUID" != "null" ] && [ -n "$FIRST_DOC_UUID" ]; then
    echo "Found document: ${FIRST_DOC_UUID}"
    
    echo ""
    echo "3️⃣ Testing initiate-periodic-review endpoint..."
    echo "POST ${API_BASE}/documents/${FIRST_DOC_UUID}/initiate-periodic-review/"
    echo "(This requires authentication - test via browser or Postman)"
    
    echo ""
    echo "4️⃣ Testing review-history endpoint..."
    echo "GET ${API_BASE}/documents/${FIRST_DOC_UUID}/review-history/"
    curl -s "${API_BASE}/documents/${FIRST_DOC_UUID}/review-history/" \
      -H "Authorization: Bearer YOUR_TOKEN" 2>/dev/null | jq '.' || echo "No auth - use browser"
else
    echo "No EFFECTIVE documents found. Create one first to test."
fi

echo ""
echo ""
echo "✅ API endpoint discovery complete"
echo ""
echo "📝 Manual testing steps:"
echo "1. Login to http://localhost:3001"
echo "2. Navigate to an EFFECTIVE document"
echo "3. Look for 'Periodic Review' button (to be implemented in frontend)"
echo "4. Test complete review flow"
