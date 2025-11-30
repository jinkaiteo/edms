import React, { useState, useEffect } from 'react';
import { BellIcon } from '@heroicons/react/24/outline';
import { BellIcon as BellIconSolid } from '@heroicons/react/24/solid';
import { useNavigate } from 'react-router-dom';
import { useNotificationWebSocket } from '../../hooks/useNotificationWebSocket.ts';

interface Notification {
  id: string;
  subject: string;
  message: string;
  notification_type: string;
  status: 'SENT' | 'READ' | 'PENDING';
  created_at: string;
  priority: 'LOW' | 'NORMAL' | 'HIGH' | 'URGENT';
}

interface NotificationBellProps {
  className?: string;
}

const NotificationBell: React.FC<NotificationBellProps> = ({ className = '' }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();
  
  // Use WebSocket hook for real-time notifications
  const {
    notifications,
    unreadCount,
    connectionState,
    markAsRead,
    markAllAsRead,
    refreshNotifications,
    isRealTime
  } = useNotificationWebSocket({
    onNewNotification: (notification) => {
      console.log('🔔 New notification:', notification.subject);
      // Could add toast notification here
    },
    onUnreadCountChange: (count) => {
      console.log(`📊 Unread count updated: ${count}`);
    },
    enabled: true
  });

  // Handle connection errors
  useEffect(() => {
    if (connectionState === 'error') {
      setError('WebSocket connection failed - using fallback');
    } else if (connectionState === 'connected') {
      setError(null);
    } else if (connectionState === 'disconnected' && !isRealTime) {
      setError('Using HTTP polling (WebSocket unavailable)');
    }
  }, [connectionState, isRealTime]);



  const formatTimeAgo = (dateString: string) => {
    const now = new Date();
    const date = new Date(dateString);
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / (1000 * 60));
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    return `${diffDays}d ago`;
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'URGENT': return 'text-red-600';
      case 'HIGH': return 'text-orange-600';
      case 'NORMAL': return 'text-blue-600';
      case 'LOW': return 'text-gray-600';
      default: return 'text-gray-600';
    }
  };

  const getNotificationIcon = (type: string) => {
    switch (type) {
      case 'WORKFLOW_COMPLETION': return '✅';
      case 'TASK_ASSIGNMENT': return '📋';
      case 'DOCUMENT_UPDATE': return '📄';
      case 'SYSTEM_ALERT': return '⚠️';
      default: return '📢';
    }
  };

  // Show connection status in header
  const getConnectionStatus = () => {
    if (isRealTime && connectionState === 'connected') {
      return '🟢 Real-time';
    } else if (connectionState === 'connecting') {
      return '🟡 Connecting...';
    } else if (!isRealTime) {
      return '🔄 Polling';
    } else {
      return '🔴 Disconnected';
    }
  };

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as Element;
      if (isOpen && !target.closest('.notification-bell')) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [isOpen]);

  return (
    <div className={`notification-bell relative ${className}`}>
      {/* Bell Icon Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="relative p-2 text-gray-600 hover:text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 rounded-full"
        aria-label={`Notifications ${unreadCount > 0 ? `(${unreadCount} unread)` : ''}`}
      >
        {unreadCount > 0 ? (
          <BellIconSolid className="h-6 w-6 text-blue-600" />
        ) : (
          <BellIcon className="h-6 w-6" />
        )}
        
        {/* Unread Count Badge */}
        {unreadCount > 0 && (
          <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full h-5 w-5 flex items-center justify-center font-medium">
            {unreadCount > 99 ? '99+' : unreadCount}
          </span>
        )}
      </button>

      {/* Notification Dropdown */}
      {isOpen && (
        <div className="absolute right-0 mt-2 w-80 bg-white rounded-lg shadow-lg border border-gray-200 z-50 max-h-96 overflow-hidden">
          {/* Header */}
          <div className="px-4 py-3 border-b border-gray-200 bg-gray-50">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold text-gray-900">
                  📢 Notifications
                </h3>
                {/* Connection status - only show if real-time or connecting */}
                {(isRealTime || connectionState === 'connecting') && (
                  <p className="text-xs text-gray-500">{getConnectionStatus()}</p>
                )}
              </div>
              {unreadCount > 0 && (
                <button
                  onClick={markAllAsRead}
                  className="text-sm text-blue-600 hover:text-blue-800 font-medium"
                >
                  Mark all as read
                </button>
              )}
            </div>
            {unreadCount > 0 && (
              <p className="text-sm text-gray-600 mt-1">
                {unreadCount} unread notification{unreadCount !== 1 ? 's' : ''}
              </p>
            )}
          </div>

          {/* Notifications List */}
          <div className="max-h-80 overflow-y-auto">
            {connectionState === 'connecting' ? (
              <div className="p-4 text-center">
                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600 mx-auto"></div>
                <p className="text-sm text-gray-600 mt-2">Connecting to notifications...</p>
              </div>
            ) : notifications.length === 0 ? (
              <div className="p-6 text-center">
                <BellIcon className="h-12 w-12 text-gray-400 mx-auto mb-2" />
                <p className="text-gray-600">No notifications yet</p>
              </div>
            ) : (
              <div className="divide-y divide-gray-100">
                {notifications.map((notification) => (
                  <div
                    key={notification.id}
                    className={`p-4 hover:bg-gray-50 cursor-pointer transition-colors ${
                      notification.status !== 'read' ? 'bg-blue-50 border-l-4 border-l-blue-500' : ''
                    }`}
                    onClick={() => markAsRead(notification.id)}
                  >
                    <div className="flex items-start space-x-3">
                      <div className="flex-shrink-0 text-lg">
                        {getNotificationIcon(notification.notification_type)}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-start justify-between">
                          <p className={`text-sm font-medium ${notification.status !== 'read' ? 'text-gray-900' : 'text-gray-700'}`}>
                            {notification.subject}
                          </p>
                          <span className={`text-xs ml-2 ${getPriorityColor(notification.priority)}`}>
                            {notification.priority}
                          </span>
                        </div>
                        <p className="text-sm text-gray-600 mt-1 line-clamp-2">
                          {notification.message}
                        </p>
                        <p className="text-xs text-gray-500 mt-2">
                          {formatTimeAgo(notification.created_at)}
                        </p>
                      </div>
                      {notification.status !== 'read' && (
                        <div className="flex-shrink-0">
                          <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="px-4 py-3 border-t border-gray-200 bg-gray-50">
            <button
              onClick={() => {
                setIsOpen(false);
                navigate('/notifications');
              }}
              className="text-sm text-blue-600 hover:text-blue-800 font-medium w-full text-center"
            >
              View all notifications
            </button>
          </div>
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div className="absolute right-0 mt-2 w-80 bg-red-50 border border-red-200 rounded-lg p-3 shadow-lg z-50">
          <p className="text-sm text-red-700">{error}</p>
          <button
            onClick={() => {
              setError(null);
              refreshNotifications();
            }}
            className="text-xs text-red-600 hover:text-red-800 mt-1"
          >
            Try again
          </button>
        </div>
      )}
    </div>
  );
};

export default NotificationBell;