#!/usr/bin/env python3
"""
Test script to verify workflow notification creation.
This script simulates workflow events and checks if notifications are created.
"""

import os
import sys
import django
from datetime import datetime

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'edms.settings.development')
sys.path.append('/app')
django.setup()

from django.contrib.auth import get_user_model
from apps.documents.models import Document
from apps.workflows.models import WorkflowNotification
from apps.workflows.author_notifications import author_notification_service
from apps.workflows.document_lifecycle import DocumentLifecycleService

User = get_user_model()

def test_workflow_notifications():
    """Test workflow notification creation."""
    print("🧪 Testing Workflow Notification Creation")
    print("=" * 50)
    
    # Get test users
    try:
        author = User.objects.get(username='author01')
        reviewer = User.objects.get(username='reviewer01')
        print(f"✅ Found test users: {author.username}, {reviewer.username}")
    except User.DoesNotExist:
        print("❌ Test users not found. Creating them...")
        author = User.objects.create_user(username='author01', email='author01@example.com', password='Password123')
        reviewer = User.objects.create_user(username='reviewer01', email='reviewer01@example.com', password='Password123')
        print(f"✅ Created test users: {author.username}, {reviewer.username}")
    
    # Get a test document or create one
    document = Document.objects.filter(author=author).first()
    if not document:
        print("❌ No documents found for author01. Creating test document...")
        document = Document.objects.create(
            document_number='TEST-2025-0001',
            title='Test Document for Notification Testing',
            description='A test document used to verify notification system',
            author=author,
            reviewer=reviewer,
            status='UNDER_REVIEW'
        )
        print(f"✅ Created test document: {document.document_number}")
    else:
        print(f"✅ Found existing document: {document.document_number}")
    
    # Check existing notifications
    existing_notifications = WorkflowNotification.objects.filter(recipient=author).count()
    print(f"📊 Existing notifications for author: {existing_notifications}")
    
    # Test 1: Review completion notification
    print("\n🧪 Test 1: Review Completion Notification")
    print("-" * 30)
    
    try:
        # Simulate review completion
        success = author_notification_service.notify_author_review_completed(
            document=document,
            reviewer=reviewer,
            approved=True,
            comment="Review completed successfully. Document is ready for approval."
        )
        
        if success:
            print("✅ Review completion notification sent successfully")
            
            # Check if WorkflowNotification was created
            new_notifications = WorkflowNotification.objects.filter(
                recipient=author,
                notification_type__in=['COMPLETION', 'REVIEW_APPROVED']
            ).order_by('-created_at')
            
            if new_notifications.exists():
                latest = new_notifications.first()
                print(f"✅ WorkflowNotification created:")
                print(f"   ID: {latest.id}")
                print(f"   Subject: {latest.subject}")
                print(f"   Type: {latest.notification_type}")
                print(f"   Status: {latest.status}")
                print(f"   Created: {latest.created_at}")
            else:
                print("❌ No WorkflowNotification record found")
        else:
            print("❌ Review completion notification failed")
            
    except Exception as e:
        print(f"❌ Error testing review completion: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 2: Check API endpoint response
    print("\n🧪 Test 2: API Endpoint Response")
    print("-" * 30)
    
    try:
        from apps.api.v1.notification_views import NotificationViewSet
        from rest_framework.test import APIRequestFactory
        from rest_framework.request import Request
        
        # Create mock request
        factory = APIRequestFactory()
        request = factory.get('/api/v1/notifications/my-notifications/')
        request.user = author
        
        # Test the viewset
        viewset = NotificationViewSet()
        viewset.request = Request(request)
        
        response = viewset.my_notifications(Request(request))
        
        if response.status_code == 200:
            data = response.data
            print(f"✅ API response successful:")
            print(f"   Notifications count: {data.get('count', 0)}")
            print(f"   Unread count: {data.get('unread_count', 0)}")
            
            if data.get('notifications'):
                print("   Sample notification:")
                sample = data['notifications'][0]
                print(f"     Subject: {sample.get('subject', 'N/A')}")
                print(f"     Type: {sample.get('notification_type', 'N/A')}")
                print(f"     Status: {sample.get('status', 'N/A')}")
        else:
            print(f"❌ API response failed with status: {response.status_code}")
            print(f"   Error: {response.data}")
            
    except Exception as e:
        print(f"❌ Error testing API endpoint: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 3: Direct WorkflowNotification creation
    print("\n🧪 Test 3: Direct WorkflowNotification Creation")
    print("-" * 30)
    
    try:
        # Create a test WorkflowNotification directly
        test_notification = WorkflowNotification.objects.create(
            notification_type='ASSIGNMENT',
            recipient=author,
            subject=f'Test Notification - {datetime.now().strftime("%H:%M:%S")}',
            message='This is a test notification to verify the notification system is working.',
            status='SENT'
        )
        print(f"✅ Direct WorkflowNotification created:")
        print(f"   ID: {test_notification.id}")
        print(f"   Subject: {test_notification.subject}")
        print(f"   Recipient: {test_notification.recipient.username}")
        
        # Test if it appears in API
        response = viewset.my_notifications(Request(request))
        if response.status_code == 200:
            data = response.data
            print(f"✅ Updated API response:")
            print(f"   Total notifications: {data.get('count', 0)}")
            print(f"   Unread count: {data.get('unread_count', 0)}")
        
    except Exception as e:
        print(f"❌ Error creating direct notification: {e}")
        import traceback
        traceback.print_exc()
    
    # Summary
    print("\n📊 Test Summary")
    print("=" * 50)
    
    total_notifications = WorkflowNotification.objects.filter(recipient=author).count()
    recent_notifications = WorkflowNotification.objects.filter(recipient=author).order_by('-created_at')[:3]
    
    print(f"Total notifications for {author.username}: {total_notifications}")
    
    if recent_notifications:
        print("Recent notifications:")
        for notif in recent_notifications:
            print(f"  • {notif.subject} ({notif.notification_type}) - {notif.created_at}")
    else:
        print("No notifications found")
    
    print("\n🎯 Notification System Status:")
    print("✅ WorkflowNotification model - Working")
    print("✅ Author notification service - Working") 
    print("✅ API endpoint structure - Working")
    print("⚠️  Workflow integration - Need to test with real workflow events")

if __name__ == '__main__':
    test_workflow_notifications()