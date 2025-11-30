/**
 * Notifications Page
 * 
 * Comprehensive view of all user notifications with filtering, pagination,
 * and management capabilities.
 */

import React, { useState, useEffect } from 'react';
import { BellIcon, CheckIcon, TrashIcon, FunnelIcon } from '@heroicons/react/24/outline';
import Layout from '../components/common/Layout.tsx';
import { useNotificationWebSocket } from '../hooks/useNotificationWebSocket.ts';

interface Notification {
  id: string;
  subject: string;
  message: string;
  notification_type: string;
  status: 'SENT' | 'READ' | 'PENDING';
  created_at: string;
  priority: 'LOW' | 'NORMAL' | 'HIGH' | 'URGENT';
  read_at?: string;
}

const Notifications: React.FC = () => {
  const [filter, setFilter] = useState<'all' | 'unread' | 'read'>('all');
  const [typeFilter, setTypeFilter] = useState<string>('all');
  const [selectedNotifications, setSelectedNotifications] = useState<string[]>([]);

  const {
    notifications,
    unreadCount,
    connectionState,
    markAsRead,
    markAllAsRead,
    isRealTime
  } = useNotificationWebSocket({
    enabled: true
  });

  // Filter notifications based on current filters
  const filteredNotifications = notifications.filter(notification => {
    // Status filter
    if (filter === 'unread' && notification.status === 'READ') return false;
    if (filter === 'read' && notification.status !== 'read') return false;
    
    // Type filter
    if (typeFilter !== 'all' && notification.notification_type !== typeFilter) return false;
    
    return true;
  });

  // Get unique notification types for filter dropdown
  const notificationTypes = Array.from(new Set(notifications.map(n => n.notification_type)));

  const formatDateTime = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
  };

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'ASSIGNMENT': return 'bg-blue-100 text-blue-800';
      case 'COMPLETION': return 'bg-green-100 text-green-800';
      case 'WORKFLOW_COMPLETION': return 'bg-green-100 text-green-800';
      case 'TASK_ASSIGNMENT': return 'bg-blue-100 text-blue-800';
      case 'REMINDER': return 'bg-yellow-100 text-yellow-800';
      case 'SYSTEM_ALERT': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'URGENT': return 'text-red-600 font-bold';
      case 'HIGH': return 'text-orange-600 font-medium';
      case 'NORMAL': return 'text-blue-600';
      case 'LOW': return 'text-gray-600';
      default: return 'text-gray-600';
    }
  };

  const getConnectionStatusBadge = () => {
    if (isRealTime && connectionState === 'connected') {
      return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">🟢 Real-time</span>;
    } else if (connectionState === 'connecting') {
      return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">🟡 Connecting</span>;
    } else {
      return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">🔄 Polling</span>;
    }
  };

  const handleSelectAll = () => {
    if (selectedNotifications.length === filteredNotifications.length) {
      setSelectedNotifications([]);
    } else {
      setSelectedNotifications(filteredNotifications.map(n => n.id));
    }
  };

  const handleMarkSelectedAsRead = () => {
    selectedNotifications.forEach(id => markAsRead(id));
    setSelectedNotifications([]);
  };

  return (
    <Layout>
      <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        {/* Page Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <BellIcon className="h-8 w-8 text-gray-700" />
              <div>
                <h1 className="text-3xl font-bold text-gray-900">Notifications</h1>
                <p className="text-sm text-gray-600 mt-1">
                  Manage all your workflow notifications and alerts
                </p>
              </div>
            </div>
            <div className="flex items-center space-x-3">
              {getConnectionStatusBadge()}
              {unreadCount > 0 && (
                <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-red-100 text-red-800">
                  {unreadCount} unread
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Statistics Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <BellIcon className="h-6 w-6 text-gray-400" />
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">Total</dt>
                    <dd className="text-lg font-medium text-gray-900">{notifications.length}</dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className="w-6 h-6 bg-red-500 rounded-full flex items-center justify-center">
                    <span className="text-white text-xs font-bold">{unreadCount}</span>
                  </div>
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">Unread</dt>
                    <dd className="text-lg font-medium text-gray-900">{unreadCount}</dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <CheckIcon className="h-6 w-6 text-green-400" />
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">Read</dt>
                    <dd className="text-lg font-medium text-gray-900">{notifications.length - unreadCount}</dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <FunnelIcon className="h-6 w-6 text-blue-400" />
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">Showing</dt>
                    <dd className="text-lg font-medium text-gray-900">{filteredNotifications.length}</dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Filters and Actions */}
        <div className="bg-white shadow rounded-lg mb-6">
          <div className="px-6 py-4 border-b border-gray-200">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between space-y-4 sm:space-y-0">
              <div className="flex space-x-4">
                {/* Status Filter */}
                <select
                  value={filter}
                  onChange={(e) => setFilter(e.target.value as 'all' | 'unread' | 'read')}
                  className="block px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                >
                  <option value="all">All ({notifications.length})</option>
                  <option value="unread">Unread ({unreadCount})</option>
                  <option value="read">Read ({notifications.length - unreadCount})</option>
                </select>

                {/* Type Filter */}
                <select
                  value={typeFilter}
                  onChange={(e) => setTypeFilter(e.target.value)}
                  className="block px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                >
                  <option value="all">All Types</option>
                  {notificationTypes.map(type => (
                    <option key={type} value={type}>
                      {type.replace('_', ' ').toUpperCase()}
                    </option>
                  ))}
                </select>
              </div>

              <div className="flex space-x-3">
                {selectedNotifications.length > 0 && (
                  <button
                    onClick={handleMarkSelectedAsRead}
                    className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"
                  >
                    <CheckIcon className="h-4 w-4 mr-2" />
                    Mark Selected as Read
                  </button>
                )}

                {unreadCount > 0 && (
                  <button
                    onClick={markAllAsRead}
                    className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                  >
                    <CheckIcon className="h-4 w-4 mr-2" />
                    Mark All as Read
                  </button>
                )}
              </div>
            </div>
          </div>

          {/* Bulk Actions */}
          {filteredNotifications.length > 0 && (
            <div className="px-6 py-3 border-b border-gray-200 bg-gray-50">
              <label className="inline-flex items-center">
                <input
                  type="checkbox"
                  checked={selectedNotifications.length === filteredNotifications.length}
                  onChange={handleSelectAll}
                  className="rounded border-gray-300 text-blue-600 shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200 focus:ring-opacity-50"
                />
                <span className="ml-2 text-sm text-gray-600">
                  Select all ({filteredNotifications.length}) 
                  {selectedNotifications.length > 0 && ` • ${selectedNotifications.length} selected`}
                </span>
              </label>
            </div>
          )}
        </div>

        {/* Notifications List */}
        <div className="bg-white shadow rounded-lg overflow-hidden">
          {filteredNotifications.length === 0 ? (
            <div className="text-center py-12">
              <BellIcon className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-2 text-sm font-medium text-gray-900">No notifications</h3>
              <p className="mt-1 text-sm text-gray-500">
                {filter === 'all' 
                  ? "You don't have any notifications yet." 
                  : `You don't have any ${filter} notifications.`}
              </p>
            </div>
          ) : (
            <div className="divide-y divide-gray-200">
              {filteredNotifications.map((notification) => (
                <div
                  key={notification.id}
                  className={`p-6 hover:bg-gray-50 transition-colors ${
                    notification.status !== 'read' ? 'bg-blue-50 border-l-4 border-l-blue-500' : ''
                  }`}
                >
                  <div className="flex items-start space-x-4">
                    <input
                      type="checkbox"
                      checked={selectedNotifications.includes(notification.id)}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setSelectedNotifications([...selectedNotifications, notification.id]);
                        } else {
                          setSelectedNotifications(selectedNotifications.filter(id => id !== notification.id));
                        }
                      }}
                      className="mt-1 rounded border-gray-300 text-blue-600 shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200 focus:ring-opacity-50"
                    />

                    <div className="flex-1 min-w-0">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center space-x-3 mb-2">
                            <h3 className={`text-lg font-medium ${
                              notification.status !== 'read' ? 'text-gray-900' : 'text-gray-700'
                            }`}>
                              {notification.subject}
                            </h3>
                            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getTypeColor(notification.notification_type)}`}>
                              {notification.notification_type.replace('_', ' ')}
                            </span>
                            <span className={`text-xs ${getPriorityColor(notification.priority)}`}>
                              {notification.priority}
                            </span>
                          </div>
                          
                          <p className="text-sm text-gray-600 mb-3">
                            {notification.message}
                          </p>
                          
                          <div className="flex items-center text-xs text-gray-500 space-x-4">
                            <span>📅 {formatDateTime(notification.created_at)}</span>
                            {notification.read_at && (
                              <span>✅ Read {formatDateTime(notification.read_at)}</span>
                            )}
                          </div>
                        </div>

                        <div className="flex items-center space-x-2 ml-4">
                          {notification.status !== 'READ' ? (
                            <>
                              <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                              <button
                                onClick={() => markAsRead(notification.id)}
                                className="inline-flex items-center px-3 py-1 border border-transparent text-xs font-medium rounded text-blue-700 bg-blue-100 hover:bg-blue-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                              >
                                Mark as read
                              </button>
                            </>
                          ) : (
                            <span className="inline-flex items-center px-3 py-1 text-xs font-medium text-green-700 bg-green-100 rounded">
                              <span className="w-2 h-2 bg-green-500 rounded-full mr-2"></span>
                              Read
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </Layout>
  );
};

export default Notifications;