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
      
      const response = await fetch('/api/v1/workflows/tasks/user-tasks/', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setNotificationData({
          taskCount: data.tasks?.length || 0,
          tasks: data.tasks || []
        });
        console.log(`📊 Tasks updated: ${data.tasks?.length || 0} pending tasks`);
      } else {
        console.warn('Failed to fetch tasks:', response.status);
      }
    } catch (err) {
      console.error('Error fetching tasks:', err);
      setError('Failed to fetch tasks');
    } finally {
      setLoading(false);
    }
  }, []);

  // HTTP polling every 30 seconds
  useEffect(() => {
    fetchTasks(); // Initial fetch
    
    const interval = setInterval(() => {
      fetchTasks();
    }, 30000); // 30 seconds
    
    return () => clearInterval(interval);
  }, [fetchTasks]);

  return {
    taskCount: notificationData.taskCount,
    tasks: notificationData.tasks,
    loading,
    error,
    refreshTasks: fetchTasks
  };
};
