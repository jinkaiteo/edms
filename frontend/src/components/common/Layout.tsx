/**
 * Main Layout Component for EDMS Frontend
 * 
 * Provides the main application layout with navigation,
 * header, sidebar, and content areas.
 */

import React, { useState, useEffect } from 'react';
import { Outlet, Link, useLocation, useNavigate } from 'react-router-dom';
import {
  DocumentTextIcon,
  Cog6ToothIcon,
  UserGroupIcon,
  ClipboardDocumentListIcon,
  UserIcon,
  ArrowRightOnRectangleIcon,
  Bars3Icon,
  XMarkIcon,
  ShieldCheckIcon,
  DocumentArrowUpIcon,
  ChartBarIcon,
  KeyIcon,
  ChevronDownIcon,
  ChevronRightIcon,
  ComputerDesktopIcon,
  ServerIcon,
  ChevronLeftIcon,
  ChevronDoubleLeftIcon,
  ChevronDoubleRightIcon,
  EnvelopeIcon
} from '@heroicons/react/24/outline';
import { useAuth } from '../../contexts/AuthContext.tsx';
import { apiService } from '../../services/api.ts';
import ChangePasswordModal from '../auth/ChangePasswordModal.tsx';
import APP_CONFIG from '../../config/app.ts';
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
  children?: NavigationItem[];
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const { user, authenticated, loading, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [showChangePassword, setShowChangePassword] = useState(false);
  const [showProfileDropdown, setShowProfileDropdown] = useState(false);
  const [expandedMenus, setExpandedMenus] = useState<Record<string, boolean>>({});

  // Document count state and refresh functionality
  const [documentCount, setDocumentCount] = useState<number>(0);

  // Smart badge refresh function  
  const refreshBadge = async () => {
    if (!authenticated || !user) {
      console.log('Badge refresh skipped - user not authenticated');
      return;
    }
    
    try {
      console.log('🔄 Badge refresh starting...');
      const data = await apiService.get('/documents/documents/?filter=my_tasks');
      const documents = data.results || [];
      const count = documents.length;
      
      setDocumentCount(count);
      console.log(`✅ Badge refreshed successfully: ${count} documents`);
      
      return count;
    } catch (err) {
      console.error('❌ Failed to refresh badge:', err);
      console.error('Badge refresh error details:', err.response?.data || err.message || 'Unknown error');
      console.error('Full error object:', err);
      
      // Don't reset to 0 on error - keep current count
      console.log('Keeping current badge count due to error');
    }
  };

  // Enhanced polling with immediate refresh capability
  useEffect(() => {
    if (!authenticated || !user) return;

    // Initial fetch
    refreshBadge();
    
    // Listen for global badge refresh events from workflow components
    const handleBadgeRefreshEvent = () => {
      refreshBadge();
    };
    
    window.addEventListener('badgeRefresh', handleBadgeRefreshEvent);
    
    // EVENT-DRIVEN: Minimal backup polling (5 minutes) for safety net only
    const backupPolling = setInterval(() => {
      console.log('🔄 Backup polling: 5-minute safety refresh');
      refreshBadge();
    }, 5 * 60 * 1000); // 5 minutes instead of 60 seconds

    return () => {
      window.removeEventListener('badgeRefresh', handleBadgeRefreshEvent);
      clearInterval(backupPolling);
    };
  }, [authenticated, user]); // FIXED: Removed lastRefreshTime to prevent infinite loop

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
      { name: 'My Tasks', href: '/?filter=pending', icon: ClipboardDocumentListIcon, badge: documentCount },
      { name: 'Periodic Reviews', href: '/?filter=periodic_review', icon: ClipboardDocumentListIcon },
      { name: 'Obsolete Documents', href: '/?filter=obsolete', icon: DocumentTextIcon },
    ];
    
    // Debug: Check navigation item construction
    console.log('🔍 Navigation debug:', {
      documentCount,
      documentCountType: typeof documentCount,
      activeDocItem: baseItems[1]
    });

    // Add role-based items with submenus
    const adminItems: NavigationItem[] = [
      { 
        name: 'Administration', 
        href: '/administration', 
        icon: Cog6ToothIcon, 
        roles: ['admin'],
        children: [
          { name: 'User Management', href: '/administration?tab=users', icon: UserGroupIcon },
          { name: 'Placeholder Management', href: '/administration?tab=placeholders', icon: DocumentTextIcon },
          { name: 'Email Notifications', href: '/administration?tab=notifications', icon: EnvelopeIcon },
          { name: 'Backup Management', href: '/administration?tab=backup', icon: ServerIcon },
          { name: 'Reports', href: '/administration?tab=reports', icon: ChartBarIcon },
          { name: 'Scheduler Dashboard', href: '/administration?tab=scheduler', icon: ComputerDesktopIcon },
          { name: 'Audit Trail', href: '/administration?tab=audit', icon: ShieldCheckIcon },
          // { name: 'System Settings', href: '/administration?tab=settings', icon: Cog6ToothIcon }, // Disabled - not yet implemented
        ]
      },
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
        // Add counter badge to "My Tasks"
        badge: item.href.includes('?filter=pending') && documentCount > 0 ? documentCount : undefined
      };
    }
    
    // For other items, check if pathname matches and no conflicting query params  
    const isPathMatch = (item.href === '/' && (location.pathname === '/' || location.pathname === '/document-management')) ||
                        location.pathname.startsWith(item.href);
    const hasFilterParam = location.search.includes('filter=pending') || 
                          location.search.includes('filter=obsolete') ||
                          location.search.includes('filter=periodic_review');
    
    // \"Document Library\" should not be active if we're viewing filtered documents OR admin pages
    if (item.href === '/' && (hasFilterParam || location.pathname.startsWith('/administration'))) {
      return {
        ...item,
        current: false
      };
    }
    
    // \"Administration\" should be active for all /administration paths
    if (item.name === 'Administration' && location.pathname.startsWith('/administration')) {
      return {
        ...item,
        current: true
      };
    }
    
    // Other items should not be active when on admin pages
    if (location.pathname.startsWith('/administration') && item.href !== '/administration') {
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
    successMessage.className = 'fixed top-4 right-4 bg-green-500 text-white px-6 py-3 rounded-lg shadow-lg z-30';
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

  const toggleSubmenu = (itemName: string) => {
    setExpandedMenus(prev => ({
      ...prev,
      [itemName]: !prev[itemName]
    }));
    
    // Clear current selection when expanding Administration submenu
    if (itemName === 'Administration') {
      // Force navigation to administration route to clear other selections
      navigate('/administration');
    }
  };

  const isSubmenuExpanded = (itemName: string) => {
    return expandedMenus[itemName] || false;
  };

  // Show loading state while checking authentication
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  // Redirect to login if not authenticated (after loading completes)
  if (!authenticated) {
    navigate('/login');
    return null;
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
            <h1 className="text-xl font-bold text-gray-900">{APP_CONFIG.title}</h1>
          </div>
          <div className="mt-5 flex-1 h-0 overflow-y-auto">
            <nav className="px-2 space-y-1">
              {navigation.map((item) => (
                <div key={item.name}>
                  {item.children ? (
                    // Parent item with children
                    <div>
                      <button
                        onClick={() => toggleSubmenu(item.name)}
                        className={`${
                          item.current
                            ? 'bg-gray-100 text-gray-900'
                            : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                        } group w-full flex items-center px-2 py-2 text-sm font-medium rounded-md`}
                      >
                        <item.icon className="mr-3 flex-shrink-0 h-5 w-5" />
                        <span className="flex-1 text-left">{item.name}</span>
                        {item.badge && item.badge > 0 && (
                          <span className="mr-2 bg-red-100 text-red-800 text-xs font-medium px-2 py-0.5 rounded-full">
                            {item.badge}
                          </span>
                        )}
                        {isSubmenuExpanded(item.name) ? (
                          <ChevronDownIcon className="ml-auto h-4 w-4" />
                        ) : (
                          <ChevronRightIcon className="ml-auto h-4 w-4" />
                        )}
                      </button>
                      
                      {isSubmenuExpanded(item.name) && (
                        <div className="mt-1 space-y-1">
                          {item.children?.map((child) => {
                            // Handle Scheduler Dashboard differently (external link)
                            if (child.href.startsWith('/admin/scheduler')) {
                              return (
                                <a
                                  key={child.name}
                                  href={child.href}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="group flex items-center pl-10 pr-2 py-2 text-sm font-medium text-gray-600 hover:text-gray-900 hover:bg-gray-50 rounded-md"
                                  onClick={() => setSidebarOpen(false)}
                                >
                                  <child.icon className="mr-3 flex-shrink-0 h-4 w-4" />
                                  {child.name}
                                </a>
                              );
                            }
                            
                            // Use React Router Link for internal navigation
                            return (
                              <Link
                                key={child.name}
                                to={child.href}
                                className="group flex items-center pl-10 pr-2 py-2 text-sm font-medium text-gray-600 hover:text-gray-900 hover:bg-gray-50 rounded-md"
                                onClick={() => setSidebarOpen(false)}
                              >
                                <child.icon className="mr-3 flex-shrink-0 h-4 w-4" />
                                {child.name}
                              </Link>
                            );
                          })}
                        </div>
                      )}
                    </div>
                  ) : (
                    // Regular item without children
                    <Link
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
                  )}
                </div>
              ))}
            </nav>
          </div>
        </div>
      </div>

      {/* Static sidebar for desktop */}
      <div className={`hidden md:flex md:flex-col md:fixed md:inset-y-0 transition-all duration-300 ${
        sidebarCollapsed ? 'md:w-16' : 'md:w-64'
      }`}>
        <div className="flex flex-col flex-grow border-r border-gray-200 pt-5 bg-white overflow-y-auto">
          <div className="flex items-center flex-shrink-0 px-4 justify-between">
            {!sidebarCollapsed && (
              <>
                <h1 className="text-xl font-bold text-gray-900">{APP_CONFIG.title}</h1>
                <button
                  onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
                  className="p-1 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-md transition-colors"
                  title="Collapse sidebar"
                >
                  <ChevronDoubleLeftIcon className="h-5 w-5" />
                </button>
              </>
            )}
            {sidebarCollapsed && (
              <div className="w-full flex items-center justify-between">
                <h1 className="text-xl font-bold text-gray-900">{APP_CONFIG.title.charAt(0)}</h1>
                <button
                  onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
                  className="p-1 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-md transition-colors"
                  title="Expand sidebar"
                >
                  <ChevronDoubleRightIcon className="h-5 w-5" />
                </button>
              </div>
            )}
          </div>
          
          <div className="mt-5 flex-grow flex flex-col">
            <nav className="flex-1 px-2 pb-4 space-y-1">
              {navigation.map((item) => (
                <div key={item.name}>
                  {item.children ? (
                    // Parent item with children
                    <div>
                      <button
                        onClick={() => toggleSubmenu(item.name)}
                        className={`${
                          item.current
                            ? 'bg-gray-100 text-gray-900'
                            : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                        } group w-full flex items-center ${sidebarCollapsed ? 'justify-center' : 'px-2'} py-2 text-sm font-medium rounded-md relative`}
                        title={sidebarCollapsed ? item.name : ''}
                      >
                        <item.icon className={`${sidebarCollapsed ? '' : 'mr-3'} flex-shrink-0 h-5 w-5`} />
                        {!sidebarCollapsed && <span className="flex-1 text-left">{item.name}</span>}
                        {!sidebarCollapsed && item.badge && item.badge > 0 && (
                          <span className="mr-2 inline-flex items-center justify-center bg-red-100 text-red-800 text-xs font-medium px-2.5 py-0.5 rounded-full min-w-[20px]">
                            {item.badge}
                          </span>
                        )}
                        {sidebarCollapsed && item.badge && item.badge > 0 && (
                          <span className="absolute -top-1 -right-1 inline-flex items-center justify-center bg-red-500 text-white text-xs font-bold rounded-full w-5 h-5">
                            {item.badge}
                          </span>
                        )}
                        {!sidebarCollapsed && (isSubmenuExpanded(item.name) ? (
                          <ChevronDownIcon className="ml-auto h-4 w-4" />
                        ) : (
                          <ChevronRightIcon className="ml-auto h-4 w-4" />
                        ))}
                      </button>
                      
                      {!sidebarCollapsed && isSubmenuExpanded(item.name) && (
                        <div className="mt-1 space-y-1">
                          {item.children?.map((child) => {
                            // Handle Scheduler Dashboard differently (external link)
                            if (child.href.startsWith('/admin/scheduler')) {
                              return (
                                <a
                                  key={child.name}
                                  href={child.href}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="group flex items-center pl-10 pr-2 py-2 text-sm font-medium text-gray-600 hover:text-gray-900 hover:bg-gray-50 rounded-md"
                                >
                                  <child.icon className="mr-3 flex-shrink-0 h-4 w-4" />
                                  {child.name}
                                </a>
                              );
                            }
                            
                            // Use React Router Link for internal navigation
                            return (
                              <Link
                                key={child.name}
                                to={child.href}
                                className="group flex items-center pl-10 pr-2 py-2 text-sm font-medium text-gray-600 hover:text-gray-900 hover:bg-gray-50 rounded-md"
                              >
                                <child.icon className="mr-3 flex-shrink-0 h-4 w-4" />
                                {child.name}
                              </Link>
                            );
                          })}
                        </div>
                      )}
                    </div>
                  ) : (
                    // Regular item without children
                    <Link
                      to={item.href}
                      className={`${
                        item.current
                          ? 'bg-gray-100 text-gray-900'
                          : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                      } group flex items-center ${sidebarCollapsed ? 'justify-center' : 'px-2'} py-2 text-sm font-medium rounded-md relative`}
                      title={sidebarCollapsed ? item.name : ''}
                    >
                      <item.icon className={`${sidebarCollapsed ? '' : 'mr-3'} flex-shrink-0 h-5 w-5`} />
                      {!sidebarCollapsed && <span className="flex-1">{item.name}</span>}
                      {!sidebarCollapsed && item.badge && item.badge > 0 && (
                        <span className="ml-2 inline-flex items-center justify-center bg-red-100 text-red-800 text-xs font-medium px-2.5 py-0.5 rounded-full min-w-[20px]">
                          {item.badge}
                        </span>
                      )}
                      {sidebarCollapsed && item.badge && item.badge > 0 && (
                        <span className="absolute -top-1 -right-1 inline-flex items-center justify-center bg-red-500 text-white text-xs font-bold rounded-full w-5 h-5">
                          {item.badge}
                        </span>
                      )}
                    </Link>
                  )}
                </div>
              ))}
            </nav>
          </div>
        </div>
      </div>

      {/* Main content */}
      <div className={`flex flex-col flex-1 transition-all duration-300 ${
        sidebarCollapsed ? 'md:pl-16' : 'md:pl-64'
      }`}>
        {/* Top header */}
        <div className="sticky top-0 z-50 flex-shrink-0 flex h-16 bg-white shadow">
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
                {(location.pathname === '/' || location.pathname === '/document-management') && location.search.includes('filter=pending') && 'My Tasks'}
                {(location.pathname === '/' || location.pathname === '/document-management') && location.search.includes('filter=obsolete') && 'Obsolete Documents'}
                {(location.pathname === '/' || location.pathname === '/document-management') && !location.search.includes('filter=') && 'Document Library'}
                {location.pathname === '/administration' && 'Administration'}
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
                  <div className="absolute right-0 mt-2 w-80 bg-white rounded-md shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none z-50">
                    <div className="py-1">
                      {/* About Section */}
                      <div className="px-4 py-3 border-b border-gray-200">
                        <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
                          About EDMS
                        </div>
                        <div className="space-y-1 text-sm">
                          <div className="flex justify-between">
                            <span className="text-gray-600">Version:</span>
                            <span className="font-medium text-gray-900">1.3.2</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-600">Build Date:</span>
                            <span className="font-medium text-gray-900">2026-02-06</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-600">Environment:</span>
                            <span className="font-medium text-gray-900">{process.env.NODE_ENV === 'production' ? 'Production' : 'Development'}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-600">Backend:</span>
                            <span className="font-medium text-gray-900">Django 4.2</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-600">Frontend:</span>
                            <span className="font-medium text-gray-900">React 18</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-600">Database:</span>
                            <span className="font-medium text-gray-900">PostgreSQL</span>
                          </div>
                        </div>
                        <div className="mt-2 pt-2 border-t border-gray-100">
                          <div className="flex items-center justify-between mb-2">
                            <span className="text-xs font-medium text-gray-500">System Status</span>
                            <div className="flex items-center">
                              <div className="h-2 w-2 bg-green-500 rounded-full mr-1.5 animate-pulse"></div>
                              <span className="text-xs font-medium text-green-600">Operational</span>
                            </div>
                          </div>
                          <p className="text-xs text-gray-500">
                            © 2024-2026 EDMS. All rights reserved.
                          </p>
                        </div>
                      </div>
                      
                      {/* Actions */}
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