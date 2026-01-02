#!/bin/bash
# Verify ALL VERSION_HISTORY timestamp locations include UTC
# This checks all 3 places where timestamps appear

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_header "VERIFY ALL VERSION_HISTORY TIMESTAMPS"

print_info "Server: lims@172.28.1.148:/home/lims/edms-staging"
print_info "Testing all 3 timestamp locations in VERSION_HISTORY"
echo ""

ssh lims@172.28.1.148 << 'ENDSSH'
cd /home/lims/edms-staging

echo "════════════════════════════════════════════════════════════"
echo "LOCATION 1: Version Date (services.py line 407)"
echo "════════════════════════════════════════════════════════════"
echo ""

docker compose -f docker-compose.prod.yml exec -T backend python manage.py shell << 'PYTHON'
from apps.placeholders.services import placeholder_service
from apps.documents.models import Document

doc = Document.objects.filter(document_number__icontains='-v').first()

if doc:
    print(f"Testing with: {doc.document_number}")
    data = placeholder_service._get_version_history_data(doc)
    
    if 'error' not in data and data.get('rows'):
        first_row = data['rows'][0]
        print(f"\nVersion Date: {first_row['date']}")
        
        has_utc = 'UTC' in first_row['date']
        print(f"{'✅' if has_utc else '❌'} LOCATION 1 - Version date includes UTC: {has_utc}")
        
        if not has_utc:
            print("   Expected format: MM/DD/YYYY UTC")
            print(f"   Actual format:   {first_row['date']}")
    else:
        print("❌ No version data available")
else:
    print("⚠️  No versioned documents found")
PYTHON

echo ""
echo "════════════════════════════════════════════════════════════"
echo "LOCATION 2: Generated Metadata (services.py line 434)"
echo "════════════════════════════════════════════════════════════"
echo ""

docker compose -f docker-compose.prod.yml exec -T backend python manage.py shell << 'PYTHON'
from apps.placeholders.services import placeholder_service
from apps.documents.models import Document

doc = Document.objects.filter(document_number__icontains='-v').first()

if doc:
    data = placeholder_service._get_version_history_data(doc)
    
    if 'error' not in data:
        generated = data.get('generated')
        print(f"Generated Metadata: {generated}")
        
        has_utc = 'UTC' in str(generated)
        print(f"{'✅' if has_utc else '❌'} LOCATION 2 - Generated metadata includes UTC: {has_utc}")
        
        if not has_utc:
            print("   Expected format: MM/DD/YYYY HH:MM AM/PM UTC")
            print(f"   Actual format:   {generated}")
    else:
        print(f"❌ Error: {data.get('error')}")
else:
    print("⚠️  No versioned documents found")
PYTHON

echo ""
echo "════════════════════════════════════════════════════════════"
echo "LOCATION 3: Bottom Text (annotation_processor.py line 256)"
echo "════════════════════════════════════════════════════════════"
echo ""

docker compose -f docker-compose.prod.yml exec -T backend python manage.py shell << 'PYTHON'
from apps.documents.annotation_processor import DocumentAnnotationProcessor
from apps.documents.models import Document

processor = DocumentAnnotationProcessor()
doc = Document.objects.filter(document_number__icontains='-v').first()

if doc:
    # Create the version history table data
    table_data = processor._create_version_history_docx_table(doc)
    
    if table_data:
        # Convert to text format (this adds the "Generated:" line at bottom)
        text_output = processor._convert_table_data_to_text(table_data)
        
        # Find the "Generated:" line
        lines = text_output.split('\n')
        generated_line = [line for line in lines if 'Generated:' in line]
        
        if generated_line:
            print(f"Bottom Text Line: {generated_line[0]}")
            
            has_utc = 'UTC' in generated_line[0]
            print(f"{'✅' if has_utc else '❌'} LOCATION 3 - Bottom text includes UTC: {has_utc}")
            
            if not has_utc:
                print("   Expected format: Generated: MM/DD/YYYY HH:MM AM/PM UTC")
                print(f"   Actual format:   {generated_line[0]}")
        else:
            print("❌ No 'Generated:' line found in output")
    else:
        print("❌ No table data returned")
else:
    print("⚠️  No versioned documents found")
PYTHON

echo ""
echo "════════════════════════════════════════════════════════════"
echo "FINAL VERIFICATION"
echo "════════════════════════════════════════════════════════════"
echo ""

docker compose -f docker-compose.prod.yml exec -T backend python manage.py shell << 'PYTHON'
from apps.placeholders.services import placeholder_service
from apps.documents.annotation_processor import DocumentAnnotationProcessor
from apps.documents.models import Document

doc = Document.objects.filter(document_number__icontains='-v').first()

if doc:
    print(f"Document: {doc.document_number}")
    print("")
    
    # Check all three locations
    results = []
    
    # Location 1: Version date
    data = placeholder_service._get_version_history_data(doc)
    if 'error' not in data and data.get('rows'):
        loc1_pass = 'UTC' in data['rows'][0]['date']
        results.append(("Location 1 (Version date)", loc1_pass))
    else:
        results.append(("Location 1 (Version date)", False))
    
    # Location 2: Generated metadata
    if 'error' not in data:
        loc2_pass = 'UTC' in str(data.get('generated'))
        results.append(("Location 2 (Generated metadata)", loc2_pass))
    else:
        results.append(("Location 2 (Generated metadata)", False))
    
    # Location 3: Bottom text
    processor = DocumentAnnotationProcessor()
    table_data = processor._create_version_history_docx_table(doc)
    if table_data:
        text_output = processor._convert_table_data_to_text(table_data)
        generated_lines = [line for line in text_output.split('\n') if 'Generated:' in line]
        if generated_lines:
            loc3_pass = 'UTC' in generated_lines[0]
            results.append(("Location 3 (Bottom text)", loc3_pass))
        else:
            results.append(("Location 3 (Bottom text)", False))
    else:
        results.append(("Location 3 (Bottom text)", False))
    
    # Summary
    print("Summary:")
    print("─" * 60)
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {name}")
    
    print("─" * 60)
    
    all_passed = all(result[1] for result in results)
    
    if all_passed:
        print("\n🎉 ALL 3 LOCATIONS INCLUDE UTC - FIX COMPLETE!")
    else:
        failed_count = sum(1 for result in results if not result[1])
        print(f"\n⚠️  {failed_count} LOCATION(S) STILL MISSING UTC")
        print("\nAction needed: Rebuild backend container")
else:
    print("⚠️  No versioned documents found for testing")
PYTHON

ENDSSH

echo ""
print_header "VERIFICATION COMPLETE"
echo ""
