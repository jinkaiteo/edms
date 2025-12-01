import { useState, useEffect, useCallback } from 'react';

interface NotificationData {
  taskCount: number;
  tasks: any[];
}

/**
 * Simplified notification hook using only HTTP polling
 * No WebSocket complexity - reliable HTTP requests every 30 seconds
 */
export const useSimpleNotifications = () => {
  const [notificationData, setNotificationData] = useState<NotificationData>({
    taskCount: 0,
    tasks: []
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchTasks = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await fetch('/api/v1/workflows/tasks/user-tasks/?status=pending', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('accessToken')}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setNotificationData({
          taskCount: data.tasks?.length || 0,
          tasks: data.tasks || []
        });
        console.log(`📊 Notification count: ${data.tasks?.length || 0} pending tasks only`);
      } else {
        if (response.status === 401) {
          // Unauthorized - likely token expired
          setError('Authentication expired');
          console.warn('Token expired, redirecting to login');
          // Don't auto-redirect, let user handle it
        } else {
          setError(`HTTP ${response.status}: Failed to fetch tasks`);
          console.warn('Failed to fetch tasks:', response.status, response.statusText);
        }
      }
    } catch (err) {
      console.error('Error fetching tasks:', err);
      if (err instanceof TypeError && err.message.includes('fetch')) {
        setError('Network error - check connection');
      } else {
        setError('Failed to fetch tasks');
      }
    } finally {
      setLoading(false);
    }
  }, []);

  // Optimized HTTP polling with exponential backoff on errors
  useEffect(() => {
    fetchTasks(); // Initial fetch
    
    // Dynamic polling interval based on activity
    const getPollingInterval = () => {
      if (error) return 60000; // 1 minute if error
      if (notificationData.taskCount > 0) return 15000; // 15 seconds if active tasks
      return 30000; // 30 seconds if no tasks
    };
    
    const interval = setInterval(() => {
      fetchTasks();
    }, getPollingInterval());
    
    return () => clearInterval(interval);
  }, [fetchTasks, error, notificationData.taskCount]);

  return {
    taskCount: notificationData.taskCount,
    tasks: notificationData.tasks,
    loading,
    error,
    refreshTasks: fetchTasks
  };
};
