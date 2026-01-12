#!/bin/bash
#
# Document System State - For Backup/Restore Testing
# Captures current state of documents, users, files, and database
#

set -e

# Configuration
OUTPUT_FILE="${1:-/tmp/system_state_$(date +%Y%m%d_%H%M%S).txt}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.yml}"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}✓${NC} $1"
}

info() {
    echo -e "${YELLOW}ℹ${NC} $1"
}

log "================================================"
log "  EDMS System State Documentation"
log "================================================"
log "Output file: $OUTPUT_FILE"
log ""

# Start output file
{
    echo "================================================"
    echo "  EDMS System State"
    echo "  Generated: $(date)"
    echo "================================================"
    echo ""
} > "$OUTPUT_FILE"

# Check if containers are running
log "Checking container status..."
if ! docker compose -f "$COMPOSE_FILE" ps | grep -q "Up"; then
    echo "ERROR: Containers are not running!" | tee -a "$OUTPUT_FILE"
    exit 1
fi
success "Containers are running"
echo ""

# Document Count
log "Counting documents..."
{
    echo "=== DOCUMENTS ==="
    echo ""
} >> "$OUTPUT_FILE"

docker compose -f "$COMPOSE_FILE" exec -T backend python manage.py shell << 'PYEOF' 2>&1 | tee -a "$OUTPUT_FILE"
from apps.documents.models import Document
from django.utils import timezone

doc_count = Document.objects.count()
print(f"Total documents: {doc_count}")
print("")

