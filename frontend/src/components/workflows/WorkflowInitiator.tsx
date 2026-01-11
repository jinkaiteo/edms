/**
 * WorkflowInitiator Component
 * 
 * Enhanced document creation form with reviewer/approver selection.
 * Integrates with UserSelector for manual assignment capabilities.
 */

import React, { useState, useEffect } from 'react';
import { DocumentTextIcon, ClockIcon, UserGroupIcon } from '@heroicons/react/24/outline';
import UserSelector from './UserSelector';

interface User {
  id: number;
  username: string;
  first_name: string;
  last_name: string;
  email: string;
  workload_status: 'low' | 'normal' | 'high';
  is_available: boolean;
}

interface DocumentType {
  id: number;
  code: string;
  name: string;
  description: string;
}

interface WorkflowInitiatorProps {
  documentId?: number;
  onWorkflowCreated: (workflowId: number) => void;
  onCancel?: () => void;
}

const WorkflowInitiator: React.FC<WorkflowInitiatorProps> = ({
  documentId,
  onWorkflowCreated,
  onCancel
}) => {
  const [formData, setFormData] = useState({
    document_id: documentId || 0,
    reviewer_id: null as number | null,
    approver_id: null as number | null,
    review_due_date: '',
    approval_due_date: '',
    comment: '',
    criticality: 'normal',
    workflow_type: 'review'
  });

  const [selectedReviewer, setSelectedReviewer] = useState<User | null>(null);
  const [selectedApprover, setSelectedApprover] = useState<User | null>(null);
  const [documentTypes, setDocumentTypes] = useState<DocumentType[]>([]);
  const [selectedDocumentType, setSelectedDocumentType] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    // Fetch document types for user selection context
    fetchDocumentTypes();
    
    // Set default due dates
    const reviewDate = new Date();
    reviewDate.setDate(reviewDate.getDate() + 5); // Default 5 days for review
    
    const approvalDate = new Date();
    approvalDate.setDate(approvalDate.getDate() + 8); // Default 8 days for approval
    
    setFormData(prev => ({
      ...prev,
      review_due_date: reviewDate.toISOString().split('T')[0],
      approval_due_date: approvalDate.toISOString().split('T')[0]
    }));
  }, []);

  const fetchDocumentTypes = async () => {
    try {
      const response = await fetch('/api/v1/document-types/', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json',
        },
      });
      if (response.ok) {
        const data = await response.json();
        setDocumentTypes(data.results || []);
      }
    } catch (error) {
      console.error('Error fetching document types:', error);
    }
  };

  const handleInputChange = (field: string, value: string | number) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
    
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({
        ...prev,
        [field]: ''
      }));
    }
  };

  const handleReviewerSelect = (user: User | null) => {
    setSelectedReviewer(user);
    setFormData(prev => ({
      ...prev,
      reviewer_id: user?.id || null
    }));
  };

  const handleApproverSelect = (user: User | null) => {
    setSelectedApprover(user);
    setFormData(prev => ({
      ...prev,
      approver_id: user?.id || null
    }));
  };

  const validateForm = () => {
    const newErrors: Record<string, string> = {};

    if (!formData.document_id) {
      newErrors.document_id = 'Document ID is required';
    }

    if (!formData.reviewer_id) {
      newErrors.reviewer_id = 'Please select a reviewer';
    }

    if (!formData.approver_id) {
      newErrors.approver_id = 'Please select an approver';
    }

    if (formData.reviewer_id === formData.approver_id) {
      newErrors.approver_id = 'Reviewer and approver must be different users';
    }

    if (!formData.review_due_date) {
      newErrors.review_due_date = 'Review due date is required';
    }

    if (!formData.approval_due_date) {
      newErrors.approval_due_date = 'Approval due date is required';
    }

    // Check that approval due date is after review due date
    if (formData.review_due_date && formData.approval_due_date) {
      if (new Date(formData.approval_due_date) <= new Date(formData.review_due_date)) {
        newErrors.approval_due_date = 'Approval due date must be after review due date';
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    setLoading(true);
    try {
      const response = await fetch('/api/v1/workflows/create_with_assignments/', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });

      if (response.ok) {
        const data = await response.json();
        onWorkflowCreated(data.workflow.id);
      } else {
        const errorData = await response.json();
        setErrors({ submit: errorData.error || 'Failed to create workflow' });
      }
    } catch (error) {
      setErrors({ submit: 'Network error occurred' });
    } finally {
      setLoading(false);
    }
  };

  const getCriticalityIcon = (criticality: string) => {
    switch (criticality) {
      case 'high':
        return '🔴';
      case 'low':
        return '🟢';
      default:
        return '🟡';
    }
  };

  return (
    <div className="max-w-2xl mx-auto bg-white shadow-lg rounded-lg">
      <div className="px-6 py-4 border-b border-gray-200">
        <h3 className="text-lg font-medium text-gray-900 flex items-center">
          <DocumentTextIcon className="h-6 w-6 mr-2 text-indigo-600" />
          Initiate Document Workflow
        </h3>
        <p className="mt-1 text-sm text-gray-600">
          Select reviewers and approvers to start the document approval process
        </p>
      </div>

      <form onSubmit={handleSubmit} className="p-6 space-y-6">
        {/* Document Information */}
        <div className="bg-gray-50 rounded-lg p-4">
          <h4 className="text-sm font-medium text-gray-900 mb-3">Document Information</h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Document ID
              </label>
              <input
                type="number"
                value={formData.document_id}
                onChange={(e) => handleInputChange('document_id', parseInt(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500"
                placeholder="Enter document ID"
              />
              {errors.document_id && (
                <p className="mt-1 text-sm text-red-600">{errors.document_id}</p>
              )}
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Document Type
              </label>
              <select
                value={selectedDocumentType}
                onChange={(e) => setSelectedDocumentType(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500"
              >
                <option value="">Select document type...</option>
                {documentTypes.map((type) => (
                  <option key={type.id} value={type.code}>
                    {type.name}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* Workflow Configuration */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Workflow Type
            </label>
            <select
              value={formData.workflow_type}
              onChange={(e) => handleInputChange('workflow_type', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500"
            >
              <option value="review">Review Workflow (30 days)</option>
              <option value="upversion">Up-version Workflow (14 days)</option>
              <option value="emergency">Emergency Workflow (3 days)</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Criticality Level
            </label>
            <select
              value={formData.criticality}
              onChange={(e) => handleInputChange('criticality', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500"
            >
              <option value="low">🟢 Low - Standard process</option>
              <option value="normal">🟡 Normal - Regular approval</option>
              <option value="high">🔴 High - Senior approval required</option>
            </select>
          </div>
        </div>

        {/* User Selection */}
        <div className="space-y-4">
          <h4 className="text-sm font-medium text-gray-900 flex items-center">
            <UserGroupIcon className="h-5 w-5 mr-2 text-indigo-600" />
            Assignment Selection
          </h4>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Select Reviewer *
              </label>
              <UserSelector
                type="reviewer"
                selectedUserId={formData.reviewer_id || undefined}
                onSelect={handleReviewerSelect}
                documentType={selectedDocumentType}
                placeholder="Choose a reviewer..."
              />
              {errors.reviewer_id && (
                <p className="mt-1 text-sm text-red-600">{errors.reviewer_id}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Select Approver *
              </label>
              <UserSelector
                type="approver"
                selectedUserId={formData.approver_id || undefined}
                onSelect={handleApproverSelect}
                criticality={formData.criticality}
                placeholder="Choose an approver..."
              />
              {errors.approver_id && (
                <p className="mt-1 text-sm text-red-600">{errors.approver_id}</p>
              )}
            </div>
          </div>
        </div>

        {/* Timeline */}
        <div className="space-y-4">
          <h4 className="text-sm font-medium text-gray-900 flex items-center">
            <ClockIcon className="h-5 w-5 mr-2 text-indigo-600" />
            Timeline Configuration
          </h4>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Review Due Date *
              </label>
              <input
                type="date"
                value={formData.review_due_date}
                onChange={(e) => handleInputChange('review_due_date', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500"
                min={new Date().toISOString().split('T')[0]}
              />
              {errors.review_due_date && (
                <p className="mt-1 text-sm text-red-600">{errors.review_due_date}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Approval Due Date *
              </label>
              <input
                type="date"
                value={formData.approval_due_date}
                onChange={(e) => handleInputChange('approval_due_date', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500"
                min={formData.review_due_date || new Date().toISOString().split('T')[0]}
              />
              {errors.approval_due_date && (
                <p className="mt-1 text-sm text-red-600">{errors.approval_due_date}</p>
              )}
            </div>
          </div>
        </div>

        {/* Comments */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Assignment Comments
          </label>
          <textarea
            value={formData.comment}
            onChange={(e) => handleInputChange('comment', e.target.value)}
            rows={3}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500"
            placeholder="Add any specific instructions or context for the reviewers/approvers..."
          />
        </div>

        {/* Assignment Summary */}
        {(selectedReviewer || selectedApprover) && (
          <div className="bg-blue-50 rounded-lg p-4">
            <h4 className="text-sm font-medium text-blue-900 mb-2">Assignment Summary</h4>
            <div className="space-y-2 text-sm text-blue-800">
              {selectedReviewer && (
                <div className="flex justify-between">
                  <span>👀 Reviewer:</span>
                  <span className="font-medium">
                    {selectedReviewer.first_name && selectedReviewer.last_name
                      ? `${selectedReviewer.first_name} ${selectedReviewer.last_name}`
                      : selectedReviewer.username
                    } ({selectedReviewer.workload_status} workload)
                  </span>
                </div>
              )}
              {selectedApprover && (
                <div className="flex justify-between">
                  <span>✅ Approver:</span>
                  <span className="font-medium">
                    {selectedApprover.first_name && selectedApprover.last_name
                      ? `${selectedApprover.first_name} ${selectedApprover.last_name}`
                      : selectedApprover.username
                    } ({selectedApprover.workload_status} workload)
                  </span>
                </div>
              )}
              {formData.review_due_date && (
                <div className="flex justify-between">
                  <span>📅 Review Due:</span>
                  <span className="font-medium">{formData.review_due_date}</span>
                </div>
              )}
              {formData.approval_due_date && (
                <div className="flex justify-between">
                  <span>📅 Approval Due:</span>
                  <span className="font-medium">{formData.approval_due_date}</span>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Error Display */}
        {errors.submit && (
          <div className="bg-red-50 border border-red-200 rounded-md p-3">
            <p className="text-sm text-red-600">{errors.submit}</p>
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex justify-end space-x-3 pt-4 border-t border-gray-200">
          {onCancel && (
            <button
              type="button"
              onClick={onCancel}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
            >
              Cancel
            </button>
          )}
          <button
            type="submit"
            disabled={loading}
            className="px-6 py-2 text-sm font-medium text-white bg-indigo-600 border border-transparent rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:bg-indigo-400 disabled:cursor-not-allowed"
          >
            {loading ? (
              <>
                <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white inline" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Creating Workflow...
              </>
            ) : (
              'Start Workflow'
            )}
          </button>
        </div>
      </form>
    </div>
  );
};

export default WorkflowInitiator;