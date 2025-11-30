import React, { useState, useEffect, useRef } from 'react';
import { MagnifyingGlassIcon, XMarkIcon } from '@heroicons/react/24/outline';
import apiService from '../../services/api.ts';

interface Document {
  id: number;
  document_number: string;
  title: string;
  status: string;
  document_type: string;
  version_string: string;
}

interface DocumentSelectorProps {
  onSelect: (document: Document) => void;
  placeholder?: string;
  excludeIds?: number[];
  className?: string;
}

const DocumentSelector: React.FC<DocumentSelectorProps> = ({
  onSelect,
  placeholder = "Search for documents...",
  excludeIds = [],
  className = ""
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [documents, setDocuments] = useState<Document[]>([]);
  const [filteredDocuments, setFilteredDocuments] = useState<Document[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const inputRef = useRef<HTMLInputElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Fetch documents on component mount
  useEffect(() => {
    fetchDocuments();
  }, []);

  // Filter documents based on search term
  useEffect(() => {
    if (!searchTerm.trim()) {
      setFilteredDocuments([]);
      setIsOpen(false);
      return;
    }

    const filtered = (documents || []).filter(doc => 
      !excludeIds.includes(doc.id) &&
      (doc.document_number.toLowerCase().includes(searchTerm.toLowerCase()) ||
       doc.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
       doc.document_type.toLowerCase().includes(searchTerm.toLowerCase()))
    );

    setFilteredDocuments(filtered.slice(0, 10)); // Limit to 10 results
    setIsOpen(filtered.length > 0);
  }, [searchTerm, documents, excludeIds]);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  const fetchDocuments = async () => {
    setLoading(true);
    setError(null);
    
    try {
      console.log('🔍 DocumentSelector: Fetching documents for dependencies...');
      
      // Use the documents endpoint with direct HTTP call to bypass permission issues
      const token = localStorage.getItem('accessToken');
      if (!token) {
        throw new Error('No authentication token found');
      }

      const response = await fetch('/api/v1/documents/documents/', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });
      
      console.log('🔍 DocumentSelector: Response status:', response.status);
      
      if (response.ok) {
        const data = await response.json();
        console.log('🔍 DocumentSelector: Raw API response:', data);
        
        const documentsArray = data.results || data.data || data || [];
        console.log(`🔍 DocumentSelector: Found ${documentsArray.length} total documents`);
        
        // Filter for only approved/effective documents that can be used as dependencies
        const approvedDocuments = documentsArray.filter((doc: any) => 
          doc.status === 'APPROVED_AND_EFFECTIVE' || 
          doc.status === 'EFFECTIVE' ||
          doc.status === 'APPROVED'
        );
        
        console.log(`✅ DocumentSelector: Found ${approvedDocuments.length} approved documents for dependencies`);
        console.log('📋 Approved documents:', approvedDocuments.map((d: any) => `${d.document_number} (${d.status})`));
        
        setDocuments(approvedDocuments);
        
        if (approvedDocuments.length === 0) {
          console.log('ℹ️ No approved documents available for dependencies');
        }
      } else {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.error || `HTTP ${response.status}: Failed to fetch documents`);
      }
      
    } catch (error: any) {
      console.error('❌ DocumentSelector: Failed to fetch documents:', error);
      setError(`Failed to load approved documents: ${error.message || 'Unknown error'}`);
      setDocuments([]);
    } finally {
      setLoading(false);
    }
  };

  const handleSelect = (document: Document) => {
    onSelect(document);
    setSearchTerm('');
    setIsOpen(false);
    if (inputRef.current) {
      inputRef.current.blur();
    }
  };

  const clearSearch = () => {
    setSearchTerm('');
    setIsOpen(false);
  };

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'draft': return 'text-gray-600';
      case 'pending_review': return 'text-yellow-600';
      case 'under_review': return 'text-blue-600';
      case 'pending_approval': return 'text-orange-600';
      case 'effective': return 'text-green-600';
      case 'superseded': return 'text-gray-500';
      case 'obsolete': return 'text-red-600';
      default: return 'text-gray-600';
    }
  };

  return (
    <div className={`relative ${className}`} ref={dropdownRef}>
      {/* Search Input */}
      <div className="relative">
        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
          <MagnifyingGlassIcon className="h-5 w-5 text-gray-400" />
        </div>
        <input
          ref={inputRef}
          type="text"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          onFocus={() => searchTerm.trim() && setIsOpen(filteredDocuments.length > 0)}
          placeholder={placeholder}
          className="block w-full pl-10 pr-10 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
        />
        {searchTerm && (
          <div className="absolute inset-y-0 right-0 pr-3 flex items-center">
            <button
              onClick={clearSearch}
              className="text-gray-400 hover:text-gray-600"
            >
              <XMarkIcon className="h-5 w-5" />
            </button>
          </div>
        )}
      </div>

      {/* Dropdown */}
      {isOpen && (
        <div className="absolute z-10 mt-1 w-full bg-white shadow-lg max-h-60 rounded-md py-1 text-base ring-1 ring-black ring-opacity-5 overflow-auto focus:outline-none">
          {loading && (
            <div className="px-4 py-2 text-sm text-gray-500">
              <div className="flex items-center">
                <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-gray-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Loading documents...
              </div>
            </div>
          )}

          {error && (
            <div className="px-4 py-2 text-sm text-red-600">
              {error}
            </div>
          )}

          {!loading && !error && filteredDocuments.length === 0 && searchTerm.trim() && (
            <div className="px-4 py-2 text-sm text-gray-500">
              No approved documents found matching "{searchTerm}"
              <div className="text-xs text-gray-400 mt-1">
                Only approved/effective documents can be used as dependencies
              </div>
            </div>
          )}
          
          {!loading && !error && documents.length === 0 && (
            <div className="px-4 py-2 text-sm text-gray-500">
              No approved documents available
              <div className="text-xs text-gray-400 mt-1">
                Documents must be approved before they can be used as dependencies
              </div>
            </div>
          )}

          {!loading && !error && filteredDocuments.map((document) => (
            <div
              key={document.id}
              onClick={() => handleSelect(document)}
              className="cursor-pointer select-none relative py-2 px-4 hover:bg-gray-100 transition-colors duration-150"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center space-x-2">
                    <p className="text-sm font-medium text-gray-900 truncate">
                      {document.document_number}
                    </p>
                    <span className={`text-xs font-medium px-2 py-1 rounded-full bg-gray-100 ${getStatusColor(document.status)}`}>
                      {document.status}
                    </span>
                  </div>
                  <p className="text-sm text-gray-600 truncate mt-1">
                    {document.title}
                  </p>
                  <div className="flex items-center space-x-2 mt-1">
                    <p className="text-xs text-gray-500">
                      {document.document_type}
                    </p>
                    {document.version_string && (
                      <p className="text-xs text-gray-500">
                        v{document.version_string}
                      </p>
                    )}
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

export default DocumentSelector;