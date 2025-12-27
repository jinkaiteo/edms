import { useState, useEffect, useCallback } from 'react';

export interface AsyncState<T> {
  data: T | null;
  loading: boolean;
  error: Error | null;
  lastUpdated: Date | null;
}

export interface UseAsyncReturn<T> extends AsyncState<T> {
  execute: () => Promise<void>;
  reset: () => void;
  setData: (data: T | null) => void;
}

export interface UseAsyncOptions {
  immediate?: boolean;
  onSuccess?: (data: any) => void;
  onError?: (error: Error) => void;
  retries?: number;
  retryDelay?: number;
}

/**
 * Custom hook for handling async operations with loading states and error handling
 */
export function useAsync<T = any>(
  asyncFunction: () => Promise<T>,
  dependencies: React.DependencyList = [],
  options: UseAsyncOptions = {}
): UseAsyncReturn<T> {
  const {
    immediate = true,
    onSuccess,
    onError,
    retries = 0,
    retryDelay = 1000
  } = options;

  const [state, setState] = useState<AsyncState<T>>({
    data: null,
    loading: false,
    error: null,
    lastUpdated: null,
  });

  const execute = useCallback(async (retryCount = 0): Promise<void> => {
    setState(prev => ({ ...prev, loading: true, error: null }));

    try {
      const data = await asyncFunction();
      setState({
        data,
        loading: false,
        error: null,
        lastUpdated: new Date(),
      });
      onSuccess?.(data);
    } catch (error) {
      const errorObj = error instanceof Error ? error : new Error(String(error));
      
      // Retry logic
      if (retryCount < retries) {
        setTimeout(() => {
          execute(retryCount + 1);
        }, retryDelay * Math.pow(2, retryCount)); // Exponential backoff
        return;
      }

      setState(prev => ({
        ...prev,
        loading: false,
        error: errorObj,
      }));
      onError?.(errorObj);
    }
  }, [asyncFunction, onSuccess, onError, retries, retryDelay]);

  const reset = useCallback(() => {
    setState({
      data: null,
      loading: false,
      error: null,
      lastUpdated: null,
    });
  }, []);

  const setData = useCallback((data: T | null) => {
    setState(prev => ({
      ...prev,
      data,
      lastUpdated: new Date(),
    }));
  }, []);

  useEffect(() => {
    if (immediate) {
      execute();
    }
  }, dependencies); // eslint-disable-line react-hooks/exhaustive-deps

  return {
    ...state,
    execute,
    reset,
    setData,
  };
}

export default useAsync;