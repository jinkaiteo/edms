/**
 * Custom hook for auto-refresh functionality
 * 
 * Provides configurable auto-refresh with pause/resume capabilities
 * and manual refresh triggers.
 */

import { useEffect, useRef, useState, useCallback } from 'react';

interface UseAutoRefreshOptions {
  refreshFn: () => Promise<void>;
  interval?: number; // in milliseconds
  enabled?: boolean;
  onError?: (error: Error) => void;
}

interface UseAutoRefreshReturn {
  isRefreshing: boolean;
  isPaused: boolean;
  lastRefresh: Date | null;
  nextRefresh: Date | null;
  refreshNow: () => Promise<void>;
  pause: () => void;
  resume: () => void;
  toggle: () => void;
}

export const useAutoRefresh = ({
  refreshFn,
  interval = 300000, // 5 minutes default
  enabled = true,
  onError
}: UseAutoRefreshOptions): UseAutoRefreshReturn => {
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isPaused, setIsPaused] = useState(!enabled);
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null);
  const [nextRefresh, setNextRefresh] = useState<Date | null>(null);
  
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const refreshFnRef = useRef(refreshFn);
  
  // Update the refresh function ref when it changes
  useEffect(() => {
    refreshFnRef.current = refreshFn;
  }, [refreshFn]);
  
  // Calculate next refresh time
  const calculateNextRefresh = useCallback(() => {
    if (!isPaused && interval > 0) {
      return new Date(Date.now() + interval);
    }
    return null;
  }, [isPaused, interval]);
  
  // Manual refresh function
  const refreshNow = useCallback(async () => {
    if (isRefreshing) return;
    
    setIsRefreshing(true);
    try {
      await refreshFnRef.current();
      setLastRefresh(new Date());
      setNextRefresh(calculateNextRefresh());
    } catch (error) {
      console.error('Auto-refresh error:', error);
      onError?.(error as Error);
    } finally {
      setIsRefreshing(false);
    }
  }, [isRefreshing, calculateNextRefresh, onError]);
  
  // Pause auto-refresh
  const pause = useCallback(() => {
    setIsPaused(true);
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    setNextRefresh(null);
  }, []);
  
  // Resume auto-refresh
  const resume = useCallback(() => {
    setIsPaused(false);
    setNextRefresh(calculateNextRefresh());
  }, [calculateNextRefresh]);
  
  // Toggle pause/resume
  const toggle = useCallback(() => {
    if (isPaused) {
      resume();
    } else {
      pause();
    }
  }, [isPaused, resume, pause]);
  
  // Setup auto-refresh interval
  useEffect(() => {
    if (!isPaused && interval > 0) {
      intervalRef.current = setInterval(() => {
        refreshNow();
      }, interval);
      
      setNextRefresh(calculateNextRefresh());
      
      return () => {
        if (intervalRef.current) {
          clearInterval(intervalRef.current);
          intervalRef.current = null;
        }
      };
    }
  }, [isPaused, interval, refreshNow, calculateNextRefresh]);
  
  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, []);
  
  return {
    isRefreshing,
    isPaused,
    lastRefresh,
    nextRefresh,
    refreshNow,
    pause,
    resume,
    toggle
  };
};