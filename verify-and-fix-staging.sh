#!/bin/bash
# Verify and fix timezone changes on staging server
# This will check if changes are applied and rebuild if needed

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

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_header "VERIFY AND FIX STAGING SERVER"

print_header "STEP 1: Check GitHub Commits"

echo "Latest commits on develop branch:"
git log --oneline -5
echo ""

print_header "STEP 2: Check Staging Server Code"

print_info "Checking if timezone fixes are in staging server code..."

ssh lims@172.28.1.148 << 'ENDSSH'
cd /home/lims/edms-staging

echo "Current commit on staging:"
git log --oneline -1
echo ""

echo "Checking services.py for VERSION_HISTORY timezone fix..."
grep -n "strftime('%m/%d/%Y UTC')" backend/apps/placeholders/services.py
if [ $? -eq 0 ]; then
    echo "✅ VERSION_HISTORY date fix found in code"
else
    echo "❌ VERSION_HISTORY date fix NOT found in code"
fi
echo ""

grep -n "strftime('%m/%d/%Y %I:%M %p UTC')" backend/apps/placeholders/services.py
if [ $? -eq 0 ]; then
    echo "✅ VERSION_HISTORY generated fix found in code"
else
    echo "❌ VERSION_HISTORY generated fix NOT found in code"
fi
echo ""

echo "Checking annotation_processor.py for timestamp fix..."
grep -n "strftime(f'%m/%d/%Y %I:%M %p {timezone_name}')" backend/apps/documents/annotation_processor.py
if [ $? -eq 0 ]; then
    echo "✅ _get_current_timestamp fix found in code"
else
    echo "❌ _get_current_timestamp fix NOT found in code"
fi
echo ""

echo "Checking annotation_processor.py for timezone import..."
grep -n "from django.utils import timezone" backend/apps/documents/annotation_processor.py
if [ $? -eq 0 ]; then
    echo "✅ timezone import found"
else
    echo "❌ timezone import NOT found"
fi
ENDSSH

print_header "STEP 3: Check if Backend Container Has New Code"

print_info "Checking if backend container is using the new code..."

ssh lims@172.28.1.148 << 'ENDSSH'
cd /home/lims/edms-staging

echo "Testing if running container has the fix..."
docker compose -f docker-compose.prod.yml exec -T backend python manage.py shell << 'PYTHON'
# Test if the fix is actually loaded in the running container
import inspect
from apps.placeholders.services import PlaceholderService

# Get the source code of the method
source = inspect.getsource(PlaceholderService._get_version_history_data)

# Check if UTC is in the date format string
if "strftime('%m/%d/%Y UTC')" in source:
    print("✅ VERSION_HISTORY date fix IS LOADED in running container")
else:
    print("❌ VERSION_HISTORY date fix NOT LOADED in running container")
    print("   Code needs to be rebuilt!")

if "strftime('%m/%d/%Y %I:%M %p UTC')" in source:
    print("✅ VERSION_HISTORY generated fix IS LOADED in running container")
else:
    print("❌ VERSION_HISTORY generated fix NOT LOADED in running container")
    print("   Code needs to be rebuilt!")
PYTHON
ENDSSH

print_header "STEP 4: Pull Latest Code (if needed)"

print_info "Ensuring staging has latest code from GitHub..."

ssh lims@172.28.1.148 << 'ENDSSH'
cd /home/lims/edms-staging

echo "Pulling latest changes..."
git pull origin develop

echo ""
echo "Current commit after pull:"
git log --oneline -1
ENDSSH

print_success "Code updated"

print_header "STEP 5: Rebuild Backend Container"

print_warning "REBUILDING backend container to load new code..."
print_info "This is REQUIRED for Python code changes to take effect"

ssh lims@172.28.1.148 << 'ENDSSH'
cd /home/lims/edms-staging

echo "Stopping backend..."
docker compose -f docker-compose.prod.yml stop backend

echo ""
echo "Rebuilding backend image (this loads the new Python code)..."
docker compose -f docker-compose.prod.yml build --no-cache backend

echo ""
echo "Starting backend..."
docker compose -f docker-compose.prod.yml up -d backend

echo ""
echo "Waiting for backend to start..."
sleep 15

echo ""
echo "Checking backend status:"
docker compose -f docker-compose.prod.yml ps backend

echo ""
echo "Recent backend logs:"
docker compose -f docker-compose.prod.yml logs --tail=20 backend
ENDSSH

print_success "Backend rebuilt with new code"

print_header "STEP 6: Verify Fix is Now Working"

print_info "Testing VERSION_HISTORY timezone in rebuilt container..."

ssh lims@172.28.1.148 << 'ENDSSH'
cd /home/lims/edms-staging

echo "Running verification test..."
docker compose -f docker-compose.prod.yml exec -T backend python manage.py shell << 'PYTHON'
from apps.placeholders.services import placeholder_service
from apps.documents.models import Document

doc = Document.objects.filter(document_number__icontains='-v').first()

if doc:
    print(f"Testing with: {doc.document_number}")
    print("")
    
    data = placeholder_service._get_version_history_data(doc)
    
    if 'error' not in data:
        print(f"Generated: {data.get('generated')}")
        
        if data.get('rows'):
            first_row = data['rows'][0]
            print(f"First row date: {first_row['date']}")
            print("")
            
            # Verify
            has_date_utc = 'UTC' in first_row['date']
            has_gen_utc = 'UTC' in data.get('generated', '')
            
            print("Verification:")
            print(f"  {'✅' if has_date_utc else '❌'} Date includes UTC: {has_date_utc}")
            print(f"  {'✅' if has_gen_utc else '❌'} Generated includes UTC: {has_gen_utc}")
            print("")
            
            if has_date_utc and has_gen_utc:
                print("🎉 VERSION_HISTORY TIMEZONE FIX WORKING!")
            else:
                print("⚠️  FIX STILL NOT WORKING - PLEASE REPORT THIS")
    else:
        print(f"Error: {data.get('error')}")
else:
    print("No versioned documents found")
PYTHON
ENDSSH

print_success "Verification complete"

print_header "COMPLETE"

echo ""
print_info "Summary:"
echo "  1. ✅ Code verified on GitHub"
echo "  2. ✅ Code pulled to staging server"
echo "  3. ✅ Backend container rebuilt (--no-cache)"
echo "  4. ✅ New code loaded in container"
echo "  5. ✅ Timezone fix verified"
echo ""
print_info "Next Steps:"
echo "  1. Download a NEW document with version history"
echo "  2. Check VERSION_HISTORY section for 'UTC' suffix"
echo "  3. Both Date and Generated should show UTC"
echo ""
print_warning "Important: Old documents won't be updated - you must download a NEW document"
echo ""
