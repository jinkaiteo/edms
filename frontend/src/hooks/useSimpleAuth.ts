/**
 * Simplified authentication hook focused on login and navigation
 */
import { useState } from 'react';

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

export const useSimpleAuth = () => {
  const [user, setUser] = useState<User | null>(null);
  const [authenticated, setAuthenticated] = useState(false);
  const [loading, setLoading] = useState(false);

  const login = async (username: string, password: string) => {
    console.log('🔐 Starting login process...', { username });
    setLoading(true);
    
    try {
      // Make direct API call to login endpoint
      const response = await fetch('http://localhost:8000/api/v1/auth/login/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include', // Include cookies for session
        body: JSON.stringify({ username, password }),
      });

      console.log('📡 API Response status:', response.status);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      console.log('📥 Login response data:', data);

      if (data.success) {
        console.log('✅ Login successful, setting user state...');
        setUser(data.user);
        setAuthenticated(true);
        console.log('🎯 Auth state updated:', { authenticated: true, user: data.user.username });
        return data;
      } else {
        throw new Error(data.error || 'Login failed');
      }
    } catch (error) {
      console.error('❌ Login error:', error);
      setUser(null);
      setAuthenticated(false);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const logout = async () => {
    console.log('🚪 Logging out...');
    try {
      await fetch('http://localhost:8000/api/v1/auth/logout/', {
        method: 'POST',
        credentials: 'include',
      });
    } catch (error) {
      console.error('Logout error:', error);
    }
    
    setUser(null);
    setAuthenticated(false);
    console.log('✅ Logged out, auth state cleared');
  };

  return {
    user,
    authenticated,
    loading,
    login,
    logout,
  };
};