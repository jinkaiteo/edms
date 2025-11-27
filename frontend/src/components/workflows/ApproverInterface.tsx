/**
 * Approver Interface Component
 * 
 * Provides interface for assigned approvers to review and approve/reject documents.
 * Used when document status is PENDING_APPROVAL.
 */

import React, { useState, useEffect } from 'react';
import { apiService } from '../../services/api.ts';
import { useAuth } from '../../contexts/AuthContext.tsx';
import { 
  XMarkIcon,
  CheckCircleIcon,
  XCircleIcon,
  DocumentTextIcon,
  ArrowDownTrayIcon,
  ClockIcon,
  ExclamationTriangleIcon,
  InformationCircleIcon
} from '@heroicons/react/24/outline';

interface Document {
  uuid: string;
  document_number: string;
  title: string;
  status: string;
  author_display: string;
  reviewer_display: string;
  description: string;
  file_name?: string;
  file_path?: string;
  created_at: string;
  review_date?: string;
}

interface ApproverInterfaceProps {
  isOpen: boolean;
  onClose: () => void;
  document: Document;
  onApprovalComplete: () => void;
}

const ApproverInterface: React.FC<ApproverInterfaceProps> = ({
  isOpen,
  onClose,
  document,
  onApprovalComplete
}) => {
  const [approvalDecision, setApprovalDecision] = useState<'approve' | 'reject' | ''>('');
  const [approvalComment, setApprovalComment] = useState<string>('');
  const [effectiveDate, setEffectiveDate] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Get current user from auth context
  const { user } = useAuth();

  useEffect(() => {
    if (isOpen) {
      // Set default effective date to tomorrow
      const tomorrow = new Date();
      tomorrow.setDate(tomorrow.getDate() + 1);
      setEffectiveDate(tomorrow.toISOString().split('T')[0]);
    }
  }, [isOpen]);

  const handleDownload = async (downloadType: 'original' | 'annotated') => {
    try {
      const response = await apiService.get(`/documents/documents/${document.uuid}/download/`, {
        params: { type: downloadType },
        responseType: 'blob'
      });

      // Create download link
      const blob = new Blob([response]);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `${document.document_number}_${downloadType}.pdf`;
      document.body.appendChild(link);
      link.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(link);
      
    } catch (error) {
      console.error('Download failed:', error);
      setError('Failed to download document. Please try again.');
    }
  };

  const handleApprovalSubmission = async () => {
    try {
      if (!approvalDecision) {
        setError('Please select an approval decision');
        return;
      }

      if (!approvalComment.trim()) {
        setError('Please provide approval comments');
        return;
      }


      setLoading(true);
      setError(null);

      // Submit approval comment
      console.log('🔍 Debug - Document Object:', {
        id: document.id,
        uuid: document.uuid,
        document_number: document.document_number,
        title: document.title,
        status: document.status
      });

      console.log('🔍 Debug - Approval Decision:', {
        approvalDecision,
        approvalComment: approvalComment?.substring(0, 100) + (approvalComment?.length > 100 ? '...' : ''),
        commentLength: approvalComment?.length
      });

      console.log('🔍 Debug - User Object:', {
        user: user ? {
          id: user.id,
          username: user.username,
          is_staff: user.is_staff
        } : 'User is null/undefined'
      });

      const commentData = {
        document: document.id,
        author: user?.id,
        comment_type: 'APPROVAL',  // Fixed: uppercase to match backend choices
        subject: `Approval Decision: ${approvalDecision}`,
        content: approvalComment,
        is_internal: false,
        requires_response: false
      };

      console.log('🔍 Debug - Comment Data Being Sent:', commentData);

      try {
        console.log('🔍 Debug - Sending comment creation request...');
        const commentResponse = await apiService.post(`/documents/comments/`, commentData);
        console.log('✅ Debug - Comment created successfully:', commentResponse);
      } catch (commentError: any) {
        console.error('❌ Debug - Comment creation failed:', commentError);
        console.log('🔍 Debug - Full comment error details:', {
          status: commentError?.response?.status,
          statusText: commentError?.response?.statusText,
          data: commentError?.response?.data,
          errorMessage: commentError?.message
        });
        throw commentError; // Re-throw to stop workflow execution
      }

      // Submit workflow transition
      
      try {
        // Prepare workflow request data
        const requestData: any = {
          action: approvalDecision === 'approve' ? 'approve_document' : 'reject_document',
          comment: approvalComment
        };

        // Add effective_date for approval (required for new simplified workflow)
        if (approvalDecision === 'approve') {
          if (!effectiveDate) {
            throw new Error('Effective date is required for approval');
          }
          requestData.effective_date = effectiveDate;
        }

        const workflowResponse = await apiService.post(`/documents/documents/${document.uuid}/workflow/`, requestData);
        
        
      } catch (workflowError: any) {
      }

      onApprovalComplete();
      onClose();

    } catch (error: any) {
      console.error('❌ WORKFLOW: Failed to submit approval - full error:', error);
      setError('Failed to submit approval. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    if (!loading) {
      setApprovalDecision('');
      setApprovalComment('');
      setError(null);
      onClose();
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-gray-500 bg-opacity-75 flex items-center justify-center">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        <div className="px-6 py-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <CheckCircleIcon className="h-6 w-6 text-green-600" />
              <h3 className="text-lg font-medium text-gray-900">
                Approval Process - {document.document_number}
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
          {/* Document Information */}
          <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <h4 className="font-medium text-blue-900 mb-3">Document Information</h4>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-blue-700">Document Number:</span>
                <p className="font-medium">{document.document_number}</p>
              </div>
              <div>
                <span className="text-blue-700">Title:</span>
                <p className="font-medium">{document.title}</p>
              </div>
              <div>
                <span className="text-blue-700">Author:</span>
                <p>{document.author_display}</p>
              </div>
              <div>
                <span className="text-blue-700">Reviewer:</span>
                <p>{document.reviewer_display}</p>
              </div>
              <div>
                <span className="text-blue-700">Status:</span>
                <p className="font-medium text-orange-600">{document.status}</p>
              </div>
              <div>
                <span className="text-blue-700">Submitted:</span>
                <p>{new Date(document.created_at).toLocaleDateString()}</p>
              </div>
            </div>
            {document.description && (
              <div className="mt-3">
                <span className="text-blue-700">Description:</span>
                <p className="mt-1">{document.description}</p>
              </div>
            )}
          </div>

          {/* Document Actions */}
          <div className="mb-6">
            <h4 className="font-medium text-gray-900 mb-3">Document Review</h4>
            <div className="flex space-x-3">
              <button
                onClick={() => handleDownload('original')}
                className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
              >
                <ArrowDownTrayIcon className="h-4 w-4" />
                <span>Download Original</span>
              </button>
              <button
                onClick={() => handleDownload('annotated')}
                className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
              >
                <DocumentTextIcon className="h-4 w-4" />
                <span>Download Annotated</span>
              </button>
            </div>
            <p className="text-xs text-gray-500 mt-2">
              Review the document thoroughly before making an approval decision.
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

          {/* Approval Decision */}
          <div className="mb-6">
            <h4 className="font-medium text-gray-900 mb-3">
              Approval Decision <span className="text-red-500">*</span>
            </h4>
            <div className="space-y-3">
              <label className="flex items-center space-x-3 p-3 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer">
                <input
                  type="radio"
                  name="approvalDecision"
                  value="approve"
                  checked={approvalDecision === 'approve'}
                  onChange={(e) => setApprovalDecision(e.target.value as 'approve')}
                  disabled={loading}
                  className="text-green-600 focus:ring-green-500"
                />
                <CheckCircleIcon className="h-5 w-5 text-green-600" />
                <div>
                  <div className="font-medium text-green-900">Approve Document</div>
                  <div className="text-sm text-green-700">
                    Document meets all requirements and can be approved for publication.
                  </div>
                </div>
              </label>
              
              <label className="flex items-center space-x-3 p-3 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer">
                <input
                  type="radio"
                  name="approvalDecision"
                  value="reject"
                  checked={approvalDecision === 'reject'}
                  onChange={(e) => setApprovalDecision(e.target.value as 'reject')}
                  disabled={loading}
                  className="text-red-600 focus:ring-red-500"
                />
                <XCircleIcon className="h-5 w-5 text-red-600" />
                <div>
                  <div className="font-medium text-red-900">Reject Document</div>
                  <div className="text-sm text-red-700">
                    Document has issues and needs to be returned to the author for revision.
                  </div>
                </div>
              </label>
            </div>
          </div>

          {/* Effective Date - Only for Approval */}
          {approvalDecision === 'approve' && (
            <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg">
              <label htmlFor="effectiveDate" className="block text-sm font-medium text-green-800 mb-2">
                Effective Date <span className="text-red-500">*</span>
              </label>
              <input
                type="date"
                id="effectiveDate"
                value={effectiveDate}
                onChange={(e) => setEffectiveDate(e.target.value)}
                disabled={loading}
                className="w-full px-3 py-2 border border-green-300 rounded-md focus:ring-2 focus:ring-green-500 focus:border-green-500 disabled:opacity-50"
                required
              />
              <div className="mt-2 text-sm">
                {effectiveDate && (
                  <span className={new Date(effectiveDate) <= new Date() 
                    ? "text-green-700 font-medium" 
                    : "text-orange-700 font-medium"
                  }>
                    {new Date(effectiveDate) <= new Date() 
                      ? "📅 Document will be effective immediately"
                      : `⏰ Document will be pending effective until ${new Date(effectiveDate).toLocaleDateString()}`
                    }
                  </span>
                )}
              </div>
            </div>
          )}

          {/* Approval Comments */}
          <div className="mb-6">
            <label htmlFor="approvalComment" className="block text-sm font-medium text-gray-700 mb-2">
              {approvalDecision === 'approve' ? 'Approval' : 'Rejection'} Comments <span className="text-red-500">*</span>
            </label>
            <textarea
              id="approvalComment"
              value={approvalComment}
              onChange={(e) => setApprovalComment(e.target.value)}
              disabled={loading}
              rows={4}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-green-500 focus:border-green-500 disabled:opacity-50"
              placeholder={approvalDecision === 'approve' 
                ? "Provide approval confirmation and any final notes..."
                : approvalDecision === 'reject'
                ? "Specify the issues that need to be addressed before resubmission..."
                : "Please select an approval decision first, then provide detailed comments..."
              }
              required
            />
            <p className="text-xs text-gray-500 mt-1">
              {approvalDecision === 'approve' 
                ? "Document your approval decision and any conditions or notes."
                : approvalDecision === 'reject'
                ? "Clearly explain what needs to be corrected for resubmission."
                : "Your comments will be shared with the author and reviewer."
              }
            </p>
          </div>

          {/* Process Information */}
          <div className="mb-6 p-4 bg-amber-50 border border-amber-200 rounded-lg">
            <div className="flex items-start space-x-3">
              <InformationCircleIcon className="h-5 w-5 text-amber-600 mt-0.5" />
              <div>
                <h4 className="font-medium text-amber-900">Approval Process</h4>
                <div className="text-sm text-amber-700 mt-1">
                  {approvalDecision === 'approve' ? (
                    <p>
                      <strong>Approval:</strong> The document will be marked as <strong>APPROVED</strong> 
                      and you will be able to set an effective date in the next step.
                    </p>
                  ) : approvalDecision === 'reject' ? (
                    <p>
                      <strong>Rejection:</strong> The document will be returned to <strong>DRAFT</strong> 
                      status and the author will be notified to address the issues you've identified.
                    </p>
                  ) : (
                    <p>
                      Please review the document and make an approval decision. Your decision and comments 
                      will be recorded in the audit trail.
                    </p>
                  )}
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
            onClick={handleApprovalSubmission}
            disabled={loading || !approvalDecision || !approvalComment.trim() || (approvalDecision === 'approve' && !effectiveDate)}
            className={`px-4 py-2 text-white rounded-md disabled:opacity-50 flex items-center space-x-2 ${
              approvalDecision === 'approve' 
                ? 'bg-green-600 hover:bg-green-700' 
                : 'bg-red-600 hover:bg-red-700'
            }`}
          >
            {loading && <ClockIcon className="h-4 w-4 animate-spin" />}
            <span>
              {loading 
                ? 'Submitting...' 
                : approvalDecision === 'approve' 
                  ? 'Approve Document' 
                  : 'Reject Document'
              }
            </span>
          </button>
        </div>
      </div>
    </div>
  );
};

export default ApproverInterface;