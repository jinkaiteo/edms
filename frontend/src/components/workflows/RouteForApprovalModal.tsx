/**
 * Route for Approval Modal Component
 * 
 * Allows document authors to select an approver and route reviewed documents for approval.
 * Used after review completion (status: REVIEW_COMPLETED/REVIEWED).
 */

import React, { useState, useEffect } from 'react';
import { apiService } from '../../services/api.ts';
import { 
  XMarkIcon,
  CheckCircleIcon,
  UserIcon,
  ClockIcon
} from '@heroicons/react/24/outline';

interface Document {
  uuid: string;
  document_number: string;
  title: string;
  status: string;
  author_display: string;
  reviewer_display: string;
}

interface Approver {
  id: string;
  username: string;
  full_name: string;
  email: string;
}

interface RouteForApprovalModalProps {
  isOpen: boolean;
  onClose: () => void;
  document: Document;
  onApprovalRouted: () => void;
}

const RouteForApprovalModal: React.FC<RouteForApprovalModalProps> = ({
  isOpen,
  onClose,
  document,
  onApprovalRouted
}) => {
  const [selectedApprover, setSelectedApprover] = useState<string>('');
  const [approvers, setApprovers] = useState<Approver[]>([]);
  const [routingComment, setRoutingComment] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen) {
      loadApprovers();
    }
  }, [isOpen]);

  const loadApprovers = async () => {
    try {
      setError(null);
      
      // Load users with approval permissions
      try {
        const response = await apiService.get('/users/users/', {
          params: {
            role: 'approver',
            permissions: 'approve_document'
          }
        });
        setApprovers(Array.isArray(response) ? response : response.results || []);
      } catch (apiError) {
        // Fallback to test approvers if API not available
        const testApprovers = [
          { id: 'approver', username: 'approver', full_name: 'Document Approver', email: 'approver@edms.com' },
          { id: 'admin', username: 'admin', full_name: 'System Administrator', email: 'admin@edms.com' }
        ];
        setApprovers(testApprovers);
      }
    } catch (error: any) {
      console.error('Error loading approvers:', error);
      setError('Failed to load approvers. Please try again.');
    }
  };

  const handleRouteForApproval = async () => {
    try {
      if (!selectedApprover || !selectedApprover.trim()) {
        setError('Please select an approver');
        return;
      }


      setLoading(true);
      setError(null);

      // Find the selected approver object to get the ID
      const selectedApproverObj = approvers.find(approver => approver.username === selectedApprover);
      if (!selectedApproverObj) {
        setError('Selected approver not found');
        return;
      }

      // Execute workflow action - the backend will handle approver assignment
      const workflowResponse = await apiService.post(`/documents/documents/${document.uuid}/workflow/`, {
        action: 'route_for_approval',
        approver_id: selectedApproverObj.id,
        comment: routingComment || 'Document routed for approval'
      });

      // Success - workflow action completed
      onApprovalRouted();
      onClose();

    } catch (workflowError: any) {
      console.error('❌ WORKFLOW: Failed to route for approval - full error:', workflowError);
      setError('Failed to route document for approval. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    if (!loading) {
      setSelectedApprover('');
      setRoutingComment('');
      setError(null);
      onClose();
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-gray-500 bg-opacity-75 flex items-center justify-center">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4">
        <div className="px-6 py-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <CheckCircleIcon className="h-6 w-6 text-green-600" />
              <h3 className="text-lg font-medium text-gray-900">
                Route for Approval
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
          <div className="mb-6 p-4 bg-gray-50 rounded-lg">
            <h4 className="font-medium text-gray-900 mb-2">Document Information</h4>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-gray-500">Document:</span>
                <p className="font-medium">{document.document_number}</p>
              </div>
              <div>
                <span className="text-gray-500">Title:</span>
                <p className="font-medium">{document.title}</p>
              </div>
              <div>
                <span className="text-gray-500">Author:</span>
                <p>{document.author_display}</p>
              </div>
              <div>
                <span className="text-gray-500">Reviewer:</span>
                <p>{document.reviewer_display}</p>
              </div>
              <div>
                <span className="text-gray-500">Status:</span>
                <p className="font-medium text-blue-600">{document.status}</p>
              </div>
            </div>
          </div>

          {/* Error Display */}
          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md">
              <p className="text-sm text-red-700">{error}</p>
            </div>
          )}

          {/* Approver Selection */}
          <div className="mb-6">
            <label htmlFor="approver" className="block text-sm font-medium text-gray-700 mb-2">
              Select Approver <span className="text-red-500">*</span>
            </label>
            <div className="relative">
              <UserIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
              <select
                id="approver"
                value={selectedApprover}
                onChange={(e) => setSelectedApprover(e.target.value)}
                disabled={loading}
                className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-green-500 focus:border-green-500 disabled:opacity-50"
                required
              >
                <option value="">Select an approver...</option>
                {approvers.map((approver) => (
                  <option key={approver.id} value={approver.username}>
                    {approver.full_name} ({approver.username})
                  </option>
                ))}
              </select>
            </div>
            {approvers.length === 0 && (
              <p className="mt-2 text-sm text-amber-600">
                Loading available approvers...
              </p>
            )}
          </div>

          {/* Routing Comment */}
          <div className="mb-6">
            <label htmlFor="routingComment" className="block text-sm font-medium text-gray-700 mb-2">
              Routing Comments
            </label>
            <textarea
              id="routingComment"
              value={routingComment}
              onChange={(e) => setRoutingComment(e.target.value)}
              disabled={loading}
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-green-500 focus:border-green-500 disabled:opacity-50"
              placeholder="Add any comments for the approver about this approval request..."
            />
          </div>

          {/* Process Info */}
          <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg">
            <div className="flex items-start space-x-3">
              <CheckCircleIcon className="h-5 w-5 text-green-600 mt-0.5" />
              <div>
                <h4 className="font-medium text-green-900">Next Steps</h4>
                <p className="text-sm text-green-700 mt-1">
                  After routing, the document will be moved to <strong>PENDING_APPROVAL</strong> status 
                  and the selected approver will be notified. They will be able to review, approve, or 
                  reject the document.
                </p>
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
            onClick={handleRouteForApproval}
            disabled={loading || !selectedApprover.trim()}
            className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50 flex items-center space-x-2"
          >
            {loading && <ClockIcon className="h-4 w-4 animate-spin" />}
            <span>{loading ? 'Routing...' : 'Route for Approval'}</span>
          </button>
        </div>
      </div>
    </div>
  );
};

export default RouteForApprovalModal;