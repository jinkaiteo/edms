import React, { useState, useEffect } from 'react';

interface NotificationBellProps {
  className?: string;
}

/**
 * Document-focused NotificationBell - shows pending document counts
 * Uses document filtering instead of separate task system
 */
export const NotificationBell: React.FC<NotificationBellProps> = ({ className = '' }) => {
  const [documentCount, setDocumentCount] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  // Using direct fetch instead of useApi hook to avoid circular dependencies

  // Poll for pending documents every 60 seconds
  useEffect(() => {
    const fetchPendingDocuments = async () => {
      try {
        setLoading(true);
        setError(null);
        
        // Get documents requiring user action using document filter
        const response = await fetch('/api/v1/documents/documents/?filter=pending_my_action', {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('accessToken') || ''}`
          }
        });
        
        if (response.ok) {
          const data = await response.json();
          setDocumentCount(data.results ? data.results.length : 0);
        } else {
          throw new Error(`HTTP ${response.status}`);
        }
      } catch (err) {
        console.error('Failed to fetch pending documents:', err);
        setError('Failed to load notifications');
        setDocumentCount(0);
      } finally {
        setLoading(false);
      }
    };

    // Initial fetch
    fetchPendingDocuments();

    // Set up polling every 60 seconds
    const interval = setInterval(fetchPendingDocuments, 60000);

    return () => clearInterval(interval);
  }, []);
  
  const handleBellClick = () => {
    // Redirect to document management with pending filter
    window.location.href = '/document-management?filter=pending';
  };

  const getBadgeContent = () => {
    if (loading) return '⟳';
    if (error) return '!';
    if (documentCount > 0) return documentCount > 99 ? '99+' : documentCount.toString();
    return null; // No badge if no pending documents
  };

  const getBadgeColor = () => {
    if (error) return 'bg-red-600';
    if (loading) return 'bg-gray-400';
    if (documentCount > 0) return 'bg-blue-600';
    return 'bg-gray-400';
  };

  const badgeContent = getBadgeContent();
  const badgeColor = getBadgeColor();

  return (
    <div className={`relative ${className}`}>
      <button
        onClick={handleBellClick}
        className="relative p-2 text-gray-600 hover:text-gray-800 focus:outline-none focus:text-gray-800"
        aria-label={`View pending documents${documentCount > 0 ? ` (${documentCount} pending)` : ''}`}
        title={error ? 'Error loading notifications' : `${documentCount} pending documents`}
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
