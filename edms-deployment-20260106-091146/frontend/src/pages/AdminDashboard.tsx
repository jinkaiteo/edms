import React, { useState, useCallback, useEffect } from 'react';
import { useLocation, Link } from 'react-router-dom';
import Layout from '../components/common/Layout.tsx';
import UserManagement from '../components/users/UserManagement.tsx';
import PlaceholderManagement from '../components/placeholders/PlaceholderManagement.tsx';
import SystemSettings from '../components/settings/SystemSettings.tsx';
import AuditTrailViewer from '../components/audit/AuditTrailViewer.tsx';
import Reports from '../components/reports/Reports.tsx';
import LoadingSpinner from '../components/common/LoadingSpinner.tsx';
import SchedulerStatusWidget from '../components/scheduler/SchedulerStatusWidget.tsx';
import BackupManagement from '../components/backup/BackupManagement.tsx';
import { useDashboardUpdates } from '../hooks/useDashboardUpdates.ts';
import { DashboardStats } from '../types/api.ts';

const AdminDashboard: React.FC = () => {
  const location = useLocation();
  
  // Get the active tab from URL parameter
  const searchParams = new URLSearchParams(location.search);
  const activeTab = searchParams.get('tab');
  
  // Clear any document selection when entering Administration page
  useEffect(() => {
    console.log('🔄 AdminDashboard: Clearing document selection on administration page entry');
    window.dispatchEvent(new CustomEvent('clearDocumentSelection'));
  }, []);
  
  // Stable callback functions to prevent dependency changes
  const handleDashboardError = useCallback((error: Error) => {
    console.error('Admin dashboard update error:', error);
  }, []);
  
  const handleDashboardUpdate = useCallback((stats: DashboardStats) => {
    // Dashboard update handled by useDashboardUpdates hook
    // No additional action needed here
  }, []);
  
  // Use dashboard updates hook for real-time data
  const {
    dashboardStats,
    isLoading,
    error,
    refreshNow,
    autoRefreshConfig
  } = useDashboardUpdates({
    enabled: true, // Always load dashboard data
    autoRefreshInterval: 300000, // 5 minutes
    // HTTP polling used for all dashboard updates
    onError: handleDashboardError,
    onUpdate: handleDashboardUpdate
  });

  // Quick links to admin sections
  const adminQuickLinks = [
    { name: 'User Management', href: '/admin?tab=users', icon: '👥', description: 'Manage users, roles, and permissions' },
    { name: 'Placeholder Management', href: '/admin?tab=placeholders', icon: '🔧', description: 'Manage document placeholders' },
    { name: 'Backup Management', href: '/admin?tab=backup', icon: '💾', description: 'Manage system backups and disaster recovery' },
    { name: 'Reports', href: '/admin?tab=reports', icon: '📊', description: 'Generate compliance reports' },
    { name: 'Scheduler Dashboard', href: '/admin?tab=scheduler', icon: '🖥️', description: 'Monitor automated tasks' },
    { name: 'Audit Trail', href: '/admin?tab=audit', icon: '📋', description: 'View system audit logs' },
  ];



  const renderOverview = () => {
    if (isLoading) {
      return (
        <div className="flex items-center justify-center py-12">
          <LoadingSpinner />
          <span className="ml-3 text-gray-600">Loading dashboard statistics...</span>
        </div>
      );
    }

    if (error) {
      return (
        <div className="bg-red-50 border border-red-200 rounded-lg p-6">
          <div className="flex items-center">
            <div className="text-red-600 text-xl mr-3">⚠️</div>
            <div>
              <h3 className="text-lg font-medium text-red-800">Error Loading Dashboard</h3>
              <p className="text-red-600 mt-1">{error}</p>
              <button
                onClick={() => refreshNow()}
                className="mt-3 bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700"
                disabled={isLoading}
              >
                {isLoading ? 'Retrying...' : 'Retry'}
              </button>
            </div>
          </div>
        </div>
      );
    }

    if (!dashboardStats) {
      return (
        <div className="text-center py-12">
          <p className="text-gray-500">No dashboard data available.</p>
        </div>
      );
    }

    return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-4">Administration Overview</h2>
        <p className="text-gray-600 mb-6">
          Manage users, configure workflows, and monitor system activities from this central admin dashboard.
        </p>
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-4 text-sm text-gray-500">
            <span>Last updated: {new Date(dashboardStats.timestamp).toLocaleString()}</span>
            
            {/* Auto-refresh status indicator */}
            <div className="flex items-center space-x-1">
              <div className={`w-2 h-2 rounded-full ${
                autoRefreshConfig.isPaused ? 'bg-gray-400' : 
                autoRefreshConfig.isRefreshing ? 'bg-blue-500 animate-pulse' : 'bg-green-500'
              }`}></div>
              <span className="text-xs">
                {autoRefreshConfig.isPaused ? 'Auto-refresh paused' : 
                 autoRefreshConfig.isRefreshing ? 'Refreshing...' : 'Auto-refresh enabled'}
              </span>
            </div>
          </div>
          
          {/* Auto-refresh controls */}
          <div className="flex items-center space-x-2">
            <button
              onClick={autoRefreshConfig.toggle}
              className={`px-3 py-1 rounded text-xs font-medium ${
                autoRefreshConfig.isPaused 
                  ? 'bg-green-100 text-green-700 hover:bg-green-200' 
                  : 'bg-yellow-100 text-yellow-700 hover:bg-yellow-200'
              }`}
              title={autoRefreshConfig.isPaused ? 'Resume auto-refresh' : 'Pause auto-refresh'}
            >
              {autoRefreshConfig.isPaused ? '▶️ Resume' : '⏸️ Pause'}
            </button>
            
            <button
              onClick={() => refreshNow()}
              disabled={isLoading}
              className="px-3 py-1 rounded text-xs font-medium bg-blue-100 text-blue-700 hover:bg-blue-200 disabled:opacity-50"
              title="Refresh now"
            >
              {isLoading ? '⏳ Refreshing...' : '🔄 Refresh'}
            </button>
          </div>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center">
                <span className="text-green-600 text-lg">👥</span>
              </div>
            </div>
            <div className="ml-5 w-0 flex-1">
              <dl>
                <dt className="text-sm font-medium text-gray-500 truncate">Active Users</dt>
                <dd className="text-lg font-medium text-gray-900">{dashboardStats.active_users}</dd>
              </dl>
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="w-8 h-8 bg-purple-100 rounded-full flex items-center justify-center">
                <span className="text-purple-600 text-lg">🔄</span>
              </div>
            </div>
            <div className="ml-5 w-0 flex-1">
              <dl>
                <dt className="text-sm font-medium text-gray-500 truncate">Active Workflows</dt>
                <dd className="text-lg font-medium text-gray-900">{dashboardStats.active_workflows}</dd>
              </dl>
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="w-8 h-8 bg-orange-100 rounded-full flex items-center justify-center">
                <span className="text-orange-600 text-lg">🔧</span>
              </div>
            </div>
            <div className="ml-5 w-0 flex-1">
              <dl>
                <dt className="text-sm font-medium text-gray-500 truncate">Placeholders</dt>
                <dd className="text-lg font-medium text-gray-900">{dashboardStats.placeholders}</dd>
              </dl>
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                <span className="text-blue-600 text-lg">📋</span>
              </div>
            </div>
            <div className="ml-5 w-0 flex-1">
              <dl>
                <dt className="text-sm font-medium text-gray-500 truncate">Audit Entries (24h)</dt>
                <dd className="text-lg font-medium text-gray-900">{dashboardStats.audit_entries_24h}</dd>
              </dl>
            </div>
          </div>
        </div>
      </div>

      {/* System Status Dashboard */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-6">
        {/* Scheduler Status Widget */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          <div className="p-4 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900 flex items-center">
              <span className="mr-2">🖥️</span>
              Scheduler & Backup Status
            </h3>
          </div>
          <div className="p-4">
            <SchedulerStatusWidget detailed={true} />
          </div>
        </div>

        {/* Quick Actions */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          <div className="p-4 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900 flex items-center">
              <span className="mr-2">⚡</span>
              Quick Actions
            </h3>
            <p className="text-sm text-gray-500 mt-1">Access admin tools from the sidebar navigation</p>
          </div>
          <div className="p-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {adminQuickLinks.map((link) => (
                <Link
                  key={link.name}
                  to={link.href}
                  className="flex items-center justify-between p-4 bg-gray-50 hover:bg-blue-50 rounded-lg transition-colors border border-gray-200 hover:border-blue-300"
                >
                  <div className="flex items-center">
                    <span className="text-2xl mr-3">{link.icon}</span>
                    <div className="text-left">
                      <div className="font-medium text-gray-900">{link.name}</div>
                      <div className="text-sm text-gray-500">{link.description}</div>
                    </div>
                  </div>
                  <span className="text-gray-400">→</span>
                </Link>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <div className="p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Admin Activities</h3>
          <div className="space-y-3">
            {dashboardStats.recent_activity.length === 0 ? (
              <div className="flex items-center justify-center p-8 bg-gray-50 rounded-lg">
                <div className="text-center">
                  <div className="w-12 h-12 mx-auto mb-3 bg-gray-200 rounded-full flex items-center justify-center">
                    <span className="text-gray-400 text-xl">📊</span>
                  </div>
                  <p className="text-sm text-gray-500">No recent admin activities</p>
                  <p className="text-xs text-gray-400 mt-1">Activities will appear when administrators perform system changes</p>
                </div>
              </div>
            ) : (
              dashboardStats.recent_activity.map((activity, index) => (
                <div key={activity.id} className="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg">
                  <div className="flex-shrink-0">
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center ${activity.iconColor}`}>
                      <span className="text-white">{activity.icon}</span>
                    </div>
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-gray-900">{activity.title}</p>
                    <p className="text-xs text-gray-500">
                      by {activity.user} • {new Date(activity.timestamp).toLocaleString()}
                    </p>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
    );
  };

  // Render the appropriate component based on the tab parameter
  const renderContent = () => {
    switch (activeTab) {
      case 'users':
        return <UserManagement />;
      case 'placeholders':
        return <PlaceholderManagement />;
      case 'backup':
        return <BackupManagement />;
      case 'reports':
        return <Reports />;
      case 'scheduler':
        return <SchedulerStatusWidget showDetails={true} />;
      case 'audit':
        return <AuditTrailViewer />;
      case 'settings':
        return <SystemSettings />;
      default:
        // No tab parameter = show overview dashboard
        return renderOverview();
    }
  };

  return (
    <Layout>
      <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
        {renderContent()}
      </div>
    </Layout>
  );
};

export default AdminDashboard;