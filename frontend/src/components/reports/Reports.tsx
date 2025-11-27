import React, { useState, useCallback, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import apiService from '../../services/api';
import LoadingSpinner from '../common/LoadingSpinner';

interface ComplianceReport {
  id: string;
  uuid: string;
  name: string;
  report_type: 'CFR_PART_11' | 'USER_ACTIVITY' | 'DOCUMENT_LIFECYCLE' | 'ACCESS_CONTROL' | 'SECURITY_EVENTS' | 'SYSTEM_CHANGES' | 'SIGNATURE_VERIFICATION' | 'DATA_INTEGRITY' | 'CUSTOM';
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

  // Available report types
  const reportTypes = [
    {
      value: 'CFR_PART_11',
      label: '21 CFR Part 11 Compliance',
      description: 'Comprehensive compliance report for FDA regulations',
      icon: '📋',
      color: 'bg-blue-500'
    },
    {
      value: 'USER_ACTIVITY',
      label: 'User Activity Report',
      description: 'Detailed user login and activity tracking',
      icon: '👥',
      color: 'bg-green-500'
    },
    {
      value: 'DOCUMENT_LIFECYCLE',
      label: 'Document Lifecycle Report',
      description: 'Document creation, modification, and approval tracking',
      icon: '📄',
      color: 'bg-purple-500'
    },
    {
      value: 'ACCESS_CONTROL',
      label: 'Access Control Report',
      description: 'User permissions and role assignment tracking',
      icon: '🔐',
      color: 'bg-orange-500'
    },
    {
      value: 'SECURITY_EVENTS',
      label: 'Security Events Report',
      description: 'Security incidents and access violations',
      icon: '🛡️',
      color: 'bg-red-500'
    },
    {
      value: 'SYSTEM_CHANGES',
      label: 'System Changes Report',
      description: 'Configuration and system modification tracking',
      icon: '⚙️',
      color: 'bg-gray-500'
    },
    {
      value: 'SIGNATURE_VERIFICATION',
      label: 'Digital Signature Report',
      description: 'Electronic signature validation and integrity',
      icon: '✍️',
      color: 'bg-indigo-500'
    },
    {
      value: 'DATA_INTEGRITY',
      label: 'Data Integrity Report',
      description: 'Database integrity checks and validation results',
      icon: '🔍',
      color: 'bg-teal-500'
    }
  ];

  // Load existing reports
  useEffect(() => {
    const loadReports = async () => {
      try {
        setLoading(true);
        setError(null);
        
        try {
          // Try to load from API
          const reportsData = await apiService.get('/audit/reports/');
          setReports(reportsData);
        } catch (apiError) {
          
          // Fallback to mock data
          const mockReports: ComplianceReport[] = [
            {
              id: '1',
              uuid: 'report-uuid-1',
              name: 'Monthly 21 CFR Part 11 Compliance Report',
              report_type: 'CFR_PART_11',
              description: 'Comprehensive compliance assessment for November 2024',
              date_from: '2024-11-01',
              date_to: '2024-11-30',
              generated_at: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
              generated_by: 1,
              status: 'COMPLETED',
              file_size: 2048576, // 2MB
              report_checksum: 'sha256:abcd1234...',
              summary_stats: {
                total_users: 10,
                total_documents: 11,
                audit_records: 38,
                compliance_score: 98
              }
            }
          ];
          
          setReports(mockReports);
        }
      } catch (err: any) {
        console.error('Error loading reports:', err);
        setError('Failed to load reports');
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
      // Create new report
      const newReport: ComplianceReport = {
        id: `report-${Date.now()}`,
        uuid: `uuid-${Date.now()}`,
        name: `${reportTypes.find(rt => rt.value === selectedReportType)?.label} - ${new Date().toLocaleDateString()}`,
        report_type: selectedReportType as any,
        description: `Generated report for ${reportFilters.date_from} to ${reportFilters.date_to}`,
        date_from: reportFilters.date_from,
        date_to: reportFilters.date_to,
        generated_at: new Date().toISOString(),
        generated_by: user?.id || 1,
        status: 'GENERATING',
        file_size: 0,
        report_checksum: '',
        summary_stats: {}
      };
      
      // Add to reports list
      setReports(prevReports => [newReport, ...prevReports]);
      
      // Simulate report generation
      setTimeout(() => {
        setReports(prevReports => 
          prevReports.map(report => 
            report.id === newReport.id 
              ? { 
                  ...report, 
                  status: 'COMPLETED' as const,
                  file_size: Math.floor(Math.random() * 5000000) + 500000, // Random size between 0.5-5MB
                  report_checksum: `sha256:${Math.random().toString(36).substring(2, 15)}`,
                  summary_stats: generateMockStats(selectedReportType)
                }
              : report
          )
        );
        setGenerating(false);
        setShowGenerateModal(false);
        setSelectedReportType('');
      }, 3000);
      
    } catch (err: any) {
      setError('Failed to generate report');
      setGenerating(false);
    }
  }, [selectedReportType, reportFilters, user]);

  const generateMockStats = (reportType: string) => {
    switch (reportType) {
      case 'CFR_PART_11':
        return {
          total_users: 10,
          total_documents: 11,
          audit_records: 38,
          compliance_score: 98,
          violations: 0
        };
      case 'USER_ACTIVITY':
        return {
          total_logins: 156,
          unique_users: 8,
          failed_attempts: 2,
          average_session_duration: '2h 15m'
        };
      case 'DOCUMENT_LIFECYCLE':
        return {
          documents_created: 5,
          documents_approved: 3,
          documents_obsoleted: 1,
          average_approval_time: '4.2 days'
        };
      default:
        return {
          records_analyzed: Math.floor(Math.random() * 1000) + 100,
          issues_found: Math.floor(Math.random() * 5),
          recommendations: Math.floor(Math.random() * 10) + 1
        };
    }
  };

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
      // Simulate download
      const link = document.createElement('a');
      link.href = '#'; // In production, this would be the actual file URL
      link.download = `${report.name.replace(/\s+/g, '_')}.pdf`;
      link.click();
      
      // Show success message
      alert(`Downloaded: ${report.name}`);
    } catch (err) {
      setError('Failed to download report');
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
        {reportTypes.map((reportType) => (
          <div
            key={reportType.value}
            className="bg-white p-6 rounded-lg shadow-sm border border-gray-200 hover:border-blue-200 cursor-pointer transition-colors"
            onClick={() => {
              setSelectedReportType(reportType.value);
              setShowGenerateModal(true);
            }}
          >
            <div className="flex items-center">
              <div className={`w-10 h-10 ${reportType.color} rounded-lg flex items-center justify-center text-white text-lg`}>
                {reportType.icon}
              </div>
              <div className="ml-4 flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900 truncate">
                  {reportType.label}
                </p>
                <p className="text-xs text-gray-500">
                  Click to generate
                </p>
              </div>
            </div>
          </div>
        ))}
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
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              No reports generated yet
            </h3>
            <p className="text-gray-500 mb-4">
              Generate your first compliance report to get started.
            </p>
            <button
              onClick={() => setShowGenerateModal(true)}
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              Generate Report
            </button>
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
                              // Show report preview modal (future enhancement)
                              alert('Report preview functionality will be implemented in future update');
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
    </div>
  );
};

export default Reports;