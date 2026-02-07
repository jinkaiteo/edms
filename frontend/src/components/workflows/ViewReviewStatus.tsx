/**
 * ViewReviewStatus Component
 * 
 * Displays comprehensive review status information for documents in the workflow system.
 * Shows review progress, timeline, comments, and current workflow state.
 */

import React, { useState, useEffect } from 'react';
import { Document, WorkflowInstance } from '../../types/api';
import { useAuth } from '../../contexts/AuthContext.tsx';

// Define WorkflowTransition interface for the component
interface WorkflowTransition {
  id: number;
  uuid: string;
  from_state: string;
  to_state: string;
  transition_name: string;
  transitioned_by: {
    id: number;
    username: string;
    full_name?: string;
  };
  transitioned_at: string;
  comment?: string;
  transition_data?: any;
}

interface ViewReviewStatusProps {
  document: Document;
  onClose?: () => void;
  onRefresh?: () => void;
}

interface ReviewStatusData {
  workflow: WorkflowInstance | null;
  transitions: WorkflowTransition[];
  currentReviewer?: {
    id: number;
    name: string;
    email: string;
    status: string;
  };
  currentApprover?: {
    id: number;
    name: string;
    email: string;
    status: string;
  };
  timeline: {
    date: string;
    action: string;
    user: string;
    status: string;
    comment?: string;
  }[];
  statistics: {
    daysInReview: number;
    daysRemaining?: number;
    isOverdue: boolean;
  };
}

