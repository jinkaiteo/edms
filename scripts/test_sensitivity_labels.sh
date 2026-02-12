#!/bin/bash
# Sensitivity Label System Test Script
# Comprehensive testing of all sensitivity label features

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

TESTS_PASSED=0
TESTS_FAILED=0
TESTS_SKIPPED=0

print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

print_test() {
    echo -e "${YELLOW}→ $1${NC}"
}

print_pass() {
    echo -e "${GREEN}✓ $1${NC}"
    ((TESTS_PASSED++))
}

print_fail() {
    echo -e "${RED}✗ $1${NC}"
    ((TESTS_FAILED++))
}

print_skip() {
    echo -e "${YELLOW}⊘ $1${NC}"
    ((TESTS_SKIPPED++))
}

# Check if running in correct directory
if [ ! -f "docker compose.yml" ]; then
    echo -e "${RED}Error: docker compose.yml not found. Please run from project root.${NC}"
    exit 1
fi

print_header "Sensitivity Label System - Test Suite"

# Test 1: Database Schema
print_header "Test Suite 1: Database Schema"

print_test "Test 1.1: Verify sensitivity columns exist"
docker compose exec -T backend python manage.py shell << 'PYEOF'
from django.db import connection
cursor = connection.cursor()
cursor.execute("""
    SELECT column_name 
    FROM information_schema.columns 
    WHERE table_name='documents_document' 
    AND column_name LIKE 'sensitivity%'
    ORDER BY column_name;
""")
columns = [row[0] for row in cursor.fetchall()]
expected = ['sensitivity_change_reason', 'sensitivity_inherited_from_id', 
            'sensitivity_label', 'sensitivity_set_at', 'sensitivity_set_by_id']

if set(columns) == set(expected):
    print("PASS: All 5 sensitivity columns found")
    exit(0)
else:
    print(f"FAIL: Expected {expected}, found {columns}")
    exit(1)
PYEOF
[ $? -eq 0 ] && print_pass "Sensitivity columns exist" || print_fail "Sensitivity columns missing"

print_test "Test 1.2: Verify indexes created"
docker compose exec -T backend python manage.py shell << 'PYEOF'
from django.db import connection
cursor = connection.cursor()
cursor.execute("""
    SELECT indexname 
    FROM pg_indexes 
    WHERE tablename='documents_document' 
    AND indexname LIKE '%sensitivity%'
    ORDER BY indexname;
""")
indexes = [row[0] for row in cursor.fetchall()]

if len(indexes) >= 2:
    print(f"PASS: Found {len(indexes)} sensitivity indexes")
    exit(0)
else:
    print(f"FAIL: Expected at least 2 indexes, found {len(indexes)}")
    exit(1)
PYEOF
[ $? -eq 0 ] && print_pass "Indexes created" || print_fail "Indexes missing"

# Test 2: Configuration Files
print_header "Test Suite 2: Configuration Files"

print_test "Test 2.1: Verify sensitivity_labels.py exists"
if docker compose exec -T backend test -f apps/documents/sensitivity_labels.py; then
    print_pass "sensitivity_labels.py exists"
else
    print_fail "sensitivity_labels.py not found"
fi

print_test "Test 2.2: Verify 5 sensitivity tiers configured"
docker compose exec -T backend python manage.py shell << 'PYEOF'
from apps.documents.sensitivity_labels import SENSITIVITY_CHOICES, SENSITIVITY_METADATA

if len(SENSITIVITY_CHOICES) == 5:
    print("PASS: 5 sensitivity tiers configured")
    print(f"  Tiers: {[c[0] for c in SENSITIVITY_CHOICES]}")
    exit(0)
else:
    print(f"FAIL: Expected 5 tiers, found {len(SENSITIVITY_CHOICES)}")
    exit(1)
PYEOF
[ $? -eq 0 ] && print_pass "5 tiers configured" || print_fail "Incorrect tier count"

print_test "Test 2.3: Verify watermark_processor.py exists"
if docker compose exec -T backend test -f apps/documents/watermark_processor.py; then
    print_pass "watermark_processor.py exists"
else
    print_fail "watermark_processor.py not found"
fi

print_test "Test 2.4: Verify 13 status watermarks configured"
docker compose exec -T backend python manage.py shell << 'PYEOF'
from apps.documents.watermark_processor import WatermarkProcessor
processor = WatermarkProcessor()

if len(processor.STATUS_CONFIG) == 13:
    print("PASS: 13 status watermarks configured")
    exit(0)
else:
    print(f"FAIL: Expected 13 statuses, found {len(processor.STATUS_CONFIG)}")
    exit(1)
PYEOF
[ $? -eq 0 ] && print_pass "13 status watermarks configured" || print_fail "Incorrect status count"

# Test 3: Placeholder System
print_header "Test Suite 3: Placeholder System"

print_test "Test 3.1: Verify sensitivity placeholders in annotation_processor"
docker compose exec -T backend python manage.py shell << 'PYEOF'
from apps.documents.models import Document
from apps.documents.annotation_processor import DocumentAnnotationProcessor

