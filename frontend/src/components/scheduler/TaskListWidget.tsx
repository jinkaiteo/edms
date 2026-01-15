/**
 * Task List Widget - Displays scheduled tasks with execution status
 * Replaces abstract health score with intuitive task table
 */

import React, { useEffect, useState } from 'react';
import apiService from '../../services/api.ts';

interface TaskRun {
  timestamp: string | null;
  relative_time: string;
  status: string;
  duration: number | null;
}

interface Task {
  name: string;
  category: string;
  schedule: string;
  last_run: TaskRun;
  next_run: TaskRun;
  status: string;
  status_message: string;
  is_registered: boolean;
}

interface TaskListData {
  timestamp: string;
  summary: {
    total_tasks: number;
    healthy: number;
    failed: number;
    warnings: number;
    overall_status: string;
  };
  tasks: Task[];
  tasks_by_category: Record<string, Task[]>;
}

const TaskListWidget: React.FC = () => {
  const [data, setData] = useState<TaskListData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedCategories, setExpandedCategories] = useState<Set<string>>(new Set());
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);
  const [showDetailModal, setShowDetailModal] = useState(false);
  const [triggeringTask, setTriggeringTask] = useState<string | null>(null);

  useEffect(() => {
    fetchTaskStatus();
    // Refresh every 30 seconds
    const interval = setInterval(fetchTaskStatus, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchTaskStatus = async () => {
    try {
      const response = await apiService.get('/scheduler/monitoring/status/');
      setData(response);
      setError(null);
    } catch (err: any) {
      console.error('Failed to fetch task status:', err);
      setError('Failed to load task status');
    } finally {
      setLoading(false);
    }
  };

  const toggleCategory = (category: string) => {
    const newExpanded = new Set(expandedCategories);
    if (newExpanded.has(category)) {
      newExpanded.delete(category);
    } else {
      newExpanded.add(category);
    }
    setExpandedCategories(newExpanded);
  };

  const handleTaskClick = (task: Task) => {
    setSelectedTask(task);
    setShowDetailModal(true);
  };

  const handleManualTrigger = async (taskName: string) => {
    if (!window.confirm(`Are you sure you want to manually trigger this task?\n\nTask: ${taskName}`)) {
      return;
    }

    setTriggeringTask(taskName);
    try {
      // Convert hyphenated schedule name to underscore format expected by backend
      const backendTaskName = taskName.replace(/-/g, '_');
      const result = await apiService.post('/scheduler/monitoring/manual-trigger/', {
        task_name: backendTaskName
      });
      
      // Immediate feedback - refresh data to show new execution
      await fetchTaskStatus();
      
      alert(`✅ Task executed successfully!\n\nTask: ${taskName}\nDuration: ${result.duration_seconds?.toFixed(2)}s\n\nThe dashboard has been refreshed.`);
    } catch (err: any) {
      console.error('Failed to trigger task:', err);
      alert(`Failed to trigger task: ${err.response?.data?.error || err.message}`);
    } finally {
      setTriggeringTask(null);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'SUCCESS':
        return 'text-green-600 bg-green-50 border-green-200';
      case 'FAILURE':
      case 'CRITICAL':
        return 'text-red-600 bg-red-50 border-red-200';
      case 'WARNING':
        return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      case 'SCHEDULED':
      case 'PENDING':
        return 'text-blue-600 bg-blue-50 border-blue-200';
      default:
        return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'SUCCESS':
        return '✅';
      case 'FAILURE':
      case 'CRITICAL':
        return '❌';
      case 'WARNING':
        return '⚠️';
      case 'SCHEDULED':
      case 'PENDING':
        return '📅';
      default:
        return '⏳';
    }
  };

  const getOverallStatusColor = (status: string) => {
    switch (status) {
      case 'HEALTHY':
        return 'bg-green-100 text-green-800 border-green-300';
      case 'WARNING':
        return 'bg-yellow-100 text-yellow-800 border-yellow-300';
      case 'CRITICAL':
        return 'bg-red-100 text-red-800 border-red-300';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-300';
    }
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-3/4 mb-4"></div>
          <div className="h-4 bg-gray-200 rounded w-1/2"></div>
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="text-red-600">
          <p className="font-semibold">Error loading scheduler status</p>
          <p className="text-sm">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow">
      {/* Header with Summary */}
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">Scheduled Tasks</h2>
            <p className="text-sm text-gray-500 mt-1">
              {data.summary.total_tasks} tasks monitored
            </p>
          </div>
          <div className={`px-4 py-2 rounded-lg border ${getOverallStatusColor(data.summary.overall_status)}`}>
            <span className="font-semibold">{data.summary.overall_status}</span>
          </div>
        </div>
        
        {/* Summary Stats */}
        <div className="mt-4 grid grid-cols-4 gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-gray-900">{data.summary.total_tasks}</div>
            <div className="text-xs text-gray-500">Total</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">{data.summary.healthy}</div>
            <div className="text-xs text-gray-500">Healthy</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-yellow-600">{data.summary.warnings}</div>
            <div className="text-xs text-gray-500">Warnings</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-red-600">{data.summary.failed}</div>
            <div className="text-xs text-gray-500">Failed</div>
          </div>
        </div>
      </div>

      {/* Task List by Category */}
      <div className="divide-y divide-gray-200">
        {Object.entries(data.tasks_by_category).map(([category, tasks]) => (
          <div key={category} className="px-6 py-4">
            {/* Category Header */}
            <button
              onClick={() => toggleCategory(category)}
              className="flex items-center justify-between w-full text-left hover:bg-gray-50 rounded px-2 py-1 -mx-2"
            >
              <div className="flex items-center">
                <span className="text-lg font-medium text-gray-900">{category}</span>
                <span className="ml-2 text-sm text-gray-500">({tasks.length} tasks)</span>
              </div>
              <svg
                className={`w-5 h-5 transition-transform ${
                  expandedCategories.has(category) ? 'transform rotate-180' : ''
                }`}
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </button>

            {/* Task Table */}
            {expandedCategories.has(category) && (
              <div className="mt-3 overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead>
                    <tr className="bg-gray-50">
                      <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Task</th>
                      <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Last Run</th>
                      <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Next Run</th>
                      <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                      <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {tasks.map((task, idx) => (
                      <tr key={idx} className="hover:bg-gray-50">
                        <td className="px-3 py-3">
                          <div className="text-sm font-medium text-gray-900">{task.name}</div>
                          <div className="text-xs text-gray-500">{task.schedule}</div>
                        </td>
                        <td className="px-3 py-3 text-sm text-gray-700">
                          {task.last_run.relative_time}
                        </td>
                        <td className="px-3 py-3 text-sm text-gray-700">
                          {task.next_run.relative_time}
                        </td>
                        <td className="px-3 py-3">
                          <span className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium border ${getStatusColor(task.status)}`}>
                            <span className="mr-1">{getStatusIcon(task.status)}</span>
                            {task.status}
                          </span>
                          {!task.is_registered && (
                            <div className="text-xs text-red-600 mt-1">
                              ⚠️ Not registered
                            </div>
                          )}
                        </td>
                        <td className="px-3 py-3">
                          <div className="flex space-x-2">
                            <button
                              onClick={() => handleTaskClick(task)}
                              className="text-blue-600 hover:text-blue-800 text-xs font-medium"
                              title="View details"
                            >
                              📊 Details
                            </button>
                            <button
                              onClick={() => handleManualTrigger(task.schedule_name)}
                              disabled={triggeringTask === task.schedule_name}
                              className="text-green-600 hover:text-green-800 text-xs font-medium disabled:text-gray-400"
                              title="Manually trigger this task"
                            >
                              {triggeringTask === task.schedule_name ? '⏳ Triggering...' : '▶️ Run Now'}
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Footer */}
      <div className="px-6 py-3 bg-gray-50 border-t border-gray-200 text-xs text-gray-500">
        Last updated: {new Date(data.timestamp).toLocaleString()} • Auto-refreshes every 30 seconds
      </div>

      {/* Task Detail Modal */}
      {showDetailModal && selectedTask && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[80vh] overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
              <h3 className="text-lg font-semibold text-gray-900">{selectedTask.name}</h3>
              <button
                onClick={() => setShowDetailModal(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                ✕
              </button>
            </div>
            
            <div className="px-6 py-4 overflow-y-auto max-h-[60vh]">
              {/* Task Information */}
              <div className="space-y-4">
                <div>
                  <h4 className="text-sm font-medium text-gray-700 mb-2">Task Information</h4>
                  <dl className="grid grid-cols-2 gap-x-4 gap-y-2 text-sm">
                    <dt className="text-gray-500">Category:</dt>
                    <dd className="text-gray-900">{selectedTask.category}</dd>
                    
                    <dt className="text-gray-500">Schedule:</dt>
                    <dd className="text-gray-900">{selectedTask.schedule}</dd>
                    
                    <dt className="text-gray-500">Task Path:</dt>
                    <dd className="text-gray-900 text-xs font-mono break-all">{selectedTask.task_path}</dd>
                    
                    <dt className="text-gray-500">Registered:</dt>
                    <dd className="text-gray-900">
                      {selectedTask.is_registered ? '✅ Yes' : '❌ No'}
                    </dd>
                  </dl>
                </div>

                <div className="border-t pt-4">
                  <h4 className="text-sm font-medium text-gray-700 mb-2">Description</h4>
                  <p className="text-sm text-gray-600">{selectedTask.description}</p>
                </div>

                <div className="border-t pt-4">
                  <h4 className="text-sm font-medium text-gray-700 mb-2">Execution Status</h4>
                  <div className="space-y-2">
                    <div className="flex justify-between items-center p-3 bg-gray-50 rounded">
                      <span className="text-sm text-gray-600">Current Status:</span>
                      <span className={`px-2 py-1 rounded text-xs font-medium ${getStatusColor(selectedTask.status)}`}>
                        {getStatusIcon(selectedTask.status)} {selectedTask.status}
                      </span>
                    </div>
                    
                    <div className="flex justify-between items-center p-3 bg-gray-50 rounded">
                      <span className="text-sm text-gray-600">Last Run:</span>
                      <span className="text-sm text-gray-900">
                        {selectedTask.last_run.relative_time}
                        {selectedTask.last_run.timestamp && (
                          <span className="text-xs text-gray-500 ml-2">
                            ({new Date(selectedTask.last_run.timestamp).toLocaleString()})
                          </span>
                        )}
                      </span>
                    </div>
                    
                    <div className="flex justify-between items-center p-3 bg-gray-50 rounded">
                      <span className="text-sm text-gray-600">Next Run:</span>
                      <span className="text-sm text-gray-900">
                        {selectedTask.next_run.relative_time}
                        {selectedTask.next_run.timestamp && (
                          <span className="text-xs text-gray-500 ml-2">
                            ({new Date(selectedTask.next_run.timestamp).toLocaleString()})
                          </span>
                        )}
                      </span>
                    </div>

                    {selectedTask.last_run.duration && (
                      <div className="flex justify-between items-center p-3 bg-gray-50 rounded">
                        <span className="text-sm text-gray-600">Last Duration:</span>
                        <span className="text-sm text-gray-900">{selectedTask.last_run.duration}s</span>
                      </div>
                    )}
                  </div>
                </div>

                {selectedTask.statistics && (
                  <div className="border-t pt-4">
                    <h4 className="text-sm font-medium text-gray-700 mb-2">Statistics (24 hours)</h4>
                    <div className="grid grid-cols-2 gap-4">
                      <div className="p-3 bg-blue-50 rounded">
                        <div className="text-2xl font-bold text-blue-600">
                          {selectedTask.statistics.runs_24h ?? 'N/A'}
                        </div>
                        <div className="text-xs text-gray-600">Total Runs</div>
                      </div>
                      
                      <div className="p-3 bg-green-50 rounded">
                        <div className="text-2xl font-bold text-green-600">
                          {selectedTask.statistics.success_rate !== null 
                            ? `${selectedTask.statistics.success_rate.toFixed(0)}%` 
                            : 'N/A'}
                        </div>
                        <div className="text-xs text-gray-600">Success Rate</div>
                      </div>
                      
                      {selectedTask.statistics.avg_duration !== null && (
                        <div className="p-3 bg-purple-50 rounded col-span-2">
                          <div className="text-2xl font-bold text-purple-600">
                            {selectedTask.statistics.avg_duration}s
                          </div>
                          <div className="text-xs text-gray-600">Average Duration</div>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {!selectedTask.is_registered && (
                  <div className="border-t pt-4">
                    <div className="bg-red-50 border border-red-200 rounded p-3">
                      <h4 className="text-sm font-medium text-red-800 mb-1">⚠️ Task Not Registered</h4>
                      <p className="text-xs text-red-600">{selectedTask.status_message}</p>
                      <p className="text-xs text-red-600 mt-1">
                        This task won't execute until the Celery worker is restarted.
                      </p>
                    </div>
                  </div>
                )}
              </div>
            </div>

            <div className="px-6 py-4 border-t border-gray-200 flex justify-between">
              <button
                onClick={() => handleManualTrigger(selectedTask.schedule_name)}
                disabled={triggeringTask === selectedTask.schedule_name || !selectedTask.is_registered}
                className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 disabled:bg-gray-300 disabled:cursor-not-allowed text-sm"
              >
                {triggeringTask === selectedTask.schedule_name ? '⏳ Triggering...' : '▶️ Run Task Now'}
              </button>
              <button
                onClick={() => setShowDetailModal(false)}
                className="px-4 py-2 bg-gray-200 text-gray-700 rounded hover:bg-gray-300 text-sm"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default TaskListWidget;

