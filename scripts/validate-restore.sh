#!/bin/bash
#
# Validate Restore - Compare pre and post restore states
# Verifies that backup/restore successfully recovered all data
#

set -e

# Configuration
PRE_STATE_FILE="${1:-/tmp/system_state_*.txt}"
POST_STATE_FILE="/tmp/post_restore_state_$(date +%Y%m%d_%H%M%S).txt"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.yml}"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}✓${NC} $1"
}

error() {
    echo -e "${RED}✗${NC} $1"
}

info() {
    echo -e "${YELLOW}ℹ${NC} $1"
}

log "================================================"
log "  EDMS Restore Validation"
log "================================================"
echo ""

# Find the most recent pre-restore state file
if [ ! -f "$PRE_STATE_FILE" ]; then
    PRE_STATE_FILE=$(ls -t /tmp/system_state_*.txt 2>/dev/null | head -1)
    if [ -z "$PRE_STATE_FILE" ]; then
        error "No pre-restore state file found!"
        info "Please run ./scripts/document-system-state.sh before testing restore"
        exit 1
    fi
fi

info "Pre-restore state: $PRE_STATE_FILE"
echo ""

# Wait for services to stabilize
log "Waiting for services to stabilize..."
sleep 10
echo ""

# Check container status
log "Checking container status..."
if docker compose -f "$COMPOSE_FILE" ps | grep -q "Up"; then
    success "Containers are running"
else
    error "Some containers are not running!"
    docker compose -f "$COMPOSE_FILE" ps
    exit 1
fi
echo ""

# Document current (post-restore) state
log "Documenting post-restore state..."
./scripts/document-system-state.sh "$POST_STATE_FILE" > /dev/null 2>&1
success "Post-restore state documented: $POST_STATE_FILE"
echo ""

# Extract counts from state files
log "Comparing states..."
echo ""

PRE_DOCS=$(grep "Total documents:" "$PRE_STATE_FILE" | head -1 | awk '{print $3}')
POST_DOCS=$(grep "Total documents:" "$POST_STATE_FILE" | head -1 | awk '{print $3}')

PRE_USERS=$(grep "Total users:" "$PRE_STATE_FILE" | head -1 | awk '{print $3}')
POST_USERS=$(grep "Total users:" "$POST_STATE_FILE" | head -1 | awk '{print $3}')

PRE_FILES=$(grep "Total files:" "$PRE_STATE_FILE" | head -1 | awk '{print $3}')
POST_FILES=$(grep "Total files:" "$POST_STATE_FILE" | head -1 | awk '{print $3}')

PRE_VERSIONS=$(grep "Total document versions:" "$PRE_STATE_FILE" | head -1 | awk '{print $4}')
POST_VERSIONS=$(grep "Total document versions:" "$POST_STATE_FILE" | head -1 | awk '{print $4}')

# Display comparison
echo "╔════════════════════════════════════════════════╗"
echo "║         BACKUP/RESTORE VALIDATION              ║"
echo "╠════════════════════════════════════════════════╣"
echo "║  Metric          │ Before │ After  │ Status   ║"
echo "╠══════════════════╪════════╪════════╪══════════╣"

# Documents comparison
printf "║  Documents       │ %6s │ %6s │ " "$PRE_DOCS" "$POST_DOCS"
if [ "$PRE_DOCS" = "$POST_DOCS" ]; then
    echo -e "${GREEN}PASS${NC}     ║"
else
    echo -e "${RED}FAIL${NC}     ║"
fi

# Users comparison
printf "║  Users           │ %6s │ %6s │ " "$PRE_USERS" "$POST_USERS"
if [ "$PRE_USERS" = "$POST_USERS" ]; then
    echo -e "${GREEN}PASS${NC}     ║"
else
    echo -e "${RED}FAIL${NC}     ║"
fi

# Files comparison
printf "║  Files           │ %6s │ %6s │ " "$PRE_FILES" "$POST_FILES"
if [ "$PRE_FILES" = "$POST_FILES" ]; then
    echo -e "${GREEN}PASS${NC}     ║"
else
    echo -e "${RED}FAIL${NC}     ║"
fi

# Versions comparison
printf "║  Versions        │ %6s │ %6s │ " "$PRE_VERSIONS" "$POST_VERSIONS"
if [ "$PRE_VERSIONS" = "$POST_VERSIONS" ]; then
    echo -e "${GREEN}PASS${NC}     ║"
else
    echo -e "${RED}FAIL${NC}     ║"
fi

echo "╚══════════════════╧════════╧════════╧══════════╝"
echo ""

# Detailed verification
PASS_COUNT=0
FAIL_COUNT=0

log "Detailed Verification"
echo ""

# 1. Document count
echo "1. Documents:"
if [ "$PRE_DOCS" = "$POST_DOCS" ]; then
    success "Document count matches ($POST_DOCS documents)"
    ((PASS_COUNT++))
else
    error "Document count mismatch! Before: $PRE_DOCS, After: $POST_DOCS"
    ((FAIL_COUNT++))
fi
echo ""

# 2. User count
echo "2. Users:"
if [ "$PRE_USERS" = "$POST_USERS" ]; then
    success "User count matches ($POST_USERS users)"
    ((PASS_COUNT++))
