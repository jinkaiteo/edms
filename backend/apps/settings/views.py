"""
Settings API Views
Handles system settings and configuration endpoints
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import get_user_model
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminUser])
def send_test_email(request):
    """
    Send a test email to verify email configuration.
    
    Sends test emails to:
    1. The requesting user
    2. All superuser accounts
    
    Returns:
        200: Email sent successfully with recipient list
        500: Email sending failed with error details
    """
    try:
        # Get recipient list
        recipients = set()
        
        # Add requesting user
        if request.user.email:
            recipients.add(request.user.email)
        
        # Add all superusers with email addresses
        superusers = User.objects.filter(is_superuser=True, email__isnull=False).exclude(email='')
        recipients.update(superusers.values_list('email', flat=True))
        
        if not recipients:
            return Response({
                'success': False,
                'message': 'No valid email addresses found. Please ensure admin users have email addresses configured.',
                'recipients': []
            }, status=status.HTTP_400_BAD_REQUEST)
        
        recipients_list = list(recipients)
        
        # Email content
        subject = 'EDMS Test Email - Configuration Successful'
        message = f"""
This is a test email from your EDMS (Electronic Document Management System).

If you're reading this, your email configuration is working correctly!

Configuration Details:
- SMTP Host: {getattr(settings, 'EMAIL_HOST', 'Not configured')}
- SMTP Port: {getattr(settings, 'EMAIL_PORT', 'Not configured')}
- Use TLS: {getattr(settings, 'EMAIL_USE_TLS', False)}
- From Email: {getattr(settings, 'DEFAULT_FROM_EMAIL', 'Not configured')}

Sent to: {', '.join(recipients_list)}
Triggered by: {request.user.get_full_name() or request.user.username}

---
This is an automated test email from EDMS.
"""
        
        # Send email
        sent_count = send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipients_list,
            fail_silently=False
        )
        
        logger.info(f"Test email sent successfully to {len(recipients_list)} recipients by {request.user.username}")
        
        return Response({
            'success': True,
            'message': f'Test email sent successfully to {len(recipients_list)} recipient(s).',
            'recipients': recipients_list,
            'sent_count': sent_count
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Failed to send test email: {str(e)}", exc_info=True)
        
        # Provide helpful error messages based on common issues
        error_message = str(e)
        if 'Authentication' in error_message or 'Username and Password not accepted' in error_message:
            error_message = 'SMTP authentication failed. Please check your email username and password in .env file.'
        elif 'Connection refused' in error_message:
            error_message = 'Could not connect to SMTP server. Please check EMAIL_HOST and EMAIL_PORT settings.'
        elif 'timed out' in error_message.lower():
            error_message = 'Connection to SMTP server timed out. Check your firewall and network settings.'
        
        return Response({
            'success': False,
            'message': f'Failed to send test email: {error_message}',
            'recipients': [],
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
