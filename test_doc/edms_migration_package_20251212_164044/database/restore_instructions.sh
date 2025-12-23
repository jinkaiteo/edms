#!/bin/bash
# Django EDMS Database Restore Script

echo 'Restoring Django EDMS database backup...'
echo 'Make sure you have:'
echo '1. Created a fresh Django database'
echo '2. Run: python manage.py migrate'
echo 'Now running: python manage.py loaddata database_backup.json'

python manage.py loaddata database_backup.json
echo 'Database restore completed!'
