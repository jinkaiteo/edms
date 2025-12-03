import React, { useState, useEffect, useRef } from 'react';
import { DocumentStatus, DocumentType, SearchFilters } from '../../types/api';

interface DocumentSearchProps {
  onSearch?: (query: string, filters: SearchFilters) => void;
  onFilterChange?: (filters: SearchFilters) => void;
  documentTypes?: DocumentType[];
  className?: string;
}

const DocumentSearch: React.FC<DocumentSearchProps> = ({
  onSearch,
  onFilterChange,
  documentTypes = [],
  className = ''
}) => {
  const [query, setQuery] = useState('');
  const [showFilters, setShowFilters] = useState(false);
  const [filters, setFilters] = useState<SearchFilters>({
    document_type: [],
    status: [],
    created_after: '',
    created_before: '',
    author: [],
    // Added relevant backend-supported filters:
    title: '',
    description: '',
    document_number: '',
    keywords: '',
    priority: '',
    reviewer: [],
    approver: []
  });
  const [recentSearches, setRecentSearches] = useState<string[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  
  const searchInputRef = useRef<HTMLInputElement>(null);

  // Mock document types if none provided
  const defaultDocumentTypes: DocumentType[] = [
    { id: 1, name: 'Policy', description: 'Company policies', prefix: 'POL', is_active: true, workflow_required: true, retention_period: null, template: null },
    { id: 2, name: 'SOP', description: 'Standard Operating Procedures', prefix: 'SOP', is_active: true, workflow_required: true, retention_period: null, template: null },
    { id: 3, name: 'Manual', description: 'User manuals', prefix: 'MAN', is_active: true, workflow_required: false, retention_period: null, template: null },
    { id: 4, name: 'Form', description: 'Forms and templates', prefix: 'FORM', is_active: true, workflow_required: false, retention_period: null, template: null }
  ];

  const availableDocumentTypes = documentTypes.length > 0 ? documentTypes : defaultDocumentTypes;

  const statusOptions: { value: DocumentStatus; label: string }[] = [
    { value: 'DRAFT', label: 'Draft' },
    { value: 'PENDING_REVIEW', label: 'Pending Review' },
    { value: 'UNDER_REVIEW', label: 'Under Review' },
    { value: 'REVIEW_COMPLETED', label: 'Review Completed' },
    { value: 'PENDING_APPROVAL', label: 'Pending Approval' },
    { value: 'UNDER_APPROVAL', label: 'Under Approval' },
    { value: 'APPROVED', label: 'Approved' },
    { value: 'APPROVED_PENDING_EFFECTIVE', label: 'Approved (Pending Effective)' },
    { value: 'EFFECTIVE', label: 'Effective' },
    { value: 'SCHEDULED_FOR_OBSOLESCENCE', label: 'Scheduled for Obsolescence' },
    { value: 'SUPERSEDED', label: 'Superseded' },
    { value: 'OBSOLETE', label: 'Obsolete' },
    { value: 'TERMINATED', label: 'Terminated' }
  ];

  // Removed departmentOptions - not supported by backend

  useEffect(() => {
    // Load recent searches from localStorage
    const saved = localStorage.getItem('edms_recent_searches');
    if (saved) {
      setRecentSearches(JSON.parse(saved));
    }
  }, []);

  useEffect(() => {
    onFilterChange?.(filters);
  }, [filters, onFilterChange]);

  const handleSearch = (searchQuery?: string) => {
    const searchTerm = searchQuery !== undefined ? searchQuery : query;
    
    if (searchTerm.trim()) {
      // Add to recent searches
      const updated = [searchTerm, ...recentSearches.filter(s => s !== searchTerm)].slice(0, 5);
      setRecentSearches(updated);
      localStorage.setItem('edms_recent_searches', JSON.stringify(updated));
    }

    onSearch?.(searchTerm, filters);
    setShowSuggestions(false);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  const updateFilter = (key: keyof SearchFilters, value: any) => {
    setFilters(prev => ({ ...prev, [key]: value }));
  };

  const toggleArrayFilter = (key: 'document_type' | 'status' | 'author' | 'reviewer' | 'approver', value: string) => {
    setFilters(prev => {
      const current = prev[key] as string[] || [];
      const updated = current.includes(value)
        ? current.filter(v => v !== value)
        : [...current, value];
      return { ...prev, [key]: updated };
    });
  };

  const clearFilters = () => {
    setFilters({
      document_type: [],
      status: [],
      created_after: '',
      created_before: '',
      author: [],
      title: '',
      description: '',
      document_number: '',
      keywords: '',
      priority: '',
      reviewer: [],
      approver: []
    });
  };

  const hasActiveFilters = Object.values(filters).some(value => 
    Array.isArray(value) ? value.length > 0 : Boolean(value)
  );

  const getActiveFilterCount = () => {
    let count = 0;
    Object.values(filters).forEach(value => {
      if (Array.isArray(value)) {
        count += value.length;
      } else if (value) {
        count += 1;
      }
    });
    return count;
  };

  return (
    <div className={`bg-white rounded-lg shadow-sm border border-gray-200 ${className}`}>
      <div className="p-6">
        {/* Search Bar */}
        <div className="relative">
          <div className="relative">
            <input
              ref={searchInputRef}
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyPress={handleKeyPress}
              onFocus={() => setShowSuggestions(true)}
              onBlur={() => setTimeout(() => setShowSuggestions(false), 200)}
              placeholder="Search documents by title, content, or document number..."
              className="w-full pl-10 pr-12 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <svg className="h-5 w-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
            <button
              onClick={() => handleSearch()}
              className="absolute inset-y-0 right-0 pr-3 flex items-center"
            >
              <svg className="h-5 w-5 text-gray-400 hover:text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
              </svg>
            </button>
          </div>

          {/* Search Suggestions */}
          {showSuggestions && recentSearches.length > 0 && (
            <div className="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-md shadow-lg">
              <div className="py-2">
                <div className="px-3 py-1 text-xs font-medium text-gray-500 uppercase tracking-wide">
                  Recent Searches
                </div>
                {recentSearches.map((search, index) => (
                  <button
                    key={index}
                    onClick={() => {
                      setQuery(search);
                      handleSearch(search);
                    }}
                    className="w-full px-3 py-2 text-left text-sm text-gray-900 hover:bg-gray-100 flex items-center space-x-2"
                  >
                    <svg className="h-4 w-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <span>{search}</span>
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Filter Toggle */}
        <div className="flex items-center justify-between mt-4">
          <button
            onClick={() => setShowFilters(!showFilters)}
            className="flex items-center space-x-2 px-3 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200"
          >
            <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.207A1 1 0 013 6.5V4z" />
            </svg>
            <span>Filters</span>
            {hasActiveFilters && (
              <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                {getActiveFilterCount()}
              </span>
            )}
          </button>

          {hasActiveFilters && (
            <button
              onClick={clearFilters}
              className="text-sm text-blue-600 hover:text-blue-800"
            >
              Clear all filters
            </button>
          )}
        </div>

        {/* Advanced Filters */}
        {showFilters && (
          <div className="mt-6 p-4 bg-gray-50 rounded-lg space-y-4">
            <h3 className="text-sm font-medium text-gray-900">Advanced Filters</h3>
            
            {/* Text-based Filters Row - More space for search inputs */}
            <div className="space-y-3">
              <h4 className="text-xs font-medium text-gray-600 uppercase tracking-wider">Text Search Filters</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-3">
                {/* Title Filter */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Title Contains
                  </label>
                  <input
                    type="text"
                    value={filters.title || ''}
                    onChange={(e) => updateFilter('title', e.target.value)}
                    placeholder="Search in document title..."
                    className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>

                {/* Description Filter */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Description Contains
                  </label>
                  <input
                    type="text"
                    value={filters.description || ''}
                    onChange={(e) => updateFilter('description', e.target.value)}
                    placeholder="Search in description..."
                    className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>

                {/* Document Number Filter */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Document Number Contains
                  </label>
                  <input
                    type="text"
                    value={filters.document_number || ''}
                    onChange={(e) => updateFilter('document_number', e.target.value)}
                    placeholder="e.g., SOP, PROC, FORM..."
                    className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>

                {/* Keywords Filter */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Keywords
                  </label>
                  <input
                    type="text"
                    value={filters.keywords || ''}
                    onChange={(e) => updateFilter('keywords', e.target.value)}
                    placeholder="Search keywords..."
                    className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
              </div>
            </div>

            {/* Selection-based Filters Row */}
            <div className="space-y-3">
              <h4 className="text-xs font-medium text-gray-600 uppercase tracking-wider">Category & Status Filters</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                {/* Document Type Filter */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Document Type
                </label>
                <div className="space-y-2">
                  {availableDocumentTypes.map(type => (
                    <label key={type.id} className="flex items-center">
                      <input
                        type="checkbox"
                        checked={(filters.document_type || []).includes(type.name)}
                        onChange={() => toggleArrayFilter('document_type', type.name)}
                        className="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                      />
                      <span className="ml-2 text-sm text-gray-700">{type.name}</span>
                    </label>
                  ))}
                </div>
              </div>

              {/* Status Filter */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Status
                </label>
                <div className="space-y-2 max-h-32 overflow-y-auto">
                  {statusOptions.map(status => (
                    <label key={status.value} className="flex items-center">
                      <input
                        type="checkbox"
                        checked={(filters.status || []).includes(status.value)}
                        onChange={() => toggleArrayFilter('status', status.value)}
                        className="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                      />
                      <span className="ml-2 text-sm text-gray-700">{status.label}</span>
                    </label>
                  ))}
                </div>
              </div>

              {/* Text-based filters moved to top row for better spacing */}
              </div>
            </div>

            {/* Date Range Filter Row */}
            <div className="space-y-3">
              <h4 className="text-xs font-medium text-gray-600 uppercase tracking-wider">Date Filters</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Date Range
                  </label>
                  <div className="space-y-2">
                    <div>
                      <label className="block text-xs text-gray-500 mb-1">From</label>
                      <input
                        type="date"
                        value={filters.created_after || ''}
                        onChange={(e) => updateFilter('created_after', e.target.value)}
                        className="w-full px-3 py-1 border border-gray-300 rounded-md text-sm focus:ring-blue-500 focus:border-blue-500"
                      />
                    </div>
                    <div>
                      <label className="block text-xs text-gray-500 mb-1">To</label>
                      <input
                        type="date"
                        value={filters.created_before || ''}
                        onChange={(e) => updateFilter('created_before', e.target.value)}
                        className="w-full px-3 py-1 border border-gray-300 rounded-md text-sm focus:ring-blue-500 focus:border-blue-500"
                      />
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Quick Filters - Updated with current status values */}
        <div className="mt-4">
          <div className="flex flex-wrap gap-2">
            <button
              onClick={() => updateFilter('status', ['EFFECTIVE'])}
              className="px-3 py-1 text-xs font-medium bg-green-100 text-green-800 rounded-full hover:bg-green-200"
            >
              Effective Documents
            </button>
            <button
              onClick={() => updateFilter('status', ['DRAFT'])}
              className="px-3 py-1 text-xs font-medium bg-gray-100 text-gray-800 rounded-full hover:bg-gray-200"
            >
              Drafts
            </button>
            <button
              onClick={() => updateFilter('status', ['PENDING_REVIEW', 'PENDING_APPROVAL'])}
              className="px-3 py-1 text-xs font-medium bg-yellow-100 text-yellow-800 rounded-full hover:bg-yellow-200"
            >
              Pending Actions
            </button>
            <button
              onClick={() => updateFilter('status', ['APPROVED_PENDING_EFFECTIVE'])}
              className="px-3 py-1 text-xs font-medium bg-blue-100 text-blue-800 rounded-full hover:bg-blue-200"
            >
              Pending Effective
            </button>
            <button
              onClick={() => updateFilter('document_type', ['Policy'])}
              className="px-3 py-1 text-xs font-medium bg-purple-100 text-purple-800 rounded-full hover:bg-purple-200"
            >
              Policies Only
            </button>
            <button
              onClick={() => updateFilter('document_type', ['SOP'])}
              className="px-3 py-1 text-xs font-medium bg-indigo-100 text-indigo-800 rounded-full hover:bg-indigo-200"
            >
              SOPs Only
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DocumentSearch;