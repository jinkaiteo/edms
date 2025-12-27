import React, { useState, useEffect } from 'react';

interface RejectionEvent {
  rejection_date: string;
  rejection_type: 'review' | 'approval';
  rejected_by: string;
  rejected_by_username: string;
  comment: string;
  from_state: string;
  can_contact: boolean;
}

interface RejectionHistoryModalProps {
  documentId: string;
  isOpen: boolean;
  onClose: () => void;
}

export const RejectionHistoryModal: React.FC<RejectionHistoryModalProps> = ({
  documentId,
  isOpen,
  onClose
}) => {
  const [rejectionHistory, setRejectionHistory] = useState<RejectionEvent[]>([]);
  const [loading, setLoading] = useState(false);
  // Use direct fetch instead of useApi hook to avoid dependency issues
  const apiCall = async (url: string, options: any = {}) => {
    const token = localStorage.getItem('accessToken');
    const response = await fetch(`/api/v1${url}`, {
      method: options.method || 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
        ...options.headers
      },
      body: options.data ? JSON.stringify(options.data) : undefined
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    const data = await response.json();
    return data;
  };

  useEffect(() => {
    if (isOpen && documentId) {
      fetchRejectionHistory();
    }
  }, [isOpen, documentId]);

  const fetchRejectionHistory = async () => {
    setLoading(true);
    try {
      const response = await apiCall(`/workflows/documents/${documentId}/rejection-history/`);
      if (response.success) {
        setRejectionHistory(response.rejection_history);
      }
    } catch (error) {
      console.error('Failed to fetch rejection history:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-2xl max-h-[80vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-bold text-gray-800">Rejection History</h2>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700"
            aria-label="Close"
          >
            ✕
          </button>
        </div>

        {loading ? (
          <div className="flex justify-center items-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          </div>
        ) : rejectionHistory.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <p>No rejection history found for this document.</p>
          </div>
        ) : (
          <div className="space-y-4">
            {rejectionHistory.map((rejection, index) => (
              <div key={index} className="border border-red-200 rounded-lg p-4 bg-red-50">
                <div className="flex justify-between items-start mb-2">
                  <div>
                    <span className={`inline-block px-2 py-1 rounded text-xs font-medium ${
                      rejection.rejection_type === 'review' 
                        ? 'bg-orange-100 text-orange-800' 
                        : 'bg-red-100 text-red-800'
                    }`}>
                      {rejection.rejection_type === 'review' ? 'Review Rejection' : 'Approval Rejection'}
                    </span>
                    <p className="text-sm text-gray-600 mt-1">
                      by <strong>{rejection.rejected_by}</strong>
                    </p>
                  </div>
                  <p className="text-xs text-gray-500">
                    {formatDate(rejection.rejection_date)}
                  </p>
                </div>
                
                <div className="mt-3">
                  <p className="text-sm font-medium text-gray-700 mb-1">Rejection Comment:</p>
                  <p className="text-sm text-gray-800 bg-white p-2 rounded border">
                    {rejection.comment}
                  </p>
                </div>

                {rejection.can_contact && (
                  <div className="mt-2">
                    <button className="text-xs text-blue-600 hover:text-blue-800 underline">
                      Contact {rejection.rejected_by} for clarification
                    </button>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        <div className="mt-6 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-gray-300 text-gray-700 rounded hover:bg-gray-400"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};