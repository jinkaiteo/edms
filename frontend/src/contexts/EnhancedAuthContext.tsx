/**
 * Enhanced Authentication Context
 * 
 * Provides comprehensive authentication management with automatic
 * token handling, session management, and API integration.
 */

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { apiService } from '../services/api.ts';

interface User {
  id: number;
  uuid: string;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  is_staff: boolean;
  is_superuser: boolean;
  last_login: string | null;
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshAuth: () => Promise<void>;
  getAuthHeaders: () => Record<string, string>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useEnhancedAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useEnhancedAuth must be used within an EnhancedAuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: React.ReactNode;
}

export const EnhancedAuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  // Get authentication headers for API calls
  const getAuthHeaders = useCallback((): Record<string, string> => {
    const token = localStorage.getItem('accessToken');
    if (token) {
      return {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      };
    }
    return {
      'Content-Type': 'application/json',
    };
  }, []);

  // Login function
  const login = useCallback(async (username: string, password: string): Promise<void> => {
    console.log('🔐 Enhanced Auth: Starting login process...', { username });
    setIsLoading(true);

    try {
      // Use API service for login
      const loginResponse = await apiService.login({ username, password });
      
      console.log('📡 Enhanced Auth: Login response:', loginResponse);

      if (loginResponse.access) {
        // Set token in API service
        apiService.setAuthToken(loginResponse.access);
        
        // Store tokens
        localStorage.setItem('accessToken', loginResponse.access);
        if (loginResponse.refresh) {
          localStorage.setItem('refreshToken', loginResponse.refresh);
        }

        // Get user information
        try {
          const userData = await apiService.getCurrentUser();
          console.log('👤 Enhanced Auth: User data retrieved:', userData);
          
          setUser(userData);
          setIsAuthenticated(true);
          
          console.log('✅ Enhanced Auth: Login successful');
        } catch (userError) {
          console.warn('⚠️ Enhanced Auth: Could not fetch user data, but login successful');
          // Still consider login successful if we have a token
          setIsAuthenticated(true);
        }
      } else {
        throw new Error('No access token received');
      }
    } catch (error) {
      console.error('❌ Enhanced Auth: Login failed:', error);
      // Clear any partial state
      setUser(null);
      setIsAuthenticated(false);
      apiService.clearAuth();
      throw error;
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Logout function
  const logout = useCallback(async (): Promise<void> => {
    console.log('🚪 Enhanced Auth: Logging out...');
    setIsLoading(true);

    try {
      // Call API logout
      await apiService.logout();
    } catch (error) {
      console.warn('⚠️ Enhanced Auth: Logout API call failed, clearing local state anyway');
    }

    // Clear local state
    setUser(null);
    setIsAuthenticated(false);
    apiService.clearAuth();
    
    // Clear storage
    localStorage.removeItem('accessToken');
    localStorage.removeItem('refreshToken');
    
    console.log('✅ Enhanced Auth: Logged out successfully');
    setIsLoading(false);
  }, []);

  // Refresh authentication status
  const refreshAuth = useCallback(async (): Promise<void> => {
    console.log('🔄 Enhanced Auth: Refreshing authentication...');
    const token = localStorage.getItem('accessToken');
    
    if (!token) {
      console.log('❌ Enhanced Auth: No token found');
      setUser(null);
      setIsAuthenticated(false);
      setIsLoading(false);
      return;
    }

    try {
      // Set token in API service
      apiService.setAuthToken(token);
      
      // Try to get current user to verify token is still valid
      const userData = await apiService.getCurrentUser();
      
      console.log('✅ Enhanced Auth: Token valid, user authenticated');
      setUser(userData);
      setIsAuthenticated(true);
    } catch (error) {
      console.warn('⚠️ Enhanced Auth: Token invalid or expired, clearing auth');
      // Token is invalid, clear everything
      setUser(null);
      setIsAuthenticated(false);
      apiService.clearAuth();
      localStorage.removeItem('accessToken');
      localStorage.removeItem('refreshToken');
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Initialize authentication on component mount
  useEffect(() => {
    console.log('🚀 Enhanced Auth: Initializing...');
    refreshAuth();
  }, [refreshAuth]);

  // Auto-refresh token periodically (optional)
  useEffect(() => {
    if (isAuthenticated) {
      const intervalId = setInterval(() => {
        console.log('🔄 Enhanced Auth: Periodic token check...');
        refreshAuth();
      }, 5 * 60 * 1000); // Check every 5 minutes

      return () => clearInterval(intervalId);
    }
  }, [isAuthenticated, refreshAuth]);

  const contextValue: AuthContextType = {
    user,
    isAuthenticated,
    isLoading,
    login,
    logout,
    refreshAuth,
    getAuthHeaders,
  };

  return (
    <AuthContext.Provider value={contextValue}>
      {children}
    </AuthContext.Provider>
  );
};

export default EnhancedAuthProvider;