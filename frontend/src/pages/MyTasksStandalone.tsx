/**
 * My Tasks - Standalone Page
 * 
 * This page shows workflow tasks assigned to the current user.
 * It provides a dedicated interface for managing personal workflow items.
 */

import React, { useState, useEffect } from 'react';
import Layout from '../components/common/Layout.tsx';
import { useAuth } from '../contexts/AuthContext.tsx';
import { apiService } from '../services/api.ts';
import LoadingSpinner from '../components/common/LoadingSpinner.tsx';
import { 
  ClipboardDocumentListIcon, 
  DocumentTextIcon,
  ClockIcon,
  CheckCircleIcon,
  ExclamationCircleIcon,
  EyeIcon,
  ChevronRightIcon
} from '@heroicons/react/24/outline';

interface WorkflowTask {
  id: string;
  document_uuid: string;
  document_number: string;
  document_title: string;
  task_type: 'review' | 'approval' | 'revision';
  status: 'pending' | 'in_progress' | 'completed' | 'overdue';
  priority: 'low' | 'medium' | 'high' | 'urgent';
  assigned_date: string;
  due_date?: string;
  assignee_display: string;
  author_display: string;
  comments_count: number;
  completed_at?: string;
  completion_note?: string;
}

const MyTasksStandalone: React.FC = () => {
  const { user, authenticated } = useAuth();
  const [tasks, setTasks] = useState<WorkflowTask[]>([]);
  const [completedTasks, setCompletedTasks] = useState<WorkflowTask[]>([]);
  const [activeTab, setActiveTab] = useState<'pending' | 'completed'>('pending');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedFilter, setSelectedFilter] = useState<string>('all');

  useEffect(() => {
    if (authenticated) {
      loadMyTasks();
      loadCompletedTasks();
    }
  }, [authenticated]);

  const loadMyTasks = async () => {
    try {
      setLoading(true);
      setError(null);

      console.log(`🔍 Loading pending tasks for user: ${user?.username} via WorkflowTask API`);

      // Load pending tasks
      const tasks = await loadTasksFromAPI('pending');
      setTasks(tasks);

      console.log(`📊 PENDING TASK COUNT for ${user?.username}: ${tasks.length}`);

    } catch (err: any) {
      console.error('Error loading pending tasks:', err);
      setError('Failed to load tasks. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const loadCompletedTasks = async () => {
    try {
      console.log(`🔍 Loading completed tasks for user: ${user?.username}`);

      // Load completed tasks
      const tasks = await loadTasksFromAPI('completed');
      setCompletedTasks(tasks);

      console.log(`📊 COMPLETED TASK COUNT for ${user?.username}: ${tasks.length}`);

    } catch (err: any) {
      console.error('Error loading completed tasks:', err);
      // Don't set error for completed tasks - just log it
    }
  };

  const loadTasksFromAPI = async (status: 'pending' | 'completed' = 'pending'): Promise<WorkflowTask[]> => {
    try {
      console.log(`🎯 Fetching ${status} tasks from API endpoint: /api/v1/workflows/tasks/user-tasks/?status=${status}`);
      
      // Use the WORKING user-tasks endpoint with proper status filtering
      const response = await apiService.get(`/workflows/tasks/user-tasks/?status=${status}`);
      console.log(`📋 TASKS DEBUG: Raw API response:`, response);
      console.log(`📋 TASKS DEBUG: Response type:`, typeof response);
      console.log(`📋 TASKS DEBUG: Response keys:`, Object.keys(response || {}));
      
      // Handle different response structures
      let tasksArray = [];
      if (response && response.tasks && Array.isArray(response.tasks)) {
        tasksArray = response.tasks;
        console.log(`📋 TASKS DEBUG: Using response.tasks array (${tasksArray.length} items)`);
      } else if (response && Array.isArray(response.results)) {
        tasksArray = response.results;
        console.log(`📋 TASKS DEBUG: Using response.results array (${tasksArray.length} items)`);
      } else if (Array.isArray(response)) {
        tasksArray = response;
        console.log(`📋 TASKS DEBUG: Using response as array (${tasksArray.length} items)`);
      } else {
        console.error(`❌ TASKS DEBUG: Unexpected response structure:`, response);
        tasksArray = [];
      }
      
      console.log(`📋 TASKS DEBUG: Final tasks array:`, tasksArray);
      
      console.log(`🔍 Backend returned ${tasksArray.length} ${status} tasks (pre-filtered)`);
      
      // Convert API task format to our component's WorkflowTask format
      // No client-side filtering needed since backend already filtered by status
      return tasksArray.map((apiTask: any) => ({
        id: apiTask.id || apiTask.uuid,
        document_uuid: apiTask.document_uuid || '',
        document_number: apiTask.document_number || 'Unknown',
        document_title: apiTask.document_title || apiTask.name || 'Unknown Task',
        task_type: apiTask.task_type === 'APPROVE' ? 'approval' : 
                  apiTask.task_type === 'REVIEW' ? 'review' : 'review',
        status: (apiTask.status || status).toLowerCase() as 'pending' | 'completed',
        priority: (apiTask.priority?.toLowerCase() || 'medium') as 'low' | 'medium' | 'high' | 'urgent',
        assigned_date: apiTask.created_at || apiTask.assigned_date,
        due_date: apiTask.due_date,
        assignee_display: user?.full_name || user?.username || 'You',
        author_display: apiTask.assigned_by || 'System',
        comments_count: 0,
        completed_at: apiTask.completed_at,
        completion_note: apiTask.completion_note
      }));
      
    } catch (error) {
      console.error('Error loading tasks from API:', error);
      console.log('⚠️ Falling back to empty task list');
      return [];
    }
  };

  // REMOVED: loadApprovalTasks - now handled by single API call
  // All tasks (review, approval, etc.) come from the unified task API

  const getPriority = (date: string): 'low' | 'medium' | 'high' | 'urgent' => {
    const daysOld = Math.floor((Date.now() - new Date(date).getTime()) / (1000 * 60 * 60 * 24));
    if (daysOld > 7) return 'urgent';
    if (daysOld > 3) return 'high';
    if (daysOld > 1) return 'medium';
    return 'low';
  };

  const calculateDueDate = (assignedDate: string): string => {
    const assigned = new Date(assignedDate);
    assigned.setDate(assigned.getDate() + 5); // 5 days to complete
    return assigned.toISOString();
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircleIcon className="h-5 w-5 text-green-500" />;
      case 'overdue':
        return <ExclamationCircleIcon className="h-5 w-5 text-red-500" />;
      case 'in_progress':
        return <ClockIcon className="h-5 w-5 text-yellow-500" />;
      default:
        return <ClockIcon className="h-5 w-5 text-blue-500" />;
    }
  };

  const getPriorityBadge = (priority: string) => {
    const colors = {
      urgent: 'bg-red-100 text-red-800',
      high: 'bg-orange-100 text-orange-800',
      medium: 'bg-yellow-100 text-yellow-800',
      low: 'bg-green-100 text-green-800'
    };
    return (
      <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${colors[priority as keyof typeof colors]}`}>
        {priority.toUpperCase()}
      </span>
    );
  };

  const getTaskTypeIcon = (taskType: string) => {
    switch (taskType) {
      case 'approval':
        return <CheckCircleIcon className="h-5 w-5 text-green-600" />;
      case 'revision':
        return <ExclamationCircleIcon className="h-5 w-5 text-yellow-600" />;
      default:
        return <DocumentTextIcon className="h-5 w-5 text-blue-600" />;
    }
  };

  const handleTaskClick = (task: WorkflowTask) => {
    // Navigate to document management with the specific document
    window.location.href = `/document-management?document=${task.document_uuid}`;
  };

  // Get the current task list based on active tab
  const currentTasks = activeTab === 'pending' ? tasks : completedTasks;
  
  const filteredTasks = currentTasks.filter(task => {
    if (selectedFilter === 'all') return true;
    if (selectedFilter === 'pending') return task.status === 'pending';
    if (selectedFilter === 'review') return task.task_type === 'review';
    if (selectedFilter === 'approval') return task.task_type === 'approval';
    return true;
  });

  const taskStats = {
    total: tasks.length,
    pending: tasks.length,
    completed: completedTasks.length,
    review: tasks.filter(t => t.task_type === 'review').length,
    approval: tasks.filter(t => t.task_type === 'approval').length
  };

  if (!authenticated) {
    return (
      <Layout>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="text-center">
            <p className="text-gray-500">Please log in to view your tasks.</p>
          </div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 flex items-center">
            <ClipboardDocumentListIcon className="h-8 w-8 mr-3 text-blue-600" />
            My Tasks
          </h1>
          <p className="mt-2 text-gray-600">
            Manage your workflow tasks and review assignments
          </p>
        </div>

        {/* Task Statistics */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <ClipboardDocumentListIcon className="h-6 w-6 text-gray-400" />
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">Total Tasks</dt>
                    <dd className="text-lg font-medium text-gray-900">{taskStats.total}</dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <ClockIcon className="h-6 w-6 text-blue-400" />
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">Pending</dt>
                    <dd className="text-lg font-medium text-gray-900">{taskStats.pending}</dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <DocumentTextIcon className="h-6 w-6 text-green-400" />
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">Reviews</dt>
                    <dd className="text-lg font-medium text-gray-900">{taskStats.review}</dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <CheckCircleIcon className="h-6 w-6 text-purple-400" />
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">Approvals</dt>
                    <dd className="text-lg font-medium text-gray-900">{taskStats.approval}</dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Main Tabs: Pending vs Completed */}
        <div className="border-b border-gray-200 mb-6">
          <nav className="-mb-px flex space-x-8">
            <button
              onClick={() => {
                setActiveTab('pending');
                setSelectedFilter('all');
              }}
              className={`${
                activeTab === 'pending'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              } whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm`}
            >
              Pending Tasks
              {taskStats.pending > 0 && (
                <span className={`ml-2 py-0.5 px-2 rounded-full text-xs ${
                  activeTab === 'pending' ? 'bg-blue-100 text-blue-600' : 'bg-gray-100 text-gray-600'
                }`}>
                  {taskStats.pending}
                </span>
              )}
            </button>
            <button
              onClick={() => {
                setActiveTab('completed');
                setSelectedFilter('all');
              }}
              className={`${
                activeTab === 'completed'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              } whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm`}
            >
              Completed Tasks
              {taskStats.completed > 0 && (
                <span className={`ml-2 py-0.5 px-2 rounded-full text-xs ${
                  activeTab === 'completed' ? 'bg-blue-100 text-blue-600' : 'bg-gray-100 text-gray-600'
                }`}>
                  {taskStats.completed}
                </span>
              )}
            </button>
          </nav>
        </div>

        {/* Filter Sub-tabs */}
        <div className="border-b border-gray-200 mb-6">
          <nav className="-mb-px flex space-x-8">
            {[
              { key: 'all', name: 'All', count: currentTasks.length },
              { key: 'review', name: 'Reviews', count: currentTasks.filter(t => t.task_type === 'review').length },
              { key: 'approval', name: 'Approvals', count: currentTasks.filter(t => t.task_type === 'approval').length }
            ].map((tab) => (
              <button
                key={tab.key}
                onClick={() => setSelectedFilter(tab.key)}
                className={`${
                  selectedFilter === tab.key
                    ? 'border-gray-500 text-gray-600'
                    : 'border-transparent text-gray-400 hover:text-gray-600 hover:border-gray-300'
                } whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm`}
              >
                {tab.name}
                {tab.count > 0 && (
                  <span className={`ml-2 py-0.5 px-2 rounded-full text-xs ${
                    selectedFilter === tab.key ? 'bg-gray-100 text-gray-600' : 'bg-gray-50 text-gray-500'
                  }`}>
                    {tab.count}
                  </span>
                )}
              </button>
            ))}
          </nav>
        </div>

        {/* Tasks List */}
        {loading ? (
          <LoadingSpinner />
        ) : error ? (
          <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
            <ExclamationCircleIcon className="mx-auto h-12 w-12 text-red-400 mb-4" />
            <h3 className="text-lg font-medium text-red-900 mb-2">Error Loading Tasks</h3>
            <p className="text-red-700 mb-4">{error}</p>
            <button
              onClick={loadMyTasks}
              className="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700"
            >
              Try Again
            </button>
          </div>
        ) : filteredTasks.length === 0 ? (
          <div className="bg-white shadow rounded-lg">
            <div className="px-6 py-8 text-center">
              <ClipboardDocumentListIcon className="mx-auto h-16 w-16 text-gray-400 mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                {selectedFilter === 'all' ? 'No tasks assigned' : `No ${selectedFilter} tasks`}
              </h3>
              <p className="text-gray-500">
                {selectedFilter === 'all' 
                  ? 'When documents are assigned to you for review or approval, they will appear here.'
                  : `You don't have any ${selectedFilter} tasks at the moment.`
                }
              </p>
            </div>
          </div>
        ) : (
          <div className="bg-white shadow rounded-lg overflow-hidden">
            <ul className="divide-y divide-gray-200">
              {filteredTasks.map((task) => (
                <li
                  key={task.id}
                  onClick={() => handleTaskClick(task)}
                  className="p-6 hover:bg-gray-50 cursor-pointer transition-colors"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-4">
                      <div className="flex-shrink-0">
                        {getTaskTypeIcon(task.task_type)}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center space-x-2">
                          <p className="text-sm font-medium text-gray-900 truncate">
                            {task.document_title}
                          </p>
                          {getPriorityBadge(task.priority)}
                        </div>
                        <p className="text-sm text-gray-500">
                          {task.document_number} • {task.task_type.toUpperCase()} • By {task.author_display}
                        </p>
                        <p className="text-xs text-gray-400">
                          Assigned {new Date(task.assigned_date).toLocaleDateString()}
                          {task.due_date && ` • Due ${new Date(task.due_date).toLocaleDateString()}`}
                          {task.completed_at && (
                            <>
                              {' • '}
                              <span className="text-green-600 font-medium">
                                Completed {new Date(task.completed_at).toLocaleDateString()}
                              </span>
                            </>
                          )}
                        </p>
                        {task.completion_note && (
                          <p className="text-xs text-gray-500 mt-1">
                            <span className="font-medium">Note:</span> {task.completion_note}
                          </p>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      {getStatusIcon(task.status)}
                      <ChevronRightIcon className="h-5 w-5 text-gray-400" />
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Refresh Button */}
        <div className="mt-6 flex justify-center">
          <button
            onClick={() => {
              loadMyTasks();
              loadCompletedTasks();
            }}
            disabled={loading}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center space-x-2"
          >
            <ClockIcon className="h-4 w-4" />
            <span>{loading ? 'Refreshing...' : 'Refresh Tasks'}</span>
          </button>
        </div>
      </div>
    </Layout>
  );
};

export default MyTasksStandalone;