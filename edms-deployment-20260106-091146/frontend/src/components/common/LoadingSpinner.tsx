/**
 * Enhanced Loading Spinner Component with Accessibility Features
 * 
 * Supports reduced motion preferences and multiple variants
 */

import React from 'react';
import { useReducedMotion } from '../../hooks/useAccessibility.ts';

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg' | 'xl';
  text?: string;
  className?: string;
  variant?: 'spinner' | 'pulse' | 'dots';
  overlay?: boolean;
}

const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  size = 'md',
  text,
  className = '',
  variant = 'spinner',
  overlay = false
}) => {
  const { prefersReducedMotion } = useReducedMotion();

  const sizeClasses = {
    sm: 'h-4 w-4',
    md: 'h-8 w-8',
    lg: 'h-12 w-12',
    xl: 'h-16 w-16'
  };

  const textSizeClasses = {
    sm: 'text-sm',
    md: 'text-base',
    lg: 'text-lg',
    xl: 'text-xl'
  };

  const renderSpinner = () => {
    if (prefersReducedMotion) {
      return (
        <div 
          className={`rounded-full border-2 border-gray-300 border-t-blue-600 ${sizeClasses[size]}`}
          role="status"
          aria-label={text || 'Loading'}
        >
          <span className="sr-only">{text || 'Loading...'}</span>
        </div>
      );
    }

    switch (variant) {
      case 'pulse':
        return (
          <div 
            className={`bg-blue-600 rounded-full animate-pulse ${sizeClasses[size]}`}
            role="status"
            aria-label={text || 'Loading'}
          >
            <span className="sr-only">{text || 'Loading...'}</span>
          </div>
        );
      
      case 'dots':
        return (
          <div className="flex space-x-1" role="status" aria-label={text || 'Loading'}>
            <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce"></div>
            <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
            <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
            <span className="sr-only">{text || 'Loading...'}</span>
          </div>
        );
      
      default: // spinner
        return (
          <div
            className={`animate-spin rounded-full border-2 border-gray-300 border-t-blue-600 ${sizeClasses[size]}`}
            role="status"
            aria-label={text || 'Loading'}
          >
            <span className="sr-only">{text || 'Loading...'}</span>
          </div>
        );
    }
  };

  if (overlay) {
    return (
      <div 
        className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
        role="dialog"
        aria-modal="true"
        aria-label="Loading"
      >
        <div className="bg-white rounded-lg p-6 shadow-xl">
          <div className={`flex flex-col items-center space-y-4 ${className}`}>
            {renderSpinner()}
            {text && (
              <p className={`text-gray-600 font-medium ${textSizeClasses[size]}`} aria-live="polite">
                {text}
              </p>
            )}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div 
      className={`flex flex-col items-center justify-center ${className}`}
      role="status"
      aria-live="polite"
    >
      {renderSpinner()}
      {text && (
        <p className={`mt-2 text-gray-600 ${textSizeClasses[size]}`}>
          {text}
        </p>
      )}
    </div>
  );
};

export default LoadingSpinner;