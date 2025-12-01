import React, { useState } from 'react';
import { useTaskNotifications } from '../hooks/useTaskNotifications';

interface NotificationBellProps {
  className?: string;
}

/**
 * Simplified NotificationBell component using HTTP polling only
 * No WebSocket complexity - reliable and simple
 */
export const NotificationBell: React.FC<NotificationBellProps> = ({ className = '' }) => {
  const { taskCount, tasks, loading, error, refreshTasks } = useTaskNotifications();
  const [isOpen, setIsOpen] = useState(false);

  const handleBellClick = () => {
    setIsOpen(!isOpen);
    if (!isOpen) {
      refreshTasks(); // Refresh when opening dropdown
    }
  };

  return (
    <div className={`relative ${className}`}>
      {/* Notification Bell */}
      <button
        onClick={handleBellClick}
        className="relative p-2 text-gray-600 hover:text-gray-800 focus:outline-none focus:text-gray-800"
        aria-label={`Notifications (${taskCount} pending tasks)`}
      >
        {/* Bell Icon */}
        <svg
          className="w-6 h-6"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"
          />
        </svg>

        {/* Badge */}
        {taskCount > 0 && (
          <span className="absolute top-0 right-0 inline-flex items-center justify-center px-2 py-1 text-xs font-bold leading-none text-white transform translate-x-1/2 -translate-y-1/2 bg-red-600 rounded-full">
            {taskCount}
          </span>
        )}

        {/* Loading indicator */}
        {loading && (
          <span className="absolute top-0 right-0 w-2 h-2 bg-blue-500 rounded-full animate-pulse"></span>
        )}
      </button>

      {/* Dropdown */}
      {isOpen && (
        <div className="absolute right-0 mt-2 w-80 bg-white border border-gray-200 rounded-lg shadow-lg z-50">
          <div className="p-4 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-800">
              My Tasks ({taskCount})
            </h3>
            <p className="text-sm text-gray-600">
              🔄 Updates every 30 seconds via HTTP polling
            </p>
          </div>

          <div className="max-h-64 overflow-y-auto">
            {error && (
              <div className="p-4 text-sm text-red-600">
                Error loading tasks: {error}
              </div>
            )}
            
            {tasks.length === 0 ? (
              <div className="p-4 text-sm text-gray-500 text-center">
                No pending tasks
              </div>
            ) : (
              <div className="divide-y divide-gray-200">
                {tasks.map((task, index) => (
                  <div key={task.id || index} className="p-4 hover:bg-gray-50">
                    <div className="font-medium text-gray-800">
                      {task.task_type || 'Task'}
                    </div>
                    <div className="text-sm text-gray-600 mt-1">
                      {task.name || 'No description'}
                    </div>
                    <div className="text-xs text-gray-500 mt-1">
                      Created: {task.created_at ? new Date(task.created_at).toLocaleDateString() : 'Unknown'}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="p-4 border-t border-gray-200">
            <button
              onClick={() => window.location.href = '/my-tasks'}
              className="w-full text-center text-sm text-blue-600 hover:text-blue-800"
            >
              View All Tasks →
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default NotificationBell;