doc = Document.objects.first()
if not doc:
    print("SKIP: No documents in database")
    exit(2)

processor = DocumentAnnotationProcessor()
metadata = processor.get_document_metadata(doc)

required_placeholders = [
    'SENSITIVITY_LABEL',
    'SENSITIVITY_LABEL_FULL',
    'SENSITIVITY_LABEL_ICON',
    'IF_CONFIDENTIAL',
    'IF_RESTRICTED',
    'IF_PROPRIETARY',
    'SENSITIVITY_SET_BY',
    'SENSITIVITY_SET_DATE',
    'SENSITIVITY_WATERMARK'
]

missing = [p for p in required_placeholders if p not in metadata]

if not missing:
    print("PASS: All 9 core placeholders found")
    exit(0)
else:
    print(f"FAIL: Missing placeholders: {missing}")
    exit(1)
PYEOF
result=$?
[ $result -eq 0 ] && print_pass "All sensitivity placeholders work" || \
[ $result -eq 2 ] && print_skip "No documents to test" || \
print_fail "Placeholders missing"

print_test "Test 3.2: Test placeholder replacement"
docker compose exec -T backend python manage.py shell << 'PYEOF'
from apps.documents.models import Document
from apps.documents.annotation_processor import DocumentAnnotationProcessor

doc = Document.objects.first()
if not doc:
    print("SKIP: No documents in database")
    exit(2)

processor = DocumentAnnotationProcessor()
metadata = processor.get_document_metadata(doc)

# Test basic placeholder
if metadata['SENSITIVITY_LABEL'] in ['PUBLIC', 'INTERNAL', 'CONFIDENTIAL', 'RESTRICTED', 'PROPRIETARY']:
    print(f"PASS: SENSITIVITY_LABEL = {metadata['SENSITIVITY_LABEL']}")
    exit(0)
else:
    print(f"FAIL: Invalid SENSITIVITY_LABEL: {metadata['SENSITIVITY_LABEL']}")
    exit(1)
PYEOF
result=$?
[ $result -eq 0 ] && print_pass "Placeholder replacement works" || \
[ $result -eq 2 ] && print_skip "No documents to test" || \
print_fail "Placeholder replacement failed"

# Test 4: Watermark System
print_header "Test Suite 4: Watermark System"

print_test "Test 4.1: Test watermark processor initialization"
docker compose exec -T backend python manage.py shell << 'PYEOF'
from apps.documents.watermark_processor import watermark_processor

# Test CONFIDENTIAL + DRAFT
info = watermark_processor.get_watermark_status('CONFIDENTIAL', 'DRAFT')

if info['has_sensitivity_header'] and info['has_status_watermark']:
    print("PASS: CONFIDENTIAL + DRAFT shows both watermarks")
    exit(0)
else:
    print("FAIL: Watermark configuration incorrect")
    exit(1)
PYEOF
[ $? -eq 0 ] && print_pass "Watermark processor works" || print_fail "Watermark processor failed"

print_test "Test 4.2: Test EFFECTIVE documents have no diagonal"
docker compose exec -T backend python manage.py shell << 'PYEOF'
from apps.documents.watermark_processor import watermark_processor

info = watermark_processor.get_watermark_status('INTERNAL', 'EFFECTIVE')

if not info['has_status_watermark']:
    print("PASS: EFFECTIVE documents have no diagonal watermark")
    exit(0)
else:
    print("FAIL: EFFECTIVE documents should not have diagonal watermark")
    exit(1)
PYEOF
[ $? -eq 0 ] && print_pass "EFFECTIVE documents are clean" || print_fail "EFFECTIVE watermark incorrect"

print_test "Test 4.3: Test all 13 status configurations"
docker compose exec -T backend python manage.py shell << 'PYEOF'
from apps.documents.watermark_processor import WatermarkProcessor
processor = WatermarkProcessor()

statuses_to_test = [
    ('DRAFT', True),
    ('PENDING_REVIEW', True),
    ('UNDER_REVIEW', True),
    ('REVIEW_COMPLETED', True),
    ('PENDING_APPROVAL', True),
    ('UNDER_APPROVAL', True),
    ('APPROVED', True),
    ('APPROVED_PENDING_EFFECTIVE', True),
    ('EFFECTIVE', False),
    ('SCHEDULED_FOR_OBSOLESCENCE', True),
    ('SUPERSEDED', True),
    ('OBSOLETE', True),
    ('TERMINATED', True),
]

all_passed = True
for status, should_watermark in statuses_to_test:
    config = processor.STATUS_CONFIG.get(status, {})
    has_watermark = config.get('show_watermark', False)
    if has_watermark != should_watermark:
        print(f"FAIL: {status} watermark={has_watermark}, expected={should_watermark}")
        all_passed = False

if all_passed:
    print("PASS: All 13 status watermarks correctly configured")
    exit(0)
else:
    exit(1)
PYEOF
[ $? -eq 0 ] && print_pass "All status watermarks configured" || print_fail "Status watermark configuration error"

# Test 5: Document Operations
print_header "Test Suite 5: Document Operations"

