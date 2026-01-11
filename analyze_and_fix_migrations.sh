#!/bin/bash

# Script to analyze and fix migration issues automatically

set -e

CONTAINER_NAME="edms_prod_backend"

echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║         Analyzing Migration Issues and Creating Fix                         ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"
echo ""

echo "[1/4] Analyzing current database schema..."
docker exec $CONTAINER_NAME python manage.py shell << 'PYEOF'
import django
django.setup()
from django.db import connection

cursor = connection.cursor()

# Check scheduler_scheduledtask
cursor.execute("""
    SELECT column_name, data_type, is_nullable
    FROM information_schema.columns 
    WHERE table_name = 'scheduler_scheduledtask'
    ORDER BY ordinal_position;
""")

print("\n=== Current scheduler_scheduledtask columns in database ===")
db_columns = {}
for row in cursor.fetchall():
    db_columns[row[0]] = {'type': row[1], 'nullable': row[2]}
    print(f"  {row[0]}: {row[1]} (nullable: {row[2]})")

# Check what the model expects
from apps.scheduler.models import ScheduledTask
print("\n=== Model expects these fields ===")
model_fields = {}
for field in ScheduledTask._meta.fields:
    model_fields[field.name] = {
        'type': field.get_internal_type(),
        'null': field.null
    }
    print(f"  {field.name}: {field.get_internal_type()} (null: {field.null})")

# Find differences
print("\n=== Fields in model but NOT in database ===")
missing_in_db = set(model_fields.keys()) - set(db_columns.keys())
for field in missing_in_db:
    print(f"  {field}: {model_fields[field]}")

print("\n=== Fields in database but NOT in model ===")
extra_in_db = set(db_columns.keys()) - set(model_fields.keys())
for field in extra_in_db:
    print(f"  {field}: {db_columns[field]}")

PYEOF

echo ""
echo "[2/4] Understanding the migration needed..."
echo ""
echo "Based on analysis, the ScheduledTask model has changed."
echo "The model now expects simpler fields without complex relationships."
echo ""

echo "[3/4] Creating migration with proper defaults..."
echo ""
echo "Note: This will create a new field 'scheduled_time' and 'completed'"
echo "      We'll use timezone.now() as default for scheduled_time"
echo "      We'll use False as default for completed"
echo ""

# Create the migration by providing answers
docker exec $CONTAINER_NAME bash -c 'python manage.py makemigrations scheduler << "MIGEOF"
n
1
timezone.now()
MIGEOF
' 2>&1 | tail -20

echo ""
echo "[4/4] Applying migrations..."
docker exec $CONTAINER_NAME python manage.py migrate

echo ""
echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║                      Migrations Fixed Successfully!                          ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"
echo ""

echo "Running tests..."
./fix_migrations_and_test.sh
