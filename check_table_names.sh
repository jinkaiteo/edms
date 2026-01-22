#!/bin/bash
# Check actual database table names on staging server

echo "Checking actual database table names..."
echo ""

docker compose exec backend python manage.py shell << 'PYTHON'
from django.db import connection

# Get all table names
with connection.cursor() as cursor:
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_type = 'BASE TABLE'
        ORDER BY table_name;
    """)
    
    tables = cursor.fetchall()
    
    print("📋 Available Database Tables:")
    print("=" * 50)
    
    for table in tables:
        table_name = table[0]
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        print(f"  {table_name:40s} ({count:4d} rows)")
    
    print("=" * 50)
    print(f"Total tables: {len(tables)}")

PYTHON

echo ""
echo "Now checking what dashboard_stats.py expects:"
echo ""
grep "FROM " backend/apps/api/dashboard_stats.py | grep -v "import" | sed 's/.*FROM /  - /' | sed 's/ .*//' | sort -u

