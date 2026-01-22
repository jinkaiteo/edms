#!/bin/bash
# Diagnose dashboard stats issue on staging server

echo "=========================================="
echo "  Dashboard Stats Diagnostic"
echo "=========================================="
echo ""

docker compose exec backend python manage.py shell << 'PYTHON'
from django.db import connection
from django.utils import timezone
from datetime import timedelta

print("📊 Checking Database Tables and Counts:")
print("=" * 60)

# Check each table that dashboard_stats.py queries
tables_to_check = {
    'users': 'Total users',
    'workflow_instances': 'Active workflows',
    'placeholders': 'Placeholder definitions',
    'audit_trail': 'Audit trail entries',
    'documents': 'Total documents',
    'login_audit': 'Login audit entries',
}

with connection.cursor() as cursor:
    for table, description in tables_to_check.items():
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            status = "✅" if count > 0 else "⚠️ "
            print(f"{status} {description:30s}: {count:5d} rows in '{table}'")
        except Exception as e:
            print(f"❌ {description:30s}: ERROR - {str(e)}")
    
    print("=" * 60)
    
    # Check if tables exist at all
    print("\n📋 Checking if tables exist:")
    print("=" * 60)
    
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_type = 'BASE TABLE'
        AND table_name IN ('users', 'workflow_instances', 'placeholders', 
                           'audit_trail', 'documents', 'login_audit',
                           'document_workflows')
        ORDER BY table_name;
    """)
    
    existing_tables = [row[0] for row in cursor.fetchall()]
    
    for table in ['users', 'workflow_instances', 'placeholders', 'audit_trail', 
                  'documents', 'login_audit', 'document_workflows']:
        if table in existing_tables:
            print(f"✅ Table '{table}' exists")
        else:
            print(f"❌ Table '{table}' DOES NOT EXIST")
    
    print("=" * 60)
    
    # Check for alternative table names
    print("\n🔍 Looking for similar table names:")
    print("=" * 60)
    
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_type = 'BASE TABLE'
        AND (table_name LIKE '%workflow%' 
             OR table_name LIKE '%audit%'
             OR table_name LIKE '%placeholder%'
             OR table_name LIKE '%document%')
        ORDER BY table_name;
    """)
    
    similar_tables = cursor.fetchall()
    for table in similar_tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
        count = cursor.fetchone()[0]
        print(f"  📄 {table[0]:40s} ({count:4d} rows)")

PYTHON

echo ""
echo "=========================================="
echo "  Diagnosis Complete"
echo "=========================================="
