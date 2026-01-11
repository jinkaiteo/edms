/**
 * Unified Submit For Review Modal Component
 * 
 * Wrapper component for UnifiedWorkflowModal configured for submit_for_review action.
 * This maintains backward compatibility while using the new unified modal.
 */

import React from 'react';
import UnifiedWorkflowModal from './UnifiedWorkflowModal.tsx';

interface SubmitForReviewModalProps {
  document: any;
  isOpen: boolean;
  onClose: () => void;
  onSubmitSuccess: () => void; // renamed from onSuccess for compatibility
}

const SubmitForReviewModalUnified: React.FC<SubmitForReviewModalProps> = ({
  document,
  isOpen,
  onClose,
  onSubmitSuccess
}) => {
  return (
    <UnifiedWorkflowModal
      document={document}
      isOpen={isOpen}
      onClose={onClose}
      onSuccess={onSubmitSuccess}
      workflowAction="submit_for_review"
      enableRejectionAwareness={true}
    />
  );
};

export default SubmitForReviewModalUnified;