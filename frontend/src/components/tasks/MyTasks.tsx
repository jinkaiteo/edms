import React, { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import LoadingSpinner from '../common/LoadingSpinner';

interface Task {
  id: string;
  name: string;
  description: string;
  task_type: string;
  priority: 'LOW' | 'NORMAL' | 'HIGH' | 'URGENT';
  status: string;
  created_at: string;
  due_date?: string;
  is_overdue: boolean;
  assigned_by: string;
  workflow_type: string;
  document_id?: number;
  document_uuid?: string;
  document_number?: string;
  document_title?: string;
  document_status?: string;
  document_version?: string;
  action_url?: string;
  priority_class: string;
}

interface TaskSummary {
  total_tasks: number;
  overdue_tasks: number;
  high_priority_tasks: number;
  upcoming_due_count: number;
  task_types: Record<string, number>;
}

const MyTasks: React.FC = () => {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [taskSummary, setTaskSummary] = useState<TaskSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [completingTask, setCompletingTask] = useState<string | null>(null);
  
  const { user } = useAuth();

  const fetchTasks = async () => {
    try {
      setLoading(true);
      setError(null);

      const token = localStorage.getItem('accessToken');
      if (!token) {
        throw new Error('No authentication token found');
      }

      // Fetch tasks and summary in parallel
      const [tasksResponse, summaryResponse] = await Promise.all([
        fetch('/api/v1/workflows/tasks/author/', {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        }),
        fetch('/api/v1/workflows/tasks/summary/', {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        })
      ]);

      if (!tasksResponse.ok) {
        throw new Error('Failed to fetch tasks');
      }

      if (!summaryResponse.ok) {
        throw new Error('Failed to fetch task summary');
      }

      const tasksData = await tasksResponse.json();
      const summaryData = await summaryResponse.json();

      setTasks(tasksData.tasks || []);
      setTaskSummary(summaryData.summary);

    } catch (err: any) {
      console.error('Error fetching tasks:', err);
      setError(err.message || 'Failed to load tasks');
    } finally {
      setLoading(false);
    }
  };

  const completeTask = async (taskId: string, completionNote: string = '') => {
    try {
      setCompletingTask(taskId);
      setError(null);

      const token = localStorage.getItem('accessToken');
      if (!token) {
        throw new Error('No authentication token found');
      }

      const response = await fetch(`/api/v1/workflows/tasks/${taskId}/complete/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          completion_note: completionNote
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to complete task');
      }

      // Refresh tasks after completion
      await fetchTasks();

    } catch (err: any) {
      console.error('Error completing task:', err);
      setError(err.message || 'Failed to complete task');
    } finally {
      setCompletingTask(null);
    }
  };

  useEffect(() => {
    if (user) {
      fetchTasks();
    }
  }, [user]);

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getPriorityIcon = (priority: string) => {
    switch (priority) {
      case 'URGENT': return '🚨';
      case 'HIGH': return '⚡';
      case 'NORMAL': return '📋';
      case 'LOW': return '📌';
      default: return '📋';
    }
  };

  const getTaskTypeIcon = (taskType: string) => {
    switch (taskType) {
      case 'REVIEW': return '👀';
      case 'APPROVE': return '✅';
      case 'VALIDATE': return '🔍';
      case 'SIGN': return '✍️';
      case 'NOTIFY': return '📢';
      default: return '📋';
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-64">
        <LoadingSpinner />
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-md p-4">
        <div className="flex">
          <div className="flex-shrink-0">
            <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
            </svg>
          </div>
          <div className="ml-3">
            <h3 className="text-sm font-medium text-red-800">Error Loading Tasks</h3>
            <div className="mt-2 text-sm text-red-700">
              {error}
            </div>
            <button
              onClick={fetchTasks}
              className="mt-2 text-sm text-red-800 hover:text-red-900 underline"
            >
              Try Again
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Task Summary */}
      {taskSummary && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">📋 My Tasks Summary</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-blue-50 p-4 rounded-lg">
              <div className="text-2xl font-bold text-blue-600">{taskSummary.total_tasks}</div>
              <div className="text-sm text-blue-800">Total Tasks</div>
            </div>
            
            <div className="bg-red-50 p-4 rounded-lg">
              <div className="text-2xl font-bold text-red-600">{taskSummary.overdue_tasks}</div>
              <div className="text-sm text-red-800">Overdue</div>
            </div>
            
            <div className="bg-orange-50 p-4 rounded-lg">
              <div className="text-2xl font-bold text-orange-600">{taskSummary.high_priority_tasks}</div>
              <div className="text-sm text-orange-800">High Priority</div>
            </div>
            
            <div className="bg-green-50 p-4 rounded-lg">
              <div className="text-2xl font-bold text-green-600">{taskSummary.upcoming_due_count}</div>
              <div className="text-sm text-green-800">Due This Week</div>
            </div>
          </div>
        </div>
      )}

      {/* Tasks List */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">
            📝 Pending Tasks ({tasks.length})
          </h2>
        </div>

        {tasks.length === 0 ? (
          <div className="px-6 py-8 text-center">
            <div className="text-4xl mb-2">🎉</div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">All caught up!</h3>
            <p className="text-gray-600">You have no pending tasks at the moment.</p>
          </div>
        ) : (
          <div className="divide-y divide-gray-200">
            {tasks.map((task) => (
              <div key={task.id} className="px-6 py-4 hover:bg-gray-50">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-2 mb-2">
                      <span className="text-lg">{getTaskTypeIcon(task.task_type)}</span>
                      <h3 className="text-sm font-medium text-gray-900">{task.name}</h3>
                      <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${task.priority_class}`}>
                        {getPriorityIcon(task.priority)} {task.priority}
                      </span>
                      {task.is_overdue && (
                        <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-red-100 text-red-800">
                          🚨 OVERDUE
                        </span>
                      )}
                    </div>
                    
                    <p className="text-sm text-gray-600 mb-2">{task.description}</p>
                    
                    {task.document_number && (
                      <div className="text-xs text-gray-500 mb-2">
                        📄 Document: <span className="font-medium">{task.document_number}</span>
                        {task.document_title && ` - ${task.document_title}`}
                        {task.document_version && ` (v${task.document_version})`}
                        <span className="ml-2 text-blue-600">{task.document_status}</span>
                      </div>
                    )}
                    
                    <div className="flex items-center space-x-4 text-xs text-gray-500">
                      <span>👤 Assigned by: {task.assigned_by}</span>
                      <span>📅 Created: {formatDate(task.created_at)}</span>
                      {task.due_date && (
                        <span className={task.is_overdue ? 'text-red-600 font-medium' : ''}>
                          ⏰ Due: {formatDate(task.due_date)}
                        </span>
                      )}
                      <span>🔄 Type: {task.workflow_type}</span>
                    </div>
                  </div>
                  
                  <div className="flex space-x-2 ml-4">
                    {task.action_url && (
                      <button
                        onClick={() => window.location.href = task.action_url!}
                        className="inline-flex items-center px-3 py-1 border border-gray-300 shadow-sm text-xs font-medium rounded text-gray-700 bg-white hover:bg-gray-50"
                      >
                        🔗 View Document
                      </button>
                    )}
                    
                    <button
                      onClick={() => completeTask(task.id, 'Task completed from My Tasks page')}
                      disabled={completingTask === task.id}
                      className="inline-flex items-center px-3 py-1 border border-transparent shadow-sm text-xs font-medium rounded text-white bg-green-600 hover:bg-green-700 disabled:opacity-50"
                    >
                      {completingTask === task.id ? (
                        <>
                          <svg className="animate-spin -ml-1 mr-1 h-3 w-3 text-white" fill="none" viewBox="0 0 24 24">
                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                            <path className="opacity-75" fill="currentColor" d="m4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                          </svg>
                          Completing...
                        </>
                      ) : (
                        <>✅ Complete</>
                      )}
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Refresh Button */}
      <div className="text-center">
        <button
          onClick={fetchTasks}
          disabled={loading}
          className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50"
        >
          {loading ? (
            <>
              <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="m4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Refreshing...
            </>
          ) : (
            <>🔄 Refresh Tasks</>
          )}
        </button>
      </div>
    </div>
  );
};

export default MyTasks;