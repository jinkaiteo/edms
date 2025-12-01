"""
Real-time Notification WebSocket Consumer

Provides real-time notification delivery to authenticated users
when workflow events occur.
"""

import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import TokenError

User = get_user_model()


class NotificationConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for real-time notifications."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user_group_name = None
        
    async def connect(self):
        """Handle WebSocket connection."""
        # Accept connection first, then check authentication
        await self.accept()
        
        # Check authentication
        user = self.scope.get('user')
        if user and user.is_authenticated:
            # Create user-specific group for notifications
            self.user_group_name = f'notifications_{user.id}'
            
            # Join user's notification group
            await self.channel_layer.group_add(
                self.user_group_name,
                self.channel_name
            )
            
            print(f"🔔 Notification WebSocket connected for user: {user.username}")
            
            # Send initial notification count
            await self.send_notification_count()
            
        else:
            print(f"⚠️ Unauthenticated WebSocket connection, will require auth for data")
            # Send auth required message
            await self.send(text_data=json.dumps({
                'type': 'auth_required',
                'message': 'Authentication required for notifications'
            }))
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        if self.user_group_name:
            # Leave user's notification group
            await self.channel_layer.group_discard(
                self.user_group_name,
                self.channel_name
            )
        
        print(f"🔌 Notification WebSocket disconnected: {close_code}")
    
    async def receive(self, text_data):
        """Handle messages from WebSocket."""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'authenticate':
                # Handle authentication token
                token = data.get('token')
                await self.handle_authentication(token)
                
            elif message_type == 'mark_notification_read':
                # Mark specific notification as read
                notification_id = data.get('notification_id')
                await self.mark_notification_read(notification_id)
                
            elif message_type == 'mark_all_read':
                # Mark all notifications as read
                await self.mark_all_notifications_read()
                
            elif message_type == 'request_notifications':
                # Client requesting current notifications
                await self.send_notifications()
                
            elif message_type == 'ping':
                # Heartbeat ping
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'timestamp': timezone.now().isoformat()
                }))
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON format'
            }))
    
    async def send_notifications(self):
        """Send current notifications to user."""
        try:
            notifications_data = await self.get_user_notifications()
            
            await self.send(text_data=json.dumps({
                'type': 'notifications_update',
                'payload': notifications_data,
                'timestamp': timezone.now().isoformat()
            }))
            
        except Exception as e:
            print(f"❌ Error sending notifications: {e}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Failed to fetch notifications'
            }))
    
    async def send_notification_count(self):
        """Send unread notification count to user."""
        try:
            count = await self.get_unread_count()
            
            await self.send(text_data=json.dumps({
                'type': 'notification_count',
                'payload': {
                    'unread_count': count
                },
                'timestamp': timezone.now().isoformat()
            }))
            
        except Exception as e:
            print(f"❌ Error sending notification count: {e}")
    
    @database_sync_to_async
    def get_user_notifications(self):
        """Get user's notifications from database."""
        from apps.scheduler.models import NotificationQueue
        
        user = self.scope.get('user')
        if not user:
            return {'notifications': [], 'count': 0, 'unread_count': 0}
        
        # Get recent notifications (last 30 days)
        recent_date = timezone.now() - timedelta(days=30)
        notifications = NotificationQueue.objects.filter(
            recipients=user,
            created_at__gte=recent_date
        ).order_by('-created_at')[:20]
        
        # Get unread count (SENT notifications are unread)
        unread_count = NotificationQueue.objects.filter(
            recipients=user,
            created_at__gte=recent_date,
            status='SENT'
        ).count()
        
        notification_data = []
        for notif in notifications:
            notification_data.append({
                'id': str(notif.id),
                'subject': notif.subject,
                'message': notif.message,
                'notification_type': notif.notification_type,
                'priority': notif.priority,
                'status': notif.status,
                'created_at': notif.created_at.isoformat(),
                'sent_at': notif.sent_at.isoformat() if notif.sent_at else None
            })
        
        return {
            'notifications': notification_data,
            'count': len(notification_data),
            'unread_count': unread_count
        }
    
    @database_sync_to_async
    def get_unread_count(self):
        """Get user's unread notification count."""
        from apps.scheduler.models import NotificationQueue
        
        user = self.scope.get('user')
        if not user:
            return 0
        
        recent_date = timezone.now() - timedelta(days=30)
        return NotificationQueue.objects.filter(
            recipients=user,
            created_at__gte=recent_date,
            status='SENT'
        ).count()
    
    @database_sync_to_async
    def mark_notification_read(self, notification_id):
        """Mark specific notification as read."""
        from apps.scheduler.models import NotificationQueue
        
        user = self.scope.get('user')
        if not user or not notification_id:
            return False
        
        try:
            notification = NotificationQueue.objects.get(
                id=notification_id,
                recipients=user
            )
            notification.status = 'READ'
            notification.save(update_fields=['status'])
            return True
        except NotificationQueue.DoesNotExist:
            return False
    
    @database_sync_to_async
    def mark_all_notifications_read(self):
        """Mark all user's notifications as read."""
        from apps.scheduler.models import NotificationQueue
        
        user = self.scope.get('user')
        if not user:
            return 0
        
        recent_date = timezone.now() - timedelta(days=30)
        count = NotificationQueue.objects.filter(
            recipients=user,
            created_at__gte=recent_date,
            status='SENT'
        ).update(
            status='READ'
        )
        return count
    
    async def handle_authentication(self, token):
        """Handle JWT token authentication."""
        if not token:
            await self.send(text_data=json.dumps({
                'type': 'auth_error',
                'message': 'No token provided'
            }))
            return
        
        try:
            # Validate JWT token
            access_token = AccessToken(token)
            user_id = access_token['user_id']
            
            # Get user from database
            user = await database_sync_to_async(User.objects.get)(id=user_id)
            
            # Update scope with authenticated user
            self.scope['user'] = user
            
            # Create user-specific group
            self.user_group_name = f'notifications_{user.id}'
            
            # Join user's notification group
            await self.channel_layer.group_add(
                self.user_group_name,
                self.channel_name
            )
            
            print(f"🔔 User authenticated via WebSocket: {user.username}")
            
            # Send authentication success
            await self.send(text_data=json.dumps({
                'type': 'auth_success',
                'message': f'Authenticated as {user.username}'
            }))
            
            # Send initial notification count
            await self.send_notification_count()
            
        except TokenError:
            await self.send(text_data=json.dumps({
                'type': 'auth_error',
                'message': 'Invalid or expired token'
            }))
        except User.DoesNotExist:
            await self.send(text_data=json.dumps({
                'type': 'auth_error',
                'message': 'User not found'
            }))
        except Exception as e:
            print(f"❌ Authentication error: {e}")
            await self.send(text_data=json.dumps({
                'type': 'auth_error',
                'message': 'Authentication failed'
            }))
    
    # WebSocket message handlers for group messages
    async def notification_created(self, event):
        """Handle new notification created."""
        notification_data = event['notification']
        
        await self.send(text_data=json.dumps({
            'type': 'new_notification',
            'payload': notification_data,
            'timestamp': timezone.now().isoformat()
        }))
        
        # Also send updated count
        await self.send_notification_count()
    
    async def notification_updated(self, event):
        """Handle notification updated."""
        await self.send_notification_count()
        
        await self.send(text_data=json.dumps({
            'type': 'notification_updated',
            'payload': event.get('payload', {}),
            'timestamp': timezone.now().isoformat()
        }))


# Helper function to send real-time notifications
@database_sync_to_async
def send_realtime_notification(user_id, notification_data):
    """Send real-time notification to specific user."""
    from channels.layers import get_channel_layer
    import asyncio
    
    channel_layer = get_channel_layer()
    group_name = f'notifications_{user_id}'
    
    # Send to user's notification group
    asyncio.create_task(
        channel_layer.group_send(
            group_name,
            {
                'type': 'notification_created',
                'notification': notification_data
            }
        )
    )