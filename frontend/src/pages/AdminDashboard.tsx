import React, { useState, useCallback, useEffect } from 'react';
import { useLocation, Link } from 'react-router-dom';
import Layout from '../components/common/Layout.tsx';
import UserManagement from '../components/users/UserManagement.tsx';
import PlaceholderManagement from '../components/placeholders/PlaceholderManagement.tsx';
import SystemSettings from '../components/settings/SystemSettings.tsx';
import AuditTrailViewer from '../components/audit/AuditTrailViewer.tsx';
import Reports from '../components/reports/Reports.tsx';
import LoadingSpinner from '../components/common/LoadingSpinner.tsx';
import TaskListWidget from '../components/scheduler/TaskListWidget.tsx';
// BackupManagement removed - backups now managed via CLI (see QUICK_START_BACKUP_RESTORE.md)
import { useDashboardUpdates } from '../hooks/useDashboardUpdates.ts';
import { useSystemInfo } from '../hooks/useSystemInfo.ts';
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
  
  // Use system info hook for version information
  const { systemInfo } = useSystemInfo();

  // Quick links to admin sections
  const adminQuickLinks = [
    { name: 'User Management', href: '/administration?tab=users', icon: '👥', description: 'Manage users, roles, and permissions', external: false },
    { name: 'Placeholder Management', href: '/administration?tab=placeholders', icon: '🔧', description: 'Manage document placeholders', external: false },
    { name: 'Backup Management', href: '/administration?tab=backup', icon: '💾', description: 'Manage system backups and restore', external: false },
    { name: 'Email Notifications', href: '/administration?tab=notifications', icon: '📧', description: 'Configure email notifications', external: false },
    { name: 'Reports', href: '/administration?tab=reports', icon: '📊', description: 'Generate compliance reports', external: false },
    { name: 'Scheduler Dashboard', href: '/administration?tab=scheduler', icon: '🖥️', description: 'Monitor automated tasks', external: false },
    { name: 'Audit Trail', href: '/administration?tab=audit', icon: '📋', description: 'View system audit logs', external: false },
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
        <h2 className="text-2xl font-bold text-gray-900 mb-6">Administration Overview</h2>
        
        {/* System Information Section */}
        <div className="bg-white shadow rounded-lg p-6 mb-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
            <svg className="h-5 w-5 mr-2 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            System Information
          </h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {/* Version & Build Info */}
            <div className="space-y-3">
              <div className="flex items-start">
                <div className="flex-shrink-0">
                  <div className="h-8 w-8 rounded-lg bg-blue-100 flex items-center justify-center">
                    <svg className="h-5 w-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
                    </svg>
                  </div>
                </div>
                <div className="ml-3 flex-1">
                  <dt className="text-sm font-medium text-gray-500">Application Version</dt>
                  <dd className="text-lg font-semibold text-gray-900">v{systemInfo?.application.version || '1.3.3'}</dd>
                  <dd className="text-xs text-gray-500">Released: {systemInfo?.application.build_date || '2026-02-08'}</dd>
                </div>
              </div>
            </div>

            {/* Environment */}
            <div className="space-y-3">
              <div className="flex items-start">
                <div className="flex-shrink-0">
                  <div className="h-8 w-8 rounded-lg bg-green-100 flex items-center justify-center">
                    <svg className="h-5 w-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2m-2-4h.01M17 16h.01" />
                    </svg>
                  </div>
                </div>
                <div className="ml-3 flex-1">
                  <dt className="text-sm font-medium text-gray-500">Environment</dt>
                  <dd className="text-lg font-semibold text-gray-900 capitalize">
                    {systemInfo?.application.environment || (process.env.NODE_ENV === 'production' ? 'Production' : 'Development')}
                  </dd>
                  <dd className="text-xs text-gray-500">
                    Backend: {systemInfo?.backend.framework || 'Django'} {systemInfo?.backend.version || '4.2'} | Frontend: React 18
                  </dd>
                </div>
              </div>
            </div>

            {/* Database */}
            <div className="space-y-3">
              <div className="flex items-start">
                <div className="flex-shrink-0">
                  <div className="h-8 w-8 rounded-lg bg-purple-100 flex items-center justify-center">
                    <svg className="h-5 w-5 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4" />
                    </svg>
                  </div>
                </div>
                <div className="ml-3 flex-1">
                  <dt className="text-sm font-medium text-gray-500">Database</dt>
                  <dd className="text-lg font-semibold text-gray-900">
                    {systemInfo?.database.type || 'PostgreSQL'} {systemInfo?.database.version ? `(${systemInfo.database.version})` : ''}
                  </dd>
                  <dd className="text-xs text-gray-500">
                    Status: {systemInfo?.database.status ? systemInfo.database.status.charAt(0).toUpperCase() + systemInfo.database.status.slice(1) : 'Connected'}
                  </dd>
                </div>
              </div>
            </div>

            {/* Storage Info */}
            <div className="space-y-3">
              <div className="flex items-start">
                <div className="flex-shrink-0">
                  <div className="h-8 w-8 rounded-lg bg-yellow-100 flex items-center justify-center">
                    <svg className="h-5 w-5 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
                    </svg>
                  </div>
                </div>
                <div className="ml-3 flex-1">
                  <dt className="text-sm font-medium text-gray-500">Document Storage</dt>
                  <dd className="text-lg font-semibold text-gray-900">{dashboardStats.total_documents || 0} Documents</dd>
                  <dd className="text-xs text-gray-500">Active files stored</dd>
                </div>
              </div>
            </div>

            {/* Active Users */}
            <div className="space-y-3">
              <div className="flex items-start">
                <div className="flex-shrink-0">
                  <div className="h-8 w-8 rounded-lg bg-indigo-100 flex items-center justify-center">
                    <svg className="h-5 w-5 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
                    </svg>
                  </div>
                </div>
                <div className="ml-3 flex-1">
                  <dt className="text-sm font-medium text-gray-500">Total Users</dt>
                  <dd className="text-lg font-semibold text-gray-900">{dashboardStats.active_users || 0} Users</dd>
                  <dd className="text-xs text-gray-500">Registered accounts</dd>
                </div>
              </div>
            </div>

            {/* Compliance Info */}
            <div className="space-y-3">
              <div className="flex items-start">
                <div className="flex-shrink-0">
                  <div className="h-8 w-8 rounded-lg bg-red-100 flex items-center justify-center">
                    <svg className="h-5 w-5 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                    </svg>
                  </div>
                </div>
                <div className="ml-3 flex-1">
                  <dt className="text-sm font-medium text-gray-500">Compliance</dt>
                  <dd className="text-lg font-semibold text-gray-900">21 CFR Part 11</dd>
                  <dd className="text-xs text-gray-500">FDA Compliant</dd>
                </div>
              </div>
            </div>
          </div>

          {/* Additional Info Bar */}
          <div className="mt-6 pt-6 border-t border-gray-200">
            <div className="flex flex-wrap items-center justify-between gap-4 text-sm">
              <div className="flex items-center text-gray-600">
                <svg className="h-4 w-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span>Server Time: {new Date().toLocaleString()}</span>
              </div>
              <div className="flex items-center text-gray-600">
                <svg className="h-4 w-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span className={`font-medium ${
                  dashboardStats.stat_cards?.system_health === 'healthy' 
                    ? 'text-green-600' 
                    : dashboardStats.stat_cards?.system_health === 'degraded'
                    ? 'text-yellow-600'
                    : 'text-red-600'
                }`}>
                  System Status: {
                    dashboardStats.stat_cards?.system_health === 'healthy' ? 'Operational' : 
                    dashboardStats.stat_cards?.system_health === 'degraded' ? 'Degraded' : 
                    dashboardStats.stat_cards?.system_health ? 'Issues Detected' : 'Checking...'
                  }
                </span>
              </div>
              <div className="text-gray-500">
                © 2024-2026 EDMS. All rights reserved.
              </div>
            </div>
          </div>
        </div>
        
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

      {/* Quick Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
        {/* Card 1: Total Documents */}
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200 hover:shadow-md transition-shadow">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                <span className="text-blue-600 text-2xl">📄</span>
              </div>
            </div>
            <div className="ml-4 flex-1 min-w-0">
              <dt className="text-sm font-medium text-gray-500">Total Documents</dt>
              <dd className="text-2xl font-bold text-gray-900 mt-1">
                {dashboardStats.stat_cards?.total_documents ?? 0}
              </dd>
            </div>
          </div>
        </div>

        {/* Card 2: Documents Needing Action */}
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200 hover:shadow-md transition-shadow">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="w-12 h-12 bg-orange-100 rounded-lg flex items-center justify-center">
                <span className="text-orange-600 text-2xl">✅</span>
              </div>
            </div>
            <div className="ml-4 flex-1 min-w-0">
              <dt className="text-sm font-medium text-gray-500">Pending Actions</dt>
              <dd className="text-2xl font-bold text-gray-900 mt-1">
                {dashboardStats.stat_cards?.documents_needing_action ?? 0}
              </dd>
            </div>
          </div>
        </div>

        {/* Card 3: Active Users (24h) */}
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200 hover:shadow-md transition-shadow">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
                <span className="text-green-600 text-2xl">👥</span>
              </div>
            </div>
            <div className="ml-4 flex-1 min-w-0">
              <dt className="text-sm font-medium text-gray-500">Active Users (24h)</dt>
              <dd className="text-2xl font-bold text-gray-900 mt-1">
                {dashboardStats.stat_cards?.active_users_24h ?? 0}
              </dd>
            </div>
          </div>
        </div>

        {/* Card 4: System Health */}
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200 hover:shadow-md transition-shadow">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className={`w-12 h-12 rounded-lg flex items-center justify-center ${
                dashboardStats.stat_cards?.system_health === 'healthy' 
                  ? 'bg-green-100' 
                  : dashboardStats.stat_cards?.system_health === 'degraded'
                  ? 'bg-yellow-100'
                  : 'bg-red-100'
              }`}>
                <span className={`text-2xl ${
                  dashboardStats.stat_cards?.system_health === 'healthy'
                    ? 'text-green-600'
                    : dashboardStats.stat_cards?.system_health === 'degraded'
                    ? 'text-yellow-600'
                    : 'text-red-600'
                }`}>
                  {dashboardStats.stat_cards?.system_health === 'healthy' ? '⚡' : 
                   dashboardStats.stat_cards?.system_health === 'degraded' ? '⚠️' : '❌'}
                </span>
              </div>
            </div>
            <div className="ml-4 flex-1 min-w-0">
              <dt className="text-sm font-medium text-gray-500">System Health</dt>
              <dd className={`text-2xl font-bold mt-1 ${
                dashboardStats.stat_cards?.system_health === 'healthy'
                  ? 'text-green-600'
                  : dashboardStats.stat_cards?.system_health === 'degraded'
                  ? 'text-yellow-600'
                  : 'text-red-600'
              }`}>
                {dashboardStats.stat_cards?.system_health === 'healthy' ? 'Healthy' : 
                 dashboardStats.stat_cards?.system_health === 'degraded' ? 'Degraded' : 
                 dashboardStats.stat_cards?.system_health ? 'Issues' : 'Loading...'}
              </dd>
            </div>
          </div>
        </div>
      </div>

      {/* System Status Dashboard */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Scheduler Status Widget */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          <div className="p-4 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900 flex items-center">
              <span className="mr-2">🖥️</span>
              Scheduler & Backup Status
            </h3>
          </div>
          <div className="p-4">
            <TaskListWidget />
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
                link.external ? (
                  <a
                    key={link.name}
                    href={link.href}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center justify-between p-4 bg-gray-50 hover:bg-blue-50 rounded-lg transition-colors border border-gray-200 hover:border-blue-300"
                  >
                    <div className="flex items-center">
                      <span className="text-2xl mr-3">{link.icon}</span>
                      <div className="text-left">
                        <div className="font-medium text-gray-900">{link.name}</div>
                        <div className="text-sm text-gray-500">{link.description}</div>
                      </div>
                    </div>
                    <span className="text-gray-400">↗</span>
                  </a>
                ) : (
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
                )
              ))}
            </div>
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
      case 'scheduler':
        return (
          <div className="bg-white shadow rounded-lg p-6">
            <h2 className="text-2xl font-semibold text-gray-900 mb-6 flex items-center">
              <span className="mr-2">🖥️</span>
              Scheduler Dashboard
            </h2>
            <TaskListWidget />
          </div>
        );
      case 'backup':
        // Backup management now handled via CLI - show instructions
        return (
          <div className="bg-white shadow rounded-lg p-6">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">💾 Backup Management</h2>
            <div className="bg-blue-50 border-l-4 border-blue-400 p-4 mb-4">
              <div className="flex">
                <div className="flex-shrink-0">
                  <svg className="h-5 w-5 text-blue-400" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                  </svg>
                </div>
                <div className="ml-3">
                  <p className="text-sm text-blue-700">
                    <strong>System backups are now managed via command line</strong> for better performance and reliability.
                  </p>
                </div>
              </div>
            </div>
            
            <div className="space-y-4">
              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-2">📅 Automated Backups (Active)</h3>
                <ul className="list-disc list-inside text-gray-700 space-y-1">
                  <li><strong>Daily:</strong> 2:00 AM every day</li>
                  <li><strong>Weekly:</strong> 3:00 AM every Sunday</li>
                  <li><strong>Monthly:</strong> 4:00 AM on the 1st of each month</li>
                </ul>
              </div>
              
              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-2">⚡ Manual Operations</h3>
                <div className="bg-gray-50 rounded p-4 font-mono text-sm">
                  <p className="text-gray-600 mb-2"># Create backup (1 second):</p>
                  <p className="text-gray-900">./scripts/backup-hybrid.sh</p>
                  
                  <p className="text-gray-600 mt-4 mb-2"># Restore from backup (9 seconds):</p>
                  <p className="text-gray-900">./scripts/restore-hybrid.sh backups/backup_YYYYMMDD_HHMMSS.tar.gz</p>
                  
                  <p className="text-gray-600 mt-4 mb-2"># View backup logs:</p>
                  <p className="text-gray-900">tail -f logs/backup.log</p>
                  
                  <p className="text-gray-600 mt-4 mb-2"># List backups:</p>
                  <p className="text-gray-900">ls -lh backups/</p>
                </div>
              </div>
              
              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-2">📚 Documentation</h3>
                <ul className="list-disc list-inside text-gray-700 space-y-1">
                  <li><code className="bg-gray-100 px-2 py-1 rounded">QUICK_START_BACKUP_RESTORE.md</code> - 5-minute quickstart</li>
                  <li><code className="bg-gray-100 px-2 py-1 rounded">CRON_BACKUP_SETUP_GUIDE.md</code> - Automation details</li>
                  <li><code className="bg-gray-100 px-2 py-1 rounded">RESTORE_TEST_RESULTS.md</code> - Test verification</li>
                </ul>
              </div>
              
              <div className="bg-green-50 border-l-4 border-green-400 p-4">
                <div className="flex">
                  <div className="flex-shrink-0">
                    <svg className="h-5 w-5 text-green-400" viewBox="0 0 20 20" fill="currentColor">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                    </svg>
                  </div>
                  <div className="ml-3">
                    <p className="text-sm text-green-700">
                      <strong>System Status:</strong> Backups are running automatically. Next backup: Tonight at 2:00 AM
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        );
      case 'reports':
        return <Reports />;
      case 'scheduler':
        return <TaskListWidget />;
      // Emails tab content merged into Settings > Notifications
      case 'emails':
        return (
          <div className="bg-white rounded-lg shadow p-6">
            <div className="text-center py-12">
              <svg className="w-16 h-16 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
              </svg>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">Email Notifications Moved</h3>
              <p className="text-gray-600 mb-6">
                Email notification documentation has been merged into Settings for better organization.
              </p>
              <a 
                href="/administration?tab=notifications"
                className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                Go to Settings → Email Notifications
                <svg className="w-4 h-4 ml-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </a>
            </div>
          </div>
        );

      case 'audit':
        return <AuditTrailViewer />;
      case 'notifications':
        return <SystemSettings />;
      
      // Redirect old 'settings' tab to 'notifications'
      case 'settings':
        window.location.href = '/administration?tab=notifications';
        return <div>Redirecting...</div>;
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