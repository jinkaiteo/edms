#!/bin/bash

# Deploy Placeholder Fix to Staging
# Commit: a0a3f71 - Adds 5 missing placeholder mappings to annotation_processor.py

echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║                                                                  ║"
echo "║  DEPLOYING PLACEHOLDER FIX TO STAGING                            ║"
echo "║  Commit: a0a3f71                                                 ║"
echo "║                                                                  ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""

echo "=== Step 1/5: Check current commit ==="
git log --oneline -1

echo ""
echo "=== Step 2/5: Pull latest code from GitHub ==="
git fetch origin main
git pull origin main

echo ""
echo "=== Step 3/5: Verify annotation_processor.py has the fix ==="
if grep -q "metadata\['DEPARTMENT'\]" backend/apps/documents/annotation_processor.py; then
    echo "✅ Code has DEPARTMENT mapping"
else
    echo "❌ Code missing DEPARTMENT mapping - git pull may have failed"
    exit 1
fi

echo ""
echo "=== Step 4/5: Rebuild backend container with new code ==="
docker compose -f docker-compose.prod.yml stop backend
docker compose -f docker-compose.prod.yml build --no-cache backend
docker compose -f docker-compose.prod.yml up -d backend

echo ""
echo "Waiting 20 seconds for backend to start..."
sleep 20

echo ""
echo "=== Step 5/5: Verify placeholders work ==="
docker compose -f docker-compose.prod.yml exec backend python manage.py shell << 'PYEOF'
from apps.documents.annotation_processor import annotation_processor
from apps.documents.models import Document

doc = Document.objects.first()
if doc:
    metadata = annotation_processor.get_document_metadata(doc)
    
    print("\n=== PLACEHOLDER VERIFICATION ===")
    success_count = 0
    for name in ['DEPARTMENT', 'DIGITAL_SIGNATURE', 'DOWNLOADED_DATE', 'PREVIOUS_VERSION', 'REVISION_COUNT']:
        if name in metadata:
            print(f"✅ {name}: Present (value: '{str(metadata[name])[:50]}...')")
            success_count += 1
        else:
            print(f"❌ {name}: MISSING")
    
    print(f"\nResult: {success_count}/5 placeholders working")
    
    if success_count == 5:
        print("\n✅ SUCCESS: All 5 placeholders are working!")
    else:
        print(f"\n❌ FAILURE: {5-success_count} placeholders still missing")
else:
    print("⚠️  No documents in database to test with")
PYEOF

echo ""
echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║                                                                  ║"
echo "║  ✅ DEPLOYMENT COMPLETE                                          ║"
echo "║                                                                  ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""
echo "Now test by:"
echo "1. Creating a document with placeholders"
echo "2. Approving it"
echo "3. Downloading the official PDF"
echo "4. Verify all placeholders are replaced"

