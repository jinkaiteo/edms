/**
 * React Hooks for API Integration
 * 
 * Custom hooks for managing API calls, loading states,
 * and error handling throughout the application.
 */

import { useState, useEffect, useCallback } from 'react';
import { apiService } from '../services/api.ts';
import { ApiError } from '../types/api.ts';

// Generic API hook for any async operation
export function useApi<T>(
  apiFunction: () => Promise<T>,
  dependencies: any[] = [],
  immediate = true
) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState<boolean>(immediate);
  const [error, setError] = useState<ApiError | null>(null);

  const execute = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const result = await apiFunction();
      setData(result);
      return result;
    } catch (err) {
      const apiError = err as ApiError;
      setError(apiError);
      throw apiError;
    } finally {
      setLoading(false);
    }
  }, dependencies);

  useEffect(() => {
    if (immediate) {
      execute();
    }
  }, [execute, immediate]);

  const reset = useCallback(() => {
    setData(null);
    setError(null);
    setLoading(false);
  }, []);

  return {
    data,
    loading,
    error,
    execute,
    reset,
    refetch: execute
  };
}

// Authentication hooks
export function useAuth() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(false); // Changed to false initially
  const [authenticated, setAuthenticated] = useState(false);
  
  console.log('useAuth state:', { user, authenticated, loading });

  // Removed automatic auth check that was interfering with login
  
  const checkAuthStatus = async () => {
    console.log('checkAuthStatus called');
    try {
      // For session-based auth, try to get current user
      const userData = await apiService.getCurrentUser();
      console.log('getCurrentUser response:', userData);
      setUser(userData);
      setAuthenticated(true);
    } catch (error) {
      console.log('getCurrentUser failed:', error);
      setUser(null);
      setAuthenticated(false);
    } finally {
      setLoading(false);
    }
  };

  const login = async (username: string, password: string) => {
    setLoading(true);
    try {
      const response = await apiService.login({ username, password });
      console.log('Setting user in auth state:', response.user);
      setUser(response.user);
      setAuthenticated(true);
      console.log('Authentication state updated:', true);
      return response;
    } catch (error) {
      console.log('Login failed, clearing auth state');
      setUser(null);
      setAuthenticated(false);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const logout = async () => {
    setLoading(true);
    try {
      await apiService.logout();
    } catch (error) {
      // Ignore logout errors
    } finally {
      setUser(null);
      setAuthenticated(false);
      setLoading(false);
    }
  };

  return {
    user,
    authenticated,
    loading,
    login,
    logout,
    checkAuthStatus
  };
}

// Documents hooks
export function useDocuments(params?: any) {
  return useApi(
    () => apiService.getDocuments(params),
    [JSON.stringify(params)]
  );
}

export function useDocument(id: number) {
  return useApi(
    () => apiService.getDocument(id),
    [id],
    !!id
  );
}

export function useCreateDocument() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<ApiError | null>(null);

  const createDocument = async (data: any) => {
    setLoading(true);
    setError(null);
    try {
      const result = await apiService.createDocument(data);
      return result;
    } catch (err) {
      const apiError = err as ApiError;
      setError(apiError);
      throw apiError;
    } finally {
      setLoading(false);
    }
  };

  return { createDocument, loading, error };
}

export function useUpdateDocument() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<ApiError | null>(null);

  const updateDocument = async (id: number, data: any) => {
    setLoading(true);
    setError(null);
    try {
      const result = await apiService.updateDocument(id, data);
      return result;
    } catch (err) {
      const apiError = err as ApiError;
      setError(apiError);
      throw apiError;
    } finally {
      setLoading(false);
    }
  };

  return { updateDocument, loading, error };
}

// Search hooks
export function useSearch() {
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<ApiError | null>(null);

  const search = async (searchRequest: any) => {
    setLoading(true);
    setError(null);
    try {
      const result = await apiService.searchDocuments(searchRequest);
      setResults(result);
      return result;
    } catch (err) {
      const apiError = err as ApiError;
      setError(apiError);
      throw apiError;
    } finally {
      setLoading(false);
    }
  };

  const reset = () => {
    setResults(null);
    setError(null);
    setLoading(false);
  };

  return { results, loading, error, search, reset };
}