else
    error "User count mismatch! Before: $PRE_USERS, After: $POST_USERS"
    ((FAIL_COUNT++))
fi
echo ""

# 3. File count
echo "3. Uploaded Files:"
if [ "$PRE_FILES" = "$POST_FILES" ]; then
    success "File count matches ($POST_FILES files)"
    ((PASS_COUNT++))
    if [ -d "storage/documents" ]; then
        info "Files in storage:"
        ls -lh storage/documents/ | tail -n +2 | awk '{print "  • " $9 " (" $5 ")"}'
    fi
else
    error "File count mismatch! Before: $PRE_FILES, After: $POST_FILES"
    ((FAIL_COUNT++))
fi
echo ""

# 4. Document versions
echo "4. Document Versions:"
if [ "$PRE_VERSIONS" = "$POST_VERSIONS" ]; then
    success "Version count matches ($POST_VERSIONS versions)"
    ((PASS_COUNT++))
else
    error "Version count mismatch! Before: $PRE_VERSIONS, After: $POST_VERSIONS"
    ((FAIL_COUNT++))
fi
echo ""

# 5. File permissions
echo "5. Storage Permissions:"
STORAGE_UID=$(stat -c "%u" storage/documents/ 2>/dev/null || echo "unknown")
STORAGE_PERMS=$(stat -c "%a" storage/documents/ 2>/dev/null || echo "unknown")
if [ "$STORAGE_UID" = "995" ] || [ "$STORAGE_UID" = "1000" ]; then
    success "Storage owned by UID $STORAGE_UID"
    ((PASS_COUNT++))
else
    error "Storage owned by UID $STORAGE_UID (expected 995 or 1000)"
    ((FAIL_COUNT++))
fi

if [ "$STORAGE_PERMS" = "775" ] || [ "$STORAGE_PERMS" = "755" ]; then
    success "Storage permissions: $STORAGE_PERMS"
else
    info "Storage permissions: $STORAGE_PERMS (expected 775 or 755)"
fi
echo ""

# 6. Container health
echo "6. Container Health:"
HEALTHY_COUNT=$(docker compose -f "$COMPOSE_FILE" ps | grep -c "(healthy)" || echo "0")
if [ "$HEALTHY_COUNT" -ge 4 ]; then
    success "$HEALTHY_COUNT containers are healthy"
    ((PASS_COUNT++))
else
    error "Only $HEALTHY_COUNT containers are healthy"
    ((FAIL_COUNT++))
fi
echo ""

# Summary
log "================================================"
log "  Validation Summary"
log "================================================"
echo ""
echo "Results:"
success "Passed: $PASS_COUNT tests"
if [ $FAIL_COUNT -gt 0 ]; then
    error "Failed: $FAIL_COUNT tests"
fi
echo ""

# Overall result
if [ $FAIL_COUNT -eq 0 ]; then
    echo -e "${GREEN}╔════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                                                ║${NC}"
    echo -e "${GREEN}║     ✓ RESTORE VALIDATION SUCCESSFUL!          ║${NC}"
    echo -e "${GREEN}║                                                ║${NC}"
    echo -e "${GREEN}║  All data has been restored correctly.         ║${NC}"
    echo -e "${GREEN}║  Backup/restore system is working perfectly!  ║${NC}"
    echo -e "${GREEN}║                                                ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════╝${NC}"
    echo ""
    
    log "Test Results:"
    success "Documents restored: $POST_DOCS/$PRE_DOCS"
    success "Users restored: $POST_USERS/$PRE_USERS"
    success "Files restored: $POST_FILES/$PRE_FILES"
    success "Versions restored: $POST_VERSIONS/$PRE_VERSIONS"
    echo ""
    
    log "Next Steps:"
    info "1. Test login with restored credentials"
    info "2. Browse documents via web interface"
    info "3. Download and verify uploaded files"
    info "4. Test workflow functionality"
    echo ""
    
    info "Access URLs:"
    SERVER_IP=$(hostname -I | awk '{print $1}')
    echo "  Frontend:    http://$SERVER_IP:3001"
    echo "  Backend API: http://$SERVER_IP:8001/api/v1/"
    echo "  Admin Panel: http://$SERVER_IP:8001/admin/"
    echo ""
    
    exit 0
else
    echo -e "${RED}╔════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║                                                ║${NC}"
    echo -e "${RED}║     ✗ RESTORE VALIDATION FAILED                ║${NC}"
    echo -e "${RED}║                                                ║${NC}"
    echo -e "${RED}║  Some data was not restored correctly.         ║${NC}"
    echo -e "${RED}║  Please review the errors above.               ║${NC}"
    echo -e "${RED}║                                                ║${NC}"
    echo -e "${RED}╚════════════════════════════════════════════════╝${NC}"
    echo ""
    
    log "Troubleshooting:"
    info "1. Check logs: docker compose -f $COMPOSE_FILE logs backend"
    info "2. Verify backup file: tar -tzf [backup-file]"
    info "3. Check container status: docker compose -f $COMPOSE_FILE ps"
    info "4. Review state files:"
    echo "     Pre:  $PRE_STATE_FILE"
    echo "     Post: $POST_STATE_FILE"
    echo ""
    
    exit 1
fi
