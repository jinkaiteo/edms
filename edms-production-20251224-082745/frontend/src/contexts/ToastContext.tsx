import React, { createContext, useContext, useState, useCallback, ReactNode } from 'react';
import { ToastContainer, ToastMessage } from '../components/common/Toast.tsx';

interface ToastContextType {
  showToast: (toast: Omit<ToastMessage, 'id'>) => void;
  showSuccess: (title: string, message: string, duration?: number) => void;
  showError: (title: string, message: string, duration?: number) => void;
  showWarning: (title: string, message: string, duration?: number) => void;
  showInfo: (title: string, message: string, duration?: number) => void;
  removeToast: (id: string) => void;
  clearAllToasts: () => void;
}

const ToastContext = createContext<ToastContextType | undefined>(undefined);

export const useToast = (): ToastContextType => {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error('useToast must be used within a ToastProvider');
  }
  return context;
};

interface ToastProviderProps {
  children: ReactNode;
  maxToasts?: number;
}

export const ToastProvider: React.FC<ToastProviderProps> = ({ 
  children, 
  maxToasts = 5 
}) => {
  const [toasts, setToasts] = useState<ToastMessage[]>([]);

  const generateId = useCallback((): string => {
    return `toast-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }, []);

  const showToast = useCallback((toast: Omit<ToastMessage, 'id'>) => {
    const newToast: ToastMessage = {
      ...toast,
      id: generateId(),
    };

    setToasts(prevToasts => {
      const updatedToasts = [newToast, ...prevToasts];
      
      // Limit the number of toasts
      if (updatedToasts.length > maxToasts) {
        return updatedToasts.slice(0, maxToasts);
      }
      
      return updatedToasts;
    });
  }, [generateId, maxToasts]);

  const showSuccess = useCallback((title: string, message: string, duration?: number) => {
    showToast({ type: 'success', title, message, duration });
  }, [showToast]);

  const showError = useCallback((title: string, message: string, duration?: number) => {
    showToast({ type: 'error', title, message, duration: duration || 8000 });
  }, [showToast]);

  const showWarning = useCallback((title: string, message: string, duration?: number) => {
    showToast({ type: 'warning', title, message, duration });
  }, [showToast]);

  const showInfo = useCallback((title: string, message: string, duration?: number) => {
    showToast({ type: 'info', title, message, duration });
  }, [showToast]);

  const removeToast = useCallback((id: string) => {
    setToasts(prevToasts => prevToasts.filter(toast => toast.id !== id));
  }, []);

  const clearAllToasts = useCallback(() => {
    setToasts([]);
  }, []);

  const value: ToastContextType = {
    showToast,
    showSuccess,
    showError,
    showWarning,
    showInfo,
    removeToast,
    clearAllToasts,
  };

  return (
    <ToastContext.Provider value={value}>
      {children}
      <ToastContainer toasts={toasts} onRemove={removeToast} />
    </ToastContext.Provider>
  );
};

export default ToastContext;