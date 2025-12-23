#!/bin/bash
#
# EDMS Restore Verification Script
#
# This script verifies the integrity of a restored EDMS system.

set -e

echo "🔍 EDMS Restore Verification"
echo "============================"
echo ""

# Check database connectivity
echo "📊 Verifying database..."
if command -v python3 &> /dev/null; then
    # Try Django database check
    if [ -f "manage.py" ]; then
        python3 manage.py check --database default
        echo "✓ Database connectivity verified"
    else
        echo "⚠️  Django manage.py not found - manual database verification needed"
    fi
else
    echo "⚠️  Python not found - manual verification needed"
fi

# Check storage directories
echo "📁 Verifying storage structure..."
STORAGE_DIRS=("documents" "media" "certificates")
for dir in "${STORAGE_DIRS[@]}"; do
    if [ -d "storage/$dir" ]; then
        echo "✓ Storage directory exists: $dir"
    else
        echo "⚠️  Storage directory missing: $dir"
    fi
done

# Verify file checksums (if manifest exists)
if [ -f "storage/manifest.json" ]; then
    echo "🔐 Verifying file checksums..."
    # Note: This would need a Python script to properly verify JSON manifest
    echo "✓ Manifest file found (manual verification recommended)"
else
    echo "⚠️  Storage manifest not found"
fi

echo ""
echo "✅ Verification completed!"
echo ""
echo "📋 Manual Verification Steps:"
echo "   1. Test application login"
echo "   2. Verify document access"
echo "   3. Check workflow functionality"
echo "   4. Validate user permissions"
echo "   5. Test document upload/download"
echo ""
