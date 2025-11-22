import React, { useState } from 'react';
import Layout from '../components/common/Layout.tsx';
import UserManagement from '../components/users/UserManagement.tsx';
import WorkflowConfiguration from '../components/workflows/WorkflowConfiguration.tsx';
import PlaceholderManagement from '../components/placeholders/PlaceholderManagement.tsx';
import SystemSettings from '../components/settings/SystemSettings.tsx';
import AuditTrailViewer from '../components/audit/AuditTrailViewer.tsx';

const AdminDashboard: React.FC = () => {
  console.log('📊 AdminDashboard: Component mounted');
  const [activeSection, setActiveSection] = useState<'overview' | 'users' | 'workflows' | 'placeholders' | 'settings' | 'audit'>('overview');

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
      key: 'workflows' as const,
      title: 'Workflow Configuration',
      description: 'Configure document workflows',
      icon: '🔄',
      color: 'bg-purple-500'
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
    }
  ];

  const renderOverview = () => (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-4">Administration Overview</h2>
        <p className="text-gray-600 mb-6">
          Manage users, configure workflows, and monitor system activities from this central admin dashboard.
        </p>
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
                <dd className="text-lg font-medium text-gray-900">4</dd>
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
                <dd className="text-lg font-medium text-gray-900">4</dd>
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
                <dd className="text-lg font-medium text-gray-900">6</dd>
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
                <dd className="text-lg font-medium text-gray-900">6</dd>
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
            {[
              {
                action: 'User account created for newuser@edms.local',
                time: '2 hours ago',
                user: 'admin',
                type: 'user'
              },
              {
                action: 'Workflow configuration updated for Document Review',
                time: '4 hours ago',
                user: 'admin',
                type: 'workflow'
              },
              {
                action: 'System backup completed successfully',
                time: '6 hours ago',
                user: 'System',
                type: 'system'
              },
              {
                action: 'New placeholder created: COMPANY_LOGO',
                time: '8 hours ago',
                user: 'admin',
                type: 'placeholder'
              }
            ].map((activity, index) => (
              <div key={index} className="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg">
                <div className="flex-shrink-0">
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                    activity.type === 'user' ? 'bg-green-100 text-green-600' :
                    activity.type === 'workflow' ? 'bg-purple-100 text-purple-600' :
                    activity.type === 'system' ? 'bg-blue-100 text-blue-600' :
                    'bg-orange-100 text-orange-600'
                  }`}>
                    {activity.type === 'user' ? '👤' :
                     activity.type === 'workflow' ? '🔄' :
                     activity.type === 'system' ? '⚙️' : '🔧'}
                  </div>
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-gray-900">{activity.action}</p>
                  <p className="text-xs text-gray-500">by {activity.user} • {activity.time}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );

  const renderActiveSection = () => {
    switch (activeSection) {
      case 'overview':
        return renderOverview();
      case 'users':
        return <UserManagement />;
      case 'workflows':
        return <WorkflowConfiguration />;
      case 'placeholders':
        return <PlaceholderManagement />;
      case 'settings':
        return <SystemSettings />;
      case 'audit':
        return <AuditTrailViewer />;
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

        {/* Help Information */}
        {activeSection !== 'overview' && (
          <div className="mt-8 bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-blue-400" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <h3 className="text-sm font-medium text-blue-800">
                  Week 20 Implementation Note
                </h3>
                <div className="mt-2 text-sm text-blue-700">
                  <p>
                    These admin interfaces represent the Week 20 deliverables from the development roadmap. 
                    Full functionality will be implemented during backend API integration phase.
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
};

export default AdminDashboard;