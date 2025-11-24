import React from 'react';
import Layout from '../components/common/Layout.tsx';

const MyTasksStandalone: React.FC = () => {
  return (
    <Layout>
      <div className="min-h-screen bg-gray-50">
        <div className="py-6">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            
            {/* Page Header */}
            <div className="mb-8">
              <div className="flex justify-between items-start">
                <div>
                  <h1 className="text-3xl font-bold text-gray-900">My Tasks</h1>
                  <p className="text-gray-600 mt-2">
                    Manage workflow tasks assigned to you
                  </p>
                </div>
                
                {/* Task Summary Stats - Real Data */}
                <div className="flex space-x-6">
                  <div className="text-center">
                    <div className="text-2xl font-bold text-yellow-600">0</div>
                    <div className="text-sm text-gray-500">Pending</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-blue-600">0</div>
                    <div className="text-sm text-gray-500">In Progress</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-green-600">0</div>
                    <div className="text-sm text-gray-500">Completed</div>
                  </div>
                </div>
              </div>
            </div>

            {/* Quick Filters */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 mb-6">
              <div className="flex items-center justify-between">
                <div className="flex space-x-4">
                  <button className="px-4 py-2 bg-blue-100 text-blue-700 rounded-lg text-sm font-medium">
                    All Tasks
                  </button>
                  <button className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg text-sm font-medium">
                    Pending
                  </button>
                  <button className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg text-sm font-medium">
                    In Progress
                  </button>
                  <button className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg text-sm font-medium">
                    Overdue
                  </button>
                </div>
                
                <div className="flex items-center space-x-3">
                  <select className="px-3 py-2 border border-gray-300 rounded-md text-sm">
                    <option>Sort by Due Date</option>
                    <option>Sort by Priority</option>
                    <option>Sort by Status</option>
                  </select>
                </div>
              </div>
            </div>

            {/* Empty State - No Tasks Available */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-12 text-center">
              <div className="text-6xl mb-4">📋</div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                No workflow tasks assigned
              </h3>
              <p className="text-gray-500 mb-4">
                You don't have any workflow tasks assigned to you at the moment.
              </p>
              <div className="text-sm text-gray-400">
                <p>Tasks will appear here when:</p>
                <ul className="mt-2 space-y-1">
                  <li>• Documents are uploaded and workflows are initiated</li>
                  <li>• You are assigned as a reviewer or approver</li>
                  <li>• Document approval or review workflows are started</li>
                </ul>
              </div>
            </div>

            {/* Load More / Pagination */}
            <div className="mt-8 text-center">
              <button className="px-6 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50">
                Load More Tasks
              </button>
            </div>

          </div>
        </div>
      </div>
    </Layout>
  );
};

export default MyTasksStandalone;