const ViewReviewStatus: React.FC<ViewReviewStatusProps> = ({
  document,
  onClose,
  onRefresh
}) => {
  const [reviewData, setReviewData] = useState<ReviewStatusData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'overview' | 'timeline' | 'comments' | 'assignments'>('overview');
  
  const { user: _user } = useAuth(); // Prefixed with _ to indicate intentionally unused

  useEffect(() => {
    loadReviewStatus();
  }, [document.uuid]);

  const loadReviewStatus = async () => {
    setLoading(true);
    setError(null);
    
    try {
      console.log('🔄 Loading review status for document:', document.uuid);
      
      // Fetch workflow status and transitions
      const [workflowResponse, transitionsResponse] = await Promise.all([
        fetch(`/api/v1/workflows/documents/${document.uuid}/status/`, {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('accessToken')}`,
            'Content-Type': 'application/json',
          },
        }).then(res => res.ok ? res.json() : null).catch(() => null),
        
        fetch(`/api/v1/workflows/documents/${document.uuid}/history/`, {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('accessToken')}`,
            'Content-Type': 'application/json',
          },
        }).then(res => res.ok ? res.json() : null).catch(() => null)
      ]);

      // Process the data and create review status
      const processedData = processReviewData(workflowResponse, transitionsResponse);
      setReviewData(processedData);
      
    } catch (err) {
      console.error('Error loading review status:', err);
      setError('Failed to load review status from API. Please verify:\n- Backend service is running\n- Document workflow is configured\n- API endpoint is accessible');
      setReviewData(null);
    } finally {
      setLoading(false);
    }
  };

  const processReviewData = (workflow: any, transitions: any): ReviewStatusData => {
    const now = new Date();
    const createdAt = new Date(document.created_at);
    const daysInReview = Math.floor((now.getTime() - createdAt.getTime()) / (1000 * 60 * 60 * 24));
    
    // Build timeline from transitions
    const timeline = [];
    
    // Add document creation
    timeline.push({
      date: document.created_at,
      action: 'Document Created',
      user: document.author_display || 'Unknown Author',
      status: 'DRAFT',
      comment: 'Document created and ready for content upload'
    });

    // Add transitions if available
    if (transitions?.results) {
      transitions.results.forEach((transition: any) => {
        timeline.push({
          date: transition.transitioned_at,
          action: getActionLabel(transition.transition_name, transition.to_state),
          user: transition.transitioned_by?.full_name || transition.transitioned_by?.username || 'System',
          status: transition.to_state,
          comment: transition.comment
        });
      });
    }

    // Sort timeline by date
    timeline.sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());

    return {
      workflow,
      transitions: transitions?.results || [],
      currentReviewer: document.reviewer_display ? {
        id: document.reviewer || 0,
        name: document.reviewer_display,
        email: '',
        status: getReviewerStatus(document.status)
      } : undefined,
      currentApprover: document.approver_display ? {
        id: document.approver || 0,
        name: document.approver_display,
        email: '',
        status: getApproverStatus(document.status)
      } : undefined,
      timeline,
      statistics: {
        daysInReview,
        isOverdue: workflow?.is_overdue || false,
        daysRemaining: workflow?.days_remaining
      }
    };
  };


  const getActionLabel = (transitionName: string, toState: string): string => {
    const actionMap: Record<string, string> = {
      'submit_for_review': 'Submitted for Review',
      'start_review': 'Review Started',
      'approve_review': 'Review Approved',
      'reject_review': 'Review Rejected',
      'route_for_approval': 'Routed for Approval',
      'start_approval': 'Approval Started',
      'approve_document': 'Document Approved',
      'activate_document': 'Document Activated'
    };

    return actionMap[transitionName] || `Transitioned to ${toState}`;
  };

  const getReviewerStatus = (documentStatus: string): string => {
    switch (documentStatus.toUpperCase()) {
      case 'PENDING_REVIEW': return 'ASSIGNED';
      case 'UNDER_REVIEW': return 'IN_PROGRESS';
      case 'REVIEW_COMPLETED':
      case 'REVIEWED': return 'COMPLETED';
      default: return 'NOT_ASSIGNED';
    }
  };

  const getApproverStatus = (documentStatus: string): string => {
    switch (documentStatus.toUpperCase()) {
      case 'PENDING_APPROVAL': return 'ASSIGNED';
      case 'UNDER_APPROVAL': return 'IN_PROGRESS';
      case 'APPROVED':
      case 'EFFECTIVE': return 'COMPLETED';
      default: return 'NOT_ASSIGNED';
    }
  };

  const getStatusColor = (status: string): string => {
    const colors: Record<string, string> = {
      DRAFT: 'bg-gray-100 text-gray-800',
      PENDING_REVIEW: 'bg-yellow-100 text-yellow-800',
      UNDER_REVIEW: 'bg-blue-100 text-blue-800',
      REVIEW_COMPLETED: 'bg-purple-100 text-purple-800',
      PENDING_APPROVAL: 'bg-orange-100 text-orange-800',
      APPROVED: 'bg-green-100 text-green-800',
      EFFECTIVE: 'bg-green-100 text-green-800',
      REJECTED: 'bg-red-100 text-red-800'
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  const getAssigneeStatusColor = (status: string): string => {
    const colors: Record<string, string> = {
      ASSIGNED: 'bg-yellow-100 text-yellow-800',
      IN_PROGRESS: 'bg-blue-100 text-blue-800',
      COMPLETED: 'bg-green-100 text-green-800',
      NOT_ASSIGNED: 'bg-gray-100 text-gray-600'
    };
    return colors[status] || 'bg-gray-100 text-gray-600';
  };

  const formatDate = (dateString: string): string => {
    return new Date(dateString).toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const formatDuration = (days: number): string => {
    if (days === 0) return 'Today';
    if (days === 1) return '1 day';
    return `${days} days`;
  };

  const renderOverviewTab = () => (
    <div className="space-y-6">
      {/* Status Overview */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <svg className="w-8 h-8 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
            <div className="ml-3">
              <h3 className="text-lg font-medium text-blue-900">Current Status</h3>
              <p className="text-blue-700">{document.status_display || document.status.replace('_', ' ')}</p>
            </div>
          </div>
        </div>

        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <svg className="w-8 h-8 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div className="ml-3">
              <h3 className="text-lg font-medium text-yellow-900">Days in Review</h3>
              <p className="text-yellow-700">{formatDuration(reviewData.statistics.daysInReview)}</p>
            </div>
          </div>
        </div>

        <div className={`border rounded-lg p-4 ${reviewData.statistics.isOverdue ? 'bg-red-50 border-red-200' : 'bg-green-50 border-green-200'}`}>
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <svg className={`w-8 h-8 ${reviewData.statistics.isOverdue ? 'text-red-600' : 'text-green-600'}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={reviewData.statistics.isOverdue ? "M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.728-.833-2.498 0L4.268 16.5c-.77.833.192 2.5 1.732 2.5z" : "M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"} />
              </svg>
            </div>
            <div className="ml-3">
              <h3 className={`text-lg font-medium ${reviewData.statistics.isOverdue ? 'text-red-900' : 'text-green-900'}`}>
                {reviewData.statistics.isOverdue ? 'Overdue' : 'On Track'}
              </h3>
              <p className={reviewData.statistics.isOverdue ? 'text-red-700' : 'text-green-700'}>
                {reviewData.statistics.daysRemaining !== undefined 
                  ? `${formatDuration(Math.abs(reviewData.statistics.daysRemaining))} ${reviewData.statistics.daysRemaining < 0 ? 'overdue' : 'remaining'}`
                  : 'No deadline set'
                }
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Progress Indicator */}
      <div className="bg-gray-50 rounded-lg p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">📊 Workflow Progress</h3>
        <div className="space-y-4">
          {/* Progress Steps */}
          <div className="flex items-center text-sm">
            <div className="flex items-center space-x-8 w-full">
              {[
                { key: 'DRAFT', label: 'Created', icon: '📝' },
                { key: 'PENDING_REVIEW', label: 'Pending Review', icon: '⏳' },
                { key: 'UNDER_REVIEW', label: 'Under Review', icon: '👁️' },
                { key: 'PENDING_APPROVAL', label: 'Pending Approval', icon: '⏳' },
                { key: 'EFFECTIVE', label: 'Effective', icon: '✅' },
              ].map((step, index) => {
                const isActive = document.status.toUpperCase() === step.key;
                const isPassed = ['DRAFT', 'PENDING_REVIEW', 'UNDER_REVIEW', 'PENDING_APPROVAL'].slice(0, index).some(s => 
                  ['UNDER_REVIEW', 'PENDING_APPROVAL', 'EFFECTIVE'].includes(document.status.toUpperCase())
                );
                
                return (
                  <div key={step.key} className="flex items-center">
                    <div className={`flex items-center space-x-2 ${isActive ? 'text-blue-600 font-medium' : isPassed ? 'text-green-600' : 'text-gray-400'}`}>
                      <span className={`w-8 h-8 rounded-full flex items-center justify-center text-xs ${isActive ? 'bg-blue-100' : isPassed ? 'bg-green-100' : 'bg-gray-100'}`}>
                        {step.icon}
                      </span>
                      <span className="whitespace-nowrap">{step.label}</span>
                    </div>
                    {index < 4 && (
                      <div className={`flex-1 h-px mx-4 ${isPassed ? 'bg-green-300' : 'bg-gray-200'}`}></div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>

      {/* Current Assignments */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {reviewData.currentReviewer && (
          <div className="border rounded-lg p-4">
            <h4 className="font-medium text-gray-900 mb-3 flex items-center">
              <span className="mr-2">👁️</span>
              Current Reviewer
            </h4>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Name:</span>
                <span className="text-sm font-medium">{reviewData.currentReviewer.name}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Status:</span>
                <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${getAssigneeStatusColor(reviewData.currentReviewer.status)}`}>
                  {reviewData.currentReviewer.status.replace('_', ' ')}
                </span>
              </div>
            </div>
          </div>
        )}

        {reviewData.currentApprover && (
          <div className="border rounded-lg p-4">
            <h4 className="font-medium text-gray-900 mb-3 flex items-center">
              <span className="mr-2">✅</span>
              Current Approver
            </h4>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Name:</span>
                <span className="text-sm font-medium">{reviewData.currentApprover.name}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Status:</span>
                <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${getAssigneeStatusColor(reviewData.currentApprover.status)}`}>
                  {reviewData.currentApprover.status.replace('_', ' ')}
                </span>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );

  const renderTimelineTab = () => (
    <div className="space-y-4">
      <h3 className="text-lg font-medium text-gray-900 mb-4">📅 Workflow Timeline</h3>
      <div className="flow-root">
        <ul className="-mb-8">
          {reviewData.timeline.map((event, eventIdx) => (
            <li key={eventIdx}>
              <div className="relative pb-8">
                {eventIdx !== reviewData.timeline.length - 1 ? (
                  <span
                    className="absolute top-4 left-4 -ml-px h-full w-0.5 bg-gray-200"
                    aria-hidden="true"
                  />
                ) : null}
                <div className="relative flex space-x-3">
                  <div>
                    <span className={`h-8 w-8 rounded-full flex items-center justify-center ring-8 ring-white ${getStatusColor(event.status)}`}>
                      <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                      </svg>
                    </span>
                  </div>
                  <div className="min-w-0 flex-1 pt-1.5">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium text-gray-900">{event.action}</p>
                        <p className="text-sm text-gray-500">by {event.user}</p>
                      </div>
                      <div className="text-right text-sm text-gray-500">
                        <time>{formatDate(event.date)}</time>
                      </div>
                    </div>
                    {event.comment && (
                      <div className="mt-2 text-sm text-gray-700 bg-gray-50 rounded-lg p-3">
                        <p className="italic">"{event.comment}"</p>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );

  const renderCommentsTab = () => {
    const commentsFromTimeline = reviewData.timeline.filter(event => event.comment);
    
    return (
      <div className="space-y-4">
        <h3 className="text-lg font-medium text-gray-900 mb-4">💬 Review Comments</h3>
        
        {commentsFromTimeline.length === 0 ? (
          <div className="text-center py-8">
            <div className="text-gray-400 mb-4">
              <svg className="w-12 h-12 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
              </svg>
            </div>
            <h3 className="text-lg font-medium text-gray-900 mb-1">No Comments Yet</h3>
            <p className="text-gray-500">Comments from reviewers and approvers will appear here.</p>
          </div>
        ) : (
          <div className="space-y-4">
            {commentsFromTimeline.map((event, index) => (
              <div key={index} className="bg-white border border-gray-200 rounded-lg p-4">
                <div className="flex items-start space-x-3">
                  <div className="flex-shrink-0">
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center ${getStatusColor(event.status)}`}>
                      <span className="text-xs font-medium">
                        {event.user.charAt(0).toUpperCase()}
                      </span>
                    </div>
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium text-gray-900">{event.user}</p>
                        <p className="text-xs text-gray-500">{event.action}</p>
                      </div>
                      <time className="text-sm text-gray-500">{formatDate(event.date)}</time>
                    </div>
                    <div className="mt-2 text-sm text-gray-700">
                      <p>{event.comment}</p>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    );
  };

  const renderAssignmentsTab = () => (
    <div className="space-y-6">
      <h3 className="text-lg font-medium text-gray-900 mb-4">👥 Workflow Assignments</h3>
      
      <div className="space-y-4">
        {/* Document Author */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="flex-shrink-0">
                <svg className="w-8 h-8 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
              </div>
              <div>
                <h4 className="font-medium text-blue-900">Document Author</h4>
                <p className="text-sm text-blue-700">{document.author_display || 'Unknown Author'}</p>
              </div>
            </div>
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
              Author
            </span>
          </div>
          <div className="mt-3 text-sm text-blue-700">
            <p>• Can edit document in DRAFT status</p>
            <p>• Submits document for review</p>
            <p>• Routes document for approval after review</p>
            <p>• Cannot review own documents (segregation of duties)</p>
          </div>
        </div>

        {/* Reviewer */}
        {reviewData.currentReviewer ? (
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div className="flex-shrink-0">
                  <svg className="w-8 h-8 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <div>
                  <h4 className="font-medium text-yellow-900">Assigned Reviewer</h4>
                  <p className="text-sm text-yellow-700">{reviewData.currentReviewer.name}</p>
                </div>
              </div>
              <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getAssigneeStatusColor(reviewData.currentReviewer.status)}`}>
                {reviewData.currentReviewer.status.replace('_', ' ')}
              </span>
            </div>
            <div className="mt-3 text-sm text-yellow-700">
              <p>• Reviews document content for accuracy</p>
              <p>• Can approve or reject the document</p>
              <p>• Must provide comments for decisions</p>
            </div>
          </div>
        ) : (
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
            <div className="flex items-center space-x-3">
              <div className="flex-shrink-0">
                <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.728-.833-2.498 0L4.268 16.5c-.77.833.192 2.5 1.732 2.5z" />
                </svg>
              </div>
              <div>
                <h4 className="font-medium text-gray-700">Reviewer</h4>
                <p className="text-sm text-gray-500">No reviewer assigned yet</p>
              </div>
            </div>
          </div>
        )}

        {/* Approver */}
        {reviewData.currentApprover ? (
          <div className="bg-green-50 border border-green-200 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div className="flex-shrink-0">
                  <svg className="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <div>
                  <h4 className="font-medium text-green-900">Assigned Approver</h4>
                  <p className="text-sm text-green-700">{reviewData.currentApprover.name}</p>
                </div>
              </div>
              <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getAssigneeStatusColor(reviewData.currentApprover.status)}`}>
                {reviewData.currentApprover.status.replace('_', ' ')}
              </span>
            </div>
            <div className="mt-3 text-sm text-green-700">
              <p>• Final approval authority for the document</p>
              <p>• Can approve or reject after review</p>
              <p>• Sets effective date upon approval</p>
            </div>
          </div>
        ) : (
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
            <div className="flex items-center space-x-3">
              <div className="flex-shrink-0">
                <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.728-.833-2.498 0L4.268 16.5c-.77.833.192 2.5 1.732 2.5z" />
                </svg>
              </div>
              <div>
                <h4 className="font-medium text-gray-700">Approver</h4>
                <p className="text-sm text-gray-500">No approver assigned yet</p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );

  if (loading) {
    return (
      <div className="fixed inset-0 overflow-y-auto" style={{ zIndex: 60 }} bg-gray-500 bg-opacity-75 flex items-center justify-center">
        <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
          <div className="flex items-center justify-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <span className="ml-2 text-gray-600">Loading review status...</span>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="fixed inset-0 overflow-y-auto" style={{ zIndex: 60 }} bg-gray-500 bg-opacity-75 flex items-center justify-center">
        <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
          <div className="text-center">
            <div className="text-red-600 mb-4">
              <svg className="w-12 h-12 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.728-.833-2.498 0L4.268 16.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
            </div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">Error Loading Review Status</h3>
            <p className="text-gray-600 mb-4">{error}</p>
            <div className="flex justify-center space-x-3">
              <button
                onClick={loadReviewStatus}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
              >
                Retry
              </button>
              {onClose && (
                <button
                  onClick={onClose}
                  className="px-4 py-2 bg-gray-300 text-gray-700 rounded-md hover:bg-gray-400"
                >
                  Close
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!reviewData) {
    return null;
  }

  return (
    <div className="fixed inset-0 overflow-y-auto" style={{ zIndex: 60 }} bg-gray-500 bg-opacity-75">
      <div className="flex min-h-full items-center justify-center p-4">
        <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-hidden">
          {/* Header */}
          <div className="px-6 py-4 border-b border-gray-200 bg-gray-50">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-xl font-semibold text-gray-900">
                  📋 Review Status: {document.title}
                </h2>
                <p className="text-sm text-gray-600 mt-1">
                  {document.document_number} • Version {document.version || '1.0'}
                </p>
              </div>
              <div className="flex items-center space-x-2">
                <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(document.status.toUpperCase())}`}>
                  {document.status_display || document.status.replace('_', ' ')}
                </span>
                {onClose && (
                  <button
                    onClick={onClose}
                    className="p-2 text-gray-400 hover:text-gray-600 rounded-full hover:bg-gray-100"
                  >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                )}
              </div>
            </div>
          </div>

          {/* Tabs */}
          <div className="border-b border-gray-200">
            <nav className="flex space-x-8 px-6" aria-label="Tabs">
              {[
                { key: 'overview', label: 'Overview', icon: '📊' },
                { key: 'timeline', label: 'Timeline', icon: '📅' },
                { key: 'comments', label: 'Comments', icon: '💬' },
                { key: 'assignments', label: 'Assignments', icon: '👥' }
              ].map((tab) => (
                <button
                  key={tab.key}
                  onClick={() => setActiveTab(tab.key as typeof activeTab)}
                  className={`py-4 px-1 border-b-2 font-medium text-sm flex items-center space-x-2 ${
                    activeTab === tab.key
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  <span>{tab.icon}</span>
                  <span>{tab.label}</span>
                </button>
              ))}
            </nav>
          </div>

          {/* Tab Content */}
          <div className="p-6 max-h-[60vh] overflow-y-auto">{renderTabContent()}</div>

          {/* Footer */}
          <div className="px-6 py-4 border-t border-gray-200 bg-gray-50">
            <div className="flex items-center justify-between">
              <div className="text-sm text-gray-600">
                Last updated: {formatDate(document.updated_at || document.created_at)}
              </div>
              <div className="flex space-x-3">
                {onRefresh && (
                  <button
                    onClick={onRefresh}
                    className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
                  >
                    Refresh
                  </button>
                )}
                {onClose && (
                  <button
                    onClick={onClose}
                    className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700"
                  >
                    Close
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  function renderTabContent() {
    switch (activeTab) {
      case 'overview':
        return renderOverviewTab();
      case 'timeline':
        return renderTimelineTab();
      case 'comments':
        return renderCommentsTab();
      case 'assignments':
        return renderAssignmentsTab();
      default:
        return renderOverviewTab();
    }
  }
};

export default ViewReviewStatus;