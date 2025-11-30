import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import './App.css';
import Dashboard from './pages/Dashboard.tsx';
import Login from './pages/Login.tsx';
import DocumentManagement from './pages/DocumentManagement.tsx';
import AdminDashboard from './pages/AdminDashboard.tsx';
import MyTasksStandalone from './pages/MyTasksStandalone.tsx';
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
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="/document-management" element={<DocumentManagement />} />
        <Route path="/my-tasks" element={<MyTasksStandalone />} />
        <Route path="/tasks" element={<MyTasksStandalone />} />
        <Route path="/notifications" element={<Notifications />} />
        {/* Audit trail moved to admin interface - route kept for direct access only */}
        <Route path="/audit-trail" element={<AuditTrail />} />
        <Route path="/workflows" element={<Navigate to="/admin" replace />} />
        <Route path="/users" element={<Navigate to="/admin" replace />} />
        <Route path="/reports" element={<Navigate to="/admin" replace />} />
        <Route path="/admin" element={<AdminDashboard />} />
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