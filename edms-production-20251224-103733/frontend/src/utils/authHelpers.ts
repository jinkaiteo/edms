/**
 * Authentication helper utilities for EDMS frontend
 */

export interface AuthTokens {
  accessToken?: string;
  refreshToken?: string;
}

export class AuthHelpers {
  
  /**
   * Get current authentication tokens
   */
  static getTokens(): AuthTokens {
    return {
      accessToken: localStorage.getItem('accessToken') || undefined,
      refreshToken: localStorage.getItem('refreshToken') || undefined,
    };
  }

  /**
   * Set authentication tokens
   */
  static setTokens(tokens: AuthTokens): void {
    if (tokens.accessToken) {
      localStorage.setItem('accessToken', tokens.accessToken);
    }
    if (tokens.refreshToken) {
      localStorage.setItem('refreshToken', tokens.refreshToken);
    }
  }

  /**
   * Clear all authentication tokens
   */
  static clearTokens(): void {
    localStorage.removeItem('accessToken');
    localStorage.removeItem('refreshToken');
  }

  /**
   * Check if user is authenticated
   */
  static isAuthenticated(): boolean {
    const tokens = this.getTokens();
    return !!tokens.accessToken;
  }

  /**
   * Get authorization header for API requests
   */
  static getAuthHeader(): Record<string, string> {
    const tokens = this.getTokens();
    
    if (tokens.accessToken) {
      return {
        'Authorization': `Bearer ${tokens.accessToken}`
      };
    }
    
    return {};
  }

  /**
   * Get CSRF token from cookies for session authentication
   */
  static getCSRFToken(): string | null {
    const cookies = document.cookie.split(';');
    const csrfCookie = cookies.find(cookie => 
      cookie.trim().startsWith('csrftoken=')
    );
    
    if (csrfCookie) {
      return csrfCookie.split('=')[1];
    }
    
    return null;
  }

  /**
   * Get session authentication headers
   */
  static getSessionHeaders(): Record<string, string> {
    const csrfToken = this.getCSRFToken();
    const headers: Record<string, string> = {};
    
    if (csrfToken) {
      headers['X-CSRFToken'] = csrfToken;
    }
    
    return headers;
  }

  /**
   * Get combined authentication headers (JWT + Session)
   */
  static getAllAuthHeaders(): Record<string, string> {
    return {
      ...this.getAuthHeader(),
      ...this.getSessionHeaders(),
    };
  }

  /**
   * Login with credentials and store tokens
   * Default system password is 'test123' for all users
   */
  static async login(credentials: { username: string; password: string }): Promise<AuthTokens> {
    const baseURL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';
    
    try {
      // Try JWT authentication first
      const jwtResponse = await fetch(`${baseURL}/auth/token/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify(credentials),
      });

      if (jwtResponse.ok) {
        const data = await jwtResponse.json();
        const tokens: AuthTokens = {
          accessToken: data.access,
          refreshToken: data.refresh,
        };
        
        this.setTokens(tokens);
        return tokens;
      }
      
      throw new Error(`Login failed: ${jwtResponse.statusText}`);
      
    } catch (error) {
      console.error('Login error:', error);
      throw error;
    }
  }

  /**
   * Refresh JWT token
   */
  static async refreshToken(): Promise<string | null> {
    const tokens = this.getTokens();
    
    if (!tokens.refreshToken) {
      return null;
    }

    const baseURL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';
    
    try {
      const response = await fetch(`${baseURL}/auth/token/refresh/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
          refresh: tokens.refreshToken
        }),
      });

      if (response.ok) {
        const data = await response.json();
        const newToken = data.access;
        
        localStorage.setItem('accessToken', newToken);
        return newToken;
      }
      
      // Refresh failed, clear tokens
      this.clearTokens();
      return null;
      
    } catch (error) {
      console.error('Token refresh error:', error);
      this.clearTokens();
      return null;
    }
  }

  /**
   * Make authenticated API request
   */
  static async authenticatedFetch(url: string, options: RequestInit = {}): Promise<Response> {
    const headers = {
      'Content-Type': 'application/json',
      ...this.getAllAuthHeaders(),
      ...options.headers,
    };

    const response = await fetch(url, {
      ...options,
      headers,
      credentials: 'include',
    });

    // If unauthorized, try to refresh token and retry
    if (response.status === 401 && this.isAuthenticated()) {
      const newToken = await this.refreshToken();
      
      if (newToken) {
        // Retry with new token
        const retryHeaders = {
          ...headers,
          'Authorization': `Bearer ${newToken}`,
        };
        
        return fetch(url, {
          ...options,
          headers: retryHeaders,
          credentials: 'include',
        });
      }
    }

    return response;
  }
}