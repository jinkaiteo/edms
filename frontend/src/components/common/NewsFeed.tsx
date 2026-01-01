import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../../contexts/AuthContext.tsx';
import apiService from '../../services/api.ts';

interface NewsItem {
  id: string;
  type: 'document' | 'workflow' | 'notification' | 'system' | 'achievement';
  title: string;
  description: string;
  timestamp: string;
  icon: string;
  priority: 'low' | 'normal' | 'high' | 'urgent';
  actionable: boolean;
  actionUrl?: string;
  actionText?: string;
  metadata?: Record<string, any>;
}

interface NewsFeedProps {
  className?: string;
  maxItems?: number;
}

const NewsFeed: React.FC<NewsFeedProps> = ({ className = '', maxItems = 10 }) => {
  const { user } = useAuth();
  const [newsItems, setNewsItems] = useState<NewsItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchNewsItems = useCallback(async () => {
    try {
      setLoading(true);
      
      // Fetch user-specific news from multiple sources
      const [myDocuments, workflows, notifications, systemStatus] = await Promise.allSettled([
        apiService.get('/documents/'),
        apiService.get('/workflows/'),
        apiService.get('/scheduler/notifications/recent/'),
        apiService.get('/scheduler/system-status/health/')
      ]);

      const newsItems: NewsItem[] = [];

      // Process My Documents
      if (myDocuments.status === 'fulfilled') {
        const docs = Array.isArray(myDocuments.value) ? myDocuments.value : [];
        
        // Pending reviews
        const pendingReviews = docs.filter((doc: any) => 
          doc.status === 'PENDING_REVIEW' && doc.reviewer?.id === user?.id
        );
        
        if (pendingReviews.length > 0) {
          newsItems.push({
            id: 'pending-reviews',
            type: 'workflow',
            title: `${pendingReviews.length} Document${pendingReviews.length > 1 ? 's' : ''} Awaiting Your Review`,
            description: `${pendingReviews.map((d: any) => d.document_number).join(', ')}`,
            timestamp: new Date().toISOString(),
            icon: '📋',
            priority: 'high',
            actionable: true,
            actionUrl: '/documents?filter=pending-review',
            actionText: 'Review Documents'
          });
        }

        // Pending approvals
        const pendingApprovals = docs.filter((doc: any) => 
          doc.status === 'PENDING_APPROVAL' && doc.approver?.id === user?.id
        );
        
        if (pendingApprovals.length > 0) {
          newsItems.push({
            id: 'pending-approvals',
            type: 'workflow',
            title: `${pendingApprovals.length} Document${pendingApprovals.length > 1 ? 's' : ''} Awaiting Your Approval`,
            description: `${pendingApprovals.map((d: any) => d.document_number).join(', ')}`,
            timestamp: new Date().toISOString(),
            icon: '✅',
            priority: 'urgent',
            actionable: true,
            actionUrl: '/documents?filter=pending-approval',
            actionText: 'Approve Documents'
          });
        }

        // Recently effective documents
        const recentEffective = docs.filter((doc: any) => {
          if (doc.status !== 'EFFECTIVE' && doc.status !== 'APPROVED_AND_EFFECTIVE') return false;
          const effectiveDate = new Date(doc.effective_date);
          const weekAgo = new Date();
          weekAgo.setDate(weekAgo.getDate() - 7);
          return effectiveDate >= weekAgo;
        });

        if (recentEffective.length > 0) {
          newsItems.push({
            id: 'recent-effective',
            type: 'achievement',
            title: `${recentEffective.length} Document${recentEffective.length > 1 ? 's' : ''} Became Effective`,
            description: `${recentEffective.map((d: any) => d.document_number).join(', ')} ${recentEffective.length > 1 ? 'are' : 'is'} now active`,
            timestamp: recentEffective[0].effective_date,
            icon: '🎯',
            priority: 'normal',
            actionable: false
          });
        }

        // My drafts needing attention
        const myDrafts = docs.filter((doc: any) => 
          doc.status === 'DRAFT' && doc.author?.id === user?.id
        );
        
        if (myDrafts.length > 0) {
          newsItems.push({
            id: 'my-drafts',
            type: 'document',
            title: `${myDrafts.length} Draft Document${myDrafts.length > 1 ? 's' : ''} Ready to Submit`,
            description: 'Complete and submit for review',
            timestamp: new Date().toISOString(),
            icon: '📄',
            priority: 'normal',
            actionable: true,
            actionUrl: '/documents?filter=my-drafts',
            actionText: 'Complete Drafts'
          });
        }
      }

      // Process Workflow Tasks
      if (workflows.status === 'fulfilled') {
        const tasks = Array.isArray(workflows.value) ? workflows.value : [];
        
        // Overdue workflows
        const overdueTasks = tasks.filter((task: any) => {
          if (!task.due_date) return false;
          return new Date(task.due_date) < new Date();
        });
        
        if (overdueTasks.length > 0) {
          newsItems.push({
            id: 'overdue-tasks',
            type: 'workflow',
            title: `${overdueTasks.length} Overdue Task${overdueTasks.length > 1 ? 's' : ''}`,
            description: 'Immediate attention required',
            timestamp: new Date().toISOString(),
            icon: '⚠️',
            priority: 'urgent',
            actionable: true,
            actionUrl: '/my-tasks',
            actionText: 'View Overdue Tasks'
          });
        }
      }

      // Process System Notifications
      if (notifications.status === 'fulfilled') {
        const notifs = notifications.value.slice(0, 3); // Top 3 recent notifications
        
        notifs.forEach((notif: any, index: number) => {
          newsItems.push({
            id: `notification-${notif.id}`,
            type: 'notification',
            title: notif.subject,
            description: notif.message.substring(0, 100) + (notif.message.length > 100 ? '...' : ''),
            timestamp: notif.created_at,
            icon: '🔔',
            priority: notif.priority?.toLowerCase() || 'normal',
            actionable: false
          });
        });
      }

      // Process System Status
      if (systemStatus.status === 'fulfilled') {
        const status = systemStatus.value;
        
        if (status.overall_status === 'HEALTHY') {
          newsItems.push({
            id: 'system-healthy',
            type: 'system',
            title: 'System Operating Normally',
            description: `All components healthy • ${status.system_statistics?.scheduler?.active_tasks || 0} active automation tasks`,
            timestamp: status.timestamp,
            icon: '✅',
            priority: 'low',
            actionable: false
          });
        } else {
          newsItems.push({
            id: 'system-warning',
            type: 'system',
            title: 'System Health Warning',
            description: status.recommendations?.join(', ') || 'System requires attention',
            timestamp: status.timestamp,
            icon: '⚠️',
            priority: 'high',
            actionable: true,
            actionUrl: '/admin/scheduler/scheduledtask/dashboard/',
            actionText: 'Check System Status'
          });
        }
      }

      // Add motivational content if no urgent items
      const hasUrgentItems = newsItems.some(item => item.priority === 'urgent');
      if (!hasUrgentItems && newsItems.length < 3) {
        newsItems.push({
          id: 'quick-action',
          type: 'system',
          title: 'Ready to Create a New Document?',
          description: 'Start your next document with our streamlined creation process',
          timestamp: new Date().toISOString(),
          icon: '➕',
          priority: 'normal',
          actionable: true,
          actionUrl: '/documents/create',
          actionText: 'Create Document'
        });
      }

      // Sort by priority and timestamp
      const priorityOrder = { urgent: 0, high: 1, normal: 2, low: 3 };
      newsItems.sort((a, b) => {
        const priorityDiff = priorityOrder[a.priority] - priorityOrder[b.priority];
        if (priorityDiff !== 0) return priorityDiff;
        return new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime();
      });

      setNewsItems(newsItems.slice(0, maxItems));
      setError(null);
    } catch (err) {
      console.error('Failed to fetch news items:', err);
      setError('Failed to load news feed');
      
      // Fallback to mock data
      setNewsItems([
        {
          id: 'welcome',
          type: 'system',
          title: 'Welcome to EDMS',
          description: 'Your document management system is ready to use',
          timestamp: new Date().toISOString(),
          icon: '👋',
          priority: 'normal',
          actionable: true,
          actionUrl: '/documents',
          actionText: 'View Documents'
        }
      ]);
    } finally {
      setLoading(false);
    }
  }, [user?.id, maxItems]);

  useEffect(() => {
    if (user) {
      fetchNewsItems();
    }
  }, [user, fetchNewsItems]);

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'urgent': return 'text-red-600 border-red-200 bg-red-50';
      case 'high': return 'text-orange-600 border-orange-200 bg-orange-50';
      case 'normal': return 'text-blue-600 border-blue-200 bg-blue-50';
      case 'low': return 'text-gray-600 border-gray-200 bg-gray-50';
      default: return 'text-gray-600 border-gray-200 bg-gray-50';
    }
  };

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffDays = Math.floor(diffHours / 24);

    if (diffDays > 0) {
      return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
    } else if (diffHours > 0) {
      return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
    } else {
      return 'Just now';
    }
  };

  if (loading) {
    return (
      <div className={`space-y-4 ${className}`}>
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
          <div className="h-3 bg-gray-200 rounded w-1/2"></div>
        </div>
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-2/3 mb-2"></div>
          <div className="h-3 bg-gray-200 rounded w-3/4"></div>
        </div>
      </div>
    );
  }

  if (error && newsItems.length === 0) {
    return (
      <div className={`text-center py-8 ${className}`}>
        <div className="text-gray-500">
          <span className="text-2xl mb-2 block">📰</span>
          <p>Unable to load news feed</p>
          <button 
            onClick={fetchNewsItems}
            className="mt-2 text-blue-600 hover:text-blue-800"
          >
            Try again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className={`space-y-4 ${className}`}>
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900">📰 News Feed</h3>
        <button 
          onClick={fetchNewsItems}
          className="text-gray-400 hover:text-gray-600 transition-colors"
          title="Refresh"
        >
          🔄
        </button>
      </div>
      
      <div className="space-y-3">
        {newsItems.length === 0 ? (
          <div className="text-center py-8">
            <div className="text-gray-500">
              <span className="text-3xl mb-3 block">🎉</span>
              <h4 className="font-medium text-gray-900 mb-1">All caught up!</h4>
              <p className="text-sm">No urgent tasks or notifications at the moment.</p>
            </div>
          </div>
        ) : (
          newsItems.map((item) => (
            <div
              key={item.id}
              className={`p-4 rounded-lg border-l-4 ${getPriorityColor(item.priority)} hover:shadow-sm transition-shadow`}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-2 mb-1">
                    <span className="text-lg">{item.icon}</span>
                    <h4 className="font-medium text-gray-900 text-sm">
                      {item.title}
                    </h4>
                    {item.priority === 'urgent' && (
                      <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-red-100 text-red-800">
                        URGENT
                      </span>
                    )}
                  </div>
                  <p className="text-gray-700 text-sm mb-2">{item.description}</p>
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-gray-500">
                      {formatTimestamp(item.timestamp)}
                    </span>
                    {item.actionable && (
                      <a
                        href={item.actionUrl}
                        className="text-xs text-blue-600 hover:text-blue-800 font-medium"
                      >
                        {item.actionText} →
                      </a>
                    )}
                  </div>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
      
      {newsItems.length > 0 && (
        <div className="text-center">
          <a
            href="/my-tasks"
            className="text-sm text-blue-600 hover:text-blue-800 font-medium"
          >
            View all tasks and activities →
          </a>
        </div>
      )}
    </div>
  );
};

export default NewsFeed;