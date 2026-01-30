#!/bin/bash

# Verify Staging Server Has Updated Code
# Check if annotation_processor.py has the 5 placeholder mappings

echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║                                                                  ║"
echo "║  VERIFYING STAGING SERVER CODE                                   ║"
echo "║                                                                  ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""

echo "=== Step 1: Check if code is pulled ==="
git log --oneline -1

echo ""
echo "=== Step 2: Check annotation_processor.py for new placeholders ==="
grep -n "DEPARTMENT\|DIGITAL_SIGNATURE\|DOWNLOADED_DATE\|PREVIOUS_VERSION\|REVISION_COUNT" backend/apps/documents/annotation_processor.py | head -10

echo ""
echo "=== Step 3: Check if backend container has the updated code ==="
docker compose -f docker-compose.prod.yml exec backend grep -c "DEPARTMENT" /app/apps/documents/annotation_processor.py || echo "NOT FOUND - Backend needs rebuild!"

echo ""
echo "=== Step 4: Test metadata generation ==="
docker compose -f docker-compose.prod.yml exec backend python manage.py shell << 'PYEOF'
from apps.documents.annotation_processor import annotation_processor
from apps.documents.models import Document

doc = Document.objects.first()
if doc:
    metadata = annotation_processor.get_document_metadata(doc)
    
    print("\n=== CHECKING FOR 5 PLACEHOLDERS IN METADATA ===")
    for name in ['DEPARTMENT', 'DIGITAL_SIGNATURE', 'DOWNLOADED_DATE', 'PREVIOUS_VERSION', 'REVISION_COUNT']:
        if name in metadata:
            print(f"✅ {name}: '{metadata[name]}'")
        else:
            print(f"❌ {name}: MISSING FROM METADATA")
else:
    print("No documents to test")
PYEOF

echo ""
echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║                                                                  ║"
echo "║  VERIFICATION COMPLETE                                           ║"
echo "║                                                                  ║"
echo "╚══════════════════════════════════════════════════════════════════╝"

