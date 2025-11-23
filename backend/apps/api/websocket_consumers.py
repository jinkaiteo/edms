"""
WebSocket consumers for real-time dashboard updates.

Provides WebSocket endpoints for real-time data streaming to frontend dashboards.
"""

import json
import asyncio
from datetime import timedelta
from django.utils import timezone
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model

User = get_user_model()


class DashboardConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for dashboard real-time updates."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.room_group_name = 'dashboard_updates'
        self.update_task = None
        
    async def connect(self):
        """Handle WebSocket connection."""
        # Check authentication
        user = self.scope.get('user')
        if user and user.is_authenticated:
            # Join dashboard updates group
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
            
            await self.accept()
            
            # Send initial dashboard data
            await self.send_dashboard_stats()
            
            # Start periodic updates (every 30 seconds)
            self.update_task = asyncio.create_task(self.periodic_updates())
            
            print(f"✅ Dashboard WebSocket connected for user: {user.username}")
        else:
            await self.close(code=4001)  # Unauthorized
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        # Cancel periodic updates
        if self.update_task:
            self.update_task.cancel()
            
        # Leave dashboard updates group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        
        print(f"🔌 Dashboard WebSocket disconnected: {close_code}")
    
    async def receive(self, text_data):
        """Handle messages from WebSocket."""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'request_update':
                # Client requesting immediate update
                await self.send_dashboard_stats()
            elif message_type == 'subscribe_to_updates':
                # Client subscribing to specific update types
                # Could implement filtering here
                pass
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON format'
            }))
    
    async def periodic_updates(self):
        """Send periodic dashboard updates."""
        try:
            while True:
                await asyncio.sleep(30)  # Update every 30 seconds
                await self.send_dashboard_stats()
        except asyncio.CancelledError:
            pass
    
    async def send_dashboard_stats(self):
        """Send current dashboard statistics."""
        try:
            stats = await self.get_dashboard_stats()
            
            await self.send(text_data=json.dumps({
                'type': 'dashboard_update',
                'payload': stats,
                'timestamp': timezone.now().isoformat()
            }))
            
        except Exception as e:
            print(f"❌ Error sending dashboard stats: {e}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Failed to fetch dashboard statistics'
            }))
    
    @database_sync_to_async
    def get_dashboard_stats(self):
        """Get dashboard statistics from database."""
        from django.db import connection
        
        with connection.cursor() as cursor:
            try:
                # Active users count
                cursor.execute("SELECT COUNT(*) FROM users WHERE is_active = true")
                active_users_count = cursor.fetchone()[0]
                
                # Active workflows count
                cursor.execute("SELECT COUNT(*) FROM workflow_instances WHERE is_active = true")
                active_workflows_count = cursor.fetchone()[0]
                
                # Placeholders count
                cursor.execute("SELECT COUNT(*) FROM placeholder_definitions")
                placeholders_count = cursor.fetchone()[0]
                
                # Audit entries in last 24 hours
                twenty_four_hours_ago = timezone.now() - timedelta(hours=24)
                cursor.execute(
                    "SELECT COUNT(*) FROM audit_trail WHERE timestamp >= %s",
                    [twenty_four_hours_ago]
                )
                audit_entries_24h = cursor.fetchone()[0]
                
                # Total documents count
                cursor.execute("SELECT COUNT(*) FROM documents")
                total_documents_count = cursor.fetchone()[0]
                
                # Pending reviews count
                cursor.execute(
                    "SELECT COUNT(*) FROM workflow_instances WHERE state ILIKE '%review%' AND is_active = true"
                )
                pending_reviews_count = cursor.fetchone()[0]
                
                # Recent activity (last 3 audit entries for WebSocket)
                cursor.execute("""
                    SELECT uuid, action, object_representation, description, timestamp, user_display_name 
                    FROM audit_trail 
                    ORDER BY timestamp DESC 
                    LIMIT 3
                """)
                
                recent_activities = cursor.fetchall()
                
                activity_list = []
                for audit in recent_activities:
                    activity_item = {
                        'id': str(audit[0]),
                        'type': self.map_audit_action_to_type(audit[1]),
                        'title': self.generate_activity_title(audit[1], audit[2]),
                        'description': audit[3],
                        'timestamp': audit[4].isoformat() if audit[4] else timezone.now().isoformat(),
                        'user': audit[5] if audit[5] else 'System',
                        'icon': self.get_activity_icon(audit[1]),
                        'iconColor': self.get_activity_color(audit[1])
                    }
                    activity_list.append(activity_item)
                
                return {
                    'total_documents': total_documents_count,
                    'pending_reviews': pending_reviews_count,
                    'active_workflows': active_workflows_count,
                    'active_users': active_users_count,
                    'placeholders': placeholders_count,
                    'audit_entries_24h': audit_entries_24h,
                    'recent_activity': activity_list,
                    'timestamp': timezone.now().isoformat(),
                    'cache_duration': 30  # WebSocket updates every 30 seconds
                }
                
            except Exception as e:
                print(f"❌ Database error in WebSocket: {e}")
                # Return fallback data
                return {
                    'total_documents': 0,
                    'pending_reviews': 0,
                    'active_workflows': 0,
                    'active_users': 0,
                    'placeholders': 0,
                    'audit_entries_24h': 0,
                    'recent_activity': [],
                    'timestamp': timezone.now().isoformat(),
                    'cache_duration': 30
                }
    
    def map_audit_action_to_type(self, action):
        """Map audit action to activity type."""
        if not action:
            return 'system_activity'
            
        action_mapping = {
            'CREATE': 'document_created',
            'UPDATE': 'document_updated', 
            'DELETE': 'document_deleted',
            'SIGN': 'document_signed',
            'LOGIN': 'user_login',
            'WORKFLOW_COMPLETE': 'workflow_completed',
            'WORKFLOW_TRANSITION': 'workflow_updated'
        }
        return action_mapping.get(action, 'system_activity')
    
    def generate_activity_title(self, action, object_representation):
        """Generate human-readable activity title."""
        if not action:
            return 'System Activity'
            
        action_titles = {
            'CREATE': f"Document Created: {object_representation or 'Unknown'}",
            'UPDATE': f"Document Updated: {object_representation or 'Unknown'}",
            'DELETE': f"Document Deleted: {object_representation or 'Unknown'}",
            'SIGN': f"Document Signed: {object_representation or 'Unknown'}",
            'LOGIN': f"User Login: {object_representation or 'Unknown'}",
            'WORKFLOW_COMPLETE': f"Workflow Completed: {object_representation or 'Unknown'}",
            'WORKFLOW_TRANSITION': f"Workflow Updated: {object_representation or 'Unknown'}"
        }
        return action_titles.get(action, f"{action}: {object_representation or 'Unknown'}")
    
    def get_activity_icon(self, action):
        """Get icon for activity type."""
        icon_mapping = {
            'CREATE': '📄',
            'UPDATE': '✏️',
            'DELETE': '🗑️',
            'SIGN': '✍️',
            'LOGIN': '🔐',
            'WORKFLOW_COMPLETE': '✅',
            'WORKFLOW_TRANSITION': '🔄'
        }
        return icon_mapping.get(action, '📊')
    
    def get_activity_color(self, action):
        """Get color for activity type."""
        color_mapping = {
            'CREATE': 'bg-green-500',
            'UPDATE': 'bg-blue-500',
            'DELETE': 'bg-red-500',
            'SIGN': 'bg-purple-500',
            'LOGIN': 'bg-indigo-500',
            'WORKFLOW_COMPLETE': 'bg-emerald-500',
            'WORKFLOW_TRANSITION': 'bg-orange-500'
        }
        return color_mapping.get(action, 'bg-gray-500')
    
    # Group message handler
    async def dashboard_update(self, event):
        """Handle dashboard update group messages."""
        await self.send(text_data=json.dumps({
            'type': 'dashboard_update',
            'payload': event['payload'],
            'timestamp': event['timestamp']
        }))