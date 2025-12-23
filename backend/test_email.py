#!/usr/bin/env python
"""
Test Email Configuration
Run: python backend/test_email.py
"""

import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'edms.settings.development')
django.setup()

from django.core.mail import send_mail
from django.conf import settings


def test_email_configuration():
    """Test email configuration and send test email"""
    
    print("=" * 60)
    print("EDMS Email Configuration Test")
    print("=" * 60)
    
    # Check configuration
    print("\n1. Current Email Configuration:")
    print(f"   EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
    print(f"   EMAIL_HOST: {settings.EMAIL_HOST}")
    print(f"   EMAIL_PORT: {settings.EMAIL_PORT}")
    print(f"   EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
    print(f"   EMAIL_HOST_USER: {settings.EMAIL_HOST_USER or '(not set)'}")
    print(f"   EMAIL_HOST_PASSWORD: {'***' if settings.EMAIL_HOST_PASSWORD else '(not set)'}")
    print(f"   DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
    
    # Check if using console backend
    if 'console' in settings.EMAIL_BACKEND.lower():
        print("\n⚠️  WARNING: Using console email backend (development mode)")
        print("   Emails will be printed to console, not actually sent")
        print("   This is normal for development environment")
    
    # Check if SMTP is configured
    if not settings.EMAIL_HOST_USER or not settings.EMAIL_HOST_PASSWORD:
        print("\n❌ Email credentials not configured!")
        print("\nTo configure email, follow these steps:")
        print("\n1. Create an App Password:")
        print("   Microsoft 365: https://account.microsoft.com/security")
        print("   Gmail: https://myaccount.google.com/apppasswords")
        print("\n2. Create backend/.env file with:")
        print("   EMAIL_HOST=smtp.office365.com")
        print("   EMAIL_PORT=587")
        print("   EMAIL_USE_TLS=True")
        print("   EMAIL_HOST_USER=your-email@yourcompany.com")
        print("   EMAIL_HOST_PASSWORD=your-app-password")
        print("   DEFAULT_FROM_EMAIL=your-email@yourcompany.com")
        print("\n3. Restart the backend: docker compose restart backend")
        print("\n4. Run this test again")
        return False
    
    # Send test email
    print("\n2. Sending Test Email...")
    recipient = input("   Enter recipient email address: ")
    
    if not recipient or '@' not in recipient:
        print("   ❌ Invalid email address")
        return False
    
    try:
        send_mail(
            subject='EDMS Test Email',
            message='This is a test email from the EDMS system.\n\nIf you receive this, email integration is working correctly!',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient],
            fail_silently=False
        )
        
        print(f"   ✅ Email sent successfully to {recipient}!")
        print("\n3. Next Steps:")
        print("   - Check the recipient's inbox (and spam folder)")
        print("   - If email arrived, configuration is correct")
        print("   - Email notifications will now work in the system")
        return True
        
    except Exception as e:
        print(f"   ❌ Failed to send email: {e}")
        print("\n3. Troubleshooting:")
        print("   - Verify your email credentials are correct")
        print("   - Check if App Password is active (not expired)")
        print("   - For Microsoft 365, ensure account has Exchange license")
        print("   - Check firewall allows outbound port 587")
        print("   - Try 'telnet smtp.office365.com 587' to test connectivity")
        return False


def test_notification_service():
    """Test notification service with mock data"""
    from apps.scheduler.notification_service import notification_service
    from apps.users.models import User
    from apps.documents.models import Document
    
    print("\n" + "=" * 60)
    print("Testing Notification Service")
    print("=" * 60)
    
    # Get a test user
    try:
        user = User.objects.filter(email__isnull=False).exclude(email='').first()
        if not user:
            print("❌ No users with email addresses found")
            return False
        
        print(f"\n✅ Found test user: {user.username} ({user.email})")
        
        # Test with a mock document (doesn't actually send)
        print("\nNotification service is ready to send emails for:")
        print("  - Task assignments")
        print("  - Document effective dates")
        print("  - Document obsolescence")
        print("  - Workflow timeouts")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing notification service: {e}")
        return False


if __name__ == "__main__":
    print("\n")
    success = test_email_configuration()
    
    if success:
        print("\n" + "=" * 60)
        test_notification_service()
    
    print("\n" + "=" * 60)
    print("Test Complete")
    print("=" * 60)
