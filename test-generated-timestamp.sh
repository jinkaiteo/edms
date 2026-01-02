#!/bin/bash
# Test the "Generated:" timestamp in VERSION_HISTORY
# This tests the actual annotation output, not just the metadata

echo "Testing 'Generated:' timestamp in VERSION_HISTORY..."
echo ""

ssh lims@172.28.1.148 << 'ENDSSH'
cd /home/lims/edms-staging

echo "Testing _convert_table_data_to_text method..."
docker compose -f docker-compose.prod.yml exec -T backend python manage.py shell <<EOF
from apps.documents.annotation_processor import DocumentAnnotationProcessor
from apps.documents.models import Document

processor = DocumentAnnotationProcessor()
doc = Document.objects.filter(document_number__icontains='-v').first()

if doc:
    print(f"Testing with: {doc.document_number}")
    print("")
    
    # Get the table data
    table_data = processor._create_version_history_docx_table(doc)
    
    if table_data:
        # Convert to text format (this is what shows "Generated:")
        text_output = processor._convert_table_data_to_text(table_data)
        
        print("VERSION_HISTORY Text Output:")
        print("─" * 60)
        print(text_output)
        print("─" * 60)
        print("")
        
        # Check if "UTC" appears in the "Generated:" line
        lines = text_output.split('\n')
        generated_line = [line for line in lines if 'Generated:' in line]
        
        if generated_line:
            print(f"Generated line found: {generated_line[0]}")
            has_utc = 'UTC' in generated_line[0]
            print(f"{'✅' if has_utc else '❌'} Contains UTC: {has_utc}")
        else:
            print("❌ No 'Generated:' line found")
    else:
        print("⚠️  No table data returned")
else:
    print("⚠️  No versioned documents found")
EOF
ENDSSH

echo ""
echo "Test complete!"