if doc_count > 0:
    print("Documents list:")
    for doc in Document.objects.all().order_by('-created_at'):
        print(f"  • {doc.document_number}")
        print(f"    Title: {doc.title}")
        print(f"    Status: {doc.status}")
        print(f"    Created: {doc.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"    Author: {doc.author.username if doc.author else 'N/A'}")
        print("")
else:
    print("No documents found")
    print("")
PYEOF

success "Documents documented"
echo ""

# User Count
log "Counting users..."
{
    echo "=== USERS ==="
    echo ""
} >> "$OUTPUT_FILE"

docker compose -f "$COMPOSE_FILE" exec -T backend python manage.py shell << 'PYEOF' 2>&1 | tee -a "$OUTPUT_FILE"
from django.contrib.auth import get_user_model
User = get_user_model()

user_count = User.objects.count()
print(f"Total users: {user_count}")
print("")

if user_count > 0:
    print("Users list:")
    for user in User.objects.all().order_by('username'):
        roles = []
        if user.is_superuser:
            roles.append("Admin")
        if user.is_staff:
            roles.append("Staff")
        role_str = ", ".join(roles) if roles else "Regular User"
        
        print(f"  • {user.username}")
        print(f"    Email: {user.email}")
        print(f"    Name: {user.first_name} {user.last_name}".strip())
        print(f"    Role: {role_str}")
        print(f"    Active: {user.is_active}")
        print(f"    Last login: {user.last_login.strftime('%Y-%m-%d %H:%M:%S') if user.last_login else 'Never'}")
        print("")
else:
    print("No users found")
    print("")
PYEOF

success "Users documented"
echo ""

# File Count
log "Counting uploaded files..."
{
    echo "=== UPLOADED FILES ==="
    echo ""
} >> "$OUTPUT_FILE"

if [ -d "storage/documents" ]; then
    FILE_COUNT=$(find storage/documents/ -type f 2>/dev/null | wc -l)
    STORAGE_SIZE=$(du -sh storage/documents/ 2>/dev/null | cut -f1)
    
    {
        echo "Total files: $FILE_COUNT"
        echo "Storage size: $STORAGE_SIZE"
        echo ""
        
        if [ "$FILE_COUNT" -gt 0 ]; then
            echo "File list (first 20):"
            ls -lh storage/documents/ 2>/dev/null | head -21 | tail -20
        else
            echo "No files found"
        fi
        echo ""
    } | tee -a "$OUTPUT_FILE"
    
    success "Files documented ($FILE_COUNT files, $STORAGE_SIZE)"
else
    {
        echo "Storage directory not found"
        echo ""
    } | tee -a "$OUTPUT_FILE"
    
    info "No storage directory"
fi
echo ""

# Workflow Instances
log "Counting workflow instances..."
{
    echo "=== WORKFLOW INSTANCES ==="
    echo ""
} >> "$OUTPUT_FILE"

docker compose -f "$COMPOSE_FILE" exec -T backend python manage.py shell << 'PYEOF' 2>&1 | tee -a "$OUTPUT_FILE"
from apps.workflows.models import WorkflowInstance

wf_count = WorkflowInstance.objects.count()
print(f"Total workflow instances: {wf_count}")
print("")

if wf_count > 0:
    print("Workflow list:")
    for wf in WorkflowInstance.objects.all().order_by('-created_at'):
        state_name = wf.current_state.name if wf.current_state else "Unknown"
        print(f"  • Document: {wf.document.document_number}")
        print(f"    Current state: {state_name}")
        print(f"    Terminated: {wf.is_terminated}")
        print(f"    Created: {wf.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        print("")
else:
    print("No workflow instances found")
    print("")
PYEOF

success "Workflows documented"
echo ""

# Document Versions
log "Counting document versions..."
{
    echo "=== DOCUMENT VERSIONS ==="
    echo ""
} >> "$OUTPUT_FILE"

docker compose -f "$COMPOSE_FILE" exec -T backend python manage.py shell << 'PYEOF' 2>&1 | tee -a "$OUTPUT_FILE"
from apps.documents.models import DocumentVersion

ver_count = DocumentVersion.objects.count()
print(f"Total document versions: {ver_count}")
print("")

if ver_count > 0:
    print("Versions by document:")
    from collections import defaultdict
    doc_versions = defaultdict(list)
    
    for ver in DocumentVersion.objects.all().order_by('document__document_number', 'version_major', 'version_minor'):
        doc_versions[ver.document.document_number].append(f"v{ver.version_major}.{ver.version_minor}")
    
    for doc_num, versions in doc_versions.items():
        print(f"  • {doc_num}: {', '.join(versions)}")
    print("")
else:
    print("No document versions found")
    print("")
PYEOF

success "Document versions documented"
echo ""

# Database Statistics
log "Gathering database statistics..."
{
    echo "=== DATABASE STATISTICS ==="
    echo ""
} >> "$OUTPUT_FILE"

docker compose -f "$COMPOSE_FILE" exec -T db psql -U "${DB_USER:-edms_user}" -d "${DB_NAME:-edms_db}" -t << 'SQLEOF' 2>&1 | tee -a "$OUTPUT_FILE"
-- Database size
SELECT 'Database size: ' || pg_size_pretty(pg_database_size(current_database()));

-- Table count
SELECT 'Total tables: ' || COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';

-- Top 5 largest tables
SELECT '';
SELECT 'Top 5 largest tables:';
SELECT '  • ' || tablename || ': ' || pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename))
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
LIMIT 5;
SQLEOF

echo "" >> "$OUTPUT_FILE"
success "Database statistics gathered"
echo ""

# Container Status
log "Documenting container status..."
{
    echo "=== CONTAINER STATUS ==="
    echo ""
} >> "$OUTPUT_FILE"

docker compose -f "$COMPOSE_FILE" ps | tee -a "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

success "Container status documented"
echo ""

# Summary
log "Creating summary..."
{
    echo "=== SUMMARY ==="
    echo ""
    echo "State captured at: $(date)"
    echo "Output file: $OUTPUT_FILE"
    echo ""
} >> "$OUTPUT_FILE"

# Display summary to console
log "================================================"
log "  State Documentation Complete!"
log "================================================"
info "Output saved to: $OUTPUT_FILE"
echo ""
success "You can view the full report with:"
echo "  cat $OUTPUT_FILE"
echo ""

# Quick summary to console
echo "Quick Summary:"
DOCS=$(docker compose -f "$COMPOSE_FILE" exec -T backend python manage.py shell -c "from apps.documents.models import Document; print(Document.objects.count())" 2>/dev/null | tail -1)
USERS=$(docker compose -f "$COMPOSE_FILE" exec -T backend python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); print(User.objects.count())" 2>/dev/null | tail -1)
FILES=$(find storage/documents/ -type f 2>/dev/null | wc -l)

echo "  Documents: $DOCS"
echo "  Users: $USERS"
echo "  Files: $FILES"
echo ""

exit 0
