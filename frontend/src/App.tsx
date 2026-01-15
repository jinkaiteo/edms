import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import './App.css';
// Dashboard removed - Document Library is now the default landing page
import Login from './pages/Login.tsx';
import DocumentManagement from './pages/DocumentManagement.tsx';
import AdminDashboard from './pages/AdminDashboard.tsx';
// MyTasksStandalone removed - using document filters instead
import AuditTrail from './pages/AuditTrail.tsx';
import Notifications from './pages/Notifications.tsx';
// Removed problematic standalone pages - functionality integrated into AdminDashboard
import { AuthProvider } from './contexts/AuthContext.tsx';
import { EnhancedAuthProvider } from './contexts/EnhancedAuthContext.tsx';
import { ToastProvider } from './contexts/ToastContext.tsx';
import ErrorBoundary from './components/common/ErrorBoundary.tsx';
import { useAnnouncer } from './hooks/useAccessibility.ts';

function AppContent() {
  const { announce } = useAnnouncer();

  React.useEffect(() => {
    // Announce page navigation for screen readers
    const handleRouteChange = () => {
      const pageTitle = document.title || 'Page loaded';
      announce(`Navigated to ${pageTitle}`, 'polite');
      
      // Clear any selected documents when navigating between pages
      console.log('🔄 App: Clearing document selection on route change');
      window.dispatchEvent(new CustomEvent('clearDocumentSelection'));
    };

    // Listen for route changes
    window.addEventListener('popstate', handleRouteChange);
    
    return () => {
      window.removeEventListener('popstate', handleRouteChange);
    };
  }, [announce]);

  return (
    <div className="App min-h-screen bg-gray-50">
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/" element={<DocumentManagement />} />
        <Route path="/document-management" element={<Navigate to="/" replace />} />
        <Route path="/my-tasks" element={<Navigate to="/?filter=pending" replace />} />
        <Route path="/tasks" element={<Navigate to="/?filter=pending" replace />} />
        <Route path="/archived-documents" element={<Navigate to="/?filter=archived" replace />} />
        <Route path="/obsolete-documents" element={<Navigate to="/?filter=obsolete" replace />} />
        <Route path="/notifications" element={<Notifications />} />
        {/* Audit trail moved to admin interface - route kept for direct access only */}
        <Route path="/audit-trail" element={<AuditTrail />} />
        <Route path="/workflows" element={<Navigate to="/administration" replace />} />
        <Route path="/users" element={<Navigate to="/administration" replace />} />
        <Route path="/reports" element={<Navigate to="/administration" replace />} />
        <Route path="/administration" element={<AdminDashboard />} />
        {/* Redirect old /admin route to avoid conflict with backend Django admin */}
        <Route path="/admin" element={<Navigate to="/administration" replace />} />
      </Routes>
    </div>
  );
}

function App() {
  return (
    <ErrorBoundary
      onError={(error, errorInfo) => {
        // In production, you would send this to an error tracking service
        if (process.env.NODE_ENV === 'production') {
          console.error('Application Error:', error, errorInfo);
          // Example: logErrorToService(error, errorInfo);
        }
      }}
    >
      <ToastProvider maxToasts={4}>
        <EnhancedAuthProvider>
          <AuthProvider>
            <Router>
              <AppContent />
            </Router>
          </AuthProvider>
        </EnhancedAuthProvider>
      </ToastProvider>
    </ErrorBoundary>
  );
}

export default App;