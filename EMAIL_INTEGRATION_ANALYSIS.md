# Email Integration Analysis - EDMS System

## Current Status: ⚠️ PARTIALLY CONFIGURED (Basic SMTP, Not Implemented)

---

## Table of Contents
1. [Current Implementation](#current-implementation)
2. [Microsoft 365 / Modern Email Integration](#microsoft-365--modern-email-integration)
3. [Integration Options Comparison](#integration-options-comparison)
4. [Recommended Implementation](#recommended-implementation)
5. [Step-by-Step Setup Guide](#step-by-step-setup-guide)
6. [Code Implementation Examples](#code-implementation-examples)

---

## Current Implementation

### ✅ What Exists

**1. Email Configuration (Backend Settings)**
Located in: `backend/edms/settings/base.py`

```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = config('EMAIL_HOST', default='localhost')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@edms-project.com')
```

**2. Notification Service**
Located in: `backend/apps/scheduler/notification_service.py`

- ✅ Service class created
- ✅ Email templates prepared (text format)
- ❌ **All email sending is commented out**
- ❌ Only prints to console: `📧 Email notification prepared...`

**Notification Types Prepared:**
- Task assignment emails
- Document effective date notifications
- Document obsolescence notifications
- Workflow timeout/overdue alerts

**3. Notification Templates Model**
Located in: `backend/apps/settings/models.py`

- ✅ Full NotificationTemplate model with:
  - Template types: EMAIL, SMS, DASHBOARD, PUSH
  - Event types: Document approved, workflow assigned, etc.
  - Template rendering with variables
- ❌ No API to manage templates
- ❌ No integration with notification service

**4. Author Notifications**
Located in: `backend/apps/workflows/author_notifications.py`

- ✅ Service for notifying document authors
- ❌ Email functionality disabled

### ❌ What's Missing

1. **No Active Email Sending** - All `send_mail()` calls are commented out
2. **No Email Configuration** - Environment variables not set
3. **No Microsoft Integration** - Using basic SMTP only
4. **No Modern Auth** - No OAuth2, no app passwords support
5. **No Email Templates** - Only plain text, no HTML
6. **No Attachments** - Cannot send reports or documents via email
7. **No Email Tracking** - No delivery status, no read receipts
8. **No Queue Management** - Emails sent synchronously (blocking)

---

## Microsoft 365 / Modern Email Integration

### Understanding Modern Microsoft Email

**Traditional SMTP (Old Way - Deprecated):**
- ❌ Username + Password authentication
- ❌ Microsoft is disabling this (Basic Auth deprecation)
- ❌ Less secure
- ❌ Requires "App Passwords" workaround

**Modern Approach (OAuth2 / Microsoft Graph API):**
- ✅ OAuth2 authentication (more secure)
- ✅ Microsoft Graph API (recommended)
- ✅ Application permissions
- ✅ Better rate limits
- ✅ Advanced features (read receipts, tracking, etc.)

---

## Integration Options Comparison

### Option 1: Basic SMTP with App Password (Quick & Simple)
**Good for:** Small deployments, testing, legacy systems

**Pros:**
- ✅ Simple configuration (5 environment variables)
- ✅ Works with existing Django code
- ✅ No additional libraries needed
- ✅ 10-minute setup

**Cons:**
- ⚠️ Requires Microsoft "App Password" (less secure)
- ⚠️ Microsoft may disable in future
- ⚠️ Limited features (no tracking, analytics)
- ⚠️ Rate limits (30 emails/minute)

**Configuration:**
```env
EMAIL_HOST=smtp.office365.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=edms@yourcompany.com
EMAIL_HOST_PASSWORD=<app-password-here>
DEFAULT_FROM_EMAIL=edms@yourcompany.com
```

---

### Option 2: Microsoft Graph API with OAuth2 (Modern & Recommended)
**Good for:** Production systems, enterprise deployments

**Pros:**
- ✅ Modern OAuth2 authentication (secure)
- ✅ Future-proof (Microsoft recommended method)
- ✅ Rich features (attachments, tracking, calendar integration)
- ✅ Better rate limits (10,000+ emails/day)
- ✅ Advanced analytics
- ✅ No password storage needed

**Cons:**
- ⚠️ More complex setup (Azure AD app registration required)
- ⚠️ Requires additional library (`msal` or `msgraph-sdk-python`)
- ⚠️ Learning curve for OAuth2 flow
- ⚠️ 1-2 hours initial setup

**Required Libraries:**
```txt
msal==1.24.0                    # Microsoft Authentication Library
msgraph-core==0.2.2            # Microsoft Graph Core
msgraph-sdk-python==1.0.0      # Microsoft Graph SDK (optional)
```

---

### Option 3: Third-Party Email Service (SendGrid, AWS SES, Mailgun)
**Good for:** High-volume, transactional emails

**Pros:**
- ✅ Very simple API integration
- ✅ Excellent deliverability
- ✅ Built-in analytics and tracking
- ✅ No SMTP configuration needed
- ✅ High rate limits

**Cons:**
- ⚠️ Additional cost ($10-100/month)
- ⚠️ Email address might not be company domain
- ⚠️ Vendor lock-in
- ⚠️ May require email verification setup

---

## Recommended Implementation

### For Your Use Case: **Option 2 (Microsoft Graph API)**

**Reasoning:**
1. ✅ You're already in Microsoft ecosystem
2. ✅ More secure than SMTP
3. ✅ Future-proof (Microsoft recommended)
4. ✅ Better for compliance (audit trail, tracking)
5. ✅ Supports advanced features (reports, attachments)

**Fallback:** Keep Option 1 (SMTP) as backup for development/testing

---

## Step-by-Step Setup Guide

### Phase 1: Quick Setup (SMTP with App Password) - 10 minutes

**Step 1: Create Microsoft App Password**
1. Go to https://account.microsoft.com/security
2. Click "Advanced security options"
3. Click "Create a new app password"
4. Copy the generated password (save securely!)

**Step 2: Configure Django**
Update `backend/.env`:
```env
EMAIL_HOST=smtp.office365.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@yourcompany.com
EMAIL_HOST_PASSWORD=<paste-app-password-here>
DEFAULT_FROM_EMAIL=your-email@yourcompany.com
```

**Step 3: Test Email**
```python
python manage.py shell
>>> from django.core.mail import send_mail
>>> send_mail(
...     'Test Email',
...     'This is a test from EDMS',
...     'your-email@yourcompany.com',
...     ['recipient@example.com'],
...     fail_silently=False
... )
```

**Step 4: Enable Notifications**
Uncomment email code in `backend/apps/scheduler/notification_service.py`:
```python
# Remove these lines:
# send_mail(
# Change to:
send_mail(
```

---

### Phase 2: Modern Setup (Microsoft Graph API) - 1-2 hours

**Step 1: Azure AD App Registration**

1. Go to https://portal.azure.com
2. Navigate to "Azure Active Directory" → "App registrations" → "New registration"
3. Set name: "EDMS Email Service"
4. Supported account types: "Single tenant"
5. Redirect URI: Leave blank for server-to-server
6. Click "Register"

**Step 2: Configure API Permissions**

1. In your app, go to "API permissions"
2. Click "Add a permission" → "Microsoft Graph" → "Application permissions"
3. Add these permissions:
   - `Mail.Send` (Send mail as any user)
   - `User.Read.All` (Read all users)
4. Click "Grant admin consent for [Your Org]"

**Step 3: Create Client Secret**

1. Go to "Certificates & secrets"
2. Click "New client secret"
3. Description: "EDMS Email Service Secret"
4. Expires: 24 months (or custom)
5. Click "Add"
6. **Copy the Value immediately** (you can't see it again!)

**Step 4: Note Your Credentials**

You'll need:
- **Tenant ID**: Found in "Overview" page
- **Client ID**: Found in "Overview" page
- **Client Secret**: The value you just copied

**Step 5: Install Python Libraries**

Add to `backend/requirements/base.txt`:
```txt
msal==1.24.0
requests==2.31.0  # Usually already installed
```

Run:
```bash
pip install msal==1.24.0
```

**Step 6: Configure Django**

Update `backend/.env`:
```env
# Microsoft Graph API Configuration
MICROSOFT_TENANT_ID=your-tenant-id-here
MICROSOFT_CLIENT_ID=your-client-id-here
MICROSOFT_CLIENT_SECRET=your-client-secret-here
MICROSOFT_FROM_EMAIL=noreply@yourcompany.com

# Keep SMTP as fallback
EMAIL_HOST=smtp.office365.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@yourcompany.com
EMAIL_HOST_PASSWORD=<app-password>
```

---

## Code Implementation Examples

### Example 1: Enhanced Email Service with Microsoft Graph

Create `backend/apps/scheduler/microsoft_email_service.py`:

```python
"""
Microsoft Graph API Email Service
"""
import msal
import requests
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


class MicrosoftEmailService:
    """Send emails via Microsoft Graph API"""
    
    def __init__(self):
        self.tenant_id = getattr(settings, 'MICROSOFT_TENANT_ID', None)
        self.client_id = getattr(settings, 'MICROSOFT_CLIENT_ID', None)
        self.client_secret = getattr(settings, 'MICROSOFT_CLIENT_SECRET', None)
        self.from_email = getattr(settings, 'MICROSOFT_FROM_EMAIL', settings.DEFAULT_FROM_EMAIL)
        
        if not all([self.tenant_id, self.client_id, self.client_secret]):
            logger.warning("Microsoft Graph API credentials not configured")
            self.enabled = False
        else:
            self.enabled = True
    
    def get_access_token(self):
        """Get OAuth2 access token from Microsoft"""
        authority = f"https://login.microsoftonline.com/{self.tenant_id}"
        app = msal.ConfidentialClientApplication(
            self.client_id,
            authority=authority,
            client_credential=self.client_secret
        )
        
        # Get token for Microsoft Graph
        result = app.acquire_token_for_client(
            scopes=["https://graph.microsoft.com/.default"]
        )
        
        if "access_token" in result:
            return result["access_token"]
        else:
            logger.error(f"Failed to get access token: {result.get('error')}")
            return None
    
    def send_email(self, to_emails, subject, body_text, body_html=None, attachments=None):
        """
        Send email via Microsoft Graph API
        
        Args:
            to_emails: List of recipient email addresses
            subject: Email subject
            body_text: Plain text body
            body_html: HTML body (optional)
            attachments: List of attachment file paths (optional)
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.enabled:
            logger.error("Microsoft Graph API not configured")
            return False
        
        # Get access token
        token = self.get_access_token()
        if not token:
            return False
        
        # Prepare email message
        message = {
            "message": {
                "subject": subject,
                "body": {
                    "contentType": "HTML" if body_html else "Text",
                    "content": body_html or body_text
                },
                "toRecipients": [
                    {"emailAddress": {"address": email}} for email in to_emails
                ]
            },
            "saveToSentItems": "true"
        }
        
        # Add attachments if provided
        if attachments:
            message["message"]["attachments"] = []
            for file_path in attachments:
                try:
                    with open(file_path, 'rb') as f:
                        import base64
                        content = base64.b64encode(f.read()).decode()
                        message["message"]["attachments"].append({
                            "@odata.type": "#microsoft.graph.fileAttachment",
                            "name": file_path.split('/')[-1],
                            "contentBytes": content
                        })
                except Exception as e:
                    logger.error(f"Failed to attach file {file_path}: {e}")
        
        # Send email via Graph API
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        # Use delegated sending (send as the from_email user)
        url = f"https://graph.microsoft.com/v1.0/users/{self.from_email}/sendMail"
        
        try:
            response = requests.post(url, json=message, headers=headers)
            
            if response.status_code == 202:
                logger.info(f"Email sent successfully to {', '.join(to_emails)}")
                return True
            else:
                logger.error(f"Failed to send email: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Exception sending email: {e}")
            return False


# Singleton instance
microsoft_email_service = MicrosoftEmailService()
```

### Example 2: Unified Notification Service (with fallback)

Update `backend/apps/scheduler/notification_service.py`:

```python
"""
Unified Notification Service with Microsoft Graph + SMTP Fallback
"""
from django.core.mail import send_mail
from django.conf import settings
from .microsoft_email_service import microsoft_email_service
import logging

logger = logging.getLogger(__name__)


class UnifiedNotificationService:
    """Send notifications with automatic fallback"""
    
    def send_email(self, to_emails, subject, body_text, body_html=None):
        """
        Send email with automatic fallback
        Tries: Microsoft Graph API → SMTP → Failure
        """
        
        # Ensure to_emails is a list
        if isinstance(to_emails, str):
            to_emails = [to_emails]
        
        # Try Microsoft Graph API first
        if microsoft_email_service.enabled:
            logger.info("Attempting to send via Microsoft Graph API")
            success = microsoft_email_service.send_email(
                to_emails=to_emails,
                subject=subject,
                body_text=body_text,
                body_html=body_html
            )
            if success:
                return True
            logger.warning("Microsoft Graph API failed, falling back to SMTP")
        
        # Fallback to Django SMTP
        try:
            logger.info("Attempting to send via SMTP")
            send_mail(
                subject=subject,
                message=body_text,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=to_emails,
                fail_silently=False,
                html_message=body_html
            )
            logger.info(f"Email sent successfully via SMTP to {', '.join(to_emails)}")
            return True
        except Exception as e:
            logger.error(f"SMTP send failed: {e}")
            return False
    
    def send_task_assignment_email(self, user, task_type, document):
        """Send task assignment notification"""
        subject = f"New Task Assigned: {task_type} - {document.document_number}"
        
        body_text = f"""
        A new {task_type.lower()} task has been assigned to you.
        
        Document: {document.document_number} - {document.title}
        Author: {document.author.get_full_name()}
        
        Please log in to the EDMS to review this document.
        """
        
        body_html = f"""
        <html>
        <body>
            <h2>New Task Assigned</h2>
            <p>A new <strong>{task_type.lower()}</strong> task has been assigned to you.</p>
            
            <table style="border-collapse: collapse; margin: 20px 0;">
                <tr>
                    <td style="padding: 8px; font-weight: bold;">Document:</td>
                    <td style="padding: 8px;">{document.document_number} - {document.title}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; font-weight: bold;">Author:</td>
                    <td style="padding: 8px;">{document.author.get_full_name()}</td>
                </tr>
            </table>
            
            <p><a href="https://edms.yourcompany.com/documents/{document.id}" style="background-color: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Review Document</a></p>
        </body>
        </html>
        """
        
        return self.send_email(
            to_emails=[user.email],
            subject=subject,
            body_text=body_text,
            body_html=body_html
        )
    
    def send_report_email(self, user, report, pdf_path):
        """Send compliance report via email with PDF attachment"""
        subject = f"Compliance Report: {report.name}"
        
        body_text = f"""
        Your compliance report has been generated and is attached.
        
        Report: {report.name}
        Type: {report.get_report_type_display()}
        Period: {report.date_from} to {report.date_to}
        """
        
        body_html = f"""
        <html>
        <body>
            <h2>Compliance Report Ready</h2>
            <p>Your compliance report has been generated and is attached to this email.</p>
            
            <table style="border-collapse: collapse; margin: 20px 0;">
                <tr>
                    <td style="padding: 8px; font-weight: bold;">Report:</td>
                    <td style="padding: 8px;">{report.name}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; font-weight: bold;">Type:</td>
                    <td style="padding: 8px;">{report.get_report_type_display()}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; font-weight: bold;">Period:</td>
                    <td style="padding: 8px;">{report.date_from} to {report.date_to}</td>
                </tr>
            </table>
        </body>
        </html>
        """
        
        # Note: Attachments only work with Microsoft Graph API
        if microsoft_email_service.enabled:
            return microsoft_email_service.send_email(
                to_emails=[user.email],
                subject=subject,
                body_text=body_text,
                body_html=body_html,
                attachments=[pdf_path]
            )
        else:
            # SMTP doesn't easily support attachments in this simple setup
            logger.warning("Attachments not supported with SMTP backend")
            return self.send_email(
                to_emails=[user.email],
                subject=subject,
                body_text=body_text + "\n\nNote: Please download the report from the EDMS system.",
                body_html=body_html
            )


# Singleton instance
notification_service = UnifiedNotificationService()
```

### Example 3: Add to Django Settings

Update `backend/edms/settings/base.py`:

```python
# Microsoft Graph API Configuration
MICROSOFT_TENANT_ID = config('MICROSOFT_TENANT_ID', default=None)
MICROSOFT_CLIENT_ID = config('MICROSOFT_CLIENT_ID', default=None)
MICROSOFT_CLIENT_SECRET = config('MICROSOFT_CLIENT_SECRET', default=None)
MICROSOFT_FROM_EMAIL = config('MICROSOFT_FROM_EMAIL', default=DEFAULT_FROM_EMAIL)

# Email backend selection
USE_MICROSOFT_GRAPH = config('USE_MICROSOFT_GRAPH', default=False, cast=bool)
```

---

## Testing

### Test Microsoft Graph API Setup

Create `backend/test_microsoft_email.py`:

```python
#!/usr/bin/env python
"""Test Microsoft Graph API email setup"""

import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'edms.settings.development')
django.setup()

from apps.scheduler.microsoft_email_service import microsoft_email_service

def test_email():
    print("Testing Microsoft Graph API Email...")
    print(f"Configured: {microsoft_email_service.enabled}")
    
    if not microsoft_email_service.enabled:
        print("❌ Microsoft Graph API not configured")
        print("Please set MICROSOFT_TENANT_ID, MICROSOFT_CLIENT_ID, and MICROSOFT_CLIENT_SECRET")
        return
    
    # Test getting token
    print("\nTesting authentication...")
    token = microsoft_email_service.get_access_token()
    
    if token:
        print("✅ Authentication successful")
        print(f"Token: {token[:20]}...")
        
        # Test sending email
        print("\nTesting email send...")
        test_email = input("Enter recipient email for test: ")
        
        success = microsoft_email_service.send_email(
            to_emails=[test_email],
            subject="EDMS Test Email",
            body_text="This is a test email from EDMS using Microsoft Graph API",
            body_html="<h1>EDMS Test Email</h1><p>This is a test email from EDMS using <strong>Microsoft Graph API</strong></p>"
        )
        
        if success:
            print("✅ Email sent successfully!")
        else:
            print("❌ Email send failed")
    else:
        print("❌ Authentication failed")
        print("Check your credentials in .env file")

if __name__ == "__main__":
    test_email()
```

Run: `python backend/test_microsoft_email.py`

---

## Summary & Recommendations

### Current State
- ⚠️ Email infrastructure 40% complete
- ✅ Notification service structure exists
- ✅ Email settings configured
- ❌ No active email sending
- ❌ No Microsoft integration

### Recommended Action Plan

**Phase 1: Quick Win (1 hour)**
1. Enable SMTP with App Password
2. Uncomment email code in notification service
3. Test with a few notifications
4. **Value:** Basic email functionality working

**Phase 2: Modern Integration (2-3 hours)**
1. Register Azure AD application
2. Install MSAL library
3. Implement Microsoft Graph service
4. Test with attachments
5. **Value:** Production-ready, secure email system

**Phase 3: Enhancement (Optional)**
1. HTML email templates
2. Email tracking and analytics
3. Scheduled/batched emails
4. Email queue (Celery integration)
5. **Value:** Enterprise-grade email system

---

## Quick Start Commands

### Enable Email Now (SMTP - 5 minutes)

```bash
# 1. Edit .env file
nano backend/.env

# Add these lines:
EMAIL_HOST=smtp.office365.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@yourcompany.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=your-email@yourcompany.com

# 2. Test
docker compose exec backend python manage.py shell
>>> from django.core.mail import send_mail
>>> send_mail('Test', 'Test message', 'from@company.com', ['to@company.com'])

# 3. Restart backend
docker compose restart backend
```

---

**Status:** ✅ Analysis Complete
**Date:** December 21, 2024
**Recommendation:** Start with Phase 1 (SMTP), then implement Phase 2 (Microsoft Graph)
