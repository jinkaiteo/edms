import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';

interface User {
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

  console.log('🔄 AuthContext state:', { authenticated, user: user?.username, loading });

  // Initialize auth state on mount - restore from localStorage
  useEffect(() => {
    const initializeAuth = async () => {
      console.log('🔄 AuthContext: Initializing authentication...');
      
      try {
        const accessToken = localStorage.getItem('accessToken');
        const refreshToken = localStorage.getItem('refreshToken');
        
        if (accessToken && refreshToken) {
          console.log('🔑 AuthContext: Found stored tokens, validating...');
          
          // Try to get user profile with stored token
          const profileResponse = await fetch('http://localhost:8000/api/v1/auth/profile/', {
            headers: {
              'Authorization': `Bearer ${accessToken}`,
              'Content-Type': 'application/json',
            },
          });
          
          if (profileResponse.ok) {
            const userProfile = await profileResponse.json();
            console.log('✅ AuthContext: Token valid, restoring user session');
            setUser(userProfile);
            setAuthenticated(true);
          } else {
            console.log('❌ AuthContext: Token expired, clearing storage');
            localStorage.removeItem('accessToken');
            localStorage.removeItem('refreshToken');
          }
        } else {
          console.log('ℹ️ AuthContext: No stored tokens found');
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
    console.log('🔐 AuthContext: Starting login process...', { username });
    setLoading(true);
    
    try {
      const response = await fetch('http://localhost:8000/api/v1/auth/token/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({ username, password }),
      });

      console.log('📡 AuthContext: API Response status:', response.status);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      console.log('📥 AuthContext: Login response data:', data);

      if (data.access && data.refresh) {
        console.log('✅ AuthContext: Login successful, storing tokens...');
        localStorage.setItem('accessToken', data.access);
        localStorage.setItem('refreshToken', data.refresh);
        
        // Fetch user profile with the token
        const profileResponse = await fetch('http://localhost:8000/api/v1/auth/profile/', {
          headers: {
            'Authorization': `Bearer ${data.access}`,
            'Content-Type': 'application/json',
          },
        });
        
        if (profileResponse.ok) {
          const userProfile = await profileResponse.json();
          setUser(userProfile);
          setAuthenticated(true);
          console.log('🎯 AuthContext: Global auth state updated:', { authenticated: true, user: userProfile.username });
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
    console.log('🚪 AuthContext: Logging out...');
    try {
      const accessToken = localStorage.getItem('accessToken');
      
      if (accessToken) {
        await fetch('http://localhost:8000/api/v1/auth/logout/', {
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
    setUser(null);
    setAuthenticated(false);
    console.log('🚪 AuthContext: User logged out successfully');
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