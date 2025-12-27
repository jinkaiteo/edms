import { useState, useEffect } from 'react';

interface TaskNotificationData {
  taskCount: number;
  tasks: any[];
  loading: boolean;
  error: string | null;
}

export const useTaskNotifications = () => {
  const [data, setData] = useState<TaskNotificationData>({
    taskCount: 0,
    tasks: [],
    loading: false,
    error: null
  });

  const fetchTasks = async () => {
    try {
      setData(prev => ({ ...prev, loading: true, error: null }));
      
      const token = localStorage.getItem('access_token');
      if (!token) {
        setData({ taskCount: 0, tasks: [], loading: false, error: null });
        return;
      }

      const response = await fetch('/api/v1/workflows/tasks/user-tasks/', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (response.ok) {
        const result = await response.json();
        const tasks = result.tasks || [];
        setData({
          taskCount: tasks.length,
          tasks: tasks,
          loading: false,
          error: null
        });
        console.log(`📊 Tasks updated: ${tasks.length} pending tasks`);
      } else {
        setData({ taskCount: 0, tasks: [], loading: false, error: 'API error' });
      }
    } catch (err) {
      console.error('Error fetching tasks:', err);
      setData(prev => ({ ...prev, loading: false, error: 'Failed to fetch tasks' }));
    }
  };

  const refreshTasks = () => {
    fetchTasks();
  };

  useEffect(() => {
    fetchTasks();
    const interval = setInterval(fetchTasks, 30000); // 30 seconds
    return () => clearInterval(interval);
  }, []);

  return {
    taskCount: data.taskCount,
    tasks: data.tasks,
    loading: data.loading,
    error: data.error,
    refreshTasks
  };
};
