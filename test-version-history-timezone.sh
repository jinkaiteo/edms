#!/bin/bash
# Test VERSION_HISTORY timezone fix
# Run this on staging server after deployment

echo "Testing VERSION_HISTORY timezone fix..."
echo ""

docker compose -f docker-compose.prod.yml exec -T backend python manage.py shell <<EOF
from apps.placeholders.services import placeholder_service
from apps.documents.models import Document

# Get a document with version history
doc = Document.objects.filter(
    document_number__icontains='-v'
).first()

if doc:
    print(f"Testing with document: {doc.document_number}")
    print("")
    
    # Get version history data
    data = placeholder_service._get_version_history_data(doc)
    
    if 'error' not in data:
        print("Version History Data:")
        print(f"  Generated: {data.get('generated')}")
        print("")
        
        if data.get('rows'):
            print("  Version History Rows:")
            for row in data['rows'][:3]:  # Show first 3 rows
                print(f"    Version: {row['version']}")
                print(f"    Date: {row['date']}")
                print(f"    Author: {row['author']}")
                print(f"    Status: {row['status']}")
                print("")
            
            # Check if timezone is included
            first_date = data['rows'][0]['date']
            has_utc = 'UTC' in first_date
            generated_has_utc = 'UTC' in data.get('generated', '')
            
            print("Verification:")
            print(f"  {'✅' if has_utc else '❌'} Date includes UTC: {has_utc}")
            print(f"  {'✅' if generated_has_utc else '❌'} Generated timestamp includes UTC: {generated_has_utc}")
            
            if has_utc and generated_has_utc:
                print("\n🎉 VERSION_HISTORY TIMEZONE FIX WORKING!")
            else:
                print("\n⚠️  TIMEZONE NOT INCLUDED")
        else:
            print("  No version history rows found")
    else:
        print(f"  Error: {data.get('error')}")
else:
    print("⚠️  No documents with versions found")
EOF

echo ""
echo "Test complete!"
