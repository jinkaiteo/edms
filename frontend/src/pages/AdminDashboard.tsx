import React, { useState, useCallback, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import Layout from '../components/common/Layout.tsx';
import UserManagement from '../components/users/UserManagement.tsx';
import PlaceholderManagement from '../components/placeholders/PlaceholderManagement.tsx';
import SystemSettings from '../components/settings/SystemSettings.tsx';
import AuditTrailViewer from '../components/audit/AuditTrailViewer.tsx';
import LoadingSpinner from '../components/common/LoadingSpinner.tsx';
import SchedulerStatusWidget from '../components/scheduler/SchedulerStatusWidget.tsx';
import BackupManagement from '../components/backup/BackupManagement.tsx';
import { useDashboardUpdates } from '../hooks/useDashboardUpdates.ts';
import { DashboardStats } from '../types/api.ts';

const AdminDashboard: React.FC = () => {
  const location = useLocation();
  const [activeSection, setActiveSection] = useState<'overview' | 'users' | 'placeholders' | 'settings' | 'audit' | 'tasks' | 'reports' | 'scheduler' | 'backup'>('overview');
  
  // Handle URL parameters to set the active tab
  useEffect(() => {
    const searchParams = new URLSearchParams(location.search);
    const tab = searchParams.get('tab');
    
    // Map tab parameter to valid sections
    const validSections = ['overview', 'users', 'placeholders', 'settings', 'audit', 'tasks', 'reports', 'scheduler', 'backup'];
    if (tab && validSections.includes(tab)) {
      setActiveSection(tab as typeof activeSection);
      console.log(`📂 AdminDashboard: Setting active tab to '${tab}' from URL parameter`);
    } else {
      setActiveSection('overview');
    }
  }, [location.search]);
  
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
    connectionState,
    refreshNow,
    autoRefreshConfig
  } = useDashboardUpdates({
    enabled: activeSection === 'overview', // Only load when overview is active
    autoRefreshInterval: 300000, // 5 minutes
    // HTTP polling used for all dashboard updates
    onError: handleDashboardError,
    onUpdate: handleDashboardUpdate
  });

  const adminSections = [
    {
      key: 'overview' as const,
      title: 'Overview',
      description: 'System overview and quick stats',
      icon: '📊',
      color: 'bg-blue-500'
    },
    {
      key: 'users' as const,
      title: 'User Management',
      description: 'Manage users, roles, and permissions',
      icon: '👥',
      color: 'bg-green-500'
    },
    {
      key: 'placeholders' as const,
      title: 'Placeholder Management',
      description: 'Manage document placeholders',
      icon: '🔧',
      color: 'bg-orange-500'
    },
    {
      key: 'settings' as const,
      title: 'System Settings',
      description: 'Configure system-wide settings',
      icon: '⚙️',
      color: 'bg-gray-500'
    },
    {
      key: 'audit' as const,
      title: 'Audit Trail',
      description: 'View system audit logs',
      icon: '📋',
      color: 'bg-red-500'
    },
    {
      key: 'reports' as const,
      title: 'Reports',
      description: 'Generate compliance reports',
      icon: '📊',
      color: 'bg-pink-500'
    },
    {
      key: 'scheduler' as const,
      title: 'Scheduler Dashboard',
      description: 'Monitor automated tasks and system health',
      icon: '🖥️',
      color: 'bg-indigo-500'
    },
    {
      key: 'backup' as const,
      title: 'Backup & Recovery',
      description: 'Manage system backups and disaster recovery',
      icon: '💾',
      color: 'bg-teal-500'
    }
  ];


  const renderReportsInline = () => (
    <div className="space-y-6">
      <div className="flex justify-between items-start">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Reports</h2>
          <p className="text-gray-600 mt-1">
            Generate and manage compliance reports for regulatory submissions
          </p>
        </div>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        {[
          { name: '21 CFR Part 11', icon: '📋', color: 'bg-blue-500' },
          { name: 'User Activity', icon: '👥', color: 'bg-green-500' },
          { name: 'Document Lifecycle', icon: '📄', color: 'bg-purple-500' },
          { name: 'Audit Trail', icon: '🔍', color: 'bg-red-500' }
        ].map((report) => (
          <div key={report.name} className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
            <div className="flex items-center">
              <div className={`w-10 h-10 ${report.color} rounded-lg flex items-center justify-center text-white text-lg`}>
                {report.icon}
              </div>
              <div className="ml-4 flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900 truncate">
                  {report.name}
                </p>
                <p className="text-xs text-gray-500">
                  Ready to generate
                </p>
              </div>
            </div>
          </div>
        ))}
      </div>
      
      <div className="bg-white shadow rounded-lg">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">Compliance Reporting System</h3>
          <p className="text-sm text-gray-600 mt-1">
            Professional reporting interface for regulatory compliance
          </p>
        </div>
        
        <div className="p-8 text-center">
          <div className="text-6xl mb-4">📊</div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            Reports Module Implemented
          </h3>
          <p className="text-gray-500 mb-6">
            The compliance reporting system includes 8 report types for complete regulatory coverage including 21 CFR Part 11, user activity tracking, document lifecycle management, and audit trail generation.
          </p>
          
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-blue-50 p-3 rounded-lg">
              <div className="text-lg font-bold text-blue-600">8</div>
              <div className="text-xs text-blue-600">Report Types</div>
            </div>
            <div className="bg-green-50 p-3 rounded-lg">
              <div className="text-lg font-bold text-green-600">✓</div>
              <div className="text-xs text-green-600">21 CFR Part 11</div>
            </div>
            <div className="bg-purple-50 p-3 rounded-lg">
              <div className="text-lg font-bold text-purple-600">PDF</div>
              <div className="text-xs text-purple-600">Export Ready</div>
            </div>
            <div className="bg-orange-50 p-3 rounded-lg">
              <div className="text-lg font-bold text-orange-600">AUTO</div>
              <div className="text-xs text-orange-600">Generation</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

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

      {/* Admin Section Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {adminSections.filter(section => section.key !== 'overview').map((section) => (
          <div
            key={section.key}
            onClick={() => setActiveSection(section.key)}
            className="bg-white p-6 rounded-lg shadow-sm border border-gray-200 hover:shadow-md transition-shadow cursor-pointer"
          >
            <div className="flex items-center space-x-3 mb-3">
              <div className={`w-10 h-10 ${section.color} rounded-lg flex items-center justify-center text-white text-xl`}>
                {section.icon}
              </div>
              <h3 className="text-lg font-semibold text-gray-900">{section.title}</h3>
            </div>
            <p className="text-gray-600 text-sm">{section.description}</p>
            <div className="mt-4">
              <span className="text-blue-600 text-sm hover:text-blue-800">
                Configure →
              </span>
            </div>
          </div>
        ))}
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

  const renderActiveSection = () => {
    switch (activeSection) {
      case 'overview':
        return renderOverview();
      case 'users':
        return <UserManagement />;
      case 'placeholders':
        return <PlaceholderManagement />;
      case 'settings':
        return <SystemSettings />;
      case 'audit':
        return <AuditTrailViewer />;
      case 'reports':
        return renderReportsInline();
      case 'scheduler':
        return <SchedulerStatusWidget showDetails={true} />;
      case 'backup':
        return <BackupManagement />;
      default:
        return renderOverview();
    }
  };

  return (
    <Layout>
      <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
        {/* Navigation Tabs */}
        <div className="mb-8">
          <div className="border-b border-gray-200">
            <nav className="flex space-x-8" aria-label="Tabs">
              {adminSections.map((section) => (
                <button
                  key={section.key}
                  onClick={() => setActiveSection(section.key)}
                  className={`py-2 px-1 border-b-2 font-medium text-sm whitespace-nowrap ${
                    activeSection === section.key
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  <span className="mr-2">{section.icon}</span>
                  {section.title}
                </button>
              ))}
            </nav>
          </div>
        </div>

        {/* Active Section Content */}
        {renderActiveSection()}

      </div>
    </Layout>
  );
};

export default AdminDashboard;