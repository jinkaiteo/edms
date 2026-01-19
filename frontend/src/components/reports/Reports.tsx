import React, { useState, useCallback, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext.tsx';
import { apiService } from '../../services/api.ts';
import LoadingSpinner from '../common/LoadingSpinner.tsx';

interface ComplianceReport {
  id: string;
  uuid: string;
  name: string;
  report_type: 'CFR_PART_11' | 'USER_ACTIVITY' | 'DOCUMENT_LIFECYCLE' | 'ACCESS_CONTROL' | 'SECURITY_EVENTS' | 'SYSTEM_CHANGES' | 'DATA_INTEGRITY' | 'CUSTOM';
  description: string;
  date_from: string;
  date_to: string;
  generated_at: string;
  generated_by: number;
  status: 'GENERATING' | 'COMPLETED' | 'FAILED' | 'ARCHIVED';
  file_size: number;
  report_checksum: string;
  summary_stats: any;
}

interface ReportFilters {
  date_from: string;
  date_to: string;
  report_type: string;
  include_user_activity: boolean;
  include_document_changes: boolean;
  include_security_events: boolean;
  include_compliance_checks: boolean;
}

interface ReportsProps {
  className?: string;
}

const Reports: React.FC<ReportsProps> = ({ className = '' }) => {
  const [reports, setReports] = useState<ComplianceReport[]>([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showGenerateModal, setShowGenerateModal] = useState(false);
  const [selectedReportType, setSelectedReportType] = useState<string>('');
  const [showPreviewModal, setShowPreviewModal] = useState(false);
  const [previewReport, setPreviewReport] = useState<ComplianceReport | null>(null);
  const [reportFilters, setReportFilters] = useState<ReportFilters>({
    date_from: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    date_to: new Date().toISOString().split('T')[0],
    report_type: '',
    include_user_activity: true,
    include_document_changes: true,
    include_security_events: true,
    include_compliance_checks: true
  });
  const { user } = useAuth();

  // Available report types with data availability status
  const reportTypes = [
    {
      value: 'CFR_PART_11',
      label: '21 CFR Part 11 Compliance',
      description: 'Comprehensive compliance report for FDA regulations',
      icon: '📋',
      color: 'bg-blue-500',
      dataStatus: 'partial' // Has audit trail data
    },
    {
      value: 'USER_ACTIVITY',
      label: 'User Activity Report',
      description: 'Detailed user login and activity tracking',
      icon: '👥',
      color: 'bg-green-500',
      dataStatus: 'partial' // Has audit data but no login tracking yet
    },
    {
      value: 'DOCUMENT_LIFECYCLE',
      label: 'Document Lifecycle Report',
      description: 'Document creation, modification, and approval tracking',
      icon: '📄',
      color: 'bg-purple-500',
      dataStatus: 'ready' // Has document data
    },
    {
      value: 'ACCESS_CONTROL',
      label: 'Access Control Report',
      description: 'User permissions and role assignment tracking',
      icon: '🔐',
      color: 'bg-orange-500',
      dataStatus: 'limited' // No role assignment data yet
    },
    {
      value: 'SECURITY_EVENTS',
      label: 'Security Events Report',
      description: 'Security incidents and access violations',
      icon: '🛡️',
      color: 'bg-red-500',
      dataStatus: 'limited' // Will populate with usage
    },
    {
      value: 'SYSTEM_CHANGES',
      label: 'System Changes Report',
      description: 'Configuration and system modification tracking',
      icon: '⚙️',
      color: 'bg-gray-500',
      dataStatus: 'limited' // Minimal system change data
    },
    // Digital Signature Report removed - not implemented
    // Uncomment when digital signature module is complete:
    // {
    //   value: 'SIGNATURE_VERIFICATION',
    //   label: 'Digital Signature Report',
    //   description: 'Electronic signature validation and integrity',
    //   icon: '✍️',
    //   color: 'bg-indigo-500',
    //   dataStatus: 'not-implemented'
    // },
    {
      value: 'DATA_INTEGRITY',
      label: 'Data Integrity Report',
      description: 'Database integrity checks and validation results',
      icon: '🔍',
      color: 'bg-teal-500',
      dataStatus: 'setup-required' // Needs scheduled checks
    }
  ];

  // Load existing reports
  useEffect(() => {
    const loadReports = async () => {
      try {
        setLoading(true);
        setError(null);
        
        // Use correct API endpoint (apiService already has /api/v1 in baseURL)
        const response = await apiService.get('/audit/compliance/');
        // Handle both paginated and non-paginated responses
        const reportsData = Array.isArray(response) ? response : (response.results || []);
        setReports(reportsData);
      } catch (err: any) {
        console.error('Error loading reports:', err);
        const errorMessage = err.response?.data?.detail || err.message || 'Failed to load compliance reports from server';
        setError(errorMessage);
        // No mock data fallback - show empty state with informative message
        setReports([]);
      } finally {
        setLoading(false);
      }
    };

    loadReports();
  }, []);

  const handleGenerateReport = useCallback(async () => {
    if (!selectedReportType) return;
    
    setGenerating(true);
    setError(null);
    
    try {
      // Generate report name
      const reportName = `${reportTypes.find(rt => rt.value === selectedReportType)?.label} - ${new Date().toLocaleDateString()}`;
      
      // Call backend API to generate report (apiService already has /api/v1 in baseURL)
      const response = await apiService.post('/audit/compliance/', {
        report_type: selectedReportType,
        name: reportName,
        description: `Generated report for ${reportFilters.date_from} to ${reportFilters.date_to}`,
        date_from: reportFilters.date_from,
        date_to: reportFilters.date_to,
        filters: {
          include_user_activity: reportFilters.include_user_activity,
          include_document_changes: reportFilters.include_document_changes,
          include_security_events: reportFilters.include_security_events,
          include_compliance_checks: reportFilters.include_compliance_checks,
        }
      });
      
      // Add the newly generated report to the list
      setReports(prevReports => [response, ...prevReports]);
      
      setGenerating(false);
      setShowGenerateModal(false);
      setSelectedReportType('');
      
      // Show success message
      console.log('✅ Report generated successfully:', response.name);
      
    } catch (err: any) {
      console.error('❌ Failed to generate report:', err);
      console.error('Error details:', {
        message: err.message,
        response: err.response?.data,
        status: err.response?.status,
        error: err.error,
        fullError: err
      });
      
      // Handle ApiService error format: { error: { code, message, timestamp } }
      let errorMessage = 'Failed to generate report';
      
      if (err.error?.message) {
        errorMessage = err.error.message;
      } else if (err.response?.data?.error) {
        errorMessage = err.response.data.error;
      } else if (err.response?.data?.detail) {
        errorMessage = err.response.data.detail;
      } else if (err.message) {
        errorMessage = err.message;
      }
      
      setError(errorMessage);
      setGenerating(false);
    }
  }, [selectedReportType, reportFilters, user]);


  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'GENERATING': return 'bg-yellow-100 text-yellow-800';
      case 'COMPLETED': return 'bg-green-100 text-green-800';
      case 'FAILED': return 'bg-red-100 text-red-800';
      case 'ARCHIVED': return 'bg-gray-100 text-gray-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const handleDownloadReport = useCallback(async (report: ComplianceReport) => {
    try {
      // Check if report is completed
      if (report.status !== 'COMPLETED') {
        setError('Report is not yet completed');
        return;
      }
      
      // Get base URL and token
      const baseURL = apiService.getBaseURL();
      const token = localStorage.getItem('accessToken');
      
      // Call backend download endpoint
      const response = await fetch(`${baseURL}/audit/compliance/${report.id}/download/`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.error || 'Failed to download report');
      }
      
      // Get the blob from response
      const blob = await response.blob();
      
      // Create download link
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `${report.name.replace(/\s+/g, '_')}.pdf`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      
      console.log('✅ Report downloaded successfully:', report.name);
    } catch (err: any) {
      console.error('❌ Failed to download report:', err);
      setError(err.message || 'Failed to download report');
    }
  }, []);

  if (loading) {
    return (
      <div className={`flex justify-center items-center py-8 ${className}`}>
        <LoadingSpinner />
      </div>
    );
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Reports</h2>
          <p className="text-gray-600 mt-1">
            Generate and manage compliance reports for regulatory submissions
          </p>
        </div>
        
        <button
          onClick={() => setShowGenerateModal(true)}
          disabled={generating}
          className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
        >
          📊 Generate Report
        </button>
      </div>

      {/* Quick Report Types Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {reportTypes.map((reportType) => {
          // Data availability badge
          const getDataBadge = (status: string) => {
            switch (status) {
              case 'ready':
                return { text: 'Ready', color: 'bg-green-100 text-green-800', icon: '✓' };
              case 'partial':
                return { text: 'Partial Data', color: 'bg-yellow-100 text-yellow-800', icon: '⚠' };
              case 'limited':
                return { text: 'Limited Data', color: 'bg-orange-100 text-orange-800', icon: '◐' };
              case 'setup-required':
                return { text: 'Setup Required', color: 'bg-blue-100 text-blue-800', icon: '⚙' };
              default:
                return { text: 'Available', color: 'bg-gray-100 text-gray-800', icon: '●' };
            }
          };

          const badge = getDataBadge(reportType.dataStatus || 'available');

          return (
            <div
              key={reportType.value}
              className="bg-white p-6 rounded-lg shadow-sm border border-gray-200 hover:border-blue-200 cursor-pointer transition-colors relative"
              onClick={() => {
                setSelectedReportType(reportType.value);
                setShowGenerateModal(true);
              }}
            >
              {/* Data Status Badge */}
              <div className="absolute top-2 right-2">
                <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${badge.color}`}>
                  <span className="mr-1">{badge.icon}</span>
                  {badge.text}
                </span>
              </div>

              <div className="flex items-center">
                <div className={`w-10 h-10 ${reportType.color} rounded-lg flex items-center justify-center text-white text-lg`}>
                  {reportType.icon}
                </div>
                <div className="ml-4 flex-1 min-w-0 pr-20">
                  <p className="text-sm font-medium text-gray-900 truncate">
                    {reportType.label}
                  </p>
                  <p className="text-xs text-gray-500">
                    Click to generate
                  </p>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Error Display */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-sm text-red-700">{error}</p>
            </div>
          </div>
        </div>
      )}

      {/* Generated Reports List */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">Generated Reports</h3>
          <p className="text-sm text-gray-600 mt-1">
            {reports.length} report{reports.length !== 1 ? 's' : ''} available for download
          </p>
        </div>
        
        {reports.length === 0 ? (
          <div className="p-8 text-center">
            <div className="text-6xl mb-4">📊</div>
            {error ? (
              <div>
                <h3 className="text-lg font-medium text-red-600 mb-2">
                  Unable to Load Reports
                </h3>
                <p className="text-gray-600 mb-3">{error}</p>
                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mt-4 text-left">
                  <p className="text-sm text-yellow-800 font-medium mb-2">Troubleshooting:</p>
                  <ul className="text-xs text-yellow-700 space-y-1 list-disc list-inside">
                    <li>Verify the audit API is accessible at <code className="bg-yellow-100 px-1 rounded">/api/v1/audit/compliance/</code></li>
                    <li>Check backend logs for authentication or permission errors</li>
                    <li>Ensure your user account has admin/audit permissions</li>
                  </ul>
                </div>
              </div>
            ) : (
              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-2">
                  No Compliance Reports Generated Yet
                </h3>
                <p className="text-gray-600 mb-2">
                  Generate your first compliance report to get started.
                </p>
                <p className="text-xs text-gray-500 mb-4">
                  Reports help meet regulatory requirements including 21 CFR Part 11
                </p>
                <button
                  onClick={() => setShowGenerateModal(true)}
                  className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                >
                  Generate Report
                </button>
              </div>
            )}
          </div>
        ) : (
          <div className="divide-y divide-gray-200">
            {reports.map((report) => {
              const reportTypeInfo = reportTypes.find(rt => rt.value === report.report_type);
              
              return (
                <div key={report.id} className="p-6 hover:bg-gray-50">
                  <div className="flex items-center justify-between">
                    <div className="flex items-start space-x-4">
                      <div className={`w-10 h-10 ${reportTypeInfo?.color || 'bg-gray-500'} rounded-lg flex items-center justify-center text-white text-lg flex-shrink-0`}>
                        {reportTypeInfo?.icon || '📄'}
                      </div>
                      
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center space-x-2 mb-1">
                          <h4 className="text-sm font-medium text-gray-900 truncate">
                            {report.name}
                          </h4>
                          
                          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(report.status)}`}>
                            {report.status}
                          </span>
                        </div>
                        
                        <p className="text-sm text-gray-600 mb-2">
                          {report.description}
                        </p>
                        
                        <div className="flex items-center space-x-4 text-xs text-gray-500">
                          <span>Generated: {formatDate(report.generated_at)}</span>
                          <span>Period: {report.date_from} to {report.date_to}</span>
                          {report.file_size > 0 && <span>Size: {formatFileSize(report.file_size)}</span>}
                        </div>
                        
                        {/* Report Summary Stats */}
                        {report.summary_stats && Object.keys(report.summary_stats).length > 0 && (
                          <div className="mt-3 flex flex-wrap gap-2">
                            {Object.entries(report.summary_stats).map(([key, value]) => (
                              <span key={key} className="inline-flex items-center px-2 py-1 rounded text-xs bg-blue-100 text-blue-800">
                                {key.replace(/_/g, ' ')}: {value}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>
                    
                    <div className="flex items-center space-x-2">
                      {report.status === 'GENERATING' && (
                        <div className="flex items-center space-x-2">
                          <LoadingSpinner />
                          <span className="text-sm text-gray-600">Generating...</span>
                        </div>
                      )}
                      
                      {report.status === 'COMPLETED' && (
                        <>
                          <button
                            onClick={() => handleDownloadReport(report)}
                            className="inline-flex items-center px-3 py-1.5 border border-transparent text-xs font-medium rounded text-blue-700 bg-blue-100 hover:bg-blue-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                          >
                            Download
                          </button>
                          <button
                            onClick={() => {
                              setPreviewReport(report);
                              setShowPreviewModal(true);
                            }}
                            className="inline-flex items-center px-3 py-1.5 border border-gray-300 text-xs font-medium rounded text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500"
                          >
                            Preview
                          </button>
                        </>
                      )}
                      
                      {report.status === 'FAILED' && (
                        <button
                          onClick={() => {
                            // Retry generation
                            setReports(reports.map(r => 
                              r.id === report.id 
                                ? { ...r, status: 'GENERATING' as const }
                                : r
                            ));
                          }}
                          className="inline-flex items-center px-3 py-1.5 border border-transparent text-xs font-medium rounded text-red-700 bg-red-100 hover:bg-red-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
                        >
                          Retry
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Generate Report Modal */}
      {showGenerateModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-full max-w-2xl shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-lg font-medium text-gray-900">
                  Generate Compliance Report
                </h3>
                <button
                  onClick={() => {
                    setShowGenerateModal(false);
                    setSelectedReportType('');
                  }}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
              
              {/* Report Type Selection */}
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 mb-3">
                  Report Type
                </label>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {reportTypes.map((reportType) => (
                    <div
                      key={reportType.value}
                      className={`p-3 border-2 rounded-lg cursor-pointer transition-colors ${
                        selectedReportType === reportType.value
                          ? 'border-blue-500 bg-blue-50'
                          : 'border-gray-200 hover:border-gray-300'
                      }`}
                      onClick={() => setSelectedReportType(reportType.value)}
                    >
                      <div className="flex items-start space-x-3">
                        <div className={`w-8 h-8 ${reportType.color} rounded-md flex items-center justify-center text-white text-sm flex-shrink-0`}>
                          {reportType.icon}
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-gray-900">
                            {reportType.label}
                          </p>
                          <p className="text-xs text-gray-500 mt-1">
                            {reportType.description}
                          </p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
              
              {/* Date Range */}
              <div className="grid grid-cols-2 gap-4 mb-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    From Date
                  </label>
                  <input
                    type="date"
                    value={reportFilters.date_from}
                    onChange={(e) => setReportFilters({ ...reportFilters, date_from: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    To Date
                  </label>
                  <input
                    type="date"
                    value={reportFilters.date_to}
                    onChange={(e) => setReportFilters({ ...reportFilters, date_to: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>
              
              {/* Report Options */}
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 mb-3">
                  Include in Report
                </label>
                <div className="space-y-2">
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={reportFilters.include_user_activity}
                      onChange={(e) => setReportFilters({ ...reportFilters, include_user_activity: e.target.checked })}
                      className="mr-2"
                    />
                    <span className="text-sm text-gray-700">User Activity & Login Records</span>
                  </label>
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={reportFilters.include_document_changes}
                      onChange={(e) => setReportFilters({ ...reportFilters, include_document_changes: e.target.checked })}
                      className="mr-2"
                    />
                    <span className="text-sm text-gray-700">Document Changes & Workflow History</span>
                  </label>
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={reportFilters.include_security_events}
                      onChange={(e) => setReportFilters({ ...reportFilters, include_security_events: e.target.checked })}
                      className="mr-2"
                    />
                    <span className="text-sm text-gray-700">Security Events & Access Violations</span>
                  </label>
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={reportFilters.include_compliance_checks}
                      onChange={(e) => setReportFilters({ ...reportFilters, include_compliance_checks: e.target.checked })}
                      className="mr-2"
                    />
                    <span className="text-sm text-gray-700">Compliance Validation & Integrity Checks</span>
                  </label>
                </div>
              </div>
              
              <div className="flex justify-end space-x-3">
                <button
                  onClick={() => {
                    setShowGenerateModal(false);
                    setSelectedReportType('');
                  }}
                  disabled={generating}
                  className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-500 disabled:opacity-50"
                >
                  Cancel
                </button>
                <button
                  onClick={handleGenerateReport}
                  disabled={generating || !selectedReportType}
                  className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
                >
                  {generating ? 'Generating...' : 'Generate Report'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Preview Modal */}
      {showPreviewModal && previewReport && (
        <div className="fixed z-10 inset-0 overflow-y-auto" aria-labelledby="modal-title" role="dialog" aria-modal="true">
          <div className="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
            <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" aria-hidden="true" onClick={() => setShowPreviewModal(false)}></div>
            <span className="hidden sm:inline-block sm:align-middle sm:h-screen" aria-hidden="true">&#8203;</span>
            
            <div className="inline-block align-bottom bg-white rounded-lg px-4 pt-5 pb-4 text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-4xl sm:w-full sm:p-6">
              <div className="absolute top-0 right-0 pt-4 pr-4">
                <button
                  type="button"
                  className="bg-white rounded-md text-gray-400 hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                  onClick={() => setShowPreviewModal(false)}
                >
                  <span className="sr-only">Close</span>
                  <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>

              <div className="sm:flex sm:items-start">
                <div className="mt-3 text-center sm:mt-0 sm:text-left w-full">
                  <h3 className="text-2xl leading-6 font-bold text-gray-900 mb-4" id="modal-title">
                    Report Preview
                  </h3>
                  
                  {/* Report Header */}
                  <div className="bg-blue-50 rounded-lg p-4 mb-6">
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="text-lg font-semibold text-gray-900">{previewReport.name}</h4>
                      <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                        previewReport.status === 'COMPLETED' ? 'bg-green-100 text-green-800' :
                        previewReport.status === 'GENERATING' ? 'bg-yellow-100 text-yellow-800' :
                        previewReport.status === 'FAILED' ? 'bg-red-100 text-red-800' :
                        'bg-gray-100 text-gray-800'
                      }`}>
                        {previewReport.status}
                      </span>
                    </div>
                    <p className="text-sm text-gray-600">{previewReport.description}</p>
                  </div>

                  {/* Report Metadata */}
                  <div className="grid grid-cols-2 gap-4 mb-6">
                    <div className="bg-white border border-gray-200 rounded-lg p-4">
                      <dt className="text-sm font-medium text-gray-500 mb-1">Report Type</dt>
                      <dd className="text-lg font-semibold text-gray-900">
                        {reportTypes.find(rt => rt.value === previewReport.report_type)?.label || previewReport.report_type}
                      </dd>
                    </div>
                    
                    <div className="bg-white border border-gray-200 rounded-lg p-4">
                      <dt className="text-sm font-medium text-gray-500 mb-1">Report Period</dt>
                      <dd className="text-sm text-gray-900">
                        {new Date(previewReport.date_from).toLocaleDateString()} - {new Date(previewReport.date_to).toLocaleDateString()}
                      </dd>
                    </div>
                    
                    <div className="bg-white border border-gray-200 rounded-lg p-4">
                      <dt className="text-sm font-medium text-gray-500 mb-1">Generated At</dt>
                      <dd className="text-sm text-gray-900">
                        {new Date(previewReport.generated_at).toLocaleString()}
                      </dd>
                    </div>
                    
                    <div className="bg-white border border-gray-200 rounded-lg p-4">
                      <dt className="text-sm font-medium text-gray-500 mb-1">File Size</dt>
                      <dd className="text-sm text-gray-900">
                        {(previewReport.file_size / 1024).toFixed(2)} KB
                      </dd>
                    </div>
                  </div>

                  {/* Summary Statistics */}
                  {previewReport.summary_stats && Object.keys(previewReport.summary_stats).length > 0 && (
                    <div className="mb-6">
                      <h5 className="text-lg font-semibold text-gray-900 mb-3">Summary Statistics</h5>
                      <div className="bg-gray-50 rounded-lg p-4">
                        <dl className="grid grid-cols-2 gap-4">
                          {Object.entries(previewReport.summary_stats).map(([key, value]) => (
                            <div key={key} className="border-b border-gray-200 pb-2">
                              <dt className="text-sm font-medium text-gray-600 capitalize">
                                {key.replace(/_/g, ' ')}
                              </dt>
                              <dd className="text-2xl font-bold text-blue-600 mt-1">
                                {typeof value === 'number' ? value.toLocaleString() : String(value)}
                              </dd>
                            </div>
                          ))}
                        </dl>
                      </div>
                    </div>
                  )}

                  {/* Report Checksum */}
                  <div className="bg-gray-50 rounded-lg p-4 mb-6">
                    <h5 className="text-sm font-medium text-gray-700 mb-2">Report Integrity</h5>
                    <div className="flex items-center space-x-2">
                      <svg className="h-5 w-5 text-green-500" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                      </svg>
                      <span className="text-xs text-gray-600 font-mono">
                        UUID: {previewReport.uuid}
                      </span>
                    </div>
                  </div>

                  {/* Action Buttons */}
                  <div className="mt-5 sm:mt-6 sm:grid sm:grid-cols-2 sm:gap-3 sm:grid-flow-row-dense">
                    {previewReport.status === 'COMPLETED' && (
                      <button
                        type="button"
                        className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-blue-600 text-base font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 sm:col-start-2 sm:text-sm"
                        onClick={() => {
                          handleDownloadReport(previewReport);
                          setShowPreviewModal(false);
                        }}
                      >
                        Download PDF
                      </button>
                    )}
                    <button
                      type="button"
                      className="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500 sm:mt-0 sm:col-start-1 sm:text-sm"
                      onClick={() => setShowPreviewModal(false)}
                    >
                      Close
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Reports;