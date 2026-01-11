import { useState, useEffect, useCallback } from 'react';
import { DashboardStats } from '../types/api';

interface UseDashboardUpdatesOptions {
  enabled?: boolean;
  autoRefreshInterval?: number;
  onError?: (error: Error) => void;
  onUpdate?: (stats: DashboardStats) => void;
}

/**
 * Dashboard updates hook using HTTP polling
 * Supports admin dashboard with proper stats structure
 */
export const useDashboardUpdates = (options: UseDashboardUpdatesOptions = {}) => {
  const {
    enabled = true,
    autoRefreshInterval = 60000,
    onError,
    onUpdate
  } = options;

  const [dashboardStats, setDashboardStats] = useState<DashboardStats | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isPaused, setIsPaused] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const fetchDashboardStats = useCallback(async () => {
    if (!enabled || isPaused) return;

    try {
      setIsLoading(true);
      setIsRefreshing(true);
      setError(null);
      
      const token = localStorage.getItem('accessToken');
      if (!token) {
        throw new Error('No authentication token found');
      }

      const response = await fetch('/api/v1/dashboard/stats/', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch dashboard stats: ${response.statusText}`);
      }

      const data = await response.json();
      setDashboardStats(data);
      
      if (onUpdate) {
        onUpdate(data);
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      console.error('Failed to fetch dashboard stats:', err);
      setError(errorMessage);
      
      if (onError && err instanceof Error) {
        onError(err);
      }
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  }, [enabled, isPaused, onError, onUpdate]);

  const refreshNow = useCallback(() => {
    fetchDashboardStats();
  }, [fetchDashboardStats]);

  const toggle = useCallback(() => {
    setIsPaused(prev => !prev);
  }, []);

  // Poll for updates
  useEffect(() => {
    if (!enabled) return;

    // Initial fetch
    fetchDashboardStats();
    
    // Set up polling interval
    const interval = setInterval(fetchDashboardStats, autoRefreshInterval);
    
    return () => clearInterval(interval);
  }, [enabled, autoRefreshInterval, fetchDashboardStats]);

  return {
    dashboardStats,
    isLoading,
    error,
    refreshNow,
    autoRefreshConfig: {
      isPaused,
      isRefreshing,
      toggle
    }
  };
};
