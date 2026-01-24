#!/bin/bash
# Quick Email Test
# Sends a test email and verifies it was sent

echo "========================================="
echo "  Email Notification Test"
echo "========================================="
echo ""

RECIPIENT="${1:-}"

if [ -z "$RECIPIENT" ]; then
    echo "Usage: $0 <recipient-email>"
    echo ""
    echo "Example: $0 admin@example.com"
    exit 1
fi

echo "Sending test email to: $RECIPIENT"
echo ""

docker compose exec -T backend python manage.py shell <<PYEOF
from django.core.mail import send_mail
from django.conf import settings
import datetime

try:
    result = send_mail(
        subject=f'EDMS Test Email - {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
        message='''This is a test email from EDMS.

If you received this, the email notification system is working correctly.

Test Details:
- Sent via monitoring script
- Timestamp: ''' + str(datetime.datetime.now()) + '''
- From: ''' + settings.DEFAULT_FROM_EMAIL + '''

---
EDMS Email Notification System''',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=['$RECIPIENT'],
        fail_silently=False,
    )
    
    if result == 1:
        print('✅ Email sent successfully!')
        print()
        print('Please check the inbox at: $RECIPIENT')
        print('(Check spam folder if not in inbox)')
    else:
        print('❌ Email sending failed (return code: {})'.format(result))
        exit(1)
        
except Exception as e:
    print(f'❌ Error sending email: {e}')
    import traceback
    traceback.print_exc()
    exit(1)
PYEOF

echo ""
echo "========================================="
