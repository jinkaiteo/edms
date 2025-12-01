import React from 'react';
import { useSimpleNotifications } from '../../hooks/useSimpleNotifications.ts';

interface NotificationBellProps {
  className?: string;
}

/**
 * Enhanced NotificationBell - now shows actual task counts with loading states
 * Uses simplified HTTP polling for reliable notification updates
 */
export const NotificationBell: React.FC<NotificationBellProps> = ({ className = '' }) => {
  const { taskCount, loading, error } = useSimpleNotifications();
  
  const handleBellClick = () => {
    // Redirect to tasks page to view actual tasks
    window.location.href = '/my-tasks';
  };

  const getBadgeContent = () => {
    if (loading) return '⟳';
    if (error) return '!';
    if (taskCount > 0) return taskCount > 99 ? '99+' : taskCount.toString();
    return null; // No badge if no tasks
  };

  const getBadgeColor = () => {
    if (error) return 'bg-red-600';
    if (loading) return 'bg-gray-400';
    if (taskCount > 0) return 'bg-blue-600';
    return 'bg-gray-400';
  };

  const badgeContent = getBadgeContent();
  const badgeColor = getBadgeColor();

  return (
    <div className={`relative ${className}`}>
      <button
        onClick={handleBellClick}
        className="relative p-2 text-gray-600 hover:text-gray-800 focus:outline-none focus:text-gray-800"
        aria-label={`View my tasks${taskCount > 0 ? ` (${taskCount} pending)` : ''}`}
        title={error ? 'Error loading notifications' : `${taskCount} pending tasks`}
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

        {/* Dynamic badge - shows actual task count, loading state, or error */}
        {badgeContent && (
          <span className={`absolute top-0 right-0 inline-flex items-center justify-center px-2 py-1 text-xs font-bold leading-none text-white transform translate-x-1/2 -translate-y-1/2 ${badgeColor} rounded-full min-w-[20px] h-5`}>
            {badgeContent}
          </span>
        )}
      </button>
    </div>
  );
};

export default NotificationBell;
