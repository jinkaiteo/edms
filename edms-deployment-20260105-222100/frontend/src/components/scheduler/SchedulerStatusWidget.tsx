/**
 * Scheduler Status Widget Component
 * 
 * Provides real-time visual indicators for scheduler status in the main UI
 */

import React, { useState, useEffect } from 'react';
import apiService from '../../services/api.ts';

interface SchedulerStatus {
  overall_status: 'EXCELLENT' | 'GOOD' | 'WARNING' | 'CRITICAL' | 'FAILURE';
  health_score: number;
  health_breakdown?: {
    total_score: number;
    max_possible: number;
    score_interpretation: {
      level: string;
      description: string;
      color: string;
    };
    components: {
      [key: string]: {
        score: number;
        max_score: number;
        status: string;
        details: string;
        recommendation: string;
      };
    };
  };
  celery_status: {
    workers_active: boolean;
    beat_status: string;
    worker_count: number;
  };
  task_statistics: {
    documents_pending_effective: number;
    documents_scheduled_obsolescence: number;
    active_workflows: number;
    overdue_workflows: number;
  };
  alerts: Array<{
    level: 'CRITICAL' | 'WARNING' | 'INFO';
    message: string;
    action: string;
  }>;
}

interface SchedulerStatusWidgetProps {
  showDetails?: boolean;
  refreshInterval?: number;
}

