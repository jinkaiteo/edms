/**
 * Unified Route For Approval Modal Component
 * 
 * Wrapper component for UnifiedWorkflowModal configured for route_for_approval action.
 * This maintains backward compatibility while using the new unified modal.
 */

import React from 'react';
import UnifiedWorkflowModal from './UnifiedWorkflowModal.tsx';

interface RouteForApprovalModalProps {
  isOpen: boolean;
  onClose: () => void;
  document: any;
  onApprovalRouted: () => void; // renamed from onSuccess for compatibility
}

const RouteForApprovalModalUnified: React.FC<RouteForApprovalModalProps> = ({
  isOpen,
  onClose,
  document,
  onApprovalRouted
}) => {
  return (
    <UnifiedWorkflowModal
      document={document}
      isOpen={isOpen}
      onClose={onClose}
      onSuccess={onApprovalRouted}
      workflowAction="route_for_approval"
      enableRejectionAwareness={true}
    />
  );
};

export default RouteForApprovalModalUnified;