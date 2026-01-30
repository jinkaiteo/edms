#!/bin/bash

# Comprehensive Staging Placeholder Diagnosis
# Compare staging vs local to find why placeholders don't work

echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║                                                                  ║"
echo "║  STAGING PLACEHOLDER DIAGNOSTIC                                  ║"
echo "║                                                                  ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""

echo "=== 1. CHECK GIT STATUS ==="
echo "Current branch:"
git branch --show-current
echo ""
echo "Latest commit:"
git log --oneline -1
echo ""
echo "Latest 5 commits:"
git log --oneline -5
echo ""

echo "=== 2. VERIFY annotation_processor.py IN REPO ==="
echo "Checking if file has the 5 placeholder mappings..."
if grep -q "metadata\['DEPARTMENT'\]" backend/apps/documents/annotation_processor.py; then
    echo "✅ DEPARTMENT mapping found in repo file"
else
    echo "❌ DEPARTMENT mapping NOT in repo file"
fi

if grep -q "metadata\['DIGITAL_SIGNATURE'\]" backend/apps/documents/annotation_processor.py; then
    echo "✅ DIGITAL_SIGNATURE mapping found in repo file"
else
    echo "❌ DIGITAL_SIGNATURE mapping NOT in repo file"
fi

echo ""
echo "=== 3. CHECK DOCKER CONTAINER HAS UPDATED CODE ==="
echo "Checking if backend container has the updated annotation_processor.py..."

docker compose -f docker-compose.prod.yml exec backend sh -c '
if grep -q "metadata\[.DEPARTMENT.\]" /app/apps/documents/annotation_processor.py; then
    echo "✅ Container has DEPARTMENT mapping"
else
    echo "❌ Container MISSING DEPARTMENT mapping - NEEDS REBUILD!"
fi

if grep -q "metadata\[.DIGITAL_SIGNATURE.\]" /app/apps/documents/annotation_processor.py; then
    echo "✅ Container has DIGITAL_SIGNATURE mapping"
else
    echo "❌ Container MISSING DIGITAL_SIGNATURE mapping - NEEDS REBUILD!"
fi
'

echo ""
echo "=== 4. TEST METADATA GENERATION ==="
docker compose -f docker-compose.prod.yml exec backend python manage.py shell << 'PYEOF'
from apps.documents.annotation_processor import annotation_processor
from apps.documents.models import Document
from apps.users.models import User

print("\n--- Testing metadata generation ---")

# Get or create test document
doc = Document.objects.first()
if not doc:
    print("⚠️  No documents exist - creating test document")
    user = User.objects.filter(is_superuser=True).first()
    if user:
        from apps.documents.models import DocumentType, DocumentSource
        doc_type = DocumentType.objects.first()
        doc_source = DocumentSource.objects.first()
        
        if doc_type and doc_source:
            doc = Document.objects.create(
                title="Test Document",
                document_number="TEST-001",
                document_type=doc_type,
                document_source=doc_source,
                author=user,
                reviewer=user,
                approver=user,
                status='DRAFT',
                created_by=user
            )
            print("✅ Created test document")
        else:
            print("❌ No document types/sources")
            exit()
    else:
        print("❌ No users found")
        exit()

print(f"\nTesting with document: {doc.document_number}")
print(f"Author: {doc.author}")
print(f"Reviewer: {doc.reviewer}")
print(f"Approver: {doc.approver}")

# Generate metadata
try:
    metadata = annotation_processor.get_document_metadata(doc, doc.author)
    print(f"\n✅ Metadata generated: {len(metadata)} keys")
    
    # Check the 5 specific placeholders
    print("\n--- Checking 5 specific placeholders ---")
    placeholders = {
        'DEPARTMENT': metadata.get('DEPARTMENT', 'NOT FOUND'),
        'DIGITAL_SIGNATURE': metadata.get('DIGITAL_SIGNATURE', 'NOT FOUND'),
        'DOWNLOADED_DATE': metadata.get('DOWNLOADED_DATE', 'NOT FOUND'),
        'PREVIOUS_VERSION': metadata.get('PREVIOUS_VERSION', 'NOT FOUND'),
        'REVISION_COUNT': metadata.get('REVISION_COUNT', 'NOT FOUND')
    }
    
    success = 0
    for name, value in placeholders.items():
        if value != 'NOT FOUND':
            print(f"✅ {name}: '{value}'")
            success += 1
        else:
            print(f"❌ {name}: NOT FOUND")
    
    print(f"\nResult: {success}/5 placeholders working")
    
    if success < 5:
        print("\n⚠️  PROBLEM: Placeholders missing from metadata generation")
        print("This means annotation_processor.py code is OLD")
        
except Exception as e:
    print(f"\n❌ ERROR generating metadata: {e}")
    import traceback
    traceback.print_exc()
PYEOF

echo ""
echo "=== 5. CHECK DOCKER IMAGE AGE ==="
echo "When was backend image last built?"
docker images | grep backend | head -3

echo ""
echo "=== 6. RECOMMENDED ACTIONS ==="
echo ""
echo "If container is missing mappings or placeholders not found:"
echo "  1. docker compose -f docker-compose.prod.yml stop backend"
echo "  2. docker compose -f docker-compose.prod.yml build --no-cache backend"
echo "  3. docker compose -f docker-compose.prod.yml up -d backend"
echo "  4. Run this diagnostic again to verify"
echo ""
echo "If repo file is missing mappings:"
echo "  1. git fetch origin main"
echo "  2. git reset --hard origin/main"
echo "  3. Verify file has mappings"
echo "  4. Rebuild container"
echo ""

echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║                                                                  ║"
echo "║  DIAGNOSTIC COMPLETE                                             ║"
echo "║                                                                  ║"
echo "╚══════════════════════════════════════════════════════════════════╝"

