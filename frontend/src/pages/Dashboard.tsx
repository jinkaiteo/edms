import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext.tsx';
import Layout from '../components/common/Layout.tsx';
import LoadingSpinner from '../components/common/LoadingSpinner.tsx';
import { useDashboardUpdates } from '../hooks/useDashboardUpdates.ts';
import { DashboardStats } from '../types/api.ts';
import NewsFeed from '../components/common/NewsFeed.tsx';

const Dashboard: React.FC = () => {
  const { user, authenticated, loading, logout } = useAuth();
  const navigate = useNavigate();
  
  // Helper function to check admin permissions
  const isUserAdmin = useCallback(() => {
    if (!user) return false;
    return user.is_staff || user.is_superuser || 
           user.roles?.some(userRole => userRole.role.permission_level === 'admin');
  }, [user]);
  
  // Stable callback functions to prevent dependency changes
  const handleDashboardError = useCallback((error: Error) => {
    console.error('Dashboard update error:', error);
  }, []);
  
  const handleDashboardUpdate = useCallback((stats: DashboardStats) => {
    // Dashboard update handled by useDashboardUpdates hook
    // No additional action needed here
  }, []);
  
  // Use the new dashboard updates hook with auto-refresh and optional WebSocket
  const {
    dashboardStats: stats,
    isLoading,
    error,
    connectionState,
    refreshNow,
    autoRefreshConfig
  } = useDashboardUpdates({
    enabled: authenticated,
    autoRefreshInterval: 300000, // 5 minutes
    useWebSocket: false, // Start with polling, can enable WebSocket later
    onError: handleDashboardError,
    onUpdate: handleDashboardUpdate
  });

  useEffect(() => {
    
    // Wait for auth loading to complete before making decisions
    if (loading) {
      return;
    }
    
    if (!authenticated) {
      navigate('/login', { replace: true });
      return;
    }
    
  }, [authenticated, loading, navigate, user]);

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const formatRelativeTime = (timestamp: string) => {
    const now = new Date();
    const time = new Date(timestamp);
    const diffInHours = Math.floor((now.getTime() - time.getTime()) / (1000 * 60 * 60));
    
    if (diffInHours === 0) {
      return 'Just now';
    } else if (diffInHours === 1) {
      return '1 hour ago';
    } else if (diffInHours < 24) {
      return `${diffInHours} hours ago`;
    } else {
      const diffInDays = Math.floor(diffInHours / 24);
      return diffInDays === 1 ? '1 day ago' : `${diffInDays} days ago`;
    }
  };

  // Show loading spinner during auth initialization or data loading
  if (loading || isLoading) {
    return (
      <Layout>
        <div className="flex items-center justify-center min-h-screen">
          <LoadingSpinner />
          <span className="ml-3 text-gray-600">
            {loading ? 'Checking authentication...' : 'Loading dashboard...'}
          </span>
        </div>
      </Layout>
    );
  }

  if (error) {
    return (
      <Layout>
        <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
          <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
            <div className="text-red-600 text-xl mb-2">⚠️</div>
            <h3 className="text-lg font-medium text-red-800 mb-2">Error Loading Dashboard</h3>
            <p className="text-red-600 mb-4">{error}</p>
            <button
              onClick={() => refreshNow()}
              className="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700"
              disabled={isLoading}
            >
              {isLoading ? 'Retrying...' : 'Retry'}
            </button>
          </div>
        </div>
      </Layout>
    );
  }

  if (!stats) {
    return (
      <Layout>
        <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <p className="text-gray-500">No dashboard data available.</p>
          </div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <div className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
              <p className="mt-1 text-sm text-gray-500">
                Welcome back, {user?.first_name || user?.username || 'User'}!
              </p>
            </div>
            <div className="flex items-center space-x-4">
              {/* Auto-refresh status and controls */}
              <div className="flex items-center space-x-3 text-sm">
                <div className="flex items-center space-x-1">
                  <div className={`w-2 h-2 rounded-full ${
                    autoRefreshConfig.isPaused ? 'bg-gray-400' : 
                    autoRefreshConfig.isRefreshing ? 'bg-blue-500 animate-pulse' : 'bg-green-500'
                  }`}></div>
                  <span className="text-gray-600">
                    {autoRefreshConfig.isPaused ? 'Paused' : 
                     autoRefreshConfig.isRefreshing ? 'Refreshing...' : 'Auto-refresh'}
                  </span>
                </div>
                
                {autoRefreshConfig.lastRefresh && (
                  <span className="text-gray-500">
                    Updated: {autoRefreshConfig.lastRefresh.toLocaleTimeString()}
                  </span>
                )}
                
                {autoRefreshConfig.nextRefresh && !autoRefreshConfig.isPaused && (
                  <span className="text-gray-400 text-xs">
                    Next: {autoRefreshConfig.nextRefresh.toLocaleTimeString()}
                  </span>
                )}
                
                <div className="flex items-center space-x-1">
                  <button
                    onClick={autoRefreshConfig.toggle}
                    className={`px-2 py-1 rounded text-xs font-medium ${
                      autoRefreshConfig.isPaused 
                        ? 'bg-green-100 text-green-700 hover:bg-green-200' 
                        : 'bg-yellow-100 text-yellow-700 hover:bg-yellow-200'
                    }`}
                    title={autoRefreshConfig.isPaused ? 'Resume auto-refresh' : 'Pause auto-refresh'}
                  >
                    {autoRefreshConfig.isPaused ? '▶️' : '⏸️'}
                  </button>
                  
                  <button
                    onClick={() => refreshNow()}
                    disabled={isLoading}
                    className="px-2 py-1 rounded text-xs font-medium bg-blue-100 text-blue-700 hover:bg-blue-200 disabled:opacity-50"
                    title="Refresh now"
                  >
                    🔄
                  </button>
                </div>
              </div>
              
              <div className="text-sm text-gray-500">
                Last login: {user?.last_login ? new Date(user.last_login).toLocaleDateString() : 'Never'}
              </div>
              <button
                onClick={handleLogout}
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="py-6">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          {/* Stats Overview */}
          <div className="mt-6 grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {/* Total Documents */}
            <div className="bg-white overflow-hidden shadow rounded-lg">
              <div className="p-5">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <div className="w-8 h-8 bg-indigo-500 rounded-md flex items-center justify-center">
                      <span className="text-white text-sm font-medium">📄</span>
                    </div>
                  </div>
                  <div className="ml-5 w-0 flex-1">
                    <dl>
                      <dt className="text-sm font-medium text-gray-500 truncate">Total Documents</dt>
                      <dd className="text-lg font-medium text-gray-900">{stats.total_documents}</dd>
                    </dl>
                  </div>
                </div>
              </div>
              <div className="bg-gray-50 px-5 py-3">
                <div className="text-sm">
                  <a href="#" className="font-medium text-indigo-700 hover:text-indigo-900">
                    View all documents
                  </a>
                </div>
              </div>
            </div>

            {/* Pending Reviews */}
            <div className="bg-white overflow-hidden shadow rounded-lg">
              <div className="p-5">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <div className="w-8 h-8 bg-yellow-500 rounded-md flex items-center justify-center">
                      <span className="text-white text-sm font-medium">⏳</span>
                    </div>
                  </div>
                  <div className="ml-5 w-0 flex-1">
                    <dl>
                      <dt className="text-sm font-medium text-gray-500 truncate">Pending Reviews</dt>
                      <dd className="text-lg font-medium text-gray-900">{stats.pending_reviews}</dd>
                    </dl>
                  </div>
                </div>
              </div>
              <div className="bg-gray-50 px-5 py-3">
                <div className="text-sm">
                  <a href="#" className="font-medium text-yellow-700 hover:text-yellow-900">
                    View pending items
                  </a>
                </div>
              </div>
            </div>

            {/* Active Workflows */}
            <div className="bg-white overflow-hidden shadow rounded-lg">
              <div className="p-5">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <div className="w-8 h-8 bg-green-500 rounded-md flex items-center justify-center">
                      <span className="text-white text-sm font-medium">🔄</span>
                    </div>
                  </div>
                  <div className="ml-5 w-0 flex-1">
                    <dl>
                      <dt className="text-sm font-medium text-gray-500 truncate">Active Workflows</dt>
                      <dd className="text-lg font-medium text-gray-900">{stats.active_workflows}</dd>
                    </dl>
                  </div>
                </div>
              </div>
              <div className="bg-gray-50 px-5 py-3">
                <div className="text-sm">
                  <a href="#" className="font-medium text-green-700 hover:text-green-900">
                    View workflows
                  </a>
                </div>
              </div>
            </div>
          </div>

          {/* Main Content Grid */}
          <div className="mt-8 grid grid-cols-1 gap-6 lg:grid-cols-3">
            {/* Quick Actions */}
            <div className="lg:col-span-1">
              <div className="bg-white shadow rounded-lg">
                <div className="px-4 py-5 sm:p-6">
                  <h3 className="text-lg leading-6 font-medium text-gray-900">Quick Actions</h3>
                  <div className="mt-5 space-y-3">
                    <button className="w-full inline-flex items-center justify-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500">
                      📄 Create Document
                    </button>
                    <button className="w-full inline-flex items-center justify-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500">
                      🔍 Search Documents
                    </button>
                    <button
                      onClick={() => navigate('/my-tasks')}
                      className="w-full inline-flex items-center justify-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                    >
                      ✅ My Tasks
                    </button>
                    {/* View Reports - Admin Only */}
                    {isUserAdmin() && (
                      <button
                        onClick={() => navigate('/reports')}
                        className="w-full inline-flex items-center justify-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                        title="Admin function - View system reports and analytics"
                      >
                        📊 View Reports
                      </button>
                    )}
                  </div>
                </div>
              </div>

              {/* User Profile Card */}
              <div className="mt-6 bg-white shadow rounded-lg">
                <div className="px-4 py-5 sm:p-6">
                  <h3 className="text-lg leading-6 font-medium text-gray-900">Profile</h3>
                  <div className="mt-5">
                    <div className="flex items-center">
                      <div className="flex-shrink-0">
                        <div className="h-12 w-12 rounded-full bg-indigo-100 flex items-center justify-center">
                          <span className="text-indigo-600 font-medium text-lg">
                            {(user?.first_name || user?.username || 'U')[0].toUpperCase()}
                          </span>
                        </div>
                      </div>
                      <div className="ml-4">
                        <div className="text-sm font-medium text-gray-900">
                          {user?.first_name && user?.last_name 
                            ? `${user.first_name} ${user.last_name}`
                            : user?.username || 'Unknown User'
                          }
                        </div>
                        <div className="text-sm text-gray-500">{user?.email}</div>
                        <div className="text-xs text-gray-400">
                          {user?.is_staff && <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800 mr-2">Staff</span>}
                          {user?.is_superuser && <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">Admin</span>}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* News Feed */}
            <div className="lg:col-span-2">
              <div className="bg-white shadow rounded-lg">
                <div className="px-4 py-5 sm:p-6">
                  <h3 className="text-lg leading-6 font-medium text-gray-900">📰 What's New</h3>
                  <p className="text-sm text-gray-500 mt-1">Your personalized activity and task summary</p>
                  <div className="mt-6">
                    <NewsFeed maxItems={6} />
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Compliance Status */}
          <div className="mt-8">
            <div className="bg-white shadow rounded-lg">
              <div className="px-4 py-5 sm:p-6">
                <h3 className="text-lg leading-6 font-medium text-gray-900">Compliance Status</h3>
                <div className="mt-5 grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
                  <div className="text-center">
                    <div className="text-3xl font-bold text-green-600">✓</div>
                    <div className="text-sm text-gray-500">21 CFR Part 11</div>
                    <div className="text-xs text-gray-400">Compliant</div>
                  </div>
                  <div className="text-center">
                    <div className="text-3xl font-bold text-green-600">✓</div>
                    <div className="text-sm text-gray-500">ALCOA Principles</div>
                    <div className="text-xs text-gray-400">Active</div>
                  </div>
                  <div className="text-center">
                    <div className="text-3xl font-bold text-green-600">✓</div>
                    <div className="text-sm text-gray-500">Audit Trail</div>
                    <div className="text-xs text-gray-400">Enabled</div>
                  </div>
                  <div className="text-center">
                    <div className="text-3xl font-bold text-green-600">✓</div>
                    <div className="text-sm text-gray-500">Data Integrity</div>
                    <div className="text-xs text-gray-400">Verified</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      </div>
    </Layout>
  );
};

export default Dashboard;