print_test "Test 5.1: Verify existing documents have sensitivity"
docker compose exec -T backend python manage.py shell << 'PYEOF'
from apps.documents.models import Document

total = Document.objects.count()
if total == 0:
    print("SKIP: No documents in database")
    exit(2)

with_sensitivity = Document.objects.exclude(sensitivity_label__isnull=True).count()

if with_sensitivity == total:
    print(f"PASS: All {total} documents have sensitivity labels")
    exit(0)
else:
    print(f"FAIL: {with_sensitivity}/{total} documents have sensitivity")
    exit(1)
PYEOF
result=$?
[ $result -eq 0 ] && print_pass "All documents have sensitivity" || \
[ $result -eq 2 ] && print_skip "No documents to test" || \
print_fail "Some documents missing sensitivity"

print_test "Test 5.2: Test document sensitivity distribution"
docker compose exec -T backend python manage.py shell << 'PYEOF'
from apps.documents.models import Document
from django.db.models import Count

total = Document.objects.count()
if total == 0:
    print("SKIP: No documents in database")
    exit(2)

distribution = Document.objects.values('sensitivity_label').annotate(count=Count('id'))
print("Document Sensitivity Distribution:")
for item in distribution:
    percentage = (item['count'] / total) * 100
    print(f"  {item['sensitivity_label']}: {item['count']} ({percentage:.1f}%)")

print("PASS: Distribution calculated")
exit(0)
PYEOF
result=$?
[ $result -eq 0 ] && print_pass "Sensitivity distribution calculated" || \
[ $result -eq 2 ] && print_skip "No documents to test" || \
print_fail "Distribution calculation failed"

# Test 6: API Integration
print_header "Test Suite 6: API Integration"

print_test "Test 6.1: Test if sensitivity fields in serializer"
docker compose exec -T backend python manage.py shell << 'PYEOF'
import inspect
from apps.documents.serializers import DocumentListSerializer

# Check if sensitivity_label field exists in serializer
serializer_code = inspect.getsource(DocumentListSerializer)

if 'sensitivity_label' in serializer_code:
    print("PASS: sensitivity_label found in DocumentListSerializer")
    exit(0)
else:
    print("FAIL: sensitivity_label not found in DocumentListSerializer")
    exit(1)
PYEOF
[ $? -eq 0 ] && print_pass "Serializer has sensitivity fields" || print_fail "Serializer missing sensitivity fields"

# Test 7: Frontend Components
print_header "Test Suite 7: Frontend Components"

print_test "Test 7.1: Verify SensitivityBadge component exists"
if [ -f "frontend/src/components/common/SensitivityBadge.tsx" ]; then
    print_pass "SensitivityBadge.tsx exists"
else
    print_fail "SensitivityBadge.tsx not found"
fi

print_test "Test 7.2: Verify SensitivityLabelSelector component exists"
if [ -f "frontend/src/components/workflows/SensitivityLabelSelector.tsx" ]; then
    print_pass "SensitivityLabelSelector.tsx exists"
else
    print_fail "SensitivityLabelSelector.tsx not found"
fi

# Test 8: Documentation
print_header "Test Suite 8: Documentation"

print_test "Test 8.1: Verify classification guide exists"
if [ -f "docs/SENSITIVITY_LABEL_CLASSIFICATION_GUIDE.md" ]; then
    print_pass "Classification guide exists"
else
    print_fail "Classification guide not found"
fi

print_test "Test 8.2: Verify watermark mockups exist"
if [ -f "docs/SENSITIVITY_WATERMARK_MOCKUPS.md" ]; then
    print_pass "Watermark mockups exist"
else
    print_fail "Watermark mockups not found"
fi

print_test "Test 8.3: Verify placeholder reference exists"
if [ -f "docs/SENSITIVITY_PLACEHOLDER_REFERENCE.md" ]; then
    print_pass "Placeholder reference exists"
else
    print_fail "Placeholder reference not found"
fi

print_test "Test 8.4: Verify implementation guide exists"
if [ -f "docs/SENSITIVITY_LABEL_IMPLEMENTATION_GUIDE.md" ]; then
    print_pass "Implementation guide exists"
else
    print_fail "Implementation guide not found"
fi

print_test "Test 8.5: Verify status watermark reference exists"
if [ -f "docs/SENSITIVITY_STATUS_WATERMARK_REFERENCE.md" ]; then
    print_pass "Status watermark reference exists"
else
    print_fail "Status watermark reference not found"
fi

# Test Summary
print_header "Test Summary"

TOTAL_TESTS=$((TESTS_PASSED + TESTS_FAILED + TESTS_SKIPPED))

echo -e "${GREEN}Passed:  ${TESTS_PASSED}/${TOTAL_TESTS}${NC}"
echo -e "${RED}Failed:  ${TESTS_FAILED}/${TOTAL_TESTS}${NC}"
echo -e "${YELLOW}Skipped: ${TESTS_SKIPPED}/${TOTAL_TESTS}${NC}"

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "\n${GREEN}✓ All tests passed!${NC}\n"
    exit 0
else
    echo -e "\n${RED}✗ Some tests failed. Please review and fix.${NC}\n"
    exit 1
fi
