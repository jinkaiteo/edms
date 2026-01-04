#!/bin/bash
#
# EDMS Backup Verification Script
#
# Verifies the integrity and completeness of an EDMS backup
#
# Usage: ./verify-backup.sh <backup_name>
#

set -e

# Configuration
BACKUP_DIR="${BACKUP_DIR:-$HOME/edms-backups}"
BACKUP_NAME="${1}"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_pass() {
    echo -e "${GREEN}✓${NC} $1"
}

log_fail() {
    echo -e "${RED}✗${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Check arguments
if [ -z "${BACKUP_NAME}" ]; then
    echo "Usage: $0 <backup_name>"
    echo ""
    echo "Available backups:"
    ls -1 "${BACKUP_DIR}" 2>/dev/null || echo "  (no backups found)"
    exit 1
fi

BACKUP_PATH="${BACKUP_DIR}/${BACKUP_NAME}"

echo "========================================"
echo "EDMS Backup Verification"
echo "========================================"
echo "Backup: ${BACKUP_NAME}"
echo "Path: ${BACKUP_PATH}"
echo ""

ERRORS=0
WARNINGS=0

# Check 1: Backup directory exists
if [ -d "${BACKUP_PATH}" ]; then
    log_pass "Backup directory exists"
else
    log_fail "Backup directory not found"
    exit 1
fi

# Check 2: Database dump exists
if [ -f "${BACKUP_PATH}/database.dump" ]; then
    DB_SIZE=$(stat -f%z "${BACKUP_PATH}/database.dump" 2>/dev/null || stat -c%s "${BACKUP_PATH}/database.dump")
    if [ ${DB_SIZE} -gt 1000 ]; then
        log_pass "Database dump exists ($(numfmt --to=iec-i --suffix=B ${DB_SIZE} 2>/dev/null || echo "${DB_SIZE} bytes"))"
    else
        log_fail "Database dump too small (${DB_SIZE} bytes)"
        ERRORS=$((ERRORS + 1))
    fi
else
    log_fail "Database dump missing"
    ERRORS=$((ERRORS + 1))
fi

# Check 3: Storage backup exists
if [ -f "${BACKUP_PATH}/storage.tar.gz" ]; then
    STORAGE_SIZE=$(stat -f%z "${BACKUP_PATH}/storage.tar.gz" 2>/dev/null || stat -c%s "${BACKUP_PATH}/storage.tar.gz")
    if [ ${STORAGE_SIZE} -gt 100 ]; then
        log_pass "Storage backup exists ($(numfmt --to=iec-i --suffix=B ${STORAGE_SIZE} 2>/dev/null || echo "${STORAGE_SIZE} bytes"))"
        
        # Verify tar integrity
        if tar -tzf "${BACKUP_PATH}/storage.tar.gz" > /dev/null 2>&1; then
            log_pass "Storage archive is valid"
        else
            log_fail "Storage archive is corrupted"
            ERRORS=$((ERRORS + 1))
        fi
    else
        log_warn "Storage backup very small (${STORAGE_SIZE} bytes)"
        WARNINGS=$((WARNINGS + 1))
    fi
else
    log_warn "Storage backup missing (may be empty)"
    WARNINGS=$((WARNINGS + 1))
fi

# Check 4: Metadata exists
if [ -f "${BACKUP_PATH}/backup_metadata.json" ]; then
    if command -v jq >/dev/null 2>&1; then
        if jq empty "${BACKUP_PATH}/backup_metadata.json" 2>/dev/null; then
            log_pass "Metadata is valid JSON"
            
            # Display metadata
            echo ""
            echo "Backup Metadata:"
            jq '.' "${BACKUP_PATH}/backup_metadata.json"
        else
            log_fail "Metadata is invalid JSON"
            ERRORS=$((ERRORS + 1))
        fi
    else
        log_pass "Metadata exists (jq not available for validation)"
    fi
else
    log_warn "Metadata missing"
    WARNINGS=$((WARNINGS + 1))
fi

# Check 5: Configuration backup
if [ -d "${BACKUP_PATH}/config" ]; then
    CONFIG_COUNT=$(ls -1 "${BACKUP_PATH}/config" | wc -l)
    log_pass "Configuration files backed up (${CONFIG_COUNT} file(s))"
else
    log_warn "No configuration backup"
    WARNINGS=$((WARNINGS + 1))
fi

# Check 6: Database dump format
if [ -f "${BACKUP_PATH}/database.dump" ]; then
    if file "${BACKUP_PATH}/database.dump" | grep -q "PostgreSQL custom database dump"; then
        log_pass "Database dump is in PostgreSQL custom format (-Fc)"
    else
        log_warn "Database dump format unrecognized (may still be valid)"
        WARNINGS=$((WARNINGS + 1))
    fi
fi

# Summary
echo ""
echo "========================================"
if [ ${ERRORS} -eq 0 ] && [ ${WARNINGS} -eq 0 ]; then
    echo -e "${GREEN}✓ Backup is valid and complete${NC}"
    exit 0
elif [ ${ERRORS} -eq 0 ]; then
    echo -e "${YELLOW}⚠ Backup is valid with ${WARNINGS} warning(s)${NC}"
    exit 0
else
    echo -e "${RED}✗ Backup has ${ERRORS} error(s) and ${WARNINGS} warning(s)${NC}"
    exit 1
fi
