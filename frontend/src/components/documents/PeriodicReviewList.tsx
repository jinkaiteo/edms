/**
 * Periodic Review List Component
 * 
 * Displays documents that need periodic review with color-coded status indicators
 */

import React, { useState, useEffect } from 'react';
import { Document } from '../../types/api';
import apiService from '../../services/api.ts';
import PeriodicReviewModal from './PeriodicReviewModal.tsx';

const PeriodicReviewList: React.FC = () => {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedDocument, setSelectedDocument] = useState<Document | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  const loadDocuments = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await apiService.getPeriodicReviewDocuments();
      const docs = Array.isArray(response) ? response : response.results || [];
      setDocuments(docs);
    } catch (err: any) {
      console.error('Failed to load periodic review documents:', err);
      setError('Failed to load documents. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDocuments();
  }, []);

  const handleCompleteReview = (doc: Document) => {
    setSelectedDocument(doc);
    setIsModalOpen(true);
  };

  const handleModalClose = () => {
    setIsModalOpen(false);
    setSelectedDocument(null);
  };

  const handleReviewSuccess = () => {
    loadDocuments(); // Refresh the list
  };

  const getStatusInfo = (doc: Document): { color: string; label: string; bgColor: string } => {
    if (!doc.next_review_date) {
      return { color: 'gray', label: 'No Date', bgColor: 'bg-gray-100 text-gray-800' };
    }

    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const dueDate = new Date(doc.next_review_date);
    dueDate.setHours(0, 0, 0, 0);
    const daysUntil = Math.floor((dueDate.getTime() - today.getTime()) / (1000 * 60 * 60 * 24));

    if (daysUntil < 0) {
      const daysOverdue = Math.abs(daysUntil);
      return {
        color: 'red',
        label: `${daysOverdue} day${daysOverdue !== 1 ? 's' : ''} overdue`,
        bgColor: 'bg-red-100 text-red-800'
      };
    }
    if (daysUntil <= 7) {
      return {
        color: 'orange',
        label: `Due in ${daysUntil} day${daysUntil !== 1 ? 's' : ''}`,
        bgColor: 'bg-orange-100 text-orange-800'
      };
    }
    if (daysUntil <= 30) {
      return {
        color: 'yellow',
        label: `Due in ${daysUntil} days`,
        bgColor: 'bg-yellow-100 text-yellow-800'
      };
    }
    return {
      color: 'green',
      label: `Due in ${daysUntil} days`,
      bgColor: 'bg-green-100 text-green-800'
    };
  };

  const getStatusIcon = (color: string) => {
    switch (color) {
      case 'red': return '🔴';
      case 'orange': return '🟡';
      case 'yellow': return '🟡';
      case 'green': return '🟢';
      default: return '⚪';
    }
  };

  const sortedDocuments = [...documents].sort((a, b) => {
    // Sort by urgency: overdue first, then by due date
    const dateA = a.next_review_date ? new Date(a.next_review_date).getTime() : Infinity;
    const dateB = b.next_review_date ? new Date(b.next_review_date).getTime() : Infinity;
    return dateA - dateB;
  });

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p className="text-gray-600">Loading periodic reviews...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Periodic Reviews</h1>
          <p className="text-gray-600 mt-1">
            Documents requiring periodic review for regulatory compliance
          </p>
        </div>
        <button
          onClick={loadDocuments}
          disabled={loading}
          className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50"
        >
          {loading ? 'Refreshing...' : 'Refresh'}
        </button>
      </div>

      {/* Summary Stats */}
      {documents.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="text-2xl font-bold text-red-800">
              {documents.filter(d => {
                const status = getStatusInfo(d);
                return status.color === 'red';
              }).length}
            </div>
            <div className="text-sm text-red-600 mt-1">Overdue</div>
          </div>
          <div className="bg-orange-50 border border-orange-200 rounded-lg p-4">
            <div className="text-2xl font-bold text-orange-800">
              {documents.filter(d => {
                const status = getStatusInfo(d);
                return status.color === 'orange';
              }).length}
            </div>
            <div className="text-sm text-orange-600 mt-1">Due This Week</div>
          </div>
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <div className="text-2xl font-bold text-yellow-800">
              {documents.filter(d => {
                const status = getStatusInfo(d);
                return status.color === 'yellow';
              }).length}
            </div>
            <div className="text-sm text-yellow-600 mt-1">Due This Month</div>
          </div>
          <div className="bg-green-50 border border-green-200 rounded-lg p-4">
            <div className="text-2xl font-bold text-green-800">
              {documents.filter(d => {
                const status = getStatusInfo(d);
                return status.color === 'green';
              }).length}
            </div>
            <div className="text-sm text-green-600 mt-1">Upcoming</div>
          </div>
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
          <p className="text-red-800">{error}</p>
        </div>
      )}

      {/* Document List */}
      {documents.length === 0 ? (
        <div className="bg-white border border-gray-200 rounded-lg p-12 text-center">
          <div className="text-6xl mb-4">📋</div>
          <h3 className="text-xl font-semibold text-gray-900 mb-2">
            No Periodic Reviews Due
          </h3>
          <p className="text-gray-600">
            All documents are up to date with their periodic reviews.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {sortedDocuments.map((doc) => {
            const statusInfo = getStatusInfo(doc);
            return (
              <div
                key={doc.uuid}
                className="bg-white border border-gray-200 rounded-lg p-6 hover:shadow-lg transition-shadow"
              >
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <span className="text-2xl">{getStatusIcon(statusInfo.color)}</span>
                      <h3 className="text-lg font-semibold text-gray-900">
                        {doc.document_number}
                      </h3>
                      <span className={`px-3 py-1 rounded-full text-xs font-medium ${statusInfo.bgColor}`}>
                        {statusInfo.label}
                      </span>
                    </div>
                    <p className="text-gray-700 mb-3">{doc.title}</p>
                    <div className="flex flex-wrap gap-4 text-sm text-gray-600">
                      <div>
                        <span className="font-medium">Type:</span> {doc.document_type_display || 'N/A'}
                      </div>
                      <div>
                        <span className="font-medium">Status:</span> {doc.status}
                      </div>
                      {doc.last_review_date && (
                        <div>
                          <span className="font-medium">Last Review:</span>{' '}
                          {new Date(doc.last_review_date).toLocaleDateString()}
                          {doc.last_reviewed_by_display && ` by ${doc.last_reviewed_by_display}`}
                        </div>
                      )}
                      {doc.next_review_date && (
                        <div>
                          <span className="font-medium">Next Review:</span>{' '}
                          {new Date(doc.next_review_date).toLocaleDateString()}
                        </div>
                      )}
                    </div>
                  </div>
                  <div className="ml-4">
                    <button
                      onClick={() => handleCompleteReview(doc)}
                      className="px-6 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors"
                    >
                      Complete Review
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Modal */}
      {selectedDocument && (
        <PeriodicReviewModal
          isOpen={isModalOpen}
          onClose={handleModalClose}
          document={selectedDocument}
          onSuccess={handleReviewSuccess}
        />
      )}
    </div>
  );
};

export default PeriodicReviewList;
