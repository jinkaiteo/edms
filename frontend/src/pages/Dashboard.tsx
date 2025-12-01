import React, { useState, useEffect } from 'react';
import { NotificationBell } from '../components/notifications/NotificationBell';

const Dashboard: React.FC = () => {
  const [user, setUser] = useState<any>(null);
  const [stats, setStats] = useState({
    totalDocuments: 0,
    pendingTasks: 0,
    myDocuments: 0,
    systemStatus: 'Operational'
  });

  useEffect(() => {
    // Get user info from localStorage
    const storedUser = localStorage.getItem('user');
    if (storedUser) {
      setUser(JSON.parse(storedUser));
    }

    // Simple stats - can be enhanced later with real API calls
    setStats({
      totalDocuments: 12,
      pendingTasks: 3,
      myDocuments: 5,
      systemStatus: 'Operational'
    });
  }, []);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div className="flex items-center">
              <h1 className="text-3xl font-bold text-gray-900">EDMS Dashboard</h1>
            </div>
            <div className="flex items-center space-x-4">
              <NotificationBell />
              <div className="text-sm text-gray-700">
                Welcome, {user?.username || 'User'}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          {/* Stats Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
            <div className="bg-white overflow-hidden shadow rounded-lg">
              <div className="p-5">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <svg className="h-6 w-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                  </div>
                  <div className="ml-5 w-0 flex-1">
                    <dl>
                      <dt className="text-sm font-medium text-gray-500 truncate">Total Documents</dt>
                      <dd className="text-lg font-medium text-gray-900">{stats.totalDocuments}</dd>
                    </dl>
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-white overflow-hidden shadow rounded-lg">
              <div className="p-5">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <svg className="h-6 w-6 text-yellow-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                  <div className="ml-5 w-0 flex-1">
                    <dl>
                      <dt className="text-sm font-medium text-gray-500 truncate">Pending Tasks</dt>
                      <dd className="text-lg font-medium text-gray-900">{stats.pendingTasks}</dd>
                    </dl>
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-white overflow-hidden shadow rounded-lg">
              <div className="p-5">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <svg className="h-6 w-6 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                    </svg>
                  </div>
                  <div className="ml-5 w-0 flex-1">
                    <dl>
                      <dt className="text-sm font-medium text-gray-500 truncate">My Documents</dt>
                      <dd className="text-lg font-medium text-gray-900">{stats.myDocuments}</dd>
                    </dl>
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-white overflow-hidden shadow rounded-lg">
              <div className="p-5">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <svg className="h-6 w-6 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                  <div className="ml-5 w-0 flex-1">
                    <dl>
                      <dt className="text-sm font-medium text-gray-500 truncate">System Status</dt>
                      <dd className="text-lg font-medium text-gray-900">{stats.systemStatus}</dd>
                    </dl>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Quick Actions */}
          <div className="bg-white shadow rounded-lg">
            <div className="px-4 py-5 sm:p-6">
              <h3 className="text-lg leading-6 font-medium text-gray-900">Quick Actions</h3>
              <div className="mt-5 grid grid-cols-1 md:grid-cols-3 gap-4">
                <button
                  onClick={() => window.location.href = '/documents'}
                  className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700"
                >
                  View Documents
                </button>
                <button
                  onClick={() => window.location.href = '/my-tasks'}
                  className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-green-600 hover:bg-green-700"
                >
                  My Tasks
                </button>
                <button
                  onClick={() => window.location.href = '/notifications'}
                  className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-yellow-600 hover:bg-yellow-700"
                >
                  Notifications
                </button>
              </div>
            </div>
          </div>

          {/* System Status */}
          <div className="mt-6 bg-white shadow rounded-lg">
            <div className="px-4 py-5 sm:p-6">
              <h3 className="text-lg leading-6 font-medium text-gray-900">System Information</h3>
              <div className="mt-5">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <div className="w-3 h-3 bg-green-400 rounded-full"></div>
                  </div>
                  <div className="ml-3">
                    <p className="text-sm text-gray-900">
                      ✅ Simplified notification system operational
                    </p>
                  </div>
                </div>
                <div className="mt-2 flex items-center">
                  <div className="flex-shrink-0">
                    <div className="w-3 h-3 bg-green-400 rounded-full"></div>
                  </div>
                  <div className="ml-3">
                    <p className="text-sm text-gray-900">
                      🔔 Task notifications working via My Tasks page
                    </p>
                  </div>
                </div>
                <div className="mt-2 flex items-center">
                  <div className="flex-shrink-0">
                    <div className="w-3 h-3 bg-green-400 rounded-full"></div>
                  </div>
                  <div className="ml-3">
                    <p className="text-sm text-gray-900">
                      📧 Email integration ready for future implementation
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
