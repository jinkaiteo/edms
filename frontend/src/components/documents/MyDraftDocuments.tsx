/**
 * My Draft Documents Component
 * 
 * Shows documents in DRAFT status with "Submit for Review" action
 * Implements the bridge between EDMS Step 1 (Create) and Step 2 (Submit for Review)
 */

import React, { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext.tsx';
import apiService from '../../services/api.ts';
import SubmitForReviewModalUnified from '../workflows/SubmitForReviewModalUnified.tsx';

interface Document {
  uuid: string;
  document_number: string;
  title: string;
  description: string;
  status: string;
  status_display: string;
  document_type: any;
  author_display: string;
  created_at: string;
  updated_at: string;
}

const MyDraftDocuments: React.FC = () => {
  const { authenticated } = useAuth();
  
  // State management
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Submit for review modal
  const [submitModalOpen, setSubmitModalOpen] = useState(false);
  const [selectedDocument, setSelectedDocument] = useState<Document | null>(null);

  // Load draft documents
  useEffect(() => {
    if (authenticated) {
      loadDraftDocuments();
    }
  }, [authenticated]);

  const loadDraftDocuments = async () => {
    try {
      setLoading(true);
      
      // Load user's draft documents
      const response = await apiService.get('/documents/documents/?status=DRAFT&author=me');
      
      const documentList = Array.isArray(response) ? response : response.results || [];
      setDocuments(documentList);
      
    } catch (error: any) {
      console.error('❌ Error loading draft documents:', error);
      setError('Failed to load draft documents');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmitForReview = (document: Document) => {
    setSelectedDocument(document);
    setSubmitModalOpen(true);
  };

  const handleSubmitSuccess = () => {
    setSubmitModalOpen(false);
    setSelectedDocument(null);
    // Reload the list to reflect status changes
    loadDraftDocuments();
  };

  const handleCloseModal = () => {
    setSubmitModalOpen(false);
    setSelectedDocument(null);
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center space-x-3">
          <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
          <span>Loading draft documents...</span>
        </div>
      </div>
    );
  }

  return (
    <>
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">📝 My Draft Documents</h3>
          <p className="text-sm text-gray-600 mt-1">
            Documents in DRAFT status ready for review submission (EDMS Step 2)
          </p>
        </div>

        {error && (
          <div className="px-6 py-3 bg-red-50 border-l-4 border-red-400">
            <p className="text-red-700 text-sm">{error}</p>
          </div>
        )}

        <div className="p-6">
          {documents.length === 0 ? (
            <div className="text-center py-8">
              <svg className="w-12 h-12 text-gray-400 mx-auto mb-4" stroke="currentColor" fill="none" viewBox="0 0 48 48">
                <path d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" />
              </svg>
              <h4 className="text-lg font-semibold text-gray-900 mb-2">No draft documents</h4>
              <p className="text-gray-600">
                Create a new document to get started with the EDMS workflow.
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {documents.map((document) => (
                <div
                  key={document.uuid}
                  className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-3 mb-2">
                        <h4 className="text-lg font-semibold text-gray-900">
                          {document.document_number}
                        </h4>
                        <span className="px-2 py-1 bg-yellow-100 text-yellow-800 text-xs rounded-full">
                          {document.status_display}
                        </span>
                      </div>
                      
                      <h5 className="font-medium text-gray-900 mb-1">
                        {document.title}
                      </h5>
                      
                      <p className="text-sm text-gray-600 mb-2">
                        {document.description}
                      </p>
                      
                      <div className="flex items-center space-x-4 text-xs text-gray-500">
                        <span>
                          <strong>Type:</strong> {document.document_type?.name || 'Unknown'}
                        </span>
                        <span>
                          <strong>Author:</strong> {document.author_display}
                        </span>
                        <span>
                          <strong>Created:</strong> {new Date(document.created_at).toLocaleDateString()}
                        </span>
                      </div>
                    </div>
                    
                    <div className="flex-shrink-0 ml-4">
                      <button
                        onClick={() => handleSubmitForReview(document)}
                        className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
                      >
                        📤 Submit for Review
                      </button>
                    </div>
                  </div>
                  
                  {/* EDMS Step Indicator */}
                  <div className="mt-3 p-3 bg-blue-50 border border-blue-200 rounded-md">
                    <div className="flex items-center text-sm">
                      <span className="text-blue-600 font-medium mr-2">📋 EDMS Step 2:</span>
                      <span className="text-blue-800">Ready to select reviewer and submit for review</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Submit for Review Modal */}
      {selectedDocument && (
        <SubmitForReviewModalUnified
          document={selectedDocument}
          isOpen={submitModalOpen}
          onClose={handleCloseModal}
          onSubmitSuccess={handleSubmitSuccess}
        />
      )}
    </>
  );
};

export default MyDraftDocuments;