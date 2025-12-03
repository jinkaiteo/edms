import React, { useState, useCallback } from 'react';
import { PlaceholderDefinition } from '../../types/api';

interface PlaceholderManagementProps {
  className?: string;
}

interface PlaceholderMatch {
  placeholder: string;
  suggestions: string[];
  confidence: number;
}

interface PlaceholderAnalysis {
  placeholder: string;
  issue: string;
  suggestion: string;
  confidence: number;
}

interface TemplateValidation {
  fileName: string;
  isValid: boolean;
  
  // Enhanced analysis categories
  identifiedPlaceholders: string[];
  misformattedPlaceholders: PlaceholderAnalysis[];
  unknownPlaceholders: PlaceholderMatch[];
  unmatchedPatterns: PlaceholderAnalysis[];
  unusedPlaceholders: {
    [category: string]: string[];
  };
  
  // Summary stats
  totalPatternsFound: number;
  totalIssues: number;
  errors: string[];
}

const PlaceholderManagement: React.FC<PlaceholderManagementProps> = ({ className = '' }) => {
  const [placeholders, setPlaceholders] = useState<PlaceholderDefinition[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<string>('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [showTemplateValidator, setShowTemplateValidator] = useState(false);
  const [templateValidation, setTemplateValidation] = useState<TemplateValidation | null>(null);
  const [validating, setValidating] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  // Load placeholders from API
  React.useEffect(() => {
    fetchPlaceholders();
  }, []);

  const fetchPlaceholders = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/v1/placeholders/definitions/', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('accessToken')}`,
          'Content-Type': 'application/json',
        },
      });
      
      if (response.ok) {
        const data = await response.json();
        console.log(`✅ Successfully fetched ${data.length} placeholders from API`);
        setPlaceholders(data);
      } else {
        console.error(`❌ Failed to fetch placeholders: ${response.status} ${response.statusText}`);
        setPlaceholders(mockPlaceholders);
      }
    } catch (error) {
      console.error('❌ Error fetching placeholders:', error);
      setPlaceholders(mockPlaceholders);
    } finally {
      setLoading(false);
    }
  };

  // Mock data fallback
  const mockPlaceholders: PlaceholderDefinition[] = [
    { id: 1, name: 'DOC_NUMBER', display_name: 'Document Number', description: 'Unique document identifier', placeholder_type: 'DOCUMENT', data_source: 'DOCUMENT_MODEL', default_value: '', is_active: true },
    { id: 2, name: 'DOC_TITLE', display_name: 'Document Title', description: 'Document title or name', placeholder_type: 'DOCUMENT', data_source: 'DOCUMENT_MODEL', default_value: '', is_active: true },
    { id: 3, name: 'AUTHOR_NAME', display_name: 'Author Name', description: 'Document author full name', placeholder_type: 'USER', data_source: 'USER_MODEL', default_value: '', is_active: true },
    { id: 4, name: 'APPROVAL_DATE', display_name: 'Approval Date', description: 'Document approval date', placeholder_type: 'DATE', data_source: 'DOCUMENT_MODEL', default_value: '', is_active: true },
    { id: 5, name: 'COMPANY_NAME', display_name: 'Company Name', description: 'Organization name', placeholder_type: 'SYSTEM', data_source: 'SYSTEM_CONFIG', default_value: '', is_active: true }
  ];

  // Validate template file
  const validateTemplate = useCallback(async (file: File) => {
    if (!file.name.toLowerCase().endsWith('.docx')) {
      setTemplateValidation({
        fileName: file.name,
        isValid: false,
        placeholdersFound: [],
        placeholdersValid: [],
        placeholdersInvalid: [],
        errors: ['Only .docx files are supported for template validation']
      });
      return;
    }

    setValidating(true);
    try {
      const formData = new FormData();
      formData.append('file', file);

      // Create a mock document for validation
      const response = await fetch('/api/v1/documents/documents/validate-template/', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('accessToken')}`,
        },
        body: formData,
      });

      if (response.ok) {
        const result = await response.json();
        setTemplateValidation({
          fileName: file.name,
          isValid: result.is_valid,
          placeholdersFound: result.placeholders_found || [],
          placeholdersValid: result.placeholders_found?.filter((p: string) => 
            placeholders.some(ph => ph.name === p)
          ) || [],
          placeholdersInvalid: result.placeholders_missing || [],
          errors: result.errors || []
        });
      } else {
        // Enhanced fallback: comprehensive client-side analysis
        // Note: Client-side can only read raw file content, not parse .docx structure
        // This is a simplified fallback - backend validation is more comprehensive
        const text = await file.text();
        const analysis = performEnhancedValidation(text, placeholders);
        setTemplateValidation({
          ...analysis,
          fileName: file.name,
          errors: [...(analysis.errors || []), 
                   'Note: Client-side validation has limited .docx parsing. Upload to server for complete analysis of tables, headers, and footers.']
        });
      }
    } catch (error) {
      console.error('Template validation error:', error);
      setTemplateValidation({
        fileName: file.name,
        isValid: false,
        placeholdersFound: [],
        placeholdersValid: [],
        placeholdersInvalid: [],
        errors: [`Validation failed: ${error}`]
      });
    } finally {
      setValidating(false);
    }
  }, [placeholders]);

  // Enhanced validation function with fuzzy matching and pattern recognition
  const performEnhancedValidation = useCallback((text: string, availablePlaceholders: PlaceholderDefinition[]): TemplateValidation => {
    const placeholderNames = availablePlaceholders.map(p => p.name);
    const placeholdersByCategory = availablePlaceholders.reduce((acc, p) => {
      const category = p.placeholder_type || 'OTHER';
      if (!acc[category]) acc[category] = [];
      acc[category].push(p.name);
      return acc;
    }, {} as Record<string, string[]>);

    // 1. Pattern recognition for various formats
    const patterns = [
      { regex: /\{\{([A-Z_][A-Z0-9_]*)\}\}/g, name: 'Standard {{PLACEHOLDER}}' },
      { regex: /\{([A-Z_][A-Z0-9_]*)\}/g, name: 'Single braces {PLACEHOLDER}' },
      { regex: /\{\{\s*([A-Z_][A-Z0-9_]*)\s*\}\}/g, name: 'Spaced {{ PLACEHOLDER }}' },
      { regex: /<<([A-Z_][A-Z0-9_]*)>>/g, name: 'Angle brackets <<PLACEHOLDER>>' },
      { regex: /\[([A-Z_][A-Z0-9_]*)\]/g, name: 'Square brackets [PLACEHOLDER]' },
      { regex: /%([A-Z_][A-Z0-9_]*)%/g, name: 'Percent signs %PLACEHOLDER%' },
      { regex: /\$\{([A-Z_][A-Z0-9_]*)\}/g, name: 'Dollar braces ${PLACEHOLDER}' },
    ];

    const identifiedPlaceholders: string[] = [];
    const misformattedPlaceholders: PlaceholderAnalysis[] = [];
    const unknownPlaceholders: PlaceholderMatch[] = [];
    const unmatchedPatterns: PlaceholderAnalysis[] = [];

    // Process each pattern
    patterns.forEach(pattern => {
      let match;
      while ((match = pattern.regex.exec(text)) !== null) {
        const placeholder = match[1];
        const fullMatch = match[0];

        if (pattern.name === 'Standard {{PLACEHOLDER}}') {
          // Check if it's a valid placeholder
          if (placeholderNames.includes(placeholder)) {
            if (!identifiedPlaceholders.includes(placeholder)) {
              identifiedPlaceholders.push(placeholder);
            }
          } else {
            // Unknown placeholder - find suggestions using fuzzy matching
            const suggestions = findClosestMatches(placeholder, placeholderNames);
            unknownPlaceholders.push({
              placeholder: fullMatch,
              suggestions: suggestions.map(s => `{{${s.match}}}`),
              confidence: suggestions[0]?.confidence || 0
            });
          }
        } else {
          // Misformatted or unmatched patterns
          if (placeholderNames.includes(placeholder)) {
            // Valid placeholder but wrong format
            misformattedPlaceholders.push({
              placeholder: fullMatch,
              issue: `Wrong format (${pattern.name})`,
              suggestion: `{{${placeholder}}}`,
              confidence: 100
            });
          } else {
            // Invalid placeholder with wrong format
            const suggestions = findClosestMatches(placeholder, placeholderNames);
            if (suggestions[0]?.confidence > 50) {
              unmatchedPatterns.push({
                placeholder: fullMatch,
                issue: `Wrong format and unknown placeholder`,
                suggestion: `{{${suggestions[0].match}}}`,
                confidence: suggestions[0].confidence
              });
            } else {
              unmatchedPatterns.push({
                placeholder: fullMatch,
                issue: `Unrecognized pattern (${pattern.name})`,
                suggestion: 'Remove or use valid placeholder format {{NAME}}',
                confidence: 0
              });
            }
          }
        }
      }
      // Reset regex lastIndex for next iteration
      pattern.regex.lastIndex = 0;
    });

    // 5. Find unused placeholders by category
    const usedPlaceholders = new Set(identifiedPlaceholders);
    const unusedPlaceholders: { [category: string]: string[] } = {};
    
    Object.entries(placeholdersByCategory).forEach(([category, names]) => {
      const unused = names.filter(name => !usedPlaceholders.has(name));
      if (unused.length > 0) {
        unusedPlaceholders[category] = unused;
      }
    });

    const totalIssues = misformattedPlaceholders.length + unknownPlaceholders.length + unmatchedPatterns.length;
    const totalPatternsFound = identifiedPlaceholders.length + totalIssues;

    return {
      fileName: 'client-validation',
      isValid: totalIssues === 0 && identifiedPlaceholders.length > 0,
      identifiedPlaceholders: identifiedPlaceholders.sort(),
      misformattedPlaceholders,
      unknownPlaceholders,
      unmatchedPatterns,
      unusedPlaceholders,
      totalPatternsFound,
      totalIssues,
      errors: totalIssues > 0 ? [`Found ${totalIssues} issues that need attention`] : []
    };
  }, []);

  // Fuzzy matching function for placeholder suggestions
  const findClosestMatches = useCallback((target: string, candidates: string[]): Array<{match: string, confidence: number}> => {
    const results = candidates.map(candidate => ({
      match: candidate,
      confidence: calculateSimilarity(target, candidate)
    }))
    .filter(result => result.confidence > 30) // Only show reasonably close matches
    .sort((a, b) => b.confidence - a.confidence)
    .slice(0, 3); // Top 3 suggestions

    return results;
  }, []);

  // String similarity calculation using Levenshtein distance
  const calculateSimilarity = useCallback((str1: string, str2: string): number => {
    const longer = str1.length > str2.length ? str1 : str2;
    const shorter = str1.length > str2.length ? str2 : str1;
    
    if (longer.length === 0) return 100;

    const distance = levenshteinDistance(longer, shorter);
    return Math.round(((longer.length - distance) / longer.length) * 100);
  }, []);

  const levenshteinDistance = useCallback((str1: string, str2: string): number => {
    const matrix = Array(str2.length + 1).fill(0).map(() => Array(str1.length + 1).fill(0));
    
    for (let i = 0; i <= str1.length; i++) matrix[0][i] = i;
    for (let j = 0; j <= str2.length; j++) matrix[j][0] = j;
    
    for (let j = 1; j <= str2.length; j++) {
      for (let i = 1; i <= str1.length; i++) {
        const cost = str1[i - 1] === str2[j - 1] ? 0 : 1;
        matrix[j][i] = Math.min(
          matrix[j - 1][i] + 1,     // deletion
          matrix[j][i - 1] + 1,     // insertion
          matrix[j - 1][i - 1] + cost // substitution
        );
      }
    }
    
    return matrix[str2.length][str1.length];
  }, []);

  // Handle file selection for validation
  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      validateTemplate(file);
    }
  };

  // Filter placeholders based on search and type
  const filteredPlaceholders = placeholders.filter(placeholder => {
    const matchesSearch = placeholder.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         placeholder.display_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         placeholder.description.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesFilter = filter === 'all' || placeholder.placeholder_type === filter;
    
    return matchesSearch && matchesFilter && placeholder.is_active;
  });

  // Group placeholders by type
  const groupedPlaceholders = filteredPlaceholders.reduce((acc, placeholder) => {
    const type = placeholder.placeholder_type || 'OTHER';
    if (!acc[type]) {
      acc[type] = [];
    }
    acc[type].push(placeholder);
    return acc;
  }, {} as Record<string, PlaceholderDefinition[]>);

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'DOCUMENT': return '📄';
      case 'USER': return '👤';
      case 'DATE': return '📅';
      case 'SYSTEM': return '⚙️';
      case 'CONDITIONAL': return '🔀';
      default: return '📋';
    }
  };

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'DOCUMENT': return 'bg-blue-50 border-blue-200 text-blue-800';
      case 'USER': return 'bg-green-50 border-green-200 text-green-800';
      case 'DATE': return 'bg-purple-50 border-purple-200 text-purple-800';
      case 'SYSTEM': return 'bg-orange-50 border-orange-200 text-orange-800';
      case 'CONDITIONAL': return 'bg-pink-50 border-pink-200 text-pink-800';
      default: return 'bg-gray-50 border-gray-200 text-gray-800';
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="bg-white shadow rounded-lg p-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Placeholder Reference</h2>
        <p className="text-gray-600">
          Browse available placeholders for use in document templates. Placeholders are automatically 
          replaced with actual values when documents are processed.
        </p>
      </div>

      {/* Template Validator */}
      <div className="bg-white shadow rounded-lg p-6">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Template Validator</h3>
          <button
            onClick={() => setShowTemplateValidator(!showTemplateValidator)}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            {showTemplateValidator ? 'Hide Validator' : 'Validate Template'}
          </button>
        </div>
        
        {showTemplateValidator && (
          <div className="space-y-4">
            <div className="border-2 border-dashed border-gray-300 rounded-lg p-6">
              <div className="text-center">
                <svg className="mx-auto h-12 w-12 text-gray-400" stroke="currentColor" fill="none" viewBox="0 0 48 48">
                  <path d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
                <div className="mt-4">
                  <label htmlFor="template-file" className="cursor-pointer">
                    <span className="mt-2 block text-sm font-medium text-gray-900">
                      Upload .docx template to validate placeholders
                    </span>
                    <input
                      id="template-file"
                      name="template-file"
                      type="file"
                      accept=".docx"
                      className="sr-only"
                      onChange={handleFileSelect}
                    />
                    <span className="mt-1 block text-sm text-gray-600">
                      or drag and drop your template file here
                    </span>
                  </label>
                </div>
              </div>
            </div>

            {validating && (
              <div className="flex items-center space-x-2 text-blue-600">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                <span>Validating template...</span>
              </div>
            )}

            {templateValidation && (
              <div className={`border rounded-lg p-6 ${templateValidation.isValid ? 'border-green-200 bg-green-50' : 'border-red-200 bg-red-50'}`}>
                <div className="flex justify-between items-center mb-4">
                  <h4 className="text-lg font-semibold">Template Analysis: {templateValidation.fileName || 'Unknown File'}</h4>
                  <div className="text-right">
                    <div className={`text-sm font-medium ${templateValidation.isValid ? 'text-green-700' : 'text-red-700'}`}>
                      {templateValidation.isValid ? '✅ Valid Template' : '❌ Issues Found'}
                    </div>
                    <div className="text-xs text-gray-600">
                      {templateValidation.totalPatternsFound || 0} patterns • {templateValidation.totalIssues || 0} issues
                    </div>
                  </div>
                </div>

                {/* 1. Identified Placeholders */}
                {templateValidation.identifiedPlaceholders && templateValidation.identifiedPlaceholders.length > 0 && (
                  <div className="mb-4">
                    <h5 className="font-medium text-green-700 mb-2">✅ Identified Placeholders ({templateValidation.identifiedPlaceholders?.length || 0})</h5>
                    <div className="bg-white border border-green-200 rounded p-3">
                      <div className="flex flex-wrap gap-2">
                        {(templateValidation.identifiedPlaceholders || []).map(placeholder => (
                          <code key={placeholder} className="px-2 py-1 bg-green-100 text-green-800 rounded text-xs">
                            {`{{${placeholder}}}`}
                          </code>
                        ))}
                      </div>
                    </div>
                  </div>
                )}

                {/* 2. Misformatted Placeholders */}
                {templateValidation.misformattedPlaceholders && templateValidation.misformattedPlaceholders.length > 0 && (
                  <div className="mb-4">
                    <h5 className="font-medium text-orange-700 mb-2">🔧 Misformatted Placeholders ({templateValidation.misformattedPlaceholders?.length || 0})</h5>
                    <div className="bg-white border border-orange-200 rounded p-3 space-y-2">
                      {(templateValidation.misformattedPlaceholders || []).map((item, index) => (
                        <div key={index} className="flex justify-between items-center text-sm">
                          <div>
                            <code className="px-1 bg-orange-100 text-orange-800 rounded">{item.placeholder}</code>
                            <span className="text-gray-600 ml-2">{item.issue}</span>
                          </div>
                          <div className="text-orange-700">
                            → <code className="px-1 bg-green-100 text-green-800 rounded">{item.suggestion}</code>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* 3. Unknown Placeholders */}
                {templateValidation.unknownPlaceholders && templateValidation.unknownPlaceholders.length > 0 && (
                  <div className="mb-4">
                    <h5 className="font-medium text-red-700 mb-2">❓ Unknown Placeholders ({templateValidation.unknownPlaceholders?.length || 0})</h5>
                    <div className="bg-white border border-red-200 rounded p-3 space-y-2">
                      {(templateValidation.unknownPlaceholders || []).map((item, index) => (
                        <div key={index} className="text-sm">
                          <div className="flex items-center mb-1">
                            <code className="px-1 bg-red-100 text-red-800 rounded">{item.placeholder}</code>
                            <span className="text-gray-600 ml-2">Not found in system</span>
                          </div>
                          {item.suggestions && item.suggestions.length > 0 && (
                            <div className="ml-4 text-gray-700">
                              <span className="text-xs text-gray-500">Did you mean:</span>
                              {(item.suggestions || []).map((suggestion, sIndex) => (
                                <code key={sIndex} className="ml-2 px-1 bg-blue-100 text-blue-800 rounded text-xs">
                                  {suggestion}
                                </code>
                              ))}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* 4. Unmatched Patterns */}
                {templateValidation.unmatchedPatterns && templateValidation.unmatchedPatterns.length > 0 && (
                  <div className="mb-4">
                    <h5 className="font-medium text-purple-700 mb-2">🔍 Unmatched Patterns ({templateValidation.unmatchedPatterns?.length || 0})</h5>
                    <div className="bg-white border border-purple-200 rounded p-3 space-y-2">
                      {(templateValidation.unmatchedPatterns || []).map((item, index) => (
                        <div key={index} className="flex justify-between items-center text-sm">
                          <div>
                            <code className="px-1 bg-purple-100 text-purple-800 rounded">{item.placeholder}</code>
                            <span className="text-gray-600 ml-2">{item.issue}</span>
                          </div>
                          <div className="text-purple-700 text-xs">
                            {item.confidence > 0 ? (
                              <>→ <code className="px-1 bg-green-100 text-green-800 rounded">{item.suggestion}</code></>
                            ) : (
                              <span className="text-gray-500">{item.suggestion}</span>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* 5. Unused Placeholders */}
                {templateValidation.unusedPlaceholders && Object.keys(templateValidation.unusedPlaceholders).length > 0 && (
                  <div className="mb-4">
                    <h5 className="font-medium text-blue-700 mb-2">📋 Available Placeholders Not Used</h5>
                    <div className="bg-white border border-blue-200 rounded p-3 space-y-3">
                      {Object.entries(templateValidation.unusedPlaceholders || {}).map(([category, placeholders]) => (
                        <div key={category}>
                          <div className="text-sm font-medium text-blue-900 mb-1">
                            {category} ({placeholders.length})
                          </div>
                          <div className="flex flex-wrap gap-1">
                            {(placeholders || []).slice(0, 10).map(placeholder => (
                              <code key={placeholder} className="px-2 py-1 bg-blue-50 text-blue-700 rounded text-xs">
                                {`{{${placeholder}}}`}
                              </code>
                            ))}
                            {(placeholders || []).length > 10 && (
                              <span className="text-xs text-gray-500 px-2 py-1">
                                ... and {(placeholders || []).length - 10} more
                              </span>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Error Summary */}
                {templateValidation.errors && templateValidation.errors.length > 0 && (
                  <div className="text-red-700 text-sm">
                    {(templateValidation.errors || []).map((error, index) => (
                      <p key={index}>• {error}</p>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Search and Filter */}
      <div className="bg-white shadow rounded-lg p-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label htmlFor="search" className="block text-sm font-medium text-gray-700 mb-2">
              Search Placeholders
            </label>
            <input
              type="text"
              id="search"
              placeholder="Search by name, display name, or description..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
          <div>
            <label htmlFor="filter" className="block text-sm font-medium text-gray-700 mb-2">
              Filter by Type
            </label>
            <select
              id="filter"
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="all">All Types</option>
              <option value="DOCUMENT">Document</option>
              <option value="USER">User</option>
              <option value="DATE">Date</option>
              <option value="SYSTEM">System</option>
              <option value="CONDITIONAL">Conditional</option>
            </select>
          </div>
        </div>
      </div>

      {/* Statistics */}
      <div className="bg-white shadow rounded-lg p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Statistics</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center">
            <div className="text-3xl font-bold text-blue-600">{placeholders.length}</div>
            <div className="text-sm text-gray-600">Total Placeholders</div>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold text-green-600">{placeholders.filter(p => p.is_active).length}</div>
            <div className="text-sm text-gray-600">Active</div>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold text-purple-600">{Object.keys(groupedPlaceholders).length}</div>
            <div className="text-sm text-gray-600">Categories</div>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold text-orange-600">{filteredPlaceholders.length}</div>
            <div className="text-sm text-gray-600">Filtered Results</div>
          </div>
        </div>
      </div>

      {/* Placeholders by Category */}
      <div className="space-y-6">
        {Object.entries(groupedPlaceholders).map(([type, typePlaceholders]) => (
          <div key={type} className="bg-white shadow rounded-lg overflow-hidden">
            <div className={`px-6 py-4 border-b ${getTypeColor(type)} border-l-4`}>
              <h3 className="text-lg font-semibold flex items-center">
                <span className="mr-2">{getTypeIcon(type)}</span>
                {type.charAt(0) + type.slice(1).toLowerCase()} Placeholders
                <span className="ml-2 text-sm font-normal">({typePlaceholders.length})</span>
              </h3>
            </div>
            <div className="p-6">
              <div className="grid gap-4">
                {typePlaceholders.map((placeholder) => (
                  <div key={placeholder.id} className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 transition-colors">
                    <div className="flex justify-between items-start">
                      <div className="flex-1">
                        <div className="flex items-center space-x-2">
                          <code className="px-2 py-1 bg-gray-100 text-gray-800 rounded text-sm font-mono">
                            {`{{${placeholder.name}}}`}
                          </code>
                          <span className="text-lg font-medium text-gray-900">
                            {placeholder.display_name}
                          </span>
                        </div>
                        <p className="text-gray-600 mt-1">{placeholder.description}</p>
                        <div className="flex items-center space-x-4 mt-2 text-sm text-gray-500">
                          <span>Source: {placeholder.data_source}</span>
                          {placeholder.default_value && (
                            <span>Default: {placeholder.default_value}</span>
                          )}
                        </div>
                      </div>
                      <div className="flex-shrink-0 ml-4">
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${placeholder.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                          {placeholder.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        ))}
      </div>

      {filteredPlaceholders.length === 0 && (
        <div className="text-center py-12">
          <div className="text-gray-400 text-lg">No placeholders found matching your search criteria</div>
        </div>
      )}

      {/* Usage Guide */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-blue-900 mb-2">📖 Usage Guide</h3>
        <div className="text-blue-800 space-y-2">
          <p><strong>In .docx templates:</strong> Use double braces like <code className="bg-blue-100 px-1 rounded">{`{{DOC_TITLE}}`}</code></p>
          <p><strong>Download processed documents:</strong> Use "Download Annotated" to get documents with placeholders replaced</p>
          <p><strong>Template validation:</strong> Upload your .docx templates above to check for valid placeholders</p>
          <p><strong>Official PDFs:</strong> Approved documents automatically include current metadata in PDF generation</p>
        </div>
      </div>
    </div>
  );
};

export default PlaceholderManagement;