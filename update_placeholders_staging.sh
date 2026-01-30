#!/bin/bash

# Update Staging with Missing 5 Placeholders
# This adds: DEPARTMENT, DIGITAL_SIGNATURE, DOWNLOADED_DATE, PREVIOUS_VERSION, REVISION_COUNT

echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║                                                                  ║"
echo "║  UPDATING PLACEHOLDERS ON STAGING                                ║"
echo "║  Adding 5 missing placeholders (32 → 35)                         ║"
echo "║                                                                  ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""

# Check current count
echo "=== Step 1/3: Checking current placeholder count ==="
docker compose -f docker-compose.prod.yml exec backend python manage.py shell -c "
from apps.placeholders.models import PlaceholderDefinition
print(f'Current placeholders: {PlaceholderDefinition.objects.filter(is_active=True).count()}')
"

echo ""
echo "=== Step 2/3: Re-running setup_placeholders command ==="
echo "This will add the 5 missing placeholders that were added in recent updates..."
docker compose -f docker-compose.prod.yml exec backend python manage.py setup_placeholders

echo ""
echo "=== Step 3/3: Verifying new placeholder count ==="
docker compose -f docker-compose.prod.yml exec backend python manage.py shell -c "
from apps.placeholders.models import PlaceholderDefinition

# Check the 5 specific placeholders
added_placeholders = ['DEPARTMENT', 'DIGITAL_SIGNATURE', 'DOWNLOADED_DATE', 'PREVIOUS_VERSION', 'REVISION_COUNT']

print('\n=== VERIFICATION ===')
for name in added_placeholders:
    exists = PlaceholderDefinition.objects.filter(name=name, is_active=True).exists()
    status = '✅' if exists else '❌'
    print(f'{status} {name}')

total = PlaceholderDefinition.objects.filter(is_active=True).count()
print(f'\nTotal active placeholders: {total}')

if total == 35:
    print('✅ SUCCESS: All 35 placeholders present!')
else:
    print(f'⚠️  Expected 35, got {total}')
"

echo ""
echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║                                                                  ║"
echo "║  ✅ PLACEHOLDER UPDATE COMPLETE                                  ║"
echo "║                                                                  ║"
echo "╚══════════════════════════════════════════════════════════════════╝"

