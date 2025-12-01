import React from 'react';
import { useTaskNotifications } from '../hooks/useTaskNotifications';

/**
 * Simplified Notifications page using HTTP polling
 * No WebSocket dependency - simple and reliable
 */
const Notifications: React.FC = () => {
  const { tasks, taskCount, loading, error, refreshTasks } = useTaskNotifications();

  return (
    <div className="container mx-auto px-4 py-6">
      <div className="bg-white rounded-lg shadow-md">
        <div className="p-6 border-b border-gray-200">
          <div className="flex justify-between items-center">
            <h1 className="text-2xl font-bold text-gray-800">
              My Notifications ({taskCount})
            </h1>
            <button
              onClick={refreshTasks}
              disabled={loading}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
            >
              {loading ? 'Refreshing...' : 'Refresh'}
            </button>
          </div>
          <p className="text-sm text-gray-600 mt-2">
            🔄 Auto-refreshes every 30 seconds via HTTP polling
          </p>
        </div>

        <div className="p-6">
          {error && (
            <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-md">
              <p className="text-red-600">Error: {error}</p>
            </div>
          )}

          {tasks.length === 0 ? (
            <div className="text-center py-8">
              <div className="text-gray-400 mb-4">
                <svg className="mx-auto h-12 w-12" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
                </svg>
              </div>
              <h3 className="text-lg font-medium text-gray-500">No pending notifications</h3>
              <p className="text-gray-400">You're all caught up!</p>
            </div>
          ) : (
            <div className="space-y-4">
              {tasks.map((task, index) => (
                <div key={task.id || index} className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <h3 className="text-lg font-medium text-gray-800">
                        {task.task_type || 'Task'}
                      </h3>
                      <p className="text-gray-600 mt-1">
                        {task.name || 'No description available'}
                      </p>
                      <div className="flex items-center mt-2 text-sm text-gray-500">
                        <span>Created: {task.created_at ? new Date(task.created_at).toLocaleDateString() : 'Unknown'}</span>
                        <span className="mx-2">•</span>
                        <span className="px-2 py-1 bg-yellow-100 text-yellow-800 rounded-md text-xs">
                          Pending
                        </span>
                      </div>
                    </div>
                    <button className="ml-4 px-3 py-1 bg-blue-600 text-white text-sm rounded-md hover:bg-blue-700">
                      View Task
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Notifications;
