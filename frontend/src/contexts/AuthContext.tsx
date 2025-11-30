import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
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
  permissions?: string[];
  roles?: Array<{
    id: number;
    name: string;
    permission_level: string;
    module: string;
  }>;
}

interface AuthContextType {
  user: User | null;
  authenticated: boolean;
  loading: boolean;
  login: (username: string, password: string) => Promise<any>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [authenticated, setAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true); // Start with loading true


  // Initialize auth state on mount - restore from localStorage
  useEffect(() => {
    const initializeAuth = async () => {
      
      try {
        const accessToken = localStorage.getItem('accessToken');
        const refreshToken = localStorage.getItem('refreshToken');
        
        if (accessToken && refreshToken) {
          
          // Try to get user profile with stored token
          const profileResponse = await fetch('/api/v1/auth/profile/', {
            headers: {
              'Authorization': `Bearer ${accessToken}`,
              'Content-Type': 'application/json',
            },
          });
          
          if (profileResponse.ok) {
            const userProfile = await profileResponse.json();
            
            // CRITICAL: Set token in apiService for restored session
            apiService.setAuthToken(accessToken);
            
            setUser(userProfile);
            setAuthenticated(true);
          } else {
            localStorage.removeItem('accessToken');
            localStorage.removeItem('refreshToken');
          }
        } else {
        }
      } catch (error) {
        console.error('❌ AuthContext: Error initializing auth:', error);
        localStorage.removeItem('accessToken');
        localStorage.removeItem('refreshToken');
      }
      
      setLoading(false);
    };
    
    initializeAuth();
  }, []);

  const login = async (username: string, password: string) => {
    setLoading(true);
    
    try {
      const response = await fetch('/api/v1/auth/token/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({ username, password }),
      });

      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();

      if (data.access && data.refresh) {
        localStorage.setItem('accessToken', data.access);
        localStorage.setItem('refreshToken', data.refresh);
        
        // CRITICAL: Set token in apiService so it includes in all API requests
        apiService.setAuthToken(data.access);
        
        // Fetch user profile with the token
        const profileResponse = await fetch('/api/v1/auth/profile/', {
          headers: {
            'Authorization': `Bearer ${data.access}`,
            'Content-Type': 'application/json',
          },
        });
        
        if (profileResponse.ok) {
          const userProfile = await profileResponse.json();
          setUser(userProfile);
          setAuthenticated(true);
          return { success: true, user: userProfile, tokens: data };
        } else {
          throw new Error('Failed to fetch user profile');
        }
      } else {
        throw new Error('Invalid login response format');
      }
    } catch (error) {
      console.error('❌ AuthContext: Login error:', error);
      setUser(null);
      setAuthenticated(false);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const logout = async () => {
    try {
      const accessToken = localStorage.getItem('accessToken');
      
      if (accessToken) {
        await fetch('/api/v1/auth/logout/', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${accessToken}`,
            'Content-Type': 'application/json',
          },
        });
      }
    } catch (error) {
      console.error('Logout error:', error);
      // Continue with logout even if API call fails
    }
    
    // Clear stored tokens and state
    localStorage.removeItem('accessToken');
    localStorage.removeItem('refreshToken');
    
    // CRITICAL: Clear token from apiService
    apiService.clearAuth();
    
    setUser(null);
    setAuthenticated(false);
  };

  return (
    <AuthContext.Provider value={{ user, authenticated, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};