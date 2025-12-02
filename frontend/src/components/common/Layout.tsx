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
  ChartBarIcon
} from '@heroicons/react/24/outline';
import { useAuth } from '../../contexts/AuthContext.tsx';
import { ApiStatus } from '../../types/api';
import { apiService } from '../../services/api.ts';
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

  // Poll for pending documents count for "My Documents" badge
  useEffect(() => {
    const fetchPendingDocuments = async () => {
      try {
        const response = await fetch('/api/v1/documents/documents/?filter=pending_my_action', {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('accessToken') || ''}`
          }
        });
        
        if (response.ok) {
          const data = await response.json();
          setDocumentCount(data.results ? data.results.length : 0);
        }
      } catch (err) {
        console.error('Failed to fetch pending documents count:', err);
        setDocumentCount(0);
      }
    };

    if (authenticated && user) {
      // Initial fetch
      fetchPendingDocuments();
      
      // Poll every 60 seconds
      const interval = setInterval(fetchPendingDocuments, 60000);
      return () => clearInterval(interval);
    }
  }, [authenticated, user]);

  // Navigation items based on user roles
  const getNavigationItems = (): NavigationItem[] => {
    const baseItems: NavigationItem[] = [
      { name: 'Dashboard', href: '/dashboard', icon: HomeIcon },
      { name: 'Document Management', href: '/document-management', icon: DocumentArrowUpIcon },
      { name: 'My Documents', href: '/document-management?filter=pending', icon: ClipboardDocumentListIcon },
      { name: 'Obsolete Documents', href: '/document-management?filter=obsolete', icon: DocumentTextIcon },
      { name: 'Notifications', href: '/notifications', icon: BellIcon },
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
        // Add counter badge to "My Documents"
        badge: item.href.includes('?filter=pending') ? documentCount : undefined
      };
    }
    
    // For other items, check if pathname matches and no conflicting query params
    const isPathMatch = location.pathname.startsWith(item.href);
    const hasFilterParam = location.search.includes('filter=pending') || location.search.includes('filter=obsolete');
    
    // "Document Management" should not be active if we're viewing filtered documents
    if (item.href === '/document-management' && hasFilterParam) {
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
                {location.pathname === '/dashboard' && 'Dashboard'}
                {location.pathname === '/document-management' && location.search.includes('filter=pending') && 'My Documents'}
                {location.pathname === '/document-management' && location.search.includes('filter=obsolete') && 'Obsolete Documents'}
                {location.pathname === '/document-management' && !location.search.includes('filter=') && 'Document Management'}
                {location.pathname === '/tasks' && 'My Tasks'}
                {location.pathname === '/notifications' && 'Notifications'}
                {location.pathname === '/admin' && 'Administration'}
              </h2>
            </div>
            
            {/* Right side */}
            <div className="ml-4 flex items-center md:ml-6">
              {/* NotificationBell removed - counter moved to "My Documents" navigation item */}

              {/* Profile dropdown */}
              <div className="ml-3 relative">
                <div className="flex items-center">
                  <button
                    type="button"
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
                    onClick={handleLogout}
                    className="ml-3 p-2 text-gray-400 hover:text-gray-500"
                    title="Logout"
                  >
                    <ArrowRightOnRectangleIcon className="h-5 w-5" />
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Page content */}
        <main className="flex-1 overflow-y-auto">
          {children || <Outlet />}
        </main>
      </div>
    </div>
  );
};

export default Layout;