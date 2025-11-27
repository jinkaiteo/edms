/**
 * Custom hook for dashboard real-time updates
 * 
 * Combines auto-refresh polling and WebSocket real-time updates
 * for optimal dashboard data synchronization.
 */

import { useCallback, useEffect, useState } from 'react';
import { useAutoRefresh } from './useAutoRefresh.ts';
import { useWebSocket } from './useWebSocket.ts';
import { apiService } from '../services/api.ts';
import { DashboardStats } from '../types/api.ts';

interface UseDashboardUpdatesOptions {
  enabled?: boolean;
  autoRefreshInterval?: number;
  useWebSocket?: boolean;
  onError?: (error: Error) => void;
  onUpdate?: (stats: DashboardStats) => void;
}

interface UseDashboardUpdatesReturn {
  dashboardStats: DashboardStats | null;
  isLoading: boolean;
  error: string | null;
  connectionState: 'connecting' | 'connected' | 'disconnected' | 'error';
  refreshNow: () => Promise<void>;
  autoRefreshConfig: {
    isRefreshing: boolean;
    isPaused: boolean;
    lastRefresh: Date | null;
    nextRefresh: Date | null;
    pause: () => void;
    resume: () => void;
    toggle: () => void;
  };
}

export const useDashboardUpdates = ({
  enabled = true,
  autoRefreshInterval = 300000, // 5 minutes
  useWebSocket: enableWebSocket = false,
  onError,
  onUpdate
}: UseDashboardUpdatesOptions): UseDashboardUpdatesReturn => {
  const [dashboardStats, setDashboardStats] = useState<DashboardStats | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Function to fetch dashboard data from API
  const fetchDashboardStats = useCallback(async (): Promise<void> => {
    if (!enabled) return;

    setIsLoading(true);
    setError(null);

    try {
      const stats = await apiService.getDashboardStats();
      
      setDashboardStats(stats);
      onUpdate?.(stats);

    } catch (err: any) {
      console.error('❌ Failed to fetch dashboard statistics:', err);
      const errorMessage = err?.response?.data?.detail || err?.message || 'Failed to load dashboard data';
      setError(errorMessage);
      onError?.(err);

      // Set fallback data on error only if no data exists yet
      setDashboardStats(prevStats => {
        if (prevStats === null) {
          return {
            total_documents: 0,
            pending_reviews: 0,
            active_workflows: 0,
            active_users: 0,
            placeholders: 0,
            audit_entries_24h: 0,
            recent_activity: [],
            timestamp: new Date().toISOString(),
            cache_duration: 0
          };
        }
        return prevStats; // Keep existing data if API fails
      });
    } finally {
      setIsLoading(false);
    }
  }, [enabled, onError, onUpdate]);

  // Auto-refresh configuration
  const autoRefresh = useAutoRefresh({
    refreshFn: fetchDashboardStats,
    interval: autoRefreshInterval,
    enabled: enabled,
    onError: onError
  });

  // WebSocket configuration for real-time updates
  const webSocket = useWebSocket({
    url: `${process.env.REACT_APP_WS_BASE_URL || 'ws://localhost:8000'}/ws/dashboard/`,
    enabled: enableWebSocket && enabled,
    onOpen: () => {
    },
    onMessage: (event) => {
      try {
        const data = JSON.parse(event.data);
        
        if (data.type === 'dashboard_update') {
          setDashboardStats(data.payload);
          onUpdate?.(data.payload);
        } else if (data.type === 'stats_partial_update') {
          // Handle partial updates (e.g., just user count change)
          setDashboardStats(prevStats => {
            if (!prevStats) return prevStats;
            return {
              ...prevStats,
              ...data.payload,
              timestamp: new Date().toISOString()
            };
          });
        }
      } catch (err) {
        console.error('Failed to parse WebSocket message:', err);
      }
    },
    onClose: (event) => {
    },
    onError: (event) => {
      console.error('❌ Dashboard WebSocket error:', event);
    },
    shouldReconnect: true,
    reconnectInterval: 5000,
    maxReconnectAttempts: 5
  });

  // Initial data load
  useEffect(() => {
    if (enabled) {
      fetchDashboardStats();
    }
  }, [enabled]); // Only run on enabled change, not on fetchDashboardStats change

  // Manual refresh function
  const refreshNow = useCallback(async (): Promise<void> => {
    return await autoRefresh.refreshNow();
  }, [autoRefresh.refreshNow]);

  return {
    dashboardStats,
    isLoading,
    error,
    connectionState: enableWebSocket ? webSocket.connectionState : 'disconnected',
    refreshNow,
    autoRefreshConfig: {
      isRefreshing: autoRefresh.isRefreshing,
      isPaused: autoRefresh.isPaused,
      lastRefresh: autoRefresh.lastRefresh,
      nextRefresh: autoRefresh.nextRefresh,
      pause: autoRefresh.pause,
      resume: autoRefresh.resume,
      toggle: autoRefresh.toggle
    }
  };
};