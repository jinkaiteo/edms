"""
Django Admin Configuration for Notification System

Provides admin interface for notification queue management and monitoring.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse, path
from django.shortcuts import redirect
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta

from .models import NotificationQueue
from .notification_service import notification_service


@admin.register(NotificationQueue)
class NotificationQueueAdmin(admin.ModelAdmin):
    """Admin interface for notification queue management."""
    
    list_display = [
        'subject_truncated',
        'notification_type',
        'status_badge',
        'priority_badge',
        'recipient_count',
        'scheduled_at',
        'delivery_attempts',
        'actions_column'
    ]
    
    list_filter = [
        'status',
        'priority',
        'notification_type',
        'scheduled_at',
        'created_at'
    ]
    
    search_fields = [
        'subject',
        'message',
        'notification_type',
        'recipients__username',
        'recipients__email'
    ]
    
    readonly_fields = [
        'created_at',
        'sent_at',
        'delivery_attempts',
        'error_message',
        'recipient_display'
    ]
    
    fieldsets = (
        ('Notification Details', {
            'fields': (
                'notification_type',
                'priority',
                'subject',
                'message'
            )
        }),
        ('Recipients', {
            'fields': (
                'recipients',
                'recipient_emails',
                'recipient_display'
            )
        }),
        ('Scheduling & Delivery', {
            'fields': (
                'scheduled_at',
                'status',
                'delivery_channels',
                'max_attempts'
            )
        }),
        ('Delivery Status', {
            'fields': (
                'sent_at',
                'delivery_attempts',
                'error_message'
            ),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': (
                'notification_data',
                'created_at',
                'created_by'
            ),
            'classes': ('collapse',)
        })
    )
    
    actions = ['send_selected_notifications', 'cancel_selected_notifications']
    
    def subject_truncated(self, obj):
        """Display truncated subject with full subject in tooltip."""
        if len(obj.subject) > 50:
            truncated = obj.subject[:50] + '...'
            return format_html(
                '<span title="{}">{}</span>',
                obj.subject,
                truncated
            )
        return obj.subject
    subject_truncated.short_description = 'Subject'
    
    def status_badge(self, obj):
        """Display status with color coding."""
        colors = {
            'PENDING': '#ffc107',  # yellow
            'SENT': '#28a745',     # green
            'FAILED': '#dc3545',   # red
            'CANCELLED': '#6c757d' # gray
        }
        color = colors.get(obj.status, '#007bff')
        
        return format_html(
            '<span style="background: {}; color: white; padding: 2px 8px; '
            'border-radius: 3px; font-size: 11px; font-weight: bold;">{}</span>',
            color,
            obj.status
        )
    status_badge.short_description = 'Status'
    
    def priority_badge(self, obj):
        """Display priority with color coding."""
        colors = {
            'LOW': '#17a2b8',    # info blue
            'NORMAL': '#28a745',  # success green
            'HIGH': '#ffc107',    # warning yellow
            'URGENT': '#dc3545'   # danger red
        }
        color = colors.get(obj.priority, '#6c757d')
        
        return format_html(
            '<span style="background: {}; color: white; padding: 2px 6px; '
            'border-radius: 3px; font-size: 10px; font-weight: bold;">{}</span>',
            color,
            obj.priority
        )
    priority_badge.short_description = 'Priority'
    
    def recipient_count(self, obj):
        """Display number of recipients."""
        count = obj.recipients.count()
        email_count = len(obj.recipient_emails or [])
        total = count + email_count
        
        if total > 0:
            return format_html(
                '<span style="font-weight: bold; color: #007bff;">{}</span> recipient{}',
                total,
                's' if total != 1 else ''
            )
        return format_html('<span style="color: #dc3545;">No recipients</span>')
    recipient_count.short_description = 'Recipients'
    
    def recipient_display(self, obj):
        """Display detailed recipient information."""
        recipients = []
        
        # User recipients
        for user in obj.recipients.all():
            recipients.append(f"👤 {user.get_full_name()} ({user.email})")
        
        # Email recipients
        for email in (obj.recipient_emails or []):
            recipients.append(f"✉️ {email}")
        
        if recipients:
            return format_html('<br>'.join(recipients))
        return "No recipients"
    recipient_display.short_description = 'Recipient Details'
    
    def actions_column(self, obj):
        """Action buttons for notification management."""
        buttons = []
        
        if obj.status == 'PENDING':
            buttons.append(
                f'<a href="{reverse("admin:scheduler_send_notification", args=[obj.pk])}" '
                f'class="button" style="background: #28a745; color: white; padding: 3px 8px; '
                f'text-decoration: none; border-radius: 3px; font-size: 11px; margin-right: 3px;">Send Now</a>'
            )
            buttons.append(
                f'<a href="{reverse("admin:scheduler_cancel_notification", args=[obj.pk])}" '
                f'class="button" style="background: #dc3545; color: white; padding: 3px 8px; '
                f'text-decoration: none; border-radius: 3px; font-size: 11px;">Cancel</a>'
            )
        elif obj.status == 'FAILED' and obj.can_retry:
            buttons.append(
                f'<a href="{reverse("admin:scheduler_retry_notification", args=[obj.pk])}" '
                f'class="button" style="background: #ffc107; color: black; padding: 3px 8px; '
                f'text-decoration: none; border-radius: 3px; font-size: 11px;">Retry</a>'
            )
        
        return format_html(' '.join(buttons))
    actions_column.short_description = 'Actions'
    
    def get_urls(self):
        """Add custom URLs for notification actions."""
        urls = super().get_urls()
        custom_urls = [
            path(
                'send/<int:notification_id>/',
                self.admin_site.admin_view(self.send_notification_view),
                name='scheduler_send_notification'
            ),
            path(
                'cancel/<int:notification_id>/',
                self.admin_site.admin_view(self.cancel_notification_view),
                name='scheduler_cancel_notification'
            ),
            path(
                'retry/<int:notification_id>/',
                self.admin_site.admin_view(self.retry_notification_view),
                name='scheduler_retry_notification'
            ),
            path(
                'test-notification/',
                self.admin_site.admin_view(self.test_notification_view),
                name='scheduler_test_notification'
            ),
            path(
                'notification-stats/',
                self.admin_site.admin_view(self.notification_stats_view),
                name='scheduler_notification_stats'
            ),
        ]
        return custom_urls + urls
    
    def send_notification_view(self, request, notification_id):
        """Send a pending notification immediately."""
        try:
            notification = NotificationQueue.objects.get(pk=notification_id)
            
            if notification.status != 'PENDING':
                messages.error(request, f'Notification is not in pending status (current: {notification.status})')
                return redirect('admin:scheduler_notificationqueue_changelist')
            
            # Get recipients
            recipients = list(notification.recipients.all())
            
            # Send notification
            success = notification_service.send_immediate_notification(
                recipients=recipients,
                subject=notification.subject,
                message=notification.message,
                notification_type=notification.notification_type
            )
            
            if success:
                # Update notification status
                notification.status = 'SENT'
                notification.sent_at = timezone.now()
                notification.delivery_attempts += 1
                notification.save()
                
                messages.success(request, f'Notification "{notification.subject}" sent successfully')
            else:
                notification.status = 'FAILED'
                notification.error_message = 'Manual send failed'
                notification.delivery_attempts += 1
                notification.save()
                
                messages.error(request, f'Failed to send notification "{notification.subject}"')
                
        except NotificationQueue.DoesNotExist:
            messages.error(request, f'Notification with ID {notification_id} not found')
        except Exception as e:
            messages.error(request, f'Error sending notification: {str(e)}')
        
        return redirect('admin:scheduler_notificationqueue_changelist')
    
    def cancel_notification_view(self, request, notification_id):
        """Cancel a pending notification."""
        try:
            notification = NotificationQueue.objects.get(pk=notification_id)
            
            if notification.status != 'PENDING':
                messages.error(request, f'Cannot cancel notification with status: {notification.status}')
                return redirect('admin:scheduler_notificationqueue_changelist')
            
            notification.status = 'CANCELLED'
            notification.save()
            
            messages.success(request, f'Notification "{notification.subject}" cancelled')
            
        except NotificationQueue.DoesNotExist:
            messages.error(request, f'Notification with ID {notification_id} not found')
        except Exception as e:
            messages.error(request, f'Error cancelling notification: {str(e)}')
        
        return redirect('admin:scheduler_notificationqueue_changelist')
    
    def retry_notification_view(self, request, notification_id):
        """Retry a failed notification."""
        try:
            notification = NotificationQueue.objects.get(pk=notification_id)
            
            if notification.status != 'FAILED':
                messages.error(request, f'Cannot retry notification with status: {notification.status}')
                return redirect('admin:scheduler_notificationqueue_changelist')
            
            if not notification.can_retry:
                messages.error(request, 'Notification has exceeded maximum retry attempts')
                return redirect('admin:scheduler_notificationqueue_changelist')
            
            # Reset notification for retry
            notification.status = 'PENDING'
            notification.error_message = ''
            notification.save()
            
            messages.success(request, f'Notification "{notification.subject}" queued for retry')
            
        except NotificationQueue.DoesNotExist:
            messages.error(request, f'Notification with ID {notification_id} not found')
        except Exception as e:
            messages.error(request, f'Error retrying notification: {str(e)}')
        
        return redirect('admin:scheduler_notificationqueue_changelist')
    
    def test_notification_view(self, request):
        """Send a test notification to verify email configuration."""
        try:
            if request.method == 'POST':
                # Send test notification to current user
                success = notification_service.send_immediate_notification(
                    recipients=[request.user],
                    subject='EDMS Test Notification',
                    message='This is a test notification from the EDMS system. If you receive this, email notifications are working correctly.',
                    notification_type='SYSTEM_TEST'
                )
                
                if success:
                    messages.success(request, 'Test notification sent successfully!')
                else:
                    messages.error(request, 'Failed to send test notification')
            
            return redirect('admin:scheduler_notificationqueue_changelist')
            
        except Exception as e:
            messages.error(request, f'Error sending test notification: {str(e)}')
            return redirect('admin:scheduler_notificationqueue_changelist')
    
    def notification_stats_view(self, request):
        """Return notification statistics as JSON."""
        try:
            # Calculate statistics
            total_notifications = NotificationQueue.objects.count()
            pending_notifications = NotificationQueue.objects.filter(status='PENDING').count()
            sent_notifications = NotificationQueue.objects.filter(status='SENT').count()
            failed_notifications = NotificationQueue.objects.filter(status='FAILED').count()
            
            # Recent activity (last 7 days)
            recent_date = timezone.now() - timedelta(days=7)
            recent_notifications = NotificationQueue.objects.filter(
                created_at__gte=recent_date
            ).count()
            
            stats = {
                'total': total_notifications,
                'pending': pending_notifications,
                'sent': sent_notifications,
                'failed': failed_notifications,
                'recent_week': recent_notifications,
                'success_rate': round((sent_notifications / total_notifications * 100), 1) if total_notifications > 0 else 0
            }
            
            return JsonResponse(stats)
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    # Bulk actions
    def send_selected_notifications(self, request, queryset):
        """Send selected pending notifications."""
        pending_notifications = queryset.filter(status='PENDING')
        sent_count = 0
        failed_count = 0
        
        for notification in pending_notifications:
            try:
                recipients = list(notification.recipients.all())
                success = notification_service.send_immediate_notification(
                    recipients=recipients,
                    subject=notification.subject,
                    message=notification.message,
                    notification_type=notification.notification_type
                )
                
                if success:
                    notification.status = 'SENT'
                    notification.sent_at = timezone.now()
                    sent_count += 1
                else:
                    notification.status = 'FAILED'
                    notification.error_message = 'Bulk send failed'
                    failed_count += 1
                
                notification.delivery_attempts += 1
                notification.save()
                
            except Exception as e:
                notification.status = 'FAILED'
                notification.error_message = str(e)
                notification.delivery_attempts += 1
                notification.save()
                failed_count += 1
        
        if sent_count > 0:
            messages.success(request, f'Successfully sent {sent_count} notifications')
        if failed_count > 0:
            messages.error(request, f'Failed to send {failed_count} notifications')
    
    send_selected_notifications.short_description = "Send selected notifications"
    
    def cancel_selected_notifications(self, request, queryset):
        """Cancel selected pending notifications."""
        pending_notifications = queryset.filter(status='PENDING')
        cancelled_count = pending_notifications.update(status='CANCELLED')
        
        if cancelled_count > 0:
            messages.success(request, f'Cancelled {cancelled_count} notifications')
        else:
            messages.info(request, 'No pending notifications to cancel')
    
    cancel_selected_notifications.short_description = "Cancel selected notifications"