const SchedulerStatusWidget: React.FC<SchedulerStatusWidgetProps> = ({
  showDetails = false,
  refreshInterval = 30000 // 30 seconds
}) => {
  const [status, setStatus] = useState<SchedulerStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());

  const fetchStatus = async () => {
    try {
      console.log('🔍 Fetching scheduler status...');
      const response = await apiService.get('/scheduler/monitoring/status/');
      console.log('📦 Full response:', response);
      console.log('📊 Response data:', response.data);
      console.log('🔍 Response keys:', Object.keys(response || {}));
      
      // Handle different response structures
      const data = response?.data || response;
      console.log('✅ Processed data:', data);
      
      if (data && typeof data === 'object' && data.overall_status) {
        setStatus(data);
        setError(null);
        setLastUpdate(new Date());
        console.log('🎯 Status set successfully:', data.overall_status, data.health_score);
      } else {
        console.warn('⚠️ Invalid data structure received:', data);
        setError('Invalid response format from scheduler API');
      }
    } catch (err) {
      console.error('❌ Scheduler status fetch error:', err);
      setError('Failed to fetch scheduler status');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
    
    const interval = setInterval(fetchStatus, refreshInterval);
    
    return () => clearInterval(interval);
  }, [refreshInterval]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'EXCELLENT': return 'text-green-600 bg-green-100';
      case 'GOOD': return 'text-green-500 bg-green-50';
      case 'WARNING': return 'text-yellow-600 bg-yellow-100';
      case 'CRITICAL': return 'text-orange-600 bg-orange-100';
      case 'FAILURE': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'EXCELLENT': return '✅';
      case 'GOOD': return '👍';
      case 'WARNING': return '⚠️';
      case 'CRITICAL': return '🔴';
      case 'FAILURE': return '❌';
      default: return '❓';
    }
  };

  const getHealthScoreColor = (score: number) => {
    if (score >= 90) return 'text-green-600';
    if (score >= 75) return 'text-green-500';
    if (score >= 50) return 'text-yellow-600';
    if (score >= 25) return 'text-orange-600';
    return 'text-red-600';
  };

  if (loading) {
    return (
      <div className="flex items-center space-x-2 text-gray-500">
        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-500"></div>
        <span className="text-sm">Checking scheduler...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center space-x-2 text-red-500">
        <span>⚠️</span>
        <span className="text-sm">Scheduler status unavailable</span>
      </div>
    );
  }

  if (!status) {
    return null;
  }

  // Compact view for header/navigation
  if (!showDetails) {
    return (
      <div className="flex items-center space-x-2">
        <div className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(status.overall_status)}`}>
          <span className="mr-1">{getStatusIcon(status.overall_status)}</span>
          Scheduler
        </div>
        
        {status.alerts.length > 0 && (
          <div className="relative">
            <span className="inline-flex items-center justify-center w-4 h-4 text-xs font-bold text-white bg-red-500 rounded-full">
              {status.alerts.length}
            </span>
          </div>
        )}
        
        <span className={`text-sm font-medium ${getHealthScoreColor(status.health_score)}`}>
          {status.health_score}%
        </span>
      </div>
    );
  }

  // Detailed view for dashboard
  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex justify-between items-start mb-4">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">Scheduler Status</h3>
          <p className="text-sm text-gray-500">Automated task monitoring</p>
        </div>
        
        <div className="text-right">
          <div className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(status.overall_status)}`}>
            <span className="mr-1">{getStatusIcon(status.overall_status)}</span>
            {status.overall_status}
          </div>
          <div className={`text-2xl font-bold ${getHealthScoreColor(status.health_score)} mt-1`}>
            {status.health_score}%
          </div>
        </div>
      </div>

      {/* Celery Infrastructure Status */}
      <div className="grid grid-cols-2 gap-4 mb-4">
        <div className={`p-3 rounded-lg ${status.celery_status.workers_active ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'}`}>
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-gray-600">Workers</span>
            <span className={`text-lg font-bold ${status.celery_status.workers_active ? 'text-green-600' : 'text-red-600'}`}>
              {status.celery_status.worker_count}
            </span>
          </div>
        </div>
        
        <div className={`p-3 rounded-lg ${status.celery_status.beat_status === 'RUNNING' ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'}`}>
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-gray-600">Beat</span>
            <span className={`text-sm font-bold ${status.celery_status.beat_status === 'RUNNING' ? 'text-green-600' : 'text-red-600'}`}>
              {status.celery_status.beat_status}
            </span>
          </div>
        </div>
      </div>

      {/* Task Statistics */}
      <div className="grid grid-cols-2 gap-4 mb-4 text-center">
        <div>
          <div className="text-2xl font-bold text-blue-600">{status.task_statistics.documents_pending_effective}</div>
          <div className="text-xs text-gray-500">Pending Effective</div>
        </div>
        <div>
          <div className="text-2xl font-bold text-orange-600">{status.task_statistics.overdue_workflows}</div>
          <div className="text-xs text-gray-500">Overdue Workflows</div>
        </div>
      </div>


      {/* Alerts */}
      {status.alerts.length > 0 && (
        <div className="space-y-2">
          <h4 className="text-sm font-medium text-gray-700">Active Alerts</h4>
          {status.alerts.map((alert, index) => (
            <div
              key={index}
              className={`p-2 rounded text-xs ${
                alert.level === 'CRITICAL' ? 'bg-red-100 text-red-800' :
                alert.level === 'WARNING' ? 'bg-yellow-100 text-yellow-800' :
                'bg-blue-100 text-blue-800'
              }`}
            >
              <div className="font-medium">{alert.message}</div>
              <div className="text-xs opacity-75 mt-1">{alert.action}</div>
            </div>
          ))}
        </div>
      )}

      {/* Health Score Breakdown */}
      {status.health_breakdown && (
        <div className="mt-4 pt-4 border-t border-gray-200">
          <div className="mb-3">
            <h4 className="text-sm font-medium text-gray-700 mb-2">Health Score Breakdown</h4>
            <div className="text-xs text-gray-600 mb-2">
              {status.health_breakdown.score_interpretation.description}
            </div>
          </div>
          
          <div className="space-y-2">
            {Object.entries(status.health_breakdown.components).map(([key, component]) => (
              <div key={key} className="flex items-center justify-between text-xs">
                <div className="flex-1">
                  <div className="flex items-center justify-between">
                    <span className="font-medium capitalize text-gray-700">
                      {key.replace(/_/g, ' ')}
                    </span>
                    <span className="text-gray-500">
                      {component.score}/{component.max_score}
                    </span>
                  </div>
                  <div className="text-gray-500 text-xs mt-1">{component.details}</div>
                  {component.recommendation !== 'Working properly' && 
                   component.recommendation !== 'Scheduler running normally' && 
                   component.recommendation !== 'Database operating normally' && 
                   component.recommendation !== 'All workflows on schedule' && 
                   component.recommendation !== 'No recent errors - system operating perfectly' && (
                    <div className="text-orange-600 text-xs mt-1 font-medium">
                      💡 {component.recommendation}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Quick Actions */}
      <div className="mt-4 pt-4 border-t border-gray-200">
        <div className="flex justify-between items-center">
          <span className="text-xs text-gray-500">
            Last updated: {lastUpdate.toLocaleTimeString()}
          </span>
          <a
            href="http://localhost:8000/admin/scheduler/monitoring/dashboard/"
            target="_blank"
            rel="noopener noreferrer"
            className="text-sm text-blue-600 hover:text-blue-800 font-medium"
          >
            Open Dashboard →
          </a>
        </div>
      </div>
    </div>
  );
};

export default SchedulerStatusWidget;