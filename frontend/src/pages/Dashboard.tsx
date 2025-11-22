import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext.tsx';
import LoadingSpinner from '../components/common/LoadingSpinner.tsx';

interface DashboardStats {
  totalDocuments: number;
  pendingReviews: number;
  activeWorkflows: number;
  recentActivity: ActivityItem[];
}

interface ActivityItem {
  id: string;
  type: 'document_created' | 'document_updated' | 'workflow_completed' | 'user_login' | 'document_signed';
  title: string;
  description: string;
  timestamp: string;
  user?: string;
  icon: string;
  iconColor: string;
}

const Dashboard: React.FC = () => {
  const [stats, setStats] = useState<DashboardStats>({
    totalDocuments: 0,
    pendingReviews: 0,
    activeWorkflows: 0,
    recentActivity: []
  });
  const [isLoading, setIsLoading] = useState(true);
  const { user, authenticated, logout } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    console.log('📊 Dashboard mounted - authenticated:', authenticated, 'user:', user?.username);
    
    if (!authenticated) {
      console.log('❌ Not authenticated, redirecting to login...');
      navigate('/login', { replace: true });
      return;
    }
    
    console.log('✅ User authenticated, loading dashboard...');

    // Load dashboard data
    const loadDashboardData = async () => {
      setIsLoading(true);
      
      // Simulate API call delay
      await new Promise(resolve => setTimeout(resolve, 800));
      
      // Mock data for demonstration
      const mockStats: DashboardStats = {
        totalDocuments: 12,
        pendingReviews: 3,
        activeWorkflows: 2,
        recentActivity: [
          {
            id: '1',
            type: 'document_created',
            title: 'Quality Manual v2.1',
            description: 'New quality manual document created',
            timestamp: new Date().toISOString(),
            user: user?.username || 'System',
            icon: '📄',
            iconColor: 'bg-blue-500'
          },
          {
            id: '2',
            type: 'workflow_completed',
            title: 'SOP Review Completed',
            description: 'Standard Operating Procedure #001 review workflow completed',
            timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
            user: 'reviewer',
            icon: '✅',
            iconColor: 'bg-green-500'
          },
          {
            id: '3',
            type: 'document_signed',
            title: 'Policy Document Signed',
            description: 'Company Policy document electronically signed',
            timestamp: new Date(Date.now() - 4 * 60 * 60 * 1000).toISOString(),
            user: 'approver',
            icon: '✍️',
            iconColor: 'bg-purple-500'
          },
          {
            id: '4',
            type: 'user_login',
            title: 'User Login',
            description: 'Successful login to EDMS',
            timestamp: new Date(Date.now() - 6 * 60 * 60 * 1000).toISOString(),
            user: user?.username || 'Unknown',
            icon: '🔐',
            iconColor: 'bg-indigo-500'
          }
        ]
      };
      
      setStats(mockStats);
      setIsLoading(false);
      console.log('✅ Dashboard data loaded successfully');
    };

    loadDashboardData();
  }, [authenticated, navigate, user]);

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

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-100">
        <LoadingSpinner />
      </div>
    );
  }

  return (
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
                      <dd className="text-lg font-medium text-gray-900">{stats.totalDocuments}</dd>
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
                      <dd className="text-lg font-medium text-gray-900">{stats.pendingReviews}</dd>
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
                      <dd className="text-lg font-medium text-gray-900">{stats.activeWorkflows}</dd>
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
                    <button className="w-full inline-flex items-center justify-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500">
                      👥 Manage Users
                    </button>
                    <button className="w-full inline-flex items-center justify-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500">
                      📊 View Reports
                    </button>
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

            {/* Recent Activity */}
            <div className="lg:col-span-2">
              <div className="bg-white shadow rounded-lg">
                <div className="px-4 py-5 sm:p-6">
                  <h3 className="text-lg leading-6 font-medium text-gray-900">Recent Activity</h3>
                  <div className="mt-6 flow-root">
                    <ul className="-my-5 divide-y divide-gray-200">
                      {stats.recentActivity.map((item) => (
                        <li key={item.id} className="py-5">
                          <div className="flex items-center space-x-4">
                            <div className="flex-shrink-0">
                              <div className={`h-8 w-8 rounded-full ${item.iconColor} flex items-center justify-center`}>
                                <span className="text-white text-sm">{item.icon}</span>
                              </div>
                            </div>
                            <div className="flex-1 min-w-0">
                              <p className="text-sm font-medium text-gray-900 truncate">{item.title}</p>
                              <p className="text-sm text-gray-500 truncate">{item.description}</p>
                            </div>
                            <div className="flex-shrink-0 text-sm text-gray-500">
                              {formatRelativeTime(item.timestamp)}
                            </div>
                          </div>
                        </li>
                      ))}
                    </ul>
                  </div>
                  <div className="mt-6">
                    <a
                      href="#"
                      className="w-full flex justify-center items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
                    >
                      View all activity
                    </a>
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
  );
};

export default Dashboard;