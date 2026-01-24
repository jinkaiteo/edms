#!/bin/bash
# Email Notification System Health Check
# Run this periodically to verify email system is working

echo "========================================="
echo "  Email Notification System Health Check"
echo "  $(date)"
echo "========================================="
echo ""

EXIT_CODE=0

# 1. Check SMTP Configuration
echo "1. SMTP Configuration"
docker compose exec -T backend python manage.py shell -c "
from django.conf import settings
backend = settings.EMAIL_BACKEND
if 'smtp' in backend.lower():
    print('   ✅ SMTP Mode Active')
    print(f'   Host: {settings.EMAIL_HOST}:{settings.EMAIL_PORT}')
else:
    print('   ❌ Console Mode (emails not sent!)')
    exit(1)
" || EXIT_CODE=1

# 2. Test SMTP Connection
echo ""
echo "2. SMTP Connection Test"
docker compose exec -T backend python manage.py shell -c "
from django.conf import settings
import smtplib
try:
    server = smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT, timeout=5)
    server.starttls()
    server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
    server.quit()
    print('   ✅ SMTP Connection Successful')
except Exception as e:
    print(f'   ❌ SMTP Connection Failed: {e}')
    exit(1)
" || EXIT_CODE=1

# 3. Check Celery Workers
echo ""
echo "3. Celery Worker Status"
if docker compose ps celery_worker | grep -q "Up"; then
    echo "   ✅ Celery Worker Running"
else
    echo "   ❌ Celery Worker Not Running"
    EXIT_CODE=1
fi

# 4. Check Email Tasks Registered
echo ""
echo "4. Email Tasks Registration"
if docker compose exec -T celery_worker celery -A edms inspect registered 2>/dev/null | grep -q "send_test_email_to_self"; then
    echo "   ✅ Email Tasks Registered"
else
    echo "   ⚠️  Cannot verify task registration (worker may be busy)"
fi

# 5. Check Recent Email Activity
echo ""
echo "5. Recent Email Activity (last 24h)"
EMAIL_COUNT=$(docker compose logs celery_worker --since="24h" 2>/dev/null | grep -c "Email sent" || echo "0")
echo "   Emails sent: $EMAIL_COUNT"
if [ $EMAIL_COUNT -gt 0 ]; then
    echo "   ✅ Email Activity Detected"
else
    echo "   ℹ️  No Email Activity (normal if no workflows triggered)"
fi

# 6. Check for Errors
echo ""
echo "6. Error Check (last 24h)"
ERROR_COUNT=$(docker compose logs backend celery_worker --since="24h" 2>/dev/null | grep -ci "error.*email\|failed.*email" || echo "0")
echo "   Email errors: $ERROR_COUNT"
if [ $ERROR_COUNT -eq 0 ]; then
    echo "   ✅ No Errors"
elif [ $ERROR_COUNT -lt 5 ]; then
    echo "   ⚠️  Few Errors (investigate if persistent)"
else
    echo "   ❌ High Error Rate (immediate investigation needed!)"
    EXIT_CODE=1
fi

# 7. Check Users with Email
echo ""
echo "7. User Email Configuration"
docker compose exec -T backend python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
total = User.objects.count()
with_email = User.objects.filter(email__isnull=False).exclude(email='').count()
print(f'   Users with email: {with_email} / {total}')
if with_email == 0:
    print('   ⚠️  No users have email addresses configured!')
"

echo ""
echo "========================================="
if [ $EXIT_CODE -eq 0 ]; then
    echo "  ✅ Health Check PASSED"
else
    echo "  ❌ Health Check FAILED"
fi
echo "========================================="

exit $EXIT_CODE
