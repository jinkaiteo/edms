/**
 * Custom hook for real-time notification WebSocket connection
 * 
 * Provides real-time notification updates via WebSocket,
 * with fallback to HTTP polling if WebSocket fails.
 */

import { useEffect, useRef, useState, useCallback } from 'react';
import { useWebSocket } from './useWebSocket.ts';

interface Notification {
  id: string;
  subject: string;
  message: string;
  notification_type: string;
  status: 'SENT' | 'READ' | 'PENDING';
  created_at: string;
  priority: 'LOW' | 'NORMAL' | 'HIGH' | 'URGENT';
}

interface NotificationData {
  notifications: Notification[];
  count: number;
  unread_count: number;
}

interface UseNotificationWebSocketOptions {
  onNotificationUpdate?: (data: NotificationData) => void;
  onNewNotification?: (notification: Notification) => void;
  onUnreadCountChange?: (count: number) => void;
  enabled?: boolean;
}

interface UseNotificationWebSocketReturn {
  notifications: Notification[];
  unreadCount: number;
  connectionState: 'connecting' | 'connected' | 'disconnected' | 'error';
  markAsRead: (notificationId: string) => void;
  markAllAsRead: () => void;
  refreshNotifications: () => void;
  isRealTime: boolean;
}

export const useNotificationWebSocket = ({
  onNotificationUpdate,
  onNewNotification,
  onUnreadCountChange,
  enabled = true
}: UseNotificationWebSocketOptions): UseNotificationWebSocketReturn => {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [isRealTime, setIsRealTime] = useState(false);
  
  // Fallback HTTP polling
  const fallbackIntervalRef = useRef<NodeJS.Timeout | null>(null);
  
  // WebSocket connection
  const {
    connectionState,
    sendMessage,
    lastMessage
  } = useWebSocket({
    url: `ws://localhost:8000/ws/notifications/`,
    enabled,
    shouldReconnect: false, // Disable auto-reconnect to prevent spam
    onOpen: () => {
      console.log('🔔 Notification WebSocket connected');
      setIsRealTime(true);
      
      // Stop HTTP polling fallback
      if (fallbackIntervalRef.current) {
        clearInterval(fallbackIntervalRef.current);
        fallbackIntervalRef.current = null;
      }
      
      // Send authentication token
      const token = localStorage.getItem('accessToken');
      if (token) {
        console.log('🔑 Sending auth token to WebSocket (length:', token.length, ')');
        sendMessage(JSON.stringify({
          type: 'authenticate',
          token: token
        }));
      } else {
        console.warn('⚠️ No access token found in localStorage');
      }
      
      // Request current notifications
      sendMessage(JSON.stringify({
        type: 'request_notifications'
      }));
    },
    onClose: () => {
      console.log('🔌 Notification WebSocket disconnected - falling back to HTTP polling');
      setIsRealTime(false);
      startHttpPolling();
    },
    onError: () => {
      console.warn('⚠️ Notification WebSocket error - falling back to HTTP polling');
      setIsRealTime(false);
      startHttpPolling();
    }
  });
  
  // Handle WebSocket messages
  useEffect(() => {
    if (!lastMessage) return;
    
    try {
      const data = JSON.parse(lastMessage.data);
      
      switch (data.type) {
        case 'auth_success':
          console.log('✅ WebSocket authenticated:', data.message);
          setIsRealTime(true);
          // Request notifications after successful auth
          sendMessage(JSON.stringify({ type: 'request_notifications' }));
          break;
          
        case 'auth_error':
          console.warn('⚠️ WebSocket auth failed:', data.message);
          setIsRealTime(false);
          startHttpPolling(); // Fall back to HTTP
          break;
          
        case 'auth_required':
          console.warn('📝 WebSocket requires authentication - attempting to authenticate');
          // Try to authenticate with current token
          const token = localStorage.getItem('accessToken');
          if (token) {
            sendMessage(JSON.stringify({
              type: 'authenticate',
              token: token
            }));
          } else {
            console.warn('No auth token found - falling back to HTTP');
            setIsRealTime(false);
            startHttpPolling();
          }
          break;
          
        case 'notifications_update':
          handleNotificationsUpdate(data.payload);
          break;
          
        case 'new_notification':
          handleNewNotification(data.payload);
          break;
          
        case 'notification_count':
          const count = data.payload.unread_count;
          setUnreadCount(count);
          onUnreadCountChange?.(count);
          break;
          
        case 'notification_updated':
          // Refresh notifications when any are updated
          refreshNotifications();
          break;
          
        case 'pong':
          // Heartbeat response
          break;
          
        case 'error':
          console.error('WebSocket error:', data.message);
          break;
          
        default:
          console.log('Unknown WebSocket message type:', data.type);
      }
    } catch (error) {
      console.error('Failed to parse WebSocket message:', error);
    }
  }, [lastMessage]);
  
  const handleNotificationsUpdate = useCallback((data: NotificationData) => {
    setNotifications(data.notifications);
    setUnreadCount(data.unread_count);
    onNotificationUpdate?.(data);
    onUnreadCountChange?.(data.unread_count);
  }, [onNotificationUpdate, onUnreadCountChange]);
  
  const handleNewNotification = useCallback((notification: Notification) => {
    console.log('🔔 New notification received:', notification.subject);
    
    // Add to notifications list
    setNotifications(prev => [notification, ...prev]);
    
    // Update unread count
    if (notification.status !== 'READ') {
      setUnreadCount(prev => prev + 1);
      onUnreadCountChange?.(unreadCount + 1);
    }
    
    onNewNotification?.(notification);
    
    // Show browser notification if permission granted
    if ('Notification' in window && Notification.permission === 'granted') {
      new Notification(notification.subject, {
        body: notification.message,
        icon: '/favicon.ico',
        tag: `notification-${notification.id}`,
      });
    }
  }, [onNewNotification, onUnreadCountChange, unreadCount]);
  
  const startHttpPolling = useCallback(() => {
    if (fallbackIntervalRef.current) return; // Already polling
    
    console.log('📡 Starting HTTP notification polling fallback');
    
    const fetchNotifications = async () => {
      try {
        const token = localStorage.getItem('accessToken');
        if (!token) return;
        
        const response = await fetch('/api/v1/notifications/my_notifications/', {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        });
        
        if (response.ok) {
          const data = await response.json();
          handleNotificationsUpdate(data);
        }
      } catch (error) {
        console.error('HTTP polling failed:', error);
      }
    };
    
    // Initial fetch
    fetchNotifications();
    
    // Poll every 30 seconds
    fallbackIntervalRef.current = setInterval(fetchNotifications, 30000);
  }, [handleNotificationsUpdate]);
  
  const markAsRead = useCallback((notificationId: string) => {
    if (connectionState === 'connected') {
      // Use WebSocket
      sendMessage(JSON.stringify({
        type: 'mark_notification_read',
        notification_id: notificationId
      }));
    } else {
      // Use HTTP fallback
      const token = localStorage.getItem('accessToken');
      if (token) {
        fetch(`/api/v1/notifications/${notificationId}/mark_read/`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        }).catch(console.error);
      }
    }
    
    // Update local state immediately for responsive UI
    setNotifications(prev => prev.map(n => 
      n.id === notificationId ? { ...n, status: 'READ' as const } : n
    ));
    setUnreadCount(prev => Math.max(0, prev - 1));
  }, [connectionState, sendMessage]);
  
  const markAllAsRead = useCallback(() => {
    if (connectionState === 'connected') {
      // Use WebSocket
      sendMessage(JSON.stringify({
        type: 'mark_all_read'
      }));
    } else {
      // Use HTTP fallback
      const token = localStorage.getItem('accessToken');
      if (token) {
        fetch('/api/v1/notifications/mark_all_read/', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        }).catch(console.error);
      }
    }
    
    // Update local state immediately
    setNotifications(prev => prev.map(n => ({ ...n, status: 'READ' as const })));
    setUnreadCount(0);
  }, [connectionState, sendMessage]);
  
  const refreshNotifications = useCallback(() => {
    if (connectionState === 'connected') {
      sendMessage(JSON.stringify({
        type: 'request_notifications'
      }));
    } else {
      // Will be handled by HTTP polling
    }
  }, [connectionState, sendMessage]);
  
  // Request browser notification permission
  useEffect(() => {
    if ('Notification' in window && Notification.permission === 'default') {
      Notification.requestPermission().then(permission => {
        console.log('Notification permission:', permission);
      });
    }
  }, []);
  
  // Cleanup
  useEffect(() => {
    return () => {
      if (fallbackIntervalRef.current) {
        clearInterval(fallbackIntervalRef.current);
      }
    };
  }, []);
  
  // Send periodic heartbeat
  useEffect(() => {
    if (connectionState !== 'connected') return;
    
    const heartbeatInterval = setInterval(() => {
      sendMessage(JSON.stringify({ type: 'ping' }));
    }, 60000); // Every minute
    
    return () => clearInterval(heartbeatInterval);
  }, [connectionState, sendMessage]);
  
  return {
    notifications,
    unreadCount,
    connectionState,
    markAsRead,
    markAllAsRead,
    refreshNotifications,
    isRealTime
  };
};