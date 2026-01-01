#!/bin/bash
# Cleanup duplicate draft documents without files
# These were created during failed upload attempts

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
    exit 1
}

log "Cleaning up duplicate draft documents without files..."
echo

# Check if we're in the right directory
if [[ ! -f "docker-compose.prod.yml" ]]; then
    error "docker-compose.prod.yml not found. Please run this from the project root directory."
fi

# Count drafts without files
log "Checking for draft documents without files..."
DRAFT_COUNT=$(docker compose -f docker-compose.prod.yml exec -T backend python manage.py shell << 'EOF'
from apps.documents.models import Document

# Find drafts without files
drafts_without_files = Document.objects.filter(
    status='DRAFT',
    file_path__isnull=True
) | Document.objects.filter(
    status='DRAFT',
    file_path=''
)

count = drafts_without_files.count()
print(f"Found {count} draft documents without files")

# Show some details
if count > 0:
    print("\nSample documents:")
    for doc in drafts_without_files[:5]:
        print(f"  - {doc.title} (ID: {doc.uuid}, Created: {doc.created_at})")
EOF
)

echo "$DRAFT_COUNT"
echo

# Ask for confirmation
read -p "Do you want to delete these draft documents? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    log "Cancelled. No documents deleted."
    exit 0
fi

# Delete drafts without files
log "Deleting draft documents without files..."
docker compose -f docker-compose.prod.yml exec -T backend python manage.py shell << 'EOF'
from apps.documents.models import Document

# Find drafts without files
drafts_without_files = Document.objects.filter(
    status='DRAFT',
    file_path__isnull=True
) | Document.objects.filter(
    status='DRAFT',
    file_path=''
)

count = drafts_without_files.count()
if count > 0:
    deleted = drafts_without_files.delete()
    print(f"✓ Deleted {deleted[0]} draft documents without files")
else:
    print("✓ No draft documents to delete")
EOF

echo
log "✅ Cleanup completed!"
echo
log "Next steps:"
echo "  1. Try creating a document again"
echo "  2. File should upload successfully now"
echo
