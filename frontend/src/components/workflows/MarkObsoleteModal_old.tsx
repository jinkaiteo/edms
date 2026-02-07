/**
 * Mark Obsolete Modal Component
 * 
 * Allows users to initiate obsolescence workflow for effective documents.
 * Checks for dependencies and starts the obsolescence process.
 */

import React, { useState, useEffect } from 'react';
import { apiService } from '../../services/api.ts';
import { 
  XMarkIcon,
  TrashIcon,
  ClockIcon,
  InformationCircleIcon,
  ExclamationTriangleIcon,
  ExclamationCircleIcon
} from '@heroicons/react/24/outline';

interface Document {
  uuid: string;
  document_number: string;
  title: string;
  status: string;
  version_string: string;
  author_display: string;
  effective_date: string;
  approver_id?: number;
  approver_display?: string;
}

interface Approver {
  id: number;
  username: string;
  first_name: string;
  last_name: string;
  email: string;
  display_name: string;
}

interface DocumentDependency {
  id: string;
  document_number: string;
  document_title: string;
  dependency_type: string;
  is_critical: boolean;
}

interface MarkObsoleteModalProps {
  isOpen: boolean;
  onClose: () => void;
  document: Document;
  onObsolescenceInitiated: () => void;
}

const MarkObsoleteModal: React.FC<MarkObsoleteModalProps> = ({
  isOpen,
  onClose,
  document,
  onObsolescenceInitiated
}) => {
  const [reasonForObsolescence, setReasonForObsolescence] = useState<string>('');
  const [obsolescenceDate, setObsolescenceDate] = useState<string>('');
  const [dependencies, setDependencies] = useState<DocumentDependency[]>([]);
  const [loading, setLoading] = useState(false);
  const [checkingDependencies, setCheckingDependencies] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [dependencyError, setDependencyError] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen) {
      checkDocumentDependencies();
    }
  }, [isOpen, document.uuid, document.approver_id]);

  const fetchAvailableApprovers = async () => {
    setLoadingApprovers(true);
    try {
      // Call the actual users endpoint
      const response = await apiService.get('/users/users/');
      console.log('🔍 Users API Response:', response); // Debug log
      
      let users = [];
      
      // Parse the API response structure
      if (response.results && Array.isArray(response.results)) {
        users = response.results; // DRF pagination structure
      } else if (response.users && Array.isArray(response.users)) {
        users = response.users; // Alternative structure
      } else if (response.data && Array.isArray(response.data)) {
        users = response.data; // Another fallback
      } else if (Array.isArray(response)) {
        users = response; // Direct array
      }
      
      console.log('🔍 API Response structure:', typeof response, Object.keys(response || {}));
      console.log('🔍 Users type:', typeof users, 'isArray:', Array.isArray(users));
      console.log('🔍 Found users:', users.length || 0, 'users'); // Debug log
      
      // Ensure users is an array before filtering
      if (!Array.isArray(users)) {
        console.error('🔍 Users is not an array:', users);
        users = []; // Fallback to empty array
      }
      
      // Filter for users who can approve - look for various indicators
      const approvers = users.filter((user: any) => {
        // Check multiple criteria for approver capability
        const hasApproverUsername = user.username && (
          user.username.includes('approver') ||
          user.username.includes('admin')
        );
        
        const hasApproverRole = user.roles && Array.isArray(user.roles) && 
          user.roles.some((role: any) => role.name === 'Approver' || role.name === 'approver');
        
        const hasApproverGroup = user.groups && Array.isArray(user.groups) && 
          user.groups.some((group: any) => 
            (typeof group === 'string' && group.toLowerCase().includes('approver')) ||
            (typeof group === 'object' && group.name && group.name.toLowerCase().includes('approver'))
          );
        
        const canApprove = user.is_staff || 
                          user.is_superuser ||
                          hasApproverUsername ||
                          hasApproverRole ||
                          hasApproverGroup;
                          
        console.log(`🔍 User ${user.username}: staff=${user.is_staff}, super=${user.is_superuser}, roles=${JSON.stringify(user.roles)}, groups=${JSON.stringify(user.groups)}, canApprove=${canApprove}`);
        return canApprove;
      });
      
      console.log('🔍 Filtered approvers:', approvers.length, 'approvers');
      
      setAvailableApprovers(approvers.map((user: any) => ({
        id: user.id,
        username: user.username,
        first_name: user.first_name || '',
        last_name: user.last_name || '',
        email: user.email || '',
        display_name: user.display_name || `${user.first_name} ${user.last_name}`.trim() || user.username
      })));
      
    } catch (error) {
      console.error('Failed to fetch approvers:', error);
      // Set current approver as only option if API fails
      if (document.approver_display && document.approver_id) {
        setAvailableApprovers([{
          id: document.approver_id,
          username: '',
          first_name: '',
          last_name: '',
          email: '',
          display_name: document.approver_display
        }]);
      }
    } finally {
      setLoadingApprovers(false);
    }
  };

  const checkDocumentDependencies = async () => {
    try {
      setCheckingDependencies(true);
      setDependencyError(null);
      

      // Check for documents that depend on this document
      const dependencyResponse = await apiService.get(`/documents/documents/${document.uuid}/dependencies/`);
      
      const dependentDocs = Array.isArray(dependencyResponse) ? dependencyResponse : dependencyResponse.dependents || [];
      setDependencies(dependentDocs);

      if (dependentDocs.length > 0) {
        setDependencyError(
          `Cannot mark document obsolete: ${dependentDocs.length} document(s) depend on this document. ` +
          `Remove or update the dependencies first.`
        );
      }

    } catch (error: any) {
      console.error('Error checking dependencies:', error);
      // If dependency check fails, allow the obsolescence but warn user
      setDependencyError('Unable to verify dependencies. Proceed with caution.');
    } finally {
      setCheckingDependencies(false);
    }
  };

  const handleMarkObsolete = async () => {
    try {
      if (!reasonForObsolescence.trim()) {
        setError('Please provide a reason for marking the document obsolete');
        return;
      }
      
      if (!obsolescenceDate) {
        setError('Obsolescence date is required');
        return;
      }
      
      // Validate that obsolescence date is in the future
      const selectedDate = new Date(obsolescenceDate);
      const today = new Date();
      today.setHours(0, 0, 0, 0);
      
      if (selectedDate <= today) {
        setError('Obsolescence date must be in the future');
        return;
      }

      if (dependencies.length > 0) {
        setError('Cannot proceed: Document has dependencies that must be resolved first');
        return;
      }


      setLoading(true);
      setError(null);

      // Initiate obsolescence workflow
      const workflowData = {
        action: 'obsolete_document_directly',
        reason: reasonForObsolescence,
        obsolescence_date: obsolescenceDate, // Required field
      };

      const workflowResponse = await apiService.post(`/workflows/documents/${document.uuid}/`, workflowData);


      onObsolescenceInitiated();
      onClose();

    } catch (workflowError: any) {
      console.error('❌ WORKFLOW: Failed to initiate obsolescence - full error:', workflowError);
      
      if (workflowError.response?.status === 400) {
        setError(workflowError.response?.data?.detail || 'Cannot mark document obsolete. Please check for dependencies.');
      } else if (workflowError.response?.status === 403) {
        setError('You do not have permission to mark this document obsolete.');
      } else {
        setError('Failed to initiate obsolescence. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    if (!loading) {
      setReasonForObsolescence('');
      setObsolescenceDate('');
      setError(null);
      setDependencyError(null);
      onClose();
    }
  };

  if (!isOpen) return null;

  const hasDependencies = dependencies.length > 0;
  const canProceed = !hasDependencies && !checkingDependencies && reasonForObsolescence.trim().length > 0 && obsolescenceDate.length > 0;

  return (
    <div className="fixed inset-0 overflow-y-auto" style={{ zIndex: 60 }} bg-gray-500 bg-opacity-75 flex items-center justify-center">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4">
        <div className="px-6 py-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <TrashIcon className="h-6 w-6 text-red-600" />
              <h3 className="text-lg font-medium text-gray-900">
                Mark Document Obsolete
              </h3>
            </div>
            <button
              onClick={handleClose}
              disabled={loading}
              className="text-gray-400 hover:text-gray-500 disabled:opacity-50"
            >
              <XMarkIcon className="h-6 w-6" />
            </button>
          </div>
        </div>

        <div className="px-6 py-4">
          {/* Document Info */}
          <div className="mb-6 p-4 bg-gray-50 border border-gray-200 rounded-lg">
            <h4 className="font-medium text-gray-900 mb-2">Document to Mark Obsolete</h4>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-gray-500">Document:</span>
                <p className="font-medium">{document.document_number}</p>
              </div>
              <div>
                <span className="text-gray-500">Version:</span>
                <p className="font-medium">{document.version_string}</p>
              </div>
              <div>
                <span className="text-gray-500">Author:</span>
                <p>{document.author_display}</p>
              </div>
              <div>
                <span className="text-gray-500">Effective Since:</span>
                <p>{new Date(document.effective_date).toLocaleDateString()}</p>
              </div>
            </div>
            <div className="mt-3">
              <span className="text-gray-500">Title:</span>
              <p className="font-medium">{document.title}</p>
            </div>
          </div>

          {/* Dependency Check Results */}
          {checkingDependencies ? (
            <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
              <div className="flex items-center space-x-3">
                <ClockIcon className="h-5 w-5 text-blue-600 animate-spin" />
                <p className="text-blue-800">Checking for document dependencies...</p>
              </div>
            </div>
          ) : dependencyError ? (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
              <div className="flex items-start space-x-3">
                <ExclamationCircleIcon className="h-5 w-5 text-red-600 mt-0.5" />
                <div>
                  <h4 className="font-medium text-red-900">Dependency Error</h4>
                  <p className="text-red-700 mt-1">{dependencyError}</p>
                </div>
              </div>
            </div>
          ) : hasDependencies ? (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
              <div className="flex items-start space-x-3">
                <ExclamationCircleIcon className="h-5 w-5 text-red-600 mt-0.5" />
                <div>
                  <h4 className="font-medium text-red-900">Cannot Mark Obsolete</h4>
                  <p className="text-red-700 mt-1 mb-3">
                    This document has {dependencies.length} dependent document(s). 
                    Remove or update these dependencies before marking obsolete:
                  </p>
                  <ul className="list-disc list-inside text-red-700 text-sm space-y-1">
                    {dependencies.map((dep) => (
                      <li key={dep.id}>
                        <strong>{dep.document_number}</strong> - {dep.document_title} 
                        {dep.is_critical && <span className="text-red-800 font-medium"> (Critical)</span>}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          ) : (
            <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg">
              <div className="flex items-center space-x-3">
                <InformationCircleIcon className="h-5 w-5 text-green-600" />
                <p className="text-green-800">No dependencies found. Document can be marked obsolete.</p>
              </div>
            </div>
          )}

          {/* Obsolescence Date - Required Field */}
          <div className="mb-6">
            <label htmlFor="obsolescenceDate" className="block text-sm font-medium text-gray-700 mb-2">
              Obsolescence Date *
              <span className="text-xs text-gray-500 ml-2">
                (Document will become obsolete on this date)
              </span>
            </label>
            <input
              type="date"
              id="obsolescenceDate"
              value={obsolescenceDate}
              onChange={(e) => setObsolescenceDate(e.target.value)}
              min={new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString().split('T')[0]} // Tomorrow
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            />
            <p className="mt-1 text-xs text-gray-500">
              Select a future date when this document will become obsolete. 
              All stakeholders will be notified immediately and on the obsolescence date.
            </p>
          </div>

          {/* Error Display */}
          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md">
              <div className="flex items-center space-x-2">
                <ExclamationTriangleIcon className="h-5 w-5 text-red-400" />
                <p className="text-sm text-red-700">{error}</p>
              </div>
            </div>
          )}


          {/* Reason for Obsolescence */}
          <div className="mb-6">
            <label htmlFor="reasonForObsolescence" className="block text-sm font-medium text-gray-700 mb-2">
              Reason for Obsolescence <span className="text-red-500">*</span>
            </label>
            <textarea
              id="reasonForObsolescence"
              value={reasonForObsolescence}
              onChange={(e) => setReasonForObsolescence(e.target.value)}
              disabled={loading || hasDependencies}
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-red-500 focus:border-red-500 disabled:opacity-50"
              placeholder="Explain why this document is being marked obsolete (e.g., superseded by new procedures, no longer applicable, regulatory changes...)"
              required
            />
          </div>


          {/* Process Information */}
          <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <div className="flex items-start space-x-3">
              <InformationCircleIcon className="h-5 w-5 text-blue-600 mt-0.5" />
              <div>
                <h4 className="font-medium text-blue-900">Direct Obsolescence Process</h4>
                <div className="text-sm text-blue-700 mt-1 space-y-1">
                  <p>
                    • Document will be <strong>scheduled for obsolescence</strong> on the selected date
                  </p>
                  <p>
                    • All stakeholders will be <strong>notified immediately</strong>
                  </p>
                  <p>
                    • Document becomes <strong>OBSOLETE</strong> automatically on the obsolescence date
                  </p>
                  <p>
                    • Obsolete documents are retained for historical reference and audit trail
                  </p>
                  <p className="font-medium text-blue-800">
                    • As an authorized user, you can obsolete this document directly
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-4 bg-gray-50 border-t border-gray-200 flex justify-end space-x-3">
          <button
            onClick={handleClose}
            disabled={loading}
            className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-100 disabled:opacity-50"
          >
            Cancel
          </button>
          <button
            onClick={handleMarkObsolete}
            disabled={loading || !canProceed}
            className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 disabled:opacity-50 flex items-center space-x-2"
          >
            {loading && <ClockIcon className="h-4 w-4 animate-spin" />}
            <TrashIcon className="h-4 w-4" />
            <span>
              {loading 
                ? 'Initiating...' 
                : 'Mark Obsolete'
              }
            </span>
          </button>
        </div>
      </div>
    </div>
  );
};

export default MarkObsoleteModal;