export function useAutocomplete() {
  const [suggestions, setSuggestions] = useState([]);
  const [loading, setLoading] = useState(false);

  const getSuggestions = useCallback(async (query: string) => {
    if (query.length < 2) {
      setSuggestions([]);
      return;
    }

    setLoading(true);
    try {
      const result = await apiService.getAutocomplete({ query });
      setSuggestions(result);
    } catch (error) {
      setSuggestions([]);
    } finally {
      setLoading(false);
    }
  }, []);

  return { suggestions, loading, getSuggestions };
}

// Workflows hooks
export function useWorkflowInstances(params?: any) {
  return useApi(
    () => apiService.getWorkflowInstances(params),
    [JSON.stringify(params)]
  );
}

export function useWorkflowInstance(id: number) {
  return useApi(
    () => apiService.getWorkflowInstance(id),
    [id],
    !!id
  );
}

export function useWorkflowTransition() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<ApiError | null>(null);

  const transitionWorkflow = async (id: number, data: any) => {
    setLoading(true);
    setError(null);
    try {
      const result = await apiService.transitionWorkflow(id, data);
      return result;
    } catch (err) {
      const apiError = err as ApiError;
      setError(apiError);
      throw apiError;
    } finally {
      setLoading(false);
    }
  };

  return { transitionWorkflow, loading, error };
}

// System Configuration hooks
export function useSystemConfigurations() {
  return useApi(() => apiService.getSystemConfigurations());
}

export function useUpdateSystemConfiguration() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<ApiError | null>(null);

  const updateConfiguration = async (id: number, value: string) => {
    setLoading(true);
    setError(null);
    try {
      const result = await apiService.updateSystemConfiguration(id, value);
      return result;
    } catch (err) {
      const apiError = err as ApiError;
      setError(apiError);
      throw apiError;
    } finally {
      setLoading(false);
    }
  };

  return { updateConfiguration, loading, error };
}

// Electronic Signatures hooks
export function useElectronicSignatures(params?: any) {
  return useApi(
    () => apiService.getElectronicSignatures(params),
    [JSON.stringify(params)]
  );
}

export function useSignDocument() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<ApiError | null>(null);

  const signDocument = async (data: any) => {
    setLoading(true);
    setError(null);
    try {
      const result = await apiService.signDocument(data);
      return result;
    } catch (err) {
      const apiError = err as ApiError;
      setError(apiError);
      throw apiError;
    } finally {
      setLoading(false);
    }
  };

  return { signDocument, loading, error };
}

// Audit Trail hooks
export function useAuditTrail(params?: any) {
  return useApi(
    () => apiService.getAuditTrail(params),
    [JSON.stringify(params)]
  );
}

// System Status hooks
export function useApiStatus() {
  return useApi(() => apiService.getApiStatus(), [], true);
}

export function useApiHealth() {
  return useApi(() => apiService.getApiHealth(), [], false);
}

// Dashboard hooks
export function useDashboardMetrics() {
  return useApi(() => apiService.getDashboardMetrics());
}

// Generic mutation hook
export function useMutation<T, P = any>() {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<ApiError | null>(null);

  const mutate = async (mutationFn: (params: P) => Promise<T>, params: P) => {
    setLoading(true);
    setError(null);
    try {
      const result = await mutationFn(params);
      setData(result);
      return result;
    } catch (err) {
      const apiError = err as ApiError;
      setError(apiError);
      throw apiError;
    } finally {
      setLoading(false);
    }
  };

  const reset = () => {
    setData(null);
    setError(null);
    setLoading(false);
  };

  return { data, loading, error, mutate, reset };
}

// Polling hook for real-time updates
export function usePolling<T>(
  apiFunction: () => Promise<T>,
  interval: number = 30000,
  enabled: boolean = true
) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<ApiError | null>(null);

  useEffect(() => {
    if (!enabled) return;

    const poll = async () => {
      try {
        setLoading(true);
        const result = await apiFunction();
        setData(result);
        setError(null);
      } catch (err) {
        setError(err as ApiError);
      } finally {
        setLoading(false);
      }
    };

    // Initial call
    poll();

    // Set up polling
    const intervalId = setInterval(poll, interval);

    return () => clearInterval(intervalId);
  }, [apiFunction, interval, enabled]);

  return { data, loading, error };
}