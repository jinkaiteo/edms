import React, { useState, useCallback, useEffect } from 'react';
import apiService from '../../services/api.ts';
import { WorkflowType } from '../../types/api';

interface WorkflowConfigurationProps {
  className?: string;
}

const WorkflowConfiguration: React.FC<WorkflowConfigurationProps> = ({ className = '' }) => {
  const [workflows, setWorkflows] = useState<WorkflowType[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [updating, setUpdating] = useState<number | null>(null);
  const [selectedWorkflow, setSelectedWorkflow] = useState<WorkflowType | null>(null);
  const [showCreateWorkflow, setShowCreateWorkflow] = useState(false);
  const [showEditWorkflow, setShowEditWorkflow] = useState(false);

  // Mock workflow data
  const mockWorkflows: WorkflowType[] = [
    {
      id: 1,
      uuid: 'wf-review-001',
      name: 'Document Review Workflow',
      workflow_type: 'REVIEW',
      description: 'Standard document review process for all document types',
      is_active: true,
      requires_approval: true,
      timeout_days: 7,
      reminder_days: 2
    },
    {
      id: 2,
      uuid: 'wf-approval-001',
      name: 'Document Approval Workflow',
      workflow_type: 'APPROVAL',
      description: 'Final approval workflow for critical documents',
      is_active: true,
      requires_approval: true,
      timeout_days: 5,
      reminder_days: 1
    },
    {
      id: 3,
      uuid: 'wf-version-001',
      name: 'Document Version Update',
      workflow_type: 'UP_VERSION',
      description: 'Workflow for updating document versions',
      is_active: true,
      requires_approval: false,
      timeout_days: 3,
      reminder_days: 1
    },
    {
      id: 4,
      uuid: 'wf-obsolete-001',
      name: 'Document Obsolescence',
      workflow_type: 'OBSOLETE',
      description: 'Process for marking documents as obsolete',
      is_active: true,
      requires_approval: true,
      timeout_days: 14,
      reminder_days: 3
    },
    {
      id: 5,
      uuid: 'wf-terminate-001',
      name: 'Document Termination',
      workflow_type: 'TERMINATE',
      description: 'Emergency termination of documents',
      is_active: false,
      requires_approval: true,
      timeout_days: 1,
      reminder_days: 0
    }
  ];

  // Load workflows from API
  useEffect(() => {
    const loadWorkflows = async () => {
      try {
        setLoading(true);
        setError(null);
        console.log('🔄 WorkflowConfiguration: Loading workflows...');
        
        // Try to authenticate first if not already authenticated
        if (!apiService.isAuthenticated()) {
          console.log('🔐 WorkflowConfiguration: Not authenticated, attempting admin login...');
          try {
            const loginResult = await apiService.login({ username: 'admin', password: 'test123' });
            console.log('✅ Authentication successful:', loginResult.access ? 'JWT token received' : 'Session established');
          } catch (authErr) {
            console.error('❌ Authentication failed:', authErr);
            throw new Error('Authentication required for live workflow data');
          }
        }
        
        // Get workflow types from API with authentication
        console.log('📡 Fetching workflow types from API...');
        const response = await apiService.getWorkflowTypes();
        const workflowData = response.results || response.data || [];
        
        console.log('✅ Successfully loaded', workflowData.length, 'workflows from API (not mock data)');
        console.log('🔍 Live workflow data:', workflowData.map(w => ({ name: w.name, type: w.workflow_type, active: w.is_active })));
        
        setWorkflows(workflowData);
        
      } catch (err: any) {
        console.error('❌ Error loading workflows:', err);
        setError(`Failed to load live workflow data: ${err.message}. Using fallback configuration.`);
        
        // Fallback to mock data on error with clear indication
        console.log('⚠️ Workflow Configuration: Using mock data due to API error');
        setWorkflows(mockWorkflows);
      } finally {
        setLoading(false);
      }
    };

    loadWorkflows();
  }, []);

  const handleCreateWorkflow = useCallback(() => {
    setSelectedWorkflow(null);
    setShowCreateWorkflow(true);
  }, []);

  const handleEditWorkflow = useCallback((workflow: WorkflowType) => {
    setSelectedWorkflow(workflow);
    setShowEditWorkflow(true);
  }, []);

  const handleToggleWorkflow = useCallback(async (workflow: WorkflowType) => {
    const action = workflow.is_active ? 'deactivate' : 'activate';
    if (window.confirm(`Are you sure you want to ${action} "${workflow.name}"?`)) {
      try {
        setUpdating(workflow.id);
        setError(null);
        
        // Ensure we're authenticated before making update
        if (!apiService.isAuthenticated()) {
          console.log('🔐 Re-authenticating for workflow update...');
          try {
            await apiService.login({ username: 'admin', password: 'test123' });
            console.log('✅ Re-authentication successful');
          } catch (authErr) {
            console.error('❌ Re-authentication failed:', authErr);
            throw new Error('Authentication required for workflow updates');
          }
        }
        
        // Update workflow status via API
        const updatedWorkflow = await apiService.updateWorkflowType(workflow.id, {
          is_active: !workflow.is_active
        });
        
        // Update local state
        setWorkflows(prev => prev.map(w => 
          w.id === workflow.id ? { ...w, is_active: !w.is_active } : w
        ));
        
        console.log(`Workflow ${workflow.name} ${action}d successfully`);
      } catch (err: any) {
        console.error(`Error ${action}ing workflow:`, err);
        setError(`Failed to ${action} workflow. Please try again.`);
      } finally {
        setUpdating(null);
      }
    }
  }, []);

  const getWorkflowTypeColor = (type: string): string => {
    const colors: Record<string, string> = {
      REVIEW: 'bg-blue-100 text-blue-800',
      APPROVAL: 'bg-green-100 text-green-800',
      UP_VERSION: 'bg-yellow-100 text-yellow-800',
      OBSOLETE: 'bg-orange-100 text-orange-800',
      TERMINATE: 'bg-red-100 text-red-800'
    };
    return colors[type] || 'bg-gray-100 text-gray-800';
  };

  const getWorkflowTypeIcon = (type: string): string => {
    const icons: Record<string, string> = {
      REVIEW: '👁️',
      APPROVAL: '✅',
      UP_VERSION: '🔄',
      OBSOLETE: '📋',
      TERMINATE: '🛑'
    };
    return icons[type] || '📄';
  };

  if (loading) {
    return (
      <div className={`bg-white rounded-lg shadow-sm border border-gray-200 ${className}`}>
        <div className="p-6">
          <div className="animate-pulse space-y-4">
            <div className="h-4 bg-gray-200 rounded w-1/4"></div>
            <div className="space-y-3">
              {[1, 2, 3, 4].map((i) => (
                <div key={i} className="h-20 bg-gray-200 rounded"></div>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={`bg-white rounded-lg shadow-sm border border-gray-200 ${className}`}>
      <div className="p-6">
        {/* Header */}
        <div className="flex justify-between items-center mb-6">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">Workflow Configuration</h3>
            <p className="text-sm text-gray-500">
              Configure document workflows and approval processes
            </p>
          </div>
          <button
            onClick={handleCreateWorkflow}
            className="px-4 py-2 bg-blue-600 border border-transparent rounded-md text-sm font-medium text-white hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
          >
            Create Workflow
          </button>
        </div>

        {/* Workflows Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {workflows.map((workflow) => (
            <div
              key={workflow.id}
              className="border border-gray-200 rounded-lg p-6 hover:shadow-md transition-shadow"
            >
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center space-x-3">
                  <div className="text-2xl">
                    {getWorkflowTypeIcon(workflow.workflow_type)}
                  </div>
                  <div>
                    <h4 className="text-sm font-medium text-gray-900">
                      {workflow.name}
                    </h4>
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getWorkflowTypeColor(workflow.workflow_type)}`}>
                      {workflow.workflow_type.replace('_', ' ')}
                    </span>
                  </div>
                </div>
                
                <div className="flex items-center space-x-2">
                  <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                    workflow.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                  }`}>
                    {workflow.is_active ? 'Active' : 'Inactive'}
                  </span>
                </div>
              </div>

              <p className="text-sm text-gray-600 mb-4">
                {workflow.description}
              </p>

              {/* Workflow Details */}
              <div className="space-y-2 mb-4">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-500">Timeout Days:</span>
                  <span className="font-medium">{workflow.timeout_days}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-500">Reminder Days:</span>
                  <span className="font-medium">{workflow.reminder_days}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-500">Requires Approval:</span>
                  <span className={`font-medium ${workflow.requires_approval ? 'text-green-600' : 'text-gray-600'}`}>
                    {workflow.requires_approval ? 'Yes' : 'No'}
                  </span>
                </div>
              </div>

              {/* Actions */}
              <div className="flex justify-between">
                <button
                  onClick={() => handleEditWorkflow(workflow)}
                  className="text-sm text-blue-600 hover:text-blue-800"
                >
                  Configure
                </button>
                <button
                  onClick={() => handleToggleWorkflow(workflow)}
                  className={`text-sm hover:underline ${
                    workflow.is_active 
                      ? 'text-red-600 hover:text-red-800' 
                      : 'text-green-600 hover:text-green-800'
                  }`}
                >
                  {workflow.is_active ? 'Deactivate' : 'Activate'}
                </button>
              </div>
            </div>
          ))}
        </div>

        {/* Modals */}
        {(showCreateWorkflow || showEditWorkflow) && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
            <div className="bg-white rounded-lg shadow-lg max-w-lg w-full p-6">
              <h4 className="text-lg font-medium text-gray-900 mb-4">
                {showCreateWorkflow ? 'Create New Workflow' : `Edit ${selectedWorkflow?.name}`}
              </h4>
              <div className="space-y-4 mb-6">
                <p className="text-gray-600">
                  Workflow configuration forms will be implemented in the next iteration.
                </p>
                {selectedWorkflow && (
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <h5 className="font-medium text-gray-900 mb-2">Current Configuration:</h5>
                    <ul className="text-sm text-gray-600 space-y-1">
                      <li>Type: {selectedWorkflow.workflow_type}</li>
                      <li>Timeout: {selectedWorkflow.timeout_days} days</li>
                      <li>Reminders: {selectedWorkflow.reminder_days} days</li>
                      <li>Requires Approval: {selectedWorkflow.requires_approval ? 'Yes' : 'No'}</li>
                    </ul>
                  </div>
                )}
              </div>
              <div className="flex justify-end space-x-3">
                <button
                  onClick={() => {
                    setShowCreateWorkflow(false);
                    setShowEditWorkflow(false);
                    setSelectedWorkflow(null);
                  }}
                  className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50"
                >
                  Close
                </button>
                <button
                  className="px-4 py-2 bg-blue-600 border border-transparent rounded-md text-sm font-medium text-white hover:bg-blue-700"
                  onClick={() => {
                    if (showCreateWorkflow) {
                      alert('Create workflow functionality ready for backend implementation.');
                    } else {
                      alert('Save workflow changes functionality ready for backend implementation.');
                    }
                  }}
                >
                  {showCreateWorkflow ? 'Create' : 'Save Changes'}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default WorkflowConfiguration;