/**
 * Main Layout Component for EDMS Frontend
 * 
 * Provides the main application layout with navigation,
 * header, sidebar, and content areas.
 */

import React, { useState, useEffect } from 'react';
import { Outlet, Link, useLocation, useNavigate } from 'react-router-dom';
import {
  HomeIcon,
  DocumentTextIcon,
  Cog6ToothIcon,
  UserGroupIcon,
  ClipboardDocumentListIcon,
  BellIcon,
  UserIcon,
  ArrowRightOnRectangleIcon,
  Bars3Icon,
  XMarkIcon,
  ShieldCheckIcon,
  DocumentArrowUpIcon,
  ChartBarIcon,
  KeyIcon
} from '@heroicons/react/24/outline';
import { useAuth } from '../../contexts/AuthContext.tsx';
import { ApiStatus } from '../../types/api';
import { apiService } from '../../services/api.ts';
import ChangePasswordModal from '../auth/ChangePasswordModal.tsx';
// NotificationBell removed - counter moved to navigation item

interface LayoutProps {
  children?: React.ReactNode;
}

interface NavigationItem {
  name: string;
  href: string;
  icon: React.ComponentType<any>;
  current?: boolean;
  roles?: string[];
  badge?: number;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const { user, authenticated, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [apiStatus, setApiStatus] = useState<ApiStatus | null>(null);
  const [documentCount, setDocumentCount] = useState<number>(0);
  const [showChangePassword, setShowChangePassword] = useState(false);
  const [showProfileDropdown, setShowProfileDropdown] = useState(false);

  // Check API status on mount - temporarily disabled
  useEffect(() => {
    const checkStatus = async () => {
      try {
        // Temporarily disable API status check to avoid 404 errors
        // const status = await apiService.getApiStatus();
        // setApiStatus(status);
        
        // Set a default healthy status for now
        setApiStatus({ status: 'healthy', timestamp: Date.now() });
      } catch (error) {
        console.error('Failed to get API status:', error);
      }
    };
    
    if (authenticated) {
      checkStatus();
      // Check status every 5 minutes
      const interval = setInterval(checkStatus, 5 * 60 * 1000);
      return () => clearInterval(interval);
    }
  }, [authenticated]);

  // Poll for "Active Documents" count (documents in my tasks/pending states)
  useEffect(() => {
    const fetchMyDocumentsCount = async () => {
      try {
        // Use same API endpoint as Active Documents page for consistency
        const response = await fetch('/api/v1/documents/documents/?filter=my_tasks', {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('accessToken') || ''}`
          }
        });
        
        if (response.ok) {
          const data = await response.json();
          const documents = data.results || [];
          
          // Count matches exactly what Active Documents page shows
          setDocumentCount(documents.length);
          console.log(`📊 Active Documents badge: ${documents.length} documents in my tasks`);
          
          // Debug: Show breakdown
          if (documents.length > 0) {
            const statusBreakdown = documents.reduce((acc: any, doc: any) => {
              acc[doc.status] = (acc[doc.status] || 0) + 1;
              return acc;
            }, {});
            console.log('📋 Status breakdown:', statusBreakdown);
          }
        }
      } catch (err) {
        console.error('Failed to fetch active documents count:', err);
        setDocumentCount(0);
      }
    };

    if (authenticated && user) {
      // Initial fetch
      fetchMyDocumentsCount();
      
      // Poll every 60 seconds
      const interval = setInterval(fetchMyDocumentsCount, 60000);
      return () => clearInterval(interval);
    }
  }, [authenticated, user]);

  // Handle click outside dropdown to close it
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as Element;
      if (showProfileDropdown && !target.closest('.profile-dropdown')) {
        setShowProfileDropdown(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [showProfileDropdown]);

  // Navigation items based on user roles
  const getNavigationItems = (): NavigationItem[] => {
    const baseItems: NavigationItem[] = [
      { name: 'Document Library', href: '/', icon: DocumentArrowUpIcon },
      { name: 'Active Documents', href: '/?filter=pending', icon: ClipboardDocumentListIcon },
      { name: 'Obsolete Documents', href: '/?filter=obsolete', icon: DocumentTextIcon },
    ];

    // Add role-based items
    const adminItems: NavigationItem[] = [
      { name: 'Administration', href: '/admin', icon: Cog6ToothIcon, roles: ['admin'] },
    ];

    // Filter items based on user roles
    // For now, show admin items if user is admin (is_staff or is_superuser)
    const isAdmin = user?.is_staff || user?.is_superuser;
    const filteredAdminItems = adminItems.filter(item => 
      !item.roles || (item.roles.includes('admin') && isAdmin) || 
      (item.roles.includes('approver') && isAdmin)
    );

    return [...baseItems, ...filteredAdminItems];
  };

  const navigation = getNavigationItems().map(item => {
    // Handle query parameters for proper navigation highlighting
    const currentUrl = location.pathname + location.search;
    
    // Special case for filtered document views with query parameters
    if (item.href.includes('?filter=pending') || item.href.includes('?filter=obsolete')) {
      return {
        ...item,
        current: currentUrl === item.href,
        // Add counter badge to "Active Documents"
        badge: item.href.includes('?filter=pending') ? documentCount : undefined
      };
    }
    
    // For other items, check if pathname matches and no conflicting query params  
    const isPathMatch = (item.href === '/' && (location.pathname === '/' || location.pathname === '/document-management')) ||
                        location.pathname.startsWith(item.href);
    const hasFilterParam = location.search.includes('filter=pending') || location.search.includes('filter=obsolete');
    
    // "Document Library" should not be active if we're viewing filtered documents
    if (item.href === '/' && hasFilterParam) {
      return {
        ...item,
        current: false
      };
    }
    
    return {
      ...item,
      current: isPathMatch
    };
  });

  const handleLogout = async () => {
    try {
      await logout();
      navigate('/login');
    } catch (error) {
      console.error('Logout failed:', error);
    }
  };

  const handlePasswordChangeSuccess = () => {
    // Show success message with better styling
    const successMessage = document.createElement('div');
    successMessage.className = 'fixed top-4 right-4 bg-green-500 text-white px-6 py-3 rounded-lg shadow-lg z-50';
    successMessage.textContent = 'Password changed successfully!';
    document.body.appendChild(successMessage);
    
    // Remove after 3 seconds
    setTimeout(() => {
      if (successMessage.parentNode) {
        successMessage.parentNode.removeChild(successMessage);
      }
    }, 3000);
    
    setShowChangePassword(false);
  };

  if (!authenticated) {
    return <Outlet />;
  }

  return (
    <div className="h-screen flex">
      {/* Mobile sidebar */}
      <div className={`fixed inset-0 flex z-40 md:hidden ${sidebarOpen ? '' : 'hidden'}`}>
        <div className="fixed inset-0 bg-gray-600 bg-opacity-75" onClick={() => setSidebarOpen(false)} />
        <div className="relative flex-1 flex flex-col max-w-xs w-full pt-5 pb-4 bg-white">
          <div className="absolute top-0 right-0 -mr-12 pt-2">
            <button
              type="button"
              className="ml-1 flex items-center justify-center h-10 w-10 rounded-full focus:outline-none focus:ring-2 focus:ring-inset focus:ring-white"
              onClick={() => setSidebarOpen(false)}
            >
              <XMarkIcon className="h-6 w-6 text-white" />
            </button>
          </div>
          <div className="flex-shrink-0 flex items-center px-4">
            <h1 className="text-xl font-bold text-gray-900">EDMS</h1>
          </div>
          <div className="mt-5 flex-1 h-0 overflow-y-auto">
            <nav className="px-2 space-y-1">
              {navigation.map((item) => (
                <Link
                  key={item.name}
                  to={item.href}
                  className={`${
                    item.current
                      ? 'bg-gray-100 text-gray-900'
                      : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                  } group flex items-center px-2 py-2 text-sm font-medium rounded-md`}
                  onClick={() => setSidebarOpen(false)}
                >
                  <item.icon className="mr-3 flex-shrink-0 h-5 w-5" />
                  {item.name}
                  {item.badge && item.badge > 0 && (
                    <span className="ml-auto bg-red-100 text-red-800 text-xs font-medium px-2 py-0.5 rounded-full">
                      {item.badge}
                    </span>
                  )}
                </Link>
              ))}
            </nav>
          </div>
        </div>
      </div>

      {/* Static sidebar for desktop */}
      <div className="hidden md:flex md:w-64 md:flex-col md:fixed md:inset-y-0">
        <div className="flex flex-col flex-grow border-r border-gray-200 pt-5 bg-white overflow-y-auto">
          <div className="flex items-center flex-shrink-0 px-4">
            <h1 className="text-xl font-bold text-gray-900">EDMS</h1>
            {apiStatus && (
              <div className={`ml-auto w-3 h-3 rounded-full ${
                apiStatus.status === 'healthy' ? 'bg-green-400' : 
                apiStatus.status === 'degraded' ? 'bg-yellow-400' : 'bg-red-400'
              }`} title={`API Status: ${apiStatus.status}`} />
            )}
          </div>
          <div className="mt-5 flex-grow flex flex-col">
            <nav className="flex-1 px-2 pb-4 space-y-1">
              {navigation.map((item) => (
                <Link
                  key={item.name}
                  to={item.href}
                  className={`${
                    item.current
                      ? 'bg-gray-100 text-gray-900'
                      : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                  } group flex items-center px-2 py-2 text-sm font-medium rounded-md`}
                >
                  <item.icon className="mr-3 flex-shrink-0 h-5 w-5" />
                  <span className="flex-1">{item.name}</span>
                  {item.badge && item.badge > 0 && (
                    <span className="ml-2 inline-flex items-center justify-center bg-red-100 text-red-800 text-xs font-medium px-2.5 py-0.5 rounded-full min-w-[20px]">
                      {item.badge}
                    </span>
                  )}
                </Link>
              ))}
            </nav>
          </div>
        </div>
      </div>

      {/* Main content */}
      <div className="md:pl-64 flex flex-col flex-1">
        {/* Top header */}
        <div className="sticky top-0 z-10 flex-shrink-0 flex h-16 bg-white shadow">
          <button
            type="button"
            className="px-4 border-r border-gray-200 text-gray-500 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-indigo-500 md:hidden"
            onClick={() => setSidebarOpen(true)}
          >
            <Bars3Icon className="h-6 w-6" />
          </button>
          
          <div className="flex-1 px-4 flex justify-between">
            {/* Page title or breadcrumbs could go here in the future */}
            <div className="flex-1 flex items-center">
              <h2 className="text-lg font-medium text-gray-900">
                {(location.pathname === '/' || location.pathname === '/document-management') && location.search.includes('filter=pending') && 'Active Documents'}
                {(location.pathname === '/' || location.pathname === '/document-management') && location.search.includes('filter=obsolete') && 'Obsolete Documents'}
                {(location.pathname === '/' || location.pathname === '/document-management') && !location.search.includes('filter=') && 'Document Library'}
                {location.pathname === '/admin' && 'Administration'}
              </h2>
            </div>
            
            {/* Right side */}
            <div className="ml-4 flex items-center md:ml-6">
              {/* NotificationBell removed - counter moved to "My Documents" navigation item */}

              {/* Profile dropdown */}
              <div className="ml-3 relative profile-dropdown">
                <div className="flex items-center">
                  <button
                    type="button"
                    onClick={() => setShowProfileDropdown(!showProfileDropdown)}
                    className="max-w-xs bg-white rounded-full flex items-center text-sm focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                  >
                    <UserIcon className="h-8 w-8 rounded-full text-gray-400" />
                  </button>
                  <div className="ml-3">
                    <div className="text-sm font-medium text-gray-700">
                      {user?.full_name || user?.username}
                    </div>
                    <div className="text-xs text-gray-500">
                      {user?.email}
                    </div>
                  </div>
                  <button
                    onClick={() => setShowProfileDropdown(!showProfileDropdown)}
                    className="ml-3 p-2 text-gray-400 hover:text-gray-500"
                    title="Account Options"
                  >
                    <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  </button>
                </div>

                {/* Profile dropdown menu */}
                {showProfileDropdown && (
                  <div className="absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none z-50">
                    <div className="py-1">
                      <button
                        onClick={() => {
                          setShowChangePassword(true);
                          setShowProfileDropdown(false);
                        }}
                        className="flex items-center w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                      >
                        <KeyIcon className="h-4 w-4 mr-3" />
                        Change Password
                      </button>
                      <hr className="my-1" />
                      <button
                        onClick={() => {
                          handleLogout();
                          setShowProfileDropdown(false);
                        }}
                        className="flex items-center w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                      >
                        <ArrowRightOnRectangleIcon className="h-4 w-4 mr-3" />
                        Logout
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Page content */}
        <main className="flex-1 overflow-y-auto">
          {children || <Outlet />}
        </main>
      </div>
      
      {/* Change Password Modal */}
      <ChangePasswordModal
        isOpen={showChangePassword}
        onClose={() => setShowChangePassword(false)}
        onSuccess={handlePasswordChangeSuccess}
      />
    </div>
  );
};

export default Layout;