#!/bin/bash
# Test timezone fix on staging server
# Run this on the staging server: bash test-timezone-staging.sh

echo "Testing timezone fix on staging..."
echo ""

docker compose -f docker-compose.prod.yml exec -T backend python manage.py shell <<EOF
from apps.documents.annotation_processor import DocumentAnnotationProcessor
from apps.documents.models import Document
from django.contrib.auth import get_user_model

User = get_user_model()
processor = DocumentAnnotationProcessor()
doc = Document.objects.first()
user = User.objects.first()

if doc and user:
    metadata = processor.get_document_metadata(doc, user)
    print(f"DOWNLOAD_TIME: {metadata.get('DOWNLOAD_TIME')}")
    print(f"TIMEZONE: {metadata.get('TIMEZONE')}")
    has_utc = 'UTC' in str(metadata.get('DOWNLOAD_TIME', ''))
    print(f"\n{'✅' if has_utc else '❌'} Timezone working: {has_utc}")
else:
    print("No test data available")
EOF

echo ""
echo "Test complete!"
