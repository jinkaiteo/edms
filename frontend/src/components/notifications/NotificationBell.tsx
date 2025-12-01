import React from 'react';

interface NotificationBellProps {
  className?: string;
}

/**
 * Temporary simplified NotificationBell - no hook dependencies
 * This allows the system to work while we resolve the hook import issues
 */
export const NotificationBell: React.FC<NotificationBellProps> = ({ className = '' }) => {
  const handleBellClick = () => {
    // Simple redirect to tasks page instead of complex hook logic
    window.location.href = '/my-tasks';
  };

  return (
    <div className={`relative ${className}`}>
      <button
        onClick={handleBellClick}
        className="relative p-2 text-gray-600 hover:text-gray-800 focus:outline-none focus:text-gray-800"
        aria-label="View my tasks"
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

        {/* Simple badge - shows "!" to indicate tasks may be available */}
        <span className="absolute top-0 right-0 inline-flex items-center justify-center px-2 py-1 text-xs font-bold leading-none text-white transform translate-x-1/2 -translate-y-1/2 bg-blue-600 rounded-full">
          !
        </span>
      </button>
    </div>
  );
};

export default NotificationBell;
